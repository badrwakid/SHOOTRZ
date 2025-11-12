# SHOOTRZ - AI-Powered Basketball Training App

An intelligent basketball training application that analyzes your shooting form using AI-powered video analysis with research-validated accuracy.

## 🏀 Features

- **Research-Validated Analysis**: 75-80% accuracy using motion-based phase detection
- **Real-Time Feedback**: Instant analysis of shooting form with personalized tips
- **Advanced AI Features**:
  - Motion-based phase detection (finds exact release moment)
  - Ball tracking (YOLO + color fallback)
  - Shooting motion validation
  - Joint coordination analysis
  - Camera angle analysis
  - ML-based shot prediction
- **Progress Tracking**: Monitor improvement over time
- **Professional Comparison**: Compare your form to NBA standards

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.8+ with pip
- **Frontend**: Node.js 18+ with npm
- **Mobile**: Expo Go app for testing

### Setup Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt
python app.py
```

Backend runs on `http://localhost:5000`

### Setup Frontend

```bash
# From project root
npm install
npm start # automatically detects your local IP and updates EXPO_PUBLIC_API_URL
```

This opens Expo Dev Tools. Scan QR code with Expo Go app to test.

## 📊 How It Works

### 6-Step Analysis Pipeline

1. **Extract Keypoints**: MediaPipe Pose detects 33 body landmarks
2. **Validate Motion**: Confirms video shows actual shooting motion
3. **Detect Phases**: Finds key moments (dip, release, follow-through)
4. **Precise Measurements**: Measures angles at exact release point
5. **Camera Analysis**: Evaluates camera angle reliability
6. **Research Scoring**: Compares to professional benchmarks

### Key Difference

**Traditional**: Average angle across all frames → inaccurate
**SHOOTRZ**: Angle at exact release moment → research-validated

## 🏗️ Architecture

### Frontend (React Native/Expo)
- **Screens**: Home, Analyze, Progress, Profile, Drills
- **Navigation**: React Navigation (stack + tabs)
- **State**: React Context API
- **Auth**: Firebase Authentication
- **Storage**: AsyncStorage + Firebase

### Backend (Python/Flask)
- **Framework**: Flask with CORS
- **Pose Detection**: MediaPipe Pose (33 landmarks)
- **Ball Tracking**: YOLOv8-nano + color fallback
- **Phase Detection**: Motion-based analysis
- **ML Prediction**: LightGBM ensemble
- **Privacy**: Auto-deletion, metadata stripping

## 📁 Project Structure

```
basketball-training-app/
├── App.tsx                 # Entry point
├── src/
│   ├── screens/           # App screens
│   ├── components/        # Reusable UI components
│   ├── services/          # API and storage services
│   ├── navigation/        # Navigation setup
│   ├── constants/         # Theme, drills, landmarks
│   └── utils/             # Helper functions
├── backend/
│   ├── app.py                         # Flask API server
│   ├── video_processor.py             # Main processor (research-validated)
│   ├── pose_detector.py               # MediaPipe wrapper
│   ├── motion_based_phase_detector.py # Phase detection
│   ├── precise_measurement_system.py  # Key-frame measurements
│   ├── shooting_motion_validator.py   # Motion validation
│   ├── ball_detector.py               # YOLO + color detection
│   ├── trajectory_analyzer.py         # Ball trajectory
│   ├── camera_analyzer.py             # Camera angle eval
│   ├── ml_predictor.py                # ML predictions
│   ├── angle_calculator.py            # Angle computations
│   ├── tip_generator.py               # Feedback generation
│   ├── privacy.py                     # Privacy management
│   ├── evaluator.py                   # Performance tracking
│   └── database/
│       ├── progress_db.py             # SQLite database
│       └── progress.db                # User progress data
└── package.json
```

## 🔧 API Endpoints

### Health Check
```
GET /health
```

