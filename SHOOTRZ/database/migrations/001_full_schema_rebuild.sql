-- ============================================================================
-- SHOOTRZ Database Migration 001: Full Schema Rebuild
-- Safe to run in Supabase SQL Editor. Fully idempotent.
-- WARNING: Does NOT drop or truncate public.users (has 1 real row).
-- ============================================================================

-- ============================================================================
-- PART A — CLEANUP (fix existing broken schema)
-- ============================================================================

-- 1. Drop the orphaned models table (no RLS policies, no FK, unused by code)
DROP TABLE IF EXISTS public.models CASCADE;

-- 2. Remove duplicate/redundant columns from videos
--    videos.angle (text) duplicates videos.camera_angle (enum)
--    videos.device (text) duplicates videos.device_info (jsonb)
ALTER TABLE public.videos DROP COLUMN IF EXISTS angle;
ALTER TABLE public.videos DROP COLUMN IF EXISTS device;

-- 3. Fix sessions: remove duplicate FK constraint and redundant date column
DO $$
DECLARE
    r record;
    kept boolean := false;
BEGIN
    FOR r IN
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'sessions'
          AND constraint_type = 'FOREIGN KEY'
          AND table_schema = 'public'
        ORDER BY constraint_name ASC
    LOOP
        IF kept THEN
            EXECUTE 'ALTER TABLE public.sessions DROP CONSTRAINT IF EXISTS ' || quote_ident(r.constraint_name);
        ELSE
            kept := true;
        END IF;
    END LOOP;
END $$;

ALTER TABLE public.sessions DROP COLUMN IF EXISTS date;

-- 4. Add missing columns to existing tables

-- sessions: add fields needed by MVP pipeline
ALTER TABLE public.sessions
    ADD COLUMN IF NOT EXISTS overall_score double precision,
    ADD COLUMN IF NOT EXISTS shot_count integer DEFAULT 0,
    ADD COLUMN IF NOT EXISTS duration_seconds double precision,
    ADD COLUMN IF NOT EXISTS notes text,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- videos: add missing useful fields
ALTER TABLE public.videos
    ADD COLUMN IF NOT EXISTS duration_seconds double precision,
    ADD COLUMN IF NOT EXISTS file_size_bytes bigint,
    ADD COLUMN IF NOT EXISTS resolution text,
    ADD COLUMN IF NOT EXISTS processing_status text DEFAULT 'pending'
        CHECK (processing_status IN ('pending','processing','completed','failed')),
    ADD COLUMN IF NOT EXISTS job_id text,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- users: add missing profile fields needed by Coach J context
ALTER TABLE public.users
    ADD COLUMN IF NOT EXISTS goals text[],
    ADD COLUMN IF NOT EXISTS dominant_hand text CHECK (dominant_hand IN ('left','right')),
    ADD COLUMN IF NOT EXISTS height_cm double precision,
    ADD COLUMN IF NOT EXISTS updated_at timestamptz DEFAULT now();

-- 5. Fix the users INSERT policy (add WITH CHECK clause — security gap fix)
DROP POLICY IF EXISTS "Users can insert themselves" ON public.users;
CREATE POLICY "Users can insert themselves" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);


-- ============================================================================
-- PART B — NEW TABLES
-- ============================================================================

-- user_profiles: extended profile (Coach J uses this for context)
CREATE TABLE IF NOT EXISTS public.user_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    primary_goal text,
    training_frequency text,
    preferred_drill_duration int DEFAULT 15,

    age int,
    height_cm double precision,
    weight_kg double precision,
    dominant_hand text CHECK (dominant_hand IN ('left','right')),
    years_playing int,

    notifications_enabled boolean DEFAULT true,
    coaching_style text DEFAULT 'balanced'
        CHECK (coaching_style IN ('encouraging','direct','analytical','balanced')),

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(user_id)
);

