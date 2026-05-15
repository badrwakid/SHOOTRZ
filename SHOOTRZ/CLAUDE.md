# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 1. AI Persona & Interaction Rules

- Act as a senior technical mentor pushing a driven AI & Data Science student to become world-class.
- **Do not just agree.** Challenge ideas constructively and point out architectural blind spots.
- Keep responses concise but insightful. Rely on strong logic, real-world examples, and clear structure over conversational filler.
- Tone: Serious and highly detailed for engineering/startup discussions; natural and human for casual topics.
- Every output must teach a concept, refine a process, or build a tangible outcome.

## 2. The Golden Rule

- **Do not make any changes until you have 95% confidence in what you need to build. Ask follow-up questions until you reach that confidence.**

## 3. Global Tech Stack & Workflow

- **Core stack:** Python (ML/CV, FastAPI, APIs), React Native (Expo).
- **Tooling preference:** GUI-driven IDEs and visual tools over CLI-heavy workflows.
- **Outputs:** Provide targeted diffs, not full-file rewrites. Do not generate boilerplate unless explicitly requested.

## 4. Personal Context Index

- **Projects:** Actively building AI startups in SportsTech (SHOOTRZ) and FinTech (Masareef AI). Read the project README for localized context.
- **Operating philosophy:** Driven by *ihsan* — pursuing excellence in every action. Values discipline, consistency, high performance.
- **Athletic framework:** Trains as a competitive basketball shooting guard. Apply the same rep-based, high-performance logic to engineering feedback.

---

## SHOOTRZ — Project Context

**What it is:** Basketball shot-mechanics analysis app. React Native / Expo frontend + FastAPI backend running MediaPipe pose + YOLOv8 ball detection + Gemini 2.5 Flash, persisting to Supabase (PostgreSQL + Auth + Storage).

**Canonical path:** `SHOOTRZ/` is the project root. Do not use the workspace-level `package.json`.

### High-level architecture

```
SHOOTRZ/
├── backend/                   # FastAPI backend (Python 3.11+)
│   ├── main.py                # App factory, CORS, lifespan, router wiring
│   ├── routers/               # HTTP endpoints: mvp, analysis, chat, user, history,
│   │                          # sessions, feedback, recommendation_routes
│   ├── mvp/core/              # Pipeline stages: video_loader → pose_estimation →
│   │                          # shot_detection → angle_computation → signal_smoothing
│   │                          # → metrics → run_tracker
│   ├── inference/             # phase_detector, pose_2d keypoint map, ball_tracker
│   │                          # (YOLOv8n, opt-in), motion_analyzer
│   ├── feedback/              # Rule-based coaching-cue engine
│   ├── services/
│   │   ├── mvp_job_service.py # ProcessPool orchestration + Gemini enrichment +
│   │   │                      # Supabase persist
│   │   ├── job_store.py       # DurableJobStore: SQLite-backed job state
│   │   └── llm/               # gemini_client, prompt_builders, output_schemas,
│   │                          # fallbacks, llm_router
│   ├── recommender/           # FAISS nearest-neighbor + LinUCB bandit drill rec
│   ├── storage/               # SupabaseDB + service_role / anon client factories
│   ├── metrics/               # biomechanics + normative_ranges.json
│   └── utils/                 # config (dotenv), supabase_auth FastAPI dependency
├── src/                       # React Native / Expo app
│   ├── screens/               # Home, MVPAnalysis, Chat, Progress, Profile, Drills,
│   │                          # Workouts, Login, Onboarding, Username, Splash, ...
│   ├── services/              # api.service.ts (Axios), supabase.client.ts (anon),
│   │                          # chat.service, chat-storage, storage.service
│   ├── context/               # AuthContext (Supabase session + PKCE), HistoryContext
│   ├── types/contracts.ts     # Canonical TypeScript types — MUST mirror backend
│   ├── constants/apiEndpoints.ts
│   └── theme/                 # Design tokens, typography, motion, scoreTier, useTokens
└── supabase/                  # SQL migration files (no Supabase CLI migrations yet)
```

### Request / job lifecycle

