# Audit: analysis history routes & expo-av (SHOOTRZ)

## Frontend — API layer

| File | Behavior | Verdict |
|------|------------|---------|
| `src/services/api.service.ts` | `getAnalysisHistory()` → `GET {base}/api/user/analysis-history`; on **404** falls back to `getHistory(userId)` → `GET {base}/history/{userId}` | Canonical + legacy fallback; warning when primary 404 |
| `src/services/api.service.ts` | `normalizeApiBaseUrl()` strips trailing `/api` | Correct — prevents `/api/api/...` |
| `src/services/api.service.ts` | `completeMVPAnalysis` → `POST {base}/api/analysis/complete` | Active |
| `src/services/api.service.ts` | `deleteAccount` → `DELETE {base}/api/user/account` | Active |
| `src/services/storage.service.ts` | `getAnalysisHistory(userId?)` = **AsyncStorage** (local), not HTTP | Different symbol; no conflict |

## Frontend — call sites

| Location | Calls | Active |
|----------|-------|--------|
| `src/screens/ProgressScreen.tsx` | `apiService.getAnalysisHistory(100, 0)` | Yes |
| `src/screens/HomeScreen.tsx` | `apiService.getAnalysisHistory(5, 0)` + local `storageService.getAnalysisHistory` | Yes |
| `src/context/AuthContext.tsx` | Prefetch `apiService.getAnalysisHistory(20, 0)` | Yes |
| Chat | Uses backend chat router + `build_user_context` (DB), **not** this HTTP path for listing | N/A |

## Frontend — video / audio

| File | Import | Active |
|------|--------|--------|
| `src/screens/MVPAnalysisScreen.tsx` | `expo-av` `Video`, `ResizeMode` — overlay preview only | Yes |
| `src/components/CameraRecorder.tsx` | `expo-camera` `CameraView` | Yes — **not** expo-av |

## Backend

| Route | Router | Prefix | Full path |
|-------|--------|--------|-----------|
| Analysis history | `user.py` | `/api` | `GET /api/user/analysis-history` |
| Complete MVP | `analysis.py` | `/api/analysis` | `POST /api/analysis/complete` |
| Delete account | `user.py` | `/api` | `DELETE /api/user/account` |
| Legacy history | `history.py` | `""` | `GET /history/{user_id}` |

| File | Role |
|------|------|
| `backend/main.py` | Registers `user.router`, `analysis.router`; `/health` exposes `has_*_route` flags |
| `backend/routers/user.py` | Implements `get_analysis_history` with `get_authenticated_user` |
| `backend/storage/db.py` | `get_user_analysis_history()` reads `analysis_summaries` + joins |

## Environment

| Variable | Purpose |
|----------|---------|
| `EXPO_PUBLIC_API_URL` | FastAPI **root** (no `/api` suffix) |

## Warning sources

1. **API 404 warning**: Emitted by **client** (`api.service.ts`) when primary endpoint returns 404 — indicates **running server** lacks that route (stale process), not a wrong path in repo.
2. **expo-av deprecation**: Emitted by **Expo** when `expo-av` is loaded — only `MVPAnalysisScreen` imports it (overlay `Video`).
