# Data persistence audit (SHOOTRZ)

| Area | Feature | Source of truth | Persistence | Auth tie | Risk (before) | Fix |
|------|---------|-----------------|-------------|----------|---------------|-----|
| MVP pipeline | Job queue / result | FastAPI `MVPJobService` + SQLite job store | Ephemeral until commit | None on `/mvp/analyze` | Completed analyses never reached Supabase for signed-in users | `POST /api/analysis/complete` with Bearer + `save_result_for_user` |
| Dashboard | Stats / streak | Supabase RPC + `user_streaks` | Server | JWT on `/api/user/*` | Home used local AsyncStorage when `totalSessions === 0` | Logged-in users always prefer `getUserStats` / `getAnalysisHistory` with offline fallback |
| Progress | Session list / charts | `analysis_summaries` + metrics | Server | JWT | Open `GET /history/{user_id}` + wrong score semantics | `GET /api/user/analysis-history` + map `overall_score` |
| Coach J | Chat context | `analysis_summaries`, profiles, stats | Server | JWT | Empty summaries if nothing committed | Resolved once commit path runs; logging when summaries count is zero |
| Profile | Delete account | N/A | Mixed | Anon Supabase client deletes | RLS blocks / partial deletes | `DELETE /api/user/account` (service role + `auth.admin.delete_user`) |
| Local cache | Analysis history | AsyncStorage | Device | Not scoped | Cross-user bleed on shared device | Keys scoped by `userId`; clear on account switch |

This table reflects the intended architecture after the repair: **verified writes** use `user_id` from JWT; **reads** for product surfaces use authenticated routes.
