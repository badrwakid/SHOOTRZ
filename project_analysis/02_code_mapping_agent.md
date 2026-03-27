# Codebase Mapping (Evidence-Based)

## 1) Executive Summary

This repository contains one primary implemented system under `SHOOTRZ/`: an Expo React Native frontend and a FastAPI backend with a deterministic MVP AI/CV pipeline.  
The true runtime path is:

- Frontend boot: `SHOOTRZ/index.ts` (`registerRootComponent(App)`) -> `SHOOTRZ/App.tsx` (`App`, `AppContent`) -> `SHOOTRZ/src/navigation/AppNavigator.tsx` (`AppNavigator`)
- Backend boot: `SHOOTRZ/backend/main.py` (`create_app`, `app = create_app()`)
- AI/CV analysis path: `SHOOTRZ/backend/routers/mvp.py` (`analyze_video`, `_process_video_job`) -> `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`)

There is also substantial non-runtime material: archived code in `SHOOTRZ/__graveyard__/`, many generated artifacts in `SHOOTRZ/backend/outputs/`, and training/evaluation scripts in `SHOOTRZ/scripts/`.

---

## 2) Repository Structure Overview

## Root (`D:/Users/Badr/Grad`)

- `SHOOTRZ/` - main application and backend implementation (**critical**)
- `project_analysis/` - presentation analysis markdown files (currently placeholders except this file)
- `.cursor/rules/` - workspace coding guidance (`python.mdc`, `typescript.mdc`)
- `MVP_SUMMARY.md` - project-level summary doc

## Main Project (`D:/Users/Badr/Grad/SHOOTRZ`)

- `src/` - React Native frontend implementation (**critical**)
- `backend/` - FastAPI server + AI/CV pipeline + storage integration (**critical**)
- `supabase/` - SQL schema/migration/policy scripts (**critical**)
- `scripts/` - dataset/training/evaluation utilities (mostly offline tooling)
- `models/` - model artifacts and model-related assets
- `__graveyard__/` - archived legacy/prototype code (**non-runtime**)
- `audit_logs/` - audit artifacts/docs
- App/tooling configs: `package.json`, `app.config.js`, `app.json`, `tsconfig.json`, `metro.config.js`

## Backend critical subtree (`SHOOTRZ/backend`)

- `main.py` - FastAPI app creation and router wiring
- `routers/` - HTTP API endpoints (`mvp.py`, `chat.py`, `history.py`, `feedback.py`, `sessions.py`, `recommendation_routes.py`, test routers)
- `mvp/core/` - primary CV pipeline implementation (`pipeline.py`, pose/angles/metrics/detection modules)
- `inference/` - phase detection and additional CV modules (some active, some experimental)
- `storage/` - Supabase data access layer (`supabase_client.py`, `db.py`)
- `chat/` - chat context + OpenAI integration
- `recommender/` - recommendation pipeline
- `metrics/` - biomechanics/metric computation helpers
- `config/mvp_config.yaml` - pipeline/scoring thresholds and weights
- `outputs/` - generated analysis artifacts by run id (**generated data, not source logic**)

## Frontend critical subtree (`SHOOTRZ/src`)

- `navigation/AppNavigator.tsx` - tab navigation root
- `context/AuthContext.tsx` - auth state and user profile orchestration
- `screens/` - user-facing screens (`MVPAnalysisScreen`, `ChatScreen`, etc.)
- `services/` - API/Supabase/storage/chat service layers
- `components/` - reusable UI components
- `hooks/` - app hooks (`useDeepLinks` active)
- `constants/`, `utils/`, `types/` - shared definitions/utilities

---

## 3) Key Entry Points

## Frontend Entry Point

- **Path:** `SHOOTRZ/package.json`
  - **Symbol:** `main: "index.ts"`
  - **Role:** Declares Expo runtime entry file.
