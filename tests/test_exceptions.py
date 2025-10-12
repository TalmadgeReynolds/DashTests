import pytest
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import pytest_asyncio

from backend.exceptions import (
    LipSyncException,
    ValidationError,
    NotFoundError,
    ProviderError,
    TransientProviderError,
    ProviderTimeoutError,
    ProviderRateLimitError,
    PostFxError,
    StorageError,
    InvalidSignatureError
)


class TestExceptions:
    """Test suite for custom exceptions"""
    
    def test_lipsync_exception_base(self):
        """Test the base LipSyncException class"""
        # Create with default values
        exc = LipSyncException()
        assert exc.code == "INTERNAL_ERROR"
        assert exc.status_code == 500
        assert exc.message == "An internal error occurred"
        assert exc.detail is None
        assert exc.request_id is None
        
        # Convert to dict
        result = exc.to_dict()
        assert result["status"] == "error"
        assert result["code"] == "INTERNAL_ERROR"
        assert result["message"] == "An internal error occurred"
        assert "detail" not in result
        assert "request_id" not in result
        
        # Create with custom values
        exc = LipSyncException(
            message="Custom error message",
            detail={"error_type": "custom"},
            request_id="req-123456"
        )
        assert exc.message == "Custom error message"
        assert exc.detail == {"error_type": "custom"}
        assert exc.request_id == "req-123456"
        
        # Convert to dict
        result = exc.to_dict()
        assert result["status"] == "error"
        assert result["code"] == "INTERNAL_ERROR"
        assert result["message"] == "Custom error message"
        assert result["detail"] == {"error_type": "custom"}
        assert result["request_id"] == "req-123456"
    
    def test_validation_error(self):
        """Test ValidationError exception"""
        exc = ValidationError()
        assert exc.code == "VALIDATION_ERROR"
        assert exc.status_code == 400
        assert exc.message == "Validation error"
        
        # With custom values
        exc = ValidationError(
            message="Invalid input data",
            detail={"field": "username", "error": "must be at least 3 characters"}
        )
        assert exc.message == "Invalid input data"
        assert exc.detail == {"field": "username", "error": "must be at least 3 characters"}
        
        # Convert to dict
        result = exc.to_dict()
        assert result["code"] == "VALIDATION_ERROR"
        assert result["message"] == "Invalid input data"
        assert result["detail"]["field"] == "username"
    
    def test_not_found_error(self):
        """Test NotFoundError exception"""
        exc = NotFoundError()
        assert exc.code == "NOT_FOUND"
        assert exc.status_code == 404
        assert exc.message == "Resource not found"
        
        # With custom message
        exc = NotFoundError(message="Job not found")
        assert exc.message == "Job not found"
    
    def test_provider_error(self):
        """Test ProviderError exception"""
        exc = ProviderError()
        assert exc.code == "PROVIDER_ERROR"
        assert exc.status_code == 502
        assert exc.message == "Provider API error"
        
        # With custom values
        exc = ProviderError(
            message="Heygen API error",
            detail={"provider": "heygen", "error_code": "H101"}
        )
        assert exc.message == "Heygen API error"
        assert exc.detail["provider"] == "heygen"
    
    def test_transient_provider_error(self):
        """Test TransientProviderError exception"""
        exc = TransientProviderError()
        assert exc.code == "TRANSIENT_PROVIDER_ERROR"
        assert exc.status_code == 503
        assert exc.message == "Temporary provider API error"
        
        # Should inherit from ProviderError
        assert isinstance(exc, ProviderError)
    
    def test_provider_timeout_error(self):
        """Test ProviderTimeoutError exception"""
        exc = ProviderTimeoutError()
        assert exc.code == "PROVIDER_TIMEOUT"
        assert exc.status_code == 503  # Inherited from TransientProviderError
        assert exc.message == "Provider API request timed out"
        
        # Should inherit from TransientProviderError
        assert isinstance(exc, TransientProviderError)
    
    def test_provider_rate_limit_error(self):
        """Test ProviderRateLimitError exception"""
        exc = ProviderRateLimitError()
        assert exc.code == "PROVIDER_RATE_LIMIT"
        assert exc.status_code == 503  # Inherited from TransientProviderError
        assert exc.message == "Provider API rate limit exceeded"
        
        # Should inherit from TransientProviderError
        assert isinstance(exc, TransientProviderError)
        
        # With custom values
        exc = ProviderRateLimitError(
            message="Rate limit exceeded, retry after 30s",
            detail={"retry_after": 30}
        )
        assert exc.message == "Rate limit exceeded, retry after 30s"
        assert exc.detail["retry_after"] == 30
    
    def test_postfx_error(self):
        """Test PostFxError exception"""
        exc = PostFxError()
        assert exc.code == "POSTFX_ERROR"
        assert exc.status_code == 500
        assert exc.message == "Post-processing failed"
        
        # With custom values
        exc = PostFxError(
            message="FFmpeg processing failed",
            detail={"error": "Invalid video format"}
        )
        assert exc.message == "FFmpeg processing failed"
        assert exc.detail["error"] == "Invalid video format"
    
    def test_storage_error(self):
        """Test StorageError exception"""
        exc = StorageError()
        assert exc.code == "STORAGE_ERROR"
        assert exc.status_code == 500
        assert exc.message == "Storage operation failed"
        
        # With custom values
        exc = StorageError(
            message="Failed to upload file to S3",
            detail={"bucket": "my-bucket", "key": "videos/test.mp4"}
        )
        assert exc.message == "Failed to upload file to S3"
        assert exc.detail["bucket"] == "my-bucket"
    
    def test_invalid_signature_error(self):
        """Test InvalidSignatureError exception"""
        exc = InvalidSignatureError()
        assert exc.code == "INVALID_SIGNATURE"
        assert exc.status_code == 401
        assert exc.message == "Invalid webhook signature"


