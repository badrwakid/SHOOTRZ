# Architecture vs Implementation Alignment (Evidence-Based)

## 1. Executive Summary

This audit compares intended architecture against implemented code for SHOOTRZ using:
- `presentation_analysis/01_architecture_agent.md`
- `project_analysis/02_code_mapping_agent.md` (used because `presentation_analysis/02_code_mapping_agent.md` is absent)
- `presentation_analysis/04_implementation_evidence_agent.md`
- direct verification in source/docs.

The strongest alignment is the MVP analysis backbone: mobile upload/polling -> FastAPI job processing -> deterministic pipeline -> artifact/result rendering. Major drift exists in legacy backend documentation (`SHOOTRZ/backend/README.md`) that still describes a Flask-era architecture and endpoints not matching current FastAPI runtime.

---

## 2. Architecture vs Implementation Overview

### Intended architecture (documented)

Primary intended design signals come from:
- `MVP_SUMMARY.md` (phase-based deterministic pipeline, reproducibility, React Native + FastAPI integration)
- `SHOOTRZ/START_HERE.md` (target flow: Analyze tab -> `/mvp/analyze` -> pipeline -> `/mvp/result/{job_id}`)
- `SHOOTRZ/backend/mvp/README.md` (MVP APIs, artifacts, pipeline sequence)
- `SHOOTRZ/backend/README.md` (legacy architecture, Flask components/endpoints; conflicts with current implementation)

### Actual implementation (verified)

- **Backend assembly:** `SHOOTRZ/backend/main.py` `create_app()`, `app = create_app()`
- **MVP API contract:** `SHOOTRZ/backend/routers/mvp.py` `analyze_video`, `get_result`, `get_artifact`, `_process_video_job`
- **Pipeline orchestrator:** `SHOOTRZ/backend/mvp/core/pipeline.py` `MVPPipeline.process_video`
- **Mobile integration:** `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` `handleAnalyzeVideo`; `SHOOTRZ/src/services/api.service.ts` `analyzeMVP`, `getMVPResult`
- **Chat stack:** `SHOOTRZ/backend/routers/chat.py` `chat`; `SHOOTRZ/backend/chat/context_builder.py` `build_user_context`; `SHOOTRZ/backend/chat/openai_client.py` `generate_chat_completion`
- **Data layer:** `SHOOTRZ/backend/storage/db.py` CRUD functions for users/videos/metrics/sessions

---

## 3. Component-by-Component Mapping

### A. Mobile Analysis UI
- **Architecture role:** user records/selects shot video and starts analysis.
- **Implementation equivalent:** `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` `recordVideo`, `pickVideo`, `handleAnalyzeVideo`.
- **Why mapping is correct:** screen owns media capture/select + API trigger + polling + rendering.
- **How it fulfills role:** calls `apiService.analyzeMVP` then polls `apiService.getMVPResult` until `status === 'completed'`.

### B. Backend API Gateway (MVP path)
- **Architecture role:** accept upload, enqueue processing, expose status/results/artifacts.
- **Implementation equivalent:** `SHOOTRZ/backend/routers/mvp.py` `analyze_video`, `_process_video_job`, `get_result`, `get_artifact`.
- **Why mapping is correct:** these are the exact HTTP entry points consumed by mobile.
- **How it fulfills role:** creates `job_id`, stores status in `job_store`, runs background task, serves artifacts from `backend/outputs/{run_id}`.

### C. Pipeline Orchestration Layer
- **Architecture role:** deterministic ordered processing steps.
- **Implementation equivalent:** `SHOOTRZ/backend/mvp/core/pipeline.py` `MVPPipeline.process_video`.
- **Why mapping is correct:** method wires all core modules in sequence.
- **How it fulfills role:** executes ingestion -> pose -> smoothing -> angles -> shot detection -> metrics -> report, with per-run outputs and metadata.

### D. Video Ingestion + Metadata
- **Architecture role:** load frames/video metadata, quality checks, frame mapping.
- **Implementation equivalent:** `SHOOTRZ/backend/mvp/core/video_loader.py` `VideoLoader` (invoked in `MVPPipeline.process_video`).
- **How fulfilled:** pipeline calls `load_metadata`, `load_frames`, exports `video_metadata.json` and `frame_mapping.csv`.

### E. Pose Estimation Layer
- **Architecture role:** detect body keypoints as basis for biomechanics.
- **Implementation equivalent:** `SHOOTRZ/backend/mvp/core/pose_estimation.py` `MVPPoseEstimator`; `SHOOTRZ/backend/inference/pose_2d.py` `MediaPipePoseDetector`.
- **How fulfilled:** per-frame pose extraction; exports `pose_keypoints.csv/json` and `confidence_summary.json`.

