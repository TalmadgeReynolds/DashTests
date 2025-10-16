"""
WebSocket routes for real-time updates
"""
import socketio
from fastapi import FastAPI

from ..utils.logging import get_logger
from ..services.websocket_utils import set_emit_function

# Create a Socket.IO server instance
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        'http://localhost:5173',
        'http://127.0.0.1:5173',
        'http://localhost:8000',
        'http://127.0.0.1:8000',
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        '*'  # Allow all origins in development
    ],
    logger=True,
    engineio_logger=True
)

# Create an ASGI app from the Socket.IO server
socket_app = socketio.ASGIApp(
    socketio_server=sio,
    socketio_path='/api/v1/ws'  # Match the path in frontend
)

logger = get_logger("websocket")

# Socket.IO event handlers
@sio.event
async def connect(sid, environ):
    """Handle new Socket.IO connection"""
    logger.info("websocket_connect", client_id=sid)


@sio.event
async def disconnect(sid):
    """Handle Socket.IO disconnection"""
    logger.info("websocket_disconnect", client_id=sid)


# Function to emit job updates to connected clients
async def emit_job_update(job_id: str, status: str, progress: float = None):
    """Emit job update to all connected clients"""
    logger.info(
        "job_update_emitted", 
        job_id=job_id,
        status=status,
        progress=progress
    )
    
    await sio.emit('job_update', {
        'job_id': job_id,
        'status': status,
        'progress': progress
    })


# Mount function for FastAPI
def setup_socketio(app: FastAPI):
    """Mount Socket.IO to FastAPI app"""
    # Register the emit function
    set_emit_function(emit_job_update)
    
    # Mount the Socket.IO app at the root path
    # The actual Socket.IO path is handled by socketio_path in ASGIApp config
    app.mount("/", socket_app)
    
    return app