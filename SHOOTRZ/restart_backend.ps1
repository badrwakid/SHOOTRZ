# Force restart backend server
Write-Host "🔄 Force Restarting SHOOTRZ Backend...`n" -ForegroundColor Cyan

# Kill any existing uvicorn processes
Write-Host "[1/4] Checking for running uvicorn processes..." -ForegroundColor Yellow
$uvicornProcs = Get-Process | Where-Object { $_.ProcessName -like "*python*" -and $_.CommandLine -like "*uvicorn*" }
if ($uvicornProcs) {
    Write-Host "   Found $($uvicornProcs.Count) uvicorn process(es)" -ForegroundColor Yellow
    Write-Host "   Stopping processes..." -ForegroundColor Yellow
    $uvicornProcs | Stop-Process -Force
    Start-Sleep -Seconds 2
} else {
    Write-Host "   No uvicorn processes found" -ForegroundColor Gray
}

# Clear Python cache
Write-Host "`n[2/4] Clearing Python cache..." -ForegroundColor Yellow
$cacheDirs = Get-ChildItem -Path "SHOOTRZ" -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue
if ($cacheDirs) {
    $cacheDirs | Remove-Item -Recurse -Force
    Write-Host "   Cleared $($cacheDirs.Count) cache directories" -ForegroundColor Green
} else {
    Write-Host "   No cache to clear" -ForegroundColor Gray
}

# Verify code
Write-Host "`n[3/4] Verifying code..." -ForegroundColor Yellow
cd D:\myprojects\Grad\SHOOTRZ
python test_health.py
if ($LASTEXITCODE -eq 0) {
    Write-Host "   ✅ Code is correct" -ForegroundColor Green
} else {
    Write-Host "   ❌ Code verification failed!" -ForegroundColor Red
    exit 1
}

# Start server
Write-Host "`n[4/4] Starting server..." -ForegroundColor Yellow
Write-Host "   Run this command in a NEW terminal:`n" -ForegroundColor Cyan
Write-Host "   cd D:\myprojects\Grad" -ForegroundColor White
Write-Host "   uvicorn SHOOTRZ.backend.main:app --reload`n" -ForegroundColor White
Write-Host "Then test with:" -ForegroundColor Cyan
Write-Host "   Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' -Method GET`n" -ForegroundColor White






