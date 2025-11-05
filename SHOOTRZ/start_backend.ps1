# Start FastAPI Backend
# This script ensures you're in the correct directory

Write-Host "🚀 Starting SHOOTRZ Backend..." -ForegroundColor Cyan

# Change to project root (where SHOOTRZ is a directory)
$projectRoot = Split-Path -Parent $PSScriptRoot
if ($PWD.Path -ne $projectRoot) {
    Write-Host "Changing to project root: $projectRoot" -ForegroundColor Yellow
    Set-Location $projectRoot
}

# Check if .env exists
if (-not (Test-Path "SHOOTRZ\backend\.env")) {
    Write-Host "⚠️  Warning: backend/.env not found!" -ForegroundColor Yellow
    Write-Host "Run .\setup_env.ps1 first to create environment variables." -ForegroundColor Yellow
}

Write-Host "`nStarting uvicorn on http://127.0.0.1:8000`n" -ForegroundColor Green
Write-Host "Press CTRL+C to stop`n" -ForegroundColor Gray

# Start uvicorn
uvicorn SHOOTRZ.backend.main:app --reload






