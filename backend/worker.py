import os
import asyncio
import time
from typing import Dict, Any, List, Callable, Optional
import uuid
import json
import functools

import redis
import backoff
from rq import Queue, Worker, Connection
from rq.job import Job as RQJob

from .db import SessionLocal
from .services.orchestrator import Orchestrator
from .utils.settings import get_settings
from .utils.logging import setup_logging, get_logger, log_job_event
from .exceptions import TransientProviderError, ProviderRateLimitError, ProviderTimeoutError

settings = get_settings()
logger = get_logger("worker")

# Configure Redis connection
redis_conn = redis.Redis.from_url(settings.REDIS_URL)

# Create RQ queues
option1_queue = Queue("option1", connection=redis_conn)
option2_queue = Queue("option2", connection=redis_conn)

# Define queue priorities (for worker processing order)
QUEUE_PRIORITY = {
    "option1": 1,  # Higher priority
    "option2": 2,  # Lower priority
}

# Helper function to get a queue by name
def get_queue(name: str) -> Queue:
    """Get a queue by name"""
    if name == "option1":
        return option1_queue
    elif name == "option2":
        return option2_queue
    else:
        raise ValueError(f"Unknown queue: {name}")

# Retry decorator for transient errors
def retry_on_transient_error(max_tries: int = 3, max_time: int = 300):
    """
    Decorator to retry functions on transient errors with exponential backoff
    
    Args:
        max_tries: Maximum number of retry attempts
        max_time: Maximum time to retry in seconds
    """
    def backoff_giveup(e):
        # Log before giving up
        logger.warning("retry_exhausted", error=str(e), error_type=type(e).__name__)
        return False  # Never give up, let max_tries handle it
    
    def backoff_handler(details):
        # Log retry attempts
        logger.info(
            "retry_attempt", 
            tries=details["tries"], 
            wait=details["wait"], 
            elapsed=details["elapsed"]
        )
    
    def decorator(func):
        @functools.wraps(func)
        @backoff.on_exception(
            backoff.expo,
            (TransientProviderError, ProviderRateLimitError, ProviderTimeoutError),
            max_tries=max_tries,
            max_time=max_time,
            on_backoff=backoff_handler,
            giveup=backoff_giveup
        )
        async def wrapped_async_func(*args, **kwargs):
            return await func(*args, **kwargs)
            
        @functools.wraps(func)
        @backoff.on_exception(
            backoff.expo,
            (TransientProviderError, ProviderRateLimitError, ProviderTimeoutError),
            max_tries=max_tries,
            max_time=max_time,
            on_backoff=backoff_handler,
            giveup=backoff_giveup
        )
        def wrapped_sync_func(*args, **kwargs):
            return func(*args, **kwargs)
            
        # Return the appropriate wrapper based on if it's async or not
        if asyncio.iscoroutinefunction(func):
            return wrapped_async_func
        return wrapped_sync_func
            
    return decorator


@retry_on_transient_error(max_tries=5, max_time=600)
async def process_job(job_id: str) -> Dict[str, Any]:
    """
    Process a job with the orchestrator
    This is the main worker function that processes jobs from the queue
    
    Uses the retry decorator to handle transient errors with exponential backoff
    """
    job_uuid = uuid.UUID(job_id)
    db = SessionLocal()
    
    try:
        log_job_event(job_id, "worker_job_start")
        
        # Initialize orchestrator with DB session
        orchestrator = Orchestrator(db)
        
        # Process the job - automatically routes to the right specialized method
        await orchestrator.process_job(job_uuid)
        
        # Get final job state
        job = orchestrator.get_job(job_uuid)
        
        log_job_event(job_id, "worker_job_complete", extra={"status": job.status})
        
        return {
            "job_id": job_id,
            "status": job.status,
            "output_url": job.output_url
        }
        
    except TransientProviderError as e:
        # Log transient error - will be retried by the decorator
        log_job_event(job_id, "worker_job_transient_error", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": True
        })
        raise  # Re-raise to trigger retry
        
    except Exception as e:
        # Log permanent error
        log_job_event(job_id, "worker_job_error", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": False
        })
        # Re-raise to let RQ handle the error
        raise
    
    finally:
        db.close()


