"""
Tests for multi-frame confidence calibration (Task 18).

calibrate_confidence_multiframe lives in pose_estimation.py which transitively
imports cv2 and mediapipe — neither is available in the lightweight test
environment.  We stub those modules in sys.modules BEFORE importing
pose_estimation so the pure-Python function can be reached without triggering
the heavy deps.
"""

import sys
import types
import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Stub out cv2 and mediapipe before importing pose_estimation
# ---------------------------------------------------------------------------

def _make_stub(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    # Some code does `from mediapipe import solutions` etc. — add a catch-all
    # __getattr__ so any attribute access returns another stub module.
    def _getattr(attr):
        sub = _make_stub(f"{name}.{attr}")
        setattr(mod, attr, sub)
        return sub
    mod.__getattr__ = _getattr
    return mod


for _stub_name in [
    "cv2",
    "mediapipe",
    "mediapipe.python",
    "mediapipe.python.solutions",
    "mediapipe.python.solutions.pose",
    "mediapipe.python.solutions.drawing_utils",
]:
    if _stub_name not in sys.modules:
        sys.modules[_stub_name] = _make_stub(_stub_name)

# ---------------------------------------------------------------------------
# Now we can safely import pose_estimation
# ---------------------------------------------------------------------------

import os
from pathlib import Path

_backend_root = Path(__file__).parent.parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from mvp.core.pose_estimation import calibrate_confidence_multiframe, MVPPoseEstimator


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_high_variance_joint_reduces_confidence():
    """A joint with high positional variance should have reduced confidence."""
    # x position varies by 0.0, 0.1, 0.2, 0.3, 0.4 — high variance
    frames = [
        {"right_elbow": {"x": i * 0.1, "y": 0.5, "conf": 0.9}}
        for i in range(5)
    ]
    calibrated = calibrate_confidence_multiframe(frames, joint="right_elbow", window=5)
    for f in calibrated:
        assert f["right_elbow"]["conf"] < 0.9, (
            f"High-variance joint must have lower confidence, got {f['right_elbow']['conf']}"
        )


def test_zero_variance_preserves_confidence():
    """A perfectly stable joint should have minimal confidence reduction."""
    # All frames identical position — std = 0
    frames = [
        {"right_elbow": {"x": 0.5, "y": 0.5, "conf": 0.9}}
        for _ in range(5)
    ]
    calibrated = calibrate_confidence_multiframe(frames, joint="right_elbow", window=5)
    for f in calibrated:
        # exp(-10 * 0) = 1.0, so conf should be unchanged
        assert abs(f["right_elbow"]["conf"] - 0.9) < 1e-6, (
            f"Zero-variance joint should keep confidence 0.9, got {f['right_elbow']['conf']}"
        )


def test_missing_joint_frame_returned_unchanged():
    """Frames without the target joint should pass through unmodified."""
    frames = [
        {"left_knee": {"x": 0.3, "y": 0.7, "conf": 0.8}},  # no right_elbow
        {"right_elbow": {"x": 0.5, "y": 0.5, "conf": 0.9}},
    ]
    calibrated = calibrate_confidence_multiframe(frames, joint="right_elbow", window=3)
    assert "right_elbow" not in calibrated[0]
    assert "right_elbow" in calibrated[1]


def test_confidence_floored_at_zero():
    """Confidence must never go negative."""
    frames = [
        {"right_elbow": {"x": i * 10.0, "y": 0.0, "conf": 0.5}}  # huge variance
        for i in range(5)
    ]
    calibrated = calibrate_confidence_multiframe(frames, joint="right_elbow", window=5)
    for f in calibrated:
        assert f["right_elbow"]["conf"] >= 0.0


def test_empty_frames_returns_empty():
    result = calibrate_confidence_multiframe([], joint="right_elbow")
    assert result == []


# ---------------------------------------------------------------------------
# Write-back test for apply_multiframe_calibration
# ---------------------------------------------------------------------------

def test_apply_multiframe_calibration_writeback():
    """
    apply_multiframe_calibration must write calibrated confidence values back
    into pose_results and all written values must be plain Python floats.

    We bypass MVPPoseEstimator.__init__ (which requires live MediaPipe) by
    constructing a bare instance and setting only the attributes the method
    reads.
    """
    # right_elbow → index 14 in BASKETBALL_KEYPOINTS
    RIGHT_ELBOW_IDX = 14
    N_LANDMARKS = 33  # MediaPipe has 33 landmarks

    def _make_result(x: float, conf: float) -> dict:
        landmarks = np.zeros((N_LANDMARKS, 3), dtype=float)
        landmarks[RIGHT_ELBOW_IDX] = [x, 0.5, 0.0]
        confidence = np.full(N_LANDMARKS, 0.8, dtype=float)
        confidence[RIGHT_ELBOW_IDX] = conf
        return {
            "frame_idx": 0,
            "processed_idx": 0,
            "timestamp": 0.0,
            "landmarks": landmarks,
            "confidence": confidence,
        }

    # Three frames with stable x → std ≈ 0, so confidence should be preserved
    pose_results = [_make_result(x=0.5 + i * 0.001, conf=0.85) for i in range(3)]

    # Build a bare MVPPoseEstimator without touching __init__
    estimator = object.__new__(MVPPoseEstimator)
    estimator.pose_results = pose_results
    estimator.confidence_threshold = 0.3

    estimator.apply_multiframe_calibration(joints=["right_elbow"], window=3)

    for result in estimator.pose_results:
        conf_seq = result["confidence"]
        written_conf = conf_seq[RIGHT_ELBOW_IDX]
        # Must be a plain Python float after write-back
        assert isinstance(written_conf, float), (
            f"Expected plain float, got {type(written_conf)}"
        )
        # Nearly-zero variance → confidence should remain close to original
        assert written_conf > 0.80, (
            f"Stable joint confidence should be near 0.85, got {written_conf}"
        )
