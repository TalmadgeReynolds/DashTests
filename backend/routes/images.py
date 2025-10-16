"""
Image generation routes using Vertex AI Imagen.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Literal
import logging
import base64
from uuid import uuid4

from ..adapters.imagen_adapter import ImagenAdapter
from ..services.storage import StorageService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/images", tags=["images"])


class GenerateImageRequest(BaseModel):
    """Request to generate an image with Imagen"""
    prompt: str = Field(..., min_length=10, max_length=1000, description="Image description")
    negative_prompt: Optional[str] = Field(None, max_length=500, description="What to avoid")
    aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = Field(default="1:1", description="Image aspect ratio")
    style: Literal["photorealistic", "cinematic", "professional"] = Field(default="photorealistic", description="Image style")


class GeneratePortraitRequest(BaseModel):
    """Request to generate a portrait optimized for lip-sync"""
    description: str = Field(..., min_length=10, max_length=500, description="Person description")
    gender: Optional[Literal["male", "female", "non-binary"]] = Field(None, description="Gender")
    age: Optional[Literal["young", "middle-aged", "elderly"]] = Field(None, description="Age range")
    ethnicity: Optional[str] = Field(None, max_length=100, description="Ethnicity")
    style: Literal["photorealistic", "cinematic", "professional"] = Field(default="photorealistic", description="Portrait style")
    aspect_ratio: Literal["1:1", "16:9", "9:16", "4:3", "3:4"] = Field(default="1:1", description="Image aspect ratio")


class ImageGenerationResponse(BaseModel):
    """Response from image generation"""
    image_url: str
    asset_id: str
    metadata: dict


def get_imagen_adapter():
    """Dependency to get Imagen adapter"""
    return ImagenAdapter()


def get_storage_service():
    """Dependency to get storage service"""
    return StorageService()


@router.post("/generate", response_model=ImageGenerationResponse)
async def generate_image(
    request: GenerateImageRequest,
    imagen: ImagenAdapter = Depends(get_imagen_adapter),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Generate an image using Vertex AI Imagen.
    
    Returns a URL to the generated image stored in S3/MinIO.
    """
    try:
        logger.info(f"Generating image: {request.prompt[:50]}...")
        
        # Generate image with Imagen
        result = await imagen.generate_image(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt,
            aspect_ratio=request.aspect_ratio,
            num_images=1
        )
        
        if not result["images"]:
            raise HTTPException(status_code=500, detail="No images generated")
        
        # Get the first image (base64)
        image_base64 = result["images"][0]
        image_bytes = base64.b64decode(image_base64)
        
        # Upload to storage
        asset_id = str(uuid4())
        filename = f"generated/{asset_id}.png"
        
        image_url = await storage.upload_bytes(
            data=image_bytes,
            filename=filename,
            content_type="image/png"
        )
        
        logger.info(f"Image generated and uploaded: {image_url}")
        
        return ImageGenerationResponse(
            image_url=image_url,
            asset_id=asset_id,
            metadata={
                **result["metadata"],
                "style": request.style
            }
        )
        
    except Exception as e:
        logger.error(f"Image generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/generate-portrait", response_model=ImageGenerationResponse)
async def generate_portrait(
    request: GeneratePortraitRequest,
    imagen: ImagenAdapter = Depends(get_imagen_adapter),
    storage: StorageService = Depends(get_storage_service)
):
    """
    Generate a portrait image optimized for lip-sync using Vertex AI Imagen.
    
    This endpoint creates front-facing portraits with clear facial features
    ideal for use with Heygen or VEO 3.
    """
    try:
        logger.info(f"Generating portrait: {request.description[:50]}...")
        
        # Generate portrait with optimized settings
        result = await imagen.generate_portrait(
            description=request.description,
            gender=request.gender,
            age=request.age,
            ethnicity=request.ethnicity,
            style=request.style,
            aspect_ratio=request.aspect_ratio
        )
        
        if not result["images"]:
            raise HTTPException(status_code=500, detail="No portrait generated")
        
        # Get the generated image (base64)
        image_base64 = result["images"][0]
        image_bytes = base64.b64decode(image_base64)
        
        # Upload to storage
        asset_id = str(uuid4())
        filename = f"portraits/{asset_id}.png"
        
        image_url = await storage.upload_bytes(
            data=image_bytes,
            filename=filename,
            content_type="image/png"
        )
        
        logger.info(f"Portrait generated and uploaded: {image_url}")
        
        return ImageGenerationResponse(
            image_url=image_url,
            asset_id=asset_id,
            metadata={
                **result["metadata"],
                "description": request.description,
                "gender": request.gender,
                "age": request.age,
                "ethnicity": request.ethnicity,
                "style": request.style,
                "optimized_for": "lip-sync"
            }
        )
        
    except Exception as e:
        logger.error(f"Portrait generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Portrait generation failed: {str(e)}")