def enqueue_job(job_id: str, job_type: str = None, queue_name: str = "option1") -> RQJob:
    """
    Enqueue a job for processing
    Returns the RQ job instance
    
    Args:
        job_id: The UUID of the job to process
        job_type: Optional job type for specialized processing ("prompt" or "audio")
        queue_name: Queue to use ("option1" or "option2"), defaults to option1 (higher priority)
    """
    if job_type:
        # Use specialized processing methods if job type is provided
        func = run_prompt_job if job_type == "prompt" else run_audio_job
    else:
        # Use default processing method
        func = process_job
    
    # Get the appropriate queue
    queue = get_queue(queue_name)
    
    logger.info(
        "enqueueing_job",
        job_id=job_id,
        job_type=job_type,
        queue=queue_name
    )
    
    return queue.enqueue(
        func,
        job_id,
        job_id=f"process-{job_id}",
        result_ttl=86400,  # 1 day
        failure_ttl=86400,  # 1 day
        timeout="30m",  # 30 minute timeout for job processing
        retry=backoff.expo,  # Use exponential backoff for RQ job retries
        max_retries=3  # Maximum number of RQ-level retries
    )


@retry_on_transient_error(max_tries=5, max_time=600)
async def run_prompt_job(job_id: str) -> Dict[str, Any]:
    """
    Process a prompt-to-lipsync job with the orchestrator
    
    Uses the retry decorator to handle transient errors with exponential backoff
    """
    job_uuid = uuid.UUID(job_id)
    db = SessionLocal()
    
    try:
        log_job_event(job_id, "worker_prompt_job_start")
        
        orchestrator = Orchestrator(db)
        await orchestrator.run_prompt_to_lipsync(job_uuid)
        
        job = orchestrator.get_job(job_uuid)
        log_job_event(job_id, "worker_job_complete", extra={"status": job.status})
        
        return {
            "job_id": job_id,
            "status": job.status,
            "output_url": job.output_url
        }
    except TransientProviderError as e:
        # Log transient error - will be retried by the decorator
        log_job_event(job_id, "worker_job_transient_error", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": True
        })
        raise  # Re-raise to trigger retry
    except Exception as e:
        log_job_event(job_id, "worker_job_error", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": False
        })
        raise
    finally:
        db.close()


@retry_on_transient_error(max_tries=5, max_time=600)
async def run_audio_job(job_id: str) -> Dict[str, Any]:
    """
    Process an audio-driven job with the orchestrator
    
    Uses the retry decorator to handle transient errors with exponential backoff
    """
    job_uuid = uuid.UUID(job_id)
    db = SessionLocal()
    
    try:
        log_job_event(job_id, "worker_audio_job_start")
        
        orchestrator = Orchestrator(db)
        await orchestrator.run_audio_driven(job_uuid)
        
        job = orchestrator.get_job(job_uuid)
        log_job_event(job_id, "worker_job_complete", extra={"status": job.status})
        
        return {
            "job_id": job_id,
            "status": job.status,
            "output_url": job.output_url
        }
    except TransientProviderError as e:
        # Log transient error - will be retried by the decorator
        log_job_event(job_id, "worker_job_transient_error", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": True
        })
        raise  # Re-raise to trigger retry
    except Exception as e:
        log_job_event(job_id, "worker_job_error", extra={
            "error": str(e),
            "error_type": type(e).__name__,
            "retryable": False
        })
        raise
    finally:
        db.close()


def start_worker(queues: Optional[List[str]] = None):
    """
    Start a worker to process jobs from the specified queues
    This is the entry point for the worker process
    
    Args:
        queues: List of queue names to process. If None, processes all queues
                in priority order (option1, option2)
    """
    # Set up logging
    setup_logging()
    
    # Default to all queues in priority order if not specified
    if queues is None:
        # Sort by priority
        queue_names = sorted(QUEUE_PRIORITY.keys(), key=lambda q: QUEUE_PRIORITY[q])
    else:
        queue_names = queues
    
    logger.info("worker_starting", queues=queue_names)
    
    with Connection(redis_conn):
        worker = Worker(queue_names)
        worker.work(with_scheduler=True)  # Enable scheduler for delayed jobs


def start_dedicated_worker(queue_name: str):
    """
    Start a worker dedicated to a single queue
    
    Args:
        queue_name: Queue to process
    """
    start_worker([queue_name])


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Start a worker process')
    parser.add_argument('--queue', '-q', help='Queue to process (option1 or option2)', 
                        choices=['option1', 'option2'])
    
    args = parser.parse_args()
    
    if args.queue:
        # Start a worker for the specified queue
        start_dedicated_worker(args.queue)
    else:
        # Start a worker for all queues in priority order
        start_worker()