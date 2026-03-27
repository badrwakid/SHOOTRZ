# 1. Executive Summary

SHOOTRZ’s most defensible technical narrative is a working, deterministic MVP pipeline: mobile upload -> FastAPI background job -> pose-based analysis -> scored output + artifacts.

- The core pipeline is clearly implemented in `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`) and exposed by `SHOOTRZ/backend/routers/mvp.py` (`analyze_video`, `get_result`, `get_artifact`).
- The strongest technical background evidence is MediaPipe-based 2D pose + signal smoothing + geometric angle computation + heuristic shot-window detection + rule-based weighted scoring.
- Architecture-to-implementation alignment is strong in the MVP path, but there is documented drift in `SHOOTRZ/backend/README.md` (legacy Flask architecture vs current FastAPI runtime in `SHOOTRZ/backend/main.py`).
- The safest presentation strategy is to emphasize what is fully wired today, while explicitly labeling partial modules (recommendation frontend wiring, progress screen integration, advanced CV modules in non-default runtime path).

Primary evidence set:
- `presentation_analysis/01_architecture_agent.md`
- `project_analysis/02_code_mapping_agent.md` (fallback because `presentation_analysis/02_code_mapping_agent.md` is missing)
- `presentation_analysis/03_ai_cv_background_agent.md`
- `presentation_analysis/04_implementation_evidence_agent.md`
- `presentation_analysis/05_alignment_agent.md`

# 2. Slide-Ready Technical Background Facts

1) **Pipeline design is deterministic and stage-based, not black-box end-to-end ML.**  
Evidence: `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`) sequentially calls video loading, pose estimation, smoothing, angle computation, shot detection, metrics/scoring; confirmed in `presentation_analysis/03_ai_cv_background_agent.md`.  
Why it matters: supports explainability and easy defense during viva.

2) **Core perception method is MediaPipe Pose (33 landmarks).**  
Evidence: `SHOOTRZ/backend/inference/pose_2d.py` (`MediaPipePoseDetector`, `BASKETBALL_KEYPOINTS`), invoked via `SHOOTRZ/backend/mvp/core/pose_estimation.py` (`MVPPoseEstimator.process_frames`).  
Why it matters: provides full-body landmarks needed for shooting biomechanics.

3) **Temporal denoising is explicitly implemented before kinematic calculations.**  
Evidence: `SHOOTRZ/backend/mvp/core/signal_smoothing.py` (`SignalSmoother._interpolate_missing`, `SignalSmoother._apply_savgol`), plus confidence-threshold logic in the same module.  
Why it matters: reduces jitter and prevents unstable downstream angles/events.

4) **Angle computation uses explicit vector geometry, not implicit model outputs.**  
Evidence: `SHOOTRZ/backend/metrics/biomechanics.py` (`joint_angle`) and `SHOOTRZ/backend/mvp/core/angle_computation.py` (`AngleComputer`).  
Why it matters: mathematically transparent and easy to justify academically.

5) **Shot event segmentation in MVP is heuristic (knee minima + wrist peak).**  
Evidence: `SHOOTRZ/backend/mvp/core/shot_detection.py` (`ShotDetector._detect_crouch`, `_detect_release`, `detect_shot_window`).  
Why it matters: practical and robust enough for MVP, but should be framed as heuristic.

6) **Scoring is rule-based and weighted (3 metrics), not a trained scoring regressor.**  
Evidence: `SHOOTRZ/backend/mvp/core/metrics.py` (`derive_metrics`, `compute_overall_score`), weights/ranges in `SHOOTRZ/backend/config/mvp_config.yaml`.  
Why it matters: high interpretability and controllable scoring behavior.

7) **Motion-based phase detector exists and is used in overlay labeling path.**  
Evidence: `SHOOTRZ/backend/inference/phase_detector.py` (`PhaseDetector.detect_phases`), called in `SHOOTRZ/backend/routers/mvp.py` before `annotate_video`; summarized in `presentation_analysis/05_alignment_agent.md`.  
Why it matters: strengthens phase-level explainability in demos.

