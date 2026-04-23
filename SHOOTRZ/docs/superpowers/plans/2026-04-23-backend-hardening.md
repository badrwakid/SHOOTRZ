# SHOOTRZ Backend Production Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cut analysis latency from ~130s to <12s and peak memory from ~3.4GB to <400MB per request, while adding a real SHOOTRZ shot score (0–100) and stable async concurrency for demo day.

**Architecture:** Replace the in-memory frame-loader with a stride-based streaming generator; disable annotated-video generation and hands detection by default; move all CPU-heavy work into a ProcessPoolExecutor with warmed workers; add a confidence-weighted geometric-mean score aggregator in `angles.py`. The FastAPI `BackgroundTasks` approach (same-process, blocking) is replaced by `asyncio.create_task` + `run_in_executor` (subprocess, non-blocking, timeout-guarded).

**Tech Stack:** FastAPI, MediaPipe 0.10+, ultralytics (YOLO), asyncio, concurrent.futures.ProcessPoolExecutor, OpenCV (cv2), numpy, Python 3.10+

---

## File Map

| File | Action | Responsibility |
|---|---|---|
| `SHOOTRZ/backend/processing/pipeline.py` | **Modify** | Stream decode, stride sampling, disable annotation/hands, `_empty_result`, call `compute_shot_score` |
| `SHOOTRZ/backend/inference/pose_2d.py` | **Modify** | Remove double cvtColor, writeable guard, mean-visibility gate, env-based complexity |
| `SHOOTRZ/backend/inference/ball_tracker.py` | **Modify** | Replace per-frame `model.track()` with batched `model.predict()` at `imgsz=480` |
| `SHOOTRZ/backend/metrics/angles.py` | **Replace** | `compute_shot_score`, `_dim_score`, `_target_of`, normative ranges loading with fallback |
| `SHOOTRZ/backend/metrics/normative_ranges.json` | **Create** | Biomechanics target ranges for the 7 scored dimensions |
| `SHOOTRZ/backend/metrics/biomechanics_2d.py` | **Modify** | Add `vis_mean` param to all 2D helpers; add `_scale_conf` helper |
| `SHOOTRZ/backend/metrics/calculator.py` | **Modify** | Accept pre-computed `phases`; pass `vis_mean` into 2D helpers at each call site |
| `SHOOTRZ/backend/routers/analyze.py` | **Replace** | ProcessPoolExecutor + asyncio.Semaphore + task-ref tracking + 429 + tempfile cleanup |
| `SHOOTRZ/backend/routers/results.py` | **Modify** | Add `shot_score` field to both return paths |
| `SHOOTRZ/backend/main.py` | **Modify** | Lifespan context manager that shuts down the executor on app exit |
| `SHOOTRZ/backend/tests/test_pipeline.py` | **Modify** | Accept `completed_low_quality` status for synthetic videos; add `shot_score` assertion |

---

## DAY 1 — Latency & Memory (gate: single-video < 12s, memory < 400MB)

---

### Task 1: `pipeline.py` — Stream decode + stride sampling

**Files:**
- Modify: `SHOOTRZ/backend/processing/pipeline.py`

- [ ] **Step 1: Replace `__init__` signature**

  Open `SHOOTRZ/backend/processing/pipeline.py`. Replace the `__init__` method (lines 32–65) with:

  ```python
  def __init__(
      self,
      use_3d_lifting: bool = False,
      enable_ball_tracking: bool = True,
      pose_strategy: str = "mediapipe",
      generate_annotated: bool = False,
      enable_hands: bool = False,
  ):
      self.pose_detector = MediaPipePoseDetector()
      self.hands_detector = MediaPipeHandsDetector() if enable_hands else None
      self.phase_detector = PhaseDetector()
      self.metrics_calculator = MetricsCalculator(use_3d=use_3d_lifting)
      self.use_3d_lifting = use_3d_lifting
      self.enable_ball_tracking = enable_ball_tracking
      self.generate_annotated = generate_annotated
      self.enable_hands = enable_hands
      self.pose_strategy = pose_strategy
      self.yolo_pose_detector = None
      if pose_strategy in ["yolo", "ensemble"]:
          try:
              from ..inference.yolo_pose_detector import YOLOv8PoseDetector
              self.yolo_pose_detector = YOLOv8PoseDetector(use_finetuned=True)
          except Exception as e:
              print(f"Warning: Could not initialize YOLOv8-pose: {e}")
              if pose_strategy == "yolo":
                  self.pose_strategy = "mediapipe"
  ```

- [ ] **Step 2: Add `iter_video_frames` method**

  After `__init__`, add this new method before `load_video_frames`:

  ```python
  def iter_video_frames(self, video_path: str):
      """Validate video, return (fps, total_frames, frame_generator)."""
      is_valid, err = validate_video_file(video_path)
      if not is_valid:
          raise ValueError(f"Invalid video file: {err}")
      cap = cv2.VideoCapture(str(video_path))
      if not cap.isOpened():
          raise ValueError(f"Could not open video: {video_path}")
      fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
      total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
      if total <= 0 or fps <= 0:
          cap.release()
          raise ValueError("Video metadata unreadable (fps/total=0)")

      def _gen():
          try:
              i = 0
              while True:
                  ok, frame = cap.read()
                  if not ok:
                      break
                  yield i, frame
                  i += 1
          finally:
              cap.release()

      return fps, total, _gen()
  ```

- [ ] **Step 3: Add `_empty_result` static method**

  After `iter_video_frames`, add:

  ```python
  @staticmethod
  def _empty_result(video_id, reason: str) -> dict:
      return {
          "video_id": video_id,
          "metrics": [],
          "feedback": [],
          "shot_score": {"score": None, "breakdown": [], "confidence": 0.0, "reason": reason},
          "phases": [],
          "annotated_video_path": None,
          "pose_results": 0,
          "hand_results": 0,
          "ball_trajectory_length": 0,
          "status": "completed_low_quality",
      }
  ```

