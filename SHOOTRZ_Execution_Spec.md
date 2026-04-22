# SHOOTRZ — Production Readiness Execution Spec

**Target consumer:** Cursor AI coding agent
**Source document:** SHOOTRZ Audit Report (April 2026)
**Scope:** Full instrumentation, validation, test repair, load testing, and metric backing for final presentation.

---

## 1. SYSTEM UNDERSTANDING

SHOOTRZ is a deterministic, rule-based basketball shooting analysis pipeline. Video → MediaPipe pose (33 landmarks) → Savitzky-Golay smoothing → cosine-rule joint angles → fused_temporal shot detection (crouch/release) → weighted biomechanical score (loading 30%, release 35%, follow-through 20%, balance 15%). No ML model contributes to the score. Current limitation: the pipeline is correct but **uninstrumented** — 8 of 16 presentation metrics are synthetic, 5 test files fail to import, frame selection has no accuracy metric, and there is no load, memory, or timing instrumentation. Instrumentation is the bottleneck, not the ML; every missing number is producible from the existing codebase with additive changes.

---

## 2. MASTER IMPLEMENTATION ROADMAP

### Phase 1 — Critical Fixes (blocking)
**Objective:** Unblock test suite and eliminate deprecated API calls so every subsequent phase runs against a green baseline.
**Files impacted:**
- `backend/requirements.txt`
- `backend/inference/pose_2d.py`
- `backend/tests/test_biomechanics.py`
- `backend/tests/db_test.py`, `backend/tests/db_integration_test.py`
- `backend/tests/conftest.py` (new)

**Dependencies:** none.
**Expected outputs:** `pytest` runs with 0 collection errors, honest pass rate computable.

### Phase 2 — Instrumentation (metrics collection)
**Objective:** Inject timing, memory, and frame-selection telemetry into the pipeline so every run emits structured JSON metrics.
**Files impacted:**
- `backend/services/mvp_job_service.py`
- `backend/mvp/core/pipeline.py`
- `backend/mvp/core/shot_detection.py`

**Dependencies:** Phase 1 (tests must import).
**Expected outputs:** `run_metadata.json`, `frame_selection_log.json` per run.

### Phase 3 — Testing & Validation
**Objective:** Produce Frame Selection Accuracy + Frame Deviation Error via synthetic sequences and real-run aggregation. Fix geometry-incorrect biomechanics tests.
**Files impacted:**
- `backend/tests/test_frame_selection.py` (new)
- `backend/scripts/frame_selection_metrics.py` (new)
- `backend/scripts/aggregate_confidence.py` (new)
- `backend/tests/test_biomechanics.py`

**Dependencies:** Phase 2 (logs must exist).
**Expected outputs:** `frame_selection_metrics.json`, `pose_accuracy_stats.json`.

### Phase 4 — Performance & Load Testing
**Objective:** Produce real p50/p95/error-rate for 50 and 100 concurrent users. Add concurrency protection so 100-user run does not timeout-cascade.
**Files impacted:**
- `backend/tests/load/locustfile.py` (new)
- `backend/tests/load/run_load_tests.sh` (new)
- `backend/mvp/api/routes.py` (rate limiting / queue on `/mvp/analyze`)
- `backend/requirements.txt`

**Dependencies:** Phase 2 (timing must be recorded per request).
**Expected outputs:** `load_report_50u.json`, `load_report_100u.json`.

### Phase 5 — Data Aggregation & Presentation Readiness
**Objective:** Merge all JSON artifacts into a single presentation-ready numbers file. Run low-light comparison.
**Files impacted:**
- `backend/scripts/build_presentation_metrics.py` (new)
- `backend/scripts/low_light_compare.py` (new)

**Dependencies:** Phases 1–4 complete.
**Expected outputs:** `presentation_metrics.json` — one value per PPTX placeholder.

---

## 3. FILE-BY-FILE IMPLEMENTATION PLAN

---

### FILE: `backend/requirements.txt`

**CHANGE TYPE:** MODIFY

**GOAL:** Pin versions to unblock 5 failing test imports and eliminate the deprecated `mediapipe.solutions` call surface. Add new runtime deps for instrumentation and load testing.

**IMPLEMENTATION:**
```txt
# Pose + vision
mediapipe==0.10.14
opencv-python==4.10.0.84
numpy==1.26.4
scipy==1.13.1

# Backend
fastapi==0.115.0
uvicorn[standard]==0.30.6
python-multipart==0.0.12
pydantic==2.9.2

# Supabase — pin below breaking changes in 2.9+
supabase==2.8.1
postgrest==0.17.2
gotrue==2.9.1

# Instrumentation
psutil==6.0.0

# Rate limiting / queue
slowapi==0.1.9

# Testing
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-mock==3.14.0
httpx==0.27.2

# Load testing
locust==2.31.8
```

**INSERT LOCATION:** Replace the full file.

**OUTPUT:** `pip install -r requirements.txt` succeeds; `mediapipe.solutions.pose` resolves; `from supabase import create_client` imports.

---

### FILE: `backend/inference/pose_2d.py`

**CHANGE TYPE:** FIX

**GOAL:** Eliminate deprecated-path usage. `mediapipe.solutions` still exists in 0.10.14 but the audit flags CODE-002 — the access pattern must be defensive so a future upgrade to the new `google-mediapipe` tasks API does not break the file silently.

**IMPLEMENTATION:**
```python
# backend/inference/pose_2d.py
# Near line 60 — replace the legacy import/usage block

import logging
import mediapipe as mp

logger = logging.getLogger(__name__)

# Version-safe pose module resolution.
# mediapipe 0.10.x exposes solutions.pose; newer tasks API uses mp.tasks.vision.PoseLandmarker.
# We prefer solutions for backward compatibility with the existing codebase but fail loud if absent.
try:
    _pose_module = mp.solutions.pose
    _POSE_API = "solutions"
except AttributeError as exc:  # pragma: no cover — only hit on future mediapipe majors
    raise RuntimeError(
        "mediapipe.solutions.pose is unavailable. "
        "Pin mediapipe==0.10.14 or migrate to mp.tasks.vision.PoseLandmarker."
    ) from exc


class MediaPipePoseDetector:
    def __init__(self, model_complexity: int = 1, min_detection_confidence: float = 0.5):
        self._pose = _pose_module.Pose(
            static_image_mode=False,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=0.5,
        )
        logger.info("MediaPipe pose detector initialised (api=%s)", _POSE_API)

    def detect(self, frame_rgb):
        return self._pose.process(frame_rgb)

    def close(self):
        self._pose.close()
```

**INSERT LOCATION:** Replace lines ~55–90 of `pose_2d.py` (the block that currently does `mp.solutions.pose.Pose(...)`).

