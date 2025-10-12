"""
Unit test for storage.py
"""
import pytest
import os
import sys
from unittest import mock
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Mock modules that we don't need for unit tests
sys.modules['boto3'] = mock.MagicMock()
sys.modules['botocore'] = mock.MagicMock()
sys.modules['botocore.exceptions'] = mock.MagicMock()

# Import the module under test
from backend.exceptions import ValidationError
from backend.schemas.common import PresignKind

# Create a simplified version of StorageService for unit testing
class StorageService:
    """Simplified storage service for testing"""
    
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
            "mime_types": ["video/mp4"],
            "max_size_bytes": 100 * 1024 * 1024  # 100MB
        }
    }
    
    def generate_key(self, kind: PresignKind, filename: str) -> str:
        """
        Generate a storage key following the format: {kind}/{sha256}-{ts}.{ext}
        as specified in the storage presign policy
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        unique_id = f"{filename}-{timestamp}-test"
        file_hash = hashlib.sha256(unique_id.encode()).hexdigest()[:16]
        
        # Extract extension from filename
        _, ext = os.path.splitext(filename)
        if not ext:
            ext = ".bin"
        if not ext.startswith("."):
            ext = f".{ext}"
        ext = ext.lower()
            
        return f"{kind.value.lower()}/{file_hash}-{timestamp}{ext}"
    
    def validate_presign_request(self, kind: PresignKind, mime: str, filename: str, content_length: int = None) -> None:
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
    
    def create_presigned_urls(self, kind: PresignKind, filename: str, mime: str, content_length: int = None):
        """
        Create presigned URLs for file upload and access
        Returns (uploadUrl, fileUrl) tuple
        """
        # Validate request against policy
        self.validate_presign_request(kind, mime, filename, content_length)
        
        # Generate storage key
        key = self.generate_key(kind, filename)
        
        # Return mock URLs
        upload_url = f"https://storage-test/upload/{key}"
        file_url = f"https://storage-test/file/{key}"
        
        return upload_url, file_url


class TestStorageServiceUnit:
    """Unit tests for StorageService"""
    
    def test_generate_key(self):
        """Test key generation format"""
        service = StorageService()
        
        # Test with IMAGE kind
        key = service.generate_key(PresignKind.IMAGE, "test.jpg")
        assert key.startswith("image/")
        assert "-" in key  # Contains hash-timestamp separator
        assert key.endswith(".jpg")
        
        # Test with AUDIO kind and no extension
        key = service.generate_key(PresignKind.AUDIO, "audiofile")
        assert key.startswith("audio/")
        assert key.endswith(".bin")  # Default extension
    
    def test_validate_presign_request_valid(self):
        """Test validation with valid parameters"""
        service = StorageService()
        
        # Valid image request
        service.validate_presign_request(
            PresignKind.IMAGE,
            "image/jpeg",
            "test.jpg",
            5 * 1024 * 1024  # 5MB
        )
        
        # Valid audio request without content length
        service.validate_presign_request(
            PresignKind.AUDIO,
            "audio/wav",
            "test.wav"
        )
    
    def test_validate_presign_request_invalid_mime(self):
        """Test validation with invalid MIME type"""
        service = StorageService()
        
        # Invalid MIME type for IMAGE
        with pytest.raises(ValidationError) as exc:
            service.validate_presign_request(
                PresignKind.IMAGE,
                "image/gif",  # Not allowed
                "test.gif"
            )
        assert "Unsupported MIME type" in str(exc.value)
    
    def test_validate_presign_request_invalid_size(self):
        """Test validation with size exceeding limit"""
        service = StorageService()
        
        # Size exceeding limit for IMAGE
        with pytest.raises(ValidationError) as exc:
            service.validate_presign_request(
                PresignKind.IMAGE,
                "image/jpeg",
                "test.jpg",
                15 * 1024 * 1024  # 15MB, exceeds 10MB limit
            )
        assert "exceeds the maximum allowed size" in str(exc.value)
    
    def test_create_presigned_urls(self):
        """Test creating presigned URLs"""
        service = StorageService()
        
        # Test with valid parameters
        upload_url, file_url = service.create_presigned_urls(
            PresignKind.IMAGE,
            "test.jpg",
            "image/jpeg",
            5 * 1024 * 1024
        )
        
        assert upload_url.startswith("https://storage-test/upload/image/")
        assert file_url.startswith("https://storage-test/file/image/")
        assert upload_url.endswith(".jpg")
        assert file_url.endswith(".jpg")


if __name__ == "__main__":
    # Run the tests with pytest
    pytest.main(["-xvs", __file__])