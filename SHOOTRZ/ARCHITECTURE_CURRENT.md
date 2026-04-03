# SHOOTRZ Current Architecture (Verified Active Paths)

This document captures what is actively used in the current repository.
It is intentionally strict: if a module is not imported by active entry paths,
it should be treated as non-core until proven otherwise.

## 1) Runtime Entry Points

- Mobile app entry: `SHOOTRZ/index.ts`
- App shell and auth gating: `SHOOTRZ/App.tsx`
- Main navigation: `SHOOTRZ/src/navigation/AppNavigator.tsx`
- Backend API entry: `SHOOTRZ/backend/main.py` (`app = create_app()`)

## 2) Active Frontend Feature Flows

### MVP Analyze (MVP-critical)
- Screen: `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx`
- API client: `SHOOTRZ/src/services/api.service.ts`
- Local persistence: `SHOOTRZ/src/services/storage.service.ts`
- UI components used directly by flow:
  - `SHOOTRZ/src/components/CameraRecorder.tsx`
  - `SHOOTRZ/src/components/AngleGraph.tsx`

### Auth + Onboarding
- Auth provider: `SHOOTRZ/src/context/AuthContext.tsx`
- Supabase client: `SHOOTRZ/src/services/supabase.client.ts`
- Screens:
  - `SHOOTRZ/src/screens/LoginScreen.tsx`
  - `SHOOTRZ/src/screens/UsernameScreen.tsx`
  - `SHOOTRZ/src/screens/OnboardingScreen.tsx`
  - `SHOOTRZ/src/screens/SplashScreen.tsx`

### Chat
- Screen: `SHOOTRZ/src/screens/ChatScreen.tsx`
- Client service: `SHOOTRZ/src/services/chat.service.ts`
- Local conversation storage: `SHOOTRZ/src/services/chat-storage.service.ts`

### History/Progress (partially active)
- Screen exists and is routed: `SHOOTRZ/src/screens/ProgressScreen.tsx`
- Backend endpoints exist:
  - `GET /history/{user_id}`
  - `GET /history/{user_id}/stats`
- Flow currently needs cleanup to ensure real data path is used end-to-end.

## 3) Active Backend API Surface

Mounted in `SHOOTRZ/backend/main.py`:

- `SHOOTRZ/backend/routers/mvp.py` (MVP upload/result/artifacts)
- `SHOOTRZ/backend/routers/chat.py`
- `SHOOTRZ/backend/routers/history.py`
- `SHOOTRZ/backend/routers/feedback.py`
- `SHOOTRZ/backend/routers/sessions.py`
- `SHOOTRZ/backend/routers/db_test.py`
- `SHOOTRZ/backend/routers/db_integration_test.py`
- `SHOOTRZ/backend/routers/recommendation_routes.py` (under `/api`)

## 4) MVP-Critical Backend Pipeline

Core deterministic path:

1. `POST /mvp/analyze` in `backend/routers/mvp.py`
2. Pipeline orchestration in `backend/mvp/core/pipeline.py`
3. Core modules in `backend/mvp/core`:
   - `video_loader.py`
   - `pose_estimation.py`
   - `signal_smoothing.py`
   - `angle_computation.py`
   - `shot_detection.py`
   - `metrics.py`
   - `run_tracker.py`
4. Artifacts written to `backend/outputs/{run_id}`
5. Result fetched via `GET /mvp/result/{job_id}`

## 5) MVP-Critical Boundaries (Do Not Break)

- Preserve current request/response behavior for:
  - `POST /mvp/analyze`
  - `GET /mvp/result/{job_id}`
  - `GET /mvp/artifacts/{run_id}/{filename}`
- Preserve artifact naming conventions consumed by mobile:
  - `angles.csv`, `report.json`, `shot_window.json`, `overlay.mp4`, etc.
- Preserve metric semantics and score meaning in:
  - `backend/mvp/core/metrics.py`
  - `backend/mvp/core/shot_detection.py`
- Preserve `MVPAnalysisScreen` UX flow:
  - Upload -> poll -> render score/metrics/angles -> persist local history.

## 6) Known Non-Core / Noise Zones

- `SHOOTRZ/__graveyard__` (archived historical code)
- Generated outputs under `SHOOTRZ/backend/outputs`
- Unwired/legacy frontend modules (tracked in `DEPRECATED_MODULES.md`)
- Documentation with stale commands should not be treated as source of truth.

## 7) Ownership (Refactor Responsibility)

- Frontend app shell and feature UX: `src/screens`, `src/navigation`, `src/components`
- Frontend API/data contracts: `src/services`, `src/types`
- Backend API contracts and orchestration: `backend/routers`, `backend/services`
- Deterministic analysis logic: `backend/mvp/core` (highest stability priority)
- Data persistence adapters: `backend/storage`
