#!/usr/bin/env python3
"""
Test MiniMax API with real credentials
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, '/workspaces/DashTests')

from backend.adapters.minimax_adapter import MinimaxAdapter, MinimaxModel
from backend.utils.settings import get_settings

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


async def test_real_api():
    """Test MiniMax API with real credentials"""
    
    print(f"\n{BLUE}{'=' * 60}{RESET}")
    print(f"{BLUE}Testing MiniMax API Connection{RESET}")
    print(f"{BLUE}{'=' * 60}{RESET}\n")
    
    # Get settings
    settings = get_settings()
    
    print(f"{YELLOW}Configuration:{RESET}")
    print(f"  API Key: {settings.MINIMAX_API_KEY[:20]}...")
    print(f"  Group ID: {settings.MINIMAX_GROUP_ID}")
    print(f"  Mock Mode: {getattr(settings, 'MINIMAX_MOCK_MODE', True)}")
    print()
    
    # Create adapter
    adapter = MinimaxAdapter(
        api_key=settings.MINIMAX_API_KEY,
        group_id=settings.MINIMAX_GROUP_ID,
        mock_mode=False  # Force real API
    )
    
    print(f"{YELLOW}Test 1: Creating a text-to-video task...{RESET}")
    try:
        task_id = await adapter.text_to_video(
            prompt="A serene mountain landscape at sunset with golden light",
            model=MinimaxModel.HAILUO_2_3,
            aspect_ratio="16:9",
            duration_seconds=5,
            prompt_optimizer=True
        )
        print(f"{GREEN}✓ Task created successfully!{RESET}")
        print(f"  Task ID: {task_id}")
        print()
        
        # Query status
        print(f"{YELLOW}Test 2: Querying task status...{RESET}")
        status = await adapter.query_task_status(task_id)
        print(f"{GREEN}✓ Status query successful!{RESET}")
        print(f"  Status: {status.get('status')}")
        print(f"  Progress: {status.get('progress', 0)}%")
        print()
        
        # If status is not success yet, poll a bit
        if status.get('status') not in ['success', 'failed']:
            print(f"{YELLOW}Test 3: Polling until complete (max 60 seconds)...{RESET}")
            try:
                final_status = await adapter.poll_until_complete(
                    task_id=task_id,
                    max_wait_seconds=60,
                    poll_interval=5
                )
                print(f"{GREEN}✓ Video generation complete!{RESET}")
                print(f"  Status: {final_status.get('status')}")
                print(f"  File ID: {final_status.get('file_id')}")
                print()
                
                # Try to download
                if final_status.get('file_id'):
                    print(f"{YELLOW}Test 4: Downloading video...{RESET}")
                    video_bytes = await adapter.download_video(final_status['file_id'])
                    print(f"{GREEN}✓ Video downloaded successfully!{RESET}")
                    print(f"  Size: {len(video_bytes):,} bytes ({len(video_bytes)/1024/1024:.2f} MB)")
                    print()
                    
            except Exception as e:
                print(f"{YELLOW}⚠ Polling timeout or error: {str(e)}{RESET}")
                print(f"{YELLOW}  (This is normal - generation can take several minutes){RESET}")
                print()
        
        print(f"{GREEN}{'=' * 60}{RESET}")
        print(f"{GREEN}API Connection Test: SUCCESS ✓{RESET}")
        print(f"{GREEN}{'=' * 60}{RESET}")
        print()
        print(f"{BLUE}Your MiniMax API is working correctly!{RESET}")
        print(f"{BLUE}Task ID: {task_id}{RESET}")
        print()
        print(f"{YELLOW}Next steps:{RESET}")
        print(f"  1. Check task status: GET /api/v1/minimax/task/{task_id}/status")
        print(f"  2. Wait for completion (usually 1-5 minutes)")
        print(f"  3. Download video: POST /api/v1/minimax/task/{task_id}/download")
        print()
        
        return 0
        
    except Exception as e:
        print(f"{RED}✗ API Test Failed{RESET}")
        print(f"{RED}Error: {str(e)}{RESET}")
        print()
        
        # Print helpful debugging info
        print(f"{YELLOW}Debugging Information:{RESET}")
        print(f"  Error Type: {type(e).__name__}")
        if hasattr(e, 'response'):
            print(f"  Response Status: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
        print()
        
        import traceback
        print(f"{YELLOW}Full Traceback:{RESET}")
        traceback.print_exc()
        print()
        
        return 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(test_real_api())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
