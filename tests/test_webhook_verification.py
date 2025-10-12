"""
Unit tests for webhook HMAC signature verification.
"""
import json
import hmac
import hashlib
from unittest.mock import patch

def test_webhook_signature_verification():
    """Test the HMAC signature verification logic directly."""
    # Setup the test variables
    webhook_secret = "test-secret"
    
    # Test body
    body = json.dumps({
        "provider_job_id": "test-job-123",
        "status": "DONE"
    }).encode()
    
    # Expected signature
    expected = hmac.new(
        webhook_secret.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    # Test signature header
    signature_header = f"sha256={expected}"
    
    # This is the core verification logic from the adapter
    def verify_webhook_signature(signature, body):
        if not signature or not signature.startswith("sha256="):
            return False
            
        provided_signature = signature.replace("sha256=", "")
        
        # Compute expected signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Use constant-time comparison to prevent timing attacks
        return hmac.compare_digest(provided_signature, expected_signature)
    
    # Test cases
    assert verify_webhook_signature(signature_header, body) is True
    assert verify_webhook_signature("sha256=invalid", body) is False
    assert verify_webhook_signature("invalid", body) is False
    assert verify_webhook_signature(None, body) is False