-- Add username column to users table
-- Run this in Supabase SQL Editor

-- Add username column (unique, nullable for existing users)
alter table users
add column if not exists username text unique;

-- Create index for faster username lookups
create index if not exists idx_users_username on users(username) where username is not null;

-- Add comment
comment on column users.username is 'Unique username for user identification and login';






