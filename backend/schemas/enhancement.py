from typing import List, Optional, Literal
from pydantic import BaseModel
import datetime
import uuid

class Resolution(BaseModel):
    width: int
    height: int

class ColorGrading(BaseModel):
    brightness: float = 0
    contrast: float = 0
    saturation: float = 0
    temperature: float = 0
    tint: float = 0

class TopazFilter(BaseModel):
    model: Literal['apo-8', 'chronos', 'proteus', 'dione', 'artemis', 'gaia']
    slowmo: Optional[float] = None
    denoiseLevel: Optional[float] = None
    sharpness: Optional[float] = None
    stabilization: Optional[bool] = None
    colorGrading: Optional[ColorGrading] = None

class TopazSettings(BaseModel):
    inputResolution: Resolution
    frameRate: float
    outputResolution: Resolution
    outputFrameRate: float
    audioCodec: Literal['AAC', 'Copy']
    audioTransfer: Literal['Copy', 'PassThrough']
    dynamicCompressionLevel: Literal['None', 'Low', 'Mid', 'High']
    container: Literal['mp4', 'mov']
    filters: List[TopazFilter]
    videoBitrate: Optional[int] = 20000  # Default to 20Mbps if not specified

class JobBase(BaseModel):
    id: str
    status: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    video_key: str
    input_url: Optional[str] = None
    output_url: Optional[str] = None
    progress: Optional[float] = None
    settings: Optional[dict] = None
    error: Optional[str] = None

class JobCreate(BaseModel):
    video_key: str
    settings: TopazSettings

class JobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[float] = None
    output_url: Optional[str] = None
    error: Optional[str] = None

class JobList(BaseModel):
    jobs: List[JobBase]