- **Path:** `SHOOTRZ/index.ts`
  - **Symbol:** `registerRootComponent(App)`
  - **Role:** Registers app root with Expo runtime.
- **Path:** `SHOOTRZ/App.tsx`
  - **Symbol:** `App`, `AppContent`
  - **Role:** Composes providers and gates auth/onboarding before navigation.

## Backend Entry Point

- **Path:** `SHOOTRZ/backend/main.py`
  - **Symbol:** `create_app`, module `app = create_app()`
  - **Role:** Builds FastAPI app, mounts routers, defines root/health handlers.
- **Path:** `SHOOTRZ/backend/RUN_SERVER.md`
  - **Command evidence:** `python -m uvicorn backend.main:app ...`
  - **Role:** Documents true server startup command.
- **Path:** `SHOOTRZ/start_backend_network.bat`
  - **Command evidence:** `python -m uvicorn SHOOTRZ.backend.main:app ...`
  - **Role:** Launches network-accessible backend.

## AI/CV Pipeline Entry Point

- **Path:** `SHOOTRZ/backend/routers/mvp.py`
  - **Symbol:** `analyze_video`
  - **Role:** Receives upload, schedules background processing.
- **Path:** `SHOOTRZ/backend/routers/mvp.py`
  - **Symbol:** `_process_video_job`
  - **Role:** Instantiates and runs pipeline, collects artifacts/results.
- **Path:** `SHOOTRZ/backend/mvp/core/pipeline.py`
  - **Symbol:** `MVPPipeline.process_video`
  - **Role:** Main orchestration for frame loading -> pose -> smoothing -> angles -> shot window -> metrics -> exports.

## Database / Storage Initialization

- **Path:** `SHOOTRZ/supabase/schema.sql`
  - **Symbols:** DDL for `users`, `videos`, `metrics`, `feedback`, `sessions`, `models`; RLS policies
  - **Role:** Core DB schema bootstrap.
- **Path:** `SHOOTRZ/supabase/migration_mvp_enhancements.sql`
  - **Role:** Schema evolution (camera angle enum, session-video relation, indexes/policies).
- **Path:** `SHOOTRZ/supabase/trigger_create_user.sql`
  - **Symbol:** `public.handle_new_user`, trigger `on_auth_user_created`
  - **Role:** Auto-create profile rows on auth user creation.
- **Path:** `SHOOTRZ/backend/storage/supabase_client.py`
  - **Symbols:** `get_service_client`, `get_anon_client`
  - **Role:** Runtime DB client initialization from env.

---

## 4) Major Modules and Responsibilities

## API Layer (Backend)

- **Purpose:** Expose REST endpoints and coordinate services.
- **Files:** `backend/main.py`, `backend/routers/*.py`
- **Key symbols:** `create_app`, `router` instances, endpoint functions (`analyze_video`, `chat`, `history`, etc.)
- **Connections:** Calls MVP pipeline, storage layer, chat layer, recommender.

## MVP AI/CV Pipeline

- **Purpose:** End-to-end shot analysis from video file.
- **Files:** `backend/mvp/core/pipeline.py`, `video_loader.py`, `pose_estimation.py`, `signal_smoothing.py`, `angle_computation.py`, `shot_detection.py`, `metrics.py`, `run_tracker.py`
- **Key symbols:** `MVPPipeline`, `VideoLoader`, `MVPPoseEstimator`, `SignalSmoother`, `AngleComputer`, `ShotDetector`, `MetricsDerivation`, `RunTracker`
- **Connections:** Called by `routers/mvp.py`; uses `inference.pose_2d` and `metrics.biomechanics`.

## Phase Detection Module

- **Purpose:** Detect motion phases for overlay/feedback segments.
- **Files:** `backend/inference/phase_detector.py`, `backend/inference/motion_analyzer.py`
- **Key symbols:** `PhaseDetector.detect_phases`, motion feature extractors
- **Connections:** Called in `routers/mvp.py` after pipeline output for annotation/fallback logic.

