"""
Screenplay routes for PDF upload and management
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from sqlalchemy import desc
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import UUID

from ..db import get_db
from ..models.job import Screenplay
from ..utils.logging import get_logger
from ..utils.pdf_processor import PDFProcessor

router = APIRouter(prefix="/screenplays", tags=["screenplays"])
logger = get_logger("screenplay_routes")


# Pydantic schemas for request/response
class ScreenplayCreate(BaseModel):
    """Request to create a new screenplay record"""
    title: str = Field(..., min_length=1, max_length=255, description="Title of the screenplay")
    filename: str = Field(..., description="Original filename")
    pdf_url: str = Field(..., description="URL to the uploaded PDF file")
    file_size_bytes: Optional[int] = Field(None, description="File size in bytes")


class ScreenplayResponse(BaseModel):
    """Response model for screenplay"""
    id: str
    title: str
    filename: str
    pdf_url: str
    text_content: Optional[str] = None
    page_count: Optional[int] = None
    file_size_bytes: Optional[int] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ScreenplayListResponse(BaseModel):
    """Response for list of screenplays"""
    screenplays: List[ScreenplayResponse]
    total: int


class TextSelectionRequest(BaseModel):
    """Request to extract selected text for prompt generation"""
    screenplay_id: str = Field(..., description="ID of the screenplay")
    selected_text: str = Field(..., min_length=1, description="Selected text from the screenplay")


class TextSelectionResponse(BaseModel):
    """Response with processed text for prompt"""
    screenplay_id: str
    selected_text: str
    processed_prompt: str


@router.post("", response_model=ScreenplayResponse, status_code=201)
@router.post("/", response_model=ScreenplayResponse, status_code=201)
async def create_screenplay(
    request: ScreenplayCreate,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new screenplay record and extract text from PDF
    
    This endpoint should be called after the PDF has been uploaded to storage
    via the /uploads/presign endpoint. It will download the PDF, extract text,
    and store the screenplay metadata in the database.
    """
    try:
        # Extract text from PDF
        pdf_processor = PDFProcessor()
        text_content, page_count = await pdf_processor.extract_text_from_url(request.pdf_url)
        
        # Create screenplay record
        screenplay = Screenplay(
            title=request.title,
            filename=request.filename,
            pdf_url=request.pdf_url,
            text_content=text_content,
            page_count=page_count,
            file_size_bytes=request.file_size_bytes
        )
        
        db.add(screenplay)
        db.commit()
        db.refresh(screenplay)
        
        logger.info(
            "screenplay_created",
            screenplay_id=str(screenplay.id),
            title=screenplay.title,
            page_count=page_count,
            request_id=getattr(req.state, "request_id", None)
        )
        
        return ScreenplayResponse(
            id=str(screenplay.id),
            title=screenplay.title,
            filename=screenplay.filename,
            pdf_url=screenplay.pdf_url,
            text_content=screenplay.text_content,
            page_count=screenplay.page_count,
            file_size_bytes=screenplay.file_size_bytes,
            created_at=screenplay.created_at.isoformat(),
            updated_at=screenplay.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(
            "screenplay_creation_failed",
            error=str(e),
            request_id=getattr(req.state, "request_id", None)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create screenplay: {str(e)}"
        )


@router.get("", response_model=ScreenplayListResponse)
@router.get("/", response_model=ScreenplayListResponse)
async def list_screenplays(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    List all screenplays, ordered by creation date (newest first)
    """
    try:
        # Get total count
        total = db.query(Screenplay).count()
        
        # Get screenplays with pagination
        screenplays = db.query(Screenplay)\
            .order_by(desc(Screenplay.created_at))\
            .offset(skip)\
            .limit(limit)\
            .all()
        
        screenplay_responses = [
            ScreenplayResponse(
                id=str(s.id),
                title=s.title,
                filename=s.filename,
                pdf_url=s.pdf_url,
                text_content=s.text_content,
                page_count=s.page_count,
                file_size_bytes=s.file_size_bytes,
                created_at=s.created_at.isoformat(),
                updated_at=s.updated_at.isoformat()
            )
            for s in screenplays
        ]
        
        return ScreenplayListResponse(
            screenplays=screenplay_responses,
            total=total
        )
        
    except Exception as e:
        logger.error("screenplay_list_failed", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list screenplays: {str(e)}"
        )


@router.get("/{screenplay_id}", response_model=ScreenplayResponse)
@router.get("/{screenplay_id}/", response_model=ScreenplayResponse)
async def get_screenplay(
    screenplay_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific screenplay by ID
    """
    screenplay = db.query(Screenplay).filter(Screenplay.id == screenplay_id).first()
    
    if not screenplay:
        raise HTTPException(
            status_code=404,
            detail=f"Screenplay with id {screenplay_id} not found"
        )
    
    return ScreenplayResponse(
        id=str(screenplay.id),
        title=screenplay.title,
        filename=screenplay.filename,
        pdf_url=screenplay.pdf_url,
        text_content=screenplay.text_content,
        page_count=screenplay.page_count,
        file_size_bytes=screenplay.file_size_bytes,
        created_at=screenplay.created_at.isoformat(),
        updated_at=screenplay.updated_at.isoformat()
    )


@router.delete("/{screenplay_id}", response_model=None)
@router.delete("/{screenplay_id}/", response_model=None)
async def delete_screenplay(
    screenplay_id: str,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Delete a screenplay
    """
    screenplay = db.query(Screenplay).filter(Screenplay.id == screenplay_id).first()
    
    if not screenplay:
        raise HTTPException(
            status_code=404,
            detail=f"Screenplay with id {screenplay_id} not found"
        )
    
    db.delete(screenplay)
    db.commit()
    
    logger.info(
        "screenplay_deleted",
        screenplay_id=str(screenplay_id),
        request_id=getattr(req.state, "request_id", None)
    )
    
    return None


@router.post("/text-selection", response_model=TextSelectionResponse)
async def process_text_selection(
    request: TextSelectionRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Process selected text from screenplay to create a prompt
    
    This endpoint receives text selected by the user from the screenplay viewer
    and can optionally process it (e.g., clean up, format) before using it as a prompt.
    """
    try:
        # Verify screenplay exists
        screenplay = db.query(Screenplay).filter(
            Screenplay.id == UUID(request.screenplay_id)
        ).first()
        
        if not screenplay:
            raise HTTPException(
                status_code=404,
                detail=f"Screenplay with id {request.screenplay_id} not found"
            )
        
        # Process the selected text (basic cleanup)
        processed_text = request.selected_text.strip()
        
        # Remove excessive whitespace
        processed_text = " ".join(processed_text.split())
        
        logger.info(
            "text_selection_processed",
            screenplay_id=request.screenplay_id,
            text_length=len(processed_text),
            request_id=getattr(req.state, "request_id", None)
        )
        
        return TextSelectionResponse(
            screenplay_id=request.screenplay_id,
            selected_text=request.selected_text,
            processed_prompt=processed_text
        )
        
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid screenplay ID format"
        )
    except Exception as e:
        logger.error(
            "text_selection_processing_failed",
            error=str(e),
            request_id=getattr(req.state, "request_id", None)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process text selection: {str(e)}"
        )
