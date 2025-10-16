from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import Optional, Dict, Any


class PresignKind(str, Enum):
    """Types of files for presigned uploads"""
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VIDEO = "VIDEO"
    SCREENPLAY = "SCREENPLAY"


class PresignRequest(BaseModel):
    """Request body for presigned upload"""
    filename: str = Field(..., description="Original filename")
    mime: str = Field(..., description="MIME type")
    kind: PresignKind = Field(..., description="File kind")
    content_length: Optional[int] = Field(None, description="Content length in bytes", gt=0)
    
    @validator('content_length')
    def validate_content_length(cls, v):
        """Validate that content length is positive if provided"""
        if v is not None and v <= 0:
            raise ValueError("Content length must be a positive integer")
        return v


class PresignResponse(BaseModel):
    """Response for presigned upload"""
    uploadUrl: str = Field(..., description="URL to upload the file to")
    fileUrl: str = Field(..., description="URL to access the file after upload")


class ErrorResponse(BaseModel):
    """Standard error response format"""
    status: str = "error"
    code: str
    message: str
    detail: Optional[dict] = None
    request_id: Optional[str] = None