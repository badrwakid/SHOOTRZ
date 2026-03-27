# Technical Background (Deep Justification) - SHOOTRZ

## 1. Executive Summary

SHOOTRZ implements a deterministic, multi-stage video analysis pipeline centered on **2D pose estimation + signal processing + rule-based biomechanics scoring**.

- **Primary implemented path (CONFIRMED):** `SHOOTRZ/backend/mvp/core/pipeline.py` → `MVPPipeline.process_video`
- **Core AI/CV in active MVP path (CONFIRMED):**
	- Pose estimation: MediaPipe Pose (`SHOOTRZ/backend/inference/pose_2d.py`, `MediaPipePoseDetector`)
	- Keypoint smoothing/interpolation: Savitzky-Golay + linear interpolation (`SHOOTRZ/backend/mvp/core/signal_smoothing.py`, `SignalSmoother`)
	- Angle computation: vector geometry (`SHOOTRZ/backend/mvp/core/angle_computation.py`, `AngleComputer`; `SHOOTRZ/backend/metrics/biomechanics.py`, `joint_angle`)
	- Shot phase windowing: knee minimum + wrist peak heuristics (`SHOOTRZ/backend/mvp/core/shot_detection.py`, `ShotDetector`)
	- Scoring/evaluation: weighted rule-based metric scoring (`SHOOTRZ/backend/mvp/core/metrics.py`, `MetricsDerivation`)
- **Additional modules exist but are not in default MVP execution path (CONFIRMED / PARTIALLY IMPLEMENTED):**
	- Motion-based phase detector (`SHOOTRZ/backend/inference/phase_detector.py`, `PhaseDetector`) used in overlay generation in `SHOOTRZ/backend/routers/mvp.py`
	- YOLOv8 ball/pose detectors (`SHOOTRZ/backend/inference/ball_tracker.py`, `detect_and_track_ball`; `SHOOTRZ/backend/inference/yolo_pose_detector.py`, `YOLOv8PoseDetector`)
	- 3D lifting wrappers and placeholders (`SHOOTRZ/backend/inference/lift_3d.py`, `lift_3d_pose`; `posemagic_lifter.py`; `hybrik_lifter.py`)

---

## 2. AI/CV Components Overview

### Pose Estimation

- **MediaPipe Pose (33 landmarks)**  
	- File: `SHOOTRZ/backend/inference/pose_2d.py`  
	- Class/Functions: `MediaPipePoseDetector`, `process_frame`, `process_video`, `BASKETBALL_KEYPOINTS`  
	- Status: **CONFIRMED (active in MVP)**

- **MediaPipe Hands (21 landmarks per hand)**  
	- File: `SHOOTRZ/backend/inference/hands_2d.py`  
	- Class/Functions: `MediaPipeHandsDetector`, `process_frame`, `detect_grip_quality`  
	- Status: **CONFIRMED module; INFERRED as non-default in MVP path**

- **YOLOv8 Pose (17 COCO keypoints)**  
	- File: `SHOOTRZ/backend/inference/yolo_pose_detector.py`  
	- Class/Functions: `YOLOv8PoseDetector`, `detect_pose_yolo`  
	- Status: **PARTIALLY IMPLEMENTED** (available, but not default in MVP pipeline)

### Object Detection / Tracking

- **YOLOv8 ball detection + ByteTrack tracking**
	- File: `SHOOTRZ/backend/inference/ball_tracker.py`
	- Function: `detect_and_track_ball` (uses `model.track(..., tracker='bytetrack.yaml')`)
	- Status: **PARTIALLY IMPLEMENTED** (not called by `MVPPipeline.process_video`)

### Segmentation

- **No project-specific segmentation pipeline found in backend execution path**
	- Evidence scan scope: `SHOOTRZ/backend/**/*.py`
	- Status: **CONFIRMED absence in active backend path**
	- Note: `SHOOTRZ/models/yolov8/...` includes upstream segmentation code/docs, but this appears to be bundled library content rather than SHOOTRZ runtime logic.

