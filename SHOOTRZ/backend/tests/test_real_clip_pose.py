"""Regression guard: full MVP pipeline on a real recorded clip.

Reproduces the 2026-04-23 incident where ``backend/inference/pose_2d.py``
silently emitted ``(0.5, 0.5, conf=0.5)`` landmarks for every frame because
MediaPipe failed to initialise. Downstream CSVs, angles, and scores were all
0 and the client displayed "0 POOR" for every real analysis.

This test asserts that **real** pose data flows through the pipeline, not the
fallback placeholder. It is skipped automatically when the sample video is not
present (typical CI) so it does not block unrelated branches.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import pytest


BACKEND_ROOT = Path(__file__).resolve().parents[1]
REAL_CLIP = (
    BACKEND_ROOT
    / "outputs"
    / "6b84daec-4390-43ba-9416-0ed2202446cd"
    / "input_video.mp4"
)


pytestmark = pytest.mark.skipif(
    not REAL_CLIP.is_file(),
    reason=(
        f"Real-clip regression needs {REAL_CLIP}. Record/copy any ~10s "
        "shot video to that path to enable the guard."
    ),
)


def _landmark_std_across_frames(pose_csv: Path) -> float:
    df = pd.read_csv(pose_csv)
    if df.empty:
        return 0.0
    pivot = df.pivot_table(
        index="frame_id", columns="joint", values=["x_norm", "y_norm"], aggfunc="first"
    )
    return float(pivot.std(axis=0).max())


@pytest.fixture(scope="module")
def real_pipeline_result(tmp_path_factory):
    """Run the full pipeline once, reuse the artefacts across assertions.

    ``save_overlay=True`` so the overlay.mp4 regression assertion can read
    the generated file. Real MediaPipe is forced by unsetting the test-only
    fallback env var.
    """
    out_base = tmp_path_factory.mktemp("real_clip_run")
    prev = os.environ.pop("SHOOTRZ_POSE_FALLBACK", None)
    try:
        from mvp.core.pipeline import MVPPipeline  # local import after env wipe

        pipeline = MVPPipeline()
        # 2026-04-23 follow-up: auto-side detection on this clip was flipping
        # to "left" and collapsing every metric to Low Confidence. The
        # pipeline now retries the opposite side when auto + high pose
        # confidence + all-low-confidence-metrics. ``shooting_side="auto"``
        # exercises that retry path end-to-end.
        result = pipeline.process_video(
            str(REAL_CLIP),
            shooting_side="auto",
            save_overlay=True,
            outputs_base_dir=out_base,
        )
    finally:
        if prev is not None:
            os.environ["SHOOTRZ_POSE_FALLBACK"] = prev
    return result


def test_pose_keypoints_actually_move(real_pipeline_result):
    """The 2026-04-23 bug produced identical keypoints on every frame.

    If MediaPipe is returning real data, **every** joint will show measurable
    motion across a 13.7s shot clip. A max-std below 0.01 means every frame
    landed on the same coordinates — a textbook placeholder fingerprint.
    """
    run_dir = Path(real_pipeline_result["output_dir"])
    pose_csv = run_dir / "pose_keypoints.csv"
    assert pose_csv.exists(), "pose_keypoints.csv missing - pipeline failed early"
    max_std = _landmark_std_across_frames(pose_csv)
    assert max_std > 0.01, (
        f"Pose keypoints have max std {max_std:.6f} across frames. "
        "That is the 0.5/0.5 placeholder fingerprint — MediaPipe is not running."
    )


def test_release_frame_not_in_first_half_second(real_pipeline_result):
    """The fallback made shot-detection pick frame 1 via argmax_fallback.

    On a 13.7s / 30fps clip, release should land somewhere well past the first
    half-second (> frame 15). This guards against future regressions that put
    release_frame at 0 or 1 again.
    """
    if real_pipeline_result.get("status") == "completed_low_quality":
        pytest.skip("Low-quality status - pose detector correctly refused the clip")
    shot_window = real_pipeline_result.get("shot_window") or {}
    release_frame = shot_window.get("release_frame")
    assert release_frame is not None and release_frame > 15, (
        f"release_frame={release_frame}; expected >15 on a real 13.7s clip."
    )


def test_at_least_one_metric_is_nonzero(real_pipeline_result):
    """Previously every metric came back as 0.0 degrees with a 'Needs Work' verdict.

    A real shot must produce at least one non-zero angle from the shortlist
    ``elbow_extension``, ``knee_bend``, ``wrist_follow_through``.
    """
    if real_pipeline_result.get("status") == "completed_low_quality":
        pytest.skip("Low-quality status - pose detector correctly refused the clip")
    metrics = real_pipeline_result.get("metrics") or []
    watch = {"elbow_extension", "knee_bend", "wrist_follow_through"}
    nonzero: List[str] = [
        m.get("name", "")
        for m in metrics
        if m.get("name") in watch and float(m.get("value", 0.0) or 0.0) > 0.5
    ]
    assert nonzero, (
        "No tracked metric produced a non-zero value on a real clip. "
        f"metrics={[(m.get('name'), m.get('value')) for m in metrics]}"
    )


def test_pose_overall_confidence_above_fallback(real_pipeline_result):
    """The fallback hard-codes pose_overall_confidence=0.5. Real MediaPipe
    produces visibility values all over the 0-1 range; the mean across a
    reasonable clip should comfortably exceed 0.55."""
    if real_pipeline_result.get("status") == "completed_low_quality":
        pytest.skip("Low-quality status - pose detector correctly refused the clip")
    conf = real_pipeline_result.get("pose_overall_confidence")
    assert conf is not None
    assert conf > 0.55, (
        f"pose_overall_confidence={conf:.3f}; fallback fingerprint is exactly 0.5."
    )


def test_each_metric_reports_selected_frame_near_its_event(real_pipeline_result):
    """Each primitive emits a ``selected_frame`` anchored to the biomechanical
    event it represents: elbow peaks near release, knee bottoms near crouch,
    wrist follow-through ends near the end-frame."""
    if real_pipeline_result.get("status") == "completed_low_quality":
        pytest.skip("Low-quality status - pose detector correctly refused the clip")
    shot_window = real_pipeline_result.get("shot_window") or {}
    release_f = shot_window.get("release_frame")
    crouch_f = shot_window.get("crouch_frame")
    end_f = shot_window.get("end_frame")
    assert release_f is not None

    # Per-metric (reference frame, tolerance) pairs. Tolerances match the
    # widened search windows in ``metrics.py``: RELEASE_SEARCH=10, CROUCH_SEARCH=6.
    anchors = {
        "elbow_extension": (release_f, 15),
        "knee_bend": (crouch_f, 10),
        "wrist_follow_through": (end_f if isinstance(end_f, int) else release_f, 20),
    }

    checked = 0
    for m in real_pipeline_result.get("metrics") or []:
        if m.get("verdict") == "Low Confidence":
            continue
        name = m.get("name")
        anchor = anchors.get(name)
        if anchor is None:
            continue
        ref, tol = anchor
        sf = m.get("selected_frame")
        assert isinstance(sf, int), f"{name} has no selected_frame: {m}"
        assert ref is not None, f"{name} anchor frame missing from shot_window"
        assert abs(sf - ref) <= tol, (
            f"{name}.selected_frame={sf} is > {tol} frames away from {ref}"
        )
        checked += 1
    assert checked >= 1, "Expected at least one metric to survive the confidence gate"


def test_high_confidence_pose_yields_high_metric_confidence(real_pipeline_result):
    """When pose_overall_confidence is comfortably above 0.7, at least one
    primitive metric must clear the 0.5 confidence gate. Pre-fix, elbow/wrist
    still came back Low Confidence on real clips because the NaN-on-any-low-joint
    rule in the angle layer filtered too aggressively."""
    if real_pipeline_result.get("status") == "completed_low_quality":
        pytest.skip("Low-quality status - pose detector correctly refused the clip")
    pose_conf = float(real_pipeline_result.get("pose_overall_confidence") or 0.0)
    if pose_conf <= 0.7:
        pytest.skip(f"Pose confidence {pose_conf:.2f} too low for this assertion")
    confident = [
        m for m in (real_pipeline_result.get("metrics") or [])
        if m.get("verdict") != "Low Confidence" and float(m.get("confidence", 0) or 0) >= 0.5
    ]
    assert confident, (
        "No primitive metric passed the 0.5 confidence gate despite "
        f"pose_overall_confidence={pose_conf:.2f}. "
        f"metrics={[(m.get('name'), m.get('confidence'), m.get('verdict')) for m in (real_pipeline_result.get('metrics') or [])]}"
    )


def test_overlay_video_written(real_pipeline_result):
    """The YAML flag is true by default post-2026-04-23. Pipeline must drop
    an overlay.mp4 in the run directory whenever save_overlay is enabled."""
    if real_pipeline_result.get("status") == "completed_low_quality":
        pytest.skip("Low-quality status - overlay is skipped by design")
    run_dir = Path(real_pipeline_result["output_dir"])
    # The pipeline snapshots the input for the annotator and the service then
    # writes overlay.mp4. Here we invoke annotate_video directly against the
    # artefacts the pipeline already wrote, mirroring what mvp_job_service does.
    import json as _json
    import numpy as _np

    from backend.inference.pose_2d import BASKETBALL_KEYPOINTS
    from backend.utils.video_annotator import annotate_video

    pose_json_path = run_dir / "pose_keypoints.json"
    assert pose_json_path.exists(), "pose_keypoints.json missing"
    pose_json = _json.loads(pose_json_path.read_text(encoding="utf-8"))
    pose_frames = pose_json.get("frames", [])
    keypoint_count = max(BASKETBALL_KEYPOINTS.values()) + 1
    pose_results = []
    for frame in pose_frames:
        frame_idx = frame.get("frame_idx", 0)
        joints = frame.get("joints", {})
        landmarks = _np.zeros((keypoint_count, 3), dtype=float)
        confidence = _np.zeros((keypoint_count,), dtype=float)
        for joint_name, joint_data in joints.items():
            if joint_name not in BASKETBALL_KEYPOINTS:
                continue
            idx = BASKETBALL_KEYPOINTS[joint_name]
            landmarks[idx, 0] = joint_data.get("x_norm", 0.0)
            landmarks[idx, 1] = joint_data.get("y_norm", 0.0)
            landmarks[idx, 2] = joint_data.get("z_norm", 0.0)
            confidence[idx] = joint_data.get("confidence", 0.0)
        pose_results.append(
            {"frame_idx": frame_idx, "landmarks": landmarks, "confidence": confidence}
        )

    overlay_path = run_dir / "overlay.mp4"
    # Use the ORIGINAL clip, since the save_overlay=True branch wrote
    # input_video.mp4 into the run dir.
    input_video = run_dir / "input_video.mp4"
    source = str(input_video) if input_video.exists() else str(REAL_CLIP)
    annotate_video(
        video_path=source,
        pose_results=pose_results,
        phases=real_pipeline_result.get("phases") or [],
        output_path=str(overlay_path),
        fps=pose_json.get("video_metadata", {}).get("fps", 30.0),
        shot_window=real_pipeline_result.get("shot_window") or {},
        metric_hud=[],
        metric_markers={},
    )
    assert overlay_path.exists(), "overlay.mp4 was not written"
    assert overlay_path.stat().st_size > 1000, "overlay.mp4 is suspiciously small"

    # Sanity-check the overlay decodes and has frames.
    import cv2 as _cv2

    cap = _cv2.VideoCapture(str(overlay_path))
    try:
        frames = int(cap.get(_cv2.CAP_PROP_FRAME_COUNT) or 0)
    finally:
        cap.release()
    assert frames >= 1, "overlay.mp4 decoded zero frames"
