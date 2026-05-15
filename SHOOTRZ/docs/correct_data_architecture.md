# Correct data architecture

## Identity

- **Supabase Auth** is the identity provider. The FastAPI backend validates `Authorization: Bearer <access_token>` and derives `user_id` for all authenticated routes.

## Canonical entities (public schema)

1. **`users`** — App profile row keyed by `id` = `auth.users.id`.
2. **`sessions`** — One logical “shot session” per analysis commit.
3. **`videos`** — Stored video metadata and linkage to the user.
4. **`session_videos`** — Join session ↔ video.
5. **`metrics`** — Per-video biomechanical metrics.
6. **`analysis_summaries`** — MVP `overall_score`, tiers, strengths, improvements (what the UI and Coach J should use as “score”).
7. **`user_streaks`**, **`user_profiles`** — Derived / preference data.

## Write path (MVP)

1. `POST /mvp/analyze` → job id (no auth required).
2. `GET /mvp/result/{job_id}` → poll until `completed`.
3. **If the user is logged in:** `POST /api/analysis/complete` `{ job_id }` with Bearer token → `save_result_for_user` writes DB rows and summary.

## Read path

- **Stats / streak:** authenticated user routes backed by `get_user_stats` and streak tables.
- **History / Progress:** `GET /api/user/analysis-history` returns summaries joined with session/video/metrics; charts use `overall_score` / `average_score` from summaries, not ad-hoc averages of angle metrics.

## AsyncStorage

Optional offline cache only; not authoritative for signed-in users. Cleared on logout; analysis cache can be cleared when the auth user id changes.
