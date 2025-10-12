from pydantic import BaseModel, Field, HttpUrl, validator
from typing import List, Optional, Any, Dict, Literal
from datetime import datetime
from uuid import UUID
from enum import Enum


class PostFX(BaseModel):
    """Post-processing options as defined in OpenAPI schema"""
    interpolate: bool = Field(default=True, description="Whether to apply frame interpolation")
    upscale: bool = Field(default=False, description="Whether to upscale the video")


class VideoOpts(BaseModel):
    """Video options as defined in OpenAPI schema"""
    fps: Literal[24, 30] = Field(default=24, description="Frames per second")
    aspect: Literal["16:9", "9:16", "1:1"] = Field(default="16:9", description="Aspect ratio")
    max_duration: int = Field(default=12, description="Maximum duration in seconds")


class TTSRequest(BaseModel):
    """Text-to-speech request as defined in OpenAPI schema"""
    provider: Literal["elevenlabs"] = Field(default="elevenlabs", description="TTS provider")
    voice_id: Optional[str] = Field(None, description="Voice ID")
    text: str = Field(..., min_length=3, description="Text to synthesize")
    stability: float = Field(default=0.65, ge=0, le=1, description="Voice stability")
    similarity_boost: float = Field(default=0.75, ge=0, le=1, description="Voice similarity boost")
    pace: float = Field(default=1.0, ge=0.5, le=1.5, description="Speech pace")


class CreatePromptJobRequest(BaseModel):
    """Request body for creating a prompt-to-lipsync job as defined in OpenAPI schema"""
    script: str = Field(..., min_length=8, max_length=500, description="Script to be spoken")
    reference_image_url: Optional[HttpUrl] = Field(None, description="Optional reference image URL")
    post: Optional[PostFX] = None
    video: Optional[VideoOpts] = None
    priority: Literal["high", "low"] = Field(default="low", description="Job processing priority")


class CreateAudioJobRequest(BaseModel):
    """Request body for creating an audio-driven job as defined in OpenAPI schema"""
    image_url: HttpUrl = Field(..., description="URL of the image to animate")
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