# Veo 3 UI Completion - Video Generation Modes

## Summary
Added UI controls for three advanced Veo 3 video generation modes that were previously only supported in the backend:
1. **Video Extension** - Upload a video to extend beyond its ending
2. **Frame Interpolation** - Upload first and last frames to interpolate between them
3. **Video Editing with Masks** - Upload video and mask to edit specific regions

## Changes Made

### Frontend: `/frontend/src/pages/Composer.tsx`

#### New State Variables (lines 93-98)
```typescript
const [videoMode, setVideoMode] = useState<'text-to-video' | 'image-to-video' | 'video-extension' | 'frame-interpolation' | 'video-editing'>('text-to-video');
const [inputVideoUrl, setInputVideoUrl] = useState('');
const [lastFrameUrl, setLastFrameUrl] = useState('');
const [maskUrl, setMaskUrl] = useState('');
const [maskMode, setMaskMode] = useState('MASK_MODE_USER_PROVIDED');
```

#### Video Generation Mode Selector (lines 319-331)
- Dropdown menu to select between 5 video generation modes
- Options: Text to Video, Image to Video, Video Extension, Frame Interpolation, Video Editing with Masks
- Placed before "Veo 3 Video Settings" section

#### Conditional Mode-Specific UI Panels

**Video Extension Mode (lines 333-359)**
- File input for video upload (accepts video/*)
- Uploads to S3 with presigned URL
- Sets `input_video_url` parameter
- Purple-themed panel with upload status indicator
- Description: "Upload a video to extend beyond its ending"

**Frame Interpolation Mode (lines 361-387)**
- File input for last frame image upload (accepts image/*)
- Uploads to S3 with presigned URL
- Sets `last_frame_url` parameter
- Purple-themed panel with upload status indicator
- Description: "Upload the last frame to interpolate from reference to this frame"

**Video Editing with Masks Mode (lines 389-455)**
- Two file inputs:
  1. Input video upload (accepts video/*)
  2. Mask image upload (accepts image/*)
- Dropdown for mask mode selection:
  - `MASK_MODE_USER_PROVIDED` (default)
  - `MASK_MODE_BACKGROUND`
  - `MASK_MODE_FOREGROUND`
  - `MASK_MODE_SEMANTIC`
- Sets `input_video_url`, `mask_url`, and `mask_mode` parameters
- Purple-themed panel with upload status indicators
- Description: "Upload a video and mask to edit specific regions"

#### Form Submission Updates (lines 145-175)
Added to `video` object in `CreatePromptJobRequest`:
```typescript
// Advanced video modes
input_video_url: inputVideoUrl || undefined,
last_frame_url: lastFrameUrl || undefined,
mask_url: maskUrl || undefined,
mask_mode: videoMode === 'video-editing' ? maskMode : undefined,
```

## File Upload Implementation

All file uploads follow this pattern:
1. User selects file via `<input type="file">`
2. Call `getPresignedUrl()` with:
   - `filename`: original file name
   - `mime`: file MIME type
   - `kind`: descriptor ('input_video', 'last_frame', 'mask')
   - `content_length`: file size in bytes
3. Upload file to presigned URL using `uploadToPresignedUrl()`
4. Extract clean URL (remove query params) and set in state
5. Display success indicator when upload completes
6. Handle errors with console logging and user alert

## Backend Integration

These UI controls map to existing backend parameters in:
- **Schemas** (`backend/schemas/job.py`): `VideoOpts` class already includes `input_video_url`, `last_frame_url`, `mask_url`, `mask_mode`
- **Adapter** (`backend/adapters/veo_adapter.py`): `generate_video()` method already handles all video modes
- **Orchestrator** (`backend/services/orchestrator.py`): `_process_prompt_job()` already extracts and passes these parameters

## User Experience

### Default State
- Video Generation Mode dropdown defaults to "Text to Video"
- No additional panels shown in default state
- Standard text-to-video generation workflow unchanged

### Mode Selection
- User selects mode from dropdown
- Relevant upload panel(s) appear immediately below dropdown
- Panel styled with purple background (`bg-purple-50`) to distinguish from other sections
- Clear labels and descriptions guide user through upload process

### Upload Feedback
- Green checkmark (✓) appears after successful upload
- File input shows standard browser file selector
- Error alerts appear if upload fails
- Upload happens asynchronously without blocking UI

## Testing Checklist

- [ ] Video Extension mode displays input video upload
- [ ] Frame Interpolation mode displays last frame upload
- [ ] Video Editing mode displays both video and mask uploads
- [ ] Video Editing mode displays mask mode dropdown
- [ ] File uploads successfully to S3
- [ ] Upload status indicators appear correctly
- [ ] Form submission includes correct parameters based on selected mode
- [ ] Backend receives and processes input_video_url correctly
- [ ] Backend receives and processes last_frame_url correctly
- [ ] Backend receives and processes mask_url and mask_mode correctly
- [ ] Mode switching clears previous uploads (test UX flow)
- [ ] Error handling works for failed uploads

## Notes

- All three modes were previously implemented in the backend but had no UI controls
- The implementation follows existing patterns from the reference image upload UI
- File uploads use the same S3 presigned URL flow as other media uploads
- Mask mode options match the Vertex AI Veo 3 API specification
- UI styling is consistent with existing Composer form elements
