import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import prometheus_client

from .db import init_db
from .utils.settings import get_settings
from .utils.logging import setup_logging, log_request_info, get_logger
from .utils.prometheus import (
    jobs_created_total, jobs_failed_total, 
    provider_latency_ms, postfx_runtime_s
)
from .exceptions import LipSyncException, ProviderError
from .routes import lipsync, jobs, uploads, webhooks, prompts

settings = get_settings()
logger = get_logger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for the application
    """
    # Set up logging
    setup_logging()
    
    # Initialize database
    init_db()
    
    logger.info("application_startup", message="Starting AI Lip-Sync API")
    yield
    logger.info("application_shutdown", message="Shutting down AI Lip-Sync API")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API for AI-powered lip-sync videos",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    # Allow frontend origin as requested
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Middleware for logging and metrics
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    # Generate request ID and log request start
    request_id = log_request_info(request)
    
    # Set request start time for latency tracking
    start_time = time.time()
    
    try:
        response = await call_next(request)
        
        # Calculate request duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Capture metrics for successful job creation (detect from path and status)
        if request.url.path.endswith("/jobs") and request.method == "POST" and response.status_code == 201:
            jobs_created_total.labels(method="api").inc()
        
        # Log request completion with structured data
        logger.info(
            "request_completed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms
        )
        
        return response
    except Exception as e:
        # Calculate duration even for failed requests
        duration_ms = (time.time() - start_time) * 1000
        
        # Log the exception - will be handled by exception handlers
        logger.info(
            "request_failed",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            duration_ms=duration_ms,
            error_type=e.__class__.__name__
        )
        
        # Let the exception propagate to appropriate handlers
        raise


# Exception handler for application exceptions
@app.exception_handler(LipSyncException)
async def lipsync_exception_handler(request: Request, exc: LipSyncException):
    """Handle LipSync application exceptions"""
    # Add request ID if available
    if hasattr(request.state, "request_id"):
        exc.request_id = request.state.request_id
        
    # Extract engine information for metrics if available in detail
    engine = None
    if exc.detail and "engine" in exc.detail:
        engine = exc.detail["engine"]
    elif exc.detail and "provider" in exc.detail:
        engine = exc.detail["provider"]
    
    # Increment failure metrics for provider errors
    if isinstance(exc, ProviderError) and engine:
        jobs_failed_total.labels(engine=engine).inc()
        
    # Log error with structured data
    logger.error(
        "api_error",
        request_id=exc.request_id,
        error_code=exc.code,
        error_message=exc.message,
        error_type=exc.__class__.__name__,
        path=request.url.path,
        detail=exc.detail
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )

# Handle validation errors from FastAPI
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    # Create generic error response
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    
    # Log unexpected error
    logger.exception(
        "unhandled_error",
        request_id=request_id,
        error_type=exc.__class__.__name__,
        path=request.url.path,
        error_message=str(exc)
    )
    
    # Return generic error response
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "request_id": request_id
        }
    )


# Mount API routes
app.include_router(lipsync.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(webhooks.router, prefix="/api/v1")
app.include_router(prompts.router, prefix="/api/v1")


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    if not settings.METRICS_ENABLED:
        return Response(content="Metrics disabled", media_type="text/plain")
        
    return Response(
        content=prometheus_client.generate_latest(),
        media_type="text/plain"
    )