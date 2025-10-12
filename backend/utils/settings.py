from pydantic_settings import BaseSettings
from typing import Optional, Dict, Any
from functools import lru_cache


class Settings(BaseSettings):
    # App config
    APP_NAME: str = "AI Lip-Sync API"
    DEBUG: bool = False
    
    # Global mock mode flag - overrides all provider-specific flags
    MOCK_PROVIDERS: bool = True
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/lipsync"
    
    # Redis queue
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Storage (S3 or MinIO)
    STORAGE_ENDPOINT: str = "minio:9000"
    STORAGE_ACCESS_KEY: str = "minioadmin"
    STORAGE_SECRET_KEY: str = "minioadmin"
    STORAGE_BUCKET: str = "lipsync"
    STORAGE_USE_SSL: bool = False  # Set to True for production
    STORAGE_PUBLIC_ENDPOINT: str = "http://localhost:9000"  # Public-facing URL for generated URLs
    
    # Provider API keys (set to None to use mock mode)
    VEO3_API_KEY: Optional[str] = None
    VEO3_MOCK_MODE: bool = True
    
    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_MOCK_MODE: bool = True
    
    HEYGEN_API_KEY: Optional[str] = None
    HEYGEN_MOCK_MODE: bool = True
    
    # Webhook verification secrets
    WEBHOOK_SECRET_HEYGEN: str = "test-webhook-secret"
    
    # Post-FX settings
    POSTFX_ENABLED: bool = True
    POSTFX_MOCK_MODE: bool = True
    POSTFX_GPU_AVAILABLE: bool = False  # Set to True if GPU is available for RIFE/Real-ESRGAN
    POSTFX_TEMP_DIR: str = "/tmp/postfx"
    
    # Cost model defaults
    COST_GENERATION_CREDITS_VEO3: float = 10.0
    COST_GENERATION_CREDITS_HEYGEN: float = 8.0
    COST_POSTFX_CENTS_PER_MINUTE: float = 5.0
    
    # Metrics
    METRICS_ENABLED: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    return Settings()