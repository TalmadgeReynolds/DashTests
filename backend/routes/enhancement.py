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

@router.get("/enhancement/debug-s3")
async def debug_s3_contents() -> Dict:
    """Debug endpoint to see what's in S3"""
    app_settings = get_settings()
    s3_client = get_s3_client()
    
    try:
        # List all objects in bucket
        response = s3_client.list_objects_v2(
            Bucket=app_settings.S3_BUCKET_NAME,
            MaxKeys=100
        )
        
        objects = []
        if 'Contents' in response:
            for obj in response['Contents']:
                objects.append({
                    "key": obj['Key'],
                    "size": obj['Size'],
                    "lastModified": obj['LastModified'].isoformat()
                })
        
        return {
            "bucket": app_settings.S3_BUCKET_NAME,
            "totalObjects": len(objects),
            "objects": objects
        }
    except Exception as e:
        logger.error("Failed to list S3 contents", error=str(e))
        return {
            "error": str(e),
            "bucket": app_settings.S3_BUCKET_NAME
        }

@router.get("/enhancement/past-videos")
async def list_past_videos() -> Dict:
    """List all processed videos from S3 with their original and processed versions"""
    app_settings = get_settings()
    s3_client = get_s3_client()
    
    try:
        # List all processed videos
        logger.info("Listing processed videos from S3", bucket=app_settings.S3_BUCKET_NAME)
        processed_response = s3_client.list_objects_v2(
            Bucket=app_settings.S3_BUCKET_NAME,
            Prefix="processed/"
        )
        
        logger.info("S3 response", 
                   has_contents='Contents' in processed_response,
                   count=len(processed_response.get('Contents', [])))
        
        videos = []
        
        # First, try to list videos from processed/ folder
        if 'Contents' in processed_response and len(processed_response.get('Contents', [])) > 0:
            logger.info("Processing S3 objects from processed/", count=len(processed_response['Contents']))
            for obj in processed_response['Contents']:
                # Extract job_id from filename (e.g., "processed/job123.mp4" -> "job123")
                filename = obj['Key'].split('/')[-1]
                logger.debug("Processing file", key=obj['Key'], filename=filename)
                
                if not filename.endswith('.mp4'):
                    logger.debug("Skipping non-mp4 file", filename=filename)
                    continue
                    
                job_id = filename.replace('.mp4', '')
                logger.debug("Found video", job_id=job_id)
                
                # Try to find the original video key from job_store
                original_key = None
                if job_id in job_store:
                    original_key = job_store[job_id].get('video_key')
                
                processed_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/{obj['Key']}"
                
                # Check if comparison exists
                comparison_key = f"comparisons/{job_id}_comparison.mp4"
                comparison_url = None
                try:
                    s3_client.head_object(Bucket=app_settings.S3_BUCKET_NAME, Key=comparison_key)
                    comparison_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/{comparison_key}"
                except:
                    pass
                
                # Get original video URL if we have the key
                original_url = None
                if original_key:
                    original_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/video/{original_key}"
                
                videos.append({
                    "jobId": job_id,
                    "originalUrl": original_url,
                    "processedUrl": processed_url,
                    "comparisonUrl": comparison_url,
                    "uploadedAt": obj['LastModified'].isoformat(),
                    "size": obj['Size']
                })
        
        # If no videos in processed/ folder, check the entire bucket
        elif 'Contents' not in processed_response or len(processed_response.get('Contents', [])) == 0:
            logger.info("No videos in processed/ folder, checking entire bucket")
            all_response = s3_client.list_objects_v2(
                Bucket=app_settings.S3_BUCKET_NAME
            )
            
            if 'Contents' in all_response:
                # Group videos by folder
                video_files = {}
                for obj in all_response['Contents']:
                    if obj['Key'].endswith('.mp4'):
                        folder = obj['Key'].split('/')[0] if '/' in obj['Key'] else 'root'
                        if folder not in video_files:
                            video_files[folder] = []
                        video_files[folder].append(obj)
                
                logger.info("Found video files", folders=list(video_files.keys()), 
                          counts={k: len(v) for k, v in video_files.items()})
                
                # Return videos from any folder as processed videos
                for folder, files in video_files.items():
                    for obj in files:
                        filename = obj['Key'].split('/')[-1]
                        job_id = filename.replace('.mp4', '')
                        
                        processed_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/{obj['Key']}"
                        
                        videos.append({
                            "jobId": job_id,
                            "originalUrl": None,
                            "processedUrl": processed_url,
                            "comparisonUrl": None,
                            "uploadedAt": obj['LastModified'].isoformat(),
                            "size": obj['Size'],
                            "folder": folder
                        })
        
        logger.info("Returning videos", count=len(videos))
        return {
            "videos": sorted(videos, key=lambda x: x['uploadedAt'], reverse=True)
        }
        
    except Exception as e:
        logger.error("Failed to list past videos", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

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

class EstimateCostRequest(BaseModel):
    video_key: str
    settings: TopazSettings

@router.post("/enhancement/estimate-cost")
async def estimate_processing_cost(request: EstimateCostRequest) -> Dict:
    """Get cost estimate from Topaz API by creating a request (doesn't charge yet)"""
    app_settings = get_settings()
    video_key = request.video_key
    settings = request.settings
    
    # Get S3 client with AWS credentials
    s3_client = get_s3_client()
    
    input_path = f"/tmp/{os.path.basename(video_key)}"
    # Ensure the video key includes the 'video/' prefix for S3
    s3_video_key = f"video/{video_key}" if not video_key.startswith("video/") else video_key
    try:
        s3_client.download_file(app_settings.S3_BUCKET_NAME, s3_video_key, input_path)
        metadata = await get_video_metadata(input_path)
        
        # Validate container format
        detected_container = metadata['container']
        if settings.container != detected_container:
            logger.warning(f"Container format mismatch. Settings: {settings.container}, Detected: {detected_container}")
            settings.container = detected_container
        
        # Call Topaz API to get REAL cost estimate
        headers = {
            "X-API-Key": app_settings.TOPAZ_API_KEY,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        topaz_payload = {
            "source": {
                "resolution": settings.inputResolution.dict(),
                "frameRate": metadata["frameRate"],
                "size": metadata["size"],
                "duration": metadata["duration"],
                "frameCount": str(metadata["frameCount"]),
                "container": metadata["container"]
            },
            "output": {
                "resolution": settings.outputResolution.dict(),
                "audioCodec": settings.audioCodec,
                "audioTransfer": settings.audioTransfer,
                "frameRate": settings.outputFrameRate,
                "dynamicCompressionLevel": settings.dynamicCompressionLevel,
                "videoBitrate": settings.videoBitrate or "10m",
                "container": settings.container
            },
            "filters": [{
                "model": filter.model,
                "slowmo": filter.slowmo or 1,
                "fps": settings.outputFrameRate
            } for filter in settings.filters]
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.topazlabs.com/video/",
                headers=headers,
                json=topaz_payload
            )
            
            logger.info("Topaz estimate response",
                       status_code=response.status_code,
                       response=response.text)
            
            if response.status_code != 200:
                raise ProviderError(f"Topaz API error: {response.text}")
            
            create_data = response.json()
            
            # Extract REAL cost estimate from Topaz
            estimates = create_data.get("estimates", {})
            cost_range = estimates.get("cost", [])
            time_range = estimates.get("time", [])
            
            # Calculate average cost and time from Topaz's range
            estimated_cost = sum(cost_range) / len(cost_range) if cost_range else 0
            estimated_duration = sum(time_range) / len(time_range) if time_range else 0
            
            logger.info("Topaz cost estimate",
                       cost=estimated_cost,
                       duration=estimated_duration,
                       cost_range=cost_range,
                       time_range=time_range,
                       request_id=create_data.get("requestId"))
            
            return {
                "requestId": create_data.get("requestId"),
                "estimatedCost": round(estimated_cost, 2),
                "estimatedDuration": round(estimated_duration, 2),
                "metadata": metadata,
                "costRange": cost_range,
                "timeRange": time_range,
                "recommendations": None  # Topaz doesn't provide recommendations
            }
        
    finally:
        # Clean up temp file
        if os.path.exists(input_path):
            os.remove(input_path)

class ConfirmProcessRequest(BaseModel):
    request_id: str
    video_key: str

@router.post("/enhancement/confirm-and-process")
async def confirm_and_process(request: ConfirmProcessRequest):
    """Accept a Topaz request and start processing (charges the account)"""
    app_settings = get_settings()
    input_path = None
    request_id = request.request_id
    video_key = request.video_key
    
    try:
        logger.info("Confirming Topaz request",
                   request_id=request_id,
                   video_key=video_key)
        
        # Get S3 client with AWS credentials
        s3_client = get_s3_client()
        
        # Ensure the video key path is complete
        full_video_key = f"video/{video_key}" if not video_key.startswith("video/") else video_key
        input_path = f"/tmp/{os.path.basename(video_key)}"
        
        # Download file from S3
        s3_client.download_file(app_settings.S3_BUCKET_NAME, full_video_key, input_path)
        
        # Get video metadata
        metadata = await get_video_metadata(input_path)
        
        # Prepare headers for Topaz API
        headers = {
            "X-API-Key": app_settings.TOPAZ_API_KEY,
            "accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Step 1: Accept the pre-created request (THIS CHARGES THE ACCOUNT)
            logger.info("Step 1: Accepting Topaz request (will charge account)", 
                       request_id=request_id)
            
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
            
            logger.info("Step 2: Uploading video to Topaz", 
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
            
            logger.info("Step 3: Completing upload", etag=etag)
            
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
            
            # Create and store job info
            job_info = {
                "id": request_id,
                "status": "processing",
                "created_at": datetime.datetime.utcnow(),
                "updated_at": datetime.datetime.utcnow(),
                "video_key": video_key,
                "progress": 0
            }
            
            job_store[request_id] = job_info
            
            logger.info("Video processing job started successfully",
                       job_id=request_id,
                       video_key=video_key)
            
            # Return response
            return {
                "jobId": request_id,
                "status": "processing",
                "video_key": video_key
            }
            
    except Exception as e:
        logger.error("topaz_confirm_error",
                     error=str(e),
                     video_key=video_key)
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
            
            # Log the complete response structure for debugging
            logger.info("Parsed Topaz status data",
                       job_id=job_id,
                       status=status,
                       has_download=("download" in job_data),
                       download_keys=list(job_data.get("download", {}).keys()) if isinstance(job_data.get("download"), dict) else "not_a_dict",
                       all_keys=list(job_data.keys()))
            
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
                        
                        # Generate public URL using bucket name and region
                        processed_video_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/{processed_key}"
                        
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

class CreateComparisonRequest(BaseModel):
    job_id: str

@router.post("/enhancement/create-comparison")
async def create_comparison_video(request: CreateComparisonRequest) -> Dict:
    """Create a side-by-side comparison video of original vs processed with labels"""
    app_settings = get_settings()
    job_id = request.job_id
    s3_client = get_s3_client()
    
    # Try to get job from store, or look up from S3
    if job_id in job_store:
        job = job_store[job_id]
        original_key = job.get("video_key")
    else:
        # Job not in store - this is a past video from S3
        logger.info("Job not in store, looking up from S3", job_id=job_id)
        original_key = None
        
        # Try to find the original video in S3
        try:
            # List all videos in the video/ folder to find a match
            video_response = s3_client.list_objects_v2(
                Bucket=app_settings.S3_BUCKET_NAME,
                Prefix="video/"
            )
            
            # For now, we'll use the first video we find (or None if no match)
            # In production, you'd want to store this mapping in a database
            if 'Contents' in video_response and len(video_response['Contents']) > 0:
                original_key = video_response['Contents'][0]['Key']
                logger.info("Found original video", original_key=original_key)
        except Exception as e:
            logger.warning("Could not find original video", error=str(e))
    
    # Check if processed video exists
    processed_key = f"processed/{job_id}.mp4"
    try:
        s3_client.head_object(Bucket=app_settings.S3_BUCKET_NAME, Key=processed_key)
    except:
        raise HTTPException(status_code=404, detail="Processed video not found in S3")
    
    comparison_key = f"comparisons/{job_id}_comparison.mp4"
    
    original_path = f"/tmp/original_{job_id}.mp4"
    processed_path = f"/tmp/processed_{job_id}.mp4"
    comparison_path = f"/tmp/comparison_{job_id}.mp4"
    
    try:
        logger.info("Downloading videos for comparison", job_id=job_id, has_original=bool(original_key))
        
        # Download processed video (required)
        s3_client.download_file(app_settings.S3_BUCKET_NAME, processed_key, processed_path)
        
        # Download original video if available
        if original_key:
            s3_client.download_file(app_settings.S3_BUCKET_NAME, original_key, original_path)
        else:
            # If no original, use processed video for both sides (just as a fallback)
            logger.warning("No original video found, using processed video for both sides")
            original_path = processed_path
        
        # Create side-by-side comparison with labels using FFmpeg
        logger.info("Creating side-by-side comparison with labels", job_id=job_id)
        
        import subprocess
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', original_path,
            '-i', processed_path,
            '-filter_complex',
            # Scale each video to half width
            '[0:v]scale=iw/2:ih[left];'
            '[1:v]scale=iw/2:ih[right];'
            # Add "ORIGINAL" label to left video
            '[left]drawtext=text=\'ORIGINAL\':fontcolor=white:fontsize=40:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=30[left_labeled];'
            # Add "ENHANCED" label to right video
            '[right]drawtext=text=\'ENHANCED\':fontcolor=white:fontsize=40:box=1:boxcolor=black@0.5:boxborderw=10:x=(w-text_w)/2:y=30[right_labeled];'
            # Combine side-by-side
            '[left_labeled][right_labeled]hstack=inputs=2',
            '-c:v', 'libx264',
            '-crf', '23',
            '-preset', 'medium',
            '-c:a', 'copy',
            '-y',
            comparison_path
        ]
        
        result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            logger.error("FFmpeg comparison failed", 
                        error=result.stderr,
                        job_id=job_id)
            raise HTTPException(status_code=500, detail=f"FFmpeg error: {result.stderr}")
        
        # Upload comparison video to S3
        logger.info("Uploading comparison video", job_id=job_id)
        s3_client.upload_file(
            comparison_path,
            app_settings.S3_BUCKET_NAME,
            comparison_key,
            ExtraArgs={'ContentType': 'video/mp4'}
        )
        
        # Generate public URL
        comparison_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/{comparison_key}"
        
        # Update job store if job exists
        if job_id in job_store:
            job_store[job_id]["comparison_video_url"] = comparison_url
        
        logger.info("Comparison video created successfully",
                   job_id=job_id,
                   url=comparison_url)
        
        return {
            "comparisonUrl": comparison_url,
            "jobId": job_id
        }
        
    except Exception as e:
        logger.error("comparison_creation_error", error=str(e), job_id=job_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up temp files
        for path in [original_path, processed_path, comparison_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception as e:
                    logger.warning(f"Failed to clean up {path}: {str(e)}")