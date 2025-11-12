from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Any, Dict, Literal, Union
from datetime import datetime
from uuid import UUID
from enum import Enum


class PostFX(BaseModel):
    """Post-processing options as defined in OpenAPI schema"""
    interpolate: bool = Field(default=True, description="Whether to apply frame interpolation")
    upscale: bool = Field(default=False, description="Whether to upscale the video")


class ReferenceImage(BaseModel):
    """Reference image for video generation"""
    image_url: Optional[HttpUrl] = Field(None, description="URL or GCS URI of the reference image")
    image_base64: Optional[str] = Field(None, description="Base64-encoded image data")
    reference_type: Literal["asset", "style"] = Field(default="asset", description="Type of reference: asset for subjects/objects, style for visual style")


class VideoOpts(BaseModel):
    """Video options with full Veo 3 feature support"""
    # Basic settings (legacy - for backward compatibility with Heygen)
    fps: Optional[Literal[24, 30]] = Field(default=24, description="Frames per second (legacy, not used by Veo)")
    aspect: Literal["16:9", "9:16", "1:1"] = Field(default="16:9", description="Aspect ratio (1:1 for Heygen only)")
    max_duration: int = Field(default=8, description="Maximum duration in seconds (legacy)")
    
    # Veo 3 specific settings
    model_id: str = Field(default="veo-3.0-generate-001", description="Veo model to use")
    duration_seconds: Literal[4, 6, 8] = Field(default=8, description="Video duration in seconds")
    resolution: Literal["720p", "1080p"] = Field(default="720p", description="Output resolution")
    generate_audio: bool = Field(default=False, description="Generate audio for the video")
    
    # Video generation modes
    input_image_url: Optional[HttpUrl] = Field(None, description="Input image URL for image-to-video")
    input_video_url: Optional[HttpUrl] = Field(None, description="Input video URL for video extension")
    first_frame_url: Optional[HttpUrl] = Field(None, description="First frame URL for frame interpolation (VEO 3.1)")
    last_frame_url: Optional[HttpUrl] = Field(None, description="Last frame URL for frame interpolation")
    mask_url: Optional[HttpUrl] = Field(None, description="Mask URL for video editing")
    mask_mode: Optional[str] = Field(None, description="Mask mode: MASK_MODE_USER_PROVIDED, etc.")
    
    # Reference images for consistency
    reference_images: Optional[List[ReferenceImage]] = Field(None, description="Up to 3 asset or 1 style reference images")
    
    # Control parameters
    enhance_prompt: bool = Field(default=True, description="Use Gemini to enhance prompts")
    negative_prompt: Optional[str] = Field(None, description="What to avoid in the video")
    seed: Optional[int] = Field(None, ge=0, le=4294967295, description="Seed for reproducibility")
    person_generation: Literal["allow_adult", "allow_all", "dont_allow"] = Field(default="allow_adult", description="Person generation setting")
    compression_quality: Literal["optimized", "lossless"] = Field(default="optimized", description="Video compression quality")
    resize_mode: Literal["pad", "crop"] = Field(default="pad", description="Resize mode for image-to-video")
    sample_count: int = Field(default=1, ge=1, le=4, description="Number of videos to generate (1-4)")


class TTSRequest(BaseModel):
    """Text-to-speech request as defined in OpenAPI schema"""
    provider: Literal["elevenlabs"] = Field(default="elevenlabs", description="TTS provider")
    voice_id: Optional[str] = Field(None, description="Voice ID")
    text: str = Field(..., min_length=3, description="Text to synthesize")
    stability: float = Field(default=0.65, ge=0, le=1, description="Voice stability")
    similarity_boost: float = Field(default=0.75, ge=0, le=1, description="Voice similarity boost")
    style: float = Field(default=0.0, ge=0, le=1, description="Style exaggeration")
    speaker_boost: bool = Field(default=True, description="Speaker boost")
    optimize_streaming_latency: int = Field(default=0, ge=0, le=4, description="Optimize streaming latency (0-4)")
    model_id: str = Field(default="eleven_turbo_v2_5", description="TTS model ID")
    output_format: str = Field(default="mp3_44100_128", description="Audio output format")
    seed: Optional[int] = Field(None, description="Optional seed for reproducible results")
    pace: float = Field(default=1.0, ge=0.5, le=1.5, description="Speech pace")


class CreatePromptJobRequest(BaseModel):
    """Request body for creating a prompt-to-lipsync job as defined in OpenAPI schema"""
    script: str = Field(..., min_length=8, max_length=500, description="Script to be spoken")
    reference_image_url: Optional[HttpUrl] = Field(None, description="Optional reference image URL")
    post: Optional[PostFX] = None
    video: Optional[VideoOpts] = None
    priority: Literal["high", "low"] = Field(default="low", description="Job processing priority")


class HeygenAvatarRequest(BaseModel):
    """Configuration for using a Heygen Photo Avatar"""
    avatar_id: str = Field(..., description="ID of the avatar to use")
    look: Optional[str] = Field(None, description="Optional avatar look (e.g., professional, casual)")


class CreateAudioJobRequest(BaseModel):
    """Request body for creating an audio-driven job as defined in OpenAPI schema"""
    image_url: Optional[HttpUrl] = Field(None, description="URL of the image to animate (for talking photo)")
    avatar: Optional[HeygenAvatarRequest] = Field(None, description="Photo Avatar configuration (for avatar videos)")
    audio_url: Optional[HttpUrl] = Field(None, description="URL of the audio to use")
    tts: Optional[TTSRequest] = Field(None, description="Text-to-speech configuration")
    action_prompt: Optional[str] = Field(None, max_length=120, description="Action prompt for animation")
    post: Optional[PostFX] = None
    video: Optional[VideoOpts] = None
    priority: Literal["high", "low"] = Field(default="low", description="Job processing priority")
    
    @validator('tts', 'audio_url')
    def validate_audio_source(cls, v, values):
        """Validate that either audio_url or tts is provided"""
        if not values.get('audio_url') and not values.get('tts') and 'audio_url' in values and 'tts' in values:
            raise ValueError("Either audio_url or tts must be provided")
        return v
        
    @validator('image_url', 'avatar')
    def validate_image_source(cls, v, values):
        """Validate that either image_url or avatar is provided"""
        if not values.get('image_url') and not values.get('avatar') and 'image_url' in values and 'avatar' in values:
            raise ValueError("Either image_url or avatar must be provided")
        return v


class JobCreate(BaseModel):
    """Internal model for job creation"""
    id: UUID
    method: str
    status: str = "QUEUED"
    engine: str
    meta: Dict[str, Any]


class JobResponse(BaseModel):
    """Response model for job creation"""
    job_id: UUID


class JobMethod(str, Enum):
    """Job method types as defined in OpenAPI schema"""
    PROMPT_TO_LIPSYNC = "PROMPT_TO_LIPSYNC"
    AUDIO_DRIVEN = "AUDIO_DRIVEN"


class JobStatus(str, Enum):
    """Job status types as defined in OpenAPI schema"""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    POST = "POST"
    DONE = "DONE"
    ERROR = "ERROR"


class EngineType(str, Enum):
    """Engine types as defined in OpenAPI schema"""
    VEO3 = "veo3"
    HEYGEN = "heygen"


class JobDetail(BaseModel):
    """Response model for job details as defined in OpenAPI schema"""
    id: str
    method: JobMethod
    status: JobStatus
    engine: EngineType
    output_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    meta: Dict[str, Any]
    
    class Config:
        from_attributes = True