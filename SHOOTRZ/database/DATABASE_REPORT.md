# SHOOTRZ Database Migration Report

**Migration file:** `database/migrations/001_full_schema_rebuild.sql`
**Date:** 2026-04-10
**Status:** Ready to run in Supabase SQL Editor

---

## 1. Schema Changes

### Tables Dropped
| Table | Reason |
|-------|--------|
| `public.models` | Orphaned — no RLS policies, no FK, not used by any backend or mobile code |

### Tables Created
| Table | Purpose |
|-------|---------|
| `user_profiles` | Extended profile (coaching style, training preferences, physical info) — used by Coach J context |
| `analysis_summaries` | Compact MVP analysis result — prevents Gemini 429 token explosion |
| `chat_history` | Coach J conversation persistence (replaces AsyncStorage-only chat) |
| `drill_completions` | Track completed drills (moved from AsyncStorage) |
| `workout_progress` | Track workout plan progress (moved from AsyncStorage) |
| `user_streaks` | Daily training streak tracking |

### Columns Removed
| Table | Column | Reason |
|-------|--------|--------|
| `videos` | `angle` (text) | Duplicates `camera_angle` (enum) |
| `videos` | `device` (text) | Duplicates `device_info` (jsonb) |
| `sessions` | `date` | Redundant — derivable from `timestamp` |

### Columns Added
| Table | Column | Type |
|-------|--------|------|
| `sessions` | `overall_score` | double precision |
| `sessions` | `shot_count` | integer (default 0) |
| `sessions` | `duration_seconds` | double precision |
| `sessions` | `notes` | text |
| `sessions` | `updated_at` | timestamptz |
| `videos` | `duration_seconds` | double precision |
| `videos` | `file_size_bytes` | bigint |
| `videos` | `resolution` | text |
| `videos` | `processing_status` | text (constrained enum) |
| `videos` | `job_id` | text |
| `videos` | `updated_at` | timestamptz |
| `users` | `goals` | text[] |
| `users` | `dominant_hand` | text (left/right) |
| `users` | `height_cm` | double precision |
| `users` | `updated_at` | timestamptz |

### Constraints Fixed
| Table | Fix |
|-------|-----|
| `sessions` | Removed duplicate FK constraint on `user_id` |
| `users` | `INSERT` policy now has `WITH CHECK (auth.uid() = id)` |

### Indexes Created
| Index | Table | Columns |
|-------|-------|---------|
| `idx_sessions_user_timestamp` | sessions | (user_id, timestamp DESC) |
| `idx_videos_user_created` | videos | (user_id, created_at DESC) |
| `idx_metrics_video` | metrics | (video_id) |
| `idx_feedback_metric` | feedback | (metric_id) |
| `idx_analysis_summaries_user` | analysis_summaries | (user_id, created_at DESC) |
| `idx_chat_history_user_created` | chat_history | (user_id, created_at DESC) |
| `idx_drill_completions_user` | drill_completions | (user_id, completed_at DESC) |

### Database Functions Created
| Function | Purpose |
|----------|---------|
| `handle_updated_at()` | Trigger: auto-set `updated_at` on UPDATE |
| `handle_new_user()` | Trigger: auto-create `user_profiles` + `user_streaks` row on INSERT into `users` |
| `update_user_streak(p_user_id)` | RPC: increment/reset streak based on last activity date |
| `get_user_stats(p_user_id)` | RPC: return aggregated stats as jsonb (total sessions, avg score, streak, etc.) |

---

## 2. RLS Audit

| Table | Policy Name | Command | Protection |
|-------|-------------|---------|------------|
| `users` | "Users can insert themselves" | INSERT | `WITH CHECK (auth.uid() = id)` |
| `user_profiles` | "Users manage own profile" | ALL | `USING/WITH CHECK (auth.uid() = user_id)` |
| `analysis_summaries` | "Users manage own analysis summaries" | ALL | `USING/WITH CHECK (auth.uid() = user_id)` |
| `chat_history` | "Users manage own chat history" | ALL | `USING/WITH CHECK (auth.uid() = user_id)` |
| `drill_completions` | "Users manage own drill completions" | ALL | `USING/WITH CHECK (auth.uid() = user_id)` |
| `workout_progress` | "Users manage own workout progress" | ALL | `USING/WITH CHECK (auth.uid() = user_id)` |
| `user_streaks` | "Users manage own streak" | ALL | `USING/WITH CHECK (auth.uid() = user_id)` |

> **Note:** Backend uses `service_role` key which bypasses RLS. RLS protects against direct client access via anon key.

---

## 3. Backend Endpoints

### Existing Endpoints (updated)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/mvp/analyze` | No* | Upload video for MVP analysis |
| GET | `/mvp/result/{job_id}` | No* | Poll MVP job result |
| GET | `/mvp/artifacts/{run_id}/{filename}` | No | Serve analysis artifacts |
| POST | `/chat` | Yes | Batch Coach J chat |
| POST | `/chat/stream` | Yes | Streaming Coach J chat (SSE) |
| GET | `/history/{user_id}` | No* | User analysis history |
| GET | `/history/{user_id}/stats` | No* | Aggregated history stats |
| GET | `/feedback/video/{video_id}` | No | Video feedback |
| POST | `/feedback/generate` | No | Generate feedback from metrics |
| POST | `/sessions/{user_id}` | No* | Create session |
| GET | `/sessions/{session_id}` | No | Get session details |
| POST | `/sessions/{sid}/videos/{vid}` | No | Add video to session |
| GET | `/sessions/user/{user_id}` | No* | Get user sessions |
| GET | `/health` | No | Health check |

