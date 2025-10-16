"""ElevenLabs voice management endpoints"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from ..adapters.tts_elevenlabs import ElevenLabsAdapter
from ..utils.settings import get_settings
from ..utils.logging import get_logger

settings = get_settings()
logger = get_logger("routes.voices")

router = APIRouter(prefix="/voices", tags=["voices"])

# Initialize adapter
tts_adapter = ElevenLabsAdapter(mock_mode=settings.ELEVENLABS_MOCK_MODE)


# ==================== Request/Response Models ====================

class VoiceResponse(BaseModel):
    """Voice information"""
    voice_id: str
    name: str
    category: str
    labels: dict = Field(default_factory=dict)
    preview_url: Optional[str] = None
    settings: Optional[dict] = None


class VoiceDetailResponse(BaseModel):
    """Detailed voice information"""
    voice_id: str
    name: str
    category: str
    labels: dict = Field(default_factory=dict)
    settings: dict = Field(default_factory=dict)
    samples: List[dict] = Field(default_factory=list)


class CloneVoiceRequest(BaseModel):
    """Request to clone a voice"""
    name: str = Field(..., description="Name for the cloned voice")
    description: Optional[str] = Field(None, description="Optional description")
    labels: Optional[dict] = Field(None, description="Optional labels (accent, age, gender, etc)")


class CloneVoiceResponse(BaseModel):
    """Response from voice cloning"""
    voice_id: str
    name: str
    message: str = "Voice cloned successfully"


class SynthesizeRequest(BaseModel):
    """Request to synthesize speech"""
    text: str = Field(..., description="Text to synthesize", min_length=1, max_length=5000)
    voice_id: str = Field(..., description="Voice ID to use")
    model_id: str = Field(default="eleven_turbo_v2", description="Model to use")
    stability: float = Field(default=0.65, ge=0.0, le=1.0)
    similarity_boost: float = Field(default=0.75, ge=0.0, le=1.0)
    style: float = Field(default=0.0, ge=0.0, le=1.0)
    speaker_boost: bool = Field(default=True)
    output_format: str = Field(default="mp3_44100_128")
    seed: Optional[int] = Field(None, description="Seed for reproducible generation")
    optimize_streaming_latency: int = Field(default=0, ge=0, le=4)


class SynthesizeResponse(BaseModel):
    """Response from synthesis"""
    audio_url: str
    audio_key: str
    size_bytes: int
    format: str
    model: str


class SubscriptionInfoResponse(BaseModel):
    """Subscription information"""
    tier: str
    character_count: int
    character_limit: int
    can_extend_character_limit: bool


class ModelsResponse(BaseModel):
    """Available models"""
    models: dict


class FormatsResponse(BaseModel):
    """Available output formats"""
    formats: dict


# ==================== Endpoints ====================

@router.get("/", response_model=List[VoiceResponse])
async def list_voices(filter_name: Optional[str] = None):
    """
    List all available voices.
    
    Args:
        filter_name: Optional filter for voice names
        
    Returns:
        List of voices
    """
    try:
        voices = await tts_adapter.list_voices(filter_name=filter_name)
        logger.info("list_voices_success", count=len(voices), filter=filter_name)
        return voices
    except Exception as e:
        logger.error("list_voices_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list voices: {str(e)}")


@router.get("/{voice_id}", response_model=VoiceDetailResponse)
async def get_voice(voice_id: str):
    """
    Get detailed information about a specific voice.
    
    Args:
        voice_id: The voice ID to retrieve
        
    Returns:
        Voice details
    """
    try:
        voice = await tts_adapter.get_voice(voice_id)
        logger.info("get_voice_success", voice_id=voice_id)
        return voice
    except Exception as e:
        logger.error("get_voice_error", voice_id=voice_id, error=str(e))
        raise HTTPException(status_code=404, detail=f"Voice not found: {str(e)}")


@router.post("/clone", response_model=CloneVoiceResponse)
async def clone_voice(
    name: str = Form(...),
    description: Optional[str] = Form(None),
    files: List[UploadFile] = File(..., description="Audio samples (1-5 files)")
):
    """
    Clone a voice from audio samples.
    
    Args:
        name: Name for the cloned voice
        description: Optional description
        files: List of audio files (MP3, WAV, M4A)
        
    Returns:
        New voice ID
    """
    try:
        # Validate file count
        if len(files) < 1:
            raise HTTPException(status_code=400, detail="At least 1 audio file required")
        if len(files) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 audio files allowed")
        
        # Read file contents
        file_contents = []
        for file in files:
            content = await file.read()
            file_contents.append(content)
            logger.info("clone_voice_file", filename=file.filename, size=len(content))
        
        # Clone voice
        voice_id = await tts_adapter.clone_voice(
            name=name,
            files=file_contents,
            description=description
        )
        
        logger.info("clone_voice_success", voice_id=voice_id, name=name, file_count=len(files))
        
        return CloneVoiceResponse(
            voice_id=voice_id,
            name=name,
            message=f"Voice '{name}' cloned successfully from {len(files)} samples"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("clone_voice_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to clone voice: {str(e)}")


@router.delete("/{voice_id}")
async def delete_voice(voice_id: str):
    """
    Delete a cloned voice.
    
    Args:
        voice_id: The voice ID to delete
        
    Returns:
        Success message
    """
    try:
        success = await tts_adapter.delete_voice(voice_id)
        
        if success:
            logger.info("delete_voice_success", voice_id=voice_id)
            return {"message": f"Voice {voice_id} deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete voice")
            
    except Exception as e:
        logger.error("delete_voice_error", voice_id=voice_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete voice: {str(e)}")


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_speech(request: SynthesizeRequest):
    """
    Synthesize speech from text.
    
    Args:
        request: Synthesis parameters
        
    Returns:
        Audio URL and metadata
    """
    try:
        from ..services.storage import StorageService
        
        # Generate audio
        audio_bytes = await tts_adapter.synthesize(
            text=request.text,
            voice_id=request.voice_id,
            model_id=request.model_id,
            stability=request.stability,
            similarity_boost=request.similarity_boost,
            style=request.style,
            speaker_boost=request.speaker_boost,
            output_format=request.output_format,
            seed=request.seed,
            optimize_streaming_latency=request.optimize_streaming_latency
        )
        
        # Save to storage
        storage = StorageService()
        
        # Determine file extension from format
        if request.output_format.startswith("mp3"):
            ext = "mp3"
            content_type = "audio/mpeg"
        elif request.output_format.startswith("pcm"):
            ext = "pcm"
            content_type = "audio/pcm"
        elif request.output_format.startswith("ulaw"):
            ext = "ulaw"
            content_type = "audio/basic"
        else:
            ext = "mp3"
            content_type = "audio/mpeg"
        
        audio_key = storage.upload_bytes(
            audio_bytes,
            filename=f"tts-{request.voice_id[:8]}-{request.seed or 'random'}.{ext}",
            content_type=content_type
        )
        
        # Get presigned URL (24 hours)
        audio_url = storage.get_presigned_url(audio_key, expires_in=86400)
        
        logger.info("synthesize_success", 
                   voice_id=request.voice_id, 
                   model=request.model_id,
                   text_len=len(request.text),
                   audio_size=len(audio_bytes),
                   audio_key=audio_key)
        
        return SynthesizeResponse(
            audio_url=audio_url,
            audio_key=audio_key,
            size_bytes=len(audio_bytes),
            format=request.output_format,
            model=request.model_id
        )
        
    except Exception as e:
        logger.error("synthesize_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to synthesize: {str(e)}")


@router.get("/subscription/info", response_model=SubscriptionInfoResponse)
async def get_subscription_info():
    """
    Get subscription information including usage.
    
    Returns:
        Subscription details
    """
    try:
        info = await tts_adapter.get_subscription_info()
        logger.info("subscription_info_success", tier=info.get("tier"))
        return info
    except Exception as e:
        logger.error("subscription_info_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get subscription info: {str(e)}")


@router.get("/models/available", response_model=ModelsResponse)
async def get_available_models():
    """
    Get list of available models.
    
    Returns:
        Available models
    """
    from ..adapters.tts_elevenlabs import MODELS
    return ModelsResponse(models=MODELS)


@router.get("/formats/available", response_model=FormatsResponse)
async def get_available_formats():
    """
    Get list of available output formats.
    
    Returns:
        Available formats
    """
    from ..adapters.tts_elevenlabs import OUTPUT_FORMATS
    return FormatsResponse(formats=OUTPUT_FORMATS)
