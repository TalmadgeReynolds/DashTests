from typing import Dict, Optional, List
from fastapi import APIRouter, HTTPException, Body, Depends, File, UploadFile
from sqlalchemy.orm import Session
from pydantic import BaseModel
import httpx
import boto3
import os
import uuid
import datetime
from botocore.exceptions import ClientError
from ..db import get_db
from ..utils.settings import get_settings
from ..exceptions import ProviderError, StorageError
from ..utils.logging import get_logger
from ..schemas.enhancement import JobBase, JobCreate, JobUpdate
from ..utils.video import get_video_metadata

def get_s3_client():
    """Create and return S3 client with credentials"""
    app_settings = get_settings()
    return boto3.client(
        's3',
        aws_access_key_id=app_settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=app_settings.AWS_SECRET_ACCESS_KEY,
        region_name=app_settings.AWS_REGION
    )

def format_bitrate(bitrate: Optional[int]) -> str:
    """Convert numeric bitrate in bps to string format (e.g., '10m')"""
    if not bitrate:
        return "10m"  # Default
    if bitrate >= 1_000_000_000:
        return f"{bitrate // 1_000_000_000}g"
    if bitrate >= 1_000_000:
        return f"{bitrate // 1_000_000}m"
    if bitrate >= 1_000:
        return f"{bitrate // 1_000}k"
    return str(bitrate)

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

@router.post("/enhancement/upload")
async def upload_file(file: UploadFile = File(...)) -> Dict[str, str]:
    """Upload a file and return its key"""
    try:
        # Create temp directory if it doesn't exist
        os.makedirs("/tmp", exist_ok=True)
        
        # Save file temporarily
        temp_path = f"/tmp/{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Get video metadata for validation
        metadata = await get_video_metadata(temp_path)
        
        # Generate video key
        video_key = f"video/{uuid.uuid4().hex}-{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.{file.filename.split('.')[-1]}"
        
        # Upload to storage
        s3_client = boto3.client(
            "s3",
            endpoint_url=f"{'https://' if settings.STORAGE_USE_SSL else 'http://'}{settings.STORAGE_ENDPOINT}",
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY
        )
        
        s3_client.upload_file(temp_path, settings.STORAGE_BUCKET, video_key)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {"videoKey": video_key}
        
    except Exception as e:
        logger.error(f"File upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enhancement/verify-file")