### F. Signal Processing Layer
- **Architecture role:** clean temporal noise and missing points before kinematic calculations.
- **Implementation equivalent:** `SHOOTRZ/backend/mvp/core/signal_smoothing.py` `SignalSmoother.smooth_keypoints`.
- **How fulfilled:** interpolation + smoothing; exports `pose_keypoints_smoothed.csv`.

### G. Biomechanics Computation + Scoring
- **Architecture role:** derive angles, detect shot window, compute metrics and overall score.
- **Implementation equivalent:**  
  - `SHOOTRZ/backend/mvp/core/angle_computation.py` `AngleComputer.compute_angles_per_frame`  
  - `SHOOTRZ/backend/mvp/core/shot_detection.py` `ShotDetector.detect_shot_window`  
  - `SHOOTRZ/backend/mvp/core/metrics.py` `MetricsDerivation.derive_metrics`, `compute_overall_score`
- **How fulfilled:** computes elbow/knee/wrist trajectories, shot phase frames, and metric verdicts/score.

### H. Artifact + Reproducibility Layer
- **Architecture role:** per-run outputs and reproducibility snapshots.
- **Implementation equivalent:** `SHOOTRZ/backend/mvp/core/run_tracker.py` `RunTracker`; `SHOOTRZ/backend/mvp/core/config_loader.py` `save_snapshot` call from pipeline.
- **How fulfilled:** run directory + `config_used.yaml` + generated CSV/JSON reports under `backend/outputs/{run_id}`.

### I. Overlay/Phase Annotation
- **Architecture role:** generate annotated video with phase labels.
- **Implementation equivalent:** `SHOOTRZ/backend/routers/mvp.py` overlay block using `PhaseDetector.detect_phases` and `annotate_video` from `SHOOTRZ/backend/utils/video_annotator.py`.
- **How fulfilled:** best-effort overlay generation updates artifact URL when successful.

### J. History / Sessions / Feedback / Chat / Recommendation
- **Architecture role:** broader platform services beyond MVP analysis.
- **Implementation equivalent:**  
  - `SHOOTRZ/backend/routers/history.py` (`history`, `get_history_stats`)  
  - `SHOOTRZ/backend/routers/sessions.py` (session endpoints)  
  - `SHOOTRZ/backend/routers/feedback.py` (feedback endpoints)  
  - `SHOOTRZ/backend/routers/chat.py` `chat`  
  - `SHOOTRZ/backend/routers/recommendation_routes.py` `recommend`
- **How fulfilled:** server-side endpoints exist and are included in `create_app`; frontend integration coverage varies by module.

---

## 4. Alignment Table (CORE)

