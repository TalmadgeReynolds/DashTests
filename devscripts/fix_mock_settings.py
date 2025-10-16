#!/usr/bin/env python3
import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Print environment variables
print("Environment variables loaded from .env:")
print(f"MOCK_PROVIDERS: {os.getenv('MOCK_PROVIDERS')}")
print(f"STORAGE_MOCK_MODE: {os.getenv('STORAGE_MOCK_MODE')}")

# Check if the value is interpreted as True/False in Python
print(f"\nPython bool conversion:")
print(f"bool('{os.getenv('MOCK_PROVIDERS')}') => {bool(os.getenv('MOCK_PROVIDERS'))}")
print("Note: Any non-empty string will be True in Python")

# Fix the environment variable directly
os.environ['MOCK_PROVIDERS'] = 'False'
print("\nUpdated MOCK_PROVIDERS to 'False'")

# Now test by importing the settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.utils.settings import get_settings
settings = get_settings()

print("\nSettings after update:")
print(f"settings.MOCK_PROVIDERS = {settings.MOCK_PROVIDERS}")
print(f"settings.STORAGE_MOCK_MODE = {settings.STORAGE_MOCK_MODE}")
print(f"Mock storage used: {settings.STORAGE_MOCK_MODE or settings.MOCK_PROVIDERS}")