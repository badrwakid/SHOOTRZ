@echo off
echo ============================================================
echo SHOOTRZ AI Backend Server
echo ============================================================
echo.
cd /d "%~dp0"
echo Starting FastAPI server from: %CD%
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause


