#!/usr/bin/env python3
"""
Check MiniMax token and explore authentication options
"""
import asyncio
import httpx
import sys
import json
import base64

sys.path.insert(0, '/workspaces/DashTests')
from backend.utils.settings import get_settings

def decode_jwt(token):
    """Decode JWT token to see payload"""
    try:
        parts = token.split('.')
        if len(parts) == 3:
            # Decode payload
            payload_data = parts[1] + '=' * (4 - len(parts[1]) % 4)
            payload = json.loads(base64.urlsafe_b64decode(payload_data))
            return payload
    except Exception as e:
        return {"error": str(e)}

async def explore_api():
    settings = get_settings()
    
    print("\n=== Current Token Analysis ===")
    payload = decode_jwt(settings.MINIMAX_API_KEY)
    print(json.dumps(payload, indent=2))
    
    # Check if TokenType indicates API vs Console
    token_type = payload.get('TokenType')
    print(f"\nToken Type: {token_type}")
    if token_type == 1:
        print("  → Type 1: Likely console/web access token")
    elif token_type == 2:
        print("  → Type 2: Might be API access token")
    
    print(f"\n=== Testing Different Approaches ===\n")
    
    # Try with group_id in URL query params instead of body
    tests = [
        {
            "name": "Group ID in URL query param",
            "url": f"https://api.minimax.chat/v1/video_generation?GroupId={settings.MINIMAX_GROUP_ID}",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.MINIMAX_API_KEY}"
            },
            "payload": {
                "model": "MiniMax-Hailuo-2.3",
                "prompt": "A sunset",
                "prompt_optimizer": True
            }
        },
        {
            "name": "Both Bearer token AND group_id in body",
            "url": "https://api.minimax.chat/v1/video_generation",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.MINIMAX_API_KEY}",
                "GroupId": settings.MINIMAX_GROUP_ID
            },
            "payload": {
                "group_id": settings.MINIMAX_GROUP_ID,
                "model": "MiniMax-Hailuo-2.3",
                "prompt": "A sunset",
                "prompt_optimizer": True
            }
        },
        {
            "name": "Check if different endpoint exists for API keys",
            "url": "https://api.minimax.chat/v1/text_to_video",
            "headers": {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.MINIMAX_API_KEY}"
            },
            "payload": {
                "group_id": settings.MINIMAX_GROUP_ID,
                "model": "MiniMax-Hailuo-2.3",
                "prompt": "A sunset",
                "prompt_optimizer": True
            }
        }
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n{'='*60}")
        print(f"Test {i}: {test['name']}")
        print(f"{'='*60}")
        print(f"URL: {test['url']}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    test['url'],
                    json=test['payload'],
                    headers=test['headers']
                )
                
                print(f"Status: {response.status_code}")
                
                try:
                    result = response.json()
                    print(f"Response: {json.dumps(result, indent=2)}")
                    
                    if "task_id" in result:
                        print(f"\n✓ SUCCESS! Task ID: {result['task_id']}")
                        return
                        
                except:
                    print(f"Response Text: {response.text}")
                    
            except Exception as e:
                print(f"✗ Exception: {e}")
    
    print(f"\n{'='*60}")
    print("Conclusion")
    print(f"{'='*60}")
    print("\nThe token you have appears to be a Console Access Token (TokenType=1).")
    print("MiniMax may require you to:")
    print("  1. Generate a separate API Key for programmatic access")
    print("  2. Or enable API access for this token in console settings")
    print("  3. Or use a different authentication method (API Key vs Bearer token)")
    print("\nPlease check:")
    print("  • MiniMax Console → Settings → API Keys")
    print("  • MiniMax Console → Developer Settings")
    print("  • Look for 'API Secret Key' or 'Generate API Key' option")

if __name__ == "__main__":
    asyncio.run(explore_api())
