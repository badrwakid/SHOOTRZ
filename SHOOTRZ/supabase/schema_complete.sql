-- =============================================================================
-- SHOOTRZ — Canonical Database Schema
-- =============================================================================
--
-- This file is the single source of truth for setting up a fresh Supabase
-- (PostgreSQL) database for the SHOOTRZ basketball shot-analysis platform.
--
-- Usage: Paste into Supabase SQL Editor (Project → SQL Editor → New Query)
--        and run. This script is fully idempotent — safe to run multiple times.
--
-- What this covers:
--   • All 12 tables used by backend/storage/db.py (plus the optional models table)
--   • Camera angle enum
--   • All RLS policies (idempotent via DO $$ EXCEPTION WHEN duplicate_object $$)
--   • All indexes
--   • Trigger + function to auto-create public.users on auth sign-up,
--     and auto-populate user_profiles / user_streaks
--   • RPCs: get_user_stats, update_user_streak
--   • Storage bucket policies for the `videos` bucket
--
-- Sources merged:
--   schema.sql
--   migration_mvp_enhancements.sql
--   migration_add_name_onboarding.sql
--   add_username_column.sql
--   add_delete_policy.sql
--   fix_oauth_signup_database_error.sql
--   trigger_create_user.sql
--   storage_policies.sql
--   backend/storage/db.py  (ground-truth for all table/column names)
--
-- Last updated: 2026-04-24
-- =============================================================================


-- =============================================================================
-- 1. EXTENSIONS
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";


-- =============================================================================
-- 2. ENUMS
-- =============================================================================

DO $$ BEGIN
  CREATE TYPE camera_angle_type AS ENUM (
    'front_side_45',
    'side',
    'behind',
    'front',
    'overhead',
    'unknown'
  );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;


-- =============================================================================
-- 3. TABLES
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 3.1  users
--      Root entity. Auth trigger populates this from auth.users on sign-up.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
  id                       uuid        PRIMARY KEY DEFAULT auth.uid(),
  email                    text        UNIQUE NOT NULL,
  username                 text        UNIQUE,
  name                     text,
  skill_level              text,
  position                 text,
  auth_provider            text        NOT NULL DEFAULT 'supabase',
  has_completed_onboarding boolean     DEFAULT false,
  created_at               timestamptz NOT NULL DEFAULT now()
);

COMMENT ON COLUMN users.username IS 'Unique username for user identification and login';


