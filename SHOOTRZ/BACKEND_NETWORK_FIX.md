# Backend Network Connection Fix

## Problem
The backend is running on `127.0.0.1:8000` (localhost only), which means it's **not accessible from your physical iPhone**.

The netstat output shows:
```
TCP    127.0.0.1:8000         0.0.0.0:0              LISTENING
```

This means the server is only accepting connections from `127.0.0.1` (localhost), not from other devices on your network (like `192.168.1.4`).

## Solution

### Option 1: Restart Backend with `--host 0.0.0.0` (Recommended)

**Stop your current backend** (Ctrl+C in the terminal running uvicorn), then restart it with:

```bash
cd SHOOTRZ/backend
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

The `--host 0.0.0.0` makes the server accept connections from **all network interfaces**, including your local network IP.

### Option 2: Use Your Computer's IP Explicitly

If you know your computer's IP is `192.168.1.4`, you can also use:

```bash
python -m uvicorn main:create_app --factory --reload --host 192.168.1.4 --port 8000
```

But `0.0.0.0` is recommended as it works for all network interfaces.

## Verify It's Working

After restarting with `--host 0.0.0.0`, check:

```powershell
netstat -an | findstr :8000
```

You should see:
```
TCP    0.0.0.0:8000         0.0.0.0:0              LISTENING
```

Or:
```
TCP    [::]:8000            [::]:0                 LISTENING
```

This means the server is listening on **all interfaces** and can accept connections from any device on your network.

## Test Connection from Phone

1. Open Safari on your iPhone
2. Navigate to: `http://192.168.1.4:8000/health`
3. You should see: `{"status":"healthy","service":"SHOOTRZ FastAPI Backend",...}`

If this works, the app should also work!

## Firewall Check

If it still doesn't work after binding to `0.0.0.0`:

1. **Windows Firewall**: May be blocking port 8000
   - Go to: Windows Security → Firewall & network protection → Advanced settings
   - Click "Inbound Rules" → "New Rule"
   - Port → TCP → 8000 → Allow

2. **Check if backend is accessible**:
   - On your computer's browser: `http://127.0.0.1:8000/health` ✅ Should work
   - On your phone's browser: `http://192.168.1.4:8000/health` ✅ Should work after fix

## Quick Fix Script

Create `SHOOTRZ/start_backend_network.bat`:

```batch
@echo off
cd /d "%~dp0backend"
echo Starting backend on all network interfaces...
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
pause
```

Then run this script instead of the default start command.