8) **Per-run artifact persistence is implemented for reproducibility.**  
Evidence: `SHOOTRZ/backend/mvp/core/run_tracker.py` (`RunTracker`), config snapshots via `SHOOTRZ/backend/mvp/core/config_loader.py`; outputs under `SHOOTRZ/backend/outputs/{run_id}`.  
Why it matters: enables evidence-driven debugging and repeatability claims.

9) **Overlay generation is integrated but best-effort.**  
Evidence: `SHOOTRZ/backend/routers/mvp.py` overlay block with fallback; renderer in `SHOOTRZ/backend/utils/video_annotator.py` (`annotate_video`).  
Why it matters: visual interpretability is available without blocking core numeric outputs.

10) **Advanced modules (YOLO ball tracking, YOLO pose, 3D lifting, hand/grip) exist but are not default MVP path.**  
Evidence: `SHOOTRZ/backend/inference/ball_tracker.py`, `yolo_pose_detector.py`, `lift_3d.py`, `hands_2d.py`; not wired in `MVPPipeline.process_video` path per `project_analysis/02_code_mapping_agent.md` and `presentation_analysis/03_ai_cv_background_agent.md`.  
Why it matters: accurate scope framing avoids overclaiming.

# 3. Slide-Ready Architecture vs Implementation Facts

1) **Mobile analysis flow is implemented exactly as architecture intent.**  
Evidence: `SHOOTRZ/src/screens/MVPAnalysisScreen.tsx` (`handleAnalyzeVideo`) + `SHOOTRZ/src/services/api.service.ts` (`analyzeMVP`, `getMVPResult`) + `/mvp/*` backend routes.  
Alignment status: **Aligned**.  
Why it matters: end-to-end feature credibility.

2) **Backend API gateway for MVP is fully implemented in FastAPI.**  
Evidence: `SHOOTRZ/backend/main.py` (`create_app`, router inclusion), `SHOOTRZ/backend/routers/mvp.py`.  
Alignment status: **Aligned**.  
Why it matters: clear service boundary and operational entry points.

3) **Deterministic core pipeline matches documented MVP processing stages.**  
Evidence: `SHOOTRZ/backend/mvp/core/pipeline.py`; documented sequence in `SHOOTRZ/backend/mvp/README.md` and `MVP_SUMMARY.md`.  
Alignment status: **Aligned**.  
Why it matters: strong architecture-to-code traceability.

4) **Artifact management and retrieval are concretely implemented.**  
Evidence: `RunTracker` in `run_tracker.py`, `/mvp/artifacts/{run_id}/{filename}` in router.  
Alignment status: **Aligned**.  
Why it matters: supports reproducibility and demo-readiness.

5) **Overlay phase labels are integrated, but resilience fallback indicates partial hard guarantees.**  
Evidence: `SHOOTRZ/backend/routers/mvp.py` try/except and fallback phase path.  
Alignment status: **Partially aligned**.  
Why it matters: honest framing of robustness trade-off.

6) **History/session/feedback backend services exist, but frontend consumption is uneven.**  
Evidence: backend routers `history.py`, `sessions.py`, `feedback.py`; `ProgressScreen` mock loading in `SHOOTRZ/src/screens/ProgressScreen.tsx`.  
Alignment status: **Partially aligned**.  
Why it matters: shows expansion beyond MVP but incomplete product integration.

7) **Recommendation backend exists but active mobile integration is not evidenced.**  
Evidence: `SHOOTRZ/backend/routers/recommendation_routes.py`; no clear active call path in analyzed frontend flow.  
Alignment status: **Partially aligned**.  
Why it matters: avoid presenting as fully delivered user feature.

8) **Legacy architecture docs are out of sync with runtime architecture.**  
Evidence: `SHOOTRZ/backend/README.md` (Flask/app.py + `/api/*`) vs `SHOOTRZ/backend/main.py` FastAPI + `/mvp/*`.  
Alignment status: **Deviation / documentation drift**.  
Why it matters: expected examiner challenge; prepare explicit explanation.

