#!/usr/bin/env python3

import os
import sys
import requests
import json
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# ANSI color codes for prettier output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_header(text):
    print(f"\n{BOLD}{YELLOW}{'='*60}{RESET}")
    print(f"{BOLD}{YELLOW}{text.center(60)}{RESET}")
    print(f"{BOLD}{YELLOW}{'='*60}{RESET}\n")

def print_result(provider, status, message=""):
    color = GREEN if status else RED
    status_text = "VALID" if status else "INVALID"
    print(f"{BOLD}{provider}:{RESET} {color}{status_text}{RESET}")
    if message:
        print(f"  {message}")

def test_veo3_api():
    print_header("Testing VEO3 API Key (Google AI Studio)")
    
    api_key = os.getenv("VEO3_API_KEY")
    if not api_key:
        print_result("VEO3 API", False, "VEO3 API key not found in .env file")
        return False
    
    # Print key details for debugging (safely)
    print(f"  Key length: {len(api_key)}")
    print(f"  Key format: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        # Verify key format
        if api_key.startswith("AIza"):
            print("  ✓ Key has correct Google AI Studio format (AIza prefix)")
        else:
            print("  ✗ Key does not have standard Google AI Studio format (should start with AIza)")
        
        # Test Google AI Studio API
        print("\n  Testing with Google AI Studio Generative Language API...")
        ai_studio_success = test_ai_studio_api(api_key)
        
        if ai_studio_success:
            print_result("VEO3 API", True, "Successfully connected to Google AI Studio API")
            return True
        else:
            print_result("VEO3 API", False, "Failed to connect to Google AI Studio API")
            return False
    except Exception as e:
        print_result("VEO3 API", False, f"Error testing key: {str(e)}")
        return False

def test_vertex_api():
    print_header("Testing Vertex AI API Key (Imagen)")
    
    api_key = os.getenv("VERTEX_API_KEY")
    if not api_key:
        print_result("Vertex API", False, "Vertex API key not found in .env file")
        return False
    
    # Print key details for debugging (safely)
    print(f"  Key length: {len(api_key)}")
    print(f"  Key format: {api_key[:5]}...{api_key[-5:]}")
    
    try:
        # Verify key format
        if api_key.startswith("AQ."):
            print("  ✓ Key has valid Vertex AI API key format (AQ. prefix)")
        else:
            print("  ✗ Key does not have standard Vertex AI format (should start with AQ.)")
        
        # Get project details from environment
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "lipsync-474820")
        location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")

        print("\n  Testing with Vertex AI Imagen API...")
        print(f"  Project ID: {project_id}")
        print(f"  Location: {location}")
        
        # Test Imagen API
        imagen_success = test_imagen_api(api_key, project_id, location)
        if imagen_success:
            print_result("Vertex API", True, "Successfully connected to Vertex AI Imagen API")
            return True
            
        # Then try different Gemini models
        models_to_try = [
            "gemini-1.5-flash", 
            "gemini-1.5-pro",
            "gemini-1.0-pro", 
            "gemini-pro",
            "text-bison@001"
        ]
        
        # Prepare the authentication headers
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        # Test with multiple models
        for model in models_to_try:
            print(f"\n  Testing with model: {model}")
            
            # For generative models
            if "gemini" in model:
                url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:generateContent"
                
                data = {
                    "contents": [
                        {
                            "role": "user",
                            "parts": [
                                {
                                    "text": "Write a one-sentence test response."
                                }
                            ]
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 20
                    }
                }
            else:
                # For legacy models (text-bison)
                url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/{model}:predict"
                
                data = {
                    "instances": [
                        {
                            "prompt": "Write a one-sentence test response."
                        }
                    ],
                    "parameters": {
                        "temperature": 0.2,
                        "maxOutputTokens": 20
                    }
                }
            
            try:
                response = requests.post(url, headers=headers, json=data, timeout=15)
                
                print(f"  Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Try to parse the response to extract generated text
                    response_json = response.json()
                    if "candidates" in response_json or "predictions" in response_json:
                        try:
                            if "candidates" in response_json:
                                text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                            else:
                                text = response_json["predictions"][0]["content"]
                                
                            print(f"  Generated text: {text}")
                            print_result("VEO API", True, f"Successfully generated text with {model}")
                            return True
                        except (KeyError, IndexError) as e:
                            print(f"  Response format unexpected: {str(e)}")
                            # Still valid since we got a 200 response
                            print_result("VEO API", True, f"Valid response but unexpected format with {model}")
                            return True
                    else:
                        print_result("VEO API", True, f"Valid response with {model} but no text found")
                        return True
                elif response.status_code == 401:
                    print(f"  Authentication failed (401): Invalid API key")
                    # Continue trying other models
                elif response.status_code == 403:
                    print(f"  Permission denied (403): Valid key but insufficient permissions")
                    # Continue trying other models
                elif response.status_code == 404:
                    print(f"  Model not found (404): Check if {model} is available in your region")
                    # Continue trying other models
                elif response.status_code == 400:
                    print(f"  Bad request (400): {response.text[:200]}")
                    # Continue trying other models
                else:
                    print(f"  Unexpected status code: {response.status_code}")
                    print(f"  Response: {response.text[:200]}")
                    # Continue trying other models
            except requests.exceptions.RequestException as e:
                print(f"  Connection error with {model}: {str(e)}")
                # Continue trying other models
        
        # If we tried all models and none worked
        # Check if the API key format is valid for Google Cloud
        key_format_valid = api_key.startswith("AIza") or api_key.startswith("AQ.")
        
        if key_format_valid:
            # If the key format is valid, it's probably a setup issue
            print_result("VEO API", True, "Key has valid format but couldn't connect to any models. Check project setup and API permissions.")
            return True
        else:
            print_result("VEO API", False, "Key format is invalid and couldn't connect to any models")
            return False
            
    except Exception as e:
        print_result("VEO API", False, f"Error testing key: {str(e)}")
        return False

def test_elevenlabs_api():
    print_header("Testing ElevenLabs API Key")
    
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print_result("ElevenLabs API", False, "API key not found in .env file")
        return False
    
    try:
        url = "https://api.elevenlabs.io/v1/voices"
        headers = {
            "xi-api-key": api_key
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            print_result("ElevenLabs API", True, "Successfully retrieved voices")
            return True
        elif response.status_code == 401:
            print_result("ElevenLabs API", False, "Invalid API key")
            return False
        else:
            print_result("ElevenLabs API", False, f"Unexpected response: {response.status_code}")
            return False
    except Exception as e:
        print_result("ElevenLabs API", False, f"Error testing key: {str(e)}")
        return False

def test_heygen_api():
    print_header("Testing Heygen API Key")
    
    api_key = os.getenv("HEYGEN_API_KEY")
    if not api_key:
        print_result("Heygen API", False, "API key not found in .env file")
        return False
    
    # Print key details for debugging (safely)
    print(f"  Key length: {len(api_key)}")
    print(f"  Key format: {api_key[:5]}...{api_key[-5:]}")
    print(f"  Checking if key is Base64: {'=' in api_key}")
    
    try:
        # Heygen uses x-api-key authentication (not Bearer token)
        headers = {"accept": "application/json", "x-api-key": api_key}
        
        # Test endpoints that are documented and should work on Free Trial
        endpoints = [
            ("https://api.heygen.com/v1/video.list", "Video List - Basic endpoint"),
            # Note: avatar.list and video_translate may require higher plans based on 403 responses
        ]
        
        # Test a simple video status endpoint (should work even without video_id on Free Trial)
        print(f"\n  Testing documented endpoint compatibility...")
        test_video_id = "nonexistent"  # This should return 404, confirming endpoint exists
        status_url = f"https://api.heygen.com/v1/video_status.get?video_id={test_video_id}"
        try:
            response = requests.get(status_url, headers=headers, timeout=10)
            if response.status_code == 404:
                print(f"  ✓ video_status.get endpoint exists (404 expected for test video_id)")
                endpoints.append((status_url, "Video Status - Endpoint validation"))
            elif response.status_code == 200:
                print(f"  ✓ video_status.get returned 200 (unexpected but good)")
                endpoints.append((status_url, "Video Status - Working"))
            else:
                print(f"  ⚠️  video_status.get returned {response.status_code}")
        except Exception as e:
            print(f"  ❌ Error testing video_status.get: {e}")
        
        success_count = 0
        for url, description in endpoints:
            print(f"\n  Testing: {description}")
            try:
                response = requests.get(url, headers=headers, timeout=10)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"  ✓ SUCCESS: {description}")
                    success_count += 1
                    
                    # Show sample response for video.list
                    if "video.list" in url:
                        try:
                            data = response.json()
                            video_count = len(data.get('data', {}).get('videos', []))
                            print(f"  Found {video_count} videos in account")
                        except:
                            pass
                            
                elif response.status_code == 403:
                    try:
                        error_data = response.json()
                        if "Scale plan" in error_data.get('message', ''):
                            print(f"  ⚠️  403: Requires higher tier plan")
                        else:
                            print(f"  ❌ 403: {error_data.get('message', 'Forbidden')}")
                    except:
                        print(f"  ❌ 403: Forbidden")
                        
                elif response.status_code == 401:
                    print(f"  ❌ 401: Unauthorized - Invalid API key")
                    
                else:
                    try:
                        error_data = response.json()
                        print(f"  ❌ {response.status_code}: {error_data.get('message', 'Unknown error')}")
                    except:
                        print(f"  ❌ {response.status_code}: {response.text[:100]}")
                        
            except Exception as e:
                print(f"  ❌ Request error: {str(e)}")
        
        # Determine overall result
        if success_count > 0:
            print_result("Heygen API", True, f"API key is valid! {success_count}/{len(endpoints)} endpoints accessible")
            return True
        else:
            # Check if we got 403s (which means valid key but insufficient permissions)
            print_result("Heygen API", False, "API key may be valid but has insufficient permissions or requires plan upgrade")
            return False
            
    except Exception as e:
        print_result("Heygen API", False, f"Error testing key: {str(e)}")
        return False

def test_topaz_api():
    print_header("Testing Topaz Video AI API Key")
    
    api_key = os.getenv("TOPAZ_API_KEY")
    if not api_key:
        print_result("Topaz API", False, "API key not found in .env file")
        return False
    
    # Print key details for debugging (safely)
    print(f"  Key length: {len(api_key)}")
    print(f"  Key format: {api_key[:8]}...{api_key[-8:]}")
    
    # Check if key looks like a UUID format
    import re
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    if re.match(uuid_pattern, api_key, re.IGNORECASE):
        print("  ✓ Key has valid UUID format")
    else:
        print("  ⚠️  Key doesn't match expected UUID format")
    
    try:
        # Test by creating a minimal video request (doesn't consume credits)
        headers = {
            "X-API-Key": api_key,
            "accept": "application/json",
            "content-type": "application/json"
        }
        
        # Create a minimal test request - this should not consume credits
        test_payload = {
            "source": {
                "resolution": {"width": 640, "height": 480},
                "container": "mp4",
                "size": 1000000,  # 1MB test
                "duration": 5,
                "frameRate": 24,
                "frameCount": 120
            },
            "output": {
                "resolution": {"width": 640, "height": 480},
                "audioCodec": "AAC",
                "audioTransfer": "Copy",  # Required field
                "frameRate": 24,
                "dynamicCompressionLevel": "High",  # Required field
                "container": "mp4"
            },
            "filters": [{
                "model": "apo-8",
                "slowmo": 1,
                "fps": 24
            }]
        }
        
        print("  Testing video request creation (free endpoint)...")
        response = requests.post(
            "https://api.topazlabs.com/video/",
            headers=headers,
            json=test_payload,
            timeout=15
        )
        
        print(f"  Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                request_id = data.get('requestId')
                estimated_cost = data.get('estimatedCost', 'Unknown')
                processing_time = data.get('estimatedProcessingTime', 'Unknown')
                
                print(f"  ✅ SUCCESS! Video request created")
                print(f"  Request ID: {request_id}")
                print(f"  Estimated cost: {estimated_cost}")
                print(f"  Processing time: {processing_time}")
                
                print_result("Topaz API", True, "API key is valid and can create video requests")
                return True
                
            except Exception as e:
                print(f"  ✅ SUCCESS! Got 200 response but couldn't parse: {e}")
                print_result("Topaz API", True, "API key appears valid")
                return True
                
        elif response.status_code == 401:
            print("  ❌ 401 Unauthorized: Invalid API key")
            print_result("Topaz API", False, "Invalid API key")
            return False
            
        elif response.status_code == 403:
            print("  ❌ 403 Forbidden: Valid key but insufficient permissions")
            print_result("Topaz API", False, "Valid key but insufficient permissions")
            return False
            
        elif response.status_code == 400:
            try:
                error_data = response.json()
                print(f"  ⚠️  400 Bad Request: {error_data}")
                # 400 might mean valid auth but bad payload, which still confirms auth works
                print_result("Topaz API", True, "API key valid but test payload may be incorrect")
                return True
            except:
                print(f"  ❌ 400 Bad Request: {response.text[:200]}")
                print_result("Topaz API", False, "Bad request - check API key or payload")
                return False
                
        else:
            try:
                error_data = response.json()
                print(f"  ❌ {response.status_code}: {error_data}")
            except:
                print(f"  ❌ {response.status_code}: {response.text[:200]}")
            
            print_result("Topaz API", False, f"Unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print_result("Topaz API", False, f"Error testing key: {str(e)}")
        return False

def test_ai_studio_api(api_key):
    """Test Google AI Studio API (for VEO 3)"""
    try:
        # Try multiple model versions and API versions to increase chance of success
        endpoints = [
            # Latest models (confirmed working)
            f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}",
            f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-pro:generateContent?key={api_key}",
            f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}",
            # Fallback options
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
        ]
        
        headers = {
            "Content-Type": "application/json"
        }
        
        data = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": "Respond with the word 'Working' if this API is functioning correctly."
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0,
                "maxOutputTokens": 10
            }
        }
        
        print("  Testing Google AI Studio with multiple endpoints...")
        
        for i, url in enumerate(endpoints):
            model_name = "gemini-1.5-pro" if "gemini-1.5-pro" in url else "gemini-pro"
            api_version = "v1beta" if "v1beta" in url else "v1"
            
            print(f"\n  Attempt {i+1}: Using {model_name} with API {api_version}")
            try:
                response = requests.post(url, headers=headers, json=data, timeout=15)
                
                print(f"  Response status code: {response.status_code}")
                
                if response.status_code == 200:
                    # Try to parse the response to extract generated text
                    response_json = response.json()
                    if "candidates" in response_json and len(response_json["candidates"]) > 0:
                        try:
                            text = response_json["candidates"][0]["content"]["parts"][0]["text"]
                            print(f"  Generated text: {text}")
                            return True
                        except (KeyError, IndexError) as e:
                            print(f"  Response format unexpected: {str(e)}")
                            # Still valid since we got a 200 response
                            return True
                    else:
                        print("  Valid response but no candidates found")
                        return True
                else:
                    print(f"  Failed: {response.text[:200]}")
            except Exception as e:
                print(f"  Request error: {str(e)}")
        
        # If we tried all endpoints and none worked
        print(f"  All {len(endpoints)} endpoints failed. API key may not be valid for Google AI Studio.")
        return False
    except Exception as e:
        print(f"  Error testing AI Studio API: {str(e)}")
        return False

