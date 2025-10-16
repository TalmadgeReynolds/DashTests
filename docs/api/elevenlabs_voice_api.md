# ElevenLabs Voice API Endpoints

## Base URL
```
http://localhost:8000/api/v1/voices
```

## Endpoints

### 1. List Voices
Get all available voices with optional filtering.

**Endpoint:** `GET /voices/`

**Query Parameters:**
- `filter_name` (optional): Filter voices by name

**Example:**
```bash
# List all voices
curl http://localhost:8000/api/v1/voices/

# Filter by name
curl http://localhost:8000/api/v1/voices/?filter_name=rachel
```

**Response:**
```json
[
  {
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "name": "Rachel",
    "category": "premade",
    "labels": {
      "accent": "american",
      "age": "young",
      "gender": "female"
    },
    "preview_url": "https://..."
  }
]
```

---

### 2. Get Voice Details
Get detailed information about a specific voice.

**Endpoint:** `GET /voices/{voice_id}`

**Example:**
```bash
curl http://localhost:8000/api/v1/voices/21m00Tcm4TlvDq8ikWAM
```

**Response:**
```json
{
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "name": "Rachel",
  "category": "premade",
  "labels": {
    "accent": "american",
    "age": "young",
    "gender": "female",
    "use_case": "narration"
  },
  "settings": {
    "stability": 0.75,
    "similarity_boost": 0.75
  },
  "samples": [...]
}
```

---

### 3. Clone Voice
Create a custom voice from audio samples.

**Endpoint:** `POST /voices/clone`

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `name` (required): Name for the cloned voice
- `description` (optional): Description of the voice
- `files` (required): 1-5 audio files (MP3, WAV, or M4A)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/voices/clone \
  -F 'name=My Brand Voice' \
  -F 'description=Professional narration voice' \
  -F 'files=@sample1.mp3' \
  -F 'files=@sample2.mp3' \
  -F 'files=@sample3.mp3'
```

**Response:**
```json
{
  "voice_id": "pNInz6obpgDQGcFmaJgB",
  "name": "My Brand Voice",
  "message": "Voice 'My Brand Voice' cloned successfully from 3 samples"
}
```

**Audio Requirements:**
- 1-5 audio files required
- Total duration: 1-5 minutes recommended
- High-quality recording with clear speech
- Minimal background noise
- Formats: MP3, WAV, M4A

---

### 4. Delete Voice
Delete a cloned voice.

**Endpoint:** `DELETE /voices/{voice_id}`

**Example:**
```bash
curl -X DELETE http://localhost:8000/api/v1/voices/pNInz6obpgDQGcFmaJgB
```

**Response:**
```json
{
  "message": "Voice pNInz6obpgDQGcFmaJgB deleted successfully"
}
```

**Note:** Only cloned voices can be deleted. Premade voices cannot be removed.

---

### 5. Synthesize Speech
Generate speech from text with advanced controls.

**Endpoint:** `POST /voices/synthesize`

**Content-Type:** `application/json`

**Request Body:**
```json
{
  "text": "Hello! This is a test of the ElevenLabs voice features.",
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "model_id": "eleven_turbo_v2",
  "stability": 0.65,
  "similarity_boost": 0.75,
  "style": 0.0,
  "speaker_boost": true,
  "output_format": "mp3_44100_128",
  "seed": 42,
  "optimize_streaming_latency": 0
}
```

**Parameters:**

| Parameter | Type | Default | Range | Description |
|-----------|------|---------|-------|-------------|
| `text` | string | required | 1-5000 chars | Text to synthesize |
| `voice_id` | string | required | - | Voice ID to use |
| `model_id` | string | `"eleven_turbo_v2"` | See models | Model to use |
| `stability` | float | `0.65` | 0.0-1.0 | Voice stability |
| `similarity_boost` | float | `0.75` | 0.0-1.0 | Voice similarity |
| `style` | float | `0.0` | 0.0-1.0 | Exaggeration level |
| `speaker_boost` | bool | `true` | - | Enhance voice clarity |
| `output_format` | string | `"mp3_44100_128"` | See formats | Audio format |
| `seed` | int | `null` | - | Seed for reproducibility |
| `optimize_streaming_latency` | int | `0` | 0-4 | Latency optimization |

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model_id": "eleven_turbo_v2",
    "stability": 0.65,
    "similarity_boost": 0.75
  }'
```

**Response:**
```json
{
  "audio_url": "https://s3.amazonaws.com/bucket/tts-21m00Tcm-42.mp3?...",
  "audio_key": "tts-21m00Tcm-42.mp3",
  "size_bytes": 24576,
  "format": "mp3_44100_128",
  "model": "eleven_turbo_v2"
}
```

---

### 6. Get Subscription Info
Get subscription information and usage statistics.

**Endpoint:** `GET /voices/subscription/info`

**Example:**
```bash
curl http://localhost:8000/api/v1/voices/subscription/info
```

**Response:**
```json
{
  "tier": "free",
  "character_count": 5000,
  "character_limit": 10000,
  "can_extend_character_limit": true
}
```

---

### 7. Get Available Models
List all available AI models.

**Endpoint:** `GET /voices/models/available`

