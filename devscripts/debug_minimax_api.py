#!/usr/bin/env python3
"""
Debug MiniMax API request
"""
import asyncio
import httpx
import sys
import os

# Add project root
sys.path.insert(0, '/workspaces/DashTests')

from backend.utils.settings import get_settings

async def debug_api_call():
    settings = get_settings()
    
    print("\n=== Configuration ===")
    print(f"API Key: {settings.MINIMAX_API_KEY}")
    print(f"Group ID: {settings.MINIMAX_GROUP_ID}")
    print()
    
    # Test with minimal payload
    url = "https://api.minimax.chat/v1/video_generation"
    
    headers = {
        "Content-Type": "application/json",
        "authorization": f"Bearer {settings.MINIMAX_API_KEY}"
    }
    
    payload = {
        "group_id": settings.MINIMAX_GROUP_ID,
        "model": "MiniMax-Hailuo-2.3",
        "prompt": "A beautiful sunset over mountains",
        "prompt_optimizer": True
    }
    
    print("=== Request ===")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    print(f"Payload: {payload}")
    print()
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Sending request...")
        try:
            response = await client.post(url, json=payload, headers=headers)
            print(f"\n=== Response ===")
            print(f"Status: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            print(f"Body: {response.text}")
            print()
            
            if response.status_code == 200:
                result = response.json()
                print(f"JSON: {result}")
                if "task_id" in result:
                    print(f"\n✓ Success! Task ID: {result['task_id']}")
                else:
                    print(f"\n✗ No task_id in response")
            else:
                print(f"\n✗ Error: {response.status_code}")
                
        except Exception as e:
            print(f"\n✗ Exception: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_call())
