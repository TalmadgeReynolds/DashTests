import json
import logging
import time
import uuid
from typing import Dict, Any, Optional

import structlog
from fastapi import Request

from .settings import get_settings

settings = get_settings()


def setup_logging():
    """Configure structured JSON logging"""
    log_level = settings.LOG_LEVEL.upper() if hasattr(settings, 'LOG_LEVEL') else "INFO"
    
    # Convert string log level to actual log level
    level = getattr(logging, log_level, logging.INFO)
    
    # Configure basic logging
    logging.basicConfig(level=level)
    
    # Configure structlog with enhanced processors
    structlog.configure(
        processors=[
            # Add context from context vars
            structlog.contextvars.merge_contextvars,
            # Add log level
            structlog.processors.add_log_level,
            # Add timestamp in ISO format
            structlog.processors.TimeStamper(fmt="iso"),
            # Add hostname
            structlog.processors.add_log_level,
            # Add caller info (file, line number)
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                    structlog.processors.CallsiteParameter.FUNC_NAME,
                ],
            ),
            # Format any exceptions
            structlog.processors.format_exc_info,
            # Render as JSON for structured logging
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        # Cache logger instances
        cache_logger_on_first_use=True,
    )


def get_logger(name: str):
    """Get a structured logger with the given name"""
    return structlog.get_logger(name)


def log_request_info(request: Request) -> str:
    """Generate a unique request ID and log basic request info"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.start_time = time.time()
    
    logger = get_logger("api")
    logger.info(
        "request_started",
        request_id=request_id,
        method=request.method,
        url=str(request.url),
    )
    
    return request_id


def log_job_event(job_id: str, event: str, provider_job_id: Optional[str] = None, 
                 extra: Dict[str, Any] = None, latency_ms: Optional[float] = None):
    """Log job-related events with consistent structure"""
    logger = get_logger("job")
    
    log_data = {
        "job_id": job_id,
        "event": event,
    }
    
    if provider_job_id:
        log_data["provider_job_id"] = provider_job_id
        
    if latency_ms is not None:
        log_data["latency_ms"] = latency_ms
        
    if extra:
        log_data.update(extra)
    
    logger.info(**log_data)


def log_provider_call(engine: str, operation: str, job_id: Optional[str] = None, 
                      provider_job_id: Optional[str] = None, latency_ms: Optional[float] = None,
                      success: bool = True, error: Optional[str] = None):
    """
    Log provider API calls with metrics tracking
    
    Args:
        engine: Provider name (e.g., 'heygen', 'veo')
        operation: Operation name (e.g., 'create_job', 'check_status')
        job_id: Our internal job ID (optional)
        provider_job_id: Provider's job ID (optional)
        latency_ms: API call latency in milliseconds
        success: Whether the call succeeded
        error: Error message if the call failed
    """
    from .prometheus import provider_latency_ms, jobs_failed_total
    
    logger = get_logger("provider")
    
    log_data = {
        "engine": engine,
        "operation": operation,
        "success": success,
    }
    
    # Add optional fields
    if job_id:
        log_data["job_id"] = job_id
    
    if provider_job_id:
        log_data["provider_job_id"] = provider_job_id
        
    if latency_ms is not None:
        log_data["latency_ms"] = latency_ms
        
        # Update Prometheus metrics
        provider_latency_ms.labels(engine=engine).observe(latency_ms)
        
    if error:
        log_data["error"] = error
        
        # Update failure metrics
        if not success:
            jobs_failed_total.labels(engine=engine).inc()
    
    if success:
        logger.info("provider_call", **log_data)
    else:
        logger.error("provider_call_failed", **log_data)


def log_postfx_operation(operation: str, duration_s: float, job_id: Optional[str] = None, 
                        success: bool = True, error: Optional[str] = None):
    """
    Log post-processing operations with metrics tracking
    
    Args:
        operation: Operation name (e.g., 'normalize', 'add_padding')
        duration_s: Operation duration in seconds
        job_id: Our internal job ID (optional)
        success: Whether the operation succeeded
        error: Error message if the operation failed
    """
    from .prometheus import postfx_runtime_s
    
    logger = get_logger("postfx")
    
    log_data = {
        "operation": operation,
        "duration_s": duration_s,
        "success": success,
    }
    
    # Add optional fields
    if job_id:
        log_data["job_id"] = job_id
        
    if error:
        log_data["error"] = error
    
    # Update Prometheus metrics
    postfx_runtime_s.labels(operation=operation).observe(duration_s)
    
    if success:
        logger.info("postfx_operation", **log_data)
    else:
        logger.error("postfx_operation_failed", **log_data)