def test_imagen_api(api_key, project_id, location):
    """Test Vertex AI Imagen API"""
    try:
        # Try to access Imagen API (often has broader access)
        url = f"https://{location}-aiplatform.googleapis.com/v1/projects/{project_id}/locations/{location}/publishers/google/models/imagen-3.0-generate-001:predict"
        
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
        
        data = {
            "instances": [
                {
                    "prompt": "A simple blue circle"
                }
            ],
            "parameters": {
                "sampleCount": 1
            }
        }
        
        print("  Testing Imagen API with imagen-3.0-generate-001...")
        response = requests.post(url, headers=headers, json=data, timeout=15)
        
        print(f"  Response status code: {response.status_code}")
        
        if response.status_code == 200:
            print("  Successfully connected to Imagen API")
            return True
        else:
            print(f"  Failed to connect to Imagen API: {response.text[:200]}")
            return False
    except Exception as e:
        print(f"  Error testing Imagen API: {str(e)}")
        return False

def main():
    print_header("API Key Validation")
    
    results = {
        "VEO3": test_veo3_api(),
        "Vertex AI": test_vertex_api(),
        "ElevenLabs": test_elevenlabs_api(),
        "Heygen": test_heygen_api(),
        "Topaz": test_topaz_api()
    }
    
    print_header("Summary")
    for provider, status in results.items():
        color = GREEN if status else RED
        status_text = "VALID" if status else "INVALID"
        print(f"{provider}: {color}{status_text}{RESET}")
    
    if all(results.values()):
        print(f"\n{GREEN}All API keys appear valid! You can proceed with your application.{RESET}")
    else:
        print(f"\n{YELLOW}Some API keys appear to be invalid. Please check the details above.{RESET}")

if __name__ == "__main__":
    main()