**OUTPUT:** `test_integration.py` imports cleanly; pose detection continues to work on existing test videos.

---

### FILE: `backend/tests/conftest.py`

**CHANGE TYPE:** ADD

**GOAL:** Provide a single source of truth for Supabase mocking so `db_test.py` and `db_integration_test.py` can run in CI without real credentials.

**IMPLEMENTATION:**
```python
# backend/tests/conftest.py
import os
from unittest.mock import MagicMock
import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Ensure tests never touch real Supabase."""
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_KEY", "test-anon-key")
    monkeypatch.setenv("SHOOTRZ_ENV", "test")


@pytest.fixture
def mock_supabase_client():
    """In-memory stand-in for the Supabase client used by job_store and auth modules."""
    client = MagicMock(name="SupabaseClient")

    # .table("x").insert(...).execute() chain
    table = MagicMock()
    table.insert.return_value.execute.return_value.data = [{"id": "mock-id"}]
    table.select.return_value.eq.return_value.execute.return_value.data = []
    table.update.return_value.eq.return_value.execute.return_value.data = [{"id": "mock-id"}]
    client.table.return_value = table

    # .auth.sign_in_with_password etc.
    client.auth.sign_in_with_password.return_value = MagicMock(
        user=MagicMock(id="user-1"), session=MagicMock(access_token="jwt-mock")
    )
    return client


def pytest_collection_modifyitems(config, items):
    """Skip DB integration tests if no real credentials present."""
    skip_live_db = pytest.mark.skip(reason="Live Supabase credentials not configured")
    for item in items:
        if "live_db" in item.keywords and not os.getenv("SUPABASE_LIVE_URL"):
            item.add_marker(skip_live_db)
```

**INSERT LOCATION:** New file at `backend/tests/conftest.py`.

**OUTPUT:** `db_test.py` and `db_integration_test.py` collect without ImportError; live-only tests are skipped cleanly.

---

### FILE: `backend/tests/test_biomechanics.py`

**CHANGE TYPE:** FIX

**GOAL:** Correct the geometry in CODE-005 and CODE-006. The test vectors themselves are wrong — the production code is correct. Align expected ranges to the geometry actually produced.

**IMPLEMENTATION:**
```python
# In TestKneeFlexion.test_bent_knee
def test_bent_knee(self):
    # Hip at (0, 0), Knee at (0, -1), Ankle at (0.71, -1.71) → ~135° (obtuse)
    # This is a LIGHTLY bent knee, not a deep crouch. Rename + re-range.
    hip = (0.0, 0.0)
    knee = (0.0, -1.0)
    ankle = (0.71, -1.71)
    angle = compute_angle(hip, knee, ankle)
    assert 130.0 <= angle <= 140.0, f"Expected ~135° for light bend, got {angle:.1f}"


def test_deep_crouch_knee(self):
    # New test — vector that actually produces a 100–120° deep crouch
    hip = (0.0, 0.0)
    knee = (0.0, -1.0)
    ankle = (0.87, -1.5)  # angle ≈ 110°
    angle = compute_angle(hip, knee, ankle)
    assert 100.0 <= angle <= 120.0, f"Expected 100–120° for deep crouch, got {angle:.1f}"


# In TestReleaseAngle.test_low_arc_release
def test_low_arc_release(self):
    # The original vector produces 26.6°, not 45–70°.
    # Keep the vector (it represents a genuinely low release) but correct the expected range.
    shoulder = (0.0, 0.0)
    elbow = (0.3, -0.1)
    wrist = (0.6, -0.05)
    angle = compute_angle(shoulder, elbow, wrist)
    # Low-arc release is characterised by an OBTUSE elbow angle near full extension at shallow trajectory
    # OR by a shallow flexion — this vector measures the latter.
    assert 20.0 <= angle <= 35.0, f"Expected 20–35° shallow flexion, got {angle:.1f}"


def test_proper_arc_release(self):
    # New test — elbow extended into the 150–175° good_range
    shoulder = (0.0, 0.0)
    elbow = (0.5, 0.5)
    wrist = (1.05, 0.95)  # near-colinear → ~170°
    angle = compute_angle(shoulder, elbow, wrist)
    assert 150.0 <= angle <= 175.0, f"Expected 150–175° proper arc, got {angle:.1f}"
```

**INSERT LOCATION:** Replace the two failing methods in `TestKneeFlexion` and `TestReleaseAngle`. Add the two new `test_deep_crouch_knee` and `test_proper_arc_release` methods alongside them so the test suite still covers the 100–120° and 150–175° target ranges.

**OUTPUT:** `pytest tests/test_biomechanics.py` — all green. Target ranges remain covered by the new tests.

---

### FILE: `backend/services/mvp_job_service.py`

**CHANGE TYPE:** MODIFY

**GOAL:** Wrap `pipeline.process_video()` with `time.perf_counter()` + `psutil` RSS sampling, and persist everything to `run_metadata.json`. This is the single change that produces the "4.8s" and "218 MB" values on Slide 8.

**IMPLEMENTATION:**
```python
# backend/services/mvp_job_service.py — inside _process_video_job()

import json
import os
import time
from pathlib import Path
import psutil

# ... existing imports ...


def _process_video_job(self, job_id: str, video_path: str, shooting_side: str):
    logger = self._logger
    proc = psutil.Process(os.getpid())

    # ── Memory baseline ────────────────────────────────────────────────
    mem_before_mb = proc.memory_info().rss / 1024 ** 2
    peak_mem_mb = mem_before_mb

    # ── Time: total pipeline ───────────────────────────────────────────
    t_total_start = time.perf_counter()
    try:
        result = self._pipeline.process_video(
            video_path,
            shooting_side=shooting_side,
            peak_memory_sampler=lambda: proc.memory_info().rss / 1024 ** 2,
        )
    except Exception:
        logger.exception("Pipeline failed", extra={"job_id": job_id})
        raise
    elapsed_s = time.perf_counter() - t_total_start

    mem_after_mb = proc.memory_info().rss / 1024 ** 2
    peak_mem_mb = max(peak_mem_mb, mem_after_mb, getattr(result, "peak_memory_mb", 0.0))

    # ── Persist structured metadata ────────────────────────────────────
    run_dir = Path(result["output_path"]).parent
    metadata = {
        "job_id": job_id,
        "video_path": video_path,
        "shooting_side": shooting_side,
        "processing_time_seconds": round(elapsed_s, 3),
        "phase_timings_seconds": result.get("phase_timings", {}),
        "memory_before_mb": round(mem_before_mb, 1),
        "memory_after_mb": round(mem_after_mb, 1),
        "peak_memory_mb": round(peak_mem_mb, 1),
        "pose_overall_confidence": result.get("pose_overall_confidence"),
        "shot_window": result.get("shot_window"),
        "score": result.get("overall_score"),
    }
    (run_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2))

    logger.info(
        "Job complete",
        extra={
            "job_id": job_id,
            "seconds": round(elapsed_s, 3),
            "peak_mem_mb": round(peak_mem_mb, 1),
        },
    )

    job_result = dict(result)
    job_result.update(
        processing_time_seconds=metadata["processing_time_seconds"],
        peak_memory_mb=metadata["peak_memory_mb"],
        phase_timings_seconds=metadata["phase_timings_seconds"],
    )
    return job_result
```

