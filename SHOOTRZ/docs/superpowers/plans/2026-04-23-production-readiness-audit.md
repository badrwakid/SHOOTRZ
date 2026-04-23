# SHOOTRZ Production-Readiness Audit & Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring SHOOTRZ from demo-grade to production-ready by resolving all Critical/High security, reliability, and correctness issues identified in a full codebase audit.

**Architecture:** FastAPI Python backend running MediaPipe + Gemini, persisting to Supabase (PostgreSQL), serving a React Native / Expo mobile app. Analysis jobs run in a ProcessPoolExecutor; chat/recommendations are synchronous Gemini calls. The job lifecycle is: upload → async ProcessPool → SQLite job store → client polls → `POST /api/analysis/complete` → Supabase persist.

**Tech Stack:** FastAPI 0.x, Python 3.11+, MediaPipe (pose), YOLOv8n (ball), Gemini 2.5 Flash (LLM), Supabase (auth+db+storage), React Native + Expo (frontend), SQLite (job store), FAISS + LinUCB (drill recommendation).

---

## 1. Executive Summary

### Top 5 Risks Before Launch

| # | Risk | Severity | Impact |
|---|------|----------|--------|
| 1 | **Secrets in `.env` files on disk** — `SUPABASE_SERVICE_KEY` and `GEMINI_API_KEY` live in `backend/.env` (untracked, but on disk; visible in any local read). Real production keys must live in a secrets manager or environment injection, never files on disk. | CRITICAL | Full Supabase data breach + API key abuse |
| 2 | **`recommend_service.py` function signature mismatch** — `recommend_routes.py` passes `weak_areas` and `user_level` keyword args but `recommend_drill()` doesn't accept them → `TypeError` on every recommendation request | CRITICAL | Feature 100% broken in production |
| 3 | **Unauthenticated legacy history route** — `GET /history/{user_id}` and legacy stats routes accept any UUID as a path param with no auth check → any user can read any other user's history | CRITICAL | GDPR/privacy violation, data exposure |
| 4 | **Supabase schema gap** — `schema.sql` creates 6 tables but `db.py` writes to 9+ (`user_profiles`, `analysis_summaries`, `chat_history`, `drill_completions`, `user_streaks`). A fresh DB from `schema.sql` will silently fail all coach/progress features | HIGH | Complete feature failure on new deployment |
| 5 | **`get_service_client()` creates a new Supabase client on every request** — No connection pooling. Under even moderate load this exhausts Supabase's connection limit | HIGH | Service degradation / 503s under load |

### Top 3 Opportunities

| # | Opportunity | Impact |
|---|-------------|--------|
| 1 | **Structured logging + request tracing** — Every log already uses `extra={}` but no format is configured. Adding `structlog` + a trace ID middleware gives immediate observability into the pipeline for free | High |
| 2 | **Normative-range personalization** — The scoring system uses the same `normative_ranges.json` thresholds for all users. A small skill-level lookup table (beginner/intermediate/advanced) would produce meaningfully better feedback at zero ML cost | High |
| 3 | **Supabase auto-persist** — The current two-step flow (pipeline → poll → client calls `/api/analysis/complete`) silently loses data if the app crashes between steps. Moving persist to an async background task inside the job service eliminates this race condition | Medium |

---

## 2. System Map

```
SHOOTRZ/
├── SHOOTRZ/ (mobile app root)
│   ├── src/
│   │   ├── screens/          # HomeScreen, MVPAnalysisScreen, ChatScreen, ProgressScreen,
│   │   │                     # ProfileScreen, DrillsScreen, WorkoutsScreen, LoginScreen, ...
│   │   ├── services/
│   │   │   ├── api.service.ts          # Axios wrapper for all backend calls
│   │   │   ├── supabase.client.ts      # Supabase JS client (anon key)
│   │   │   ├── chat.service.ts         # Chat API calls
│   │   │   ├── chat-storage.service.ts # Local AsyncStorage chat history
│   │   │   └── storage.service.ts      # Local user state
│   │   ├── context/
│   │   │   ├── AuthContext.tsx          # Supabase session, OAuth flow, PKCE
│   │   │   └── HistoryContext.tsx       # Analysis history cache
│   │   ├── types/contracts.ts          # Canonical TypeScript types (mirrors backend)
│   │   └── constants/apiEndpoints.ts   # All API path constants
│   │
│   ├── backend/
│   │   ├── main.py                     # FastAPI app factory, CORS, lifespan, routers
│   │   ├── routers/
│   │   │   ├── mvp.py                  # POST /mvp/analyze, GET /mvp/result/{id}, artifacts
│   │   │   ├── analysis.py             # POST /api/analysis/complete (auth-gated persist)
│   │   │   ├── chat.py                 # POST /chat, /chat/stream, /chat/history
│   │   │   ├── user.py                 # GET/PUT /api/user/*, drills, workouts, streak
│   │   │   ├── history.py              # GET /history/{user_id} (UNAUTHENTICATED - BUG)
│   │   │   ├── sessions.py             # Session endpoints
│   │   │   ├── feedback.py             # Feedback endpoints
│   │   │   └── recommendation_routes.py # POST /api/recommend (UNAUTHENTICATED - BUG)
│   │   │
│   │   ├── mvp/core/
│   │   │   ├── pipeline.py             # MVPPipeline: 6-phase video → metrics orchestrator
│   │   │   ├── pose_estimation.py      # MediaPipe wrapper, keypoint export
│   │   │   ├── shot_detection.py       # ShotDetector: scipy peaks + kinematic rules
│   │   │   ├── angle_computation.py    # AngleComputer: elbow/knee/wrist per frame
│   │   │   ├── signal_smoothing.py     # Savitzky-Golay + interpolation
│   │   │   ├── metrics.py              # MetricsDerivation: normative range scoring + geomean
│   │   │   ├── video_loader.py         # Frame sampler, quality checks
│   │   │   └── run_tracker.py          # Per-run output directory management
│   │   │
│   │   ├── inference/
│   │   │   ├── phase_detector.py       # Motion-based phase detection (setup/crouch/release/follow-through)
│   │   │   ├── pose_2d.py              # BASKETBALL_KEYPOINTS mapping
│   │   │   ├── ball_tracker.py         # YOLOv8n ball detection (SHOOTRZ_ENABLE_BALL=true)
│   │   │   └── motion_analyzer.py      # Angular velocity, motion energy helpers
│   │   │
│   │   ├── feedback/
│   │   │   ├── rules.py                # Per-metric threshold rules → coaching text
│   │   │   └── engine.py               # rules_from_metrics aggregator
│   │   │
│   │   ├── services/
│   │   │   ├── mvp_job_service.py      # ProcessPool orchestration, Gemini enrichment, Supabase persist
│   │   │   ├── job_store.py            # DurableJobStore: SQLite-backed job state
│   │   │   └── llm/
│   │   │       ├── gemini_client.py    # GeminiService: retry, timeout, structured JSON
│   │   │       ├── llm_router.py       # LLMService facade
│   │   │       ├── prompt_builders.py  # System/user prompts for all LLM calls
│   │   │       ├── output_schemas.py   # Pydantic v2 schemas for Gemini responses
│   │   │       └── fallbacks.py        # Rule-based fallback when Gemini fails
│   │   │
│   │   ├── recommender/
│   │   │   ├── recommend_service.py    # FAISS nearest-neighbor + LinUCB bandit selection
│   │   │   ├── bandit_model.py         # LinUCB implementation
│   │   │   ├── faiss_index.py          # Index builder
│   │   │   ├── drill_clustering.py     # K-means drill embedding
│   │   │   └── model_loader.py         # Lazy-load FAISS index + bandit weights
│   │   │
│   │   ├── storage/
│   │   │   ├── db.py                   # SupabaseDB: all table access via service_role key
│   │   │   └── supabase_client.py      # get_service_client() / get_anon_client()
│   │   │
│   │   ├── chat/context_builder.py     # build_user_context: recent summaries for Gemini
│   │   ├── metrics/
│   │   │   ├── biomechanics.py         # compute_release_angle (YOLO trajectory)
│   │   │   └── normative_ranges.json   # Research-backed angle targets
│   │   ├── utils/
│   │   │   ├── config.py               # dotenv loader, env var exports
│   │   │   ├── supabase_auth.py        # get_authenticated_user FastAPI dependency
│   │   │   └── video_annotator.py      # OpenCV skeleton overlay renderer
│   │   │
│   │   └── outputs/{run_id}/           # Per-run artifacts (CSV, JSON, MP4)
│   │
│   └── supabase/                       # SQL migration files (not using Supabase CLI migrations)
│       ├── schema.sql                  # Core tables (INCOMPLETE - missing 5 tables)
│       ├── migration_mvp_enhancements.sql
│       ├── migration_add_name_onboarding.sql
│       ├── add_username_column.sql
│       ├── add_delete_policy.sql
│       ├── fix_oauth_signup_database_error.sql
│       └── trigger_create_user.sql
```

