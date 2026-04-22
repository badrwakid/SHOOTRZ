# Start SHOOTRZ FastAPI from the repo root. Kills anything already listening on port 8000 (Windows).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$port = 8000
# Do not use $pid — it is a reserved automatic variable (current shell PID) in PowerShell.
$listeners = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
$procIds = $listeners | ForEach-Object { $_.OwningProcess } | Where-Object { $_ -gt 0 } | Select-Object -Unique
foreach ($procId in $procIds) {
    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
        Write-Host "Stopping PID $procId on port $port..."
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Seconds 1

Write-Host "Starting uvicorn from: $root"
Write-Host "Open http://127.0.0.1:8000/health — expect version 0.2.0, api_build_id shootrz-main-2026-04-analysis-routes, has_analysis_history_route true"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port $port