```
Upload → POST /mvp/analyze → asyncio semaphore (cap 8)
  → MVPJobService.queue_job_async
    → DurableJobStore (SQLite) upsert {status:queued}
    → asyncio.create_task(_process_video_job_async)
      → ProcessPoolExecutor._run_pipeline_sync
        → MVPPipeline.process_video (6 phases, ~15–40 s)
      → _enrich_with_gemini (10 s timeout)
      → DurableJobStore upsert {status:completed, payload}

Client polls GET /mvp/result/{job_id}
  → on completed: POST /api/analysis/complete (auth-gated)
    → SupabaseDB: sessions, videos, metrics, analysis_summaries, user_streaks
```

**Known race:** If the client crashes between the completion poll and `/api/analysis/complete`, the analysis is never persisted (SQLite job store expires at 72 h). Task 15 of the audit plan moves persist into the pipeline.

### Ground-truth locations

- **API contracts:** `src/types/contracts.ts` must mirror Pydantic models in `backend/routers/` + `backend/services/llm/output_schemas.py`.
- **Supabase schema:** `supabase/schema_complete.sql` is the canonical schema — includes all tables (`sessions`, `session_videos`, `video_metrics`, `analysis_summaries`, `chat_history`, `drill_completions`, `user_streaks`, `user_profiles`), RLS policies, indexes, and triggers. `supabase/schema.sql` is a legacy partial file; ignore it.
- **Biomechanics thresholds:** `backend/metrics/normative_ranges.json`. Scoring is a confidence-weighted geometric mean over per-joint angle deviations.
- **Per-run artifacts:** `backend/outputs/{run_id}/` (do not commit; runtime state).
- **Environment:** `SHOOTRZ/.env` (frontend, `EXPO_PUBLIC_*`) and `SHOOTRZ/backend/.env` (backend). `.env.example` files TBD.

### Core commands (run from `SHOOTRZ/`)

| Purpose | Command |
|---------|---------|
| Backend dev server | `python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000` |
| Mobile dev | `npm install` then `npm start` |
| Backend tests (all) | `python -m pytest backend/ -v --ignore=backend/__graveyard__` |
| Single backend test | `python -m pytest backend/tests/test_<name>.py -v` |
| Mobile unit tests | `npm test` |
| Mobile typecheck | `npx tsc --noEmit` |
| Mobile lint | `npx eslint src` |
| Health probe | `curl http://localhost:8000/health` |

### Environment variables

**Backend (`SHOOTRZ/backend/.env`):**
`SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL` (default `gemini-2.5-flash`), `GEMINI_TIMEOUT`, `GEMINI_MAX_RETRIES`, `SHOOTRZ_ENABLE_BALL` (opt-in YOLO), `SHOOTRZ_MAX_UPLOAD_MB`.

**Frontend (`SHOOTRZ/.env`):**
`EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY`, `EXPO_PUBLIC_API_URL`.

### Active initiatives

- **Production-readiness audit** — `docs/superpowers/plans/2026-04-23-production-readiness-audit.md`. Phase 1 focus: recommender signature bug (C-1), unauthenticated history/recommend/upload routes (C-2/C-3/C-5), upload size cap (H-1), print→logger (M-5), chat rate limiting (H-6).
- **Design-system v3 rollout** — `docs/superpowers/plans/2026-04-23-design-system-v3-rollout.md`. New tokens/typography/motion, FocusRing, buttonTokens, TextRole.

### Conventions worth respecting

- Keep targeted diffs; don't rewrite files wholesale.
- Python tests live in `backend/tests/` or a sibling `test_*.py` next to the module (e.g. `backend/recommender/test_recommend_service.py`). Check both patterns before creating a new test file.
- `__graveyard__/` is dead code kept locally for reference — never import from it; exclude it in greps and pytest runs.
- All Supabase writes go through `backend/storage/db.py` → `get_service_client()` (service_role, RLS-bypassing). The anon client (`get_anon_client`) is used only for JWT verification.
- Logging uses `logger = logging.getLogger(__name__)` with `extra={...}` kwargs. Do not use `print()` in production code.
- Always run backend commands from `SHOOTRZ/`, not the workspace root — the backend imports as `backend.*`.
