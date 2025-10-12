
# AI Lip‑Sync Companion App (Option 1 & Option 2)

> S- 🔌 **Two turnkey methods:** m**Frontend:** React (Vite) — Two "wizards," one per option, plus a Jobs/Gallery view.  
**Backend:** FastAPI — REST + background workers (RQ/Celery) + provider adapters.  
**Storage:** S3‑compatible (e.g., AWS S3, MinIO) for assets; Postgres for metadata.  
**Queue:** Redis.  
**AI Providers:** VEO 3, Vertex AI Imagen, ElevenLabs, Heygen, Topaz Video AI  
**Post‑FX:** RIFE (interpolate), Real‑ESRGAN (upscale), Topaz Video AI (premium).

```mermaid
flowchart LR
A[User] --> B[React ## Troubleshooting

### API & Authenticatio**Q: Can I generate the portrait instead of uploading?**  
A: Yes—use Vertex AI Imagen for portrait generation. The app supports both uploaded images and AI-generated ones.

**Q: Do I need Topaz Video AI?**  
A: No—RIFE + Real‑ESRGAN are the free defaults. Topaz is a premium option for professional-grade enhancement.

**Q: What's the difference between VEO 3 and Vertex AI?**  
A: VEO 3 (Google AI Studio) is for direct text-to-video. Vertex AI provides Imagen for image generation and other ML services.

**Q: How do I test if my API keys are working?**  
A: Run `python test_api_keys.py` - it validates all providers and shows detailed connection status.

**Q: What about 9:16 for Shorts/Reels/TikTok?**  
A: Select aspect ratio in the UI; app letterboxes/pillarboxes and normalizes fps for platform targets.

**Q: Will Option 1 ever keep the same voice?**  
A: Not reliably. Use Option 2 with a saved ElevenLabs `voice_id` for consistency across videos.

**Q: Can I use multiple AI providers together?**  
A: Yes! The app supports mixing providers - e.g., Vertex AI for images + ElevenLabs for voice + Heygen for lip-sync.**API keys not working:** Run `python test_api_keys.py` to validate all keys and check authentication
- **403 Forbidden errors:** Valid key but insufficient plan (upgrade to higher tier)
- **401 Unauthorized:** Invalid API key format or expired key
- **Heygen authentication fails:** Ensure using `X-Api-Key` header format (not Bearer token)
- **Provider timeouts:** Check network connectivity and provider service status

### Video Quality Issues  
- **No/Bad lip motion:** ensure front‑facing image; remove heavy occlusions; reduce action prompt complexity
- **Frame wobble:** enable interpolation; normalize to 24 or 30 fps
- **Mushy detail after upscale:** perform interpolation **before** upscaling; try different models
- **Voice inconsistency (Option 1):** that's expected; switch to Option 2 and reuse `voice_id`

### Content & Safety
- **Provider 422 "unsafe":** try different image; remove logos/celebrity likeness; add consent note
- **Topaz 400 errors:** Check payload format - ensure `audioTransfer` and `dynamicCompressionLevel` are set

### Performance & Processing
- **Slow processing:** Check if GPU acceleration is available for RIFE/Real-ESRGAN
- **Out of memory:** Reduce video resolution or enable CPU fallback modes
- **Queue backlog:** Monitor Redis queue status and scale workers as needed->|create job| C[FastAPI API]
C -->|validate keys| T[API Testing]
C -->|enqueue| D[Background Worker]
D -->|Option 1| E[VEO 3 / Vertex AI]
D -->|Option 2| F[ElevenLabs TTS] --> G[Heygen Photo→Video]
E --> H[(S3 Storage)]
G --> H
D -->|Post-FX| I[RIFE/Topaz/Real-ESRGAN] --> H
C -->|webhooks| J[Heygen/Provider Callbacks]
C -->|status| B
```l's Option 1 & Option 2
- 🧩 **Provider adapters:** `veo_adapter`, `heygen_adapter`, `tts_elevenlabs`, `postfx`
- 🎯 **Mult### Provider Setup Notes

