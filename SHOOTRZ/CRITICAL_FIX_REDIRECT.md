# ⚠️ CRITICAL FIX: Supabase Ignoring redirectTo Parameter

## The Problem

Your logs show:
```
🔗 OAuth URL contains redirectTo: false
```

This means Supabase is **completely ignoring** your `redirectTo` parameter because it's not in the allowed redirect URLs list.

## The Fix (REQUIRED)

### Step 1: Add Redirect URL to Supabase Dashboard

1. **Go to Supabase Dashboard:**
   - https://app.supabase.com/
   - Select your project

2. **Navigate to:**
   - **Settings** (gear icon in left sidebar)
   - **Authentication**
   - **URL Configuration** tab

3. **Under "Redirect URLs" section:**
   - Click **"Add URL"** or the **"+"** button
   - Add this EXACT URL:
     ```
     exp://192.168.56.1:8081/--/auth/callback
     ```
   - **Important:** Replace `192.168.56.1` with your actual IP if different
   - Make sure there are NO trailing slashes
   - The URL must match EXACTLY (case-sensitive)

4. **Keep the default Supabase callback URL:**
   ```
   https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
   ```
   (Don't remove this one!)

5. **Click "Save"** at the bottom

### Step 2: Verify Site URL

In the same **URL Configuration** section:
- **Site URL** should be: `https://apbtuxchrymgmjbjxltm.supabase.co`
- If it's different, update it
- Click **"Save"** if you made changes

### Step 3: Restart Your App

1. Stop Metro bundler (Ctrl+C)
2. Reload the app
3. Try Google Sign-In again

### Step 4: Verify It's Fixed

After adding the redirect URL, check your logs. You should now see:
```
🔗 OAuth URL contains redirectTo: true
🔍 Actual redirect_to in Supabase URL: exp://192.168.56.1:8081/--/auth/callback
```

If you see `true`, Supabase will now redirect correctly!

## Why This Happens

Supabase has a **security feature** that validates all redirect URLs against the dashboard settings. This prevents malicious redirects.

If your `redirectTo` URL isn't in the allowed list:
- Supabase silently ignores it
- Uses default Site URL or localhost
- Causes "Could not connect to server" error

## Summary

**The `redirectTo` parameter is being ignored because Supabase doesn't recognize the URL as allowed. Add it to Supabase Dashboard → Settings → Authentication → URL Configuration.**

After adding it, Supabase will include your redirect URL in the OAuth flow, and the sign-in should work!






