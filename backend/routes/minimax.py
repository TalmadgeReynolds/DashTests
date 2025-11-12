"""
MiniMax Hailuo 2.3 video generation routes

Provides endpoints for all video generation modes:
- Text-to-Video (T2V)
- Image-to-Video (I2V)
- First/Last Frame to Video (FL2V)
- Subject Reference to Video (S2V)
- Task status polling
- Video download
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Optional, Dict, Any
import logging

from ..services.minimax_service import MinimaxService
from ..schemas.minimax import (
    TextToVideoRequest,
    ImageToVideoRequest,
    FirstLastFrameToVideoRequest,
    SubjectReferenceToVideoRequest,
    TaskCreatedResponse,
    TaskStatusResponse,
    VideoDownloadResponse,
    MinimaxModelCapabilities,
    MinimaxModelEnum
)
from ..exceptions import ProviderError, ValidationError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/minimax", tags=["minimax", "video-generation"])


def get_minimax_service():
    """Dependency to get MiniMax service"""
    return MinimaxService()


@router.post("/generate/text-to-video", response_model=TaskCreatedResponse)
async def create_text_to_video(
    request: TextToVideoRequest,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Generate video from text prompt (T2V)
    
    **Supported Models:**
    - MiniMax-Hailuo-2.3: Best quality with advanced movement and realism
    - MiniMax-Hailuo-2.3-Fast: Faster generation
    - MiniMax-Hailuo-02: Higher resolution (1080p) and longer duration (up to 10s)
    
    **Parameters:**
    - prompt: Text description of the video (required)
    - model: Model to use (default: Hailuo-2.3)
    - aspect_ratio: Video aspect ratio (default: 16:9)
    - duration_seconds: Video duration 2-10s depending on model (default: 6s)
    - prompt_optimizer: Enable automatic prompt enhancement (default: true)
    - seed: Random seed for reproducibility (optional)
    - callback_url: Webhook URL for completion notification (optional)
    
    **Returns:**
    - task_id: Use this to poll for status and download video when complete
    """
    try:
        logger.info(f"Creating T2V job: {request.prompt[:50]}...")
        
        result = await service.create_text_to_video_job(request)
        
        return TaskCreatedResponse(
            task_id=result["task_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValidationError as e:
        logger.error(f"T2V validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ProviderError as e:
        logger.error(f"T2V provider error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"T2V unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/generate/image-to-video", response_model=TaskCreatedResponse)
async def create_image_to_video(
    request: ImageToVideoRequest,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Generate video from image and text prompt (I2V)
    
    **Best Model:** MiniMax-Hailuo-2.3-Fast (optimized for image-to-video)
    
    **Parameters:**
    - prompt: Text description of how the image should animate (required)
    - first_frame_image: Base64 encoded image or image URL (required)
    - model: Model to use (default: Hailuo-2.3-Fast)
    - aspect_ratio: Video aspect ratio (default: 16:9)
    - duration_seconds: Video duration (default: 6s)
    - prompt_optimizer: Enable automatic prompt enhancement (default: true)
    - seed: Random seed for reproducibility (optional)
    
    **Returns:**
    - task_id: Use this to poll for status and download video when complete
    """
    try:
        logger.info(f"Creating I2V job: {request.prompt[:50]}...")
        
        result = await service.create_image_to_video_job(request)
        
        return TaskCreatedResponse(
            task_id=result["task_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValidationError as e:
        logger.error(f"I2V validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ProviderError as e:
        logger.error(f"I2V provider error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"I2V unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/generate/first-last-frame", response_model=TaskCreatedResponse)
async def create_first_last_frame_video(
    request: FirstLastFrameToVideoRequest,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Generate video interpolating between first and last frames (FL2V)
    
    **Use Case:** Create smooth transitions between two keyframes
    
    **Parameters:**
    - prompt: Text description of the transition/motion (required)
    - first_frame_image: Base64 encoded starting frame (required)
    - last_frame_image: Base64 encoded ending frame (required)
    - model: Model to use (default: Hailuo-2.3)
    - aspect_ratio: Video aspect ratio (default: 16:9)
    - duration_seconds: Video duration (default: 6s)
    - prompt_optimizer: Enable automatic prompt enhancement (default: true)
    - seed: Random seed for reproducibility (optional)
    
    **Returns:**
    - task_id: Use this to poll for status and download video when complete
    """
    try:
        logger.info(f"Creating FL2V job: {request.prompt[:50]}...")
        
        result = await service.create_first_last_frame_job(request)
        
        return TaskCreatedResponse(
            task_id=result["task_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValidationError as e:
        logger.error(f"FL2V validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ProviderError as e:
        logger.error(f"FL2V provider error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"FL2V unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/generate/subject-reference", response_model=TaskCreatedResponse)
async def create_subject_reference_video(
    request: SubjectReferenceToVideoRequest,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Generate video with consistent subject/style from reference image (S2V)
    
    **Use Case:** Maintain character or style consistency across video generation
    
    **Parameters:**
    - prompt: Text description of the video (required)
    - reference_image: Base64 encoded reference image (required)
    - reference_type: "character" or "style" (default: character)
    - model: Model to use (default: Hailuo-2.3)
    - aspect_ratio: Video aspect ratio (default: 16:9)
    - duration_seconds: Video duration (default: 6s)
    - prompt_optimizer: Enable automatic prompt enhancement (default: true)
    - seed: Random seed for reproducibility (optional)
    
    **Returns:**
    - task_id: Use this to poll for status and download video when complete
    """
    try:
        logger.info(f"Creating S2V job: {request.prompt[:50]}, ref_type: {request.reference_type.value}")
        
        result = await service.create_subject_reference_job(request)
        
        return TaskCreatedResponse(
            task_id=result["task_id"],
            status=result["status"],
            message=result["message"]
        )
        
    except ValidationError as e:
        logger.error(f"S2V validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except ProviderError as e:
        logger.error(f"S2V provider error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"S2V unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/task/{task_id}/status", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Query the status of a video generation task
    
    **Parameters:**
    - task_id: Task ID returned from generation request
    
    **Returns:**
    - status: Current task status (queued, processing, success, failed)
    - progress: Progress percentage (0-100)
    - file_id: File ID when status is "success" - use this to download video
    - error: Error message if status is "failed"
    
    **Status Values:**
    - queued: Task is waiting to be processed
    - processing: Video is being generated
    - success: Video is ready for download (file_id provided)
    - failed: Generation failed (error message provided)
    """
    try:
        logger.info(f"Querying status for task: {task_id}")
        
        status = await service.get_job_status(task_id)
        
        return status
        
    except ProviderError as e:
        logger.error(f"Status query error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"Status query unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/task/{task_id}/download")
async def download_and_store_video(
    task_id: str,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Download generated video and store in S3
    
    **Prerequisites:**
    1. Task status must be "success"
    2. You must have the file_id from status query
    
    **Parameters:**
    - task_id: Task ID from generation request
    
    **Returns:**
    - video_url: Public URL to access the video
    - size_bytes: Video file size
    
    **Note:** This endpoint automatically retrieves the file_id from the task status.
    The video will be downloaded from MiniMax and uploaded to your S3 storage.
    """
    try:
        logger.info(f"Downloading video for task: {task_id}")
        
        # First check status to get file_id
        status = await service.get_job_status(task_id)
        
        if status.status != "success":
            raise HTTPException(
                status_code=400,
                detail=f"Task is not complete. Current status: {status.status}"
            )
        
        if not status.file_id:
            raise HTTPException(
                status_code=400,
                detail="No file_id available for this task"
            )
        
        # Download and store
        result = await service.download_and_store_video(task_id, status.file_id)
        
        return result
        
    except HTTPException:
        raise
    except ProviderError as e:
        logger.error(f"Download error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"Download unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/task/{task_id}/poll")
async def poll_task_until_complete(
    task_id: str,
    max_wait_seconds: int = 300,
    auto_download: bool = True,
    background_tasks: BackgroundTasks = None,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    Poll task status until completion and optionally download video
    
    **Use this endpoint for a "fire and forget" workflow.**
    
    **Parameters:**
    - task_id: Task ID from generation request
    - max_wait_seconds: Maximum time to wait (default: 300s = 5 minutes)
    - auto_download: Automatically download and store video when complete (default: true)
    
    **Returns:**
    - task_id: Task identifier
    - status: Final task status
    - file_id: File identifier
    - video_url: Public URL if auto_download is true
    - size_bytes: Video size if downloaded
    
    **Note:** This is a long-running endpoint that waits for the video to complete.
    Consider using webhooks (callback_url) for production use.
    """
    try:
        logger.info(f"Polling task until complete: {task_id}")
        
        result = await service.poll_job_until_complete(
            task_id=task_id,
            max_wait_seconds=max_wait_seconds,
            auto_download=auto_download
        )
        
        return result
        
    except ProviderError as e:
        logger.error(f"Poll error: {str(e)}")
        raise HTTPException(status_code=502, detail=f"Provider error: {str(e)}")
    except Exception as e:
        logger.error(f"Poll unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.get("/models/capabilities")
async def get_model_capabilities():
    """
    Get capabilities and features of all available MiniMax models
    
    **Returns:** List of model capabilities including:
    - Supported generation modes
    - Maximum duration
    - Key features
    - Recommended use cases
    """
    capabilities = [
        {
            "model": "MiniMax-Hailuo-2.3",
            "max_duration_seconds": 6,
            "supported_modes": ["t2v", "i2v", "fl2v", "s2v"],
            "features": [
                "Advanced body movement",
                "Detailed facial expressions",
                "Physical realism",
                "Best prompt adherence"
            ],
            "recommended_for": "High-quality video generation with best movement and realism",
            "resolution": "720p"
        },
        {
            "model": "MiniMax-Hailuo-2.3-Fast",
            "max_duration_seconds": 6,
            "supported_modes": ["i2v", "t2v"],
            "features": [
                "Fast processing",
                "Image animation",
                "Quick generation"
            ],
            "recommended_for": "Fast image-to-video conversion and quick generation",
            "resolution": "720p"
        },
        {
            "model": "MiniMax-Hailuo-02",
            "max_duration_seconds": 10,
            "supported_modes": ["t2v", "i2v"],
            "features": [
                "1080p resolution",
                "Longer duration (up to 10s)",
                "Strong prompt adherence"
            ],
            "recommended_for": "Higher resolution and longer videos",
            "resolution": "1080p"
        }
    ]
    
    return {
        "models": capabilities,
        "supported_aspect_ratios": ["16:9", "9:16", "1:1", "4:3", "3:4", "21:9", "9:21"],
        "generation_modes": {
            "t2v": "Text to Video - Generate videos from text prompts",
            "i2v": "Image to Video - Animate static images",
            "fl2v": "First/Last Frame to Video - Interpolate between keyframes",
            "s2v": "Subject Reference to Video - Maintain character/style consistency"
        }
    }


@router.get("/jobs")
async def list_jobs(
    limit: int = 50,
    status: Optional[str] = None,
    service: MinimaxService = Depends(get_minimax_service)
):
    """
    List recent video generation jobs
    
    **Parameters:**
    - limit: Maximum number of jobs to return (default: 50)
    - status: Filter by status (queued, processing, success, failed)
    
    **Returns:** List of job metadata including task_id, status, mode, etc.
    """
    try:
        from ..adapters.minimax_adapter import TaskStatus
        
        status_filter = TaskStatus(status) if status else None
        jobs = service.list_jobs(limit=limit, status_filter=status_filter)
        
        return {
            "jobs": [job.dict() for job in jobs],
            "count": len(jobs)
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    except Exception as e:
        logger.error(f"List jobs error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
