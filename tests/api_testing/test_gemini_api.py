#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

print("===== Testing Gemini API Access =====")

# Get environment variables
api_key = os.getenv("VEO_API_KEY")
project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
location = os.getenv("GOOGLE_CLOUD_LOCATION")

print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
print(f"Project ID: {project_id}")
print(f"Location: {location}")

# Set up headers - use the x-goog-api-key header that worked for Imagen
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key
}

# List of models to try - include both legacy formats and newer ones
gemini_models = [
    "gemini-1.0-pro",
    "gemini-pro",
    "gemini-pro-vision",
    "gemini-1.5-pro",
    "gemini-1.5-flash"
]

for model in gemini_models:
    print(f"\nTesting model: {model}")
    
    # Build the API URL - try both endpoints
    endpoints = [
        # Standard format
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:generateContent",
        # Alternative format
        f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:predict"
    ]
    
    for url in endpoints:
        print(f"\nTrying endpoint: {url}")
        
        # Create a simple request payload - adjust based on model
        if ":generateContent" in url:
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
        else:
            payload = {
                "instances": [
                    {
                        "prompt": "Write a one-word response: Working"
                    }
                ],
                "parameters": {
                    "temperature": 0,
                    "maxOutputTokens": 5
                }
            }
        
        try:
            # Make the API request
            print(f"Making request with payload structure: {list(payload.keys())}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            print(f"Status code: {response.status_code}")
            
            if response.status_code == 200:
                print("SUCCESS! The API key has access to this model.")
                print(f"Response: {json.dumps(response.json(), indent=2)[:500]}")
                # Exit loops if successful
                break
            else:
                print(f"Error response: {response.text[:500]}")
        except Exception as e:
            print(f"Request error: {str(e)}")
    
    # Exit the model loop if we found a working one
    if response.status_code == 200:
        break

print("\n===== Test Complete =====")