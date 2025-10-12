#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("===== Testing Imagen API Access =====")

# Get environment variables
api_key = os.getenv("VEO_API_KEY")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
print(f"Project ID: {project_id}")
print(f"Location: {location}")

# Set up headers - use the x-goog-api-key header
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key
}

# List of models to try
imagen_models = [
    "imagen-3.0-generate-001",
    "imagen-3.0-fast-generate-001",
    "imagen-4.0-generate-001",
    "imagen-4.0-fast-generate-001"
]

for model in imagen_models:
    print(f"\nTesting model: {model}")
    
    # Build the API URL
    url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:predict"
    
    # Create a simple request payload
    payload = {
        "instances": [
            {
                "prompt": "A simple test image of a blue circle"
            }
        ],
        "parameters": {
            "sampleCount": 1
        }
    }
    
    try:
        # Make the API request
        print(f"Making request to: {url}")
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            print("SUCCESS! The API key has access to this model.")
            # Don't print the entire response since it contains the image data
            print("Response contains image data (not shown)")
            print(f"Response keys: {list(response.json().keys())}")
            break
        else:
            print(f"Error response: {response.text[:500]}")
    except Exception as e:
        print(f"Request error: {str(e)}")

print("\n===== Test Complete =====")