**Example:**
```bash
curl http://localhost:8000/api/v1/voices/models/available
```

**Response:**
```json
{
  "models": {
    "eleven_monolingual_v1": "English v1 - Original English model",
    "eleven_multilingual_v1": "Multilingual v1 - Original multilingual",
    "eleven_multilingual_v2": "Multilingual v2 - Latest multilingual (29+ languages)",
    "eleven_turbo_v2": "Turbo v2 - Fast generation",
    "eleven_turbo_v2_5": "Turbo v2.5 - Latest fast model"
  }
}
```

**Model Comparison:**

| Model | Languages | Latency | Quality | Best For |
|-------|-----------|---------|---------|----------|
| `eleven_turbo_v2_5` | English | ~200ms | Very High | Real-time, interactive |
| `eleven_turbo_v2` | English | ~300ms | High | Fast applications |
| `eleven_multilingual_v2` | 29+ | ~1000ms | Highest | Professional content |
| `eleven_multilingual_v1` | 29+ | ~1000ms | High | General multilingual |
| `eleven_monolingual_v1` | English | ~500ms | High | Legacy support |

---

### 8. Get Available Formats
List all available output formats.

**Endpoint:** `GET /voices/formats/available`

**Example:**
```bash
curl http://localhost:8000/api/v1/voices/formats/available
```

**Response:**
```json
{
  "formats": {
    "mp3_44100_128": "MP3 44.1kHz 128kbps (recommended)",
    "mp3_44100_192": "MP3 44.1kHz 192kbps (high quality)",
    "pcm_16000": "PCM 16kHz (mobile/telephony)",
    "pcm_22050": "PCM 22.05kHz",
    "pcm_24000": "PCM 24kHz",
    "pcm_44100": "PCM 44.1kHz (studio quality, uncompressed)",
    "ulaw_8000": "μ-law 8kHz (telephony)"
  }
}
```

**Format Comparison:**

| Format | Sample Rate | File Size | Quality | Use Case |
|--------|-------------|-----------|---------|----------|
| `mp3_44100_128` | 44.1 kHz | ~1 MB/min | High | **General use (recommended)** |
| `mp3_44100_192` | 44.1 kHz | ~1.4 MB/min | Very High | Professional production |
| `pcm_16000` | 16 kHz | ~1.9 MB/min | Good | Mobile apps, telephony |
| `pcm_22050` | 22.05 kHz | ~2.6 MB/min | High | Voice-only content |
| `pcm_24000` | 24 kHz | ~2.8 MB/min | High | Enhanced clarity |
| `pcm_44100` | 44.1 kHz | ~10 MB/min | Highest | Studio, archival |
| `ulaw_8000` | 8 kHz | ~0.5 MB/min | Basic | Legacy telephony |

---

## Common Workflows

### Workflow 1: Quick Synthesis
Generate audio with default settings:

```bash
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your text here",
    "voice_id": "21m00Tcm4TlvDq8ikWAM"
  }'
```

### Workflow 2: Create and Use Custom Voice

1. Clone voice:
```bash
curl -X POST http://localhost:8000/api/v1/voices/clone \
  -F 'name=Custom Voice' \
  -F 'files=@sample1.mp3' \
  -F 'files=@sample2.mp3'
```

2. Use returned `voice_id` for synthesis:
```bash
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello from my custom voice!",
    "voice_id": "pNInz6obpgDQGcFmaJgB"
  }'
```

### Workflow 3: High-Quality Production

```bash
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Professional narration...",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model_id": "eleven_multilingual_v2",
    "output_format": "mp3_44100_192",
    "stability": 0.75,
    "similarity_boost": 0.85,
    "speaker_boost": true
  }'
```

### Workflow 4: Real-Time/Low Latency

```bash
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Quick response",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "model_id": "eleven_turbo_v2_5",
    "output_format": "pcm_16000",
    "optimize_streaming_latency": 4
  }'
```

### Workflow 5: Reproducible Generation

```bash
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Test audio",
    "voice_id": "21m00Tcm4TlvDq8ikWAM",
    "seed": 42
  }'
```

Same seed = identical audio every time (useful for testing, A/B comparisons).

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "Invalid model_id: eleven_turbo_v3. Must be one of [...]"
}
```

### 404 Not Found
```json
{
  "detail": "Voice not found: invalid_voice_id"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Failed to synthesize: ElevenLabs API error"
}
```

---

## Rate Limits

ElevenLabs API rate limits vary by subscription tier:

- **Free:** 10,000 characters/month
- **Starter:** 30,000 characters/month  
- **Creator:** 100,000 characters/month
- **Pro:** 500,000 characters/month

Check usage with:
```bash
curl http://localhost:8000/api/v1/voices/subscription/info
```

---

## Testing

Run the test suite:
```bash
python tests/test_voice_features.py
```

Or test individual endpoints with curl as shown above.

---

## Related Documentation

- [ELEVENLABS_VOICE_FEATURES.md](../docs/features/ELEVENLABS_VOICE_FEATURES.md) - Complete feature guide
- [ELEVENLABS_ENHANCEMENT_SUMMARY.md](../ELEVENLABS_ENHANCEMENT_SUMMARY.md) - Implementation details
- [README.md](../docs/README.md) - Main documentation
