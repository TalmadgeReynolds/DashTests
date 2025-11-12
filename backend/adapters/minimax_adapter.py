"""
MiniMax Hailuo 2.3 Video Generation Adapter

Supports all MiniMax Hailuo models and generation modes:
- Models: Hailuo 2.3, 2.3-Fast, 02
- Modes: Text-to-Video (T2V), Image-to-Video (I2V), First/Last Frame (FL2V), Subject Reference (S2V)
- Full async task management with polling and file download
"""
import time
import uuid
import base64
from typing import Dict, Optional, List, Literal, Union, Any
from enum import Enum

import httpx
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, TransientProviderError, ProviderTimeoutError, ProviderRateLimitError

settings = get_settings()
logger = get_logger("minimax_adapter")


class MinimaxModel(str, Enum):
    """Available MiniMax Hailuo models"""
    HAILUO_2_3 = "MiniMax-Hailuo-2.3"  # Premium model with best quality
    HAILUO_2_3_FAST = "MiniMax-Hailuo-2.3-Fast"  # Fast image-to-video
    HAILUO_02 = "MiniMax-Hailuo-02"  # Legacy model with 1080p support


class TaskStatus(str, Enum):
    """Task status values"""
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    QUEUED = "queued"


class GenerationMode(str, Enum):
    """Video generation modes"""
    TEXT_TO_VIDEO = "t2v"  # Text to video
    IMAGE_TO_VIDEO = "i2v"  # Image to video
    FIRST_LAST_TO_VIDEO = "fl2v"  # First frame + last frame to video
    SUBJECT_REFERENCE = "s2v"  # Subject reference to video