| Architecture Component | Intended Role | Implementation Equivalent | Evidence | Alignment Status | Notes |
|---|---|---|---|---|---|
| Mobile analysis input + trigger | Capture/select shot and initiate analysis | `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` `handleAnalyzeVideo`, `pickVideo`, `recordVideo` | Calls `apiService.analyzeMVP` then polling loop on `getMVPResult` | ALIGNED AND IMPLEMENTED | End-to-end user path is present |
| MVP upload endpoint | Accept video and enqueue async processing | `SHOOTRZ/backend/routers/mvp.py` `analyze_video` | `@router.post("/analyze")`, writes `job_store[job_id] = {"status":"queued"}` and schedules background task | ALIGNED AND IMPLEMENTED | Core contract matches docs |
| Async processing worker | Execute pipeline and publish result | `SHOOTRZ/backend/routers/mvp.py` `_process_video_job` | Instantiates `MVPPipeline`, composes `job_store[job_id]` result payload | ALIGNED AND IMPLEMENTED | In-memory job state only |
| Pipeline orchestrator | Deterministic phase execution | `SHOOTRZ/backend/mvp/core/pipeline.py` `MVPPipeline.process_video` | Sequential calls: loader -> pose -> smoothing -> angles -> shot -> metrics | ALIGNED AND IMPLEMENTED | Strongest architecture-code alignment |
| Pose subsystem | Keypoint extraction | `SHOOTRZ/backend/mvp/core/pose_estimation.py` `MVPPoseEstimator`; `SHOOTRZ/backend/inference/pose_2d.py` `MediaPipePoseDetector` | Pipeline invokes `process_frames`, exports pose artifacts | ALIGNED AND IMPLEMENTED | MediaPipe-backed |
| Smoothing subsystem | Denoise/interpolate trajectories | `SHOOTRZ/backend/mvp/core/signal_smoothing.py` `SignalSmoother.smooth_keypoints` | Called in pipeline; writes `pose_keypoints_smoothed.csv` | ALIGNED AND IMPLEMENTED | Config-driven |
| Angle subsystem | Compute elbow/knee/wrist time series | `SHOOTRZ/backend/mvp/core/angle_computation.py` `AngleComputer.compute_angles_per_frame` | Pipeline writes `angles.csv` from computed angles | ALIGNED AND IMPLEMENTED | Wrist is proxy metric |
| Shot phase/window detector | Detect key shot frames | `SHOOTRZ/backend/mvp/core/shot_detection.py` `ShotDetector.detect_shot_window` | Called in pipeline; exports `shot_window.json` | ALIGNED AND IMPLEMENTED | Heuristic approach |
| Metrics/scoring engine | 3 metrics + weighted total score | `SHOOTRZ/backend/mvp/core/metrics.py` `derive_metrics`, `compute_overall_score` | Pipeline exports `report.json` and returns score + feedback | ALIGNED AND IMPLEMENTED | Core MVP deliverable |
| Artifact serving | Expose generated files | `SHOOTRZ/backend/routers/mvp.py` `get_artifact` | `@router.get("/artifacts/{run_id}/{filename}")` uses `FileResponse` | ALIGNED AND IMPLEMENTED | Direct run-folder serving |
| Overlay generation + phase labels | Render annotated output video | `SHOOTRZ/backend/routers/mvp.py` overlay block + `PhaseDetector.detect_phases` + `annotate_video` | Wrapped in `try/except`, fallback phase mode, may set `overlay_video=None` on error | PARTIALLY ALIGNED | Implemented as best-effort, not guaranteed |
| FastAPI app composition | Register routers/services in one backend app | `SHOOTRZ/backend/main.py` `create_app` | `app.include_router(...)` for mvp/chat/history/feedback/sessions/recommendation | ALIGNED AND IMPLEMENTED | Actual backend is FastAPI |
| History backend | Serve user analysis history + stats | `SHOOTRZ/backend/routers/history.py` (`history`, `get_history_stats`) | Uses `get_user_history`/`get_video_metrics` from `storage/db.py` | ALIGNED AND IMPLEMENTED | API exists |
| Progress/history frontend | Display real historical session analytics | `SHOOTRZ/src/screens/ProgressScreen.tsx` `loadSessions` | Contains `mockSessions: Session[] = []` with comment "replace with actual API call" | DOCUMENTED BUT NOT IMPLEMENTED | UI is placeholder for backend data |
| Chat coaching service | Personalized coaching with context + LLM | `SHOOTRZ/backend/routers/chat.py` `chat`; `context_builder.py`; `openai_client.py` | `/chat` endpoint builds context and calls OpenAI completion | ALIGNED AND IMPLEMENTED | Requires auth + API key |
| Recommendation service | Recommend drill from user vector/context | `SHOOTRZ/backend/routers/recommendation_routes.py` `recommend` | Endpoint exists, loads recommender, returns drill recommendation | PARTIALLY ALIGNED | Backend exists; active frontend usage not evidenced |
| Legacy Flask API architecture | Flask app + `/api/*` endpoints and old modules | `SHOOTRZ/backend/README.md` (`app.py`, `/api/analyze`, etc.) | Conflicts with `backend/main.py` and `/mvp/*` runtime routes | IMPLEMENTED DIFFERENTLY THAN DESIGNED | Documentation drift from older architecture |

---

## 5. Architecture Drift Analysis

### 5.1 Where implementation deviates from design

1. **Flask-era design drifted to FastAPI runtime**
   - Design evidence: `SHOOTRZ/backend/README.md` references `app.py`, Flask stack, `/api/analyze`.
   - Runtime evidence: `SHOOTRZ/backend/main.py` + `SHOOTRZ/backend/routers/mvp.py` expose FastAPI `/mvp/*`.
   - Likely reason: architecture evolution during implementation; docs not fully updated.

2. **Phase logic split between scoring path and overlay path**
   - Scoring uses `ShotDetector.detect_shot_window` in `pipeline.py`.
   - Overlay labels use `PhaseDetector.detect_phases` in `routers/mvp.py` with fallback.
   - Likely reason: incremental introduction of refined phase detector without replacing existing metric path.

3. **Async job state is process-local**
   - Evidence: `job_store` dict in `SHOOTRZ/backend/routers/mvp.py`.
   - Likely reason: MVP speed/simplicity; persistent queue/store deferred.

### 5.2 Where design was simplified

- **History/progress UI integration simplified to placeholder**
  - `ProgressScreen.loadSessions` uses mock array.
  - Likely reason: prioritization of MVP analysis pipeline over analytics dashboard completion.

- **Overlay treated as optional**
  - `overlay_video` can be `None` if annotation fails.
  - Likely reason: preserve successful numeric analysis even when rendering fails.

### 5.3 Where implementation evolved beyond design

