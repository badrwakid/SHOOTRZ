# 1. Executive Summary

SHOOTRZ is implemented as a mobile + backend system centered on an MVP basketball-shot analysis
pipeline.

- Frontend/mobile is an Expo React Native app (`SHOOTRZ/src`) with an analysis screen
	`MVPAnalysisScreen` in `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx`.
- Backend is FastAPI-based (`SHOOTRZ/backend/main.py`, `create_app`) and exposes MVP analysis,
	chat, history, feedback, sessions, and recommendation routes.
- Core AI/CV processing is implemented in `SHOOTRZ/backend/mvp/core/*` and
	`SHOOTRZ/backend/inference/*`, orchestrated by `MVPPipeline.process_video` in
	`SHOOTRZ/backend/mvp/core/pipeline.py`.
- Output artifacts are persisted to per-run folders in `SHOOTRZ/backend/outputs/{run_id}` via
	`RunTracker` (`SHOOTRZ/backend/mvp/core/run_tracker.py`).
- Documentation includes strong architecture intent, but part of `SHOOTRZ/backend/README.md` is
	outdated versus actual code (Flask/docs mismatch vs actual FastAPI implementation).

# 2. Repository Structure Overview

## High-Level Tree (evidence-based)

```text
D:/Users/Badr/Grad
├── SHOOTRZ
│   ├── backend
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── mvp/core/
│   │   ├── inference/
│   │   ├── metrics/
│   │   ├── chat/
│   │   ├── storage/
│   │   ├── config/
│   │   └── mvp/tests/, inference/tests/, tests/
│   ├── src
│   │   ├── screens/
│   │   ├── services/
│   │   ├── navigation/
│   │   ├── components/
│   │   └── context/, hooks/, utils/
│   ├── models
│   │   ├── hrnet/
│   │   └── yolov8/
│   ├── notebooks/
│   ├── scripts/
│   ├── supabase/
│   └── docs/status markdown files
├── MVP_SUMMARY.md
├── project_analysis/
└── presentation_analysis/
```

## Classification

- **Architecture-related**
	- `MVP_SUMMARY.md`
	- `SHOOTRZ/START_HERE.md`
	- `SHOOTRZ/MVP_IMPLEMENTATION_COMPLETE.md`
	- `SHOOTRZ/MVP_COMPLETE.md`
	- `SHOOTRZ/MVP_PHASE_DETECTOR_INTEGRATION.md`
	- `SHOOTRZ/PHASE_DETECTION_IMPLEMENTATION_COMPLETE.md`
	- `SHOOTRZ/PHASE_DETECTION_REFINEMENT.md`
	- `SHOOTRZ/backend/README.md`
	- `SHOOTRZ/backend/mvp/README.md`
- **Implementation-related**
	- Backend code: `SHOOTRZ/backend/*`
	- Mobile app code: `SHOOTRZ/src/*`
	- Config/package files: `SHOOTRZ/backend/config/mvp_config.yaml`,
		`SHOOTRZ/backend/requirements.txt`, `SHOOTRZ/package.json`, `SHOOTRZ/app.json`
	- DB migration SQL: `SHOOTRZ/supabase/*.sql`
- **AI/CV-related**
	- MVP and inference modules:
		`SHOOTRZ/backend/mvp/core/*`, `SHOOTRZ/backend/inference/*`, `SHOOTRZ/backend/metrics/biomechanics.py`
	- Models and research assets: `SHOOTRZ/models/*`
	- Notebook(s): `SHOOTRZ/notebooks/train_yolov8_ball_colab.ipynb`

# 3. Architecture Sources Reviewed

## Primary sources and contribution

1. `SHOOTRZ/backend/main.py` (`create_app`)
	- Defines backend composition (router wiring, CORS, root/health endpoints).
2. `SHOOTRZ/backend/routers/mvp.py` (`analyze_video`, `_process_video_job`, `get_result`,
	`get_artifact`)
	- Defines asynchronous analysis API contract and artifact serving.
3. `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline`, `process_video`)
	- Defines actual end-to-end AI/CV + scoring execution order.
