#!/usr/bin/env python3
"""
Test script for ElevenLabs voice features
Demonstrates all new voice management capabilities
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

def print_section(title):
    """Print a section header"""
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}\n")


def test_available_models():
    """Test: Get available models"""
    print_section("1. Available Models")
    
    response = requests.get(f"{BASE_URL}/voices/models/available")
    
    if response.status_code == 200:
        models = response.json()["models"]
        print("✅ Available Models:")
        for model_id, description in models.items():
            print(f"   • {model_id}: {description}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_available_formats():
    """Test: Get available output formats"""
    print_section("2. Available Output Formats")
    
    response = requests.get(f"{BASE_URL}/voices/formats/available")
    
    if response.status_code == 200:
        formats = response.json()["formats"]
        print("✅ Available Formats:")
        for format_id, description in formats.items():
            print(f"   • {format_id}: {description}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_list_voices():
    """Test: List all voices"""
    print_section("3. List All Voices")
    
    response = requests.get(f"{BASE_URL}/voices/")
    
    if response.status_code == 200:
        voices = response.json()
        print(f"✅ Found {len(voices)} voices:")
        for voice in voices[:5]:  # Show first 5
            print(f"   • {voice['name']} ({voice['voice_id'][:12]}...)")
            print(f"     Category: {voice['category']}")
            if voice.get('labels'):
                print(f"     Labels: {voice['labels']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_filter_voices():
    """Test: Filter voices by name"""
    print_section("4. Filter Voices (search for 'rachel')")
    
    response = requests.get(f"{BASE_URL}/voices/", params={"filter_name": "rachel"})
    
    if response.status_code == 200:
        voices = response.json()
        print(f"✅ Found {len(voices)} matching voices:")
        for voice in voices:
            print(f"   • {voice['name']} ({voice['voice_id'][:12]}...)")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_get_voice():
    """Test: Get specific voice details"""
    print_section("5. Get Voice Details (Rachel)")
    
    # Rachel's voice ID
    voice_id = "21m00Tcm4TlvDq8ikWAM"
    
    response = requests.get(f"{BASE_URL}/voices/{voice_id}")
    
    if response.status_code == 200:
        voice = response.json()
        print(f"✅ Voice Details:")
        print(f"   Name: {voice['name']}")
        print(f"   ID: {voice['voice_id']}")
        print(f"   Category: {voice['category']}")
        if voice.get('labels'):
            print(f"   Labels: {json.dumps(voice['labels'], indent=6)}")
        if voice.get('settings'):
            print(f"   Default Settings: {voice['settings']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_synthesize():
    """Test: Synthesize speech"""
    print_section("6. Synthesize Speech")
    
    payload = {
        "text": "Hello! This is a test of the new ElevenLabs voice features.",
        "voice_id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "model_id": "eleven_turbo_v2",
        "stability": 0.65,
        "similarity_boost": 0.75,
        "style": 0.2,
        "speaker_boost": True,
        "output_format": "mp3_44100_128",
        "seed": 42,  # For reproducible generation
        "optimize_streaming_latency": 0
    }
    
    print("Sending synthesis request...")
    response = requests.post(f"{BASE_URL}/voices/synthesize", json=payload)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Synthesis Successful:")
        print(f"   Audio URL: {result['audio_url'][:60]}...")
        print(f"   Audio Key: {result['audio_key']}")
        print(f"   Size: {result['size_bytes']:,} bytes ({result['size_bytes']/1024:.1f} KB)")
        print(f"   Format: {result['format']}")
        print(f"   Model: {result['model']}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_subscription_info():
    """Test: Get subscription info"""
    print_section("7. Subscription Information")
    
    response = requests.get(f"{BASE_URL}/voices/subscription/info")
    
    if response.status_code == 200:
        info = response.json()
        usage_pct = (info['character_count'] / info['character_limit']) * 100 if info['character_limit'] > 0 else 0
        
        print(f"✅ Subscription Status:")
        print(f"   Tier: {info['tier']}")
        print(f"   Usage: {info['character_count']:,} / {info['character_limit']:,} characters")
        print(f"   Usage: {usage_pct:.1f}%")
        print(f"   Can Extend: {'Yes' if info['can_extend_character_limit'] else 'No'}")
    else:
        print(f"❌ Failed: {response.status_code}")
        print(response.text)


def test_clone_voice_demo():
    """Test: Voice cloning (demo - requires audio files)"""
    print_section("8. Voice Cloning (Demo)")
    
    print("ℹ️  Voice cloning requires audio files.")
    print("   Example usage:")
    print()
    print("   ```bash")
    print("   curl -X POST http://localhost:8000/api/v1/voices/clone \\")
    print("     -F 'name=My Custom Voice' \\")
    print("     -F 'description=Professional narration voice' \\")
    print("     -F 'files=@sample1.mp3' \\")
    print("     -F 'files=@sample2.mp3' \\")
    print("     -F 'files=@sample3.mp3'")
    print("   ```")
    print()
    print("   Requirements:")
    print("   • 1-5 audio samples (MP3, WAV, or M4A)")
    print("   • Total duration: 1-5 minutes")
    print("   • High-quality recording with clear speech")
    print("   • Minimal background noise")


def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("  ElevenLabs Voice Features Test Suite")
    print("=" * 60)
    print(f"\n🔗 Testing API at: {BASE_URL}")
    print("⚠️  Make sure the backend is running!")
    
    tests = [
        test_available_models,
        test_available_formats,
        test_list_voices,
        test_filter_voices,
        test_get_voice,
        test_synthesize,
        test_subscription_info,
        test_clone_voice_demo
    ]
    
    for test_func in tests:
        try:
            test_func()
        except requests.exceptions.ConnectionError:
            print(f"\n❌ Connection Error: Is the backend running at {BASE_URL}?")
            break
        except Exception as e:
            print(f"\n❌ Error in {test_func.__name__}: {str(e)}")
    
    print("\n" + "=" * 60)
    print("  Test Suite Complete")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    run_all_tests()
