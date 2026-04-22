# SHOOTRZ Model Audit

Evidence gathered by static inspection of the repository (Python imports, call chains, dependency lists, and file presence). Items marked **confirmed** have direct code paths from the FastAPI app or MVP pipeline unless noted otherwise.

## 1. Executive Summary

The **production video analysis path** (`MVPPipeline` → `MVPJobService`) relies on **one on-device computer-vision model family**: **Google MediaPipe Pose** (2D body landmarks), exposed through `mediapipe` in `backend/inference/pose_2d.py`. **Shot timing, metrics, and scoring** are **rule-based and signal-processing** (SciPy, pandas, geometry), not separate learned models.

**Google Gemini** (default **`gemini-2.5-flash`** via `google-genai`) is used for **natural-language** coaching content (chat, feedback enrichment, drill explanations, summaries) when `GEMINI_API_KEY` is configured; otherwise deterministic fallbacks run.

The **drill recommender** uses **FAISS** (vector similarity search on precomputed embeddings) and **Mabwiser** (LinUCB contextual bandit). This is **not** a neural network training stack in-repo; embeddings are loaded from static files.

Several **dependencies listed in `backend/requirements.txt`** (Ultralytics/YOLOv8, LightGBM, scikit-learn, PyTorch, ONNX Runtime, joblib, filterpy) show **no `import` usage anywhere under `backend/`** in the current tree and are **not confirmed as active** in the backend. **Vendored** `models/yolov8/` and `models/hrnet/` trees exist as upstream projects; **no backend code imports them**. **Scripts** reference **removed or missing modules** (`backend/inference/model_loader`, `ball_tracker`, `yolo_pose_detector`, etc.), so those script paths are **not runnable as-is** without restoration.

---

## 2. Confirmed Models in Active Use

### 2.1 MediaPipe Pose (Google)

| Field | Detail |
|--------|--------|
| **Model name** | MediaPipe Pose (BlazePose-class full-body model bundled with MediaPipe; complexity selectable 0/1/2) |
| **Model type** | 2D (and weak 3D z) body pose estimation |
| **Framework/library** | `mediapipe` Python package; uses MediaPipe’s bundled TFLite inference internally |
| **Where found** | `backend/inference/pose_2d.py` (`MediaPipePoseDetector`), `backend/mvp/core/pose_estimation.py` (`MVPPoseEstimator`) |
| **Evidence summary** | `mp.solutions.pose.Pose(...)` and `self.pose.process(frame_rgb)` populate 33 landmarks per frame. |
| **Pipeline role** | Primary **pose keypoint extraction** for the MVP pipeline. |
| **Input** | RGB `numpy` frames `[H,W,3]` (from `mvp/core/video_loader.py`). |
| **Output** | Per frame: 33×3 normalized landmarks + per-joint visibility in `pose_keypoints.csv` / `pose_keypoints.json`. |
| **Pretrained / trained** | **Pretrained** weights shipped inside MediaPipe; **not** trained by SHOOTRZ. |
| **Training in repo** | **No** MediaPipe training code. |
| **Confidence** | **High** |

### 2.2 Google Gemini (default: gemini-2.5-flash)

| Field | Detail |
|--------|--------|
| **Model name** | Configurable via `GEMINI_MODEL`; default `gemini-2.5-flash` (`backend/utils/config.py`, `backend/services/llm/gemini_client.py`) |
| **Model type** | Large language model (multimodal-capable SDK; SHOOTRZ uses text/JSON generation) |
| **Framework/library** | `google-genai` (`genai.Client`) |
| **Where found** | `backend/services/llm/gemini_client.py`, `backend/services/llm/llm_router.py`, call sites: `backend/services/mvp_job_service.py` (`_enrich_with_gemini`), `backend/routers/chat.py`, `backend/recommender/recommend_service.py`, `backend/routers/user.py`, optional enrichment in `backend/feedback/rules.py` |
| **Evidence summary** | `GeminiService.generate`, `generate_structured`, streaming; HTTP 503 when API key missing. |
| **Pipeline role** | **NLP layer**: rephrase/enrich feedback, chat coach, drill explanation, session summary, progress insight—not geometric inference. |
| **Input** | Prompts built from metrics/context (`prompt_builders.py`, `chat/context_builder.py`). |
| **Output** | Text or JSON validated against Pydantic schemas in `output_schemas.py`. |
| **Pretrained / trained** | **Pretrained** Google foundation model accessed by API; **not** fine-tuned in-repo. |
| **Training in repo** | **No**. |
| **Confidence** | **High** (when API key present; otherwise fallbacks in `fallbacks.py`) |

### 2.3 FAISS index (approximate nearest neighbor retrieval)