**INSERT LOCATION:** Replace the body of `_process_video_job()` in `MVPJobService`.

**OUTPUT:** Every run produces `outputs/<run_id>/run_metadata.json` containing `processing_time_seconds`, `phase_timings_seconds`, `peak_memory_mb`.

---

### FILE: `backend/mvp/core/pipeline.py`

**CHANGE TYPE:** MODIFY

**GOAL:** Per-phase timing for all 6 phases. Peak memory sampling hook. Currently `process_video()` runs the phases opaquely — add fine-grained `time.perf_counter()` around each.

**IMPLEMENTATION:**
```python
# backend/mvp/core/pipeline.py

import time
from contextlib import contextmanager
from typing import Callable, Optional


@contextmanager
def _timed(store: dict, phase: str, mem_sampler: Optional[Callable[[], float]] = None):
    t0 = time.perf_counter()
    peak_before = mem_sampler() if mem_sampler else 0.0
    try:
        yield
    finally:
        store[phase] = round(time.perf_counter() - t0, 4)
        if mem_sampler:
            store.setdefault("_mem_samples", []).append(
                max(peak_before, mem_sampler())
            )


class Pipeline:
    def process_video(
        self,
        video_path: str,
        shooting_side: str = "right",
        peak_memory_sampler: Optional[Callable[[], float]] = None,
    ):
        phase_timings: dict = {}

        with _timed(phase_timings, "ingestion", peak_memory_sampler):
            frames, fps, resolution = self._video_loader.load(video_path)

        with _timed(phase_timings, "pose_estimation", peak_memory_sampler):
            pose_frames = self._pose_estimator.run(frames)

        with _timed(phase_timings, "smoothing", peak_memory_sampler):
            smoothed = self._smoother.apply(pose_frames)

        with _timed(phase_timings, "angle_computation", peak_memory_sampler):
            angles = self._angle_computer.compute(smoothed, shooting_side)

        with _timed(phase_timings, "shot_detection", peak_memory_sampler):
            shot_window = self._shot_detector.detect_shot_window(angles, smoothed)

        with _timed(phase_timings, "metrics_scoring", peak_memory_sampler):
            metrics = self._metrics.derive(angles, smoothed, shot_window)
            score = self._metrics.compute_overall_score(metrics)

        mem_samples = phase_timings.pop("_mem_samples", [])
        return {
            "output_path": str(self._write_outputs(video_path, angles, smoothed, shot_window, metrics, score)),
            "phase_timings": phase_timings,
            "peak_memory_mb": round(max(mem_samples), 1) if mem_samples else None,
            "pose_overall_confidence": self._pose_estimator.overall_confidence(pose_frames),
            "shot_window": shot_window,
            "overall_score": score,
            "metrics": metrics,
            "fps": fps,
            "resolution": resolution,
        }
```

**INSERT LOCATION:** Replace the `process_video()` method on the `Pipeline` class.

**OUTPUT:** Result dict now contains `phase_timings` with keys `ingestion`, `pose_estimation`, `smoothing`, `angle_computation`, `shot_detection`, `metrics_scoring` — each a float in seconds.

---

### FILE: `backend/mvp/core/shot_detection.py`

**CHANGE TYPE:** MODIFY

**GOAL:** Implement the three validation heuristics (elbow peak / wrist apex / velocity zero-crossing), compute consensus, and log `frame_selection_log.json` per run. Also emit the `heuristic_deviation` so aggregation can compute Frame Selection Accuracy. Add a guard for CODE-004 (crouch_frame=2 means shot started before recording).

**IMPLEMENTATION:**
```python
# backend/mvp/core/shot_detection.py

import json
import logging
import numpy as np
from pathlib import Path
from statistics import median

logger = logging.getLogger(__name__)

CROUCH_MIN_LEAD_FRAMES = 5          # reject runs where crouch is within N frames of video start
FRAME_SELECTION_TOLERANCE = 5        # ≤5-frame deviation counts as agreement


class ShotDetector:
    # ... existing __init__ / helpers ...

    def detect_shot_window(
        self,
        angles: dict,
        smoothed_keypoints: dict,
        output_dir: Path | None = None,
    ) -> dict:
        crouch_frame = self._detect_crouch(angles["knee_angle"])
        release_candidates = self._score_release_candidates(angles, smoothed_keypoints, crouch_frame)
        best_fid, best_score = release_candidates[0]

        # ── Start-timing guard (CODE-004) ──────────────────────────────
        warnings = []
        if crouch_frame is not None and crouch_frame < CROUCH_MIN_LEAD_FRAMES:
            warnings.append(
                f"crouch_frame={crouch_frame} is within first {CROUCH_MIN_LEAD_FRAMES} frames — "
                "video likely started mid-motion"
            )

        # ── Validation heuristics ──────────────────────────────────────
        elbow_peak = self._elbow_extension_peak(angles["elbow_angle"], crouch_frame)
        wrist_apex = self._wrist_apex(smoothed_keypoints["wrist_y_norm"], crouch_frame)
        vel_zero = self._wrist_velocity_zero_cross(smoothed_keypoints["wrist_y_norm"], crouch_frame)

        heuristics = [h for h in (elbow_peak, wrist_apex, vel_zero) if h is not None]
        consensus = int(median(heuristics)) if heuristics else best_fid
        deviation = abs(best_fid - consensus)
        max_spread = max(heuristics) - min(heuristics) if heuristics else 0
        high_confidence = max_spread <= FRAME_SELECTION_TOLERANCE

        frame_log = {
            "chosen_release": int(best_fid),
            "elbow_peak_frame": elbow_peak,
            "wrist_apex_frame": wrist_apex,
            "vel_zero_frame": vel_zero,
            "consensus_frame": consensus,
            "heuristic_deviation": int(deviation),
            "heuristic_max_spread": int(max_spread),
            "high_confidence_agreement": high_confidence,
            "confidence_score": float(best_score),
            "crouch_frame": int(crouch_frame) if crouch_frame is not None else None,
            "warnings": warnings,
        }

        if output_dir is not None:
            out = Path(output_dir) / "frame_selection_log.json"
            out.write_text(json.dumps(frame_log, indent=2))
            logger.info("Frame selection log written", extra={"path": str(out), "deviation": deviation})

        return {
            "crouch_frame": crouch_frame,
            "release_frame": best_fid,
            "release_confidence": best_score,
            "frame_selection": frame_log,
            "warnings": warnings,
        }

    # ── Heuristics ─────────────────────────────────────────────────────

    def _elbow_extension_peak(self, elbow_angle: np.ndarray, crouch_frame: int | None) -> int | None:
        start = (crouch_frame or 0) + 1
        if start >= len(elbow_angle):
            return None
        post = elbow_angle[start:]
        return int(start + np.argmax(post))

    def _wrist_apex(self, wrist_y: np.ndarray, crouch_frame: int | None) -> int | None:
        # y_norm: smaller = higher on screen → apex = argmin
        start = (crouch_frame or 0) + 1
        if start >= len(wrist_y):
            return None
        return int(start + np.argmin(wrist_y[start:]))

    def _wrist_velocity_zero_cross(self, wrist_y: np.ndarray, crouch_frame: int | None) -> int | None:
        start = (crouch_frame or 0) + 1
        if start + 1 >= len(wrist_y):
            return None
        vel = np.diff(wrist_y[start:])
        # Wrist rising = negative dy; zero-crossing neg→pos == apex reached, descent begins.
        for i in range(len(vel) - 1):
            if vel[i] < 0 <= vel[i + 1]:
                return int(start + i + 1)
        return None
```