9) **Async job orchestration is implemented as in-memory store (MVP trade-off).**  
Evidence: `job_store` usage in `SHOOTRZ/backend/routers/mvp.py`.  
Alignment status: **Aligned for MVP scope, limited for production scale**.  
Why it matters: clear technical debt with easy justification.

10) **Formal SRS/SDD artifacts are not present; architecture is mostly implementation-inferred.**  
Evidence: absence noted in `presentation_analysis/01_architecture_agent.md`; architecture reconstructed from code modules and call graph.  
Alignment status: **Inferred architecture baseline**.  
Why it matters: be explicit about evidence source type in presentation.

# 4. Technical Background Table

| Component | Technique Used | Why It Was Used | Evidence |
|---|---|---|---|
| Pose extraction | MediaPipe Pose 33-landmark detection | Full-body joints for biomechanics | `SHOOTRZ/backend/inference/pose_2d.py` (`MediaPipePoseDetector`), `mvp/core/pose_estimation.py` |
| Side detection | Wrist-height heuristic | Choose left/right side-specific metrics | `mvp/core/pose_estimation.py` (`determine_shooting_side`) |
| Missing-data handling | Confidence masking + interpolation | Handle temporary landmark dropouts | `mvp/core/signal_smoothing.py` (`_interpolate_missing`) |
| Trajectory smoothing | Savitzky-Golay filter | Reduce frame-level jitter before derivatives/extrema | `mvp/core/signal_smoothing.py` (`_apply_savgol`) |
| Angle features | Vector-angle geometry (`arccos`) | Interpretable elbow/knee/wrist kinematics | `backend/metrics/biomechanics.py` (`joint_angle`), `mvp/core/angle_computation.py` |
| Shot segmentation | Knee minima + wrist peak heuristics | Detect crouch/release and shot window | `mvp/core/shot_detection.py` (`ShotDetector`) |
| Metric evaluation | Rule-based thresholds + verdict ranges | Coach-readable biomechanical assessment | `mvp/core/metrics.py` (`derive_metrics`), `config/mvp_config.yaml` |
| Overall score | Weighted aggregation with confidence influence | Single summary score for UX/presentation | `mvp/core/metrics.py` (`compute_overall_score`) |
| Phase annotation | Motion-signal phase detector + fallback | Improve interpretability of overlay video | `inference/phase_detector.py`, `routers/mvp.py`, `utils/video_annotator.py` |
| Reproducibility layer | Per-run artifacts + config snapshot | Traceability, debugging, evidence in defense | `mvp/core/run_tracker.py`, `mvp/core/config_loader.py`, `backend/outputs/{run_id}` |

# 5. Architecture vs Implementation Table

| Architecture Component | Implementation Equivalent | Status | Notes |
|---|---|---|---|
| Mobile analysis entry | `MVPAnalysisScreen` + `api.service.ts` | Implemented | Upload + poll + render loop is wired |
| MVP analyze endpoint | `backend/routers/mvp.py` (`analyze_video`) | Implemented | Accepts upload and queues background processing |
| Async processor | `_process_video_job` | Implemented | Uses in-memory `job_store` |
| Pipeline orchestrator | `MVPPipeline.process_video` | Implemented | Deterministic sequential stages |
| Pose/smoothing/angles modules | `pose_estimation.py`, `signal_smoothing.py`, `angle_computation.py` | Implemented | Core biomechanics pipeline |
| Shot detection + metrics | `shot_detection.py`, `metrics.py` | Implemented | Produces shot window + score/report |
| Artifact delivery | `get_artifact` + run tracker outputs | Implemented | Downloadable output files |
| Overlay phase video | `PhaseDetector` + `annotate_video` | Partially implemented | Best-effort, fallback path on failure |
| History/progress experience | Backend history endpoints + frontend progress screen | Partially implemented | `ProgressScreen` still uses `mockSessions` |
| Recommendation workflow | `/api/recommend` backend route | Partially implemented | Frontend consumption not evidenced in main flow |
| Backend architecture docs | `backend/README.md` | Misaligned docs | Describes legacy Flask architecture |

# 6. Strongest Technical Claims

