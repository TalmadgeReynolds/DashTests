import pytest
from unittest import mock
from botocore.exceptions import ClientError

from backend.services.storage import StorageService
from backend.schemas.common import PresignKind
from backend.exceptions import ValidationError, StorageError

# Mock boto3 client for testing
@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client for testing storage service"""
    with mock.patch('boto3.client') as mock_client:
        mock_s3 = mock.MagicMock()
        mock_client.return_value = mock_s3
        
        # Mock head_bucket to return success (bucket exists)
        mock_s3.head_bucket.return_value = {}
        
        # Mock generate_presigned_url to return a test URL
        mock_s3.generate_presigned_url.return_value = "https://test-storage/presigned-url"
        
        yield mock_s3

class TestStorageService:
    """Test suite for StorageService"""
    
    def test_init_bucket_exists(self, mock_s3_client):
        """Test initializing when bucket already exists"""
        service = StorageService()
        
        # Should check if bucket exists
        mock_s3_client.head_bucket.assert_called_once()
        
        # Should not try to create bucket
        mock_s3_client.create_bucket.assert_not_called()
    
    def test_init_bucket_not_exists(self, mock_s3_client):
        """Test initializing when bucket doesn't exist"""
        # Make head_bucket raise a 404 error
        error_response = {'Error': {'Code': '404'}}
        mock_s3_client.head_bucket.side_effect = ClientError(error_response, 'HeadBucket')
        
        service = StorageService()
        
        # Should check if bucket exists
        mock_s3_client.head_bucket.assert_called_once()
        
        # Should create bucket
        mock_s3_client.create_bucket.assert_called_once()
        
        # Should set bucket policy
        mock_s3_client.put_bucket_policy.assert_called_once()
    
    def test_generate_key(self):
        """Test key generation follows the required format"""
        with mock.patch('boto3.client'):
            service = StorageService()
            
            # Test IMAGE key
            image_key = service.generate_key(PresignKind.IMAGE, "test.jpg")
            assert image_key.startswith("image/")
            assert image_key.endswith(".jpg")
            
            # Test AUDIO key
            audio_key = service.generate_key(PresignKind.AUDIO, "test.mp3")
            assert audio_key.startswith("audio/")
            assert audio_key.endswith(".mp3")
            
            # Test with no extension
            no_ext_key = service.generate_key(PresignKind.VIDEO, "videofile")
            assert no_ext_key.startswith("video/")
            assert "." in no_ext_key  # Should have added an extension
    
    def test_validate_presign_request_valid(self):
        """Test validation with valid parameters"""
        with mock.patch('boto3.client'):
            service = StorageService()
            
            # Valid image request
            service.validate_presign_request(
                PresignKind.IMAGE,
                "image/jpeg",
                "test.jpg",
                5 * 1024 * 1024  # 5MB
            )
            
            # Valid audio request
            service.validate_presign_request(
                PresignKind.AUDIO,
                "audio/mpeg",
                "test.mp3",
                15 * 1024 * 1024  # 15MB
            )
            
            # Valid video request
            service.validate_presign_request(
                PresignKind.VIDEO,
                "video/mp4",
                "test.mp4",
                50 * 1024 * 1024  # 50MB
            )
    
    def test_validate_presign_request_invalid_mime(self):
        """Test validation with invalid MIME type"""
        with mock.patch('boto3.client'):
            service = StorageService()
            
            # Invalid MIME type for IMAGE
            with pytest.raises(ValidationError) as exc:
                service.validate_presign_request(
                    PresignKind.IMAGE,
                    "image/gif",  # Not allowed
                    "test.gif"
                )
            assert "Unsupported MIME type" in str(exc.value)
            
            # Invalid MIME type for AUDIO
            with pytest.raises(ValidationError) as exc:
                service.validate_presign_request(
                    PresignKind.AUDIO,
                    "audio/ogg",  # Not allowed
                    "test.ogg"
                )
            assert "Unsupported MIME type" in str(exc.value)
    
    def test_validate_presign_request_invalid_size(self):
        """Test validation with size exceeding limit"""
        with mock.patch('boto3.client'):
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
            
            # Size exceeding limit for AUDIO
            with pytest.raises(ValidationError) as exc:
                service.validate_presign_request(
                    PresignKind.AUDIO,
                    "audio/wav",
                    "test.wav",
                    25 * 1024 * 1024  # 25MB, exceeds 20MB limit
                )
            assert "exceeds the maximum allowed size" in str(exc.value)
    
    def test_create_presigned_urls(self, mock_s3_client):
        """Test creating presigned URLs"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Test with content length
            upload_url, file_url = service.create_presigned_urls(
                PresignKind.IMAGE,
                "test.jpg",
                "image/jpeg",
                5 * 1024 * 1024  # 5MB
            )
            
            # Should have called generate_presigned_url with content length
            mock_s3_client.generate_presigned_url.assert_called_with(
                "put_object",
                Params=mock.ANY,
                ExpiresIn=3600
            )
            
            # Get the Params passed to generate_presigned_url
            params = mock_s3_client.generate_presigned_url.call_args[1]['Params']
            assert params['ContentType'] == "image/jpeg"
            assert params['ContentLength'] == 5 * 1024 * 1024
            
            # Check returned URLs
            assert upload_url == "https://test-storage/presigned-url"
            assert file_url  # Should have a non-empty file URL
    
    def test_create_presigned_urls_no_content_length(self, mock_s3_client):
        """Test creating presigned URLs without content length"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Test without content length
            upload_url, file_url = service.create_presigned_urls(
                PresignKind.IMAGE,
                "test.jpg",
                "image/jpeg"
            )
            
            # Should have called generate_presigned_url without content length
            mock_s3_client.generate_presigned_url.assert_called_with(
                "put_object",
                Params=mock.ANY,
                ExpiresIn=3600
            )
            
            # Get the Params passed to generate_presigned_url
            params = mock_s3_client.generate_presigned_url.call_args[1]['Params']
            assert params['ContentType'] == "image/jpeg"
            assert 'ContentLength' not in params
            
            # Check returned URLs
            assert upload_url == "https://test-storage/presigned-url"
            assert file_url  # Should have a non-empty file URL
            
    def test_upload_file(self, mock_s3_client, tmp_path):
        """Test direct file upload method"""
        with mock.patch('boto3.client', return_value=mock_s3_client):
            service = StorageService()
            
            # Create a temporary test file
            test_file = tmp_path / "test_video.mp4"
            test_file.write_bytes(b"dummy video content")
            file_path = str(test_file)
            
            # Mock the validate_presign_request method to avoid validation errors
            with mock.patch.object(service, 'validate_presign_request') as mock_validate:
                # Mock the generate_key method to return a predictable key
                with mock.patch.object(service, 'generate_key', return_value="video/test-123456.mp4"):
                    # Call the upload_file method
                    key, url = service.upload_file(file_path, PresignKind.VIDEO)
                    
                    # Check that validation was called with correct parameters
                    mock_validate.assert_called_once()
                    assert mock_validate.call_args[0][0] == PresignKind.VIDEO
                    assert mock_validate.call_args[0][1] == "video/mp4"
                    
                    # Check that upload_file was called with correct parameters
                    mock_s3_client.upload_file.assert_called_once_with(
                        Filename=file_path,
                        Bucket=service.bucket,
                        Key="video/test-123456.mp4",
                        ExtraArgs={"ContentType": "video/mp4"}
                    )
                    
                    # Check returned key and URL
                    assert key == "video/test-123456.mp4"
                    assert url == f"{service.public_endpoint}/{service.bucket}/{key}"