-- analysis_summaries: compact MVP result for Coach J (prevents Gemini 429 token explosion)
CREATE TABLE IF NOT EXISTS public.analysis_summaries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id uuid NOT NULL REFERENCES public.sessions(id) ON DELETE CASCADE,
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    overall_score double precision,
    shot_count int DEFAULT 0,

    elbow_angle_score double precision,
    knee_bend_score double precision,
    release_angle_score double precision,
    follow_through_score double precision,
    balance_score double precision,

    elbow_angle_value double precision,
    knee_bend_value double precision,
    release_angle_value double precision,

    phases_detected text[],
    dominant_phase_issue text,

    top_strengths text[],
    top_improvements text[],

    score_tier text CHECK (score_tier IN ('elite','great','good','fair','poor')),

    created_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(session_id)
);

-- chat_history: Coach J conversation persistence
CREATE TABLE IF NOT EXISTS public.chat_history (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    role text NOT NULL CHECK (role IN ('user','assistant')),
    content text NOT NULL,

    session_id uuid REFERENCES public.sessions(id) ON DELETE SET NULL,

    model_used text,
    token_count int,
    response_time_ms int,

    created_at timestamptz NOT NULL DEFAULT now()
);

-- drill_completions: track which drills users have done
CREATE TABLE IF NOT EXISTS public.drill_completions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    drill_id text NOT NULL,
    drill_name text NOT NULL,

    completed_at timestamptz NOT NULL DEFAULT now(),
    duration_seconds int,

    user_rating int CHECK (user_rating BETWEEN 1 AND 5),
    notes text
);

-- workout_progress: track workout plan progress
CREATE TABLE IF NOT EXISTS public.workout_progress (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    workout_id text NOT NULL,
    workout_name text NOT NULL,

    status text NOT NULL DEFAULT 'in_progress'
        CHECK (status IN ('not_started','in_progress','completed')),

    drills_completed int DEFAULT 0,
    drills_total int NOT NULL DEFAULT 0,

    started_at timestamptz DEFAULT now(),
    completed_at timestamptz,

    UNIQUE(user_id, workout_id)
);

-- user_streaks: daily training streaks
CREATE TABLE IF NOT EXISTS public.user_streaks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES public.users(id) ON DELETE CASCADE,

    current_streak int NOT NULL DEFAULT 0,
    longest_streak int NOT NULL DEFAULT 0,
    last_activity_date date,

    updated_at timestamptz NOT NULL DEFAULT now(),

    UNIQUE(user_id)
);