## Chat Coaching Module

- **Purpose:** Build context and call OpenAI chat model.
- **Files:** `backend/routers/chat.py`, `backend/chat/context_builder.py`, `backend/chat/openai_client.py`
- **Key symbols:** `chat`, `build_user_context`, `generate_chat_completion`
- **Connections:** Uses auth (`utils/supabase_auth.py`) and storage (`storage/db.py`).

## Storage/Data Access Layer

- **Purpose:** Supabase CRUD and retrieval for user/history/session/metrics/feedback.
- **Files:** `backend/storage/supabase_client.py`, `backend/storage/db.py`
- **Key symbols:** `record_video`, `record_metrics`, `record_feedback`, `get_user_history`, `create_session`, `add_video_to_session`
- **Connections:** Invoked by history/session/feedback/chat and test routes.

## Recommendation Module

- **Purpose:** Drill recommendation based on embeddings/bandit/recent metrics.
- **Files:** `backend/routers/recommendation_routes.py`, `backend/recommender/*.py`
- **Key symbols:** `recommend`, `get_recommender`, `load_recommender`, `recommend_drill`
- **Connections:** Route layer -> recommender service/model/index.

## Frontend App Shell + Navigation

- **Purpose:** App startup and authenticated routing.
- **Files:** `App.tsx`, `src/navigation/AppNavigator.tsx`, `src/context/AuthContext.tsx`
- **Key symbols:** `App`, `AppContent`, `AppNavigator`, `AuthProvider`, `useAuth`
- **Connections:** Renders screens and provides auth/session state.

## Frontend Analysis UX Module

- **Purpose:** Record/upload video, call analysis API, poll result, render feedback.
- **Files:** `src/screens/MVPAnalysisScreen.tsx`, `src/services/api.service.ts`, `src/components/AngleGraph.tsx`
- **Key symbols:** `handleAnalyzeVideo`, `ApiService.analyzeMVP`, `ApiService.getMVPResult`
- **Connections:** UI -> backend `/mvp/*` endpoints -> render score/metrics/video.

## Frontend Chat UX Module

- **Purpose:** Chat with Coach J using backend `/chat`.
- **Files:** `src/screens/ChatScreen.tsx`, `src/services/chat.service.ts`, `src/services/chat-storage.service.ts`
- **Key symbols:** `send`, `chatService.sendMessage`, `saveConversation/loadConversation`
- **Connections:** Includes local context from `storage.service.ts`, auth token from Supabase.

## Frontend Local Data Module

- **Purpose:** Local persistence (AsyncStorage) for user data, preferences, analysis history.
- **Files:** `src/services/storage.service.ts`
- **Key symbols:** `storageService` methods (`saveAnalysisResult`, profile/goals/preferences operations)
- **Connections:** Used by screens and chat service context builder.

---

## 5) Function/Class Breakdown

## Core backend orchestration

- `create_app` - `SHOOTRZ/backend/main.py`
  - **Purpose:** Construct FastAPI app and include routers.
  - **Inputs:** none
  - **Outputs:** `FastAPI` application object.
  - **Module:** API layer.

- `analyze_video` - `SHOOTRZ/backend/routers/mvp.py`
  - **Purpose:** Accept upload, validate, create `job_id`, queue background process.
  - **Inputs:** uploaded video (`UploadFile`), `shooting_side`
  - **Outputs:** job metadata (`job_id`, status).
  - **Module:** API -> MVP bridge.

- `_process_video_job` - `SHOOTRZ/backend/routers/mvp.py`
  - **Purpose:** Run `MVPPipeline`, build result payload, write job status.
  - **Inputs:** `job_id`, temp `video_path`, `shooting_side`
  - **Outputs:** in-memory `job_store[job_id]` completed/failed payload.
  - **Module:** Async processing bridge.

