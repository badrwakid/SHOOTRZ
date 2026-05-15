import numpy as np
import pandas as pd

from backend.mvp.core.shot_detection import ShotDetector


def _synthetic_dataframes(n_frames: int, release_frame: int, noise_std: float = 0.0, seed: int = 0):
    rng = np.random.default_rng(seed)
    t = np.arange(n_frames)
    crouch_frame = max(5, release_frame - 15)

    knee_angle = 140 - 32 * np.exp(-((t - crouch_frame) ** 2) / (2 * 5 ** 2))
    elbow_angle = 95 + 78 * np.exp(-((t - release_frame) ** 2) / (2 * 4 ** 2))
    wrist_angle = 85 + 10 * np.exp(-((t - release_frame) ** 2) / (2 * 6 ** 2))
    wrist_y = 0.8 - 0.3 * np.exp(-((t - release_frame) ** 2) / (2 * 5 ** 2))
    hip_y = 0.55 + 0.05 * np.exp(-((t - crouch_frame) ** 2) / (2 * 8 ** 2))

    if noise_std > 0:
        knee_angle += rng.normal(0, noise_std, size=n_frames)
        elbow_angle += rng.normal(0, noise_std, size=n_frames)
        wrist_y += rng.normal(0, noise_std / 120.0, size=n_frames)

    angles_df = pd.DataFrame(
        {
            "frame_id": t,
            "timestamp": t / 30.0,
            "knee_angle": knee_angle,
            "elbow_angle": elbow_angle,
            "wrist_angle": wrist_angle,
            "confidence_knee": np.full(n_frames, 0.95),
            "confidence_elbow": np.full(n_frames, 0.95),
            "confidence_wrist": np.full(n_frames, 0.95),
        }
    )

    pose_rows = []
    for fid in t:
        pose_rows.append(
            {
                "frame_id": int(fid),
                "joint": "right_wrist",
                "y_norm_smooth": float(wrist_y[fid]),
                "confidence": 0.95,
            }
        )
        pose_rows.append(
            {
                "frame_id": int(fid),
                "joint": "right_hip",
                "y_norm_smooth": float(hip_y[fid]),
                "confidence": 0.95,
            }
        )
    pose_df = pd.DataFrame(pose_rows)
    return angles_df, pose_df


def test_clean_release_detection_near_ground_truth():
    detector = ShotDetector({})
    angles_df, pose_df = _synthetic_dataframes(100, 45)
    result = detector.detect_shot_window(angles_df, pose_df, "right")
    assert abs(result["release_frame"] - 45) <= 3


def test_noisy_release_detection_within_tolerance():
    detector = ShotDetector({})
    angles_df, pose_df = _synthetic_dataframes(100, 45, noise_std=5.0)
    result = detector.detect_shot_window(angles_df, pose_df, "right")
    assert abs(result["release_frame"] - 45) <= 5


def test_high_heuristic_agreement_for_clean_signal():
    detector = ShotDetector({})
    angles_df, pose_df = _synthetic_dataframes(100, 60)
    result = detector.detect_shot_window(angles_df, pose_df, "right")
    fs = result["frame_selection"]
    assert fs["high_confidence_agreement"] is True
    assert fs["heuristics_n"] >= 2
    assert fs["heuristic_max_spread"] <= 5


def test_early_crouch_warning_present():
    detector = ShotDetector({})
    angles_df, pose_df = _synthetic_dataframes(60, 10)
    # Force an obvious crouch minimum near start to trigger warning path deterministically.
    angles_df.loc[angles_df["frame_id"] == 2, "knee_angle"] = 95.0
    result = detector.detect_shot_window(angles_df, pose_df, "right")
    assert "crouch_lt_lead_frames" in result["warnings"]


def test_release_argmax_fallback_is_annotated():
    detector = ShotDetector({"release_search_max_frames": 50, "consensus_fallback_deviation": 6})
    angles_df, pose_df = _synthetic_dataframes(110, 55)

    # Force a monotonic wrist segment after crouch so peak detection finds no
    # local maxima and the detector must use argmax fallback.
    crouch_guess = 40
    mask = (pose_df["joint"] == "right_wrist") & (pose_df["frame_id"] > crouch_guess)
    pose_df.loc[mask, "y_norm_smooth"] = np.linspace(0.72, 0.52, mask.sum())

    result = detector.detect_shot_window(angles_df, pose_df, "right")
    fs = result["frame_selection"]

    assert "release_argmax_fallback" in result["warnings"]
    assert fs["selection_reason"] in {"argmax_fallback", "consensus_fallback"}
    assert fs["used_fallback"] is True
    assert result["release_frame"] > result["crouch_frame"]


def test_consensus_fallback_is_bounded_by_release_cap():
    detector = ShotDetector({"release_search_max_frames": 10, "consensus_fallback_deviation": 2})
    angles_df, pose_df = _synthetic_dataframes(120, 72)
    expected_crouch = max(5, 72 - 15)

    # Force an early scored release candidate so consensus fallback path must
    # reconcile against later heuristic frames and clamp to release cap.
    detector._detect_release_scored = lambda *args, **kwargs: (
        expected_crouch + 2,
        0.8,
        {"chosen": {"kind": "peak"}, "candidates": []},
    )

    result = detector.detect_shot_window(angles_df, pose_df, "right")
    fs = result["frame_selection"]
    release_cap = result["crouch_frame"] + 10

    assert "release_consensus_fallback" in result["warnings"]
    assert fs["selection_reason"] == "consensus_fallback"
    assert result["release_frame"] <= release_cap


def test_release_selection_is_deterministic_for_same_input():
    detector = ShotDetector({"release_search_max_frames": 12, "consensus_fallback_deviation": 3})
    angles_df, pose_df = _synthetic_dataframes(120, 70, noise_std=3.0, seed=77)

    first = detector.detect_shot_window(angles_df, pose_df, "right")
    second = detector.detect_shot_window(angles_df, pose_df, "right")

    assert first["release_frame"] == second["release_frame"]
    assert first["frame_selection"]["selection_reason"] == second["frame_selection"]["selection_reason"]
    assert first["warnings"] == second["warnings"]
