# FORCE RESTART BACKEND - This will completely kill and restart the server
Write-Host "`n🔄 FORCE RESTARTING SHOOTRZ BACKEND`n" -ForegroundColor Red
Write-Host "=" * 60 -ForegroundColor Gray

# Step 1: Kill ALL Python processes
Write-Host "`n[STEP 1] Killing all Python processes..." -ForegroundColor Yellow
$pythonProcs = Get-Process | Where-Object { $_.ProcessName -eq "python" -or $_.ProcessName -eq "pythonw" }
if ($pythonProcs) {
    Write-Host "   Found $($pythonProcs.Count) Python process(es)" -ForegroundColor Yellow
    $pythonProcs | ForEach-Object {
        Write-Host "   Killing PID $($_.Id)..." -ForegroundColor Gray
        Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
    }
    Start-Sleep -Seconds 3
    Write-Host "   ✅ All Python processes killed" -ForegroundColor Green
} else {
    Write-Host "   No Python processes running" -ForegroundColor Gray
}

# Step 2: Clear ALL Python cache
Write-Host "`n[STEP 2] Clearing Python cache..." -ForegroundColor Yellow
$cacheCount = 0
Get-ChildItem -Path "SHOOTRZ" -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    $cacheCount++
}
Get-ChildItem -Path "SHOOTRZ" -Recurse -Filter "*.pyc" -ErrorAction SilentlyContinue | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
    $cacheCount++
}
if ($cacheCount -gt 0) {
    Write-Host "   ✅ Cleared $cacheCount cache items" -ForegroundColor Green
} else {
    Write-Host "   No cache found" -ForegroundColor Gray
}

# Step 3: Verify code
Write-Host "`n[STEP 3] Verifying code..." -ForegroundColor Yellow
cd D:\myprojects\Grad
python SHOOTRZ\backend\diagnose_health.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Code verification passed" -ForegroundColor Green
} else {
    Write-Host "   ❌ Code verification failed!" -ForegroundColor Red
    exit 1
}

# Step 4: Instructions
Write-Host "`n[STEP 4] Ready to start server" -ForegroundColor Yellow
Write-Host "`n" + ("=" * 60) -ForegroundColor Gray
Write-Host "✅ All processes killed and cache cleared" -ForegroundColor Green
Write-Host "`n📋 NEXT: Start the server in a NEW terminal window:" -ForegroundColor Cyan
Write-Host "`n   cd D:\myprojects\Grad" -ForegroundColor White
Write-Host "   uvicorn SHOOTRZ.backend.main:app --reload`n" -ForegroundColor White
Write-Host "Then test with:" -ForegroundColor Cyan
Write-Host "   Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -Method GET`n" -ForegroundColor White
Write-Host "=" * 60 -ForegroundColor Gray