- **Additional platform services beyond MVP path**
  - Chat context + LLM (`chat.py`, `context_builder.py`, `openai_client.py`)
  - Recommendation endpoint (`recommendation_routes.py`)
  - Session/history APIs (`sessions.py`, `history.py`)
  - Likely reason: feature expansion for full product vision around MVP core.

### 5.4 Where architecture exists but code does not (as documented)

- Legacy documented modules like `pose_detector.py`, `tip_generator.py`, `video_processor.py` in `backend/README.md` are not current architecture modules in active path.
- Current code reorganized under `backend/mvp/core/*`, `backend/inference/*`, `backend/routers/*`.

---

## 6. Undocumented Implementation

The following implemented behavior is not clearly represented in legacy architecture docs:

1. **Current FastAPI router composition**
   - `SHOOTRZ/backend/main.py` `create_app` includes `mvp`, `chat`, `history`, `feedback`, `sessions`, `recommendation_router`.

2. **Deterministic per-run artifact governance**
   - `SHOOTRZ/backend/mvp/core/run_tracker.py` and config snapshot save in `pipeline.py`.

3. **Dual-context AI chat orchestration**
   - `SHOOTRZ/backend/chat/context_builder.py` merges server history + local client context.

4. **Phase detector integration with runtime fallback**
   - `SHOOTRZ/backend/routers/mvp.py` records detector version (`motion_based_v2` or `fallback`) and continues service.

---

## 7. Implementation Gaps

1. **Progress/history screen not connected to backend**
   - `SHOOTRZ/src/screens/ProgressScreen.tsx` uses mock sessions.
   - Gap type: frontend integration gap.

2. **Recommendation flow lacks proven frontend consumption**
   - Backend endpoint exists (`recommendation_routes.py`), but active invocation from mobile runtime was not evidenced in analyzed screens/services.
   - Gap type: cross-layer integration gap.

3. **Legacy endpoints in client service remain non-implemented**
   - `SHOOTRZ/src/services/api.service.ts` methods `getPerformanceMetrics`, `getSystemStatus`, `forceCleanup` explicitly return null/false with warnings.
   - Gap type: API contract inconsistency/legacy residue.

4. **Durability/scalability gap for jobs**
   - In-memory `job_store` means no persistence across process restart.
   - Gap type: operational architecture gap.

---

## 8. Final Alignment Summary

### Fully aligned (strongest parts)
- Mobile analysis UI -> MVP backend API -> deterministic processing pipeline -> result/artifact delivery.
- Core modules for pose, smoothing, angle extraction, shot window detection, metrics scoring are wired and functioning in one path (`MVPPipeline.process_video`).
- FastAPI assembly and endpoint structure match the active runtime model.

### Partially implemented
- Overlay phase annotation is best-effort with fallback.
- Recommendation, history/session/feedback ecosystem exists server-side but not uniformly demonstrated in frontend UX.
- Progress analytics UI exists but data layer wiring is unfinished.

### Missing or not implemented (against documented expectations)
- Legacy Flask architecture and `/api/*` endpoint set documented in `backend/README.md` are not the implemented runtime.
- Some client legacy methods explicitly indicate unimplemented FastAPI equivalents.

### Changed from original/legacy design
- Architecture shifted from monolithic Flask-style module layout to modular FastAPI + MVP core pipeline + additional service routers.

---

## 9. Presentation-Ready Insights

### Strongest alignment points to highlight
- **Traceable deterministic pipeline:** `MVPPipeline.process_video` shows explicit, staged processing and reproducible artifacts.
- **Real end-to-end path:** `MVPAnalysisScreen.handleAnalyzeVideo` -> `/mvp/analyze` -> `/mvp/result/{job_id}`.
- **Evidence-rich outputs:** structured CSV/JSON artifacts under `backend/outputs/{run_id}`.

### Acceptable deviations (defensible framing)
- **FastAPI migration vs Flask docs:** frame as architectural modernization where implementation advanced faster than documentation updates.
- **Best-effort overlay:** frame as resilience design (core scoring still delivered even if rendering fails).
- **In-memory jobs:** frame as MVP trade-off for delivery speed before production hardening.

### Risky areas (prepare defense)
- Progress screen currently uses mock data.
- Legacy API methods remain in client service.
- Recommendation feature may be perceived as incomplete without UI integration evidence.
- Documentation governance gap can cause reviewer confusion unless explicitly acknowledged.

---

## 10. Open Questions / Uncertain Areas

1. Is there an intended immediate migration plan to durable job orchestration (Redis/queue) beyond `job_store`?
2. Which phase source is canonical for future scoring: `ShotDetector` windows or `PhaseDetector` segments?
3. Which frontend screen(s) are intended to consume `/api/recommend` in the current milestone?
4. Should `SHOOTRZ/backend/README.md` be formally deprecated or rewritten to current FastAPI architecture to remove ambiguity?