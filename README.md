# SHOOTRZ — AI Basketball Shot Mechanics Analyzer

SHOOTRZ is a full-stack AI application that analyzes basketball shooting form from video. It extracts pose landmarks with MediaPipe, computes biomechanics angles across six pipeline phases, scores them against normative ranges, and delivers personalized coaching feedback via Google Gemini 2.5 Flash — all from a React Native mobile app.

> **Repository layout:** All project source lives in the `SHOOTRZ/` subdirectory.  
> After cloning, `cd SHOOTRZ` once to enter the project.

---

## Table of Contents

1. [Features](#features)
2. [Tech Stack](#tech-stack)
3. [Architecture](#architecture)
4. [Prerequisites](#prerequisites)
5. [Setup — Backend](#setup--backend)
6. [Setup — Database](#setup--database)
7. [Setup — Frontend](#setup--frontend)
8. [Running the App](#running-the-app)
9. [Environment Variables Reference](#environment-variables-reference)
10. [Testing](#testing)
11. [Project Structure](#project-structure)
12. [API Reference](#api-reference)
13. [Troubleshooting](#troubleshooting)
14. [License](#license)

---

## Features

- **6-phase analysis pipeline** — video ingestion, pose estimation, signal smoothing, angle computation, shot detection, and scoring run in a background process pool so the API never blocks
- **Biomechanics scoring** — elbow extension, knee bend, and wrist follow-through scored against configurable normative ranges; confidence-weighted so low-quality frames don't corrupt the result
- **Skill-adaptive thresholds** — scoring bands tighten or loosen for beginner / intermediate / advanced players
- **AI coaching (Coach J)** — Gemini 2.5 Flash generates personalized drill tips grounded in the player's actual metric data; falls back gracefully when offline
- **Drill recommendations** — FAISS nearest-neighbour + LinUCB bandit balances relevance with exploration
- **Persistent history** — sessions, metrics, summaries, and chat stored in Supabase PostgreSQL with RLS
- **Streaming chat** — SSE-based coach chat with 3-phase context fallback (RPC → local cache → degraded)
- **Offline-capable** — chat history cached locally; analysis results survive client crashes via 72 h job store

---

## Tech Stack

| Layer | Technology |
|---|---|
| Mobile app | Expo 54 · React Native 0.81 · TypeScript |
| Backend API | FastAPI 0.110+ · Python 3.11 · uvicorn |
| Pose estimation | MediaPipe Pose 0.10.14 (33 landmarks) |
| Ball detection | YOLOv8n via `ultralytics` (opt-in) |
| Shot classification | Custom phase detector · LightGBM |
| Signal processing | Savitzky-Golay filter · filterpy Kalman |
| AI coaching | Google Gemini 2.5 Flash (`google-genai`) |
| Recommendations | FAISS · MABWiser LinUCB bandit |
| Auth & database | Supabase (PostgreSQL + Auth + Storage) |
| Job queue | asyncio + `ProcessPoolExecutor` + SQLite |
| Rate limiting | slowapi |
| Testing | pytest · Jest · Locust |

---

## Architecture

```
Mobile App (Expo)
  │
  ├── POST /mvp/analyze          Upload video → queued job
  │     └── MVPJobService
  │           ├── DurableJobStore (SQLite) → status: queued
  │           └── ProcessPoolExecutor
  │                 └── MVPPipeline (6 phases, ~15–40 s)
  │                       ├── Phase 1+2  VideoLoader + MediaPipe pose (fused stream)
  │                       ├── Phase 3    Savitzky-Golay signal smoothing
  │                       ├── Phase 4+5a Angle computation + shot-window detection
  │                       ├── Phase 5b   Motion-based phase labelling
  │                       └── Phase 6    Metric scoring + confidence weighting
  │                 └── GeminiEnrichment  personalised coaching text
  │                 └── SupabasePersist   sessions · metrics · summaries
  │
  ├── GET  /mvp/result/{job_id}  Poll until completed → render results
  └── POST /chat/stream          SSE coach chat (Coach J)
```

---

## Prerequisites

Install these before starting:

| Tool | Required version | Download |
|---|---|---|
| Python | 3.11 or 3.12 | [python.org](https://www.python.org/downloads/) |
| conda | Any recent | [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/) |
| Node.js | 18 or 20 LTS | [nodejs.org](https://nodejs.org/) |
| npm | Bundled with Node | — |
| Git | Any | [git-scm.com](https://git-scm.com/) |
| Expo Go | Latest | [iOS](https://apps.apple.com/app/expo-go/id982107779) / [Android](https://play.google.com/store/apps/details?id=host.exp.exponent) |

**Accounts you need:**

| Service | Purpose | Free tier |
|---|---|---|
| [Supabase](https://supabase.com/) | Database, auth, file storage | ✅ Yes |
| [Google AI Studio](https://aistudio.google.com/apikey) | Gemini API key | ✅ Yes |

> **Note on PyTorch:** `requirements.txt` includes `torch>=2.0.0` (~2 GB download). If disk space is tight, install CPU-only: `pip install torch --index-url https://download.pytorch.org/whl/cpu` before running `pip install -r requirements.txt`.

---

## Setup — Backend

### 1. Clone and enter the project

```bash
git clone https://github.com/badrwakid/SHOOTRZ.git
cd SHOOTRZ      # enter the repo
cd SHOOTRZ      # enter the project directory (yes, twice)
```

### 2. Create a conda environment

```bash
conda create -n shootrz python=3.11 -y
conda activate shootrz
```

### 3. Install Python dependencies

```bash
pip install -r backend/requirements.txt
```

This installs MediaPipe, FastAPI, Supabase client, Gemini SDK, PyTorch, FAISS, and all other backend packages. Expect 5–15 minutes on first install.

### 4. Configure backend environment

```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your values:

```env
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=60
GEMINI_MAX_RETRIES=3
```

Where to find each value:
- **SUPABASE_URL** / **SUPABASE_ANON_KEY** / **SUPABASE_SERVICE_KEY** → Supabase Dashboard → Project Settings → API
- **GEMINI_API_KEY** → [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

### 5. Verify the backend loads

```bash
python -c "from backend.main import app; print('Backend OK —', len(app.routes), 'routes')"
```

Expected output: `Backend OK — 38 routes` (number may vary slightly).

---

## Setup — Database

All schema and policies live in the `supabase/` directory. Apply them to your Supabase project in this order:

### 1. Apply the canonical schema

Go to **Supabase Dashboard → SQL Editor**, paste and run:

```
supabase/schema_complete.sql
```

This creates all 13 tables (`users`, `user_profiles`, `sessions`, `videos`, `metrics`, `analysis_summaries`, `chat_history`, `drill_completions`, `workout_progress`, `user_streaks`, `session_videos`, `feedback`, `models`), enums, RLS policies, and indexes.

### 2. Apply storage policies

In the same SQL Editor, run:

```
supabase/storage_policies.sql
```

This sets up the `videos` storage bucket with per-user read/write/delete policies.

### 3. Apply migrations (in order)

Run each of these in sequence:

```
supabase/trigger_create_user.sql
supabase/migration_mvp_enhancements.sql
supabase/migration_add_name_onboarding.sql
supabase/add_username_column.sql
supabase/add_delete_policy.sql
supabase/fix_oauth_signup_database_error.sql
supabase/migration_coach_context_rpc.sql
supabase/migration_user_profile_atomic_rpc.sql
supabase/migration_user_profile_preferences.sql
```

### 4. Configure Supabase Auth

In **Supabase Dashboard → Authentication → URL Configuration**:

- **Site URL**: `http://localhost:8081` (for local Expo development)
- **Redirect URLs**: Add `shootrz://auth/callback` (for Google OAuth deep link)

### 5. Verify the schema

```
supabase/verify_setup.sql
```

Run this in the SQL Editor — it returns a summary of tables, RLS status, and row counts.

---

## Setup — Frontend

### 1. Install Node dependencies

```bash
# From inside SHOOTRZ/ (the project directory)
npm install
```

### 2. Configure frontend environment

```bash
cp .env.example .env
```

Open `.env` and fill in:

```env
EXPO_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
EXPO_PUBLIC_API_URL=http://YOUR_LOCAL_IP:8000
```

> **Important:** `EXPO_PUBLIC_API_URL` must be your machine's **local network IP address**, not `localhost`. The mobile device or emulator cannot reach `localhost` on your computer.
>
> Find your IP:
> - **Windows:** `ipconfig` → look for IPv4 Address (e.g. `192.168.1.42`)
> - **macOS/Linux:** `ifconfig` or `ip addr`
>
> Set it as: `EXPO_PUBLIC_API_URL=http://192.168.1.42:8000`

---

## Running the App

You need two terminals running simultaneously.

### Terminal 1 — Backend

```bash
# From inside SHOOTRZ/ (the project directory)
conda activate shootrz
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Confirm it's running:

```bash
curl http://localhost:8000/health
```

Expected response includes `"status": "ok"` and `"version": "0.2.0"`.

### Terminal 2 — Frontend

```bash
# From inside SHOOTRZ/ (the project directory)
npm start
```

Then:
- **Physical device** — Scan the QR code with Expo Go (same Wi-Fi network as your computer)
- **Android emulator** — Press `a` (requires Android Studio + AVD)
- **iOS simulator** — Press `i` (macOS only, requires Xcode)

### Optional: Enable YOLOv8 ball detection

Ball tracking is disabled by default to keep startup fast. To enable it:

```env
# Add to backend/.env
SHOOTRZ_ENABLE_BALL=1
```

Restart the backend. The first request will download `yolov8n.pt` automatically (~6 MB).

---

## Environment Variables Reference

### Backend — `backend/.env`

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | ✅ | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anon/public key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key (bypasses RLS for server writes) |
| `GEMINI_API_KEY` | ✅ | Google Gemini API key |
| `GEMINI_MODEL` | Optional | Model name (default: `gemini-2.5-flash`) |
| `GEMINI_TIMEOUT` | Optional | Request timeout in seconds (default: `60`) |
| `GEMINI_MAX_RETRIES` | Optional | Retry count on transient errors (default: `3`) |
| `SHOOTRZ_ENABLE_BALL` | Optional | Set to `1` to enable YOLOv8 ball detection |
| `SHOOTRZ_MAX_UPLOAD_MB` | Optional | Max video upload size in MB (default: `100`) |

### Frontend — `.env`

| Variable | Required | Description |
|---|---|---|
| `EXPO_PUBLIC_SUPABASE_URL` | ✅ | Your Supabase project URL |
| `EXPO_PUBLIC_SUPABASE_ANON_KEY` | ✅ | Supabase anon/public key |
| `EXPO_PUBLIC_API_URL` | ✅ | Backend base URL — use your machine's LAN IP, not localhost |

---

## Testing

### Backend tests

```bash
# From inside SHOOTRZ/
conda activate shootrz

# Fast unit tests (no MediaPipe/GPU required, ~5 s)
python -m pytest backend/tests/test_api_contracts.py backend/tests/test_job_store.py -v

# Full test suite
python -m pytest backend/ -v --ignore=backend/__graveyard__

# Single test file
python -m pytest backend/tests/test_shot_score.py -v

# With coverage
python -m pytest backend/ --cov=backend --cov-report=term-missing
```

### Frontend tests

```bash
# Unit tests
npm test

# Watch mode
npm run test:watch

# TypeScript type check
npm run typecheck

# Lint
npm run lint
```

### Load tests (optional)

```bash
pip install locust
locust -f backend/tests/load/locustfile.py --host=http://localhost:8000
```

Open `http://localhost:8089` to configure and run load scenarios.

---

## Project Structure

```
SHOOTRZ/                         ← repo root
└── SHOOTRZ/                     ← project root (run all commands from here)
    ├── backend/
    │   ├── main.py              # FastAPI app factory, CORS, router wiring
    │   ├── routers/             # HTTP endpoints
    │   │   ├── mvp.py           # POST /mvp/analyze, GET /mvp/result/{id}
    │   │   ├── chat.py          # POST /chat/stream (SSE)
    │   │   ├── analysis.py      # POST /api/analysis/complete
    │   │   ├── user.py          # GET/PATCH /api/user/*
    │   │   ├── history.py       # GET /history/{user_id}
    │   │   ├── sessions.py      # CRUD /api/sessions
    │   │   ├── feedback.py      # POST /api/feedback
    │   │   └── recommendation_routes.py
    │   ├── mvp/core/            # 6-phase analysis pipeline
    │   │   ├── pipeline.py      # Orchestrator (entry point)
    │   │   ├── video_loader.py  # Frame extraction
    │   │   ├── pose_estimation.py
    │   │   ├── signal_smoothing.py
    │   │   ├── angle_computation.py
    │   │   ├── shot_detection.py
    │   │   └── metrics.py
    │   ├── inference/           # ML model wrappers
    │   │   ├── pose_2d.py       # MediaPipe wrapper
    │   │   ├── ball_tracker.py  # YOLOv8 (opt-in)
    │   │   └── phase_detector.py
    │   ├── services/
    │   │   ├── mvp_job_service.py   # Job queue + Gemini enrichment + Supabase persist
    │   │   ├── job_store.py         # SQLite-backed DurableJobStore
    │   │   └── llm/                 # Gemini client, prompt builders, output schemas
    │   ├── recommender/         # FAISS + LinUCB drill recommendation
    │   ├── storage/             # Supabase client factories + SupabaseDB class
    │   ├── metrics/             # Scoring logic + normative_ranges.json
    │   ├── chat/                # Context builder for Coach J
    │   ├── feedback/            # Rule-based coaching cue engine
    │   ├── contracts/           # Pydantic request/response models
    │   ├── config/              # mvp_config.yaml, models.yaml
    │   ├── utils/               # Config loader, auth dependency, validators
    │   └── tests/               # pytest test suites
    ├── src/
    │   ├── screens/             # All app screens (Home, Analyze, Chat, Profile, …)
    │   ├── components/          # Reusable UI components
    │   ├── context/             # AuthContext, HistoryContext, ProfileContext
    │   ├── navigation/          # AppNavigator (8-tab layout)
    │   ├── services/            # API client (Axios), Supabase client, chat cache
    │   ├── theme/               # Design tokens, typography, motion, scoreTier
    │   ├── hooks/               # useDeepLinks, useReduceMotion
    │   ├── utils/               # deepLinks, hapticFeedback, eventBus
    │   └── types/contracts.ts   # TypeScript ↔ backend type mirror (source of truth)
    ├── supabase/                # SQL schema and migrations (apply via Supabase dashboard)
    ├── assets/                  # App icons, fonts, design system
    ├── scripts/                 # Dev utilities (start_backend.ps1, verify_setup.py, …)
    ├── notebooks/               # train_yolov8_ball_colab.ipynb
    ├── models/                  # Model download instructions (weights via pip, not tracked)
    ├── docs/                    # Architecture references
    ├── App.tsx                  # Root component
    ├── index.ts                 # Expo entry point
    ├── app.json                 # Expo config (name: SHOOTRZ, scheme: shootrz)
    ├── package.json
    └── backend/requirements.txt
```

---

## API Reference

All backend endpoints are also available via the auto-generated docs at `http://localhost:8000/docs` when the backend is running.

### Analysis

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/mvp/analyze` | Optional | Submit video for analysis. Returns `job_id`. |
| `GET` | `/mvp/result/{job_id}` | Optional | Poll job status. Returns result when `status: completed`. |
| `POST` | `/api/analysis/complete` | ✅ Required | Persist completed analysis to Supabase. |

### Chat

| Method | Path | Auth | Description |
|---|---|---|---|
| `POST` | `/chat/stream` | ✅ Required | SSE streaming coach chat. |

### User & History

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/user/account` | ✅ Required | Get user account data. |
| `PATCH` | `/api/user/profile` | ✅ Required | Update extended profile fields. |
| `GET` | `/api/user/stats` | ✅ Required | Aggregate stats (sessions, streaks). |
| `GET` | `/api/user/streak` | ✅ Required | Current and longest streak. |
| `GET` | `/api/user/analysis-history` | ✅ Required | Paginated analysis history. |
| `GET` | `/history/{user_id}` | None | Public session history (legacy). |

### Sessions & Drills

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/sessions` | ✅ Required | List sessions. |
| `GET` | `/api/sessions/{id}` | ✅ Required | Session detail. |
| `GET` | `/api/recommendations` | ✅ Required | Personalised drill recommendations. |

### Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Backend health, version, uptime. |
| `GET` | `/docs` | Auto-generated Swagger UI. |

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'backend'`**  
You must run all Python commands from inside the `SHOOTRZ/` project directory, not from the repo root. The package is `backend.*`, not `SHOOTRZ.backend.*`.

**`Network request failed` on the mobile app**  
`EXPO_PUBLIC_API_URL` is set to `localhost`. Change it to your machine's LAN IP address (e.g. `http://192.168.1.42:8000`). The phone/emulator cannot reach your computer's localhost.

**MediaPipe installation fails on Apple Silicon**  
Use `pip install mediapipe --no-cache-dir`. If that fails, try `pip install mediapipe-silicon` (community build).

**`torch` download takes too long or fails**  
Install the CPU-only version first, then install the rest:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r backend/requirements.txt
```

**Supabase `permission denied` errors**  
The `SUPABASE_SERVICE_KEY` (service role key) is needed for server-side writes that bypass RLS. Make sure you copied the **service role** key, not the anon key.

**`CORS` error from the mobile app**  
The backend allows all origins by default. If you see a CORS error, confirm the backend is actually running and reachable at the URL in `EXPO_PUBLIC_API_URL`.

**Video analysis stuck at `queued`**  
Check that `backend/outputs/` is writable. The pipeline writes temporary files there during processing. Also check backend logs for MediaPipe import errors.

**Expo Metro bundler port conflict**  
If port 8081 is busy: `npx expo start --port 8082`

---

## License

Academic project — All rights reserved.
