#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("===== Testing Vertex AI API Key =====")

# Get environment variables
api_key = os.getenv("VEO_API_KEY")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

# Print configuration
print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
print(f"Project ID: {project_id}")
print(f"Location: {location}")

# Set up headers
if api_key.startswith("AQ."):
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key
    }
else:
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": api_key  # Changed from Authorization: Bearer to use x-goog-api-key
    }

print("\n1. Attempting to list available models...")
try:
    # Try to list available models in the project
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models"
    response = requests.get(url, headers=headers)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        # Successfully retrieved models
        models = response.json()
        print("Available models:")
        for model in models.get("models", [])[:5]:  # Show first 5 models
            print(f"- {model.get('name')}")
        
        if len(models.get("models", [])) > 5:
            print(f"...and {len(models.get('models', [])) - 5} more")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Error listing models: {str(e)}")

print("\n2. Testing with gemini-pro model...")
try:
    # Try a simple request to a commonly available model
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/gemini-pro:generateContent"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Write a one-word response: Working"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0,
            "maxOutputTokens": 5
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2)[:200] + "...")
        print("Test succeeded!")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Error testing model: {str(e)}")

print("\n===== Test Complete =====")