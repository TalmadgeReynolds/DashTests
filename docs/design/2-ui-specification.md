# UI Specification

**Version**: 1.0.0  
**Last Updated**: October 12, 2025  
**Status**: Design Complete, Ready for Development

---

## Table of Contents

1. [Overview](#overview)
2. [Information Architecture](#information-architecture)
3. [Layout System](#layout-system)
4. [Screen Specifications](#screen-specifications)
   - [Dashboard / Jobs Gallery](#1-dashboard--jobs-gallery)
   - [Composer (Main Creation)](#2-composer-main-creation)
   - [Job Detail](#3-job-detail)
   - [Preset Manager](#4-preset-manager)
   - [Batch Import](#5-batch-import)
   - [Settings](#6-settings)
5. [Component Specifications](#component-specifications)
6. [User Flows](#user-flows)
7. [Implementation Notes](#implementation-notes)

---

## Overview

### Purpose
The AI Lip-Sync Companion App enables users to create AI-generated lip-sync videos using two workflows:
- **Option 1**: Text prompt → VEO3 video generation
- **Option 2**: Image + Audio → Heygen talking head

### Target Users
- **Content Creators**: Social media, marketing, education
- **Professionals**: Video producers, agencies, studios
- **Experimenters**: AI enthusiasts, hobbyists

### Key Design Goals
1. Simple enough for first-time users (< 2 min to first video)
2. Powerful enough for professionals (batch processing, presets)
3. Transparent costs and AI decisions (trust-building)
4. Fast iteration (compare, rerun, tweak)

---

## Information Architecture

```
App Structure:
├── Dashboard (Home)
│   ├── Job Gallery (grid/list view)
│   ├── Filters & Search
│   └── Quick Actions
├── Composer (Create New)
│   ├── Mode Selector (Prompt | Image+Audio)
│   ├── Prompt Mode Interface
│   │   ├── Script Editor
│   │   ├── Prompt Sharpener
│   │   ├── Reference Image Upload
│   │   └── Settings
│   ├── Image+Audio Mode Interface
│   │   ├── Portrait Upload
│   │   ├── Audio Upload / TTS
│   │   ├── Action Prompts
│   │   └── Settings
│   └── Context Panel (Preview, Cost, Presets)
├── Job Detail
│   ├── Video Player
│   ├── Timeline
│   ├── Logs
│   └── Actions (Download, Rerun, Compare)
├── Library
│   ├── Preset Manager
│   ├── Voice Library (saved ElevenLabs voices)
│   └── Asset Manager
├── Batch
│   ├── CSV Upload
│   ├── Validation
│   └── Queue Management
└── Settings
    ├── API Keys
    ├── Webhooks
    ├── Billing
    └── Preferences
```

---

## Layout System

### Desktop Layout (1280px+)

```
┌─────────────────────────────────────────────────────────────────┐
│  TopBar (64px height)                                           │
│  Logo | Project Dropdown | Cost Budget Bar | User Avatar        │
├───────┬─────────────────────────────────────────────┬───────────┤
│       │                                             │           │
│  Nav  │            Main Canvas                      │  Context  │
│ Rail  │           (Flexible width)                  │   Panel   │
│ 72px  │                                             │   320px   │
│       │                                             │           │
│   •   │  Screen-specific content                    │  Preview  │
│ Home  │                                             │  Player   │
│       │                                             │           │
│   •   │                                             │  Cost     │
│ Jobs  │                                             │  Est.     │
│       │                                             │           │
│   •   │                                             │  Presets  │
│Create │                                             │  Quick    │
│       │                                             │  Actions  │
│   •   │                                             │           │
│Library│                                             │           │
│       │                                             │           │
│   •   │                                             │           │
│ Batch │                                             │           │
│       │                                             │           │
│   •   │                                             │           │
│Settings                                             │           │
│       │                                             │           │
└───────┴─────────────────────────────────────────────┴───────────┘
```

### Responsive Breakpoints

| Breakpoint | Width | Layout | Nav | Context Panel |
|------------|-------|--------|-----|---------------|
| Mobile | < 768px | Single column | Bottom tabs | Drawer (swipe up) |
| Tablet | 768-1279px | 2 column | Side rail | Collapsible |
| Desktop | 1280-1919px | 3 column | Side rail | Fixed 280px |
| Wide | ≥ 1920px | 3 column | Side rail | Fixed 320px |

---

## Screen Specifications

### 1. Dashboard / Jobs Gallery

**Route**: `/` or `/dashboard`  
**Purpose**: Overview of all jobs with filtering, sorting, and quick actions

#### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Dashboard                                      [+ New Job]      │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Filters:                                                    │ │
│  │ [All Status ▾] [All Engines ▾] [Date Range ▾] [Search...]  │ │
│  │                                                             │ │
│  │ View: [⊞ Grid] [☰ List] [📊 Timeline]     Sort: [Recent ▾] │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ Job Card 1   │ Job Card 2   │ Job Card 3   │ Job Card 4   │  │
│  │              │              │              │              │  │
│  │ [Thumbnail]  │ [Thumbnail]  │ [Thumbnail]  │ [Thumbnail]  │  │
│  │              │              │              │              │  │
│  │ "Product     │ "Welcome     │ "Tutorial    │ "Social      │  │
│  │  Demo"       │  Message"    │  Intro"      │  Post"       │  │
│  │              │              │              │              │  │
│  │ VEO3 • 15s   │ Heygen • 12s │ VEO3 • 20s   │ Heygen • 8s  │  │
│  │ $8.50        │ $3.20        │ $12.40       │ $2.10        │  │
│  │              │              │              │              │  │
│  │ ✓ Completed  │ ⚙ Running    │ ✓ Completed  │ ❌ Failed    │  │
│  │ 2 hrs ago    │ ●●●●○ 75%    │ 1 day ago    │ 3 hrs ago    │  │
│  │              │              │              │              │  │
│  │ [Play][⋮]    │ [View][⋮]    │ [Play][⋮]    │ [Retry][⋮]   │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                  │
│  ┌──────────────┬──────────────┬──────────────┬──────────────┐  │
│  │ Job Card 5   │ Job Card 6   │ Job Card 7   │ Job Card 8   │  │
│  │ ...          │ ...          │ ...          │ ...          │  │
│  └──────────────┴──────────────┴──────────────┴──────────────┘  │
│                                                                  │
│  [Load More...]                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Job Card Specifications

**Dimensions**: 280×320px (grid), full-width (list)  
**Padding**: 16px  
**Border radius**: 12px  
**Shadow**: 0 1px 3px rgba(0,0,0,0.1)

**Components**:
- **Thumbnail**: 248×140px, 16:9 aspect, loading placeholder
- **Title**: 1-2 lines, truncate with ellipsis, font-weight: 600
- **Metadata**: Engine • Duration • Cost
- **Status Badge**:
  - ✓ Completed (green)
  - ⚙ Running (blue, animated spinner)
  - ⏳ Pending (gray)
  - ❌ Failed (red)
- **Progress Bar**: Only for running jobs (0-100%)
- **Actions**:
  - Play (completed jobs)
  - View (all jobs)
  - Retry (failed jobs)
  - Menu (⋮): Download, Rerun, Compare, Delete

#### States

**Empty State**:
```
┌─────────────────────────────────────┐
│                                     │
│  📹  No jobs yet                    │
│                                     │
│  Create your first AI video         │
│  [Get Started →]                    │
│                                     │
│  or try a sample:                   │
│  • Product Demo Template            │
│  • Tutorial Intro Template          │
│  • Social Media Post Template       │
│                                     │
└─────────────────────────────────────┘
```

**Loading State**: Skeleton cards with shimmer animation

**Error State**: "Failed to load jobs. [Retry]"

#### Interactions

1. **Click card**: Navigate to Job Detail
2. **Click Play**: Open video player modal (completed jobs only)
3. **Click Menu (⋮)**: Show contextual menu
4. **Select multiple** (Shift/Cmd+click): Enable bulk actions bar
5. **Drag to compare**: Drag 2+ cards into compare zone

#### Compare Mode

When 2+ jobs selected:
```
┌─────────────────────────────────────────────────────────────────┐
│  Compare Selected (3 jobs)                      [Exit Compare]  │
├─────────────────────────────────────────────────────────────────┤
│  ┌────────────────┬────────────────┬────────────────┐           │
│  │ Job 1          │ Job 2          │ Job 3          │           │
│  │ [Video Player] │ [Video Player] │ [Video Player] │           │
│  │                │                │                │           │
│  │ VEO3 • $8.50   │ Heygen • $3.20 │ VEO3 • $12.40  │           │
│  │ 30fps, 1080p   │ 24fps, 720p    │ 60fps, 4K      │           │
│  │                │                │                │           │
│  │ [Download]     │ [Download]     │ [Download]     │           │
│  └────────────────┴────────────────┴────────────────┘           │
│                                                                  │
│  [✓ Sync Playback] [Export All] [Create Variant From Best]     │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2. Composer (Main Creation)

**Route**: `/create`  
**Purpose**: Single-page workspace for creating jobs (both workflows)

#### Top Toolbar

```
┌─────────────────────────────────────────────────────────────────┐
│  Create New Job                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ Mode: ●Prompt to Video  ○Image + Audio                     │ │
│  │                                                             │ │
│  │ [Load Preset ▾] [Batch Import] [Save as Draft] [Run Job →]│ │
│  └────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

#### Prompt Mode Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  Script / Prompt                                    [AI ✨]      │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ We finally shipped the feature—and yes, it actually      │   │
│  │ works!                                                    │   │
│  │                                                           │   │
│  │                                                           │   │
│  │  82 characters • ~6 seconds • Estimated: $4.20           │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Reference Image (optional)                [Upload or Generate] │
│  ┌──────────────────────────────────┐                           │
│  │ [Drag & drop or click]           │    [🎨 AI Generate Face] │
│  │                                  │                           │
│  │  Supported: JPG, PNG, WEBP       │    Tip: Use front-facing │
│  │  Max size: 10 MB                 │    photos for best       │
│  │  Face detection: ✓ Required      │    lip-sync quality      │
│  └──────────────────────────────────┘                           │
│                                                                  │
│  Engine: ●VEO3  ○Heygen                                         │
│                                                                  │
│  ▶ Advanced Settings                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Duration Override: [Auto ▾]  (Auto-calculated from text) │   │
│  │ Aspect Ratio: [16:9 ▾]  (16:9, 9:16, 1:1, 4:5)          │   │
│  │ FPS: [30 ▾]  (24, 30, 60)                                │   │
│  │                                                           │   │
│  │ Post-FX:                                                  │   │
│  │ [✓] Interpolate (smooth motion, 2x frame rate)           │   │
│  │ [✓] Upscale (enhance to 1080p/4K)                        │   │
│  │ [ ] Topaz Video AI (premium quality, +$5/min)            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### Prompt Sharpener Modal

Triggered by clicking [AI ✨] button next to script field.

```
┌─────────────────────────────────────────────────────────────────┐
│  ✨ AI Prompt Sharpener                              [✕ Close]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Original Prompt:                                                │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ "We finally shipped the feature—and yes, it actually     │   │
│  │  works!"                                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Model: [●Both GPT+Claude  ○GPT-4o  ○Claude ▾]                  │
│  Variants: [3 ▾]  Temperature: [0.1 ▾]                          │
│                                                                  │
│  [✨ Generate Variants]                                          │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  ⭐ Variant 1 (GPT-4o) • Score: 0.92 • Best Match               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ "Tight medium close-up, subject centered, soft frontal   │   │
│  │  key light, shallow depth of field. Subject speaks       │   │
│  │  clearly: 'We finally shipped the feature, and it        │   │
│  │  actually works!' Natural micro head motion, genuine      │   │
│  │  smile, steady eye contact. Avoid exaggerated gestures." │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  📊 Changes Made:                                                │
│  • Added camera framing: "Tight medium close-up, centered"      │
│  • Added lighting: "soft frontal key light"                     │
│  • Explicit speech: Wrapped dialogue in quotes                  │
│  • Performance cues: "micro head motion, genuine smile"         │
│  • Negative prompt: "Avoid exaggerated gestures"                │
│                                                                  │
│  💡 Why Changed: Added shot framing, lighting direction,         │
│  explicit speech text, and subtle performance cues. These       │
│  improve VEO3's ability to generate accurate lip-sync and       │
│  natural facial expressions.                                    │
│                                                                  │
│  Similarity to Original: ██████████████░░ 0.89 (Intent preserved)│
│                                                                  │
│  [← Edit] [Apply to Composer →] [↻ Regenerate]                 │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  Variant 2 (Claude) • Score: 0.89                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ "Medium shot with centered subject and soft lighting.     │   │
│  │  Clear delivery: 'We finally shipped the feature—it       │   │
│  │  actually works.' Subtle positive body language and       │   │
│  │  natural facial expressions."                             │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  📊 Changes: camera angle, lighting, delivery style             │
│  💡 Why: More conversational, less technical framing            │
│                                                                  │
│  [← Edit] [Apply to Composer →]                                │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  Variant 3 (GPT-4o) • Score: 0.85                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ "Frontal close-up. Speak: 'We finally shipped the        │   │
│  │  feature and yes, it works!' Natural expression."         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  [← Edit] [Apply to Composer →]                                │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Diff Viewer (Toggle View)**:

```
Diff View (click "Show Diff"):
┌──────────────────────────────────────────────────────────────┐
│ [-We finally shipped the feature—and yes, it actually works!-]│
│                                                               │
│ {+"Tight medium close-up, subject centered, soft frontal key │
│  light, shallow depth of field. Subject speaks clearly:      │
│  'We finally shipped the feature, and it actually works!'    │
│  Natural micro head motion, genuine smile, steady eye        │
│  contact. Avoid exaggerated gestures."+}                     │
└──────────────────────────────────────────────────────────────┘

Legend:
[-text-]  = Removed
{+text+}  = Added
```

#### Image+Audio Mode Interface

```
┌─────────────────────────────────────────────────────────────────┐
│  Portrait Image                                  [Upload to S3] │
│  ┌──────────────────────────────────┐                           │
│  │                                  │                           │
│  │  [Drag image or click]           │  Requirements:            │
│  │                                  │  • Front-facing portrait  │
│  │  Face Detection: ✓ Detected      │  • Clear facial features │
│  │  Quality: ● Excellent            │  • Well lit              │
│  │                                  │  • No sunglasses         │
│  └──────────────────────────────────┘                           │
│                                                                  │
│  Audio Source:                                                   │
│  ○ Upload Audio File    ● Generate with TTS                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Text for Speech:                                          │   │
│  │ ┌────────────────────────────────────────────────────┐   │   │
│  │ │ Welcome to our new platform. Let me show you       │   │   │
│  │ │ some of the exciting features we've built...       │   │   │
│  │ │                                                     │   │   │
│  │ │  142 characters • ~12 seconds • $0.42              │   │   │
│  │ └────────────────────────────────────────────────────┘   │   │
│  │                                                           │   │
│  │ Voice: [Rachel - Conversational ▾]         [▶ Preview]   │   │
│  │                                                           │   │
│  │ Stability:  ●────────○───  0.7  (Lower = more variable)  │   │
│  │ Similarity: ●──────────○─  0.8  (Higher = closer match)  │   │
│  │ Speed:      ●──────○─────  1.0  (0.5x - 2.0x)            │   │
│  │                                                           │   │
│  │ [Save as Preset Voice] [Browse Voice Library]            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Action Prompts (optional - what should the person do?)         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Smile warmly and gesture with right hand                 │   │
│  │                                                           │   │
│  │  ✓ Valid • 42 characters                                 │   │
│  │  Examples: "Occasional blink", "Slight nod", "Big smile" │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ▶ Advanced Settings                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ Aspect Ratio: [16:9 ▾]                                   │   │
│  │ Background: [Auto ▾]  (Auto, Solid Color, Custom)        │   │
│  │                                                           │   │
│  │ Post-FX:                                                  │   │
│  │ [✓] Interpolate (smooth motion)                          │   │
│  │ [✓] Upscale (enhance quality)                            │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

#### Context Panel (Right Side - Always Visible)

```
┌───────────────────────┐
│ Preview               │
│ ┌───────────────────┐ │
│ │                   │ │
│ │  [Video Player]   │ │
│ │   or Image        │ │
│ │                   │ │
│ │  ▶ Play           │ │
│ │  ━━━━━━○━━━ 0:08  │ │
│ └───────────────────┘ │
│                       │
│ Cost Estimate         │
│ ─────────────────     │
│ VEO3 Generation $4.20 │
│ TTS (11Labs)    $0.30 │
│ Interpolation   $1.00 │
│ Upscale         $2.00 │
│ ─────────────────     │
│ Total:          $7.50 │
│                       │
│ Duration: ~15 sec     │
│ Credits: 47 left      │
│                       │
│ ⚠ Over budget ($5)   │
│ [Adjust Settings]     │
│                       │
│ ─────────────────     │
│                       │
│ Quick Presets         │
│ • ⚡ Budget ($1.50)  │
│ • 💼 Studio ($8.50)  │
│ • 💎 Premium ($15)   │
│                       │
│ My Presets            │
│ • Product Demo        │
│ • Tutorial Intro      │
│ [+ New Preset]        │
│                       │
│ ─────────────────     │
│                       │
│ Tips                  │
│ 💡 Use "Sharpen" for  │
│ better prompts        │
│                       │
│ 💡 Front-facing photos│
│ work best for Heygen  │
└───────────────────────┘
```

---

### 3. Job Detail

**Route**: `/jobs/:id`  
**Purpose**: Deep dive into single job with timeline, logs, actions

```
┌─────────────────────────────────────────────────────────────────┐
│  ← Back to Jobs                                                  │
│                                                                  │
│  Product Announcement • Job #abc123                              │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  [Video Player - Full Width 16:9]                          │ │
│  │                                                             │ │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━ 0:15 / 0:15                      │ │
│  │  [⏮][⏪][▶][⏩][⏭] [🔊] [⚙ Quality] [⛶ Fullscreen]        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  Status: ● Completed  •  Engine: VEO3  •  Cost: $8.50          │
│  Created: Oct 12, 2025 10:00 AM  •  Duration: 15s  •  30fps    │
│                                                                  │
│  [⬇ Download MP4] [🔁 Rerun Same] [✏ Rerun & Edit] [📊 Compare]│
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  ▼ Timeline (Click to expand)                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ ✓ 10:00:00  Job created (user: john@example.com)          │ │
│  │ ✓ 10:00:02  Assets validated (script: 82 chars, image: OK)│ │
│  │ ✓ 10:00:05  VEO3 generation started (provider_id: veo_123)│ │
│  │ ✓ 10:02:30  VEO3 generation completed (webhook received)   │ │
│  │ ✓ 10:02:35  Post-FX: RIFE interpolation started            │ │
│  │ ✓ 10:03:10  Post-FX: RIFE completed (30fps → 60fps)        │ │
│  │ ✓ 10:03:15  Post-FX: Real-ESRGAN upscale started           │ │
│  │ ✓ 10:04:00  Post-FX: Upscale completed (720p → 1080p)      │ │
│  │ ✓ 10:04:05  Final video uploaded to S3                     │ │
│  │ ✓ 10:04:06  Job marked as completed                        │ │
│  │                                                             │ │
│  │ Total runtime: 4 minutes 6 seconds                         │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ▶ Technical Details                                            │
│  ▶ Full Logs (streaming)                                        │
│  ▶ Original Input                                               │
│  ▶ Cost Breakdown                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Expandable Sections**:

**Technical Details**:
```
Resolution: 1920×1080 (1080p)
Frame Rate: 60fps (interpolated from 30fps)
Codec: H.264, AAC audio
Bitrate: 8000 kbps
File Size: 15.2 MB
S3 URL: s3://bucket/jobs/abc123/final.mp4
Public URL: https://cdn.example.com/abc123.mp4 (expires in 24h)
```

**Full Logs** (with download button):
```
[2025-10-12 10:00:00] INFO  Job created: job_id=abc123
[2025-10-12 10:00:02] INFO  Validating assets...
[2025-10-12 10:00:02] INFO  Script validated: 82 characters, ~6 seconds
[2025-10-12 10:00:05] INFO  Calling VEO3 API: provider_job_id=veo_123
[2025-10-12 10:00:05] DEBUG VEO3 request payload: {...}
[2025-10-12 10:02:30] INFO  VEO3 webhook received: status=completed
[2025-10-12 10:02:30] INFO  Downloading VEO3 output from provider
...
```

**Original Input**:
```
Prompt: "We finally shipped the feature—and yes, it actually works!"
Reference Image: [thumbnail] portrait-123.jpg
Engine: VEO3
Settings:
  • FPS: 30
  • Aspect Ratio: 16:9
  • Post-FX: Interpolate (✓), Upscale (✓), Topaz (✗)
  • Duration Override: Auto
```

**Cost Breakdown**:
```
VEO3 Generation:        $4.20
  • Base generation:    $3.50
  • Premium voice:      $0.70

Post-FX:                $4.30
  • RIFE interpolation: $1.20
  • Real-ESRGAN upscale:$3.10

Total:                  $8.50
Credits Used:           85 credits
```

---

### 4. Preset Manager

**Route**: `/library/presets`  
**Purpose**: Save/load/share common configurations

```
┌─────────────────────────────────────────────────────────────────┐
│  Preset Library                              [+ Create New]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  My Presets (5)                     [Search presets...]          │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  📦 Product Demo                         [Edit] [Delete]   │ │
│  │  VEO3 • 30fps • 16:9 • Interpolate ✓ • Upscale ✓          │ │
│  │  Avg. cost: ~$8.50/video • Avg. duration: 15s              │ │
│  │  Used: 47 times • Last used: 2 days ago                    │ │
│  │  [Load in Composer]                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  💼 Tutorial Intro                       [Edit] [Delete]   │ │
│  │  Heygen • 24fps • 16:9 • No Post-FX                        │ │
│  │  Avg. cost: ~$2.80/video • Avg. duration: 10s              │ │
│  │  Voice: Rachel (Conversational) • Action: "Smile warmly"   │ │
│  │  Used: 23 times • Last used: 1 week ago                    │ │
│  │  [Load in Composer]                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  📱 Social Media (9:16)                  [Edit] [Delete]   │ │
│  │  VEO3 • 30fps • 9:16 • Interpolate ✓ • No Upscale          │ │
│  │  Avg. cost: ~$4.20/video • Avg. duration: 8s               │ │
│  │  Used: 12 times • Last used: yesterday                     │ │
│  │  [Load in Composer]                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  System Presets (always available)                              │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  ⚡ Fast Preview - $1.50                                   │ │
│  │  VEO3 • 24fps • 720p • No Post-FX                          │ │
│  │  Perfect for: Quick tests, draft reviews                   │ │
│  │  [Load in Composer]                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  💼 Studio Quality - $8.50                                 │ │
│  │  VEO3 • 30fps • 1080p • Interpolate ✓ • Upscale ✓         │ │
│  │  Perfect for: Final output, client delivery                │ │
│  │  [Load in Composer]                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │  💎 Premium (Topaz AI) - $15.00                            │ │
│  │  VEO3 • 60fps • 4K • Interpolate ✓ • Topaz Upscale ✓      │ │
│  │  Perfect for: Broadcast, cinema, premium clients           │ │
│  │  [Load in Composer]                                        │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Create/Edit Preset Modal**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Create Preset                                       [✕ Close]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Preset Name: [My Custom Preset___________________________]     │
│                                                                  │
│  Workflow: ●Prompt to Video  ○Image + Audio                     │
│                                                                  │
│  Engine: [VEO3 ▾]                                               │
│  FPS: [30 ▾]                                                    │
│  Aspect Ratio: [16:9 ▾]                                         │
│                                                                  │
│  Post-FX:                                                       │
│  [✓] Interpolate                                                │
│  [✓] Upscale                                                    │
│  [ ] Topaz Video AI                                             │
│                                                                  │
│  Default Duration: [Auto ▾]                                     │
│                                                                  │
│  Tags (optional): [tutorial, product, demo___]                  │
│                                                                  │
│  [Cancel] [Save Preset]                                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 5. Batch Import

**Route**: `/batch`  
**Purpose**: Upload CSV to queue multiple jobs

```
┌─────────────────────────────────────────────────────────────────┐
│  Batch Job Import                       [Download CSV Template] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Step 1: Upload CSV                                             │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                                                             │ │
│  │  Drag & drop CSV file or [click to browse]                 │ │
│  │                                                             │ │
│  │  Required columns: prompt, engine                           │ │
│  │  Optional: reference_image_url, fps, aspect, duration       │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  Step 2: Preview & Validate                                     │
│                                                                  │
│  ✓ File uploaded: prompts_batch_001.csv (52 rows)              │
│  ✓ Validation complete: 48 valid • 4 warnings • 0 errors       │
│                                                                  │
│  Preview (first 10 rows):                                       │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ # │ Prompt              │ Engine│ FPS│ Status              │ │
│  │───┼─────────────────────┼───────┼────┼─────────────────────│ │
│  │ 1 │ "Welcome message"   │ VEO3  │ 30 │ ✓ Ready             │ │
│  │ 2 │ "Product demo"      │ VEO3  │ 30 │ ✓ Ready             │ │
│  │ 3 │ "Tutorial intro"    │ Heygen│ 24 │ ✓ Ready             │ │
│  │ 4 │ "Very long prompt..."│ VEO3 │ 30 │ ⚠ Truncated (>200)  │ │
│  │ 5 │ "Social post"       │ VEO3  │ 60 │ ✓ Ready             │ │
│  │ 6 │ "Announcement"      │ VEO3  │ 30 │ ✓ Ready             │ │
│  │ 7 │ ""                  │ VEO3  │ 30 │ ⚠ Empty prompt      │ │
│  │ 8 │ "Feature highlight" │ Heygen│ 24 │ ✓ Ready             │ │
│  │ 9 │ "Q&A response"      │ VEO3  │ 30 │ ✓ Ready             │ │
│  │10 │ "Call to action"    │ VEO3  │ 30 │ ✓ Ready             │ │
│  │...│                     │       │    │                     │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                  │
│  [Download Validation Report]                                   │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  Step 3: Configure Batch Settings                               │
│                                                                  │
│  Apply Preset to All: [None ▾]  (or configure individually)    │
│                                                                  │
│  Default Post-FX:                                               │
│  [✓] Interpolate  [✓] Upscale  [ ] Topaz                       │
│                                                                  │
│  Priority: [●Normal  ○High (+20% cost)]                         │
│                                                                  │
│  ──────────────────────────────────────────────────────────────  │
│                                                                  │
│  Step 4: Review & Submit                                        │
│                                                                  │
│  Total Jobs: 48 valid                                           │
│  Estimated Cost: $425.50                                        │
│  Estimated Time: ~3.5 hours (parallel processing)               │
│                                                                  │
│  ⚠ This will use 4,255 credits from your account               │
│  Current Balance: 12,500 credits ($125.00)                      │
│  Balance After: 8,245 credits ($82.45)                          │
│                                                                  │
│  [← Back] [Cancel] [Queue All Jobs →]                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**CSV Template**:
```csv
prompt,engine,fps,aspect,duration,reference_image_url,interpolate,upscale
"Welcome to our platform",VEO3,30,16:9,auto,,true,true
"Product demo introduction",Heygen,24,16:9,12,https://example.com/face.jpg,false,false
"Tutorial lesson 1",VEO3,30,16:9,auto,,true,false
```

---

### 6. Settings

**Route**: `/settings`  
**Purpose**: API keys, billing, preferences

```
┌─────────────────────────────────────────────────────────────────┐
│  Settings                                                        │
│  ┌────────────┬────────────────────────────────────────────────┐│
│  │ General    │                                                 ││
│  │ API Keys   │ API Keys & Authentication                       ││
│  │ Webhooks   │                                                 ││
│  │ Billing    │ All keys are encrypted and stored server-side. ││
│  │ Preferences│ Never share your API keys.                      ││
│  │ Usage      │                                                 ││
│  │ Team       │ ┌─────────────────────────────────────────────┐││
│  │            │ │ VEO3 (Google AI Studio)                     │││
│  │            │ │ ●●●●●●●●●●●●●f4aB [Test] [Rotate] [Remove] │││
│  │            │ │ Status: ✓ Valid • Last tested: 2 hrs ago    │││
│  │            │ └─────────────────────────────────────────────┘││
│  │            │                                                 ││
│  │            │ ┌─────────────────────────────────────────────┐││
│  │            │ │ ElevenLabs TTS                              │││
│  │            │ │ ●●●●●●●●●●●●●8ca6 [Test] [Rotate] [Remove] │││
│  │            │ │ Status: ✓ Valid • Plan: Creator • 125K chars││
│  │            │ └─────────────────────────────────────────────┘││
│  │            │                                                 ││
│  │            │ ┌─────────────────────────────────────────────┐││
│  │            │ │ Heygen                                      │││
│  │            │ │ ●●●●●●●●●●●●●7b2c [Test] [Rotate] [Remove] │││
│  │            │ │ Status: ✓ Valid • Credits: 450 remaining    │││
│  │            │ └─────────────────────────────────────────────┘││
│  │            │                                                 ││
│  │            │ ┌─────────────────────────────────────────────┐││
│  │            │ │ OpenAI (Prompt Sharpener)                   │││
│  │            │ │ ●●●●●●●●●●●●●9d1e [Test] [Rotate] [Remove] │││
│  │            │ │ Status: ✓ Valid • Usage: $45.20 this month  │││
│  │            │ └─────────────────────────────────────────────┘││
│  │            │                                                 ││
│  │            │ ┌─────────────────────────────────────────────┐││
│  │            │ │ Anthropic Claude (Prompt Sharpener)         │││
│  │            │ │ ●●●●●●●●●●●●●5a3f [Test] [Rotate] [Remove] │││
│  │            │ │ Status: ✓ Valid • Usage: $12.80 this month  │││
│  │            │ └─────────────────────────────────────────────┘││
│  │            │                                                 ││
│  │            │ [+ Add New API Key]                             ││
│  └────────────┴────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Billing Tab**:
```
Credit Balance: $125.50 (1,255 credits)
[Add Credits] [View Invoice History] [Auto-Refill Settings]

Usage This Month:
┌────────────────────────────────────────────────────────────────┐
│ Oct 2025: $342.15 spent                                        │
│                                                                 │
│ By Provider:                                                    │
│ VEO3:        $195.40 (57%)  ████████████████░░░                │
│ Heygen:       $82.20 (24%)  ███████░░░░░░░░░░░                │
│ ElevenLabs:   $38.50 (11%)  ███░░░░░░░░░░░░░░░                │
│ Post-FX:      $26.05 (8%)   ██░░░░░░░░░░░░░░░░                │
│                                                                 │
│ By Feature:                                                     │
│ Video Gen:   $277.60 (81%)  █████████████████░░                │
│ TTS:          $38.50 (11%)  ███░░░░░░░░░░░░░░░                │
│ Post-FX:      $26.05 (8%)   ██░░░░░░░░░░░░░░░░                │
│                                                                 │
│ Jobs: 47 completed • 2 failed • $7.28 avg/job                  │
└────────────────────────────────────────────────────────────────┘

[Download Detailed Report CSV]
```

---

## Component Specifications

### Buttons

**Primary Button**:
```css
background: #6366F1 (indigo-600)
color: white
padding: 12px 24px
border-radius: 8px
font-weight: 600
hover: #4F46E5 (indigo-700)
active: #4338CA (indigo-800)
disabled: #CBD5E1 (slate-300), cursor: not-allowed
```

**Secondary Button**:
```css
background: transparent
border: 2px solid #6366F1
color: #6366F1
padding: 10px 22px (compensate for border)
border-radius: 8px
font-weight: 600
hover: background #EEF2FF (indigo-50)
```

**Ghost Button**:
```css
background: transparent
color: #475569 (slate-600)
padding: 12px 16px
border-radius: 8px
font-weight: 500
hover: background #F1F5F9 (slate-100)
```

### Form Inputs

**Text Input**:
```css
border: 1px solid #CBD5E1 (slate-300)
padding: 12px 16px
border-radius: 8px
font-size: 14px
focus: border #6366F1, ring 3px #C7D2FE (indigo-200 @ 40%)

With error:
border: 1px solid #EF4444 (red-500)
focus-ring: #FCA5A5 (red-300)
```

**Select Dropdown**:
```css
Similar to text input
Add chevron-down icon on right
padding-right: 40px (space for icon)
```

**Textarea**:
```css
Similar to text input
min-height: 120px
resize: vertical
```

**Checkbox**:
```css
width: 20px, height: 20px
border: 2px solid #CBD5E1
border-radius: 4px
checked: background #6366F1, white checkmark
```

### Cards

**Standard Card**:
```css
background: white
border: 1px solid #E2E8F0 (slate-200)
border-radius: 12px
padding: 24px
box-shadow: 0 1px 3px rgba(0,0,0,0.1)
hover: box-shadow: 0 4px 6px rgba(0,0,0,0.1)
transition: box-shadow 200ms ease
```

### Modals

**Standard Modal**:
```css
backdrop: rgba(0,0,0,0.5), backdrop-blur: 4px
container: white, border-radius: 16px
max-width: 640px (small), 960px (large)
padding: 32px
box-shadow: 0 20px 25px -5px rgba(0,0,0,0.2)
animation: fade-in 200ms, slide-up 200ms
```

### Progress Bars

**Linear Progress**:
```css
height: 8px
background: #E2E8F0 (slate-200)
border-radius: 9999px
fill: #6366F1 (indigo-600)
animation: indeterminate shimmer (when loading)
```

### Status Badges

```css
Completed: bg #D1FAE5 (green-100), text #065F46 (green-900)
Running:   bg #DBEAFE (blue-100), text #1E40AF (blue-800)
Pending:   bg #F1F5F9 (slate-100), text #475569 (slate-600)
Failed:    bg #FEE2E2 (red-100), text #991B1B (red-900)

padding: 4px 12px
border-radius: 9999px
font-size: 12px
font-weight: 600
```

---

## User Flows

### Flow 1: Create First Job (Prompt Mode)

```
1. Land on Dashboard (empty state)
   ↓
2. Click "Get Started" or [+ New Job]
   ↓
3. Composer loads (Prompt Mode default)
   ↓
4. User types prompt: "Person announcing news"
   • Cost updates in real-time: "$4.20"
   ↓
5. (Optional) Click [AI ✨] to sharpen
   • Modal opens with 3 variants
   • User reviews diffs
   • Click "Apply to Composer"
   ↓
6. (Optional) Upload reference image
   • Drag/drop or browse
   • Face detection runs
   ↓
7. Review cost estimate in context panel
   ↓
8. Click [Run Job →]
   • Toast: "Job queued! #abc123"
   • Redirect to Job Detail
   ↓
9. Watch progress in real-time
   • Progress bar updates via WebSocket
   • Timeline shows each step
   ↓
10. Job completes
    • Toast: "Job complete! [Download]"
    • Video player shows result
    ↓
11. Review, download, or rerun
```

### Flow 2: Batch Processing

```
1. Click "Batch" in nav
   ↓
2. Download CSV template
   ↓
3. Fill template with 50 prompts
   ↓
4. Upload CSV
   • Validation runs automatically
   • Shows 48 valid, 2 warnings
   ↓
5. Fix 2 warnings inline
   ↓
6. Apply "Studio Quality" preset to all
   ↓
7. Review cost: "$425"
   • Check credit balance
   ↓
8. Click [Queue All Jobs]
   • Progress modal shows queuing
   • "48 jobs queued successfully"
   ↓
9. Return to Dashboard
   • See all jobs in "Pending" state
   • Watch them process in real-time
```

### Flow 3: Compare & Iterate

```
1. Dashboard: Select 3 completed jobs
   • Shift+click to multi-select
   ↓
2. Click [Compare] button
   • Compare view loads
   • 3 video players side-by-side
   ↓
3. Play all with [Sync Playback]
   • Scrubber linked across all
   ↓
4. Identify best version (Job 2)
   ↓
5. Click job's [Rerun & Edit]
   • Composer loads with Job 2's settings
   • Prompt pre-filled
   ↓
6. Make small edit (change FPS 30→60)
   ↓
7. [Run Job] creates new variant
   ↓
8. Compare again: original vs new
```

---

## Implementation Notes

### Tech Stack

**Frontend**:
- React 18 + TypeScript
- Vite (build tool)
- TailwindCSS (styling)
- Radix UI (accessible components)
- Zustand (state management)
- React Query (API calls + caching)
- Socket.io-client (WebSocket real-time updates)
- Framer Motion (animations)
- React Player (video playback)

**State Management**:
```typescript
// Global store (Zustand)
interface AppStore {
  user: User | null
  jobs: Job[]
  presets: Preset[]
  costBudget: number
  
  // Actions
  fetchJobs: () => Promise<void>
  createJob: (params) => Promise<Job>
  updateJob: (id, updates) => void
}
```

**API Client** (generated from OpenAPI):
```typescript
// Auto-generated from docs/api/openapi.yaml
import { ApiClient } from '@/lib/api-client'

const api = new ApiClient({ baseURL: '/api/v1' })

// Type-safe calls
const job = await api.jobs.create({
  method: 'PROMPT_TO_LIPSYNC',
  script: 'Hello world',
  engine: 'veo3'
})
```

### Real-Time Updates

```typescript
// WebSocket connection
import io from 'socket.io-client'

const socket = io('/api/v1/ws')

socket.on('job_update', (data) => {
  // Update job in store
  updateJob(data.job_id, {
    status: data.status,
    progress: data.progress
  })
  
  // Show toast if completed
  if (data.status === 'DONE') {
    toast.success(`Job ${data.job_id} completed!`)
  }
})
```

### Performance Optimizations

1. **Code Splitting**: Lazy load routes
```typescript
const Composer = lazy(() => import('./pages/Composer'))
const JobDetail = lazy(() => import('./pages/JobDetail'))
```

2. **Virtual Scrolling**: Large job lists (react-window)

3. **Image Optimization**: 
   - WebP format
   - Lazy loading with Intersection Observer
   - Thumbnails (240p) for gallery, full-res on detail

4. **API Caching**: React Query with 5min stale time

5. **Optimistic Updates**: Update UI before server confirms

### Accessibility

```typescript
// Example: Accessible button
<button
  aria-label="Run job"
  onClick={handleRun}
  disabled={!isValid}
  aria-disabled={!isValid}
>
  Run Job →
</button>

// Keyboard shortcuts
useHotkeys('cmd+k', () => openCommandPalette())
useHotkeys('n', () => navigateToComposer())
useHotkeys('esc', () => closeModal())
```

### Testing Strategy

1. **Unit Tests**: Components with Vitest + RTL
2. **Integration Tests**: User flows with Playwright
3. **Visual Regression**: Chromatic (Storybook)
4. **Accessibility**: axe-core automated tests
5. **Performance**: Lighthouse CI on PR

---

## Next Steps

### Phase 1: MVP (2-3 weeks)
- [ ] Composer (Prompt Mode only)
- [ ] Job Gallery (grid view)
- [ ] Basic Job Detail
- [ ] Cost estimator
- [ ] Simple upload

### Phase 2: Core Features (2-3 weeks)
- [ ] Image+Audio Mode
- [ ] Prompt Sharpener
- [ ] Preset Library
- [ ] Compare Mode
- [ ] Real-time updates (WebSocket)

### Phase 3: Advanced (2-3 weeks)
- [ ] Batch import
- [ ] Advanced settings UI
- [ ] Settings / API keys
- [ ] Detailed timeline & logs
- [ ] Mobile responsive

### Phase 4: Polish (1-2 weeks)
- [ ] Animations & transitions
- [ ] Dark mode
- [ ] Accessibility audit
- [ ] Performance optimization
- [ ] Documentation

---

**Version**: 1.0.0  
**Last Updated**: October 12, 2025  
**Status**: ✅ Design Complete, Ready for Development  
**Next**: Begin Phase 1 implementation
