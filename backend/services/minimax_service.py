"""
MiniMax Service Layer

Business logic for MiniMax Hailuo video generation including job tracking,
status management, and integration with storage.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, Any, List
from io import BytesIO

from ..adapters.minimax_adapter import MinimaxAdapter, MinimaxModel, GenerationMode, TaskStatus
from ..services.storage import StorageService
from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import ProviderError, ValidationError
from ..schemas.minimax import (
    TextToVideoRequest,
    ImageToVideoRequest,
    FirstLastFrameToVideoRequest,
    SubjectReferenceToVideoRequest,
    TaskStatusResponse,
    MinimaxJobMetadata
)

settings = get_settings()
logger = get_logger("minimax_service")


class MinimaxService:
    """Service for managing MiniMax video generation jobs"""
    
    def __init__(self):
        self.adapter = MinimaxAdapter()
        self.storage = StorageService()
        # In-memory job tracking (in production, use database)
        self._jobs: Dict[str, MinimaxJobMetadata] = {}
    
    async def create_text_to_video_job(
        self,
        request: TextToVideoRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a text-to-video generation job
        
        Args:
            request: T2V request parameters
            user_id: Optional user identifier
            
        Returns:
            Job information with task_id
        """
        logger.info("minimax_service_create_t2v",
                   prompt=request.prompt[:50],
                   model=request.model.value)
        
        try:
            # Create video generation task
            task_id = await self.adapter.text_to_video(
                prompt=request.prompt,
                model=MinimaxModel(request.model.value),
                aspect_ratio=request.aspect_ratio.value,
                duration_seconds=request.duration_seconds,
                prompt_optimizer=request.prompt_optimizer,
                seed=request.seed,
                callback_url=request.callback_url
            )
            
            # Store job metadata
            job_metadata = MinimaxJobMetadata(
                task_id=task_id,
                mode="t2v",
                model=request.model.value,
                prompt=request.prompt,
                status=TaskStatus.QUEUED,
                created_at=datetime.utcnow().isoformat(),
                duration_seconds=request.duration_seconds,
                aspect_ratio=request.aspect_ratio.value
            )
            
            self._jobs[task_id] = job_metadata
            
            logger.info("minimax_service_job_created",
                       task_id=task_id,
                       mode="t2v")
            
            return {
                "task_id": task_id,
                "status": "queued",
                "mode": "t2v",
                "message": "Text-to-video generation task created successfully"
            }
            
        except Exception as e:
            logger.error("minimax_service_t2v_error", error=str(e))
            raise ProviderError(f"Failed to create T2V job: {str(e)}")
    
    async def create_image_to_video_job(
        self,
        request: ImageToVideoRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an image-to-video generation job
        
        Args:
            request: I2V request parameters
            user_id: Optional user identifier
            
        Returns:
            Job information with task_id
        """
        logger.info("minimax_service_create_i2v",
                   prompt=request.prompt[:50],
                   model=request.model.value)
        
        try:
            # Create video generation task
            task_id = await self.adapter.image_to_video(
                prompt=request.prompt,
                first_frame_image=request.first_frame_image,
                model=MinimaxModel(request.model.value),
                aspect_ratio=request.aspect_ratio.value,
                duration_seconds=request.duration_seconds,
                prompt_optimizer=request.prompt_optimizer,
                seed=request.seed,
                callback_url=request.callback_url
            )
            
            # Store job metadata
            job_metadata = MinimaxJobMetadata(
                task_id=task_id,
                mode="i2v",
                model=request.model.value,
                prompt=request.prompt,
                status=TaskStatus.QUEUED,
                created_at=datetime.utcnow().isoformat(),
                duration_seconds=request.duration_seconds,
                aspect_ratio=request.aspect_ratio.value
            )
            
            self._jobs[task_id] = job_metadata
            
            logger.info("minimax_service_job_created",
                       task_id=task_id,
                       mode="i2v")
            
            return {
                "task_id": task_id,
                "status": "queued",
                "mode": "i2v",
                "message": "Image-to-video generation task created successfully"
            }
            
        except Exception as e:
            logger.error("minimax_service_i2v_error", error=str(e))
            raise ProviderError(f"Failed to create I2V job: {str(e)}")
    
    async def create_first_last_frame_job(
        self,
        request: FirstLastFrameToVideoRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a first/last frame to video generation job
        
        Args:
            request: FL2V request parameters
            user_id: Optional user identifier
            
        Returns:
            Job information with task_id
        """
        logger.info("minimax_service_create_fl2v",
                   prompt=request.prompt[:50],
                   model=request.model.value)
        
        try:
            # Create video generation task
            task_id = await self.adapter.first_last_frame_to_video(
                prompt=request.prompt,
                first_frame_image=request.first_frame_image,
                last_frame_image=request.last_frame_image,
                model=MinimaxModel(request.model.value),
                aspect_ratio=request.aspect_ratio.value,
                duration_seconds=request.duration_seconds,
                prompt_optimizer=request.prompt_optimizer,
                seed=request.seed,
                callback_url=request.callback_url
            )
            
            # Store job metadata
            job_metadata = MinimaxJobMetadata(
                task_id=task_id,
                mode="fl2v",
                model=request.model.value,
                prompt=request.prompt,
                status=TaskStatus.QUEUED,
                created_at=datetime.utcnow().isoformat(),
                duration_seconds=request.duration_seconds,
                aspect_ratio=request.aspect_ratio.value
            )
            
            self._jobs[task_id] = job_metadata
            
            logger.info("minimax_service_job_created",
                       task_id=task_id,
                       mode="fl2v")
            
            return {
                "task_id": task_id,
                "status": "queued",
                "mode": "fl2v",
                "message": "First/last frame to video generation task created successfully"
            }
            
        except Exception as e:
            logger.error("minimax_service_fl2v_error", error=str(e))
            raise ProviderError(f"Failed to create FL2V job: {str(e)}")
    
    async def create_subject_reference_job(
        self,
        request: SubjectReferenceToVideoRequest,
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a subject reference to video generation job
        
        Args:
            request: S2V request parameters
            user_id: Optional user identifier
            
        Returns:
            Job information with task_id
        """
        logger.info("minimax_service_create_s2v",
                   prompt=request.prompt[:50],
                   model=request.model.value,
                   ref_type=request.reference_type.value)
        
        try:
            # Create video generation task
            task_id = await self.adapter.subject_reference_to_video(
                prompt=request.prompt,
                reference_image=request.reference_image,
                model=MinimaxModel(request.model.value),
                reference_type=request.reference_type.value,
                aspect_ratio=request.aspect_ratio.value,
                duration_seconds=request.duration_seconds,
                prompt_optimizer=request.prompt_optimizer,
                seed=request.seed,
                callback_url=request.callback_url
            )
            
            # Store job metadata
            job_metadata = MinimaxJobMetadata(
                task_id=task_id,
                mode="s2v",
                model=request.model.value,
                prompt=request.prompt,
                status=TaskStatus.QUEUED,
                created_at=datetime.utcnow().isoformat(),
                duration_seconds=request.duration_seconds,
                aspect_ratio=request.aspect_ratio.value
            )
            
            self._jobs[task_id] = job_metadata
            
            logger.info("minimax_service_job_created",
                       task_id=task_id,
                       mode="s2v")
            
            return {
                "task_id": task_id,
                "status": "queued",
                "mode": "s2v",
                "message": "Subject reference to video generation task created successfully"
            }
            
        except Exception as e:
            logger.error("minimax_service_s2v_error", error=str(e))
            raise ProviderError(f"Failed to create S2V job: {str(e)}")
    
    async def get_job_status(self, task_id: str) -> TaskStatusResponse:
        """
        Get the status of a video generation job
        
        Args:
            task_id: Task identifier
            
        Returns:
            Current task status with details
        """
        logger.info("minimax_service_get_status", task_id=task_id)
        
        try:
            # Query task status from adapter
            status_data = await self.adapter.query_task_status(task_id)
            
            # Update local job metadata if exists
            if task_id in self._jobs:
                job = self._jobs[task_id]
                job.status = TaskStatus(status_data.get("status"))
                if status_data.get("file_id"):
                    job.file_id = status_data["file_id"]
                if status_data.get("status") == TaskStatus.SUCCESS.value:
                    job.completed_at = datetime.utcnow().isoformat()
                if status_data.get("error"):
                    job.error_message = status_data["error"]
            
            return TaskStatusResponse(**status_data)
            
        except Exception as e:
            logger.error("minimax_service_status_error",
                        task_id=task_id,
                        error=str(e))
            raise ProviderError(f"Failed to get job status: {str(e)}")
    
    async def download_and_store_video(
        self,
        task_id: str,
        file_id: str
    ) -> Dict[str, Any]:
        """
        Download generated video and store in S3
        
        Args:
            task_id: Task identifier
            file_id: File identifier from completed task
            
        Returns:
            Dict with video URL and metadata
        """
        logger.info("minimax_service_download_store",
                   task_id=task_id,
                   file_id=file_id)
        
        try:
            # Download video from MiniMax
            video_bytes = await self.adapter.download_video(file_id)
            
            # Generate unique filename
            video_filename = f"minimax_{task_id}_{file_id}.mp4"
            video_key = f"videos/minimax/{video_filename}"
            
            # Upload to S3
            video_file = BytesIO(video_bytes)
            s3_url = self.storage.upload_file(
                file=video_file,
                key=video_key,
                content_type="video/mp4"
            )
            
            # Update job metadata
            if task_id in self._jobs:
                self._jobs[task_id].video_url = s3_url
            
            logger.info("minimax_service_video_stored",
                       task_id=task_id,
                       url=s3_url,
                       size_bytes=len(video_bytes))
            
            return {
                "task_id": task_id,
                "file_id": file_id,
                "video_url": s3_url,
                "size_bytes": len(video_bytes),
                "message": "Video downloaded and stored successfully"
            }
            
        except Exception as e:
            logger.error("minimax_service_download_error",
                        task_id=task_id,
                        error=str(e))
            raise ProviderError(f"Failed to download and store video: {str(e)}")
    
    async def poll_job_until_complete(
        self,
        task_id: str,
        max_wait_seconds: int = 300,
        auto_download: bool = True
    ) -> Dict[str, Any]:
        """
        Poll job status until completion and optionally download
        
        Args:
            task_id: Task identifier
            max_wait_seconds: Maximum time to wait
            auto_download: Automatically download and store when complete
            
        Returns:
            Final job result with video URL if auto_download is True
        """
        logger.info("minimax_service_poll_start",
                   task_id=task_id,
                   max_wait=max_wait_seconds)
        
        try:
            # Use adapter's polling method
            final_status = await self.adapter.poll_until_complete(
                task_id=task_id,
                max_wait_seconds=max_wait_seconds
            )
            
            result = {
                "task_id": task_id,
                "status": final_status.get("status"),
                "file_id": final_status.get("file_id")
            }
            
            # Auto-download if requested and successful
            if auto_download and final_status.get("status") == TaskStatus.SUCCESS.value:
                file_id = final_status.get("file_id")
                if file_id:
                    download_result = await self.download_and_store_video(task_id, file_id)
                    result.update(download_result)
            
            return result
            
        except Exception as e:
            logger.error("minimax_service_poll_error",
                        task_id=task_id,
                        error=str(e))
            raise ProviderError(f"Failed to poll job: {str(e)}")
    
    def get_job_metadata(self, task_id: str) -> Optional[MinimaxJobMetadata]:
        """Get local job metadata"""
        return self._jobs.get(task_id)
    
    def list_jobs(
        self,
        limit: int = 50,
        status_filter: Optional[TaskStatus] = None
    ) -> List[MinimaxJobMetadata]:
        """List jobs with optional filtering"""
        jobs = list(self._jobs.values())
        
        if status_filter:
            jobs = [j for j in jobs if j.status == status_filter]
        
        # Sort by creation time, newest first
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        return jobs[:limit]
