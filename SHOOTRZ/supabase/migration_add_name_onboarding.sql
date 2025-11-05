-- Migration: Add missing fields to users table
-- Run this in Supabase SQL Editor

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