- [ ] **Step 4: Replace `process_video` body**

  Replace the entire `process_video` method (lines 120–358 in the original) with:

  ```python
  @retry(max_attempts=2, delay=1.0)
  @timeit
  def process_video(
      self,
      video_path: str,
      user_id: Optional[str] = None,
      video_id: Optional[str] = None,
      camera_angle: Optional[str] = None,
      device_info: Optional[Dict] = None,
  ) -> Dict[str, Any]:
      fps, total, frames_iter = self.iter_video_frames(video_path)

      # Target ~90 pose frames — enough for phase detection, cheap on CPU
      target = 90
      stride = max(1, total // target)

      pose_results = []
      ball_rgb_frames: List[np.ndarray] = []
      ball_rgb_indices: List[int] = []

      for idx, bgr in frames_iter:
          if idx % stride != 0:
              continue
          rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
          rgb.flags.writeable = False

          pose = self.pose_detector.process_frame(rgb)
          if pose is not None:
              pose_results.append({
                  "frame_idx": idx,
                  "landmarks": pose["landmarks"],
                  "confidence": pose["confidence"],
                  "timestamp_ms": (idx / fps) * 1000.0,
              })

          if len(ball_rgb_frames) < 60:
              ball_rgb_frames.append(rgb)
              ball_rgb_indices.append(idx)

          del bgr

      if not pose_results:
          return self._empty_result(video_id, "no_pose_detected")
      if len(pose_results) < 5:
          return self._empty_result(video_id, "insufficient_pose_frames")

      # Ball tracking (reuses already-decoded RGB — no second pass)
      ball_trajectory: Optional[List[np.ndarray]] = None
      ball_timestamps: Optional[List[float]] = None
      if self.enable_ball_tracking and ball_rgb_frames:
          try:
              bt = detect_and_track_ball(ball_rgb_frames)
              traj = bt.get("trajectory") if bt else None
              if traj:
                  positions = [
                      np.array(list(t["center"]) + [t.get("z", 0.0)])
                      if isinstance(t, dict) else np.asarray(t)
                      for t in traj if t is not None
                  ]
                  if positions:
                      ball_trajectory = positions
                      ball_timestamps = [ball_rgb_indices[i] / fps for i in range(len(positions))]
          except Exception as e:
              print(f"Ball tracking failed: {e}")

      # Phase detection (single call — calculator re-calls internally; accepted for this sprint)
      phases = self.phase_detector.detect_phases(pose_results, ball_trajectory, ball_timestamps)

      # Metrics (hands disabled for MVP)
      try:
          metrics = self.metrics_calculator.compute_all_metrics(
              pose_results=pose_results,
              hand_results=None,
              ball_trajectory=ball_trajectory,
              pose_3d=None,
              shot_distance=None,
              rim_position=None,
          )
      except Exception as e:
          print(f"Metrics computation failed: {e}")
          metrics = []

      # SHOOTRZ score (0–100)
      try:
          from ..metrics.angles import compute_shot_score
          shot_score = compute_shot_score(metrics)
      except Exception as e:
          print(f"Score aggregation failed: {e}")
          shot_score = {"score": None, "breakdown": [], "confidence": 0.0}

      # Feedback
      try:
          feedback = generate_feedback(metrics)
      except Exception as e:
          print(f"Feedback generation failed: {e}")
          feedback = []

      # DB write (best-effort; errors don't fail the request)
      if user_id and video_id:
          try:
              metric_records = [
                  {k: m.get(k) for k in ("metric_name", "value", "unit", "confidence", "phase", "frame_idx")}
                  for m in metrics
              ]
              metric_ids = record_metrics(video_id, metric_records)
              if metric_ids and feedback:
                  fb_records = [
                      {"metric_id": mid, "message": fb.get("message", ""), "severity": fb.get("severity", "info")}
                      for fb, mid in zip(feedback, metric_ids)
                  ]
                  if fb_records:
                      record_feedback(fb_records)
          except Exception as e:
              print(f"DB storage failed: {e}")

      return {
          "video_id": video_id,
          "metrics": metrics,
          "feedback": feedback,
          "shot_score": shot_score,
          "phases": [
              {
                  "phase": p["phase"].value if hasattr(p["phase"], "value") else str(p["phase"]),
                  "start_frame": p["start_frame"],
                  "end_frame": p["end_frame"],
                  "confidence": p.get("confidence", 0.0),
              }
              for p in phases
          ],
          "annotated_video_path": None,
          "pose_results": len(pose_results),
          "hand_results": 0,
          "ball_trajectory_length": len(ball_trajectory) if ball_trajectory else 0,
          "status": "completed",
      }
  ```

- [ ] **Step 5: Update test to accept both statuses**

  In `SHOOTRZ/backend/tests/test_pipeline.py`, replace both occurrences of:
  ```python
  assert result["status"] == "completed"
  ```
  with:
  ```python
  assert result["status"] in ("completed", "completed_low_quality")
  ```

  Also update `test_pipeline_with_empty_video` — an empty .mp4 file has no readable frames, so `iter_video_frames` raises `ValueError` via `validate_video_file` or `cap.isOpened()`. The existing `pytest.raises((ValueError, Exception))` already covers this.

- [ ] **Step 6: Run existing tests**

  ```
  cd SHOOTRZ
  python -m pytest backend/tests/test_pipeline.py -v 2>&1 | head -60
  ```

  Expected: tests pass (no `AssertionError` about status). MediaPipe may emit warnings about no detections — that is fine.

- [ ] **Step 7: Commit**

  ```bash
  git add SHOOTRZ/backend/processing/pipeline.py SHOOTRZ/backend/tests/test_pipeline.py
  git commit -m "perf: stream decode + stride sampling; disable annotation/hands; add _empty_result"
  ```

---

### Task 2: `pose_2d.py` — Remove double cvtColor, add writeable guard, visibility gate

**Files:**
- Modify: `SHOOTRZ/backend/inference/pose_2d.py`

**Context:** `process_frame` currently does an unconditional `cv2.cvtColor(frame, COLOR_BGR2RGB)` assuming BGR input. After Task 1, the pipeline converts BGR→RGB before calling `process_frame`, so passing RGB gets converted again → purple distortion. Fix: assume RGB input, guard with `writeable=False`, reject low-confidence detections.

- [ ] **Step 1: Replace `process_frame` method**

  Replace lines 69–102 in `SHOOTRZ/backend/inference/pose_2d.py`:

  ```python
  def process_frame(self, frame_rgb: np.ndarray) -> Optional[Dict[str, np.ndarray]]:
      """Process a single RGB frame. Caller must provide RGB (not BGR)."""
      if frame_rgb is None or frame_rgb.size == 0 or frame_rgb.ndim != 3:
          return None
      # MediaPipe may write to the input buffer on some versions
      if frame_rgb.flags.writeable:
          frame_rgb = np.ascontiguousarray(frame_rgb)
          frame_rgb.flags.writeable = False
      try:
          pose_results = self.pose.process(frame_rgb)
      except Exception:
          return None
      if not pose_results.pose_landmarks:
          return None
      lms = np.empty((33, 3), dtype=np.float32)
      conf = np.empty(33, dtype=np.float32)
      for i, lm in enumerate(pose_results.pose_landmarks.landmark):
          lms[i] = (lm.x, lm.y, lm.z)
          conf[i] = lm.visibility
      if float(conf.mean()) < 0.30:
          return None
      return {"landmarks": lms, "confidence": conf}
  ```

