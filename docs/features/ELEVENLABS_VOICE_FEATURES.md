# ElevenLabs Voice Features

This document describes the comprehensive ElevenLabs Text-to-Speech (TTS) integration in DashTests, including voice library management, voice cloning, model selection, and advanced synthesis features.

## Table of Contents

1. [Overview](#overview)
2. [Voice Library Management](#voice-library-management)
3. [Voice Cloning](#voice-cloning)
4. [Model Selection](#model-selection)
5. [Advanced Synthesis Settings](#advanced-synthesis-settings)
6. [Audio Storage](#audio-storage)
7. [Configuration](#configuration)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

## Overview

The ElevenLabs adapter provides professional-grade text-to-speech synthesis with:

- **Voice Library**: Access to ElevenLabs' extensive library of pre-made voices
- **Voice Cloning**: Create custom voices from audio samples (instant and professional)
- **Multiple Models**: Choose between 5 AI models optimized for different use cases
- **Advanced Controls**: Fine-tune stability, similarity, style, and speaker boost
- **Output Formats**: 7 different audio formats for various quality/size tradeoffs
- **Audio Storage**: Automatic S3/MinIO storage integration with presigned URLs
- **Subscription Management**: Track usage and character limits

### Key Features

- ✅ Voice discovery and filtering
- ✅ Instant voice cloning (1-5 audio samples)
- ✅ Professional voice cloning (30+ minutes of audio)
- ✅ Multilingual support (29+ languages)
- ✅ Turbo models for low-latency applications
- ✅ Reproducible generation with seeds
- ✅ Streaming optimization
- ✅ SSML support for advanced control

## Voice Library Management

### Listing Voices

The adapter provides methods to discover available voices:

```python
from backend.adapters.tts_elevenlabs import ElevenLabsAdapter

adapter = ElevenLabsAdapter()

# List all voices
voices = await adapter.list_voices()

# Filter voices by name
rachel_voices = await adapter.list_voices(filter_name="rachel")
```

**Response Format:**
```json
[
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
    "samples": [...],
    "preview_url": "https://..."
  }
]
```

### Getting Voice Details

Retrieve detailed information about a specific voice:

```python
voice = await adapter.get_voice("21m00Tcm4TlvDq8ikWAM")
```

**Response includes:**
- Voice ID and name
- Category (premade, cloned, professional)
- Fine-tuning settings (stability, similarity_boost)
- Audio samples
- Labels and metadata

### Voice Categories

1. **Premade Voices**: ElevenLabs' professionally designed voices
2. **Cloned Voices**: User-created voices via instant cloning
3. **Professional Voices**: High-quality clones from extensive training data

## Voice Cloning

### Instant Voice Cloning

Create a custom voice from 1-5 audio samples:

```python
# Read audio samples
with open("sample1.mp3", "rb") as f1, open("sample2.mp3", "rb") as f2:
    audio_samples = [f1.read(), f2.read()]

# Clone voice
voice_id = await adapter.clone_voice(
    name="My Custom Voice",
    files=audio_samples,
    description="Clear, professional narration voice",
    labels={
        "accent": "american",
        "age": "middle_aged",
        "gender": "male",
        "use_case": "narration"
    }
)

print(f"Created voice: {voice_id}")
```

### Audio Requirements for Cloning

**Recommended:**
- **Format**: MP3, WAV, or M4A
- **Duration**: 1-5 minutes total across all samples
- **Quality**: High-quality recording, minimal background noise
- **Content**: Clear speech, varied emotions/tones
- **Sample Count**: 2-5 samples for best results

**Best Practices:**
- Use professional microphone if possible
- Record in quiet environment
- Include natural pauses and varied intonation
- Avoid music, overlapping speech, or heavy processing
- Keep consistent recording quality across samples

### Voice Management

Delete a cloned voice:

```python
success = await adapter.delete_voice(voice_id)
```

**Note**: Only user-created cloned voices can be deleted. Premade voices cannot be removed.

## Model Selection

The adapter supports 5 ElevenLabs models with different characteristics:

### Available Models

| Model ID | Description | Languages | Latency | Quality | Use Case |
|----------|-------------|-----------|---------|---------|----------|
| `eleven_turbo_v2_5` | Latest turbo model | English | Lowest | Very High | Real-time applications |
| `eleven_turbo_v2` | Fast turbo model | English | Very Low | High | Interactive experiences |
| `eleven_multilingual_v2` | Latest multilingual | 29+ | Medium | Highest | Professional content |
| `eleven_multilingual_v1` | Original multilingual | 29+ | Medium | High | General multilingual |
| `eleven_monolingual_v1` | Original English | English | High | High | Legacy support |

### Model Recommendations

**For Real-Time/Interactive:**
```python
audio = await adapter.synthesize(
    text="Hello, how can I help you today?",
    voice_id=voice_id,
    model_id="eleven_turbo_v2_5",
    optimize_streaming_latency=4  # Maximum optimization
)
```

**For Professional Content:**
```python
audio = await adapter.synthesize(
    text="Welcome to our documentary...",
    voice_id=voice_id,
    model_id="eleven_multilingual_v2",
    style=0.3,  # More expressive
    speaker_boost=True
)
```

**For Multilingual:**
```python
audio = await adapter.synthesize(
    text="Bonjour! Comment allez-vous?",
    voice_id=voice_id,
    model_id="eleven_multilingual_v2"
)
```

## Advanced Synthesis Settings

### Core Parameters

```python
audio_bytes = await adapter.synthesize(
    text="Your script here",
    voice_id="21m00Tcm4TlvDq8ikWAM",
    
    # Model selection
    model_id="eleven_turbo_v2",
    
    # Voice settings
    stability=0.65,           # 0-1: Lower = more variation, Higher = more stable
    similarity_boost=0.75,    # 0-1: How closely to match voice sample
    style=0.0,                # 0-1: Exaggeration/emotion level
    speaker_boost=True,       # Enhance voice clarity
    
    # Audio format
    output_format="mp3_44100_128",  # Quality/size tradeoff
    
    # Advanced
    seed=42,                  # For reproducible generation
    optimize_streaming_latency=2,  # 0-4: Latency vs quality
)
```

### Parameter Details

#### Stability (0.0 - 1.0)
- **Low (0.0-0.3)**: More variable, expressive, emotional
- **Medium (0.4-0.7)**: Balanced, natural
- **High (0.8-1.0)**: Very consistent, stable, predictable

**Use Cases:**
- Low: Character voices, storytelling
- Medium: General narration (recommended default)
- High: Technical content, consistency critical

#### Similarity Boost (0.0 - 1.0)
Controls how closely the output matches the voice sample:
- **Low (0.0-0.4)**: More creative interpretation
- **Medium (0.5-0.8)**: Balanced (recommended default)
- **High (0.9-1.0)**: Maximum similarity to original voice

#### Style (0.0 - 1.0)
Exaggeration level for emotions and expression:
- **0.0**: Neutral, natural delivery
- **0.3-0.5**: Moderate expression
- **1.0**: Maximum exaggeration

**Note**: Works best with Turbo v2 and v2.5 models.

#### Speaker Boost
When enabled, enhances voice similarity and clarity:
- **True**: Better voice consistency (recommended for most cases)
- **False**: Slightly faster generation

### Output Formats

| Format | Sample Rate | Bitrate | File Size | Quality | Use Case |
|--------|-------------|---------|-----------|---------|----------|
| `mp3_44100_128` | 44.1 kHz | 128 kbps | Medium | High | **Recommended default** |
| `mp3_44100_192` | 44.1 kHz | 192 kbps | Large | Very High | Professional production |
| `pcm_16000` | 16 kHz | Uncompressed | Small | Good | Phone/mobile apps |
| `pcm_22050` | 22.05 kHz | Uncompressed | Medium | High | Voice-only content |
| `pcm_24000` | 24 kHz | Uncompressed | Medium+ | High | Enhanced clarity |
| `pcm_44100` | 44.1 kHz | Uncompressed | Very Large | Highest | Studio quality |
| `ulaw_8000` | 8 kHz | 64 kbps | Smallest | Basic | Telephony |

**Recommendations:**
- General use: `mp3_44100_128`
- Professional: `mp3_44100_192`
- Mobile/streaming: `pcm_16000` or `pcm_22050`
- Archival: `pcm_44100`

### Reproducible Generation

Use seeds for consistent output:

```python
# Same seed = same audio every time
audio1 = await adapter.synthesize(text="Hello", seed=42)
audio2 = await adapter.synthesize(text="Hello", seed=42)
# audio1 == audio2

# Different seed = different audio
audio3 = await adapter.synthesize(text="Hello", seed=123)
# audio3 != audio1
```

**Use Cases:**
- A/B testing
- Regression testing
- Consistent regeneration

### Streaming Optimization

Control latency vs quality tradeoff:

```python
audio = await adapter.synthesize(
    text="Your text",
    optimize_streaming_latency=2  # 0-4
)
```

**Levels:**
- **0**: No optimization, highest quality
- **1-2**: Balanced (recommended for most streaming)
- **3-4**: Maximum optimization, lowest latency

## Audio Storage

The adapter automatically stores generated audio in S3/MinIO:

### Storage Flow

1. **Synthesis**: Generate audio with ElevenLabs
2. **Upload**: Save audio bytes to storage with `upload_bytes()`
3. **URL Generation**: Create presigned URL for access
4. **Metadata**: Store both key and URL in job metadata

### Integration in Orchestrator

```python
# Generate audio
audio_bytes = await self.tts_adapter.synthesize(
    text=tts_text,
    voice_id=voice_id,
    model_id="eleven_turbo_v2"
)

# Save to storage
audio_key = self.storage_service.upload_bytes(
    audio_bytes,
    filename=f"tts-{job.id}.mp3",
    content_type="audio/mpeg"
)

# Get presigned URL (24 hour expiry)
audio_url = self.storage_service.get_presigned_url(
    audio_key, 
    expires_in=86400
)
```

### Storage Keys

Audio files are stored with keys like:
```
tts-{job_id}.mp3
```

This makes it easy to:
- Associate audio with jobs
- Clean up old files
- Debug audio generation issues

## Configuration

### Environment Variables

```bash
# Required
ELEVENLABS_API_KEY=your-api-key-here

# Optional
ELEVENLABS_MOCK_MODE=false        # Enable mock mode for testing
ELEVENLABS_DEFAULT_MODEL=eleven_turbo_v2  # Default model
ELEVENLABS_DEFAULT_VOICE=21m00Tcm4TlvDq8ikWAM  # Rachel
```

### Mock Mode

For testing without API calls:

```python
adapter = ElevenLabsAdapter(mock_mode=True)

# Returns mock data without API calls
voices = await adapter.list_voices()
voice_id = await adapter.clone_voice("Test Voice", [b"mock audio"])
audio = await adapter.synthesize("Test text")
```

### Subscription Tracking

Monitor usage and limits:

```python
info = await adapter.get_subscription_info()
print(f"Used: {info['character_count']} / {info['character_limit']}")
print(f"Tier: {info['tier']}")
```

## Best Practices

### Voice Selection

1. **Test Multiple Voices**: Try 3-5 voices for your use case
2. **Consider Accent**: Match accent to target audience
3. **Age/Gender**: Choose appropriate for content
4. **Preview First**: Listen to samples before committing

### Voice Cloning

1. **Quality Over Quantity**: 2-3 high-quality samples > 5 poor samples
2. **Consistent Environment**: Use same microphone/room for all samples
3. **Varied Content**: Include different emotions and speaking styles
4. **Clear Speech**: Enunciate clearly, avoid mumbling
5. **Professional Setup**: Invest in good microphone and quiet space

### Model Selection

1. **Turbo for Interactive**: Use `eleven_turbo_v2_5` for chatbots, gaming
2. **Multilingual v2 for Quality**: Best overall quality for production
3. **Test Latency**: Balance quality vs speed for your use case
4. **Regional Deployment**: Consider API latency from your region

### Parameter Tuning

1. **Start with Defaults**: Begin with stability=0.65, similarity_boost=0.75
2. **Adjust Incrementally**: Change by 0.1 increments
3. **Test with Real Content**: Use actual production scripts
4. **Document Settings**: Save successful configurations
5. **Version Control**: Track parameter changes with content versions

### Cost Optimization

1. **Cache Audio**: Store generated audio for reuse
2. **Batch Generation**: Process multiple scripts in one session
3. **Appropriate Format**: Don't use `pcm_44100` if `mp3_44100_128` suffices
4. **Monitor Usage**: Track character consumption via `get_subscription_info()`
5. **Delete Unused Voices**: Clean up old cloned voices

## Troubleshooting

### Common Issues

#### "Voice not found" Error

**Problem**: Specified voice_id doesn't exist or isn't accessible

**Solutions:**
1. List voices to see available IDs: `await adapter.list_voices()`
2. Check if voice was deleted
3. Verify API key has access to voice
4. For cloned voices, ensure you have ownership

#### Poor Voice Quality

**Problem**: Generated audio sounds robotic or unclear

**Solutions:**
1. Increase `similarity_boost` to 0.85-0.95
2. Enable `speaker_boost=True`
3. Try `eleven_multilingual_v2` for better quality
4. Check if cloned voice had good source samples
5. Adjust `stability` for more natural variation

#### High Latency

**Problem**: Audio generation takes too long

**Solutions:**
1. Switch to `eleven_turbo_v2_5` model
2. Set `optimize_streaming_latency=3` or `4`
3. Use lower quality format like `pcm_16000`
4. Consider regional API endpoints
5. Implement streaming if supported by client

#### Rate Limit Errors

**Problem**: `ProviderRateLimitError: ElevenLabs API rate limit exceeded`

**Solutions:**
1. Check subscription tier limits
2. Implement exponential backoff (built into adapter)
3. Batch requests appropriately
4. Upgrade subscription if needed
5. Monitor usage with `get_subscription_info()`

#### Voice Cloning Fails

**Problem**: `clone_voice()` returns error

**Solutions:**
1. Check audio file format (MP3, WAV, M4A)
2. Ensure samples are 1-5 minutes total
3. Verify audio quality (no noise, clear speech)
4. Try with fewer samples (2-3 instead of 5)
5. Check API key has cloning permissions
6. Verify subscription tier supports cloning

#### Audio Storage Failures

**Problem**: Audio generated but not saved to storage

**Solutions:**
1. Check S3/MinIO credentials
2. Verify bucket exists and is accessible
3. Check storage service logs
4. Ensure sufficient disk space
5. Verify content-type is set correctly

### Debug Mode

Enable detailed logging:

```python
import logging
logging.getLogger("tts_elevenlabs").setLevel(logging.DEBUG)
```

This will show:
- API request/response details
- Audio generation parameters
- Storage upload progress
- Error stack traces

### API Status

Check ElevenLabs status:
- Status page: https://status.elevenlabs.io/
- API docs: https://docs.elevenlabs.io/

### Getting Help

1. Check logs: `logs/backend.log` and `logs/worker.log`
2. Review job metadata for TTS timeline
3. Test in mock mode to isolate API vs code issues
4. Verify API key permissions in ElevenLabs dashboard
5. Check subscription limits and usage

## Related Documentation

- [Main README](../README.md)
- [API Documentation](../api/openapi.yaml)
- [Voice Cloning Best Practices](https://elevenlabs.io/docs/voice-cloning)
- [Model Comparison](https://elevenlabs.io/docs/models)
- [Storage Configuration](../storage/presign_policy.md)
