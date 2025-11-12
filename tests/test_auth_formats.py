#!/usr/bin/env python3
"""
Test different MiniMax API authentication formats
"""
import asyncio
import httpx
import sys
import json

sys.path.insert(0, '/workspaces/DashTests')
from backend.utils.settings import get_settings

async def test_auth_formats():
    settings = get_settings()
    
    print("\n=== Testing MiniMax API Authentication ===\n")
    
    # Test different endpoints and header formats
    tests = [
        {
            "name": "Standard Bearer with authorization (lowercase)",
            "url": "https://api.minimax.chat/v1/video_generation",
            "headers": {
                "Content-Type": "application/json",
                "authorization": f"Bearer {settings.MINIMAX_API_KEY}"
            }
        },
        {
            "name": "Standard Bearer with Authorization (capitalized)",
            "url": "https://api.minimax.chat/v1/video_generation",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.MINIMAX_API_KEY}"
            }
        },
        {
            "name": "Direct JWT token (no Bearer)",
            "url": "https://api.minimax.chat/v1/video_generation",
            "headers": {
                "Content-Type": "application/json",
                "authorization": settings.MINIMAX_API_KEY
            }
        },
        {
            "name": "Direct JWT token with Authorization (cap, no Bearer)",
            "url": "https://api.minimax.chat/v1/video_generation",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": settings.MINIMAX_API_KEY
            }
        }
    ]
    
    payload = {
        "group_id": settings.MINIMAX_GROUP_ID,
        "model": "MiniMax-Hailuo-2.3",
        "prompt": "A beautiful sunset",
        "prompt_optimizer": True
    }
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"URL: {test['url']}")
        print(f"Headers: {json.dumps({k: v[:50] + '...' if len(v) > 50 else v for k, v in test['headers'].items()}, indent=2)}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    test['url'],
                    json=payload,
                    headers=test['headers']
                )
                
                print(f"\nStatus: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    if "task_id" in result:
                        print(f"✓ SUCCESS! Task ID: {result['task_id']}")
                        print(f"\nThis authentication format works!")
                        return test
                    else:
                        print(f"Response: {json.dumps(result, indent=2)}")
                else:
                    try:
                        error = response.json()
                        print(f"Error Response: {json.dumps(error, indent=2)}")
                    except:
                        print(f"Error Text: {response.text}")
                        
            except Exception as e:
                print(f"✗ Exception: {type(e).__name__}: {e}")
    
    print(f"\n{'='*60}")
    print("All authentication formats failed")
    print(f"{'='*60}")
    
    # Additional diagnostics
    print(f"\n=== Diagnostics ===")
    print(f"API Key length: {len(settings.MINIMAX_API_KEY)} chars")
    print(f"API Key starts with: {settings.MINIMAX_API_KEY[:30]}...")
    print(f"API Key ends with: ...{settings.MINIMAX_API_KEY[-30:]}")
    print(f"Group ID: {settings.MINIMAX_GROUP_ID}")
    
    # Try to decode the JWT to verify it's valid
    try:
        import base64
        parts = settings.MINIMAX_API_KEY.split('.')
        if len(parts) == 3:
            # Decode header
            header_data = parts[0] + '=' * (4 - len(parts[0]) % 4)
            header = json.loads(base64.urlsafe_b64decode(header_data))
            print(f"\nJWT Header: {json.dumps(header, indent=2)}")
            
            # Decode payload
            payload_data = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_data))
            print(f"JWT Payload: {json.dumps(payload, indent=2)}")
            print(f"\nJWT appears valid!")
    except Exception as e:
        print(f"\nJWT decode error: {e}")

if __name__ == "__main__":
    asyncio.run(test_auth_formats())