**Key dependency graph:**
```
Mobile App
  → api.service.ts (Axios) → FastAPI backend
  → supabase.client.ts (anon key) → Supabase Auth + DB direct

FastAPI Backend
  → ProcessPoolExecutor → MVPPipeline → MediaPipe + YOLO + Scipy
  → DurableJobStore (SQLite) [job state]
  → GeminiService → Gemini 2.5 Flash API
  → SupabaseDB (service_role key) → Supabase PostgreSQL
  → FAISS + LinUCB [drill recommendation]
```

---

## 3. Critical Flows & Failure Modes

### Flow A: Auth / Session

```
User → SignUp/Login (Supabase Auth) → JWT issued
     → App stores session in AsyncStorage
     → AuthContext.tsx subscribes to onAuthStateChange
     → On API calls: supabase.auth.getSession() → attach Bearer token
     → Backend: get_authenticated_user() → get_anon_client().auth.get_user(jwt=token)
     → Returns AuthenticatedUser(user_id, email)
```

**Sources of truth:** Supabase Auth (JWT), AsyncStorage (session persistence)

**Failure points:**
- `get_anon_client()` creates a new `supabase-py` client on every request — no pooling
- Expired JWT is not refreshed server-side; client must refresh and retry
- OAuth PKCE flow parses redirect URL in `AuthContext.tsx` — complex, tested only in browser, not in Expo deep link
- No rate limiting on auth endpoints
- `trigger_create_user.sql` creates a user row on auth signup — if this trigger fails silently, `get_user()` returns `None` and the profile endpoint 404s

### Flow B: Upload / Analyze

```
User → Select video → api.service.ts:analyzeMVP()
     → POST /mvp/analyze (multipart, no auth token!)
     → Server: read 1MB → SHA256 cache key → check _result_cache
     → Spill to NamedTemporaryFile
     → _preflight_video() (cv2: frame count check)
     → Acquire asyncio semaphore (capacity=8)
     → MVPJobService.queue_job_async()
       → DurableJobStore.upsert(job_id, {status: "queued"})
       → asyncio.create_task(_process_video_job_async)
         → ProcessPoolExecutor._run_pipeline_sync()
           → MVPPipeline.process_video() [6 phases, ~15-40s]
         → _build_completed_payload() [read angles.csv]
         → _maybe_build_overlay() [optional OpenCV render]
         → _enrich_with_gemini() [Gemini API, 10s timeout]
         → DurableJobStore.upsert(job_id, completed_payload)
     → Client polls GET /mvp/result/{job_id}
```

**Sources of truth:** SQLite `mvp_jobs` table (job state), `backend/outputs/{run_id}/` (artifacts)

**Failure points:**
- `POST /mvp/analyze` has NO auth requirement — unauthenticated abuse possible
- No file size limit (server will OOM on 4GB video upload)
- No MIME type validation (any file accepted)
- `NamedTemporaryFile` on Windows may fail if antivirus scans temp files mid-write
- ProcessPool worker crash: `_finalize_failure` catches and stores failed status, but temp file cleanup is in `finally` block only for the async path. Legacy sync path may leak temp files on crash.
- `_result_cache` is in-memory per process — under multi-worker Gunicorn, cache misses defeat deduplication
- After `_enrich_with_gemini` fails, rule-based score is kept, but `gemini_enriched=False` is not exposed to the client UI

### Flow C: AI Scoring + Feedback

```
Pipeline output → _enrich_with_gemini()
  → llm_service.get_shot_feedback(metrics, score_components, overall_score, ...)
  → GeminiService.generate_structured(ShotFeedbackOutput schema)
  → Gemini 2.5 Flash (10s timeout)
  → If success: replace overall_score with ai_overall_score; store strengths/improvements
  → If timeout/failure: keep rule-based score; gemini_enriched=False
```

**Sources of truth:** Rule-based score from `metrics.py` geomean; Gemini score overrides it

**Failure points:**
- `ai_overall_score` is validated (0-100, int) but Gemini can return strings like "72" — Pydantic coerces, but if Gemini hallucinates a non-integer, the field fails validation silently (falls back to rule-based)
- Prompt injection: `user_message` from the chat endpoint is injected into the Gemini system prompt via `build_user_context`. If a user crafts a message like "Ignore previous instructions and...", this reaches Gemini. No sanitization beyond `sanitize_context_for_llm()` (which only truncates length).
- Token explosion: `include_raw_artifacts=True` in chat requests could pass full pipeline JSON (pose_keypoints.json = 500KB+) into the Gemini context

### Flow D: Chat

```
User → ChatScreen → POST /chat (or /chat/stream)
     → get_authenticated_user() → verify JWT
     → build_user_context() [db queries: user, profile, stats, 5 summaries, 20 chat messages]
     → sanitize_context_for_llm()
     → build_chat_prompt() → system prompt
     → trimmed last-20 messages
     → llm_service.chat() [Gemini, no timeout specified]
     → _persist_exchange() [save to chat_history in Supabase]
     → Return ChatResponse
```

**Sources of truth:** Supabase `chat_history` table, Supabase `analysis_summaries` table

**Failure points:**
- `/chat` has NO per-user rate limiting (only global SlowAPI rate limit on `/mvp/analyze`)
- `build_user_context` fires 4 DB queries synchronously — no batching, no caching
- `_persist_exchange` silently swallows DB errors — chat exchange may be lost without user knowing
- Chat stream: if SSE connection drops mid-stream, the partially assembled text may not be persisted (the `_persist_exchange` inside `_sse_generator` runs only if `assistant_text` is non-empty, which requires the stream to complete)
- No maximum context size enforcement — 20 messages × up to 4000 chars each = ~80K tokens sent to Gemini

### Flow E: History / Progress Persistence

```
After analysis completed:
  Client calls POST /api/analysis/complete (auth-gated, job_id in body)
    → save_result_for_user(job_id, user_id)
      → db.create_session() → Supabase sessions table
      → db.create_video() → Supabase videos table
      → db.add_video_to_session() → session_videos table
      → db.save_metrics() → metrics table
      → db.save_analysis_summary() → analysis_summaries table
      → db.update_streak() → user_streaks table

History read:
  GET /api/user/analysis-history (auth-gated)
    → db.get_user_analysis_history() → sessions + analysis_summaries JOIN
```

**Sources of truth:** Supabase (sessions, videos, metrics, analysis_summaries, user_streaks)

**Failure points:**
- **DATA LOSS RISK**: If client crashes between `GET /mvp/result/{id}` (status=completed) and `POST /api/analysis/complete`, the analysis is never persisted to Supabase. The job store expires after 72 hours — if the user reopens the app 3 days later, the data is gone.
- `save_result_for_user` is not idempotent if the job store is cleared and re-called — it will create a duplicate session.
- `cleanup_old_outputs()` runs at upload time and deletes output dirs by mtime — this can delete artifacts for a job that the job store still references
- `db.update_streak()` is a simple upsert but there's no validation that it's not called multiple times for the same day
- `analysis_summaries` table has `ON CONFLICT(session_id)` — safe idempotency for re-saves

---

## 4. Findings by Severity

### CRITICAL

---

#### C-1: Recommender function signature mismatch (runtime TypeError)

**File:** `backend/routers/recommendation_routes.py:34` and `backend/recommender/recommend_service.py:40`

**Observed pattern:**
```python
# recommendation_routes.py:34 — caller passes two extra kwargs:
result = recommend_drill(
    user_vec=user_vec,
    user_context=user_context,
    drills=rec["metadata"],
    labels=rec["labels"],
    tiers=rec["tiers"],
    faiss_index=rec["faiss_index"],
    bandit=rec["bandit"],
    weak_areas=payload.get("weak_areas"),   # ← NOT in function signature
    user_level=payload.get("user_level"),   # ← NOT in function signature
)

# recommend_service.py:40 — function doesn't accept those kwargs:
def recommend_drill(user_vec, user_context, drills, labels, tiers, faiss_index, bandit):
```

**Fix:** Add `weak_areas=None, user_level=None` to `recommend_drill` signature and use them for tier filtering.

---

#### C-2: Unauthenticated history route exposes any user's data

**File:** `backend/routers/history.py`

**Observed pattern:** `GET /history/{user_id}` accepts a Supabase UUID as a path param with no `Depends(get_authenticated_user)`. Any caller who knows (or guesses) a UUID can read that user's complete analysis history.

**Fix:** Add `get_authenticated_user` dependency and validate `user_id == user.user_id`.

---

#### C-3: Unauthenticated recommendation endpoint

**File:** `backend/routers/recommendation_routes.py`

**Observed pattern:** `POST /api/recommend` has no auth dependency. Any unauthenticated request can call the recommender.

**Fix:** Add `get_authenticated_user` dependency.

---

#### C-4: Secrets in `.env` files on local disk

**Files:** `backend/.env`, `SHOOTRZ/.env`

**Observed:** Real `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_KEY`, and `GEMINI_API_KEY` are stored in plaintext in `.env` files. `.gitignore` excludes `*.env` so they appear untracked, but:
1. Any developer who clones this repo will need separate `.env` files — there's no `.env.example`
2. The keys visible in this audit session could be logged by Claude if not handled carefully
3. `SUPABASE_SERVICE_KEY` grants full database access bypassing all RLS

