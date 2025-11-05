# Quick Fix: Backend Connection Issue

## Problem
Frontend shows: "Health check failed: Network Error"

## Solution

The backend is now running! ✅ But if you're using a **physical device**, you need to configure the API URL.

### Option 1: Update .env File (Recommended)

Create or update `SHOOTRZ/.env`:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.4:8000
```

Replace `192.168.1.4` with your computer's actual IP address.

**To find your IP:**
- Windows: Run `ipconfig` in PowerShell/CMD, look for "IPv4 Address"
- Mac/Linux: Run `ifconfig` or `ip addr`

### Option 2: Update api.service.ts Directly

If `.env` doesn't work, edit `SHOOTRZ/src/services/api.service.ts` line 15:

```typescript
const API_BASE_URL = __DEV__
  ? 'http://192.168.1.4:8000' // ← Change to your IP
  : 'https://api.shootrz.com';
```

### For iOS Simulator
Keep `127.0.0.1:8000` - it should work as-is.

### For Android Emulator
Use `http://10.0.2.2:8000` instead.

### Verify Backend is Running

Check: http://127.0.0.1:8000/health

You should see:
```json
{
  "status": "healthy",
  "service": "SHOOTRZ FastAPI Backend",
  "version": "1.0.0"
}
```

### After Making Changes

1. Restart Expo: Press `r` in the Expo terminal or restart with `npm start`
2. Reload the app on your device/simulator
3. Check logs - the health check should now pass

## Current Status

✅ Backend server: **RUNNING** on port 8000  
✅ Health endpoint: **WORKING**  
⚠️ Frontend connection: Needs IP configuration for physical devices



