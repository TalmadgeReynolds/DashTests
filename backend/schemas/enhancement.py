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
    model: Literal[
        # Enhancement Models
        'prob-4',      # Proteus - Best for most videos
        'ahq-12',      # Artemis High Quality
        'amq-13',      # Artemis Medium Quality
        'alq-13',      # Artemis Low Quality
        'nyx-3',       # Nyx - Dedicated for denoise
        'nxf-1',       # Nyx Fast
        'rhea-1',      # Rhea - Advanced 4x upscaling
        'ghq-5',       # Gaia High Quality - Best for GenAI/CG/Animation
        'gcg-5',       # Gaia Computer Generated
        # Frame Interpolation Models
        'apo-8',       # Apollo - Best overall, up to 8x slowmo
        'apf-2',       # Apollo Fast
        'chr-2',       # Chronos - General framerate conversions
        'chf-3',       # Chronos Fast
        # Advanced Enhancement Models
        'ddv-3',       # Dione DV Footage
        'dtd-4',       # Dione Robust
        'dtds-2',      # Dione Robust Dehalo
        'dtv-4',       # Dione TV
        'dtvs-2',      # Dione Halo
        'alqs-2',      # Artemis Strong Halo
        'amqs-2',      # Artemis Dehalo
        'aaa-9',       # Artemis Aliased & Moire
        'thd-3',       # Theia Detail - High fidelity
        'thf-4',       # Theia Fidelity
        'iris-3',      # Iris - Specialized for faces
        'thm-2'        # Themis - Motion deblur
    ]
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