4. `SHOOTRZ/backend/mvp/core/*` modules
	- `VideoLoader`, `MVPPoseEstimator`, `SignalSmoother`, `AngleComputer`, `ShotDetector`,
		`MetricsDerivation`, `RunTracker`, `MVPConfig`.
5. `SHOOTRZ/backend/inference/phase_detector.py` (`PhaseDetector.detect_phases`) +
	`SHOOTRZ/backend/inference/motion_analyzer.py` (`analyze_motion_patterns`)
	- Defines motion-based phase subsystem.
6. `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx`
	- Defines user-side capture/upload, polling, and result rendering flow.
7. `SHOOTRZ/src/services/api.service.ts` (`analyzeMVP`, `getMVPResult`)
	- Defines frontend-backend API usage.
8. `SHOOTRZ/backend/chat/*` + `SHOOTRZ/backend/routers/chat.py`
	- Defines LLM coaching context + completion path (`build_user_context`,
		`generate_chat_completion`).
9. `SHOOTRZ/backend/storage/*`
	- Defines persistence interfaces to Supabase.
10. Documentation files:
	- `MVP_SUMMARY.md`, `SHOOTRZ/START_HERE.md`, `SHOOTRZ/backend/mvp/README.md`,
		`SHOOTRZ/backend/README.md`.

## SRS/SDD/UML status

- No first-party populated SRS/SDD/UML files were found in project docs.
- Any architecture docs under `SHOOTRZ/models/yolov8/docs/*` describe YOLO vendor/model internals,
	not SHOOTRZ system architecture.
- Status: **INFERRED** from implementation + project markdowns, not formal SRS/SDD artifacts.

# 4. Intended Architecture Breakdown

## Intended architecture from docs

From `MVP_SUMMARY.md`, `SHOOTRZ/START_HERE.md`, and `SHOOTRZ/backend/mvp/README.md`, intended
architecture is:

- Mobile app uploads shot video.
- Backend queues background processing.
- Deterministic multi-phase pipeline computes pose -> smoothing -> angles -> shot phase -> metrics.
- Artifacts are persisted by run ID.
- Client polls result and renders score/metrics/graphs/video overlay.

## Actual architecture from code

- Backend entrypoint: `SHOOTRZ/backend/main.py` `create_app` includes routers:
	`mvp`, `chat`, `history`, `feedback`, `sessions`, `db_test`, `db_integration_test`,
	`recommendation_router`.
- MVP analysis endpoint receives multipart upload:
	`SHOOTRZ/backend/routers/mvp.py` `analyze_video` (`POST /mvp/analyze`).
- Processing occurs in background task:
	`SHOOTRZ/backend/routers/mvp.py` `_process_video_job`.
- Core orchestration:
	`SHOOTRZ/backend/mvp/core/pipeline.py` `MVPPipeline.process_video`.
- Output artifacts served by:
	`SHOOTRZ/backend/routers/mvp.py` `get_artifact` (`GET /mvp/artifacts/{run_id}/{filename}`).

# 5. Layer-by-Layer Explanation

## Layer A: UI / Input Layer (Mobile)

- **Responsibilities**
	- Capture or select video.
	- Trigger analysis.
	- Poll for completion.
	- Display metrics, score, angle plots, and overlay video.
- **Components**
	- `MVPAnalysisScreen` (`SHOOTRZ/src/screens/MVPAnalysisScreen.tsx`)
		- `pickVideo`, `recordVideo`, `handleAnalyzeVideo`, polling loop.
	- API client (`SHOOTRZ/src/services/api.service.ts`)
		- `analyzeMVP`, `getMVPResult`, health checks.
	- Navigation (`SHOOTRZ/src/navigation/AppNavigator.tsx`)
		- Analyze tab points to `MVPAnalysisScreen`.
- **Interactions**
	- Calls backend `/mvp/analyze` and `/mvp/result/{job_id}`.
	- Downloads overlay via artifact URL and local caches it.

## Layer B: Backend API Layer

- **Responsibilities**
	- Route registration and HTTP API.
	- Request admission, file ingestion, job status/results.
	- Expose artifact files.
