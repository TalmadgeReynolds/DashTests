#!/usr/bin/env python3
import sys
import os
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.utils.settings import get_settings

def check_file_in_s3(key):
    # Get settings
    settings = get_settings()

    # Initialize S3 client
    s3_client = boto3.client(
        service_name="s3",
        endpoint_url=f"{'https' if settings.STORAGE_USE_SSL else 'http'}://{settings.STORAGE_ENDPOINT}",
        aws_access_key_id=settings.STORAGE_ACCESS_KEY,
        aws_secret_access_key=settings.STORAGE_SECRET_KEY,
        region_name="us-east-1"  # Default region
    )

    # Check if the file exists
    try:
        s3_client.head_object(Bucket=settings.STORAGE_BUCKET, Key=key)
        print(f"✅ File exists: s3://{settings.STORAGE_BUCKET}/{key}")
        
        # Generate a presigned URL
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': settings.STORAGE_BUCKET, 'Key': key},
                ExpiresIn=3600
            )
            print(f"✅ Presigned URL (valid for 1 hour): {url}")
        except Exception as e:
            print(f"❌ Error generating presigned URL: {str(e)}")
            
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            print(f"❌ File does not exist: s3://{settings.STORAGE_BUCKET}/{key}")
            
            # List files with similar prefix
            prefix = '/'.join(key.split('/')[:-1]) + '/'
            try:
                response = s3_client.list_objects_v2(
                    Bucket=settings.STORAGE_BUCKET,
                    Prefix=prefix
                )
                
                if 'Contents' in response:
                    print(f"\nFiles with similar prefix '{prefix}':")
                    for obj in response['Contents']:
                        print(f"  - {obj['Key']}")
                else:
                    print(f"\nNo files found with prefix '{prefix}'")
            except Exception as e:
                print(f"❌ Error listing objects: {str(e)}")
                
            return False
        else:
            print(f"❌ Error checking file: {str(e)}")
            return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 check_s3_file.py <key>")
        print("Example: python3 check_s3_file.py screenplay/34e2eaa973a0b78f-20251016152610.pdf")
        sys.exit(1)
        
    key = sys.argv[1]
    check_file_in_s3(key)