# MVP Core Pipeline

This directory contains the deterministic, config-driven analysis core.

## Design Rules

- Keep logic deterministic and reproducible.
- Avoid API/web concerns here.
- Preserve artifact names and metric semantics unless explicitly versioned.

## Module Boundaries

- `video_loader.py`: ingest frames + metadata
- `pose_estimation.py`: pose extraction and export
- `signal_smoothing.py`: denoise/interpolate landmarks
- `angle_computation.py`: compute per-frame joint angles
- `shot_detection.py`: detect shot events/window
- `metrics.py`: derive explainable metrics and score
- `pipeline.py`: orchestration only
- `run_tracker.py`: run IDs and output paths

## Contract Sensitivity

Outputs consumed by mobile/backend contracts:

- `angles.csv`
- `shot_window.json`
- `report.json`
- `pose_keypoints.json`

Any changes to shape/meaning must include contract and regression updates.