### Keypoint Processing / Signal Processing

- **Confidence-threshold missingness + interpolation + Savitzky-Golay smoothing**
	- File: `SHOOTRZ/backend/mvp/core/signal_smoothing.py`
	- Class/Functions: `SignalSmoother`, `_interpolate_missing`, `_apply_savgol`
	- Status: **CONFIRMED**

### Shot Detection / Phase Logic

- **MVP shot-window detector (crouch/release heuristics)**
	- File: `SHOOTRZ/backend/mvp/core/shot_detection.py`
	- Class/Functions: `ShotDetector`, `detect_shot_window`, `_detect_crouch`, `_detect_release`
	- Status: **CONFIRMED (active in MVP)**

- **Motion-based phase state machine (stance/crouch/release/landing)**
	- File: `SHOOTRZ/backend/inference/phase_detector.py`
	- Class/Functions: `PhaseDetector`, `detect_phases`
	- Status: **CONFIRMED (used for overlay phase annotation), PARTIALLY IMPLEMENTED for full product integration**

### Scoring / Evaluation

- **Three-metric scoring + weighted aggregation**
	- File: `SHOOTRZ/backend/mvp/core/metrics.py`
	- Class/Functions: `MetricsDerivation`, `derive_metrics`, `compute_overall_score`
	- Status: **CONFIRMED**

- **Rule-based coaching feedback engine (broader metrics set)**
	- Files: `SHOOTRZ/backend/feedback/engine.py`, `SHOOTRZ/backend/feedback/rules.py`
	- Functions: `generate_feedback`, `rules_from_metrics`, multiple `get_*_feedback`
	- Status: **CONFIRMED module; INFERRED as not central in MVP endpoint response**

### 3D Lifting / ML Models

- **3D lifting orchestrator**
	- File: `SHOOTRZ/backend/inference/lift_3d.py`
	- Functions: `lift_3d_pose`, `lift_3d_posemagic`, `lift_3d_hybrik`
	- Status: **PARTIALLY IMPLEMENTED**

- **PoseMagic / HybrIK lifters**
	- Files: `SHOOTRZ/backend/inference/posemagic_lifter.py`, `SHOOTRZ/backend/inference/hybrik_lifter.py`
	- Classes: `PoseMagicLifter`, `HybrIKLifter`
	- Status: **PARTIALLY IMPLEMENTED** (model-loading stubs + heuristic fallbacks)

---

## 3. Deep Technical Breakdown (by component)

### 3.1 MVP Orchestration

- **Technique/Method:** deterministic staged pipeline
- **Implementation evidence:** `SHOOTRZ/backend/mvp/core/pipeline.py` → `MVPPipeline.process_video`
- **Input:** `video_path`, `shooting_side`
- **Output:** `run_id`, metrics, score, shot window, artifacts (`csv/json`)
- **How it works:** sequential phases: video ingest → pose detection → smoothing → angle computation → shot detection → metric derivation/scoring.
- **Why used here:** provides reproducible basketball-shot analysis with auditable intermediate artifacts.
- **Type:** **hybrid** orchestration (pretrained vision + deterministic algorithms)

### 3.2 Pose Estimation (MediaPipe Pose)

- **Technique/Method:** MediaPipe Pose 2D landmark estimation
- **Evidence:** `SHOOTRZ/backend/inference/pose_2d.py` → `MediaPipePoseDetector.process_frame`
- **Input:** RGB/BGR frame (`np.ndarray`)
- **Output:** `landmarks` `[33,3]` + `confidence` visibility `[33]`
- **How it works:** initializes `mp.solutions.pose.Pose(...)`; runs `self.pose.process(frame_rgb)`; extracts normalized `(x,y,z)` and visibility.
- **Why used here:** full-body kinematic landmarks required for shooting joints (shoulder/elbow/wrist/hip/knee/ankle).
- **Type:** **pretrained model**

