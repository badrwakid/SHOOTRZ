# 🗄️ Testing Supabase Database Connection

## Quick Test

**Test the database endpoint:**
```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/db/test" -Method GET
```

## What the Test Checks

The `/db/test` endpoint verifies:

1. **Configuration Check:**
   - ✅ Supabase URL is set
   - ✅ Anon key is set  
   - ✅ Service key is set

2. **Connection Test:**
   - ✅ Anonymous client connection
   - ✅ Service role client connection

3. **Operations Test:**
   - ✅ `record_video()` - Insert video record
   - ✅ `record_metrics()` - Insert metrics
   - ✅ `record_feedback()` - Insert feedback
   - ✅ `get_user_history()` - Query user history

## Expected Response

**Success:**
```json
{
  "timestamp": "2025-01-11T...",
  "config_check": {
    "supabase_url_set": true,
    "anon_key_set": true,
    "service_key_set": true
  },
  "connection_test": {
    "anon_client": "✅ Connected",
    "service_client": "✅ Connected"
  },
  "operations_test": {
    "record_video": "✅ Success (video_id: ...)",
    "record_metrics": "✅ Success (metric_ids: [...])",
    "record_feedback": "✅ Success",
    "get_user_history": "✅ Success (found X records)"
  },
  "status": "success"
}
```

**Error (Missing Config):**
```json
{
  "status": "error",
  "error": "Missing environment variables. Check backend/.env file"
}
```

## Troubleshooting

### Error: "Missing environment variables"
**Solution:** Create `SHOOTRZ/backend/.env`:
```env
SUPABASE_URL=https://apbtuxchrymgmjbjxltm.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Then restart the server.

### Error: "Connection failed"
**Possible causes:**
1. Wrong Supabase URL
2. Invalid API keys
3. Network/firewall blocking Supabase
4. Supabase project is paused or deleted

**Check:** Go to https://supabase.com/dashboard and verify your project is active.

### Error: "Table does not exist"
**Solution:** Run the schema SQL in Supabase:
1. Go to Supabase Dashboard → SQL Editor
2. Run `supabase/schema.sql`

## Manual Verification

**1. Check Supabase Dashboard:**
- Go to: https://supabase.com/dashboard/project/apbtuxchrymgmjbjxltm
- Database → Table Editor
- Verify tables exist: `videos`, `metrics`, `feedback`, `users`

**2. Check Test Data:**
After running `/db/test`, check:
- `videos` table should have test record
- `metrics` table should have test metric
- `feedback` table should have test feedback

**3. Query Directly:**
```sql
-- In Supabase SQL Editor
SELECT * FROM videos ORDER BY created_at DESC LIMIT 5;
SELECT * FROM metrics ORDER BY created_at DESC LIMIT 5;
SELECT * FROM feedback ORDER BY created_at DESC LIMIT 5;
```

## Integration Test

Test the full flow:
```powershell
# 1. Analyze endpoint (creates video record)
$analyze = Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST `
  -Body (@{user_id="test-user"; file_url="https://example.com/test.mp4"} | ConvertTo-Json) `
  -ContentType "application/json"

# 2. Get history (queries database)
Invoke-RestMethod -Uri "http://127.0.0.1:8000/history/test-user" -Method GET
```

## Summary

✅ **Database working if:**
- `/db/test` returns `"status": "success"`
- All operations show ✅
- You can query data in Supabase Dashboard

❌ **Database NOT working if:**
- Missing env variables
- Connection errors
- Table not found errors






