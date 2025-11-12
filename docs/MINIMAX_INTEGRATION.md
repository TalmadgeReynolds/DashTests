# MiniMax Hailuo 2.3 Integration Guide

## Overview

Complete integration of MiniMax Hailuo 2.3 video generation API with support for all models, generation modes, and features.

## Features Implemented

### ✅ Models (A)
- **MiniMax-Hailuo-2.3**: Premium model with best quality
  - Advanced body movement
  - Detailed facial expressions
  - Physical realism
  - Best prompt adherence
  - Max duration: 6 seconds
  - Resolution: 720p

- **MiniMax-Hailuo-2.3-Fast**: Optimized for speed
  - Fast image-to-video conversion
  - Quick generation
  - Max duration: 6 seconds
  - Resolution: 720p

- **MiniMax-Hailuo-02**: Legacy model with extended features
  - Higher resolution (1080p)
  - Longer duration (up to 10 seconds)
  - Strong prompt adherence

### ✅ Generation Modes (B)

#### 1. Text-to-Video (T2V)
Generate videos from text descriptions only.

**Endpoint**: `POST /api/v1/minimax/generate/text-to-video`

**Request**:
```json
{
  "prompt": "A dog running through a field of flowers",
  "model": "MiniMax-Hailuo-2.3",
  "aspect_ratio": "16:9",
  "duration_seconds": 6,
  "prompt_optimizer": true,
  "seed": 42
}
```

#### 2. Image-to-Video (I2V)
Animate static images into videos.

**Endpoint**: `POST /api/v1/minimax/generate/image-to-video`

**Request**:
```json
{
  "prompt": "The person smiles and waves at the camera",
  "first_frame_image": "base64_encoded_image_or_url",
  "model": "MiniMax-Hailuo-2.3-Fast",
  "aspect_ratio": "16:9",
  "duration_seconds": 6
}
```

#### 3. First/Last Frame to Video (FL2V)
Generate video interpolating between two keyframes.

**Endpoint**: `POST /api/v1/minimax/generate/first-last-frame`

**Request**:
```json
{
  "prompt": "Smooth camera pan from left to right",
  "first_frame_image": "base64_encoded_first_frame",
  "last_frame_image": "base64_encoded_last_frame",
  "model": "MiniMax-Hailuo-2.3",
  "aspect_ratio": "16:9",
  "duration_seconds": 6
}
```

#### 4. Subject Reference to Video (S2V)
Maintain character or style consistency across generation.

**Endpoint**: `POST /api/v1/minimax/generate/subject-reference`

**Request**:
```json
{
  "prompt": "Character walks forward confidently",
  "reference_image": "base64_encoded_reference",
  "reference_type": "character",
  "model": "MiniMax-Hailuo-2.3",
  "aspect_ratio": "16:9",
  "duration_seconds": 6
}
```

### ✅ Configuration Options (C)

#### Aspect Ratios
- `16:9` - Widescreen (default)
- `9:16` - Vertical/Portrait
- `1:1` - Square
- `4:3` - Standard
- `3:4` - Portrait
- `21:9` - Ultrawide
- `9:21` - Ultra Vertical

#### Duration
- Hailuo 2.3 / 2.3-Fast: 2-6 seconds
- Hailuo 02: 2-10 seconds

#### Other Parameters
- **prompt_optimizer**: Enable automatic prompt enhancement (default: true)
- **seed**: Random seed for reproducibility (optional)
- **callback_url**: Webhook URL for completion notification (optional)

### ✅ Async Task Management (D)

#### 1. Create Task
All generation endpoints return a `task_id`:

**Response**:
```json
{
  "task_id": "task_abc123xyz",
  "status": "queued",
  "message": "Task created successfully"
}
```

#### 2. Poll Task Status
Query the status of a video generation task.

**Endpoint**: `GET /api/v1/minimax/task/{task_id}/status`

**Response**:
```json
{
  "task_id": "task_abc123xyz",
  "status": "processing",
  "progress": 75,
  "duration": 6,
  "aspect_ratio": "16:9",
  "created_at": "2025-11-12T10:30:00Z"
}
```