### 3.3 Pose Export + Side Detection

- **Technique/Method:** confidence-filtered side inference + coordinate normalization/persistence
- **Evidence:** `SHOOTRZ/backend/mvp/core/pose_estimation.py` → `MVPPoseEstimator.determine_shooting_side`, `export_pose_keypoints_csv`
- **Input:** per-frame landmarks/confidence from MediaPipe
- **Output:** detected side (`left/right`), keypoint CSV/JSON
- **How it works:** compares minimum Y (highest point) reached by left vs right wrist under confidence threshold.
- **Why used here:** all downstream angle formulas are side-specific.
- **Type:** **heuristic/rule-based**

### 3.4 Temporal Cleaning and Smoothing

- **Technique/Method:** confidence masking + gap interpolation + Savitzky-Golay filter
- **Evidence:** `SHOOTRZ/backend/mvp/core/signal_smoothing.py` → `SignalSmoother._interpolate_missing`, `SignalSmoother._apply_savgol`
- **Input:** raw keypoint table (`pose_keypoints.csv`)
- **Output:** smoothed coordinates (`*_smooth` columns) + interpolation flags
- **How it works:** low-confidence points marked missing; short consecutive gaps (`<= max_gap_frames`) linearly interpolated; each coordinate filtered by `savgol_filter`.
- **Why used here:** reduces pose jitter before derivative-dependent logic (angles, peaks).
- **Type:** **deterministic signal-processing**

### 3.5 Angle Computation

- **Technique/Method:** 3-point joint-angle vector math
- **Evidence:**  
	- `SHOOTRZ/backend/mvp/core/angle_computation.py` → `AngleComputer._compute_elbow_angle`, `_compute_knee_angle`, `_compute_wrist_angle`  
	- `SHOOTRZ/backend/metrics/biomechanics.py` → `joint_angle`
- **Input:** smoothed joint coordinates + confidences
- **Output:** per-frame `elbow_angle`, `knee_angle`, `wrist_angle`, confidence fields
- **How it works:** constructs vectors BA and BC around joint B, uses `arccos( dot(BA,BC)/(|BA||BC|) )`, converts to degrees.
- **Why used here:** core biomechanical features for shooting quality evaluation.
- **Type:** **rule-based geometry**

### 3.6 Shot Window Detection (MVP)

- **Technique/Method:** signal extrema + thresholds
- **Evidence:** `SHOOTRZ/backend/mvp/core/shot_detection.py` → `ShotDetector.detect_shot_window`
- **Input:** `angles_df`, `pose_keypoints_df`, shooting side
- **Output:** `start_frame`, `crouch_frame`, `release_frame`, `end_frame`, confidence
- **How it works:** crouch from knee-angle minima (`find_peaks` on inverted knee angle) with threshold checks; release from wrist vertical peak after crouch (`find_peaks` on inverted wrist Y).
- **Why used here:** extracts shot-relevant temporal window to evaluate form at key instants.
- **Type:** **heuristic/rule-based**

### 3.7 Metric Derivation + Scoring

- **Technique/Method:** threshold-range assessment + weighted continuous scoring
- **Evidence:** `SHOOTRZ/backend/mvp/core/metrics.py` → `derive_metrics`, `_assign_verdict`, `compute_overall_score`
- **Input:** angle time series + shot window
- **Output:** metric objects, verdicts, overall 0-100 score, textual feedback summary
- **How it works:** computes 3 metrics (elbow extension near release, knee bend at crouch, wrist follow-through delta); scores by optimal/good ranges and confidence penalties; weighted sum using config.
- **Why used here:** provides coach-readable assessment with deterministic logic.
- **Type:** **rule-based / heuristic scoring**

### 3.8 Motion-Based Phase Detector (overlay path)