1. The MVP analysis is a deterministic staged pipeline, not an opaque black-box model.  
Evidence: `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`).

2. The active pose backbone is MediaPipe Pose with 33 landmarks.  
Evidence: `SHOOTRZ/backend/inference/pose_2d.py`, `mvp/core/pose_estimation.py`.

3. Keypoint trajectories are cleaned by confidence-based interpolation and Savitzky-Golay smoothing.  
Evidence: `SHOOTRZ/backend/mvp/core/signal_smoothing.py`.

4. Joint angles are computed through explicit vector math.  
Evidence: `SHOOTRZ/backend/metrics/biomechanics.py` (`joint_angle`), `angle_computation.py`.

5. Shot timing is derived with explicit crouch/release heuristics from kinematic signals.  
Evidence: `SHOOTRZ/backend/mvp/core/shot_detection.py`.

6. Scoring is configurable and rule-based with weighted metrics.  
Evidence: `SHOOTRZ/backend/mvp/core/metrics.py`, `SHOOTRZ/backend/config/mvp_config.yaml`.

7. Motion-phase segmentation exists and is integrated for video annotation.  
Evidence: `SHOOTRZ/backend/inference/phase_detector.py`, call in `SHOOTRZ/backend/routers/mvp.py`.

8. The system produces traceable artifacts for every run (CSV/JSON/report/config snapshot).  
Evidence: `SHOOTRZ/backend/mvp/core/run_tracker.py`, `config_loader.py`, output structure under `backend/outputs`.

9. Mobile app and backend are connected through async job polling endpoints.  
Evidence: `MVPAnalysisScreen.tsx`, `api.service.ts`, `/mvp/analyze` + `/mvp/result/{job_id}` in router.

10. Overlay visualization is integrated into result delivery when generation succeeds.  
Evidence: `routers/mvp.py` + `utils/video_annotator.py`, UI handling in `MVPAnalysisScreen.tsx`.

# 7. Strongest Alignment Claims

1. Intended upload->analyze->poll->display flow is implemented end-to-end.  
Evidence: `src/screens/MVPAnalysisScreen.tsx`, `src/services/api.service.ts`, `backend/routers/mvp.py`.

2. FastAPI app composition reflects a modular service architecture.  
Evidence: `SHOOTRZ/backend/main.py` (`create_app`, `include_router` calls).

3. MVP core modules are cleanly separated by responsibility and wired in orchestration order.  
Evidence: `backend/mvp/core/*.py` usage inside `pipeline.py`.

4. Artifact and reproducibility design is implemented in runtime, not only documentation.  
Evidence: `run_tracker.py`, config snapshot in pipeline, output artifacts.

5. Chat architecture is implemented as context builder + model client + API route.  
Evidence: `backend/chat/context_builder.py`, `backend/chat/openai_client.py`, `backend/routers/chat.py`.

6. Supabase persistence layer exists with dedicated client/data modules.  
Evidence: `backend/storage/supabase_client.py`, `backend/storage/db.py`.

7. Phase detector integration shows incremental architecture evolution.  
Evidence: `phase_detector.py` + fallback integration in `routers/mvp.py`.

8. Recommendation service architecture exists server-side but is not fully product-integrated.  
Evidence: `backend/routers/recommendation_routes.py`; partial status in `presentation_analysis/04_implementation_evidence_agent.md`.

9. Progress analytics architecture is only partially implemented in frontend.  
Evidence: `src/screens/ProgressScreen.tsx` (`mockSessions` path).

10. Legacy backend documentation no longer matches implemented architecture.  
Evidence: `backend/README.md` vs `backend/main.py` and `backend/routers/*`.

# 8. Key Achievements

1. **Delivered a real end-to-end MVP analysis loop** from mobile capture/upload to scored results and visualization.  
Evidence: `MVPAnalysisScreen.tsx`, `api.service.ts`, `routers/mvp.py`, `pipeline.py`.

2. **Implemented an explainable biomechanics engine** with explicit formulas and thresholds.  
Evidence: `biomechanics.py`, `angle_computation.py`, `metrics.py`, `mvp_config.yaml`.

