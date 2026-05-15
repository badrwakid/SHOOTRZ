-- Atomic user + profile update RPC for /api/user/profile

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
