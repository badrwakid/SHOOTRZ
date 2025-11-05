-- Verification Queries for Supabase Setup
-- Run these in Supabase SQL Editor to verify your setup

-- 1. Check if schema exists and tables are created
SELECT 
  table_name,
  table_type
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('users', 'videos', 'metrics', 'feedback', 'sessions')
ORDER BY table_name;

-- 2. Verify trigger function exists
SELECT 
  proname AS function_name,
  prosrc AS function_body
FROM pg_proc
WHERE proname = 'handle_new_user';

-- 3. Verify trigger exists and is enabled
SELECT 
  tgname AS trigger_name,
  tgenabled AS is_enabled,
  tgrelid::regclass AS table_name,
  proname AS function_name
FROM pg_trigger t
JOIN pg_proc p ON t.tgfoid = p.oid
WHERE tgname = 'on_auth_user_created';

-- 4. Check RLS is enabled on all tables
SELECT 
  schemaname,
  tablename,
  rowsecurity AS rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename IN ('users', 'videos', 'metrics', 'feedback', 'sessions');

-- 5. List all RLS policies
SELECT 
  schemaname,
  tablename,
  policyname,
  permissive,
  roles,
  cmd AS command,
  qual AS using_expression,
  with_check AS with_check_expression
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- 6. Check if extensions are enabled
SELECT 
  extname AS extension_name,
  extversion AS version
FROM pg_extension
WHERE extname IN ('pgcrypto', 'uuid-ossp', 'pgvector');

-- 7. Verify users table structure
SELECT 
  column_name,
  data_type,
  is_nullable,
  column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'users'
ORDER BY ordinal_position;

-- 8. Count existing users (should match auth.users count)
SELECT 
  (SELECT COUNT(*) FROM auth.users) AS auth_users_count,
  (SELECT COUNT(*) FROM public.users) AS public_users_count;