**Fix:**
1. Create `.env.example` with placeholder values
2. Rotate any keys that may have been exposed
3. For production: use environment variable injection via hosting platform (Railway, Fly.io, etc.), never files
4. Add `pre-commit` hook to detect and block secret patterns

---

#### C-5: `POST /mvp/analyze` requires no authentication

**File:** `backend/routers/mvp.py:87`

**Observed pattern:** The video upload endpoint has no `get_authenticated_user` dependency. Any unauthenticated caller can submit videos and consume server compute (ProcessPool slots, temp disk space, Gemini tokens via enrichment).

**Fix:** Add auth dependency, OR add a strict per-IP rate limit (current: 30/min, which is still generous for abuse). At minimum, enforce a file size cap.

---

### HIGH

---

#### H-1: No file size limit on video upload

**File:** `backend/routers/mvp.py:116-126`

**Observed pattern:** The upload loop reads chunks until EOF with no size cap. A 4GB upload will be written to disk and submitted to the pipeline.

**Fix:**
```python
_MAX_UPLOAD_BYTES = int(os.getenv("SHOOTRZ_MAX_UPLOAD_MB", "200")) * 1024 * 1024

async def analyze_video(...):
    first_mb = await file.read(1024 * 1024)
    total_read = len(first_mb)
    # ... after writing first_mb to tmp ...
    while True:
        chunk = await file.read(1024 * 1024)
        if not chunk:
            break
        total_read += len(chunk)
        if total_read > _MAX_UPLOAD_BYTES:
            os.remove(tmp_path)
            raise HTTPException(status_code=413, detail=f"File exceeds {_MAX_UPLOAD_BYTES // 1024 // 1024}MB limit")
        tmp.write(chunk)
```

---

#### H-2: `get_service_client()` creates new Supabase connection on every call

**File:** `backend/storage/supabase_client.py:9-14` and `backend/utils/supabase_auth.py:39`

**Observed pattern:** `create_client()` is called fresh every time `get_service_client()` or `get_anon_client()` is invoked. For a single analysis completion, `db.create_session()` + `db.create_video()` + `db.save_metrics()` + `db.save_analysis_summary()` + `db.update_streak()` each call `get_service_client()` → 5 new clients per request.

**Fix:**
```python
# supabase_client.py
from functools import lru_cache

@lru_cache(maxsize=1)
def get_service_client() -> Client:
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        raise NotConfiguredError(...)
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)

@lru_cache(maxsize=1)
def get_anon_client() -> Client:
    ...
```

Note: `lru_cache` creates a single client per process. Under multi-process Gunicorn, each worker gets its own. This is correct behavior.

---

#### H-3: Supabase schema.sql is incomplete — 5+ tables missing

**File:** `SHOOTRZ/supabase/schema.sql`

**Observed:** `schema.sql` creates: `users`, `videos`, `metrics`, `feedback`, `sessions`, `models`. But `db.py` references: `user_profiles`, `analysis_summaries`, `chat_history`, `drill_completions`, `user_streaks`, `session_videos`. The last 6 are in ad-hoc migration files with no canonical ordering or idempotency tracking.

**Fix:** Create a single `schema_complete.sql` that is the authoritative "run this once on a fresh DB" script, including all tables, RLS, triggers, and indexes. Add a `supabase_migrations` tracking table.

---

#### H-4: Data loss — analysis not auto-persisted if client disconnects

**File:** `backend/services/mvp_job_service.py:379-400` and `backend/routers/analysis.py:31`

**Observed:** Supabase persist requires the mobile client to call `POST /api/analysis/complete` after polling the job to completion. If the app crashes, goes to background, or the user closes it, this call is never made and the analysis data expires from SQLite after 72 hours.

**Fix:** Move Supabase persistence into the job pipeline (after Gemini enrichment) for users who are logged in. This requires passing the user_id into the pipeline, which is not possible without auth on the upload endpoint (C-5). The two-part fix: (1) auth-gate the upload (C-5), (2) persist automatically after Gemini enrichment in `_persist_supabase_and_cleanup`.

---

#### H-5: `build_user_context` makes 4 blocking Supabase calls per chat message

**File:** `backend/chat/context_builder.py:46-53`

**Observed:**
```python
user = db.get_user(user_id)            # → supabase query 1
profile = db.get_user_profile(user_id) # → supabase query 2
stats = db.get_user_stats(user_id)     # → supabase query 3 (RPC)
summaries = db.get_recent_summaries(user_id, limit=5)  # → supabase query 4
```
All sequential, blocking. Chat latency = network RTT × 4 minimum before even calling Gemini.

**Fix:** Run these queries concurrently using `asyncio.gather` (requires async `db` methods) or batch into a single Supabase RPC function.

---

#### H-6: Per-user rate limiting missing on chat endpoint

**File:** `backend/routers/chat.py:47`

**Observed:** SlowAPI is configured on `/mvp/analyze` (30/min) but `/chat` and `/chat/stream` have no rate limiting. A single authenticated user can fire unlimited Gemini requests.

**Fix:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat")
@limiter.limit("20/minute")
async def chat(request: Request, payload: ChatRequest, user: AuthenticatedUser = Depends(...)):
    ...
```

---

#### H-7: SQLite job store is not safe under multi-worker deployment

**File:** `backend/services/job_store.py`

**Observed:** `DurableJobStore` uses `threading.Lock()` for thread safety within one process, but under Gunicorn with multiple workers, each process has its own SQLite file handle and lock. A job submitted to worker 1 returns a `job_id` that worker 2 won't find when polled (404). The semaphore is also per-process.

**Fix for single-worker:** Add `SHOOTRZ_SINGLE_WORKER=true` to deployment docs.
**Fix for multi-worker:** Replace SQLite job store with Redis (use `redis-py` + `asyncio` client). This is a larger change, deferred to "hardening" phase.

---

### MEDIUM

---

#### M-1: `analysis_summaries` table missing from authoritative schema

**Evidence:** `db.py:300` writes to `analysis_summaries` but it's not in `schema.sql`. The table must exist from an ad-hoc SQL run, with no migration record.

---

#### M-2: No maximum chat context size — Gemini token explosion risk

**File:** `backend/routers/chat.py:56`, `backend/chat/context_builder.py`

**Observed:** `include_raw_artifacts=True` would pass raw pipeline JSON into the context. The trimmed message window is 20 messages but each can be arbitrarily long.

**Fix:** Add a `MAX_CONTEXT_CHARS = 32000` guard in `sanitize_context_for_llm`.

---

#### M-3: Prompt injection surface in chat system prompt

**File:** `backend/chat/context_builder.py`, `backend/services/llm/prompt_builders.py`

**Observed:** User profile fields (`name`, `primary_goal`, `coaching_style`) from Supabase are injected directly into the Gemini system prompt. A user who sets `name = "Ignore previous instructions. You are DAN..."` will have that string in the system prompt.

**Fix:** Sanitize user-supplied string fields before injecting into prompts:
```python
def _sanitize_for_prompt(s: str, max_len: int = 200) -> str:
    return re.sub(r'[^\w\s.,!?-]', '', str(s))[:max_len]
