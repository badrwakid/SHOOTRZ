-- Database Trigger to Auto-Create User Record
-- This trigger automatically creates a row in the users table when a new auth user is created
-- Run this in Supabase SQL Editor after running schema.sql

-- Full function + triggers: see fix_oauth_signup_database_error.sql (auth + public.users + profiles/streaks).
-- Kept minimal here — run fix_oauth_signup_database_error.sql on projects that use user_profiles / user_streaks.

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  resolved_email text;
  v_id uuid;
begin
  if tg_table_schema = 'auth' and tg_table_name = 'users' then
    v_id := new.id;
    resolved_email := coalesce(
      nullif(trim(new.email), ''),
      nullif(trim(new.raw_user_meta_data->>'email'), ''),
      nullif(trim(new.raw_user_meta_data->>'preferred_username'), '')
    );
    if resolved_email is null then
      resolved_email := 'user-' || replace(v_id::text, '-', '') || '@oauth.placeholder';
    end if;
    insert into public.users (id, email, auth_provider)
    values (
      v_id,
      resolved_email,
      coalesce(nullif(trim(new.raw_app_meta_data->>'provider'), ''), 'supabase')
    )
    on conflict (id) do nothing;
    return new;
  elsif tg_table_schema = 'public' and tg_table_name = 'users' then
    v_id := new.id;
    if to_regclass('public.user_profiles') is not null then
      insert into public.user_profiles (user_id)
      values (v_id)
      on conflict (user_id) do nothing;
    end if;
    if to_regclass('public.user_streaks') is not null then
      insert into public.user_streaks (user_id)
      values (v_id)
      on conflict (user_id) do nothing;
    end if;
    return new;
  end if;
  return new;
end;
$$;

alter function public.handle_new_user() owner to postgres;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created
  after insert on auth.users
  for each row execute function public.handle_new_user();

drop trigger if exists on_user_created on public.users;
create trigger on_user_created
  after insert on public.users
  for each row execute function public.handle_new_user();

-- Runs on sign-up / OAuth. If you see "Database error saving new user", run fix_oauth_signup_database_error.sql

