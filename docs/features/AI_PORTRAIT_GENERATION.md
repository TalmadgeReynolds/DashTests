# AI Portrait Generation with Vertex AI Imagen

## Overview

The application now supports **AI-powered portrait generation** using Google's **Vertex AI Imagen** model. This feature is available in **both Option 1 and Option 2 workflows**, allowing users to generate photorealistic portraits optimized for lip-sync instead of uploading their own images.

## Key Features

- 🎨 **Generate photorealistic portraits** from text descriptions
- 🎯 **Optimized for lip-sync** with front-facing poses and clear facial features
- ✨ **Available in both workflows** (Option 1: VEO 3 and Option 2: ElevenLabs + Heygen)
- 🎭 **Customizable demographics** (gender, age, ethnicity)
- 🎬 **Multiple styles** (photorealistic, cinematic, professional)
- 📐 **Flexible aspect ratios** (1:1, 16:9, 9:16, 4:3, 3:4)

## How It Works

### In the UI

1. **Navigate to Composer** (`/create` page)
2. **Choose Option 1 or Option 2** workflow
3. **Select "Generate with AI"** tab in the image section
4. **Describe the person** you want to generate (e.g., "professional woman in her 30s, confident expression")
5. **Click "Generate Portrait"** and wait ~10-15 seconds
6. **Review the generated image** in the preview
7. **Continue with your workflow** to create the video

### What Gets Generated

The system automatically:
- Creates a **front-facing portrait** suitable for lip-sync
- Applies **soft, even lighting** for natural appearance
- Ensures **clear facial features** with no occlusions
- Uses **shallow depth of field** for professional look
- Avoids common issues (sunglasses, masks, profile views, etc.)

## API Endpoints

### Generate Portrait (Recommended)

**Endpoint:** `POST /api/v1/images/generate-portrait`

**Use Case:** Generate portraits specifically optimized for lip-sync workflows

**Request:**
```json
{
  "description": "professional businessman in his 40s, warm smile",
  "gender": "male",
  "age": "middle-aged",
  "ethnicity": "Asian",
  "style": "photorealistic",
  "aspect_ratio": "1:1"
}
```

**Response:**
```json
{
  "image_url": "https://s3.../portraits/abc123-20251013.png",
  "asset_id": "abc123-def456-789",
  "metadata": {
    "description": "professional businessman in his 40s, warm smile",
    "gender": "male",
    "age": "middle-aged",
    "model": "imagen-3.0",
    "optimized_for": "lip-sync",
    "prompt": "Professional headshot portrait photograph, middle-aged male Asian professional businessman in his 40s, warm smile, front-facing, neutral expression..."
  }
}
```

**Parameters:**
- `description` (required): Basic description of the person (10-500 chars)
- `gender` (optional): `male`, `female`, or `non-binary`
- `age` (optional): `young`, `middle-aged`, or `elderly`
- `ethnicity` (optional): Ethnicity description
- `style` (optional): `photorealistic` (default), `cinematic`, or `professional`
- `aspect_ratio` (optional): Image dimensions (default: `1:1`)

### Generate Custom Image

**Endpoint:** `POST /api/v1/images/generate`

**Use Case:** Generate images with full control over the prompt

**Request:**
```json
{
  "prompt": "cinematic portrait of a detective, film noir lighting, dramatic shadows",
  "negative_prompt": "blurry, low quality, cartoonish",
  "aspect_ratio": "16:9",
  "style": "cinematic"
}
```

**Response:**
```json
{
  "image_url": "https://s3.../generated/xyz789-20251013.png",
  "asset_id": "xyz789-abc123-456",
  "metadata": {
    "prompt": "cinematic portrait of a detective...",
    "aspect_ratio": "16:9",
    "model": "imagen-3.0",
    "style": "cinematic"
  }
}
```

## Backend Implementation

### Imagen Adapter

**File:** `backend/adapters/imagen_adapter.py`

**Key Methods:**
- `generate_image()` - Generate any image from a prompt
- `generate_portrait()` - Generate lip-sync optimized portraits

**Example Usage:**
```python
from backend.adapters.imagen_adapter import ImagenAdapter

adapter = ImagenAdapter()

# Generate a portrait
result = await adapter.generate_portrait(
    description="young woman, professional attire",
    gender="female",
    age="young",
    style="photorealistic"
)

# Result contains base64-encoded image
image_base64 = result["images"][0]
```

### Routes

**File:** `backend/routes/images.py`

Provides FastAPI endpoints that:
1. Accept generation requests
2. Call Imagen adapter
3. Upload generated images to S3/MinIO
4. Return public URLs

### Storage Integration

Generated images are automatically:
- Uploaded to S3/MinIO storage
- Stored in `portraits/` or `generated/` folders
- Given public URLs for immediate use
- Validated against size limits (≤10MB)

## Frontend Integration

