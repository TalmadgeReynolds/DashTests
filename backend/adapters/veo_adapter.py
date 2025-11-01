import time
import uuid
from typing import Dict, Optional, List, Literal, Union
import base64

import httpx
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, TransientProviderError, ProviderTimeoutError, ProviderRateLimitError

settings = get_settings()
logger = get_logger("veo_adapter")


class VeoAdapter:
    """Adapter for Veo 3 video generation API with full feature support"""
    
    def __init__(self, api_key: Optional[str] = None, project_id: Optional[str] = None, location: Optional[str] = None, mock_mode: bool = None):
        self.api_key = api_key or settings.VEO3_API_KEY
        self.project_id = project_id or settings.get("VERTEX_PROJECT_ID", "")
        self.location = location or settings.get("VERTEX_LOCATION", "us-central1")
        # Check both specific setting and global MOCK_PROVIDERS flag
        self.mock_mode = mock_mode if mock_mode is not None else (settings.VEO3_MOCK_MODE or settings.MOCK_PROVIDERS)
        
        # Use Vertex AI Veo endpoint
        self.base_url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models"
        
        if not self.api_key and not self.mock_mode:
            logger.warning("veo_no_api_key", message="No Veo API key provided and mock mode is disabled")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def generate_video(
        self,
        prompt: str,
        model_id: str = "veo-3.0-generate-001",
        # Video generation modes
        input_image: Optional[Union[str, bytes]] = None,  # For image-to-video
        input_video: Optional[Union[str, bytes]] = None,  # For video extension
        last_frame: Optional[Union[str, bytes]] = None,  # For frame interpolation
        mask: Optional[Union[str, bytes]] = None,  # For video editing
        mask_mode: Optional[str] = None,  # MASK_MODE_USER_PROVIDED, etc.
        # Reference images for consistency
        reference_images: Optional[List[Dict]] = None,  # List of {image, referenceType: asset/style}
        # Video parameters
        aspect_ratio: str = "16:9",
        duration_seconds: int = 8,
        resolution: str = "720p",
        # Audio and enhancement
        generate_audio: bool = False,
        enhance_prompt: bool = True,
        negative_prompt: Optional[str] = None,
        # Control parameters
        seed: Optional[int] = None,
        person_generation: str = "allow_adult",
        compression_quality: str = "optimized",
        resize_mode: str = "pad",  # For image-to-video: pad or crop
        sample_count: int = 1,
        storage_uri: Optional[str] = None
    ) -> str:
        """
        Generate video using Veo 3 with full feature support
        
        Supports:
        - Text-to-video: Just provide prompt
        - Image-to-video: Provide prompt + input_image
        - Video extension: Provide prompt + input_video
        - Frame interpolation: Provide prompt + input_video + last_frame
        - Video editing: Provide prompt + input_video + mask
        
        Returns: Operation name for long-running operation
        """
        if self.mock_mode:
            logger.info("veo_mock_generate_video", prompt=prompt[:30], model=model_id)
            time.sleep(1)
            mock_id = f"mock-veo-op-{hash(prompt) % 1000:03d}-{int(time.time())}"
            logger.info("veo_mock_operation_created", operation_id=mock_id)
            return mock_id
        
        start_time = time.time()
        
        # Build request payload
        instances = [{
            "prompt": prompt
        }]
        
        # Add input image for image-to-video
        if input_image:
            instances[0]["image"] = self._prepare_media(input_image, "image")
        
        # Add input video for video extension
        if input_video:
            instances[0]["video"] = self._prepare_media(input_video, "video")
        
        # Add last frame for interpolation
        if last_frame:
            instances[0]["lastFrame"] = self._prepare_media(last_frame, "image")
        
        # Add mask for video editing
        if mask:
            mask_obj = self._prepare_media(mask, "image")
            if mask_mode:
                mask_obj["maskMode"] = mask_mode
            instances[0]["mask"] = mask_obj
        
        # Add reference images
        if reference_images:
            instances[0]["referenceImages"] = []
            for ref in reference_images:
                ref_obj = {
                    "image": self._prepare_media(ref["image"], "image"),
                    "referenceType": ref.get("referenceType", "asset")
                }
                instances[0]["referenceImages"].append(ref_obj)
        
        # Build parameters
        parameters = {
            "aspectRatio": aspect_ratio,
            "durationSeconds": duration_seconds,
            "resolution": resolution,
            "generateAudio": generate_audio,
            "enhancePrompt": enhance_prompt,
            "personGeneration": person_generation,
            "compressionQuality": compression_quality,
            "sampleCount": sample_count
        }
        
        if input_image and resize_mode:
            parameters["resizeMode"] = resize_mode
        
        if negative_prompt:
            parameters["negativePrompt"] = negative_prompt
        
        if seed is not None:
            parameters["seed"] = seed
        
        if storage_uri:
            parameters["storageUri"] = storage_uri
        
        payload = {
            "instances": instances,
            "parameters": parameters
        }
        
        try:
            with httpx.Client(timeout=60.0) as client:
                url = f"{self.base_url}/{model_id}:predictLongRunning"
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "veo_generate_video_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms,
                    model=model_id
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Veo API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Veo API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Veo API error: {response.text}")
                
                result = response.json()
                return result["name"]  # Returns operation name
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Veo API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Veo API request error: {str(e)}")
    
    def _prepare_media(self, media: Union[str, bytes], media_type: str) -> Dict:
        """Prepare media (image/video) for API request"""
        if isinstance(media, str):
            # Assume it's a GCS URI if starts with gs://
            if media.startswith("gs://"):
                mime_type = "video/mp4" if media_type == "video" else "image/jpeg"
                return {
                    "gcsUri": media,
                    "mimeType": mime_type
                }
            # Assume it's a URL
            else:
                mime_type = "video/mp4" if media_type == "video" else "image/jpeg"
                return {
                    "gcsUri": media,
                    "mimeType": mime_type
                }
        else:
            # It's bytes, encode as base64
            encoded = base64.b64encode(media).decode('utf-8')
            mime_type = "video/mp4" if media_type == "video" else "image/jpeg"
            return {
                "bytesBase64Encoded": encoded,
                "mimeType": mime_type
            }
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def create_job(self, script: str, reference_image_url: Optional[str], fps: int, aspect: str, max_duration: int) -> str:
        """
        Legacy method for backward compatibility - creates a simple text-to-video job
        Deprecated: Use generate_video() for new implementations
        """
        # Map to new generate_video method
        operation_name = self.generate_video(
            prompt=script,
            input_image=reference_image_url,
            aspect_ratio=aspect,
            duration_seconds=min(max_duration, 8),  # Veo 3 max is 8 seconds
            generate_audio=False,
            enhance_prompt=True
        )
        return operation_name
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def poll_operation(self, operation_name: str, model_id: str = "veo-3.0-generate-001") -> Dict:
        """
        Poll the status of a long-running video generation operation
        
        Returns:
            Dict with:
            - done: bool - whether operation is complete
            - status: str - RUNNING, DONE, or ERROR
            - videos: List[Dict] - list of generated videos with gcsUri/bytesBase64Encoded
            - error: Optional[str] - error message if failed
        """
        if self.mock_mode:
            logger.info("veo_mock_poll_operation", operation_name=operation_name)
            time.sleep(1)
            
            # Extract timestamp to simulate time-based completion
            if "mock-veo-op-" not in operation_name:
                is_done = len(operation_name) % 2 == 0
            else:
                try:
                    parts = operation_name.split('-')
                    if len(parts) >= 4:
                        op_timestamp = int(parts[-1])
                        # Operations complete after 15 seconds in mock mode
                        is_done = (time.time() - op_timestamp) > 15
                    else:
                        is_done = len(operation_name) % 2 == 0
                except (ValueError, IndexError):
                    is_done = len(operation_name) % 2 == 0
            
            if is_done:
                video_url = f"gs://mock-veo-bucket/{operation_name}.mp4"
                logger.info("veo_mock_operation_completed", operation_name=operation_name)
                return {
                    "done": True,
                    "status": "DONE",
                    "videos": [{
                        "gcsUri": video_url,
                        "mimeType": "video/mp4"
                    }],
                    "raiMediaFilteredCount": 0
                }
            else:
                logger.info("veo_mock_operation_running", operation_name=operation_name)
                return {
                    "done": False,
                    "status": "RUNNING",
                    "videos": []
                }
        
        start_time = time.time()
        try:
            with httpx.Client(timeout=10.0) as client:
                url = f"{self.base_url}/{model_id}:fetchPredictOperation"
                response = client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={"operationName": operation_name}
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "veo_poll_operation_response",
                    operation_name=operation_name,
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Veo API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Veo API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Veo API error: {response.text}")
                
                result = response.json()
                
                # Check if operation is complete
                done = result.get("done", False)
                
                if done and "response" in result:
                    response_data = result["response"]
                    videos = response_data.get("videos", [])
                    
                    return {
                        "done": True,
                        "status": "DONE",
                        "videos": videos,
                        "raiMediaFilteredCount": response_data.get("raiMediaFilteredCount", 0),
                        "raiMediaFilteredReasons": response_data.get("raiMediaFilteredReasons", [])
                    }
                elif done and "error" in result:
                    return {
                        "done": True,
                        "status": "ERROR",
                        "error": result["error"].get("message", "Unknown error"),
                        "videos": []
                    }
                else:
                    return {
                        "done": False,
                        "status": "RUNNING",
                        "videos": []
                    }
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Veo API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Veo API request error: {str(e)}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def poll_result(self, provider_job_id: str) -> Dict:
        """
        Legacy method for backward compatibility
        Deprecated: Use poll_operation() for new implementations
        """
        result = self.poll_operation(provider_job_id)
        
        # Convert new format to old format
        if result["done"] and result["status"] == "DONE" and result["videos"]:
            video = result["videos"][0]
            video_url = video.get("gcsUri") or video.get("bytesBase64Encoded")
            return {
                "status": "DONE",
                "video_url": video_url
            }
        elif result["done"] and result["status"] == "ERROR":
            return {
                "status": "ERROR",
                "video_url": None,
                "error": result.get("error")
            }
        else:
            return {
                "status": "RUNNING",
                "video_url": None
            }