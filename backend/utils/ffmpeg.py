import os
import json
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, Tuple

from .logging import get_logger
from .settings import get_settings

settings = get_settings()
logger = get_logger("ffmpeg")


def check_ffmpeg_installed() -> bool:
    """Check if FFmpeg is installed and available in PATH"""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except (subprocess.SubprocessError, FileNotFoundError):
        logger.error("ffmpeg_not_found", message="FFmpeg is not installed or not in PATH")
        return False


def get_video_info(video_path: str) -> Dict:
    """Get video information using ffprobe"""
    try:
        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            video_path
        ]
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except (subprocess.SubprocessError, json.JSONDecodeError) as e:
        logger.error("ffprobe_failed", error=str(e), video_path=video_path)
        raise RuntimeError(f"Failed to get video info: {str(e)}")


def add_padding_to_video(video_path: str, output_path: str, padding_ms: int = 300) -> str:
    """Add padding to the end of the video (300ms by default)"""
    try:
        cmd = [
            "ffmpeg",
            "-i", video_path,
            "-vf", f"tpad=stop_duration={padding_ms/1000}:stop_mode=clone",
            "-c:a", "copy",
            "-y", output_path
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.SubprocessError as e:
        logger.error("padding_failed", error=str(e), video_path=video_path)
        raise RuntimeError(f"Failed to add padding to video: {str(e)}")


def normalize_video(video_path: str, output_path: str, target_fps: int = 24) -> str:
    """Normalize video to h264/aac or preserve ProRes with target framerate"""
    try:
        logger.info("Starting video normalization", 
                   input_path=video_path, 
                   output_path=output_path,
                   target_fps=target_fps,
                   exists=os.path.exists(video_path),
                   size=os.path.getsize(video_path) if os.path.exists(video_path) else None)
        
        # Get input video information
        info = get_video_info(video_path)
        video_stream = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
        audio_stream = next((s for s in info["streams"] if s["codec_type"] == "audio"), None)
        
        logger.info("Video streams analysis", 
                   video_codec=video_stream.get("codec_name") if video_stream else None,
                   video_width=video_stream.get("width") if video_stream else None,
                   video_height=video_stream.get("height") if video_stream else None,
                   video_fps=video_stream.get("r_frame_rate") if video_stream else None,
                   audio_codec=audio_stream.get("codec_name") if audio_stream else None,
                   audio_channels=audio_stream.get("channels") if audio_stream else None,
                   format_name=info.get("format", {}).get("format_name"))
        if video_stream and video_stream.get("codec_name", "").lower() == "prores":
            # For ProRes, preserve the video codec
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-c:v", "copy",  # Copy video stream without re-encoding
                "-r", str(target_fps),
                "-c:a", "aac",  # Convert audio to AAC
                "-b:a", "256k",  # Higher quality audio for pro format
                "-y", output_path
            ]
            logger.info("Using ProRes preservation pipeline", command=" ".join(cmd))
        else:
            # For other formats, use h264
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-r", str(target_fps),
                "-movflags", "+faststart",  # Enable streaming optimization
                "-c:a", "aac",
                "-b:a", "128k",
                "-y", output_path
            ]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return output_path
    except subprocess.SubprocessError as e:
        logger.error("normalization_failed", error=str(e), video_path=video_path)
        raise RuntimeError(f"Failed to normalize video: {str(e)}")