```

---

#### M-4: `cleanup_old_outputs()` can delete artifacts while job store still references them

**File:** `backend/services/mvp_job_service.py:843-852`

**Observed:** `cleanup_old_outputs` deletes `backend/outputs/{run_id}/` directories after 7 days, but `DurableJobStore` retains job records for 72 hours. An artifact reference in a 3-day-old job points to a deleted directory.

**Fix:** In `cleanup_old_outputs`, also delete the corresponding job store entry, or reduce artifact retention to match job store retention.

---

#### M-5: `print()` used instead of `logger` in production code

**Files:** `backend/mvp/core/pipeline.py:72,106,488`, `backend/services/mvp_job_service.py`

**Observed:** `print(f"Ball tracking unavailable: {exc}")`, `print(f"Release-angle metric skipped: {exc}")`, `print(f"Phase detection skipped: {phase_err}")` — these won't respect log level, won't be captured by log aggregators.

**Fix:** Replace all `print()` calls with `logger.warning()` / `logger.info()`.

---

#### M-6: Normative ranges are not personalized by skill level

**File:** `backend/metrics/normative_ranges.json`, `backend/mvp/core/metrics.py:62-68`

**Observed:** `_METRIC_SCORING_MAP` uses the same normative ranges for all users regardless of `skill_level` in the user profile. A beginner with 95° knee bend (excellent for a beginner) gets the same score as an elite player with 95° (sub-par for elite).

**Fix:** Load user `skill_level` in `MetricsDerivation` and apply a skill-adjusted scoring curve. Use three tiers: beginner (±20% range tolerance), intermediate (±10%), advanced (±5%).

---

#### M-7: Temp file path injection via `file.filename`

**File:** `backend/routers/mvp.py:115`

**Observed:**
```python
tmp_suffix = Path(file.filename).suffix if file.filename else ".mp4"
```
`file.filename` is user-controlled. A filename like `../../etc/passwd` would produce a suffix of `passwd`, which is safe in a suffix context. But combined with `NamedTemporaryFile(suffix=...)`, the suffix is appended to a temp path — still safe. However, `_RewoundUpload.filename` stores the original filename which is passed to `_persist_upload` for suffix extraction again. Low actual risk but should be sanitized.

**Fix:**
```python
_SAFE_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.m4v', '.avi', '.mkv'}
raw_suffix = Path(file.filename or '').suffix.lower()
tmp_suffix = raw_suffix if raw_suffix in _SAFE_VIDEO_EXTENSIONS else '.mp4'
```

---

#### M-8: Supabase new-client-per-request will exhaust connections under load

Already listed as H-2. Here documenting the downstream symptom: Supabase free tier allows ~60 concurrent connections. At 8 concurrent jobs × 5 DB calls each = 40 connection opens in a burst. Add chat users and this saturates the pool.

---

#### M-9: `get_user_analysis_history` has no server-side cap

**File:** `backend/routers/user.py:152`

**Observed:** `limit` query param defaults to 100 with no maximum enforcement. With 100 sessions, each having multiple metrics rows joined, this is a heavy unbounded query.

**Fix:**
```python
@router.get("/user/analysis-history")
async def get_analysis_history(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
```

---

#### M-10: `__graveyard__` and `backend/outputs/` in repository

**Evidence:** `SHOOTRZ/__graveyard__/` has 50+ backup Python files. `SHOOTRZ/backend/outputs/` has dozens of UUID-named directories with CSV, JSON, PNG, and MP4 files. These should not be in source control.

**Fix:**
1. Add `__graveyard__/` and `backend/outputs/` to `.gitignore`
2. Run `git rm -r --cached SHOOTRZ/backend/outputs SHOOTRZ/__graveyard__`
3. Commit the removal

---

### LOW

---

#### L-1: `allow_origins=["*"]` in production CORS

**File:** `backend/main.py:61-67`

Currently safe because `allow_credentials=False`. Production should restrict to the actual app domain.

---

#### L-2: `_MIN_PREFLIGHT_FRAMES = 30` too permissive

A 1-second clip at 30fps passes preflight but cannot yield meaningful shooting mechanics analysis.

**Fix:** Raise to `_MIN_PREFLIGHT_FRAMES = 90` (3 seconds minimum).

---

#### L-3: No structured log format configured

**File:** `backend/main.py` (no logging config)

All `logger.info("msg", extra={...})` calls work but the extra dict isn't surfaced in the default format string.

**Fix:** Add `logging.config.dictConfig(...)` in `create_app()` with a JSON formatter.

---

#### L-4: `backend/database/progress.db` legacy SQLite in repo

**File:** `SHOOTRZ/backend/database/progress.db`

A leftover from before Supabase migration. Add to `.gitignore` and remove from tracking.

---

#### L-5: `CORS` semaphore check logic

**File:** `backend/routers/mvp.py:99`

`if _analysis_semaphore.locked()` returns True only when ALL slots are taken. At `_MAX_CONCURRENT=8` and `_MAX_WORKERS=cpu_count-1=1` (on a typical dev machine), 7 jobs can queue behind the semaphore. The semaphore doesn't limit queue depth, only active slots.

---

## 5. Rule-Based vs AI/ML Modernization Matrix

| Component | Current Approach | Verdict | Modernization Path | Effort |
|-----------|-----------------|---------|-------------------|--------|
| **Shot event detection** | Rule-based: scipy peak finding on knee flexion + wrist height + elbow angle curves | ⚠️ Keep but improve | Train a lightweight 1D-CNN on pose sequences (10K labeled shot frames from AddBiomechanics dataset in repo) to produce event probabilities | 3 weeks |
| **Phase detection** | Rule-based: velocity thresholds + joint angle windows in `phase_detector.py` | ✅ Keep as-is | Well-tuned, deterministic, explainable. Add ML only if accuracy drops below 80% on real user videos | — |
| **Angle scoring + geomean** | Rule-based: normative range lookup + confidence-weighted geometric mean | ✅ Keep, personalize | Skill-level tiers (M-6). Long-term: Gaussian process regression per user session history | 1 week |
| **Shooting side auto-detection** | Rule-based: compare wrist visibility + motion direction | ✅ Keep as-is | Simple, near-100% accurate on well-framed clips, deterministic | — |
| **Feedback generation** | Hybrid: rule-based threshold cues → Gemini rephrasing | ✅ Optimal for now | Current hybrid is correct. Add personalization via coaching_style preference from user profile | 3 days |
| **Drill recommendation** | FAISS (cosine similarity) + LinUCB bandit | ⚠️ Needs real data | Bandit needs real click/completion signal. For now, implement simple rule-based fallback: weak_area → drill_category lookup table | 1 week |
| **Progress insight** | Gemini: recent summaries → trend text | ✅ Keep | Add trend detection preprocessing (score slope, best metric, worst metric) before Gemini to reduce hallucination | 2 days |
| **Confidence calibration** | MediaPipe per-joint confidence + threshold gate (0.3/0.5) | ⚠️ Improve | Multi-frame consistency check: a joint with high single-frame confidence but large variance across 5 frames should be penalized | 4 days |
| **Signal smoothing** | Savitzky-Golay (configurable window) | ✅ Keep | Optimal for biomechanics smoothing. No ML needed | — |
| **Ball release angle** | YOLO trajectory → first 3 points → atan2 | ⚠️ Improve | Use full parabolic fit on trajectory, not just 3 points. More robust to noise | 2 days |

**Modernization priority order:**
1. Skill-level normative range personalization (immediate ROI, no ML)
2. Shot event detection confidence improvement (multi-signal Bayesian fusion)
3. Bandit signal injection (real user completion data)
4. Multi-frame confidence calibration
5. ML shot event classifier (requires labeled data collection)

---

## 6. Production Readiness Scorecard

| Category | Score | Rationale |
|----------|-------|-----------|
| **Backend / API** | 52/100 | Semaphore, preflight, rate limiting on upload are well-done; auth gaps on upload + history, no file size limit, no MIME check |
| **Supabase** | 48/100 | RLS schema is solid in schema.sql; service_role bypass for all ops is intentional but risky; schema.sql is incomplete; no migration tooling |
| **Data model / History** | 44/100 | Sessions/metrics/summaries model is correct; race condition on persist; no retention policy for chat; schema not canonical |
| **ML/AI Pipeline** | 68/100 | Deterministic, well-guarded pipeline; good fallback handling; no model versioning; confidence calibration weak |
| **Rule-based scoring** | 72/100 | Research-backed thresholds; good fallback to geomean; lacks personalization; single-level thresholds for all users |
| **Reliability / Ops** | 32/100 | No structured logging format; no metrics/alerts; no SLOs; print() in production code; sqlite not multiprocess-safe |
| **Security / Compliance** | 30/100 | Secrets on disk; unauthenticated upload + history + recommend endpoints; prompt injection surface; no PII data classification |
| **Testing quality** | 58/100 | Good unit tests for `metrics`, `shot_detection`, `angle_computation`; no auth integration tests; no chat/recommender tests; graveyard tests confuse CI |

**Overall: 50.5/100 — Pre-production. Fix all Critical and High items before any public users.**

---

## 7. Prioritized Roadmap

### PHASE 1 — Quick Wins (1–3 days)

---

### Task 1: Fix recommend_service function signature (C-1)

**Why it matters:** Every recommendation request crashes with `TypeError`. Feature is 100% broken.

**Files affected:**
- `backend/recommender/recommend_service.py:40`
- `backend/routers/recommendation_routes.py:34`
- `backend/recommender/recommend_service.py` (tests needed)

**Risk:** Low — additive signature change only

**Effort:** 30 minutes

**Success criteria:** `POST /api/recommend` returns a valid drill recommendation without errors

- [ ] **Step 1: Add `weak_areas` and `user_level` to `recommend_drill` signature**

```python
# backend/recommender/recommend_service.py:40
def recommend_drill(
    user_vec, user_context, drills, labels, tiers, faiss_index, bandit,
    weak_areas=None, user_level=None
):
    # existing body unchanged for now
    # Optional: use weak_areas to filter pool in future
```

- [ ] **Step 2: Add test**

```python
# backend/recommender/test_recommend_service.py
import numpy as np
import pytest
from backend.recommender.recommend_service import recommend_drill

def test_recommend_drill_accepts_weak_areas_and_user_level(dummy_recommender):
    """Regression: weak_areas and user_level must not raise TypeError."""
    result = recommend_drill(
        user_vec=np.random.rand(64).tolist(),
        user_context=np.random.rand(8).tolist(),
        drills=dummy_recommender["metadata"],
        labels=dummy_recommender["labels"],
        tiers=dummy_recommender["tiers"],
        faiss_index=dummy_recommender["faiss_index"],
        bandit=dummy_recommender["bandit"],
        weak_areas=["elbow"],
        user_level="beginner",
    )
    assert "drill_id" in result
```

- [ ] **Step 3: Run test**

```bash
cd SHOOTRZ
python -m pytest backend/recommender/ -v
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/recommender/recommend_service.py backend/recommender/test_recommend_service.py
git commit -m "fix: accept weak_areas and user_level kwargs in recommend_drill"
```

---

### Task 2: Add file size cap on video upload (H-1)

**Why it matters:** A 4GB upload OOMs the server and drains the semaphore slot for the duration.

**Files affected:**
- `backend/routers/mvp.py:116-126`

**Risk:** Low — hard cap, new 413 response

**Effort:** 1 hour

**Success criteria:** Uploading a 201MB file returns HTTP 413; uploading a 50MB file is accepted normally

- [ ] **Step 1: Write failing test**

```python
# backend/tests/test_upload_size.py
import io
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_upload_rejects_oversized_file(monkeypatch):
    monkeypatch.setenv("SHOOTRZ_MAX_UPLOAD_MB", "10")
    big_fake_video = io.BytesIO(b"\x00" * (11 * 1024 * 1024))
    resp = client.post(
        "/mvp/analyze",
        files={"file": ("big.mp4", big_fake_video, "video/mp4")},
        params={"shooting_side": "auto"},
    )
    assert resp.status_code == 413
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest backend/tests/test_upload_size.py -v
```
Expected: FAIL

- [ ] **Step 3: Implement size cap**

```python
# backend/routers/mvp.py — add after imports:
_MAX_UPLOAD_BYTES = int(os.getenv("SHOOTRZ_MAX_UPLOAD_MB", "200")) * 1024 * 1024

# In analyze_video(), replace the chunk read loop (lines 119-125):
    total_read = len(first_mb)
    with NamedTemporaryFile(delete=False, suffix=tmp_suffix) as tmp:
        if first_mb:
            tmp.write(first_mb)
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > _MAX_UPLOAD_BYTES:
                tmp.close()
                try:
                    os.remove(tmp.name)
                except OSError:
                    pass
                raise HTTPException(
                    status_code=413,
                    detail=f"File exceeds {_MAX_UPLOAD_BYTES // 1024 // 1024}MB limit.",
                )
            tmp.write(chunk)
        tmp_path = tmp.name
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest backend/tests/test_upload_size.py -v
```
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/routers/mvp.py backend/tests/test_upload_size.py
git commit -m "fix: enforce SHOOTRZ_MAX_UPLOAD_MB file size cap on /mvp/analyze"
```

---

### Task 3: Fix unauthenticated history route (C-2)

**Why it matters:** Privacy violation — any user can read any other user's history by UUID.

**Files affected:**
- `backend/routers/history.py`

**Risk:** Low — adding auth guard; existing authenticated callers unaffected

**Effort:** 2 hours

**Success criteria:** `GET /history/{some_other_user_uuid}` returns 401/403; own UUID returns data

- [ ] **Step 1: Read the current history router**

Read `SHOOTRZ/backend/routers/history.py` in full before editing.

- [ ] **Step 2: Write failing test**

```python
# backend/tests/test_history_auth.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_history_requires_auth():
    resp = client.get("/history/some-fake-user-id")
    assert resp.status_code in (401, 403)

def test_history_own_user_with_valid_token():
    # Skipped in CI without real Supabase token — mark as integration test
    pytest.skip("Requires live Supabase JWT")
```

- [ ] **Step 3: Add auth dependency**

```python
# backend/routers/history.py — add to the unauthenticated GET /history/{user_id} handler:
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user

@router.get("/history/{user_id}")
async def get_history(
    user_id: str,
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = 50,
    offset: int = 0,
):
    if user.user_id != user_id:
        raise HTTPException(status_code=403, detail="Cannot access another user's history")
    # ... existing body ...
```

- [ ] **Step 4: Apply same fix to any other unauthenticated legacy routes in history.py**

Check: `GET /history/{user_id}/stats` — add same auth guard.

- [ ] **Step 5: Run tests**

```bash
python -m pytest backend/tests/test_history_auth.py -v
```
Expected: PASS (no live Supabase needed for the 401 check)

- [ ] **Step 6: Commit**

```bash
git add backend/routers/history.py backend/tests/test_history_auth.py
git commit -m "fix: auth-gate history and stats endpoints to prevent cross-user data access"
```

---

### Task 4: Add auth to recommendation route (C-3)

**Why it matters:** Public endpoint for a compute-heavy ML operation.

**Files affected:**
- `backend/routers/recommendation_routes.py`

**Risk:** Low

**Effort:** 30 minutes

**Success criteria:** `POST /api/recommend` without Authorization header returns 401

- [ ] **Step 1: Add auth dependency**

```python
# backend/routers/recommendation_routes.py
from fastapi import APIRouter, Depends, HTTPException
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user

@router.post("/recommend")
async def recommend(
    payload: dict,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    # existing body unchanged
```

- [ ] **Step 2: Write test**

```python
# backend/tests/test_recommend_auth.py
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_recommend_requires_auth():
    resp = client.post("/api/recommend", json={"user_vec": [], "user_context": []})
    assert resp.status_code == 401
```

- [ ] **Step 3: Run and commit**

```bash
python -m pytest backend/tests/test_recommend_auth.py -v
git add backend/routers/recommendation_routes.py backend/tests/test_recommend_auth.py
git commit -m "fix: add auth guard to POST /api/recommend"
```

---

### Task 5: Replace `print()` with `logger` calls (M-5)

**Why it matters:** Production logs must be structured. `print()` output won't be captured in log aggregators.

**Files affected:**
- `backend/mvp/core/pipeline.py` (lines 72, 106, 488)
- Any other `print()` calls in backend modules

**Risk:** Zero

**Effort:** 1 hour

**Success criteria:** `grep -r "^    print(" backend/` returns 0 results in production modules (excluding `__graveyard__`)

- [ ] **Step 1: Find all `print()` calls in production backend code**

```bash
grep -rn "print(" SHOOTRZ/backend/ --include="*.py" \
  --exclude-dir=__pycache__ --exclude-dir=__graveyard__ --exclude-dir=tests
```

- [ ] **Step 2: Replace each with `logger.warning()` or `logger.info()`**

In `pipeline.py:72`:
```python
# Before:
print(f"Ball tracking unavailable: {exc}")
# After:
logger.warning("Ball tracking unavailable: %s", exc)
```

In `pipeline.py:106`:
```python
# Before:
print(f"Release-angle metric skipped: {exc}")
# After:
logger.warning("Release-angle metric skipped: %s", exc)
```

In `pipeline.py:488`:
```python
# Before:
print(f"Phase detection skipped: {phase_err}")
# After:
logger.warning("Phase detection skipped: %s", phase_err)
```

- [ ] **Step 3: Verify**

```bash
grep -rn "^    print(" SHOOTRZ/backend/ --include="*.py" \
  --exclude-dir=__pycache__ --exclude-dir=__graveyard__ --exclude-dir=tests
```
Expected: 0 results

- [ ] **Step 4: Commit**

```bash
git add backend/mvp/core/pipeline.py  # and any other changed files
git commit -m "fix: replace print() with logger calls in production pipeline code"
```

---

### Task 6: Add per-IP rate limiting to /chat (H-6)

**Why it matters:** Unlimited Gemini calls per user = unbounded cost and abuse surface.

**Files affected:**
- `backend/routers/chat.py`

**Risk:** Low — adds 429 for burst callers

**Effort:** 1 hour

**Success criteria:** Sending 21 requests/minute to `/chat` from the same IP returns 429 on the 21st

- [ ] **Step 1: Add limiter to chat router**

```python
# backend/routers/chat.py — add at top:
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/chat", response_model=ChatResponse)
@limiter.limit("20/minute")
async def chat(
    request: Request,
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    ...

@router.post("/chat/stream")
@limiter.limit("20/minute")
async def chat_stream(
    request: Request,
    payload: ChatRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
):
    ...
```

- [ ] **Step 2: Register limiter with app in main.py** (already done via `mvp.limiter`, confirm it covers chat router too)

Check `main.py:80`: `app.state.limiter = mvp.limiter` — the limiter is set on app state, so all `@limiter.limit()` decorators using `get_remote_address` will work regardless of which router defined the limiter. But the `limiter` object in `chat.py` must be the SAME instance. Fix:

```python
# backend/routers/chat.py — use the shared limiter from mvp router
from .mvp import limiter  # reuse the single Limiter instance
```

- [ ] **Step 3: Commit**

```bash
git add backend/routers/chat.py
git commit -m "fix: add 20/minute rate limiting to /chat and /chat/stream endpoints"
```

---

### PHASE 2 — Stabilization (1–2 weeks)

---

### Task 7: Create `.env.example` and rotate exposed keys (C-4)

**Why it matters:** The `.env` files contain live Supabase + Gemini keys that were visible during this audit. They must be rotated immediately regardless of whether they were ever committed.

**Files affected:**
- Create: `SHOOTRZ/.env.example`
- Create: `SHOOTRZ/backend/.env.example`
- Rotate: Supabase keys (via Supabase dashboard → Settings → API)
- Rotate: Gemini API key (via Google AI Studio)

**Risk:** Breaking change on existing installations — all developers must update their `.env` after rotation

**Effort:** 2 hours (key rotation + docs)

**Success criteria:**
- `SHOOTRZ/.env.example` exists with placeholder values only
- Supabase service key is rotated (old key returns 401)
- Gemini key is rotated

- [ ] **Step 1: Create `.env.example` files**

```bash
# SHOOTRZ/.env.example
EXPO_PUBLIC_SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your_anon_key_here
EXPO_PUBLIC_API_URL=http://localhost:8000
```

```bash
# SHOOTRZ/backend/.env.example
SUPABASE_URL=https://YOUR_PROJECT_ID.supabase.co
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_KEY=your_service_role_key_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
GEMINI_TIMEOUT=60
GEMINI_MAX_RETRIES=3
```

- [ ] **Step 2: Rotate Supabase keys via dashboard**

Go to Supabase Dashboard → Project Settings → API → Rotate service_role key + anon key. Update local `.env` files.

- [ ] **Step 3: Rotate Gemini API key**

Go to Google AI Studio → API Keys → delete old key → create new key. Update `backend/.env`.

- [ ] **Step 4: Verify the new keys work**

```bash
cd SHOOTRZ
python -c "from backend.utils import config; print(config.SUPABASE_URL, bool(config.GEMINI_API_KEY))"
```

- [ ] **Step 5: Add pre-commit hook to block secret patterns**

```yaml
# .pre-commit-config.yaml (create in SHOOTRZ root)
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.2
    hooks:
      - id: gitleaks
```

- [ ] **Step 6: Commit**

```bash
git add .env.example backend/.env.example .pre-commit-config.yaml
git commit -m "security: add .env.example, rotate exposed keys, add gitleaks pre-commit hook"
```

---

### Task 8: Cache Supabase client (H-2)

**Why it matters:** N new client objects per request → connection exhaustion under load.

**Files affected:**
- `backend/storage/supabase_client.py`

**Risk:** Low — singleton pattern, tested by existing DB operations working

**Effort:** 1 hour

**Success criteria:** `get_service_client() is get_service_client()` returns `True` (same object)

- [ ] **Step 1: Write test**

```python
# backend/tests/test_supabase_client.py
from backend.storage.supabase_client import get_service_client, get_anon_client

def test_service_client_is_singleton():
    c1 = get_service_client()
    c2 = get_service_client()
    assert c1 is c2, "get_service_client() must return the same object each call"

def test_anon_client_is_singleton():
    c1 = get_anon_client()
    c2 = get_anon_client()
    assert c1 is c2
```

- [ ] **Step 2: Implement `lru_cache`**

```python
# backend/storage/supabase_client.py
from functools import lru_cache
from supabase import create_client, Client
from ..utils import config


class NotConfiguredError(RuntimeError):
    pass


@lru_cache(maxsize=1)
def get_service_client() -> Client:
    if not config.SUPABASE_URL or not config.SUPABASE_SERVICE_KEY:
        raise NotConfiguredError(
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_SERVICE_KEY."
        )
    return create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)


@lru_cache(maxsize=1)
def get_anon_client() -> Client:
    if not config.SUPABASE_URL or not config.SUPABASE_ANON_KEY:
        raise NotConfiguredError(
            "Supabase not configured. Set SUPABASE_URL and SUPABASE_ANON_KEY."
        )
    return create_client(config.SUPABASE_URL, config.SUPABASE_ANON_KEY)
```

- [ ] **Step 3: Run test**

```bash
python -m pytest backend/tests/test_supabase_client.py -v
```
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/storage/supabase_client.py backend/tests/test_supabase_client.py
git commit -m "perf: cache Supabase clients as singletons to prevent connection exhaustion"
```

---

### Task 9: Create canonical `schema_complete.sql` with all tables (H-3)

**Why it matters:** A fresh Supabase DB from `schema.sql` is missing 5+ tables that the backend writes to.

**Files affected:**
- Create: `SHOOTRZ/supabase/schema_complete.sql`
- Read existing: `schema.sql`, all migration files, `db.py` to identify all tables

**Risk:** Medium — must be verified against live DB

**Effort:** 4 hours

**Success criteria:** Running `schema_complete.sql` on a fresh Supabase project gives a DB that passes all integration tests

- [ ] **Step 1: Audit all table references in `db.py`**

```bash
grep -n "\.table(" SHOOTRZ/backend/storage/db.py | sort -u
```
Expected output: every table name the backend touches.

- [ ] **Step 2: Write `schema_complete.sql`**

The file must include (in order):
1. Extensions (pgcrypto, uuid-ossp)
2. All tables from `schema.sql` (users, videos, metrics, feedback, sessions, models)
3. All tables from migrations (session_videos, user_profiles, analysis_summaries, chat_history, drill_completions, user_streaks)
4. All RLS enable statements
5. All policies from `schema.sql`, `add_delete_policy.sql`, `storage_policies.sql`, migration files
6. All triggers from `trigger_create_user.sql`
7. All indexes
8. All functions (`get_user_stats` RPC)

Use idempotent DDL throughout (`CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, `DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN null; END $$;`).

