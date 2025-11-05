# iOS Deep Link Setup - Fix "Invalid Address" Error

## The Problem

After completing Google OAuth, Safari shows: **"Safari cannot open the page because the address is invalid"**

This happens because iOS doesn't recognize `shootrz://` as a valid URL scheme for your app.

## The Solution

### Option 1: Rebuild App with Deep Link Config (Recommended for Production)

I've already added the iOS configuration to `app.json`. Now you need to rebuild:

**Steps:**
1. Stop Metro bundler (Ctrl+C)
2. Delete the app from your iOS simulator/device
3. Rebuild the app:
   ```bash
   cd SHOOTRZ
   npx expo run:ios --clear
   ```

**Why rebuild is needed:**
- iOS deep link configuration (`CFBundleURLSchemes`) is compiled into the app binary
- It's in `Info.plist`, which is generated during build
- Hot reload won't update this - full rebuild required

### Option 2: Use Expo Go with exp:// Scheme (Easier for Development)

If you're using Expo Go for development, use `exp://` scheme instead:

1. Update Supabase redirect URL to use `exp://`:
   - In Supabase Dashboard → Settings → Authentication → URL Configuration
   - Add redirect URL: `exp://192.168.1.4:8081/--/auth/callback`
   - Or use: `exp://localhost:8081/--/auth/callback`

2. Update code to use `exp://` for development:
   ```typescript
   const redirectTo = __DEV__ 
     ? 'exp://192.168.1.4:8081/--/auth/callback'
     : 'shootrz://auth/callback';
   ```

**Note:** This is only for development with Expo Go. Production should use `shootrz://`.

## What I've Already Configured

In `app.json`, I added:
- ✅ iOS `CFBundleURLSchemes: ["shootrz"]`
- ✅ Android intent filters for `shootrz://`
- ✅ Deep link scheme: `"scheme": "shootrz"`

## Verification

After rebuilding, test if deep links work:

**Test manually:**
```bash
# iOS Simulator
xcrun simctl openurl booted "shootrz://auth/callback?code=test123"
```

If the app opens, deep links are configured correctly!

## Alternative: Use Supabase's Built-in Redirect

Instead of custom deep links, you could use Supabase's built-in redirect handling:

1. Set redirect to Supabase callback:
   ```typescript
   redirectTo: 'https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback'
   ```

2. Supabase will show a success page
3. User manually returns to app

This works but is less seamless than deep links.

## Recommended Approach

**For Development:**
- Use Expo Go with `exp://` scheme
- No rebuild needed
- Faster iteration

**For Production:**
- Rebuild with `shootrz://` scheme
- Better user experience
- Professional deep link handling

## Current Status

✅ iOS deep link config added to `app.json`
✅ Android deep link config added
✅ OAuth callback parsing improved
⚠️ **App needs rebuild for iOS deep links to work**

After rebuild, the "invalid address" error should be resolved!