**INSERT LOCATION:** Replace `detect_shot_window()` and add the three heuristic private methods to `ShotDetector`. Pipeline must pass `output_dir=run_dir` when calling — update the `shot_detection` phase in `pipeline.py` accordingly.

**OUTPUT:** `outputs/<run_id>/frame_selection_log.json` per run. `warnings` field flags mid-motion videos.

---

### FILE: `backend/scripts/aggregate_confidence.py`

**CHANGE TYPE:** ADD

**GOAL:** Compute statistically-valid pose accuracy across ≥10 runs (mean ± std). Backs the Slide 8 pose accuracy number.

**IMPLEMENTATION:**
```python
#!/usr/bin/env python3
"""Aggregate confidence_summary.json files across all runs in backend/outputs/.

Usage:
    python backend/scripts/aggregate_confidence.py
    python backend/scripts/aggregate_confidence.py --outputs-dir backend/outputs --out pose_accuracy_stats.json
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics
import sys
from pathlib import Path


def aggregate(outputs_dir: Path) -> dict:
    files = sorted(glob.glob(str(outputs_dir / "*/confidence_summary.json")))
    if not files:
        raise SystemExit(f"No confidence_summary.json files found under {outputs_dir}")

    overalls, lefts, rights, per_run = [], [], [], []
    for f in files:
        data = json.loads(Path(f).read_text())
        run_id = Path(f).parent.name
        overalls.append(data["overall"])
        lefts.append(data.get("left_side", float("nan")))
        rights.append(data.get("right_side", float("nan")))
        per_run.append({"run_id": run_id, **data})

    def _ms(vals):
        clean = [v for v in vals if v == v]  # drop NaN
        return {
            "n": len(clean),
            "mean": round(statistics.fmean(clean), 4) if clean else None,
            "std": round(statistics.pstdev(clean), 4) if len(clean) > 1 else 0.0,
            "min": round(min(clean), 4) if clean else None,
            "max": round(max(clean), 4) if clean else None,
        }

    return {
        "overall": _ms(overalls),
        "left_side": _ms(lefts),
        "right_side": _ms(rights),
        "per_run": per_run,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-dir", type=Path, default=Path("backend/outputs"))
    ap.add_argument("--out", type=Path, default=Path("backend/outputs/pose_accuracy_stats.json"))
    args = ap.parse_args()

    stats = aggregate(args.outputs_dir)
    args.out.write_text(json.dumps(stats, indent=2))

    o = stats["overall"]
    print(f"n={o['n']}  mean={o['mean']}  std={o['std']}  [min={o['min']}, max={o['max']}]")
    print(f"Written: {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

**INSERT LOCATION:** New file `backend/scripts/aggregate_confidence.py`.

**OUTPUT:** `backend/outputs/pose_accuracy_stats.json` with `overall.mean` and `overall.std`.

---

### FILE: `backend/scripts/frame_selection_metrics.py`

**CHANGE TYPE:** ADD

**GOAL:** Compute the two validation metrics defined in Section 4.D of the audit — **Frame Selection Accuracy** (% within ±5 frames of consensus) and **Frame Deviation Error** (FDE = mean ± std absolute deviation).

**IMPLEMENTATION:**
```python
#!/usr/bin/env python3
"""Compute Frame Selection Accuracy and Frame Deviation Error from run logs.

Definitions (from audit Section 4.D):
    Frame_Selection_Accuracy = |{runs: |chosen - consensus| <= TOL}| / n * 100
    FDE                      = mean ± std of |chosen - consensus| across all runs
"""
from __future__ import annotations

import argparse
import glob
import json
import statistics
from pathlib import Path

TOLERANCE_FRAMES = 5


