from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import Dict

from ..db import get_db
from ..schemas.common import PresignRequest, PresignResponse, PresignKind
from ..services.storage import StorageService
from ..utils.logging import get_logger
from ..exceptions import ValidationError, StorageError

router = APIRouter(prefix="/uploads")
logger = get_logger("uploads_routes")


@router.post("/presign", response_model=PresignResponse)
async def create_presigned_upload(
    request: PresignRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Create a presigned upload URL for a file
    Implements the policy constraints from /docs/storage/presign_policy.md
    as specified in the OpenAPI schema
    
    Accepted file types and size limits:
    - IMAGE: image/jpeg, image/png (≤ 10MB)
    - AUDIO: audio/mpeg, audio/wav (≤ 20MB)
    - VIDEO: video/mp4 (≤ 100MB)
    
    Returns presigned upload URL and public file URL
    """
    # Validate kind
    if request.kind not in [k for k in PresignKind]:
        valid_kinds = ", ".join([k.value for k in PresignKind])
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file kind. Must be one of: {valid_kinds}"
        )
    
    # Validate filename is provided
    if not request.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )
    
    # Validate mime type is provided
    if not request.mime:
        raise HTTPException(
            status_code=400,
            detail="MIME type is required"
        )
    
    storage_service = StorageService()
    
    try:
        # Generate presigned URLs based on the request
        upload_url, file_url = storage_service.create_presigned_urls(
            request.kind,
            request.filename,
            request.mime,
            request.content_length
        )
        
        logger.info(
            "presign_created",
            kind=request.kind,
            mime=request.mime,
            content_length=request.content_length,
            request_id=getattr(req.state, "request_id", None)
        )
        
        return {
            "uploadUrl": upload_url,
            "fileUrl": file_url
        }
    except ValidationError as e:
        # Catch validation errors from storage service
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    except StorageError as e:
        # Catch storage service errors
        logger.error(
            "presign_error",
            error=str(e),
            request_id=getattr(req.state, "request_id", None)
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to generate presigned URL"
        )