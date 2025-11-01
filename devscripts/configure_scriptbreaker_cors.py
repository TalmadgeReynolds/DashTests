#!/usr/bin/env python3
"""
Configure CORS settings for the scriptbreaker S3 bucket
"""
import boto3
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def configure_bucket_cors():
    """Configure CORS for scriptbreaker bucket"""
    
    # Get AWS credentials from environment
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    bucket_name = os.getenv('SCREENPLAY_BUCKET', 'scriptbreaker')
    region = 'us-east-1'  # scriptbreaker is in us-east-1
    
    if not aws_access_key or not aws_secret_key:
        print("ERROR: AWS credentials not found in environment")
        return False
    
    # Create S3 client
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=region
    )
    
    # CORS configuration
    cors_configuration = {
        'CORSRules': [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['GET', 'PUT', 'POST', 'DELETE', 'HEAD'],
                'AllowedOrigins': ['*'],  # In production, restrict this to your domain
                'ExposeHeaders': ['ETag'],
                'MaxAgeSeconds': 3000
            }
        ]
    }
    
    try:
        # Apply CORS configuration
        s3_client.put_bucket_cors(
            Bucket=bucket_name,
            CORSConfiguration=cors_configuration
        )
        print(f"✅ CORS configuration applied successfully to bucket: {bucket_name}")
        
        # Verify CORS configuration
        response = s3_client.get_bucket_cors(Bucket=bucket_name)
        print(f"\n📋 Current CORS configuration:")
        print(f"   Bucket: {bucket_name}")
        print(f"   Region: {region}")
        print(f"   Rules: {len(response['CORSRules'])}")
        for i, rule in enumerate(response['CORSRules'], 1):
            print(f"\n   Rule {i}:")
            print(f"     - Allowed Methods: {', '.join(rule['AllowedMethods'])}")
            print(f"     - Allowed Origins: {', '.join(rule['AllowedOrigins'])}")
            print(f"     - Allowed Headers: {', '.join(rule['AllowedHeaders'])}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error configuring CORS: {str(e)}")
        return False

if __name__ == "__main__":
    print("Configuring CORS for scriptbreaker bucket...\n")
    success = configure_bucket_cors()
    exit(0 if success else 1)
