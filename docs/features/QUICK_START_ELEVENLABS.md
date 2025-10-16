# Quick Start Guide - ElevenLabs Features

## 🚀 Starting the Application

Your `run.sh` script has been updated to handle starting the backend without requiring a database.

### Start Everything (Recommended)

```bash
./run.sh
```

This starts:
- ✅ Backend API (http://localhost:8000) - **Works without database**
- ✅ Frontend UI (http://localhost:5173 or 3000)
- ⚠️ Worker (requires Redis - will skip if not available)

### Start Backend Only

```bash
./run.sh api
```

This starts just the FastAPI backend on port 8000.

### Start Frontend Only

```bash
./run.sh frontend
```

This starts just the React frontend.

## 🎤 Accessing ElevenLabs Features

Once the app is running:

1. **Open your browser**: http://localhost:5173 (or http://localhost:3000)
2. **Click "Voices"** in the left sidebar (microphone icon 🎤)
3. **You'll see**:
   - Voice library with Rachel, Drew, Clyde voices
   - Subscription info (mock data shows Free tier)
   - Search/filter functionality
   - "Clone Voice" button
   - Use Voice buttons

## 📡 API Endpoints Available

All these work right now (using mock data by default):

```bash
# List all voices
curl http://localhost:8000/api/v1/voices/

# Get available models
curl http://localhost:8000/api/v1/voices/models/available

# Get available formats
curl http://localhost:8000/api/v1/voices/formats/available

# Get subscription info
curl http://localhost:8000/api/v1/voices/subscription/info

# Synthesize speech
curl -X POST http://localhost:8000/api/v1/voices/synthesize \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello world!",
    "voice_id": "mock-voice-rachel-11111",
    "model_id": "eleven_turbo_v2"
  }'
```

## 🎭 Mock Mode vs Real Mode

### Currently Using: Mock Mode ✅

**Mock mode** is enabled by default so you can:
- ✅ Test all features without API keys
- ✅ See the UI working
- ✅ No API costs
- ✅ Works without internet

Your backend is currently returning mock data:
- 3 mock voices (Rachel, Drew, Clyde)
- Mock audio generation
- Mock subscription info

### To Use Real ElevenLabs API:

1. Get your API key from https://elevenlabs.io
2. Edit `.env` file:
   ```bash
   ELEVENLABS_API_KEY=your-actual-key-here
   ELEVENLABS_MOCK_MODE=false
   ```
3. Restart backend: `./run.sh api`

## 🗄️ About the Database

The backend **does not require** a database to start. Features that work without DB:

- ✅ ElevenLabs voice features (all of them!)
- ✅ Voice library browsing
- ✅ Voice cloning
- ✅ Speech synthesis
- ✅ Model/format listings

Features that need database (for later when you set up RDS):
- Job tracking
- Job history
- Job status updates
- Job metadata

## 📝 Current Status

✅ **Backend Running**: Port 8000  
✅ **Frontend Running**: Port 5173/3000  
✅ **ElevenLabs API**: All 8 endpoints working  
✅ **Voice Library UI**: Fully functional  
✅ **Mock Mode**: Enabled (no API key needed)  
⚠️ **Database**: Optional (not needed yet)  
⚠️ **Redis**: Optional (only for job queue)

## 🎯 What You Can Do Right Now

1. **Browse Voices** - See Rachel, Drew, Clyde in the UI
2. **Search Voices** - Filter by name
3. **See Mock Subscription** - Visual usage bars
4. **Test Clone UI** - Upload form (mock mode simulates cloning)
5. **View Models** - See all 5 AI models available
6. **View Formats** - See all 7 audio formats

## 🔧 Troubleshooting

### Backend won't start?
```bash
# Kill any existing process on port 8000
lsof -ti:8000 | xargs kill -9

# Start fresh
./run.sh api
```

### Frontend not showing Voices page?
1. Check backend is running: `curl http://localhost:8000/health`
2. Clear browser cache
3. Hard refresh: Ctrl+Shift+R (Cmd+Shift+R on Mac)

### Want to see backend logs?
```bash
tail -f /tmp/api.log
```

## 📚 Documentation

- **API Docs**: `docs/api/elevenlabs_voice_api.md`
- **Feature Guide**: `docs/features/ELEVENLABS_VOICE_FEATURES.md`
- **Implementation**: `ELEVENLABS_ENHANCEMENT_SUMMARY.md`

## 🎉 You're All Set!

Your ElevenLabs features are **live and working**!

Just run:
```bash
./run.sh
```

Then visit: **http://localhost:5173** and click **"Voices"** 🎤
