"""
WebSocket test endpoint
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from uuid import UUID

from ..db import get_db
from ..utils.logging import get_logger
from ..services.websocket_utils import update_job_with_ws

router = APIRouter(prefix="/websocket", tags=["websocket"])
logger = get_logger("websocket_routes")


@router.post("/test/{job_id}", status_code=200)
async def test_websocket(
    job_id: UUID,
    status: str = "RUNNING",
    progress: float = 0.5,
    db: Session = Depends(get_db)
):
    """
    Test WebSocket connection by sending an update for a job
    
    This endpoint is for testing only
    """
    logger.info("websocket_test", job_id=str(job_id), status=status, progress=progress)
    
    await update_job_with_ws(job_id, status, progress)
    
    return {
        "success": True,
        "message": f"WebSocket update sent for job {job_id} with status {status}"
    }