async def verify_file_exists(file_url: str = Body(...)):
    app_settings = get_settings()
    """Verify if a file exists in S3 and return its metadata"""
    try:
        # Parse the S3 URL to get bucket and key
        if not file_url.startswith(app_settings.STORAGE_PUBLIC_ENDPOINT):
            raise HTTPException(status_code=400, detail="Invalid file URL")
            
        file_path = file_url.replace(app_settings.STORAGE_PUBLIC_ENDPOINT, "").lstrip("/")
        
        s3 = boto3.client('s3')
        try:
            # Attempt to get object metadata
            response = s3.head_object(Bucket=settings.STORAGE_BUCKET, Key=file_path)
            return {
                "exists": True,
                "size": response.get('ContentLength', 0),
                "last_modified": response.get('LastModified', None),
                "content_type": response.get('ContentType', None)
            }
        except ClientError as e:
            error_code = int(e.response['Error']['Code'])
            if error_code == 404:
                return {"exists": False, "error": "File not found in S3"}
            else:
                logger.error(f"S3 error checking file {file_path}: {str(e)}")
                raise HTTPException(status_code=500, detail=f"S3 error: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error verifying file {file_url}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
    dynamicCompressionLevel: str  # Must be "Low", "Mid", or "High"
    videoBitrate: Optional[str] = "10m"  # Format: number + suffix (k, m, g)
    container: str
    filters: list[Filter]

class VideoProcessRequest(BaseModel):
    videoKey: str
    settings: TopazSettings

@router.get("/enhancement/upload-url")
async def get_upload_url() -> Dict:
    app_settings = get_settings()
    """Get a presigned URL for uploading a video to S3"""
    try:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=app_settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=app_settings.AWS_SECRET_ACCESS_KEY,
            region_name=app_settings.AWS_REGION
        )
        
        video_key = f"uploads/{uuid.uuid4().hex}.mov"  # Preserve MOV extension for ProRes
        
        # Generate presigned URL for upload
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': settings.S3_BUCKET_NAME,
                'Key': video_key,
                'ContentType': 'video/quicktime'  # For ProRes MOV files
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
async def estimate_processing_cost(video_key: str = Body(...), settings: TopazSettings = Body(...)) -> Dict:
    """Estimate the cost of processing a video with the given settings"""
    # Get app settings
    app_settings = get_settings()
    
    # Get video file from storage
    s3_client = boto3.client(
        "s3",
        endpoint_url=f"{'https://' if app_settings.STORAGE_USE_SSL else 'http://'}{app_settings.STORAGE_ENDPOINT}",
        aws_access_key_id=app_settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=app_settings.STORAGE_SECRET_KEY
    )
    
    # Download video for metadata analysis
    input_path = f"/tmp/{os.path.basename(video_key)}"
    try:
        s3_client.download_file(app_settings.STORAGE_BUCKET, video_key, input_path)
        metadata = await get_video_metadata(input_path)
        
        # Validate and adjust container format if needed
        detected_container = metadata['container']
        if settings.container != detected_container:
            logger.warning(f"Container format mismatch. Settings: {settings.container}, Detected: {detected_container}")
            settings.container = detected_container  # Auto-correct to detected format
        
        # Validate container format matches metadata
        if settings.container != metadata.get('container', 'mp4'):
            logger.warning(f"Container format mismatch. Settings: {settings.container}, Detected: {metadata.get('container', 'mp4')}")
            # Auto-correct container format
            settings.container = metadata.get('container', 'mp4')
        
        # Base cost calculation using actual duration
        minutes = metadata['duration'] / 60
        resolution_multiplier = (settings.outputResolution.width * settings.outputResolution.height) / (1920 * 1080)
        fps_multiplier = settings.outputFrameRate / 30
        
        # Base cost per minute of video
        base_cost = 0.50  # $0.50 per minute for 1080p30
        
        # Adjust for resolution and frame rate
        adjusted_cost = base_cost * resolution_multiplier * fps_multiplier * minutes
        
        # Add costs for additional filters
        for filter in settings.filters:
            if filter.stabilization:
                adjusted_cost *= 1.2  # 20% extra for stabilization
            if filter.model in ["chronos", "proteus"]:
                adjusted_cost *= 1.3  # 30% extra for advanced models
        
        # Get Topaz recommendations for the video
        headers = {
            "X-API-Key": app_settings.TOPAZ_API_KEY,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.topazlabs.com/video/analyze",
                headers=headers,
                json={
                    "source": {
                        "resolution": settings.inputResolution.dict(),
                        "frameRate": metadata["frameRate"],
                        "size": metadata["size"],
                        "duration": metadata["duration"],
                        "frameCount": metadata["frameCount"],
                        "container": metadata["container"]
                    }
                }
            )
            
            recommendations = response.json() if response.status_code == 200 else None
            
        return {
            "estimatedCost": round(adjusted_cost, 2),
            "metadata": metadata,
            "recommendations": recommendations
        }
        
    finally:
        # Clean up temp file
        if os.path.exists(input_path):
            os.remove(input_path)

