Write-Host "🔧 Setting up environment variables..." -ForegroundColor Cyan

# Create backend .env
$backendEnv = @"
SUPABASE_URL=https://apbtuxchrymgmjbjxltm.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwYnR1eGNocnltZ21qYmp4bHRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE3MTU2ODksImV4cCI6MjA3NzI5MTY4OX0.glcDi2nFYtI_4J8otd15vi2mOGcYpKeIXKpi0mBh-s4
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwYnR1eGNocnltZ21qYmp4bHRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MTcxNTY4OSwiZXhwIjoyMDc3MjkxNjg5fQ.CmFbbZLIze9mdj3DsiIFOACqjnaCZJycwoDX2uPQbpc
"@

$backendEnv | Out-File -FilePath "backend\.env" -Encoding utf8 -NoNewline
Write-Host "✅ Created backend\.env" -ForegroundColor Green

# Create frontend .env
$frontendEnv = @"
EXPO_PUBLIC_SUPABASE_URL=https://apbtuxchrymgmjbjxltm.supabase.co
EXPO_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFwYnR1eGNocnltZ21qYmp4bHRtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE3MTU2ODksImV4cCI6MjA3NzI5MTY4OX0.glcDi2nFYtI_4J8otd15vi2mOGcYpKeIXKpi0mBh-s4
"@

$frontendEnv | Out-File -FilePath ".env" -Encoding utf8 -NoNewline
Write-Host "✅ Created .env (frontend)" -ForegroundColor Green

Write-Host "`n✅ Environment setup complete!`n" -ForegroundColor Green






