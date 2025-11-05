# Supabase Authentication Testing Checklist

## Prerequisites

Before testing, ensure:
- [ ] Database schema is deployed (`supabase/schema.sql`)
- [ ] Database trigger is created (`supabase/trigger_create_user.sql`)
- [ ] Email provider is configured (Supabase default or custom SMTP)
- [ ] Environment variables are set (`EXPO_PUBLIC_SUPABASE_URL`, `EXPO_PUBLIC_SUPABASE_ANON_KEY`)
- [ ] Deep link scheme is configured in `app.json`

## Test 1: Signup with Email Confirmation

### Steps:
1. Open app
2. Tap "Sign Up"
3. Enter:
   - Name: Test User
   - Username: testuser
   - Email: test@example.com
   - Password: testpass123
4. Tap "Create Account"

### Expected Results:
- [ ] Signup succeeds (shows success message)
- [ ] User sees "Check your email" message
- [ ] Confirmation email is received within 1-2 minutes
- [ ] Database trigger creates user record in `users` table
- [ ] Email contains confirmation link

### Verify Database:
```sql
-- Check user was created
SELECT id, email, created_at FROM auth.users WHERE email = 'test@example.com';
SELECT id, email, auth_provider FROM public.users WHERE email = 'test@example.com';
```

## Test 2: Email Confirmation

### Steps:
1. Open confirmation email
2. Click confirmation link
3. App should open (if closed) or handle deep link (if open)

### Expected Results:
- [ ] Deep link is parsed correctly (`shootrz://confirm-email?token=...`)
- [ ] Email is confirmed in Supabase
- [ ] User is automatically logged in
- [ ] User data is synced from database

### Verify:
```sql
-- Check email confirmed
SELECT id, email, email_confirmed_at FROM auth.users WHERE email = 'test@example.com';
```

## Test 3: Login After Email Confirmation

### Steps:
1. If not already logged in, open app
2. Enter email and password
3. Tap "Sign In"

### Expected Results:
- [ ] Login succeeds
- [ ] User is authenticated
- [ ] User data loads correctly
- [ ] App navigates to main screen

## Test 4: Session Persistence

### Steps:
1. While logged in, close app completely
2. Reopen app
3. Wait for app to initialize

### Expected Results:
- [ ] App restores session from Supabase
- [ ] User remains logged in
- [ ] No login screen shown
- [ ] User data is loaded

### Verify:
- Check console logs for "Session restored successfully"
- User data should be available immediately

## Test 5: Password Reset

### Steps:
1. On login screen, tap "Forgot Password?"
2. Enter registered email
3. Tap "Send Reset Link"
4. Check email inbox

### Expected Results:
- [ ] Success message displayed
- [ ] Reset email received within 1-2 minutes
- [ ] Email contains reset link with deep link (`shootrz://reset-password?token=...`)

## Test 6: Complete Password Reset Flow

### Steps:
1. Click reset link in email
2. App opens (if closed) or handles deep link (if open)
3. Enter new password (when password reset screen is implemented)
4. Submit new password

### Expected Results:
- [ ] Deep link is parsed correctly
- [ ] Password reset token is validated
- [ ] Password can be updated
- [ ] User can login with new password

## Test 7: OAuth - Google Sign In

### Prerequisites:
- [ ] Google OAuth configured in Supabase
- [ ] Redirect URL configured: `shootrz://auth/callback`

### Steps:
1. On login screen, tap "Sign in with Google"
2. Complete Google OAuth flow
3. Return to app

### Expected Results:
- [ ] OAuth redirect works
- [ ] Deep link is handled (`shootrz://auth/callback?access_token=...`)
- [ ] User is logged in after OAuth
- [ ] User record exists in database

## Test 8: OAuth - Apple Sign In

### Prerequisites:
- [ ] Apple OAuth configured in Supabase
- [ ] Redirect URL configured: `shootrz://auth/callback`

### Steps:
1. On login screen, tap "Sign in with Apple"
2. Complete Apple OAuth flow
3. Return to app

### Expected Results:
- [ ] OAuth redirect works
- [ ] Deep link is handled
- [ ] User is logged in after OAuth
- [ ] User record exists in database

