# VOIDORA — Automated AI Video Production Pipeline

> **End-to-end AI video automation system generating Shorts and documentary videos with n8n orchestration and automated YouTube publishing.**

An automated pipeline for discovering topics, generating scripts, producing voiceovers, assembling visual assets, rendering cinematic videos (Shorts and Long-form), and publishing directly to YouTube.

---

## 🚀 Architecture Overview

The system consists of three core components running in harmony:

1. **Orchestrator (`n8n`)**: Manages the multi-stage workflows, heuristic topic scoring, scheduling, and error alerting.
2. **Database (`PostgreSQL 16`)**: Dedicated schema (`voidora_prod`) for topics, production jobs, scenes, asset caching, and publishing logs.
3. **Processing Worker (`FastAPI / Python 3.11`)**: High-performance video rendering engine utilizing MoviePy, ImageMagick, Whisper/TTS, and AI generative video integrations (Fal.ai, Runway, Kling, Luma).

```
[ Research / RSS / APIs ]
           │
           ▼
     [ n8n Workflows ] ───► [ PostgreSQL (voidora_prod) ]
           │                               │
           ▼                               │
   [ Worker API / Jobs ] ◄─────────────────┘
           │
   ┌───────┴───────────────────────────────┐
   │ • Script Generation (Gemini)          │
   │ • Voiceover Narration (Edge-TTS)      │
   │ • Subtitle Generation & Placement     │
   │ • Generative & Stock Media Engine     │
   │ • Video Composition & QC              │
   └───────┬───────────────────────────────┘
           │
           ▼
[ Rendered Video (`media/06_rendered_output`) ]
           │
           ▼
[ YouTube Publishing Engine ]
```

---

## 📁 Repository Structure

```
.
├── docker-compose.yml           # PostgreSQL and n8n orchestration
├── .env.example                 # Environment variables template
├── media/                       # Pipeline media storage (isolated runtime directories)
│   ├── 01_raw_inbox/            # Local raw media imports
│   ├── 02_audio_narrations/     # Generated voice tracks (.mp3)
│   ├── 03_music_sfx/            # Background music and audio effects
│   ├── 04_visual_assets/        # Generated canvases, images, and clips
│   ├── 05_subtitles/            # Subtitle files (.srt, .ass)
│   ├── 06_rendered_output/      # Final rendered videos (.mp4)
│   └── 07_thumbnails/           # Generated video thumbnails
├── scripts/
│   ├── 01_init_voidora_schema.sql      # Database schema initialization
│   ├── backup.sh                       # Automated backup routine
│   ├── sync_from_windows.ps1           # Windows local syncing & dispatcher
│   ├── voidora_pipeline_workflow.json  # Complete n8n pipeline export
│   └── voidora_youtube_publisher.py    # YouTube API v3 uploader
├── worker/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py                     # FastAPI application entrypoint
│       ├── config.py                   # App configuration & settings
│       ├── database.py                 # SQLAlchemy engine & session maker
│       ├── models.py                   # Database models
│       ├── schemas.py                  # Pydantic validation schemas
│       └── services/                   # Core pipeline engines
│           ├── ai_video_engine.py
│           ├── asset_engine.py
│           ├── compositor_engine.py
│           ├── qc_engine.py
│           ├── script_engine.py
│           ├── subtitle_engine.py
│           └── voice_engine.py
└── backups/
    └── workflows/                      # Modular n8n workflow definitions
```

---

## 🛠️ Quick Start

### 1. Configuration
Copy the sample environment file and configure your credentials:
```bash
cp .env.example .env
```
Fill in your database credentials, API keys (Gemini, Fal.ai, Kling, Runway), and host details.

### 2. Start Services
Launch PostgreSQL and n8n with Docker Compose:
```bash
docker compose up -d
```

### 3. Initialize Database Schema
Run the schema initialization script inside the PostgreSQL container:
```bash
docker compose exec -T postgres psql -U n8n_dbuser -d n8n_production < scripts/01_init_voidora_schema.sql
```

### 4. Build & Run Video Worker
To run the worker locally or inside a container:
```bash
cd worker
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## 🔒 Security & Privacy

- `.env` and production secrets are strictly excluded via `.gitignore`.
- Rendered binary video and audio assets are stored locally in `media/` and excluded from version control.