-- -----------------------------------------------------------------------------
-- 3.2  user_profiles
--      Extended profile data auto-created by on_user_created trigger.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_profiles (
  user_id     uuid        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  bio         text,
  avatar_url  text,
  updated_at  timestamptz DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.3  user_streaks
--      Daily activity streaks; rows auto-created by on_user_created trigger.
--      update_user_streak() RPC manages current/longest streak logic.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_streaks (
  user_id            uuid        PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  current_streak     int         NOT NULL DEFAULT 0,
  longest_streak     int         NOT NULL DEFAULT 0,
  last_activity_date date,
  updated_at         timestamptz DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.4  sessions
--      A training session groups one or more video analyses.
--      db.py writes: title, overall_score, shot_count, duration_seconds, notes.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sessions (
  id               uuid          PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid          NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title            text,
  timestamp        timestamptz   NOT NULL DEFAULT now(),
  date             date,
  avg_score        double precision,
  overall_score    double precision,
  shot_count       int,
  duration_seconds int,
  notes            text
);


-- -----------------------------------------------------------------------------
-- 3.5  videos
--      One video per analysis run. Tracks processing state and job correlation.
--      db.py writes: file_url, camera_angle, device_info, fps, processing_status,
--                    job_id, duration_seconds, resolution, recorded_at.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS videos (
  id                uuid               PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id           uuid               NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  file_url          text               NOT NULL,
  angle             text,
  camera_angle      camera_angle_type  DEFAULT 'unknown',
  fps               int,
  device            text,
  device_info       jsonb,
  processing_status text,
  job_id            text,
  duration_seconds  int,
  resolution        text,
  recorded_at       timestamptz,
  created_at        timestamptz        NOT NULL DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.6  session_videos
--      Junction table linking sessions to their video(s).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS session_videos (
  session_id  uuid  NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  video_id    uuid  NOT NULL REFERENCES videos(id)   ON DELETE CASCADE,
  PRIMARY KEY (session_id, video_id)
);


-- -----------------------------------------------------------------------------
-- 3.7  metrics
--      Per-video biomechanics measurements.
--      db.py writes: metric_name, value, confidence, unit, phase, frame_idx.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metrics (
  id           uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
  video_id     uuid              NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  metric_name  text              NOT NULL,
  value        double precision  NOT NULL,
  confidence   double precision  NOT NULL DEFAULT 0,
  unit         text,
  phase        text,
  frame_idx    integer,
  created_at   timestamptz       NOT NULL DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.8  feedback
--      Coaching cues linked to a metric row.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS feedback (
  id          uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
  metric_id   uuid         NOT NULL REFERENCES metrics(id) ON DELETE CASCADE,
  message     text         NOT NULL,
  severity    text         NOT NULL DEFAULT 'info',
  created_at  timestamptz  NOT NULL DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.9  analysis_summaries
--      AI-generated session summary (Gemini enrichment).
--      db.py writes: session_id, user_id, overall_score, shot_count, score_tier,
--                    top_strengths, top_improvements, and any extra summary_data keys.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS analysis_summaries (
  id               uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
  session_id       uuid              UNIQUE REFERENCES sessions(id) ON DELETE CASCADE,
  user_id          uuid              NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  overall_score    double precision,
  shot_count       int,
  score_tier       text,
  top_strengths    jsonb,
  top_improvements jsonb,
  gemini_summary   text,
  raw_payload      jsonb,
  created_at       timestamptz       NOT NULL DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.10 chat_history
--      Persistent Coach J conversation log.
--      db.py writes: user_id, role, content, session_id, model_used, token_count,
--                    response_time_ms.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS chat_history (
  id               uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id          uuid         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  session_id       uuid         REFERENCES sessions(id) ON DELETE SET NULL,
  role             text         NOT NULL,   -- 'user' | 'assistant' | 'system'
  content          text         NOT NULL,
  model_used       text,
  token_count      int,
  response_time_ms int,
  created_at       timestamptz  NOT NULL DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.11 drill_completions
--      Records each time a user finishes a recommended drill.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS drill_completions (
  id            uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id       uuid         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  drill_id      text,
  drill_name    text,
  score         double precision,
  reps          int,
  duration_secs int,
  notes         text,
  completed_at  timestamptz  NOT NULL DEFAULT now()
);


-- -----------------------------------------------------------------------------
-- 3.12 workout_progress
--      Tracks per-user, per-workout progress (upserted on user_id + workout_id).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS workout_progress (
  id              uuid         PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid         NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  workout_id      text         NOT NULL,
  status          text,        -- 'in_progress' | 'completed' | 'abandoned'
  completed_drills jsonb,
  score           double precision,
  started_at      timestamptz  DEFAULT now(),
  completed_at    timestamptz,
  UNIQUE (user_id, workout_id)
);


-- -----------------------------------------------------------------------------
-- 3.13 models  (optional — stores ML model version metadata)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS models (
  id          uuid              PRIMARY KEY DEFAULT gen_random_uuid(),
  version     text              NOT NULL,
  name        text              NOT NULL DEFAULT 'unknown',
  description text,
  latency     double precision,
  fps         double precision,
  mpjpe       double precision,
  pa_mpjpe    double precision,
  created_at  timestamptz       NOT NULL DEFAULT now()
);


-- =============================================================================
-- 4. INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_users_username
  ON users(username)
  WHERE username IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_onboarding
  ON users(has_completed_onboarding);

CREATE INDEX IF NOT EXISTS idx_sessions_user_id
  ON sessions(user_id);

CREATE INDEX IF NOT EXISTS idx_videos_user_id
  ON videos(user_id);

CREATE INDEX IF NOT EXISTS idx_videos_camera_angle
  ON videos(camera_angle);

CREATE INDEX IF NOT EXISTS idx_session_videos_session_id
  ON session_videos(session_id);

CREATE INDEX IF NOT EXISTS idx_session_videos_video_id
  ON session_videos(video_id);

CREATE INDEX IF NOT EXISTS idx_metrics_metric_name
  ON metrics(metric_name);

CREATE INDEX IF NOT EXISTS idx_metrics_phase
  ON metrics(phase)
  WHERE phase IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_analysis_summaries_user_id
  ON analysis_summaries(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_id
  ON chat_history(user_id);

CREATE INDEX IF NOT EXISTS idx_chat_history_created_at
  ON chat_history(created_at);

CREATE INDEX IF NOT EXISTS idx_drill_completions_user_id
  ON drill_completions(user_id);

CREATE INDEX IF NOT EXISTS idx_workout_progress_user_id
  ON workout_progress(user_id);


-- =============================================================================
-- 5. ROW LEVEL SECURITY — enable on every user-data table
-- =============================================================================

ALTER TABLE users              ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles      ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_streaks       ENABLE ROW LEVEL SECURITY;
ALTER TABLE sessions           ENABLE ROW LEVEL SECURITY;
ALTER TABLE videos             ENABLE ROW LEVEL SECURITY;
ALTER TABLE session_videos     ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics            ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback           ENABLE ROW LEVEL SECURITY;
ALTER TABLE analysis_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE chat_history       ENABLE ROW LEVEL SECURITY;
ALTER TABLE drill_completions  ENABLE ROW LEVEL SECURITY;
ALTER TABLE workout_progress   ENABLE ROW LEVEL SECURITY;
-- models has no user_id column — leave RLS off (service-role only access)


-- =============================================================================
-- 6. RLS POLICIES
--    All idempotent: DO $$ BEGIN ... EXCEPTION WHEN duplicate_object THEN NULL $$
-- =============================================================================

-- users
DO $$ BEGIN
  CREATE POLICY "Users can read themselves" ON users
    FOR SELECT USING (auth.uid() = id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "Users can insert themselves" ON users
    FOR INSERT WITH CHECK (auth.uid() = id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "Users can update themselves" ON users
    FOR UPDATE USING (auth.uid() = id) WITH CHECK (auth.uid() = id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "Users can delete themselves" ON users
    FOR DELETE USING (auth.uid() = id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- user_profiles
DO $$ BEGIN
  CREATE POLICY "User owns their profile" ON user_profiles
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- user_streaks
DO $$ BEGIN
  CREATE POLICY "User owns their streak" ON user_streaks
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- sessions
DO $$ BEGIN
  CREATE POLICY "User owns sessions" ON sessions
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- videos
DO $$ BEGIN
  CREATE POLICY "User owns video rows" ON videos
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- session_videos (via sessions)
DO $$ BEGIN
  CREATE POLICY "User owns session_videos via sessions" ON session_videos
    FOR ALL USING (
      EXISTS (
        SELECT 1 FROM sessions s
        WHERE s.id = session_videos.session_id
          AND s.user_id = auth.uid()
      )
    ) WITH CHECK (
      EXISTS (
        SELECT 1 FROM sessions s
        WHERE s.id = session_videos.session_id
          AND s.user_id = auth.uid()
      )
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- metrics (via videos)
DO $$ BEGIN
  CREATE POLICY "User owns metrics via video" ON metrics
    FOR ALL USING (
      EXISTS (
        SELECT 1 FROM videos v
        WHERE v.id = metrics.video_id
          AND v.user_id = auth.uid()
      )
    ) WITH CHECK (
      EXISTS (
        SELECT 1 FROM videos v
        WHERE v.id = metrics.video_id
          AND v.user_id = auth.uid()
      )
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- feedback (via metrics → videos)
DO $$ BEGIN
  CREATE POLICY "User owns feedback via metrics->video" ON feedback
    FOR ALL USING (
      EXISTS (
        SELECT 1 FROM metrics m
        JOIN videos v ON v.id = m.video_id
        WHERE m.id = feedback.metric_id
          AND v.user_id = auth.uid()
      )
    ) WITH CHECK (
      EXISTS (
        SELECT 1 FROM metrics m
        JOIN videos v ON v.id = m.video_id
        WHERE m.id = feedback.metric_id
          AND v.user_id = auth.uid()
      )
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- analysis_summaries
DO $$ BEGIN
  CREATE POLICY "User owns analysis summaries" ON analysis_summaries
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- chat_history
DO $$ BEGIN
  CREATE POLICY "User owns chat history" ON chat_history
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- drill_completions
DO $$ BEGIN
  CREATE POLICY "User owns drill completions" ON drill_completions
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

-- workout_progress
DO $$ BEGIN
  CREATE POLICY "User owns workout progress" ON workout_progress
    FOR ALL USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- =============================================================================
-- 7. STORAGE POLICIES  (videos bucket — create the bucket in Dashboard first)
-- =============================================================================

DO $$ BEGIN
  CREATE POLICY "User read own videos" ON storage.objects
    FOR SELECT USING (
      bucket_id = 'videos'
      AND auth.role() = 'authenticated'
      AND split_part(name, '/', 1) = auth.uid()::text
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "User write own videos" ON storage.objects
    FOR INSERT WITH CHECK (
      bucket_id = 'videos'
      AND auth.role() = 'authenticated'
      AND split_part(name, '/', 1) = auth.uid()::text
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;

DO $$ BEGIN
  CREATE POLICY "User delete own videos" ON storage.objects
    FOR DELETE USING (
      bucket_id = 'videos'
      AND auth.role() = 'authenticated'
      AND split_part(name, '/', 1) = auth.uid()::text
    );
EXCEPTION WHEN duplicate_object THEN NULL; END $$;


-- =============================================================================
-- 8. FUNCTIONS / RPCs
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 8.1  handle_new_user()
--      Called by both on_auth_user_created (auth schema) and
--      on_user_created (public.users).  Two-phase:
--        auth INSERT  → INSERT into public.users (ON CONFLICT DO NOTHING)
--        users INSERT → INSERT into user_profiles + user_streaks
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  resolved_email text;
  v_id           uuid;
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


-- -----------------------------------------------------------------------------
-- 8.2  get_user_stats(p_user_id uuid)
--      Called by db.get_user_stats().  Returns aggregate stats for a user.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_user_stats(p_user_id uuid)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_result jsonb;
BEGIN
  SELECT jsonb_build_object(
    'total_sessions',   COUNT(DISTINCT s.id),
    'total_videos',     COUNT(DISTINCT v.id),
    'avg_score',        ROUND(AVG(a.overall_score)::numeric, 2),
    'best_score',       MAX(a.overall_score),
    'total_drills',     (
                          SELECT COUNT(*) FROM drill_completions dc
                          WHERE dc.user_id = p_user_id
                        ),
    'current_streak',   COALESCE((
                          SELECT us.current_streak FROM user_streaks us
                          WHERE us.user_id = p_user_id
                        ), 0),
    'longest_streak',   COALESCE((
                          SELECT us.longest_streak FROM user_streaks us
                          WHERE us.user_id = p_user_id
                        ), 0)
  )
  INTO v_result
  FROM sessions s
  LEFT JOIN analysis_summaries a ON a.session_id = s.id
  LEFT JOIN session_videos sv    ON sv.session_id = s.id
  LEFT JOIN videos v             ON v.id = sv.video_id
  WHERE s.user_id = p_user_id;

  RETURN COALESCE(v_result, '{}'::jsonb);
END;
$$;


-- -----------------------------------------------------------------------------
-- 8.3  update_user_streak(p_user_id uuid)
--      Called by db.update_streak().  Bumps streak if activity today or yesterday.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.update_user_streak(p_user_id uuid)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  v_today        date := CURRENT_DATE;
  v_last_date    date;
  v_current      int;
  v_longest      int;
BEGIN
  -- Upsert row so it always exists
  INSERT INTO public.user_streaks (user_id, current_streak, longest_streak, last_activity_date, updated_at)
  VALUES (p_user_id, 1, 1, v_today, now())
  ON CONFLICT (user_id) DO NOTHING;

  SELECT last_activity_date, current_streak, longest_streak
  INTO v_last_date, v_current, v_longest
  FROM public.user_streaks
  WHERE user_id = p_user_id;

  IF v_last_date = v_today THEN
    -- Already counted today — just refresh updated_at
    UPDATE public.user_streaks
    SET updated_at = now()
    WHERE user_id = p_user_id;

  ELSIF v_last_date = v_today - INTERVAL '1 day' THEN
    -- Consecutive day — extend streak
    v_current := v_current + 1;
    v_longest := GREATEST(v_longest, v_current);
    UPDATE public.user_streaks
    SET current_streak     = v_current,
        longest_streak     = v_longest,
        last_activity_date = v_today,
        updated_at         = now()
    WHERE user_id = p_user_id;

  ELSE
    -- Streak broken — reset
    UPDATE public.user_streaks
    SET current_streak     = 1,
        longest_streak     = GREATEST(v_longest, 1),
        last_activity_date = v_today,
        updated_at         = now()
    WHERE user_id = p_user_id;
  END IF;
END;
$$;


-- =============================================================================
-- 9. TRIGGERS
-- =============================================================================

-- Fires on auth.users INSERT → populates public.users
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();

-- Fires on public.users INSERT → populates user_profiles + user_streaks
DROP TRIGGER IF EXISTS on_user_created ON public.users;
CREATE TRIGGER on_user_created
  AFTER INSERT ON public.users
  FOR EACH ROW
  EXECUTE FUNCTION public.handle_new_user();


-- =============================================================================
-- END OF SCHEMA
-- =============================================================================
