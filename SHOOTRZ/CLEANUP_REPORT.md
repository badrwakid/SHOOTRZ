# SHOOTRZ Codebase Cleanup Report

**Cleanup Date:** 2026-04-09
**Scope:** Dead file deletion, debug statement removal, unused import cleanup
**Prerequisite:** BUG_REPORT.md fixes (Agent 1) applied first

---

## Summary

| Category | Count |
|----------|-------|
| Files deleted | 6 |
| Directories removed | 2 (empty after deletion) |
| Files with console.log/print removed | 15 |
| Files with unused imports removed | 18 |
| Estimated lines removed | ~380 |
| Files marked UNCERTAIN (kept) | ~130 (scripts, models, graveyard) |

---

## Phase 1 — Dependency Graph

Entry points traced:
- **Backend:** `backend/main.py` → 8 routers → services, inference, MVP pipeline, recommender, chat, feedback, storage, utils
- **Frontend:** `App.tsx` → `AppNavigator` → 8 screens → components, services, hooks, utils, types, constants

All 57 backend Python modules and 41 frontend TypeScript modules reachable from entry points confirmed as **LIVE**.

---

## Phase 2 — Files Deleted

| File | Lines | Reason Dead | Confirmed Not Imported By |
|------|-------|-------------|---------------------------|
| `backend/middleware/request_logging.py` | 54 | Not wired in `main.py`, not imported by any module | Grep across full backend |
| `backend/metrics/consistency.py` | 13 | Stub (`{"intra_session_std": 0.0}`), not imported anywhere | Grep across full backend |
| `backend/utils/video_io.py` | 14 | Placeholder (`extract_frames` returns `[]`), not imported | Grep across full backend + scripts |
| `backend/utils/smoothing.py` | 20 | Superseded by `mvp/core/signal_smoothing.py`, not imported | Grep across full backend + scripts |
| `backend/diagnose_health.py` | 79 | One-off diagnostic script for B28 (health endpoint). Issue now fixed. Not referenced by any file | Grep across full repo |
| `src/config/supabase.config.ts` | 47 | Exports `USE_SUPABASE`, `TABLES`, `STORAGE_BUCKETS` — zero imports anywhere. Real client is `src/services/supabase.client.ts` | Grep across full frontend |

**Directories removed:** `backend/middleware/` and `src/config/` (both empty after file deletion)

---

## Phase 3A — Debug Statement Removal

Removed `console.log()` and `print()` debug/trace statements. Preserved `console.error()`, `console.warn()`, and any logging inside explicit error handlers.

| File | Statements Removed | Kept |
|------|--------------------|------|
| `src/context/AuthContext.tsx` | ~55 console.log | All console.error (35), console.warn (7) |
| `src/hooks/useDeepLinks.ts` | ~28 console.log | All console.error (10), console.warn (2) |
| `src/screens/ProfileScreen.tsx` | 14 console.log | All console.error/warn (13) |
| `App.tsx` | 11 console.log | console.warn (1), console.error (1) |
| `src/screens/HomeScreen.tsx` | 10 console.log | console.error in catch (1) |
| `src/services/api.service.ts` | 6 console.log (+ empty `__DEV__` blocks) | console.error (10) |
| `src/screens/UsernameScreen.tsx` | 5 console.log | console.error (5) |
| `src/screens/LoginScreen.tsx` | 3 console.log | console.error (2) |
| `src/components/CameraRecorder.tsx` | 3 console.log | console.error/warn (4) |
| `src/screens/MVPAnalysisScreen.tsx` | 1 console.log | console.error (6) |
| `src/services/storage.service.ts` | 1 console.log | console.error (20) |
| `backend/utils/video_annotator.py` | 2 print() | None in these blocks (error handler print in `storage/db.py` kept) |

**Total:** ~139 debug statements removed across 12 files

---

## Phase 3B — Unused Import Removal

### Frontend (8 files, 10 symbols removed)

