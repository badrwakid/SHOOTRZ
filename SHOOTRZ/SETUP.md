# SHOOTRZ Setup Guide

This guide covers all manual setup steps required to get SHOOTRZ running.

## Prerequisites

- Python 3.12+ (for backend)
- Node.js 18+ and npm (for frontend)
- Supabase account (free tier is fine)
- Git

## Step 1: Database Setup (Supabase)

### 1.1 Create Supabase Project

1. Go to [supabase.com](https://supabase.com)
2. Create a new project
3. Note down your:
   - Project URL (e.g., `https://xxxxx.supabase.co`)
   - Service Role Key (from Settings → API)
   - Anon Key (from Settings → API)

### 1.2 Run Database Migrations

**IMPORTANT:** Run these migrations in order in the Supabase SQL Editor:

1. **Base Schema** (if not already created):
   - Create tables: `users`, `videos`, `metrics`, `feedback`, `sessions`
   - Set up RLS policies
   - (This may already exist in your Supabase project)

2. **MVP Enhancements Migration:**
   ```sql
   -- Run: SHOOTRZ/supabase/migration_mvp_enhancements.sql
   ```
   - Copy contents from `supabase/migration_mvp_enhancements.sql`
   - Paste into Supabase SQL Editor
   - Execute

3. **User Onboarding Migration:**
   ```sql
   -- Run: SHOOTRZ/supabase/migration_add_name_onboarding.sql
   ```
   - Copy contents from `supabase/migration_add_name_onboarding.sql`
   - Paste into Supabase SQL Editor
   - Execute

### 1.3 Set Up Storage Bucket

1. In Supabase Dashboard → Storage
2. Create a new bucket named `videos`
3. Set bucket to **Public** (or configure RLS policies)
4. Add policy:
   ```sql
   CREATE POLICY "Allow authenticated uploads"
   ON storage.objects FOR INSERT
   TO authenticated
   WITH CHECK (bucket_id = 'videos');
   
   CREATE POLICY "Allow public reads"
   ON storage.objects FOR SELECT
   TO public
   USING (bucket_id = 'videos');
   ```

## Step 2: Backend Setup

### 2.1 Install Python Dependencies

```bash
cd SHOOTRZ/backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2.2 Configure Environment Variables

Create `SHOOTRZ/backend/.env` file:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_ANON_KEY=your-anon-key

# FastAPI Configuration
API_HOST=127.0.0.1
API_PORT=8000
DEBUG=True

# Optional: For production
# CORS_ORIGINS=http://localhost:8081,https://yourdomain.com
```

**⚠️ IMPORTANT:** Add `.env` to `.gitignore` - never commit secrets!

### 2.3 Test Backend

```bash
cd SHOOTRZ/backend
# For localhost only (simulator/emulator):
python -m uvicorn main:create_app --factory --reload --host 127.0.0.1 --port 8000

# For physical devices on network (RECOMMENDED):
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

Or use the FastAPI CLI:
```bash
fastapi dev main.py
```

Visit `http://127.0.0.1:8000/docs` to see API documentation.

### 2.4 Verify Database Connection

Test the connection:
```bash
curl http://127.0.0.1:8000/health
```

Or use the test endpoint:
```bash
curl http://127.0.0.1:8000/test-db
```

## Step 3: Frontend Setup

### 3.1 Install Dependencies

```bash
cd SHOOTRZ
npm install
```

**Note:** The `react-native-chart-kit` package was added - make sure it installs correctly.

### 3.2 Configure Environment Variables

Create `SHOOTRZ/.env` file (or update `app.config.js`):

```env
# Supabase Configuration
EXPO_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Backend API
EXPO_PUBLIC_API_URL=http://127.0.0.1:8000

# Optional: For production
# EXPO_PUBLIC_API_URL=https://api.yourdomain.com
```

### 3.3 Update API Service Configuration

Edit `SHOOTRZ/src/services/api.service.ts` and verify the `baseURL`:

```typescript
// Should match your backend URL
private baseURL = process.env.EXPO_PUBLIC_API_URL || 'http://127.0.0.1:8000';
```

### 3.4 Start Frontend

```bash
cd SHOOTRZ
npm start
# Then press 'a' for Android, 'i' for iOS, or 'w' for web
```

## Step 4: Model Setup (Optional)

### 4.1 YOLOv8 for Ball Detection

YOLOv8 models are downloaded automatically when first used. However, if you want to use a fine-tuned model:

1. Fine-tune YOLOv8 (see `scripts/finetune_yolo_ball.py`):
   ```bash
   python scripts/finetune_yolo_ball.py --dataset data/ball/basketball-instants/data.yaml
   ```

2. Update `SHOOTRZ/backend/inference/ball_tracker.py` to use your fine-tuned model:
   ```python
   model_path = "models/yolov8n_basketball.pt"  # Your fine-tuned model
   ```

### 4.2 MediaPipe Models

MediaPipe models are downloaded automatically on first use. No manual setup needed.

## Step 5: Testing

### 5.1 Backend Tests

```bash
cd SHOOTRZ/backend
pytest tests/ -v
```

### 5.2 Frontend Tests (if configured)

```bash
cd SHOOTRZ
npm test
```

### 5.3 Manual Integration Test

1. Start backend: `cd backend && python -m uvicorn main:create_app --factory --reload`
2. Start frontend: `cd SHOOTRZ && npm start`
3. In the app:
   - Create account / Sign in
   - Record or upload a basketball shooting video
   - Submit for analysis
   - Wait for processing (polling happens automatically)
   - View results: metrics, feedback, phase markers

## Step 6: Production Deployment (Optional)

### 6.1 Backend Deployment

**Option A: Railway / Render**
1. Connect your GitHub repo
2. Set environment variables
3. Deploy

**Option B: Docker**
```bash
cd SHOOTRZ/backend
docker build -t shootrz-backend .
docker run -p 8000:8000 --env-file .env shootrz-backend
```

### 6.2 Frontend Deployment

**Expo EAS Build:**
```bash
cd SHOOTRZ
eas build --platform android
eas build --platform ios
```

## Troubleshooting

### Backend Issues

**Error: "Module not found"**
- Make sure virtual environment is activated
- Run `pip install -r requirements.txt` again

**Error: "Supabase connection failed"**
- Verify `.env` file has correct `SUPABASE_URL` and keys
- Test connection in Supabase Dashboard → SQL Editor

**Error: "Video processing fails"**
- Check that MediaPipe is installed: `pip install mediapipe`
- Verify OpenCV can read videos: `python -c "import cv2; print(cv2.__version__)"`

### Frontend Issues

**Error: "Cannot connect to API"**
- Verify backend is running: `curl http://127.0.0.1:8000/health`
- Check `EXPO_PUBLIC_API_URL` in `.env`
- For Android emulator, use `10.0.2.2:8000` instead of `127.0.0.1:8000`

**Error: "Supabase auth fails"**
- Verify `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY`
- Check Supabase Dashboard → Authentication → Settings

**Error: "Charts not rendering"**
- Ensure `react-native-chart-kit` is installed: `npm install react-native-chart-kit`
- May need to rebuild: `npx expo start --clear`

### Database Issues

**Error: "Table does not exist"**
- Run migrations in Supabase SQL Editor
- Check migration order (base schema → mvp_enhancements → onboarding)

**Error: "RLS policy violation"**
- Verify RLS policies are set correctly
- Check user authentication status
- Review Supabase Dashboard → Authentication → Policies

## Quick Checklist

- [ ] Supabase project created
- [ ] Database migrations run (2 files)
- [ ] Storage bucket `videos` created
- [ ] Backend `.env` configured
- [ ] Backend dependencies installed
- [ ] Backend running on port 8000
- [ ] Frontend `.env` configured
- [ ] Frontend dependencies installed
- [ ] Frontend running
- [ ] Can upload video
- [ ] Analysis completes successfully
- [ ] Results display correctly

## Next Steps

1. **Fine-tune YOLOv8** (optional): Download basketball datasets and train
2. **Add 3D lifting** (optional): Integrate PoseMagic model weights
3. **Set up monitoring**: Add error tracking (Sentry) and analytics
4. **Deploy to production**: Set up CI/CD and production environments

## Support

For issues, check:
- Backend logs: `uvicorn` output
- Frontend logs: Expo/Metro bundler output
- Supabase logs: Dashboard → Logs
- API docs: `http://127.0.0.1:8000/docs`

