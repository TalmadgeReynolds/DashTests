from typing import Optional, Dict, Any


class LipSyncException(Exception):
    """Base exception for all app-specific exceptions"""
    code = "INTERNAL_ERROR"
    status_code = 500
    message = "An internal error occurred"

    def __init__(self, message: Optional[str] = None, detail: Optional[Dict[str, Any]] = None, request_id: Optional[str] = None):
        self.message = message or self.message
        self.detail = detail
        self.request_id = request_id
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert the exception to a dictionary for response"""
        result = {
            "status": "error",
            "code": self.code,
            "message": self.message
        }
        
        if self.detail:
            result["detail"] = self.detail
            
        if self.request_id:
            result["request_id"] = self.request_id
            
        return result


class ValidationError(LipSyncException):
    """Raised when input validation fails"""
    code = "VALIDATION_ERROR"
    status_code = 400
    message = "Validation error"


class NotFoundError(LipSyncException):
    """Raised when a resource is not found"""
    code = "NOT_FOUND"
    status_code = 404
    message = "Resource not found"


class ProviderError(LipSyncException):
    """Raised when a provider API returns an error"""
    code = "PROVIDER_ERROR"
    status_code = 502
    message = "Provider API error"


class TransientProviderError(ProviderError):
    """Raised when a provider API returns a transient error (retryable)"""
    code = "TRANSIENT_PROVIDER_ERROR"
    status_code = 503
    message = "Temporary provider API error"


class ProviderTimeoutError(TransientProviderError):
    """Raised when a provider API request times out"""
    code = "PROVIDER_TIMEOUT"
    message = "Provider API request timed out"


class ProviderRateLimitError(TransientProviderError):
    """Raised when a provider API rate limit is exceeded"""
    code = "PROVIDER_RATE_LIMIT"
    message = "Provider API rate limit exceeded"


class PostFxError(LipSyncException):
    """Raised when post-processing fails"""
    code = "POSTFX_ERROR"
    status_code = 500
    message = "Post-processing failed"


class StorageError(LipSyncException):
    """Raised when storage operations fail"""
    code = "STORAGE_ERROR"
    status_code = 500
    message = "Storage operation failed"


class InvalidSignatureError(LipSyncException):
    """Raised when webhook signature verification fails"""
    code = "INVALID_SIGNATURE"
    status_code = 401
    message = "Invalid webhook signature"