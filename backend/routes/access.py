# Create a backend API endpoint to generate presigned URLs for PDFs
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
from ..services.storage import StorageService
from ..utils.logging import get_logger

router = APIRouter(prefix="/access")
logger = get_logger("access_routes")


@router.get("/presign/{key:path}", response_model=Dict[str, str])
async def create_presigned_access_url(key: str):
    """
    Create a presigned URL for accessing a file (like a PDF)
    
    Args:
        key: The storage key of the file
    
    Returns:
        Dict with presignedUrl
    """
    try:
        storage_service = StorageService()
        presigned_url = storage_service.create_presigned_get_url(key)
        
        logger.info("presigned_access_url_created", key=key)
        
        return {
            "presignedUrl": presigned_url
        }
    except Exception as e:
        logger.error("presigned_access_url_error", error=str(e), key=key)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate presigned access URL"
        )