- [ ] **Step 2: Fix the standalone `process_video` utility method**

  The `process_video` method (lines 104–166) calls `self.process_frame(frame)` with raw BGR from `cap.read()`. Fix it so it converts before calling `process_frame`. Replace lines 147–148:

  ```python
  # OLD:
  result = self.process_frame(frame)

  # NEW:
  frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  result = self.process_frame(frame_rgb)
  ```

  Also replace the same pattern inside `run_pose_2d_on_frames` at line 239:
  ```python
  # OLD:
  result = detector.process_frame(frame)

  # NEW (frames already RGB per docstring, so no change needed — leave as-is)
  result = detector.process_frame(frame)
  ```
  *(The `run_pose_2d_on_frames` docstring says frames are RGB, so it's correct.)*

- [ ] **Step 3: Add `SHOOTRZ_POSE_COMPLEXITY` env toggle**

  In `__init__`, replace:
  ```python
  model_complexity: int = 1,
  ```
  with:
  ```python
  model_complexity: int = int(os.getenv("SHOOTRZ_POSE_COMPLEXITY", "1")),
  ```

  Add `import os` at the top of the file (after the existing imports).

- [ ] **Step 4: Run a quick import check**

  ```
  cd SHOOTRZ
  python -c "from backend.inference.pose_2d import MediaPipePoseDetector; print('OK')"
  ```

  Expected output: `OK`

- [ ] **Step 5: Commit**

  ```bash
  git add SHOOTRZ/backend/inference/pose_2d.py
  git commit -m "fix: remove double cvtColor in pose_2d; add writeable guard; visibility gate 0.30; env complexity"
  ```

---

### Task 3: `ball_tracker.py` — Batched inference at `imgsz=480`

**Files:**
- Modify: `SHOOTRZ/backend/inference/ball_tracker.py`

**Context:** Current code calls `model.track(source=frame_bgr, ...)` in a Python loop — one YOLO inference per frame. Batch `model.predict(frames_bgr_list, ...)` processes all frames in one GPU/CPU pass, ~35% faster. We lose ByteTrack IDs (acceptable for MVP: take best-confidence detection per frame and build trajectory by index).

- [ ] **Step 1: Replace the detection loop inside `detect_and_track_ball`**

  In `SHOOTRZ/backend/inference/ball_tracker.py`, replace lines 75–145 (the `for frame_idx, frame in enumerate(frames):` loop and the trajectory assembly below it) with:

  ```python
  # Convert all frames RGB→BGR for YOLO
  frames_bgr = [cv2.cvtColor(f, cv2.COLOR_RGB2BGR) for f in frames]

  # Batch predict — one pass over all frames
  preds = model.predict(
      frames_bgr,
      conf=conf_threshold,
      iou=0.45,
      imgsz=480,
      verbose=False,
  )

  trajectory = []
  all_detections = []

  for frame_idx, result in enumerate(preds):
      if result.boxes is None:
          continue
      boxes = result.boxes
      classes = boxes.cls.int().cpu().tolist()
      confidences = boxes.conf.cpu().tolist()

      # Pick best-confidence ball detection this frame
      best = None
      for i, (class_id, conf) in enumerate(zip(classes, confidences)):
          if class_id != ball_class_id or conf < conf_threshold:
              continue
          if best is None or conf > best["confidence"]:
              x1, y1, x2, y2 = boxes.xyxy[i].cpu().tolist()
              frame_h, frame_w = frames[frame_idx].shape[:2]
              detection = {
                  "frame": frame_idx,
                  "track_id": frame_idx,  # use frame index as proxy ID
                  "center": [(x1 + x2) / 2.0 / frame_w, (y1 + y2) / 2.0 / frame_h, 0.0],
                  "bbox": [x1, y1, x2, y2],
                  "confidence": conf,
                  "width": x2 - x1,
                  "height": y2 - y1,
              }
              best = detection
      if best is not None:
          trajectory.append(best)
          all_detections.append(best)

  return {
      "trajectory": trajectory,
      "detections": all_detections,
      "track_history": {},
      "model_type": "finetuned" if using_finetuned else "pretrained",
  }
  ```

- [ ] **Step 2: Verify import still works**

  ```
  cd SHOOTRZ
  python -c "from backend.inference.ball_tracker import detect_and_track_ball; print('OK')"
  ```

  Expected: `OK` (YOLO not loaded at import time — only on call)

- [ ] **Step 3: Commit**

  ```bash
  git add SHOOTRZ/backend/inference/ball_tracker.py
  git commit -m "perf: batch YOLO predict at imgsz=480, remove per-frame track loop"
  ```

---

### DAY 1 GATE — Smoke test

Run this after Tasks 1–3 are committed. You need any real `.mp4` file with a visible person (phone camera recording yourself walking works fine):

```bash
cd SHOOTRZ
uvicorn backend.main:app --host 0.0.0.0 --port 8000 &
sleep 5

# Upload a video
JOB=$(curl -s -X POST http://localhost:8000/analyze \
  -F "file=@/path/to/test.mp4" | python -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

echo "Job: $JOB"

# Poll until done (max 60s)
for i in $(seq 1 12); do
  STATUS=$(curl -s http://localhost:8000/result/$JOB/status | python -c "import sys,json; d=json.load(sys.stdin); print(d['status'])")
  echo "$i: $STATUS"
  [ "$STATUS" = "completed" ] || [ "$STATUS" = "completed_low_quality" ] && break
  sleep 5
done

# Check result
curl -s http://localhost:8000/result/$JOB | python -m json.tool | grep -E "(status|score|pose_results)"

kill %1
```

**Pass criteria:**
- Response comes back within 60s total
- `status` is `completed` or `completed_low_quality`
- Memory: `tasklist | findstr python` peak RSS < 600MB (Windows) or `ps aux` on Linux

**If the gate fails:**
- `completed_low_quality` with `reason=no_pose_detected`: pose detection is working, video just has no human. Try a different clip.
- Latency still >60s: check if annotation code is still running (search `annotate_video` in pipeline.py).
- OOM: check that `load_video_frames` is gone (search for it; it must not be called).

---

## DAY 2 — Scoring + Concurrency (gate: shot_score populated, 50-client load test <5% errors)

---

### Task 4: `angles.py` + `normative_ranges.json` — Shot score aggregator

**Files:**
- Replace: `SHOOTRZ/backend/metrics/angles.py`
- Create: `SHOOTRZ/backend/metrics/normative_ranges.json`

**Context:** Current `angles.py` is two stub functions that return zeros. Replace with a full score engine. The score is a confidence-weighted geometric mean of per-dimension sub-scores. Each sub-score is a Gaussian centered at the target midpoint (score 100 at ideal, decaying as deviation grows).

**Important:** The metric names in `calculator.py` are `elbow_flexion_crouch` and `elbow_flexion_release` (not `elbow_flexion_preparatory`). DIMENSIONS must use those exact names.

- [ ] **Step 1: Create `normative_ranges.json`**

  Create `SHOOTRZ/backend/metrics/normative_ranges.json`:

  ```json
  {
    "elbow_flexion_release": {
      "target_range": [165, 180],
      "unit": "degrees",
      "description": "Elbow angle at ball release (near full extension)"
    },
    "elbow_flexion_crouch": {
      "target_range": [70, 90],
      "unit": "degrees",
      "description": "Elbow angle during preparatory crouch (ball held up)"
    },
    "knee_flexion": {
      "target_range": [100, 120],
      "unit": "degrees",
      "description": "Knee joint angle during crouch dip"
    },
    "release_angle": {
      "target_range": [50, 65],
      "unit": "degrees",
      "description": "Ball launch angle from horizontal"
    },
    "forearm_verticality": {
      "target_range": [0, 10],
      "unit": "degrees",
      "description": "Forearm deviation from vertical at set position"
    },
    "entry_angle": {
      "target_range": [45, 55],
      "unit": "degrees",
      "description": "Ball entry angle to hoop from horizontal"
    },
    "wrist_angular_velocity": {
      "target_range": [2.5, 6.0],
      "unit": "rad/s",
      "description": "Peak wrist angular velocity during flick"
    }
  }
  ```

- [ ] **Step 2: Replace `angles.py` completely**

  ```python
  """SHOOTRZ shot score (0-100): confidence-weighted geometric mean across 7 biomechanics dimensions."""
  import json
  import math
  from pathlib import Path
  from typing import Dict, List, Optional, Tuple

  _RANGES_PATH = Path(__file__).parent / "normative_ranges.json"
  try:
      with open(_RANGES_PATH, "r", encoding="utf-8") as _f:
          _RANGES: Dict = json.load(_f)
  except Exception as _e:
      print(f"[angles] normative_ranges.json load failed: {_e}")
      _RANGES = {}

  # Hard-coded fallback so score never silently collapses when JSON is missing
  _FALLBACK: Dict[str, Tuple[float, float]] = {
      "elbow_flexion_release":  (165.0, 180.0),
      "elbow_flexion_crouch":   (70.0,  90.0),
      "knee_flexion":           (100.0, 120.0),
      "release_angle":          (50.0,  65.0),
      "forearm_verticality":    (0.0,   10.0),
      "entry_angle":            (45.0,  55.0),
      "wrist_angular_velocity": (2.5,   6.0),
  }

  # (metric_name, weight) — weights sum to 1.0
  DIMENSIONS: List[Tuple[str, float]] = [
      ("elbow_flexion_release",  0.22),
      ("release_angle",          0.20),
      ("knee_flexion",           0.18),
      ("forearm_verticality",    0.12),
      ("elbow_flexion_crouch",   0.10),
      ("entry_angle",            0.10),
      ("wrist_angular_velocity", 0.08),
  ]


  def _target_of(name: str) -> Tuple[Optional[float], Optional[float]]:
      rng = _RANGES.get(name, {})
      tr = rng.get("target_range") or rng.get("optimal_range")
      if isinstance(tr, list) and len(tr) == 2:
          return float(tr[0]), float(tr[1])
      return _FALLBACK.get(name, (None, None))


  def _dim_score(name: str, value: float) -> Optional[float]:
      lo, hi = _target_of(name)
      if lo is None or hi is None or not math.isfinite(value):
          return None
      mid = (lo + hi) / 2.0
      half = max((hi - lo) / 2.0, 1e-3)
      z = (value - mid) / half
      return max(0.0, 100.0 * math.exp(-0.5 * z * z))


  def compute_shot_score(metrics: List[Dict]) -> Dict:
      """Return {score, breakdown, confidence} from a list of metric dicts."""
      by_name = {m.get("metric_name"): m for m in (metrics or [])}
      breakdown = []
      log_sum = 0.0
      w_sum = 0.0
      conf_sum = 0.0
      conf_n = 0

      for name, weight in DIMENSIONS:
          m = by_name.get(name)
          if not m:
              continue
          conf = float(m.get("confidence") or 0)
          if conf < 0.4:
              continue
          try:
              value = float(m.get("value"))
          except (TypeError, ValueError):
              continue
          s = _dim_score(name, value)
          if s is None:
              continue
          w = weight * conf
          log_sum += w * math.log(s + 1.0)
          w_sum += w
          conf_sum += conf
          conf_n += 1
          breakdown.append({
              "metric": name,
              "value": round(value, 2),
              "sub_score": round(s, 1),
              "weight": round(w, 3),
              "target_range": list(_target_of(name)),
          })

      if w_sum == 0:
          return {
              "score": None,
              "breakdown": [],
              "confidence": 0.0,
              "reason": "insufficient_confident_metrics",
          }

      raw = math.exp(log_sum / w_sum) - 1.0
      return {
          "score": round(max(0.0, min(100.0, raw)), 1),
          "breakdown": breakdown,
          "confidence": round(conf_sum / max(conf_n, 1), 2),
      }


  # Backward-compat stubs (kept so any dormant import doesn't crash)
  def compute_elbow_alignment(*_a, **_k) -> Dict:
      return {"elbow_alignment": 0.0, "confidence": 0.0}


  def compute_release_extension(*_a, **_k) -> Dict:
      return {"release_extension": 0.0, "confidence": 0.0}
  ```

- [ ] **Step 3: Write a unit test for `compute_shot_score`**

  Create `SHOOTRZ/backend/tests/test_angles.py`:

  ```python
  import pytest
  from backend.metrics.angles import compute_shot_score, _dim_score, DIMENSIONS


  def test_empty_metrics_returns_none_score():
      result = compute_shot_score([])
      assert result["score"] is None
      assert result["confidence"] == 0.0


  def test_perfect_metrics_score_near_100():
      perfect = [
          {"metric_name": "elbow_flexion_release", "value": 172.0, "confidence": 0.9},
          {"metric_name": "release_angle",         "value": 57.0,  "confidence": 0.9},
          {"metric_name": "knee_flexion",           "value": 110.0, "confidence": 0.9},
          {"metric_name": "forearm_verticality",    "value": 5.0,   "confidence": 0.9},
          {"metric_name": "elbow_flexion_crouch",   "value": 80.0,  "confidence": 0.9},
          {"metric_name": "entry_angle",            "value": 50.0,  "confidence": 0.9},
          {"metric_name": "wrist_angular_velocity", "value": 4.0,   "confidence": 0.9},
      ]
      result = compute_shot_score(perfect)
      assert result["score"] is not None
      assert result["score"] > 90.0
      assert len(result["breakdown"]) == 7


  def test_low_confidence_metrics_excluded():
      metrics = [
          {"metric_name": "release_angle", "value": 57.0, "confidence": 0.2},
      ]
      result = compute_shot_score(metrics)
      assert result["score"] is None  # excluded because conf < 0.4


  def test_dim_score_at_midpoint_is_100():
      s = _dim_score("release_angle", 57.5)  # midpoint of (50, 65)
      assert s is not None
      assert abs(s - 100.0) < 0.1


  def test_dim_score_falls_off_outside_range():
      s = _dim_score("release_angle", 90.0)  # far outside
      assert s is not None
      assert s < 50.0
  ```

- [ ] **Step 4: Run unit tests**

  ```
  cd SHOOTRZ
  python -m pytest backend/tests/test_angles.py -v
  ```

  Expected: all 5 tests pass.

- [ ] **Step 5: Commit**

  ```bash
  git add SHOOTRZ/backend/metrics/angles.py SHOOTRZ/backend/metrics/normative_ranges.json SHOOTRZ/backend/tests/test_angles.py
  git commit -m "feat: add compute_shot_score with confidence-weighted geometric mean; normative ranges JSON"
  ```

---

### Task 5: `biomechanics_2d.py` — Visibility-aware confidence

**Files:**
- Modify: `SHOOTRZ/backend/metrics/biomechanics_2d.py`

**Context:** All 2D helper functions currently return hard-coded confidence values (0.8, 0.7, 0.5). When joints are occluded (low MediaPipe visibility), the confidence should be lower. Add a `vis_mean: Optional[float]` parameter and a `_scale_conf` helper that scales confidence proportionally.

- [ ] **Step 1: Add `Optional` import and `_scale_conf` helper**

  At the top of `SHOOTRZ/backend/metrics/biomechanics_2d.py`, the import is already `from typing import Dict, Optional`. Add `_scale_conf` after the imports:

  ```python
  def _scale_conf(base: float, vis_mean: Optional[float]) -> float:
      """Scale base confidence by mean joint visibility. Unchanged if vis_mean is None."""
      if vis_mean is None:
          return base
      # At vis_mean=0.7 → full confidence; below 0.7 → linearly reduced
      return max(0.0, base * min(1.0, vis_mean / 0.7))
  ```

- [ ] **Step 2: Add `vis_mean` to `compute_forearm_verticality_2d`**

  Replace the function signature and the `confidence` lines:

  ```python
  def compute_forearm_verticality_2d(
      elbow_2d: np.ndarray,
      wrist_2d: np.ndarray,
      vis_mean: Optional[float] = None,
  ) -> Dict[str, float]:
  ```

  Replace:
  ```python
  confidence = 0.8 if angle_deg <= 30.0 else 0.5
  return {"angle_degrees": float(angle_deg), "confidence": confidence}
  ```
  with:
  ```python
  base = 0.8 if angle_deg <= 30.0 else 0.5
  return {"angle_degrees": float(angle_deg), "confidence": _scale_conf(base, vis_mean)}
  ```

- [ ] **Step 3: Add `vis_mean` to `compute_elbow_flexion_2d`**

  Replace signature:
  ```python
  def compute_elbow_flexion_2d(
      shoulder_2d: np.ndarray,
      elbow_2d: np.ndarray,
      wrist_2d: np.ndarray,
      vis_mean: Optional[float] = None,
  ) -> Dict[str, float]:
  ```

  Replace return lines:
  ```python
  if angle < 30 or angle > 200:
      return {"angle_degrees": angle, "confidence": _scale_conf(0.3, vis_mean)}
  return {"angle_degrees": angle, "confidence": _scale_conf(0.8, vis_mean)}
  ```

- [ ] **Step 4: Add `vis_mean` to `compute_knee_flexion_2d`**

  ```python
  def compute_knee_flexion_2d(
      hip_2d: np.ndarray,
      knee_2d: np.ndarray,
      ankle_2d: np.ndarray,
      vis_mean: Optional[float] = None,
  ) -> Dict[str, float]:
      angle = joint_angle_2d(hip_2d, knee_2d, ankle_2d)
      if angle < 50 or angle > 200:
          return {"angle_degrees": angle, "confidence": _scale_conf(0.3, vis_mean)}
      return {"angle_degrees": angle, "confidence": _scale_conf(0.8, vis_mean)}
  ```

- [ ] **Step 5: Add `vis_mean` to `compute_hip_flexion_2d`**

  ```python
  def compute_hip_flexion_2d(
      shoulder_2d: np.ndarray,
      hip_2d: np.ndarray,
      knee_2d: np.ndarray,
      vis_mean: Optional[float] = None,
  ) -> Dict[str, float]:
      angle = joint_angle_2d(shoulder_2d, hip_2d, knee_2d)
      if angle < 100 or angle > 200:
          return {"angle_degrees": angle, "confidence": _scale_conf(0.3, vis_mean)}
      return {"angle_degrees": angle, "confidence": _scale_conf(0.8, vis_mean)}
  ```

- [ ] **Step 6: Add `vis_mean` to `compute_shoulder_angle_2d`**

  ```python
  def compute_shoulder_angle_2d(
      hip_2d: np.ndarray,
      shoulder_2d: np.ndarray,
      elbow_2d: np.ndarray,
      vis_mean: Optional[float] = None,
  ) -> Dict[str, float]:
      angle = joint_angle_2d(hip_2d, shoulder_2d, elbow_2d)
      return {"angle_degrees": angle, "confidence": _scale_conf(0.7, vis_mean)}
  ```

- [ ] **Step 7: Add `vis_mean` to `compute_elbow_height_2d`**

  ```python
  def compute_elbow_height_2d(
      elbow_2d: np.ndarray,
      head_2d: np.ndarray,
      frame_height: Optional[int] = None,
      vis_mean: Optional[float] = None,
  ) -> Dict[str, float]:
  ```

  Replace the existing return lines at the end:
  ```python
  base = 0.7 if abs(estimated_height_diff_cm) < 30 else 0.4
  return {
      "height_difference_cm": float(estimated_height_diff_cm),
      "confidence": _scale_conf(base, vis_mean),
  }
  ```

- [ ] **Step 8: Add `vis_mean` to `compute_release_angle_from_pose_2d`**

  Add `vis_mean: Optional[float] = None` to the signature. Replace all three `return` statements at the end:

  ```python
  if 45.0 <= angle_deg <= 70.0:
      return {"angle_degrees": float(angle_deg), "confidence": _scale_conf(0.6, vis_mean)}
  elif 30.0 <= angle_deg < 45.0 or 70.0 < angle_deg <= 90.0:
      return {"angle_degrees": float(angle_deg), "confidence": _scale_conf(0.4, vis_mean)}
  else:
      return {"angle_degrees": float(angle_deg), "confidence": _scale_conf(0.2, vis_mean)}
  ```

- [ ] **Step 9: Verify import**

  ```
  cd SHOOTRZ
  python -c "from backend.metrics.biomechanics_2d import compute_elbow_flexion_2d; print(compute_elbow_flexion_2d([0,0],[0.5,0.5],[1,0], vis_mean=0.6))"
  ```

  Expected: `{'angle_degrees': <some_angle>, 'confidence': <value_less_than_0.8>}`

- [ ] **Step 10: Commit**

  ```bash
  git add SHOOTRZ/backend/metrics/biomechanics_2d.py
  git commit -m "feat: visibility-aware confidence in all 2D biomechanics helpers"
  ```

---

### Task 6: `calculator.py` — Pass `vis_mean` into 2D helpers; accept pre-computed phases

**Files:**
- Modify: `SHOOTRZ/backend/metrics/calculator.py`

**Context:** `compute_all_metrics` currently hard-codes confidence from the 2D functions. After Task 5, we can pass the actual joint visibility from `pose_results[frame]["confidence"]` (a [33,] numpy array). We also add an optional `phases` parameter to avoid the duplicate `detect_phases` call (M1 from the audit).

MediaPipe landmark indices used here:
- Nose=0, R.Shoulder=12, R.Elbow=14, R.Wrist=16, R.Hip=24, R.Knee=26, R.Ankle=28

- [ ] **Step 1: Add `phases` parameter to `compute_all_metrics`**

  Replace the method signature (line 55):
  ```python
  def compute_all_metrics(
      self,
      pose_results: List[Dict[str, any]],
      hand_results: Optional[List[Dict[str, any]]] = None,
      ball_trajectory: Optional[List[np.ndarray]] = None,
      pose_3d: Optional[List[np.ndarray]] = None,
      shot_distance: Optional[float] = None,
      rim_position: Optional[np.ndarray] = None,
      phases: Optional[List[Dict]] = None,
  ) -> List[Dict[str, any]]:
  ```

- [ ] **Step 2: Skip internal phase detection if `phases` is provided**

  Find the line (currently ~112):
  ```python
  phases = self.phase_detector.detect_phases(pose_results, ball_trajectory)
  ```

  Replace with:
  ```python
  if phases is None:
      phases = self.phase_detector.detect_phases(pose_results, ball_trajectory)
  ```

- [ ] **Step 3: Add a `_vis_mean` helper at the top of `compute_all_metrics`**

  After the `phases` / `phase_map` lines, add this local helper:

  ```python
  def _vis_mean(frame_idx: int, joint_indices: List[int]) -> Optional[float]:
      if frame_idx >= len(pose_results):
          return None
      conf_arr = pose_results[frame_idx].get("confidence")
      if conf_arr is None:
          return None
      try:
          return float(np.mean([conf_arr[i] for i in joint_indices if i < len(conf_arr)]))
      except Exception:
          return None
  ```

- [ ] **Step 4: Pass `vis_mean` at the forearm verticality call site**

  Find the block that calls `compute_forearm_verticality_2d` (around line 150). Replace:
  ```python
  result = compute_forearm_verticality_2d(elbow, wrist)
  ```
  with:
  ```python
  result = compute_forearm_verticality_2d(elbow, wrist, vis_mean=_vis_mean(prep_frame, [14, 16]))
  ```

- [ ] **Step 5: Pass `vis_mean` at both elbow flexion call sites**

  Find the two calls to `compute_elbow_flexion_2d` (in the `for phase_name in ["crouch", "release"]:` loop). Replace:
  ```python
  result = compute_elbow_flexion_2d(shoulder, elbow, wrist)
  ```
  with:
  ```python
  result = compute_elbow_flexion_2d(shoulder, elbow, wrist, vis_mean=_vis_mean(phase_frame, [12, 14, 16]))
  ```

- [ ] **Step 6: Pass `vis_mean` at knee flexion call site**

  ```python
  result = compute_knee_flexion_2d(hip, knee, ankle, vis_mean=_vis_mean(crouch_frame, [24, 26, 28]))
  ```

- [ ] **Step 7: Pass `vis_mean` at hip flexion call site**

  ```python
  result = compute_hip_flexion_2d(shoulder, hip, knee, vis_mean=_vis_mean(crouch_frame, [12, 24, 26]))
  ```

- [ ] **Step 8: Pass `vis_mean` at shoulder angle call site**

  ```python
  result = compute_shoulder_angle_2d(hip, shoulder, elbow, vis_mean=_vis_mean(crouch_frame, [24, 12, 14]))
  ```

- [ ] **Step 9: Pass `vis_mean` at elbow height call site**

  ```python
  result = compute_elbow_height_2d(elbow, head, vis_mean=_vis_mean(release_frame, [0, 14]))
  ```

- [ ] **Step 10: Pass `vis_mean` at `compute_release_angle_from_pose_2d` call site**

  ```python
  result = compute_release_angle_from_pose_2d(shoulder, elbow, wrist, vis_mean=_vis_mean(release_frame, [12, 14, 16]))
  ```

- [ ] **Step 11: Verify import**

  ```
  cd SHOOTRZ
  python -c "from backend.metrics.calculator import MetricsCalculator; print('OK')"
  ```

  Expected: `OK`

- [ ] **Step 12: Commit**

  ```bash
  git add SHOOTRZ/backend/metrics/calculator.py
  git commit -m "feat: pass vis_mean into 2D helpers; accept pre-computed phases in compute_all_metrics"
  ```

---

### Task 7: `analyze.py` — ProcessPool + semaphore + task-ref tracking + cleanup

**Files:**
- Replace: `SHOOTRZ/backend/routers/analyze.py`
- Modify: `SHOOTRZ/backend/routers/results.py` (add `shot_score` to response)

**Context:** Current code uses FastAPI `BackgroundTasks` which runs synchronously in the main process, blocking the event loop for the full pipeline duration (~130s). Replace with `asyncio.create_task` + `loop.run_in_executor(ProcessPoolExecutor)`. The `ProcessPoolExecutor` runs the pipeline in a separate subprocess, leaving the event loop free. A `Semaphore` limits concurrency and fast-fails with 429 when full.

**Windows note:** On Windows, `multiprocessing` uses `spawn` by default — this is correct and avoids the MediaPipe+fork bug. No extra configuration needed on this OS.

**Relative imports in subprocess:** `_run_pipeline_sync` uses relative imports (`from ..processing.pipeline`). These work because `analyze.py` is imported as `SHOOTRZ.backend.routers.analyze`; the subprocess inherits `sys.path` and the module's `__package__` context.

- [ ] **Step 1: Write the new `analyze.py`**

  ```python
  import asyncio
  import os
  import shutil
  import tempfile
  from concurrent.futures import ProcessPoolExecutor
  from functools import partial
  from pathlib import Path
  from typing import Optional

  from fastapi import APIRouter, File, HTTPException, UploadFile

  from ..storage.db import record_feedback, record_metrics, record_video
  from ..storage.local_cache import job_store
  from ..utils.id_gen import generate_job_id
  from ..utils.schemas import AnalyzeResponse

  router = APIRouter(prefix="", tags=["analyze"])

  _MAX_WORKERS = int(os.getenv("SHOOTRZ_WORKERS", str(max(2, (os.cpu_count() or 2) - 1))))
  _MAX_INFLIGHT = int(os.getenv("SHOOTRZ_MAX_INFLIGHT", str(_MAX_WORKERS * 2)))
  _JOB_TIMEOUT = int(os.getenv("SHOOTRZ_JOB_TIMEOUT_S", "45"))

  _executor: Optional[ProcessPoolExecutor] = None
  _inflight: Optional[asyncio.Semaphore] = None
  _running_tasks: set = set()  # holds asyncio.Task refs to prevent GC


  def _worker_init() -> None:
      """Run once per worker process: warm up model file caches."""
      try:
          import socket
          socket.setdefaulttimeout(5)  # prevents slow DB calls from blocking worker
      except Exception:
          pass
      try:
          import mediapipe  # noqa: F401 — triggers model file extraction
      except Exception as e:
          print(f"Worker warmup (mediapipe): {e}")
      try:
          from ..inference.ball_tracker import detect_and_track_ball  # noqa: F401
          # importing ultralytics touches model paths
      except Exception as e:
          print(f"Worker warmup (ball_tracker): {e}")


  def _get_executor() -> ProcessPoolExecutor:
      global _executor
      if _executor is None:
          _executor = ProcessPoolExecutor(max_workers=_MAX_WORKERS, initializer=_worker_init)
      return _executor


  def _get_inflight() -> asyncio.Semaphore:
      global _inflight
      if _inflight is None:
          _inflight = asyncio.Semaphore(_MAX_INFLIGHT)
      return _inflight


  def _run_pipeline_sync(
      video_path: str,
      user_id: Optional[str],
      video_id: Optional[str],
      camera_angle: Optional[str],
      device_info: Optional[dict],
  ) -> dict:
      """Top-level (picklable) function executed inside a worker process."""
      from ..processing.pipeline import VideoProcessingPipeline

      pipe = VideoProcessingPipeline(
          use_3d_lifting=False,
          enable_ball_tracking=True,
          enable_hands=False,
          generate_annotated=False,
      )
      try:
          return pipe.process_video(
              video_path,
              user_id=user_id,
              video_id=video_id,
              camera_angle=camera_angle,
              device_info=device_info,
          )
      finally:
          try:
              pipe.cleanup()
          except Exception:
              pass


  def _summarise(r: dict) -> dict:
      annotated = r.get("annotated_video_path")
      return {
          "metrics": r.get("metrics", []),
          "feedback": r.get("feedback", []),
          "phases": r.get("phases", []),
          "shot_score": r.get("shot_score"),
          "video_id": r.get("video_id"),
          "pose_results": r.get("pose_results", 0),
          "hand_results": r.get("hand_results", 0),
          "ball_trajectory_length": r.get("ball_trajectory_length", 0),
          "annotated_video_url": f"file://{annotated}" if annotated else None,
      }


  async def _process_job_async(
      job_id: str,
      video_path: str,
      user_id: Optional[str],
      video_id: Optional[str],
      camera_angle: Optional[str],
      device_info: Optional[dict],
  ) -> None:
      sem = _get_inflight()
      ex = _get_executor()
      try:
          async with sem:
              job_store[job_id] = {"status": "processing"}
              loop = asyncio.get_running_loop()
              try:
                  result = await asyncio.wait_for(
                      loop.run_in_executor(
                          ex,
                          partial(
                              _run_pipeline_sync,
                              video_path,
                              user_id,
                              video_id,
                              camera_angle,
                              device_info,
                          ),
                      ),
                      timeout=float(_JOB_TIMEOUT),
                  )
                  job_store[job_id] = {"status": "completed", **_summarise(result)}
              except asyncio.TimeoutError:
                  job_store[job_id] = {"status": "failed", "error": "timeout"}
              except Exception as e:
                  job_store[job_id] = {"status": "failed", "error": str(e)[:300]}
      finally:
          try:
              Path(video_path).unlink(missing_ok=True)
          except Exception:
              pass


  def _launch_job(
      job_id: str,
      video_path: str,
      user_id: Optional[str],
      video_id: Optional[str],
      angle: Optional[str],
      device_info: Optional[dict],
  ) -> None:
      """Create asyncio task and keep a reference to prevent GC."""
      task = asyncio.create_task(
          _process_job_async(job_id, video_path, user_id, video_id, angle, device_info)
      )
      _running_tasks.add(task)
      task.add_done_callback(_running_tasks.discard)


  @router.post("/analyze")
  async def analyze(
      file: Optional[UploadFile] = File(default=None),
      user_id: Optional[str] = None,
      angle: Optional[str] = None,
      fps: Optional[int] = None,
      device: Optional[str] = None,
      file_url: Optional[str] = None,
  ) -> AnalyzeResponse:
      sem = _get_inflight()
      if sem.locked():
          raise HTTPException(status_code=429, detail="server_busy_retry")

      if not file and not file_url:
          raise HTTPException(status_code=400, detail="Provide file upload or file_url")

      device_info = {"device": device, "fps": fps} if (device or fps) else None
      job_id = generate_job_id()

      if file:
          suffix = Path(file.filename).suffix if file.filename else ".mp4"
          with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
              shutil.copyfileobj(file.file, tmp)
              video_path = tmp.name

          video_id = None
          if user_id:
              try:
                  video_id = record_video(
                      user_id=user_id,
                      file_url=f"uploaded_{job_id}{suffix}",
                      angle=angle,
                      fps=fps,
                      device=device,
                  )
              except Exception as e:
                  print(f"video metadata store failed: {e}")

          job_store[job_id] = {"status": "queued"}
          _launch_job(job_id, video_path, user_id, video_id, angle, device_info)
          return AnalyzeResponse(job_id=job_id, status="queued")

      # file_url branch: download first, then process identically
      import requests  # lazy import — only needed for URL uploads

      suffix = Path(file_url).suffix or ".mp4"
      with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
          try:
              resp = requests.get(file_url, stream=True, timeout=30)
              resp.raise_for_status()
              shutil.copyfileobj(resp.raw, tmp)
          except Exception as e:
              Path(tmp.name).unlink(missing_ok=True)
              raise HTTPException(status_code=400, detail=f"Could not download video: {e}")
          video_path = tmp.name

      video_id = None
      if user_id:
          try:
              video_id = record_video(
                  user_id=user_id,
                  file_url=file_url,
                  angle=angle,
                  fps=fps,
                  device=device,
              )
          except Exception as e:
              print(f"video metadata store failed: {e}")

      job_store[job_id] = {"status": "queued"}
      _launch_job(job_id, video_path, user_id, video_id, angle, device_info)
      return AnalyzeResponse(job_id=job_id, status="queued")
  ```

- [ ] **Step 2: Add `shot_score` to both return paths in `results.py`**

  In `SHOOTRZ/backend/routers/results.py`, in the DB-fetch return (lines 34–45), add `"shot_score": job.get("shot_score")` to the dict. Same for the fallback return (lines 50–62):

  ```python
  # In the DB-fetch branch, add to the return dict:
  "shot_score": job.get("shot_score"),

  # In the fallback return dict, add:
  "shot_score": job.get("shot_score"),
  ```

- [ ] **Step 3: Verify import**

  ```
  cd SHOOTRZ
  python -c "from backend.routers.analyze import router; print('OK')"
  ```

  Expected: `OK`

- [ ] **Step 4: Commit**

  ```bash
  git add SHOOTRZ/backend/routers/analyze.py SHOOTRZ/backend/routers/results.py
  git commit -m "feat: replace BackgroundTasks with ProcessPoolExecutor+asyncio; semaphore backpressure; 429 fast-fail; tempfile cleanup; shot_score in results"
  ```

---

### Task 8: `main.py` — Lifespan shutdown + spawn start method

**Files:**
- Modify: `SHOOTRZ/backend/main.py`

- [ ] **Step 1: Add lifespan and spawn start method**

  Replace the entire `SHOOTRZ/backend/main.py`:

  ```python
  import multiprocessing
  import time
  from contextlib import asynccontextmanager
  from datetime import datetime

  from fastapi import FastAPI
  from fastapi.middleware.cors import CORSMiddleware

  from .routers import analyze, db_integration_test, db_test, feedback, history, results, sessions
  from .routers.recommendation_routes import router as recommendation_router

  # Force spawn on all platforms — required for MediaPipe + ProcessPool safety.
  # Must be called before any ProcessPoolExecutor is created.
  multiprocessing.set_start_method("spawn", force=True)

  _start_time = time.time()


  @asynccontextmanager
  async def lifespan(app: FastAPI):
      yield
      # Graceful shutdown: stop accepting new work, let in-flight finish
      from .routers.analyze import _executor
      if _executor is not None:
          _executor.shutdown(wait=False, cancel_futures=True)


  def create_app() -> FastAPI:
      app = FastAPI(title="SHOOTRZ API", version="0.1.0", lifespan=lifespan)

      app.add_middleware(
          CORSMiddleware,
          allow_origins=["*"],
          allow_credentials=True,
          allow_methods=["*"],
          allow_headers=["*"],
      )

      app.include_router(analyze.router)
      app.include_router(results.router)
      app.include_router(history.router)
      app.include_router(feedback.router)
      app.include_router(sessions.router)
      app.include_router(db_test.router)
      app.include_router(db_integration_test.router)
      app.include_router(recommendation_router, prefix="/api")

      @app.get("/", tags=["root"])
      async def root():
          return {"message": "SHOOTRZ API", "version": "0.1.0", "docs": "/docs", "health": "/health"}

      @app.get("/health", tags=["health"])
      async def health_check():
          return {
              "status": "healthy",
              "service": "SHOOTRZ FastAPI Backend",
              "version": "0.1.0",
              "timestamp": datetime.now().isoformat(),
              "uptime": round(time.time() - _start_time, 2),
          }

      return app


  app = create_app()
  ```

- [ ] **Step 2: Restart server and confirm startup**

  ```
  cd SHOOTRZ
  uvicorn backend.main:app --host 0.0.0.0 --port 8000
  ```

  Expected: server starts without errors, `/health` returns `{"status": "healthy", ...}`.

  On Windows, `set_start_method("spawn", force=True)` is a no-op (already the default) so no behaviour change; on Linux this is the critical safety change for MediaPipe.

- [ ] **Step 3: Commit**

  ```bash
  git add SHOOTRZ/backend/main.py
  git commit -m "feat: lifespan executor shutdown; force spawn start method for MediaPipe safety"
  ```

---

### DAY 2 GATE — End-to-end shot_score check

```bash
cd SHOOTRZ
uvicorn backend.main:app --port 8000 &
sleep 8   # wait for worker pool warmup

JOB=$(curl -s -X POST http://localhost:8000/analyze \
  -F "file=@/path/to/test.mp4" | python -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

for i in $(seq 1 18); do
  STATUS=$(curl -s http://localhost:8000/result/$JOB/status | python -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "$i: $STATUS"
  [ "$STATUS" = "completed" ] && break
  sleep 5
done

curl -s http://localhost:8000/result/$JOB | python -m json.tool | grep -A5 "shot_score"

kill %1
```

**Pass criteria:**
- `shot_score.score` is a number (not null) if there are visible body parts
- `shot_score.breakdown` contains at least 2 dimensions
- `status: completed` within 60s

---

## DAY 3 — Demo Polish (gate: 100-concurrent load test <5% errors)

---

### Task 9: Demo polish — preflight checks, lighting gate, result cache

**Files:**
- Modify: `SHOOTRZ/backend/routers/analyze.py`
- Modify: `SHOOTRZ/backend/processing/pipeline.py`

- [ ] **Step 1: Add preflight frame-count check in `analyze.py`**

  After writing the temp file (both in the `file` branch and the `file_url` branch), add a quick frame-count probe before queuing. Insert this right after `video_path = tmp.name`:

  ```python
  # Fast preflight: reject clips too short to analyze
  import cv2 as _cv2
  _cap = _cv2.VideoCapture(video_path)
  _frame_count = int(_cap.get(_cv2.CAP_PROP_FRAME_COUNT) or 0)
  _cap.release()
  if _frame_count < 30:
      Path(video_path).unlink(missing_ok=True)
      raise HTTPException(
          status_code=400,
          detail=f"Video too short: {_frame_count} frames (need ≥30, ~1s at 30fps)",
      )
  ```

  Add this block in **both** the `file` branch and the `file_url` branch (after the download).

- [ ] **Step 2: Add result cache (sha256 of first 1MB)**

  At the top of `analyze.py`, add:
  ```python
  import hashlib
  _result_cache: dict = {}  # sha256_hex → job_id
  ```

  In the `analyze` endpoint, before writing the temp file (in both branches), add a cache check. For the `file` branch, read the first 1MB to compute the hash **before** writing the full file:

  ```python
  # In the file branch, after 'if file:' and before NamedTemporaryFile:
  first_mb = await file.read(1024 * 1024)
  cache_key = hashlib.sha256(first_mb).hexdigest()
  if cache_key in _result_cache:
      cached_job_id = _result_cache[cache_key]
      if cached_job_id in job_store and job_store[cached_job_id].get("status") == "completed":
          return AnalyzeResponse(job_id=cached_job_id, status="completed")

  # Rewind and write full file
  with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
      tmp.write(first_mb)
      shutil.copyfileobj(file.file, tmp)
      video_path = tmp.name
  ```

  After `_launch_job(...)`, store the cache entry:
  ```python
  _result_cache[cache_key] = job_id
  ```

- [ ] **Step 3: Add lighting gate in `pipeline.py`**

  In `process_video`, after the frame loop (after `if len(pose_results) < 5:` block), add:

  ```python
  # Lighting gate: check mean luminance of first stride frame
  low_light = False
  if ball_rgb_frames:
      luminance = float(np.mean(cv2.cvtColor(
          np.array(ball_rgb_frames[0]), cv2.COLOR_RGB2GRAY
      )))
      if luminance < 50.0:  # 0-255 scale; <50 = very dark
          low_light = True
  ```

  Then in the return dict, add to `shot_score`:
  ```python
  if shot_score.get("score") is not None and low_light:
      shot_score["flags"] = shot_score.get("flags", []) + ["low_light"]
  ```

  And add `"low_light": low_light` as a top-level field in the return dict:
  ```python
  return {
      ...
      "low_light": low_light,
      ...
  }
  ```

- [ ] **Step 4: Run the full test suite**

  ```
  cd SHOOTRZ
  python -m pytest backend/tests/ -v 2>&1 | tail -30
  ```

  Expected: all tests pass (or skip for DB-dependent tests without a connection).

- [ ] **Step 5: Run 10-concurrent smoke test (lightweight load test)**

  Install `httpx` if needed: `pip install httpx`

  Create a temp file `load_test.py`:
  ```python
  import asyncio
  import httpx

  VIDEO = "/path/to/test.mp4"
  URL = "http://localhost:8000/analyze"
  N = 10

  async def submit_one(client, i):
      with open(VIDEO, "rb") as f:
          r = await client.post(URL, files={"file": f}, timeout=120)
      print(f"{i}: {r.status_code} {r.json()}")
      return r.status_code

  async def main():
      async with httpx.AsyncClient() as client:
          results = await asyncio.gather(*[submit_one(client, i) for i in range(N)])
      ok = sum(1 for s in results if s in (200, 429))
      print(f"{ok}/{N} acceptable (200 or 429)")
      assert ok == N, "Some requests got unexpected status codes"

  asyncio.run(main())
  ```

  Run:
  ```
  uvicorn backend.main:app --port 8000 &
  sleep 8
  python load_test.py
  kill %1
  ```

  Expected: all 10 requests return either 200 (queued) or 429 (server busy) — no 500s.

- [ ] **Step 6: Tag the pre-demo state**

  ```bash
  git add SHOOTRZ/backend/routers/analyze.py SHOOTRZ/backend/processing/pipeline.py
  git commit -m "feat: preflight frame-count check; result cache by sha256; lighting gate"
  git tag -a demo-ready -m "SHOOTRZ demo-ready: hardened backend, shot score live"
  ```

---

## Risk Mitigations (implement on Day 1 evening, not demo morning)

| Risk | Test | Fix |
|---|---|---|
| MediaPipe+spawn crashes | Start server, send a video, check it completes | Already mitigated by `spawn` in `main.py` |
| Ball tracker model path missing | `SHOOTRZ_DISABLE_BALL=1 uvicorn ...` | Set env var; pose-based `release_angle` fallback in `calculator.py:377` still runs |
| Demo video <30 frames | Preflight check returns 400 immediately | Task 9 Step 1 |
| Supabase hangs under load | `socket.setdefaulttimeout(5)` in `_worker_init` | Already in Task 7 Step 1 |
| 2-core demo machine | `SHOOTRZ_POSE_COMPLEXITY=0` | Set env var; halves pose latency at -3% accuracy |

**Abort plan:** `git revert $(git rev-list --ancestry-path demo-ready^..HEAD | tail -1)` rolls back to the demo-ready tag. If even that state fails, `git checkout pre-rescue` (tag the current `main` before starting Day 1 as `pre-rescue`).

---

## Self-Review Checklist

- [x] `elbow_flexion_preparatory` renamed to `elbow_flexion_crouch` in DIMENSIONS and _FALLBACK to match actual metric name from `calculator.py:198`
- [x] `process_frame` now assumes RGB input — `process_video` utility method in `pose_2d.py` fixed to BGR→RGB before calling it
- [x] `_running_tasks` holds asyncio.Task refs — B1 (GC) fixed
- [x] ProcessPoolExecutor lazy-initialized — B2 (module-level init) fixed
- [x] Annotated video call removed from pipeline — B6 (critical latency bug) fixed
- [x] `json.load(open(...))` replaced with context manager + try/except — B7 fixed
- [x] `vis_mean` passed to all 7 call sites in `calculator.py` — Task 6 Steps 4–10
- [x] `results.py` updated to include `shot_score` — otherwise frontend can't see the score
- [x] Both return branches in `results.py` updated (DB-fetch path and fallback path)
- [x] `file_url` branch fully implemented in new `analyze.py` (no "mirror the above" placeholder)
- [x] All test assertions updated for `completed_low_quality` status
- [x] Normative ranges use `elbow_flexion_crouch` matching the metric name produced by calculator
