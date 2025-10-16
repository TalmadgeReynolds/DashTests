"""
Test WebSocket update endpoint
"""
import requests
import uuid

# Test job ID (replace with a real job ID if available)
job_id = str(uuid.uuid4())

# Send a test update
response = requests.post(
    f"http://localhost:8000/api/v1/websocket/test/{job_id}",
    params={"status": "RUNNING", "progress": 0.75}
)

print(f"Response status code: {response.status_code}")
print(f"Response body: {response.json()}")