# Testing the MVP Implementation

Quick guide to test the newly implemented MVP system.

## Prerequisites Check

```bash
# Check Python version
python --version  # Should be 3.12.x

# Check if backend dependencies are installed
cd SHOOTRZ/backend
pip list | grep -E "mediapipe|opencv|fastapi|scipy|pyyaml"
```

## Test 1: Config Loading

```bash
cd SHOOTRZ/backend
python -c "
from mvp.core.config_loader import load_config
config = load_config()
print('✅ Config loaded successfully')
print(f'Pose model complexity: {config.get(\"pose_detection.model_complexity\")}')
print(f'Smoothing window: {config.get(\"smoothing.window_length\")}')
"
```

Expected output:
```
✅ Config loaded successfully
Pose model complexity: 1
Smoothing window: 5
```

## Test 2: Run Unit Tests

```bash
cd SHOOTRZ/backend/mvp
pytest tests/test_angle_computation.py -v
```

Expected: 5 tests pass

```bash
pytest tests/test_shot_detection.py -v
```

Expected: 2 tests pass

```bash
pytest tests/test_metric_scoring.py -v
```

Expected: 5 tests pass

## Test 3: Start Backend

```bash
cd SHOOTRZ/backend
uvicorn backend.main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

## Test 4: Test Health Endpoint

In another terminal:
```bash
curl http://127.0.0.1:8000/health
```

Expected:
```json
{
  "status": "healthy",
  "service": "SHOOTRZ FastAPI Backend",
  "version": "1.0.0"
}
```

## Test 5: View API Documentation

Open in browser: http://127.0.0.1:8000/docs

Should see interactive API docs with `/mvp/analyze` and `/mvp/result/{job_id}` endpoints.

## Test 6: Test MVP Endpoint (With Sample Video)

If you have a sample video:

```bash
curl -X POST http://127.0.0.1:8000/mvp/analyze \
  -F "file=@path/to/your/shot.mp4" \
  -F "shooting_side=auto"
```

Expected response:
```json
{
  "job_id": "some-uuid",
  "status": "queued"
}
```

Wait 30-60 seconds, then check results:
```bash
curl http://127.0.0.1:8000/mvp/result/YOUR_JOB_ID
```

Expected when completed:
```json
{
  "status": "completed",
  "run_id": "uuid",
  "overall_score": 75,
  "metrics": [
    {
      "name": "elbow_extension",
      "value": 165.3,
      "verdict": "Good",
      ...
    },
    ...
  ]
}
```

## Test 7: Verify Outputs Created

```bash
cd SHOOTRZ/backend/outputs
ls -la
```

Should see directory with run_id (UUID).

```bash
cd {run_id}
ls -la
```

Should see all artifacts:
- config_used.yaml
- video_metadata.json
- pose_keypoints.csv
- angles.csv
- shot_window.json
- report.json
- etc.

## Test 8: React Native App

### Start the app
```bash
cd SHOOTRZ
npm start
```

### Test in app
1. Press `i` (iOS) or `a` (Android)
2. App should open
3. Navigate to "Analyze" tab (should be visible in bottom nav)
4. Should see upload/record interface
5. Record or upload a video
6. Should see loading state
7. After processing, should see:
   - Overall score (large number)
   - Three metric cards with verdicts
   - Angle graph (if AngleGraph component works)
   - "Analyze Another Shot" button

## Validation Checklist

- [ ] Config file exists and loads correctly
- [ ] Unit tests pass
- [ ] Backend starts without errors
- [ ] Health endpoint returns healthy
- [ ] API docs show MVP endpoints
- [ ] Sample video can be analyzed via curl
- [ ] Outputs directory created with artifacts
- [ ] All expected files present in output/{run_id}/
- [ ] React Native app shows Analyze tab
- [ ] Can upload/record video from app
- [ ] Results display correctly in app

## Common Issues

### Issue: `ModuleNotFoundError: No module named 'mvp'`
**Solution:** Make sure you're running from `backend/` directory or adjust Python path

### Issue: `FileNotFoundError: Config file not found`
**Solution:** Check that `backend/config/mvp_config.yaml` exists

### Issue: Backend starts but `/mvp/analyze` returns 404
**Solution:** Check that `mvp.router` is imported and registered in `main.py`

### Issue: React Native can't connect
**Solution:** 
- Check backend is running on port 8000
- Verify `EXPO_PUBLIC_API_URL` in .env
- For physical device, use computer IP instead of 127.0.0.1

## Performance Benchmark

For a typical 3-second video (90 frames @ 30fps):

- Phase 1 (Video loading): < 1 second
- Phase 2 (Pose detection): ~2-3 seconds
- Phase 3 (Smoothing): < 1 second
- Phase 4 (Angles): < 1 second
- Phase 5 (Shot detection): < 1 second
- Phase 6 (Metrics): < 1 second

**Total: ~5-10 seconds**

## Next Steps After Testing

1. **Calibrate config** - Use real videos to tune parameters
2. **Add pose overlay** - Implement skeleton rendering in overlay.mp4
3. **Enhance UI** - Add download buttons, improve angle graph
4. **Collect feedback** - Test with real users
5. **Iterate** - Refine based on field testing

## Debug Mode

To see detailed logs, add to config:
```yaml
debug:
  verbose_logging: true
  save_intermediate_frames: true
```

Then check backend console for detailed processing logs.

## Success Criteria

✅ All tests pass
✅ Backend starts and serves MVP endpoints
✅ Sample video produces complete output set
✅ React Native app connects and displays results
✅ All artifacts are traceable and reproducible

---

**Ready for field testing!** 🏀