- **Components**
	- App assembly: `SHOOTRZ/backend/main.py` `create_app`.
	- MVP router: `SHOOTRZ/backend/routers/mvp.py`:
		- `analyze_video`
		- `_process_video_job`
		- `get_result`
		- `get_artifact`
		- `test_phase_detection`
	- Additional routers:
		- `SHOOTRZ/backend/routers/chat.py` (`chat`)
		- `SHOOTRZ/backend/routers/history.py`
		- `SHOOTRZ/backend/routers/feedback.py`
		- `SHOOTRZ/backend/routers/sessions.py`
		- `SHOOTRZ/backend/routers/recommendation_routes.py`
- **Interactions**
	- Invokes MVP core pipeline.
	- Uses in-memory `job_store` (`SHOOTRZ/backend/routers/mvp.py`) for async status.

## Layer C: AI/CV Processing Layer

- **Responsibilities**
	- Pose extraction, signal cleanup, kinematic feature generation.
	- Phase detection and analysis overlays.
- **Components**
	- Pose detector wrapper:
		`SHOOTRZ/backend/inference/pose_2d.py` `MediaPipePoseDetector`, `BASKETBALL_KEYPOINTS`.
	- MVP adapter:
		`SHOOTRZ/backend/mvp/core/pose_estimation.py` `MVPPoseEstimator`.
	- Signal smoothing:
		`SHOOTRZ/backend/mvp/core/signal_smoothing.py` `SignalSmoother`.
	- Motion-phase subsystem:
		`SHOOTRZ/backend/inference/motion_analyzer.py` (`analyze_motion_patterns`) +
		`SHOOTRZ/backend/inference/phase_detector.py` (`PhaseDetector.detect_phases`).
	- Overlay renderer:
		`SHOOTRZ/backend/utils/video_annotator.py` `annotate_video`, `draw_skeleton`,
		`draw_phase_label`.
- **Interactions**
	- Receives frames from video ingestion.
	- Returns structured pose/phase signals to downstream scoring and artifact layer.

## Layer D: Logic / Scoring Layer

- **Responsibilities**
	- Compute elbow/knee/wrist angles.
	- Detect shot window.
	- Derive 3 metrics and weighted score.
- **Components**
	- Angle computation: `SHOOTRZ/backend/mvp/core/angle_computation.py` `AngleComputer`.
	- Shot window: `SHOOTRZ/backend/mvp/core/shot_detection.py` `ShotDetector`.
	- Metric derivation + overall score:
		`SHOOTRZ/backend/mvp/core/metrics.py` `MetricsDerivation`.
- **Interactions**
	- Consumes smoothed keypoint data and phase windows.
	- Produces report metrics consumed by API response and storage/history.

## Layer E: Output / Persistence / Integration Layer

- **Responsibilities**
	- Persist per-run artifacts and metadata.
	- Serve artifacts.
	- Persist user data/history in Supabase.
	- Build chat context and call LLM.
- **Components**
	- Run/output management:
		`SHOOTRZ/backend/mvp/core/run_tracker.py` `RunTracker`.
	- Configuration snapshotting:
		`SHOOTRZ/backend/mvp/core/config_loader.py` `MVPConfig.save_snapshot`.
	- Supabase persistence:
		`SHOOTRZ/backend/storage/supabase_client.py` (`get_service_client`, `get_anon_client`);
		`SHOOTRZ/backend/storage/db.py` (`record_video`, `record_metrics`, `get_user_history`, etc.).
	- Chat context + model call:
		`SHOOTRZ/backend/chat/context_builder.py` `build_user_context`;
		`SHOOTRZ/backend/chat/openai_client.py` `generate_chat_completion`;
		router `SHOOTRZ/backend/routers/chat.py` `chat`.
- **Interactions**
	- Bridges MVP results into downloadable assets and user-facing coaching context.

# 6. System Data Flow

## End-to-end evidence flow

1. **User provides video**
	- UI in `MVPAnalysisScreen.handleAnalyzeVideo`
		(`SHOOTRZ/src/screens/MVPAnalysisScreen.tsx`).
2. **Upload request**
	- `apiService.analyzeMVP` posts multipart to `/mvp/analyze`
		(`SHOOTRZ/src/services/api.service.ts`).
