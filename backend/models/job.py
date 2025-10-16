from sqlalchemy import Column, String, DateTime, Boolean, Integer, JSON, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()


class Job(Base):
    """Database model for lipsync jobs"""
    __tablename__ = "jobs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    method = Column(String, nullable=False, index=True)  # prompt, audio
    status = Column(String, nullable=False, default="created", index=True)
    name = Column(String, nullable=True)
    engine = Column(String, nullable=False, default="veo3", index=True)
    provider_job_id = Column(String, nullable=True, unique=True, index=True)
    
    # Request parameters
    prompt = Column(Text, nullable=True)  # For prompt-based jobs
    voice_id = Column(String, nullable=True)  # For prompt jobs only
    
    # Processing metadata
    error = Column(String, nullable=True)
    meta = Column(JSON, nullable=True)
    
    # Billing and cost information
    generation_credits = Column(Integer, nullable=True)
    postfx_minutes = Column(Integer, nullable=True)
    total_estimate_cents = Column(Integer, nullable=True)
    
    # Webhook configuration
    webhook_url = Column(String, nullable=True)
    webhook_secret = Column(String, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    assets = relationship("Asset", back_populates="job", cascade="all, delete-orphan")
    
    # Add composite indexes at the table level
    __table_args__ = (
        Index('idx_job_status_created', status, created_at),
    )
    
    @property
    def is_terminal(self) -> bool:
        """Return True if the job is in a terminal state (DONE or ERROR)"""
        return self.status in ("DONE", "ERROR")


class Asset(Base):
    """Database model for assets associated with jobs"""
    __tablename__ = "assets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id", ondelete="CASCADE"), nullable=False, index=True)
    
    kind = Column(String, nullable=False, index=True)  # IMAGE, AUDIO, VIDEO
    url = Column(String, nullable=False)
    mime = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    
    # Optional metadata
    meta = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="assets")
    
    def __repr__(self):
        return f"<Asset id={self.id} kind={self.kind} job_id={self.job_id}>"


class Screenplay(Base):
    """Database model for uploaded screenplays"""
    __tablename__ = "screenplays"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    
    # Storage URLs
    pdf_url = Column(String, nullable=False)  # URL to the uploaded PDF file
    
    # Extracted text content from PDF
    text_content = Column(Text, nullable=True)  # Full text extracted from PDF
    
    # Metadata
    page_count = Column(Integer, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    # meta field is defined in the migration but not used in the application
    # meta = Column(JSON, nullable=True)  # Additional metadata like author, format info, etc.
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Screenplay id={self.id} title={self.title}>"