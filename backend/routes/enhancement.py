from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException, Body, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import boto3
import os
import uuid
import datetime
from ..db import get_db
from ..utils.settings import get_settings
from ..exceptions import ProviderError
from ..utils.logging import get_logger
from ..schemas.enhancement import JobBase, JobCreate, JobUpdate

settings = get_settings()
logger = get_logger("topaz_adapter")

router = APIRouter(tags=["enhancement"])

# In-memory job storage for demo (replace with database in production)
job_store = {}

@router.get("/enhancement/jobs", response_model=List[JobBase], name="list_jobs")
async def list_jobs(db: Session = Depends(get_db)):
    """List all enhancement jobs"""
    jobs = list(job_store.values())
    jobs.sort(key=lambda x: x['created_at'], reverse=True)
    return jobs

@router.get("/enhancement/jobs/{job_id}", response_model=JobBase, name="get_job")
async def get_job(job_id: str, db: Session = Depends(get_db)):
    """Get a specific job by ID"""
    if job_id not in job_store:
        raise HTTPException(status_code=404, detail="Job not found")
    return job_store[job_id]

class Resolution(BaseModel):
    width: int
    height: int

class ColorGrading(BaseModel):
    brightness: float
    contrast: float
    saturation: float
    temperature: float
    tint: float

class Filter(BaseModel):
    model: str
    slowmo: Optional[float] = None
    denoiseLevel: Optional[float] = None
    sharpness: Optional[float] = None
    stabilization: Optional[bool] = None
    colorGrading: Optional[ColorGrading] = None

class TopazSettings(BaseModel):
    inputResolution: Resolution
    frameRate: int
    outputResolution: Resolution
    outputFrameRate: int
    audioCodec: str
    audioTransfer: str
    dynamicCompressionLevel: str
    container: str
    filters: list[Filter]

class VideoProcessRequest(BaseModel):
    videoKey: str
    settings: TopazSettings

@router.get("/enhancement/upload-url")
async def get_upload_url() -> Dict:
    """Get a presigned URL for uploading a video to S3"""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        video_key = f"uploads/{uuid.uuid4().hex}.mp4"
        
        # Generate presigned URL for upload
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': video_key,
                'ContentType': 'video/mp4'
            },
            ExpiresIn=3600  # URL expires in 1 hour
        )
        
        return {
            "uploadUrl": presigned_url,
            "videoKey": video_key
        }
        
    except Exception as e:
        logger.error("upload_url_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhancement/estimate-cost")
async def estimate_processing_cost(settings: TopazSettings = Body(...)) -> float:
    """Estimate the cost of processing a video with the given settings"""
    # Base cost calculation
    resolution_multiplier = (settings.outputResolution.width * settings.outputResolution.height) / (1920 * 1080)
    fps_multiplier = settings.outputFrameRate / 30
    
    # Base cost per minute of video
    base_cost = 0.50  # $0.50 per minute for 1080p30
    
    # Adjust for resolution and frame rate
    adjusted_cost = base_cost * resolution_multiplier * fps_multiplier
    
    # Add costs for additional filters
    for filter in settings.filters:
        if filter.stabilization:
            adjusted_cost *= 1.2  # 20% extra for stabilization
        if filter.model in ["chronos", "proteus"]:
            adjusted_cost *= 1.3  # 30% extra for advanced models
            
    return adjusted_cost

@router.post("/enhancement/process")
async def process_video(request: VideoProcessRequest) -> Dict:
    """Process a video using Topaz Video AI"""
    try:
        # Get the video file from S3
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        
        # Download video to temp location
        input_path = f"/tmp/{request.videoKey}"
        s3_client.download_file(settings.S3_BUCKET_NAME, request.videoKey, input_path)
        
        # Prepare Topaz API request
        headers = {
            "X-API-Key": settings.TOPAZ_API_KEY,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        # Convert our settings to Topaz API format
        topaz_payload = {
            "source": {
                "resolution": request.settings.inputResolution.dict(),
                "container": request.settings.container,
                "frameRate": request.settings.frameRate
            },
            "output": {
                "resolution": request.settings.outputResolution.dict(),
                "audioCodec": request.settings.audioCodec,
                "audioTransfer": request.settings.audioTransfer,
                "frameRate": request.settings.outputFrameRate,
                "dynamicCompressionLevel": request.settings.dynamicCompressionLevel,
                "container": request.settings.container
            },
            "filters": [filter.dict(exclude_none=True) for filter in request.settings.filters]
        }
        
        # Submit job to Topaz
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.topazlabs.com/video/",
                headers=headers,
                json=topaz_payload
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Topaz API error: {response.text}")
                
            job_data = response.json()
            job_id = job_data["id"]
            
            # Upload video to Topaz
            upload_url = job_data["uploadUrl"]
            with open(input_path, "rb") as f:
                upload_response = await client.put(upload_url, content=f.read())
                
            if upload_response.status_code != 200:
                raise ProviderError("Failed to upload video to Topaz")
                
            # Start processing
            start_response = await client.post(
                f"https://api.topazlabs.com/video/{job_id}/start",
                headers=headers
            )
            
            if start_response.status_code != 200:
                raise ProviderError("Failed to start Topaz processing")
            
            # Create and store job info
            job_info = {
                "id": job_id,
                "status": "processing",
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow(),
                "video_key": request.videoKey,
                "settings": request.settings.dict(),
                "progress": 0
            }
            job_store[job_id] = job_info
            
            return job_info
            
    except Exception as e:
        logger.error("topaz_process_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if os.path.exists(input_path):
            os.remove(input_path)

@router.get("/status/{job_id}")
async def get_processing_status(job_id: str) -> Dict:
    """Get the status of a Topaz processing job"""
    try:
        headers = {
            "X-API-Key": settings.TOPAZ_API_KEY,
            "accept": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.topazlabs.com/video/{job_id}",
                headers=headers
            )
            
            if response.status_code != 200:
                raise ProviderError(f"Topaz API error: {response.text}")
                
            job_data = response.json()
            
            if job_data["status"] == "completed":
                # Get the processed video URL
                download_response = await client.get(
                    f"https://api.topazlabs.com/video/{job_id}/download",
                    headers=headers
                )
                
                if download_response.status_code != 200:
                    raise ProviderError("Failed to get processed video URL")
                    
                download_data = download_response.json()
                
                # Update job info
                if job_id in job_store:
                    job_store[job_id].update({
                        "status": "completed",
                        "updated_at": datetime.datetime.utcnow(),
                        "output_url": download_data["url"],
                        "progress": 100
                    })
                    return job_store[job_id]
                
                return {
                    "status": "completed",
                    "processedVideoUrl": download_data["url"]
                }
            
            return {
                "status": job_data["status"],
                "progress": job_data.get("progress", 0)
            }
            
    except Exception as e:
        logger.error("topaz_status_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))