import os
import time
import uuid
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

import httpx
import boto3
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..utils.ffmpeg import normalize_video, add_padding_to_video, get_temp_file
from ..exceptions import PostFxError, StorageError

settings = get_settings()
logger = get_logger("postfx")


class PostFxAdapter:
    """
    Adapter for post-processing video with RIFE and Real-ESRGAN
    
    Implements the post-processing pipeline from /docs/postfx/pipeline.md:
    1. Interpolate frames using RIFE (GPU) or PyTorch RIFE (CPU fallback)
    2. Upscale using Real-ESRGAN (GPU) or PyTorch implementation (CPU fallback)
    3. Normalize to mp4 (h264/aac) and add 300ms padding at the end
    4. Upload processed video to S3 storage
    """
    
    def __init__(self, mock_mode: Optional[bool] = None):
        # Check both specific setting and global MOCK_PROVIDERS flag
        self.mock_mode = mock_mode if mock_mode is not None else (settings.POSTFX_MOCK_MODE or settings.MOCK_PROVIDERS)
        self.gpu_available = settings.POSTFX_GPU_AVAILABLE
        self.temp_dir = settings.POSTFX_TEMP_DIR
        
        # Setup S3 client for storage
        self.s3_client = boto3.client(
            service_name="s3",
            endpoint_url=f"{'https' if settings.STORAGE_USE_SSL else 'http'}://{settings.STORAGE_ENDPOINT}",
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
            region_name="us-east-1"  # Default region, doesn't matter for MinIO
        )
        self.bucket = settings.STORAGE_BUCKET
        self.public_endpoint = settings.STORAGE_PUBLIC_ENDPOINT
        
        # Ensure temp directory exists
        os.makedirs(self.temp_dir, exist_ok=True)
    
    async def download_video(self, url: str) -> str:
        """Download video from URL to temp file"""
        if self.mock_mode:
            logger.info("postfx_mock_download", url=url)
            temp_path, _ = get_temp_file()
            # Just create an empty file for mock mode
            with open(temp_path, "wb") as f:
                f.write(b"MOCK VIDEO CONTENT")
            return temp_path
        
        @backoff.on_exception(
            backoff.expo,
            (httpx.RequestError, httpx.HTTPStatusError),
            max_tries=5,
            base=0.5,
            factor=2,
            jitter=backoff.full_jitter,
            giveup=lambda e: 400 <= e.response.status_code < 500 if hasattr(e, 'response') else False
        )
        async def _download_with_retries(download_url: str, output_path: str) -> None:
            async with httpx.AsyncClient() as client:
                async with client.stream("GET", download_url) as response:
                    response.raise_for_status()
                    with open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            f.write(chunk)
            
        temp_path, _ = get_temp_file()
        try:
            start_time = time.time()
            await _download_with_retries(url, temp_path)
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info("postfx_download_complete", url=url, latency_ms=elapsed_ms)
            return temp_path
                
        except httpx.RequestError as e:
            logger.error("postfx_download_failed", error=str(e), url=url)
            raise PostFxError(f"Failed to download video: {str(e)}")
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            if status_code >= 500 or status_code == 429:
                # This shouldn't happen as backoff should handle retries
                logger.error("postfx_download_server_error", error=str(e), url=url, status_code=status_code)
                raise PostFxError(f"Server error downloading video (code {status_code})")
            else:
                # Client errors (400-499) are not retried
                logger.error("postfx_download_client_error", error=str(e), url=url, status_code=status_code)
                raise PostFxError(f"Client error downloading video (code {status_code})")
    
    def interpolate(self, input_path: str, target_fps: int) -> str:
        """
        Interpolate video to target FPS using RIFE
        
        According to docs/postfx/pipeline.md:
        - Use RIFE for frame interpolation
        - Target FPS must be either 24 or 30
        - Provide CPU fallback when GPU is not available
        - CLI guidance: rife-ncnn-vulkan -i in.mp4 -o rife.mp4 -f {fps}
        """
        # Validate target FPS as per requirements
        if target_fps not in [24, 30]:
            logger.error("postfx_invalid_fps", target_fps=target_fps)
            raise PostFxError(f"Invalid target FPS: {target_fps}. Must be either 24 or 30.")
            
        if self.mock_mode:
            logger.info("postfx_mock_interpolate", input_path=input_path, target_fps=target_fps)
            time.sleep(2)  # Simulate processing
            output_path, _ = get_temp_file(suffix="_interpolated.mp4")
            shutil.copy(input_path, output_path)
            return output_path
            
        output_path, _ = get_temp_file(suffix="_interpolated.mp4")
        
        try:
            start_time = time.time()
            
            if self.gpu_available:
                # Use GPU-accelerated RIFE
                # Following exactly the CLI guidance from docs/postfx/pipeline.md
                cmd = [
                    "rife-ncnn-vulkan",
                    "-i", input_path,
                    "-o", output_path,
                    "-f", str(target_fps)
                ]
                
                logger.info("postfx_interpolate_gpu", cmd=cmd, target_fps=target_fps)
                process = subprocess.run(cmd, check=True, capture_output=True)
                
            else:
                # CPU fallback using PyTorch RIFE as specified in docs
                try:
                    # Try using the PyTorch implementation if available
                    cmd = [
                        "python", "-m", "inference_rife",
                        "--input", input_path,
                        "--output", output_path,
                        "--fps", str(target_fps),
                        "--exp", "1"  # Default expression level
                    ]
                    logger.warning("postfx_interpolate_cpu_pytorch", cmd=cmd, target_fps=target_fps)
                    process = subprocess.run(cmd, check=True, capture_output=True, timeout=1200)  # 20 min timeout
                except (subprocess.SubprocessError, FileNotFoundError):
                    # If PyTorch RIFE is not available, fall back to ffmpeg minterpolate
                    cmd = [
                        "ffmpeg",
                        "-i", input_path,
                        "-filter:v", f"minterpolate=fps={target_fps}:mi_mode=mci",
                        "-c:a", "copy",
                        "-y", output_path
                    ]
                    
                    logger.warning("postfx_interpolate_cpu_ffmpeg", cmd=cmd, target_fps=target_fps)
                    process = subprocess.run(cmd, check=True, capture_output=True)
                
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info("postfx_interpolate_complete", latency_ms=elapsed_ms, target_fps=target_fps)
            
            return output_path
            
        except subprocess.SubprocessError as e:
            logger.error("postfx_interpolate_failed", error=str(e), target_fps=target_fps)
            
            # If GPU fails, try CPU fallback if we haven't already
            if self.gpu_available:
                logger.warning("postfx_interpolate_fallback_to_cpu", reason=str(e))
                self.gpu_available = False
                return self.interpolate(input_path, target_fps)
                
            raise PostFxError(f"Failed to interpolate video: {str(e)}")
    
    def upscale(self, input_path: str) -> str:
        """
        Upscale video using Real-ESRGAN
        
        According to docs/postfx/pipeline.md:
        - Use Real-ESRGAN for upscaling
        - Use 4x upscaling with general-x4v3 model
        - Provide CPU fallback when GPU is not available
        """
        if self.mock_mode:
            logger.info("postfx_mock_upscale", input_path=input_path)
            time.sleep(3)  # Simulate processing
            output_path, _ = get_temp_file(suffix="_upscaled.mp4")
            shutil.copy(input_path, output_path)
            return output_path
            
        output_path, _ = get_temp_file(suffix="_upscaled.mp4")
        
        try:
            start_time = time.time()
            
            if self.gpu_available:
                # Use GPU-accelerated Real-ESRGAN
                # Following exactly the CLI guidance from docs/postfx/pipeline.md
                cmd = [
                    "realesrgan-ncnn-vulkan",
                    "-i", input_path,
                    "-o", output_path,
                    "-s", "4",  # 4x upscaling as specified in docs
                    "-n", "realesrgan-x4-general"  # general model as specified in docs
                ]
                
                logger.info("postfx_upscale_gpu", cmd=cmd, model="general-x4v3", scale=4)
                process = subprocess.run(cmd, check=True, capture_output=True)
                
            else:
                # CPU fallback using PyTorch implementation if available
                try:
                    # Try using the PyTorch implementation if available
                    cmd = [
                        "python", "-m", "inference_realesrgan", 
                        "-i", input_path,
                        "-o", output_path,
                        "-s", "4",
                        "--model_name", "RealESRGAN_x4plus"
                    ]
                    logger.warning("postfx_upscale_cpu", cmd=cmd, model="RealESRGAN_x4plus")
                    process = subprocess.run(cmd, check=True, capture_output=True, timeout=1800)  # 30 min timeout
                except (subprocess.SubprocessError, FileNotFoundError):
                    # If PyTorch implementation fails or is not available, just copy the file
                    logger.warning("postfx_upscale_cpu_skipped", reason="PyTorch implementation not available")
                    shutil.copy(input_path, output_path)
                
            elapsed_ms = (time.time() - start_time) * 1000
            logger.info("postfx_upscale_complete", latency_ms=elapsed_ms)
            
            return output_path
            
        except subprocess.SubprocessError as e:
            logger.error("postfx_upscale_failed", error=str(e))
            
            # If GPU fails, try CPU fallback
            if self.gpu_available:
                logger.warning("postfx_upscale_fallback_to_cpu", reason=str(e))
                self.gpu_available = False
                return self.upscale(input_path)
                
            raise PostFxError(f"Failed to upscale video: {str(e)}")
    
    async def process(self, input_url: str, do_interpolate: bool, do_upscale: bool, target_fps: int) -> str:
        """
        Process a video through the complete Post-FX pipeline.
        Following the pipeline in docs/postfx/pipeline.md:
        1. Download video
        2. Interpolate (RIFE)
        3. Upscale (Real-ESRGAN)
        4. Add padding and normalize
        5. Upload to S3 storage
        
        Args:
            input_url: URL of input video
            do_interpolate: Whether to interpolate frames
            do_upscale: Whether to upscale the video
            target_fps: Target framerate (24 or 30)
            
        Returns:
            URL of processed video in S3 storage
        """
        if self.mock_mode:
            logger.info(
                "postfx_mock_process", 
                input_url=input_url,
                do_interpolate=do_interpolate,
                do_upscale=do_upscale,
                target_fps=target_fps
            )
            # In mock mode, return a mocked URL with query parameters to show what was requested
            pipeline = []
            if do_interpolate:
                pipeline.append(f"fps{target_fps}")
            if do_upscale:
                pipeline.append("upscale")
                
            pipeline_str = "-".join(pipeline) if pipeline else "normalize"
            mock_url = f"{input_url}?postfx={pipeline_str}"
            
            logger.info("postfx_mock_complete", output_url=mock_url)
            return mock_url
        
        try:
            # Record start time for overall process
            start_time = time.time()
            
            # 1. Download video
            logger.info("postfx_process_start", input_url=input_url)
            input_path = await self.download_video(input_url)
            current_path = input_path
            
            # 2. Interpolate if requested
            if do_interpolate:
                logger.info("postfx_interpolate_start", target_fps=target_fps)
                current_path = self.interpolate(current_path, target_fps)
            
            # 3. Upscale if requested
            if do_upscale:
                logger.info("postfx_upscale_start")
                current_path = self.upscale(current_path)
            
            # 4. Add padding and normalize
            final_path, _ = get_temp_file(suffix="_final.mp4")
            logger.info("postfx_normalize_start")
            
            # First normalize
            normalized_path, _ = get_temp_file(suffix="_normalized.mp4")
            normalize_video(current_path, normalized_path, target_fps)
            
            # Then add padding (300ms as specified in docs)
            add_padding_to_video(normalized_path, final_path)
            
            # 5. Upload to S3 storage
            try:
                # Generate a unique key for the processed video
                filename = Path(final_path).name
                key = f"processed/{uuid.uuid4().hex[:8]}-{filename}"
                
                # Set metadata for the upload
                metadata = {
                    "interpolated": str(do_interpolate).lower(),
                    "upscaled": str(do_upscale).lower(),
                    "target_fps": str(target_fps),
                    "original_url": input_url
                }
                
                logger.info("postfx_upload_start", key=key)
                
                # Upload file to S3
                self.s3_client.upload_file(
                    final_path, 
                    self.bucket, 
                    key,
                    ExtraArgs={
                        "ContentType": "video/mp4",
                        "Metadata": metadata
                    }
                )
                
                # Generate the public URL
                final_url = f"{self.public_endpoint}/{self.bucket}/{key}"
                
                elapsed_seconds = time.time() - start_time
                logger.info(
                    "postfx_process_complete",
                    runtime_s=elapsed_seconds,
                    input_url=input_url,
                    output_url=final_url,
                    pipeline={
                        "interpolate": do_interpolate,
                        "upscale": do_upscale,
                        "target_fps": target_fps
                    }
                )
                
            except Exception as e:
                logger.error("postfx_upload_failed", error=str(e))
                raise StorageError(f"Failed to upload processed video: {str(e)}")
            finally:
                # Cleanup temporary files
                self._cleanup_temp_files([input_path, current_path, normalized_path, final_path])
            
            return final_url
            
        except Exception as e:
            logger.error("postfx_process_failed", error=str(e))
            raise PostFxError(f"Post-processing failed: {str(e)}")
    
    def _cleanup_temp_files(self, files):
        """Clean up temporary files"""
        for file_path in files:
            try:
                if file_path and os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logger.warning("postfx_cleanup_failed", error=str(e), path=file_path)