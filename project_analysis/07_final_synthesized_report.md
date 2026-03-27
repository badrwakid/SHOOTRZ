# 1. Executive Summary

SHOOTRZ has a strong, evidence-backed MVP core: mobile video upload triggers a FastAPI background job, which runs a deterministic AI/CV + biomechanics pipeline and returns scored results with artifacts. This core path is consistently supported across the available analysis reports.

- **Most defensible claim:** the MVP analysis flow is truly implemented end-to-end.
- **Primary architecture reality:** FastAPI backend + React Native frontend + deterministic processing modules.
- **Main governance gap:** legacy backend documentation describes an older Flask architecture that does not match current runtime.
- **Main delivery gap:** some platform features (progress/history UI integration, recommendation UX integration, advanced CV modules) are only partial or not in the default MVP execution path.

Missing input file:
- `presentation_analysis/02_code_mapping_agent.md` was not found.
- Reconstruction used `project_analysis/02_code_mapping_agent.md` as fallback where needed, and claims were retained only when consistent with the other presentation-analysis files.

# 2. Final Consolidated Architecture View

## Major Layers and Components

1. **Mobile/UI layer**
	- `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx`
	- `SHOOTRZ/src/services/api.service.ts`
	- Role: capture/select video, upload, poll status, render score/metrics/overlay.

2. **Backend API layer (FastAPI)**
	- `SHOOTRZ/backend/main.py` (`create_app`, router inclusion)
	- `SHOOTRZ/backend/routers/mvp.py` (`analyze_video`, `_process_video_job`, `get_result`, `get_artifact`)
	- Role: ingest uploads, dispatch background processing, expose results/artifacts.

3. **AI/CV and biomechanics processing layer**
	- Orchestrator: `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`)
	- Core modules: `video_loader.py`, `pose_estimation.py`, `signal_smoothing.py`, `angle_computation.py`, `shot_detection.py`, `metrics.py`
	- Supporting phase module: `SHOOTRZ/backend/inference/phase_detector.py` (+ `motion_analyzer.py`) for overlay labeling path.

4. **Artifact and persistence layer**
	- `SHOOTRZ/backend/mvp/core/run_tracker.py`
	- `SHOOTRZ/backend/mvp/core/config_loader.py` snapshot behavior
	- `SHOOTRZ/backend/storage/db.py`, `supabase_client.py`
	- Role: per-run outputs, reproducibility artifacts, user/session/history persistence APIs.

5. **Ancillary service layer**
	- Chat: `backend/routers/chat.py`, `chat/context_builder.py`, `chat/openai_client.py`
	- Recommendation: `backend/routers/recommendation_routes.py` + recommender modules
	- Sessions/history/feedback routes present, frontend usage uneven.

## Consolidated Data Flow

1. Mobile screen triggers `analyzeMVP` upload.
2. Backend `/mvp/analyze` creates `job_id`, sets in-memory status, runs background task.
3. Background task executes `MVPPipeline.process_video` stages:
	- metadata/frames -> pose keypoints -> smoothing -> angles -> shot window -> metrics/score/report.
4. Router optionally runs phase detection + overlay annotation (best effort).
5. Client polls `/mvp/result/{job_id}` until completed, then renders outputs and optionally downloads overlay artifact.
6. Artifacts are served via `/mvp/artifacts/{run_id}/{filename}`.

## Architecture Intent vs Implemented Reality

- **Intent (from MVP docs):** deterministic, explainable shot analysis with artifacts and client polling.
- **Reality:** this intent is implemented for the MVP path.
- **Drift:** legacy `backend/README.md` describes Flask-era modules/endpoints not matching current FastAPI runtime.

# 3. Final Technical Background

## Confirmed Methods Used in Active MVP Path

1. **Pose extraction**
	- MediaPipe Pose (`MediaPipePoseDetector`) in `backend/inference/pose_2d.py`.
	- Used through `MVPPoseEstimator` in `backend/mvp/core/pose_estimation.py`.

2. **Temporal signal conditioning**
	- Confidence-based missing point handling + interpolation + Savitzky-Golay smoothing in `signal_smoothing.py`.

3. **Biomechanical feature extraction**
	- Angle computation via explicit vector geometry (`joint_angle` style math) in `angle_computation.py` and `metrics/biomechanics.py`.

4. **Shot segmentation**
	- Heuristic shot window detection from kinematic extrema in `shot_detection.py` (crouch/release framing).

5. **Scoring**
	- Rule-based metric derivation + weighted overall score in `metrics.py`, with config-driven ranges/weights (`config/mvp_config.yaml`).

