# Heygen Feature Enhancement Plan

## Current State (Very Limited)
Currently in Option 2, Heygen only has:
- Action Prompt: Simple text input (max 120 chars)
- FPS: 24 or 30
- Aspect Ratio: 16:9, 9:16, 1:1

## Heygen API Typical Features

### 1. **Talking Photo API Features**
- `image_url` - Portrait image (currently supported)
- `audio_url` - Audio file (currently supported)
- `action_prompt` - Actions like "nod head" (currently supported)
- `fps` - Frame rate (currently supported: 24, 30)
- `output_format` - Video format (hardcoded to "mp4")
- `quality` - Video quality settings
- `background_color` - Background color/image
- `expression_intensity` - Control facial expression strength
- `voice_settings` - Voice modulation if using built-in voices
- `aspect_ratio` - Video dimensions
- `duration` - Max video duration

### 2. **Avatar API Features** (if switching to avatars)
- `avatar_id` - Pre-made avatar selection
- `avatar_style` - Realistic, cartoon, etc.
- `voice_id` - Built-in voice library
- `background` - Green screen, custom, templates
- `camera_angle` - Front, side, close-up
- `props` - Virtual objects/props
- `clothing` - Avatar clothing options

### 3. **Video Enhancement Features**
- `auto_caption` - Auto-generate captions
- `remove_background` - Greenscreen effect
- `add_watermark` - Custom watermark
- `thumbnail` - Custom thumbnail
- `intro/outro` - Video bookends

## Proposed Enhancement for Option 2

### Add Heygen Advanced Settings Section (Similar to ElevenLabs)

```
┌─────────────────────────────────────────────────────────────┐
│ 🎬 Heygen Video Settings                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ Quality                                                     │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ High (1080p) ▼                                          │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Output Format                                               │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ MP4 (H.264) ▼                                           │ │
│ └─────────────────────────────────────────────────────────┘ │
│                                                             │
│ Expression Intensity                                        │
│ ├────────●─────────────────────────────────────────────────┤ │
│ 0                      0.7                            1.0   │
│ Subtle                 Natural                    Exaggerated │
│                                                             │
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Advanced Video Settings                            ▼   │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Expanded Advanced Settings
```
┌─────────────────────────────────────────────────────────────┐
│ Background Options                                          │
│ ○ Original   ● Blur   ○ Color   ○ Remove                   │
│                                                             │
│ [If Color selected]                                         │
│ Background Color: [#FFFFFF] 🎨                              │
│                                                             │
│ Camera Movement                                             │
│ ○ Static   ● Subtle Zoom   ○ Follow Face                    │
│                                                             │
│ Auto Captions                                               │
│ ☐ Add automatic captions                                    │
│ Language: [English ▼]                                       │
│                                                             │
│ Watermark                                                   │
│ ☐ Add watermark                                             │
│ Text: [                    ]                                │
│ Position: [Bottom Right ▼]                                  │
│                                                             │
│ Video Duration Limit                                        │
│ ┌────────────────────────────────────────────────┐          │
│ │ 60 seconds                                     │          │
│ └────────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Backend Enhancement
1. Update `heygen_adapter.py` to support new parameters
2. Add new fields to adapter's `create_talking_photo()` method
3. Update mock mode to simulate new features

### Phase 2: Frontend Enhancement
1. Add new state variables for Heygen settings
2. Create Heygen Settings section in Option 2 form
3. Add quality, format, expression intensity controls
4. Add collapsible Advanced Settings panel
5. Update form submission to include all parameters

### Phase 3: Type Updates
1. Update `CreateAudioJobRequest` to include Heygen options
2. Add `HeygenVideoSettings` interface
3. Update job schema types

## Comparison: ElevenLabs vs Heygen

### ElevenLabs (Audio) - DONE ✅
- Voice selection dropdown
- Browse voices modal
- Clone voice feature
- 5 AI models
- 7 output formats
- 6 advanced synthesis settings
- Subscription usage tracking

### Heygen (Video) - TO DO 📋
- Quality settings
- Output format selection
- Expression intensity control
- Background options
- Camera movement
- Auto captions
- Watermark
- Duration limits

Both should have similar UI patterns for consistency.
