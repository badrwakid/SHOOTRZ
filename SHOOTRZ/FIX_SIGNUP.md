# 🔧 Fix: Signup Not Creating Database Records

## Problem
Signup creates user in Supabase Auth, but **not** in the `users` table.

## Root Cause
`supabase.auth.signUp()` only creates a user in `auth.users` (Supabase Auth system), not in our custom `users` table.

## Solution Applied

**Fixed in `AuthContext.tsx`:**
- After `auth.signUp()`, manually insert into `users` table
- Added error handling
- Added logging for debugging

## Code Flow (Fixed)

```
1. User submits signup form
   ↓
2. supabase.auth.signUp() → Creates auth user
   ↓
3. supabase.from('users').insert() → Creates database record ✅
   ↓
4. Cache user data locally
   ↓
5. User can now login and use app
```

## Better Solution: Database Trigger (Recommended)

**Option 1: Use Database Trigger (Automatic)**

Run this SQL in Supabase SQL Editor:
```sql
-- File: supabase/trigger_create_user.sql
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, auth_provider)
  values (new.id, new.email, 'supabase');
  return new;
end;
$$ language plpgsql security definer;

create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

**Benefits:**
- ✅ Automatic - no frontend code needed
- ✅ More reliable - can't be bypassed
- ✅ Works even if frontend fails

**If trigger is set up:** You can remove the manual insert code from `AuthContext.tsx`.

## Test Signup

**1. Try signup in the app**

**2. Check Supabase Dashboard:**
- Go to: https://supabase.com/dashboard/project/apbtuxchrymgmjbjxltm
- **Authentication → Users** → Should see new user
- **Database → Table Editor → users** → Should see new record

**3. Check console logs:**
- Should see: `✅ Supabase auth user created`
- Should see: `✅ User record created in database`

## Troubleshooting

### Error: "new row violates row-level security policy"
**Cause:** Email confirmation might be required, user doesn't have active session yet  
**Fix:** 
1. Disable email confirmation in Supabase Settings → Authentication
2. OR use database trigger (bypasses RLS)

### Error: "duplicate key value violates unique constraint"
**Cause:** User already exists  
**Fix:** Try logging in instead, or delete existing user

### User created in Auth but not in users table
**Possible causes:**
1. RLS policy blocking insert
2. Email confirmation required (no session yet)
3. Trigger not set up

**Solution:** Use the database trigger - it runs with `security definer` and bypasses RLS.

## Verification

After signup:
```sql
-- In Supabase SQL Editor
SELECT * FROM users ORDER BY created_at DESC LIMIT 5;
```

Should show your new user record.