| File | Removed Import | Reason |
|------|---------------|--------|
| `App.tsx` | `React` (default), `AsyncStorage` | No `React.` usage; `AsyncStorage` never referenced |
| `src/context/AuthContext.tsx` | `emailService`, `Platform` | Neither referenced after console.log cleanup removed `Platform.OS` log |
| `src/screens/LoginScreen.tsx` | `useCallback` | Never called |
| `src/screens/ProfileScreen.tsx` | `LinearGradient` | Never used in JSX |
| `src/screens/HomeScreen.tsx` | `Animated` | Never used (only in a JSX comment) |
| `src/services/api.service.ts` | `MVPEventAlternative` | Never referenced |
| `src/components/MetricsTable.tsx` | `React` (default) | No `React.` usage |
| `src/components/CameraRecorder.tsx` | `React` (default) | No `React.` usage |

### Backend (10 files, 13 symbols removed)

| File | Removed Import | Reason |
|------|---------------|--------|
| `backend/contracts/history.py` | `Any` from typing | Not in any type annotation |
| `backend/metrics/biomechanics.py` | `List`, `Tuple` from typing | Not in any type annotation |
| `backend/inference/pose_2d.py` | `Path` from pathlib | Only in docstring text, not code |
| `backend/inference/phase_detector.py` | `savgol_filter` from scipy.signal | Never called |
| `backend/mvp/core/pose_estimation.py` | `Tuple` from typing | Not in any type annotation |
| `backend/mvp/core/angle_computation.py` | `List` from typing | Not in any type annotation |
| `backend/routers/feedback.py` | `List`, `Optional` from typing | Neither used in type annotations |
| `backend/routers/sessions.py` | `List` from typing, `date` from datetime | Neither used in code (field named `date` is `str` type) |
| `backend/routers/recommendation_routes.py` | `numpy as np` | Never called |
| `backend/utils/validation.py` | `Any` from typing | Not in any type annotation |

---

## Phase 3C — Commented-Out Code

Scanned all live files for multi-line commented-out code blocks and single-line dead code patterns (`// const`, `// import`, `# def`, `# return`, etc.).

**Result:** No commented-out dead code found. Existing comments are:
- BUG FIX annotations from Agent 1 (document past fixes — kept)
- Section headers / separators
- Explanatory comments (why, not what)
- ESLint/type directives

---

## Files Marked UNCERTAIN (Kept)

| Category | Count | Reason Kept |
|----------|-------|-------------|
| `scripts/*.py` (16 files) | 16 | Standalone CLI tools. Some have broken imports (BUG_REPORT B55) but are not production code. Constraint: preserve all scripts. |
| `models/` (HRNet + YOLOv8 trees) | ~200+ | Vendored ML research code. Constraint: "Not in models/ — leave it." |
| `__graveyard__/` (96 files) | 96 | Already archived. Constraint: "Not in __graveyard__/ — leave it." |
| `backend/storage/db.py` print() | 1 line | `print()` inside error handler — kept per rules |

---

## "Do Not Touch" List

| File/Directory | Why Kept |
|----------------|----------|
| `__graveyard__/` | Archived iterations, explicitly excluded |
| `models/` | Vendored ML code, explicitly excluded |
| `scripts/` | Standalone CLI tools, preserved per constraint |
| All `__init__.py` files | Package markers, even if docstring-only |
| All test files (`tests/`, `mvp/tests/`, `inference/tests/`) | Tests preserved per constraint |
| `.env`, `.env.example` files | Config/secrets, preserved per constraint |
| `backend/storage/db.py` | Contains one `print()` inside an error handler — kept |
| `BUG_REPORT.md` | Agent 1 output, documentation |
| All `// BUG FIX:` comments | Document past fixes, carry context |
| `app.config.js`, `metro.config.js`, `.eslintrc.js` | Build/config files |
| `tsconfig.json`, `package.json`, `requirements.txt` | Dependency/config files |

---

## Estimated Line Count Reduction

| Source | Lines Removed |
|--------|--------------|
| Deleted files (6) | ~227 |
| console.log / print removal (12 files) | ~139 |
| Unused imports (18 files) | ~18 |
| **Total** | **~384** |

---

## Verification

- Zero linter errors introduced (verified via ReadLints on all edited files)
- No logic changes — only removal of dead weight
- No feature additions, UI changes, or architectural changes
- All tests, scripts, configs, and documentation preserved
