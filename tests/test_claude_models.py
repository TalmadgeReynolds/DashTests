#!/usr/bin/env python3
"""
Test which Claude models are available with your API key.
"""
import os
import sys
from pathlib import Path
from anthropic import Anthropic
import requests

# Add parent directory to path to import from backend
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv()

# Get API key from environment
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    print("ERROR: ANTHROPIC_API_KEY not set in .env file")
    exit(1)

client = Anthropic(api_key=api_key)

# First, try to list available models using the Models API
print("Fetching available models from Anthropic API...\n")
try:
    response = requests.get(
        "https://api.anthropic.com/v1/models",
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    )
    if response.status_code == 200:
        models_data = response.json()
        print("✅ Available models for your API key:\n")
        for model in models_data.get("data", []):
            model_id = model.get("id", "unknown")
            display_name = model.get("display_name", "")
            created_at = model.get("created_at", "")
            print(f"  • {model_id}")
            if display_name:
                print(f"    Name: {display_name}")
            if created_at:
                print(f"    Created: {created_at}")
            print()
    else:
        print(f"⚠️  Could not fetch models list (status {response.status_code})")
        print("Falling back to manual testing...\n")
except Exception as e:
    print(f"⚠️  Error fetching models: {e}")
    print("Falling back to manual testing...\n")

# List of Claude models to test (from most recent to oldest)
models_to_test = [
    "claude-3-5-sonnet-20241022",  # Oct 2024
    "claude-3-5-sonnet-20240620",  # June 2024
    "claude-3-opus-20240229",      # Feb 2024 (most capable)
    "claude-3-sonnet-20240229",    # Feb 2024
    "claude-3-haiku-20240307",     # March 2024 (fastest)
]

print("Testing Claude models with your API key...\n")

for model in models_to_test:
    try:
        print(f"Testing {model}... ", end="", flush=True)
        response = client.messages.create(
            model=model,
            max_tokens=10,
            messages=[
                {"role": "user", "content": "Say 'test successful'"}
            ]
        )
        print(f"✅ WORKS - Response: {response.content[0].text}")
    except Exception as e:
        error_msg = str(e)
        if "not_found_error" in error_msg:
            print(f"❌ NOT FOUND - Model doesn't exist or not available")
        elif "permission" in error_msg.lower():
            print(f"❌ PERMISSION DENIED - API key doesn't have access")
        else:
            print(f"❌ ERROR - {error_msg[:100]}")

print("\n✅ = Model works with your API key")
print("❌ = Model not available")