3. **Job accepted**
	- `analyze_video` creates `job_id`, stores `queued` in `job_store`, adds background task
		(`SHOOTRZ/backend/routers/mvp.py`).
4. **Background processing starts**
	- `_process_video_job` instantiates `MVPPipeline` and calls `process_video`.
5. **Pipeline phase execution**
	- `VideoLoader.load_metadata` + `load_frames` (`video_loader.py`).
	- `MVPPoseEstimator.process_frames` + exports pose CSV/JSON/confidence
		(`pose_estimation.py`).
	- `SignalSmoother.smooth_keypoints` (`signal_smoothing.py`).
	- `AngleComputer.compute_angles_per_frame` (`angle_computation.py`).
	- `ShotDetector.detect_shot_window` (`shot_detection.py`).
	- `MetricsDerivation.derive_metrics` + `compute_overall_score` + `export_report_json`
		(`metrics.py`).
	- Metadata saved by `RunTracker.save_metadata`.
6. **Overlay generation**
	- Router-level best-effort call to `annotate_video` in `_process_video_job`
		(`SHOOTRZ/backend/routers/mvp.py`, `SHOOTRZ/backend/utils/video_annotator.py`).
	- Phase source is `PhaseDetector.detect_phases` with fallback mapping.
7. **Result retrieval**
	- Client polls `GET /mvp/result/{job_id}` via `apiService.getMVPResult`.
	- Completed payload includes score, metrics, shot window, angles arrays, artifact URLs.
8. **Artifact download/stream**
	- `GET /mvp/artifacts/{run_id}/{filename}` serves file from `backend/outputs/{run_id}`.
9. **Optional persistence/chat flows**
	- Session/history/metrics route through `storage/db.py`.
	- Chat route builds context from DB + local context then calls OpenAI.

# 7. Architecture Components Table

| Architecture Component | Purpose | File Path Evidence | Status |
|---|---|---|---|
| FastAPI app composition | Assemble backend app and routers | `SHOOTRZ/backend/main.py` (`create_app`) | Implemented |
| MVP analysis endpoint | Accept upload and enqueue analysis | `SHOOTRZ/backend/routers/mvp.py` (`analyze_video`) | Implemented |
| Job processing worker | Execute MVP pipeline and package response | `SHOOTRZ/backend/routers/mvp.py` (`_process_video_job`) | Implemented |
| Pipeline orchestrator | Coordinate all MVP phases | `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`) | Implemented |
| Video ingestion | Metadata, frame extraction, quality checks | `SHOOTRZ/backend/mvp/core/video_loader.py` (`VideoLoader`) | Implemented |
| Pose extraction adapter | Wrap MediaPipe and export pose artifacts | `SHOOTRZ/backend/mvp/core/pose_estimation.py` (`MVPPoseEstimator`) | Implemented |
| Raw pose detector | Frame-level 33-landmark detection | `SHOOTRZ/backend/inference/pose_2d.py` (`MediaPipePoseDetector`) | Implemented |
| Signal smoothing | Interpolate + Savitzky-Golay smoothing | `SHOOTRZ/backend/mvp/core/signal_smoothing.py` (`SignalSmoother`) | Implemented |
| Angle computation | Compute elbow/knee/wrist angles | `SHOOTRZ/backend/mvp/core/angle_computation.py` (`AngleComputer`) | Implemented |
| Shot window detector | Detect crouch/release and shot boundaries | `SHOOTRZ/backend/mvp/core/shot_detection.py` (`ShotDetector`) | Implemented |
| Motion-phase detector | Detect stance/crouch/release/landing via motion signals | `SHOOTRZ/backend/inference/phase_detector.py` (`PhaseDetector.detect_phases`) | Implemented |
| Motion signal extraction | Generate velocities/accelerations/angles for phase logic | `SHOOTRZ/backend/inference/motion_analyzer.py` (`analyze_motion_patterns`) | Implemented |
| Metrics + scoring | Derive metric verdicts and overall score | `SHOOTRZ/backend/mvp/core/metrics.py` (`MetricsDerivation`) | Implemented |
| Artifact management | Run ID directories and metadata persistence | `SHOOTRZ/backend/mvp/core/run_tracker.py` (`RunTracker`) | Implemented |
| Artifact serving | Download report/csv/video outputs | `SHOOTRZ/backend/routers/mvp.py` (`get_artifact`) | Implemented |
| Mobile analysis UI | Capture/upload/poll/render results | `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` (`MVPAnalysisScreen`) | Implemented |
| Mobile API integration | HTTP calls to analysis backend | `SHOOTRZ/src/services/api.service.ts` (`analyzeMVP`, `getMVPResult`) | Implemented |
| Chat API | Personalized AI coaching endpoint | `SHOOTRZ/backend/routers/chat.py` (`chat`) | Implemented |
| Chat context builder | Merge server history + local context + optional artifacts | `SHOOTRZ/backend/chat/context_builder.py` (`build_user_context`) | Implemented |
| LLM client wrapper | OpenAI completion calls | `SHOOTRZ/backend/chat/openai_client.py` (`generate_chat_completion`) | Implemented |
| Supabase adapter | DB client creation and DB operations | `SHOOTRZ/backend/storage/supabase_client.py`, `SHOOTRZ/backend/storage/db.py` | Implemented |
| Formal SRS/SDD architecture spec | Requirements/design baseline docs | No first-party populated SRS/SDD files found in repo scan | INFERRED (absent artifact) |