**Status Values**:
- `queued` - Waiting to be processed
- `processing` - Video is being generated
- `success` - Video is ready (includes `file_id`)
- `failed` - Generation failed (includes `error`)

#### 3. Download Video
Download and store the generated video.

**Endpoint**: `POST /api/v1/minimax/task/{task_id}/download`

**Response**:
```json
{
  "task_id": "task_abc123xyz",
  "file_id": "file_xyz789",
  "video_url": "https://your-s3-bucket.s3.amazonaws.com/videos/minimax/video.mp4",
  "size_bytes": 5242880,
  "message": "Video downloaded and stored successfully"
}
```

#### 4. Poll Until Complete (Convenience Endpoint)
Automatically poll until completion and download.

**Endpoint**: `POST /api/v1/minimax/task/{task_id}/poll?max_wait_seconds=300&auto_download=true`

**Response**:
```json
{
  "task_id": "task_abc123xyz",
  "status": "success",
  "file_id": "file_xyz789",
  "video_url": "https://...",
  "size_bytes": 5242880
}
```

## Backend Architecture

### Files Created/Modified

```
backend/
├── adapters/
│   └── minimax_adapter.py          # Core adapter with all generation modes
├── schemas/
│   └── minimax.py                  # Pydantic schemas for requests/responses
├── services/
│   └── minimax_service.py          # Business logic and job tracking
├── routes/
│   └── minimax.py                  # API routes for all endpoints
├── utils/
│   └── settings.py                 # Updated with MiniMax settings
└── main.py                         # Registered MiniMax routes

tests/
└── test_minimax_adapter.py         # Comprehensive test suite
```

### Key Classes

#### MinimaxAdapter
Core adapter class handling API communication:
- `text_to_video()` - T2V generation
- `image_to_video()` - I2V generation
- `first_last_frame_to_video()` - FL2V generation
- `subject_reference_to_video()` - S2V generation
- `query_task_status()` - Status polling
- `download_video()` - File download
- `poll_until_complete()` - Automated polling

#### MinimaxService
Business logic layer:
- Job tracking and metadata storage
- Integration with storage service
- Automatic video download and S3 upload
- Job listing and filtering

## Frontend Integration

### Files Created

```
frontend/src/
├── components/
│   └── MinimaxVideoGenerator.tsx   # Comprehensive UI component
├── pages/
│   └── MinimaxVideo.tsx            # Page wrapper
└── App.tsx                         # Updated with route
```

### Component Features

The `MinimaxVideoGenerator` component provides:

✅ **Mode Selection**
- Visual buttons for all 4 generation modes
- Mode-specific configuration UI

✅ **Configuration**
- Text prompt input with validation
- Image upload for I2V, FL2V, S2V modes
- Model selection dropdown
- Aspect ratio selector
- Duration slider
- Prompt optimizer toggle
- Seed input for reproducibility

✅ **Task Management**
- Real-time status display
- Progress bar for processing tasks
- Automatic polling
- Video preview when complete
- Download link

✅ **Recent Tasks**
- List of recent generation tasks
- Status indicators with icons
- Quick access to previous generations

### Usage

Navigate to `/minimax` in the frontend application to access the full UI.

## Configuration

### Environment Variables

Add to `.env`:

```bash
# MiniMax API Configuration
MINIMAX_API_KEY=your_api_key_here
MINIMAX_GROUP_ID=your_group_id_here  # Optional
MINIMAX_MOCK_MODE=true  # Set to false for production
```

### Mock Mode

By default, the integration runs in mock mode for development and testing:

- ✅ All API calls work without actual API keys
- ✅ Instant responses with mock data
- ✅ Full workflow testing
- ✅ No API charges

Set `MINIMAX_MOCK_MODE=false` when ready to use real API.

## API Endpoints Reference

### Generation Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/minimax/generate/text-to-video` | POST | Text-to-Video generation |
| `/api/v1/minimax/generate/image-to-video` | POST | Image-to-Video generation |
| `/api/v1/minimax/generate/first-last-frame` | POST | First/Last frame interpolation |
| `/api/v1/minimax/generate/subject-reference` | POST | Subject reference generation |