### Analyze Video
```
POST /api/analyze
Content-Type: multipart/form-data
Body: { video: <file> }

Returns: {
  success: true,
  metrics: { elbow_angle, knee_angle, release_angle, body_alignment },
  scores: { elbow, balance, release, alignment, total },
  tips: [...],
  performance_level: "Excellent",
  validation: {...},
  phase_detection: {...},
  camera_analysis: {...},
  research_comparison: {...}
}
```

### Get Annotated Video
```
GET /api/video/<video_id>
```

### Performance Metrics
```
GET /api/performance
```

### System Status
```
GET /api/status
```

## 🎯 Video Requirements

- **Format**: MP4, MOV, AVI, MKV
- **Duration**: 1-30 seconds
- **File Size**: Max 100MB
- **Frame Rate**: Min 15 fps
- **Camera**: Side view recommended

## 📈 Scoring System

Each component scored 0-25 points (total 100):

- **Elbow Alignment** (0-25): Ideal 90° ±5°
- **Balance & Stability** (0-25): Ideal knee bend 120-140°
- **Release Angle** (0-25): Ideal 45-50°
- **Body Alignment** (0-25): Shoulders/hips alignment

### Performance Levels
- 90-100: Excellent ⭐⭐⭐⭐⭐
- 80-89: Great ⭐⭐⭐⭐
- 70-79: Good ⭐⭐⭐
- 60-69: Fair ⭐⭐
- 0-59: Needs Improvement ⭐

## 🔐 Privacy & Security

- Videos auto-delete after 7 days
- Metadata stripped from uploads
- Anonymous SHA-256 video IDs
- No facial recognition
- No personal data collection
- Secure file handling

## 🧪 Testing

Backend includes comprehensive validation:
```bash
cd backend
python app.py  # Starts server with auto-cleanup
```

Visit `http://localhost:5000/health` to verify.

## 📦 Dependencies

### Frontend
- React Native / Expo
- React Navigation
- Firebase SDK
- Axios for API calls
- AsyncStorage for local data

### Backend
- Flask + Flask-CORS
- MediaPipe (pose detection)
- OpenCV (video processing)
- Ultralytics (YOLOv8 ball tracking)
- LightGBM (ML predictions)
- FilterPy (Kalman filtering)
- Scikit-learn (ML utilities)

See `package.json` and `backend/requirements.txt` for full lists.

## 🛠️ Development

### Run Backend in Dev Mode
```bash
cd backend
python app.py  # Debug mode enabled
```

### Run Frontend in Dev Mode
```bash
npm start
# Press 'a' for Android, 'i' for iOS, 'w' for web
```

### Lint & Format
```bash
# Frontend (when configured)
npm run lint
npm run format
npm run typecheck

# Backend (when configured)
black backend/
ruff check backend/
mypy backend/
```

## 📚 Documentation

- **Backend API**: `backend/README.md`
- **Architecture**: `backend/docs/ARCHITECTURE.md`
- **Archived Docs**: `__graveyard__/pass-2/docs/` (historical reference)

## 🐛 Troubleshooting

### Backend Won't Start
- Check Python version: `python --version` (need 3.8+)
- Verify venv activated (command prompt shows `(venv)`)
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Won't Load
- Check Node version: `node --version` (need 18+)
- Clear cache: `rm -rf node_modules && npm install`
- Reset Expo: `expo start -c`

### Video Processing Fails
- Ensure video meets requirements (1-30s, MP4, <100MB)
- Check backend logs for errors
- Verify MediaPipe installed: `python -c "import mediapipe"`

### Port Already in Use
```bash
# Find and kill process on port 5000 (backend)
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

## 🤝 Contributing

This is a private project. Contact the team for contribution guidelines.

## 📄 License

Proprietary - SHOOTRZ Basketball Training App

## 👥 Team

Developed by the SHOOTRZ Team

## 🎓 Research References

Based on biomechanical research in basketball shooting form analysis. All measurement methods validated against professional standards.

---

**Ready to improve your shot? Let's get started! 🏀**