6. **Phase labeling (overlay path)**
	- Motion-based phase detector (`phase_detector.py`) with motion signals (`motion_analyzer.py`), used in router overlay flow.

## Frameworks / Models Confirmed

- **Backend framework:** FastAPI (`backend/main.py`, routers).
- **Frontend framework:** React Native/Expo (from file paths and analysis sources).
- **Primary CV model in MVP runtime:** MediaPipe Pose.
- **Optional/expansion modules present but non-default in MVP path:** YOLO modules, 3D lifting wrappers, hand/grip modules.

## Why These Choices Fit This Project

- Deterministic post-processing and scoring improves explainability for coaching and viva defense.
- Intermediate artifacts (`pose_keypoints`, smoothed data, angles, shot window, report, config snapshot) support traceability and reproducibility.
- Hybrid design (pretrained perception + deterministic logic) reduces dependence on large labeled datasets for end-to-end learned scoring.

## Limitations and Simplifications (Evidence-Based)

- Core scoring is 2D-pose based (depth not fully modeled in default path).
- Shot/phase boundaries rely on heuristics and thresholds.
- Overlay generation is best-effort, not guaranteed each run.
- In-memory `job_store` limits durability/scalability compared with persistent job queues.
- Advanced modules exist but are not the default runtime path of MVP analysis.

# 4. Final Architecture vs Implementation Alignment

## ALIGNED AND IMPLEMENTED

- Mobile upload/poll/render flow maps cleanly to backend `/mvp/*` endpoints.
- `MVPPipeline.process_video` implements documented deterministic stage sequence.
- Core pipeline modules (video, pose, smoothing, angles, shot detection, metrics) are wired and producing artifacts.
- Artifact serving path is implemented.
- Chat backend path is implemented (with auth/env dependency constraints).

## PARTIALLY ALIGNED

- Overlay phase labeling is integrated but fallback/best-effort.
- History/sessions/feedback services exist server-side; full frontend integration is not consistently evidenced.
- Recommendation route exists, but active frontend consumption is not strongly evidenced in main flow.

## DOCUMENTED BUT NOT IMPLEMENTED (or outdated docs)

- Legacy backend README architecture and Flask endpoint set do not match current runtime.
- Some frontend progress/history behavior remains mock/placeholder despite backend endpoints existing.

## IMPLEMENTED DIFFERENTLY THAN DESIGNED

- Historical design narrative (Flask-style app and old module names) evolved into modular FastAPI + `mvp/core/*` architecture.
- Phase logic currently split: shot detection path for scoring vs phase detector path for overlay labeling.

## Strongest Alignment Evidence

- Cross-file consistency on the MVP path from UI trigger to pipeline to result polling.
- Direct mapping between intended MVP architecture docs and `MVPPipeline` sequence.
- Artifact-based outputs confirm concrete execution stages.

## Major Deviations / Gaps

- Documentation drift (Flask vs FastAPI).
- In-memory async job state only.
- Partial productization around recommendation/progress analytics.

# 5. Final Technical Background Table

| Component | Technique / Method | Evidence | Why It Matters |
|---|---|---|---|
| Pose estimation | MediaPipe Pose 2D landmarks | `backend/inference/pose_2d.py`, `mvp/core/pose_estimation.py` | Provides core body keypoints for biomechanics |
| Side determination | Wrist-trajectory heuristic | `mvp/core/pose_estimation.py` | Enables side-specific joint metrics |
| Missing data handling | Confidence masking + interpolation | `mvp/core/signal_smoothing.py` | Stabilizes trajectories under occlusion/dropout |
| Denoising | Savitzky-Golay smoothing | `mvp/core/signal_smoothing.py` | Reduces jitter before extrema/angles |
| Kinematics | Vector geometry angle computation | `mvp/core/angle_computation.py`, `metrics/biomechanics.py` | Transparent and defensible biomechanics math |
| Shot event windowing | Heuristic crouch/release detection | `mvp/core/shot_detection.py` | Anchors metric extraction in shot timeline |
| Metric scoring | Rule-based thresholds + weighted aggregate | `mvp/core/metrics.py`, `config/mvp_config.yaml` | Explainable coach-facing score generation |
| Phase annotation | Motion-signal phase detector with fallback | `inference/phase_detector.py`, `inference/motion_analyzer.py`, `routers/mvp.py` | Adds interpretable phase labels to overlay |
| Reproducibility artifacts | Per-run outputs + config snapshot | `mvp/core/run_tracker.py`, `mvp/core/config_loader.py` | Enables evidence, debugging, and repeatability |

# 6. Final Alignment Table

