#!/usr/bin/env python3
"""
Test script for the prompt sharpening endpoint.
Tests both GPT and Claude models.
"""
import requests
import json
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Check if LLM providers are available."""
    print("🔍 Checking LLM provider availability...")
    response = requests.get(f"{BASE_URL}/prompts/health")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ OpenAI available: {data['openai_available']} (model: {data['openai_model']})")
        print(f"✅ Claude available: {data['claude_available']} (model: {data['claude_model']})")
        return data
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return None

def test_sharpen(original_prompt: str, model: str = "both", variants: int = 3):
    """Test the sharpen endpoint."""
    print(f"\n📝 Testing prompt sharpening with model='{model}'...")
    print(f"Original: {original_prompt}")
    print("-" * 80)
    
    payload = {
        "original": original_prompt,
        "model": model,
        "variants": variants,
        "temperature": 0.1,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/prompts/sharpen",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Generated {len(data['variants'])} variants:\n")
            
            for i, variant in enumerate(data['variants'], 1):
                print(f"Variant {i} (from {variant['source']}):")
                print(f"  Score: {variant['score']:.4f} | Similarity: {variant['similarity']:.4f}")
                print(f"  Text: {variant['text']}")
                print(f"  Diff: {variant['diff'][:150]}...")
                print()
            
            return data
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request error: {e}")
        return None

def main():
    """Run tests."""
    print("=" * 80)
    print("Prompt Sharpening API Test")
    print("=" * 80)
    
    # Check health
    health = test_health()
    if not health:
        print("\n⚠️  Cannot proceed without API connectivity")
        sys.exit(1)
    
    # Test prompts
    test_prompts = [
        "A person talking about shipping a new product",
        "Happy excited announcement about a new feature",
        "Professional presentation about quarterly results"
    ]
    
    for prompt in test_prompts:
        test_sharpen(prompt, model="both", variants=3)
        print("=" * 80)
    
    # Test individual models if both are available
    if health.get("openai_available") and health.get("claude_available"):
        print("\n🔬 Testing individual models...\n")
        test_sharpen("Quick test of model selection", model="gpt", variants=2)
        test_sharpen("Quick test of model selection", model="claude", variants=2)
    
    print("\n✨ Testing complete!")

if __name__ == "__main__":
    main()
