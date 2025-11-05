# Fix: Google OAuth Error 400 - redirect_uri_mismatch

## The Problem

Google is blocking the sign-in because the redirect URI doesn't match what's configured in Google Cloud Console.

## The Solution

### Step 1: Find Your Exact Supabase Callback URL

From your Supabase Dashboard (API Settings), your Project URL is:
```
https://apbtuxchrymgmjbjxltm.supabase.co
```

The redirect URI must be exactly:
```
https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
```

**Important:** 
- Use your actual Supabase project URL (check in Supabase Dashboard → Settings → API)
- The URL must be **exactly** this format
- No trailing slashes
- Must be `https://` (not `http://`)

### Step 2: Add Redirect URI in Google Cloud Console

1. Go to: https://console.cloud.google.com/
2. Select your project (or create one)
3. Navigate to: **APIs & Services → Credentials**
4. Find your OAuth 2.0 Client ID (the one you created for SHOOTRZ)
5. Click on it to edit
6. In **"Authorized redirect URIs"**, add:
   ```
   https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
   ```
7. **Important:** Make sure there are NO other characters:
   - No spaces before/after
   - No trailing slash
   - Copy-paste exactly as shown above (replace with your actual Supabase URL if different)
8. Click **"Save"**

### Step 3: Verify in Supabase

1. Go to: Supabase Dashboard → Settings → Authentication → URL Configuration
2. **Site URL** should be your app URL (doesn't affect OAuth redirect)
3. **Redirect URLs** should include:
   ```
   shootrz://auth/callback
   ```
   (This is for the app deep link, not the Google redirect)

### Step 4: Wait and Test

1. **Wait 5-10 minutes** after saving in Google Console (Google caches redirect URIs)
2. Try Google Sign-In again
3. Should work now!

## Common Mistakes

### ❌ Wrong Redirect URI Format
```
https://anhtuvshumamihivitm.supabase.co/auth/v1/callback/  ← Extra slash
http://anhtuvshumamihivitm.supabase.co/auth/v1/callback    ← Wrong protocol
https://supabase.co/auth/v1/callback                       ← Wrong domain
```

### ✅ Correct Format
```
https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
```

### ❌ Adding App Deep Link to Google Console
Don't add `shootrz://auth/callback` to Google Console redirect URIs.
- Google Console needs: `https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback`
- Supabase redirect URLs needs: `shootrz://auth/callback`

These are different - Google redirects to Supabase, Supabase redirects to app.

## How OAuth Flow Works

```
1. User taps "Sign in with Google"
   ↓
2. App → Supabase → Google (with redirect_uri: https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback)
   ↓
3. Google validates redirect_uri matches what's in Google Console
   ↓
4. User signs in with Google
   ↓
5. Google redirects back to: https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback?code=...
   ↓
6. Supabase exchanges code for session
   ↓
7. Supabase redirects to app: shootrz://auth/callback?code=...
   ↓
8. App exchanges code for final session
   ↓
9. User logged in ✅
```

## Quick Verification Checklist

- [ ] Google Cloud Console → Credentials → OAuth Client ID
- [ ] "Authorized redirect URIs" contains: `https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback`
- [ ] Exact match (no typos, no extra characters)
- [ ] Saved in Google Console
- [ ] Waited 5-10 minutes after saving
- [ ] Supabase redirect URLs includes: `shootrz://auth/callback`

## Still Not Working?

1. **Double-check the exact URL:**
   - Go to Supabase Dashboard → Settings → API
   - Copy the "Project URL"
   - Append `/auth/v1/callback`
   - Use that exact URL in Google Console

2. **Check for typos:**
   - Compare character-by-character
   - Check for extra spaces
   - Verify protocol is `https://`

3. **Try creating a new OAuth Client ID:**
   - Sometimes creating fresh helps
   - Make sure to add the redirect URI immediately

4. **Check Google Console logs:**
   - APIs & Services → OAuth consent screen
   - Look for error details

## Your Supabase Project URL

To find your exact Supabase callback URL:
1. Supabase Dashboard → Settings → API
2. Project URL: `https://anhtuvshumamihivitm.supabase.co`
3. Callback URL: `https://anhtuvshumamihivitm.supabase.co/auth/v1/callback`

Use this **exact** URL in Google Cloud Console.