- `MVPPipeline.process_video` - `SHOOTRZ/backend/mvp/core/pipeline.py`
  - **Purpose:** Full analysis orchestration and artifact export.
  - **Inputs:** `video_path`, `shooting_side`, optional `run_id`
  - **Outputs:** analysis dict (`overall_score`, `metrics`, `shot_window`, `output_dir`, etc.).
  - **Module:** MVP pipeline core.

## CV/math building blocks

- `MVPPoseEstimator.process_frames` - `backend/mvp/core/pose_estimation.py`
  - **Purpose:** Run pose detection per frame.
  - **Inputs:** frames + frame mapping
  - **Outputs:** pose keypoint records list.
  - **Module:** Pose estimation.

- `SignalSmoother.smooth_keypoints` - `backend/mvp/core/signal_smoothing.py`
  - **Purpose:** Temporal smoothing of keypoints.
  - **Inputs:** pose keypoints frame data
  - **Outputs:** smoothed keypoints dataframe/records.
  - **Module:** Signal processing.

- `AngleComputer.compute_angles_per_frame` - `backend/mvp/core/angle_computation.py`
  - **Purpose:** Compute elbow/knee/wrist angles over time.
  - **Inputs:** keypoints dataframe
  - **Outputs:** angles dataframe with confidence fields.
  - **Module:** Angle calculation.

- `ShotDetector.detect_shot_window` - `backend/mvp/core/shot_detection.py`
  - **Purpose:** Detect start/crouch/release/end frames.
  - **Inputs:** angles + keypoints + side
  - **Outputs:** shot window dict.
  - **Module:** Shot detection.

- `MetricsDerivation.derive_metrics` + `compute_overall_score` - `backend/mvp/core/metrics.py`
  - **Purpose:** Derive metric list and aggregate score.
  - **Inputs:** angles, shot window, keypoints, metadata
  - **Outputs:** metrics list and score tuple.
  - **Module:** Scoring logic.

- `PhaseDetector.detect_phases` - `backend/inference/phase_detector.py`
  - **Purpose:** Motion-phase segmentation.
  - **Inputs:** pose results (+ side/params)
  - **Outputs:** phase segments.
  - **Module:** Phase analysis.

## Backend user features

- `chat` - `backend/routers/chat.py`
  - **Purpose:** Authenticated coaching chat endpoint.
  - **Inputs:** `ChatRequest`, auth user
  - **Outputs:** `ChatResponse`.
  - **Module:** Chat API.

- `build_user_context` - `backend/chat/context_builder.py`
  - **Purpose:** Build context from DB + optional local fields.
  - **Inputs:** `user_id`, local context fields/options
  - **Outputs:** context text + metadata.
  - **Module:** Chat context.

- `generate_chat_completion` - `backend/chat/openai_client.py`
  - **Purpose:** Send prompt/messages to OpenAI API.
  - **Inputs:** prompt/messages/model params
  - **Outputs:** generated response payload.
  - **Module:** LLM integration.

## Frontend runtime

- `AppContent` - `SHOOTRZ/App.tsx`
  - **Purpose:** Gate flows (splash/login/username/onboarding/main app).
  - **Inputs:** auth/profile completion state from `useAuth`
  - **Outputs:** screen tree.
  - **Module:** App shell.

- `AppNavigator` - `src/navigation/AppNavigator.tsx`
  - **Purpose:** Define main tab routes.
  - **Inputs:** navigation state/user interaction
  - **Outputs:** screen routing.
  - **Module:** UI navigation.

- `handleAnalyzeVideo` - `src/screens/MVPAnalysisScreen.tsx`
  - **Purpose:** Trigger API analysis and result polling.
  - **Inputs:** local media URI + side selection
  - **Outputs:** screen state update with analysis result.
  - **Module:** Analysis UX.