- **Technique/Method:** finite-state style phase detection from fused kinematic signals
- **Evidence:**  
	- `SHOOTRZ/backend/inference/phase_detector.py` → `PhaseDetector.detect_phases`  
	- `SHOOTRZ/backend/inference/motion_analyzer.py` → `analyze_motion_patterns`
	- `SHOOTRZ/backend/routers/mvp.py` → `_process_video_job` constructs and calls `PhaseDetector(fps).detect_phases(...)`
- **Input:** reconstructed pose sequence (`landmarks`, `confidence`)
- **Output:** phase intervals (STANCE/CROUCH/RELEASE/LANDING), with `peak_frame` and confidence
- **How it works:** computes hip/wrist velocities, wrist acceleration, knee and arm angles; uses adaptive thresholds and multi-signal candidates (acceleration peaks, velocity zero-crossings, wrist extrema).
- **Why used here:** richer temporal semantics for annotated overlays and phase-level explanation.
- **Type:** **heuristic state-machine**

### 3.9 YOLO Ball Tracking

- **Technique/Method:** YOLOv8 detection + ByteTrack ID persistence
- **Evidence:** `SHOOTRZ/backend/inference/ball_tracker.py` → `detect_and_track_ball`
- **Input:** frame list
- **Output:** detections + selected primary trajectory
- **How it works:** `model.track(..., tracker='bytetrack.yaml', persist=True)`; filters sports-ball class; normalizes box centers.
- **Why used here:** intended for ball trajectory metrics (release/entry) and ball-conditioned analytics.
- **Type:** **pretrained/fine-tuned detection + tracking**
- **Status:** **PARTIALLY IMPLEMENTED** (not in default MVP pipeline execution chain)

### 3.10 YOLO Pose Alternative

- **Technique/Method:** YOLOv8-pose (COCO 17 keypoints)
- **Evidence:** `SHOOTRZ/backend/inference/yolo_pose_detector.py` → `YOLOv8PoseDetector.process_frame`
- **Input:** frame
- **Output:** normalized `[17,2]` keypoints + confidence
- **How it works:** runs ultralytics inference, selects first person, normalizes keypoints by image size.
- **Why used here:** alternative to MediaPipe, supports model fallback/fine-tune path.
- **Type:** **pretrained/fine-tuned model**
- **Status:** **PARTIALLY IMPLEMENTED**

### 3.11 3D Lifting

- **Technique/Method:** wrapper-based 2D→3D lifting with heuristic fallback
- **Evidence:** `SHOOTRZ/backend/inference/lift_3d.py` → `lift_3d_pose`; `posemagic_lifter.py`; `hybrik_lifter.py`
- **Input:** sequence of 2D landmarks
- **Output:** 3D keypoint sequences + confidence
- **How it works:** normalizes by pelvis/shoulder width, interpolates missing frames, dispatches to PoseMagic/HybrIK modules; currently falls back to geometric depth estimation in placeholder methods.
- **Why used here:** designed path for richer biomechanics beyond 2D.
- **Type:** **hybrid planned learned+heuristic**
- **Status:** **PARTIALLY IMPLEMENTED**

### 3.12 Hand/Grip Module

- **Technique/Method:** MediaPipe Hands + geometric grip heuristics
- **Evidence:** `SHOOTRZ/backend/inference/hands_2d.py` and `SHOOTRZ/backend/metrics/grip.py`
- **Input:** hand landmarks, optional ball center
- **Output:** grip quality score + thumb-index distance + palm-contact estimate
- **How it works:** computes Euclidean finger distances and simple threshold scoring; palm contact estimated from ball distance or spread fallback.
- **Why used here:** intended to assess shooting-hand release quality.
- **Type:** **pretrained landmarks + rule-based postprocessing**
- **Status:** **PARTIALLY IMPLEMENTED / not central in MVP route**

---

## 4. Model-Specific Analysis

### 4.1 YOLO (if used)