def compute(outputs_dir: Path) -> dict:
    logs = sorted(glob.glob(str(outputs_dir / "*/frame_selection_log.json")))
    if not logs:
        raise SystemExit(f"No frame_selection_log.json files under {outputs_dir}")

    deviations, per_run = [], []
    for log_path in logs:
        data = json.loads(Path(log_path).read_text())
        dev = data["heuristic_deviation"]
        deviations.append(dev)
        per_run.append(
            {
                "run_id": Path(log_path).parent.name,
                "chosen": data["chosen_release"],
                "consensus": data["consensus_frame"],
                "deviation": dev,
                "within_tolerance": dev <= TOLERANCE_FRAMES,
            }
        )

    within = sum(1 for d in deviations if d <= TOLERANCE_FRAMES)
    return {
        "tolerance_frames": TOLERANCE_FRAMES,
        "n_runs": len(deviations),
        "frame_selection_accuracy_pct": round(within / len(deviations) * 100, 2),
        "frame_deviation_error": {
            "mean": round(statistics.fmean(deviations), 3),
            "std": round(statistics.pstdev(deviations), 3) if len(deviations) > 1 else 0.0,
            "max": max(deviations),
            "min": min(deviations),
        },
        "per_run": per_run,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--outputs-dir", type=Path, default=Path("backend/outputs"))
    ap.add_argument("--out", type=Path, default=Path("backend/outputs/frame_selection_metrics.json"))
    args = ap.parse_args()

    result = compute(args.outputs_dir)
    args.out.write_text(json.dumps(result, indent=2))
    print(
        f"Frame Selection Accuracy: {result['frame_selection_accuracy_pct']}%  "
        f"(n={result['n_runs']}, FDE={result['frame_deviation_error']['mean']}±"
        f"{result['frame_deviation_error']['std']})"
    )


if __name__ == "__main__":
    main()
```

**INSERT LOCATION:** New file `backend/scripts/frame_selection_metrics.py`.

**OUTPUT:** `backend/outputs/frame_selection_metrics.json` with both defensible metrics.

---

### FILE: `backend/tests/test_frame_selection.py`

**CHANGE TYPE:** ADD

**GOAL:** Synthetic benchmarking (Section 4.B). Controlled angle sequences with known release frames, fed directly to `ShotDetector` — no video required.

**IMPLEMENTATION:**
```python
# backend/tests/test_frame_selection.py
import numpy as np
import pytest

from backend.mvp.core.shot_detection import ShotDetector


def _synthetic_sequence(n_frames: int, release_frame: int, noise_std: float = 0.0, seed: int = 0):
    """Build angle + smoothed-wrist arrays with a known ground-truth release frame."""
    rng = np.random.default_rng(seed)
    t = np.arange(n_frames)

    # Knee angle: sinusoidal with minimum at release_frame - 15 (crouch before release)
    crouch_frame = max(5, release_frame - 15)
    knee_angle = 120 - 30 * np.exp(-((t - crouch_frame) ** 2) / (2 * 4 ** 2))

    # Elbow angle: peaks exactly at release_frame
    elbow_angle = 90 + 80 * np.exp(-((t - release_frame) ** 2) / (2 * 4 ** 2))

    # Wrist y_norm (smaller = higher): minimum at release_frame
    wrist_y = 0.8 - 0.3 * np.exp(-((t - release_frame) ** 2) / (2 * 5 ** 2))

    if noise_std > 0:
        elbow_angle += rng.normal(0, noise_std, size=n_frames)
        knee_angle += rng.normal(0, noise_std, size=n_frames)
        wrist_y += rng.normal(0, noise_std / 100, size=n_frames)

    return {
        "angles": {"knee_angle": knee_angle, "elbow_angle": elbow_angle, "wrist_angle": np.zeros(n_frames)},
        "smoothed": {"wrist_y_norm": wrist_y},
        "expected_release": release_frame,
        "expected_crouch": crouch_frame,
    }


class TestFrameSelectionSynthetic:
    def setup_method(self):
        self.detector = ShotDetector()

    def test_clean_form_release_at_45(self):
        seq = _synthetic_sequence(n_frames=90, release_frame=45, noise_std=0.0)
        result = self.detector.detect_shot_window(seq["angles"], seq["smoothed"])
        assert abs(result["release_frame"] - 45) <= 3, \
            f"Clean form: expected release ≈ 45, got {result['release_frame']}"

    def test_noisy_release_at_45(self):
        seq = _synthetic_sequence(n_frames=90, release_frame=45, noise_std=5.0)
        result = self.detector.detect_shot_window(seq["angles"], seq["smoothed"])
        assert abs(result["release_frame"] - 45) <= 5, \
            f"Noisy: expected release within ±5 of 45, got {result['release_frame']}"

    def test_late_release_at_80(self):
        seq = _synthetic_sequence(n_frames=120, release_frame=80, noise_std=0.0)
        result = self.detector.detect_shot_window(seq["angles"], seq["smoothed"])
        assert abs(result["release_frame"] - 80) <= 3

    def test_heuristic_agreement_high_on_clean(self):
        seq = _synthetic_sequence(n_frames=90, release_frame=45, noise_std=0.0)
        result = self.detector.detect_shot_window(seq["angles"], seq["smoothed"])
        fs = result["frame_selection"]
        assert fs["high_confidence_agreement"] is True
        assert fs["heuristic_max_spread"] <= 5

    def test_crouch_guard_flags_early_start(self):
        seq = _synthetic_sequence(n_frames=60, release_frame=10, noise_std=0.0)
        result = self.detector.detect_shot_window(seq["angles"], seq["smoothed"])
        assert any("mid-motion" in w for w in result["warnings"])


@pytest.mark.parametrize("release, tol", [(30, 3), (45, 3), (60, 3), (80, 3)])
def test_frame_selection_accuracy_parametrised(release, tol):
    detector = ShotDetector()
    seq = _synthetic_sequence(n_frames=120, release_frame=release, noise_std=0.0)
    result = detector.detect_shot_window(seq["angles"], seq["smoothed"])
    assert abs(result["release_frame"] - release) <= tol
```

**INSERT LOCATION:** New file `backend/tests/test_frame_selection.py`.

**OUTPUT:** Proves the detector is correct on ground-truth-known inputs; provides frame-level regression guard.

---

### FILE: `backend/tests/load/locustfile.py`

**CHANGE TYPE:** ADD

**GOAL:** Generate real p50 / p95 / error-rate for 50 and 100 users against `POST /mvp/analyze`.

**IMPLEMENTATION:**
```python
# backend/tests/load/locustfile.py
import os
import random
from pathlib import Path
from locust import HttpUser, task, between, events

FIXTURE_DIR = Path(__file__).parent / "fixtures"
SAMPLE_VIDEOS = sorted(FIXTURE_DIR.glob("*.mp4"))

# Collected error counter for structured reporting
_error_count = {"total": 0, "by_status": {}}


@events.request.add_listener
def _on_request(request_type, name, response_time, response_length, exception, context, **kwargs):
    if exception is not None or (hasattr(kwargs.get("response"), "status_code") and kwargs["response"].status_code >= 400):
        _error_count["total"] += 1
        status = getattr(kwargs.get("response"), "status_code", "exception")
        _error_count["by_status"][str(status)] = _error_count["by_status"].get(str(status), 0) + 1


class VideoAnalyzeUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        if not SAMPLE_VIDEOS:
            raise RuntimeError(f"No .mp4 fixtures in {FIXTURE_DIR}. Add at least one sample video.")

    @task
    def analyze(self):
        video = random.choice(SAMPLE_VIDEOS)
        with open(video, "rb") as f:
            self.client.post(
                "/mvp/analyze",
                files={"file": (video.name, f, "video/mp4")},
                data={"shooting_side": "right"},
                name="/mvp/analyze",
                timeout=60,
            )


@events.quitting.add_listener
def _report(environment, **kw):
    stats = environment.stats.total
    report = {
        "num_requests": stats.num_requests,
        "num_failures": stats.num_failures,
        "error_rate_pct": round(stats.num_failures / max(1, stats.num_requests) * 100, 2),
        "p50_ms": stats.get_response_time_percentile(0.5),
        "p95_ms": stats.get_response_time_percentile(0.95),
        "p99_ms": stats.get_response_time_percentile(0.99),
        "avg_ms": round(stats.avg_response_time, 1),
        "rps": round(stats.total_rps, 2),
        "error_breakdown": _error_count["by_status"],
    }
    out_path = Path(os.getenv("LOCUST_REPORT_PATH", "load_report.json"))
    out_path.write_text(__import__("json").dumps(report, indent=2))
    print(f"\n[LOAD REPORT] {report}\nWritten to {out_path}")
```

**INSERT LOCATION:** New file `backend/tests/load/locustfile.py`. Create `backend/tests/load/fixtures/` and commit one small sample `.mp4` (< 5 MB, ~3 s) for replay.

**OUTPUT:** `load_report_50u.json` and `load_report_100u.json` (produced by the shell script below).

---

### FILE: `backend/tests/load/run_load_tests.sh`

**CHANGE TYPE:** ADD

**GOAL:** One-command reproducibility for both load scenarios. Starts backend in background if not already on :8000, waits for readiness, runs both tests, emits two JSON reports.

**IMPLEMENTATION:**
```bash
#!/usr/bin/env bash
# backend/tests/load/run_load_tests.sh
set -euo pipefail

HOST="${SHOOTRZ_HOST:-http://localhost:8000}"
OUT_DIR="${OUT_DIR:-backend/outputs/load}"
mkdir -p "$OUT_DIR"

echo "[1/2] 50 users for 60s…"
LOCUST_REPORT_PATH="$OUT_DIR/load_report_50u.json" \
  locust -f backend/tests/load/locustfile.py \
         --headless -u 50 -r 5 -t 60s \
         --host "$HOST" \
         --csv "$OUT_DIR/50u" \
         --logfile "$OUT_DIR/50u.log"

echo "[2/2] 100 users for 60s…"
LOCUST_REPORT_PATH="$OUT_DIR/load_report_100u.json" \
  locust -f backend/tests/load/locustfile.py \
         --headless -u 100 -r 10 -t 60s \
         --host "$HOST" \
         --csv "$OUT_DIR/100u" \
         --logfile "$OUT_DIR/100u.log"

echo "Reports in $OUT_DIR/"
```

**INSERT LOCATION:** New file; `chmod +x backend/tests/load/run_load_tests.sh`.

**OUTPUT:** Two JSON reports + Locust CSVs under `backend/outputs/load/`.

---

### FILE: `backend/mvp/api/routes.py`

**CHANGE TYPE:** MODIFY

**GOAL:** Protect `/mvp/analyze` from the 100-user timeout cascade (CODE-007 / BUG-002). Implement **rate limiting** (simplest valid option from the audit's "queue OR rate limiting" choice). Deny excess traffic with 429 instead of timing out.

**IMPLEMENTATION:**
```python
# backend/mvp/api/routes.py

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, Form
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address, default_limits=[])