- `send` - `src/screens/ChatScreen.tsx`
  - **Purpose:** Send user message and append assistant response.
  - **Inputs:** user text
  - **Outputs:** updated message list/context label.
  - **Module:** Chat UX.

- `AuthProvider` methods (`login`, `signup`, `logout`, `updateProfile`) - `src/context/AuthContext.tsx`
  - **Purpose:** Auth lifecycle and profile sync against Supabase.
  - **Inputs:** credentials/profile payload
  - **Outputs:** auth state/user updates.
  - **Module:** Authentication.

---

## 6) Implementation Mapping Table

| Architectural Responsibility | File Path | Class/Function | What It Does | Related Components |
|---|---|---|---|---|
| App bootstrapping (mobile) | `SHOOTRZ/index.ts` | `registerRootComponent(App)` | Registers root app for Expo runtime | `App.tsx`, Expo |
| Root UI composition | `SHOOTRZ/App.tsx` | `App`, `AppContent` | Wraps providers, gates auth/onboarding, renders main navigator | `AuthProvider`, `AppNavigator` |
| Main navigation | `SHOOTRZ/src/navigation/AppNavigator.tsx` | `AppNavigator` | Defines tab-based routing | screen components |
| Auth state management | `SHOOTRZ/src/context/AuthContext.tsx` | `AuthProvider`, `useAuth` | Session listening, login/signup/social login/profile update | `supabase.client.ts`, auth screens |
| Video analysis UI flow | `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` | `handleAnalyzeVideo` | Uploads video, polls job status, renders analysis | `api.service.ts`, `AngleGraph` |
| Backend API service | `SHOOTRZ/src/services/api.service.ts` | `ApiService.analyzeMVP`, `getMVPResult` | Calls `/mvp/analyze` and `/mvp/result/{jobId}` | backend `routers/mvp.py` |
| Chat UI flow | `SHOOTRZ/src/screens/ChatScreen.tsx` | `send` | Sends/receives chat messages | `chat.service.ts`, `chat-storage.service.ts` |
| Chat HTTP client | `SHOOTRZ/src/services/chat.service.ts` | `sendMessage` | Calls backend `/chat` with local context and auth token | `routers/chat.py`, `storage.service.ts` |
| Local persistence | `SHOOTRZ/src/services/storage.service.ts` | `storageService` | AsyncStorage for user/goals/preferences/history/results | screens + `chat.service.ts` |
| Supabase client init (frontend) | `SHOOTRZ/src/services/supabase.client.ts` | `supabase` | Initializes browser/mobile Supabase SDK client | `AuthContext`, storage upload service |
| Backend app assembly | `SHOOTRZ/backend/main.py` | `create_app`, `app` | Creates FastAPI app and includes routers | all `backend/routers/*` |
| MVP upload endpoint | `SHOOTRZ/backend/routers/mvp.py` | `analyze_video` | Accepts video and enqueues async processing | `_process_video_job`, `MVPPipeline` |
| Async job processor | `SHOOTRZ/backend/routers/mvp.py` | `_process_video_job` | Runs pipeline and prepares API result payload | `pipeline.py`, `video_annotator.py`, `PhaseDetector` |
| Job result endpoint | `SHOOTRZ/backend/routers/mvp.py` | `get_result` | Returns job status/result from in-memory store | `job_store` |
| Artifact serving | `SHOOTRZ/backend/routers/mvp.py` | `get_artifact` | Serves generated artifact files by run id | `backend/outputs/*` |
| Pipeline orchestrator | `SHOOTRZ/backend/mvp/core/pipeline.py` | `MVPPipeline.process_video` | Runs full deterministic CV/scoring pipeline and writes outputs | `video_loader`, `pose_estimation`, `shot_detection`, `metrics`, `run_tracker` |
| Video ingest | `SHOOTRZ/backend/mvp/core/video_loader.py` | `VideoLoader` | Reads metadata/frames from source video | pipeline |
| Pose estimation | `SHOOTRZ/backend/mvp/core/pose_estimation.py` | `MVPPoseEstimator` | Converts frames to pose keypoints | `inference/pose_2d.py` |
| Keypoint smoothing | `SHOOTRZ/backend/mvp/core/signal_smoothing.py` | `SignalSmoother` | Smooths noisy pose trajectories | pipeline |
| Angle computation | `SHOOTRZ/backend/mvp/core/angle_computation.py` | `AngleComputer` | Computes elbow/knee/wrist angles | `metrics/biomechanics.py` |
| Shot boundary detection | `SHOOTRZ/backend/mvp/core/shot_detection.py` | `ShotDetector` | Detects temporal shot window landmarks | angles + keypoints |
| Metric derivation and score | `SHOOTRZ/backend/mvp/core/metrics.py` | `MetricsDerivation` | Produces metric records and overall score | shot window + angles |
| Output run tracking | `SHOOTRZ/backend/mvp/core/run_tracker.py` | `RunTracker`, `create_run_tracker` | Creates run directory and stores metadata | `backend/outputs` |
| Phase segmentation | `SHOOTRZ/backend/inference/phase_detector.py` | `PhaseDetector.detect_phases` | Estimates movement phases for overlays | `motion_analyzer.py`, `routers/mvp.py` |
| Video annotation | `SHOOTRZ/backend/utils/video_annotator.py` | `annotate_video` | Renders annotated output video | `routers/mvp.py` |
| Chat endpoint | `SHOOTRZ/backend/routers/chat.py` | `chat` | Handles authenticated chat request/response | `context_builder.py`, `openai_client.py` |
| Chat context builder | `SHOOTRZ/backend/chat/context_builder.py` | `build_user_context` | Builds context from Supabase + optional local fields | `storage/db.py` |
| LLM client | `SHOOTRZ/backend/chat/openai_client.py` | `generate_chat_completion` | Performs OpenAI completion call | env from `utils/config.py` |
| History API | `SHOOTRZ/backend/routers/history.py` | `history`, `get_history_stats` | Serves user history and stats | `storage/db.py` |
| Feedback API | `SHOOTRZ/backend/routers/feedback.py` | `get_video_feedback_endpoint`, `generate_feedback_endpoint` | Retrieves/generates coaching feedback | `storage/db.py`, `feedback/engine.py` |
| Sessions API | `SHOOTRZ/backend/routers/sessions.py` | `create_session_endpoint`, `add_video_to_session_endpoint` | Session creation and video-session linking | `storage/db.py` |
| Recommendation API | `SHOOTRZ/backend/routers/recommendation_routes.py` | `recommend`, `get_recommender` | Exposes drill recommendation endpoint | `recommender/recommend_service.py` |
| Supabase DB access | `SHOOTRZ/backend/storage/db.py` | `record_*`, `get_*`, session helpers | DB read/write wrapper functions | routers + chat context |
| Supabase client bootstrap | `SHOOTRZ/backend/storage/supabase_client.py` | `get_service_client`, `get_anon_client` | Creates DB clients from env keys | `storage/db.py` |
| DB schema bootstrap | `SHOOTRZ/supabase/schema.sql` | SQL DDL/policies | Creates tables + RLS policies | backend storage layer |
| DB migration | `SHOOTRZ/supabase/migration_mvp_enhancements.sql` | SQL migration statements | Extends schema for MVP/session features | `schema.sql` |

