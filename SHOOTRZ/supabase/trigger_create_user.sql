-- Database Trigger to Auto-Create User Record
-- This trigger automatically creates a row in the users table when a new auth user is created
-- Run this in Supabase SQL Editor after running schema.sql

-- Create function to handle new user creation
-- This runs automatically when a new user is created in auth.users
-- Works even if email confirmation is enabled (runs before confirmation)
create or replace function public.handle_new_user()
returns trigger as $$
begin
  insert into public.users (id, email, auth_provider)
  values (
    new.id,
    new.email,
    'supabase'
  )
  on conflict (id) do nothing; -- Prevent errors if record already exists
  return new;
end;
$$ language plpgsql security definer;

-- Create trigger that fires when a new user is created in auth.users
create or replace trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();

-- Note: This trigger runs automatically when supabase.auth.signUp() is called
-- No need to manually insert into users table in the frontend

