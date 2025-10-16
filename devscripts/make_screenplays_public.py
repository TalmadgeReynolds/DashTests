#!/usr/bin/env python3
"""
Script to make screenplay objects in the S3 bucket publicly readable
"""
import sys
import os

# Add parent directory to path to allow importing from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import boto3
from botocore.exceptions import ClientError
from backend.utils.settings import get_settings

settings = get_settings()

def update_object_acl():
    """Update the ACL for screenplay objects to be publicly readable"""
    try:
        print("Initializing S3 client...")
        s3_client = boto3.client(
            service_name="s3",
            endpoint_url=f"{'https' if settings.STORAGE_USE_SSL else 'http'}://{settings.STORAGE_ENDPOINT}",
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
            region_name="us-east-1"
        )

        # List all objects in the screenplay folder
        print(f"Listing objects in bucket: {settings.STORAGE_BUCKET}, prefix: screenplay/")
        response = s3_client.list_objects_v2(
            Bucket=settings.STORAGE_BUCKET,
            Prefix="screenplay/"
        )

        if 'Contents' not in response:
            print("No screenplay objects found in the bucket.")
            return

        for obj in response['Contents']:
            key = obj['Key']
            print(f"Setting public-read ACL for: {key}")
            
            # Make the object publicly readable
            s3_client.put_object_acl(
                Bucket=settings.STORAGE_BUCKET,
                Key=key,
                ACL='public-read'
            )
            
            print(f"Successfully updated ACL for: {key}")

        print("All screenplay objects have been made publicly readable.")
        
        # Also update bucket policy to make screenplay objects readable
        print("Updating bucket policy...")
        bucket_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "PublicReadForScreenplays",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": f"arn:aws:s3:::{settings.STORAGE_BUCKET}/screenplay/*"
                }
            ]
        }
        
        # Convert policy to JSON string
        import json
        bucket_policy_string = json.dumps(bucket_policy)
        
        # Set the new policy
        s3_client.put_bucket_policy(
            Bucket=settings.STORAGE_BUCKET,
            Policy=bucket_policy_string
        )
        
        print(f"Bucket policy updated for {settings.STORAGE_BUCKET}")
        
    except ClientError as e:
        print(f"Error: {str(e)}")
        return False
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting S3 ACL update for screenplays...")
    success = update_object_acl()
    if success:
        print("Script completed successfully.")
    else:
        print("Script encountered errors.")