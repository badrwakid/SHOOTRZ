# SHOOTRZ Testing Guide - FastAPI + Supabase

## ✅ Complete Testing Checklist

### 1. Backend Setup & Verification

#### Step 1: Verify Environment Variables
```powershell
# Check if .env files exist
Test-Path SHOOTRZ\backend\.env
Test-Path SHOOTRZ\.env

# If missing, create them:
# SHOOTRZ/backend/.env should have:
# SUPABASE_URL=https://apbtuxchrymgmjbjxltm.supabase.co
# SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
# SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Step 2: Install Backend Dependencies
```powershell
cd D:\myprojects\Grad\SHOOTRZ\backend
pip install -r requirements.txt
```

#### Step 3: Start FastAPI Backend
```powershell
cd D:\myprojects\Grad
uvicorn SHOOTRZ.backend.main:app --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

#### Step 4: Test Backend Endpoints

**A. Health Check:**
```powershell
curl http://127.0.0.1:8000/health
# Or open in browser: http://127.0.0.1:8000/health
```
**Expected:** `{"status":"healthy","service":"SHOOTRZ API",...}`

**B. API Docs:**
- Open: http://127.0.0.1:8000/docs
- Should show Swagger UI with all endpoints

**C. Test Analyze Endpoint (JSON):**
```powershell
$body = @{
    user_id = "test-user-id-123"
    file_url = "https://example.com/video.mp4"
    angle = "45"
    fps = 30
    device = "mobile"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST -Body $body -ContentType "application/json"
```
**Expected:** `{"job_id":"...","status":"queued"}`

**D. Test Result Endpoint:**
```powershell
# Use job_id from previous response
Invoke-RestMethod -Uri "http://127.0.0.1:8000/result/YOUR_JOB_ID" -Method GET
```
**Expected:** `{"job_id":"...","status":"completed","metrics":[...],"feedback":[...]}`

**E. Test History Endpoint:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/history/test-user-id-123" -Method GET
```
**Expected:** `{"user_id":"...","sessions":[...]}`

---

### 2. Frontend Setup & Verification

#### Step 1: Verify Environment Variables
```powershell
# Check if .env exists
Test-Path SHOOTRZ\.env

# SHOOTRZ/.env should have:
# EXPO_PUBLIC_SUPABASE_URL=https://apbtuxchrymgmjbjxltm.supabase.co
# EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

#### Step 2: Install Frontend Dependencies
```powershell
cd D:\myprojects\Grad\SHOOTRZ
npm install
```

#### Step 3: Start Expo
```powershell
npx expo start
```

**Expected:** Expo DevTools opens, QR code displayed

#### Step 4: Test Frontend Components

**A. Auth Flow:**
1. Open app → Should show LoginScreen
2. Sign up with email → Should create Supabase user
3. Login → Should navigate to HomeScreen
4. Logout → Should return to LoginScreen

**B. Supabase Connection:**
- Check browser console for errors
- No "Supabase not configured" errors
- Auth session should persist on reload

---

### 3. End-to-End Testing

#### Test 1: Video Upload → Analysis Flow

**Using New Supabase Flow:**
1. Login to app
2. Go to AnalyzeScreen
3. Pick/record video
4. Should upload to Supabase Storage
5. Should call `/analyze` with file_url
6. Should poll `/result/{job_id}` 
7. Should display metrics and feedback

**Using Direct Upload (AnalyzeScreen):**
1. Login to app
2. Go to AnalyzeScreen  
3. Pick video
4. Should upload file directly to `/analyze`
5. Should get job_id
6. Should poll for results
7. Should display transformed metrics

#### Test 2: Supabase Database Verification

**Check Supabase Dashboard:**
1. Go to: https://supabase.com/dashboard/project/apbtuxchrymgmjbjxltm
2. Database → Table Editor:
   - `users` table should have your user
   - `videos` table should have video records
   - `metrics` table should have metric rows
   - `feedback` table should have feedback rows

**SQL Query Test:**
```sql
-- Check recent videos
SELECT * FROM videos ORDER BY created_at DESC LIMIT 5;

-- Check metrics
SELECT * FROM metrics ORDER BY created_at DESC LIMIT 10;

-- Check feedback
SELECT * FROM feedback ORDER BY created_at DESC LIMIT 10;
```

#### Test 3: Storage Verification

**Supabase Dashboard:**
1. Storage → Buckets → `videos`
2. Should see uploaded video files
3. File paths should be: `{user_id}/{timestamp}-filename.mp4`

---

### 4. Common Issues & Fixes

#### Issue: Backend won't start
**Fix:**
```powershell
# Check Python path
python --version  # Should be 3.12+

# Check imports
cd D:\myprojects\Grad
python -c "from SHOOTRZ.backend.main import app; print('OK')"

# Check env vars are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv('SHOOTRZ/backend/.env'); print(os.getenv('SUPABASE_URL'))"
```

#### Issue: Frontend can't connect to backend
**Fix:**
- Check backend is running on port 8000
- For physical device, update API_BASE_URL to your computer's IP
- Check firewall isn't blocking port 8000
- Verify CORS is enabled (already set in main.py)

#### Issue: Supabase auth not working
**Fix:**
- Verify .env has EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY
- Check browser console for errors
- Restart Expo after changing .env

#### Issue: Database writes failing
**Fix:**
- Verify SUPABASE_SERVICE_KEY is set in backend/.env
- Check Supabase RLS policies are applied
- Verify schema.sql was run in Supabase SQL Editor

---

### 5. Quick Health Check Script

Save this as `test_backend.ps1`:
```powershell
Write-Host "Testing SHOOTRZ Backend..." -ForegroundColor Cyan

# Test health endpoint
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET
    Write-Host "✅ Health check passed: $($health.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
}

# Test analyze endpoint (JSON)
try {
    $body = @{
        user_id = "test-123"
        file_url = "https://example.com/test.mp4"
    } | ConvertTo-Json
    
    $analyze = Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST -Body $body -ContentType "application/json"
    Write-Host "✅ Analyze endpoint works. Job ID: $($analyze.job_id)" -ForegroundColor Green
    
    # Test result endpoint
    Start-Sleep -Seconds 2
    $result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/result/$($analyze.job_id)" -Method GET
    Write-Host "✅ Result endpoint works. Status: $($result.status)" -ForegroundColor Green
} catch {
    Write-Host "❌ Analyze/Result test failed: $_" -ForegroundColor Red
}

Write-Host "`nDone!" -ForegroundColor Cyan
```

Run with: `.\test_backend.ps1`

---

### 6. Final Verification Checklist

- [ ] Backend starts without errors on port 8000
- [ ] `/health` endpoint returns `{"status":"healthy"}`
- [ ] `/docs` shows Swagger UI
- [ ] `/analyze` accepts JSON and returns `job_id`
- [ ] `/result/{job_id}` returns metrics and feedback
- [ ] `/history/{user_id}` returns sessions
- [ ] Frontend starts with Expo
- [ ] Login/Signup works with Supabase
- [ ] Video upload works (either flow)
- [ ] Analysis results display correctly
- [ ] Supabase Dashboard shows new rows in tables
- [ ] Storage bucket has uploaded videos

---

## 🚀 Quick Start Commands

**Backend:**
```powershell
cd D:\myprojects\Grad
uvicorn SHOOTRZ.backend.main:app --reload
```

**Frontend:**
```powershell
cd D:\myprojects\Grad\SHOOTRZ
npx expo start
```

**Check Both:**
- Backend: http://127.0.0.1:8000/docs
- Frontend: Expo DevTools + mobile app






