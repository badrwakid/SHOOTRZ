# ✅ Verify Application Uses Database Correctly

## Quick Test

**Run the integration test:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/db/integration-test" -Method GET
```

## What This Tests

The integration test simulates the **complete application flow**:

1. **Create User** → Creates test user (like signup)
2. **Analyze Video** → Records video (like `/analyze` endpoint)
3. **Record Metrics** → Saves metrics (backend processing)
4. **Record Feedback** → Saves feedback (feedback engine)
5. **Get History** → Queries history (like `/history/{user_id}` endpoint)
6. **Verify Data** → Confirms all data exists in database

## Expected Output

**Success:**
```json
{
  "timestamp": "2025-11-01T...",
  "test_name": "Full Application Integration Test",
  "steps": {
    "create_user": {"status": "success", "user_id": "..."},
    "analyze_video": {"status": "success", "video_id": "..."},
    "record_metrics": {"status": "success", "metric_count": 3},
    "record_feedback": {"status": "success", "feedback_count": 2},
    "get_history": {"status": "success", "video_count": 1},
    "verify_data": {"status": "success", "video_exists": true, ...}
  },
  "status": "success"
}
```

## Manual Verification Steps

### 1. Test Analyze Endpoint → Database
```powershell
# This should create a video record in database
$body = @{
    user_id = "00000000-0000-0000-0000-000000000001"  # Valid UUID
    file_url = "https://example.com/test.mp4"
    angle = "45"
    fps = 30
    device = "mobile"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST `
  -Body $body -ContentType "application/json"
```

**Then check Supabase Dashboard:**
- Go to: https://supabase.com/dashboard/project/apbtuxchrymgmjbjxltm
- Database → Table Editor → `videos` table
- You should see the new video record

### 2. Test History Endpoint → Database
```powershell
# Use the user_id from step 1
Invoke-RestMethod -Uri "http://127.0.0.1:8000/history/00000000-0000-0000-0000-000000000001" -Method GET
```

**Should return:** Video records from database

### 3. Verify Frontend Connection

**Check frontend Supabase client:**
1. Open: `SHOOTRZ/src/services/supabase.client.ts`
2. Verify: `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` are set

**Test in frontend (when app is running):**
- Sign up → Creates user in `users` table
- Upload video → Calls `/analyze` → Creates video record
- View history → Calls `/history/{user_id}` → Reads from database

## Check Real Application Flow

### Backend Flow:
1. **`/analyze` endpoint** → `record_video()` → Inserts into `videos` table
2. **Background processing** → `record_metrics()` → Inserts into `metrics` table
3. **Feedback generation** → `record_feedback()` → Inserts into `feedback` table
4. **`/history/{user_id}` endpoint** → `get_user_history()` → Queries `videos` table

### Frontend Flow:
1. **Upload video** → `uploadVideo()` → Uploads to Supabase Storage
2. **Call `/analyze`** → `analyzeJson()` → Backend records video
3. **Poll `/result/{job_id}`** → Get analysis results
4. **View history** → `getHistory()` → Backend queries database

## Verify in Supabase Dashboard

After running integration test or using the app:

1. **`users` table:**
   ```sql
   SELECT * FROM users ORDER BY created_at DESC LIMIT 5;
   ```

2. **`videos` table:**
   ```sql
   SELECT v.*, u.email 
   FROM videos v 
   JOIN users u ON v.user_id = u.id 
   ORDER BY v.created_at DESC LIMIT 5;
   ```

3. **`metrics` table:**
   ```sql
   SELECT m.*, v.user_id 
   FROM metrics m 
   JOIN videos v ON m.video_id = v.id 
   ORDER BY m.created_at DESC LIMIT 10;
   ```

4. **`feedback` table:**
   ```sql
   SELECT f.*, m.metric_name 
   FROM feedback f 
   JOIN metrics m ON f.metric_id = m.id 
   ORDER BY f.created_at DESC LIMIT 10;
   ```

## Common Issues

### Issue: "user_id not found"
**Cause:** User doesn't exist in `users` table  
**Fix:** Create user via Supabase Auth or insert into `users` table first

### Issue: "Foreign key violation"
**Cause:** Referenced ID doesn't exist  
**Fix:** Ensure parent records exist (user before video, video before metric, etc.)

### Issue: Frontend can't connect
**Cause:** Missing `.env` file or wrong keys  
**Fix:** Verify `EXPO_PUBLIC_SUPABASE_URL` and `EXPO_PUBLIC_SUPABASE_ANON_KEY` in frontend `.env`

## Summary

✅ **Application uses database correctly if:**
- Integration test returns `"status": "success"`
- `/analyze` endpoint creates video records
- `/history/{user_id}` returns data from database
- Supabase Dashboard shows records
- Frontend can read/write data

❌ **Issue if:**
- Integration test fails
- Endpoints return 500 errors
- No data appears in Supabase
- Foreign key violations