| Field | Detail |
|--------|--------|
| **Model name** | FAISS index file (`faiss_index.bin`) |
| **Model type** | Vector index / retrieval (not a learned neural net in this repo) |
| **Framework/library** | `faiss-cpu` |
| **Where found** | `backend/recommender/faiss_index.py`, `backend/recommender/recommend_service.py` (`faiss_index.search`) |
| **Evidence summary** | `faiss.read_index` loads binary index; `search` returns neighbor drill IDs. |
| **Pipeline role** | **Nearest-drill retrieval** given normalized `user_vec`. |
| **Input** | Normalized user embedding vector (from API payload). |
| **Output** | Neighbor indices for drill selection pool. |
| **Pretrained / trained** | **Index is pre-built offline**; no builder script found under `backend/`. Vectors loaded from `drill_embeddings.npy`. |
| **Training in repo** | **No** index-building code in backend. |
| **Confidence** | **High** for *code intent*; **note**: `backend/storage/drill_embeddings.npy`, `faiss_index.bin`, and `drills_metadata.csv` were **not present** in this workspace snapshot—endpoint would raise `FileNotFoundError` until artifacts exist. |

### 2.4 Mabwiser LinUCB (contextual bandit)

| Field | Detail |
|--------|--------|
| **Model name** | MAB with `LearningPolicy.LinUCB` |
| **Model type** | Contextual bandit (linear UCB)—**classical ML**, not deep learning |
| **Framework/library** | `mabwiser` |
| **Where found** | `backend/recommender/bandit_model.py`, `recommend_service.py` (`bandit.predict_expectations`) |
| **Evidence summary** | `initialize_bandit` fits a **single dummy** context/reward pair then serves predictions. |
| **Pipeline role** | Chooses **cluster/tier arm** to pick among FAISS neighbors. |
| **Input** | `user_context` vector from API payload. |
| **Output** | Expected reward per arm; best arm selects `(cluster, tier)`. |
| **Pretrained / trained** | **Not meaningfully trained** on real SHOOTRZ data in code—only dummy initialization. |
| **Training in repo** | **Minimal placeholder** fit; no dataset-driven training loop. |
| **Confidence** | **High** |

---

## 3. Referenced or Planned Models

### 3.1 Ultralytics YOLOv8 (ball / pose)

| Field | Detail |
|--------|--------|
| **Evidence** | `backend/requirements.txt` lists `ultralytics>=8.0.0`; `scripts/finetune_yolo_ball.py`, `scripts/download_from_colab.py`, `scripts/create_pose_dataset.py` reference YOLO training or weights; vendored `models/yolov8/` is full upstream Ultralytics. |
| **Why not confirmed in production** | **No** `import ultralytics` or `YOLO` under `backend/` in the current tree. MVP pipeline uses **MediaPipe only** for pose. |
| **Confidence** | **Medium** (dependency + scripts indicate intent; not wired to live API). |

### 3.2 PyTorch / HRNet

| Field | Detail |
|--------|--------|
| **Evidence** | `torch` in `requirements.txt`; `models/hrnet/` contains `lib/models/pose_hrnet.py`, `tools/train.py`. |
| **Why not confirmed** | **No** backend import path from `backend/` into `models/hrnet`. |
| **Confidence** | **Low–Medium** (vendored research code; unused by app). |

### 3.3 LightGBM / scikit-learn / ONNX Runtime / joblib / filterpy

| Field | Detail |
|--------|--------|
| **Evidence** | All appear in `backend/requirements.txt` with comments implying shot prediction, validation, Kalman smoothing. |
| **Why not confirmed** | **Grep over `backend/**/*.py` found zero imports** of `lightgbm`, `sklearn`, `onnxruntime`, `joblib`, or `filterpy`. Smoothing uses **`scipy.signal.savgol_filter`** (`signal_smoothing.py`), not Kalman in code. |
| **Confidence** | **High** that they are **unused** in current backend code (possibly stale requirements). |

### 3.4 Legacy script modules (`ball_tracker`, `yolo_pose_detector`, `model_loader`, `lift_3d`, `hands_2d`, `MetricsCalculator`)

| Field | Detail |
|--------|--------|
| **Evidence** | `scripts/comprehensive_evaluation.py`, `scripts/evaluate_metrics.py` import `backend.inference.model_loader`, `ball_tracker`, etc. |
| **Why not confirmed** | Those modules **do not exist** under `backend/inference/` (only `pose_2d`, `phase_detector`, `motion_analyzer`). Scripts are **broken references** relative to current tree. |
| **Confidence** | **High** (stale or removed code). |

### 3.5 “PoseMagic” / “Hybrik” 3D lifting (script-only)

