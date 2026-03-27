# MVP Calibration Guide

Guide for tuning `config/mvp_config.yaml` parameters using real videos.

## Calibration Workflow

1. Record or collect 3-5 sample videos with known good/bad form
2. Run analysis on each video
3. Review outputs (angles.csv, shot_window.json, report.json)
4. Adjust config parameters
5. Re-run and compare
6. Iterate until metrics align with expert assessment

## Parameter Tuning

### Pose Detection

**Symptom**: Jittery skeleton, missing joints
**Parameter**: `pose_detection.min_detection_confidence`
- **Default**: 0.5
- **Lower** (0.3-0.4): More detections but noisier
- **Higher** (0.6-0.7): Fewer but more confident detections

**Symptom**: Smooth tracking lost between frames
**Parameter**: `pose_detection.min_tracking_confidence`
- **Default**: 0.5
- **Adjust**: Match detection confidence

### Smoothing

**Symptom**: Angles still jittery after smoothing
**Parameter**: `smoothing.window_length`
- **Default**: 5
- **Increase** (7, 9, 11): More smoothing, may lag
- **Decrease** (3): Less smoothing, more responsive

**Symptom**: Smoothed curve doesn't follow trend
**Parameter**: `smoothing.polyorder`
- **Default**: 2 (quadratic)
- **Increase** (3): Fits more complex curves
- **Decrease** (1): Linear interpolation

### Shot Detection

**Symptom**: Release detected too early
**Parameter**: `shot_detection.wrist_peak_window`
- **Default**: 15 frames
- **Increase** (20-30): Finds later peaks
- **Effect**: Searches over wider window

**Symptom**: Crouch not detected (too shallow)
**Parameter**: `shot_detection.knee_flexion_threshold`
- **Default**: 100° (flexion below this = crouch)
- **Lower** (90-95°): Detects shallower crouches
- **Higher** (105-110°): Only deep crouches

**Symptom**: Shot window too short/long
**Parameters**:
- `shot_detection.pre_frames`: Frames before crouch (default: 10)
- `shot_detection.post_frames`: Frames after release (default: 20)

### Metrics

**Symptom**: Good form marked "Needs Work"
**Parameters**: Adjust `good_range` for each metric
- `metrics.elbow_extension.good_range`: [150, 175]
- `metrics.knee_bend.good_range`: [85, 120]
- `metrics.wrist_follow_through.good_range`: [10, 30]

**Example**: If shooters with 145° elbow are performing well:
```yaml
metrics:
  elbow_extension:
    good_range: [145, 175]  # Lowered minimum
    optimal_range: [160, 170]
```

### Scoring

**Symptom**: Score too harsh/lenient
**Parameters**: Adjust `scoring.weights`
- **Default**: `{elbow: 0.40, knee: 0.30, wrist: 0.30}`
- **Emphasize elbow**: `{elbow: 0.50, knee: 0.25, wrist: 0.25}`
- **Balanced**: `{elbow: 0.33, knee: 0.33, wrist: 0.34}`

**Symptom**: Low confidence penalized too much
**Parameter**: `scoring.confidence_penalty`
- **Default**: 0.5 (multiply score by 50%)
- **Lenient**: 0.7-0.8
- **Strict**: 0.3-0.4

## Example Calibration Session

### Scenario: Release detection is consistently 5 frames too early

**Diagnosis**:
1. Check `shot_window.json`: `"release_frame": 45`
2. Review `angles.csv`: Plot wrist angle, expect peak near frame 50
3. Watch overlay video: Actual release at frame 50

**Solution**:
```yaml
shot_detection:
  wrist_peak_window: 20  # Increased from 15
  post_frames: 25  # Increased from 20 for more follow-through data
```

**Verification**:
- Re-run analysis
- Check new `shot_window.json`: Should now detect frame 50
- Verify metrics extracted at correct frame

### Scenario: Knee bend metric says "Needs Work" for good shooters

**Diagnosis**:
1. Check `report.json`: Knee bend values are 115-125°
2. Good shooters have slightly less flexion than expected

**Solution**:
```yaml
metrics:
  knee_bend:
    good_range: [85, 130]  # Extended upper bound from 120 to 130
    optimal_range: [95, 120]  # Kept optimal stricter
```

## Validation Checklist

After tuning, verify:

- [ ] Shot window aligns with visual inspection (check overlay.mp4)
- [ ] Crouch frame is at deepest knee bend
- [ ] Release frame is at or just before actual ball release
- [ ] Angle curves are smooth (check angles.csv plot)
- [ ] Metrics reflect expert assessment
- [ ] Score differentiates good/poor form
- [ ] Feedback text is actionable

## Best Practices

1. **Test on diverse videos**: Different shooters, angles, lighting
2. **Compare to expert assessment**: Validate metrics against coach feedback
3. **Document changes**: Note why each parameter was changed
4. **Version config**: Save tuned configs with descriptive names
5. **Re-test after changes**: Run full test suite after calibration

## Common Issues

### Issue: All metrics show "Low Confidence"
**Cause**: Poor video quality or lighting
**Fix**: 
- Improve recording conditions
- Lower `pose_detection.confidence_threshold` (not recommended)

### Issue: Angles seem inverted or wrong
**Cause**: Shooting side detection error
**Fix**: 
- Explicitly set `shooting_side` parameter when calling API
- Check `pose_keypoints.json` for correct wrist detection

### Issue: Multiple shots detected, wrong one selected
**Cause**: Not implemented in MVP (single shot only)
**Workaround**: 
- Trim video to single shot before upload
- Future: Implement multi-shot ranking

## Performance Tuning

For faster processing:

```yaml
video:
  frame_skip: 2  # Process every 2nd frame
  max_frames: 90  # Limit to 3 seconds @ 30fps

pose_detection:
  model_complexity: 0  # Fastest model
```

Trade-off: May reduce accuracy slightly.

## Advanced Tuning

### Context-Aware Ranges

Different shot distances may need different ranges. Edit config per use case:

**Close range (<3m)**:
```yaml
metrics:
  elbow_extension:
    good_range: [155, 180]  # More extension for close shots
```

**Long range (>6m)**:
```yaml
metrics:
  knee_bend:
    good_range: [75, 110]  # Deeper bend for power
```

### Confidence Weighting

Weight metrics by confidence:

```yaml
scoring:
  use_confidence_weighting: true  # Future feature
  min_confidence_for_scoring: 0.5
```

## Feedback

If calibration doesn't resolve issues:
1. Save problematic video + outputs
2. Note expected vs actual behavior
3. Check intermediate artifacts (angles.csv, shot_window.json)
4. Report issue with full diagnostics