### Imagen API Client

**File:** `frontend/src/lib/imagen-api.ts`

**Functions:**
- `generatePortrait()` - Generate optimized portraits
- `generateImage()` - Generate custom images

**Example:**
```typescript
import { generatePortrait } from '@/lib/imagen-api';

const result = await generatePortrait({
  description: "elderly professor, glasses, kind expression",
  age: "elderly",
  style: "professional"
});

console.log(result.image_url); // Use in job creation
```

### UI Components

The Composer page includes:
- **Toggle buttons** to switch between Upload and Generate
- **Description input** for portrait prompts
- **Generate button** with loading states
- **Image preview** showing the generated portrait
- **Error handling** with user-friendly messages

## Configuration

### Environment Variables

**Required:**
```bash
VERTEX_API_KEY=your-vertex-ai-key
```

**Optional:**
```bash
VERTEX_PROJECT_ID=your-gcp-project
VERTEX_LOCATION=us-central1
```

### Getting a Vertex AI Key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Enable **Vertex AI API**
3. Enable **Imagen API**
4. Create an API key or service account key
5. Add to your `.env` file

## Best Practices

### For Portrait Generation

**Good Prompts:**
- "professional woman in her 30s, business attire, confident smile"
- "young man, casual clothing, friendly expression"
- "elderly woman, warm smile, wise appearance"

**Avoid:**
- Overly complex descriptions
- Multiple people
- Specific celebrity names
- Copyrighted characters

### For Lip-Sync Optimization

The system automatically adds these constraints:
- ✓ Front-facing orientation
- ✓ Neutral or slight smile
- ✓ Clear facial features
- ✓ Soft, even lighting
- ✓ No occlusions (sunglasses, masks, hands)
- ✓ Single person only

### Aspect Ratios

Choose based on your video output:
- **1:1** - Square format (social media)
- **16:9** - Landscape (YouTube, TV)
- **9:16** - Portrait (TikTok, Reels, Shorts)
- **4:3** - Classic portrait orientation

## Troubleshooting

### Image Generation Fails

**Error:** `Failed to generate portrait`

**Possible Causes:**
1. Invalid API key → Check `VERTEX_API_KEY` in `.env`
2. Quota exceeded → Check Google Cloud quota limits
3. Content policy violation → Try different description
4. Network timeout → Retry the generation

**Solution:**
```bash
# Test API key
python test_api_keys.py

# Check logs
tail -f /tmp/api.log | grep imagen
```

### Generated Image Not Suitable

**Problem:** Face not front-facing or occluded

**Solution:**
- Use `/images/generate-portrait` instead of `/images/generate`
- The portrait endpoint has optimization specifically for lip-sync
- Add descriptors like "looking at camera" in your prompt

### Slow Generation

**Normal:** 10-15 seconds per image  
**Slow:** >30 seconds

**Causes:**
- High Imagen API load
- Network latency
- Complex prompts

**Solutions:**
- Simplify prompts
- Use recommended aspect ratios (1:1 is fastest)
- Check network connectivity

## Workflow Examples

### Option 1 with Generated Portrait

1. Navigate to Composer → Option 1
2. Enter your script: "We're launching something incredible today"
3. Click "Generate with AI"
4. Describe: "tech CEO, confident, professional attire"
5. Click "Generate Portrait"
6. Review image → Continue with video settings
7. Click "Create Video Job"

### Option 2 with Generated Portrait

1. Navigate to Composer → Option 2
2. Click "Generate with AI" for image
3. Describe: "news anchor, professional, engaging smile"
4. Click "Generate Portrait"
5. Choose audio source (TTS or upload)
6. Add action prompt: "Occasional blink, steady gaze"
7. Click "Create Video Job"

## Cost Considerations

**Imagen API Pricing:**
- ~$0.02-0.05 per image generation
- Varies by resolution and model version
- Check [Google Cloud Pricing](https://cloud.google.com/vertex-ai/pricing)

**Storage Costs:**
- Generated images stored in S3/MinIO
- ~1-3 MB per portrait
- Standard S3 storage rates apply

## Security & Privacy

**Content Policies:**
- No celebrity likenesses without rights
- No copyrighted characters
- No inappropriate content
- Age-appropriate content only

**Data Handling:**
- Images generated on-demand
- Stored in your S3 bucket
- Not cached or shared
- Subject to your retention policies

## Future Enhancements

Planned improvements:
- [ ] Style presets (corporate, creative, casual)
- [ ] Batch generation (multiple variations)
- [ ] Fine-tuning options (lighting, expression)
- [ ] Seed storage for reproducibility
- [ ] Custom model support
- [ ] A/B testing generated vs uploaded

## Related Documentation

- [Vertex AI Imagen Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview)
- [Main README](../README.md)
- [API Specification](../api/openapi.yaml)
- [Storage Policy](../storage/presign_policy.md)
