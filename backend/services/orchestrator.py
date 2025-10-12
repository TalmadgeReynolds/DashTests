import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy.orm import Session

from ..models.job import Job, Asset
from ..schemas.job import CreatePromptJobRequest, CreateAudioJobRequest, VideoOpts, PostFX
from ..utils.settings import get_settings
from ..utils.logging import get_logger, log_job_event
from ..exceptions import NotFoundError
from ..adapters.veo_adapter import VeoAdapter
from ..adapters.heygen_adapter import HeygenAdapter
from ..adapters.tts_elevenlabs import ElevenLabsAdapter
from ..adapters.postfx import PostFxAdapter
from ..db import db_transaction

settings = get_settings()
logger = get_logger("orchestrator")


class Orchestrator:
    """
    Service that orchestrates the job workflow, ensuring state transitions follow
    the state machine defined in /docs/arch/job_state_machine.md
    
    State Machine:
    QUEUED → RUNNING → POST → DONE | ERROR
    
    Transitions:
    - enqueue -> QUEUED
    - worker start -> RUNNING
    - provider finished -> (if postfx on) POST else DONE
    - postfx ok -> DONE
    - any failure -> ERROR
    
    Job meta contains a timeline array capturing { step, ts, data } for each state transition.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.veo_adapter = VeoAdapter(mock_mode=settings.VEO3_MOCK_MODE)
        self.heygen_adapter = HeygenAdapter(mock_mode=settings.HEYGEN_MOCK_MODE)
        self.tts_adapter = ElevenLabsAdapter(mock_mode=settings.ELEVENLABS_MOCK_MODE)
        self.postfx_adapter = PostFxAdapter(mock_mode=settings.POSTFX_MOCK_MODE)
    
    def create_prompt_job(self, request: CreatePromptJobRequest) -> uuid.UUID:
        """Create a new prompt → lip-sync job"""
        job_id = uuid.uuid4()
        
        # Calculate cost estimate
        generation_credits = settings.COST_GENERATION_CREDITS_VEO3
        postfx_minutes = 0  # Estimate based on script length
        total_estimate_cents = int(generation_credits * 10)  # Example calculation
        
        # Initialize timeline array in metadata
        now = datetime.utcnow().isoformat()
        
        # Build metadata
        meta = {
            "script": request.script,
            "reference_image_url": request.reference_image_url,
            "post": request.post.dict() if request.post else {"interpolate": True, "upscale": False},
            "video": request.video.dict() if request.video else {"fps": 24, "aspect": "16:9", "max_duration": 12},
            "cost": {
                "generation_credits": generation_credits,
                "postfx_minutes": postfx_minutes,
                "total_estimate_cents": total_estimate_cents
            },
            "timeline": [
                {
                    "step": "created",
                    "ts": now,
                    "data": {"method": "PROMPT_TO_LIPSYNC"}
                }
            ]
        }
        
        # Create job record
        with db_transaction() as session:
            job = Job(
                id=job_id,
                method="PROMPT_TO_LIPSYNC",
                status="QUEUED",
                engine="veo3",
                meta=meta,
                generation_credits=generation_credits,
                postfx_minutes=postfx_minutes,
                total_estimate_cents=total_estimate_cents
            )
            
            session.add(job)
        
        log_job_event(str(job_id), "job_created", extra={"method": "PROMPT_TO_LIPSYNC"})
        
        return job_id
    
    def create_audio_job(self, request: CreateAudioJobRequest) -> uuid.UUID:
        """Create a new audio-driven lip-sync job"""
        job_id = uuid.uuid4()
        
        # Calculate cost estimate
        generation_credits = settings.COST_GENERATION_CREDITS_HEYGEN
        postfx_minutes = 0  # Estimate based on audio duration
        total_estimate_cents = int(generation_credits * 10)  # Example calculation
        
        # Initialize timeline array in metadata
        now = datetime.utcnow().isoformat()
        
        # Build metadata
        meta = {
            "image_url": request.image_url,
            "audio_url": request.audio_url,
            "tts": request.tts.dict() if request.tts else None,
            "action_prompt": request.action_prompt,
            "post": request.post.dict() if request.post else {"interpolate": True, "upscale": False},
            "video": request.video.dict() if request.video else {"fps": 24, "aspect": "16:9", "max_duration": 12},
            "cost": {
                "generation_credits": generation_credits,
                "postfx_minutes": postfx_minutes,
                "total_estimate_cents": total_estimate_cents
            },
            "timeline": [
                {
                    "step": "created",
                    "ts": now,
                    "data": {"method": "AUDIO_DRIVEN"}
                }
            ]
        }
        
        # Create job record
        with db_transaction() as session:
            job = Job(
                id=job_id,
                method="AUDIO_DRIVEN",
                status="QUEUED",
                engine="heygen",
                meta=meta,
                generation_credits=generation_credits,
                postfx_minutes=postfx_minutes,
                total_estimate_cents=total_estimate_cents
            )
            
            session.add(job)
        
        log_job_event(str(job_id), "job_created", extra={"method": "AUDIO_DRIVEN"})
        
        return job_id
    
    def get_job(self, job_id: uuid.UUID) -> Job:
        """Get a job by ID"""
        job = self.db.query(Job).filter(Job.id == job_id).first()
        if not job:
            raise NotFoundError(f"Job {job_id} not found")
        return job
    
    def list_jobs(self, status: Optional[str] = None, method: Optional[str] = None, 
                  limit: int = 25, offset: int = 0) -> List[Job]:
        """List jobs with optional filtering"""
        query = self.db.query(Job)
        
        if status:
            query = query.filter(Job.status == status)
            
        if method:
            query = query.filter(Job.method == method)
            
        query = query.order_by(Job.created_at.desc())
        query = query.limit(limit).offset(offset)
        
        return query.all()
    
    async def run_prompt_to_lipsync(self, job_id: uuid.UUID) -> None:
        """
        Process a prompt-to-lipsync job through its workflow
        Following the state machine: QUEUED → RUNNING → POST → DONE
        """
        job = self.get_job(job_id)
        
        # Check if job is already in a terminal state
        if job.status in ("DONE", "ERROR"):
            log_job_event(str(job_id), "job_already_terminal", extra={"status": job.status})
            return
            
        # Validate job method
        if job.method != "PROMPT_TO_LIPSYNC":
            log_job_event(str(job_id), "invalid_job_method", extra={
                "expected": "PROMPT_TO_LIPSYNC", 
                "actual": job.method
            })
            self._transition_to_error(job, f"Invalid job method: {job.method}")
            return
        
        try:
            # Process based on current state
            if job.status == "QUEUED":
                self._transition_to_running(job)
                await self._process_prompt_job(job)
            elif job.status == "RUNNING":
                await self._check_prompt_job_status(job)
            elif job.status == "POST":
                await self._process_post_fx(job)
        except Exception as e:
            # Handle exceptions and transition to ERROR state
            logger.error("job_processing_failed", job_id=str(job_id), error=str(e))
            self._transition_to_error(job, str(e))
            
    async def run_audio_driven(self, job_id: uuid.UUID) -> None:
        """
        Process an audio-driven job through its workflow
        Following the state machine: QUEUED → RUNNING → POST → DONE
        """
        job = self.get_job(job_id)
        
        # Check if job is already in a terminal state
        if job.status in ("DONE", "ERROR"):
            log_job_event(str(job_id), "job_already_terminal", extra={"status": job.status})
            return
            
        # Validate job method
        if job.method != "AUDIO_DRIVEN":
            log_job_event(str(job_id), "invalid_job_method", extra={
                "expected": "AUDIO_DRIVEN", 
                "actual": job.method
            })
            self._transition_to_error(job, f"Invalid job method: {job.method}")
            return
            
        try:
            # Process based on current state
            if job.status == "QUEUED":
                self._transition_to_running(job)
                await self._process_audio_job(job)
            elif job.status == "RUNNING":
                await self._check_audio_job_status(job)
            elif job.status == "POST":
                await self._process_post_fx(job)
        except Exception as e:
            # Handle exceptions and transition to ERROR state
            logger.error("job_processing_failed", job_id=str(job_id), error=str(e))
            self._transition_to_error(job, str(e))
    
    async def process_job(self, job_id: uuid.UUID) -> None:
        """
        Process a job through its workflow based on its method
        This is a convenience method that routes to the appropriate specialized method
        """
        job = self.get_job(job_id)
        
        if job.method == "PROMPT_TO_LIPSYNC":
            await self.run_prompt_to_lipsync(job_id)
        elif job.method == "AUDIO_DRIVEN":
            await self.run_audio_driven(job_id)
        else:
            logger.error("unsupported_job_method", job_id=str(job_id), method=job.method)
            self._transition_to_error(job, f"Unsupported job method: {job.method}")
    
    def _transition_to_running(self, job: Job) -> None:
        """Transition a job from QUEUED to RUNNING"""
        if job.status != "QUEUED":
            logger.warning("invalid_transition", job_id=str(job.id), 
                          from_status=job.status, to_status="RUNNING")
            return
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline in metadata
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "start_processing",
            "ts": now_iso,
            "data": {"from_status": job.status, "to_status": "RUNNING"}
        })
            
        job.status = "RUNNING"
        job.updated_at = now
        job.meta = meta
        
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "status_changed", extra={"status": "RUNNING"})
    
    def _transition_to_post(self, job: Job) -> None:
        """Transition a job from RUNNING to POST"""
        if job.status != "RUNNING":
            logger.warning("invalid_transition", job_id=str(job.id), 
                          from_status=job.status, to_status="POST")
            return
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline in metadata
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "provider_finished",
            "ts": now_iso,
            "data": {"from_status": job.status, "to_status": "POST", "provider_job_id": job.provider_job_id}
        })
            
        job.status = "POST"
        job.updated_at = now
        job.meta = meta
        
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "status_changed", extra={"status": "POST"})
    
    def _transition_to_done(self, job: Job, output_url: str) -> None:
        """Transition a job to DONE state with output URL"""
        # Only valid transitions are from RUNNING or POST
        if job.status not in ("RUNNING", "POST"):
            logger.warning("invalid_transition", job_id=str(job.id), 
                          from_status=job.status, to_status="DONE")
            return
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        completed_at = now
        
        # Update timeline in metadata
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        step_name = "postfx_complete" if job.status == "POST" else "provider_finished"
        
        meta["timeline"].append({
            "step": step_name,
            "ts": now_iso,
            "data": {
                "from_status": job.status, 
                "to_status": "DONE", 
                "output_url": output_url
            }
        })
            
        job.status = "DONE"
        job.output_url = output_url
        job.updated_at = now
        job.completed_at = completed_at
        job.meta = meta
        
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "status_changed", extra={"status": "DONE", "output_url": output_url})
    
    def _transition_to_error(self, job: Job, error_message: str, error_code: str = "PROCESSING_ERROR") -> None:
        """Transition a job to ERROR state"""
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline in metadata
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "error",
            "ts": now_iso,
            "data": {
                "from_status": job.status, 
                "to_status": "ERROR", 
                "error_code": error_code,
                "error_message": error_message
            }
        })
        
        job.status = "ERROR"
        job.error = error_message
        job.meta = meta
        job.updated_at = now
        
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "status_changed", extra={"status": "ERROR", "error_message": error_message})
    
    async def _process_prompt_job(self, job: Job) -> None:
        """Process a prompt-to-lipsync job with Veo 3"""
        meta = job.meta
        script = meta["script"]
        reference_image_url = meta.get("reference_image_url")
        
        video_opts = meta.get("video", {})
        fps = video_opts.get("fps", 24)
        aspect = video_opts.get("aspect", "16:9")
        max_duration = video_opts.get("max_duration", 12)
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Submit job to Veo 3
        provider_job_id = self.veo_adapter.create_job(
            script, 
            reference_image_url,
            fps,
            aspect,
            max_duration
        )
        
        # Update job with provider job ID and timeline
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "provider_job_created",
            "ts": now_iso,
            "data": {"provider": "veo3", "provider_job_id": provider_job_id}
        })
        
        job.provider_job_id = provider_job_id
        job.meta = meta
        
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "provider_job_created", provider_job_id=provider_job_id)
        
        # Check initial status
        await self._check_prompt_job_status(job)
    
    async def _check_prompt_job_status(self, job: Job) -> None:
        """Check the status of a Veo job"""
        if not job.provider_job_id:
            logger.error("missing_provider_job_id", job_id=str(job.id))
            self._transition_to_error(job, "Missing provider job ID")
            return
            
        # Poll Veo for status
        result = self.veo_adapter.poll_result(job.provider_job_id)
        status = result["status"]
        video_url = result.get("video_url")
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline with provider status check
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "provider_status_check",
            "ts": now_iso,
            "data": {
                "provider": "veo3", 
                "provider_job_id": job.provider_job_id,
                "status": status
            }
        })
        
        job.meta = meta
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "provider_status", provider_job_id=job.provider_job_id, 
                      extra={"provider_status": status})
        
        if status == "ERROR":
            self._transition_to_error(job, "Provider job failed")
            return
            
        if status == "DONE" and video_url:
            # Job completed successfully
            meta = job.meta
            post_opts = meta.get("post", {})
            
            if post_opts.get("interpolate", True) or post_opts.get("upscale", False):
                # Transition to POST and start post-processing
                self._transition_to_post(job)
                await self._process_post_fx(job, video_url)
            else:
                # No post-processing needed, go directly to DONE
                self._transition_to_done(job, video_url)
    
    async def _process_audio_job(self, job: Job) -> None:
        """Process an audio-driven job with Heygen"""
        meta = job.meta
        image_url = meta["image_url"]
        audio_url = meta.get("audio_url")
        tts = meta.get("tts")
        action_prompt = meta.get("action_prompt")
        
        video_opts = meta.get("video", {})
        fps = video_opts.get("fps", 24)
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        if "timeline" not in meta:
            meta["timeline"] = []
        
        # If TTS is specified, generate audio first
        if tts and not audio_url:
            tts_text = tts.get("text", "")
            voice_id = tts.get("voice_id")
            stability = tts.get("stability", 0.65)
            similarity_boost = tts.get("similarity_boost", 0.75)
            pace = tts.get("pace", 1.0)
            
            meta["timeline"].append({
                "step": "tts_start",
                "ts": now_iso,
                "data": {
                    "provider": "elevenlabs",
                    "text_length": len(tts_text),
                    "voice_id": voice_id
                }
            })
            
            job.meta = meta
            with db_transaction() as session:
                session.add(job)
            
            log_job_event(str(job.id), "tts_start")
            
            # Generate speech with ElevenLabs
            audio_url = self.tts_adapter.synthesize(
                tts_text,
                voice_id,
                stability,
                similarity_boost,
                pace
            )
            
            now = datetime.utcnow()
            now_iso = now.isoformat()
            
            # Update job metadata with the generated audio URL
            meta["audio_url"] = audio_url
            meta["timeline"].append({
                "step": "tts_complete",
                "ts": now_iso,
                "data": {"audio_url": audio_url}
            })
            
            job.meta = meta
            with db_transaction() as session:
                session.add(job)
            
            log_job_event(str(job.id), "tts_complete", extra={"audio_url": audio_url})
        
        # Submit job to Heygen
        provider_job_id = self.heygen_adapter.create_talking_photo(
            image_url,
            audio_url,
            action_prompt,
            fps
        )
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update job with provider job ID and timeline
        meta["timeline"].append({
            "step": "provider_job_created",
            "ts": now_iso,
            "data": {"provider": "heygen", "provider_job_id": provider_job_id}
        })
        
        job.provider_job_id = provider_job_id
        job.meta = meta
        
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "provider_job_created", provider_job_id=provider_job_id)
        
        # Check initial status
        await self._check_audio_job_status(job)
    
    async def _check_audio_job_status(self, job: Job) -> None:
        """Check the status of a Heygen job"""
        if not job.provider_job_id:
            logger.error("missing_provider_job_id", job_id=str(job.id))
            self._transition_to_error(job, "Missing provider job ID")
            return
            
        # Poll Heygen for status
        result = self.heygen_adapter.poll_result(job.provider_job_id)
        status = result["status"]
        video_url = result.get("video_url")
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline with provider status check
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "provider_status_check",
            "ts": now_iso,
            "data": {
                "provider": "heygen", 
                "provider_job_id": job.provider_job_id,
                "status": status
            }
        })
        
        job.meta = meta
        with db_transaction() as session:
            session.add(job)
        
        log_job_event(str(job.id), "provider_status", provider_job_id=job.provider_job_id, 
                      extra={"provider_status": status})
        
        if status == "ERROR":
            self._transition_to_error(job, "Provider job failed")
            return
            
        if status == "DONE" and video_url:
            # Job completed successfully
            meta = job.meta
            post_opts = meta.get("post", {})
            
            if post_opts.get("interpolate", True) or post_opts.get("upscale", False):
                # Transition to POST and start post-processing
                self._transition_to_post(job)
                await self._process_post_fx(job, video_url)
            else:
                # No post-processing needed, go directly to DONE
                self._transition_to_done(job, video_url)
    
    async def _process_post_fx(self, job: Job, video_url: Optional[str] = None) -> None:
        """Process post-effects for a job"""
        meta = job.meta
        post_opts = meta.get("post", {})
        video_opts = meta.get("video", {})
        
        do_interpolate = post_opts.get("interpolate", True)
        do_upscale = post_opts.get("upscale", False)
        target_fps = video_opts.get("fps", 24)
        
        # Use provided video URL or get from job
        video_url = video_url or job.meta.get("video_url")
        if not video_url:
            logger.error("missing_video_url", job_id=str(job.id))
            self._transition_to_error(job, "Missing video URL for post-processing")
            return
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline with postfx start
        if "timeline" not in meta:
            meta["timeline"] = []
            
        meta["timeline"].append({
            "step": "postfx_start",
            "ts": now_iso,
            "data": {
                "interpolate": do_interpolate,
                "upscale": do_upscale,
                "target_fps": target_fps,
                "input_url": video_url
            }
        })
        
        job.meta = meta
        with db_transaction() as session:
            session.add(job)
            
        log_job_event(str(job.id), "postfx_start", extra={
            "interpolate": do_interpolate,
            "upscale": do_upscale,
            "target_fps": target_fps
        })
        
        # Process through PostFX pipeline
        output_url = await self.postfx_adapter.process(
            video_url,
            do_interpolate,
            do_upscale,
            target_fps
        )
        
        log_job_event(str(job.id), "postfx_complete", extra={"output_url": output_url})
        
        # Transition to DONE with the processed output URL
        self._transition_to_done(job, output_url)
    
    def handle_webhook(self, provider: str, provider_job_id: str, status: str, output_url: Optional[str] = None) -> None:
        """
        Handle webhook callback from provider
        Implements webhook handling as described in /docs/engines/webhooks.md
        
        Features:
        - Idempotent updates (ignores jobs in terminal states)
        - Records webhook event in job timeline
        - Updates job status based on provider status
        - Handles post-processing transition if needed
        """
        # Find job by provider_job_id
        job = self.db.query(Job).filter(Job.provider_job_id == provider_job_id).first()
        
        if not job:
            logger.warning("webhook_job_not_found", provider=provider, provider_job_id=provider_job_id)
            return
            
        # Check if job is already in a terminal state (idempotency)
        if job.status in ("DONE", "ERROR"):
            logger.info("webhook_job_already_terminal", 
                        job_id=str(job.id), 
                        status=job.status, 
                        provider_job_id=provider_job_id)
            return
        
        now = datetime.utcnow()
        now_iso = now.isoformat()
        
        # Update timeline with webhook event
        meta = job.meta
        if "timeline" not in meta:
            meta["timeline"] = []
            
        # Record detailed webhook event data
        webhook_data = {
            "provider": provider,
            "provider_job_id": provider_job_id,
            "status": status,
            "output_url": output_url,
            "received_at": now_iso,
        }
            
        meta["timeline"].append({
            "step": "webhook_received",
            "ts": now_iso,
            "data": webhook_data
        })
        
        # Store provider job details for tracking
        if "provider_data" not in meta:
            meta["provider_data"] = {}
        
        meta["provider_data"][provider] = {
            "job_id": provider_job_id,
            "status": status,
            "last_update": now_iso
        }
        
        job.meta = meta
        
        # Save job metadata update - already in a transaction from the caller
        self.db.add(job)
            
        log_job_event(str(job.id), "webhook_received", provider_job_id=provider_job_id,
                     extra={"provider": provider, "status": status})
        
        if status == "DONE" or status == "success":
            meta = job.meta
            post_opts = meta.get("post", {})
            
            if (post_opts.get("interpolate", True) or post_opts.get("upscale", False)) and output_url:
                # Needs post-processing
                self._transition_to_post(job)
                
                # Store video URL in metadata for post-processing
                meta["video_url"] = output_url
                job.meta = meta
                with db_transaction() as session:
                    session.add(job)
                
            elif output_url:
                # No post-processing needed
                self._transition_to_done(job, output_url)
                
        elif status == "ERROR" or status == "failed":
            self._transition_to_error(job, f"Provider webhook reported failure: {provider}")