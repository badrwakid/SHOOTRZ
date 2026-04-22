# History route & Expo AV — fix report

## 1. Exact cause of the 404 warning

- **Code in this repo** registers `GET /api/user/analysis-history` (`backend/routers/user.py` + `main.py`).
- **404** means the HTTP **server process** the app talks to does **not** expose that path (stale uvicorn, wrong `app` module, or undeployed production API).
- The client path was already correct; **operations fix** = restart FastAPI from this repo and verify `GET {base}/health` → `has_analysis_history_route: true`.

**Helper:** `python backend/scripts/verify_api_routes.py http://YOUR_IP:8000`

## 2. Expo AV warning — cause and status

- **Cause:** Expo SDK 54 deprecates `expo-av`; importing it logs a framework warning.
- **Usage audit:** Only **annotated overlay playback** in `MVPAnalysisScreen` used `expo-av`. **Camera recording** uses `expo-camera` (unchanged).
- **Fix:** Replaced overlay with **`expo-video`** (`AnalysisOverlayVideo` → `VideoView` + `useVideoPlayer`), removed **`expo-av`** from dependencies, added **`expo-video`** + config plugin in `app.config.js`.

## 3. Files changed

| File | Change |
|------|--------|
| `src/constants/apiEndpoints.ts` | **New** — canonical path constants |
| `src/services/api.service.ts` | Uses `API_PATHS`; one-time `[api] resolved base` log; clearer 404 warning with `/health` hint |
| `src/components/AnalysisOverlayVideo.tsx` | **New** — expo-video overlay |
| `src/screens/MVPAnalysisScreen.tsx` | Uses `AnalysisOverlayVideo` instead of `expo-av` |
| `app.config.js` | `plugins: [..., 'expo-video']` |
| `package.json` / lock | `expo-video` added, `expo-av` removed |
| `backend/scripts/verify_api_routes.py` | **New** — verify health flags |
| `docs/history_route_and_expoav_audit.md` | **New** — audit |
| `docs/history_route_root_cause.md` | **New** — root cause |
| `docs/history_route_fix_report.md` | This file |

**Not changed:** `backend/routers/user.py` route implementation (already correct); legacy `GET /history/{user_id}` fallback kept.

## 4. Testing checklist (manual)

| # | Check | How |
|---|--------|-----|
| 1 | `/docs` lists analysis history | Open `{base}/docs`, search `analysis-history` |
| 2 | Health flags | `GET {base}/health` or `verify_api_routes.py` |
| 3 | Progress loads | Logged-in user with backend restarted |
| 4 | Empty history | New user → empty list, no crash |
| 5 | Fallback | Only when primary 404 (old server) |
| 6 | `/mvp/analyze` | Upload/record still queues job |
| 7 | Overlay | After analysis, annotated video plays with native controls |

## 5. Intentionally not changed

- Chat pipeline (uses backend DB context builder, not this HTTP path for listing).
- Legacy `GET /history/{user_id}` router and fallback behavior.
- `normalizeApiBaseUrl` behavior.

## 6. Remaining risks / follow-up

- **Production** `https://api.shootrz.com` must deploy the same FastAPI revision or clients will keep falling back.
- **expo-video** native rebuild may be required after adding the config plugin (`npx expo prebuild` / EAS) for bare workflow; Expo Go includes expo-video per docs.
- **Typecheck:** Project has pre-existing TS errors in other screens; not introduced by this change.

## 7. Final deliverable summary

| Item | Result |
|------|--------|
| 404 cause | Stale/mismatched server process, not wrong client path |
| expo-av | Removed from app; overlay uses `expo-video` |
| Architecture | Single `API_PATHS` + canonical backend routes; legacy fallback explicit |
