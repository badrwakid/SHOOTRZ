# Implementation Evidence Audit (Repository Reality Check)

## 1. Executive Summary

This repository contains a **real, connected MVP flow** for basketball shot analysis: mobile video capture/upload, backend processing pipeline, result polling, and result visualization with metrics + overlay video.  
Core evidence:
- Frontend analyze flow in `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` (`handleAnalyzeVideo`)
- Backend API and router registration in `SHOOTRZ/backend/main.py` (`create_app`)
- MVP pipeline orchestration in `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`)

At the same time, multiple areas are **partial, placeholder, or not wired into the main flow**:
- Progress/history UI is largely mock (`SHOOTRZ/src/screens/ProgressScreen.tsx`)
- Recommender endpoint exists but has no frontend integration (`SHOOTRZ/backend/routers/recommendation_routes.py`)
- Several advanced CV/biomechanics modules exist but are not part of the active MVP execution path (`SHOOTRZ/backend/inference/*`, `SHOOTRZ/backend/metrics/trajectory.py`, `SHOOTRZ/backend/inference/ball_tracker.py`)
- Backend README documents legacy Flask endpoints not matching the running FastAPI app (`SHOOTRZ/backend/README.md`)

---

## 2. Major Features Identified

1. Mobile auth/onboarding (Supabase auth + app onboarding)
2. Video capture and gallery upload in mobile app
3. MVP analysis API (upload + async job polling + artifact serving)
4. MVP processing pipeline (video loading, pose, smoothing, angles, shot window, metrics/scoring)
5. Annotated overlay generation and delivery
6. Chat assistant ("Coach J") with authenticated backend + OpenAI
7. Supabase data-access endpoints (history/sessions/feedback/db tests)
8. Drill/workout UI and local persistence
9. Recommendation endpoint and recommender modules
10. Advanced CV/3D/ball/trajectory modules (mostly not in active runtime path)

---

## 3. Feature-by-Feature Status Analysis

### A) Mobile authentication + onboarding
- **Status:** FULLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/src/context/AuthContext.tsx` (`login`, `signup`, `signInWithGoogle`, `logout`, auth state listener), `SHOOTRZ/App.tsx` (`AppContent` gating login/onboarding/main app), `SHOOTRZ/src/services/supabase.client.ts`
- **Why:** End-to-end state handling exists (session restore, auth transitions, onboarding flags, username checks, DB updates).

### B) Video capture + upload trigger from mobile
- **Status:** FULLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/src/components/CameraRecorder.tsx` (`startRecording`, `stopRecording`), `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` (`pickVideo`, `recordVideo`, `handleVideoRecorded`)
- **Why:** Camera and gallery paths both lead into analysis trigger logic.

### C) MVP analysis API upload, queue, poll, artifact URLs
- **Status:** FULLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/backend/routers/mvp.py` (`analyze_video`, `_process_video_job`, `get_result`, `get_artifact`), router included in `SHOOTRZ/backend/main.py` (`app.include_router(mvp.router)`)
- **Why:** Upload endpoint creates jobs, background processing fills in-memory job store, result endpoint returns status/data, artifact endpoint serves files.

### D) MVP backend processing pipeline
- **Status:** FULLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`) calls:
  - `VideoLoader` (`mvp/core/video_loader.py`)
  - `MVPPoseEstimator` (`mvp/core/pose_estimation.py`)
  - `SignalSmoother` (`mvp/core/signal_smoothing.py`)
  - `AngleComputer` (`mvp/core/angle_computation.py`)
  - `ShotDetector` (`mvp/core/shot_detection.py`)
  - `MetricsDerivation` (`mvp/core/metrics.py`)
- **Why:** These are executed sequentially in one orchestration path and exported artifacts are used by API response flow.

### E) Shot phase detection for overlay labeling
- **Status:** PARTIALLY IMPLEMENTED
- **Evidence:** Called in `SHOOTRZ/backend/routers/mvp.py` (`PhaseDetector.detect_phases` before `annotate_video`), implementation in `SHOOTRZ/backend/inference/phase_detector.py`
- **Why:** It is connected, but wrapped in fallback logic to old `shot_window`-based phases if detector fails; marked as non-critical best-effort in runtime.

### F) Overlay video generation and consumption in app
- **Status:** FULLY IMPLEMENTED
- **Evidence:** Backend generation in `SHOOTRZ/backend/routers/mvp.py` (`annotate_video` call from `utils/video_annotator.py`), frontend playback in `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` (`overlayUri`, `downloadOverlayToLocal`, `Video` player)
- **Why:** The full backend->artifact->frontend loop is wired.

