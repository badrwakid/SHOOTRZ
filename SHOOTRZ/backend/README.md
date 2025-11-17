# SHOOTRZ AI Backend - MediaPipe Pose Detection API

Production-ready backend for basketball shooting form analysis using MediaPipe Pose estimation.

## Features

- **Real-time Pose Detection**: MediaPipe Pose with 33 body landmarks
- **Angle Analysis**: Elbow, knee, release angle, and body alignment calculations
- **Smart Coaching**: AI-generated tips based on shooting form metrics
- **Annotated Videos**: Skeleton overlay on analyzed videos
- **Privacy First**: Auto-deletion, metadata stripping, anonymous IDs
- **Performance Tracking**: Metrics and analytics for all processed videos

## Quick Start

### 1. Setup Virtual Environment (Recommended)

Create and activate a virtual environment:

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages including:
- Flask & Flask-CORS (API server)
- MediaPipe (pose detection)
- OpenCV (video processing)
- Ultralytics (YOLOv8 ball tracking)
- LightGBM (ML predictions)
- FilterPy (Kalman filtering)
- And more...

### 3. Start Server

```bash
python start_server.py
```

Or directly:

```bash
python app.py
```

Server will run on `http://localhost:5000`

## API Endpoints

### Health Check
```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "service": "SHOOTRZ Pose Detection API",
  "version": "1.0.0",
  "timestamp": "2025-10-17T..."
}
```

### Analyze Video
```
POST /api/analyze
Content-Type: multipart/form-data

Body:
- video: video file (mp4, mov, avi, mkv)
```

Response:
```json
{
  "success": true,
  "video_id": "abc123...",
  "metrics": {
    "elbow_angle": 92.5,
    "knee_angle": 128.3,
    "release_angle": 46.8,
    "body_alignment": 87.5
  },
  "scores": {
    "elbow": 23.75,
    "balance": 24.5,
    "release": 24.0,
    "alignment": 21.88,
    "total": 94.13
  },
  "tips": [
    "Great elbow alignment! Your 90° shooting form is optimal for accuracy.",
    "Perfect knee bend! Your leg positioning provides excellent power and balance.",
    "Excellent release angle! Your shot arc is optimal for consistent shooting."
  ],
  "performance_level": "Excellent",
  "processing_stats": {
    "processing_time": 8.5,
    "total_frames": 240,
    "processed_frames": 238,
    "pose_detection_rate": 99.17,
    "processing_fps": 28.24
  },
  "timestamp": "2025-10-17T..."
}
```

### Get Annotated Video
```
GET /api/video/<video_id>
```

Returns: MP4 video with pose skeleton overlay

### Performance Metrics
```
GET /api/performance
```

Response:
```json
{
  "success": true,
  "summary": {
    "total_evaluations": 5,
    "average_processing_time": 9.2,
    "average_fps": 26.1,
    "successful_analyses": 5,
    "failed_analyses": 0
  },
  "trends": {...}
}
```

### System Status
```
GET /api/status
```

Response:
```json
{
  "success": true,
  "system_status": {
    "max_video_length": 30,
    "max_file_size_mb": 100,
    "allowed_extensions": ["mp4", "mov", "avi", "mkv"]
  },
  "privacy_status": {
    "total_pending": 3,
    "retention_days": 7,
    "cleanup_thread_running": true
  }
}
```

### Force Cleanup
```
POST /api/cleanup
```

Manually triggers cleanup of old files.

## Architecture

### Components

1. **pose_detector.py** - MediaPipe Pose wrapper
   - 33-point body landmark detection
   - Basketball-specific keypoint extraction
   - Pose visibility validation

2. **angle_calculator.py** - Angle computation engine
   - Vector-based angle calculations
   - Frame-by-frame analysis
   - Statistical aggregation

3. **tip_generator.py** - AI coaching tips
   - Smart feedback generation
   - Component scoring (0-25 each)
   - Performance level assessment

4. **video_processor.py** - Video analysis pipeline
   - Frame-by-frame processing
   - Annotated video generation
   - Processing statistics