class MinimaxAdapter:
    """Adapter for MiniMax Hailuo 2.3 video generation with full feature support"""
    
    def __init__(self, api_key: Optional[str] = None, group_id: Optional[str] = None, mock_mode: bool = None):
        self.api_key = api_key or settings.MINIMAX_API_KEY
        self.group_id = group_id or getattr(settings, "MINIMAX_GROUP_ID", "")
        # Check both specific setting and global MOCK_PROVIDERS flag
        self.mock_mode = mock_mode if mock_mode is not None else (
            getattr(settings, "MINIMAX_MOCK_MODE", True) or settings.MOCK_PROVIDERS
        )
        
        # MiniMax API endpoints
        self.base_url = "https://api.minimax.io/v1/video_generation"
        self.query_url = "https://api.minimax.io/v1/query/video_generation"
        self.download_url = "https://api.minimax.io/v1/files/retrieve"
        
        if not self.api_key and not self.mock_mode:
            logger.warning("minimax_no_api_key", message="No MiniMax API key provided and mock mode is disabled")
    
    def _encode_image(self, image: Union[str, bytes]) -> str:
        """Encode image to base64 string"""
        if isinstance(image, bytes):
            return base64.b64encode(image).decode('utf-8')
        elif isinstance(image, str):
            # Check if already base64
            if image.startswith('data:image') or image.startswith('/9j/') or image.startswith('iVBOR'):
                return image
            # Assume it's a file path
            with open(image, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        return image
    
    def _build_headers(self) -> Dict[str, str]:
        """Build request headers"""
        headers = {
            "Content-Type": "application/json",
        }
        if self.api_key:
            headers["authorization"] = f"Bearer {self.api_key}"
        return headers
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    async def text_to_video(
        self,
        prompt: str,
        model: MinimaxModel = MinimaxModel.HAILUO_2_3,
        # Video parameters
        aspect_ratio: str = "16:9",
        duration_seconds: int = 6,
        # Enhancement options
        prompt_optimizer: bool = True,
        # Control parameters
        seed: Optional[int] = None,
        callback_url: Optional[str] = None,
    ) -> str:
        """
        Generate video from text prompt (T2V)
        
        Args:
            prompt: Text description of the video to generate
            model: Model to use for generation
            aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1, 4:3, 3:4, 21:9, 9:21)
            duration_seconds: Video duration (2-6 for Hailuo 2.3, up to 10 for Hailuo 02)
            prompt_optimizer: Enable automatic prompt enhancement
            seed: Random seed for reproducibility
            callback_url: Webhook URL for completion notification
            
        Returns:
            task_id: Task ID for status polling
        """
        if self.mock_mode:
            logger.info("minimax_mock_t2v", prompt=prompt[:50], model=model.value)
            time.sleep(0.5)
            mock_task_id = f"mock-minimax-t2v-{hash(prompt) % 10000:04d}"
            logger.info("minimax_mock_task_created", task_id=mock_task_id, mode="t2v")
            return mock_task_id
        
        payload = {
            "model": model.value,
            "prompt": prompt,
            "prompt_optimizer": prompt_optimizer,
        }
        
        # Add optional parameters
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if duration_seconds:
            payload["duration_seconds"] = duration_seconds
        if seed is not None:
            payload["seed"] = seed
        if callback_url:
            payload["callback_url"] = callback_url
        
        return await self._create_task(payload, GenerationMode.TEXT_TO_VIDEO)
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    async def image_to_video(
        self,
        prompt: str,
        first_frame_image: Union[str, bytes],
        model: MinimaxModel = MinimaxModel.HAILUO_2_3_FAST,
        # Video parameters
        aspect_ratio: str = "16:9",
        duration_seconds: int = 6,
        # Enhancement options
        prompt_optimizer: bool = True,
        # Control parameters
        seed: Optional[int] = None,
        callback_url: Optional[str] = None,
    ) -> str:
        """
        Generate video from image and text prompt (I2V)
        
        Args:
            prompt: Text description of how the image should animate
            first_frame_image: Input image (path, bytes, or base64 string)
            model: Model to use (Hailuo 2.3-Fast recommended for I2V)
            aspect_ratio: Video aspect ratio
            duration_seconds: Video duration
            prompt_optimizer: Enable automatic prompt enhancement
            seed: Random seed for reproducibility
            callback_url: Webhook URL for completion notification
            
        Returns:
            task_id: Task ID for status polling
        """
        if self.mock_mode:
            logger.info("minimax_mock_i2v", prompt=prompt[:50], model=model.value)
            time.sleep(0.5)
            mock_task_id = f"mock-minimax-i2v-{hash(prompt) % 10000:04d}"
            logger.info("minimax_mock_task_created", task_id=mock_task_id, mode="i2v")
            return mock_task_id
        
        # Encode image
        encoded_image = self._encode_image(first_frame_image)
        
        payload = {
            "model": model.value,
            "prompt": prompt,
            "first_frame_image": encoded_image,
            "prompt_optimizer": prompt_optimizer,
        }
        
        # Add optional parameters
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if duration_seconds:
            payload["duration_seconds"] = duration_seconds
        if seed is not None:
            payload["seed"] = seed
        if callback_url:
            payload["callback_url"] = callback_url
        
        return await self._create_task(payload, GenerationMode.IMAGE_TO_VIDEO)
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    async def first_last_frame_to_video(
        self,
        prompt: str,
        first_frame_image: Union[str, bytes],
        last_frame_image: Union[str, bytes],
        model: MinimaxModel = MinimaxModel.HAILUO_2_3,
        # Video parameters
        aspect_ratio: str = "16:9",
        duration_seconds: int = 6,
        # Enhancement options
        prompt_optimizer: bool = True,
        # Control parameters
        seed: Optional[int] = None,
        callback_url: Optional[str] = None,
    ) -> str:
        """
        Generate video interpolating between first and last frames (FL2V)
        
        Args:
            prompt: Text description of the transition/motion
            first_frame_image: Starting frame image
            last_frame_image: Ending frame image
            model: Model to use for generation
            aspect_ratio: Video aspect ratio
            duration_seconds: Video duration
            prompt_optimizer: Enable automatic prompt enhancement
            seed: Random seed for reproducibility
            callback_url: Webhook URL for completion notification
            
        Returns:
            task_id: Task ID for status polling
        """
        if self.mock_mode:
            logger.info("minimax_mock_fl2v", prompt=prompt[:50], model=model.value)
            time.sleep(0.5)
            mock_task_id = f"mock-minimax-fl2v-{hash(prompt) % 10000:04d}"
            logger.info("minimax_mock_task_created", task_id=mock_task_id, mode="fl2v")
            return mock_task_id
        
        # Encode images
        first_encoded = self._encode_image(first_frame_image)
        last_encoded = self._encode_image(last_frame_image)
        
        payload = {
            "model": model.value,
            "prompt": prompt,
            "first_frame_image": first_encoded,
            "last_frame_image": last_encoded,
            "prompt_optimizer": prompt_optimizer,
        }
        
        # Add optional parameters
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if duration_seconds:
            payload["duration_seconds"] = duration_seconds
        if seed is not None:
            payload["seed"] = seed
        if callback_url:
            payload["callback_url"] = callback_url
        
        return await self._create_task(payload, GenerationMode.FIRST_LAST_TO_VIDEO)
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    async def subject_reference_to_video(
        self,
        prompt: str,
        reference_image: Union[str, bytes],
        model: MinimaxModel = MinimaxModel.HAILUO_2_3,
        # Reference type
        reference_type: Literal["character", "style"] = "character",
        # Video parameters
        aspect_ratio: str = "16:9",
        duration_seconds: int = 6,
        # Enhancement options
        prompt_optimizer: bool = True,
        # Control parameters
        seed: Optional[int] = None,
        callback_url: Optional[str] = None,
    ) -> str:
        """
        Generate video with consistent subject/style from reference image (S2V)
        
        Args:
            prompt: Text description of the video
            reference_image: Reference image for character/style consistency
            model: Model to use for generation
            reference_type: Type of reference ("character" or "style")
            aspect_ratio: Video aspect ratio
            duration_seconds: Video duration
            prompt_optimizer: Enable automatic prompt enhancement
            seed: Random seed for reproducibility
            callback_url: Webhook URL for completion notification
            
        Returns:
            task_id: Task ID for status polling
        """
        if self.mock_mode:
            logger.info("minimax_mock_s2v", prompt=prompt[:50], model=model.value, ref_type=reference_type)
            time.sleep(0.5)
            mock_task_id = f"mock-minimax-s2v-{hash(prompt) % 10000:04d}"
            logger.info("minimax_mock_task_created", task_id=mock_task_id, mode="s2v")
            return mock_task_id
        
        # Encode reference image
        ref_encoded = self._encode_image(reference_image)
        
        payload = {
            "model": model.value,
            "prompt": prompt,
            "reference_image": ref_encoded,
            "reference_type": reference_type,
            "prompt_optimizer": prompt_optimizer,
        }
        
        # Add optional parameters
        if aspect_ratio:
            payload["aspect_ratio"] = aspect_ratio
        if duration_seconds:
            payload["duration_seconds"] = duration_seconds
        if seed is not None:
            payload["seed"] = seed
        if callback_url:
            payload["callback_url"] = callback_url
        
        return await self._create_task(payload, GenerationMode.SUBJECT_REFERENCE)
    
    async def _create_task(self, payload: Dict[str, Any], mode: GenerationMode) -> str:
        """
        Internal method to create a video generation task
        
        Args:
            payload: Request payload
            mode: Generation mode
            
        Returns:
            task_id: Task ID for polling
        """
        start_time = time.time()
        
        # Add group_id to payload if provided
        if self.group_id:
            payload["group_id"] = self.group_id
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                logger.info("minimax_create_task", mode=mode.value, model=payload.get("model"))
                
                response = await client.post(
                    f"{self.base_url}",
                    json=payload,
                    headers=self._build_headers()
                )
                
                elapsed = time.time() - start_time
                
                if response.status_code == 429:
                    logger.warning("minimax_rate_limit", elapsed=elapsed)
                    raise ProviderRateLimitError("MiniMax rate limit exceeded")
                
                if response.status_code >= 500:
                    logger.error("minimax_server_error", status=response.status_code, elapsed=elapsed)
                    raise TransientProviderError(f"MiniMax server error: {response.status_code}")
                
                response.raise_for_status()
                result = response.json()
                
                task_id = result.get("task_id")
                if not task_id:
                    logger.error("minimax_no_task_id", result=result)
                    raise ProviderError("No task_id in MiniMax response")
                
                logger.info("minimax_task_created", 
                           task_id=task_id, 
                           mode=mode.value,
                           elapsed=elapsed)
                
                return task_id
                
        except httpx.TimeoutException as e:
            elapsed = time.time() - start_time
            logger.error("minimax_timeout", error=str(e), elapsed=elapsed)
            raise ProviderTimeoutError(f"MiniMax request timeout: {e}")
        except httpx.HTTPStatusError as e:
            elapsed = time.time() - start_time
            logger.error("minimax_http_error", 
                        status=e.response.status_code,
                        error=str(e),
                        elapsed=elapsed)
            raise ProviderError(f"MiniMax HTTP error: {e}")
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error("minimax_unexpected_error", error=str(e), elapsed=elapsed)
            raise ProviderError(f"MiniMax unexpected error: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError),
        max_tries=3,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    async def query_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Query the status of a video generation task
        
        Args:
            task_id: Task ID returned from generation request
            
        Returns:
            Dict containing:
                - status: Task status (processing, success, failed)
                - file_id: File ID when status is success
                - error: Error message if status is failed
                - progress: Progress percentage (0-100)
        """
        if self.mock_mode:
            logger.info("minimax_mock_query_status", task_id=task_id)
            # Simulate processing delay
            if task_id.startswith("mock-minimax-"):
                # Return success after mock delay
                return {
                    "task_id": task_id,
                    "status": TaskStatus.SUCCESS.value,
                    "file_id": f"mock-file-{task_id[-8:]}",
                    "progress": 100,
                    "duration": 6,
                    "message": "Mock video generation completed"
                }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                logger.info("minimax_query_status", task_id=task_id)
                
                response = await client.get(
                    self.query_url,
                    params={"task_id": task_id},
                    headers=self._build_headers()
                )
                
                if response.status_code == 404:
                    logger.error("minimax_task_not_found", task_id=task_id)
                    raise ProviderError(f"Task not found: {task_id}")
                
                response.raise_for_status()
                result = response.json()
                
                logger.info("minimax_status_retrieved", 
                           task_id=task_id,
                           status=result.get("status"))
                
                return result
                
        except httpx.TimeoutException as e:
            logger.error("minimax_status_timeout", task_id=task_id, error=str(e))
            raise ProviderTimeoutError(f"MiniMax status query timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error("minimax_status_http_error",
                        task_id=task_id,
                        status=e.response.status_code,
                        error=str(e))
            raise ProviderError(f"MiniMax status query error: {e}")
        except Exception as e:
            logger.error("minimax_status_unexpected_error", task_id=task_id, error=str(e))
            raise ProviderError(f"MiniMax status query failed: {e}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError),
        max_tries=3,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    async def download_video(self, file_id: str) -> bytes:
        """
        Download generated video file
        
        Args:
            file_id: File ID returned from successful task query
            
        Returns:
            bytes: Video file content
        """
        if self.mock_mode:
            logger.info("minimax_mock_download", file_id=file_id)
            # Return mock video data (1KB of zeros as placeholder)
            return b'\x00' * 1024
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                logger.info("minimax_download_video", file_id=file_id)
                
                # First, get the download URL
                response = await client.get(
                    self.download_url,
                    params={"file_id": file_id},
                    headers=self._build_headers()
                )
                
                if response.status_code == 404:
                    logger.error("minimax_file_not_found", file_id=file_id)
                    raise ProviderError(f"File not found: {file_id}")
                
                response.raise_for_status()
                result = response.json()
                
                # Extract download URL from response
                download_url = result.get("file", {}).get("download_url")
                if not download_url:
                    raise ProviderError(f"No download URL in response for file {file_id}")
                
                # Download the actual video file
                logger.info("minimax_downloading_from_url", file_id=file_id, url=download_url)
                video_response = await client.get(download_url)
                video_response.raise_for_status()
                video_bytes = video_response.content
                
                logger.info("minimax_video_downloaded",
                           file_id=file_id,
                           size_bytes=len(video_bytes))
                
                return video_bytes
                
        except httpx.TimeoutException as e:
            logger.error("minimax_download_timeout", file_id=file_id, error=str(e))
            raise ProviderTimeoutError(f"MiniMax download timeout: {e}")
        except httpx.HTTPStatusError as e:
            logger.error("minimax_download_http_error",
                        file_id=file_id,
                        status=e.response.status_code,
                        error=str(e))
            raise ProviderError(f"MiniMax download error: {e}")
        except Exception as e:
            logger.error("minimax_download_unexpected_error", file_id=file_id, error=str(e))
            raise ProviderError(f"MiniMax download failed: {e}")
    
    async def poll_until_complete(
        self,
        task_id: str,
        max_wait_seconds: int = 300,
        poll_interval: int = 5
    ) -> Dict[str, Any]:
        """
        Poll task status until completion or timeout
        
        Args:
            task_id: Task ID to poll
            max_wait_seconds: Maximum time to wait (default 5 minutes)
            poll_interval: Time between polls in seconds (default 5s)
            
        Returns:
            Final task status dict with file_id on success
        """
        start_time = time.time()
        
        while (time.time() - start_time) < max_wait_seconds:
            status_result = await self.query_task_status(task_id)
            
            status = status_result.get("status")
            
            # MiniMax API returns capitalized status: "Success", "Fail"
            if status and status.lower() == TaskStatus.SUCCESS.value:
                logger.info("minimax_task_completed",
                           task_id=task_id,
                           elapsed=time.time() - start_time)
                return status_result
            
            if status and status.lower() == TaskStatus.FAILED.value:
                error_msg = status_result.get("error", "Unknown error")
                logger.error("minimax_task_failed",
                            task_id=task_id,
                            error=error_msg)
                raise ProviderError(f"Task failed: {error_msg}")
            
            # Still processing, wait and retry
            logger.info("minimax_task_processing",
                       task_id=task_id,
                       progress=status_result.get("progress", 0),
                       elapsed=time.time() - start_time)
            
            await asyncio.sleep(poll_interval)
        
        # Timeout reached
        logger.error("minimax_polling_timeout",
                    task_id=task_id,
                    elapsed=time.time() - start_time)
        raise ProviderTimeoutError(f"Task polling timeout after {max_wait_seconds}s")


# Import asyncio for sleep
import asyncio
