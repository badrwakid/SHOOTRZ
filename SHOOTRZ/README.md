# SHOOTRZ — AI Basketball Shot Mechanics Analyzer

> Upload a video. Get instant biomechanics feedback. Train like a pro.

SHOOTRZ is a full-stack AI application that analyzes basketball shooting form using computer vision and large language models. Upload a short video clip — SHOOTRZ processes your joint angles, shot phases, release mechanics, and returns a scored breakdown with personalized AI coaching feedback.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Mobile | Expo 54 · React Native · TypeScript |
| Backend | FastAPI · Python 3.12 · uvicorn |
| Pose estimation | MediaPipe Pose (33 landmarks) |
| Ball detection | YOLOv8n (opt-in, `SHOOTRZ_ENABLE_BALL=1`) |
| Shot classification | LightGBM · custom phase detector |
| AI coaching | Google Gemini 2.5 Flash |
| Drill recommendations | FAISS nearest-neighbor + LinUCB bandit |
| Auth & Database | Supabase (PostgreSQL + Auth + Storage) |
| Job queue | asyncio + ProcessPoolExecutor + SQLite |

---

## Architecture Overview

```
Mobile App (Expo)
  │
  ├── POST /mvp/analyze  (upload video)
  │     └── MVPJobService → DurableJobStore (SQLite) → ProcessPoolExecutor
  │           └── MVPPipeline (6 phases, ~15–40 s)
  │                 ├── VideoLoader → frame extraction
  │                 ├── PoseEstimation → MediaPipe 33-landmark
  │                 ├── ShotDetection → phase segmentation
  │                 ├── AngleComputation → biomechanics
  │                 ├── SignalSmoothing → Kalman filter
  │                 └── Metrics → confidence-weighted scoring
  │           └── GeminiEnrichment → personalized coaching text
  │           └── SupabasePersist → sessions, metrics, summaries
  │
  └── GET /mvp/result/{job_id}  (poll until completed)
        └── App renders score ring, metric cards, angle graphs
```

---

## Quick Start

### Prerequisites

- Python 3.11+ with conda (`C:\...\miniconda3\python.exe` on Windows)
- Node.js 18+ and npm
- Expo Go app (iOS / Android) or an emulator
- Supabase project (free tier works)
- Google Gemini API key (free at [aistudio.google.com](https://aistudio.google.com/apikey))

### 1. Clone

```bash
git clone https://github.com/badrwakid/SHOOTRZ.git
cd SHOOTRZ
```

### 2. Backend setup

```bash
# Create and activate environment
conda create -n shootrz python=3.12 -y
conda activate shootrz
pip install -r backend/requirements.txt

# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env and fill in:
#   SUPABASE_URL, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY, GEMINI_API_KEY
```

### 3. Frontend setup

```bash
cp .env.example .env
# Edit .env and fill in:
#   EXPO_PUBLIC_SUPABASE_URL, EXPO_PUBLIC_SUPABASE_ANON_KEY
#   EXPO_PUBLIC_API_URL=http://<your-local-ip>:8000

npm install
```

### 4. Run

```bash
# Terminal 1 — backend
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
npm start
```

Scan the QR code with Expo Go, or press `a` for Android emulator / `i` for iOS simulator.

---

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | Supabase service role key (bypasses RLS) |
| `GEMINI_API_KEY` | Google Gemini API key |
| `GEMINI_MODEL` | Model name (default: `gemini-2.5-flash`) |
| `SHOOTRZ_ENABLE_BALL` | Set to `1` to enable YOLOv8 ball detection |
| `SHOOTRZ_MAX_UPLOAD_MB` | Max upload size in MB (default: 100) |

### Frontend (`SHOOTRZ/.env`)

| Variable | Description |
|----------|-------------|
| `EXPO_PUBLIC_SUPABASE_URL` | Your Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/public key |
| `EXPO_PUBLIC_API_URL` | Backend URL (e.g. `http://192.168.1.x:8000`) |

---

## Database

Apply the complete schema to your Supabase project:

1. Open your Supabase dashboard → SQL Editor
2. Run `supabase/schema_complete.sql`
3. Apply any additional policies in `supabase/storage_policies.sql`

---

## Testing

```bash
# Backend — fast unit tests (no MediaPipe required)
python -m pytest backend/tests/test_api_contracts.py backend/tests/test_job_store.py -q

# Backend — full suite
python -m pytest backend/ -v --ignore=backend/__graveyard__

# Frontend — unit tests
npm test

# Frontend — type check
npx tsc --noEmit

# Frontend — lint
npx eslint src
```

---

## Project Structure

```
SHOOTRZ/
├── backend/              # FastAPI application
│   ├── main.py           # App factory, CORS, router registration
│   ├── routers/          # HTTP endpoints (mvp, chat, history, user, analysis, …)
│   ├── mvp/core/         # 6-phase analysis pipeline
│   ├── inference/        # Phase detector, pose keypoints, ball tracker
│   ├── services/llm/     # Gemini client, prompt builders, output schemas
│   ├── recommender/      # FAISS + LinUCB drill recommendation
│   ├── metrics/          # Biomechanics scoring + normative ranges
│   ├── storage/          # Supabase client factories
│   └── utils/            # Config loader, auth dependency, validators
├── src/                  # React Native / Expo app
│   ├── screens/          # All app screens
│   ├── components/       # Reusable UI components
│   ├── context/          # AuthContext, HistoryContext
│   ├── services/         # API client, Supabase client, chat/storage
│   ├── theme/            # Design tokens, typography, motion
│   └── types/contracts.ts # Canonical TypeScript ↔ backend type mirror
├── supabase/             # SQL migrations and schema
├── docs/                 # Architecture docs and dissertation
├── models/               # Model download instructions (weights via pip)
└── assets/               # App icons, fonts, design system
```

---

## Key Features

- **Shot phase detection** — automatically segments set position, loading, release, follow-through
- **Biomechanics scoring** — 8 key angles (elbow, wrist, knee, hip) scored against normative ranges, weighted by confidence
- **Skill-adaptive scoring** — thresholds adjust for beginner / intermediate / advanced profiles
- **AI coaching** — Gemini 2.5 Flash generates personalized feedback grounded in your actual metrics
- **Drill recommendations** — FAISS similarity + LinUCB exploration for personalized drill suggestions
- **Persistent history** — all sessions, metrics, and summaries stored in Supabase
- **Offline-capable chat** — coach chat with 3-phase context fallback (RPC → local cache → graceful degradation)

---

## License

Academic project — All rights reserved.