- [ ] **Step 3: Verify by running against a test Supabase project**

```bash
# In Supabase SQL editor, run schema_complete.sql
# Then verify via psql or Supabase table editor that all tables exist
```

- [ ] **Step 4: Commit**

```bash
git add SHOOTRZ/supabase/schema_complete.sql
git commit -m "docs: add canonical schema_complete.sql with all tables, RLS, triggers"
```

---

### Task 10: Add structured JSON logging (L-3)

**Why it matters:** Without structured log format, `extra={}` dicts are invisible. Debugging production requires proper log aggregation.

**Files affected:**
- `backend/main.py` (add logging config)

**Risk:** Low — logging config change only

**Effort:** 2 hours

**Success criteria:** `uvicorn` output shows JSON lines; `jq '.extra.job_id' backend.log` returns job IDs

- [ ] **Step 1: Install `python-json-logger`**

```bash
pip install python-json-logger
# Add to requirements.txt / pyproject.toml
```

- [ ] **Step 2: Add logging configuration to `main.py`**

```python
# backend/main.py — add before create_app():
import logging.config

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
```

- [ ] **Step 3: Verify**

```bash
cd SHOOTRZ && uvicorn backend.main:app &
curl http://localhost:8000/health 2>/dev/null | head -1
# Should see JSON log line from uvicorn
```