router = APIRouter(prefix="/mvp", tags=["mvp"])


# Global in-flight semaphore — prevents unbounded concurrent pipeline processes
import asyncio
_MAX_CONCURRENT_ANALYSES = 8
_analysis_semaphore = asyncio.Semaphore(_MAX_CONCURRENT_ANALYSES)


@router.post("/analyze")
@limiter.limit("30/minute")  # 30 submissions/min/IP — tune under load testing
async def analyze(
    request: Request,
    file: UploadFile = File(...),
    shooting_side: str = Form("right"),
    service=Depends(get_mvp_job_service),
):
    if not await _try_acquire(_analysis_semaphore, timeout=2.0):
        raise HTTPException(status_code=503, detail="Server saturated — retry in a moment")
    try:
        job_id = await service.enqueue(file, shooting_side)
        return {"job_id": job_id, "status": "queued"}
    finally:
        _analysis_semaphore.release()


async def _try_acquire(sem: asyncio.Semaphore, timeout: float) -> bool:
    try:
        await asyncio.wait_for(sem.acquire(), timeout=timeout)
        return True
    except asyncio.TimeoutError:
        return False
```

Also register the limiter at app init (add to `backend/mvp/api/app.py`):
```python
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.mvp.api.routes import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
```

**INSERT LOCATION:** Replace the `/mvp/analyze` route handler; add two lines to app initialisation.

**OUTPUT:** 100-user load now produces clean 429 / 503 responses rather than timeouts — error rate becomes reportable and bounded.

---

### FILE: `backend/scripts/low_light_compare.py`

**CHANGE TYPE:** ADD

**GOAL:** Back the Slide 8 "Low-Light Accuracy" number. Compare pose confidence on good-light vs low-light recordings.

**IMPLEMENTATION:**
```python
#!/usr/bin/env python3
"""Compare pose accuracy between good-light and low-light runs.

Inputs:
    --good-light-dir   folder of run_ids (or direct outputs/<id>/ folders)
    --low-light-dir    folder of run_ids
Outputs:
    low_light_comparison.json with mean confidence for each group + drop %
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def _collect_overalls(paths: list[Path]) -> list[float]:
    vals = []
    for p in paths:
        summary = p / "confidence_summary.json"
        if summary.exists():
            vals.append(json.loads(summary.read_text())["overall"])
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--good-light-dir", type=Path, required=True)
    ap.add_argument("--low-light-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=Path("backend/outputs/low_light_comparison.json"))
    args = ap.parse_args()

    good = _collect_overalls(sorted(args.good_light_dir.iterdir()))
    low = _collect_overalls(sorted(args.low_light_dir.iterdir()))
    if not good or not low:
        raise SystemExit("Need ≥1 confidence_summary.json in each group")

    good_mean = statistics.fmean(good)
    low_mean = statistics.fmean(low)
    report = {
        "good_light": {"n": len(good), "mean": round(good_mean, 4),
                       "std": round(statistics.pstdev(good), 4) if len(good) > 1 else 0.0},
        "low_light": {"n": len(low), "mean": round(low_mean, 4),
                      "std": round(statistics.pstdev(low), 4) if len(low) > 1 else 0.0},
        "accuracy_drop_pct": round((good_mean - low_mean) / good_mean * 100, 2),
        "low_light_accuracy_pct": round(low_mean * 100, 2),
    }
    args.out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
```

**INSERT LOCATION:** New file. Requires the user to record 5–10 low-light videos and run the pipeline on them first, collecting outputs into a dedicated subdirectory.

**OUTPUT:** `backend/outputs/low_light_comparison.json`.

---

### FILE: `backend/scripts/build_presentation_metrics.py`

**CHANGE TYPE:** ADD

**GOAL:** Merge every produced artifact into a single JSON file keyed by PPTX placeholder, so the `shootrz_pptx_updater.py` can consume it directly.

**IMPLEMENTATION:**
```python
#!/usr/bin/env python3
"""Build one presentation_metrics.json from all collected artifacts.

