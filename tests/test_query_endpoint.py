#!/usr/bin/env python3
"""
Test querying the task we just created
"""
import asyncio
import httpx
import sys
import json

sys.path.insert(0, '/workspaces/DashTests')
from backend.utils.settings import get_settings

async def test_query():
    settings = get_settings()
    task_id = "333469291581846"  # From previous test
    
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {settings.MINIMAX_API_KEY}"
    }
    
    # Try different query URL patterns
    urls = [
        f"https://api.minimax.io/v1/video_generation/{task_id}",
        f"https://api.minimax.io/v1/video_generation?task_id={task_id}",
        f"https://api.minimax.io/v1/query?task_id={task_id}",
    ]
    
    print("\n=== Testing Task Query Endpoints ===\n")
    
    for url in urls:
        print(f"Testing: {url}")
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(url, headers=headers)
                print(f"  Status: {response.status_code}")
                try:
                    result = response.json()
                    print(f"  Response: {json.dumps(result, indent=4)}")
                    if result.get('task_id'):
                        print(f"  ✓ Found task!")
                except:
                    print(f"  Text: {response.text}")
            except Exception as e:
                print(f"  Error: {e}")
        print()

if __name__ == "__main__":
    asyncio.run(test_query())
