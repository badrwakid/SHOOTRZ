# SHOOTRZ MVP - Basketball Shooting Analysis

A deterministic, config-driven pipeline for analyzing basketball shooting form using pose estimation and biomechanics.

## Features

- **Three Core Metrics**: Elbow extension, knee bend depth, wrist follow-through
- **Deterministic Outputs**: Same input + config = same output
- **Traceable Results**: Every metric references exact frames and formulas
- **Config-Driven**: All thresholds in `config/mvp_config.yaml`
- **Comprehensive Artifacts**: CSV, JSON, pose overlay video

## Setup

### 1. Install Dependencies

```bash
cd SHOOTRZ/backend
pip install -r requirements.txt
```

### 2. Start Backend Server

```bash
uvicorn backend.main:app --reload --port 8000
```

### 3. Start React Native App

```bash
cd SHOOTRZ
npm start
```

## API Usage

### Analyze Video

```bash
POST /mvp/analyze
Content-Type: multipart/form-data

Parameters:
- file: Video file (mp4, mov)
- shooting_side: "auto", "left", or "right" (optional)

Returns:
{
  "job_id": "uuid",
  "status": "queued"
}
```

### Get Results

```bash
GET /mvp/result/{job_id}

Returns:
{
  "status": "completed",
  "run_id": "uuid",
  "overall_score": 78,
  "feedback_summary": "Good form overall...",
  "metrics": [
    {
      "name": "elbow_extension",
      "value": 165.3,
      "unit": "degrees",
      "verdict": "Good",
      "explanation": "...",
      "confidence": 0.92
    },
    ...
  ],
  "shot_window": {...},
  "angles_data": {...},
  "artifacts": {...}
}
```

### Download Artifacts

```bash
GET /mvp/artifacts/{run_id}/angles.csv
GET /mvp/artifacts/{run_id}/report.json
GET /mvp/artifacts/{run_id}/overlay.mp4
```

## Output Structure

Each analysis run creates a directory in `backend/outputs/{run_id}/` containing:

- `config_used.yaml` - Configuration snapshot
- `video_metadata.json` - Video info (fps, resolution, etc.)
- `frame_mapping.csv` - Frame index to timestamp mapping
- `pose_keypoints.csv` - Raw 2D pose landmarks
- `pose_keypoints.json` - Structured pose data
- `pose_keypoints_smoothed.csv` - Smoothed landmarks
- `angles.csv` - Per-frame joint angles
- `shot_window.json` - Detected shot phases
- `confidence_summary.json` - Pose detection confidence stats
- `report.json` - Final metrics, score, and feedback
- `run_metadata.json` - Run tracking metadata
- `overlay.mp4` - Pose skeleton overlay video (if enabled)

## Configuration

Edit `backend/config/mvp_config.yaml` to tune:

- **Pose detection**: Model complexity, confidence thresholds
- **Smoothing**: Savitzky-Golay parameters
- **Shot detection**: Knee/wrist thresholds, window sizes
- **Metrics**: Good/optimal ranges for each metric
- **Scoring**: Weights and confidence penalties

## Recording Guidelines

For best results:

1. **Camera Position**: Side view or 45° angle capturing full body
2. **Distance**: 2-4 meters from shooter
3. **Lighting**: Well-lit, avoid shadows
4. **Duration**: 2-5 seconds per shot
5. **Framing**: Full body visible from feet to extended arm
6. **Background**: Clear, minimal distractions
7. **Resolution**: 720p or higher
8. **FPS**: 30fps minimum

## Known Limitations

- **2D Perspective**: Depth information is estimated, not measured
- **Camera Angle**: Assumes roughly side-on view (not behind/front)
- **Wrist Proxy**: Wrist angle is approximation (no hand landmarks in MVP)
- **Single Shot**: Analyzes most prominent shot if multiple present
- **No Ball Tracking**: Uses pose-based release detection only

## Metric Definitions

### 1. Elbow Extension at Release
- **Definition**: Internal angle at elbow joint (shoulder-elbow-wrist) averaged over release window
- **Units**: Degrees
- **Good Range**: 150-175°
- **Optimal**: 160-170°
- **Physics**: Optimal extension provides power without over-extension

### 2. Knee Bend Depth
- **Definition**: Minimum internal angle at knee joint (hip-knee-ankle) during crouch phase
- **Units**: Degrees
- **Good Range**: 85-120°
- **Optimal**: 95-110°
- **Physics**: Proper bend generates leg drive while maintaining balance

### 3. Wrist Follow-Through
- **Definition**: Change in wrist angle from release to end of shot window
- **Units**: Degrees
- **Good Range**: 10-30° change
- **Optimal**: 15-25° change
- **Physics**: Proper snap generates backspin and arc

## Calibration

If detection is inaccurate:

1. **Release too early/late**: Adjust `shot_detection.wrist_peak_window`
2. **Crouch not detected**: Lower `shot_detection.knee_flexion_threshold`
3. **Noisy angles**: Increase `smoothing.window_length`
4. **Missing joints**: Lower `pose_detection.confidence_threshold`

## Testing

Run unit tests:

```bash
cd backend/mvp
pytest tests/ -v
```

Run integration test:

```bash
pytest tests/test_integration.py -v
```

## Troubleshooting

### Video won't load
- Check file format (mp4, mov supported)
- Check file is not corrupted
- Verify duration > 1 second

### Low pose confidence
- Improve lighting
- Ensure full body is visible
- Check camera is stable
- Verify subject is in frame

### Inaccurate metrics
- Review `confidence_summary.json` for pose quality
- Check `shot_window.json` for correct phase detection
- Tune config parameters
- Verify camera angle is side-on

## Architecture

```
Pipeline Flow:
Video → Frames → Pose Detection → Smoothing → Angles → 
Shot Detection → Metrics → Scoring → Report
```

Each phase saves intermediate artifacts for reproducibility and debugging.

## Support

For issues or questions, check:
- Output logs in console
- `run_metadata.json` for processing details
- `confidence_summary.json` for pose quality
- Quality warnings in `video_metadata.json`


