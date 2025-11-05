-- Add DELETE policy for users table
-- This allows users to delete their own account
-- Run this in Supabase SQL Editor

-- Drop existing policy if it exists (in case it was added with different name)
drop policy if exists "Users can delete themselves" on users;

-- Create DELETE policy
create policy "Users can delete themselves" on users
  for delete using (auth.uid() = id);

-- Also add UPDATE policy if missing (for username/profile updates)
drop policy if exists "Users can update themselves" on users;

create policy "Users can update themselves" on users
  for update using (auth.uid() = id) with check (auth.uid() = id);