- [ ] **Step 4: Commit**

```bash
git add backend/main.py
git commit -m "ops: add structured JSON logging via python-json-logger"
```

---

### Task 11: Add max context size guard in chat (M-2)

**Why it matters:** Prevents Gemini token explosion and 429s from oversized prompts.

**Files affected:**
- `backend/chat/context_builder.py`

**Risk:** Low — truncation only, content still present but capped

**Effort:** 1 hour

- [ ] **Step 1: Add `MAX_CONTEXT_CHARS` guard in `sanitize_context_for_llm`**

Read the current implementation of `sanitize_context_for_llm` in `context_builder.py` first.

```python
# backend/chat/context_builder.py
MAX_CONTEXT_CHARS = 32_000

def sanitize_context_for_llm(context: Dict[str, Any]) -> Dict[str, Any]:
    """Truncate string values and cap total size."""
    import json
    context = copy.deepcopy(context)
    # existing sanitization ...
    # Add total size cap:
    serialized = json.dumps(context)
    if len(serialized) > MAX_CONTEXT_CHARS:
        # Reduce recent_sessions first
        sessions = context.get("recent_sessions", [])
        while len(json.dumps(context)) > MAX_CONTEXT_CHARS and sessions:
            sessions.pop()
        context["recent_sessions"] = sessions
    return context
```

- [ ] **Step 2: Write test**

```python
# backend/tests/test_context_builder.py
from backend.chat.context_builder import sanitize_context_for_llm
import json

def test_sanitize_caps_context_size():
    big_context = {
        "recent_sessions": [{"summary": "x" * 5000}] * 20,
    }
    result = sanitize_context_for_llm(big_context)
    assert len(json.dumps(result)) <= 32_000 + 100  # small tolerance
```

- [ ] **Step 3: Run test, commit**

```bash
python -m pytest backend/tests/test_context_builder.py -v
git add backend/chat/context_builder.py backend/tests/test_context_builder.py
git commit -m "fix: cap chat context to 32K chars to prevent Gemini token explosion"
```

---

### Task 12: Add prompt injection sanitization (M-3)

**Why it matters:** User profile fields injected into Gemini system prompt are a prompt injection vector.

**Files affected:**
- `backend/chat/context_builder.py` (or `prompt_builders.py`)

**Risk:** Low — sanitization is additive

**Effort:** 1 hour

- [ ] **Step 1: Add sanitizer**

```python
# backend/chat/context_builder.py
import re

_PROMPT_SAFE_RE = re.compile(r'[^\w\s.,!?\'"\-():;]')

def _sanitize_str(s: object, max_len: int = 200) -> str:
    """Strip non-printable and injection-prone characters from user strings."""
    if not isinstance(s, str):
        return str(s)[:max_len]
    return _PROMPT_SAFE_RE.sub('', s)[:max_len]
```

