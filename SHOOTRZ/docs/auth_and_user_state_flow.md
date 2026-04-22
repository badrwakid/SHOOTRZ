# Auth and user state flow

## Cold start

1. `supabase.auth.getSession()` restores a session if present.
2. User profile is loaded into React state and persisted to `@shootrz_user_data`.
3. If the restored user id differs from the previous session’s id, scoped analysis cache for the prior id is cleared.

## Sign-in

1. Password / OAuth completes → `onAuthStateChange` fires with `session.user`.
2. On **user id change** (account switch), previous user’s namespaced analysis cache is removed.
3. A background prefetch runs: `getUserStats`, `getUserStreak`, `getAnalysisHistory` so Home/Progress warm quickly.

## Sign-out

1. `logout()` clears user state, AsyncStorage (including all analysis keys), and calls `supabase.auth.signOut()`.

## Delete account

1. `DELETE /api/user/account` with Bearer token removes public rows in FK-safe order, then `auth.admin.delete_user`.
2. Client calls `logout()` (or clears storage if the session is already invalid).

## Threat model note

Open `GET /history/{user_id}` must not be used in production clients; authenticated routes enforce `user_id` from the JWT.
