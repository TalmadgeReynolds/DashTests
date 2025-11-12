#!/usr/bin/env python3
"""
Complete end-to-end test of MiniMax API
"""
import asyncio
import sys
import os

sys.path.insert(0, '/workspaces/DashTests')

from backend.adapters.minimax_adapter import MinimaxAdapter, MinimaxModel
from backend.utils.settings import get_settings

# Color codes
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


async def complete_test():
    """Complete end-to-end test"""
    
    print(f"\n{BLUE}{'=' * 70}{RESET}")
    print(f"{BLUE}MiniMax API - Complete End-to-End Test{RESET}")
    print(f"{BLUE}{'=' * 70}{RESET}\n")
    
    settings = get_settings()
    
    adapter = MinimaxAdapter(
        api_key=settings.MINIMAX_API_KEY,
        group_id=settings.MINIMAX_GROUP_ID,
        mock_mode=False
    )
    
    print(f"{YELLOW}Step 1: Creating video generation task...{RESET}")
    try:
        task_id = await adapter.text_to_video(
            prompt="A peaceful mountain landscape at golden hour with clouds drifting by",
            model=MinimaxModel.HAILUO_2_3,
            aspect_ratio="16:9",
            duration_seconds=6,
            prompt_optimizer=True
        )
        print(f"{GREEN}✓ Task created: {task_id}{RESET}\n")
    except Exception as e:
        print(f"{RED}✗ Failed to create task: {e}{RESET}")
        return 1
    
    print(f"{YELLOW}Step 2: Polling for completion (max 5 minutes)...{RESET}")
    print(f"{BLUE}This typically takes 1-3 minutes...{RESET}\n")
    
    try:
        final_status = await adapter.poll_until_complete(
            task_id=task_id,
            max_wait_seconds=300,  # 5 minutes
            poll_interval=10
        )
        
        print(f"{GREEN}✓ Video generation complete!{RESET}")
        print(f"  Status: {final_status.get('status')}")
        print(f"  File ID: {final_status.get('file_id')}")
        print(f"  Resolution: {final_status.get('video_width')}x{final_status.get('video_height')}")
        print()
        
        file_id = final_status.get('file_id')
        if not file_id:
            print(f"{RED}✗ No file_id in response{RESET}")
            return 1
            
    except Exception as e:
        print(f"{RED}✗ Polling failed: {e}{RESET}")
        print(f"{YELLOW}Task ID for manual check: {task_id}{RESET}")
        return 1
    
    print(f"{YELLOW}Step 3: Downloading video...{RESET}")
    try:
        video_bytes = await adapter.download_video(file_id)
        
        size_mb = len(video_bytes) / 1024 / 1024
        print(f"{GREEN}✓ Video downloaded successfully!{RESET}")
        print(f"  Size: {len(video_bytes):,} bytes ({size_mb:.2f} MB)")
        print()
        
        # Save to file
        output_path = f"/workspaces/DashTests/minimax_test_video_{task_id}.mp4"
        with open(output_path, 'wb') as f:
            f.write(video_bytes)
        
        print(f"{GREEN}✓ Video saved to: {output_path}{RESET}")
        print()
        
    except Exception as e:
        print(f"{RED}✗ Download failed: {e}{RESET}")
        return 1
    
    print(f"{GREEN}{'=' * 70}{RESET}")
    print(f"{GREEN}SUCCESS! Complete End-to-End Test Passed ✓{RESET}")
    print(f"{GREEN}{'=' * 70}{RESET}\n")
    
    print(f"{BLUE}Summary:{RESET}")
    print(f"  ✓ Task creation working")
    print(f"  ✓ Status polling working")
    print(f"  ✓ Video download working")
    print(f"  ✓ API authentication correct")
    print(f"  ✓ All endpoints configured properly")
    print()
    print(f"{GREEN}Your MiniMax integration is fully operational!{RESET}")
    print()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(complete_test())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Test interrupted by user{RESET}")
        sys.exit(1)
