import pytest
import os
import sys
from pathlib import Path

# Add project root to path so we can import backend modules
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment variables
os.environ.setdefault("ENV", "test")
os.environ.setdefault("WEBHOOK_SECRET_HEYGEN", "test-webhook-secret")
os.environ.setdefault("STORAGE_ENDPOINT", "localhost:9000")
os.environ.setdefault("STORAGE_ACCESS_KEY", "test-access-key")
os.environ.setdefault("STORAGE_SECRET_KEY", "test-secret-key")
os.environ.setdefault("STORAGE_BUCKET", "test-bucket")
os.environ.setdefault("STORAGE_PUBLIC_ENDPOINT", "http://localhost:9000")
os.environ.setdefault("STORAGE_USE_SSL", "false")
os.environ.setdefault("VEO3_MOCK_MODE", "true")
os.environ.setdefault("HEYGEN_MOCK_MODE", "true")
os.environ.setdefault("ELEVENLABS_MOCK_MODE", "true")
os.environ.setdefault("MOCK_PROVIDERS", "true")