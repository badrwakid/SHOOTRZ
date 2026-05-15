-- Persist profile preference flags on user_profiles for existing databases.
-- Safe to re-run.

ALTER TABLE public.user_profiles
	ADD COLUMN IF NOT EXISTS dark_mode_enabled boolean NOT NULL DEFAULT true,
	ADD COLUMN IF NOT EXISTS analytics_enabled boolean NOT NULL DEFAULT true;

ALTER TABLE public.user_profiles
	ADD COLUMN IF NOT EXISTS notifications_enabled boolean;

-- Align notifications column with canonical schema requirements.
UPDATE public.user_profiles
SET notifications_enabled = true
WHERE notifications_enabled IS NULL;

ALTER TABLE public.user_profiles
	ALTER COLUMN notifications_enabled SET DEFAULT true;

ALTER TABLE public.user_profiles
	ALTER COLUMN notifications_enabled SET NOT NULL;