---

## 7) Code-Level Data Flow

## Flow A: User video analysis

1. User action in `src/screens/MVPAnalysisScreen.tsx` (`handleAnalyzeVideo`) selects/records video.
2. Screen calls `src/services/api.service.ts` -> `ApiService.analyzeMVP` (`POST /mvp/analyze`).
3. Backend endpoint `backend/routers/mvp.py::analyze_video` validates and queues `_process_video_job`.
4. `_process_video_job` calls `backend/mvp/core/pipeline.py::MVPPipeline.process_video`.
5. Pipeline executes staged modules:
   - `VideoLoader` -> `MVPPoseEstimator` -> `SignalSmoother` -> `AngleComputer` -> `ShotDetector` -> `MetricsDerivation`
6. Pipeline writes artifacts to `backend/outputs/{run_id}` (`angles.csv`, `shot_window.json`, `report.json`, etc.) via `RunTracker`.
7. Router composes final result payload (with optional annotated video generated by `utils/video_annotator.py` and phase segments from `PhaseDetector` or fallback).
8. Frontend polls `ApiService.getMVPResult(jobId)` until completed and renders score/metrics/video/graphs.

## Flow B: Coach chat

1. User action in `src/screens/ChatScreen.tsx` (`send`) submits a message.
2. `src/services/chat.service.ts::sendMessage` gathers:
   - recent conversation payload,
   - local context via `storage.service.ts`,
   - access token via `supabase.auth.getSession()`.
