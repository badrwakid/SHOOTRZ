# SHOOTRZ Final Submission Cleanup Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform the SHOOTRZ repository into a clean, secure, professional, submission-ready codebase — removing debug endpoints, binary artifacts, clutter, and stale docs without breaking any functionality.

**Architecture:** SHOOTRZ is a FastAPI backend + Expo React Native frontend with MediaPipe/YOLOv8 CV pipeline, Gemini LLM enrichment, and Supabase persistence. All cleanup must preserve the full request lifecycle: upload → job queue → pipeline → Gemini → Supabase persist → poll → render.

**Tech Stack:** Python 3.12 / FastAPI / MediaPipe / Ultralytics YOLOv8 / LightGBM / FAISS / Supabase · TypeScript / Expo 54 / React Native / Axios

---

## Pre-flight: environment check

Before any task, confirm you can run these from `SHOOTRZ/`:

```powershell
# Backend
C:\Users\Badr\miniconda3\python.exe -m pytest backend/tests/test_api_contracts.py backend/tests/test_job_store.py -q
# Expected: all pass (or known pre-existing failures only)

# Frontend
npx tsc --noEmit
# Expected: 0 errors
```

---

## Task 1: SECURITY — Remove debug router endpoints from production

**Why this is first:** `/db/test` and `/db/integration-test` are live FastAPI routes that expose Supabase client connectivity, full CRUD operations, and error messages. They are mounted unconditionally in `create_app()`.

**Files:**
- Modify: `backend/main.py`
- Keep (but not mounted): `backend/routers/db_test.py`, `backend/routers/db_integration_test.py`

- [ ] **Step 1: Verify the live endpoints**

```powershell
# Start the backend first, then check in another terminal:
# GET http://localhost:8000/db/test
# GET http://localhost:8000/db/integration-test
# Both should return 200 with database state — confirming they are exposed
```

- [ ] **Step 2: Remove the debug router imports and mounts from main.py**

Open `backend/main.py`. Remove lines 26 and 98–99:

```python
# BEFORE (line 26):
from .routers import history, feedback, db_test, db_integration_test, sessions, mvp, user

# AFTER (line 26):
from .routers import history, feedback, sessions, mvp, user
```

```python
# BEFORE (lines 98–99):
    app.include_router(db_test.router)  # Database test endpoint
    app.include_router(db_integration_test.router)  # Integration test endpoint

# AFTER: delete both lines entirely
```

