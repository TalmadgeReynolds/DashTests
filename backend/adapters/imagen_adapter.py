"""
Vertex AI Imagen adapter for image generation.

Provides functionality to generate portrait images using Google's Imagen model.
"""
import httpx
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ImagenAdapter:
    """Adapter for Vertex AI Imagen image generation"""
    
    def __init__(self):
        self.api_key = os.getenv("VERTEX_API_KEY")
        if not self.api_key:
            raise ValueError("VERTEX_API_KEY environment variable not set")
        
        # Vertex AI Imagen endpoint
        self.project_id = os.getenv("VERTEX_PROJECT_ID", "")
        self.location = os.getenv("VERTEX_LOCATION", "us-central1")
        
        # Use Imagen API endpoint
        self.base_url = f"https://{self.location}-aiplatform.googleapis.com/v1/projects/{self.project_id}/locations/{self.location}/publishers/google/models/imagen-3.0-generate-001:predict"
        
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        aspect_ratio: str = "1:1",
        num_images: int = 1,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate an image using Vertex AI Imagen.
        
        Args:
            prompt: Text description of the image to generate
            negative_prompt: What to avoid in the image
            aspect_ratio: Image aspect ratio (1:1, 16:9, 9:16, etc.)
            num_images: Number of images to generate (1-4)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing:
                - images: List of base64-encoded images
                - metadata: Generation metadata
        """
        logger.info(f"Generating image with Imagen: prompt='{prompt[:50]}...'")
        
        # Build request payload
        payload = {
            "instances": [
                {
                    "prompt": prompt
                }
            ],
            "parameters": {
                "sampleCount": num_images,
                "aspectRatio": aspect_ratio,
                "safetyFilterLevel": "block_some",
                "personGeneration": "allow_adult"
            }
        }
        
        if negative_prompt:
            payload["instances"][0]["negativePrompt"] = negative_prompt
        
        # Add optional parameters
        if "guidance_scale" in kwargs:
            payload["parameters"]["guidanceScale"] = kwargs["guidance_scale"]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(
                    self.base_url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Imagen generation successful")
                
                # Extract images from response
                images = []
                if "predictions" in result:
                    for pred in result["predictions"]:
                        if "bytesBase64Encoded" in pred:
                            images.append(pred["bytesBase64Encoded"])
                
                return {
                    "images": images,
                    "metadata": {
                        "prompt": prompt,
                        "aspect_ratio": aspect_ratio,
                        "model": "imagen-3.0",
                        "num_generated": len(images)
                    }
                }
                
            except httpx.HTTPStatusError as e:
                logger.error(f"Imagen API error: {e.response.status_code} - {e.response.text}")
                raise Exception(f"Imagen generation failed: {e.response.text}")
            except Exception as e:
                logger.error(f"Imagen generation error: {str(e)}")
                raise
    
    async def generate_portrait(
        self,
        description: str,
        gender: Optional[str] = None,
        age: Optional[str] = None,
        ethnicity: Optional[str] = None,
        style: str = "photorealistic",
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate a portrait image optimized for lip-sync.
        
        Args:
            description: Basic description of the person
            gender: Gender (male, female, non-binary)
            age: Age description (young, middle-aged, elderly)
            ethnicity: Ethnicity description
            style: Image style (photorealistic, cinematic, professional)
            **kwargs: Additional parameters
            
        Returns:
            Dict containing generated image data
        """
        # Build optimized prompt for lip-sync portraits
        prompt_parts = []
        
        # Base style
        if style == "photorealistic":
            prompt_parts.append("Professional headshot portrait photograph,")
        elif style == "cinematic":
            prompt_parts.append("Cinematic portrait with film lighting,")
        elif style == "professional":
            prompt_parts.append("Studio portrait with professional lighting,")
        
        # Add demographic details
        if age:
            prompt_parts.append(f"{age}")
        if gender:
            prompt_parts.append(f"{gender}")
        if ethnicity:
            prompt_parts.append(f"{ethnicity}")
        
        # Add description
        prompt_parts.append(description)
        
        # Lip-sync optimization guidance
        prompt_parts.append("front-facing, neutral expression, clear facial features,")
        prompt_parts.append("soft even lighting, shallow depth of field,")
        prompt_parts.append("high detail face, professional photo quality")
        
        prompt = " ".join(prompt_parts)
        
        # Negative prompt for lip-sync
        negative_prompt = (
            "profile view, side angle, occluded face, sunglasses, mask, "
            "hand covering mouth, extreme expression, blurry, low quality, "
            "multiple faces, distorted features"
        )
        
        logger.info(f"Generating portrait for lip-sync: {prompt[:100]}...")
        
        return await self.generate_image(
            prompt=prompt,
            negative_prompt=negative_prompt,
            aspect_ratio=kwargs.get("aspect_ratio", "1:1"),
            num_images=1,
            **kwargs
        )
