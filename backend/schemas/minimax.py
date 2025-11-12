"""
Pydantic schemas for MiniMax Hailuo video generation API
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal, List
from enum import Enum


class MinimaxModelEnum(str, Enum):
    """Available MiniMax Hailuo models"""
    HAILUO_2_3 = "MiniMax-Hailuo-2.3"
    HAILUO_2_3_FAST = "MiniMax-Hailuo-2.3-Fast"
    HAILUO_02 = "MiniMax-Hailuo-02"


class AspectRatioEnum(str, Enum):
    """Supported aspect ratios"""
    RATIO_16_9 = "16:9"
    RATIO_9_16 = "9:16"
    RATIO_1_1 = "1:1"
    RATIO_4_3 = "4:3"
    RATIO_3_4 = "3:4"
    RATIO_21_9 = "21:9"
    RATIO_9_21 = "9:21"


class ReferenceTypeEnum(str, Enum):
    """Reference image types for S2V"""
    CHARACTER = "character"
    STYLE = "style"


class TaskStatusEnum(str, Enum):
    """Task status values"""
    QUEUED = "queued"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"


# ===== Request Schemas =====

class TextToVideoRequest(BaseModel):
    """Request schema for text-to-video generation"""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of the video")
    model: MinimaxModelEnum = Field(default=MinimaxModelEnum.HAILUO_2_3, description="Model to use")
    aspect_ratio: AspectRatioEnum = Field(default=AspectRatioEnum.RATIO_16_9, description="Video aspect ratio")
    duration_seconds: int = Field(default=6, ge=2, le=10, description="Video duration in seconds")
    prompt_optimizer: bool = Field(default=True, description="Enable automatic prompt enhancement")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed for reproducibility")
    callback_url: Optional[str] = Field(default=None, description="Webhook URL for completion notification")
    
    @validator('duration_seconds')
    def validate_duration(cls, v, values):
        """Validate duration based on model"""
        model = values.get('model')
        if model == MinimaxModelEnum.HAILUO_02 and v > 10:
            raise ValueError("Duration cannot exceed 10 seconds for Hailuo-02")
        elif model in [MinimaxModelEnum.HAILUO_2_3, MinimaxModelEnum.HAILUO_2_3_FAST] and v > 6:
            raise ValueError("Duration cannot exceed 6 seconds for Hailuo 2.3 models")
        return v


class ImageToVideoRequest(BaseModel):
    """Request schema for image-to-video generation"""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of animation")
    first_frame_image: str = Field(..., description="Base64 encoded first frame image or image URL")
    model: MinimaxModelEnum = Field(default=MinimaxModelEnum.HAILUO_2_3_FAST, description="Model to use (2.3-Fast recommended)")
    aspect_ratio: AspectRatioEnum = Field(default=AspectRatioEnum.RATIO_16_9, description="Video aspect ratio")
    duration_seconds: int = Field(default=6, ge=2, le=10, description="Video duration in seconds")
    prompt_optimizer: bool = Field(default=True, description="Enable automatic prompt enhancement")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed for reproducibility")
    callback_url: Optional[str] = Field(default=None, description="Webhook URL for completion notification")


class FirstLastFrameToVideoRequest(BaseModel):
    """Request schema for first/last frame to video generation"""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of transition")
    first_frame_image: str = Field(..., description="Base64 encoded first frame image")
    last_frame_image: str = Field(..., description="Base64 encoded last frame image")
    model: MinimaxModelEnum = Field(default=MinimaxModelEnum.HAILUO_2_3, description="Model to use")
    aspect_ratio: AspectRatioEnum = Field(default=AspectRatioEnum.RATIO_16_9, description="Video aspect ratio")
    duration_seconds: int = Field(default=6, ge=2, le=10, description="Video duration in seconds")
    prompt_optimizer: bool = Field(default=True, description="Enable automatic prompt enhancement")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed for reproducibility")
    callback_url: Optional[str] = Field(default=None, description="Webhook URL for completion notification")


class SubjectReferenceToVideoRequest(BaseModel):
    """Request schema for subject reference to video generation"""
    prompt: str = Field(..., min_length=1, max_length=2000, description="Text description of the video")
    reference_image: str = Field(..., description="Base64 encoded reference image")
    reference_type: ReferenceTypeEnum = Field(default=ReferenceTypeEnum.CHARACTER, description="Type of reference")
    model: MinimaxModelEnum = Field(default=MinimaxModelEnum.HAILUO_2_3, description="Model to use")
    aspect_ratio: AspectRatioEnum = Field(default=AspectRatioEnum.RATIO_16_9, description="Video aspect ratio")
    duration_seconds: int = Field(default=6, ge=2, le=10, description="Video duration in seconds")
    prompt_optimizer: bool = Field(default=True, description="Enable automatic prompt enhancement")
    seed: Optional[int] = Field(default=None, ge=0, description="Random seed for reproducibility")
    callback_url: Optional[str] = Field(default=None, description="Webhook URL for completion notification")


# ===== Response Schemas =====

class TaskCreatedResponse(BaseModel):
    """Response schema for task creation"""
    task_id: str = Field(..., description="Unique task identifier")
    status: TaskStatusEnum = Field(default=TaskStatusEnum.QUEUED, description="Initial task status")
    message: str = Field(default="Task created successfully", description="Status message")
    estimated_wait_seconds: Optional[int] = Field(default=None, description="Estimated processing time")


class TaskStatusResponse(BaseModel):
    """Response schema for task status query"""
    task_id: str = Field(..., description="Task identifier")
    status: TaskStatusEnum = Field(..., description="Current task status")
    progress: Optional[int] = Field(default=None, ge=0, le=100, description="Progress percentage")
    file_id: Optional[str] = Field(default=None, description="File ID when status is success")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    duration: Optional[int] = Field(default=None, description="Video duration in seconds")
    aspect_ratio: Optional[str] = Field(default=None, description="Video aspect ratio")
    created_at: Optional[str] = Field(default=None, description="Task creation timestamp")
    completed_at: Optional[str] = Field(default=None, description="Task completion timestamp")
    message: Optional[str] = Field(default=None, description="Status message")


class VideoDownloadResponse(BaseModel):
    """Response schema for video download"""
    file_id: str = Field(..., description="File identifier")
    download_url: str = Field(..., description="Presigned URL for video download")
    expires_at: Optional[str] = Field(default=None, description="URL expiration timestamp")
    size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    duration_seconds: Optional[int] = Field(default=None, description="Video duration")


class MinimaxErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    task_id: Optional[str] = Field(default=None, description="Task ID if applicable")
    details: Optional[dict] = Field(default=None, description="Additional error details")


# ===== Internal Schemas =====

class MinimaxJobMetadata(BaseModel):
    """Metadata for tracking MiniMax jobs in database"""
    task_id: str
    mode: Literal["t2v", "i2v", "fl2v", "s2v"]
    model: str
    prompt: str
    status: TaskStatusEnum
    file_id: Optional[str] = None
    video_url: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    duration_seconds: Optional[int] = None
    aspect_ratio: Optional[str] = None


class MinimaxModelCapabilities(BaseModel):
    """Model capabilities reference"""
    model: MinimaxModelEnum
    max_duration_seconds: int
    supported_modes: List[str]
    features: List[str]
    recommended_for: str
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "model": "MiniMax-Hailuo-2.3",
                    "max_duration_seconds": 6,
                    "supported_modes": ["t2v", "i2v", "fl2v", "s2v"],
                    "features": ["body_movement", "facial_expressions", "physical_realism", "prompt_adherence"],
                    "recommended_for": "High-quality video generation with best movement and realism"
                },
                {
                    "model": "MiniMax-Hailuo-2.3-Fast",
                    "max_duration_seconds": 6,
                    "supported_modes": ["i2v", "t2v"],
                    "features": ["fast_processing", "image_animation"],
                    "recommended_for": "Fast image-to-video conversion and quick generation"
                },
                {
                    "model": "MiniMax-Hailuo-02",
                    "max_duration_seconds": 10,
                    "supported_modes": ["t2v", "i2v"],
                    "features": ["1080p_resolution", "longer_duration", "strong_prompt_adherence"],
                    "recommended_for": "Higher resolution and longer videos"
                }
            ]
        }
