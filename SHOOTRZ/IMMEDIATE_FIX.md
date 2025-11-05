# 🚨 IMMEDIATE FIX: Restart Backend for iPhone Access

## The Problem
Your backend is running on `127.0.0.1:8000` which **only works for simulator/emulator**, not physical devices.

**Current backend output shows:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

**Your iPhone needs:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## Quick Fix Steps

### 1. Stop the Current Backend
In the terminal where you see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

Press: **`CTRL + C`** (maybe twice if needed)

### 2. Restart with Network Access

**From the Grad directory:**
```powershell
cd SHOOTRZ\backend
python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

**Or if you prefer the shorthand:**
```powershell
uvicorn SHOOTRZ.backend.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Verify Success

After restarting, you should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

NOT `127.0.0.1`!

### 4. Test from iPhone

1. Open Safari on your iPhone
2. Navigate to: `http://192.168.1.4:8000/health`
3. You should see JSON: `{"status":"healthy",...}`

**If Safari can connect, your app will too!**

## Still Not Working?

### Check Windows Firewall
If Safari still can't connect:

1. Open **Windows Security** → **Firewall & network protection**
2. Click **Advanced settings**
3. Click **Inbound Rules** → **New Rule**
4. Select **Port** → **Next**
5. **TCP** → **Specific local ports**: `8000` → **Next**
6. **Allow the connection** → **Next**
7. Check all profiles → **Next**
8. Name it: "SHOOTRZ Backend" → **Finish**

### Verify Backend is Listening Correctly

Run this in PowerShell:
```powershell
netstat -an | Select-String ":8000"
```

You should see:
```
TCP    0.0.0.0:8000         0.0.0.0:0              LISTENING
```

If you see `127.0.0.1:8000`, the server is still in localhost mode - restart it!

## Why This Happens

- `127.0.0.1` = localhost only (same computer)
- `0.0.0.0` = all network interfaces (accessible from network)
- Your iPhone is on `192.168.1.4` and needs network access!

## One-Line Command (Copy & Paste)

```powershell
cd D:\myprojects\Grad\SHOOTRZ\backend; python -m uvicorn main:create_app --factory --reload --host 0.0.0.0 --port 8000
```



