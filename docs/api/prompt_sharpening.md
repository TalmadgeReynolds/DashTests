# Prompt Sharpening API

## Overview
The prompt sharpening API uses GPT-4o and Claude to rewrite user prompts into clearer, more actionable prompts optimized for AI video generation.

## Endpoints

### Health Check
Check which LLM providers are available:

```bash
curl http://localhost:8000/api/v1/prompts/health
```

**Response:**
```json
{
  "openai_available": true,
  "openai_model": "gpt-4o",
  "claude_available": true,
  "claude_model": "claude-3-5-sonnet-20241022"
}
```

### Sharpen Prompt
Rewrite a prompt with AI assistance:

```bash
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{
    "original": "A person talking about shipping a new product",
    "model": "both",
    "variants": 3,
    "temperature": 0.1,
    "max_tokens": 200
  }'
```

**Request Parameters:**
- `original` (required): The original prompt text (3-2000 characters)
- `model` (optional): Which LLM to use - `"gpt"`, `"claude"`, or `"both"` (default: `"both"`)
- `variants` (optional): Number of variants to generate, 1-6 (default: 3)
- `temperature` (optional): Sampling temperature, 0.0-1.0 (default: 0.1, lower = more deterministic)
- `max_tokens` (optional): Maximum tokens per variant, 50-500 (default: 200)

**Response:**
```json
{
  "original": "A person talking about shipping a new product",
  "variants": [
    {
      "text": "Tight medium close-up, subject centered, soft frontal key light. Subject speaks clearly: 'We finally shipped the feature, and it actually works.' Natural micro head motion, slight smile.",
      "source": "gpt",
      "score": 0.8234,
      "similarity": 0.7891,
      "diff": "[-A person talking about shipping a new product-]{+Tight medium close-up, subject centered, soft frontal key light. Subject speaks clearly: 'We finally shipped the feature, and it actually works.' Natural micro head motion, slight smile.+}"
    },
    {
      "text": "Close-up shot, professional setting. Subject centered, confident posture. Speaks: 'We're excited to announce our new product is now shipping.' Steady gaze, minimal gestures.",
      "source": "claude",
      "score": 0.7956,
      "similarity": 0.7654,
      "diff": "..."
    }
  ]
}
```

**Response Fields:**
- `variants`: List of sharpened prompts, ranked by quality score
  - `text`: The rewritten prompt
  - `source`: Which model generated it (`"gpt"` or `"claude"`)
  - `score`: Overall quality score (0-1, higher is better)
  - `similarity`: Semantic similarity to original (0-1, measures intent preservation)
  - `diff`: Human-readable diff showing changes

## Model Selection

### Use Both Models (Recommended)
```json
{"model": "both"}
```
Generates variants from both GPT and Claude, then ranks them by quality. Best for getting diverse, high-quality options.

### Use Only GPT
```json
{"model": "gpt"}
```
Faster and more cost-efficient if you only need GPT-4o variants.

### Use Only Claude
```json
{"model": "claude"}
```
Use Claude if you prefer its style or for comparison.

## Examples

### Budget Mode (Fast & Cheap)
```bash
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{
    "original": "Happy person talking",
    "model": "gpt",
    "variants": 2,
    "temperature": 0.0
  }'
```

### Studio Mode (Best Quality)
```bash
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{
    "original": "Professional business presentation",
    "model": "both",
    "variants": 5,
    "temperature": 0.2,
    "max_tokens": 300
  }'
```

### Creative Mode (More Variation)
```bash
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{
    "original": "Energetic product demo",
    "model": "both",
    "variants": 4,
    "temperature": 0.5
  }'
```

## Error Handling

### API Key Not Configured
```json
{
  "detail": "OpenAI API key not configured"
}
```
Set `OPENAI_API_KEY` and/or `ANTHROPIC_API_KEY` in your `.env` file.

### Model Not Available
If a requested model isn't available, the API will try to use the other model or return an error if neither is available.

### Rate Limits
Both OpenAI and Anthropic have rate limits. If you hit them, you'll receive a 429 or 502 error. Consider:
- Reducing `variants` count
- Adding request throttling
- Caching results

## Integration Tips

1. **Always show variants to users** - Don't auto-apply; let users choose or edit
2. **Cache results** - Same original prompt → same results (with low temperature)
3. **Start with "both" model** - Get diverse options, let users pick their favorite
4. **Use similarity score** - Ensure variants preserve original intent (>0.7 recommended)
5. **Add rate limiting** - Protect against runaway API costs

## Cost Estimates

Approximate costs per request (varies by prompt length):

- **GPT-4o**: ~$0.002-0.005 per variant
- **Claude**: ~$0.003-0.007 per variant
- **Embeddings** (for scoring): ~$0.0001 per variant

Example: 3 variants from both models = ~$0.015-0.036 per request

## Python Example

```python
import requests

def sharpen_prompt(original: str, model: str = "both"):
    response = requests.post(
        "http://localhost:8000/api/v1/prompts/sharpen",
        json={
            "original": original,
            "model": model,
            "variants": 3
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        # Get the best variant
        best = data["variants"][0]
        print(f"Best variant (score {best['score']}):")
        print(best["text"])
        return data
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage
sharpen_prompt("A person announcing exciting news")
```
