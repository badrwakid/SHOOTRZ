@echo off
echo ============================================================
echo SHOOTRZ AI Backend Server - Network Mode
echo ============================================================
echo.
echo Starting backend on ALL network interfaces (0.0.0.0:8000)
echo This allows connections from your iPhone at 192.168.1.4
echo.
REM Change to parent directory (project root)
cd /d "%~dp0\.."
echo Current directory: %CD%
echo.
REM Verify we're in the right place
if not exist "SHOOTRZ\backend\main.py" (
    echo ERROR: Cannot find SHOOTRZ\backend\main.py
    echo Please ensure you're running from the project root directory.
    pause
    exit /b 1
)
echo.
echo Running: python -m uvicorn SHOOTRZ.backend.main:app --reload --host 0.0.0.0 --port 8000
echo.
python -m uvicorn SHOOTRZ.backend.main:app --reload --host 0.0.0.0 --port 8000
pause



