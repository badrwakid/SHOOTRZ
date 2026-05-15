-- Creates a single RPC to fetch all coach context data in one round-trip.
-- Replaces the 4 sequential queries in context_builder.py:build_user_context.

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
