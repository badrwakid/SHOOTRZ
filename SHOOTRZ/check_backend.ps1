Write-Host "🔍 Backend Diagnostics`n" -ForegroundColor Cyan

# Check if server is running
Write-Host "[1/3] Checking if server is running..." -ForegroundColor Yellow
try {
    $docs = Invoke-WebRequest -Uri "http://127.0.0.1:8000/docs" -TimeoutSec 2 -ErrorAction Stop
    Write-Host "✅ Server is running on port 8000`n" -ForegroundColor Green
} catch {
    Write-Host "❌ Server is NOT running!`n" -ForegroundColor Red
    Write-Host "   Start it with: uvicorn SHOOTRZ.backend.main:app --reload`n" -ForegroundColor Yellow
    exit 1
}

# Check available endpoints
Write-Host "[2/3] Checking available endpoints..." -ForegroundColor Yellow
try {
    $api = Invoke-RestMethod -Uri "http://127.0.0.1:8000/openapi.json" -ErrorAction Stop
    $endpoints = $api.paths.PSObject.Properties.Name
    Write-Host "✅ Found $($endpoints.Count) endpoints:" -ForegroundColor Green
    $endpoints | ForEach-Object { Write-Host "   $_" -ForegroundColor Cyan }
    
    if ($endpoints -contains "/health") {
        Write-Host "`n✅ /health endpoint is registered!`n" -ForegroundColor Green
    } else {
        Write-Host "`n⚠️  /health endpoint is NOT in OpenAPI schema" -ForegroundColor Yellow
        Write-Host "   But it might still work - testing..." -ForegroundColor Yellow
    }
    Write-Host ""
} catch {
    Write-Host "❌ Could not fetch API schema: $_`n" -ForegroundColor Red
}

# Test health endpoint
Write-Host "[3/3] Testing /health endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET -ErrorAction Stop
    Write-Host "✅ /health endpoint WORKS!`n" -ForegroundColor Green
    Write-Host "   Status: $($health.status)" -ForegroundColor Cyan
    Write-Host "   Service: $($health.service)" -ForegroundColor Cyan
    Write-Host "   Version: $($health.version)" -ForegroundColor Cyan
    Write-Host "   Uptime: $($health.uptime)s`n" -ForegroundColor Cyan
} catch {
    Write-Host "❌ /health endpoint returned 404`n" -ForegroundColor Red
    Write-Host "   SOLUTION: Restart the uvicorn server" -ForegroundColor Yellow
    Write-Host "   1. Press CTRL+C in the uvicorn terminal" -ForegroundColor White
    Write-Host "   2. Run: uvicorn SHOOTRZ.backend.main:app --reload`n" -ForegroundColor White
}

Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "   - If /health works: Start frontend with 'npx expo start'" -ForegroundColor White
Write-Host "   - If /health fails: Restart backend server`n" -ForegroundColor White






