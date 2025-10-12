from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session
from typing import Dict

from ..db import get_db
from ..schemas.job import CreatePromptJobRequest, CreateAudioJobRequest, JobResponse
from ..services.orchestrator import Orchestrator
from ..utils.logging import get_logger

router = APIRouter(prefix="/lipsync")
logger = get_logger("lipsync_routes")


@router.post("/prompt", status_code=201, response_model=JobResponse)
async def create_prompt_job(
    request: CreatePromptJobRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """Create a prompt → lip-sync job as specified in the OpenAPI schema"""
    # Validate script length as per OpenAPI spec
    if len(request.script) < 8 or len(request.script) > 500:
        raise HTTPException(
            status_code=400, 
            detail=f"Script must be between 8 and 500 characters (currently {len(request.script)})"
        )
    
    from ..worker import enqueue_job
    orchestrator = Orchestrator(db)
    
    # Create the job
    job_id = orchestrator.create_prompt_job(request)
    
    # Determine which queue to use based on priority settings
    queue_name = "option1" if request.priority == "high" else "option2"
    
    # Enqueue job for processing by worker
    enqueue_job(str(job_id), job_type="prompt", queue_name=queue_name)
    
    logger.info(
        "prompt_job_created", 
        job_id=str(job_id),
        queue=queue_name,
        request_id=getattr(req.state, "request_id", None)
    )
    
    return {"job_id": job_id}


@router.post("/audio", status_code=201, response_model=JobResponse)
async def create_audio_job(
    request: CreateAudioJobRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """Create an audio-driven lip-sync job as specified in the OpenAPI schema"""
    # Validate that either audio_url or tts is provided
    if not request.audio_url and not request.tts:
        raise HTTPException(
            status_code=400, 
            detail="Either audio_url or tts must be provided"
        )
    
    # Validate TTS text if provided
    if request.tts and len(request.tts.text) < 3:
        raise HTTPException(
            status_code=400, 
            detail=f"TTS text must be at least 3 characters long (currently {len(request.tts.text)})"
        )
    
    # Validate action prompt if provided
    if request.action_prompt and len(request.action_prompt) > 120:
        raise HTTPException(
            status_code=400, 
            detail=f"Action prompt must be at most 120 characters (currently {len(request.action_prompt)})"
        )
    
    from ..worker import enqueue_job
    orchestrator = Orchestrator(db)
    
    # Create the job
    job_id = orchestrator.create_audio_job(request)
    
    # Determine which queue to use based on priority settings
    queue_name = "option1" if request.priority == "high" else "option2"
    
    # Enqueue job for processing by worker
    enqueue_job(str(job_id), job_type="audio", queue_name=queue_name)
    
    logger.info(
        "audio_job_created", 
        job_id=str(job_id),
        queue=queue_name,
        request_id=getattr(req.state, "request_id", None)
    )
    
    return {"job_id": job_id}