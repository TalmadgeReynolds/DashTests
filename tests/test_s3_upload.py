#!/usr/bin/env python3
"""
Test S3 upload functionality without running full Topaz processing.
Simulates a completed job with a test video file.
"""

import asyncio
import sys
import os
import httpx
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.utils.settings import get_settings
from backend.routes.enhancement import get_s3_client
from backend.utils.logging import get_logger

logger = get_logger("test_s3_upload")


async def test_s3_upload():
    """Test uploading a mock video to S3 and generating public URL"""
    app_settings = get_settings()
    
    # Create a small test video content (just some bytes for testing)
    test_video_content = b"This is test video content - not a real video"
    test_job_id = "test-job-123"
    
    try:
        # Upload to S3
        processed_key = f"processed/{test_job_id}.mp4"
        
        logger.info("Testing S3 upload", job_id=test_job_id, key=processed_key)
        
        s3_client = get_s3_client()
        s3_client.put_object(
            Bucket=app_settings.S3_BUCKET_NAME,
            Key=processed_key,
            Body=test_video_content,
            ContentType="video/mp4"
        )
        
        # Generate public URL
        processed_video_url = f"https://{app_settings.S3_BUCKET_NAME}.s3.{app_settings.AWS_REGION}.amazonaws.com/{processed_key}"
        
        logger.info("✅ SUCCESS! Video uploaded to S3",
                   job_id=test_job_id,
                   processed_key=processed_key,
                   url=processed_video_url)
        
        print(f"\n✅ Test passed!")
        print(f"📦 Bucket: {app_settings.S3_BUCKET_NAME}")
        print(f"🔑 Key: {processed_key}")
        print(f"🔗 URL: {processed_video_url}")
        
        # Test if we can access the object
        response = s3_client.head_object(
            Bucket=app_settings.S3_BUCKET_NAME,
            Key=processed_key
        )
        print(f"📊 Size: {response['ContentLength']} bytes")
        print(f"📅 Last Modified: {response['LastModified']}")
        
        # Clean up test file
        print(f"\n🧹 Cleaning up test file...")
        s3_client.delete_object(
            Bucket=app_settings.S3_BUCKET_NAME,
            Key=processed_key
        )
        print(f"✅ Test file deleted")
        
        return True
        
    except Exception as e:
        logger.error("❌ Test failed", error=str(e))
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Testing S3 Upload Functionality\n")
    success = asyncio.run(test_s3_upload())
    sys.exit(0 if success else 1)
