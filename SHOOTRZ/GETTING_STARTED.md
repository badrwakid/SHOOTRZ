# Getting Started with SHOOTRZ

🎉 **Congratulations!** You've completed the setup. Here's how to use SHOOTRZ.

## Quick Start

### 1. Verify Setup

Run the verification script:
```bash
cd SHOOTRZ
python scripts/verify_setup.py
```

Run quick functionality tests:
```bash
python scripts/quick_test.py
```

### 2. Start the Backend

```bash
cd SHOOTRZ/backend
python -m uvicorn main:create_app --factory --reload
```

The backend will start on `http://127.0.0.1:8000`

**Verify it's running:**
- Visit: http://127.0.0.1:8000/health
- API Docs: http://127.0.0.1:8000/docs
- Database Test: http://127.0.0.1:8000/test-db

### 3. Start the Frontend

In a new terminal:
```bash
cd SHOOTRZ
npm start
```

Then:
- Press `a` for Android emulator
- Press `i` for iOS simulator
- Press `w` for web browser
- Scan QR code with Expo Go app (for physical device)

## First Use

### 1. Sign Up / Sign In

- Create an account or sign in with existing credentials
- Complete onboarding (if prompted)

### 2. Record or Upload a Video

**Recording Guidelines:**
- **Duration**: 1-30 seconds
- **Angle**: Side view recommended (45° or 90°)
- **Distance**: 2-5 meters from shooter
- **Lighting**: Good lighting, avoid backlight
- **Stability**: Keep camera steady

**Best Practices:**
- Capture full body (head to feet)
- Include ball release moment
- Show follow-through

### 3. Submit for Analysis

1. Upload video (or record directly in app)
2. Wait for processing (typically 10-30 seconds)
3. View results:
   - **Metrics**: Detailed biomechanical measurements
   - **Feedback**: Actionable tips for improvement
   - **Phases**: Key moments (stance, crouch, release, landing)
   - **Visualization**: Skeleton overlay and ball trajectory

### 4. Review Progress

- Navigate to Progress tab
- View:
  - Metric trends over time
  - Session comparisons
  - Consistency scores
  - Improvement percentages

## Understanding the Results

### Metrics Explained

**Forearm Verticality** (0-10° optimal)
- Angle between forearm and vertical axis
- Lower is better (more vertical = better control)

**Elbow Flexion** 
- Preparatory: 70-85° (optimal power loading)
- Release: 165-180° (full extension)

**Knee Flexion** (100-120° optimal)
- Depth of crouch before release
- More flexion = more power

**Release Angle** (distance-dependent)
- Close shots (2.8m): 70-80°
- Mid-range (4.6m): 60-70°
- Long-range: 55-65°

**Entry Angle** (45-55° optimal)
- Angle of ball at rim entry
- Steeper entry = higher scoring chance

### Feedback Severity

- **Error** (Red): Critical issues that significantly impact accuracy
- **Warning** (Yellow): Important improvements that enhance performance
- **Info** (Blue): Minor optimizations for consistency

## Troubleshooting

### Backend Issues

**Port already in use:**
```bash
# Find process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or change port in .env
```

**Import errors:**
```bash
# Reinstall dependencies
cd backend
pip install -r requirements.txt
```

**Supabase connection failed:**
- Verify `.env` file has correct credentials
- Check Supabase dashboard → Settings → API
- Test connection: `curl http://127.0.0.1:8000/test-db`

### Frontend Issues

**Can't connect to backend:**
- Verify backend is running: `curl http://127.0.0.1:8000/health`
- Check `EXPO_PUBLIC_API_URL` in `.env`
- For Android emulator, use `10.0.2.2:8000` instead of `127.0.0.1:8000`

**Video upload fails:**
- Check video format (MP4, MOV, AVI supported)
- Verify file size < 100MB
- Check backend logs for errors

**Charts not rendering:**
- Clear cache: `npx expo start --clear`
- Reinstall: `rm -rf node_modules && npm install`

### Processing Issues

**Analysis takes too long:**
- Check backend logs for errors
- Verify MediaPipe is installed: `python -c "import mediapipe"`
- Check video quality (lower resolution = faster processing)

**No metrics returned:**
- Ensure video shows full shooting motion
- Verify pose detection is working (check skeleton overlay)
- Check backend logs for error messages

**Ball not detected:**
- Ensure ball is visible in frame
- Try different camera angle
- Check lighting conditions

## Next Steps

### Advanced Features

1. **Fine-tune YOLOv8** (Optional):
   ```bash
   python scripts/download_datasets.py --datasets deepsport
   python scripts/finetune_yolo_ball.py --dataset data/ball/basketball-instants/data.yaml
   ```

2. **Enable 3D Lifting** (Optional):
   - Download PoseMagic model weights
   - Update `use_3d_lifting=True` in pipeline

3. **Set Up Monitoring**:
   - Add error tracking (Sentry)
   - Set up analytics
   - Configure logging

### Production Deployment

See `SETUP.md` for production deployment instructions.

## API Testing

Test the API directly:

```bash
# Health check
curl http://127.0.0.1:8000/health

# Upload video (example)
curl -X POST http://127.0.0.1:8000/analyze \
  -F "file=@path/to/video.mp4" \
  -F "user_id=test-user-123"

# Check result
curl http://127.0.0.1:8000/result/{job_id}
```

## Support Resources

- **API Documentation**: http://127.0.0.1:8000/docs
- **Backend Logs**: Check terminal output
- **Supabase Dashboard**: Monitor database and storage
- **Expo Logs**: Check Metro bundler output

## Tips for Best Results

1. **Recording Quality**
   - Use highest resolution available
   - Stable camera (tripod recommended)
   - Good lighting
   - Clear background

2. **Camera Positioning**
   - Side view (90°) is most accurate
   - 45° angle also works well
   - Avoid front/rear views

3. **Practice Consistency**
   - Record multiple shots per session
   - Use similar conditions each time
   - Review trends, not single results

4. **Improvement Focus**
   - Address "Error" feedback first
   - Work on "Warning" items systematically
   - Use "Info" tips for fine-tuning

---

**Ready to improve your shot? Start analyzing! 🏀**



