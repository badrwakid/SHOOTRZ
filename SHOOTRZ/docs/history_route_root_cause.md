# Root cause — history 404 warning & expo-av

## 1. `GET /api/user/analysis-history` (404 + client warning)

### Exact cause

- **Repository state**: `backend/routers/user.py` defines `@router.get("/user/analysis-history")` on `APIRouter(prefix="/api")`, and `backend/main.py` includes `user.router`. The **intended** URL is **`/api/user/analysis-history`**.
- **Runtime state**: The HTTP client receives **404 Not Found** for that path against `http://192.168.1.43:8000`. A 404 means the **process bound to port 8000** did not register that path at request time.
- **Verified earlier**: OpenAPI from a stale local server listed `/api/user/stats` but **not** `/api/user/analysis-history` nor `/api/analysis/complete` — consistent with an **older uvicorn worker** or a **different app** than `backend.main:app` from the current tree.

### What this is not

- **Not** a frontend typo: the client uses `/api/user/analysis-history` matching the repo.
- **Not** auth hiding the route: missing auth yields **401**, not 404.
- **Not** duplicate prefix in env after `normalizeApiBaseUrl` (unless mis-set elsewhere).

### Role of fallback

- `getAnalysisHistory` catches **404** and calls legacy `GET /history/{user_id}` so Progress does not hard-fail.
- Legacy data shape differs (video-centric vs summary-centric); the warning alerts that **canonical MVP history is unavailable** until the server matches the repo.

## 2. Expo AV deprecation warning

### Exact cause

- `expo-av` is **deprecated** in Expo SDK 54; Expo logs a framework warning when the module loads.
- **Only** `src/screens/MVPAnalysisScreen.tsx` imports `expo-av` (for **annotated overlay playback**). Recording uses `expo-camera`, not `expo-av`.

### Migration status

- Replacing overlay playback with **`expo-video`** (`VideoView` + `useVideoPlayer`) removes the deprecation warning for that usage path without touching camera recording.
