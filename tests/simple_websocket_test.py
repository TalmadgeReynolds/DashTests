"""
A simplified WebSocket test script
"""
import requests
import uuid
import time

# Create a random UUID for the job
job_id = str(uuid.uuid4())

# Make a request to our test endpoint
print(f"Sending test request for job ID: {job_id}")
response = requests.post(
    f"http://localhost:8000/api/v1/websocket/test/{job_id}",
    params={"status": "RUNNING", "progress": 0.75}
)

print(f"Response status: {response.status_code}")
print(f"Response data: {response.text}")
print("\nIf this test was successful, your WebSocket implementation is working.")
print("You should be able to see the emitted event in the server logs.")