## Test 9: Error Handling

### Test Invalid Login:
1. Enter incorrect email/password
2. Tap "Sign In"

**Expected:**
- [ ] Clear error message: "Invalid email or password"
- [ ] No technical jargon

### Test Unconfirmed Email Login:
1. Sign up new user (don't confirm email)
2. Try to login

**Expected:**
- [ ] Error message: "Please confirm your email address before signing in"
- [ ] Helpful guidance

### Test Network Error:
1. Disable internet
2. Try to login/signup

**Expected:**
- [ ] Error message: "Network error. Please check your internet connection"
- [ ] Graceful failure

## Test 10: Logout

### Steps:
1. While logged in, go to Profile screen
2. Tap "Logout"
3. Close and reopen app

### Expected Results:
- [ ] User is logged out
- [ ] Local storage is cleared
- [ ] Supabase session is cleared
- [ ] App shows login screen on next open

## Test 11: Database Trigger Verification

### Test Trigger Creates User Record:

**Steps:**
1. Sign up new user
2. Wait 1-2 seconds
3. Check database

**Verify:**
```sql
-- Should return 1 row (created by trigger)
SELECT id, email, auth_provider, created_at 
FROM public.users 
WHERE email = 'newuser@example.com';

-- Should match auth.users
SELECT 
  (SELECT COUNT(*) FROM auth.users) AS auth_count,
  (SELECT COUNT(*) FROM public.users) AS public_count;
-- Should be equal
```

## Test 12: Multiple Signup Attempts

### Test Duplicate Email:
1. Try to sign up with existing email

**Expected:**
- [ ] Error: "An account with this email already exists. Please sign in instead."

### Test Duplicate Username (if implemented):
1. Sign up with username that exists

**Expected:**
- [ ] Appropriate error message

## Common Issues & Solutions

### Issue: Email not received
**Check:**
- Email provider configured?
- Email in spam folder?
- Rate limit reached? (3/hour on free tier)
- Check Supabase logs: Settings → Logs → Auth Logs

### Issue: User record not created
**Check:**
- Trigger exists? Run: `SELECT * FROM pg_trigger WHERE tgname = 'on_auth_user_created';`
- Trigger function exists? Run: `SELECT * FROM pg_proc WHERE proname = 'handle_new_user';`
- Check Supabase logs for errors

### Issue: Deep link not working
**Check:**
- Deep link scheme in `app.json`?
- Redirect URL configured in Supabase?
- URL format correct: `shootrz://reset-password?token=...`

### Issue: OAuth not redirecting
**Check:**
- OAuth provider configured in Supabase?
- Redirect URL added to allowed URLs?
- Deep link handler in App.tsx?

### Issue: Session not persisting
**Check:**
- `persistSession: true` in Supabase client?
- AsyncStorage working?
- Session expired? (default: 1 hour, can extend)

## Verification Queries

Run these in Supabase SQL Editor:

```sql
-- 1. Check all users
SELECT 
  au.id,
  au.email,
  au.email_confirmed_at,
  au.created_at,
  pu.id IS NOT NULL AS has_profile
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
ORDER BY au.created_at DESC;

-- 2. Verify trigger exists
SELECT tgname, tgenabled 
FROM pg_trigger 
WHERE tgname = 'on_auth_user_created';

-- 3. Check RLS policies
SELECT tablename, policyname, cmd 
FROM pg_policies 
WHERE schemaname = 'public';

-- 4. Verify email confirmations
SELECT 
  email,
  email_confirmed_at IS NOT NULL AS is_confirmed,
  created_at
FROM auth.users
ORDER BY created_at DESC
LIMIT 10;
```

## Test Report Template

For each test:
- [ ] Test completed
- [ ] Expected results met
- [ ] Issues found (if any)
- [ ] Screenshots/logs attached

## Success Criteria

All tests should pass:
- [ ] Signup creates auth user and database record
- [ ] Email confirmation works
- [ ] Login works after confirmation
- [ ] Session persists across app restarts
- [ ] Password reset flow works
- [ ] OAuth flows work
- [ ] Error messages are user-friendly
- [ ] All deep links are handled correctly