**Confirmed repository usage points:**

- `SHOOTRZ/backend/inference/ball_tracker.py` (`detect_and_track_ball`)
- `SHOOTRZ/backend/inference/yolo_pose_detector.py` (`YOLOv8PoseDetector`)
- `SHOOTRZ/backend/inference/model_loader.py` (`ModelLoader.load_yolov8_ball`, `load_yolov8_pose`)
- `SHOOTRZ/backend/config/models.yaml` (`models.yolov8_ball`, `models.yolov8_pose`)

**Version evidence (what can be confirmed):**

- The code targets **Ultralytics YOLOv8 family naming** (`'yolov8n.pt'`, `'yolov8n-pose.pt'`) via model loader and detector code.  
- Requirement pin is package-level: `ultralytics>=8.0.0` in `SHOOTRZ/backend/requirements.txt`.  
- Exact sub-version is **not fixed** in code.

**Architecture (Backbone/Neck/Head):**

- **INFERRED:** standard YOLOv8 detection/pose architecture from Ultralytics runtime.
- In this repo, architecture internals are not custom-defined in backend runtime files; backend treats YOLO as a black-box inference module.

**Role in this project:**

- Ball detection/tracking for trajectory and shot-event support (module ready)
- Alternative pose detector path using COCO 17 keypoints

### 4.2 Pose Estimation

**Primary model/framework (CONFIRMED):**

- MediaPipe Pose in `SHOOTRZ/backend/inference/pose_2d.py`, class `MediaPipePoseDetector`

**Keypoint count/output format (CONFIRMED):**

- 33 landmarks/frame from MediaPipe; each landmark `[x,y,z]` normalized
- Confidence from landmark visibility
- Exported formats:
	- CSV rows per joint/frame in `MVPPoseEstimator.export_pose_keypoints_csv`
	- structured JSON in `MVPPoseEstimator.export_pose_keypoints_json`

**Confidence usage (CONFIRMED):**

- Missingness threshold in `SignalSmoother` (`confidence < confidence_threshold`)
- Side detection and angle validity checks in `MVPPoseEstimator` and `AngleComputer`

**Frame processing pipeline (CONFIRMED):**

- `VideoLoader.load_frames` → `MVPPoseEstimator.process_frames` → persistence and confidence summary

### 4.3 Segmentation

- No backend segmentation pipeline was found in active SHOOTRZ backend code paths.
- Any segmentation references under `SHOOTRZ/models/yolov8/...` are upstream library content and not evidenced as active SHOOTRZ runtime calls.

---

## 5. Mathematical & Logic Components

### 5.1 Angle Calculation

- **Formula (CONFIRMED):** in `SHOOTRZ/backend/metrics/biomechanics.py`, `joint_angle`
	- `BA = A - B`, `BC = C - B`
	- `theta = arccos( dot(BA,BC) / (||BA||*||BC||) )`
	- returns degrees
- **Where applied:**
	- Elbow: `AngleComputer._compute_elbow_angle`
	- Knee: `AngleComputer._compute_knee_angle`
	- Wrist proxy: `AngleComputer._compute_wrist_angle` (vertical reference point above elbow)

### 5.2 Smoothing / Filtering

- **Savitzky-Golay filtering (CONFIRMED):**
	- `SHOOTRZ/backend/mvp/core/signal_smoothing.py` (`_apply_savgol`)
	- optional in motion analyzer for acceleration smoothing (`_savgol_smooth`)
- **Moving average (CONFIRMED):**
	- `SHOOTRZ/backend/inference/motion_analyzer.py`, `moving_average`
- **Gap interpolation (CONFIRMED):**
	- Linear interpolation over short confidence-drop gaps in `SignalSmoother._interpolate_missing`
- **Why needed:** stabilize noisy per-frame landmarks to avoid false extrema and unstable angle derivatives.

### 5.3 Shot Detection

