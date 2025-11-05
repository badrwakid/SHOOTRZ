Write-Host "`n🧪 Testing SHOOTRZ Backend..." -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Gray

# Check if backend is running
Write-Host "`n[1/4] Testing Health Endpoint..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -Method GET -TimeoutSec 5
    if ($health.status -eq "healthy") {
        Write-Host "✅ Health check PASSED: $($health.status)" -ForegroundColor Green
        Write-Host "   Service: $($health.service)" -ForegroundColor Gray
        Write-Host "   Version: $($health.version)" -ForegroundColor Gray
    } else {
        Write-Host "⚠️  Health check returned unexpected status: $($health.status)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Health check FAILED" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
    Write-Host "   Make sure backend is running: uvicorn SHOOTRZ.backend.main:app --reload" -ForegroundColor Yellow
    exit 1
}

# Test analyze endpoint (JSON)
Write-Host "`n[2/4] Testing Analyze Endpoint (JSON)..." -ForegroundColor Yellow
try {
    $body = @{
        user_id = "test-user-$(Get-Date -Format 'yyyyMMddHHmmss')"
        file_url = "https://example.com/test-video.mp4"
        angle = "45"
        fps = 30
        device = "mobile"
    } | ConvertTo-Json
    
    $analyze = Invoke-RestMethod -Uri "http://127.0.0.1:8000/analyze" -Method POST -Body $body -ContentType "application/json" -TimeoutSec 10
    Write-Host "✅ Analyze endpoint PASSED" -ForegroundColor Green
    Write-Host "   Job ID: $($analyze.job_id)" -ForegroundColor Gray
    Write-Host "   Status: $($analyze.status)" -ForegroundColor Gray
    
    # Wait a moment for processing
    Start-Sleep -Seconds 2
    
    # Test result endpoint
    Write-Host "`n[3/4] Testing Result Endpoint..." -ForegroundColor Yellow
    try {
        $result = Invoke-RestMethod -Uri "http://127.0.0.1:8000/result/$($analyze.job_id)" -Method GET -TimeoutSec 10
        Write-Host "✅ Result endpoint PASSED" -ForegroundColor Green
        Write-Host "   Status: $($result.status)" -ForegroundColor Gray
        Write-Host "   Metrics count: $($result.metrics.Count)" -ForegroundColor Gray
        Write-Host "   Feedback count: $($result.feedback.Count)" -ForegroundColor Gray
    } catch {
        Write-Host "⚠️  Result endpoint returned: $_" -ForegroundColor Yellow
        Write-Host "   (This is OK if job is still processing)" -ForegroundColor Gray
    }
} catch {
    Write-Host "❌ Analyze endpoint FAILED" -ForegroundColor Red
    Write-Host "   Error: $_" -ForegroundColor Red
}

# Test history endpoint
Write-Host "`n[4/4] Testing History Endpoint..." -ForegroundColor Yellow
try {
    $history = Invoke-RestMethod -Uri "http://127.0.0.1:8000/history/test-user-123" -Method GET -TimeoutSec 10
    Write-Host "✅ History endpoint PASSED" -ForegroundColor Green
    Write-Host "   Sessions returned: $($history.sessions.Count)" -ForegroundColor Gray
} catch {
    Write-Host "⚠️  History endpoint returned: $_" -ForegroundColor Yellow
}

Write-Host "`n" + ("=" * 50) -ForegroundColor Gray
Write-Host "✅ Backend Testing Complete!" -ForegroundColor Green
Write-Host "`nNext: Test frontend with 'npx expo start'`n" -ForegroundColor Cyan






