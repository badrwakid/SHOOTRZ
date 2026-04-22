-- Fix "Database error saving new user" on Google / OAuth sign-up
-- Run in Supabase → SQL Editor (whole file).
--
-- Typical cause: handle_new_user() only inserted into user_profiles / user_streaks (FK → public.users)
-- while the auth.users trigger still ran on sign-up — no public.users row → FK violation.
--
-- Flow: auth.users INSERT → create public.users → AFTER INSERT on public.users → profiles + streaks.

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  resolved_email text;
  v_id uuid;
BEGIN
  IF tg_table_schema = 'auth' AND tg_table_name = 'users' THEN
    v_id := NEW.id;

    resolved_email := COALESCE(
      NULLIF(trim(NEW.email), ''),
      NULLIF(trim(NEW.raw_user_meta_data->>'email'), ''),
      NULLIF(trim(NEW.raw_user_meta_data->>'preferred_username'), '')
    );

    IF resolved_email IS NULL THEN
      resolved_email := 'user-' || replace(v_id::text, '-', '') || '@oauth.placeholder';
    END IF;

    INSERT INTO public.users (id, email, auth_provider)
    VALUES (
      v_id,
      resolved_email,
      COALESCE(NULLIF(trim(NEW.raw_app_meta_data->>'provider'), ''), 'supabase')
    )
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;

  ELSIF tg_table_schema = 'public' AND tg_table_name = 'users' THEN
    v_id := NEW.id;

    IF to_regclass('public.user_profiles') IS NOT NULL THEN
      INSERT INTO public.user_profiles (user_id)
      VALUES (v_id)
      ON CONFLICT (user_id) DO NOTHING;
    END IF;

    IF to_regclass('public.user_streaks') IS NOT NULL THEN
      INSERT INTO public.user_streaks (user_id)
      VALUES (v_id)
      ON CONFLICT (user_id) DO NOTHING;
    END IF;

    RETURN NEW;
  END IF;

  RETURN NEW;
END;
$$;

ALTER FUNCTION public.handle_new_user() OWNER TO postgres;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- Ensures profile rows are created after public.users (skip if you have no user_profiles table)
DROP TRIGGER IF EXISTS on_user_created ON public.users;
CREATE TRIGGER on_user_created
  AFTER INSERT ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();
