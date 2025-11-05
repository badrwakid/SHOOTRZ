# Google Sign-In Troubleshooting Guide

## Common Issues & Fixes

### Issue 1: Button Does Nothing / No Response

**Possible Causes:**
1. Google OAuth not configured in Supabase
2. Missing Client ID/Secret
3. Redirect URL mismatch

**Fixes:**
1. **Verify Google OAuth is enabled in Supabase:**
   - Go to: Supabase Dashboard → Authentication → Providers → Google
   - Ensure "Enable Sign in with Google" is ON
   - Verify Client ID and Client Secret are filled in

2. **Check redirect URLs:**
   - In Supabase: Settings → Authentication → URL Configuration
   - Add: `shootrz://auth/callback`
   - In Google Console: Verify redirect URI matches Supabase callback URL

3. **Check console for errors:**
   - Look for errors in Metro bundler or device logs
   - Common errors: "redirect_uri_mismatch", "invalid_client"

### Issue 2: Browser Opens But Doesn't Redirect Back

**Possible Causes:**
1. Deep link not configured
2. Redirect URL not in allowed list
3. App not handling deep link

**Fixes:**
1. **Verify deep link scheme in app.json:**
   ```json
   {
     "expo": {
       "scheme": "shootrz"
     }
   }
   ```

2. **Check redirect URLs in Supabase:**
   - Settings → Authentication → URL Configuration
   - Must include: `shootrz://auth/callback`

3. **Verify deep link handling:**
   - Check `App.tsx` has `useDeepLinks` hook
   - Check `src/hooks/useDeepLinks.ts` exists

### Issue 3: "Redirect URI Mismatch" Error

**Fix:**
1. In Google Cloud Console:
   - APIs & Services → Credentials → Your OAuth Client
   - Add this exact URL to "Authorized redirect URIs":
     ```
     https://anhtuvshumamihivitm.supabase.co/auth/v1/callback
     ```
   - Note: Use your actual Supabase project URL

2. Wait 5-10 minutes after updating (Google caches)

### Issue 4: "Invalid Client" Error

**Fix:**
1. Verify Client ID in Supabase matches Google Console
2. Verify Client Secret is correct
3. Check credentials are not expired or deleted

### Issue 5: Works on Web But Not Mobile

**Possible Causes:**
1. Mobile app needs special handling
2. Deep links not configured properly
3. Expo development build needed

**Fixes:**
1. **For Expo Go (development):**
   - Use `exp://localhost:8081` as redirect URL
   - Or use Expo's URL scheme

2. **For Production/Development Build:**
   - Deep link scheme must match: `shootrz://`
   - Verify `app.json` has scheme configured

3. **Test deep links manually:**
   ```bash
   # iOS Simulator
   xcrun simctl openurl booted "shootrz://auth/callback?token=test"
   
   # Android
   adb shell am start -W -a android.intent.action.VIEW -d "shootrz://auth/callback?token=test"
   ```

## Step-by-Step Debugging

### 1. Check Console Logs

```typescript
// In LoginScreen.tsx, handleGoogleSignIn should log:
console.log('🔐 Starting Google Sign-In...');
```

**If no logs:**
- Button handler not called
- Check button `onPress` prop
- Check if button is disabled

**If error logs:**
- Check error message
- Verify Supabase configuration
- Check network connection

### 2. Verify Supabase Configuration

**Run in Supabase SQL Editor:**
```sql
-- Check if auth is enabled
SELECT * FROM auth.config;
```

**In Supabase Dashboard:**
1. Authentication → Providers → Google
2. Verify toggle is ON
3. Verify Client ID format: `xxxxx.apps.googleusercontent.com`
4. Verify Client Secret starts with: `GOCSPX-`

### 3. Test OAuth Flow Manually

**Step 1:** Test Supabase OAuth endpoint directly:
```
https://anhtuvshumamihivitm.supabase.co/auth/v1/authorize?provider=google
```

**Should redirect to Google login**

**Step 2:** After Google login, should redirect to:
```
https://anhtuvshumamihivitm.supabase.co/auth/v1/callback?code=...
```

### 4. Check Code Implementation

**Verify AuthContext has:**
```typescript
const signInWithGoogle = async () => {
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: 'shootrz://auth/callback',
    },
  });
};
```

**Verify LoginScreen calls it:**
```typescript
const result = await signInWithGoogle();
```

## Quick Fix Checklist

- [ ] Google OAuth enabled in Supabase
- [ ] Client ID and Secret configured
- [ ] Redirect URL in Google Console matches Supabase callback
- [ ] Deep link scheme in `app.json`: `"scheme": "shootrz"`
- [ ] Redirect URLs in Supabase include: `shootrz://auth/callback`
- [ ] `useDeepLinks` hook in `App.tsx`
- [ ] No errors in console
- [ ] Network connection active
- [ ] App rebuilt after config changes

## Testing

### Test 1: Check Button Works
```typescript
// Add to handleGoogleSignIn:
console.log('Button clicked');
setLoading(true);
```

### Test 2: Check OAuth Initiated
```typescript
// Check if signInWithOAuth is called
const result = await signInWithGoogle();
console.log('Result:', result);
```

### Test 3: Check Browser Opens
- Should see browser open with Google login
- If not, OAuth not initiating

### Test 4: Check Deep Link Received
```typescript
// In useDeepLinks hook:
console.log('🔗 Processing deep link:', url);
```

## Still Not Working?

1. **Check Supabase logs:**
   - Dashboard → Logs → Auth Logs
   - Look for OAuth errors

2. **Check Google Console:**
   - APIs & Services → Credentials
   - Verify OAuth client is active
   - Check quota/limits

3. **Test with Postman/curl:**
   ```bash
   curl "https://anhtuvshumamihivitm.supabase.co/auth/v1/authorize?provider=google"
   ```

4. **Verify environment variables:**
   ```typescript
   console.log('Supabase URL:', process.env.EXPO_PUBLIC_SUPABASE_URL);
   console.log('Anon Key:', process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY?.substring(0, 20));
   ```

5. **Clear cache and rebuild:**
   ```bash
   npx expo start --clear
   ```






