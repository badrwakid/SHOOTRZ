# Data persistence test plan

## Automated (backend)

- `pytest backend/tests/test_analysis_complete.py` — mocks `mvp_service.save_result_for_user`; asserts JWT override and 200/400 behavior.

## Manual flows

### A — Commit analysis (signed in)

1. Log in.
2. Run MVP analysis; wait for completion.
3. Confirm network: `POST /api/analysis/complete` returns 200.
4. Open Progress: sessions appear with expected scores.
5. Open Coach J: context references recent summaries (when available).

### B — Guest

1. Sign out.
2. Run analysis; confirm no 401 on complete (skipped); local cache still optional.

### C — Home vs Progress consistency

1. As logged-in user with zero server sessions, confirm Home does not silently use only local data unless API fails (then scoped local fallback).

### D — Logout

1. Log out; confirm AsyncStorage cleared; no prior user’s analysis list.

### E — Account switch

1. Sign in as user A; note cache.
2. Sign out; sign in as user B; confirm A’s cached analyses are not shown.

### F — Delete account

1. Delete account from Profile; confirm 200 from `DELETE /api/user/account`, app returns to login, cannot sign in with same credentials.

### Failure cases

- Complete before job finished → 400 from API; app should still show MVP result from poll.
- Complete with expired token → 401; user should refresh session or re-login.
- Network loss on complete → optional local cache; Progress may lag until retry or next session.
