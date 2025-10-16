from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, HttpUrl, Field

from ..adapters.heygen_adapter import HeygenAdapter
from ..utils.settings import get_settings

settings = get_settings()
router = APIRouter(prefix="/avatars", tags=["avatars"])


class AvatarCreateRequest(BaseModel):
    """Request to create a new Heygen photo avatar"""
    image_urls: List[HttpUrl] = Field(..., min_items=1, description="URLs of the face images to use for creating the avatar")
    name: Optional[str] = Field(None, description="Optional name for the avatar")


class AvatarResponse(BaseModel):
    """Response model for avatar operations"""
    avatar_id: str = Field(..., description="ID of the created avatar")
    name: Optional[str] = Field(None, description="Name of the avatar")
    image_url: Optional[str] = Field(None, description="URL of the avatar image")
    status: str = Field(..., description="Status of the avatar (e.g., ready, processing)")
    created_at: int = Field(..., description="Unix timestamp of creation")


class AvatarListResponse(BaseModel):
    """Response model for avatar listing"""
    avatars: List[AvatarResponse] = Field(..., description="List of avatars")


@router.post("/create", response_model=AvatarResponse, summary="Create a new photo avatar")
async def create_avatar(request: AvatarCreateRequest):
    """
    Create a new photo avatar from face images.
    
    This endpoint uses the Heygen Photo Avatar API to create a new avatar from provided face images.
    The images should be clear photos of a person's face with good lighting and minimal occlusion.
    
    Returns the avatar ID and status.
    """
    adapter = HeygenAdapter()
    
    try:
        # Convert pydantic URLs to strings for the adapter
        image_urls = [str(url) for url in request.image_urls]
        
        # Create the avatar
        avatar_id = adapter.create_avatar(
            image_urls=image_urls,
            avatar_name=request.name
        )
        
        # Get details
        avatars = adapter.list_avatars([avatar_id])
        if not avatars:
            raise HTTPException(status_code=500, detail="Avatar created but could not retrieve details")
        
        return avatars[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=AvatarListResponse, summary="List available avatars")
async def list_avatars(avatar_ids: Optional[List[str]] = Query(None)):
    """
    List available photo avatars.
    
    This endpoint retrieves a list of avatars created with the Heygen Photo Avatar API.
    Optionally filter by specific avatar IDs.
    """
    adapter = HeygenAdapter()
    
    try:
        avatars = adapter.list_avatars(avatar_ids)
        return {"avatars": avatars}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{avatar_id}", response_model=AvatarResponse, summary="Get avatar details")
async def get_avatar(avatar_id: str):
    """
    Get details for a specific avatar.
    
    This endpoint retrieves details for a specific avatar by its ID.
    """
    adapter = HeygenAdapter()
    
    try:
        avatars = adapter.list_avatars([avatar_id])
        if not avatars:
            raise HTTPException(status_code=404, detail=f"Avatar with ID {avatar_id} not found")
        
        return avatars[0]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))