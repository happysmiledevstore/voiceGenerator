# Voice Generator — Web Edition

Record, transform, and synthesize voice in the browser.  
**Stack:** FastAPI (Python) + Next.js (TypeScript)

The original PyQt desktop UI has been replaced by a modern web frontend. All audio DSP, TTS, and voice-profile logic lives in the shared `core/` package and is exposed via REST API.

## Features

- **Voice Recorder** — browser mic recording, file upload, live waveform, effects, presets, voice profile analysis
- **Text to Speech** — gTTS (online) or pyttsx3 (offline), 12 languages, voice profile matching
- **Effects** — pitch, speed, robot / echo / reverb / alien + one-click presets

## Project Structure

```
voiceGenerator/
├── backend/           # FastAPI REST API
│   └── app/
│       ├── main.py
│       ├── routers/   # audio, tts, profiles
│       └── storage.py
├── frontend/          # Next.js 15 web UI
│   ├── app/
│   │   ├── recorder/
│   │   └── tts/
│   └── components/
├── core/              # Shared Python audio engine (unchanged)
├── data/              # Uploaded/processed audio (created at runtime)
└── ui/                # Legacy desktop UI (optional, not used by web app)
```

## Quick Start

### 1. Backend (FastAPI)

```bash
# From project root
python -m venv .venv

# Windows
.venv\Scripts\activate

pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 2. Frontend (Next.js)

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

## API Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/audio/upload` | Upload audio file |
| POST | `/api/audio/transform` | Apply pitch/speed/effects |
| POST | `/api/audio/apply-preset` | Apply named preset |
| GET | `/api/audio/{id}/file` | Download WAV |
| POST | `/api/tts/generate` | Generate speech from text |
| POST | `/api/profiles/save` | Analyse and/or save profile in app |
| GET | `/api/profiles` | List saved profiles |
| GET | `/api/profiles/{id}` | Get saved profile |
| GET | `/api/profiles/{id}/export` | Export profile as JSON |
| DELETE | `/api/profiles/{id}` | Delete saved profile |
| POST | `/api/profiles/analyze` | Analyse voice (preview, no save) |
| POST | `/api/profiles/apply` | Apply profile to audio |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend → API base URL |
| `VG_CORS_ORIGINS` | `localhost:3000` | Comma-separated CORS origins (optional) |

## Notes

- **MP3 export** is not exposed in the web UI yet; downloads are WAV. FFmpeg + pydub can be added server-side.
- **Offline TTS (pyttsx3)** works when the backend runs on Windows with SAPI voices installed.
- **Voice profiles** are stored server-side in `data/profiles/`. Import/export JSON is still supported from the UI.

## Legacy Desktop App

The PyQt desktop app can still be run with `python main.py` if PyQt5 is installed (`pip install -r requirements.txt`).

## License

MIT (add your license here)
