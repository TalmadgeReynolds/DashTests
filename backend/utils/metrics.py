"""
Metrics utilities for Prometheus monitoring
"""
import time
import asyncio
from typing import Callable, Any, Optional
import functools

from .logging import log_postfx_operation, log_provider_call
from .prometheus import jobs_created_total, jobs_failed_total, provider_latency_ms, postfx_runtime_s


def track_provider_latency(engine: str, operation: str):
    """
    Decorator to track provider API call latency and update Prometheus metrics
    
    Args:
        engine: Provider name (e.g., 'heygen', 'veo')
        operation: Operation name (e.g., 'create_job', 'check_status')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            job_id = kwargs.get("job_id")
            provider_job_id = kwargs.get("provider_job_id")
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                # Extract provider_job_id from result if it's returned and not provided
                if not provider_job_id and isinstance(result, dict) and "provider_job_id" in result:
                    provider_job_id = result["provider_job_id"]
                
                # Log successful provider call with latency
                latency_ms = (time.time() - start_time) * 1000
                log_provider_call(
                    engine=engine,
                    operation=operation,
                    job_id=job_id,
                    provider_job_id=provider_job_id,
                    latency_ms=latency_ms,
                    success=True
                )
                
                return result
            except Exception as e:
                # Log failed provider call with latency
                latency_ms = (time.time() - start_time) * 1000
                log_provider_call(
                    engine=engine,
                    operation=operation,
                    job_id=job_id,
                    provider_job_id=provider_job_id,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            job_id = kwargs.get("job_id")
            provider_job_id = kwargs.get("provider_job_id")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Extract provider_job_id from result if it's returned and not provided
                if not provider_job_id and isinstance(result, dict) and "provider_job_id" in result:
                    provider_job_id = result["provider_job_id"]
                
                # Log successful provider call with latency
                latency_ms = (time.time() - start_time) * 1000
                log_provider_call(
                    engine=engine,
                    operation=operation,
                    job_id=job_id,
                    provider_job_id=provider_job_id,
                    latency_ms=latency_ms,
                    success=True
                )
                
                return result
            except Exception as e:
                # Log failed provider call with latency
                latency_ms = (time.time() - start_time) * 1000
                log_provider_call(
                    engine=engine,
                    operation=operation,
                    job_id=job_id,
                    provider_job_id=provider_job_id,
                    latency_ms=latency_ms,
                    success=False,
                    error=str(e)
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def track_postfx_runtime(operation: str):
    """
    Decorator to track post-processing operation runtime and update Prometheus metrics
    
    Args:
        operation: Operation name (e.g., 'normalize', 'add_padding')
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            job_id = kwargs.get("job_id")
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                
                # Log successful operation with duration
                duration_s = time.time() - start_time
                log_postfx_operation(
                    operation=operation,
                    duration_s=duration_s,
                    job_id=job_id,
                    success=True
                )
                
                return result
            except Exception as e:
                # Log failed operation with duration
                duration_s = time.time() - start_time
                log_postfx_operation(
                    operation=operation,
                    duration_s=duration_s,
                    job_id=job_id,
                    success=False,
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            job_id = kwargs.get("job_id")
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                
                # Log successful operation with duration
                duration_s = time.time() - start_time
                log_postfx_operation(
                    operation=operation,
                    duration_s=duration_s,
                    job_id=job_id,
                    success=True
                )
                
                return result
            except Exception as e:
                # Log failed operation with duration
                duration_s = time.time() - start_time
                log_postfx_operation(
                    operation=operation,
                    duration_s=duration_s,
                    job_id=job_id,
                    success=False,
                    error=str(e)
                )
                raise
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator