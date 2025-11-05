# Frontend Connection Fix

## Problem Found ✅

There were **TWO** service files with hardcoded API URLs:

1. `src/services/api.service.ts` - ✅ Fixed to use environment variables
2. `src/services/fastapi.service.ts` - ✅ Fixed to use environment variables

The `fastapi.service.ts` was hardcoded to `http://127.0.0.1:8000`, which doesn't work on physical devices.

## Solution Applied

### 1. Updated `fastapi.service.ts`
- Now reads from `EXPO_PUBLIC_API_URL` environment variable
- Falls back to `http://127.0.0.1:8000` only if env var not set
- Added debug logging

### 2. Updated `api.service.ts`
- Added debug logging to show which URL is being used
- Enhanced error logging for health checks

### 3. Updated `app.config.js`
- Now passes environment variables to Expo config

## Next Steps

### Create `.env` File

Create `SHOOTRZ/.env`:

```env
EXPO_PUBLIC_API_URL=http://192.168.1.4:8000
```

Replace `192.168.1.4` with your computer's actual IP address.

### Restart Expo

After creating `.env` file:

1. Stop Expo (Ctrl+C)
2. Restart: `npx expo start --clear`

### Verify

After restarting, check the logs. You should see:
```
🔗 API Base URL: http://192.168.1.4:8000
🔗 FastAPI Service Base URL: http://192.168.1.4:8000
🔗 Environment variable EXPO_PUBLIC_API_URL: http://192.168.1.4:8000
```

And when the health check runs:
```
🏥 Health check: GET http://192.168.1.4:8000/health
✅ Health check response: { status: "healthy", ... }
```

## For Different Devices

### iOS Simulator
Keep `EXPO_PUBLIC_API_URL` unset or use `http://127.0.0.1:8000`

### Android Emulator
Use: `EXPO_PUBLIC_API_URL=http://10.0.2.2:8000`

### Physical Device
Use your computer's IP: `EXPO_PUBLIC_API_URL=http://YOUR_IP:8000`

To find your IP:
- Windows: `ipconfig` → Look for "IPv4 Address"
- Mac/Linux: `ifconfig` or `ip addr`

## Debug Information

Both services now log:
- Which API URL they're using
- Whether environment variable is set
- Detailed error information if health check fails

Check the Expo logs to see what URL is being used!



