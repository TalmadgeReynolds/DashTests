#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

print("==== Testing Direct Google API Access ====")

# Get environment variables
api_key = os.getenv("VEO_API_KEY")

# Try a simpler Google API that should be broadly accessible
url = "https://language.googleapis.com/v1/documents:analyzeEntities"
headers = {
    "Content-Type": "application/json",
    "x-goog-api-key": api_key
}

payload = {
    "document": {
        "type": "PLAIN_TEXT",
        "content": "Google Cloud Platform is a suite of cloud computing services."
    },
    "encodingType": "UTF8"
}

try:
    print("Testing Natural Language API...")
    response = requests.post(url, headers=headers, json=payload)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print("Response:")
        print(json.dumps(result, indent=2)[:200] + "...")
    else:
        print(f"Error: {response.text[:200]}")
except Exception as e:
    print(f"Error: {str(e)}")

print("==== Test Complete ====")