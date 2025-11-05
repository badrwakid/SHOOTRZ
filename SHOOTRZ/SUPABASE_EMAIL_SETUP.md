# Supabase Email Configuration Guide

## Overview

This guide walks you through configuring Supabase to send emails for:
- Email confirmation (signup)
- Password reset
- Email change verification

## Step 1: Access Email Settings

1. Go to your Supabase Dashboard
2. Navigate to: **Settings → Authentication → Email Templates**
3. Or: **Settings → Auth → Email**

## Step 2: Configure Email Provider

### Option A: Use Supabase's Default Email Service (Recommended for Development)

**Default Setup:**
- Supabase uses its own SMTP service by default
- Limited to 3 emails/hour for free tier
- Works immediately, no configuration needed

**Verify it's enabled:**
1. Settings → Authentication → Email
2. Ensure "Enable email confirmations" is ON
3. Ensure "Enable email signups" is ON

### Option B: Configure Custom SMTP (Recommended for Production)

**Why use custom SMTP:**
- Higher email limits
- Better deliverability
- Custom branding
- Better analytics

**SMTP Providers (Recommended):**
1. **SendGrid** (Free tier: 100 emails/day)
2. **Mailgun** (Free tier: 5,000 emails/month)
3. **Amazon SES** (Very cheap, high limits)
4. **Resend** (Modern, developer-friendly)

**Setup Custom SMTP:**
1. Go to: **Settings → Authentication → Email**
2. Scroll to **SMTP Settings**
3. Enter your SMTP credentials:
   - **Host**: smtp.provider.com
   - **Port**: 587 (TLS) or 465 (SSL)
   - **Username**: Your SMTP username
   - **Password**: Your SMTP password
   - **Sender email**: noreply@yourdomain.com
   - **Sender name**: SHOOTRZ

**Example (SendGrid):**
```
Host: smtp.sendgrid.net
Port: 587
Username: apikey
Password: SG.your_sendgrid_api_key
Sender email: noreply@shootrz.com
Sender name: SHOOTRZ
```

## Step 3: Configure Email Templates

### 1. Signup Confirmation Email

1. Go to: **Settings → Authentication → Email Templates**
2. Click **"Confirm signup"** template
3. Customize the email:

**Subject:** `Confirm your SHOOTRZ account`

**Body (HTML):**
```html
<h2>Welcome to SHOOTRZ!</h2>
<p>Thanks for signing up. Click the link below to confirm your email address:</p>
<p><a href="{{ .ConfirmationURL }}">Confirm Email</a></p>
<p>This link will expire in 24 hours.</p>
<p>If you didn't create this account, you can safely ignore this email.</p>
<p>- SHOOTRZ Team</p>
```

**Redirect URL:**
- Development: `shootrz://confirm-email?token={{ .Token }}`
- Production: `https://app.shootrz.com/confirm-email?token={{ .Token }}`

### 2. Password Reset Email

1. Click **"Reset password"** template
2. Customize:

**Subject:** `Reset your SHOOTRZ password`

**Body (HTML):**
```html
<h2>Reset Your Password</h2>
<p>We received a request to reset your password for your SHOOTRZ account.</p>
<p><a href="{{ .ConfirmationURL }}">Reset Password</a></p>
<p>This link will expire in 1 hour.</p>
<p>If you didn't request this, you can safely ignore this email. Your password will remain unchanged.</p>
<p>- SHOOTRZ Team</p>
```

**Redirect URL:**
- Development: `shootrz://reset-password?token={{ .Token }}`
- Production: `https://app.shootrz.com/reset-password?token={{ .Token }}`

### 3. Magic Link Email (Optional)

**Subject:** `Sign in to SHOOTRZ`

**Body:**
```html
<h2>Sign in to SHOOTRZ</h2>
<p>Click the link below to sign in:</p>
<p><a href="{{ .ConfirmationURL }}">Sign In</a></p>
<p>This link will expire in 1 hour.</p>
```

## Step 4: Configure Redirect URLs

### In Supabase Dashboard:

1. Go to: **Settings → Authentication → URL Configuration**
2. Set **Site URL**: 
   - Development: `exp://localhost:8081`
   - Production: `https://app.shootrz.com`
3. Add **Redirect URLs**:
   ```
   shootrz://confirm-email
   shootrz://reset-password
   shootrz://auth/callback
   exp://localhost:8081
   ```

### In app.json:

Already configured with deep link scheme: `shootrz://`

## Step 5: Email Settings

### Enable Email Confirmations

1. Go to: **Settings → Authentication → Email**
2. Toggle **"Enable email confirmations"** ON
3. This requires users to confirm email before they can login

### Email Rate Limits

**Free tier:** 3 emails/hour (Supabase default)
**Custom SMTP:** Depends on provider limits

**Important:** For production, use custom SMTP to avoid rate limits.

## Step 6: Test Email Delivery

### Test Signup Email:

1. Sign up a new user in the app
2. Check email inbox (and spam folder)
3. Verify email is received within 1-2 minutes
4. Check email format and links work

### Test Password Reset:

1. Click "Forgot Password" in app
2. Enter email address
3. Check inbox for reset email
4. Click link and verify redirect works

### Troubleshooting:

**No emails received?**
- Check spam folder
- Verify SMTP settings are correct
- Check Supabase logs: **Settings → Logs → Auth Logs**
- Verify email provider isn't blocking Supabase IPs

**Emails going to spam?**
- Use custom SMTP with verified domain
- Set up SPF, DKIM, DMARC records for your domain
- Use professional sender email (noreply@yourdomain.com)

## Step 7: Verify Email Configuration

Run this query in Supabase SQL Editor:

```sql
-- Check email confirmation status for test user
SELECT 
  id,
  email,
  email_confirmed_at,
  created_at
FROM auth.users
WHERE email = 'your-test-email@example.com';
```

## Production Checklist

- [ ] Custom SMTP configured with verified domain
- [ ] Email templates customized with branding
- [ ] Redirect URLs point to production app
- [ ] Email confirmation enabled
- [ ] Test emails sent successfully
- [ ] SPF/DKIM records set up for domain
- [ ] Email rate limits acceptable for user base
- [ ] Monitoring set up for failed email deliveries

## Support

If emails still not sending:
1. Check Supabase dashboard logs
2. Verify SMTP credentials are correct
3. Test SMTP connection outside Supabase
4. Contact Supabase support if using default email service






