# SHOOTRZ MVP - Quick Start Guide

Get up and running with the MVP in 5 minutes.

## Prerequisites

- Python 3.12
- Node.js (for React Native app)
- iOS Simulator or Android Emulator

## Step 1: Install Backend Dependencies

```bash
cd SHOOTRZ/backend
pip install -r requirements.txt
```

## Step 2: Start Backend Server

```bash
# From SHOOTRZ/backend directory
uvicorn backend.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

## Step 3: Verify Backend

Open http://127.0.0.1:8000/docs in your browser to see the API documentation.

Test health endpoint:
```bash
curl http://127.0.0.1:8000/health
```

Should return:
```json
{
  "status": "healthy",
  "service": "SHOOTRZ FastAPI Backend",
  "version": "1.0.0"
}
```

## Step 4: Start React Native App

```bash
cd SHOOTRZ
npm install  # If first time
npm start
```

Press:
- `i` for iOS Simulator
- `a` for Android Emulator

## Step 5: Test MVP Analysis

1. Open the app
2. Navigate to "Analyze" tab
3. Record or upload a basketball shooting video
4. Wait for analysis (1-2 minutes)
5. View results: score, metrics, angle graphs

## Test with Sample Video

If you have a sample basketball shooting video:

```bash
curl -X POST http://127.0.0.1:8000/mvp/analyze \
  -F "file=@your_shot_video.mp4" \
  -F "shooting_side=auto"
```

Response:
```json
{
  "job_id": "uuid-here",
  "status": "queued"
}
```

Check results:
```bash
curl http://127.0.0.1:8000/mvp/result/{job_id}
```

## Outputs Location

All analysis outputs are saved in:
```
SHOOTRZ/backend/outputs/{run_id}/
```

Each run creates a unique directory with all artifacts.

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (should be 3.12)
- Verify all dependencies installed: `pip list | grep mediapipe`
- Check port 8000 is not in use

### App can't connect to backend
- Verify backend is running on port 8000
- Check `EXPO_PUBLIC_API_URL` in `.env` (should be `http://127.0.0.1:8000`)
- For physical device, use your computer's IP instead of 127.0.0.1

### Analysis fails
- Check backend logs for errors
- Verify video format (mp4, mov)
- Check video shows full body
- Review quality warnings in results

## Next Steps

- Review [README.md](README.md) for detailed documentation
- Check [CALIBRATION_GUIDE.md](CALIBRATION_GUIDE.md) for tuning parameters
- Run tests: `pytest tests/ -v`
- Tune `config/mvp_config.yaml` for your use case

## API Endpoints

- `POST /mvp/analyze` - Upload video for analysis
- `GET /mvp/result/{job_id}` - Get analysis results
- `GET /mvp/artifacts/{run_id}/{filename}` - Download artifacts
- `GET /health` - Check API health
- `GET /docs` - Interactive API documentation

## Support

If you encounter issues:
1. Check backend console for errors
2. Review output artifacts in `outputs/{run_id}/`
3. Check `confidence_summary.json` for pose detection quality
4. Verify video meets recording guidelines in README