| Field | Detail |
|--------|--------|
| **Evidence** | `scripts/comprehensive_evaluation.py` calls `lift_3d_pose(..., method="posemagic"|"hybrik")`. |
| **Why not confirmed** | Implementation file **not present**; not used by FastAPI. |
| **Confidence** | **Low** (aspirational / removed). |

---

## 4. Non-Model Logic Mistaken for AI

| Component | Location | Nature |
|-----------|----------|--------|
| **Shot window / release detection** | `backend/mvp/core/shot_detection.py` | Heuristics + **`scipy.signal.find_peaks`**, thresholds, fused wrist/hip/knee signals—not a learned detector. |
| **Phase detection (overlay)** | `backend/inference/phase_detector.py`, `motion_analyzer.py` | **Rule-based state machine** + peak/zero-crossing logic + adaptive thresholds; uses **`scipy.signal.find_peaks`**. Runs in `mvp_job_service._build_overlay_artifact` for visualization; primary shot metrics still come from `shot_window` JSON from `ShotDetector`. |
| **Angle metrics** | `backend/mvp/core/angle_computation.py`, `backend/metrics/biomechanics.py` | **Geometry** (`joint_angle`, vector math). |
| **Smoothing** | `backend/mvp/core/signal_smoothing.py` | Interpolation + **Savitzky–Golay** (`scipy.signal.savgol_filter`). |
| **Scoring & feedback (core)** | `backend/mvp/core/metrics.py`, `backend/feedback/rules.py` | **Handcrafted scoring** from ranges/weights in config; LLM only **optional enrichment**. |
| **Pydantic “models”** | `backend/services/llm/output_schemas.py` | **Data validation models**, not ML. |
| **Video I/O & drawing** | `mvp/core/video_loader.py`, `utils/video_annotator.py` | OpenCV **only**; optional ball trajectory drawing if passed—**MVP job does not pass ball trajectory** (no ball CV in production path). |

---

## 5. End-to-End AI Pipeline Mapping

Supported **only** by code that exists and is called today:

1. **Mobile app** uploads video to **`POST /mvp/analyze`** (`backend/routers/mvp.py` → `MVPJobService.queue_job`).
2. **Temporary file** → **`MVPPipeline.process_video`** (`backend/mvp/core/pipeline.py`).
3. **VideoLoader** decodes frames (`opencv-python`).
4. **MVPPoseEstimator** → **MediaPipe Pose** → per-frame landmarks (`pose_keypoints.csv/json`).
5. **SignalSmoother** → Savitzky–Golay smoothing (`pose_keypoints_smoothed.csv`).
6. **AngleComputer** → kinematic angles (`angles.csv`).
7. **ShotDetector** → heuristic shot window + diagnostics (`shot_window.json`, `event_*.json`).
8. **MetricsDerivation** → rule-based metrics + weighted score (`report.json`).
9. **MVPJobService** → optional **Gemini** enrichment of feedback text; **PhaseDetector** on saved pose JSON for overlay phases; **OpenCV** writes **`overlay.mp4`**.
10. **Separate**: **`POST /api/recommend`** → FAISS + LinUCB + optional Gemini drill text (requires static storage files).

**Not present in this chain**: YOLO ball detection, YOLO pose, 3D lifting, LightGBM shot classifier, ONNX models.

---

## 6. Training Status Audit

| Item | Inference-only | Trainable in-repo | Training scripts | Notes |
|------|----------------|-------------------|------------------|-------|
| MediaPipe Pose | Yes | No | No | Uses bundled weights |
| Gemini | Yes (API) | No | No | Remote model |
| FAISS drill index | Retrieval only | N/A | **No builder in backend** | Vectors supplied offline |
| LinUCB bandit | Yes | Could be, but **not done** | No real data fit | Dummy fit only |
| YOLOv8 (scripts/vendor) | Would be if used | Yes (Ultralytics) | `scripts/finetune_yolo_ball.py`, vendor `ultralytics` | **Not connected to backend** |
| HRNet (vendor) | Would be if used | Yes | `models/hrnet/tools/train.py` | **Unused by app** |
| Stale requirements (LGBM, sklearn, torch in app) | — | — | — | **No training pipeline wired** |

---

## 7. Dataset Requirements If We Want Training

*(No web search; inferred from task types and repo scripts only.)*