- [ ] **Step 3: Verify no import error at startup**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -c "from backend.main import app; print('OK')"
```

Expected output: `OK`

- [ ] **Step 4: Verify the endpoints are gone**

```powershell
C:\Users\Badr\miniconda3\python.exe -c "
from backend.main import app
routes = [getattr(r, 'path', '') for r in app.routes]
assert '/db/test' not in routes, '/db/test is still exposed!'
assert '/db/integration-test' not in routes, '/db/integration-test is still exposed!'
print('PASS: debug endpoints removed')
"
```

Expected output: `PASS: debug endpoints removed`

- [ ] **Step 5: Run existing API contract tests**

```powershell
C:\Users\Badr\miniconda3\python.exe -m pytest backend/tests/test_api_contracts.py -v
```

Expected: all tests pass (route count may decrease by 2 — acceptable).

- [ ] **Step 6: Commit**

```powershell
cd D:\Users\Badr\Grad
git add SHOOTRZ/backend/main.py
git commit -m "security: remove /db/test and /db/integration-test endpoints from production app"
```

---

## Task 2: GIT — Harden .gitignore and untrack binary ML artifacts

**Why:** `backend/storage/faiss_index.bin` and `drill_embeddings.npy` are ML runtime artifacts tracked in git. On every `git clone` they inflate checkout size and they're regenerated at deploy-time. Additionally, `*.bin`/`*.npy` are missing from `.gitignore`.

**Files:**
- Modify: `SHOOTRZ/.gitignore`
- Untrack (keep file locally): `backend/storage/faiss_index.bin`, `backend/storage/drill_embeddings.npy`

- [ ] **Step 1: Add missing patterns to .gitignore**

Open `SHOOTRZ/.gitignore` and add the following section at the end:

```
# ML artifacts (regenerated at runtime — do not track)
*.npy
*.bin
backend/storage/*.npy
backend/storage/*.bin

# Ad-hoc test/result files
test_results.json
test_health.py
overlay.log

# Local project copies not part of SHOOTRZ
basketball-training-app/
```

- [ ] **Step 2: Remove binary artifacts from git index**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
git rm --cached backend/storage/faiss_index.bin backend/storage/drill_embeddings.npy
```

Expected output:
```
rm 'SHOOTRZ/backend/storage/faiss_index.bin'
rm 'SHOOTRZ/backend/storage/drill_embeddings.npy'
```

- [ ] **Step 3: Verify files are still present locally**

```powershell
Test-Path D:\Users\Badr\Grad\SHOOTRZ\backend\storage\faiss_index.bin
Test-Path D:\Users\Badr\Grad\SHOOTRZ\backend\storage\drill_embeddings.npy
```

Both should print `True` — untrack ≠ delete.

- [ ] **Step 4: Verify .gitignore now covers them**

```powershell
cd D:\Users\Badr\Grad
git status SHOOTRZ/backend/storage/faiss_index.bin
# Expected: nothing — file should be gitignored now
git check-ignore -v SHOOTRZ/backend/storage/faiss_index.bin
# Expected: shows the matching .gitignore pattern
```

- [ ] **Step 5: Commit**

```powershell
git add SHOOTRZ/.gitignore
git commit -m "security: untrack binary ML artifacts, harden .gitignore patterns"
```

---

## Task 3: GIT — Remove broken model submodule pointers

**Why:** `models/hrnet` and `models/yolov8` are gitlink objects (mode 160000) — git submodule pointers — but there is no `.gitmodules` file. Anyone who clones this repo gets broken empty directories. The production backend uses `mediapipe` and `ultralytics` via pip, not the cloned source trees.

**Files:**
- Modify: `models/README.md`
- Git: remove gitlink entries for `models/hrnet`, `models/yolov8`

- [ ] **Step 1: Confirm the broken submodule state**

```powershell
cd D:\Users\Badr\Grad
git ls-files -s SHOOTRZ/models/hrnet SHOOTRZ/models/yolov8
```

Expected output shows mode `160000` (gitlink) — confirms they are submodule pointers.

- [ ] **Step 2: Remove the broken gitlink entries from the index**

```powershell
cd D:\Users\Badr\Grad
git rm --cached SHOOTRZ/models/hrnet SHOOTRZ/models/yolov8
```

Expected output:
```
rm 'SHOOTRZ/models/hrnet'
rm 'SHOOTRZ/models/yolov8'
```

Note: The local directories remain on disk — only the broken pointers are removed.

- [ ] **Step 3: Add models/hrnet and models/yolov8 to .gitignore**

Add to `SHOOTRZ/.gitignore`:

```
# Research model source clones (use pip packages instead)
models/hrnet/
models/yolov8/
```

- [ ] **Step 4: Update models/README.md to explain the model sources**

Rewrite `SHOOTRZ/models/README.md` to:

```markdown
# Models

This directory contains references to the AI model architectures used in SHOOTRZ.

## Pose Estimation
- **MediaPipe Pose** — installed via `pip install mediapipe` (no local clone needed)
- HRNet reference: https://github.com/HRNet/deep-high-resolution-net.pytorch

## Ball Detection
- **YOLOv8** — installed via `pip install ultralytics` (no local clone needed)
- Ultralytics reference: https://github.com/ultralytics/ultralytics
- Pre-trained weights (`yolov8n.pt`) are downloaded automatically by ultralytics on first use

## Model Weights
Model weight files (`.pt`, `.pth`, `.onnx`) are excluded from git via `.gitignore`.
They are downloaded automatically by the `ultralytics` package or regenerated via training scripts.
```

- [ ] **Step 5: Verify models/README.md is tracked**

```powershell
cd D:\Users\Badr\Grad
git status SHOOTRZ/models/
```

Expected: `models/README.md` shows as modified; `models/hrnet` and `models/yolov8` should NOT appear as staged for deletion (already removed in step 2) and should be gitignored.

- [ ] **Step 6: Commit**

```powershell
cd D:\Users\Badr\Grad
git add SHOOTRZ/.gitignore SHOOTRZ/models/README.md
git commit -m "cleanup: remove broken submodule pointers for models/hrnet and models/yolov8, add pip-install notes"
```

---

## Task 4: GIT — Remove tracked clutter files

**Why:** `test_health.py` (ad-hoc import script), `test_results.json` (JSON test output), `BUG_REPORT.md`, `CLEANUP_REPORT.md`, `MODERNIZATION_REPORT.md` (AI-generated process reports from April 2026), and `INSTALL_SOCIAL_AUTH.txt` (installation note for an old `basketball-training-app` that no longer exists) are all tracked in git. They add noise to the repo and are not useful to anyone reviewing the project.

**Files to remove from git tracking:**
- `SHOOTRZ/test_health.py`
- `SHOOTRZ/test_results.json`
- `SHOOTRZ/BUG_REPORT.md`
- `SHOOTRZ/CLEANUP_REPORT.md`
- `SHOOTRZ/MODERNIZATION_REPORT.md`
- `SHOOTRZ/INSTALL_SOCIAL_AUTH.txt`

- [ ] **Step 1: Confirm these files are tracked**

```powershell
cd D:\Users\Badr\Grad
git ls-files SHOOTRZ/test_health.py SHOOTRZ/test_results.json SHOOTRZ/BUG_REPORT.md SHOOTRZ/CLEANUP_REPORT.md SHOOTRZ/MODERNIZATION_REPORT.md SHOOTRZ/INSTALL_SOCIAL_AUTH.txt
```

Expected: all 6 paths are listed.

- [ ] **Step 2: Remove from git and delete from disk**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
git rm test_health.py test_results.json BUG_REPORT.md CLEANUP_REPORT.md MODERNIZATION_REPORT.md INSTALL_SOCIAL_AUTH.txt
```

- [ ] **Step 3: Verify deletion**

```powershell
Test-Path D:\Users\Badr\Grad\SHOOTRZ\test_health.py
Test-Path D:\Users\Badr\Grad\SHOOTRZ\BUG_REPORT.md
```

Both should print `False`.

- [ ] **Step 4: Commit**

```powershell
cd D:\Users\Badr\Grad
git commit -m "cleanup: remove stale process reports, ad-hoc test scripts, and install notes from repo root"
```

---

## Task 5: BACKEND — Fix misnamed package init file in recommender

**Why:** `backend/recommender/init.py` (1 byte, empty) is named without double underscores. Python 3 namespace packages still work without `__init__.py`, but:
1. The file was almost certainly intended as the package initializer
2. Some import scanners, type checkers, and pytest plugins require `__init__.py` for proper package detection
3. It signals poor craftsmanship to reviewers

**Files:**
- Rename: `backend/recommender/init.py` → `backend/recommender/__init__.py`

- [ ] **Step 1: Rename the file using git mv**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
git mv backend/recommender/init.py backend/recommender/__init__.py
```

- [ ] **Step 2: Verify the recommender package still imports correctly**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -c "from backend.recommender.recommend_service import recommend_drill; print('OK')"
```

Expected output: `OK`

- [ ] **Step 3: Run recommender-specific tests**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -m pytest backend/recommender/ backend/tests/test_recommend_auth.py -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```powershell
cd D:\Users\Badr\Grad
git add SHOOTRZ/backend/recommender/__init__.py
git commit -m "fix: rename recommender/init.py to __init__.py for proper package declaration"
```

---

## Task 6: DOCS — Prune internal process documentation

**Why:** `docs/` contains 14 internal working documents (Gemini integration audits, history route fix reports, data persistence audits, root cause analyses) that were created during development sprints. These are valuable as a paper trail but not as documentation for submission reviewers or new contributors. They make the docs directory noisy and hard to navigate.

**Keep (reference quality):**
- `docs/latex/` — dissertation chapters
- `docs/superpowers/plans/` — implementation plans
- `docs/shootrz_model_audit.md` — explains model choices
- `docs/FINAL_REPORT.md` — project summary
- `docs/auth_and_user_state_flow.md` — architecture reference
- `docs/correct_data_architecture.md` — architecture reference

**Remove (internal process docs):**
- `docs/gemini_feature_mapping.md`
- `docs/gemini_future_improvements.md`
- `docs/gemini_integration_audit.md`
- `docs/gemini_integration_overview.md`
- `docs/gemini_prompt_system.md`
- `docs/gemini_setup.md`
- `docs/gemini_use_cases.md`
- `docs/final_gemini_integration_report.md`
- `docs/data_persistence_audit.md`
- `docs/data_persistence_test_plan.md`
- `docs/final_data_fix_report.md`
- `docs/history_and_chat_data_flow.md`
- `docs/history_route_and_expoav_audit.md`
- `docs/history_route_fix_report.md`
- `docs/history_route_root_cause.md`
- `docs/root_cause_analysis.md`
- `database/DATABASE_REPORT.md` (duplicate of what's in docs)

- [ ] **Step 1: Remove docs that are internal process artifacts**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
git rm docs/gemini_feature_mapping.md `
       docs/gemini_future_improvements.md `
       docs/gemini_integration_audit.md `
       docs/gemini_integration_overview.md `
       docs/gemini_prompt_system.md `
       docs/gemini_setup.md `
       docs/gemini_use_cases.md `
       docs/final_gemini_integration_report.md `
       docs/data_persistence_audit.md `
       docs/data_persistence_test_plan.md `
       docs/final_data_fix_report.md `
       docs/history_and_chat_data_flow.md `
       docs/history_route_and_expoav_audit.md `
       docs/history_route_fix_report.md `
       docs/history_route_root_cause.md `
       docs/root_cause_analysis.md `
       database/DATABASE_REPORT.md
```

- [ ] **Step 2: Verify remaining docs structure**

```powershell
Get-ChildItem D:\Users\Badr\Grad\SHOOTRZ\docs -Recurse -File | Select-Object -ExpandProperty FullName
```

Expected survivors: `FINAL_REPORT.md`, `auth_and_user_state_flow.md`, `correct_data_architecture.md`, `shootrz_model_audit.md`, `latex/**`, `superpowers/plans/**`, `data/README.md`

- [ ] **Step 3: Commit**

```powershell
cd D:\Users\Badr\Grad
git commit -m "docs: remove 16 internal process/audit docs, keep architecture references and dissertation"
```

---

## Task 7: README — Professional rewrite

**Why:** The current README is 53 lines of minimal commands. For final submission, recruiter review, and GitHub profile visibility, SHOOTRZ needs a README that communicates the full scope of the project.

**File:**
- Modify: `SHOOTRZ/README.md`

- [ ] **Step 1: Rewrite README.md**

Replace the entire contents of `SHOOTRZ/README.md` with:

```markdown
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
```

- [ ] **Step 2: Verify the README renders cleanly**

```powershell
# Quick sanity check — look for unclosed code fences
$content = Get-Content D:\Users\Badr\Grad\SHOOTRZ\README.md -Raw
$fence_count = ([regex]::Matches($content, '(?m)^```')).Count
if ($fence_count % 2 -ne 0) { Write-Error "Odd number of backtick fences — unclosed block!" }
else { Write-Host "Fence check OK: $fence_count fences (all paired)" }
```

Expected output: `Fence check OK: X fences (all paired)`

- [ ] **Step 3: Commit**

```powershell
cd D:\Users\Badr\Grad
git add SHOOTRZ/README.md
git commit -m "docs: rewrite README with full project description, architecture, setup guide, and feature list"
```

---

## Task 8: CLAUDE.md — Remove stale schema reference

**Why:** CLAUDE.md line 95–98 says `supabase/schema.sql` is "incomplete — missing user_profiles, analysis_summaries, …". That note was written before `supabase/schema_complete.sql` was created. The note now misleads future Claude sessions into thinking the canonical schema is missing tables.

**File:**
- Modify: `SHOOTRZ/CLAUDE.md`

- [ ] **Step 1: Update the Ground-truth locations section**

Find and update this section in `CLAUDE.md`:

```markdown
# BEFORE (lines ~93-96):
- **Supabase schema:** `supabase/schema.sql` is **incomplete** — missing `user_profiles`, `analysis_summaries`, `chat_history`, `drill_completions`, `user_streaks`, `session_videos`. Audit plan consolidates them into `supabase/schema_complete.sql`.

# AFTER:
- **Supabase schema:** `supabase/schema_complete.sql` is the canonical schema — includes all tables (`sessions`, `session_videos`, `video_metrics`, `analysis_summaries`, `chat_history`, `drill_completions`, `user_streaks`, `user_profiles`), RLS policies, indexes, and triggers. `supabase/schema.sql` is a legacy partial file; ignore it.
```

- [ ] **Step 2: Verify the edit looks correct**

```powershell
Select-String -Path D:\Users\Badr\Grad\SHOOTRZ\CLAUDE.md -Pattern "schema_complete"
```

Expected: two matches (the one you just wrote).

- [ ] **Step 3: Commit**

```powershell
cd D:\Users\Badr\Grad
git add SHOOTRZ/CLAUDE.md
git commit -m "docs: update CLAUDE.md to reference schema_complete.sql as canonical, remove stale incomplete note"
```

---

## Task 9: VALIDATION — Full project health check

This task verifies the repo is still fully functional after all cleanup tasks.

**Files:** No changes — validation only.

- [ ] **Step 1: Verify backend imports cleanly**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -c "
from backend.main import app
from backend.routers import mvp, chat, history, feedback, sessions, user, analysis
from backend.recommender.recommend_service import recommend_drill
from backend.mvp.core.pipeline import MVPPipeline
from backend.services.mvp_job_service import MVPJobService
print('All imports OK')
print(f'Routes registered: {len(app.routes)}')
"
```

Expected: `All imports OK` and a route count of approximately 30–40.

- [ ] **Step 2: Run core backend test suite**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -m pytest `
    backend/tests/test_api_contracts.py `
    backend/tests/test_job_store.py `
    backend/tests/test_history_auth.py `
    backend/tests/test_recommend_auth.py `
    backend/tests/test_upload_size.py `
    backend/tests/test_shot_score.py `
    backend/tests/test_biomechanics.py `
    -v --tb=short
```

Expected: all pass (or pre-existing failures unrelated to cleanup).

- [ ] **Step 3: Run recommender tests (validates Task 5)**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -m pytest backend/recommender/ -v
```

Expected: all pass.

- [ ] **Step 4: Run MVP pipeline tests**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
C:\Users\Badr\miniconda3\python.exe -m pytest backend/mvp/tests/ -v
```

Expected: all pass.

- [ ] **Step 5: Run frontend type check**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
npx tsc --noEmit
```

Expected: 0 errors.

- [ ] **Step 6: Run frontend lint**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
npx eslint src --max-warnings=0
```

Expected: 0 errors, 0 warnings. If there are pre-existing warnings, document them but do not let this block submission.

- [ ] **Step 7: Run frontend unit tests**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
npm test -- --passWithNoTests
```

Expected: all pass.

- [ ] **Step 8: Verify git status is clean**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
git status
```

Expected: working tree clean after all commits.

- [ ] **Step 9: Commit validation summary**

No code changes — this task is validation only. If everything passes, proceed to the final commit.

```powershell
cd D:\Users\Badr\Grad
git log --oneline -10
```

Review: the last 8 commits should be the cleanup tasks from this plan.

---

## Task 10: FINAL — Scorecard commit and tag

- [ ] **Step 1: Verify final tracked file count is clean**

```powershell
cd D:\Users\Badr\Grad
git ls-files SHOOTRZ/ | grep -v "node_modules\|venv\|__pycache__\|fonts/" | wc -l
```

Aim for < 250 tracked files (was ~300+ before cleanup).

- [ ] **Step 2: Check for any remaining secrets in tracked files**

```powershell
cd D:\Users\Badr\Grad\SHOOTRZ
# Search tracked files for JWT-style tokens
git grep -l "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" 2>$null
# Search for Google API key prefixes
git grep -l "AIzaSy" 2>$null
# Search for raw Supabase URL
git grep -l "apbtuxchrymgmjbjxltm" 2>$null
```

Expected: no output (no tracked files with secrets).

- [ ] **Step 3: Create final submission commit**

```powershell
cd D:\Users\Badr\Grad
git add -A SHOOTRZ/
git commit -m "chore: final pre-submission cleanup and validation complete

- Removed debug DB router endpoints from production API
- Untracked binary ML artifacts (faiss_index.bin, drill_embeddings.npy)
- Removed broken submodule pointers for models/hrnet and models/yolov8
- Pruned 16 internal process/audit documents from docs/
- Removed root-level clutter (BUG_REPORT, CLEANUP_REPORT, MODERNIZATION_REPORT)
- Fixed recommender/__init__.py naming
- Rewrote README with full project description and setup guide
- Updated CLAUDE.md to reference schema_complete.sql as canonical"
```

---

## Self-review checklist

| # | Requirement | Covered in |
|---|-------------|-----------|
| Security: no debug endpoints | ✅ | Task 1 |
| Security: no tracked secrets | ✅ | Task 2 + Task 10 |
| Binary artifacts untracked | ✅ | Task 2 |
| .gitignore hardened | ✅ | Task 2 |
| Broken submodules removed | ✅ | Task 3 |
| Root clutter removed | ✅ | Task 4 |
| Backend package naming fixed | ✅ | Task 5 |
| Docs pruned to reference quality | ✅ | Task 6 |
| README professional | ✅ | Task 7 |
| CLAUDE.md updated | ✅ | Task 8 |
| All tests pass | ✅ | Task 9 |
| TypeScript checks | ✅ | Task 9 |
| Git log clean/logical | ✅ | Task 10 |

---

## Estimated effort

| Task | Effort |
|------|--------|
| 1 — Security (debug endpoints) | 5 min |
| 2 — Binary artifacts | 3 min |
| 3 — Broken submodules | 5 min |
| 4 — Root clutter removal | 2 min |
| 5 — recommender init.py | 3 min |
| 6 — Docs consolidation | 5 min |
| 7 — README rewrite | 10 min |
| 8 — CLAUDE.md fix | 2 min |
| 9 — Full validation | 10 min |
| 10 — Final commit | 2 min |
| **Total** | **~47 min** |