- **MVP logic (CONFIRMED):**
	- Crouch = minimum knee angle using `find_peaks` on inverted knee signal (`ShotDetector._detect_crouch`)
	- Release = wrist height peak after crouch from inverted wrist-Y (`ShotDetector._detect_release`)
	- Window = `pre_frames` before crouch and `post_frames` after release
- **Release confidence:** based on keypoint confidence and fallback penalties.

### 5.4 Scoring System

- **Rule-based (CONFIRMED):**
	- ranges and weights in `SHOOTRZ/backend/config/mvp_config.yaml`
	- `MetricsDerivation.compute_overall_score` converts metric values to continuous scores and applies confidence scaling.
- **No supervised score regressor in MVP path (CONFIRMED).**

---

## 6. Full Technical Pipeline

Video Input -> Frame Processing -> Keypoints -> Angles -> Shot Detection -> Scoring -> Output

1. **Video Input / Metadata**
	- File/Function: `SHOOTRZ/backend/mvp/core/video_loader.py`, `VideoLoader.load_metadata`
	- Reads FPS, frame count, resolution, duration; adds quality warnings.

2. **Frame Processing**
	- File/Function: `SHOOTRZ/backend/mvp/core/video_loader.py`, `VideoLoader.load_frames`, `create_frame_mapping`
	- Loads RGB frames with configurable `frame_skip`; creates processed↔original frame timestamp mapping.

3. **Pose Keypoint Extraction**
	- File/Function: `SHOOTRZ/backend/mvp/core/pose_estimation.py`, `MVPPoseEstimator.process_frames`
	- Calls `MediaPipePoseDetector.process_frame` from `SHOOTRZ/backend/inference/pose_2d.py`.
	- Exports CSV/JSON and confidence summary.

4. **Temporal Cleaning / Smoothing**
	- File/Function: `SHOOTRZ/backend/mvp/core/signal_smoothing.py`, `SignalSmoother.smooth_keypoints`
	- Marks low-confidence points, interpolates gaps, applies Savitzky-Golay smoothing.

5. **Angle Computation**
	- File/Function: `SHOOTRZ/backend/mvp/core/angle_computation.py`, `AngleComputer.compute_angles_per_frame`
	- Uses `joint_angle` from `SHOOTRZ/backend/metrics/biomechanics.py`.

6. **Shot Detection**
	- File/Function: `SHOOTRZ/backend/mvp/core/shot_detection.py`, `ShotDetector.detect_shot_window`
	- Determines crouch/release and shot window boundaries.

7. **Metric Derivation & Score**
	- File/Function: `SHOOTRZ/backend/mvp/core/metrics.py`, `MetricsDerivation.derive_metrics`, `compute_overall_score`
	- Produces three metric evaluations + weighted overall score + feedback summary.

8. **Result Packaging / API**
	- File/Function: `SHOOTRZ/backend/routers/mvp.py`, `_process_video_job`, `/mvp/result/{job_id}`
	- Loads artifacts and serves structured output for mobile app.

9. **Overlay (phase annotation)**
	- File/Function: `SHOOTRZ/backend/routers/mvp.py` + `SHOOTRZ/backend/utils/video_annotator.py`
	- Uses `PhaseDetector.detect_phases` for phase labels in overlay video.

---

## 7. Technical Components Table