| Intent | Task type | Data needed | Labels | Notes |
|--------|-----------|-------------|--------|-------|
| **MediaPipe (keep as-is)** | Pose inference | None for deployment | N/A | Already general-purpose; basketball-specific accuracy is a **product** issue, not a training issue in-repo. |
| **YOLOv8 ball / player** | Object detection | Video frames + bounding boxes | Class id, bbox | `finetune_yolo_ball.py` mentions DeepSport-style splits (`train/images`, etc.). Public sports detection datasets may help; **in-game basketball** often needs **custom** labels. |
| **YOLOv8-pose (script `create_pose_dataset.py`)** | Pose estimation | Images | COCO-format keypoints | Script uses **MediaPipe pseudo-labels** to generate training labels—implies **domain adaptation**, not ground-truth accuracy without human QA. |
| **HRNet (vendor)** | 2D human pose | COCO/MPII-style pipelines | Keypoint heatmaps | Standard pose datasets; **basketball-specific** fine-tuning would need **custom** labeled frames. |
| **Gemini / LLM** | Text generation | Optional fine-tuning not in scope of repo | N/A for current integration | Production uses **prompting** only; improvement is via **prompt/data** engineering on **language** side, not CV labels. |
| **Shot / phase classifiers (if added)** | Temporal classification / segmentation | Time-series of angles & keypoints | Phase boundaries, release frame | Would need **per-frame or event labels** on basketball video (custom labeling). |
| **LightGBM shot quality (if revived)** | Regression / ranking | Feature table rows + outcomes | Continuous score or success label | Would need **labeled shots** (make/miss or form grades)—**custom** data. |
| **FAISS / recommender** | Embedding quality | Drill metadata + user-drill interaction | Implicit feedback (completion, ratings) | To learn **user_vec** and refresh embeddings, need **interaction logs** and possibly **content embeddings** from an encoder (not implemented here). |

---

## 8. Key Files Reviewed

| File / area | Contribution to audit |
|-------------|-------------------------|
| `backend/requirements.txt` | Declared deps vs actual usage mismatch for several ML packages. |
| `backend/mvp/core/pipeline.py` | Authoritative MVP stage order; confirms MediaPipe → smooth → angles → shot → metrics. |
| `backend/inference/pose_2d.py` | MediaPipe Pose instantiation and outputs. |
| `backend/mvp/core/pose_estimation.py`, `shot_detection.py`, `signal_smoothing.py`, `metrics.py` | Pose wrapper; heuristics; Savitzky–Golay; rule scoring. |
| `backend/inference/phase_detector.py`, `motion_analyzer.py` | Non-NN phase logic for overlays. |
| `backend/services/mvp_job_service.py` | Job orchestration, Gemini enrichment, PhaseDetector + `annotate_video`. |
| `backend/services/llm/*.py` | Gemini client, router, prompts, schemas, fallbacks. |
| `backend/recommender/*.py` | FAISS + Mabwiser integration. |
| `backend/main.py` | Router registration; health exposes Gemini config. |
| `package.json` | Frontend: no ML libs; API client only. |
| `scripts/finetune_yolo_ball.py`, `create_pose_dataset.py`, `comprehensive_evaluation.py` | Shows experimental/stale YOLO and evaluation intent; several imports missing. |
| `models/yolov8/`, `models/hrnet/` | Vendored third-party code; not imported by backend. |

---

## 9. Final Answer for ChatGPT Handoff

**Confirmed models in SHOOTRZ today**

- **MediaPipe Pose**: 2D body keypoints for the full analysis pipeline; **pretrained**, **inference-only**, local.
- **Google Gemini (`gemini-2.5-flash` default)**: LLM for coach chat, feedback wording, drill explanations, summaries; **remote API**, **inference-only**; optional if key missing.
- **FAISS + precomputed `drill_embeddings.npy`**: nearest-neighbor drill retrieval; **not neural training** in-repo; needs offline-built index/vectors.
- **Mabwiser LinUCB**: bandit for cluster/tier choice; **hardly trained** (dummy fit).

**Likely / planned / stale (not driving the live MVP pipeline)**

- **YOLOv8** (ball / pose): scripts + vendored Ultralytics; **not imported** by backend MVP.
- **HRNet / PyTorch pose**: vendored; **unused** by app.
- **LightGBM, sklearn, ONNX, joblib, filterpy** in requirements: **no backend imports found**—treat as **stale or future** unless restored.
- **3D lifting / ball tracking modules** referenced by old scripts: **files missing**—not active.

**What needs datasets if you train**

- **YOLO detection / pose**: labeled basketball images/video (bboxes and/or keypoints); scripts point to YOLO-format datasets; pseudo-label path exists via MediaPipe.
- **Custom shooting quality / phases**: time-aligned labels (release, crouch, make/miss, coach scores) on video—**custom basketball data** is likely essential.
- **Recommender**: user-drill interaction history to train meaningful **user embeddings** and refresh **FAISS**; not present as a pipeline today.
- **Gemini**: no training in-repo; improvement is **prompting and optional Google-side fine-tuning**, not SHOOTRZ CV data.

---

*End of report.*
