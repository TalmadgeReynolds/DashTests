import json
import time
from datetime import datetime
from fastapi import APIRouter, Depends, Request, Header, Body, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Optional

from ..db import get_db, db_transaction
from ..services.orchestrator import Orchestrator
from ..adapters.heygen_adapter import HeygenAdapter
from ..exceptions import InvalidSignatureError
from ..utils.logging import get_logger

router = APIRouter(prefix="/webhooks")
logger = get_logger("webhooks_routes")


@router.post("/heygen")
async def heygen_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_heygen_signature: Optional[str] = Header(None)
):
    """
    Handle webhooks from Heygen
    
    Implements the webhook contract from /docs/engines/webhooks.md:
    - HMAC verification with constant-time compare
    - Idempotent DB updates (ignore if job is in terminal state)
    - Responds 200 only after DB commit
    - Logs request_id, provider_job_id, and latency_ms
    """
    # Record webhook receipt time for latency calculation
    webhook_received_time = time.time()
    request_id = getattr(request.state, "request_id", None)
    
    # Read request body
    body = await request.body()
    
    # Verify webhook signature using HMAC with constant-time compare
    adapter = HeygenAdapter()
    if not adapter.verify_webhook_signature(x_heygen_signature, body):
        logger.warning(
            "webhook_invalid_signature",
            signature=x_heygen_signature,
            request_id=request_id
        )
        raise InvalidSignatureError("Invalid webhook signature")
    
    try:
        # Parse webhook payload
        payload = json.loads(body)
        provider_job_id = payload.get("provider_job_id")
        status = payload.get("status")
        output_url = payload.get("output_url")
        
        # Calculate webhook latency if timestamp is provided in the payload
        webhook_latency_ms = None
        if "timestamp" in payload:
            try:
                # Calculate latency between provider event time and receipt time
                provider_timestamp = datetime.fromisoformat(payload["timestamp"].replace("Z", "+00:00"))
                provider_timestamp_ms = provider_timestamp.timestamp() * 1000
                webhook_received_ms = webhook_received_time * 1000
                webhook_latency_ms = int(webhook_received_ms - provider_timestamp_ms)
            except (ValueError, TypeError):
                # If timestamp parsing fails, ignore latency calculation
                pass
        
        if not provider_job_id or not status:
            logger.warning(
                "webhook_invalid_payload",
                payload=payload,
                request_id=request_id
            )
            raise HTTPException(status_code=400, detail="Invalid webhook payload")
        
        # Process webhook (idempotent) with DB transaction
        with db_transaction():
            orchestrator = Orchestrator(db)
            orchestrator.handle_webhook("heygen", provider_job_id, status, output_url)
        
        # Log with all required fields from docs/engines/webhooks.md
        logger.info(
            "webhook_processed",
            provider="heygen",
            provider_job_id=provider_job_id,
            status=status,
            latency_ms=webhook_latency_ms,
            request_id=request_id
        )
        
        # Return 200 response only after DB commit (as per requirements)
        return {
            "status": "ok", 
            "provider_job_id": provider_job_id,
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except json.JSONDecodeError:
        logger.error(
            "webhook_invalid_json",
            request_id=request_id
        )
        raise HTTPException(status_code=400, detail="Invalid JSON payload")