| Technical Component | Technique Used | File Path | Input | Output | Why Used |
|---|---|---|---|---|---|
| MVP orchestrator | Deterministic staged pipeline | `SHOOTRZ/backend/mvp/core/pipeline.py` (`MVPPipeline.process_video`) | video path, side | full analysis dict + artifacts | reproducible end-to-end analysis |
| Pose estimation | MediaPipe Pose (33 landmarks) | `SHOOTRZ/backend/inference/pose_2d.py` (`MediaPipePoseDetector`) | frames | landmarks + visibility | body-joint extraction for biomechanics |
| Keypoint mapping/export | joint subset mapping + CSV/JSON export | `SHOOTRZ/backend/mvp/core/pose_estimation.py` (`MVPPoseEstimator`) | pose results | structured keypoint datasets | auditable downstream processing |
| Side detection | wrist-height comparison heuristic | `SHOOTRZ/backend/mvp/core/pose_estimation.py` (`determine_shooting_side`) | left/right wrist trajectories | shooting side | side-specific angle formulas |
| Missing-data handling | confidence threshold + linear interpolation | `SHOOTRZ/backend/mvp/core/signal_smoothing.py` (`_interpolate_missing`) | raw keypoints | filled gaps | robust trajectories under occlusion |
| Trajectory smoothing | Savitzky-Golay filter | `SHOOTRZ/backend/mvp/core/signal_smoothing.py` (`_apply_savgol`) | per-joint coordinates | smoothed coordinates | reduce jitter/noise |
| Angle engine | vector-angle geometry (`arccos`) | `SHOOTRZ/backend/metrics/biomechanics.py` (`joint_angle`) + `angle_computation.py` | joint triplets | elbow/knee/wrist angles | biomechanical metrics |
| Shot window detector | extrema + threshold heuristics | `SHOOTRZ/backend/mvp/core/shot_detection.py` (`ShotDetector`) | angles + wrist trajectory | crouch/release/start/end frames | isolate shot event timing |
| Metric derivation | release/crouch anchored feature extraction | `SHOOTRZ/backend/mvp/core/metrics.py` (`derive_metrics`) | angles + shot window | 3 metric dicts | form-quality assessment |
| Overall score | weighted continuous scoring + confidence penalty | `SHOOTRZ/backend/mvp/core/metrics.py` (`compute_overall_score`) | metric values/confidence | 0-100 score + summary | single interpretable performance value |
| Motion phase detector | multi-signal heuristic state machine | `SHOOTRZ/backend/inference/phase_detector.py` (`PhaseDetector`) | pose sequence | STANCE/CROUCH/RELEASE/LANDING intervals | phase labeling and explainability overlays |
| Motion signal extraction | velocities, acceleration, extrema | `SHOOTRZ/backend/inference/motion_analyzer.py` | pose sequence | `MotionSignals` | robust phase-event candidates |
| Video overlay annotation | keypoint draw + phase label rendering | `SHOOTRZ/backend/utils/video_annotator.py` (`annotate_video`) | video + pose + phases | overlay mp4 | visual debugging and presentation |
| YOLO ball tracking | YOLOv8 + ByteTrack | `SHOOTRZ/backend/inference/ball_tracker.py` (`detect_and_track_ball`) | frames | ball detections/trajectory | planned trajectory-based metrics |
| YOLO pose alternative | YOLOv8-pose (17 keypoints) | `SHOOTRZ/backend/inference/yolo_pose_detector.py` | frames | COCO keypoints | alternate detector/fallback path |
| 3D lifting wrapper | PoseMagic/HybrIK dispatch + fallback | `SHOOTRZ/backend/inference/lift_3d.py` | 2D keypoint sequence | 3D sequence | planned richer biomechanics |
| Hand/grip analysis | MediaPipe Hands + geometric scoring | `SHOOTRZ/backend/inference/hands_2d.py`, `SHOOTRZ/backend/metrics/grip.py` | hand landmarks (+optional ball center) | grip score metrics | planned release quality refinement |

---

## 8. Confirmed vs Inferred

### CONFIRMED

- Active MVP route calls `MVPPipeline.process_video` (`SHOOTRZ/backend/routers/mvp.py`)
- MVP uses MediaPipe Pose path (`MVPPoseEstimator` -> `MediaPipePoseDetector`)
- Smoothing uses Savitzky-Golay and interpolation (`SignalSmoother`)
- Angles use explicit vector math (`joint_angle`)
- Shot detection uses knee minimum + wrist peak logic (`ShotDetector`)
- Scoring is weighted rule-based from configurable ranges (`MetricsDerivation` + `mvp_config.yaml`)
- Motion-based `PhaseDetector` is used for overlay labeling in router flow.