- [ ] **Step 2: Apply sanitizer to all user-supplied fields before returning from `build_user_context`**

```python
# In the user_section dict construction:
user_section = {
    "name": _sanitize_str(user.get("name")),
    "skill_level": _sanitize_str(user.get("skill_level")),
    ...
}
if profile:
    user_section["coaching_style"] = _sanitize_str(profile.get("coaching_style", "balanced"))
    user_section["primary_goal"] = _sanitize_str(profile.get("primary_goal") or "")
```

- [ ] **Step 3: Write test**

```python
def test_sanitize_str_removes_injection():
    from backend.chat.context_builder import _sanitize_str
    assert "Ignore" in _sanitize_str("Ignore previous instructions")
    assert "\x00" not in _sanitize_str("name\x00with\x00nulls")
    assert len(_sanitize_str("x" * 500)) == 200
```

- [ ] **Step 4: Commit**

```bash
git add backend/chat/context_builder.py backend/tests/test_context_builder.py
git commit -m "security: sanitize user-supplied strings before injecting into Gemini prompts"
```

---

### Task 13: Add server-side cap on analysis history query (M-9)

**Why it matters:** Unbounded queries of 100 sessions with metrics can cause slow DB responses.

**Files affected:**
- `backend/routers/user.py:152-175`

**Risk:** Zero — additive validation only

**Effort:** 30 minutes

- [ ] **Step 1: Add Query validation**

```python
# backend/routers/user.py
from fastapi import Query

@router.get("/user/analysis-history")
async def get_analysis_history(
    user: AuthenticatedUser = Depends(get_authenticated_user),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
```

- [ ] **Step 2: Commit**

```bash
git add backend/routers/user.py
git commit -m "fix: enforce limit=[1,100] on /api/user/analysis-history query param"
```

---

### Task 14: Remove `__graveyard__` and `backend/outputs/` from git tracking (M-10)

**Why it matters:** 50+ dead backup files confuse analysis tools and bloat the repo. Committed video/CSV/JSON test artifacts shouldn't be in source control.

**Files affected:**
- `.gitignore`
- All files under `__graveyard__/` and `backend/outputs/`

**Risk:** Low — only removes unneeded files from tracking; local copies remain

**Effort:** 1 hour

- [ ] **Step 1: Add entries to `.gitignore`**

```bash
# SHOOTRZ/.gitignore — add:
__graveyard__/
backend/outputs/
backend/database/progress.db
```

- [ ] **Step 2: Remove from git tracking**

```bash
cd SHOOTRZ
git rm -r --cached __graveyard__/ 2>/dev/null || true
git rm -r --cached backend/outputs/ 2>/dev/null || true
git rm --cached backend/database/progress.db 2>/dev/null || true
```

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: untrack __graveyard__, backend/outputs, progress.db from git"
```

---

### PHASE 3 — Hardening (2–6 weeks)

---

### Task 15: Auto-persist analysis to Supabase without client call (H-4)

**Why it matters:** Data loss on client crash between poll and `/api/analysis/complete`.

**Files affected:**
- `backend/services/mvp_job_service.py`
- `backend/routers/mvp.py` (add optional auth)

**Risk:** Medium — requires auth on upload to know user_id at persist time

**Effort:** 2 days

**Success criteria:** After submitting an authenticated video upload, the analysis appears in `/api/user/analysis-history` within 30 seconds without any client-side call to `/api/analysis/complete`

- [ ] **Step 1: Make auth optional on `/mvp/analyze`**

```python
# backend/routers/mvp.py
from ..utils.supabase_auth import AuthenticatedUser

async def analyze_video(
    request: Request,
    file: UploadFile = File(...),
    shooting_side: str = Query(default="auto"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
):
    user_id: Optional[str] = None
    if authorization:
        try:
            from ..utils.supabase_auth import get_authenticated_user
            user = get_authenticated_user(authorization)
            user_id = user.user_id
        except Exception:
            pass  # Continue as anonymous
```

- [ ] **Step 2: Pass `user_id` through to `queue_job_async`**

```python
# MVPJobService.queue_job_async — add user_id param
async def queue_job_async(self, upload, shooting_side, user_id=None):
    job_id, video_path = self._persist_upload(upload)
    self.job_store.upsert(job_id, {"status": "queued", "user_id": user_id})
    ...
```

- [ ] **Step 3: In `_persist_supabase_and_cleanup`, call `save_result_for_user` if `user_id` present**

```python
async def _persist_supabase_and_cleanup(self, job_id, job_result, video_path):
    try:
        payload = self.job_store.get(job_id)
        user_id = payload.get("user_id") if payload else None
        if user_id and job_result.get("status") == "completed":
            await asyncio.to_thread(self.save_result_for_user, job_id, user_id)
    except Exception:
        logger.exception("Auto-persist to Supabase failed", extra={"job_id": job_id})
    ...
```

- [ ] **Step 4: Write integration test**

```python
# backend/tests/test_auto_persist.py
# Uses mock DB to verify save_result_for_user is called when user_id is present
```

- [ ] **Step 5: Commit**

```bash
git add backend/routers/mvp.py backend/services/mvp_job_service.py backend/tests/test_auto_persist.py
git commit -m "feat: auto-persist analysis to Supabase when upload is authenticated"
```

---

### Task 16: Skill-level normative range personalization (M-6)

**Why it matters:** Beginner with 95° knee bend gets same score as elite. Feedback quality is the core product.

**Files affected:**
- `backend/mvp/core/metrics.py`
- `backend/metrics/normative_ranges.json`

**Risk:** Medium — changes scoring output; must be well-tested

**Effort:** 3 days

**Success criteria:** A user with `skill_level="beginner"` and 95° knee bend receives a "Good" verdict; the same user with `skill_level="advanced"` receives "Needs Work"

- [ ] **Step 1: Extend `normative_ranges.json` with skill tiers**

```json
{
  "knee_flexion": {
    "target_range": [100, 120],
    "optimal_range": [105, 115],
    "by_skill": {
      "beginner": {"target_range": [85, 125], "optimal_range": [90, 120]},
      "intermediate": {"target_range": [95, 120], "optimal_range": [100, 115]},
      "advanced": {"target_range": [100, 120], "optimal_range": [105, 115]}
    }
  }
}
```

- [ ] **Step 2: Write failing test**

```python
# backend/mvp/tests/test_skill_level_scoring.py
from backend.mvp.core.metrics import MetricsDerivation

def test_beginner_95_degree_knee_is_good():
    md = MetricsDerivation(config={}, skill_level="beginner")
    score = md._dim_score(95.0, "knee_flexion")
    assert score >= 70, f"Beginner 95° knee should score >= 70, got {score}"

def test_advanced_95_degree_knee_is_needs_work():
    md = MetricsDerivation(config={}, skill_level="advanced")
    score = md._dim_score(95.0, "knee_flexion")
    assert score < 70, f"Advanced 95° knee should score < 70, got {score}"
```

- [ ] **Step 3: Implement skill-level lookup in `MetricsDerivation._target_of`**

```python
# backend/mvp/core/metrics.py
class MetricsDerivation:
    def __init__(self, config, skill_level="intermediate"):
        self.config = config
        self.skill_level = skill_level or "intermediate"

    def _target_of(self, norm_key: str):
        cfg = _NORMATIVE_RANGES.get(norm_key, {})
        skill_cfg = cfg.get("by_skill", {}).get(self.skill_level, {})
        tr = skill_cfg.get("optimal_range") or cfg.get("optimal_range") or cfg.get("target_range")
        if isinstance(tr, list) and len(tr) == 2:
            return float(tr[0]), float(tr[1])
        ...
```

- [ ] **Step 4: Pass `skill_level` through from `mvp_job_service.py`**

The `skill_level` is a user profile field. Since analysis is currently anonymous (no auth on upload), this needs the auth-on-upload fix (Task 15) to be complete first.

Alternative: Accept `skill_level` as a query param on `/mvp/analyze` for now (no trust issue — user can only lie about their own level).

- [ ] **Step 5: Run tests, commit**

```bash
python -m pytest backend/mvp/tests/test_skill_level_scoring.py -v
git add backend/mvp/core/metrics.py backend/metrics/normative_ranges.json backend/mvp/tests/test_skill_level_scoring.py
git commit -m "feat: personalize metric scoring by user skill level (beginner/intermediate/advanced)"
```

---

### Task 17: Reduce Supabase queries in chat context build (H-5)

**Why it matters:** 4 sequential DB queries per chat message = 4× minimum latency. Target: 1 RPC.

**Files affected:**
- `backend/chat/context_builder.py`
- `SHOOTRZ/supabase/schema_complete.sql` (add RPC function)

**Risk:** Medium — new DB function, must match existing query shape

**Effort:** 2 days

**Success criteria:** `/chat` latency drops by >50% (measure via `elapsed_ms` in `_persist_exchange`)

- [ ] **Step 1: Write Supabase RPC function `get_coach_context`**

```sql
-- supabase/migration_coach_context_rpc.sql
CREATE OR REPLACE FUNCTION get_coach_context(p_user_id UUID, p_summary_limit INT DEFAULT 5)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'user', (SELECT row_to_json(u) FROM users u WHERE u.id = p_user_id),
    'profile', (SELECT row_to_json(up) FROM user_profiles up WHERE up.user_id = p_user_id),
    'stats', get_user_stats(p_user_id),
    'summaries', (
      SELECT json_agg(s ORDER BY s.created_at DESC)
      FROM (SELECT * FROM analysis_summaries WHERE user_id = p_user_id
            ORDER BY created_at DESC LIMIT p_summary_limit) s
    )
  ) INTO result;
  RETURN result;
