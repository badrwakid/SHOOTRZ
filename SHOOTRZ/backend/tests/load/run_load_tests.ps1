$ErrorActionPreference = "Stop"

$HostUrl = if ($env:SHOOTRZ_HOST) { $env:SHOOTRZ_HOST } else { "http://127.0.0.1:8000" }
$OutDir = if ($env:OUT_DIR) { $env:OUT_DIR } else { "backend/outputs/load" }
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

$env:SHOOTRZ_DISABLE_RATE_LIMIT = "1"

Write-Host "[1/3] Starting backend (4 workers)..."
$server = Start-Process -FilePath python -ArgumentList "-m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 4" -PassThru
try {
    Write-Host "[2/3] Waiting for /health..."
    $ready = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            Invoke-WebRequest -Uri "$HostUrl/health" -UseBasicParsing | Out-Null
            $ready = $true
            break
        } catch {
            Start-Sleep -Seconds 1
        }
    }
    if (-not $ready) {
        throw "Backend did not become healthy in time."
    }

    Write-Host "[3/3] Running Locust scenarios..."
    $env:LOCUST_REPORT_PATH = "$OutDir/load_report_50u.json"
    locust -f backend/tests/load/locustfile.py --headless -u 50 -r 5 -t 60s --host $HostUrl --csv "$OutDir/50u" --logfile "$OutDir/50u.log"

    $env:LOCUST_REPORT_PATH = "$OutDir/load_report_100u.json"
    locust -f backend/tests/load/locustfile.py --headless -u 100 -r 10 -t 60s --host $HostUrl --csv "$OutDir/100u" --logfile "$OutDir/100u.log"

    Write-Host "Load reports written to $OutDir"
}
finally {
    if ($server -and -not $server.HasExited) {
        Stop-Process -Id $server.Id -Force
    }
}