### Task Management Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/minimax/task/{task_id}/status` | GET | Query task status |
| `/api/v1/minimax/task/{task_id}/download` | POST | Download and store video |
| `/api/v1/minimax/task/{task_id}/poll` | POST | Poll until complete |

### Information Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/minimax/models/capabilities` | GET | List all model capabilities |
| `/api/v1/minimax/jobs` | GET | List recent jobs |

## Testing

Run the comprehensive test suite:

```bash
# Run all MiniMax tests
pytest tests/test_minimax_adapter.py -v

# Run specific test class
pytest tests/test_minimax_adapter.py::TestMinimaxAdapterMockMode -v

# Run with coverage
pytest tests/test_minimax_adapter.py --cov=backend.adapters.minimax_adapter
```

### Test Coverage

✅ Mock mode operations
✅ All 4 generation modes
✅ Parameter validation
✅ Aspect ratio support
✅ Duration ranges
✅ Seed reproducibility
✅ Polling functionality
✅ Image encoding
✅ Error handling
✅ Complete workflows
✅ Integration tests

## Usage Examples

### Python (Backend)

```python
from backend.adapters.minimax_adapter import MinimaxAdapter, MinimaxModel

adapter = MinimaxAdapter()

# Text-to-Video
task_id = await adapter.text_to_video(
    prompt="A cat playing with a ball of yarn",
    model=MinimaxModel.HAILUO_2_3,
    aspect_ratio="16:9",
    duration_seconds=6
)

# Poll until complete
result = await adapter.poll_until_complete(task_id)

# Download video
video_bytes = await adapter.download_video(result["file_id"])
```

### TypeScript/React (Frontend)

```tsx
import MinimaxVideoGenerator from '@/components/MinimaxVideoGenerator';

function MyPage() {
  const handleVideoGenerated = (videoUrl: string, taskId: string) => {
    console.log('Video ready:', videoUrl);
  };

  return (
    <MinimaxVideoGenerator 
      onVideoGenerated={handleVideoGenerated}
      defaultMode="t2v"
    />
  );
}
```

### cURL (API)

```bash
# Create T2V task
curl -X POST http://localhost:8000/api/v1/minimax/generate/text-to-video \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A bird flying through clouds",
    "model": "MiniMax-Hailuo-2.3",
    "aspect_ratio": "16:9",
    "duration_seconds": 6
  }'

# Check status
curl http://localhost:8000/api/v1/minimax/task/task_abc123/status

# Download video
curl -X POST http://localhost:8000/api/v1/minimax/task/task_abc123/download
```

## Best Practices

### Model Selection
- Use **Hailuo 2.3** for best quality and realism
- Use **Hailuo 2.3-Fast** for quick I2V conversions
- Use **Hailuo 02** for higher resolution or longer videos

### Prompt Writing
- Be specific and descriptive
- Enable prompt optimizer for better results
- Include motion descriptions
- Specify camera movements

### Error Handling
- Always check task status before downloading
- Implement retry logic for transient errors
- Set reasonable polling timeouts
- Handle rate limits gracefully

### Performance
- Use webhooks (callback_url) instead of polling for production
- Cache task results
- Implement background processing for long tasks
- Monitor API usage and costs

## Troubleshooting

### Common Issues

**Issue**: Task stuck in "queued" status
- **Solution**: Check API key and rate limits

**Issue**: Video download fails
- **Solution**: Ensure task status is "success" before downloading

**Issue**: Mock mode not working
- **Solution**: Verify `MINIMAX_MOCK_MODE=true` in settings

**Issue**: Frontend component not showing
- **Solution**: Check route is registered in App.tsx

## Summary

✅ **All Features Implemented**:
- ✅ A: All 3 models (Hailuo 2.3, 2.3-Fast, 02)
- ✅ B: All 4 generation modes (T2V, I2V, FL2V, S2V)
- ✅ C: Full configuration support (aspect ratios, durations, etc.)
- ✅ D: Complete async workflow (create, poll, download)

✅ **Additional Features**:
- Comprehensive error handling
- Mock mode for development
- Full test coverage
- Beautiful frontend UI
- Webhook support
- Job tracking
- Model capabilities API

The integration is production-ready and follows best practices for async video generation workflows.
