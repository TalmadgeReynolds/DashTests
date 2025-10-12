# Prompt Sharpening Feature - Implementation Summary

## What We Built

A dual-LLM prompt sharpening system that rewrites user prompts into professional, AI-video-optimized prompts using GPT-4o and Claude.

## Key Features

✅ **Dual Model Support**: Users can choose GPT-4o, Claude, or both
✅ **Quality Scoring**: Automatic ranking using embeddings + heuristics  
✅ **Intent Preservation**: Similarity scoring ensures original meaning is kept
✅ **Visual Optimization**: Adds cinematic details (shot type, lighting, framing)
✅ **Diff Visualization**: Shows exact changes made to the prompt
✅ **Production Ready**: Error handling, logging, fallbacks

## Files Created

1. **`backend/routes/prompts.py`** - Main FastAPI router with endpoints
2. **`tests/test_prompt_sharpening.py`** - Test script
3. **`docs/api/prompt_sharpening.md`** - API documentation with examples

## Files Modified

1. **`backend/main.py`** - Added prompts router
2. **`backend/routes/__init__.py`** - Exported prompts module
3. **`requirements.txt`** - Added openai, anthropic, numpy packages

## API Endpoints

### `GET /api/v1/prompts/health`
Check which LLM providers are configured and available.

### `POST /api/v1/prompts/sharpen`
Sharpen a prompt using GPT-4o and/or Claude.

**Request:**
```json
{
  "original": "A person talking about shipping a new product",
  "model": "both",
  "variants": 3,
  "temperature": 0.1
}
```

**Response:**
```json
{
  "original": "...",
  "variants": [
    {
      "text": "Tight medium close-up, subject centered...",
      "source": "gpt",
      "score": 0.8234,
      "similarity": 0.7891,
      "diff": "[-old-]{+new+}"
    }
  ]
}
```

## How It Works

1. **Generation Phase**
   - Sends prompt to GPT-4o and/or Claude with few-shot examples
   - Each model generates 1-3 variants (configurable)
   - Low temperature (0.1) ensures deterministic, focused rewrites

2. **Scoring Phase**
   - Computes embeddings for original + all variants (OpenAI embeddings)
   - Calculates semantic similarity (cosine distance)
   - Applies heuristic bonuses/penalties:
     - ✅ Bonus: Contains visual keywords (close-up, centered, lighting, etc.)
     - ❌ Penalty: Excessive length (>2x original)
   - Final score = similarity + detail_bonus - length_penalty

3. **Ranking & Response**
   - Deduplicates identical variants from different models
   - Sorts by score (descending)
   - Returns top N variants with diffs

## Configuration

Add to your `.env`:

```bash
# Required for GPT
OPENAI_API_KEY=sk-proj-...
OPENAI_MODEL=gpt-4o  # or gpt-4-turbo, gpt-3.5-turbo
OPENAI_EMBED_MODEL=text-embedding-3-large

# Required for Claude
ANTHROPIC_API_KEY=sk-ant-api03-...
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022  # or claude-3-opus
```

## Next Steps

### Installation
```bash
pip install -r requirements.txt
```

### Start Server
```bash
uvicorn backend.main:app --reload
```

### Run Tests
```bash
python tests/test_prompt_sharpening.py
```

## Usage Patterns

### Quick Test (CLI)
```bash
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{"original": "Person announcing news", "model": "both", "variants": 3}'
```

### In Your UI
```javascript
async function sharpenPrompt(original) {
  const response = await fetch('/api/v1/prompts/sharpen', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      original,
      model: 'both',
      variants: 3
    })
  });
  
  const data = await response.json();
  // Show variants to user for selection
  return data.variants;
}
```

## Cost Considerations

Per request (3 variants from both models):
- GPT-4o calls: ~$0.006-0.015
- Claude calls: ~$0.009-0.021  
- Embeddings: ~$0.0003
- **Total: ~$0.015-0.036 per request**

### Cost Optimization Tips
1. Use `model: "gpt"` for cheaper bulk processing
2. Reduce `variants` count to 2 instead of 3
3. Cache results (same prompt = same output at temp 0.1)
4. Add rate limiting per user

## Quality Tips

### Best Results
- Use `model: "both"` for diversity
- Keep temperature low (0.1-0.2) for consistency
- Request 3-5 variants, show top 3 to user
- Always let users edit/approve before using

### When to Use Each Model
- **GPT**: Concise, production-ready, fast
- **Claude**: More detailed, safety-conscious
- **Both**: Best quality, most variety

## Monitoring

The endpoint logs:
- Model selection
- Generation success/failure
- Scoring results
- Top variant scores

Check logs with:
```bash
grep "sharpen_" logs/app.log
```

## Future Enhancements

Potential additions:
- [ ] Server-side caching (Redis)
- [ ] Rate limiting per API key
- [ ] Fine-tuned models for your specific style
- [ ] Batch endpoint for multiple prompts
- [ ] A/B testing framework
- [ ] User feedback loop (thumbs up/down on variants)
- [ ] Cost tracking per user
- [ ] Preset templates (commercial, narrative, tutorial, etc.)

## Support

See full API docs: `/docs/api/prompt_sharpening.md`
Run tests: `python tests/test_prompt_sharpening.py`
Check health: `curl http://localhost:8000/api/v1/prompts/health`
