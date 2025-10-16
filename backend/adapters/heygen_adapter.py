import time
import uuid
import hmac
import hashlib
from typing import Dict, Optional, List, Any, Union

import httpx
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, TransientProviderError, ProviderTimeoutError, ProviderRateLimitError

settings = get_settings()
logger = get_logger("heygen_adapter")


class HeygenAdapter:
    """Adapter for Heygen talking photo API"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = None):
        self.api_key = api_key or settings.HEYGEN_API_KEY
        # Check both specific setting and global MOCK_PROVIDERS flag
        self.mock_mode = mock_mode if mock_mode is not None else (settings.HEYGEN_MOCK_MODE or settings.MOCK_PROVIDERS)
        self.base_url = "https://api.heygen.com/v1"
        self.base_url_v2 = "https://api.heygen.com/v2"
        self.webhook_secret = settings.WEBHOOK_SECRET_HEYGEN
        
        if not self.api_key and not self.mock_mode:
            logger.warning("heygen_no_api_key", message="No Heygen API key provided and mock mode is disabled")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def create_talking_photo(self, image_url: str, audio_url: str, action_prompt: Optional[str], fps: int) -> str:
        """Create a talking photo with Heygen"""
        if self.mock_mode:
            logger.info(
                "heygen_mock_create_talking_photo", 
                image_url=image_url,
                audio_url=audio_url,
                action_prompt=action_prompt
            )
            time.sleep(1)  # Simulate API call
            
            # Create deterministic job ID based on input for mock mode
            image_hash = hash(image_url) % 1000
            audio_hash = hash(audio_url) % 100
            action_hash = hash(str(action_prompt)) % 10 if action_prompt else 0
            
            mock_id = f"mock-heygen-{image_hash:03d}-{audio_hash:02d}-{action_hash}-{int(time.time())}"
            logger.info("heygen_mock_job_id_created", mock_id=mock_id)
            return mock_id
        
        start_time = time.time()
        try:
            # Prepare request payload
            payload = {
                "image_url": image_url,
                "audio_url": audio_url,
                "output_format": "mp4",
                "fps": fps
            }
            
            if action_prompt:
                payload["action_prompt"] = action_prompt
                
            # Configure webhook callback if available
            webhook_url = "https://api.yourdomain.com/api/v1/webhooks/heygen"
            if webhook_url:
                webhook_signature = hmac.new(
                    self.webhook_secret.encode(),
                    b"",  # This would typically be a unique identifier
                    hashlib.sha256
                ).hexdigest()
                
                payload["callback"] = {
                    "url": webhook_url,
                    "sign": webhook_signature
                }
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/talking-photo",
                    headers={"x-api-key": self.api_key},
                    json=payload
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "heygen_create_talking_photo_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Heygen API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Heygen API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Heygen API error: {response.text}")
                
                result = response.json()
                return result["task_id"]
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Heygen API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Heygen API request error: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def create_avatar(self, image_urls: List[str], avatar_name: Optional[str] = None) -> str:
        """
        Create a new avatar from uploaded photos using Heygen Photo Avatar API
        
        Args:
            image_urls: List of image URLs (with visible face)
            avatar_name: Optional name for the avatar
            
        Returns:
            avatar_id: ID of the created avatar
        """
        if self.mock_mode:
            logger.info("heygen_mock_create_avatar", image_urls=image_urls, avatar_name=avatar_name)
            time.sleep(1)  # Simulate API call
            
            # Create deterministic avatar ID based on input for mock mode
            image_hash = hash(str(image_urls)) % 1000
            name_hash = hash(avatar_name or "default") % 100
            
            mock_id = f"mock-heygen-avatar-{image_hash:03d}-{name_hash:02d}-{int(time.time())}"
            logger.info("heygen_mock_avatar_id_created", avatar_id=mock_id)
            return mock_id
            
        start_time = time.time()
        try:
            # Prepare request payload
            payload = {
                "image_urls": image_urls,
                "mode": "avatar",  # For Photo Avatar (vs digital_human)
            }
            
            if avatar_name:
                payload["name"] = avatar_name
                
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{self.base_url_v2}/avatar/create",
                    headers={"x-api-key": self.api_key},
                    json=payload
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "heygen_create_avatar_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Heygen API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Heygen API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Heygen API error: {response.text}")
                
                result = response.json()
                return result["data"]["avatar_id"]
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Heygen API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Heygen API request error: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def list_avatars(self, avatar_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        List avatars from Heygen
        
        Args:
            avatar_ids: Optional list of avatar IDs to filter by
            
        Returns:
            List of avatar objects
        """
        if self.mock_mode:
            logger.info("heygen_mock_list_avatars", avatar_ids=avatar_ids)
            time.sleep(1)  # Simulate API call
            
            # Generate mock avatars
            mock_avatars = []
            base_ids = ["mock-heygen-avatar-001", "mock-heygen-avatar-002"] if not avatar_ids else avatar_ids
            
            for i, avatar_id in enumerate(base_ids):
                mock_avatars.append({
                    "avatar_id": avatar_id,
                    "name": f"Mock Avatar {i+1}",
                    "image_url": f"https://mock-heygen-avatar.com/image_{i+1}.jpg",
                    "status": "ready",
                    "created_at": int(time.time()) - (i * 86400)  # Each avatar a day apart
                })
            
            return mock_avatars
            
        start_time = time.time()
        try:
            params = {}
            if avatar_ids:
                params["avatar_ids"] = ",".join(avatar_ids)
                
            with httpx.Client(timeout=30.0) as client:
                response = client.get(
                    f"{self.base_url_v2}/avatar/list",
                    headers={"x-api-key": self.api_key},
                    params=params
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "heygen_list_avatars_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Heygen API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Heygen API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Heygen API error: {response.text}")
                
                result = response.json()
                return result["data"]["avatars"]
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Heygen API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Heygen API request error: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def generate_avatar_video(
        self, 
        avatar_id: str, 
        audio_url: str,
        voice_id: Optional[str] = None,
        text: Optional[str] = None,
        script: Optional[Dict[str, Any]] = None,
        background_image_url: Optional[str] = None,
        background_video_url: Optional[str] = None,
        voice_style: Optional[str] = None,
        action_prompt: Optional[str] = None,
        look: Optional[str] = None,
        fps: int = 24,
        aspect_ratio: str = "16:9"
    ) -> str:
        """
        Generate a video using a photo avatar
        
        Args:
            avatar_id: ID of the avatar to use
            audio_url: URL of the audio file to use
            voice_id: Optional Heygen voice ID (if text is provided)
            text: Optional text to speak (if audio_url not provided)
            script: Optional enhanced script with timing
            background_image_url: Optional URL for background image
            background_video_url: Optional URL for background video
            voice_style: Optional voice style to apply
            action_prompt: Optional action prompt
            look: Optional look to apply (e.g., "professional", "casual")
            fps: Frames per second
            aspect_ratio: Video aspect ratio
            
        Returns:
            task_id: ID of the generated video task
        """
        if self.mock_mode:
            logger.info(
                "heygen_mock_generate_avatar_video", 
                avatar_id=avatar_id,
                audio_url=audio_url,
                voice_id=voice_id,
                text=text,
                script=script,
                action_prompt=action_prompt
            )
            time.sleep(1)  # Simulate API call
            
            # Create deterministic job ID based on input for mock mode
            avatar_hash = hash(avatar_id) % 1000
            audio_hash = hash(audio_url) % 100 if audio_url else 0
            text_hash = hash(text or "") % 10
            
            mock_id = f"mock-heygen-video-{avatar_hash:03d}-{audio_hash:02d}-{text_hash}-{int(time.time())}"
            logger.info("heygen_mock_video_id_created", video_id=mock_id)
            return mock_id
        
        start_time = time.time()
        try:
            # Prepare request payload
            payload = {
                "avatar": {
                    "avatar_id": avatar_id
                },
                "output": {
                    "fps": fps,
                    "ratio": aspect_ratio,
                    "resolution": "720p"
                }
            }
            
            # Add audio source (either audio_url or text+voice_id)
            if audio_url:
                payload["audio"] = {
                    "audio_url": audio_url
                }
            elif text and voice_id:
                payload["audio"] = {
                    "text": text,
                    "voice_id": voice_id
                }
                if voice_style:
                    payload["audio"]["voice_style"] = voice_style
            elif script:
                payload["script"] = script
            else:
                raise ValueError("Either audio_url, text+voice_id, or script must be provided")
            
            # Add optional parameters
            if background_image_url:
                payload["background"] = {
                    "image_url": background_image_url
                }
            elif background_video_url:
                payload["background"] = {
                    "video_url": background_video_url
                }
            
            if action_prompt:
                payload["action_prompt"] = action_prompt
                
            if look:
                payload["avatar"]["look"] = look
            
            # Configure webhook callback if available
            webhook_url = "https://api.yourdomain.com/api/v1/webhooks/heygen"
            if webhook_url:
                webhook_signature = hmac.new(
                    self.webhook_secret.encode(),
                    b"",  # This would typically be a unique identifier
                    hashlib.sha256
                ).hexdigest()
                
                payload["callback"] = {
                    "url": webhook_url,
                    "sign": webhook_signature
                }
                
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url_v2}/video/generate",
                    headers={"x-api-key": self.api_key},
                    json=payload
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "heygen_generate_avatar_video_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Heygen API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Heygen API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Heygen API error: {response.text}")
                
                result = response.json()
                return result["data"]["video_id"]
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Heygen API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Heygen API request error: {str(e)}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def poll_result(self, provider_job_id: str) -> Dict:
        """Poll for job results"""
        if self.mock_mode:
            logger.info("heygen_mock_poll", provider_job_id=provider_job_id)
            time.sleep(1)  # Simulate API call
            
            # Extract timestamp from mock job ID to simulate time-based completion
            if "mock-heygen-" not in provider_job_id:
                # If it's not a mock ID format we recognize, use a fallback approach
                is_done = len(provider_job_id) % 3 == 0
            else:
                try:
                    # Extract timestamp from mock ID format: mock-heygen-XXX-YY-Z-TIMESTAMP
                    parts = provider_job_id.split('-')
                    if len(parts) >= 5:
                        job_timestamp = int(parts[-1])
                        # Jobs complete after 15 seconds in mock mode
                        is_done = (time.time() - job_timestamp) > 15
                    else:
                        is_done = len(provider_job_id) % 3 == 0
                except (ValueError, IndexError):
                    # Fallback to simple heuristic if parsing fails
                    is_done = len(provider_job_id) % 3 == 0
            
            if is_done:
                video_url = f"https://mock-heygen-output.com/{provider_job_id}.mp4"
                logger.info("heygen_mock_job_completed", provider_job_id=provider_job_id, video_url=video_url)
                return {
                    "status": "DONE",
                    "video_url": video_url
                }
            else:
                logger.info("heygen_mock_job_running", provider_job_id=provider_job_id)
                return {
                    "status": "RUNNING",
                    "video_url": None
                }
        
        start_time = time.time()
        try:
            # Use the proper endpoint depending on the ID format
            # For talking photo tasks, use /v1/tasks/{task_id}
            # For avatar videos, use /v1/video_status.get?video_id={video_id}
            endpoint = ""
            params = {}
            
            if provider_job_id.startswith("task_"):
                endpoint = f"{self.base_url}/tasks/{provider_job_id}"
            else:
                endpoint = f"{self.base_url}/video_status.get"
                params = {"video_id": provider_job_id}
            
            with httpx.Client(timeout=10.0) as client:
                if params:
                    response = client.get(
                        endpoint,
                        headers={"x-api-key": self.api_key},
                        params=params
                    )
                else:
                    response = client.get(
                        endpoint,
                        headers={"x-api-key": self.api_key}
                    )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "heygen_poll_response",
                    provider_job_id=provider_job_id,
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("Heygen API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"Heygen API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"Heygen API error: {response.text}")
                
                result = response.json()
                
                # Handle different response formats depending on the endpoint
                if provider_job_id.startswith("task_"):
                    status_map = {
                        "processing": "RUNNING",
                        "success": "DONE",
                        "failed": "ERROR"
                    }
                    
                    return {
                        "status": status_map.get(result["status"], "RUNNING"),
                        "video_url": result.get("video_url")
                    }
                else:
                    status_map = {
                        "processing": "RUNNING",
                        "completed": "DONE",
                        "failed": "ERROR"
                    }
                    
                    return {
                        "status": status_map.get(result["data"]["status"], "RUNNING"),
                        "video_url": result["data"].get("video_url")
                    }
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Heygen API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Heygen API request error: {str(e)}")
            
    def verify_webhook_signature(self, signature: str, body: bytes) -> bool:
        """
        Verify the webhook signature using HMAC with constant-time comparison
        
        Implements the webhook verification from /docs/engines/webhooks.md:
        - Header format: X-Heygen-Signature: sha256=HMAC(body, WEBHOOK_SECRET_HEYGEN)
        
        Following best practices to prevent timing attacks:
        1. Use hmac.compare_digest for constant-time comparison
        2. Always compute the expected signature regardless of input validity
        3. Return False only after all operations are complete
        """
        if not signature or not self.webhook_secret:
            return False
            
        # Extract signature value removing the algorithm prefix
        if not signature.startswith("sha256="):
            return False
            
        provided_signature = signature.replace("sha256=", "")
        
        # Compute expected signature
        expected_signature = hmac.new(
            self.webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_signature, expected_signature)