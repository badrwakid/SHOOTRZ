# Testing Instructions - Analysis Feature Fixes

## Quick Test

1. **Start the backend**:
   ```bash
   cd SHOOTRZ
   python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
   ```

2. **Upload a form-only video** (no ball required):
   - Use the mobile app
   - Record or upload a shooting form video
   - Wait for analysis to complete

3. **Check the results**:
   - All scores should be > 0 (not all zeros)
   - Metrics should have values (not undefined)
   - Arc height should not be negative (or not computed if no ball)

## Expected Results

### Metrics That Should Be Computed (Form-Only Video):
- ✅ `forearm_verticality` (elbow position)
- ✅ `elbow_flexion_release` (elbow angle at release)
- ✅ `elbow_flexion_crouch` (elbow angle at crouch)
- ✅ `knee_flexion` (knee alignment)
- ✅ `hip_flexion` (hip alignment)
- ✅ `shoulder_angle` (shoulder position)
- ✅ `elbow_height` (release height)
- ✅ `release_angle` (estimated from pose)
- ✅ `wrist_angular_velocity` (follow through)
- ✅ `grip_quality` (if hands detected)

### Metrics That Won't Be Computed (No Ball):
- ❌ `arc_height` (requires ball trajectory)
- ❌ `entry_angle` (requires ball trajectory)
- ❌ `release_height` (from ball, but we have `elbow_height` from pose)

### Scores Should Be:
- **Non-zero**: Based on actual form analysis
- **Reasonable**: Angles in 0-180° range, heights in cm
- **Confidence**: Most metrics should have confidence > 0.5

## Debug Mode

To see detailed metric computation logs:

```bash
# Set environment variable
export DEBUG_METRICS=true  # Linux/Mac
set DEBUG_METRICS=true     # Windows PowerShell

# Then start backend
python -m uvicorn backend.main:app --reload
```

This will print:
- Which metrics were computed
- Which metrics are missing
- Confidence scores for each metric

## Troubleshooting

### If scores are still 0:
1. Check if pose detection is working (should see pose landmarks in logs)
2. Verify phases are detected (stance, crouch, release, landing)
3. Enable DEBUG_METRICS to see which metrics are missing

### If metrics are undefined:
1. Check pose detection confidence (should be > 0.5)
2. Verify video has clear view of shooter
3. Check that required keypoints are detected (shoulders, elbows, wrists, knees)

### If arc height is still negative:
1. This should only happen if ball trajectory exists
2. Check ball tracking is working correctly
3. Verify coordinate conversion is applied

## Verification Checklist

- [ ] Backend starts without errors
- [ ] Video uploads successfully
- [ ] Analysis completes (no errors)
- [ ] At least 5-7 metrics are computed
- [ ] Scores are non-zero
- [ ] No negative arc height (or arc height not computed)
- [ ] Release angle is reasonable (45-65°)
- [ ] All pose-based metrics have values

## Next Steps After Testing

If everything works:
1. ✅ System is ready for use
2. Consider fine-tuning models for better accuracy
3. Train on basketball-specific datasets

If issues remain:
1. Check DEBUG_METRICS output
2. Verify video quality and lighting
3. Ensure shooter is fully visible in frame

