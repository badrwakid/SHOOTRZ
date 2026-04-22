# Root cause analysis — Supabase persistence

## 1. Completed analyses not stored for logged-in users

`MVPJobService.save_result_for_user` existed but was never invoked from the API after `/mvp/analyze` completed. The analyze route is intentionally unauthenticated (guest uploads). The mobile app only called `storageService.saveAnalysisResult` locally, so Supabase never received `sessions`, `videos`, `metrics`, or `analysis_summaries` for authenticated users.

**Evidence:** No caller of `save_result_for_user` except the new `POST /api/analysis/complete` handler.

## 2. Progress and history read empty tables

`GET /history/{user_id}` depended on `videos` rows. Without the commit step, history stayed empty. Even when data existed, the legacy route could mislabel identifiers and averaged raw metric angles instead of MVP `overall_score`.

## 3. Split brain: Home vs Progress

Home fell back to AsyncStorage when server `totalSessions` was zero; Progress used only the server. After login, dashboards could disagree.

## 4. Delete account

Client-side deletes against Supabase with the anon key are unreliable under RLS and omitted dependent tables. Account removal now runs through the backend with the service role and Auth Admin API.

## 5. Local storage not user-scoped

Global `@shootrz_analysis_history` could show another user’s cached analyses if the session changed without a full clear. Analysis history keys are now namespaced per user where applicable, with explicit clear on user id change.