### G) Chat assistant with user context + LLM
- **Status:** FULLY IMPLEMENTED (config-dependent)
- **Evidence:** API route `SHOOTRZ/backend/routers/chat.py` (`/chat`), auth dependency `SHOOTRZ/backend/utils/supabase_auth.py`, LLM call `SHOOTRZ/backend/chat/openai_client.py`, frontend usage `SHOOTRZ/src/screens/ChatScreen.tsx` + `SHOOTRZ/src/services/chat.service.ts`
- **Why:** End-to-end request path exists and is used by UI.  
- **Limitation:** Requires valid Supabase token + backend env `OPENAI_API_KEY`.

### H) History and progress analytics (UI side)
- **Status:** PLACEHOLDER / MOCK
- **Evidence:** `SHOOTRZ/src/screens/ProgressScreen.tsx` in `loadSessions` explicitly uses `const mockSessions: Session[] = []` and comments "replace with actual API call"
- **Why:** Screen renders, but real backend fetch is not implemented.

### I) History/session/feedback backend endpoints
- **Status:** PARTIALLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/backend/routers/history.py`, `sessions.py`, `feedback.py`; DB operations in `SHOOTRZ/backend/storage/db.py`
- **Why:** Endpoints and DB functions exist, but frontend usage is missing for history/sessions/feedback (only MVP and chat are actively consumed).

### J) Recommendation API (drill recommendation)
- **Status:** PARTIALLY IMPLEMENTED
- **Evidence:** Route `SHOOTRZ/backend/routers/recommendation_routes.py` (`POST /api/recommend`), loader/service in `backend/recommender/model_loader.py`, `recommend_service.py`
- **Why:** Backend route + logic exist; no frontend calls found in `SHOOTRZ/src` to this endpoint.

### K) Drills/workouts user features
- **Status:** PARTIALLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/src/screens/DrillsScreen.tsx` (filterable drill catalog from constants), `WorkoutsScreen.tsx` (local workout state and completion save)
- **Why:** Good UI and local behaviors exist; largely static/local, not integrated with backend recommendation engine.

### L) Supabase storage upload helper hook/path
- **Status:** PARTIALLY IMPLEMENTED
- **Evidence:** `SHOOTRZ/src/hooks/useUpload.ts`, `SHOOTRZ/src/services/supabase.storage.ts`
- **Why:** Implemented utility path exists but not used in active MVP analyze screen (analysis uses backend upload directly via `apiService.analyzeMVP`).

### M) Advanced ball tracking / trajectory / 3D lifting modules
- **Status:** PARTIALLY IMPLEMENTED (code exists), **not connected to main MVP runtime**
- **Evidence:** Modules include `backend/inference/ball_tracker.py`, `backend/inference/lift_3d.py`, `backend/metrics/trajectory.py`, `backend/inference/hybrik_lifter.py`, `backend/inference/posemagic_lifter.py`
- **Why:** No execution path from `MVPPipeline.process_video` to these modules in current MVP flow.

### N) Legacy Flask API described in docs
- **Status:** DOCUMENTED ONLY (for current repo runtime)
- **Evidence:** `SHOOTRZ/backend/README.md` documents Flask (`app.py`, `/api/analyze`, port 5000), while actual runtime is FastAPI in `SHOOTRZ/backend/main.py`
- **Why:** Documentation and actual implementation are misaligned.

---

## 4. Real Execution / Connectivity Analysis

### Actual connected path (mobile -> backend -> mobile)
1. `MVPAnalysisScreen.handleAnalyzeVideo` -> `apiService.analyzeMVP` (`SHOOTRZ/src/services/api.service.ts`)
2. Backend `/mvp/analyze` queues `_process_video_job` (`SHOOTRZ/backend/routers/mvp.py`)
3. `_process_video_job` runs `MVPPipeline.process_video` (`SHOOTRZ/backend/mvp/core/pipeline.py`)
4. Result stored in `job_store`, polled by `/mvp/result/{job_id}`
5. Frontend polls until `status === 'completed'`, then renders score/metrics/graphs/overlay

### Connected but optional/degraded
- Phase detection for overlay labels: connected, but fallback path to simple phases exists (`mvp.py` fallback block on detector exceptions).

### Present but not connected from frontend
- `/api/recommend` (`backend/routers/recommendation_routes.py`)
- History/session/feedback endpoints (`backend/routers/history.py`, `sessions.py`, `feedback.py`) not called from active UI flow.

### Present in code but not in primary runtime path
- Ball trajectory and 3D lifting modules are not called in `MVPPipeline.process_video`.

---

## 5. Demo-Ready Parts

### Demo-capable now
1. **Auth + app launch flow**
   - Control files: `SHOOTRZ/App.tsx`, `src/context/AuthContext.tsx`, `src/services/supabase.client.ts`
   - Needs: Supabase env values in mobile app
   - Risk: Missing env throws runtime error in dev (`supabase.client.ts`)