5. **privacy.py** - Privacy & security
   - SHA-256 anonymous IDs
   - Metadata stripping
   - Auto-deletion (7 days)

6. **evaluator.py** - Performance tracking
   - Processing metrics
   - Accuracy measurements
   - Trend analysis

7. **app.py** - Flask REST API server
   - Request handling
   - File validation
   - Error management

## Video Requirements

- **Format**: MP4, MOV, AVI, MKV
- **Max Duration**: 30 seconds
- **Max File Size**: 100 MB
- **Min FPS**: 15 fps
- **Min Duration**: 1 second

## Scoring System

Each component scored 0-25 points, total max 100:

- **Elbow Alignment** (0-25): Ideal 90° ±5°
- **Balance & Stability** (0-25): Ideal knee bend 120-140°
- **Release Angle** (0-25): Ideal 45-50°
- **Body Alignment** (0-25): Shoulders/hips alignment

### Performance Levels

- **90-100**: Excellent
- **80-89**: Great
- **70-79**: Good
- **60-69**: Fair
- **0-59**: Needs Improvement

## Privacy & Ethics

- Videos auto-delete after 7 days
- Metadata stripped from uploads
- Anonymous SHA-256 video IDs
- No facial recognition
- No personal data collection
- Secure file handling

## Error Handling

The API returns appropriate HTTP status codes:

- **200**: Success
- **400**: Bad request (invalid file, etc.)
- **404**: Resource not found
- **413**: File too large
- **500**: Server error

## Development

### Project Structure

```
backend/
├── app.py                 # Main Flask server
├── pose_detector.py       # MediaPipe Pose wrapper
├── video_processor.py     # Video analysis logic
├── angle_calculator.py    # Angle computations
├── tip_generator.py       # Coaching tips
├── privacy.py            # Privacy management
├── evaluator.py          # Performance metrics
├── start_server.py       # Startup script
├── test_backend.py       # Comprehensive tests
├── test_imports.py       # Import verification
├── requirements.txt      # Python dependencies
├── uploads/             # Temporary uploads
└── processed/           # Annotated videos
```

### Testing

Test with curl:
```bash
# Health check
curl http://localhost:5000/health

# Performance metrics
curl http://localhost:5000/api/performance
```

## Performance

Target metrics:
- **Processing Speed**: <10 seconds for 10-second 1080p video
- **Pose Detection Rate**: >95%
- **Accuracy**: ±5° angle precision
- **FPS**: Real-time or better (30+ fps)

Actual performance (MediaPipe):
- **MediaPipe Version**: 0.10.21
- **OpenCV Version**: 4.11.0
- **No GPU Required**: Runs on CPU
- **33 Landmarks**: vs YOLO's 17

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:
```bash
pip install flask flask-cors opencv-python numpy mediapipe
```

### Port Already in Use

If port 5000 is taken, modify in `app.py`:
```python
app.run(host='0.0.0.0', port=5001, debug=True)
```

### Video Codec Issues

If video output fails, install ffmpeg:
- Windows: `choco install ffmpeg`
- Mac: `brew install ffmpeg`
- Linux: `sudo apt install ffmpeg`

## Model Training

### Fine-tuning YOLOv8 for Ball Detection

The system supports fine-tuned YOLOv8 models for improved ball/player detection:

1. **Prepare Dataset**:
   ```bash
   python scripts/convert_deepsport_to_yolo.py
   ```

2. **Train Model**:
   ```bash
   python scripts/finetune_yolo_ball.py --dataset data/ball/deepsport_yolo/data.yaml
   ```

3. **Model Location**: Trained model saved to `models/yolov8n_basketball_deepsport.pt`

4. **Automatic Loading**: The pipeline automatically loads fine-tuned models if available, falls back to pretrained YOLOv8n otherwise.

See `docs/TRAINING_GUIDE.md` for detailed training instructions.

## License

Proprietary - SHOOTRZ Basketball Training App

## Support

For issues or questions, contact the development team.