- **VEO 3 (Google AI Studio)**: Get API key from [Google AI Studio](https://aistudio.google.com/). Enable Generative Language API. Key format: `AIza...`
- **Vertex AI**: Get API key from Google Cloud Console. Enable Vertex AI API and Imagen. Key format: `AQ....`
- **Heygen**: Get API key from account settings → Subscriptions → HeyGen API. Uses `X-Api-Key` authentication.
- **ElevenLabs**: Get API key from [ElevenLabs](https://elevenlabs.io/). Create/select a **voice** and capture the `voice_id` for consistency.
- **Topaz Video AI**: Get API key from [Topaz Labs](https://topazlabs.com/). UUID format: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

> **API Key Testing**: Run `python test_api_keys.py` to validate all your API keys before deployment.

> **Topaz Video AI**: Optional premium enhancement. If you have a license, set `POSTFX_USE_TOPAZ=true` and provide your API key. Otherwise, the app uses OSS defaults (RIFE + Real‑ESRGAN).tegration:** VEO 3, Vertex AI Imagen, ElevenLabs TTS, Heygen, Topaz Video AI
- 🧠 **Consistent voices (Option 2):** store & reuse **ElevenLabs voice_id**
- 🎛️ **Action prompts:** atomic motion cues for Heygen (blink/nod/tilt)
- 🧽 **Polish pipeline:** **Interpolate → Upscale** (RIFE + Real‑ESRGAN by default; Topaz Video AI optional)
- 🔧 **API key testing:** Built-in validation for all provider APIshe exact two workflows from the tutorial as a small, production‑sound web app.  
> **Option 1:** *Prompt → Lip‑Sync* (Veo 3 → optional Topaz/OSS polish)  
> **Option 2:** *Audio + Image → Lip‑Sync* (ElevenLabs → Heygen → optional polish)

---

## Table of Contents

- [What This Is](#what-this-is)
- [Feature Highlights](#feature-highlights)
- [Architecture](#architecture)
- [Workflows](#workflows)
  - [Option 1 — Prompt → Lip‑Sync (Veo 3)](#option-1--prompt--lip-sync-veo-3)
  - [Option 2 — Audio + Image → Lip‑Sync (ElevenLabs + Heygen)](#option-2--audio--image--lip-sync-elevenlabs--heygen)
- [Quality Polish (Post‑FX)](#quality-polish-post-fx)
- [Security, Consent & Compliance](#security-consent--compliance)
- [Local Quickstart](#local-quickstart)
- [Configuration](#configuration)
  - [.env Template](#env-template)
  - [Provider Setup Notes](#provider-setup-notes)
- [Running With Docker](#running-with-docker)
- [Database & Migrations](#database--migrations)
- [API Specification](#api-specification)
  - [Jobs](#jobs)
  - [Option 1 Endpoints](#option-1-endpoints)
  - [Option 2 Endpoints](#option-2-endpoints)
  - [Webhooks](#webhooks)
  - [Error Codes](#error-codes)
- [Data Model](#data-model)
- [Prompt Kits & Presets](#prompt-kits--presets)
- [Cost Controls](#cost-controls)
- [Observability](#observability)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [FAQ](#faq)
- [License](#license)

---

## What This Is

A minimal, batteries‑included web app (React + FastAPI) that reproduces the **two practical AI lip‑sync workflows** from the tutorial:

- **Option 1 — Prompt → Lip‑Sync** using **Veo 3** text‑to‑video, then optional post‑processing.
- **Option 2 — Audio + Image → Lip‑Sync** using **ElevenLabs** for consistent voice generation and **Heygen** “Photo → Video” for facial animation, then optional post‑processing.

Both options share the same queue, storage, and post‑FX pipeline. Adapters keep vendors swappable.

---

## Feature Highlights

- 🔌 **Two turnkey methods:** mirrors the tutorial’s Option 1 & Option 2
- 🧩 **Provider adapters:** `veo_adapter`, `heygen_adapter`, `tts_elevenlabs`, `postfx`
- 🧠 **Consistent voices (Option 2):** store & reuse **ElevenLabs voice_id**
- 🎛️ **Action prompts:** atomic motion cues for Heygen (blink/nod/tilt)
- 🧽 **Polish pipeline:** **Interpolate → Upscale** (RIFE + Real‑ESRGAN by default; Topaz optional)
- 🗂️ **Job gallery:** compare takes, re‑run with different presets
- 🧾 **Lineage:** render.json per take (inputs, prompts, settings, hashes)
- 💵 **Cost controls:** budget vs studio presets, estimated credit/$ readout
- 🛡️ **Safety/consent:** voice‑likeness disclaimers, basic content checks
- 📈 **Observability:** structured logs, metrics hooks, job timeline

---

## Architecture

**Frontend:** React (Vite) — Two “wizards,” one per option, plus a Jobs/Gallery view.  
**Backend:** FastAPI — REST + background workers (RQ/Celery) + provider adapters.  
**Storage:** S3‑compatible (e.g., AWS S3, MinIO) for assets; Postgres for metadata.  
**Queue:** Redis.  
**Post‑FX:** RIFE (interpolate), Real‑ESRGAN (upscale). Topaz is a premium optional.

```mermaid
flowchart LR
A[User] --> B[React UI]
B -->|create job| C[FastAPI]
C -->|enqueue| D[Worker]
D -->|Option 1| E[Veo 3 API]
D -->|Option 2| F[ElevenLabs TTS] --> G[Heygen Photo→Video]
E --> H[(S3)]
G --> H
D -->|Post-FX| I[RIFE/Topaz/Real-ESRGAN] --> H
C -->|status| B
```

---

## Workflows

### Option 1 — Prompt → Lip‑Sync (Veo 3)

**Input:** Script (what the character says), optional reference portrait.  
**Engine:** Veo 3 (Text→Video).  
**Post‑FX:** Optional interpolation (if needed) → optional upscale.

**Why use:** Speed. One text line → a talking head. Ideal for mockups, social bits, experiments.  
**Caveat:** Voice is not guaranteed to be consistent across takes.

**Recommended shot scaffold (prepend to prompt):**  
> “Tight medium close‑up, subject centered, soft key light, shallow depth of field, natural micro‑head‑motion, authentic lip sync. The subject clearly speaks the following line:”

**Duration heuristic:** `seconds ≈ len(script)/12` (cap at 12–15s by default; UI override available).

---

### Option 2 — Audio + Image → Lip‑Sync (ElevenLabs + Heygen)

**Input:** Image (front‑facing face) + Audio (upload or generate with ElevenLabs).  
**Engines:** ElevenLabs (TTS; stored `voice_id`) → Heygen (Photo→Video; **Action Prompt**).  
**Post‑FX:** Interpolation ON by default (Heygen can wobble), optional upscale.

**Why use:** Studio‑safe *voice consistency* and stronger lip realism across episodes.  
**Pro tip:** Keep **action prompts atomic** (single verbs per clause) for better adherence.

**Action prompt examples:**  
- “Occasional blink every 2–3 seconds; minimal head motion.”  
- “Steady gaze to camera; tiny nod on final phrase.”  
- “Subtle head tilt right; small smile on last words.”

**Face checks:** App warns on multiple faces, occlusions, extreme angles; selects largest face box by default.

---

## Quality Polish (Post‑FX)

**Order matters →** `Interpolate → Upscale`  
- **Interpolation:** RIFE (default). Smooths micro‑stutters and frame‑skip artifacts.  
- **Upscale:** Real‑ESRGAN (default) or **Topaz Video AI** (optional “Pro” toggle).

**FPS normalization:** Force 24 or 30 fps.  
**Aspect ratios:** 16:9, 9:16, 1:1 presets with auto letterboxing/pillarboxing when needed.  
**Audio prep:** trim leading silence; normalize loudness; pad 250–500 ms tail for natural closures.

---

## Security, Consent & Compliance

- **Voice consent:** If cloning a real person, confirm you have explicit permission.  
- **Likeness use:** Avoid misleading usage; comply with platform & provider TOS.  
- **Content checks:** Basic celebrity/logo detection as a pre‑flight warning.  
- **Secrets:** Provider keys never sent to client; keep in server env/secret manager.  
- **Storage:** Signed URLs; set reasonable TTLs; do not store raw provider tokens.  

---

## Local Quickstart

Requirements: Python 3.10+, Node 18+, Postgres 14+, Redis 6+, FFmpeg.  
(Optional) GPU for RIFE/ESRGAN; otherwise CPU paths are used (slower).

```bash
# 1) Clone & env
git clone <your-repo-url> lipsync-app && cd lipsync-app
cp .env.example .env  # then fill in API keys

# 2) Validate API keys
python test_api_keys.py  # Ensure all providers are working

# 3) Backend setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head  # or run provided SQL
uvicorn backend.main:app --reload

# 4) Worker process
python backend/worker.py

# 5) Frontend (if applicable)
cd frontend && npm i && npm run dev
```

### Quick Setup Checklist
- [ ] Get API keys from all providers (VEO 3, Vertex AI, ElevenLabs, Heygen, Topaz)
- [ ] Add keys to `.env` file
- [ ] Run `python test_api_keys.py` to validate
- [ ] Set up Postgres database and Redis
- [ ] Configure S3-compatible storage (AWS S3 or MinIO)
- [ ] Start backend API server
- [ ] Start background worker process
- [ ] Test with a simple job creation

---

## Configuration

### .env Template

Create `.env` in repo root:

```dotenv
# Backend
APP_ENV=dev
PORT=8000
LOG_LEVEL=INFO

# Database & Queue
DATABASE_URL=postgresql+psycopg2://user:pass@localhost:5432/lipsync
REDIS_URL=redis://localhost:6379/0

# Storage
S3_ENDPOINT= # leave empty for AWS
S3_BUCKET=lipsync-assets
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=changeme
AWS_SECRET_ACCESS_KEY=changeme

# Providers
VEO3_API_KEY=changeme                    # Google AI Studio API key for Veo 3
VERTEX_API_KEY=changeme                  # Google Cloud Vertex AI key for Imagen
ELEVENLABS_API_KEY=changeme              # ElevenLabs TTS API key
HEYGEN_API_KEY=changeme                  # Heygen talking photo API key
TOPAZ_API_KEY=changeme                   # Topaz Video AI API key (optional)

# Post-FX
POSTFX_USE_TOPAZ=false
TOPAZ_CLI_PATH= # path if available
RIFE_MODEL=rife-v4
REAL_ESRGAN_MODEL=realesr-animevideov3  # or general-x4v3

# Webhooks
WEBHOOK_SECRET_HEYGEN=changeme
WEBHOOK_SECRET_VEO=changeme
PUBLIC_BASE_URL=http://localhost:8000

# Video defaults
DEFAULT_FPS=24
DEFAULT_MAX_DURATION=12
DEFAULT_AR=16:9
```

### Provider Setup Notes

- **Veo 3**: Enable Text→Video; ensure your key has appropriate quota.  
- **Heygen**: Use “Photo to Video” endpoint; enable webhooks if available.  
- **ElevenLabs**: Create/select a **voice** and capture the `voice_id` for consistency.

> Topaz Video AI: If you have a license and headless capability, set `POSTFX_USE_TOPAZ=true` and point `TOPAZ_CLI_PATH`. Otherwise, the app uses OSS defaults (RIFE + Real‑ESRGAN).

---

## Running With Docker

`docker-compose.yml` (skeleton):

```yaml
version: "3.9"
services:
  api:
    build: ./backend
    env_file: .env
    ports: ["8000:8000"]
    depends_on: [db, redis]
  worker:
    build: ./backend
    command: python worker.py
    env_file: .env
    depends_on: [api, db, redis]
  web:
    build: ./frontend
    ports: ["5173:5173"]
    depends_on: [api]
  db:
    image: postgres:14
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: lipsync
    ports: ["5432:5432"]
  redis:
    image: redis:6
    ports: ["6379:6379"]
```

---

## Database & Migrations

**Alembic** (recommended) or raw SQL. Minimal schema:

```sql
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  method TEXT CHECK (method IN ('PROMPT_TO_LIPSYNC','AUDIO_DRIVEN')) NOT NULL,
  status TEXT CHECK (status IN ('QUEUED','RUNNING','POST','DONE','ERROR')) NOT NULL,
  engine TEXT,
  input_text TEXT,
  audio_asset_id UUID,
  image_asset_id UUID,
  output_url TEXT,
  post_upsample BOOLEAN DEFAULT false,
  post_interpolate BOOLEAN DEFAULT true,
  cost_estimate_cents INT DEFAULT 0,
  meta JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE assets (
  id UUID PRIMARY KEY,
  kind TEXT CHECK (kind IN ('IMAGE','AUDIO','VIDEO')) NOT NULL,
  url TEXT NOT NULL,
  meta JSONB DEFAULT '{}'::jsonb,
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## API Specification

Base URL: `http://localhost:8000/api/v1`

### Jobs API

**GET `/jobs/{job_id}`** - Get job details by ID
```json
{
  "job_id": "uuid",
  "method": "PROMPT_TO_LIPSYNC",
  "status": "RUNNING",
  "engine": "veo3",
  "output_url": null,
  "created_at": "2025-10-12T13:02:00Z",
  "updated_at": "2025-10-12T13:02:30Z",
  "metadata": {}
}
```

**GET `/jobs`** - List jobs with filtering
- **Query Parameters**: `status`, `method`, `limit` (1-100, default 25), `offset` (default 0)
- **Returns**: Array of job details

### Uploads API

**POST `/uploads/presign`** - Create presigned upload URLs
```json
{
  "kind": "IMAGE",
  "filename": "portrait.jpg",
  "content_type": "image/jpeg"
}
```
**Response:**
```json
{
  "upload_url": "https://s3.../presigned-url",
  "asset_id": "uuid",
  "asset_url": "https://s3.../final-url"
}
```

**File Limits:**
- **IMAGE**: JPEG/PNG, ≤ 10MB
- **AUDIO**: MP3/WAV, ≤ 20MB  
- **VIDEO**: MP4, ≤ 100MB

---

### Option 1 - Prompt to Lip-Sync

**POST `/lipsync/prompt`** - Create prompt-based lip-sync job
```json
{
  "script": "We finally shipped the feature—and yes, it actually works.",
  "reference_image_url": "https://s3/.../face.jpg",
  "engine": "veo3",
  "priority": "standard",
  "post_processing": {
    "upscale": true, 
    "interpolate": true
  },
  "video_settings": {
    "fps": 24, 
    "aspect_ratio": "16:9", 
    "max_duration": 12
  }
}
```
**201** → `{ "job_id": "uuid" }`

**Validation:**
- Script: 8-500 characters
- Supported engines: `veo3`, `vertex-imagen`

---

### Option 2 - Audio-Driven Lip-Sync

**POST `/lipsync/audio`** - Create audio-driven lip-sync job
```json
{
  "image_url": "https://s3/.../face.jpg",
  "audio_url": "https://s3.../audio.mp3",
  "tts": {
    "provider": "elevenlabs",
    "voice_id": "your_voice_id",
    "text": "This is a test of the emergency broadcast system.",
    "stability": 0.5,
    "similarity_boost": 0.8
  },
  "action_prompt": "Occasional blink every 2–3 seconds; tiny nod at the end.",
  "priority": "standard",
  "post_processing": {
    "upscale": false, 
    "interpolate": true
  },
  "video_settings": {
    "fps": 24, 
    "aspect_ratio": "16:9"
  }
}
```
**201** → `{ "job_id": "uuid" }`

**Validation:**
- Either `audio_url` OR `tts` must be provided
- TTS text: ≥ 3 characters  
- Action prompt: ≤ 120 characters

---

### Webhooks

- **POST `/webhooks/heygen`**
  - Header: `X-Heygen-Signature`
  - Body: job_id, status, output_url
  - Verify signature with `WEBHOOK_SECRET_HEYGEN`

- **POST `/webhooks/veo`** (if supported)
  - Header: `X-Veo-Signature`
  - Body: job_id, status, output_url

**Response:** `200 OK` after idempotent update. Retries tolerated.

---

### API Key Testing & Validation

The application includes comprehensive API key testing functionality:

**Run API Key Tests:**
```bash
python test_api_keys.py
```

**Supported Providers:**
- ✅ **VEO3 (Google AI Studio)**: Text-to-video generation
- ✅ **Vertex AI**: Imagen image generation and processing  
- ✅ **ElevenLabs**: Text-to-speech with voice cloning
- ✅ **Heygen**: Photo-to-video talking head generation
- ✅ **Topaz Video AI**: Professional video enhancement and interpolation

**Test Output Example:**
```
============================================================
                     API Key Validation                     
============================================================

VEO3: VALID
Vertex AI: VALID  
ElevenLabs: VALID
Heygen: VALID
Topaz: VALID

All API keys appear valid! You can proceed with your application.
```

The testing script validates:
- API key format and structure
- Authentication and connectivity
- Basic endpoint functionality
- Plan/quota limitations
- Provider-specific requirements

---

### Error Codes

- `400`: invalid input (missing script/audio/image; bad URL; bad aspect).  
- `401`: provider auth failed; missing/invalid API key.  
- `404`: job not found.  
- `409`: job already completed or in incompatible state.  
- `422`: provider rejected (face not detected; unsafe content; length too long).  
- `500`: internal error (adapter exception; post‑FX failed).

---

## Data Model

**jobs.meta** suggestions:
```json
{
  "provider_job_ids": {"veo": "abc", "heygen": "xyz"},
  "prompts": {
    "shot_scaffold": "Tight medium close-up...",
    "action_prompt": "Occasional blink..."
  },
  "video": {"fps": 24, "aspect": "16:9", "duration_s": 9.8},
  "postfx": {"interpolate": true, "upscale": false, "models": {"rife":"v4","esrgan":"x4v3"}}
}
```

**assets.meta** suggestions:
```json
{"hash":"sha256:...","width":1080,"height":1920,"duration_s":10.0,"codec":"h264"}
```

---

## Prompt Kits & Presets

### Veo 3 (Option 1) — *prepend to script*
> “Tight medium close‑up, subject centered, soft frontal key light, shallow depth of field, natural micro‑head‑motion, authentic lip sync. The subject clearly speaks:”

**Negative cues:** “no exaggerated mouth shapes; no teeth distortion; avoid rapid head bobbing.”

### Heygen Action Prompts (Option 2)
- “Occasional blink every 2–3 s; minimal head motion.”
- “Steady gaze into camera; tiny nod after key phrase.”
- “Slight head tilt right; small smile on final words.”

### ElevenLabs Voice Briefs
- “Warm baritone, broadcast clarity, neutral American accent; avoid vocal fry.”  
**Params:** `stability=0.6–0.7`, `similarity_boost=0.7–0.8`, pace `0.95–1.0`

---

## Cost Controls

- **Budget preset:** Interpolate OFF; Upscale OFF; 24 fps; 720p.  
- **Studio preset:** Interpolate ON; Upscale ON; 24 or 30 fps; 1080p/4K.  
- **Estimate line itemization:** generation vs post‑FX per minute.  
- **Kill switches:** max duration caps; daily credit limits.

---

## Observability

- **Logs:** per step with timestamps; include provider request IDs.  
- **Metrics:** jobs_created, jobs_failed, provider_latency_ms, postfx_runtime_s.  
- **Tracing (optional):** OpenTelemetry spans around adapter calls & post‑FX.

---

## Troubleshooting

- **No/Bad lip motion:** ensure front‑facing image; remove heavy occlusions; reduce action prompt complexity.  
- **Frame wobble:** enable interpolation; normalize to 24 or 30 fps.  
- **Mushy detail after upscale:** perform interpolation **before** upscaling; try a different ESRGAN model.  
- **Voice inconsistency (Option 1):** that’s expected; switch to Option 2 and reuse `voice_id`.  
- **Provider 422 “unsafe”**: try different image; remove logos/celebrity likeness; add consent note.

---

## Roadmap

- Batch scripting (CSV of lines → Option 1 auto‑renders)  
- A/B takes (action‑prompt variants side‑by‑side)  
- Basic lip‑sync drift heuristic (flag >120 ms)  
- Additional engines (Runway, Kling) via adapters  
- In‑app consent capture for voice/likeness

---

## FAQ

**Q: Can I generate the portrait instead of uploading?**  
A: Yes—wire a “Generate Image” button (e.g., Stability/SDXL/Leonardo). Store the seed for reproducibility.

**Q: Do I need Topaz?**  
A: No—RIFE + Real‑ESRGAN are the defaults. Topaz is a Pro toggle if licensed.

**Q: What about 9:16 for Shorts/Reels/TikTok?**  
A: Select AR in the UI; app letterboxes/pillarboxes and normalizes fps for platform targets.

**Q: Will Option 1 ever keep the same voice?**  
A: Not reliably. Use Option 2 with a saved ElevenLabs `voice_id` for consistency across videos.

---

## License

MIT (or your preferred license).

---

### Developer Prompts (paste into your assistant/tooling)

- “Generate a FastAPI `heygen_adapter.py` with auth, submit, poll, and robust error handling.”  
- “Implement Redis RQ workers and idempotent post‑FX chaining (Interpolate → Upscale).”  
- “Create a minimal React wizard for Option 2 with S3 presigned uploads and field validation.”  
- “Add OpenTelemetry spans around provider calls and write Prometheus metrics for runtimes.”