class TestExceptionHandler:
    """Test suite for exception handlers"""
    
    @pytest_asyncio.fixture
    async def app(self):
        """Create a FastAPI test app with exception handlers"""
        app = FastAPI()
        
        # Register our own exception handlers
        @app.exception_handler(LipSyncException)
        async def lipsync_exception_handler(request: Request, exc: LipSyncException):
            """Handle LipSync application exceptions"""
            return JSONResponse(
                status_code=exc.status_code,
                content=exc.to_dict()
            )
        
        # Add test routes that raise different exceptions
        @app.get("/validation-error")
        def validation_error_route():
            raise ValidationError(message="Test validation error")
            
        @app.get("/not-found-error")
        def not_found_error_route():
            raise NotFoundError(message="Test resource not found")
            
        @app.get("/provider-error")
        def provider_error_route():
            raise ProviderError(message="Test provider error")
            
        @app.get("/storage-error")
        def storage_error_route():
            raise StorageError(message="Test storage error")
        
        return app
    
    @pytest.mark.asyncio
    async def test_validation_error_handler(self, app):
        """Test validation error handler"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/validation-error")
        
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"
        assert data["code"] == "VALIDATION_ERROR"
        assert data["message"] == "Test validation error"
    
    @pytest.mark.asyncio
    async def test_not_found_error_handler(self, app):
        """Test not found error handler"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/not-found-error")
        
        assert response.status_code == 404
        data = response.json()
        assert data["status"] == "error"
        assert data["code"] == "NOT_FOUND"
        assert data["message"] == "Test resource not found"
    
    @pytest.mark.asyncio
    async def test_provider_error_handler(self, app):
        """Test provider error handler"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/provider-error")
        
        assert response.status_code == 502
        data = response.json()
        assert data["status"] == "error"
        assert data["code"] == "PROVIDER_ERROR"
        assert data["message"] == "Test provider error"
    
    @pytest.mark.asyncio
    async def test_storage_error_handler(self, app):
        """Test storage error handler"""
        from fastapi.testclient import TestClient
        
        client = TestClient(app)
        response = client.get("/storage-error")
        
        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert data["code"] == "STORAGE_ERROR"
        assert data["message"] == "Test storage error"