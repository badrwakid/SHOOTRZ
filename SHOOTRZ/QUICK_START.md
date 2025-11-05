# 🚀 SHOOTRZ Quick Start & Testing Guide

## ⚡ Quick Setup (5 minutes)

### 1. Setup Environment Variables
```powershell
cd D:\myprojects\Grad\SHOOTRZ
.\setup_env.ps1
```

This creates both `.env` files automatically.

### 2. Start Backend

**Option A: Use helper script (Recommended)**
```powershell
cd D:\myprojects\Grad\SHOOTRZ
.\start_backend.ps1
```

**Option B: Manual start**
```powershell
# ⚠️ IMPORTANT: Run from project root, NOT from SHOOTRZ or SHOOTRZ\backend
cd D:\myprojects\Grad
uvicorn SHOOTRZ.backend.main:app --reload
```

**Expected:** `INFO: Uvicorn running on http://127.0.0.1:8000`

**If you get `ModuleNotFoundError: No module named 'SHOOTRZ'`:**
- Make sure you're in `D:\myprojects\Grad` (project root)
- NOT in `D:\myprojects\Grad\SHOOTRZ` or `D:\myprojects\Grad\SHOOTRZ\backend`

### 3. Test Backend (in new terminal)
```powershell
cd D:\myprojects\Grad\SHOOTRZ
.\test_backend.ps1
```

**Expected:** All 4 tests pass (✅)

### 4. Start Frontend
```powershell
cd D:\myprojects\Grad\SHOOTRZ
npx expo start
```

**Expected:** Expo DevTools opens with QR code

---

## ✅ Complete Testing Workflow

### Phase 1: Backend Verification

#### A. Check Health
Open browser: http://127.0.0.1:8000/health
- Should return: `{"status":"healthy",...}`

#### B. Check API Docs
Open browser: http://127.0.0.1:8000/docs
- Should show Swagger UI with all endpoints

#### C. Run Test Script
```powershell
.\test_backend.ps1
```
- Should pass all 4 tests

#### D. Manual API Test
```powershell
# Test analyze
$body = @{ user_id = "test-123"; file_url = "https://example.com/test.mp4" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST -Body $body -ContentType "application/json"
```

---

### Phase 2: Frontend Verification

#### A. Start Expo
```powershell
npx expo start
```

#### B. Test Auth Flow
1. App opens → LoginScreen
2. Sign up with email → Creates Supabase user
3. Login → Navigates to HomeScreen
4. Check Supabase Dashboard → `users` table has your user

#### C. Test Video Analysis
1. Go to AnalyzeScreen
2. Pick/record video
3. Video uploads → Supabase Storage
4. Backend processes → `/analyze` called
5. Results poll → `/result/{job_id}` called
6. Metrics display → Check console for errors

#### D. Verify Supabase
1. Go to: https://supabase.com/dashboard/project/apbtuxchrymgmjbjxltm
2. **Database → Table Editor:**
   - `users` → Should have your user
   - `videos` → Should have video records
   - `metrics` → Should have metric rows
   - `feedback` → Should have feedback rows
3. **Storage → Buckets → videos:**
   - Should see uploaded video files

---

## 🐛 Troubleshooting

### Backend won't start
```powershell
# Check Python
python --version  # Should be 3.12+

# Check dependencies
cd D:\myprojects\Grad\SHOOTRZ\backend
pip install -r requirements.txt

# Check imports
cd D:\myprojects\Grad
python -c "from SHOOTRZ.backend.main import app; print('OK')"
```

### Frontend can't connect
- Check backend is running on port 8000
- For physical device: Update `API_BASE_URL` in `api.service.ts` to your computer's IP
- Check firewall isn't blocking port 8000

### Supabase errors
- Verify `.env` files exist and have correct values
- Restart Expo after changing `.env`
- Check browser console for specific errors

### Database writes fail
- Verify `SUPABASE_SERVICE_KEY` in `backend/.env`
- Check Supabase RLS policies are applied (run `schema.sql` and `storage_policies.sql`)

---

## 📋 Final Checklist

Before deploying:
- [ ] Backend starts without errors
- [ ] `/health` returns `{"status":"healthy"}`
- [ ] `/docs` shows Swagger UI
- [ ] `test_backend.ps1` passes all tests
- [ ] Frontend starts with Expo
- [ ] Login/Signup works
- [ ] Video upload works
- [ ] Analysis results display
- [ ] Supabase Dashboard shows data
- [ ] No console errors in frontend
- [ ] No errors in backend logs

---

## 🎯 Next Steps

After everything works:
1. Implement actual video processing in `_process_job()` (currently stub)
2. Add PoseMagic/HybrIK lifting adapters
3. Add real-time feedback via Supabase Realtime
4. Implement advanced metrics calculations
5. Add model download scripts

---

## 📚 Additional Resources

- Backend API Docs: http://127.0.0.1:8000/docs
- Supabase Dashboard: https://supabase.com/dashboard/project/apbtuxchrymgmjbjxltm
- Testing Guide: See `TESTING_GUIDE.md`
- Environment Setup: See `SETUP_ENV.md`

