# Fix: Supabase Redirecting to localhost Instead of IP

## The Problem

After Google OAuth completes, you see:
```
Unknown error: Could not connect to the server
exp://localhost:8081?
code=cdc14c4d-8c4b-45d0-9075-34936e178de7
```

This means Supabase is redirecting to `localhost` instead of your IP address (`192.168.56.1`).

## Root Cause

Supabase may be:
1. Not using the `redirectTo` parameter correctly for React Native
2. Using a default/fallback redirect URL
3. Having the redirect URL misconfigured in Supabase Dashboard

## Solutions

### Solution 1: Verify Supabase Dashboard Configuration

1. Go to: **Supabase Dashboard → Settings → Authentication → URL Configuration**
2. Under **"Redirect URLs"**, make sure you have:
   ```
   exp://192.168.56.1:8081/--/auth/callback
   ```
   (Replace with your actual IP if different)

3. **Also check "Site URL":**
   - This should be: `https://apbtuxchrymgmjbjxltm.supabase.co`
   - Or your custom domain if you have one

4. Click **"Save"**

### Solution 2: Check OAuth URL Generation

The code now logs the actual OAuth URL being generated. Check your console logs:

```
🔗 OAuth URL contains redirectTo: true/false
🔍 Actual redirect_uri in OAuth URL: [URL]
```

If `redirectTo` is false or the `redirect_uri` is wrong, Supabase isn't using your parameter correctly.

### Solution 3: Handle localhost Redirect (Workaround)

I've added code to handle the case where Supabase redirects to localhost. The deep link handler will:
1. Detect the localhost redirect
2. Extract the OAuth code from the URL
3. Exchange it for a session manually

This should work even if Supabase redirects incorrectly.

### Solution 4: Alternative - Use Supabase's Built-in Redirect

Instead of using `exp://` URLs, you could:

1. Let Supabase redirect to its default callback page
2. User manually returns to app
3. Check for session in app

But this is less seamless than deep links.

## Debugging Steps

1. **Check console logs:**
   - When you click "Sign in with Google", look for:
     - `📱 Using redirect URL: exp://192.168.56.1:8081/--/auth/callback`
     - `🔗 OAuth URL contains redirectTo: true`
     - `🔍 Actual redirect_uri in OAuth URL: [URL]`

2. **Check Supabase Dashboard:**
   - Verify redirect URLs are correctly configured
   - Make sure no conflicting redirect URLs exist

3. **Test the redirect:**
   - After Google OAuth, check what URL Supabase redirects to
   - If it's localhost, the code will handle it automatically now

## Current Implementation

The code now:
- ✅ Logs the actual redirect_uri being used
- ✅ Handles localhost redirects as a fallback
- ✅ Extracts OAuth code from localhost URLs
- ✅ Exchanges code for session even if redirect is wrong

## Expected Behavior

1. User clicks "Sign in with Google"
2. Browser opens with Google OAuth
3. User completes sign-in
4. Supabase redirects (ideally to `exp://192.168.56.1:8081/--/auth/callback`)
5. If redirect goes to localhost, code extracts the OAuth code
6. Code exchanges for session
7. User is signed in

The localhost redirect handler should work as a fallback, but ideally Supabase should redirect to the correct URL.






