import os
import tempfile
import pytest
from unittest import mock
from botocore.exceptions import ClientError
from pathlib import Path

from backend.services.storage import StorageService
from backend.schemas.common import PresignKind
from backend.exceptions import ValidationError, StorageError


class TestStorageServiceAdvanced:
    """Advanced tests for StorageService"""
    
    @pytest.fixture
    def mock_s3_client(self):
        """Create a mock S3 client for testing storage service"""
        with mock.patch('boto3.client') as mock_client:
            mock_s3 = mock.MagicMock()
            mock_client.return_value = mock_s3
            
            # Mock head_bucket to return success (bucket exists)
            mock_s3.head_bucket.return_value = {}
            
            # Mock generate_presigned_url to return a test URL
            mock_s3.generate_presigned_url.return_value = "https://test-storage/presigned-url"
            
            yield mock_s3
    
    def test_upload_file_with_unknown_mime_type(self, mock_s3_client, tmp_path):
        """Test uploading a file with unknown MIME type"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Create a test file with unusual extension
            test_file = tmp_path / "test_data.xyz"
            test_file.write_bytes(b"test data content")
            file_path = str(test_file)
            
            # Mock mimetypes.guess_type to return None
            with mock.patch('mimetypes.guess_type', return_value=(None, None)):
                # Mock validate_presign_request to avoid validation errors
                with mock.patch.object(service, 'validate_presign_request'):
                    # Mock generate_key to return predictable key
                    with mock.patch.object(service, 'generate_key', return_value="video/test-123456.xyz"):
                        # Call upload_file with VIDEO kind
                        key, url = service.upload_file(file_path, PresignKind.VIDEO)
                        
                        # Should have used default MIME type for VIDEO
                        mock_s3_client.upload_file.assert_called_once_with(
                            Filename=file_path,
                            Bucket=service.bucket,
                            Key="video/test-123456.xyz",
                            ExtraArgs={"ContentType": "video/mp4"}  # Default for VIDEO
                        )
    
    def test_upload_file_s3_client_error(self, mock_s3_client, tmp_path):
        """Test handling S3 client errors during upload"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Create a test file
            test_file = tmp_path / "test.mp4"
            test_file.write_bytes(b"test video content")
            file_path = str(test_file)
            
            # Mock upload_file to raise a ClientError
            mock_s3_client.upload_file.side_effect = ClientError(
                {'Error': {'Code': '403', 'Message': 'Access Denied'}},
                'UploadFile'
            )
            
            # Mock validate_presign_request to avoid validation errors
            with mock.patch.object(service, 'validate_presign_request'):
                # Call should raise StorageError
                with pytest.raises(StorageError) as exc:
                    service.upload_file(file_path, PresignKind.VIDEO)
                
                assert "Failed to upload file" in str(exc.value)
                assert "Access Denied" in str(exc.value)
    
    def test_upload_file_with_validation_error(self, mock_s3_client, tmp_path):
        """Test validation errors are propagated during upload"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Create a test file
            test_file = tmp_path / "test.mp4"
            test_file.write_bytes(b"test video content")
            file_path = str(test_file)
            
            # Mock validate_presign_request to raise a ValidationError
            validation_error = ValidationError("File size exceeds limit")
            with mock.patch.object(
                service, 
                'validate_presign_request', 
                side_effect=validation_error
            ):
                # Call should raise the original ValidationError
                with pytest.raises(ValidationError) as exc:
                    service.upload_file(file_path, PresignKind.VIDEO)
                
                # Should be the exact same error
                assert exc.value == validation_error
                
                # Should not attempt to upload
                mock_s3_client.upload_file.assert_not_called()
    
    def test_upload_file_not_found(self, mock_s3_client):
        """Test handling file not found errors during upload"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Use a non-existent file path
            file_path = "/path/to/nonexistent/file.mp4"
            
            # Call should raise StorageError
            with pytest.raises(StorageError) as exc:
                service.upload_file(file_path, PresignKind.VIDEO)
            
            assert "Failed to upload file" in str(exc.value)
            
            # Should not attempt to upload
            mock_s3_client.upload_file.assert_not_called()
    
    def test_integration_with_real_temp_file(self, mock_s3_client):
        """Test a more realistic upload with a real temporary file"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Create a real temporary file
            with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                temp_file.write(b"test video content" * 1000)  # Add some content
                file_path = temp_file.name
                
            try:
                # Mock validate_presign_request to avoid validation issues
                with mock.patch.object(service, 'validate_presign_request'):
                    # Call upload_file
                    key, url = service.upload_file(file_path, PresignKind.VIDEO)
                    
                    # Check upload was called with correct parameters
                    mock_s3_client.upload_file.assert_called_once_with(
                        Filename=file_path,
                        Bucket=service.bucket,
                        Key=mock.ANY,  # Don't care about exact key
                        ExtraArgs={"ContentType": "video/mp4"}
                    )
                    
                    # Check key format
                    assert key.startswith("video/")
                    assert key.endswith(".mp4")
            finally:
                # Clean up the temporary file
                if os.path.exists(file_path):
                    os.unlink(file_path)