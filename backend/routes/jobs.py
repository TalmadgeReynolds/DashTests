from fastapi import APIRouter, Depends, Query, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
import uuid

from ..db import get_db
from ..schemas.job import JobDetail, JobStatus, JobMethod
from ..services.orchestrator import Orchestrator
from ..utils.logging import get_logger

router = APIRouter(prefix="/jobs")
logger = get_logger("jobs_routes")


@router.get("/{id}", response_model=JobDetail)
async def get_job(
    id: uuid.UUID,
    req: Request,
    db: Session = Depends(get_db)
):
    """Get job details by ID"""
    orchestrator = Orchestrator(db)
    job = orchestrator.get_job(id)
    
    logger.info(
        "job_details_accessed",
        job_id=str(id),
        request_id=getattr(req.state, "request_id", None)
    )
    
    return job


@router.get("/", response_model=List[JobDetail])
async def list_jobs(
    status: Optional[str] = None,
    method: Optional[str] = None,
    limit: int = Query(25, ge=1, le=100, description="Maximum number of jobs to return (1-100)"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip"),
    req: Request = None,
    db: Session = Depends(get_db)
):
    """List jobs with optional filtering as specified in the OpenAPI schema"""
    # Validate status if provided
    if status is not None and status not in [s.value for s in JobStatus]:
        valid_statuses = ", ".join([s.value for s in JobStatus])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )
    
    # Validate method if provided
    if method is not None and method not in [m.value for m in JobMethod]:
        valid_methods = ", ".join([m.value for m in JobMethod])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid method. Must be one of: {valid_methods}"
        )
    
    orchestrator = Orchestrator(db)
    jobs = orchestrator.list_jobs(status, method, limit, offset)
    
    logger.info(
        "jobs_list_accessed",
        filters={"status": status, "method": method},
        count=len(jobs),
        request_id=getattr(req.state, "request_id", None)
    )
    
    return jobs