### New Endpoints (added in this migration)
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/chat/history` | Yes | Get persisted chat history |
| DELETE | `/chat/history` | Yes | Clear chat history |
| GET | `/api/user/profile` | Yes | Get user + profile merged |
| PUT | `/api/user/profile` | Yes | Update user_profiles table |
| GET | `/api/user/stats` | Yes | Calls `get_user_stats` DB function |
| GET | `/api/user/streak` | Yes | Get current streak |
| GET | `/api/sessions` | Yes | Paginated session list |
| GET | `/api/sessions/{id}` | Yes | Single session with summary |
| GET | `/api/drills/completions` | Yes | User drill completion history |
| POST | `/api/drills/complete` | Yes | Log a drill completion |
| GET | `/api/workouts/progress` | Yes | User workout progress |
| PUT | `/api/workouts/{id}/progress` | Yes | Update workout progress |

> `*` = These older endpoints accept user_id as a path parameter. New endpoints derive user_id from the auth token.

---

## 4. Data Flow Map

### MVP Analysis
```
Mobile uploads video → POST /mvp/analyze
Backend pipeline runs → writes to local SQLite job store
Mobile polls GET /mvp/result/{job_id}
When authenticated endpoint saves results:
  → sessions (new row: overall_score, shot_count)
  → videos (new row: processing_status=completed, job_id)
  → metrics (metric rows per video)
  → analysis_summaries (compact summary for Coach J)
  → user_streaks (streak updated via RPC)
```

### Coach J Chat
```
Mobile sends POST /chat/stream with auth token
Backend builds context:
  → users table (name, skill_level, position)
  → user_profiles table (coaching_style, goals, training_frequency)
  → get_user_stats() RPC (total_sessions, avg_score, streak)
  → analysis_summaries (last 5 sessions — compact, no raw pose data)
Backend streams response via SSE
After stream completes:
  → chat_history (user message saved)
  → chat_history (assistant message saved with model, tokens, latency)
Mobile reads GET /chat/history on screen mount
```

### User Profile
```
Mobile reads GET /api/user/profile → users + user_profiles merged
Mobile updates PUT /api/user/profile → user_profiles table
```

### Dashboard / Home Screen
```
Mobile reads GET /api/user/stats → calls get_user_stats() DB function
Mobile reads GET /api/user/streak → user_streaks table
Falls back to AsyncStorage if API unreachable
```

### Drills & Workouts
```
Mobile reads GET /api/drills/completions → drill_completions table
Mobile writes POST /api/drills/complete → drill_completions + streak update
Mobile reads GET /api/workouts/progress → workout_progress table
Mobile writes PUT /api/workouts/{id}/progress → workout_progress table (upsert)
```

---

## 5. AsyncStorage → Supabase Migration Map

### Moved to Supabase (fetched via API)
| AsyncStorage Key | New Source | Endpoint |
|------------------|-----------|----------|
| `@shootrz_analysis_history` | `sessions` + `analysis_summaries` | `GET /api/sessions`, `GET /api/user/stats` |
| `@shootrz_drill_completions` | `drill_completions` table | `GET /api/drills/completions` |
| `@shootrz_workout_history` | `workout_progress` table | `GET /api/workouts/progress` |
| `@shootrz_chat_conversation_v1` | `chat_history` table | `GET /chat/history` |

### Kept in AsyncStorage (appropriate for local-only)
| Key | Reason |
|-----|--------|
| `@shootrz_user_data` | Quick auth check, offline profile cache |
| `@shootrz_preferences` | UI preferences (dark mode, notifications) — non-critical |
| `@shootrz_goals` | Local goal tracking (could migrate later) |
| `@shootrz_onboarding_completed` | One-time flag |

### Migration Function
`StorageService.migrateToSupabase()` in `storage.service.ts`:
- Reads existing drill completions and workout history from AsyncStorage
- POSTs each to the respective Supabase-backed API endpoint
- Clears local copies after successful sync
- Gated by `@shootrz_supabase_migration_v1_complete` flag — runs once

---

## 6. Known Gaps

1. **MVP analysis → Supabase save requires authentication.** The current `/mvp/analyze` endpoint is unauthenticated. `MVPJobService._save_to_supabase()` prepares the summary, but `save_result_for_user()` must be called from an authenticated context. A future endpoint like `POST /api/sessions/save-analysis` should be added where the mobile app sends `{ job_id }` with auth, triggering the save.

2. **Existing videos table rows** reference the now-dropped `angle` and `device` columns. No existing video data rows exist (0 rows), so this is safe. If there were rows, a data migration would be needed.

3. **Goals table** not created in Supabase — goals are still managed in AsyncStorage. Consider migrating goals to a `user_goals` table in a future migration.

4. **History endpoints** (`GET /history/{user_id}`) still accept user_id as a path param (no auth). These should eventually migrate to auth-only patterns like the new `/api/*` endpoints.

5. **`session_videos` join table** is used by existing code but was not modified in this migration. It continues to work as-is.

6. **Manual testing required:**
   - Run the SQL migration in Supabase SQL Editor
   - Verify `handle_new_user` trigger fires correctly on new user signup
   - Test `update_user_streak` RPC with consecutive-day activity
   - Test chat persistence round-trip (send message → reload screen → see it)
   - Verify Coach J context is compact (no 429 errors on Gemini)
   - Test the AsyncStorage → Supabase one-time migration on app upgrade