| Architecture Component | Implementation Equivalent | Status | Evidence | Notes |
|---|---|---|---|---|
| Mobile analysis entry | `MVPAnalysisScreen` + `api.service.ts` | ALIGNED AND IMPLEMENTED | `src/screens/MVPAnalysisScreen.tsx`, `src/services/api.service.ts` | Upload + polling + rendering are wired |
| MVP analyze API | `routers/mvp.py` upload/result/artifact routes | ALIGNED AND IMPLEMENTED | `backend/routers/mvp.py`, `backend/main.py` | Core API contract is active |
| Async job execution | `_process_video_job` + `job_store` | ALIGNED AND IMPLEMENTED | `backend/routers/mvp.py` | MVP-appropriate, non-durable |
| Core processing pipeline | `MVPPipeline.process_video` | ALIGNED AND IMPLEMENTED | `backend/mvp/core/pipeline.py` | Strongest architecture-code alignment |
| Pose/smoothing/angles/metrics modules | `mvp/core/*.py` chain | ALIGNED AND IMPLEMENTED | `pipeline.py` + module files | Deterministic staged sequence |
| Overlay phase video | `PhaseDetector` + `annotate_video` path | PARTIALLY ALIGNED | `backend/inference/phase_detector.py`, `backend/routers/mvp.py` | Best-effort with fallback |
| History/session/feedback platform services | Corresponding backend routers | PARTIALLY ALIGNED | `backend/routers/history.py`, `sessions.py`, `feedback.py` | Backend exists; frontend consumption uneven |
| Recommendation flow | `/api/recommend` backend route | PARTIALLY ALIGNED | `backend/routers/recommendation_routes.py` | UX integration not strongly evidenced |
| Progress analytics UX | `ProgressScreen` | DOCUMENTED BUT NOT IMPLEMENTED | `src/screens/ProgressScreen.tsx` | Uses mock session loading in analysis evidence |
| Legacy backend architecture docs | Flask-style README content | IMPLEMENTED DIFFERENTLY THAN DESIGNED | `backend/README.md` vs `backend/main.py` | Documentation drift risk |

# 7. Contradictions / Weak Claims to Verify

## Contradictions Between Prior Analyses

1. **Overlay feature status wording differs**
	- Conflict:
		- `presentation_analysis/04_implementation_evidence_agent.md` labels overlay as fully implemented end-to-end.
		- `presentation_analysis/01_architecture_agent.md` and `presentation_analysis/05_alignment_agent.md` emphasize best-effort/fallback behavior.
	- Stronger interpretation: **partially aligned operational guarantee** (implemented path exists, but not guaranteed every run).
	- Why stronger: multiple files mention explicit fallback and optional `overlay_video` behavior.
	- Verification needed: inspect current `routers/mvp.py` runtime branch behavior in latest commit.

2. **History/session/feedback status varies by perspective**
	- Conflict:
		- Some analyses treat backend endpoints as implemented/aligned.
		- Others mark feature as partial due to weak frontend integration.
	- Stronger interpretation: **backend implemented, product integration partial**.
	- Why stronger: both claims can coexist; endpoint existence does not imply complete UX integration.
	- Verification needed: check actual frontend calls across all screens/services for these endpoints.

## Weak or Unsupported Claims to Avoid

1. **“YOLO/3D/hand modules are part of current MVP runtime”**
	- Weakness: analyses repeatedly state these modules exist but are not default pipeline path.
	- Safer claim: these are extension paths / partial implementations.

2. **“Recommendation is live in user flow”**
	- Weakness: backend exists, frontend integration not strongly evidenced.
	- Safer claim: backend recommendation capability exists; user-flow integration remains partial.

3. **“Architecture is fully documented and synchronized”**
	- Weakness: legacy README mismatch is repeatedly documented.
	- Safer claim: implementation is strong; architecture docs need synchronization.

# 8. Recommended Presentation Outline — Technical Background

1. **Problem and technical objective**
	- Focus on explainable basketball shot analysis from video.

2. **Pipeline philosophy**
	- Hybrid design: pretrained perception + deterministic biomechanics logic.

3. **Step-by-step AI/CV pipeline**
	- Pose extraction -> smoothing -> angle math -> shot window -> scoring.

4. **Mathematical and rule logic**
	- Briefly show angle geometry and scoring ranges/weights.

5. **Artifact traceability**
	- Show how each stage exports evidence files for reproducibility.

6. **Limitations and boundaries**
	- 2D constraints, heuristic thresholds, best-effort overlay, in-memory job state.

Strongest points to include:
- Deterministic orchestrator and stage evidence.
- Explicit noise handling and transparent math.
- Config-driven weighted scoring and run artifacts.

Weaker points to avoid over-emphasizing:
- Full production use of YOLO/3D/hand modules.
- Claims of complete advanced analytics integration.

