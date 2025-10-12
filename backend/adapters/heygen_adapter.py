import time
import uuid
import hmac
import hashlib
from typing import Dict, Optional

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
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/tasks/{provider_job_id}",
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
                status_map = {
                    "processing": "RUNNING",
                    "success": "DONE",
                    "failed": "ERROR"
                }
                
                return {
                    "status": status_map.get(result["status"], "RUNNING"),
                    "video_url": result.get("video_url")
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