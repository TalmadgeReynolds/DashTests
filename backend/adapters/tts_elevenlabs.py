import asyncio
import time
import uuid
from typing import Dict, Optional, List, Literal
from pathlib import Path

import httpx
import backoff

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, TransientProviderError, ProviderTimeoutError, ProviderRateLimitError

settings = get_settings()
logger = get_logger("tts_elevenlabs")

# Available models
MODELS = {
    "eleven_monolingual_v1": "English v1 - Original English model",
    "eleven_multilingual_v1": "Multilingual v1 - Original multilingual",
    "eleven_multilingual_v2": "Multilingual v2 - Latest multilingual (29+ languages)",
    "eleven_turbo_v2": "Turbo v2 - Fastest, lowest latency",
    "eleven_turbo_v2_5": "Turbo v2.5 - Enhanced turbo model"
}

# Output formats
OUTPUT_FORMATS = {
    "mp3_44100_128": "MP3 44.1kHz 128kbps",
    "mp3_44100_192": "MP3 44.1kHz 192kbps", 
    "pcm_16000": "PCM 16kHz",
    "pcm_22050": "PCM 22.05kHz",
    "pcm_24000": "PCM 24kHz",
    "pcm_44100": "PCM 44.1kHz",
    "ulaw_8000": "μ-law 8kHz"
}