-- ============================================================================
-- PART C — INDEXES (performance)
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_sessions_user_timestamp
    ON public.sessions(user_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_videos_user_created
    ON public.videos(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_video
    ON public.metrics(video_id);

CREATE INDEX IF NOT EXISTS idx_feedback_metric
    ON public.feedback(metric_id);

CREATE INDEX IF NOT EXISTS idx_analysis_summaries_user
    ON public.analysis_summaries(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_chat_history_user_created
    ON public.chat_history(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_drill_completions_user
    ON public.drill_completions(user_id, completed_at DESC);


-- ============================================================================
-- PART D — RLS POLICIES (security)
-- ============================================================================

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.analysis_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.drill_completions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.workout_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_streaks ENABLE ROW LEVEL SECURITY;

-- user_profiles: full CRUD for own profile
DROP POLICY IF EXISTS "Users manage own profile" ON public.user_profiles;
CREATE POLICY "Users manage own profile" ON public.user_profiles
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- analysis_summaries: read/write own summaries
DROP POLICY IF EXISTS "Users manage own analysis summaries" ON public.analysis_summaries;
CREATE POLICY "Users manage own analysis summaries" ON public.analysis_summaries
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- chat_history: read/write own chat
DROP POLICY IF EXISTS "Users manage own chat history" ON public.chat_history;
CREATE POLICY "Users manage own chat history" ON public.chat_history
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- drill_completions: read/write own completions
DROP POLICY IF EXISTS "Users manage own drill completions" ON public.drill_completions;
CREATE POLICY "Users manage own drill completions" ON public.drill_completions
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- workout_progress: read/write own progress
DROP POLICY IF EXISTS "Users manage own workout progress" ON public.workout_progress;
CREATE POLICY "Users manage own workout progress" ON public.workout_progress
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- user_streaks: read/write own streak
DROP POLICY IF EXISTS "Users manage own streak" ON public.user_streaks;
CREATE POLICY "Users manage own streak" ON public.user_streaks
    FOR ALL USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);


-- ============================================================================
-- PART E — DATABASE FUNCTIONS (server-side logic)
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS trigger AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE OR REPLACE TRIGGER handle_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE OR REPLACE TRIGGER handle_sessions_updated_at
    BEFORE UPDATE ON public.sessions
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE OR REPLACE TRIGGER handle_videos_updated_at
    BEFORE UPDATE ON public.videos
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE OR REPLACE TRIGGER handle_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

CREATE OR REPLACE TRIGGER handle_user_streaks_updated_at
    BEFORE UPDATE ON public.user_streaks
    FOR EACH ROW EXECUTE FUNCTION public.handle_updated_at();

-- Auto-create user_profile + user_streak on new user
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger AS $$
BEGIN
    INSERT INTO public.user_profiles (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;

    INSERT INTO public.user_streaks (user_id)
    VALUES (NEW.id)
    ON CONFLICT (user_id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE OR REPLACE TRIGGER on_user_created
    AFTER INSERT ON public.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Update streak when user completes a session
CREATE OR REPLACE FUNCTION public.update_user_streak(p_user_id uuid)
RETURNS void AS $$
DECLARE
    v_last_date date;
    v_today date := CURRENT_DATE;
    v_current integer;
    v_longest integer;
BEGIN
    SELECT last_activity_date, current_streak, longest_streak
    INTO v_last_date, v_current, v_longest
    FROM public.user_streaks
    WHERE user_id = p_user_id;

    IF NOT FOUND THEN
        INSERT INTO public.user_streaks (user_id, current_streak, longest_streak, last_activity_date)
        VALUES (p_user_id, 1, 1, v_today);
        RETURN;
    END IF;

    IF v_last_date = v_today THEN
        RETURN;
    ELSIF v_last_date = v_today - INTERVAL '1 day' THEN
        v_current := v_current + 1;
    ELSE
        v_current := 1;
    END IF;

    v_longest := GREATEST(v_longest, v_current);

    UPDATE public.user_streaks
    SET current_streak = v_current,
        longest_streak = v_longest,
        last_activity_date = v_today,
        updated_at = now()
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Get user stats summary (used by Coach J context builder)
CREATE OR REPLACE FUNCTION public.get_user_stats(p_user_id uuid)
RETURNS jsonb AS $$
DECLARE
    v_result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'total_sessions', COALESCE(COUNT(DISTINCT s.id), 0),
        'avg_score', ROUND(COALESCE(AVG(s.overall_score), 0)::numeric, 1),
        'best_score', COALESCE(MAX(s.overall_score), 0),
        'total_shots', COALESCE(SUM(s.shot_count), 0),
        'current_streak', COALESCE(us.current_streak, 0),
        'longest_streak', COALESCE(us.longest_streak, 0),
        'last_session_date', MAX(s.timestamp)
    ) INTO v_result
    FROM public.sessions s
    LEFT JOIN public.user_streaks us ON us.user_id = p_user_id
    WHERE s.user_id = p_user_id;

    RETURN COALESCE(v_result, '{}'::jsonb);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Backfill: create user_profiles and user_streaks for existing users
INSERT INTO public.user_profiles (user_id)
SELECT id FROM public.users
WHERE id NOT IN (SELECT user_id FROM public.user_profiles)
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO public.user_streaks (user_id)
SELECT id FROM public.users
WHERE id NOT IN (SELECT user_id FROM public.user_streaks)
ON CONFLICT (user_id) DO NOTHING;
