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
