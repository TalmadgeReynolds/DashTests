#!/usr/bin/env python3
import sys
import os
import json
import boto3
from botocore.exceptions import ClientError

# Add parent directory to path so we can import backend modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.utils.settings import get_settings

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

# Define CORS configuration
cors_configuration = {
    'CORSRules': [{
        'AllowedHeaders': ['*'],
        'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
        'AllowedOrigins': ['*'],  # In production, replace with specific origins
        'ExposeHeaders': ['ETag'],
        'MaxAgeSeconds': 3000
    }]
}

# Define public read policy for the bucket
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicReadGetObject",
            "Effect": "Allow",
            "Principal": "*",
            "Action": ["s3:GetObject"],
            "Resource": [f"arn:aws:s3:::{settings.STORAGE_BUCKET}/*"]
        }
    ]
}

try:
    # Apply the CORS configuration to the bucket
    s3_client.put_bucket_cors(
        Bucket=settings.STORAGE_BUCKET,
        CORSConfiguration=cors_configuration
    )
    print(f"CORS configuration applied to bucket '{settings.STORAGE_BUCKET}'")
    
    # Apply the bucket policy for public read access
    s3_client.put_bucket_policy(
        Bucket=settings.STORAGE_BUCKET,
        Policy=json.dumps(bucket_policy)
    )
    print(f"Public read policy applied to bucket '{settings.STORAGE_BUCKET}'")
    
except ClientError as e:
    print(f"Error configuring bucket: {str(e)}")