def get_temp_file(suffix: str = ".mp4") -> Tuple[str, str]:
    """Get a temporary file path and its directory"""
    os.makedirs(settings.POSTFX_TEMP_DIR, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(suffix=suffix, dir=settings.POSTFX_TEMP_DIR)
    os.close(fd)
    return temp_path, os.path.dirname(temp_path)


def process_and_upload_video(
    video_path: str, 
    add_padding: bool = True, 
    normalize: bool = True,
    job_id: str = None
) -> Tuple[str, str]:
    """
    Process a video (normalize and add padding) and upload to S3
    
    Args:
        video_path: Path to the input video file
        add_padding: Whether to add padding to the end of the video
        normalize: Whether to normalize the video (h264/aac)
        job_id: Optional job ID for logging
        
    Returns:
        Tuple of (storage_key, public_url)
    """
    from ..services.storage import StorageService
    from ..schemas.common import PresignKind
    from ..utils.logging import log_postfx_operation
    from ..exceptions import PostFxError
    
    logger.info("processing_video", path=video_path, add_padding=add_padding, normalize=normalize, job_id=job_id)
    start_time = time.time()
    
    # Verify FFmpeg is available
    if not check_ffmpeg_installed():
        error_msg = "FFmpeg is not available, cannot process video"
        log_postfx_operation(
            operation="process_video", 
            duration_s=time.time() - start_time,
            job_id=job_id,
            success=False,
            error=error_msg
        )
        raise PostFxError(error_msg)
    
    # Create storage service
    storage = StorageService()
    
    # Process the video if needed
    processed_path = video_path
    
    try:
        # Create temporary file for processing
        if add_padding or normalize:
            temp_path, _ = get_temp_file()
            
            # Add padding if requested
            if add_padding:
                padding_start = time.time()
                try:
                    padding_path, _ = get_temp_file()
                    processed_path = add_padding_to_video(processed_path, padding_path)
                    
                    # Log padding operation
                    log_postfx_operation(
                        operation="add_padding", 
                        duration_s=time.time() - padding_start,
                        job_id=job_id,
                        success=True
                    )
                    
                    # If no normalization needed, use this as the final path
                    if not normalize:
                        temp_path = padding_path
                except Exception as e:
                    # Log padding failure
                    log_postfx_operation(
                        operation="add_padding", 
                        duration_s=time.time() - padding_start,
                        job_id=job_id,
                        success=False,
                        error=str(e)
                    )
                    raise
            
            # Normalize if requested
            if normalize:
                normalize_start = time.time()
                try:
                    processed_path = normalize_video(processed_path, temp_path)
                    
                    # Log normalization operation
                    log_postfx_operation(
                        operation="normalize", 
                        duration_s=time.time() - normalize_start,
                        job_id=job_id,
                        success=True
                    )
                except Exception as e:
                    # Log normalization failure
                    log_postfx_operation(
                        operation="normalize", 
                        duration_s=time.time() - normalize_start,
                        job_id=job_id,
                        success=False,
                        error=str(e)
                    )
                    raise
        
        # Upload the processed video
        upload_start = time.time()
        try:
            storage_key, public_url = storage.upload_file(
                file_path=processed_path,
                kind=PresignKind.VIDEO
            )
            
            # Log upload operation
            log_postfx_operation(
                operation="upload", 
                duration_s=time.time() - upload_start,
                job_id=job_id,
                success=True
            )
        except Exception as e:
            # Log upload failure
            log_postfx_operation(
                operation="upload", 
                duration_s=time.time() - upload_start,
                job_id=job_id,
                success=False,
                error=str(e)
            )
            raise
        
        # Log overall success
        total_duration = time.time() - start_time
        log_postfx_operation(
            operation="process_video", 
            duration_s=total_duration,
            job_id=job_id,
            success=True
        )
        
        logger.info(
            "video_processed_and_uploaded", 
            original_path=video_path, 
            processed_path=processed_path,
            storage_key=storage_key, 
            public_url=public_url,
            duration_s=total_duration,
            job_id=job_id
        )
        
        return storage_key, public_url
        
    except Exception as e:
        # Log overall failure
        log_postfx_operation(
            operation="process_video", 
            duration_s=time.time() - start_time,
            job_id=job_id,
            success=False,
            error=str(e)
        )
        
        # Raise PostFxError
        if isinstance(e, PostFxError):
            raise
        else:
            raise PostFxError(f"Failed to process video: {str(e)}", detail={"error": str(e)})
            
    finally:
        # Clean up temporary files if they were created and are different from the input
        if processed_path != video_path and os.path.exists(processed_path):
            try:
                os.unlink(processed_path)
            except Exception as e:
                logger.warning("failed_to_delete_temp_file", path=processed_path, error=str(e))