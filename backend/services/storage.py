import os
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
import mimetypes

import boto3
from botocore.exceptions import ClientError

from ..utils.settings import get_settings
from ..utils.logging import get_logger
from ..exceptions import StorageError, ValidationError
from ..schemas.common import PresignKind

settings = get_settings()
logger = get_logger("storage")


class StorageService:
    """
    Service for handling file storage and presigned URLs
    Implements the presign policy from /docs/storage/presign_policy.md
    """
    
    # Accepted MIME types and size limits from /docs/storage/presign_policy.md
    MIME_LIMITS = {
        PresignKind.IMAGE: {
            "mime_types": ["image/jpeg", "image/png"],
            "max_size_bytes": 10 * 1024 * 1024  # 10MB
        },
        PresignKind.AUDIO: {
            "mime_types": ["audio/mpeg", "audio/wav"],
            "max_size_bytes": 20 * 1024 * 1024  # 20MB
        },
        PresignKind.VIDEO: {
            "mime_types": ["video/mp4", "video/quicktime"],  # QuickTime is the standard MIME type for ProRes
            "max_size_bytes": 2 * 1024 * 1024 * 1024  # 2GB to accommodate ProRes files
        },
        PresignKind.SCREENPLAY: {
            "mime_types": ["application/pdf"],
            "max_size_bytes": 50 * 1024 * 1024  # 50MB
        }
    }
    
    def __init__(self):
        self.mock_mode = settings.STORAGE_MOCK_MODE or settings.MOCK_PROVIDERS
        self.bucket = settings.STORAGE_BUCKET
        self.screenplay_bucket = settings.SCREENPLAY_BUCKET
        self.public_endpoint = settings.STORAGE_PUBLIC_ENDPOINT
        self.screenplay_public_endpoint = settings.SCREENPLAY_PUBLIC_ENDPOINT
        
        # Always initialize s3_client, even in mock mode
        self.s3_client = boto3.client(
            service_name="s3",
            endpoint_url=f"{'https' if settings.STORAGE_USE_SSL else 'http'}://{settings.STORAGE_ENDPOINT}",
            aws_access_key_id=settings.STORAGE_ACCESS_KEY,
            aws_secret_access_key=settings.STORAGE_SECRET_KEY,
            region_name="us-east-1"  # Default region, doesn't matter for MinIO
        )
            
        # Ensure buckets exist if not in mock mode
        if not self.mock_mode:
            self._ensure_bucket(self.bucket)
            self._ensure_bucket(self.screenplay_bucket)
        else:
            logger.info("storage_mock_mode", message="Using mock storage mode - real S3 client created but operations will be limited")
    
    def _ensure_bucket(self, bucket_name: str) -> None:
        """Ensure the storage bucket exists"""
        try:
            self.s3_client.head_bucket(Bucket=bucket_name)
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                # Bucket doesn't exist, create it
                self.s3_client.create_bucket(Bucket=bucket_name)
                
                # Set public read policy for the bucket
                self.s3_client.put_bucket_policy(
                    Bucket=bucket_name,
                    Policy=f'''{{
                        "Version": "2012-10-17",
                        "Statement": [
                            {{
                                "Sid": "PublicRead",
                                "Effect": "Allow",
                                "Principal": "*",
                                "Action": ["s3:GetObject"],
                                "Resource": ["arn:aws:s3:::{bucket_name}/*"]
                            }}
                        ]
                    }}'''
                )
                
                logger.info("storage_bucket_created", bucket=bucket_name)
            else:
                logger.error("storage_bucket_check_failed", error=str(e))
                raise StorageError(f"Failed to check storage bucket: {str(e)}")
    
    def _get_bucket_for_kind(self, kind: PresignKind) -> str:
        """Get the appropriate bucket name based on file kind"""
        if kind == PresignKind.SCREENPLAY:
            return self.screenplay_bucket
        return self.bucket
    
    def _get_endpoint_for_kind(self, kind: PresignKind) -> str:
        """Get the appropriate public endpoint based on file kind"""
        if kind == PresignKind.SCREENPLAY:
            return self.screenplay_public_endpoint
        return self.public_endpoint
    
    def generate_key(self, kind: PresignKind, filename: str) -> str:
        """
        Generate a storage key following the format: {kind}/{sha256}-{ts}.{ext}
        as specified in the storage presign policy
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        # Generate a SHA256 hash of the filename plus timestamp to ensure uniqueness
        # Use the first 16 characters of the hash for brevity
        unique_id = f"{filename}-{timestamp}-{uuid.uuid4()}"
        file_hash = hashlib.sha256(unique_id.encode()).hexdigest()[:16]
        
        # Extract extension from filename
        _, ext = os.path.splitext(filename)
        
        if not ext:
            # If no extension, try to get it from mime type
            ext = mimetypes.guess_extension("application/octet-stream") or ".bin"
            
        # Ensure extension starts with a dot and is lowercase
        if not ext.startswith("."):
            ext = f".{ext}"
        ext = ext.lower()
            
        return f"{kind.value.lower()}/{file_hash}-{timestamp}{ext}"
    
    def validate_presign_request(self, kind: PresignKind, mime: str, filename: str, content_length: Optional[int] = None) -> None:
        """Validate a presign request against the policy"""
        limits = self.MIME_LIMITS.get(kind)
        
        if not limits:
            raise ValidationError(f"Unsupported file kind: {kind}")
            
        if mime not in limits["mime_types"]:
            allowed = ", ".join(limits["mime_types"])
            raise ValidationError(
                f"Unsupported MIME type: {mime}. Allowed types for {kind}: {allowed}",
                detail={"allowed_types": limits["mime_types"]}
            )
            
        # Validate content length if provided
        if content_length is not None and content_length > limits["max_size_bytes"]:
            max_size_mb = limits["max_size_bytes"] / (1024 * 1024)
            raise ValidationError(
                f"File size exceeds the maximum allowed size of {max_size_mb} MB for {kind}",
                detail={"max_size_bytes": limits["max_size_bytes"], "provided_size": content_length}
            )
    
    def create_presigned_urls(self, kind: PresignKind, filename: str, mime: str, content_length: Optional[int] = None) -> Tuple[str, str]:
        """
        Create presigned URLs for file upload and access
        Returns (uploadUrl, fileUrl) tuple
        
        Args:
            kind: Type of file (IMAGE, AUDIO, VIDEO, SCREENPLAY)
            filename: Original filename
            mime: MIME type of the file
            content_length: Size of file in bytes, used to validate against size limits
        """
        # Validate request against policy
        self.validate_presign_request(kind, mime, filename, content_length)
        
        # Generate storage key
        key = self.generate_key(kind, filename)
        
        # Get the appropriate bucket and endpoint for this file kind
        bucket = self._get_bucket_for_kind(kind)
        public_endpoint = self._get_endpoint_for_kind(kind)
        
        try:
            if self.mock_mode:
                # In mock mode, return fake URLs that point to the key
                upload_url = f"http://mock-storage/{bucket}/{key}"
                file_url = f"http://mock-storage/{bucket}/{key}"
                logger.info("mock_presigned_url_created", kind=kind, key=key, bucket=bucket)
            else:
                # Prepare parameters for presigned URL
                params = {
                    "Bucket": bucket,
                    "Key": key,
                    "ContentType": mime
                }
                
                # Add content length condition if provided
                if content_length is not None:
                    params["ContentLength"] = content_length
                    
                # Create presigned PUT URL for upload with conditions
                upload_url = self.s3_client.generate_presigned_url(
                    "put_object",
                    Params=params,
                    ExpiresIn=3600  # URL valid for 1 hour
                )
                
                # Generate public URL for file access
                file_url = f"{public_endpoint}/{key}"
                
                logger.info("presigned_url_created", kind=kind, key=key, bucket=bucket)
            
            return upload_url, file_url
            
        except ClientError as e:
            logger.error("presign_failed", error=str(e), bucket=bucket)
            raise StorageError(f"Failed to generate presigned URL: {str(e)}")
    
    def get_file_url(self, key: str) -> str:
        """Generate public URL for a stored file"""
        if self.mock_mode:
            return f"http://mock-storage/{self.bucket}/{key}"
            
    def create_presigned_get_url(self, key: str, expires_in: int = 3600) -> str:
        """
        Generate a presigned GET URL for accessing a file
        
        Args:
            key: The storage key of the file (e.g., "screenplay/abc.pdf")
            expires_in: Expiration time in seconds
            
        Returns:
            Presigned URL for GET access
        """
        # Determine bucket based on key prefix
        bucket = self.screenplay_bucket if key.startswith("screenplay/") else self.bucket
        
        if self.mock_mode:
            return f"http://mock-storage/{bucket}/{key}"
        
        try:
            # Create presigned GET URL
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": bucket,
                    "Key": key
                },
                ExpiresIn=expires_in
            )
            
            logger.info("presigned_get_url_created", key=key, bucket=bucket, expires_in=expires_in)
            return url
            
        except ClientError as e:
            logger.error("presign_get_failed", error=str(e), key=key, bucket=bucket)
            raise StorageError(f"Failed to generate presigned GET URL: {str(e)}")
    
    def upload_file(self, file_path: str, kind: PresignKind) -> Tuple[str, str]:
        """
        Upload a file directly from the server to storage
        
        Args:
            file_path: Path to the file on server disk
            kind: Type of file (IMAGE, AUDIO, VIDEO)
            
        Returns:
            Tuple of (key, url) where key is the S3 object key and url is the public access URL
        """
        try:
            # Get filename from path
            filename = os.path.basename(file_path)
            
            # Determine MIME type
            mime_type, _ = mimetypes.guess_type(file_path)
            if not mime_type:
                # Default to appropriate MIME type based on kind
                if kind == PresignKind.VIDEO:
                    mime_type = "video/mp4"
                elif kind == PresignKind.AUDIO:
                    mime_type = "audio/mpeg"
                elif kind == PresignKind.IMAGE:
                    mime_type = "image/jpeg"
                else:
                    mime_type = "application/octet-stream"
            
            # Validate file type and get file size
            file_size = os.path.getsize(file_path)
            self.validate_presign_request(kind, mime_type, filename, file_size)
            
            # Generate storage key
            key = self.generate_key(kind, filename)
            
            # Get the appropriate bucket for this file kind
            bucket = self._get_bucket_for_kind(kind)
            
            if not self.mock_mode:
                # Upload file to S3 when not in mock mode
                self.s3_client.upload_file(
                    Filename=file_path,
                    Bucket=bucket,
                    Key=key,
                    ExtraArgs={"ContentType": mime_type}
                )
            else:
                logger.info("mock_file_upload", message=f"Mock upload of {file_path} to {key}")
            
            # Generate public URL
            file_url = self.get_file_url(key)
            
            logger.info("file_uploaded", kind=kind, key=key, size=file_size, bucket=bucket)
            
            return key, file_url
            
        except ClientError as e:
            logger.error("upload_failed", error=str(e), file=file_path)
            raise StorageError(f"Failed to upload file: {str(e)}")
        except ValidationError as e:
            # Pass through validation errors
            raise
        except Exception as e:
            logger.error("upload_failed", error=str(e), file=file_path)
            raise StorageError(f"Failed to upload file: {str(e)}")
    
    async def upload_bytes(self, data: bytes, filename: str, content_type: str) -> str:
        """
        Upload raw bytes directly to storage
        
        Args:
            data: File data as bytes
            filename: Desired filename (used for key generation)
            content_type: MIME type of the content
            
        Returns:
            Public URL of the uploaded file
        """
        try:
            # Determine kind from content type
            if content_type.startswith("image/"):
                kind = PresignKind.IMAGE
            elif content_type.startswith("audio/"):
                kind = PresignKind.AUDIO
            elif content_type.startswith("video/"):
                kind = PresignKind.VIDEO
            elif content_type.startswith("application/pdf"):
                kind = PresignKind.SCREENPLAY
            else:
                raise ValidationError(f"Unsupported content type: {content_type}")
            
            # Validate size
            file_size = len(data)
            self.validate_presign_request(kind, content_type, filename, file_size)
            
            # Generate storage key
            key = self.generate_key(kind, filename)
            
            # Get the appropriate bucket for this file kind
            bucket = self._get_bucket_for_kind(kind)
            
            if not self.mock_mode:
                # Upload bytes to S3 when not in mock mode
                self.s3_client.put_object(
                    Bucket=bucket,
                    Key=key,
                    Body=data,
                    ContentType=content_type
                )
            else:
                logger.info("mock_bytes_upload", message=f"Mock upload of {len(data)} bytes to {key}")
            
            # Generate public URL
            file_url = self.get_file_url(key)
            
            logger.info("bytes_uploaded", kind=kind, key=key, size=file_size, bucket=bucket)
            
            return file_url
            
        except ClientError as e:
            logger.error("upload_bytes_failed", error=str(e))
            raise StorageError(f"Failed to upload bytes: {str(e)}")
        except ValidationError as e:
            # Pass through validation errors
            raise
        except Exception as e:
            logger.error("upload_bytes_failed", error=str(e))
            raise StorageError(f"Failed to upload bytes: {str(e)}")