# 9. Recommended Presentation Outline — Architecture vs Implementation

1. **Intended architecture snapshot**
	- Mobile, API, processing, artifact/persistence layers.

2. **Implementation mapping table**
	- One slide mapping architecture components to concrete files/functions.

3. **End-to-end proof path**
	- UI action -> `/mvp/analyze` -> background pipeline -> `/mvp/result` -> render.

4. **Aligned core**
	- Emphasize MVP path completeness and reproducibility artifacts.

5. **Partial and divergent areas**
	- Overlay reliability mode, progress/recommendation integration gaps.

6. **Engineering honesty slide**
	- Legacy doc drift and MVP trade-offs (in-memory jobs), plus forward plan.

Strongest mappings to highlight:
- `MVPAnalysisScreen` <-> `routers/mvp.py` <-> `MVPPipeline.process_video`.
- `mvp/core/*` stage boundaries.
- Artifact generation/serving loop.

Weaker mappings to soften:
- Recommendation as “available backend capability, partial UX integration.”
- Progress/history as “in progress on frontend integration.”

# 10. Likely Examiner Questions

1. **How is your scoring scientifically defensible without end-to-end ML?**
	- Why ask: methodology rigor.
	- Answer direction: deterministic angle-based metrics, config-defined thresholds/weights, reproducible artifacts.

2. **How do you handle noisy pose estimates?**
	- Why ask: robustness.
	- Answer direction: confidence gating, interpolation, Savitzky-Golay smoothing before kinematic extraction.

3. **How do you detect shot phases/events?**
	- Why ask: temporal validity.
	- Answer direction: distinguish scoring shot window (`ShotDetector`) from overlay phase labeling (`PhaseDetector`).

4. **Can you prove architecture is implemented, not only designed?**
	- Why ask: implementation credibility.
	- Answer direction: trace concrete call chain from mobile screen to API routes to pipeline to result rendering.

5. **Why do docs mention Flask while code uses FastAPI?**
	- Why ask: engineering governance.
	- Answer direction: acknowledge architecture evolution; current source of truth is FastAPI code; docs need sync.

6. **Is your system production-ready under restart/load?**
	- Why ask: operational maturity.
	- Answer direction: current MVP uses in-memory job state; durable queue/store is a known next hardening step.

7. **Are advanced modules (YOLO/3D) active now?**
	- Why ask: detect overclaim.
	- Answer direction: present as implemented extensions, not core default MVP runtime.

8. **Is recommendation/progress fully integrated in user journey?**
	- Why ask: product completeness.
	- Answer direction: backend capabilities exist; frontend integration is partial and explicitly tracked as future work.

# 11. Final Defense Guidance

## Strongest Claims You Can Confidently Make

- The MVP analysis loop is implemented end-to-end and testable through actual app/API flow.
- Core technical method is explainable, deterministic, and traceable with exported artifacts.
- Architecture-to-code alignment is strongest in the MVP pipeline path.

## Safest Wording for Uncertain Areas

- “Implemented as an extension path” for YOLO/3D/hand modules.
- “Backend capability exists; frontend integration is partial” for recommendation/history-related UX.
- “Best-effort with fallback” for overlay generation.
- “Known MVP trade-off” for in-memory asynchronous job state.

## What Not to Overclaim

- Do not claim full production-scale orchestration durability.
- Do not claim full architecture-document synchronization.
- Do not claim advanced CV modules are default runtime in current MVP flow.
- Do not claim complete progress analytics integration in current frontend.

## How to Frame Deviations Positively and Honestly

- Documentation drift: frame as normal evolution from legacy architecture to modernized FastAPI implementation.
- Partial integrations: frame as staged roadmap after core MVP validation.
- In-memory job store: frame as speed-of-delivery decision suitable for MVP, with clear next hardening step.

# 12. Open Questions / Missing Evidence

1. `presentation_analysis/02_code_mapping_agent.md` is missing; synthesis used fallback evidence from `project_analysis/02_code_mapping_agent.md`.
2. `presentation_analysis/06_presentation_evidence_agent.md` is available and consistent, but references the same missing `presentation_analysis/02_code_mapping_agent.md` fallback.
3. Current runtime availability of optional model assets (YOLO fine-tuned weights, 3D lifting model files) is not execution-verified in this synthesis.
4. Full frontend consumption mapping for all non-MVP backend routes (history/sessions/feedback/recommendation) needs a targeted code walk-through to eliminate residual uncertainty.
5. Formal SRS/SDD/UML architecture baselines are not identified in the available evidence set; architecture confidence is primarily code-derived plus project markdowns.