class ElevenLabsAdapter:
    """
    Enhanced adapter for ElevenLabs Text-to-Speech API
    
    Features:
    - Voice library management
    - Voice cloning
    - Multiple models (including Turbo v2 and Multilingual v2)
    - Advanced voice settings
    - Audio storage integration
    - History tracking
    """
    
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
    
    async def list_voices(self, filter_name: Optional[str] = None) -> List[Dict]:
        """
        List all available voices.
        
        Args:
            filter_name: Optional filter for voice names
            
        Returns:
            List of voice dictionaries with id, name, category, labels, etc.
        """
        if self.mock_mode:
            logger.info("elevenlabs_mock_list_voices")
            mock_voices_list = [
                {
                    "voice_id": self.mock_voices["rachel"],
                    "name": "Rachel",
                    "category": "premade",
                    "labels": {"accent": "american", "age": "young", "gender": "female"}
                },
                {
                    "voice_id": self.mock_voices["drew"],
                    "name": "Drew",
                    "category": "premade",
                    "labels": {"accent": "american", "age": "middle_aged", "gender": "male"}
                },
                {
                    "voice_id": self.mock_voices["clyde"],
                    "name": "Clyde",
                    "category": "premade",
                    "labels": {"accent": "american", "age": "middle_aged", "gender": "male"}
                }
            ]
            
            if filter_name:
                mock_voices_list = [v for v in mock_voices_list if filter_name.lower() in v["name"].lower()]
            
            return mock_voices_list
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/voices",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("ElevenLabs API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"ElevenLabs API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"ElevenLabs API error: {response.text}")
                
                voices = response.json()["voices"]
                
                if filter_name:
                    voices = [v for v in voices if filter_name.lower() in v["name"].lower()]
                
                logger.info("elevenlabs_list_voices", count=len(voices))
                return voices
                
        except httpx.TimeoutException:
            raise ProviderTimeoutError("ElevenLabs API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")
    
    async def get_voice(self, voice_id: str) -> Dict:
        """
        Get detailed information about a specific voice.
        
        Args:
            voice_id: The voice ID to retrieve
            
        Returns:
            Voice details dictionary
        """
        if self.mock_mode:
            logger.info("elevenlabs_mock_get_voice", voice_id=voice_id)
            return {
                "voice_id": voice_id,
                "name": "Mock Voice",
                "category": "cloned",
                "settings": {"stability": 0.75, "similarity_boost": 0.75}
            }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/voices/{voice_id}",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code >= 400:
                    raise ProviderError(f"Voice not found or API error: {response.text}")
                
                return response.json()
                
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")
    
    async def clone_voice(self, name: str, files: List[bytes], description: Optional[str] = None,
                         labels: Optional[Dict] = None) -> str:
        """
        Clone a voice from audio samples.
        
        Args:
            name: Name for the cloned voice
            files: List of audio file contents (bytes)
            description: Optional description
            labels: Optional labels (e.g., {"accent": "american", "age": "young"})
            
        Returns:
            voice_id of the newly created voice
        """
        if self.mock_mode:
            logger.info("elevenlabs_mock_clone_voice", name=name, file_count=len(files))
            mock_voice_id = f"mock-cloned-{hash(name) % 10000}"
            return mock_voice_id
        
        try:
            # Prepare multipart form data
            files_data = []
            for idx, file_bytes in enumerate(files):
                files_data.append(("files", (f"sample_{idx}.mp3", file_bytes, "audio/mpeg")))
            
            data = {"name": name}
            if description:
                data["description"] = description
            if labels:
                data["labels"] = str(labels)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/voices/add",
                    headers={"xi-api-key": self.api_key},
                    data=data,
                    files=files_data
                )
                
                if response.status_code >= 400:
                    raise ProviderError(f"Voice cloning failed: {response.text}")
                
                result = response.json()
                voice_id = result["voice_id"]
                
                logger.info("elevenlabs_voice_cloned", voice_id=voice_id, name=name)
                return voice_id
                
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")
    
    async def delete_voice(self, voice_id: str) -> bool:
        """
        Delete a cloned voice.
        
        Args:
            voice_id: The voice ID to delete
            
        Returns:
            True if successful
        """
        if self.mock_mode:
            logger.info("elevenlabs_mock_delete_voice", voice_id=voice_id)
            return True
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self.base_url}/voices/{voice_id}",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code >= 400:
                    raise ProviderError(f"Voice deletion failed: {response.text}")
                
                logger.info("elevenlabs_voice_deleted", voice_id=voice_id)
                return True
                
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")
    
    async def get_subscription_info(self) -> Dict:
        """
        Get subscription information including character limits and usage.
        
        Returns:
            Dictionary with subscription details
        """
        if self.mock_mode:
            logger.info("elevenlabs_mock_subscription_info")
            return {
                "tier": "free",
                "character_count": 5000,
                "character_limit": 10000,
                "can_extend_character_limit": True
            }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/user/subscription",
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code >= 400:
                    raise ProviderError(f"Failed to get subscription info: {response.text}")
                
                return response.json()
                
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
    async def synthesize(
        self, 
        text: str, 
        voice_id: Optional[str] = None,
        model_id: str = "eleven_turbo_v2",
        stability: float = 0.65, 
        similarity_boost: float = 0.75, 
        style: float = 0.0,
        speaker_boost: bool = True,
        pace: float = 1.0,
        output_format: str = "mp3_44100_128",
        seed: Optional[int] = None,
        optimize_streaming_latency: int = 0
    ) -> bytes:
        """
        Synthesize speech from text and return the audio content.
        
        Args:
            text: Text to synthesize
            voice_id: Voice ID to use (defaults to Rachel)
            model_id: Model to use (default: eleven_turbo_v2)
            stability: Voice stability (0-1)
            similarity_boost: Voice similarity (0-1)
            style: Exaggeration level (0-1)
            speaker_boost: Enhance voice similarity
            pace: Speech speed multiplier
            output_format: Audio format (e.g., mp3_44100_128)
            seed: Seed for reproducible generation
            optimize_streaming_latency: Latency optimization level (0-4)
            
        Returns:
            Audio content as bytes
        """
        if not voice_id:
            voice_id = await self.ensure_voice(self.default_voice)
        
        if self.mock_mode:
            logger.info("elevenlabs_mock_synthesize", voice_id=voice_id, text_len=len(text), model=model_id)
            await asyncio.sleep(1.0)
            # Return mock audio bytes (1 second of silence as MP3)
            mock_audio = b'\xff\xfb\x90\x00' + b'\x00' * 1024
            return mock_audio
        
        # Validate parameters
        if model_id not in MODELS:
            raise ValueError(f"Invalid model_id: {model_id}. Must be one of {list(MODELS.keys())}")
        if output_format not in OUTPUT_FORMATS:
            raise ValueError(f"Invalid output_format: {output_format}. Must be one of {list(OUTPUT_FORMATS.keys())}")
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": stability,
                "similarity_boost": similarity_boost,
                "style": style,
                "use_speaker_boost": speaker_boost
            }
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        # Build query parameters
        params = {
            "output_format": output_format,
            "optimize_streaming_latency": optimize_streaming_latency
        }
        
        try:
            start = time.time()
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice_id}",
                    json=payload,
                    params=params,
                    headers={"xi-api-key": self.api_key}
                )
                
                if response.status_code == 429:
                    raise ProviderRateLimitError("ElevenLabs API rate limit exceeded")
                elif response.status_code >= 500:
                    raise TransientProviderError(f"ElevenLabs API server error: {response.status_code}")
                elif response.status_code >= 400:
                    raise ProviderError(f"ElevenLabs API error: {response.text}")
                
                audio_content = response.content
                duration = time.time() - start
                
                logger.info("elevenlabs_synthesize_success",
                           voice_id=voice_id, text_len=len(text), audio_size=len(audio_content),
                           duration_sec=round(duration, 2), model=model_id, format=output_format)
                
                return audio_content
        
        except httpx.TimeoutException:
            raise ProviderTimeoutError("ElevenLabs API request timed out")
        except httpx.RequestError as e:
            raise TransientProviderError(f"ElevenLabs API request error: {str(e)}")