3. **Added reproducibility and traceability infrastructure** via run-level artifacts and config snapshots.  
Evidence: `run_tracker.py`, `config_loader.py`, output files in `backend/outputs/{run_id}`.

4. **Integrated motion-based phase labels into overlay generation** while preserving fallback resilience.  
Evidence: `phase_detector.py`, `routers/mvp.py`, `video_annotator.py`.

5. **Implemented authenticated AI coaching chat path** tied to user context.  
Evidence: `routers/chat.py`, `context_builder.py`, `openai_client.py`, frontend `ChatScreen.tsx`.

# 9. Limitations / Simplifications

1. **MVP scoring is 2D-pose based**; depth effects are not fully modeled in the main path.  
Evidence: active path uses `pose_2d.py` + 2D angle modules; partial 3D modules in `inference/lift_3d.py`.

2. **Shot-window and phase logic are heuristic**, sensitive to pose quality/camera setup.  
Evidence: threshold/extrema logic in `shot_detection.py`; heuristic state logic in `phase_detector.py`.

3. **Async job state is in-memory**, so restart/multi-worker durability is limited.  
Evidence: `job_store` in `backend/routers/mvp.py`.

4. **Frontend progress/history is not fully wired** to backend data retrieval.  
Evidence: `ProgressScreen.tsx` (`mockSessions`, replacement comment).

5. **Advanced modules are not in default MVP execution path** (YOLO tracking/pose, hands, 3D lifting).  
Evidence: modules in `backend/inference/*`; non-inclusion in `MVPPipeline.process_video` path (see `project_analysis/02_code_mapping_agent.md`).

# 10. Claims to Avoid or Soften

1. **Avoid:** "The platform already uses full 3D biomechanics in production."  
Soften to: "3D lifting modules exist as extension paths, while current MVP uses robust 2D biomechanics."  
Evidence: `inference/lift_3d.py` partial; active MVP path is 2D.

2. **Avoid:** "Recommendation is fully integrated in user journey."  
Soften to: "Recommendation backend exists; frontend integration is still partial."  
Evidence: `backend/routers/recommendation_routes.py`; partial integration in analysis reports.

3. **Avoid:** "Progress analytics screen is fully live from backend."  
Soften to: "Progress UI exists, with backend connection still under completion."  
Evidence: `src/screens/ProgressScreen.tsx`.

4. **Avoid:** "Architecture is fully documented and synchronized."  
Soften to: "Implementation is strong; some legacy docs still need synchronization."  
Evidence: `backend/README.md` mismatch vs `backend/main.py`.

5. **Avoid:** "Overlay generation always succeeds."  
Soften to: "Overlay is generated when possible; core numerical analysis remains available even on annotation failure."  
Evidence: fallback/best-effort logic in `backend/routers/mvp.py`.

# 11. Likely Examiner Questions

## Technical Background Questions

1) **Why did you choose rule-based scoring instead of training a single end-to-end scoring model?**  
Why they may ask: to test methodological rigor and trade-offs.  
Answer direction: emphasize interpretability, controllability, and auditable metric logic in `metrics.py` + `mvp_config.yaml`; mention this is suitable for MVP and academic defense.

2) **How do you handle noisy or missing keypoints?**  
Why they may ask: CV robustness concern.  
Answer direction: confidence thresholding + interpolation + Savitzky-Golay in `signal_smoothing.py`.

3) **How exactly are elbow/knee/wrist metrics computed?**  
Why they may ask: mathematical validity.  
Answer direction: vector-angle math in `biomechanics.py::joint_angle` and per-joint logic in `angle_computation.py`.

4) **How do you detect shot phases/events?**  
Why they may ask: event segmentation reliability.  
Answer direction: distinguish MVP `ShotDetector` for scoring (`shot_detection.py`) from motion-based `PhaseDetector` for overlay (`phase_detector.py`, router integration).

## Architecture vs Implementation Questions