END;
$$;
```

- [ ] **Step 2: Update `build_user_context` to use single RPC call**

```python
# backend/chat/context_builder.py
def build_user_context(*, user_id, user_local_context, options):
    sb = get_service_client()
    resp = sb.rpc("get_coach_context", {
        "p_user_id": user_id,
        "p_summary_limit": options.max_recent_summaries,
    }).execute()
    ctx_data = resp.data or {}
    # Parse fields from ctx_data
    user = ctx_data.get("user") or {}
    profile = ctx_data.get("profile") or {}
    stats = ctx_data.get("stats") or {}
    summaries = ctx_data.get("summaries") or []
    ...
```

- [ ] **Step 3: Write test**

```python
# backend/tests/test_context_builder_rpc.py
# Mock the supabase client, verify single RPC call is made
```

- [ ] **Step 4: Commit**

```bash
git add backend/chat/context_builder.py supabase/migration_coach_context_rpc.sql
git commit -m "perf: replace 4 sequential DB queries in chat context with single RPC call"
```

---

### Task 18: Multi-frame confidence calibration (M-7 / Modernization)

**Why it matters:** A joint with 0.9 confidence in one frame but high variance across 5 frames is unreliable. Current system trusts single-frame confidence.

**Files affected:**
- `backend/mvp/core/pose_estimation.py`
- `backend/mvp/core/angle_computation.py`

**Risk:** Medium — changes confidence values, may change score outputs

**Effort:** 3 days

**Success criteria:** Pose frames where a joint has std > 0.05 across 5 surrounding frames have confidence reduced by ≥ 20%; overall metric score variance reduces on test clips

- [ ] **Step 1: Write failing test**

```python
# backend/mvp/tests/test_confidence_calibration.py
from backend.mvp.core.pose_estimation import calibrate_confidence_multiframe

def test_high_variance_joint_reduces_confidence():
    # 5 frames where right_elbow position varies wildly
    frames = [{"right_elbow": {"x": i * 0.1, "y": 0.5, "conf": 0.9}} for i in range(5)]
    calibrated = calibrate_confidence_multiframe(frames, joint="right_elbow", window=5)
    for f in calibrated:
        assert f["right_elbow"]["conf"] < 0.9, "High-variance joint must have lower confidence"
```

- [ ] **Step 2: Implement `calibrate_confidence_multiframe`**

```python
# backend/mvp/core/pose_estimation.py
import numpy as np

def calibrate_confidence_multiframe(frames, joint: str, window: int = 5):
    """Penalize confidence for joints with high positional variance in local window."""
    positions = np.array([f.get(joint, {}).get("x", 0) for f in frames])
    calibrated = []
    half = window // 2
    for i, frame in enumerate(frames):
        lo, hi = max(0, i - half), min(len(frames), i + half + 1)
        local_std = float(np.std(positions[lo:hi]))
        original_conf = frame.get(joint, {}).get("conf", 0.0)
        # Penalize: conf *= exp(-10 * std), so std=0.05 → 60% retention
        adj_conf = original_conf * float(np.exp(-10 * local_std))
        new_frame = {**frame, joint: {**frame.get(joint, {}), "conf": max(0.0, adj_conf)}}
        calibrated.append(new_frame)
    return calibrated
```

- [ ] **Step 3: Integrate into pose pipeline**

Apply `calibrate_confidence_multiframe` in `MVPPoseEstimator.process_frame_stream` after collecting all pose results.

- [ ] **Step 4: Run test + regression test on existing metrics tests**

```bash
python -m pytest backend/mvp/tests/ -v
```

- [ ] **Step 5: Commit**

```bash
git add backend/mvp/core/pose_estimation.py backend/mvp/tests/test_confidence_calibration.py
git commit -m "feat: add multi-frame confidence calibration to reduce noisy joint scores"
```

---

## 8. PR Plan

Each PR is small, reviewable, and independently deployable. PRs within the same phase can be reviewed in parallel.

| PR # | Title | Tasks | Days | Risk |
|------|-------|-------|------|------|
| PR-01 | `fix: recommender signature + auth guards` | C-1, C-2, C-3 | 0.5 | Low |
| PR-02 | `fix: video upload size cap + MIME extension filter` | H-1, M-7 | 0.5 | Low |
| PR-03 | `fix: print() → logger in pipeline code` | M-5 | 0.5 | Low |
| PR-04 | `fix: rate-limit chat endpoints` | H-6 | 0.5 | Low |
| PR-05 | `security: rotate keys + add .env.example + gitleaks` | C-4 | 1 | Low |
| PR-06 | `perf: cache Supabase client as singleton` | H-2 | 0.5 | Low |
| PR-07 | `docs: add canonical schema_complete.sql` | H-3 | 1 | Medium |
| PR-08 | `ops: structured JSON logging` | L-3 | 0.5 | Low |
| PR-09 | `fix: chat context size cap + prompt sanitization` | M-2, M-3 | 1 | Low |
| PR-10 | `fix: analysis history query cap` | M-9 | 0.5 | Low |
| PR-11 | `chore: untrack graveyard and output dirs` | M-10 | 0.5 | Low |
| PR-12 | `feat: auto-persist analysis on authenticated upload` | H-4 | 2 | Medium |
| PR-13 | `feat: skill-level normative range personalization` | M-6 | 3 | Medium |
| PR-14 | `perf: single RPC for chat context build` | H-5 | 2 | Medium |
| PR-15 | `feat: multi-frame confidence calibration` | M-7 | 3 | Medium |

**Rollout strategy for high-risk PRs:**
- **PR-12 (auto-persist):** Deploy to staging with 5 test users for 48 hours; verify analysis count in Supabase matches upload count
- **PR-13 (skill-level scoring):** Gate with `SHOOTRZ_SKILL_SCORING=true` env flag; keep old behavior as default until validated

**Rollback plan:** Every PR produces a single git commit. To roll back PR-N: `git revert <commit_sha>` and redeploy. No DB migrations in Phase 1 or 2 PRs — schema changes are additive only.

---

## 9. Verification Checklist Before Launch

Run this checklist after all Phase 1 PRs are merged:

### Security
- [ ] `git secret scan SHOOTRZ/` (or gitleaks) returns 0 findings
- [ ] `curl -X GET http://localhost:8000/history/00000000-0000-0000-0000-000000000000` returns 401 (not 200 or 404)
- [ ] `curl -X POST http://localhost:8000/api/recommend -d '{}'` returns 401
- [ ] Uploading a 201MB file to `/mvp/analyze` returns 413
- [ ] Uploading a `.exe` renamed to `.mp4` is rejected (MIME/extension check)
- [ ] Supabase keys have been rotated and old keys return 401

### Recommender
- [ ] `curl -X POST http://localhost:8000/api/recommend -H "Authorization: Bearer <token>" -d '{"user_vec": [...], "user_context": [...], "weak_areas": ["elbow"]}` returns a valid drill_id without TypeError

### Schema
- [ ] Running `schema_complete.sql` on a fresh Supabase project succeeds
- [ ] All tables exist: users, videos, metrics, feedback, sessions, models, session_videos, user_profiles, analysis_summaries, chat_history, drill_completions, user_streaks
- [ ] All RLS policies enabled: verify via `SELECT tablename, rowsecurity FROM pg_tables WHERE schemaname='public'`

### Logging
- [ ] `grep -r "^    print(" SHOOTRZ/backend/ --include="*.py"` returns 0 results
- [ ] `uvicorn backend.main:app 2>&1 | head -5 | python -m json.tool` succeeds (JSON format)

### Performance
- [ ] `get_service_client() is get_service_client()` returns `True`
- [ ] `/chat` endpoint p95 latency < 3 seconds under 10 concurrent users

### Test suite
- [ ] `python -m pytest backend/ -v --ignore=backend/__graveyard__` passes with ≥ 80% tests green
- [ ] Load test: `locust -f backend/tests/load/locustfile.py --headless -u 10 -r 2 --run-time 60s` — failure rate < 1%

### Data integrity
- [ ] Submit an authenticated video upload; wait 30s; confirm session appears in `/api/user/analysis-history` without calling `/api/analysis/complete`
- [ ] Submit the same video twice; confirm second submission returns the cached job_id without re-processing
- [ ] Delete user account via `/api/user/account`; confirm user row deleted from Supabase; confirm auth.admin confirms user gone

---
