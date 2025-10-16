"""
Test WebSocket functionality
"""
import asyncio
import socketio

# Create a Socket.IO client
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('WebSocket connected!')

@sio.event
async def disconnect():
    print('WebSocket disconnected!')

@sio.event
async def job_update(data):
    print(f'Job update received: {data}')

async def main():
    try:
        # Connect to the WebSocket server
        await sio.connect(
            'http://localhost:8000', 
            socketio_path='/api/v1/ws',
            headers={'Origin': 'http://localhost:5173'}
        )
        
        print('Connected to WebSocket server, waiting for updates...')
        
        # Keep the connection open for a while
        await asyncio.sleep(30)
        
        # Disconnect
        await sio.disconnect()
    except Exception as e:
        print(f"Error connecting to WebSocket server: {e}")

if __name__ == "__main__":
    asyncio.run(main())