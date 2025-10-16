#!/usr/bin/env python3
import sys
import os
# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.settings import get_settings

# Get settings
settings = get_settings()

# Print storage settings
print("\n--- STORAGE SETTINGS ---")
print(f"STORAGE_MOCK_MODE: {settings.STORAGE_MOCK_MODE}")
print(f"MOCK_PROVIDERS: {settings.MOCK_PROVIDERS}")
print(f"STORAGE_ENDPOINT: {settings.STORAGE_ENDPOINT}")
print(f"STORAGE_BUCKET: {settings.STORAGE_BUCKET}")
print(f"STORAGE_USE_SSL: {settings.STORAGE_USE_SSL}")
print(f"STORAGE_PUBLIC_ENDPOINT: {settings.STORAGE_PUBLIC_ENDPOINT}")
print(f"Mock storage used: {settings.STORAGE_MOCK_MODE or settings.MOCK_PROVIDERS}")

# Check S3 connection
print("\n--- TESTING S3 CONNECTION ---")
try:
    import boto3
    from botocore.exceptions import ClientError
    
    s3_client = boto3.client(
        service_name="s3",
        endpoint_url=f"{'https' if settings.STORAGE_USE_SSL else 'http'}://{settings.STORAGE_ENDPOINT}",
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        region_name="us-east-1"  # For global S3 endpoint, need to use us-east-1
    )
    
    # Test if we can list buckets
    response = s3_client.list_buckets()
    print(f"Connection successful. Found {len(response['Buckets'])} buckets:")
    for bucket in response['Buckets']:
        print(f"  - {bucket['Name']}")
    
    # Check if our bucket exists
    try:
        s3_client.head_bucket(Bucket=settings.STORAGE_BUCKET)
        print(f"\nBucket '{settings.STORAGE_BUCKET}' exists!")
        
        # List some objects in the bucket
        try:
            objects = s3_client.list_objects_v2(Bucket=settings.STORAGE_BUCKET, MaxKeys=5)
            if 'Contents' in objects:
                print(f"First {min(5, len(objects['Contents']))} objects in bucket:")
                for obj in objects['Contents'][:5]:
                    print(f"  - {obj['Key']}")
            else:
                print("Bucket is empty.")
        except ClientError as e:
            print(f"Error listing objects: {e}")
    except ClientError as e:
        print(f"\nBucket does not exist or is not accessible: {e}")
        
        # Try to create bucket
        try:
            s3_client.create_bucket(Bucket=settings.STORAGE_BUCKET)
            print(f"Created bucket '{settings.STORAGE_BUCKET}'")
        except ClientError as e:
            print(f"Error creating bucket: {e}")
            
except Exception as e:
    print(f"Error testing S3 connection: {str(e)}")