# 8. Documented vs Implemented vs Inferred

## Documented Architecture

- Deterministic, config-driven MVP pipeline and artifact model:
	`MVP_SUMMARY.md`, `SHOOTRZ/backend/mvp/README.md`, `SHOOTRZ/START_HERE.md`.
- Mobile -> backend -> run artifacts -> result polling flow:
	`SHOOTRZ/START_HERE.md`.
- Four-phase detector integration intent:
	`SHOOTRZ/MVP_PHASE_DETECTOR_INTEGRATION.md`.

## Actual Implementation

- Backend is FastAPI (not Flask app.py entry):
	`SHOOTRZ/backend/main.py` + `uvicorn backend.main:app` usage in docs.
- API endpoints are `/mvp/*`, `/chat`, `/history/*`, `/feedback/*`, `/sessions/*`:
	`SHOOTRZ/backend/routers/*.py`.
- Pipeline modules exist and are wired by `MVPPipeline.process_video`:
	`SHOOTRZ/backend/mvp/core/*.py`.
- Motion-based phase detection is called inside overlay generation path:
	`SHOOTRZ/backend/routers/mvp.py` using `PhaseDetector.detect_phases`.
- Supabase-backed data access exists:
	`SHOOTRZ/backend/storage/db.py`, `SHOOTRZ/backend/storage/supabase_client.py`.

## Documented But Not Implemented

1. `SHOOTRZ/backend/README.md` describes Flask server startup (`python app.py`) and
	`/api/analyze`, `/api/video/<video_id>`, `/api/performance`, `/api/status`, `/api/cleanup`.
	- Evidence of docs: `SHOOTRZ/backend/README.md`.
	- Evidence of implementation mismatch: active routes in
		`SHOOTRZ/backend/main.py` + `SHOOTRZ/backend/routers/mvp.py` and no such Flask `app.py`
		active module in current backend structure.
	- Status: **DOCUMENTED BUT NOT IMPLEMENTED** (or outdated docs).

2. `SHOOTRZ/backend/README.md` architecture section names modules like `pose_detector.py`,
	`angle_calculator.py`, `tip_generator.py`, `video_processor.py`, `privacy.py`, `evaluator.py`
	as core backend files.
	- Evidence of docs: `SHOOTRZ/backend/README.md`.
	- Evidence of actual code structure: core now under `SHOOTRZ/backend/mvp/core/*`,
		`SHOOTRZ/backend/inference/*`, `SHOOTRZ/backend/metrics/*`.
	- Status: **DOCUMENTED BUT NOT IMPLEMENTED** (as written in that doc).

## Partially Implemented

1. Overlay/video artifact expectations vary across docs:
	- `SHOOTRZ/START_HERE.md` output table labels `overlay.mp4` as `(future)`.
	- Actual code attempts generation in `_process_video_job` and serves via artifacts
		(`SHOOTRZ/backend/routers/mvp.py`, `SHOOTRZ/backend/utils/video_annotator.py`), but as
		best-effort with failure fallback (`overlay_video` may be set `None`).
	- Status: **PARTIALLY IMPLEMENTED** (implemented best-effort, not guaranteed).

