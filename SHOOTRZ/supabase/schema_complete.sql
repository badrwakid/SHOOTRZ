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
--   • RPCs: get_user_stats, get_coach_context, update_user_streak
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
  id                       uuid        PRIMARY KEY DEFAULT gen_random_uuid(),
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
  user_id                   uuid             PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  bio                       text,
  avatar_url                text,
  primary_goal              text,
  coaching_style            text,
  training_frequency        text,
  preferred_drill_duration  int,
  age                       int,
  height_cm                 double precision,
  weight_kg                 double precision,
  dominant_hand             text,
  years_playing             int,
  notifications_enabled     boolean          NOT NULL DEFAULT true,
  dark_mode_enabled         boolean          NOT NULL DEFAULT true,
  analytics_enabled         boolean          NOT NULL DEFAULT true,
  updated_at                timestamptz      DEFAULT now()
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
  total_sessions     int         NOT NULL DEFAULT 0,
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

CREATE INDEX IF NOT EXISTS idx_metrics_video_id ON metrics(video_id);
CREATE INDEX IF NOT EXISTS idx_feedback_metric_id ON feedback(metric_id);

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

-- Composite patterns for “list by user, newest first” (history / dashboards).
CREATE INDEX IF NOT EXISTS idx_sessions_user_timestamp
  ON sessions(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_videos_user_created_at
  ON videos(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_analysis_summaries_user_created_at
  ON analysis_summaries(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_created_at
  ON chat_history(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_drill_completions_user_completed_at
  ON drill_completions(user_id, completed_at DESC);

CREATE INDEX IF NOT EXISTS idx_workout_progress_user_started_at
  ON workout_progress(user_id, started_at DESC);


-- -----------------------------------------------------------------------------
-- 4.1  CHECK constraints (idempotent; safe to re-apply on existing DBs)
-- -----------------------------------------------------------------------------
DO $$ BEGIN
  ALTER TABLE metrics
    ADD CONSTRAINT metrics_confidence_range_chk
    CHECK (confidence IS NULL OR (confidence >= 0::double precision AND confidence <= 1::double precision));
EXCEPTION
  WHEN duplicate_object THEN NULL;
END $$;


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

DO $$ BEGIN
  CREATE POLICY "User update own videos" ON storage.objects
    FOR UPDATE USING (
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
  caller_role TEXT := COALESCE(auth.role(), current_setting('request.jwt.claim.role', true), '');
  v_result jsonb;
BEGIN
  IF auth.uid() IS DISTINCT FROM p_user_id
     AND caller_role <> 'service_role'
     AND session_user <> 'postgres' THEN
    RAISE EXCEPTION 'Not allowed to fetch another user stats'
      USING ERRCODE = '42501';
  END IF;

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

REVOKE ALL ON FUNCTION public.get_user_stats(UUID) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_user_stats(UUID) FROM anon;
GRANT EXECUTE ON FUNCTION public.get_user_stats(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_user_stats(UUID) TO service_role;


-- -----------------------------------------------------------------------------
-- 8.3  get_coach_context(p_user_id uuid, p_summary_limit int)
--      Called by chat context builder. Returns compact coach context payload.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.get_coach_context(
  p_user_id uuid,
  p_summary_limit int DEFAULT 5
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  caller_role TEXT := COALESCE(auth.role(), current_setting('request.jwt.claim.role', true), '');
  v_limit int := GREATEST(1, LEAST(COALESCE(p_summary_limit, 5), 20));
BEGIN
  IF auth.uid() IS DISTINCT FROM p_user_id
     AND caller_role <> 'service_role'
     AND session_user <> 'postgres' THEN
    RAISE EXCEPTION 'Not allowed to fetch another user coach context'
      USING ERRCODE = '42501';
  END IF;

  RETURN jsonb_build_object(
    'user', (
      SELECT COALESCE(row_to_json(u)::jsonb, '{}'::jsonb)
      FROM (
        SELECT id, name, skill_level, position
        FROM users
        WHERE id = p_user_id
      ) u
    ),
    'profile', (
      SELECT COALESCE(row_to_json(up)::jsonb, '{}'::jsonb)
      FROM (
        SELECT
          coaching_style,
          primary_goal,
          training_frequency,
          years_playing,
          dominant_hand
        FROM user_profiles
        WHERE user_id = p_user_id
      ) up
    ),
    'stats', COALESCE(public.get_user_stats(p_user_id), '{}'::jsonb),
    'summaries', COALESCE((
      SELECT jsonb_agg(row_to_json(s)::jsonb)
      FROM (
        SELECT created_at, overall_score, score_tier, top_improvements, top_strengths
        FROM analysis_summaries
        WHERE user_id = p_user_id
        ORDER BY created_at DESC
        LIMIT v_limit
      ) s
    ), '[]'::jsonb),
    'recent_chat', COALESCE((
      SELECT jsonb_agg(row_to_json(ch)::jsonb)
      FROM (
        SELECT role, content, created_at
        FROM chat_history
        WHERE user_id = p_user_id
        ORDER BY created_at DESC
        LIMIT 20
      ) ch
    ), '[]'::jsonb)
  );
END;
$$;

REVOKE ALL ON FUNCTION public.get_coach_context(UUID, INT) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.get_coach_context(UUID, INT) FROM anon;
GRANT EXECUTE ON FUNCTION public.get_coach_context(UUID, INT) TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_coach_context(UUID, INT) TO service_role;


-- -----------------------------------------------------------------------------
-- 8.4  update_user_streak(p_user_id uuid)
--      Called by db.update_streak().  Bumps streak if activity today or yesterday.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_user_streak(p_user_id UUID)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  v_today date := CURRENT_DATE;
  v_last_date date;
  v_current_streak int;
  v_longest_streak int;
BEGIN
  -- Atomic upsert: create row if absent, otherwise do nothing but lock the row
  INSERT INTO public.user_streaks (user_id, current_streak, longest_streak, last_activity_date, total_sessions)
  VALUES (p_user_id, 1, 1, v_today, 1)
  ON CONFLICT (user_id) DO UPDATE
    SET total_sessions = user_streaks.total_sessions + 1
    -- only increment total_sessions here; streak logic below uses RETURNING
  RETURNING last_activity_date, current_streak, longest_streak
  INTO v_last_date, v_current_streak, v_longest_streak;

  -- If this is the first insert (v_last_date = v_today from the INSERT), we're done
  IF v_last_date = v_today AND v_current_streak = 1 THEN
    RETURN; -- fresh row, already set correctly
  END IF;

  -- Streak update logic (safe: we hold the row lock from the upsert above)
  IF v_last_date = v_today THEN
    -- Already counted today (duplicate call), just return
    RETURN;
  ELSIF v_last_date = v_today - INTERVAL '1 day' THEN
    -- Consecutive day — extend streak
    UPDATE public.user_streaks
    SET current_streak = v_current_streak + 1,
        longest_streak = GREATEST(v_longest_streak, v_current_streak + 1),
        last_activity_date = v_today
    WHERE user_id = p_user_id;
  ELSE
    -- Streak broken — reset
    UPDATE public.user_streaks
    SET current_streak = 1,
        last_activity_date = v_today
    WHERE user_id = p_user_id;
  END IF;
END;
$$;


-- -----------------------------------------------------------------------------
-- 8.5  public.update_user_full_atomic(p_user_id uuid, p_core jsonb, p_profile jsonb)
--      Atomic RPC for user + profile updates with caller boundary checks.
-- -----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.update_user_full_atomic(
  p_user_id UUID,
  p_core JSONB DEFAULT '{}'::jsonb,
  p_profile JSONB DEFAULT '{}'::jsonb
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  caller_role TEXT := COALESCE(auth.role(), current_setting('request.jwt.claim.role', true), '');
  core_allowed CONSTANT TEXT[] := ARRAY[
    'name',
    'username',
    'skill_level',
    'position',
    'has_completed_onboarding'
  ];
  profile_allowed CONSTANT TEXT[] := ARRAY[
    'bio',
    'avatar_url',
    'primary_goal',
    'training_frequency',
    'preferred_drill_duration',
    'age',
    'height_cm',
    'weight_kg',
    'dominant_hand',
    'years_playing',
    'notifications_enabled',
    'dark_mode_enabled',
    'analytics_enabled',
    'coaching_style'
  ];
  core_payload JSONB := '{}'::jsonb;
  profile_payload JSONB := '{}'::jsonb;
  out_user users%ROWTYPE;
  out_profile user_profiles%ROWTYPE;
BEGIN
  IF auth.uid() IS DISTINCT FROM p_user_id
     AND caller_role <> 'service_role'
     AND session_user <> 'postgres' THEN
    RAISE EXCEPTION 'Not allowed to update another user profile'
      USING ERRCODE = '42501';
  END IF;

  IF p_core IS NOT NULL THEN
    SELECT COALESCE(jsonb_object_agg(e.key, e.value), '{}'::jsonb)
    INTO core_payload
    FROM jsonb_each(p_core) AS e
    WHERE e.key = ANY(core_allowed);
  END IF;

  IF p_profile IS NOT NULL THEN
    SELECT COALESCE(jsonb_object_agg(e.key, e.value), '{}'::jsonb)
    INTO profile_payload
    FROM jsonb_each(p_profile) AS e
    WHERE e.key = ANY(profile_allowed);
  END IF;

  UPDATE users
  SET
    name = CASE WHEN core_payload ? 'name' THEN core_payload->>'name' ELSE name END,
    username = CASE WHEN core_payload ? 'username' THEN core_payload->>'username' ELSE username END,
    skill_level = CASE WHEN core_payload ? 'skill_level' THEN core_payload->>'skill_level' ELSE skill_level END,
    position = CASE WHEN core_payload ? 'position' THEN core_payload->>'position' ELSE position END,
    has_completed_onboarding = CASE
      WHEN core_payload ? 'has_completed_onboarding'
      THEN (core_payload->>'has_completed_onboarding')::boolean
      ELSE has_completed_onboarding
    END
  WHERE id = p_user_id
  RETURNING * INTO out_user;

  IF out_user.id IS NULL THEN
    RAISE EXCEPTION 'User % not found', p_user_id;
  END IF;

  INSERT INTO user_profiles (
    user_id,
    bio,
    avatar_url,
    primary_goal,
    training_frequency,
    preferred_drill_duration,
    age,
    height_cm,
    weight_kg,
    dominant_hand,
    years_playing,
    notifications_enabled,
    dark_mode_enabled,
    analytics_enabled,
    coaching_style
  )
  VALUES (
    p_user_id,
    CASE WHEN profile_payload ? 'bio' THEN profile_payload->>'bio' ELSE NULL END,
    CASE WHEN profile_payload ? 'avatar_url' THEN profile_payload->>'avatar_url' ELSE NULL END,
    CASE WHEN profile_payload ? 'primary_goal' THEN profile_payload->>'primary_goal' ELSE NULL END,
    CASE WHEN profile_payload ? 'training_frequency' THEN profile_payload->>'training_frequency' ELSE NULL END,
    CASE WHEN profile_payload ? 'preferred_drill_duration' THEN (profile_payload->>'preferred_drill_duration')::integer ELSE NULL END,
    CASE WHEN profile_payload ? 'age' THEN (profile_payload->>'age')::integer ELSE NULL END,
    CASE WHEN profile_payload ? 'height_cm' THEN (profile_payload->>'height_cm')::double precision ELSE NULL END,
    CASE WHEN profile_payload ? 'weight_kg' THEN (profile_payload->>'weight_kg')::double precision ELSE NULL END,
    CASE WHEN profile_payload ? 'dominant_hand' THEN profile_payload->>'dominant_hand' ELSE NULL END,
    CASE WHEN profile_payload ? 'years_playing' THEN (profile_payload->>'years_playing')::integer ELSE NULL END,
    CASE WHEN profile_payload ? 'notifications_enabled' THEN (profile_payload->>'notifications_enabled')::boolean ELSE NULL END,
    CASE WHEN profile_payload ? 'dark_mode_enabled' THEN (profile_payload->>'dark_mode_enabled')::boolean ELSE NULL END,
    CASE WHEN profile_payload ? 'analytics_enabled' THEN (profile_payload->>'analytics_enabled')::boolean ELSE NULL END,
    CASE WHEN profile_payload ? 'coaching_style' THEN profile_payload->>'coaching_style' ELSE NULL END
  )
  ON CONFLICT (user_id) DO UPDATE
  SET
    bio = CASE WHEN profile_payload ? 'bio' THEN EXCLUDED.bio ELSE user_profiles.bio END,
    avatar_url = CASE WHEN profile_payload ? 'avatar_url' THEN EXCLUDED.avatar_url ELSE user_profiles.avatar_url END,
    primary_goal = CASE WHEN profile_payload ? 'primary_goal' THEN EXCLUDED.primary_goal ELSE user_profiles.primary_goal END,
    training_frequency = CASE WHEN profile_payload ? 'training_frequency' THEN EXCLUDED.training_frequency ELSE user_profiles.training_frequency END,
    preferred_drill_duration = CASE
      WHEN profile_payload ? 'preferred_drill_duration' THEN EXCLUDED.preferred_drill_duration
      ELSE user_profiles.preferred_drill_duration
    END,
    age = CASE WHEN profile_payload ? 'age' THEN EXCLUDED.age ELSE user_profiles.age END,
    height_cm = CASE WHEN profile_payload ? 'height_cm' THEN EXCLUDED.height_cm ELSE user_profiles.height_cm END,
    weight_kg = CASE WHEN profile_payload ? 'weight_kg' THEN EXCLUDED.weight_kg ELSE user_profiles.weight_kg END,
    dominant_hand = CASE WHEN profile_payload ? 'dominant_hand' THEN EXCLUDED.dominant_hand ELSE user_profiles.dominant_hand END,
    years_playing = CASE WHEN profile_payload ? 'years_playing' THEN EXCLUDED.years_playing ELSE user_profiles.years_playing END,
    notifications_enabled = CASE
      WHEN profile_payload ? 'notifications_enabled' THEN EXCLUDED.notifications_enabled
      ELSE user_profiles.notifications_enabled
    END,
    dark_mode_enabled = CASE
      WHEN profile_payload ? 'dark_mode_enabled' THEN EXCLUDED.dark_mode_enabled
      ELSE user_profiles.dark_mode_enabled
    END,
    analytics_enabled = CASE
      WHEN profile_payload ? 'analytics_enabled' THEN EXCLUDED.analytics_enabled
      ELSE user_profiles.analytics_enabled
    END,
    coaching_style = CASE WHEN profile_payload ? 'coaching_style' THEN EXCLUDED.coaching_style ELSE user_profiles.coaching_style END
  RETURNING * INTO out_profile;

  RETURN json_build_object(
    'user', row_to_json(out_user),
    'profile', row_to_json(out_profile)
  );
END;
$$;

REVOKE ALL ON FUNCTION public.update_user_full_atomic(UUID, JSONB, JSONB) FROM PUBLIC;
REVOKE ALL ON FUNCTION public.update_user_full_atomic(UUID, JSONB, JSONB) FROM anon;
GRANT EXECUTE ON FUNCTION public.update_user_full_atomic(UUID, JSONB, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION public.update_user_full_atomic(UUID, JSONB, JSONB) TO service_role;


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
