#!/usr/bin/env python3

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{BOLD}{YELLOW}{'='*60}{RESET}")
    print(f"{BOLD}{YELLOW}{text.center(60)}{RESET}")
    print(f"{BOLD}{YELLOW}{'='*60}{RESET}\n")

def list_available_models():
    """List available models for Google AI Studio"""
    print_header("Listing Available Models for Google AI Studio")
    
    api_key = os.getenv("VEO3_API_KEY")
    if not api_key:
        print(f"{RED}VEO3 API key not found in .env file{RESET}")
        return
    
    print(f"API Key: {api_key[:5]}...{api_key[-5:]}")
    
    # Try multiple API versions
    versions = ["v1", "v1beta"]
    
    for version in versions:
        url = f"https://generativelanguage.googleapis.com/{version}/models?key={api_key}"
        
        print(f"\nTrying to list models with API version: {version}")
        
        try:
            response = requests.get(url, timeout=15)
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                models = response.json()
                print(f"{GREEN}Successfully retrieved models list!{RESET}")
                
                if "models" in models and models["models"]:
                    print(f"Available models ({len(models['models'])}):")
                    
                    # Sort models by name for better readability
                    sorted_models = sorted(models["models"], key=lambda x: x.get("name", ""))
                    
                    for model in sorted_models:
                        name = model.get("name", "").split("/")[-1] if "name" in model else "Unknown"
                        display_name = model.get("displayName", "No display name")
                        support_generation = "generateContent" in model.get("supportedGenerationMethods", [])
                        
                        status = f"{GREEN}✓{RESET}" if support_generation else f"{RED}✗{RESET}"
                        print(f"  {status} {name:20} - {display_name}")
                        
                    # Recommend models that support content generation
                    supported_models = [
                        model.get("name", "").split("/")[-1]
                        for model in models["models"]
                        if "generateContent" in model.get("supportedGenerationMethods", [])
                    ]
                    
                    if supported_models:
                        print(f"\n{GREEN}Models that support content generation:{RESET}")
                        for model in supported_models[:5]:  # Show top 5 models
                            print(f"  - {model}")
                        
                        if len(supported_models) > 5:
                            print(f"  - ...and {len(supported_models) - 5} more")
                        
                        print(f"\n{YELLOW}Recommended model to try:{RESET} {supported_models[0]}")
                    else:
                        print(f"\n{RED}No models found that support content generation{RESET}")
                else:
                    print(f"{RED}No models found in the response{RESET}")
                
                # Return after successful API call
                return supported_models[0] if supported_models else None
            else:
                print(f"{RED}Failed to list models: {response.text[:200]}{RESET}")
        except Exception as e:
            print(f"{RED}Error: {str(e)}{RESET}")
    
    print(f"{RED}Failed to list models with all API versions{RESET}")
    return None

def test_model_with_key(model_name=None):
    """Test a specific model with the API key"""
    if not model_name:
        print(f"{RED}No model name provided{RESET}")
        return False
    
    print_header(f"Testing Model: {model_name}")
    
    api_key = os.getenv("VEO3_API_KEY")
    if not api_key:
        print(f"{RED}VEO3 API key not found in .env file{RESET}")
        return False
    
    # Try multiple API versions
    versions = ["v1beta", "v1"]
    
    for version in versions:
        url = f"https://generativelanguage.googleapis.com/{version}/models/{model_name}:generateContent?key={api_key}"
        
        print(f"Trying API version: {version}")
        print(f"URL: {url}")
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
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
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=15)
            
            print(f"Response status code: {response.status_code}")
            
            if response.status_code == 200:
                print(f"{GREEN}Success! The model responded correctly.{RESET}")
                
                # Parse the response
                response_json = response.json()
                if "candidates" in response_json and len(response_json["candidates"]) > 0:
                    try:
                        text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                        print(f"{GREEN}Generated text:{RESET} {text}")
                        return True
                    except (KeyError, IndexError) as e:
                        print(f"{RED}Response format unexpected: {str(e)}{RESET}")
                        print(f"Raw response: {json.dumps(response_json, indent=2)[:200]}...")
                        return True  # Still valid since we got a 200 response
                else:
                    print(f"{YELLOW}No candidates found in response{RESET}")
                    print(f"Raw response: {json.dumps(response_json, indent=2)[:200]}...")
                    return True  # Still valid since we got a 200 response
            else:
                print(f"{RED}Failed: {response.text[:200]}{RESET}")
        except Exception as e:
            print(f"{RED}Error: {str(e)}{RESET}")
    
    print(f"{RED}Failed to test model with all API versions{RESET}")
    return False

if __name__ == "__main__":
    recommended_model = list_available_models()
    
    if recommended_model:
        print(f"\n{YELLOW}Testing with recommended model: {recommended_model}{RESET}")
        test_model_with_key(recommended_model)
    else:
        print(f"\n{RED}No suitable model found to test{RESET}")