# Fix: "Could not connect to the server" Deep Link Error

## The Problem

After Google OAuth, you see this error:
```
Unknown error: Could not connect to the server
exp://localhost:8081?
code=cdc14c4d-8c4b-45d0-9075-34936e178de7
```

## The Cause

The redirect URL is using `localhost` instead of your computer's actual IP address. When testing on a **physical device**, `localhost` refers to the phone itself, not your computer running Metro bundler.

## The Solution

### Option 1: Update IP Address in Code (Quick Fix)

1. **Find your computer's IP address:**
   ```powershell
   # Windows
   ipconfig
   
   # Look for "IPv4 Address" under your active network adapter
   # Example: 192.168.56.1 (or 192.168.1.x)
   ```

2. **Update the code:**
   - Open: `SHOOTRZ/src/context/AuthContext.tsx`
   - Line ~421: Update the IP address:
   ```typescript
   const redirectTo = __DEV__ 
     ? 'exp://YOUR_IP_HERE:8081/--/auth/callback' // Replace YOUR_IP_HERE
     : 'shootrz://auth/callback';
   ```

3. **IMPORTANT: Google Cloud Console DOES NOT accept exp:// URLs!**
   - Go to: Google Cloud Console → APIs & Services → Credentials
   - Click your OAuth Client ID
   - Under "Authorized redirect URIs", **ONLY have this:**
     ```
     https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
     ```
   - **DO NOT add the exp:// URL** - Google rejects custom URL schemes!
   - Click **Save**

4. **Update in Supabase Dashboard (this is where exp:// URLs go):**
   - Supabase Dashboard → Settings → Authentication → URL Configuration
   - Under "Redirect URLs", add:
     ```
     exp://YOUR_IP_HERE:8081/--/auth/callback
     ```
   - Also keep the default Supabase callback URL
   - Click **Save**

### Option 2: Use Expo's Built-in IP Detection (Better)

Install `expo-constants` to get the development server URL dynamically:

```typescript
import Constants from 'expo-constants';

const redirectTo = __DEV__ 
  ? `${Constants.expoConfig?.hostUri?.split(':')[0] ? `exp://${Constants.expoConfig.hostUri.split(':')[0]}:8081/--/auth/callback` : 'exp://192.168.56.1:8081/--/auth/callback'}`
  : 'shootrz://auth/callback';
```

### Option 3: Use LAN URL from Expo (Best)

When you run `npx expo start`, Expo shows the LAN URL. Use that:

```bash
# Expo will show something like:
# Metro waiting on exp://192.168.56.1:8081
```

Copy that exact URL and use it in the redirect URL.

## Important Notes

1. **Metro Bundler Must Be Running:**
   - Make sure you have `npx expo start` running
   - The app needs to connect to Metro on port 8081

2. **Same Wi-Fi Network:**
   - Your computer and phone must be on the **same Wi-Fi network**
   - Mobile data won't work - must use Wi-Fi

3. **Firewall:**
   - Windows Firewall might block port 8081
   - Allow Expo/Metro through firewall if needed

4. **IP Can Change:**
   - If your IP changes (e.g., reconnect to Wi-Fi), update the redirect URL again
   - Consider using Option 2 or 3 for dynamic IP

## Quick Checklist

- [ ] Metro bundler is running (`npx expo start`)
- [ ] Computer and phone on same Wi-Fi
- [ ] Updated IP in `AuthContext.tsx` (line ~421)
- [ ] Updated IP in Google Cloud Console redirect URIs
- [ ] Saved changes and restarted app

## Your Current IP

From `ipconfig`, your IP is: **192.168.56.1**

Update the code to:
```typescript
'exp://192.168.56.1:8081/--/auth/callback'
```

