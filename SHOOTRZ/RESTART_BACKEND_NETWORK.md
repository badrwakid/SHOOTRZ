# ⚠️ CRITICAL: Restart Backend for Network Access

## Current Problem
Your backend is running on `127.0.0.1:8000` (localhost only), which is **NOT accessible from your iPhone**.

Current status:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

## Solution

### Step 1: Stop Current Backend
In the terminal where uvicorn is running, press:
```
CTRL + C
```

### Step 2: Restart with Network Access

**Option A: Using the correct command**
```bash
cd D:\myprojects\Grad\SHOOTRZ\backend
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

**Option B: If you're using the uvicorn command from root**
```bash
uvicorn SHOOTRZ.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 3: Verify

After restarting, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

NOT `http://127.0.0.1:8000`!

### Step 4: Test Connection

1. Open Safari on your iPhone
2. Go to: `http://192.168.1.4:8000/health`
3. You should see: `{"status":"healthy",...}`

If this works, your app should connect!

## Quick PowerShell Command

Run this in PowerShell:
```powershell
cd D:\myprojects\Grad\SHOOTRZ\backend
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

## What's the Difference?

- `--host 127.0.0.1` = Only accessible from this computer (simulator/emulator)
- `--host 0.0.0.0` = Accessible from ANY device on your network (physical iPhone/Android)

Your iPhone at `192.168.1.4` needs `0.0.0.0` to connect!



