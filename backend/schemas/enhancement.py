from typing import List, Optional
from pydantic import BaseModel
import datetime
import uuid

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
    settings: dict

class JobUpdate(BaseModel):
    status: Optional[str] = None
    progress: Optional[float] = None
    output_url: Optional[str] = None
    error: Optional[str] = None

class JobList(BaseModel):
    jobs: List[JobBase]