2. **MVP shot analysis end-to-end**
   - Control files: `src/screens/MVPAnalysisScreen.tsx`, `src/services/api.service.ts`, `backend/routers/mvp.py`, `backend/mvp/core/pipeline.py`
   - Needs: FastAPI backend running, Python deps installed, camera/gallery permissions
   - Risk: Processing timeout, pose quality failures, overlay generation can fail (handled as best-effort)

3. **Coach J chat**
   - Control files: `src/screens/ChatScreen.tsx`, `src/services/chat.service.ts`, `backend/routers/chat.py`
   - Needs: Supabase auth token + backend `OPENAI_API_KEY`
   - Risk: Missing key/token leads to hard failures (401/500/502 paths)

### Demo-able with caveats
- **Drills/workouts UI**: looks complete visually, but mostly static/local logic (`DrillsScreen`, `WorkoutsScreen`)
- **History/progress page**: should be presented as in-progress (currently mock session loading)

---

## 6. Risks / Gaps / Technical Debt

- Backend docs mismatch runtime architecture: Flask docs vs FastAPI implementation (`backend/README.md` vs `backend/main.py`)
- In-memory job store in MVP router (`job_store` in `backend/routers/mvp.py`) is non-persistent and single-process only.
- Many API methods in mobile `api.service.ts` are legacy/non-implemented (`getPerformanceMetrics`, `getSystemStatus`, `forceCleanup` return null/false with warnings).
- Progress analytics UI explicitly mocks data (`ProgressScreen.loadSessions`).
- Recommendation backend exists without frontend wiring (risk of overclaim if presented as active feature).
- Advanced CV modules exist but are not part of current MVP execution chain.
- Duplicate/unused health route file (`backend/routers/health.py`) while main app defines health endpoint in `main.py`.
- Hardcoded debug logging hooks to local path in backend/frontend (`.cursor/debug.log`/local ingest URL snippets) can be fragile outside dev setup.

---

## 7. Feature Status Table

| Feature / Module | Status | Evidence | Relevant Files | Notes / Limitations |
|---|---|---|---|---|
| Supabase auth + onboarding flow | FULLY IMPLEMENTED | `AuthContext` manages session/login/signup/logout/onboarding and DB sync | `SHOOTRZ/src/context/AuthContext.tsx`, `SHOOTRZ/App.tsx`, `SHOOTRZ/src/services/supabase.client.ts` | Requires env setup |
| Mobile video recording/upload UX | FULLY IMPLEMENTED | Camera + gallery paths call analysis handler | `SHOOTRZ/src/components/CameraRecorder.tsx`, `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` | Dependent on permissions |
| MVP analyze API endpoints | FULLY IMPLEMENTED | `/mvp/analyze`, `/mvp/result/{job_id}`, `/mvp/artifacts/...` | `SHOOTRZ/backend/routers/mvp.py`, `SHOOTRZ/backend/main.py` | Uses in-memory job store |
| MVP deterministic processing pipeline | FULLY IMPLEMENTED | Full staged orchestration in `process_video` | `SHOOTRZ/backend/mvp/core/pipeline.py` + core modules | Main technical core |
| Pose estimation in pipeline | FULLY IMPLEMENTED | `MVPPoseEstimator` wraps MediaPipe and exports keypoints/confidence | `SHOOTRZ/backend/mvp/core/pose_estimation.py`, `SHOOTRZ/backend/inference/pose_2d.py` | Quality depends on visibility |
| Smoothing + interpolation | FULLY IMPLEMENTED | Confidence-based missing interpolation + Savitzky-Golay | `SHOOTRZ/backend/mvp/core/signal_smoothing.py` | Interpolation bounded by gap size |
| Angle computation (elbow/knee/wrist proxy) | FULLY IMPLEMENTED | Per-frame angle extraction with confidences | `SHOOTRZ/backend/mvp/core/angle_computation.py` | Wrist is proxy angle, not direct ball angle |
| Shot window detection | FULLY IMPLEMENTED | Crouch/release detection and shot window JSON export | `SHOOTRZ/backend/mvp/core/shot_detection.py` | Heuristic-based |
| Metric scoring/reporting | FULLY IMPLEMENTED | 3 metrics + weighted score + explanations + report export | `SHOOTRZ/backend/mvp/core/metrics.py` | Scope limited to MVP 3 metrics |
| Overlay rendering and serving | FULLY IMPLEMENTED | Backend annotates video; frontend downloads/plays artifact | `SHOOTRZ/backend/utils/video_annotator.py`, `SHOOTRZ/backend/routers/mvp.py`, `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` | Best-effort generation |
| Motion-based phase detection | PARTIALLY IMPLEMENTED | Connected in overlay path but fallback on failure | `SHOOTRZ/backend/inference/phase_detector.py`, `SHOOTRZ/backend/routers/mvp.py` | Not hard guarantee in all runs |
| Chat assistant (Coach J) | FULLY IMPLEMENTED | Authenticated `/chat` + context builder + OpenAI completion + UI client | `SHOOTRZ/backend/routers/chat.py`, `SHOOTRZ/backend/chat/openai_client.py`, `SHOOTRZ/src/screens/ChatScreen.tsx`, `SHOOTRZ/src/services/chat.service.ts` | Requires Supabase + OpenAI keys |
| History API backend | PARTIALLY IMPLEMENTED | Endpoints query Supabase history/metrics | `SHOOTRZ/backend/routers/history.py`, `SHOOTRZ/backend/storage/db.py` | Not wired into active Progress UI |
| Sessions API backend | PARTIALLY IMPLEMENTED | Session creation and linking endpoints exist | `SHOOTRZ/backend/routers/sessions.py`, `SHOOTRZ/backend/storage/db.py` | Limited frontend consumption |
| Feedback API backend | PARTIALLY IMPLEMENTED | Fetch/generate feedback endpoints exist | `SHOOTRZ/backend/routers/feedback.py`, `SHOOTRZ/backend/feedback/engine.py` | No clear active UI path |
| Progress/history mobile UI | PLACEHOLDER / MOCK | Uses `mockSessions` and TODO-style comments | `SHOOTRZ/src/screens/ProgressScreen.tsx` | Not production-connected |
| Recommendation endpoint | PARTIALLY IMPLEMENTED | `/api/recommend` and recommender pipeline exist | `SHOOTRZ/backend/routers/recommendation_routes.py`, `SHOOTRZ/backend/recommender/*` | No frontend integration found |
| Drills/workouts user screens | PARTIALLY IMPLEMENTED | Functional local UX with static drill/workout data | `SHOOTRZ/src/screens/DrillsScreen.tsx`, `SHOOTRZ/src/screens/WorkoutsScreen.tsx`, `SHOOTRZ/src/constants/drills.ts` | Mostly local/static |
| Advanced ball/3D/trajectory analytics | PARTIALLY IMPLEMENTED | Code modules exist | `SHOOTRZ/backend/inference/ball_tracker.py`, `SHOOTRZ/backend/inference/lift_3d.py`, `SHOOTRZ/backend/metrics/trajectory.py` | Not connected to current MVP pipeline |
| Legacy Flask architecture docs | DOCUMENTED ONLY | README describes Flask endpoints/files not matching runtime | `SHOOTRZ/backend/README.md` vs `SHOOTRZ/backend/main.py` | Presentation risk if cited as current |

