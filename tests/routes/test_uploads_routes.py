import pytest
from unittest import mock
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from backend.routes.uploads import router as uploads_router
from backend.schemas.common import PresignKind
from backend.exceptions import ValidationError, StorageError

# Create a test app with the uploads router
app = FastAPI()
app.include_router(uploads_router)
client = TestClient(app)

# Mock database session
@pytest.fixture
def mock_db():
    """Mock database session"""
    with mock.patch("backend.routes.uploads.get_db") as mock_get_db:
        mock_session = mock.MagicMock()
        mock_get_db.return_value = mock_session
        yield mock_session

# Mock StorageService
@pytest.fixture
def mock_storage_service():
    """Mock StorageService"""
    with mock.patch("backend.routes.uploads.StorageService") as mock_service_class:
        mock_service = mock.MagicMock()
        mock_service_class.return_value = mock_service
        
        # Mock create_presigned_urls to return test URLs
        mock_service.create_presigned_urls.return_value = (
            "https://test-storage/upload-url",
            "https://test-storage/file-url"
        )
        
        yield mock_service

class TestUploadsRoutes:
    """Test suite for uploads routes"""
    
    def test_create_presigned_upload_success(self, mock_db, mock_storage_service):
        """Test successful presigned upload creation"""
        # Valid request data
        request_data = {
            "filename": "test.jpg",
            "mime": "image/jpeg",
            "kind": "IMAGE",
            "content_length": 5 * 1024 * 1024  # 5MB
        }
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 200
        assert response.json() == {
            "uploadUrl": "https://test-storage/upload-url",
            "fileUrl": "https://test-storage/file-url"
        }
        
        # Check storage service was called correctly
        mock_storage_service.create_presigned_urls.assert_called_with(
            PresignKind.IMAGE,
            "test.jpg",
            "image/jpeg",
            5 * 1024 * 1024
        )
    
    def test_create_presigned_upload_no_content_length(self, mock_db, mock_storage_service):
        """Test presigned upload creation without content length"""
        # Request data without content_length
        request_data = {
            "filename": "test.jpg",
            "mime": "image/jpeg",
            "kind": "IMAGE"
        }
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 200
        assert response.json() == {
            "uploadUrl": "https://test-storage/upload-url",
            "fileUrl": "https://test-storage/file-url"
        }
        
        # Check storage service was called correctly (with None content_length)
        mock_storage_service.create_presigned_urls.assert_called_with(
            PresignKind.IMAGE,
            "test.jpg",
            "image/jpeg",
            None
        )
    
    def test_create_presigned_upload_invalid_kind(self, mock_db):
        """Test presigned upload with invalid kind"""
        # Request data with invalid kind
        request_data = {
            "filename": "test.jpg",
            "mime": "image/jpeg",
            "kind": "INVALID_KIND"  # Invalid
        }
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 422  # Validation error
    
    def test_create_presigned_upload_missing_fields(self, mock_db):
        """Test presigned upload with missing required fields"""
        # Request data missing filename
        request_data = {
            "mime": "image/jpeg",
            "kind": "IMAGE"
        }
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 422  # Validation error
    
    def test_create_presigned_upload_validation_error(self, mock_db, mock_storage_service):
        """Test presigned upload with validation error from storage service"""
        # Valid request data
        request_data = {
            "filename": "test.gif",
            "mime": "image/gif",  # Not allowed
            "kind": "IMAGE"
        }
        
        # Mock validation error
        mock_storage_service.create_presigned_urls.side_effect = ValidationError(
            "Unsupported MIME type: image/gif"
        )
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 400
        assert "Unsupported MIME type" in response.json()["detail"]
    
    def test_create_presigned_upload_storage_error(self, mock_db, mock_storage_service):
        """Test presigned upload with storage error"""
        # Valid request data
        request_data = {
            "filename": "test.jpg",
            "mime": "image/jpeg",
            "kind": "IMAGE"
        }
        
        # Mock storage error
        mock_storage_service.create_presigned_urls.side_effect = StorageError(
            "Failed to generate presigned URL"
        )
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 500
        assert "Failed to generate presigned URL" in response.json()["detail"]
    
    def test_create_presigned_upload_invalid_content_length(self, mock_db):
        """Test presigned upload with invalid content length"""
        # Request data with invalid content length
        request_data = {
            "filename": "test.jpg",
            "mime": "image/jpeg",
            "kind": "IMAGE",
            "content_length": -1  # Invalid
        }
        
        # Make request
        response = client.post("/uploads/presign", json=request_data)
        
        # Check response
        assert response.status_code == 422  # Validation error