@router.post("/enhancement/process")
async def process_video(request: JobCreate):
    """Process a video using Topaz Video AI - follows their multi-step workflow"""
    input_path = None
    
    # Get global settings and validate request settings
    app_settings = get_settings()
    topaz_settings = request.settings
    
    try:
        # Get the video file from S3
        s3_client = boto3.client(
            "s3",
            endpoint_url=f"{'https://' if app_settings.STORAGE_USE_SSL else 'http://'}{app_settings.STORAGE_ENDPOINT}",
            aws_access_key_id=app_settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=app_settings.STORAGE_SECRET_KEY,
            region_name="us-east-1"
        )
        
        # Create temp directory if it doesn't exist
        os.makedirs("/tmp", exist_ok=True)
        
        # Ensure the video key path is complete
        video_key = f"video/{request.video_key}" if not request.video_key.startswith("video/") else request.video_key
        
        # Download video to temp location
        input_path = f"/tmp/{os.path.basename(request.video_key)}"
        
        # Download file from S3
        s3_client.download_file(app_settings.STORAGE_BUCKET, video_key, input_path)
        
        # Get video metadata for source info
        metadata = await get_video_metadata(input_path)
        
        # Prepare headers for Topaz API
        headers = {
            "X-API-Key": app_settings.TOPAZ_API_KEY,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        # Step 1: Create video request (FREE - just gets cost estimate and requestId)
        topaz_payload = {
            "source": {
                "resolution": topaz_settings.inputResolution.dict(),
                "frameRate": metadata["frameRate"],
                "size": metadata["size"],
                "duration": metadata["duration"],
                "frameCount": str(metadata["frameCount"]),  # Topaz expects string
                "container": metadata["container"]
            },
            "output": {
                "resolution": topaz_settings.outputResolution.dict(),
                "audioCodec": topaz_settings.audioCodec,
                "audioTransfer": topaz_settings.audioTransfer,
                "frameRate": topaz_settings.outputFrameRate,
                "dynamicCompressionLevel": topaz_settings.dynamicCompressionLevel,
                "videoBitrate": format_bitrate(topaz_settings.videoBitrate),
                "container": topaz_settings.container
            },
            "filters": [{
                "model": filter.model,
                "slowmo": filter.slowmo or 1,
                "fps": topaz_settings.outputFrameRate
            } for filter in topaz_settings.filters]
        }
        
        logger.info("Step 1: Creating Topaz video request", payload=topaz_payload)
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Create request
            create_response = await client.post(
                "https://api.topazlabs.com/video/",
                headers=headers,
                json=topaz_payload
            )
            
            logger.info("Topaz create response", 
                       status_code=create_response.status_code,
                       response=create_response.text)
            
            if create_response.status_code != 200:
                raise ProviderError(f"Topaz API error: {create_response.text}")
                
            create_data = create_response.json()
            request_id = create_data["requestId"]
            
            # Log the raw response to see what Topaz actually returns
            logger.info("Raw Topaz create response", 
                       request_id=request_id,
                       keys=list(create_data.keys()),
                       full_data=create_data)
            
            # Extract estimates data from Topaz response
            estimates = create_data.get("estimates", {})
            cost_range = estimates.get("cost", [])
            time_range = estimates.get("time", [])
            
            # Calculate estimated cost (average of range) and duration
            estimated_cost = sum(cost_range) / len(cost_range) if cost_range else None
            estimated_duration = sum(time_range) / len(time_range) if time_range else None
            
            # Capture all Topaz response data with extracted estimates
            topaz_metadata = {
                "requestId": request_id,
                "estimatedCost": estimated_cost,
                "estimatedDuration": estimated_duration,
                "rawResponse": create_data  # Store complete response
            }
            
            logger.info("Extracted metadata", 
                       metadata=topaz_metadata)
            
            logger.info("Step 2: Accepting Topaz request", 
                       request_id=request_id,
                       metadata=topaz_metadata)
            
            # Step 2: Accept the request to get upload URLs
            accept_response = await client.patch(
                f"https://api.topazlabs.com/video/{request_id}/accept",
                headers={
                    "X-API-Key": app_settings.TOPAZ_API_KEY,
                    "accept": "application/json"
                }
            )
            
            logger.info("Accept response received",
                       status_code=accept_response.status_code,
                       response=accept_response.text)
            
            if accept_response.status_code not in [200, 201, 202]:
                raise ProviderError(f"Failed to accept Topaz request: {accept_response.text}")
                
            accept_data = accept_response.json()
            upload_urls = accept_data.get("urls", [])  # Topaz returns "urls" not "uploadUrls"
            
            if not upload_urls:
                raise ProviderError("No upload URLs received from Topaz")
            
            logger.info("Step 3: Uploading video to Topaz", 
                       num_parts=len(upload_urls))
            
            # Step 3: Upload video (for now, assume single part upload)
            upload_url = upload_urls[0]  # Get the first URL directly (it's a string, not a dict)
            
            with open(input_path, "rb") as f:
                video_content = f.read()
                upload_response = await client.put(
                    upload_url,
                    content=video_content,
                    headers={"Content-Type": f"video/{metadata['container']}"}
                )
                
            if upload_response.status_code not in [200, 204]:
                raise ProviderError(f"Failed to upload video to Topaz: {upload_response.status_code}")
            
            # Get eTag from response headers
            etag = upload_response.headers.get("ETag", "").strip('"')
            
            logger.info("Step 4: Completing upload", etag=etag)
            
            # Step 4: Complete the upload to start processing
            complete_response = await client.patch(
                f"https://api.topazlabs.com/video/{request_id}/complete-upload",
                headers=headers,
                json={
                    "uploadResults": [{
                        "partNum": 1,
                        "eTag": etag
                    }]
                }
            )
            
            logger.info("Complete upload response",
                       status_code=complete_response.status_code,
                       response=complete_response.text)
            
            if complete_response.status_code not in [200, 201, 202]:
                raise ProviderError(f"Failed to complete upload: {complete_response.text}")
            
            complete_data = complete_response.json()
            logger.info("Processing queued successfully", message=complete_data.get("message"))
            
            # Create and store job info with all Topaz metadata
            job_info = {
                "id": request_id,
                "status": "processing",
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow(),
                "video_key": request.video_key,
                "settings": topaz_settings.dict(),
                "progress": 0,
                "topaz_metadata": topaz_metadata
            }
            
            job_store[request_id] = job_info
            
            logger.info("Video processing job created successfully",
                       job_id=request_id,
                       video_key=request.video_key,
                       metadata=topaz_metadata)
            
            # Return response in format frontend expects with all Topaz data
            return {
                "jobId": request_id,
                "status": "processing",
                "video_key": request.video_key,
                "estimatedCost": topaz_metadata.get("estimatedCost"),
                "estimatedDuration": topaz_metadata.get("estimatedDuration"),
                "metadata": topaz_metadata
            }
            
    except Exception as e:
        logger.error("topaz_process_error",
                     error=str(e),
                     video_key=request.video_key)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp file
        if input_path and os.path.exists(input_path):
            try:
                os.remove(input_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temp file: {str(e)}")

@router.get("/enhancement/status/{job_id}")
async def get_processing_status(job_id: str) -> Dict:
    """Get the status of a Topaz processing job and download when complete"""
    app_settings = get_settings()
    
    try:
        headers = {
            "X-API-Key": app_settings.TOPAZ_API_KEY,
            "accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(
                f"https://api.topazlabs.com/video/{job_id}/status",
                headers=headers
            )
            
            logger.info("Topaz status response",
                       job_id=job_id,
                       status_code=response.status_code,
                       response=response.text)
            
            if response.status_code != 200:
                raise ProviderError(f"Topaz API error: {response.text}")
                
            job_data = response.json()
            status = job_data.get("status")
            
            # If processing is complete, download the video
            processed_video_url = None
            # Topaz returns status as "complete" (not "completed")
            # and the download URL is in job_data.download.url
            if status == "complete":
                download_data = job_data.get("download", {})
                output_url = download_data.get("url") if download_data else None
                
                if not output_url:
                    logger.warning("Job complete but no download URL found",
                                 job_id=job_id,
                                 download_data=download_data)
                if not output_url:
                    logger.warning("Job complete but no download URL found",
                                 job_id=job_id,
                                 download_data=download_data)
                else:
                    logger.info("Downloading processed video from Topaz",
                               job_id=job_id,
                               output_url=output_url)
                    
                    # Download the video
                    video_response = await client.get(output_url)
                    if video_response.status_code == 200:
                        # Upload to S3
                        video_content = video_response.content
                        processed_key = f"processed/{job_id}.mp4"
                        
                        s3_client = get_s3_client()
                        s3_client.put_object(
                            Bucket=app_settings.S3_BUCKET_NAME,
                            Key=processed_key,
                            Body=video_content,
                            ContentType="video/mp4"
                        )
                        
                        # Generate public URL
                        processed_video_url = f"{app_settings.S3_BUCKET_URL}/{processed_key}"
                        
                        logger.info("Processed video uploaded to S3",
                                   job_id=job_id,
                                   processed_key=processed_key,
                                   url=processed_video_url)
            
            # Update local job store with all data
            if job_id in job_store:
                job_store[job_id].update({
                    "status": status,
                    "progress": job_data.get("progress", 0),
                    "updated_at": datetime.datetime.utcnow(),
                    "processed_video_url": processed_video_url,
                    "topaz_status_data": job_data  # Store complete status response
                })
            
            # Return all Topaz data plus our processed URL
            return {
                **job_data,  # Include all Topaz response fields
                "processedVideoUrl": processed_video_url,
                "jobId": job_id
            }
            
    except Exception as e:
        logger.error("topaz_status_error", error=str(e), job_id=job_id)
        raise HTTPException(status_code=500, detail=str(e))