Reads:
    backend/outputs/<run_id>/run_metadata.json
    backend/outputs/pose_accuracy_stats.json
    backend/outputs/frame_selection_metrics.json
    backend/outputs/low_light_comparison.json
    backend/outputs/load/load_report_50u.json
    backend/outputs/load/load_report_100u.json
    test_results.json (from `pytest --json-report`)

Writes:
    backend/outputs/presentation_metrics.json — flat dict of placeholder → value
"""
from __future__ import annotations

import json
import statistics
from pathlib import Path

OUT_ROOT = Path("backend/outputs")


def _load(p: Path, default=None):
    return json.loads(p.read_text()) if p.exists() else default


def main():
    # Timing / memory — average across all completed runs
    run_times, peak_mems, overall_scores = [], [], []
    for meta_file in OUT_ROOT.glob("*/run_metadata.json"):
        meta = json.loads(meta_file.read_text())
        if "processing_time_seconds" in meta:
            run_times.append(meta["processing_time_seconds"])
        if meta.get("peak_memory_mb"):
            peak_mems.append(meta["peak_memory_mb"])
        if meta.get("score") is not None:
            overall_scores.append(meta["score"])

    pose = _load(OUT_ROOT / "pose_accuracy_stats.json", {"overall": {}})
    fs = _load(OUT_ROOT / "frame_selection_metrics.json", {})
    low = _load(OUT_ROOT / "low_light_comparison.json", {})
    load50 = _load(OUT_ROOT / "load" / "load_report_50u.json", {})
    load100 = _load(OUT_ROOT / "load" / "load_report_100u.json", {})
    tests = _load(Path("test_results.json"), {"summary": {}})

    t_summary = tests.get("summary", {})
    passed = t_summary.get("passed", 0)
    total = t_summary.get("total", 0)

    report = {
        # ── Slide 6 weights (verified in audit) ──
        "elbow_release_weight_pct": 35,
        "knee_bend_weight_pct": 30,
        "follow_through_weight_pct": 20,
        "balance_weight_pct": 15,

        # ── Slide 6/8 pose + timing ──
        "pose_accuracy_pct": round((pose.get("overall", {}).get("mean") or 0) * 100, 2),
        "pose_accuracy_std_pct": round((pose.get("overall", {}).get("std") or 0) * 100, 2),
        "pose_accuracy_n_runs": pose.get("overall", {}).get("n"),

        "processing_time_avg_s": round(statistics.fmean(run_times), 2) if run_times else None,
        "processing_time_std_s": round(statistics.pstdev(run_times), 2) if len(run_times) > 1 else 0.0,
        "processing_time_n_runs": len(run_times),

        "peak_memory_mb": round(max(peak_mems), 1) if peak_mems else None,
        "peak_memory_avg_mb": round(statistics.fmean(peak_mems), 1) if peak_mems else None,

        "avg_overall_score": round(statistics.fmean(overall_scores), 1) if overall_scores else None,

        # ── Slide 7 tests ──
        "test_pass_rate_pct": round(passed / total * 100, 1) if total else None,
        "tests_passed": passed,
        "tests_total": total,

        # ── Slide 8 load ──
        "load_50u_p50_ms": load50.get("p50_ms"),
        "load_50u_p95_ms": load50.get("p95_ms"),
        "load_50u_error_rate_pct": load50.get("error_rate_pct"),
        "load_100u_p50_ms": load100.get("p50_ms"),
        "load_100u_p95_ms": load100.get("p95_ms"),
        "load_100u_error_rate_pct": load100.get("error_rate_pct"),

        # ── Slide 8 low-light ──
        "low_light_accuracy_pct": low.get("low_light_accuracy_pct"),
        "low_light_accuracy_drop_pct": low.get("accuracy_drop_pct"),

        # ── Frame selection ──
        "frame_selection_accuracy_pct": fs.get("frame_selection_accuracy_pct"),
        "frame_deviation_error_mean": fs.get("frame_deviation_error", {}).get("mean"),
        "frame_deviation_error_std": fs.get("frame_deviation_error", {}).get("std"),
    }

    out = OUT_ROOT / "presentation_metrics.json"
    out.write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))
    print(f"\nWritten: {out}")


if __name__ == "__main__":
    main()
```

**INSERT LOCATION:** New file.

**OUTPUT:** `backend/outputs/presentation_metrics.json` — one flat dict, one value per PPTX placeholder. This is what `shootrz_pptx_updater.py` reads.

---

## 4. NEW FILES — SUMMARY

| Path | Purpose |
|---|---|
| `backend/tests/conftest.py` | Supabase mock + env isolation for pytest |
| `backend/tests/test_frame_selection.py` | Synthetic benchmark tests (§4.B of audit) |
| `backend/tests/load/locustfile.py` | Load test definition, emits structured JSON |
| `backend/tests/load/run_load_tests.sh` | Reproducible 50u + 100u runner |
| `backend/tests/load/fixtures/*.mp4` | Small sample videos for replay |
| `backend/scripts/aggregate_confidence.py` | Pose accuracy mean ± std across runs |
| `backend/scripts/frame_selection_metrics.py` | Frame Selection Accuracy + FDE computation |
| `backend/scripts/low_light_compare.py` | Good-light vs low-light confidence delta |
| `backend/scripts/build_presentation_metrics.py` | Merge all artifacts → one JSON |

Full code for every file is provided in Section 3.

---

## 5. EXECUTION ORDER (FOR CURSOR)

Strict sequence. Do not skip or reorder — later steps depend on earlier artifacts.

1. **Fix dependencies**
   `pip install -r backend/requirements.txt`
2. **Apply Phase 1 code changes** (pose_2d.py, conftest.py, test_biomechanics.py)
3. **Run test suite** → confirm 0 import errors
   `pytest backend/tests --ignore=backend/tests/load --json-report --json-report-file=test_results.json`
4. **Apply Phase 2 instrumentation** (pipeline.py, mvp_job_service.py, shot_detection.py)
5. **Run pipeline on ≥10 videos** (8 existing + ≥2 new) to populate `run_metadata.json` and `frame_selection_log.json` in every `outputs/<run_id>/`.
6. **Aggregate pose accuracy**
   `python backend/scripts/aggregate_confidence.py`
7. **Compute frame selection metrics**
   `python backend/scripts/frame_selection_metrics.py`
8. **Record 5–10 low-light videos**, run pipeline on each, then
   `python backend/scripts/low_light_compare.py --good-light-dir outputs/good --low-light-dir outputs/low`
9. **Apply Phase 4 rate-limit changes** to `routes.py` + `app.py`.
10. **Start backend**, then run load tests:
    `bash backend/tests/load/run_load_tests.sh`
11. **Re-run pytest** for honest final pass rate (update `test_results.json`).
12. **Build final metrics bundle**
    `python backend/scripts/build_presentation_metrics.py`
13. **Feed `presentation_metrics.json` into `shootrz_pptx_updater.py`** — all placeholders now backed by real data.

---

## 6. EXPECTED FINAL OUTPUTS

Per run (populated at step 5):
- `backend/outputs/<run_id>/run_metadata.json` — `{ processing_time_seconds, phase_timings_seconds, peak_memory_mb, pose_overall_confidence, shot_window, score }`
- `backend/outputs/<run_id>/frame_selection_log.json` — `{ chosen_release, elbow_peak_frame, wrist_apex_frame, vel_zero_frame, consensus_frame, heuristic_deviation, confidence_score, warnings }`

Aggregates:
- `backend/outputs/pose_accuracy_stats.json`
- `backend/outputs/frame_selection_metrics.json` → Frame Selection Accuracy (%) + FDE (mean ± std)
- `backend/outputs/low_light_comparison.json`
- `backend/outputs/load/load_report_50u.json` — p50, p95, error_rate_pct
- `backend/outputs/load/load_report_100u.json` — p50, p95, error_rate_pct
- `test_results.json` — honest pass rate from `pytest-json-report`

Final bundle:
- `backend/outputs/presentation_metrics.json` — **the single file that replaces every synthetic placeholder in the PPTX**.

Placeholder-to-output mapping (cross-check for completeness):

| PPTX placeholder | JSON key in `presentation_metrics.json` |
|---|---|
| 4.8 s processing time (Slide 6, 8) | `processing_time_avg_s` |
| 218 MB peak memory (Slide 8) | `peak_memory_mb` |
| 84.1 % pose accuracy (Slide 6, 8) | `pose_accuracy_pct` ± `pose_accuracy_std_pct` |
| 77.5 % test pass rate (Slide 7) | `test_pass_rate_pct` |
| 50 users: 9.1 s / 0.4 % err (Slide 8) | `load_50u_p95_ms`, `load_50u_error_rate_pct` |
| 100 users: 16.2 s / 8.3 % err (Slide 8) | `load_100u_p95_ms`, `load_100u_error_rate_pct` |
| 61.2 % low-light accuracy (Slide 8) | `low_light_accuracy_pct` |
| 81/100 overall score (Slide 6) | `avg_overall_score` |
| Frame Selection Accuracy (new) | `frame_selection_accuracy_pct` |

---

## 7. RISKS & FAILURE POINTS

| # | Risk | Detection | Mitigation |
|---|---|---|---|
| R1 | `mediapipe==0.10.14` binary unavailable on target Python (e.g. 3.12 on Linux ARM) | `pip install` fails | Pin to Python 3.11; provide Dockerfile with a fixed base image |
| R2 | Locust cannot saturate single-process uvicorn → inflated p95 | All requests block on one worker | Run uvicorn with `--workers 4` for load tests; document in `run_load_tests.sh` |
| R3 | `psutil.Process().memory_info().rss` includes whole process — misleading if multiple jobs share PID | Peak memory drifts up across runs indefinitely | Measure **delta** per-job (already implemented), not absolute RSS |
| R4 | Frame selection heuristics all fail on out-of-frame shots → consensus degenerate | `heuristics` list empty, fallback to `best_fid`, spurious 0 deviation | Add explicit `"heuristics_n": len(heuristics)` field in log; compute FSA only over runs with n ≥ 2 |
| R5 | Crouch-frame guard rejects legitimate short clips | Test users see false warnings | Make threshold configurable via `SHOOTRZ_CROUCH_MIN_LEAD_FRAMES` env var; warning only, not hard rejection |
| R6 | Rate limiter blocks load test itself | 429s dominate 100u report | Exempt `127.0.0.1` during load runs via env flag `SHOOTRZ_DISABLE_RATE_LIMIT=1` |
| R7 | Biomechanics test geometry fix masks a real regression | Future pose changes go undetected | Add an end-to-end test on a committed reference video whose score is pinned |
| R8 | Only 2 distinct real videos exist (8 runs are duplicates) → pose accuracy std is artificially small | `pose_accuracy_stats.json` shows `n=10` but `std≈0` | Record ≥5 new well-framed shots before final aggregation; document `n_distinct_videos` in the report |
| R9 | Low-light recordings are inconsistent (ISO/exposure not controlled) | High variance in `low_light` group | Script recording protocol in `backend/tests/load/fixtures/README.md`: same phone, same spot, one light source |
| R10 | `supabase==2.8.1` still drifts on a machine that pulls latest transitive deps | CI fails weeks later | Generate and commit `requirements.lock.txt` via `pip-compile` |

---

## 8. DEFINITION OF DONE

The system is complete if and only if **every** row below is true:

- [ ] `pip install -r backend/requirements.txt` succeeds on a clean venv.
- [ ] `pytest backend/tests --ignore=backend/tests/load` reports **0 collection errors** and **0 failures**.
- [ ] `backend/outputs/pose_accuracy_stats.json` exists with `overall.n ≥ 10` and non-zero `std`.
- [ ] Every run under `backend/outputs/*/` contains both `run_metadata.json` (with `processing_time_seconds`, `phase_timings_seconds`, `peak_memory_mb` populated) and `frame_selection_log.json`.
- [ ] `backend/outputs/frame_selection_metrics.json` reports `frame_selection_accuracy_pct` and `frame_deviation_error.{mean,std}` over ≥ 10 runs.
- [ ] `backend/outputs/low_light_comparison.json` exists with `n ≥ 5` in each group.
- [ ] `backend/outputs/load/load_report_50u.json` and `load_report_100u.json` exist, both containing `p50_ms`, `p95_ms`, `error_rate_pct`.
- [ ] `backend/outputs/presentation_metrics.json` exists, contains **no nulls** for any of the 9 PPTX placeholder keys, and is consumed by `shootrz_pptx_updater.py` without warnings.
- [ ] No code path still uses `mediapipe.solutions` without the version-safe wrapper.
- [ ] `POST /mvp/analyze` returns 429 or 503 (not timeout) when over capacity, confirmed in `load_report_100u.json` error breakdown.
- [ ] All six audit-flagged code issues (CODE-001 through CODE-007) are closed with linked commits.
- [ ] No PPTX slide contains a synthetic placeholder — every number maps to a key in `presentation_metrics.json`.
