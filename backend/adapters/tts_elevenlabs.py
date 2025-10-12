import time
import uuid
from typing import Dict, Optional

import httpx
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, TransientProviderError, ProviderTimeoutError, ProviderRateLimitError

settings = get_settings()
logger = get_logger("tts_elevenlabs")


class ElevenLabsAdapter:
    """Adapter for ElevenLabs Text-to-Speech API"""
    
    def __init__(self, api_key: Optional[str] = None, mock_mode: bool = None):
        self.api_key = api_key or settings.ELEVENLABS_API_KEY
        # Check both specific setting and global MOCK_PROVIDERS flag
        self.mock_mode = mock_mode if mock_mode is not None else (settings.ELEVENLABS_MOCK_MODE or settings.MOCK_PROVIDERS)
        self.base_url = "https://api.elevenlabs.io/v1"
        # Dictionary of mock voices for deterministic responses
        self.mock_voices = {
            "rachel": "mock-voice-rachel-11111",
            "drew": "mock-voice-drew-22222",
            "clyde": "mock-voice-clyde-33333",
            "default": "mock-voice-default-00000"
        }
        
        if not self.api_key and not self.mock_mode:
            logger.warning("elevenlabs_no_api_key", message="No ElevenLabs API key provided and mock mode is disabled")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def ensure_voice(self, voice_name: str) -> str:
        """Ensure a voice exists and return its ID"""
        if self.mock_mode:
            logger.info("elevenlabs_mock_ensure_voice", voice_name=voice_name)
            # Return deterministic voice ID based on name
            voice_key = voice_name.lower()
            voice_id = self.mock_voices.get(voice_key, self.mock_voices["default"])
            logger.info("elevenlabs_mock_voice_id", voice_name=voice_name, voice_id=voice_id)
            return voice_id
        
        # First, check if the voice already exists
        start_time = time.time()
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "elevenlabs_list_voices_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("ElevenLabs API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"ElevenLabs API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"ElevenLabs API error: {response.text}")
                
                voices = response.json()["voices"]
                for voice in voices:
                    if voice["name"].lower() == voice_name.lower():
                        return voice["voice_id"]
                
                # Voice not found, we'd need to create one
                # But this requires a voice sample, so we'll use a default voice instead
                return "21m00Tcm4TlvDq8ikWAM"  # Default voice
        
        except httpx.TimeoutException:
            raise ProviderTimeoutError("ElevenLabs API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")
    
    @backoff.on_exception(
        backoff.expo,
        (httpx.RequestError, ProviderTimeoutError, ProviderRateLimitError),
        max_tries=5,
        base=0.5,
        factor=2,
        jitter=backoff.full_jitter
    )
    def synthesize(self, text: str, voice_id: Optional[str] = None, 
                  stability: float = 0.65, similarity_boost: float = 0.75, pace: float = 1.0) -> str:
        """Synthesize speech from text and return the audio URL"""
        if self.mock_mode:
            logger.info("elevenlabs_mock_synthesize", text=text[:30], voice_id=voice_id)
            time.sleep(2)  # Simulate API call
            
            # Create deterministic audio ID based on input parameters
            if not voice_id:
                voice_id = self.mock_voices["default"]
                
            # Create a deterministic hash for consistent results in mock mode
            text_hash = hash(text) % 1000
            voice_hash = hash(voice_id) % 100
            params_hash = hash(f"{stability}-{similarity_boost}-{pace}") % 10
            
            mock_audio_id = f"mock-tts-{text_hash:03d}-{voice_hash:02d}-{params_hash}-{int(time.time())}"
            audio_url = f"https://mock-elevenlabs.com/{mock_audio_id}.mp3"
            
            logger.info("elevenlabs_mock_audio_url", audio_url=audio_url)
            return audio_url
        
        # Use default voice if none provided
        voice_id = voice_id or "21m00Tcm4TlvDq8ikWAM"
        
        start_time = time.time()
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    headers={"xi-api-key": self.api_key},
                    json={
                        "text": text,
                        "model_id": "eleven_monolingual_v1",
                        "voice_settings": {
                            "stability": stability,
                            "similarity_boost": similarity_boost,
                            "style": 0,
                            "use_speaker_boost": True,
                            "speed": pace
                        }
                    }
                )
                
                elapsed_ms = (time.time() - start_time) * 1000
                logger.info(
                    "elevenlabs_synthesize_response",
                    status_code=response.status_code,
                    latency_ms=elapsed_ms,
                    text_length=len(text)
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("ElevenLabs API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"ElevenLabs API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"ElevenLabs API error: {response.text}")
                
                # We need to save the audio file and get a URL
                # In a real implementation, this would upload to storage
                # For now, let's mock this part
                audio_content = response.content
                audio_id = uuid.uuid4()
                audio_url = f"https://storage.example.com/audio/{audio_id}.mp3"
                
                # TODO: Save audio to storage service
                
                return audio_url
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("ElevenLabs API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")