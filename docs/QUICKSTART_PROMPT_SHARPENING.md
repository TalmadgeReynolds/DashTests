# Prompt Sharpening - Quick Start Guide

## 🚀 Setup (30 seconds)

1. **Add API keys to `.env`:**
```bash
OPENAI_API_KEY=sk-proj-xVDi-3gWMGr1MQ...
ANTHROPIC_API_KEY=sk-ant-api03-L-9Zbb1updm...
```

2. **Install dependencies:**
```bash
pip install openai anthropic numpy
```

3. **Start server:**
```bash
uvicorn backend.main:app --reload
```

## 🎯 Basic Usage

### Check Status
```bash
curl http://localhost:8000/api/v1/prompts/health
```

### Sharpen a Prompt
```bash
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{"original": "Person talking about a product", "model": "both"}'
```

## 🎨 Model Selection

| Model | Use When | Cost | Speed |
|-------|----------|------|-------|
| `"gpt"` | Budget mode, fast iteration | $ | ⚡⚡⚡ |
| `"claude"` | Safety-first, detailed | $$ | ⚡⚡ |
| `"both"` | Best quality, diversity | $$$ | ⚡ |

## 📊 Response Format

```json
{
  "variants": [
    {
      "text": "Sharpened prompt with visual details...",
      "source": "gpt",
      "score": 0.85,        // Higher = better (0-1)
      "similarity": 0.82,   // How close to original (0-1)
      "diff": "[changes]"   // What was modified
    }
  ]
}
```

## ⚙️ Parameters

```javascript
{
  original: string,           // Your prompt (required)
  model: "gpt"|"claude"|"both",  // Default: "both"
  variants: number,           // 1-6, default: 3
  temperature: number,        // 0.0-1.0, default: 0.1
  max_tokens: number         // 50-500, default: 200
}
```

## 💡 Pro Tips

✅ **Always use `"both"`** for production - best quality  
✅ **Show all variants** - let users choose  
✅ **Check similarity > 0.7** - ensures intent preserved  
✅ **Cache results** - same input = same output (low temp)  
✅ **Start with temp 0.1** - increase for more variety  

## 🔥 Common Patterns

### Simple Integration
```python
import requests

def sharpen(prompt):
    resp = requests.post(
        "http://localhost:8000/api/v1/prompts/sharpen",
        json={"original": prompt, "model": "both"}
    )
    return resp.json()["variants"][0]["text"]
```

### Get Top 3 Variants
```python
def get_variants(prompt):
    resp = requests.post(
        "http://localhost:8000/api/v1/prompts/sharpen",
        json={"original": prompt, "variants": 3}
    )
    return [v["text"] for v in resp.json()["variants"]]
```

### Compare Models
```python
def compare_models(prompt):
    gpt = sharpen_with_model(prompt, "gpt")
    claude = sharpen_with_model(prompt, "claude")
    return {"gpt": gpt, "claude": claude}
```

## 🎬 Example Transformations

**Input:** `"Person announcing news"`

**GPT Output:**
```
Tight medium close-up, subject centered, soft frontal key light. 
Subject speaks: "I have exciting news to share today!" 
Natural micro head motion, genuine smile, steady eye contact.
```

**Claude Output:**
```
Close-up shot, professional setting, neutral background. 
Subject centered with confident posture. Delivers: "I'm thrilled 
to announce..." Minimal gestures, authentic expression.
```

## 📈 Cost Calculator

| Variants | Models | ~Cost/Request |
|----------|--------|---------------|
| 2 | gpt | $0.004-0.010 |
| 3 | gpt | $0.006-0.015 |
| 3 | both | $0.015-0.036 |
| 5 | both | $0.025-0.060 |

## 🐛 Troubleshooting

**No API keys configured:**
```bash
# Add to .env
echo "OPENAI_API_KEY=sk-..." >> .env
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env
```

**Import errors:**
```bash
pip install openai anthropic numpy
```

**Server not responding:**
```bash
# Check health
curl http://localhost:8000/api/v1/prompts/health
```

**Rate limits hit:**
- Reduce `variants` count
- Add caching layer
- Space out requests

## 📚 More Info

- Full API docs: `docs/api/prompt_sharpening.md`
- Implementation details: `docs/features/PROMPT_SHARPENING.md`
- Test script: `tests/test_prompt_sharpening.py`

## 🎪 Test Drive

```bash
# Run the test script
python tests/test_prompt_sharpening.py

# Or quick curl test
curl -X POST http://localhost:8000/api/v1/prompts/sharpen \
  -H "Content-Type: application/json" \
  -d '{
    "original": "Happy person talking about a new feature",
    "model": "both",
    "variants": 3
  }' | jq
```

---

**Questions?** Check the full docs or test the health endpoint to verify your setup! 🚀
