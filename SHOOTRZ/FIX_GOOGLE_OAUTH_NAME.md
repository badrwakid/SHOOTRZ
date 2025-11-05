# Fix: Show "SHOOTRZ" Instead of Supabase URL in Google OAuth

## The Problem

When signing in with Google, the OAuth screen shows:
- **Current:** "You're signing back in to apbtuxchrymgmjbjxltm.supabase.co"
- **Desired:** "You're signing back in to SHOOTRZ"

## Solution: Configure OAuth Consent Screen in Google Cloud Console

The app name shown in Google OAuth is configured in **Google Cloud Console**, not in your app code.

### Steps:

1. **Go to Google Cloud Console:**
   - Visit: https://console.cloud.google.com/
   - Select your project (the one with your OAuth credentials)

2. **Navigate to OAuth Consent Screen:**
   - Left sidebar → **APIs & Services** → **OAuth consent screen**

3. **Configure the App Information:**
   - **App name:** Enter `SHOOTRZ`
   - **User support email:** Select your email
   - **App logo:** (Optional) Upload SHOOTRZ logo if you have one
   - **App domain:** (Optional) Your domain if you have one
   - **Developer contact information:** Your email

4. **Scopes (if editing):**
   - Keep the default scopes or add what you need
   - Usually: `email`, `profile`, `openid`

5. **Test users (if app is in Testing mode):**
   - Add test users who can sign in during testing
   - Your email: `BadrWakid@gmail.com`

6. **Click "Save and Continue"** through all steps

7. **Submit for Verification (if needed):**
   - If you want to publish the app, you may need verification
   - For testing, you can keep it in "Testing" mode

### Notes:

- The Supabase domain (`apbtuxchrymgmjbjxltm.supabase.co`) will still appear in the redirect URL and technical details, but the **main app name** will show as "SHOOTRZ"
- Changes take effect immediately (no waiting)
- If the app is in "Testing" mode, only users you add as test users can sign in

## Alternative: Custom Domain (Advanced)

If you want to completely hide the Supabase URL:
1. Set up a custom domain for Supabase (paid feature)
2. Configure it to point to your Supabase project
3. Use that domain in redirect URLs

But for MVP/testing, just changing the app name in OAuth consent screen is sufficient!






