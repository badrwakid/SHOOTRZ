-- Creates a single RPC to fetch all coach context data in one round-trip.
-- Replaces the 4 sequential queries in context_builder.py:build_user_context.

CREATE OR REPLACE FUNCTION get_coach_context(p_user_id UUID, p_summary_limit INT DEFAULT 5)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'user',      (SELECT row_to_json(u)  FROM users u        WHERE u.id = p_user_id),
    'profile',   (SELECT row_to_json(up) FROM user_profiles up WHERE up.user_id = p_user_id),
    'stats',     get_user_stats(p_user_id),
    'summaries', (
      SELECT COALESCE(json_agg(s ORDER BY s.created_at DESC), '[]'::json)
      FROM (
        SELECT * FROM analysis_summaries
        WHERE user_id = p_user_id
        ORDER BY created_at DESC
        LIMIT p_summary_limit
      ) s
    )
  ) INTO result;
  RETURN result;
END;
$$;
