# Google OAuth Setup Guide for SHOOTRZ

## Quick Setup Steps

### 1. Create Google Cloud Project & Credentials

1. Go to: https://console.cloud.google.com/
2. Create a new project (or select existing):
   - Click project dropdown → "New Project"
   - Name: "SHOOTRZ" (or any name)
   - Click "Create"

3. Enable Google+ API:
   - APIs & Services → Library
   - Search "Google+ API" → Click it → "Enable"

4. Configure OAuth Consent Screen (THIS CONTROLS THE APP NAME):
   - APIs & Services → OAuth consent screen
   - User Type: **External** (unless using Google Workspace)
   - **App name: `SHOOTRZ`** ← This is what users see in Google sign-in screen!
   - User support email: Your email
   - App logo: (Optional) Upload SHOOTRZ logo if available
   - Developer contact: Your email
   - Click "Save and Continue"
   - Scopes: Keep defaults (`email`, `profile`, `openid`)
   - Click "Save and Continue"
   - **Test users:** Add your email here (e.g., `BadrWakid@gmail.com`) if app is in Testing mode
   - Click "Back to Dashboard"
   
   **IMPORTANT:** The app name you enter here determines what shows in the Google OAuth screen. 
   Users will see "You're signing back in to [App Name]" - make sure it says "SHOOTRZ"!

5. Create OAuth Credentials:
   - APIs & Services → Credentials
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: **Web application**
   - Name: `SHOOTRZ Web Client`
   - Authorized redirect URIs: Add **ONLY this URL**:
     ```
     https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
     ```
     **IMPORTANT:** Google Cloud Console does NOT accept `exp://` URLs!
     The `exp://` URL goes in Supabase Dashboard instead (see step 2 below).
   - Click "Create"
   - **IMPORTANT**: Copy the Client ID and Client Secret immediately
     - Client ID: `xxxxx.apps.googleusercontent.com`
     - Client Secret: `GOCSPX-xxxxx`

### 2. Configure in Supabase Dashboard

1. **Configure Redirect URLs:**
   - Go to: Supabase Dashboard → Settings → Authentication → URL Configuration
   - Under "Redirect URLs", add:
     ```
     exp://192.168.56.1:8081/--/auth/callback
     ```
     (Replace `192.168.56.1` with your computer's IP if different)
   - **Keep the default Supabase callback URL** as well
   - Click **Save**

2. **Configure Google Provider:**
   - Go to: Supabase Dashboard → Authentication → Providers → Google

2. Fill in the form:
   - **Client IDs**: Paste your Client ID (the one ending in `.apps.googleusercontent.com`)
   - **Client Secret (for OAuth)**: Paste your Client Secret
   - **Skip nonce checks**: Leave OFF (unless specifically needed for iOS)
   - **Allow users without an email**: Leave OFF (recommended)
   - **Callback URL**: Already set (verify it matches):
     ```
     https://apbtuxchrymgmjbjxltm.supabase.co/auth/v1/callback
     ```

3. Click "Save"

### 3. Configure Redirect URLs in Supabase

1. Go to: Settings → Authentication → URL Configuration

2. Add to **Redirect URLs**:
   ```
   shootrz://auth/callback
   exp://localhost:8081
   ```

3. **Site URL** should be:
   - Development: `exp://localhost:8081`
   - Or: Your app's URL scheme

### 4. Test Google Sign In

1. In your app, tap "Sign in with Google"
2. Should redirect to Google login
3. After login, should redirect back to app
4. User should be logged in

## Troubleshooting

### "Redirect URI mismatch" error
**Fix:**
- Verify the redirect URI in Google Console exactly matches:
  ```
  https://anhtuvshumamihivitm.supabase.co/auth/v1/callback
  ```
- Check for typos or extra slashes
- Wait a few minutes after updating (Google caches)

### "Invalid client" error
**Fix:**
- Verify Client ID is correct (ends with `.apps.googleusercontent.com`)
- Verify Client Secret is correct
- Check credentials are not expired

### OAuth works but app doesn't receive callback
**Fix:**
- Verify deep link scheme is configured in `app.json`:
  ```json
  "scheme": "shootrz"
  ```
- Check redirect URLs in Supabase are set correctly
- For development, use `exp://localhost:8081`

### Testing in Development

For local development, you may need to:
1. Use Expo's development URL scheme
2. Or configure additional redirect URLs in Google Console:
   ```
   exp://localhost:8081
   ```

## Important Notes

- **Never commit Client Secret** to git
- Client Secret should only be in Supabase dashboard
- For production, consider using separate credentials
- Google OAuth works for both web and mobile (React Native)

## Verification Checklist

- [ ] Google Cloud project created
- [ ] Google+ API enabled
- [ ] OAuth consent screen configured
- [ ] OAuth client ID created
- [ ] Redirect URI added in Google Console
- [ ] Client ID added in Supabase
- [ ] Client Secret added in Supabase
- [ ] Redirect URLs configured in Supabase
- [ ] Deep link scheme in `app.json`
- [ ] Test sign-in works

## Next Steps

After Google OAuth is working:
1. Test the full flow (sign-in → app callback → logged in)
2. Consider setting up Apple Sign In (similar process)
3. Test both OAuth providers in your app

