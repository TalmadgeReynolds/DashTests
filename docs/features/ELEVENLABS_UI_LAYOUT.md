# ElevenLabs in Option 2 - Visual Guide

## Before & After

### BEFORE (Simple Voice ID Input)
```
┌─────────────────────────────────────────┐
│ Voice ID (Optional)                     │
│ ┌─────────────────────────────────────┐ │
│ │ Enter ElevenLabs voice ID...        │ │
│ └─────────────────────────────────────┘ │
│ Leave empty to use default voice        │
└─────────────────────────────────────────┘
```

### AFTER (Full-Featured Voice Controls)
```
┌────────────────────────────────────────────────────────────────┐
│ Voice Selection                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Rachel (female, young, american) ▼                         │ │
│ └────────────────────────────────────────────────────────────┘ │
│ premade • Natural, professional voice with clear pronunciation │
│                                                                │
│ ┌─────────────────────────┐ ┌─────────────────────────────┐   │
│ │ 🎭 Browse Voices        │ │ 🎙️ Clone Voice          │   │
│ └─────────────────────────┘ └─────────────────────────────┘   │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Character Usage (Free)          1,234 / 10,000            │ │
│ │ ████████░░░░░░░░░░░░░░░░░░░░░░                            │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                │
│ AI Model                                                       │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Turbo v2.5 - Enhanced turbo model ▼                        │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                │
│ Audio Format                                                   │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ MP3 44.1kHz 128kbps ▼                                      │ │
│ └────────────────────────────────────────────────────────────┘ │
│                                                                │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Advanced Voice Settings                              ▼    │ │
│ └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

### EXPANDED Advanced Settings
```
┌────────────────────────────────────────────────────────────────┐
│ ┌────────────────────────────────────────────────────────────┐ │
│ │ Advanced Voice Settings                              ▲    │ │
│ └────────────────────────────────────────────────────────────┘ │
│ ┌────────────────────────────────────────────────────────────┐ │
│ │                                                            │ │
│ │ Stability                                        0.65      │ │
│ │ ├────────●───────────────────────────────────────────────┤ │ │
│ │ Higher = more stable, Lower = more variable                │ │
│ │                                                            │ │
│ │ Similarity Boost                                 0.75      │ │
│ │ ├──────────●─────────────────────────────────────────────┤ │ │
│ │ Enhance voice similarity to original                       │ │
│ │                                                            │ │
│ │ Style Exaggeration                               0.00      │ │
│ │ ├●─────────────────────────────────────────────────────┤ │ │
│ │ Amplify the style of the voice                             │ │
│ │                                                            │ │
│ │ ☑ Speaker Boost                                            │ │
│ │   Boost similarity to speaker (recommended)                │ │
│ │                                                            │ │
│ │ Seed (Optional)                                            │ │
│ │ ┌────────────────────────────────────────────────────────┐ │ │
│ │ │ Random seed for reproducibility                        │ │ │
│ │ └────────────────────────────────────────────────────────┘ │ │
│ │ Set a seed for reproducible results                        │ │
│ │                                                            │ │
│ │ Optimize Streaming Latency                                 │ │
│ │ ┌────────────────────────────────────────────────────────┐ │ │
│ │ │ 0 - Default (best quality) ▼                           │ │ │
│ │ └────────────────────────────────────────────────────────┘ │ │
│ │ Higher values reduce latency but may affect quality        │ │
│ │                                                            │ │
│ └────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────┘
```

## Modals

### Browse Voices Modal
```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Browse Voices                                              ✕   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Search voices...                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌────────────────────────┐  ┌────────────────────────────┐    │
│  │ Rachel           ✓     │  │ Drew                       │    │
│  │ premade                │  │ premade                    │    │
│  │ Natural, professional  │  │ Deep, authoritative male   │    │
│  │ 🟣 female 🟣 young    │  │ 🟣 male 🟣 middle aged    │    │
│  └────────────────────────┘  └────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────┐  ┌────────────────────────────┐    │
│  │ Clyde                  │  │ [More voices...]           │    │
│  │ premade                │  │                            │    │
│  │ Warm, conversational   │  │                            │    │
│  │ 🟣 male 🟣 young      │  │                            │    │
│  └────────────────────────┘  └────────────────────────────┘    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Clone Voice Modal
```
┌────────────────────────────────────────────────────────────┐
│                                                            │
│  Clone a Voice                                        ✕   │
│                                                            │
│  Voice Name *                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │ e.g., My Custom Voice                              │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Description (Optional)                                    │
│  ┌────────────────────────────────────────────────────┐   │
│  │ Describe this voice...                             │   │
│  │                                                    │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  Audio Samples *                                           │
│  ┌────────────────────────────────────────────────────┐   │
│  │ [Choose Files] No file chosen                      │   │
│  └────────────────────────────────────────────────────┘   │
│  Upload 1-3 audio samples (MP3, WAV)                      │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │ sample1.mp3                              2.34 MB   │   │
│  │ sample2.wav                              1.87 MB   │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌──────────────────────────────┐  ┌─────────────────┐   │
│  │ Clone Voice                  │  │ Cancel          │   │
│  └──────────────────────────────┘  └─────────────────┘   │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

## Complete Option 2 Form Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ Create New Job                                                  │
│ Generate AI-powered lip-sync videos                            │
│                                                                 │
│ ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│ │ Option 1: Prompt    │  │ Option 2: Audio + Image         │  │ ← TABS
│ └─────────────────────┘  └──────────────────────────────────┘  │
│                                                                 │
│ ═══════════════════════════════════════════════════════════════ │
│                                                                 │
│ Portrait Image *                                                │
│ ┌─────────────────────┐  ┌──────────────────────────────────┐  │
│ │ Upload Image        │  │ ✨ Generate with AI             │  │ ← SOURCE TOGGLE
│ └─────────────────────┘  └──────────────────────────────────┘  │
│ [File input or AI generation UI]                               │
│                                                                 │
│ Audio Source *                                                  │
│ ┌─────────────────────────────────┐  ┌──────────────────────┐  │
│ │ 🎙️ Text-to-Speech (ElevenLabs)│  │ 📁 Upload Audio File │  │ ← SOURCE TOGGLE
│ └─────────────────────────────────┘  └──────────────────────┘  │
│                                                                 │
│ Text to Speak *                                                 │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Enter the text you want the character to speak...          │ │
│ │                                                             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│ 🎙️ ELEVENLABS VOICE FEATURES (SECTION STARTS HERE) ═══════════ │
│                                                                 │
│ Voice Selection                                                 │
│ [Voice dropdown]                                                │
│ [Browse Voices] [Clone Voice] buttons                           │
│ [Subscription usage bar]                                        │
│ [Model selector]                                                │
│ [Format selector]                                               │
│ [Advanced Settings toggle]                                      │
│   ↳ [Stability slider]                                          │
│   ↳ [Similarity boost slider]                                   │
│   ↳ [Style slider]                                              │
│   ↳ [Speaker boost checkbox]                                    │
│   ↳ [Seed input]                                                │
│   ↳ [Optimize latency selector]                                 │
│                                                                 │
│ 🎙️ ELEVENLABS VOICE FEATURES (SECTION ENDS HERE) ═════════════ │
│                                                                 │
│ Action Prompt (Optional)                                        │
│ [Text input]                                                    │
│                                                                 │
│ Video Options                                                   │
│ [FPS selector] [Aspect ratio selector]                          │
│                                                                 │
│ Post-Processing Enhancement                                     │
│ ☑ Frame Interpolation (RIFE)                                   │
│ ☑ Upscale Video (Topaz/Real-ESRGAN)                           │
│                                                                 │
│ Processing Priority                                             │
│ [Priority selector]                                             │
│                                                                 │
│ ┌────────────────────────────────┐  ┌──────────────────────┐   │
│ │ Create Lip-Sync Job            │  │ Cancel               │   │
│ └────────────────────────────────┘  └──────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Features Highlighted

### 🎯 Voice Selection
- **Dropdown** with all available voices
- Shows voice name + labels (gender, age, accent)
- Displays selected voice details below

### 🎭 Voice Browsing
- Opens full-screen modal
- Grid layout with voice cards
- Search/filter functionality
- Click to select

### 🎙️ Voice Cloning
- Upload 1-3 audio samples
- Name and describe your voice
- Creates custom voice immediately
- Auto-selects after cloning

### 📊 Subscription Tracking
- Shows current tier
- Character usage progress bar
- Visible during configuration

### 🤖 Model Selection
- 5 AI models to choose from
- Turbo v2.5 (fastest) default
- Descriptions for each model

### 🎵 Format Selection
- 7 audio formats available
- MP3, PCM, μ-law options
- Different sample rates/bitrates

### ⚙️ Advanced Settings
- Collapsible panel
- 6 fine-tuning parameters
- Sliders, checkboxes, inputs
- Tooltips explain each setting

## Mobile Responsive
All elements stack vertically on mobile:
- Tabs become full width
- Voice browser modal adapts
- Sliders remain usable
- Grid becomes single column
