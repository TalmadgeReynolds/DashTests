"""
Extension to support WebSocket updates
"""
import asyncio
from uuid import UUID
from typing import Optional, Dict, Any

# Create reference to be set later
_emit_job_update = None

def set_emit_function(emit_function):
    """Set the emit function to avoid circular imports"""
    global _emit_job_update
    _emit_job_update = emit_function

async def update_job_with_ws(
    job_id: UUID, 
    status: str, 
    progress: Optional[float] = None
):
    """Update job status and emit via WebSocket"""
    # Run the emit in a separate task to avoid blocking
    if _emit_job_update:
        await _emit_job_update(str(job_id), status, progress)
    else:
        # If the emit function is not set yet, just return
        pass