---

## 8. Strongest Defensible Implementation Claims

1. The project has a **working end-to-end MVP shot analysis pipeline** from mobile video input to backend analysis results and visualized outputs.
2. The backend is **actively implemented in FastAPI**, with real `/mvp/analyze` + polling + artifact retrieval endpoints.
3. Core biomechanical MVP metrics (elbow extension, knee bend, wrist follow-through) are computed and scored from extracted pose data.
4. Annotated overlay generation is integrated into runtime and displayed in app when available.
5. Coach J chat is implemented with authenticated context + OpenAI backend integration.

---

## 9. Claims That Should Be Avoided or Softened

- Avoid claiming full production analytics dashboard/progress tracking (current screen uses mock session list).
- Avoid claiming recommendation engine is active in user flow (backend exists, no frontend wiring found).
- Avoid claiming full advanced CV stack (ball tracking + 3D lifting + trajectory) is part of current MVP runtime.
- Avoid presenting backend README Flask endpoints as current implementation; actual runtime is FastAPI.
- Avoid claiming robust multi-worker/persistent async jobs; current `job_store` is in-memory.

---

## 10. Open Questions / Uncertain Areas

1. Whether recommender model assets (FAISS index/embeddings/bandit files) are fully present and valid at runtime was not executed here.
2. Supabase schema consistency (tables/triggers/constraints) cannot be fully validated without live DB inspection.
3. End-to-end stability under production load (multi-worker, restarts, large queue) is uncertain because job state is memory-only.
4. Some legacy/experimental modules may be used by scripts outside app runtime, but not by currently wired user flow.

---

## 11. Presentation-Relevant Insights

- Best demo narrative: **"MVP analysis is real and connected"** (record/upload -> backend deterministic pipeline -> scored output + overlay).
- Strong technical defense: show exact staged backend pipeline (`MVPPipeline.process_video`) and matching frontend polling/render flow.
- Chat can be demonstrated as a separate implemented capability, but mention dependency on auth + OpenAI key.
- Present drills/workouts as supporting UX features; do not frame them as AI-personalized pipeline unless recommendation wiring is completed.
- Explicitly label progress/history analytics as under active development if shown.
- If asked about architecture evolution, acknowledge that docs still contain legacy Flask descriptions while current code runs FastAPI.