## Inferred Architecture

- Explicit layered architecture (UI/API/AI-Processing/Scoring/Output) is not formally codified in
	a single SDD; it is reconstructed from module boundaries and call graph.
- Status: **INFERRED**.

# 9. System Flow Summary

User records/uploads basketball video in mobile app (`MVPAnalysisScreen`) -> mobile API client
posts multipart file to `POST /mvp/analyze` (`api.service.ts` -> `routers/mvp.py`) -> backend
stores queued job and runs `_process_video_job` in background -> `MVPPipeline.process_video`
executes video ingestion, pose extraction, smoothing, angle computation, shot-window detection,
metric derivation, scoring, report export -> artifacts are written to
`backend/outputs/{run_id}/` via `RunTracker` -> backend returns completed result payload at
`GET /mvp/result/{job_id}` including metrics/score/angles/artifact URLs -> mobile renders score,
metrics, graph, and optionally cached overlay video; artifacts are downloadable via
`GET /mvp/artifacts/{run_id}/{filename}`.

# 10. Inconsistencies / Gaps

1. **Backend README mismatch (major)**
	- `SHOOTRZ/backend/README.md` still documents Flask-style architecture/endpoints not matching
		current FastAPI implementation (`SHOOTRZ/backend/main.py`, `SHOOTRZ/backend/routers/*`).

2. **Mixed phase detection logic paths**
	- Core metric pipeline still uses `ShotDetector.detect_shot_window`
		(`SHOOTRZ/backend/mvp/core/shot_detection.py`) while overlay phase labels use
		`PhaseDetector.detect_phases` (`SHOOTRZ/backend/routers/mvp.py`).
	- This means metric timing source and overlay phase source are related but not identical.

3. **In-memory async job state**
	- `job_store` is process-local in `SHOOTRZ/backend/routers/mvp.py`.
	- No persistent queue/store is implemented in this path.
	- Operationally acceptable for local MVP; scale behavior is limited.

4. **No formal SRS/SDD artifact in repository**
	- Architecture exists in implementation + progress docs, but no dedicated structured SRS/SDD
		document was found.

5. **Model-folder scope ambiguity**
	- `SHOOTRZ/models/yolov8/*` and `SHOOTRZ/models/hrnet/*` include large third-party sources/docs.
	- Current MVP pipeline code path relies on MediaPipe pose + local modules; YOLO/HRNet role in
		current runtime path is not fully wired in MVP core orchestrator.

# 11. Open Questions / Uncertain Areas

1. Which production path is canonical for phase-dependent metrics?
	- `ShotDetector` window vs `PhaseDetector` phases are both present.
2. Are recommendation routes (`SHOOTRZ/backend/routers/recommendation_routes.py`) actively used
	in the current mobile UX?
3. What is the definitive backend architecture reference: `backend/README.md` or MVP docs under
	`SHOOTRZ/*MVP*.md`?
4. Which model stack is intended for production in this branch for non-MVP routes:
	MediaPipe-only, YOLO-assisted, or hybrid?
5. What persistence guarantees are required for analysis jobs (in-memory `job_store` vs durable)?

# 12. Presentation-Relevant Insights

1. **Clear, demonstrable layered architecture** exists in code:
	UI (`src`) -> API (`routers`) -> AI/CV pipeline (`mvp/core`, `inference`) -> scoring/report ->
	artifacts/output.
2. **Strong reproducibility pattern** is implemented:
	`RunTracker` + config snapshot (`config_used.yaml`) + per-run artifact folder.
3. **Evidence-rich AI pipeline** supports technical presentation:
	video metadata, frame mapping, keypoints, smoothed trajectories, angles, shot window, report,
	overlay.
4. **Architecture maturity is mixed**:
	core MVP pipeline is concrete and test-backed, while some top-level backend docs are outdated.
5. **Best presentation framing**:
	emphasize "implemented architecture with traceable outputs" and explicitly call out "doc drift"
	as an engineering governance gap discovered during analysis.