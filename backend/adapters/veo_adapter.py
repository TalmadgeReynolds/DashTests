import time
import uuid
from typing import Dict, Optional

import httpx
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, TransientProviderError, ProviderTimeoutError, ProviderRateLimitError

settings = get_settings()
logger = get_logger("veo_adapter")


class VeoAdapter:
    """Adapter for Veo 3 lip-sync API"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = None):
        self.api_key = api_key or settings.VEO3_API_KEY
        # Check both specific setting and global MOCK_PROVIDERS flag
        self.mock_mode = mock_mode if mock_mode is not None else (settings.VEO3_MOCK_MODE or settings.MOCK_PROVIDERS)
        self.base_url = "https://api.veo.co/v3"
        
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
    def create_job(self, script: str, reference_image_url: Optional[str], fps: int, aspect: str, max_duration: int) -> str:
        """Create a new lip-sync job with Veo 3"""
        if self.mock_mode:
            logger.info("veo_mock_create_job", script=script[:30], reference_image_url=reference_image_url)
            time.sleep(1)  # Simulate API call
            
            # Create deterministic job ID based on input for mock mode
            script_hash = hash(script) % 1000
            mock_id = f"mock-veo-{script_hash:03d}-{int(time.time())}"
            logger.info("veo_mock_job_id_created", mock_id=mock_id)
            return mock_id
        
        start_time = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/lipsync",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "script": script,
                        "reference_image_url": reference_image_url,
                        "fps": fps,
                        "aspect_ratio": aspect,
                        "max_duration_seconds": max_duration
                    }
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "veo_create_job_response",
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
                return result["job_id"]
                
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
        """Poll for job results"""
        if self.mock_mode:
            logger.info("veo_mock_poll", provider_job_id=provider_job_id)
            time.sleep(1)  # Simulate API call
            
            # Extract timestamp from mock job ID to simulate time-based completion
            if "mock-veo-" not in provider_job_id:
                # If it's not a mock ID format we recognize, use a fallback approach
                is_done = len(provider_job_id) % 2 == 0
            else:
                try:
                    # Extract timestamp from mock ID format: mock-veo-XXX-TIMESTAMP
                    parts = provider_job_id.split('-')
                    if len(parts) >= 4:
                        job_timestamp = int(parts[-1])
                        # Jobs complete after 10 seconds in mock mode
                        is_done = (time.time() - job_timestamp) > 10
                    else:
                        is_done = len(provider_job_id) % 2 == 0
                except (ValueError, IndexError):
                    # Fallback to simple heuristic if parsing fails
                    is_done = len(provider_job_id) % 2 == 0
            
            if is_done:
                video_url = f"https://mock-veo-output.com/{provider_job_id}.mp4"
                logger.info("veo_mock_job_completed", provider_job_id=provider_job_id, video_url=video_url)
                return {
                    "status": "DONE",
                    "video_url": video_url
                }
            else:
                logger.info("veo_mock_job_running", provider_job_id=provider_job_id)
                return {
                    "status": "RUNNING",
                    "video_url": None
                }
        
        start_time = time.time()
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/jobs/{provider_job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "veo_poll_response",
                    provider_job_id=provider_job_id,
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
                status_map = {
                    "processing": "RUNNING",
                    "completed": "DONE",
                    "failed": "ERROR"
                }
                
                return {
                    "status": status_map.get(result["status"], "RUNNING"),
                    "video_url": result.get("output_url")
                }
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("Veo API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"Veo API request error: {str(e)}")