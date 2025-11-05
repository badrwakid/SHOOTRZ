@echo off
echo ============================================================
echo SHOOTRZ AI Backend Server - Network Mode
echo ============================================================
echo.
echo Starting backend on ALL network interfaces (0.0.0.0:8000)
echo This allows connections from your iPhone at 192.168.1.4
echo.
cd /d "%~dp0backend"
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
pause