5) **Can you prove the architecture is actually implemented end-to-end?**  
Why they may ask: verify non-theoretical delivery.  
Answer direction: trace `MVPAnalysisScreen` -> `api.service.ts` -> `/mvp/analyze` -> `_process_video_job` -> `MVPPipeline.process_video` -> `/mvp/result`.

6) **Why does documentation mention Flask while code uses FastAPI?**  
Why they may ask: governance and engineering maturity.  
Answer direction: acknowledge architecture evolution; current runtime source of truth is `backend/main.py`; note doc synchronization as identified technical debt.

7) **How reproducible are your results?**  
Why they may ask: scientific reliability.  
Answer direction: per-run artifact set + config snapshot under `backend/outputs/{run_id}` via `RunTracker`.

## Limitation/Risk Questions

8) **What happens if the backend restarts during analysis?**  
Why they may ask: production readiness.  
Answer direction: current MVP uses in-memory `job_store`; explain as known limitation and future durable queue/store plan.

9) **Are advanced modules (YOLO, 3D, hand/grip) fully used now?**  
Why they may ask: detect overclaiming.  
Answer direction: state clearly they are present as expansion paths; default MVP path centers on MediaPipe 2D + deterministic scoring.

10) **Is progress/history fully functional for users?**  
Why they may ask: feature completeness check.  
Answer direction: backend endpoints exist; frontend progress screen still has mock session loading and is planned integration work.

# 12. Speaking Support

## A) Technical Background Section

Key talking points:
- "Our core design is hybrid: AI for perception, deterministic logic for evaluation."
- "Every stage is explicit and traceable, from keypoints to final score."
- "We prioritized explainability over opaque scoring to make coaching feedback defensible."

Strong verbal phrases:
- "We intentionally chose a transparent biomechanics pipeline."
- "The scoring logic is configurable, auditable, and reproducible."
- "Noise handling is first-class in our pipeline through confidence filtering and temporal smoothing."

Concise technical wording:
- "MediaPipe Pose provides 33 landmarks per frame, then we perform confidence-aware interpolation and Savitzky-Golay smoothing."
- "Angles are computed through vector geometry, and shot events are segmented using kinematic extrema."
- "Final scoring is weighted rule-based aggregation defined in configuration, not hidden model behavior."

## B) Architecture vs Implementation Section

Key talking points:
- "The MVP architecture is fully connected from mobile UI to backend artifacts."
- "Our strongest alignment is the deterministic pipeline and result retrieval loop."
- "Where there is drift, we can point to it explicitly and explain why."

Strong verbal phrases:
- "What we designed for MVP is what we actually run."
- "The main deviation is documentation lag, not missing core functionality."
- "Partial modules are clearly isolated and presented as future integration, not claimed as complete."

Concise technical wording:
- "The active backend is FastAPI-based with modular routers; legacy Flask docs are retained but outdated."
- "Phase annotation is integrated as best-effort with fallback to preserve service continuity."
- "Current async orchestration uses in-memory job state, which is acceptable for MVP but not final production scale."

# 13. Open Questions / Uncertain Areas

1. `presentation_analysis/02_code_mapping_agent.md` is missing; this report used `project_analysis/02_code_mapping_agent.md` as fallback evidence.  
Impact: low, because mapping claims were cross-consistent with other presentation analyses.

2. Frontend usage coverage of recommendation/history/session endpoints is partially inferred from analyzed main flows and may miss non-primary screens/services.  
Evidence basis: `presentation_analysis/04_implementation_evidence_agent.md`, `project_analysis/02_code_mapping_agent.md`.

3. Runtime availability of optional model assets (YOLO fine-tuned files, 3D lifter weights) was not execution-validated in this pass.  
Impact: claims about those modules are intentionally softened to "partial/extension path."

4. Formal SRS/SDD artifacts were not identified; architecture confidence comes from implemented code and project markdowns.  
Evidence: `presentation_analysis/01_architecture_agent.md`.

5. Operational behavior under production-scale load (multi-worker durability, queue resilience) remains uncertain without deployment-level validation.  
Evidence: in-memory `job_store` design in `SHOOTRZ/backend/routers/mvp.py`.