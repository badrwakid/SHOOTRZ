# OAuth Flow Explanation - Why exp:// URL Can't Go in Google Cloud Console

## The Problem

Google Cloud Console **rejects** `exp://192.168.56.1:8081/--/auth/callback` as a redirect URI because:
- Google only accepts **HTTPS/HTTP URLs** for redirect URIs
- Custom schemes like `exp://` are not supported by Google OAuth

## The Correct OAuth Flow

Here's how it actually works:

```
User clicks "Sign in with Google"
    ↓
App opens browser with Google OAuth URL
    ↓
User signs in with Google
    ↓
Google redirects to: https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
    ↓
Supabase processes OAuth callback
    ↓
Supabase redirects to: exp://192.168.56.1:8081/--/auth/callback (our app deep link)
    ↓
App receives deep link and completes sign-in
```

## What Goes Where

### ✅ Google Cloud Console → Authorized Redirect URIs
**ONLY add this:**
```
https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
```

**DO NOT add** the `exp://` URL - Google doesn't support it!

### ✅ Your Code (AuthContext.tsx)
**Use the `exp://` URL here** - this tells Supabase where to redirect AFTER it processes the OAuth:
```typescript
const redirectTo = __DEV__ 
  ? 'exp://192.168.56.1:8081/--/auth/callback'
  : 'shootrz://auth/callback';
```

This `redirectTo` parameter is passed to Supabase's `signInWithOAuth`, and Supabase uses it to redirect back to your app after handling the Google OAuth callback.

### ✅ Supabase Dashboard → Authentication → URL Configuration
**Add BOTH:**
1. `https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback` (default)
2. `exp://192.168.56.1:8081/--/auth/callback` (for development)

Supabase supports custom schemes in its redirect configuration.

## Summary

- **Google Cloud Console:** Only HTTPS URLs (Supabase callback URL)
- **Supabase Dashboard:** Both HTTPS and `exp://` URLs
- **Your Code:** Use `exp://` URL for `redirectTo` parameter

This is the standard flow for React Native OAuth with Supabase!