3. Backend `backend/routers/chat.py::chat` authenticates via `utils/supabase_auth.py`.
4. Context assembled in `backend/chat/context_builder.py::build_user_context` from DB and optional local context.
5. OpenAI call in `backend/chat/openai_client.py::generate_chat_completion`.
6. Response returns to frontend; chat screen appends message and saves conversation with `chat-storage.service.ts`.

## Flow C: Auth and onboarding gate

1. Startup enters `App.tsx::AppContent`.
2. `useAuth()` state from `src/context/AuthContext.tsx` determines route:
   - unauthenticated -> `LoginScreen`,
   - missing username -> `UsernameScreen`,
   - incomplete onboarding -> `OnboardingScreen`,
   - complete -> `AppNavigator`.
3. Auth methods call Supabase SDK in `supabase.client.ts`; profile writes/reads use `users` table operations.

---

## 8) Dead / Partial / Placeholder Code

## UNUSED / DEAD CODE

- `SHOOTRZ/backend/routers/health.py` - defines router `health_check`, but `backend/main.py` does not include this router; health is implemented directly in `main.py`.
- `SHOOTRZ/src/services/fastapi.service.ts` - exports `getHistory` and `checkHealth`; no active frontend integration path found in runtime flow.
- `SHOOTRZ/src/hooks/useUpload.ts` - hook exists but not wired into active screen flow.
- `SHOOTRZ/src/hooks/useAnalysis.ts` - hook exists but not used in active screen path.
- `SHOOTRZ/src/pages/HistoryPage.tsx` - page exists but not registered in `AppNavigator`.
- `SHOOTRZ/src/context/SettingsContext.tsx` - provider/hook defined but app root uses only `AuthProvider`.
- `SHOOTRZ/src/screens/GoalsScreen.tsx` - implemented screen but not routed from `AppNavigator`.

## PARTIALLY IMPLEMENTED

- `SHOOTRZ/src/screens/ProgressScreen.tsx` - explicit "replace with actual API call" comment and `mockSessions` structure indicate incomplete backend integration.
- `SHOOTRZ/backend/routers/mvp.py` - phase generation includes fallback mode (`phase_detector_version = "fallback"`) when primary detection path fails.
- `SHOOTRZ/backend/utils/schemas.py` - schema models present; some imported symbols are not consistently used as endpoint response models.

## PLACEHOLDER

- `SHOOTRZ/backend/metrics/angles.py` (`compute_elbow_alignment`, `compute_release_extension`) - returns constant stub values.
- `SHOOTRZ/backend/metrics/posture.py` (`compute_posture_metrics`) - returns constant-like zeros.
- `SHOOTRZ/backend/metrics/consistency.py` (`compute_consistency`) - fixed stub-style dictionary.
- `SHOOTRZ/backend/inference/hybrik_lifter.py` - explicit placeholder/warning fallback implementation path.
- `SHOOTRZ/backend/inference/posemagic_lifter.py` - placeholder fallback behavior documented in code.
- `SHOOTRZ/backend/inference/ball_tracker.py` - placeholder return path when optional dependency/model unavailable.
- `SHOOTRZ/src/services/mediapipe.service.ts` - explicitly marked "Mock implementation for POC."
- `SHOOTRZ/src/utils/drawing.ts` - placeholder drawing functions.

