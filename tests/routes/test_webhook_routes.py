"""
Tests for webhook routes and HMAC verification
"""
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock

import pytest

from backend.exceptions import InvalidSignatureError
from backend.adapters.heygen_adapter import HeygenAdapter


class TestHeygenWebhook:
    """Test suite for Heygen webhook HMAC verification"""
    
    def test_hmac_verification_implementation(self):
        """Test the HMAC verification implementation for webhooks"""
        # Create a webhook secret
        webhook_secret = "test-secret"
        
        # Create a test body
        payload = {
            "provider_job_id": "test-job-123",
            "status": "DONE",
            "output_url": "https://example.com/video.mp4",
            "timestamp": "2025-10-11T12:00:00Z"
        }
        body = json.dumps(payload).encode()
        
        # Calculate the expected signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Create a signature header
        signature_header = f"sha256={expected_signature}"
        
        # Mock the settings to return our test secret
        with patch('backend.adapters.heygen_adapter.settings') as mock_settings:
            # Set the webhook secret
            mock_settings.WEBHOOK_SECRET_HEYGEN = webhook_secret
            
            adapter = HeygenAdapter()
            
            # Verify that the correct signature passes
            assert adapter.verify_webhook_signature(signature_header, body) is True
            
            # Verify that an incorrect signature fails
            assert adapter.verify_webhook_signature("sha256=invalid-signature", body) is False
            
            # Verify that a missing signature prefix fails
            assert adapter.verify_webhook_signature(expected_signature, body) is False
            
            # Verify that None signature fails safely
            assert adapter.verify_webhook_signature(None, body) is False
    
    def test_constant_time_comparison(self):
        """Test that comparison is done in constant time"""
        # This is a basic test to ensure hmac.compare_digest is being used
        with patch('hmac.compare_digest') as mock_compare:
            mock_compare.return_value = True
            
            adapter = HeygenAdapter()
            result = adapter.verify_webhook_signature("sha256=test", b"test")
            
            # Verify that compare_digest was called
            mock_compare.assert_called_once()

    def test_hmac_verification_implementation(self):
        """Test the actual HMAC verification implementation"""
        # This test verifies the actual implementation of the verify_webhook_signature method
        from backend.adapters.heygen_adapter import HeygenAdapter
        
        # Create a webhook secret
        webhook_secret = "test-secret"
        
        # Create a test body
        body = json.dumps({
            "provider_job_id": "test-job-123",
            "status": "DONE"
        }).encode()
        
        # Calculate the expected signature
        expected_signature = hmac.new(
            webhook_secret.encode(),
            body,
            hashlib.sha256
        ).hexdigest()
        
        # Create a signature header
        signature_header = f"sha256={expected_signature}"
        
        # Create an adapter instance with the test secret
        adapter = HeygenAdapter()
        
        # Manually set the webhook secret since we're not using mocks
        adapter.webhook_secret = webhook_secret
        
        # Verify that the correct signature passes
        assert adapter.verify_webhook_signature(signature_header, body) is True
        
        # Verify that an incorrect signature fails
        assert adapter.verify_webhook_signature("sha256=invalid-signature", body) is False
        
        # Verify that a missing signature prefix fails
        assert adapter.verify_webhook_signature(expected_signature, body) is False