### INFERRED

- `SHOOTRZ/models/yolov8` appears largely vendored/upstream library content, not the direct active runtime of MVP endpoint.
- Broader feedback rule system in `SHOOTRZ/backend/feedback/rules.py` is present; its centrality to MVP endpoint output is not explicit in `MVPPipeline` path.
- Frontend `MediaPipeService` (`SHOOTRZ/src/services/mediapipe.service.ts`) appears as a mock/POC and likely non-production for backend analytics.

### PARTIALLY IMPLEMENTED

- YOLO pose/ball modules are implemented but not wired into default MVP pipeline.
- 3D lifting modules (`PoseMagicLifter`, `HybrIKLifter`) contain placeholder model-loading comments and heuristic fallback logic.
- Hand/grip pathway exists but not evidenced in default MVP endpoint execution.

---

## 9. Limitations / Simplifications

1. **2D-first biomechanics approximation (CONFIRMED):** core MVP metrics are derived from 2D pose projections; depth effects are not fully resolved.
2. **Heuristic shot detection (CONFIRMED):** release/crouch use thresholds and extrema, which can be sensitive to camera angle and occlusion.
3. **Wrist metric proxy (CONFIRMED):** wrist follow-through in MVP is a proxy angle, not full hand-joint articulation.
4. **No integrated learned scoring model in MVP path (CONFIRMED):** score is deterministic rules + weighting, not trained end-to-end regression/classification.
5. **3D model path incomplete (PARTIALLY IMPLEMENTED):** PoseMagic/HybrIK inference uses placeholders/fallback heuristics when models unavailable.
6. **Ball trajectory not mandatory in MVP scoring (CONFIRMED):** default MVP metrics can run without active ball tracking.

---

## 10. Open Questions / Uncertain Areas

1. Are fine-tuned model files (`yolov8n_basketball_deepsport.pt`, `yolov8n_pose_basketball.pt`, `posemagic_basketball.pth`, `hybrik_basketball.pth`) present in deployment environments at runtime? (`SHOOTRZ/backend/inference/model_loader.py`, `SHOOTRZ/backend/config/models.yaml`)
2. Is motion-based `PhaseDetector` intended to replace `ShotDetector` for core metric extraction, or remain overlay-only?
3. Should hand/grip metrics be included in production scoring outputs, and if yes, where in MVP pipeline should they be integrated?
4. Are old backend docs (`SHOOTRZ/backend/README.md`) fully synchronized with current FastAPI + MVP implementation?
5. Is YOLO strategy switching (mediapipe/yolo/ensemble in `models.yaml`) wired to runtime endpoint selection, or currently configuration-only?

---

## 11. Presentation-Relevant Insights

- SHOOTRZ’s strongest technical justification is **engineering reliability and explainability**: every stage outputs intermediate artifacts (`pose_keypoints.csv`, `pose_keypoints_smoothed.csv`, `angles.csv`, `shot_window.json`, `report.json`) for traceability.
- The system uses a **hybrid AI + deterministic biomechanics design**:
	- AI model for perception (MediaPipe Pose, optional YOLO)
	- deterministic logic for temporal events, metrics, and scoring
- This design is appropriate for graduation-project defense because it enables:
	- reproducibility from fixed config (`SHOOTRZ/backend/config/mvp_config.yaml`)
	- explicit mathematical interpretability (`joint_angle`, threshold ranges, weighted score)
	- modular future upgrades (YOLO integration, 3D lifting, hand/grip integration) without replacing the full pipeline.
- The repository clearly separates:
	- **currently production-ready MVP path** (2D pose + deterministic scoring)
	- **expansion paths** (YOLO, 3D lifting, advanced phase logic), some still partial.