---

## 9) Real vs Non-Real Implementation

## REAL IMPLEMENTATION (active runtime path)

- Frontend boot and routing:
  - `SHOOTRZ/index.ts`, `SHOOTRZ/App.tsx`, `SHOOTRZ/src/navigation/AppNavigator.tsx`
- Frontend core features:
  - analysis screen/service (`src/screens/MVPAnalysisScreen.tsx`, `src/services/api.service.ts`)
  - chat screen/service (`src/screens/ChatScreen.tsx`, `src/services/chat.service.ts`)
  - auth/context (`src/context/AuthContext.tsx`, `src/services/supabase.client.ts`)
- Backend runtime:
  - `SHOOTRZ/backend/main.py`, `backend/routers/*.py`
  - MVP pipeline `backend/mvp/core/*`
  - storage/chat/recommender runtime modules
- DB setup:
  - `SHOOTRZ/supabase/schema.sql` + migrations/policies/triggers.

## DEMO / TEST / PROTOTYPE / EXPERIMENTAL

- `SHOOTRZ/__graveyard__/` - archived backup/prototype code by naming and location.
- `SHOOTRZ/backend/routers/db_test.py`, `db_integration_test.py` - diagnostic test endpoints, not product feature endpoints.
- `SHOOTRZ/scripts/*.py` - mostly offline dataset/evaluation/training utilities.
- Several inference modules not wired to main `/mvp/analyze` pipeline (`hybrik_lifter.py`, `posemagic_lifter.py`, `ball_tracker.py`, `hands_2d.py`, `yolo_pose_detector.py`, etc.).
- Generated run outputs in `SHOOTRZ/backend/outputs/*` are data artifacts, not source implementation.

## UNUSED / NON-INTEGRATED (non-runtime despite existing source)

- Frontend unused hooks/services/pages/context listed in Section 8.
- Backend `routers/health.py` router file is non-integrated.

---

## 10) Open Questions / Uncertain Areas

- `SHOOTRZ/backend/README.md` references Flask-era startup (`python app.py`), while active backend is FastAPI (`backend/main.py`). This appears stale and should be reconciled.
- Some `backend/inference/*` and `backend/metrics/*` modules may be intended for future integration; current determination is based on present call paths from `main.py` and active routers.
- Root `package-lock.json` exists alongside `SHOOTRZ/package.json`; whether root JS runtime is still intended is unclear from current call graph.
- Many files in `backend/outputs/` are versioned in git status snapshots; expected tracking policy for generated artifacts is unclear.

---

## 11) Presentation-Relevant Insights

- **Architecture-implementation alignment is strongest in the MVP path:** UI analysis action maps cleanly to backend endpoint and deterministic CV pipeline (`MVPAnalysisScreen` -> `/mvp/analyze` -> `MVPPipeline.process_video`).
- **Clear modular decomposition exists:** API, CV pipeline, storage, chat, recommendation, and frontend UI layers are separated by folders and service boundaries.
- **Technical debt is visible and presentable:** stale docs/start scripts and placeholder modules can be explicitly framed as migration residue and future work.
- **Evidence of maturity in core workflow:** artifact tracking (`RunTracker`), config-driven thresholds (`mvp_config.yaml`), and test suites (`backend/mvp/tests`, `backend/inference/tests`) support implementation credibility.
- **Non-real code is easy to isolate:** `__graveyard__`, mock services, and placeholder metric/inference files can be marked as non-production to avoid over-claiming in presentation.

