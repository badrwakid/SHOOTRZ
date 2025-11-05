# ⚠️ CRITICAL: Database Migration Required

## Immediate Action Required

The authentication system has been updated and requires a database migration to be run **before the app will work**.

## Error You'll See Without Migration

```
⚠️ Error checking user: {"code": "42703", "message": "column users.name does not exist"}
ERROR ❌ Failed to update user in database: {"code": "PGRST204", "message": "Could not find the 'position' column of 'users' in the schema cache"}
```

## Solution: Run This Migration

1. Open **Supabase Dashboard** → **SQL Editor**
2. Copy and paste the following migration script:

```sql
-- Add name field to users table
alter table users add column if not exists name text;

-- Add skill_level field to users table
alter table users add column if not exists skill_level text;

-- Add position field to users table
alter table users add column if not exists position text;

-- Add has_completed_onboarding field to users table
alter table users add column if not exists has_completed_onboarding boolean default false;

-- Update existing users: if they have a username, mark onboarding as complete
update users 
set has_completed_onboarding = true 
where username is not null 
  and username != '' 
  and username != lower(split_part(email, '@', 1));

-- Add index for faster onboarding status lookups
create index if not exists idx_users_onboarding on users(has_completed_onboarding);
```

3. Click **Run** or press `Ctrl+Enter`
4. Verify success: You should see "Success. No rows returned"
5. **Restart your app** to load the changes

## Verification

After running the migration, verify in Supabase:

1. Go to **Table Editor** → **users** table
2. Check that columns exist:
   - ✅ `name` (text, nullable)
   - ✅ `skill_level` (text, nullable)
   - ✅ `position` (text, nullable)
   - ✅ `has_completed_onboarding` (boolean, default false)
3. Check that index exists:
   - ✅ `idx_users_onboarding`

## What This Migration Does

- Adds `name` column to store user's full name from Google or email signup
- Adds `skill_level` column to store user's skill level (beginner/intermediate/advanced)
- Adds `position` column to store user's basketball position
- Adds `has_completed_onboarding` column to track if user completed onboarding
- Marks existing users who have usernames as onboarding complete
- Creates index for faster queries on onboarding status

## Next Steps

After migration is complete, the app will:
- ✅ Extract and store names from Google profiles
- ✅ Properly detect new vs returning users
- ✅ Show UsernameScreen for new users only
- ✅ Show OnboardingScreen after username is set

---

**File Location**: `supabase/migration_add_name_onboarding.sql`

## Additional Step: Clean Up Old Username

If you have an old username in the database that matches your email prefix (like `badrwakid`), you need to either:

**Option 1**: Delete it to trigger the username screen again:
```sql
UPDATE users SET username = NULL WHERE username = 'badrwakid';
```

**Option 2**: Keep it but you'll be asked for a new username next time you log in

This is a one-time cleanup issue.

