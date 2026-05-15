# SHOOTRZ Bilingual (EN/AR + RTL) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Tasks use the strict 8-field format defined below; do NOT invent steps outside their stated scope.

**Goal:** Add production-grade English ↔ Arabic bilingual support with full RTL layout to SHOOTRZ across the React Native (Expo) frontend, FastAPI backend, Supabase schema, and Gemini LLM, executed as a phased `Add → Backfill → Dual-read → Switch → Cleanup` migration that resolves every one of the 70 risks documented in `docs/superpowers/audits/2026-04-28-bilingual-arabic-rtl-audit.md` without breaking production.

**Architecture:** The frontend gains a global `LocaleProvider` powered by `i18next` + `react-i18next` + `expo-localization`, owning `{language, dir, isRTL, setLanguage}`. Direction flips via a single explicit user-driven `I18nManager.forceRTL` + `Updates.reloadAsync()`. The backend gains a `Depends(get_locale)` resolver (priority: body.language → user.preferred_language → Accept-Language → 'en') that propagates locale into every Gemini prompt builder via bilingual `_COACH_PERSONA[locale]` + `LANGUAGE_RULE[locale]`. Chat history is tagged with `language`; only same-language messages are sent to the LLM context. Enums (verdict, score_tier, position, primary_goal, coaching_style, training_frequency, dominant_hand) become stable English snake_case keys on the wire and in the DB; display labels live in client-side i18n catalogs. Every breaking change is additive-first and feature-flagged.

**Tech Stack:** React Native + Expo SDK 51+ • `i18next` ^23 • `react-i18next` ^14 • `expo-localization` • `i18next-icu` (ICU plural rules) • `expo-updates` (one-shot reload on direction flip) • FastAPI + Pydantic v2 • Supabase (PostgreSQL + RLS) • Google Gemini 2.5 Flash via `google-genai` • `ts-morph` (codemods) • `langdetect` (Python, language detection retry guard) • ESLint with custom `no-restricted-syntax` rules.

**Risk traceability convention:** Audit risks are referenced as `R-1` through `R-70`. Every task lists the exact `R-N` IDs it resolves. Phase 0 maps the full set; no risk is left orphaned.

---

## Phase 0 — Audit Coverage Mapping

🎯 **Goal:** Lock the contract between the 70 audit risks and the strategy. No implementation work happens in this phase — only the mapping that proves the plan is exhaustive.

### Coverage Matrix

#### Category A — i18n / Hardcoded Strings (16 risks)

| Risk | Affected area | Strategy solution | Resolved in |
|---|---|---|---|
| R-1 | Repo-wide: no i18n runtime | Install i18next + LocaleProvider | Phase 2 |
| R-2 | All screens with literal `<Text>` content | String-extraction codemod → `t()` | Phase 3 |
| R-3 | `src/constants/drills.ts`, OnboardingScreen option lists | Move drill text to `locales/*/drills.json`; split value/label on options | Phases 5, 7 |
| R-23 | Placeholders in Login/Profile/Onboarding/Username/Chat | Codemod also rewrites `placeholder=` literals | Phase 3 |
| R-30 | LoginScreen "OR" divider | Replaced via codemod with `t('auth.or')` | Phase 3 |
| R-36 | UsernameScreen + OnboardingScreen validation messages | Validators return error keys; UI translates | Phases 3, 5 |
| R-39 | Apple/Google branded buttons | Translated label keys (`auth.sign_in_google`/`apple`) | Phase 3 |
| R-43 | ChatScreen "Include raw artifacts" toggle | Codemod-translated | Phase 3 |
| R-44 | EmptyState/ErrorState/Loading copy passed by callers | Codemod converts callers; component itself is i18n-agnostic | Phase 3 |
| R-48 | Drill catalogue duplicated across FE/BE | Drills become id-only; titles/descriptions live in `drills.json` | Phases 5, 7 |
| R-51 | ProfileScreen position placeholder | Translated, comma replaced with locale-correct comma | Phase 3 |
| R-53 | OnboardingScreen Skip/Back buttons | Translated; placement still flips via Phase 3 logical layout | Phase 3 |
| R-56 | MVPAnalysisScreen tracking quality chip | Threshold-to-key mapping + `t('analysis.tracking.<key>')` | Phase 3 |
| R-60 | `src/utils/iconMapper.ts` English keys | Keep keys (machine), only display labels translate | Confirmed in Phase 5 |
| R-66 | OnboardingScreen step.title array | Convert array to keys (`onboarding.step.welcome.title`) | Phase 3 |
| R-69 | `app.json` / `app.config.js` no locales | Declare `locales` + `supportsRTL` | Phase 2 |

#### Category B — RTL Layout (14 risks)

| Risk | Affected area | Strategy solution | Resolved in |
|---|---|---|---|
| R-4 | ~80 instances of `flexDirection: 'row'` + physical `marginLeft/Right`, `paddingLeft/Right` | Logical-styles codemod | Phase 3 |
| R-5 | ChatBubble physical `borderTopLeftRadius`/etc. | Codemod converts to `borderTopStartRadius`/etc. | Phase 3 |
| R-6 | CameraRecorder, AngleGraph, ProfileScreen absolute `left:N` offsets | Manual review pass: convert symmetrical to `start:`, audit asymmetric | Phase 3 |
| R-7 | `chevron-back`/`chevron-forward`/`hand-left` icon names | Direction-aware `Chevron` wrapper that selects glyph based on `isRTL` | Phase 6 |
| R-8 | Tab bar order + ScreenHeader back placement | Auto-flip via `flexDirection: 'row'` post-codemod; verify `accessibilityLabel` translated | Phase 3 |
| R-22 | Fixed-width pills, `numberOfLines={1}`, 4-equal phase blocks | Replace fixed widths with `flexShrink/grow` + `flexWrap`; phase blocks switch to flex-grow | Phase 3 |
| R-27 | ChatBubble single-direction styling | Per-message first-strong direction detection | Phase 6 |
| R-31 | RN `Switch` direction on Android | Wrap in `RTLSwitch` that mirrors thumb when `isRTL` | Phase 6 |
| R-40 | MetricCard value/unit row BiDi | Format module wraps numbers with FSI/PDI marks | Phase 2 |
| R-41 | CoachContextChip ' + ' joiner | Replace literal join with `t('chat.context_joiner')` (locale-aware separator) | Phase 6 |
| R-55 | MVPAnalysisScreen 4-element phase array indexed positionally | Phase data becomes `[{key, color}]`; rendering iterates and translates key | Phase 3 |
| R-57 | `formatMetricName` ASCII `\b\w` regex | Drop the regex; use translated metric labels via `t('enums.metric.<key>')` | Phase 5 |
| R-61 | `accessibilityLabel` English literals | Codemod also rewrites a11y labels | Phase 3 |
| R-67 | No `Accept-Language` header | Set on Axios + chat fetch wrappers | Phase 1 |

#### Category C — Chat / LLM (14 risks)

| Risk | Affected area | Strategy solution | Resolved in |
|---|---|---|---|
| R-9 | `prompt_builders.py` English persona + rubric | Bilingual `_COACH_PERSONA` + `LANGUAGE_RULE` per builder | Phase 4 |
| R-10 | Persisted history mixes languages | `chat_history.language` column + LLM context filter | Phase 6 |
| R-11 | ChatScreen contextLabel + QUICK_CHIPS + COACH_GREETING English | Translation keys for all chat-screen strings | Phases 3, 6 |
| R-15 | `feedback/rules.py` returns English messages | Each rule returns `{en, ar}` dict; caller selects | Phases 4, 7 |
| R-16 | `fallbacks.py` English-only | Locale-parameterized fallbacks | Phase 7 |
| R-33 | Chat metadata badge "Profile/Goals/History" + naming mismatch | Fix field names + translate via `t()` | Phase 6 |
| R-34 | Drill recommendation/session summary/progress insight English-only | Locale flows into all LLM prompts | Phase 4 |
| R-35 | `analysis_summaries` persisted English text | Add `language` column + tag at write time | Phases 1, 6 |
| R-47 | Streaming SSE error messages English | Backend yields error `code` + frontend translates | Phases 4, 6 |
| R-58 | `chat_history` no language column | Migration adds column | Phase 1 |
| R-62 | SSE delimiter edge case for Arabic content | JSON encoding already escapes `\n`; add unit test | Phase 6 |
| R-64 | Streaming response no language echo | Add `language` field in `done` SSE payload | Phase 6 |
| R-65 | `recent_chat` replays English content | Filter by language in context_builder | Phase 6 |
| R-50 | `primary_goal` raw flow into English persona | Same as R-65 — solved by locale propagation + filtered context | Phase 4 |

#### Category D — Backend Locale Handling (8 risks)

| Risk | Affected area | Strategy solution | Resolved in |
|---|---|---|---|
| R-13 | `_PROMPT_SAFE_RE` strips Arabic punctuation | Rewrite regex (deny-list, not allow-list) | Phase 4 |
| R-14 | `MAX_CONTEXT_CHARS` ignores token cost | Replace with token-aware budget (`_CHARS_PER_TOKEN[locale]`) | Phase 4 |
| R-17 | HTTPException `detail` English strings | Replace with error codes; UI maps to `errors.<code>` | Phase 4 |
| R-29 | Frontend service errors English | Same as R-17 (codes) + locale-aware fallback | Phase 4 |
| R-37 | Sanitization not uniform; mixed-language prompt context | Locale-aware persona + filtered history | Phases 4, 6 |
| R-42 | `sanitize_str` codepoint truncation orphans Arabic diacritics | Truncate on grapheme cluster boundary | Phase 4 |
| R-67 | No `Accept-Language` header on requests | Set on Axios + fetch | Phase 1 |
| R-68 | date-fns no locale | format module routes through `Intl.DateTimeFormat` | Phase 2 |

#### Category E — Data Model / Enums (8 risks)

| Risk | Affected area | Strategy solution | Resolved in |
|---|---|---|---|
| R-12 | `verdict`/`score_tier` strings used as both display + key | Pydantic `Literal` enums + frontend `t('enums.verdict.<key>')` | Phase 5 |
| R-32 | Frontend `theme.ts`/`scoreTier.ts` mirrors English literals | Returns enum keys; theme palette keys remain English (machine) | Phase 5 |
| R-49 | OnboardingScreen position/goal display==value | `{value, labelKey}` split | Phase 5 |
| R-54 | `score_components[].name` English substring matching | Backend emits stable keys; frontend uses `===` on key | Phase 5 |
| R-58 | `chat_history` no language tag | Migration | Phase 1 |
| R-59 | `analysis_summaries` / `users` / `user_profiles` no language tag | Add `language` / `*_lang` columns | Phase 1 |
| R-63 | Position/coaching_style/dominantHand enum hygiene mismatch | Normalize to lowercase keys | Phase 5 |
| R-70 | `score_tier` values used as palette keys in `SCORE_TIER_CARD_SURFACE` | Keys stay English; translation only at render | Phase 5 |

#### Category F — UX / Alerts / Formatting / Persistence (10 risks)

| Risk | Affected area | Strategy solution | Resolved in |
|---|---|---|---|
| R-18 | English plural `s` toggles | `Intl.PluralRules` via i18next ICU | Phase 2 |
| R-19 | Date/time English locale | `format.ts` wraps `Intl.DateTimeFormat` | Phase 2 |
| R-20 | Number/unit BiDi mixing | `format.ts` wraps with FSI/PDI marks | Phase 2 |
| R-21 | `toUpperCase` / `split(' ')[0]` ASCII assumptions | Replace with translated short-name + `Intl.Locale`-aware splitting | Phase 3 |
| R-24 | `Alert.alert` English titles/bodies | `LocalizedAlert` wrapper | Phase 2 |
| R-25 | AsyncStorage cache desync on language change | Cache namespacing not needed (data is language-tagged at source); document explicit invalidation on `setLanguage` | Phase 2 |
| R-26 | Supabase session + I18nManager restart | `setLanguage` flushes in-flight stream then `Updates.reloadAsync` | Phase 2 |
| R-28 | Chat composer auto-capitalize ignores Arabic | Set `autoCorrect={isRTL ? true : false}` and `textContentType` | Phase 6 |
| R-38 | `recent_chat` LTR ordering assumption | Acceptable (chronological); covered by R-10 same-language filter | Phase 6 |
| R-45 | `feedback_summary` English fallback string | Localized fallback | Phase 7 |
| R-46 | Profile delete confirmation English | `LocalizedAlert` | Phase 2 |
| R-52 | `getGreeting` Latin comma in name interpolation | Use locale-correct separator key | Phase 3 |

**Coverage assertion:** All 70 risks (R-1 through R-70) are mapped to a phase and a concrete task in this plan. No orphans.

---

## Phase 1 — Infrastructure & Language Plumbing

🎯 **Goal:** Make the system *capable* of locale awareness without changing any user-visible behavior. Pure additive plumbing.

---

### Task 1.1: Add `users.preferred_language` column

🎯 **Objective:** Persist each user's chosen UI language at the source of truth (Supabase).

📂 **Files Affected:**
- Create: `supabase/migrations/2026_04_28_001_add_preferred_language.sql`
- Modify: `supabase/schema_complete.sql`
- Modify: `backend/storage/db.py` (read/write helpers for `preferred_language`)

🔧 **Change Summary:** Add `preferred_language CHAR(2) NOT NULL DEFAULT 'en'` to `users`. Add a Postgres `CHECK (preferred_language IN ('en','ar'))` constraint. Update `db.py` to read and write the column on every user fetch/upsert path.

🧩 **Strategy Link:** §2.B Backend Language Awareness — "Persistence — `users.preferred_language CHAR(2) NOT NULL DEFAULT 'en'`."

⚠️ **Risks Resolved:** R-59 (users table no language tag).

🔗 **Dependencies:** None (this is the foundation migration).

🚀 **Unlocks:** Tasks 1.4, 1.6, 4.5, 7.7.

✅ **Verification:**
- Run `python -m pytest backend/tests/test_supabase_client.py -v` — existing tests must still pass.
- Confirm via Supabase SQL editor: `SELECT preferred_language FROM users LIMIT 5;` returns `'en'` for all rows.
- Insert a test row with `preferred_language='ar'`; CHECK constraint allows it. Insert `'fr'`; constraint rejects it.

---

### Task 1.2: Add `chat_history.language` column

🎯 **Objective:** Tag every persisted chat message with the language it was created in, so the LLM context filter can later exclude cross-language history.

📂 **Files Affected:**
- Create: `supabase/migrations/2026_04_28_002_add_chat_history_language.sql`
- Modify: `supabase/schema_complete.sql`

🔧 **Change Summary:** Add `language CHAR(2) NOT NULL DEFAULT 'en'`. Add composite index `chat_history_user_lang_created_idx (user_id, language, created_at DESC)` to keep the filtered query fast. CHECK constraint matches users' constraint.

🧩 **Strategy Link:** §2.C "Tag every `chat_history` row with `language`; context builder includes ONLY same-language history."

⚠️ **Risks Resolved:** R-10, R-58, R-65.

🔗 **Dependencies:** None.

🚀 **Unlocks:** Tasks 6.1, 6.2, 6.3.

✅ **Verification:**
- `EXPLAIN ANALYZE SELECT * FROM chat_history WHERE user_id=? AND language=? ORDER BY created_at DESC LIMIT 20;` uses the new index.
- All existing rows show `language='en'` after migration.

---

### Task 1.3: Add `analysis_summaries.language` and `user_profiles.primary_goal_lang`

🎯 **Objective:** Allow free-text user content and LLM-generated coaching summaries to be filtered or labeled by source language.

📂 **Files Affected:**
- Create: `supabase/migrations/2026_04_28_003_add_summary_and_goal_language.sql`
- Modify: `supabase/schema_complete.sql`
- Modify: `backend/storage/db.py` (insert paths for analysis summaries)
- Modify: `backend/services/mvp_job_service.py` (writes `analysis_summaries`)

🔧 **Change Summary:** Add `analysis_summaries.language CHAR(2) NOT NULL DEFAULT 'en'`. Add `user_profiles.primary_goal_lang CHAR(2)` (nullable; populated when `primary_goal` is written). Update writers to capture locale (passed in from the request).

🧩 **Strategy Link:** §5 Migration — "Bucket 2: free-text user content gets a `*_lang` companion column."

⚠️ **Risks Resolved:** R-35, R-59 (free-text user content not tagged).

🔗 **Dependencies:** Task 1.1.

🚀 **Unlocks:** Tasks 4.5 (LLM enrichment can pass locale), 7.5 (Arabic launch can label new summaries correctly).

✅ **Verification:**
- New `analysis_summary` insert with `language='ar'` succeeds.
- Existing summaries return `language='en'` when queried.

---

### Task 1.4: Add backend `get_locale` dependency

🎯 **Objective:** Single source of truth for "which language should this response be in?" across all FastAPI routers.

📂 **Files Affected:**
- Create: `backend/utils/locale.py`
- Modify: `backend/main.py` (no behavior change yet — just imports the module)

🔧 **Change Summary:** Define `LocaleType = Literal['en', 'ar']`. Define `get_locale(request, user, body_language=None) -> LocaleType` that resolves: explicit body field → `user.preferred_language` → first match in `Accept-Language` header → `'en'`. Internal helper `_parse_accept_language(header: str)` returns `'ar'` if any `ar*` tag is present, else `'en'`.

🧩 **Strategy Link:** §2.B "One FastAPI dependency `get_locale()` resolves the request locale."

⚠️ **Risks Resolved:** R-67 (no Accept-Language plumbing).

🔗 **Dependencies:** Task 1.1.

🚀 **Unlocks:** Tasks 1.6, 4.4, 4.5, 4.8.

✅ **Verification:**
- New unit tests in `backend/tests/test_locale.py`:
  - User with `preferred_language='ar'` and no header → returns `'ar'`.
  - Body field overrides user preference.
  - `Accept-Language: ar-SA,en;q=0.5` → `'ar'`.
  - No signal anywhere → `'en'`.

---

### Task 1.5: Set `Accept-Language` header on all frontend HTTP clients

🎯 **Objective:** Frontend always tells the backend which language it expects responses in, even before the user has explicitly picked one.

📂 **Files Affected:**
- Modify: `src/services/api.service.ts` (Axios `defaults.headers.common['Accept-Language']`)
- Modify: `src/services/chat.service.ts` (`fetch` calls in `getChatHistory`, `clearChatHistory`, `sendMessage`, `sendMessageStream` — set `'Accept-Language'`)
- Modify: `src/services/email.service.ts` (any `fetch` calls)

🔧 **Change Summary:** Read current language from a small synchronous accessor (`getCurrentLanguage()`) backed by a module-level variable kept in sync with `LocaleProvider`. Set the header at request build time. Default `'en'` until LocaleProvider boots in Phase 2.

🧩 **Strategy Link:** §2.B "Frontend sends `Accept-Language` header AND `user.language` column persisted."

⚠️ **Risks Resolved:** R-67.

🔗 **Dependencies:** Task 1.4 (so the backend can read the header even though the dependency isn't wired into routers yet).

🚀 **Unlocks:** Tasks 4.5, 4.8.

✅ **Verification:**
- DevTools / Charles inspect: every outbound request shows `Accept-Language` header.
- Backend log shows the header in request logs (no parsing yet).

---

### Task 1.6: Wire `language` field through `ChatRequest` contract

🎯 **Objective:** Chat API call carries an explicit language so the LLM can be deterministic.

📂 **Files Affected:**
- Modify: `backend/contracts/chat.py` (add `language: Literal['en','ar'] = 'en'`)
- Modify: `backend/routers/chat.py` (`_parse_chat_payload` accepts `language`/`lang` body keys with normalization)
- Modify: `src/types/contracts.ts` (`ChatRequestDto` adds `language?: 'en'|'ar'`)
- Modify: `src/services/chat.service.ts` (include `language: getCurrentLanguage()` in body for `sendMessage` and `sendMessageStream`)

🔧 **Change Summary:** Additive optional field on the contract; backend defaults to `'en'` if missing. Routers extract it but do not yet consume it (Phase 4 wires it into prompt builders).

🧩 **Strategy Link:** §2.B "Body field `language` on requests where the response language must be deterministic."

⚠️ **Risks Resolved:** R-50, R-65 (preconditions).

🔗 **Dependencies:** Task 1.4.

🚀 **Unlocks:** Tasks 4.4, 4.5, 6.5.

✅ **Verification:**
- Backend test `backend/tests/test_chat_contract.py`: `ChatRequest(messages=[...], language='ar')` validates; `ChatRequest(messages=[...])` defaults to `'en'`; `language='fr'` raises `ValidationError`.
- Frontend `apiService` sends `language` in body; backend log shows extracted value.

---

### Task 1.7: Add backend `Depends(get_locale)` to chat + analysis routes (resolver only, no behavior change)

🎯 **Objective:** Routers compute the locale on every request so Phase 4 can plug logic in without re-touching every handler.

📂 **Files Affected:**
- Modify: `backend/routers/chat.py` (add `locale: LocaleType = Depends(get_locale)` to `chat`, `chat_stream`, `get_chat_history`, `clear_chat_history`)
- Modify: `backend/routers/mvp.py`, `backend/routers/analysis.py`, `backend/routers/feedback.py`, `backend/routers/recommendation_routes.py`, `backend/routers/sessions.py`, `backend/routers/user.py`, `backend/routers/history.py`

🔧 **Change Summary:** Add the dependency parameter to every user-facing route signature. Log the resolved locale at INFO level. No behavior change.

🧩 **Strategy Link:** §2.B "Every router that returns user-facing text takes `locale: str = Depends(get_locale)`."

⚠️ **Risks Resolved:** Pre-condition for R-9, R-15, R-16, R-17, R-29, R-34, R-47.

🔗 **Dependencies:** Tasks 1.4, 1.6.

🚀 **Unlocks:** All Phase 4 prompt-builder + error-code tasks.

✅ **Verification:**
- Hit each endpoint with `Accept-Language: ar`; log shows `locale=ar`.
- Existing route contracts are unchanged (response bodies still English).
- Full backend test suite passes.

---

## Phase 2 — Frontend i18n Foundation

🎯 **Goal:** Stand up the i18next runtime, the locale state, the format helpers, and the alert wrapper. Catalog is English-only at this point.

---

### Task 2.1: Install dependencies

🎯 **Objective:** Add the i18n library set without code yet.

📂 **Files Affected:**
- Modify: `SHOOTRZ/package.json`
- Modify: `SHOOTRZ/package-lock.json`

🔧 **Change Summary:** `npm install i18next@^23 react-i18next@^14 expo-localization i18next-icu`. Verify `expo-updates` is already present (used in Task 2.3); if not, `npx expo install expo-updates`.

🧩 **Strategy Link:** §2.A "Library: i18next + react-i18next + expo-localization."

⚠️ **Risks Resolved:** Pre-condition for R-1.

🔗 **Dependencies:** None.

🚀 **Unlocks:** Tasks 2.2–2.7.

✅ **Verification:**
- `npm test` still passes (no app code touched yet).
- `npx tsc --noEmit` passes.

---

### Task 2.2: Create i18n initialization module + English skeleton catalog

🎯 **Objective:** Boot i18next with namespaces, ICU plurals, and a placeholder catalog.

📂 **Files Affected:**
- Create: `src/i18n/index.ts`
- Create: `src/i18n/locales/en/common.json`
- Create: `src/i18n/locales/en/home.json`
- Create: `src/i18n/locales/en/chat.json`
- Create: `src/i18n/locales/en/analysis.json`
- Create: `src/i18n/locales/en/onboarding.json`
- Create: `src/i18n/locales/en/profile.json`
- Create: `src/i18n/locales/en/drills.json`
- Create: `src/i18n/locales/en/enums.json`
- Create: `src/i18n/locales/en/errors.json`
- Create: `src/i18n/locales/en/auth.json`

🔧 **Change Summary:** Initialize `i18next.use(ICU).use(initReactI18next).init({...})` with `fallbackLng: 'en'`, namespaces listed above, `lng` derived from `expo-localization` (treat any `ar*` device locale as `ar`, else `en`). Each namespace JSON file ships as an empty object `{}` — Phase 3 codemod populates them.

🧩 **Strategy Link:** §2.A — Translation file structure, namespaces.

⚠️ **Risks Resolved:** Pre-condition for R-1, R-2, R-23, R-24, R-30, R-43, R-44.

🔗 **Dependencies:** Task 2.1.

🚀 **Unlocks:** Tasks 2.3, 3.1.

✅ **Verification:**
- `import i18n from './src/i18n'` loads in Metro without errors.
- `i18n.t('common:nonexistent')` returns `'common:nonexistent'` (i18next default).

---

### Task 2.3: Create `LocaleProvider` component

🎯 **Objective:** Single React context that owns `{language, dir, isRTL, setLanguage}` and gates RTL flips.

📂 **Files Affected:**
- Create: `src/i18n/LocaleProvider.tsx`
- Create: `src/i18n/getCurrentLanguage.ts` (synchronous accessor used by Task 1.5)

🔧 **Change Summary:** On mount, hydrate language from `AsyncStorage('@shootrz_language')` → fallback to Supabase user `preferred_language` → fallback to device locale → `'en'`. If `I18nManager.isRTL !== (lang === 'ar')`, call `I18nManager.allowRTL(true) + forceRTL(...)` and `Updates.reloadAsync()` once. Expose `setLanguage(lang)` that: (1) cancels in-flight chat streams via the existing `eventBus`, (2) writes AsyncStorage + Supabase profile, (3) calls `i18n.changeLanguage(lang)`, (4) flips `I18nManager`, (5) reloads.

🧩 **Strategy Link:** §2.A "RTL toggling strategy — strict, simple, one-time."

⚠️ **Risks Resolved:** R-1 (infrastructure), R-26 (Supabase session + restart safe), R-25 (cache invalidation flushed at the gate).

🔗 **Dependencies:** Tasks 1.1, 2.2.

🚀 **Unlocks:** Tasks 2.4, 7.7.

✅ **Verification:**
- Unit test (`src/i18n/__tests__/LocaleProvider.test.tsx`): mounting with `language='ar'` while `I18nManager.isRTL=false` schedules a `reloadAsync` (mock both modules).
- Manual: change language in dev menu → app restarts in Arabic → `I18nManager.isRTL === true`.

---

### Task 2.4: Wire `LocaleProvider` into App.tsx

🎯 **Objective:** Mount the provider above all other contexts.

📂 **Files Affected:**
- Modify: `SHOOTRZ/App.tsx`

🔧 **Change Summary:** Wrap existing provider tree with `<LocaleProvider>` *outside* `AuthProvider` so language is known before auth/network calls. Import `./src/i18n` for side-effect init.

🧩 **Strategy Link:** §2.A — provider hierarchy.

⚠️ **Risks Resolved:** R-1.

🔗 **Dependencies:** Task 2.3.

🚀 **Unlocks:** Phase 3 codemod can now safely use `t()` because the provider is mounted.

✅ **Verification:**
- App boots; React DevTools shows `LocaleProvider` at root.
- `npm test` passes (mock provider in test setup if needed).

---

### Task 2.5: Create `format.ts` module

🎯 **Objective:** Single entry point for number, date, percent, angle, relative-time, and BiDi-safe interpolation.

📂 **Files Affected:**
- Create: `src/i18n/format.ts`
- Create: `src/i18n/__tests__/format.test.ts`

🔧 **Change Summary:** Export `fmtNum`, `fmtPercent`, `fmtAngle`, `fmtDate`, `fmtRelativeDay`, `fmtCount(key, count)`. Each pulls current language from `i18n.language`. `fmtAngle` and any function emitting digits inside a translated string wraps the numeric run in U+2068 (FSI) … U+2069 (PDI) to prevent BiDi reversal.

🧩 **Strategy Link:** §3 Change 9 — format module.

⚠️ **Risks Resolved:** R-18, R-19, R-20, R-40, R-68.

🔗 **Dependencies:** Task 2.2.

🚀 **Unlocks:** Tasks 3.6 (codemod can replace `toFixed`), screen refactors in Phase 3.

✅ **Verification:**
- Tests: `fmtAngle(165.4)` returns `'⁨165.4⁩°'` under `ar`, `'165.4°'` under `en`.
- `fmtDate('2026-04-28')` returns `'٢٨ أبر، ٢٠٢٦'` under `ar`, `'Apr 28, 2026'` under `en` (or device-locale equivalents).
- `fmtCount('progress.session_count', 1)` resolves to "1 session"; `fmtCount(..., 2)` to "2 sessions"; under Arabic, six plural forms supported.

---

### Task 2.6: Create `LocalizedAlert` wrapper

🎯 **Objective:** Replace direct `Alert.alert()` usage with a translation-aware helper.

📂 **Files Affected:**
- Create: `src/utils/alert.ts`
- Create: `src/utils/__tests__/alert.test.ts`

🔧 **Change Summary:** Export `showAlert({ titleKey, bodyKey, bodyParams, actions: [{textKey, style, onPress}] })`. Internally calls `i18n.t()` for each key. Style options match RN: `'default' | 'cancel' | 'destructive'`.

🧩 **Strategy Link:** §3 Change 8 — `LocalizedAlert` wrapper.

⚠️ **Risks Resolved:** R-24, R-46.

🔗 **Dependencies:** Task 2.2.

🚀 **Unlocks:** Phase 3 codemod can rewrite `Alert.alert(...)` calls.

✅ **Verification:**
- Mock `Alert.alert` in test; assert it's called with translated strings.
- `showAlert({titleKey:'common.error', bodyKey:'errors.upload.network'})` resolves both keys.

---

### Task 2.7: Declare locales + RTL in Expo config

🎯 **Objective:** iOS App Store and Android settings recognize the app as Arabic-capable.

📂 **Files Affected:**
- Modify: `SHOOTRZ/app.config.js` (or `app.json`)

🔧 **Change Summary:** Add `extra.locales: ['en', 'ar']` (or platform-specific `ios.infoPlist.CFBundleLocalizations`). Add `ios.supportsTablet` is unrelated; this is about `CFBundleLocalizations` and Android `android:supportsRtl="true"` (default in modern RN, but verify).

🧩 **Strategy Link:** §3 — config plumbing.

⚠️ **Risks Resolved:** R-69.

🔗 **Dependencies:** None.

🚀 **Unlocks:** App appears as Arabic-capable in iOS settings.

✅ **Verification:**
- iOS: Settings → General → Language & Region → SHOOTRZ shows Arabic option.
- Android: APK manifest contains `android:supportsRtl="true"`.

---

## Phase 3 — Codebase Transformation (Codemods)

🎯 **Goal:** Mechanically rewrite the codebase: hardcoded strings → `t()` calls; physical layout → logical layout. Enforce via ESLint to prevent regression.

---

### Task 3.1: Build string-extraction codemod

🎯 **Objective:** Automate extraction of every JSX string literal into the i18n catalog.

📂 **Files Affected:**
- Create: `scripts/i18n/extract-strings.ts`
- Create: `scripts/i18n/key-from-text.ts` (slugify + dedupe helper)
- Create: `scripts/i18n/namespace-from-file.ts` (file-path → namespace mapping)

🔧 **Change Summary:** ts-morph script. For each `.tsx` in `src/`, walk all `JsxText`, `StringLiteral` inside JSX attributes (`placeholder`, `accessibilityLabel`, `accessibilityHint`), `Alert.alert` first/second arg literals. Generate a key `<namespace>:<component>.<slug>`. Append to `src/i18n/locales/en/<namespace>.json`. Replace the literal with `{t('<key>')}`. Add `import { useTranslation } from 'react-i18next'` and `const { t } = useTranslation('<namespace>')` at the top of any component that didn't have it.

🧩 **Strategy Link:** §3 Change 2 — string extraction codemod.

⚠️ **Risks Resolved:** R-2, R-23, R-30, R-39, R-43, R-44, R-51, R-53, R-56 (precondition; full sweep happens in 3.2/3.3).

🔗 **Dependencies:** Tasks 2.2, 2.4.

🚀 **Unlocks:** Tasks 3.2, 3.3.

✅ **Verification:**
- Dry-run on `src/screens/UsernameScreen.tsx`; diff shows literals replaced with `t()` and matching entries added to `locales/en/onboarding.json` (or chosen namespace).
- `npx tsc --noEmit` passes after dry-run.

---

### Task 3.2: Run string-extraction codemod across all screens

🎯 **Objective:** Mechanical conversion of every screen.

📂 **Files Affected:**
- Modify: every file under `src/screens/*.tsx` (excluding `__tests__/`)
- Modify: `src/i18n/locales/en/*.json` (auto-populated)

🔧 **Change Summary:** Run `node scripts/i18n/extract-strings.ts src/screens`. Manually review the diff; merge near-duplicate keys; verify `useTranslation` namespace is correct per file.

🧩 **Strategy Link:** §3 Change 2.

⚠️ **Risks Resolved:** R-2 (full screen coverage), R-23, R-30, R-39, R-44, R-51, R-53, R-56, R-66 (onboarding step keys).

🔗 **Dependencies:** Task 3.1.

🚀 **Unlocks:** Task 7.1 (Arabic translation).

✅ **Verification:**
- `npm test` and `npx tsc --noEmit` pass.
- Visual smoke test: every screen still renders with English text identical to before.
- `grep -nE '<Text[^>]*>[A-Z]' src/screens/*.tsx` returns zero matches (no hardcoded English left in `<Text>`).

---

### Task 3.3: Run string-extraction codemod across components + utils

🎯 **Objective:** Same as 3.2, for the components layer.

📂 **Files Affected:**
- Modify: every file under `src/components/*.tsx` (excluding `__tests__/`)
- Modify: `src/utils/*.ts` (any user-facing strings)
- Modify: `src/i18n/locales/en/*.json`

🔧 **Change Summary:** Run codemod on the components directory. Special handling for `EmptyState`, `ErrorState`, `TypingIndicator`, `CoachContextChip`, `ScreenHeader` — these have a11y labels that must use `t()` too.

🧩 **Strategy Link:** §3 Change 2.

⚠️ **Risks Resolved:** R-44, R-61.

🔗 **Dependencies:** Task 3.1.

🚀 **Unlocks:** Phase 7 Arabic translation completeness.

✅ **Verification:**
- `npm test` passes.
- `grep -RE 'accessibilityLabel="[A-Z]' src/components/` returns zero matches.

---

### Task 3.4: Replace `Alert.alert(...)` calls with `showAlert({...})`

🎯 **Objective:** Funnel every alert through the localized wrapper.

📂 **Files Affected:**
- Modify: `src/screens/LoginScreen.tsx`, `ProfileScreen.tsx`, `MVPAnalysisScreen.tsx`, `WorkoutsScreen.tsx`, `DrillDetailScreen.tsx`, `UsernameScreen.tsx`
- Modify: `src/components/CameraRecorder.tsx`
- Modify: `src/hooks/useDeepLinks.ts`
- Modify: `src/services/email.service.ts`
- Modify: `src/i18n/locales/en/common.json`, `errors.json`

🔧 **Change Summary:** Manual (or codemod-assisted) rewrite of each `Alert.alert(title, body, [actions])` → `showAlert({ titleKey, bodyKey, bodyParams, actions })`. Add corresponding keys to catalog. Action button keys go to `common.cancel`, `common.delete`, `common.retry`, etc.

🧩 **Strategy Link:** §3 Change 8.

⚠️ **Risks Resolved:** R-24, R-46.

🔗 **Dependencies:** Tasks 2.6, 3.2, 3.3.

🚀 **Unlocks:** Phase 7 destructive-action UX in Arabic.

✅ **Verification:**
- `grep -RE 'Alert\.alert\(' src/` returns only the test files.
- All alert flows still work in English.

---

### Task 3.5: Build logical-styles codemod

🎯 **Objective:** Mechanically convert physical to logical layout properties.

📂 **Files Affected:**
- Create: `scripts/i18n/codemod-logical-styles.ts`

🔧 **Change Summary:** ts-morph script. In any `StyleSheet.create({...})` or inline `style={{...}}` object, rename keys: `marginLeft` → `marginStart`, `marginRight` → `marginEnd`, `paddingLeft` → `paddingStart`, `paddingRight` → `paddingEnd`, `borderTopLeftRadius` → `borderTopStartRadius`, `borderTopRightRadius` → `borderTopEndRadius`, `borderBottomLeftRadius` → `borderBottomStartRadius`, `borderBottomRightRadius` → `borderBottomEndRadius`. For string values: `textAlign: 'left'` → `'start'`, `textAlign: 'right'` → `'end'`. Skip files in `__graveyard__/`.

🧩 **Strategy Link:** §3 Change 3 — logical-direction codemod.

⚠️ **Risks Resolved:** R-4, R-5 (structural foundation).

🔗 **Dependencies:** None (independent codemod).

🚀 **Unlocks:** Task 3.6.

✅ **Verification:**
- Dry-run on `src/components/ChatBubble.tsx`: `borderTopLeftRadius` → `borderTopStartRadius` etc.
- `npx tsc --noEmit` passes.

---

### Task 3.6: Run logical-styles codemod across `src/`

🎯 **Objective:** Apply the conversion to the whole codebase.

📂 **Files Affected:**
- Modify: every `.tsx`/`.ts` under `src/components/`, `src/screens/`

🔧 **Change Summary:** Run `node scripts/i18n/codemod-logical-styles.ts src/`. Manually audit `position: 'absolute'` blocks (R-6) — for each, decide whether the offset should become `start` or remain physical (e.g., a logo always pinned to a specific corner regardless of language). Document each kept-physical exception with a `// rtl-physical: <reason>` comment.

🧩 **Strategy Link:** §3 Change 3.

⚠️ **Risks Resolved:** R-4 (full sweep), R-5, R-6 (with manual audit).

🔗 **Dependencies:** Task 3.5.

🚀 **Unlocks:** Visual RTL correctness in Phase 7.

✅ **Verification:**
- `grep -RnE 'marginLeft|marginRight|paddingLeft|paddingRight|borderTop[LR](eft|ight)Radius|borderBottom[LR](eft|ight)Radius' src/` returns zero non-test matches.
- `grep -RnE "textAlign:\s*['\"](left|right)['\"]" src/` returns zero non-test matches.
- All snapshot tests pass under both `I18nManager.isRTL=false` and forced `=true`.

---

### Task 3.7: Add ESLint rules to forbid physical styles + hardcoded JSX strings

🎯 **Objective:** Make regression mechanically impossible.

📂 **Files Affected:**
- Modify: `SHOOTRZ/eslint.config.js`

🔧 **Change Summary:** Add `no-restricted-syntax` rules that error on:
- `Property[key.name=/^(marginLeft|marginRight|paddingLeft|paddingRight|borderTopLeftRadius|borderTopRightRadius|borderBottomLeftRadius|borderBottomRightRadius)$/]`
- `Property[key.name='textAlign'][value.value=/^(left|right)$/]`
- (Phase 8) `JSXText[value=/[A-Za-z]{4,}/]` outside `__tests__` to forbid raw English.
- (Phase 8) Direct import of `Alert.alert` from `'react-native'` outside `src/utils/alert.ts`.

For Phase 3, the JSX-string rule is set to `warn` (not `error`) until codemod sweep is verified clean.

🧩 **Strategy Link:** §6 "Don't ship without an ESLint rule banning hardcoded JSX strings and physical margins."

⚠️ **Risks Resolved:** Future regression of R-2, R-4, R-24, R-44.

🔗 **Dependencies:** Tasks 3.6, 3.4.

🚀 **Unlocks:** Phase 8 strictness escalation.

✅ **Verification:**
- `npx eslint src/` exits 0 (warnings allowed, errors not).
- Insert a test violation (`marginLeft: 4` somewhere); ESLint reports an error.

---

### Task 3.8: Catalog review and namespace cleanup

🎯 **Objective:** Manual pass over the auto-generated `locales/en/*.json` to merge duplicates, fix awkward auto-keys, group near-identical strings.

📂 **Files Affected:**
- Modify: every `src/i18n/locales/en/*.json`
- Modify: any caller using a key that gets renamed.

🔧 **Change Summary:** Read every catalog entry. Rename keys that are too literal (`home.welcome_to_shootrz_basketball` → `home.welcome_title`). Move misplaced entries to the right namespace. Confirm plural-aware entries use ICU syntax. Add comments for translators in keys with placeholders.

🧩 **Strategy Link:** §2.A — key naming convention.

⚠️ **Risks Resolved:** Quality gate before Arabic translation kicks off.

🔗 **Dependencies:** Tasks 3.2, 3.3.

🚀 **Unlocks:** Task 7.1 (Arabic translator hand-off).

✅ **Verification:**
- All callers compile (`npx tsc --noEmit`).
- Catalog has < 5% duplicate values across keys (manual spot check).

---

### Task 3.9: Refactor `getGreeting`, `name.split`, `charAt(0).toUpperCase()` patterns

🎯 **Objective:** Replace ASCII-string-manipulation patterns with translation keys.

📂 **Files Affected:**
- Modify: `src/screens/HomeScreen.tsx` (lines 37–39, 201–204, 254–256)
- Modify: `src/screens/MVPAnalysisScreen.tsx` (line 282)
- Modify: `src/screens/ProgressScreen.tsx` (line 194)

🔧 **Change Summary:** `getGreeting` returns a key (`'morning'/'afternoon'/'evening'`) and the JSX renders `t('home.greeting.' + key)`. Greeting comma comes from `t('home.greeting.separator')` (English: `, `, Arabic: `، `). For "Today/Yesterday/X days ago", use `fmtRelativeDay`. For `side.charAt(0).toUpperCase()`, lookup `t('analysis.side.' + side)`. For `r.charAt(0).toUpperCase()` in ProgressScreen, lookup `t('progress.range.' + r)`.

🧩 **Strategy Link:** §3 Change 9, §6 (don't use ASCII string manipulation as i18n).

⚠️ **Risks Resolved:** R-19, R-21, R-52.

🔗 **Dependencies:** Tasks 2.5, 3.2.

🚀 **Unlocks:** Phase 7 Arabic copy correctness.

✅ **Verification:**
- HomeScreen still renders "Good morning, Ahmad" in English.
- Snapshot tests under simulated Arabic locale render "صباح الخير، أحمد" with Arabic comma.

---

### Task 3.10: Replace `MetricsTable.formatMetricName` with i18n lookup

🎯 **Objective:** Stop using ASCII regex (`\b\w`) on metric names; use translation keys instead.

📂 **Files Affected:**
- Modify: `src/components/MetricsTable.tsx`
- Modify: `src/screens/MVPAnalysisScreen.tsx` (line 362 `m.name.replace(/_/g, ' ')`)
- Modify: `src/screens/ProgressScreen.tsx` (line 246 `mt.name.replace(/_/g, ' ')`)
- Modify: `src/i18n/locales/en/enums.json` (`metric.elbow_flexion_release`, `metric.knee_flexion`, etc.)

🔧 **Change Summary:** Backend already emits stable snake_case `metric_name`. Frontend looks up `t('enums.metric.' + name)` instead of regex-formatting. Catalog has one entry per metric.

🧩 **Strategy Link:** §3 Change 6 — enum keys; §2.D enum decoupling.

⚠️ **Risks Resolved:** R-57.

🔗 **Dependencies:** Task 3.2.

🚀 **Unlocks:** Phase 7 Arabic metric labels.

✅ **Verification:**
- All metric labels still render English correctly.
- Adding an Arabic catalog entry produces correct Arabic label without code changes.

---

### Task 3.11: Refactor MVPAnalysisScreen phase bar to keyed data

🎯 **Objective:** Stop indexing colors by phase position; bind both via a single source of truth that survives RTL flips.

📂 **Files Affected:**
- Modify: `src/screens/MVPAnalysisScreen.tsx` (lines 391–396)
- Modify: `src/i18n/locales/en/analysis.json` (`phase.setup`, `phase.load`, `phase.release`, `phase.follow_through`)

🔧 **Change Summary:** Replace `['Setup', 'Load', 'Release', 'Follow-Through'].map((phase, i) => ... [colors...][i])` with `PHASES = [{key:'setup', color:colors.brand.orangeDim}, ...]`. JSX maps over the list and renders `t('analysis.phase.' + p.key)`. Block widths use `flex: 1` so Arabic-localized labels can grow without overflow.

🧩 **Strategy Link:** §1 Tier 2 — translation keys; §2.D enum decoupling.

⚠️ **Risks Resolved:** R-22 (phase block sizing), R-55.

🔗 **Dependencies:** Task 3.6.

🚀 **Unlocks:** Phase 7 Arabic phase names render correctly.

✅ **Verification:**
- Phase bar still renders identically in English.
- Forcing `t('analysis.phase.setup')` to a 12-character string keeps the layout intact (no overflow).

---

## Phase 4 — Backend Language Intelligence

🎯 **Goal:** Make the backend genuinely locale-aware: prompts switch language, sanitizers respect Arabic punctuation, error responses use codes, and the LLM context window never crosses language boundaries.

---

### Task 4.1: Rewrite `_PROMPT_SAFE_RE` and `_sanitize_str` for Arabic safety

🎯 **Objective:** Stop stripping Arabic punctuation from user-supplied strings; use grapheme-aware truncation.

📂 **Files Affected:**
- Modify: `backend/chat/context_builder.py` (lines 15–24)
- Create: `backend/tests/test_sanitize_arabic.py`

🔧 **Change Summary:** Switch from allow-list to deny-list: strip control characters (`\x00-\x1F\x7F`), backticks, angle brackets, square brackets, curly braces. Allow everything else (including Arabic, CJK, emoji). Replace `s[:max_len]` with grapheme-cluster truncation (use `regex` library: `regex.findall(r'\X', s)[:max_len]`). Update `requirements.txt` to include `regex`.

🧩 **Strategy Link:** §3 Change 5; §6 (don't break Arabic punctuation).

⚠️ **Risks Resolved:** R-13, R-42.

🔗 **Dependencies:** Task 1.7 (locale dep available, though this task doesn't use it).

🚀 **Unlocks:** Tasks 4.4, 4.5.

✅ **Verification:**
- Test: `_sanitize_str('تحسين الدقة، خاصة من الزاوية')` returns the input unchanged.
- Test: `_sanitize_str('hello\x00world')` returns `'helloworld'`.
- Test: `_sanitize_str('محمَّد', max_len=5)` returns `'محمَّد'` (5 grapheme clusters), not orphan diacritics.

---

### Task 4.2: Replace `MAX_CONTEXT_CHARS` with token-aware budget

🎯 **Objective:** Don't blow Gemini's context window for Arabic users.

📂 **Files Affected:**
- Modify: `backend/chat/context_builder.py` (lines 26, 268–305)
- Create: `backend/tests/test_context_budget.py`

🔧 **Change Summary:** Replace `MAX_CONTEXT_CHARS = 32_000` with `def _budget_chars(locale: str) -> int: return int(8_000 * _CHARS_PER_TOKEN.get(locale, 3.0))` where `_CHARS_PER_TOKEN = {'en': 4.0, 'ar': 2.0}`. Update `sanitize_context_for_llm(context, locale)` to take the locale and use the new budget. Trimming logic stays the same.

🧩 **Strategy Link:** §3 Change 5.

⚠️ **Risks Resolved:** R-14.

🔗 **Dependencies:** Task 1.4 (`LocaleType`).

🚀 **Unlocks:** Task 4.5.

✅ **Verification:**
- Test: a 30 000-char Arabic context gets trimmed to ~16 000 chars (Arabic budget).
- A 30 000-char English context stays at 30 000.

---

### Task 4.3: Build bilingual persona + language-rule tables

🎯 **Objective:** Centralize Coach J's persona for both languages.

📂 **Files Affected:**
- Modify: `backend/services/llm/prompt_builders.py`
- Create: `backend/tests/test_prompt_builders_locale.py`

🔧 **Change Summary:** Replace the single `_COACH_PERSONA` string with `_COACH_PERSONA: Dict[Literal['en','ar'], str]`. Author the Arabic version (Modern Standard Arabic, second-person addressing the player). Add `_LANGUAGE_RULE: Dict[...]` with `'en': 'Respond in English only.'` and `'ar': 'أجب باللغة العربية الفصحى فقط. لا تخلط الإنجليزية مع العربية.'` Add `_CHAT_RULES: Dict[...]` for the rule list at end of `build_chat_prompt`.

🧩 **Strategy Link:** §2.C — system prompt design.

⚠️ **Risks Resolved:** Pre-condition for R-9.

🔗 **Dependencies:** None (pure refactor).

🚀 **Unlocks:** Task 4.4.

✅ **Verification:**
- Test: `_COACH_PERSONA['en']` and `_COACH_PERSONA['ar']` both return non-empty strings.
- Manual translation review by an Arabic speaker before merge.

---

### Task 4.4: Locale-parameterize `build_chat_prompt`

🎯 **Objective:** Chat system prompt switches language based on caller-provided locale.

📂 **Files Affected:**
- Modify: `backend/services/llm/prompt_builders.py` (`build_chat_prompt`)
- Modify: `backend/routers/chat.py` (`_build_system_prompt(context, locale)`)

🔧 **Change Summary:** `build_chat_prompt(user_context, *, locale: Literal['en','ar']) -> str`. Returns `f"{_COACH_PERSONA[locale]}\n{_LANGUAGE_RULE[locale]}\n{_CHAT_RULES[locale]}\nPLAYER_DATA_JSON:\n{json.dumps(...)}"`. Router passes `locale` from `Depends(get_locale)` (or from `payload.language` for chat).

🧩 **Strategy Link:** §3 Change 4; §2.C.

⚠️ **Risks Resolved:** R-9 (chat persona).

🔗 **Dependencies:** Tasks 1.4, 1.6, 1.7, 4.3.

🚀 **Unlocks:** Phase 7 Arabic chat replies.

✅ **Verification:**
- Test: `build_chat_prompt({}, locale='ar')` contains the Arabic persona text.
- Integration test: send `{language: 'ar'}` to `/chat`; assistant_message detected as Arabic by `langdetect` ≥ 95% of the time.

---

### Task 4.5: Locale-parameterize remaining prompt builders

🎯 **Objective:** Apply the same locale switch to shot feedback, drill recommendation, session summary, progress insight, metric explanation, and feedback rephrase prompts.

📂 **Files Affected:**
- Modify: `backend/services/llm/prompt_builders.py` (six remaining functions)
- Modify: `backend/services/llm/llm_router.py` (callers pass locale)
- Modify: `backend/services/mvp_job_service.py` (passes locale into `get_shot_feedback`, `rephrase_feedback`)
- Modify: `backend/feedback/rules.py` (`_enrich_with_llm` passes locale)

🔧 **Change Summary:** Each builder gains `locale: Literal['en','ar']` keyword argument. System prompt uses bilingual persona. User prompt strings (e.g. "Generate a session summary.") are in the target language. Schema field descriptions stay English (Gemini reads them as metadata).

🧩 **Strategy Link:** §2.C — every LLM call locale-aware.

⚠️ **Risks Resolved:** R-9, R-34.

🔗 **Dependencies:** Tasks 4.3, 4.4.

🚀 **Unlocks:** Phase 7 — drill recommendations and session summaries in Arabic.

✅ **Verification:**
- Tests for each builder check the rendered prompt contains target-language tokens.
- End-to-end: Arabic user analyzes a shot; `feedback_summary` and bullets come back in Arabic.

---

### Task 4.6: Convert `feedback/rules.py` to bilingual `{en, ar}` returns

🎯 **Objective:** Rule-based deterministic feedback returns both languages; caller picks.

📂 **Files Affected:**
- Modify: `backend/feedback/rules.py` (every `get_*_feedback` function)
- Modify: callers: `backend/feedback/engine.py`, `backend/services/mvp_job_service.py`, `backend/routers/feedback.py`

🔧 **Change Summary:** Each `get_X_feedback` returns `{'message': {'en':..., 'ar':...}, 'details': {'en':..., 'ar':...}, 'severity': ..., 'metric_name': ..., 'value': ...}`. Caller selects `item['message'][locale]` based on resolver. Arabic translations authored manually with sports-science terminology preserved.

🧩 **Strategy Link:** §3 Change 7-equivalent for rule-based; §1 Tier 2 — bilingual fallbacks.

⚠️ **Risks Resolved:** R-15.

🔗 **Dependencies:** Task 1.7.

🚀 **Unlocks:** Phase 7 Arabic deterministic feedback.

✅ **Verification:**
- Test: `get_elbow_flexion_feedback(150, 'preparatory', 0.9)['message']['ar']` returns valid Arabic.
- Integration: low-Gemini-confidence path returns rule-based Arabic on `locale='ar'`.

---

### Task 4.7: Localize `fallbacks.py`

🎯 **Objective:** When Gemini is unreachable, the user still gets target-language text.

📂 **Files Affected:**
- Modify: `backend/services/llm/fallbacks.py`
- Modify: callers in `backend/services/llm/llm_router.py`

🔧 **Change Summary:** Each fallback function takes `locale` and selects from a `{en, ar}` dict. `CHAT_FALLBACK_TEXT` becomes `CHAT_FALLBACK = {'en': "...", 'ar': "..."}`. Score / session / progress fallbacks format numbers with locale-aware separator if interpolated.

🧩 **Strategy Link:** §3 Change 7.

⚠️ **Risks Resolved:** R-16, R-45.

🔗 **Dependencies:** Task 4.5.

🚀 **Unlocks:** Phase 7 Gemini-down UX in Arabic.

✅ **Verification:**
- Force Gemini timeout in test; chat returns Arabic fallback under `locale='ar'`.
- Test: `fallback_session_summary(data, locale='ar').summary` contains Arabic text.

---

### Task 4.8: Replace HTTPException English `detail` strings with error codes

🎯 **Objective:** Backend never sends user-facing English; frontend resolves codes via i18n.

📂 **Files Affected:**
- Modify: `backend/routers/chat.py` (`Invalid chat payload` → `chat_invalid_payload`)
- Modify: `backend/routers/mvp.py` (`Video file could not be opened.` → `video_open_failed`, `server_busy_retry` already a code, etc.)
- Modify: `backend/routers/analysis.py`, `feedback.py`, `history.py`, `sessions.py`, `user.py`, `recommendation_routes.py`
- Modify: `src/services/api.service.ts`, `chat.service.ts` (translate `error.response.data.detail` via `t('errors.<code>')` with English fallback)
- Create: `backend/contracts/errors.py` (Enum of error codes)
- Modify: `src/i18n/locales/en/errors.json` (one entry per code)

🔧 **Change Summary:** Define a closed `ErrorCode` enum on the backend. Every `HTTPException(status_code=X, detail=...)` raises with `detail=ErrorCode.<NAME>.value` (snake_case string). Frontend service layer wraps thrown errors: `new Error(t(\`errors.${code}\`, { defaultValue: humanReadableFallback }))`. Add a small helper `mapBackendError(err): { code: string, message: string }`.

🧩 **Strategy Link:** §3 Change 4 backend; §2.B "Returning error codes."

⚠️ **Risks Resolved:** R-17, R-29, R-47 (chat stream errors).

🔗 **Dependencies:** Task 1.7.

🚀 **Unlocks:** Phase 7 Arabic error UX.

✅ **Verification:**
- Test: triggering each error path returns the expected code in `detail`.
- Frontend: invalid upload triggers Arabic-translated banner under `locale='ar'`.

---

### Task 4.9: Localize streaming SSE error payloads

🎯 **Objective:** Streaming chat error events carry codes, not raw English exception strings.

📂 **Files Affected:**
- Modify: `backend/routers/chat.py` (`_sse_generator` `event: error` payload)
- Modify: `src/services/chat.service.ts` (`parseSSEEvents` translates code on receive)

🔧 **Change Summary:** SSE error payload becomes `{code: string, message?: string}`. Frontend's `callbacks.onError` receives `new Error(t('errors.' + code, { defaultValue: message ?? code }))`.

🧩 **Strategy Link:** §3 Change 4 + §2.C streaming.

⚠️ **Risks Resolved:** R-47.

🔗 **Dependencies:** Tasks 4.4, 4.8.

🚀 **Unlocks:** Phase 7 Arabic chat error UX.

✅ **Verification:**
- Force a Gemini error mid-stream; client banner reads the translated code, not raw English.

---

## Phase 5 — Enum & Data Model Refactor

🎯 **Goal:** Decouple stable machine keys from display labels. Migrate existing data using the additive-first pattern.

---

### Task 5.1: Define backend `Verdict` and `ScoreTier` Literal enums

🎯 **Objective:** Replace free-string `verdict` and `score_tier` with closed enums on the wire.

📂 **Files Affected:**
- Modify: `backend/services/llm/output_schemas.py`
- Modify: `backend/contracts/mvp.py`
- Modify: `backend/contracts/history.py`

🔧 **Change Summary:** Define `class Verdict(str, Enum): GOOD='good'; NEEDS_WORK='needs_work'; LOW_CONFIDENCE='low_confidence'; UNKNOWN='unknown'`. Same for `ScoreTier`. Update `MetricExplanation.verdict`, `ShotFeedbackOutput.score_tier`, `AnalysisSummary.score_tier` to use the enum types.

🧩 **Strategy Link:** §3 Change 6.

⚠️ **Risks Resolved:** Pre-condition for R-12, R-32.

🔗 **Dependencies:** None.

🚀 **Unlocks:** Tasks 5.2, 5.3, 5.4.

✅ **Verification:**
- Pydantic raises `ValidationError` on `verdict='Low Confidence'` (capital with space).
- Existing test fixtures continue to pass (some require lowercase fixture updates).

---

### Task 5.2: Rewrite `mvp/core/metrics.py` to emit lowercase enum keys

🎯 **Objective:** Pipeline emits the new enum values everywhere `verdict` is set.

📂 **Files Affected:**
- Modify: `backend/mvp/core/metrics.py` (`_assign_verdict` and all callers)
- Modify: `backend/mvp/core/pipeline.py` (line 99 `"Good" if ... else "Needs Work"` → `"good"` / `"needs_work"`)
- Modify: `backend/services/mvp_job_service.py` (line 567 `payload["verdict"] = "Low Confidence"` → `"low_confidence"`)

🔧 **Change Summary:** Change every literal: `"Good"` → `"good"`, `"Needs Work"` → `"needs_work"`, `"Low Confidence"` → `"low_confidence"`, `"Unknown"` → `"unknown"`.

🧩 **Strategy Link:** §3 Change 6.

⚠️ **Risks Resolved:** R-12 (backend half).

🔗 **Dependencies:** Task 5.1.

🚀 **Unlocks:** Tasks 5.5, 5.6.

✅ **Verification:**
- All MVP tests pass after fixture updates.
- Hitting `/mvp/result/{job_id}` returns `verdict: 'good'` (not `'Good'`).

---

### Task 5.3: SQL migration — lowercase existing verdict / score_tier rows

🎯 **Objective:** Backfill data so dual-read works with one truth (lowercase keys).

📂 **Files Affected:**
- Create: `supabase/migrations/2026_04_28_004_lowercase_enums.sql`

🔧 **Change Summary:** `UPDATE analysis_summaries SET score_tier = LOWER(score_tier) WHERE score_tier ~ '[A-Z]';` Add CHECK constraint `score_tier IN ('elite','great','good','fair','poor','unknown')`. Same idempotent transform for any other table storing these values.

🧩 **Strategy Link:** §5 Migration — Bucket 1 enum-like normalization.

⚠️ **Risks Resolved:** R-12 (data normalization), R-32.

🔗 **Dependencies:** Task 5.2.

🚀 **Unlocks:** Frontend can rely on lowercase keys (Task 5.4).

✅ **Verification:**
- `SELECT DISTINCT score_tier FROM analysis_summaries;` returns only lowercase values.
- CHECK constraint rejects an INSERT with `score_tier='Elite'`.

---

### Task 5.4: Update `src/types/contracts.ts` to Literal types

🎯 **Objective:** TypeScript catches any code still comparing to the old strings.

📂 **Files Affected:**
- Modify: `src/types/contracts.ts`

🔧 **Change Summary:** `verdict?: 'good' | 'needs_work' | 'low_confidence' | 'unknown'`. `score_tier?: 'elite' | 'great' | 'good' | 'fair' | 'poor' | 'unknown'`. Plus same for `MetricExplanation`.

🧩 **Strategy Link:** §3 Change 6.

⚠️ **Risks Resolved:** R-12 (frontend typing).

🔗 **Dependencies:** Task 5.1.

🚀 **Unlocks:** Task 5.5.

✅ **Verification:**
- `npx tsc --noEmit` flags every comparison against old strings.

---

### Task 5.5: Refactor MVPAnalysisScreen to use enum keys

🎯 **Objective:** Stop `m.verdict === 'Low Confidence'`; use stable key + i18n label.

📂 **Files Affected:**
- Modify: `src/screens/MVPAnalysisScreen.tsx` (lines 361–366)
- Modify: `src/i18n/locales/en/enums.json`

🔧 **Change Summary:** Equality check: `m.verdict === 'low_confidence'`. Display: `t(\`enums.verdict.${m.verdict}\`)`. Display unit fallback: `t('analysis.metric.na')`.

🧩 **Strategy Link:** §3 Change 6.

⚠️ **Risks Resolved:** R-12.

🔗 **Dependencies:** Tasks 5.2, 5.3, 5.4.

🚀 **Unlocks:** Phase 7 Arabic verdict labels.

✅ **Verification:**
- Visual smoke: low-confidence metric still shows "Low Confidence" label and the "--" / "N/A" UI.

---

### Task 5.6: Update `theme/scoreTier.ts` and `getScoreTier` to return enum keys

🎯 **Objective:** Color palette keys remain stable English (machine), display label only via `t()`.

📂 **Files Affected:**
- Modify: `src/theme/scoreTier.ts` (`SCORE_TIER_CARD_SURFACE` keys stay English)
- Modify: `src/constants/theme.ts` (`getScoreTier` returns `'elite' | ...`)
- Modify: any caller showing tier text (e.g., `TierBadge.tsx`) — render via `t('enums.tier.' + tier)`

🔧 **Change Summary:** No change to palette key strings (they're internal). `TierBadge` lookup: `<Text>{t(\`enums.tier.${tier}\`)}</Text>`.

🧩 **Strategy Link:** §3 Change 6 + §6 (don't translate machine keys).

⚠️ **Risks Resolved:** R-32, R-70.

🔗 **Dependencies:** Tasks 5.4, 3.2.

🚀 **Unlocks:** Phase 7 Arabic tier labels.

✅ **Verification:**
- Color rendering unchanged.
- Text label switches with `t()`.

---

### Task 5.7: Refactor onboarding option lists to `{value, labelKey}`

🎯 **Objective:** Stop sending display strings as backend values for `position`, `primary_goal`, `training_frequency`.

📂 **Files Affected:**
- Modify: `src/screens/OnboardingScreen.tsx` (lines 22–65 and rendering)
- Modify: `src/screens/ProfileScreen.tsx` (Edit Profile modal — lines 415–425)
- Modify: `src/i18n/locales/en/onboarding.json` (or `enums.json`)

🔧 **Change Summary:** Replace `positions = ['Guard','Forward','Center','All-Around']` with `POSITION_OPTIONS = [{value:'guard'}, {value:'forward'}, ...] as const`. Render: `t('enums.position.' + value)`. Same pattern for `goalOptions` (`improve_shooting_accuracy`, `perfect_form`, etc.) and `trainingFrequencyOptions` (`one_to_two_per_week`, `three_to_four_per_week`, `five_plus_per_week`). Hand and coaching style already use `{value, label}` shape — convert to `{value, labelKey}`.

🧩 **Strategy Link:** §3 Change 6 + §2.D.

⚠️ **Risks Resolved:** R-3 (option lists), R-49, R-63.

🔗 **Dependencies:** Tasks 3.2, 5.4.

🚀 **Unlocks:** Tasks 5.8, 5.9.

✅ **Verification:**
- `npx tsc --noEmit` passes.
- Selected onboarding answers send `'guard'` (lowercase) to backend, not `'Guard'`.

---

### Task 5.8: SQL migration — normalize `position`, `coaching_style`, `dominant_hand`, `training_frequency`, `primary_goal` keys

🎯 **Objective:** Backfill DB to lowercase enum keys for existing users.

📂 **Files Affected:**
- Create: `supabase/migrations/2026_04_28_005_normalize_profile_enums.sql`

🔧 **Change Summary:** SQL UPDATE with explicit mapping per column:
- `users.position`: `'Guard' → 'guard'`, `'Forward' → 'forward'`, `'Center' → 'center'`, `'All-Around' → 'all_around'`
- `user_profiles.coaching_style`: lowercase (already mostly lowercase)
- `user_profiles.dominant_hand`: lowercase (already lowercase)
- `user_profiles.training_frequency`: `'1-2 times per week' → 'one_to_two_per_week'`, `'3-4 times per week' → 'three_to_four_per_week'`, `'5+ times per week' → 'five_plus_per_week'`
- `user_profiles.primary_goal`: kept raw (free-text), but if it matches one of the canonical onboarding options, map to a key; else leave as-is and set `primary_goal_lang` via `langdetect`. (Use a Python-side script for the langdetect step.)
- Add CHECK constraints where the set is closed.

🧩 **Strategy Link:** §5 Migration — Bucket 1.

⚠️ **Risks Resolved:** R-3 (option-list values), R-49, R-63.

🔗 **Dependencies:** Tasks 1.3, 5.7.

🚀 **Unlocks:** Task 5.9.

✅ **Verification:**
- `SELECT DISTINCT position FROM users;` returns only `guard|forward|center|all_around`.
- CHECK constraint rejects `'Guard'`.

---

### Task 5.9: Backfill `primary_goal_lang` via langdetect

🎯 **Objective:** Tag every existing free-text goal with its detected language so Phase 6 LLM context filter can use it.

📂 **Files Affected:**
- Create: `backend/scripts/backfill_primary_goal_lang.py`

🔧 **Change Summary:** Iterate every `user_profiles` row with `primary_goal_lang IS NULL` and `primary_goal IS NOT NULL`. Run `langdetect.detect()`. Map result: `'ar'` → `'ar'`; anything else → `'en'`. Update row. Run as one-shot script during deployment.

🧩 **Strategy Link:** §5 Migration — Bucket 2.

⚠️ **Risks Resolved:** R-59 (free-text language tag).

🔗 **Dependencies:** Tasks 1.3, 5.8.

🚀 **Unlocks:** Phase 7 launch.

✅ **Verification:**
- `SELECT primary_goal_lang, COUNT(*) FROM user_profiles GROUP BY 1;` shows tagged values.
- Manual spot-check: 10 random rows where the language matches the goal text.

---

### Task 5.10: Refactor `score_components.name` substring matching to enum keys

🎯 **Objective:** Stop using `name.toLowerCase().includes('elbow')` heuristic.

📂 **Files Affected:**
- Modify: `src/screens/MVPAnalysisScreen.tsx` (lines 225–233 — `fmv`, `fcv` helpers)

🔧 **Change Summary:** Backend already emits `score_components[].name` as stable English keys (`elbow_extension`, `balance`, `release`, `loading`). Replace `.find(c => c.name?.toLowerCase().includes(k))` with `.find(c => c.name === k)` after auditing the backend to confirm the canonical names.

🧩 **Strategy Link:** §3 Change 6.

⚠️ **Risks Resolved:** R-54.

🔗 **Dependencies:** Audit of backend score-components naming.

🚀 **Unlocks:** Future renames are explicit, not silently lossy.

✅ **Verification:**
- Test: a session where backend emits `score_components` with `name='loading'` correctly populates `scores.alignment` (or whatever the audit determines is the canonical mapping).

---

## Phase 6 — Chat System Hardening

🎯 **Goal:** Make Coach J fully bilingual and BiDi-correct end-to-end.

---

### Task 6.1: Tag every `chat_history` insert with `language`

🎯 **Objective:** Persisted messages carry the language they were created in.

📂 **Files Affected:**
- Modify: `backend/storage/db.py` (`save_chat_message(user_id, role, content, *, language: str, metadata=None)`)
- Modify: `backend/routers/chat.py` (`_persist_exchange` accepts and forwards `locale`)

🔧 **Change Summary:** Add required keyword `language` to `save_chat_message`. Caller passes the resolved locale. No behavior change for English users; Arabic users now get `language='ar'` on new rows.

🧩 **Strategy Link:** §2.C — tag every chat_history row.

⚠️ **Risks Resolved:** R-10, R-58 (write-side).

🔗 **Dependencies:** Tasks 1.2, 1.7, 4.4.

🚀 **Unlocks:** Tasks 6.2, 6.3.

✅ **Verification:**
- Insert a chat exchange under `locale='ar'`; row in DB has `language='ar'`.

---

### Task 6.2: Filter `recent_chat` in context builder by language

🎯 **Objective:** LLM never sees cross-language history.

📂 **Files Affected:**
- Modify: `backend/chat/context_builder.py` (`_build_context_via_direct_queries` chat_resp query, and `build_user_context` signature)
- Modify: `backend/routers/chat.py` (passes locale into `build_user_context`)

🔧 **Change Summary:** `build_user_context(*, user_id, user_local_context, options, locale)` queries `chat_history` with `.eq('language', locale)`. Same for the RPC `get_coach_context` — extend the SQL function signature to take `p_language` (additive migration).

🧩 **Strategy Link:** §2.C — same-language filter.

⚠️ **Risks Resolved:** R-10, R-65.

🔗 **Dependencies:** Tasks 6.1, 1.2.

🚀 **Unlocks:** Task 6.3.

✅ **Verification:**
- Test: user with 5 English + 3 Arabic messages; `build_user_context(locale='ar')` returns only the 3 Arabic.

---

### Task 6.3: Add cross-language bridge sentence

🎯 **Objective:** When same-language history is empty, give the LLM a one-line context bridge.

📂 **Files Affected:**
- Modify: `backend/chat/context_builder.py`
- Modify: `backend/services/llm/prompt_builders.py` (`build_chat_prompt`)

🔧 **Change Summary:** If `len(filtered_recent_chat) < 3` AND prior cross-language history exists, prepend a bridge string to the system prompt. Bridge text is locale-aware: `en → "(Previous conversation was in Arabic. Continue in English.)"`, `ar → "(تمت المحادثة السابقة بالإنجليزية. تابع بالعربية الفصحى.)"`.

🧩 **Strategy Link:** §4 — bridge strategy.

⚠️ **Risks Resolved:** R-65 (continuity).

🔗 **Dependencies:** Tasks 6.2, 4.4.

🚀 **Unlocks:** Smooth language switch UX.

✅ **Verification:**
- Test: user switches from English to Arabic; first Arabic chat reply does NOT reference English-only prior content but the prompt includes the bridge.

---

### Task 6.4: Implement post-call language detection + retry guard

🎯 **Objective:** Catch the rare case where Gemini ignores the language directive; retry once.

📂 **Files Affected:**
- Modify: `backend/services/llm/llm_router.py` (`chat`, `chat_stream`)
- Add dependency: `langdetect>=1.0.9` to `backend/requirements.txt`

🔧 **Change Summary:** After the chat response is fully assembled (or for streaming, after `done` event), call `langdetect.detect(text)`. If the detected language does NOT match `locale` AND `locale='ar'`, retry once with a stronger directive prepended (`"⚠️ MUST RESPOND IN ARABIC ONLY"`). Log mismatch rate. Skip detection if response is < 30 chars (langdetect unreliable).

🧩 **Strategy Link:** §2.C — three layers of language enforcement.

⚠️ **Risks Resolved:** R-9 (enforcement layer 3).

🔗 **Dependencies:** Task 4.4.

🚀 **Unlocks:** Quality gate for Phase 7.

✅ **Verification:**
- Mock Gemini returning English for `locale='ar'`; retry logic engages; second call returns Arabic; final response is Arabic.
- Log entry produced on mismatch.

---

### Task 6.5: Per-message direction detection in `ChatBubble`

🎯 **Objective:** Each chat bubble renders in its own text direction regardless of UI direction.

📂 **Files Affected:**
- Modify: `src/components/ChatBubble.tsx`

🔧 **Change Summary:** Add `detectDir(s: string): 'rtl' | 'ltr'` based on first-strong character match against `[֐-ࣿ]` (Hebrew + Arabic block). Apply `writingDirection: detectDir(message)` to the `Text` component. Streaming cursor `|` rendered absolutely-positioned at the trailing edge using `start: 0` semantics (or simpler: append after the message text always, and let writingDirection handle visual placement).

🧩 **Strategy Link:** §3 Change 10.

⚠️ **Risks Resolved:** R-27, R-10 (visual cohabitation).

🔗 **Dependencies:** Task 3.6.

🚀 **Unlocks:** Mixed-language transcripts render correctly.

✅ **Verification:**
- Snapshot test: bubble with English content has LTR direction; bubble with Arabic has RTL.
- Manual: chat with mixed-language history shows each bubble correctly oriented.

---

### Task 6.6: Make chat bubble corner radii logical

🎯 **Objective:** Bubble tails point toward the speaker even after RTL flip.

📂 **Files Affected:**
- Modify: `src/components/ChatBubble.tsx` (already touched in 3.6, verify here)

🔧 **Change Summary:** Confirm `borderTopLeftRadius` → `borderTopStartRadius` etc. applied. User bubble: large start corners, small bottom-end corner. Coach bubble: large end corners, small bottom-start corner. Verify by toggling `I18nManager.isRTL`.

🧩 **Strategy Link:** §3 Change 3.

⚠️ **Risks Resolved:** R-5.

🔗 **Dependencies:** Task 3.6.

🚀 **Unlocks:** RTL chat visually correct.

✅ **Verification:**
- Render in both directions; tail points to correct corner.

---

### Task 6.7: Translate ChatScreen `COACH_GREETING`, `QUICK_CHIPS`, contextLabel chips

🎯 **Objective:** Initial chat surfaces speak the user's language.

📂 **Files Affected:**
- Modify: `src/screens/ChatScreen.tsx` (lines 35–40, 42–46, 165–172, 374, 385)
- Modify: `src/i18n/locales/en/chat.json`

🔧 **Change Summary:** `COACH_GREETING.content = t('chat.greeting')` (resolved at provider mount, not at module load). `QUICK_CHIPS = [{key:'review_last_shot'}, ...]` — render via `t('chat.quick_chips.' + key)`. `contextLabel` parts join via `t('chat.context.joiner')` (English: `' + '`, Arabic: `' + '` with FSI/PDI marks via format module). Composer placeholder `t('chat.composer.placeholder')`. Send button `t('common.send')`.

🧩 **Strategy Link:** §3 Change 2 (chat-specific portion).

⚠️ **Risks Resolved:** R-11, R-33 (also fixes the `goals_and_drills` key bug — rename to `recent_summaries` to match backend `context_used.recent_summaries_count`).

🔗 **Dependencies:** Tasks 3.2, 3.4.

🚀 **Unlocks:** Phase 7 Arabic chat copy.

✅ **Verification:**
- Open chat in English; greeting and chips identical to before.
- ContextLabel chip shows correct parts based on actual `context_used` boolean flags.

---

### Task 6.8: RTL-mirror `Switch` and direction-aware chevrons

🎯 **Objective:** Toggles and back/forward icons match locale direction.

📂 **Files Affected:**
- Create: `src/components/RTLSwitch.tsx`
- Create: `src/components/Chevron.tsx`
- Modify: `src/components/ScreenHeader.tsx` (use `<Chevron direction='back' />` instead of literal `chevron-back`)
- Modify: `src/screens/HomeScreen.tsx` (use `<Chevron direction='forward' />`)
- Modify: `src/components/MetricsTable.tsx`

🔧 **Change Summary:** `RTLSwitch` wraps RN `Switch` and applies `transform:[{scaleX: isRTL ? -1 : 1}]` if needed (or uses platform-specific RTL handling). `Chevron` selects glyph: `direction='back'` resolves to `chevron-back` in LTR and `chevron-forward` in RTL (and vice versa). Replaces every literal `Ionicons name="chevron-back"` / `"chevron-forward"`.

🧩 **Strategy Link:** §1 Tier 2 — direction-aware components.

⚠️ **Risks Resolved:** R-7, R-31.

🔗 **Dependencies:** Tasks 2.4, 3.6.

🚀 **Unlocks:** Phase 7 Arabic navigation feels native.

✅ **Verification:**
- ScreenHeader back arrow points right in Arabic, left in English.
- Profile screen toggles animate in the visually-correct direction.

---

### Task 6.9: Streaming SSE done payload includes `language`

🎯 **Objective:** Frontend can label the assistant message with its language for direction detection.

📂 **Files Affected:**
- Modify: `backend/routers/chat.py` (`_sse_generator` `done` payload includes `language`)
- Modify: `src/services/chat.service.ts` (`ChatStreamDone` type adds `language`)
- Modify: `src/types/contracts.ts`

🔧 **Change Summary:** `done` event payload becomes `{model, context_used, language, usage}`. Frontend stores `language` on the message and `ChatBubble` uses it as a hint (alongside first-strong detection).

🧩 **Strategy Link:** §6 — direction detection per message.

⚠️ **Risks Resolved:** R-64.

🔗 **Dependencies:** Tasks 4.4, 6.5.

🚀 **Unlocks:** More reliable direction detection for short replies.

✅ **Verification:**
- SSE done event carries `language='ar'` when chat was Arabic.

---

### Task 6.10: Composer keyboard hints

🎯 **Objective:** Arabic users get appropriate text input behavior.

📂 **Files Affected:**
- Modify: `src/screens/ChatScreen.tsx` (TextInput composer)
- Modify: `src/screens/LoginScreen.tsx` (input renderer)

🔧 **Change Summary:** Composer `autoCorrect` defaults to `true` and `autoCapitalize='sentences'` (RN handles Arabic correctly with default). LoginScreen email field stays `autoCorrect={false}` — it's an identifier; password the same. Add `textContentType` hints on iOS where appropriate.

🧩 **Strategy Link:** §1 Tier 3 polish.

⚠️ **Risks Resolved:** R-28.

🔗 **Dependencies:** Task 3.2.

🚀 **Unlocks:** Better typing UX for Arabic users.

✅ **Verification:**
- Manual: typing Arabic in chat composer engages OS Arabic spell-check.

---

## Phase 7 — Arabic Enablement (Feature Flag)

🎯 **Goal:** Author Arabic content, hide behind a feature flag, validate end-to-end with internal users, then roll out publicly.

---

### Task 7.1: Author Arabic translation catalog

🎯 **Objective:** Every English key has an Arabic translation.

📂 **Files Affected:**
- Create: `src/i18n/locales/ar/common.json`, `home.json`, `chat.json`, `analysis.json`, `onboarding.json`, `profile.json`, `drills.json`, `enums.json`, `errors.json`, `auth.json`

🔧 **Change Summary:** Professional translator (or translation agency) authors Modern Standard Arabic for every key in `locales/en/*.json`. Maintain a glossary doc (`docs/i18n/glossary-en-ar.md`) for basketball-specific terminology (e.g., "elbow flexion" → "ثني الكوع") for consistency.

🧩 **Strategy Link:** §5 Phase 2 of migration.

⚠️ **Risks Resolved:** R-1, R-2, R-3, R-23, R-30, R-39, R-43, R-44, R-51, R-53, R-56, R-66 (Arabic content).

🔗 **Dependencies:** Tasks 3.2, 3.3, 3.8.

🚀 **Unlocks:** Tasks 7.7, 7.8, 7.10, 7.11.

✅ **Verification:**
- Every key in `locales/en/*.json` has a corresponding entry in `locales/ar/*.json`.
- Linter script: `node scripts/i18n/verify-parity.ts` exits 0.
- Native-speaker review of glossary terms.

---

### Task 7.2: Arabic Coach J persona and rule-based feedback

🎯 **Objective:** Native Arabic prompt content for the LLM and deterministic feedback.

📂 **Files Affected:**
- Modify: `backend/services/llm/prompt_builders.py` (`_COACH_PERSONA['ar']` etc. populated)
- Modify: `backend/feedback/rules.py` (every `{en, ar}` dict populated)
- Modify: `backend/services/llm/fallbacks.py` (Arabic strings populated)

🔧 **Change Summary:** Translator (sports-domain familiar) writes the Arabic persona text, language rule, chat rules, and every per-rule message + details. Manually reviewed by a basketball coach who reads Arabic, where possible.

🧩 **Strategy Link:** §5 — Phase 2.

⚠️ **Risks Resolved:** R-9 (Arabic content), R-15 (Arabic content), R-16 (Arabic content).

🔗 **Dependencies:** Tasks 4.3, 4.6, 4.7.

🚀 **Unlocks:** Task 7.10.

✅ **Verification:**
- Integration test: end-to-end Arabic chat returns coherent Arabic.
- Sample: 10 sample shots through `feedback/rules.py` produce Arabic that a native speaker validates.

---

### Task 7.3: Arabic drill catalog

🎯 **Objective:** Drill names, descriptions, and instructions in Arabic.

📂 **Files Affected:**
- Modify: `src/i18n/locales/ar/drills.json`
- (Drill data layer — see Task 8.4 for the full migration.)

🔧 **Change Summary:** Each drill from `src/constants/drills.ts` becomes a key set: `drills.<id>.name`, `drills.<id>.description`, `drills.<id>.instruction.<index>`, `drills.<id>.focus_area.<index>`. Same for `WORKOUTS`. Phase 7 adds Arabic translations; Phase 8 (Task 8.4) refactors `drills.ts` to remove inline strings entirely.

🧩 **Strategy Link:** §5 Migration — Bucket 3 app-owned static text.

⚠️ **Risks Resolved:** R-3, R-48 (Arabic content).

🔗 **Dependencies:** Task 7.1.

🚀 **Unlocks:** Task 8.4 (full data-layer cleanup).

✅ **Verification:**
- Drills screen in Arabic shows Arabic drill names and descriptions.

---

### Task 7.4: Add language toggle UI in Profile

🎯 **Objective:** User-visible control to switch between English and Arabic.

📂 **Files Affected:**
- Modify: `src/screens/ProfileScreen.tsx` (add a "Language / اللغة" preference row)
- Modify: `src/i18n/locales/en/profile.json` and `ar/profile.json`

🔧 **Change Summary:** New row under preferences. On tap, opens an action sheet listing `English` and `العربية`. Selection calls `LocaleProvider.setLanguage()`. Show a "Restarting app..." toast immediately before `Updates.reloadAsync()`. Behind a feature flag `EXPO_PUBLIC_ENABLE_ARABIC` (env var).

🧩 **Strategy Link:** §5 Phase 2 — feature flag rollout.

⚠️ **Risks Resolved:** R-1 (user control surface).

🔗 **Dependencies:** Tasks 2.3, 7.1.

🚀 **Unlocks:** Tasks 7.5, 7.6.

✅ **Verification:**
- Toggle hidden when flag = `false`; visible when `true`.
- Tapping `العربية` triggers reload; app restarts with Arabic UI + RTL layout.

---

### Task 7.5: Auto-detect device locale on first launch

🎯 **Objective:** Arabic-locale device users get a one-time prompt to use Arabic.

📂 **Files Affected:**
- Modify: `src/i18n/LocaleProvider.tsx`
- Modify: `src/screens/HomeScreen.tsx` (mount-time check)

🔧 **Change Summary:** On first launch (`@shootrz_language_prompted` flag missing), if device locale is Arabic AND user `preferred_language='en'` (default), show a localized prompt: "Switch to Arabic? / التبديل إلى العربية؟" with Yes/No. Set the flag regardless of choice.

🧩 **Strategy Link:** §5 Phase 3 — public Arabic launch UX.

⚠️ **Risks Resolved:** R-69 (discoverability).

🔗 **Dependencies:** Tasks 7.1, 7.4.

🚀 **Unlocks:** Public rollout.

✅ **Verification:**
- Fresh install on Arabic-locale device shows the prompt once.
- Already-prompted user does not see it again.

---

### Task 7.6: Internal beta rollout

🎯 **Objective:** Validate Arabic UX with internal team before public launch.

📂 **Files Affected:**
- Modify: `app.config.js` (set `EXPO_PUBLIC_ENABLE_ARABIC=true` for beta channel)

🔧 **Change Summary:** Ship a build to the internal Expo channel with the flag enabled. Collect bug reports for two weeks. Triage and fix.

🧩 **Strategy Link:** §5 Phase 2.

⚠️ **Risks Resolved:** Validation gate for the entire plan.

🔗 **Dependencies:** Tasks 7.1, 7.2, 7.3, 7.4, 7.5.

🚀 **Unlocks:** Task 7.7.

✅ **Verification:**
- At least 5 internal users complete one full session (analyze shot + chat + browse drills) in Arabic without UX-blocking bugs.

---

### Task 7.7: Public Arabic launch

🎯 **Objective:** Enable the flag in production.

📂 **Files Affected:**
- Modify: `app.config.js` (production channel sets `EXPO_PUBLIC_ENABLE_ARABIC=true`)

🔧 **Change Summary:** Ship the production build with the flag on. Monitor crash reports, language-mismatch retry rate (Task 6.4), and Supabase `users.preferred_language` adoption.

🧩 **Strategy Link:** §5 Phase 3.

⚠️ **Risks Resolved:** Final delivery.

🔗 **Dependencies:** Task 7.6.

🚀 **Unlocks:** Phase 8.

✅ **Verification:**
- Feature flag `true` for all users.
- Adoption dashboard shows Arabic users week 1.

---

## Phase 8 — Cleanup & Regression Enforcement

🎯 **Goal:** Lock the architecture down. Drop deprecated columns, escalate ESLint to error-level, remove the last hardcoded strings.

---

### Task 8.1: Drop deprecated columns

🎯 **Objective:** After two stable releases on the new shape, drop dual-read fallbacks.

📂 **Files Affected:**
- Create: `supabase/migrations/2026_06_xx_drop_deprecated.sql` (date set when actually executed)

🔧 **Change Summary:** If any helper columns were kept dual-read (e.g., a transitional `position_old` column from the migration), drop them. None should remain if Tasks 5.3 and 5.8 normalized in place; this task is a no-op if so. Confirm by reading the schema.

🧩 **Strategy Link:** §5 Phase 4 cleanup.

⚠️ **Risks Resolved:** Schema hygiene.

🔗 **Dependencies:** Task 7.7 + 2 production weeks.

🚀 **Unlocks:** Lower DB row size.

✅ **Verification:**
- `\d users` and `\d user_profiles` show only the canonical columns.

---

### Task 8.2: Escalate ESLint rules to error-level

🎯 **Objective:** Make regression unmergeable.

📂 **Files Affected:**
- Modify: `eslint.config.js`

🔧 **Change Summary:** Promote the JSX-string rule to `error`. Add rule banning direct import of `Alert` from `'react-native'` outside `src/utils/alert.ts`. Add rule banning literal `Ionicons name="chevron-back|chevron-forward"` outside `src/components/Chevron.tsx`.

🧩 **Strategy Link:** §6 — "Don't ship without an ESLint rule."

⚠️ **Risks Resolved:** Regression of R-2, R-4, R-7, R-24.

🔗 **Dependencies:** Tasks 3.2, 3.4, 3.6, 6.8.

🚀 **Unlocks:** Project enters maintenance mode.

✅ **Verification:**
- `npx eslint src/` exits 0.
- A PR reintroducing `Alert.alert()` directly fails CI.

---

### Task 8.3: Refactor `drills.ts` to id-only catalog

🎯 **Objective:** Remove the last inline English strings from `src/constants/drills.ts`.

📂 **Files Affected:**
- Modify: `src/constants/drills.ts`
- Modify: callers: `DrillsScreen.tsx`, `DrillDetailScreen.tsx`, `WorkoutsScreen.tsx`
- (Catalog files already populated in Tasks 7.1, 7.3.)

🔧 **Change Summary:** `Drill` type loses `name`, `description`, `instructions`, `focusAreas`. Keeps `id`, `category`, `difficulty`, `duration`, optional `videoUrl`. Callers render labels via `t('drills.' + drill.id + '.name')` etc.

🧩 **Strategy Link:** §5 Migration — Bucket 3.

⚠️ **Risks Resolved:** R-3, R-48 (final cleanup).

🔗 **Dependencies:** Tasks 7.1, 7.3, 7.7.

🚀 **Unlocks:** Adding new drills only requires JSON edits.

✅ **Verification:**
- `grep -E "name:|description:|instructions:" src/constants/drills.ts` returns zero matches.
- All drills still render correctly in both languages.

---

### Task 8.4: End-to-end regression tests

🎯 **Objective:** Lock the system against future breakage.

📂 **Files Affected:**
- Create: `src/screens/__tests__/i18n-rtl.regression.test.tsx`
- Create: `backend/tests/test_chat_locale.py`

🔧 **Change Summary:** Frontend regression: snapshot every top-level screen under both `lng='en'` (forced LTR) and `lng='ar'` (forced RTL). Verify no hardcoded English text appears in RTL snapshot. Backend regression: `test_chat_locale` covers (a) Arabic body field → Arabic response, (b) Accept-Language header → Arabic response, (c) cross-language history filter, (d) bridge sentence, (e) `_sanitize_str` preserves Arabic punctuation.

🧩 **Strategy Link:** Architectural validation.

⚠️ **Risks Resolved:** Future regression of all 70 risks.

🔗 **Dependencies:** Phases 1–7 complete.

🚀 **Unlocks:** Confidence to add a third language.

✅ **Verification:**
- `npm test` and `python -m pytest backend/` both green.
- Tests cover ≥ 90% of the catalog namespaces.

---

### Task 8.5: Documentation and contributor guide

🎯 **Objective:** New contributors can add features without re-introducing locale bugs.

📂 **Files Affected:**
- Create: `docs/i18n/contributor-guide.md`
- Create: `docs/i18n/glossary-en-ar.md`
- Modify: `CLAUDE.md` (add reference to the contributor guide)

🔧 **Change Summary:** Document: how to add a new translation key, how to run codemods, where the bilingual personas live, how to test RTL locally (`I18nManager.forceRTL` + dev menu reload), how to add a third language. Glossary lists every basketball-specific term and its agreed Arabic equivalent.

🧩 **Strategy Link:** Long-term scalability.

⚠️ **Risks Resolved:** Knowledge transfer.

🔗 **Dependencies:** All prior tasks.

🚀 **Unlocks:** Adding French/Spanish/Turkish becomes a one-week project.

✅ **Verification:**
- New engineer follows the guide to add 5 keys without consulting Slack — review only the PR.

---

## Cross-Phase Dependency Graph (high-level)

```
Phase 1 (DB + locale resolver + Accept-Language)
   ├─→ Phase 2 (i18n runtime, alert wrapper, format module, app.json locales)
   │    └─→ Phase 3 (codemods + ESLint warn)
   │         ├─→ Phase 5 (enum refactor, depends on Phase 3 catalog organization)
   │         └─→ Phase 6 (chat hardening, depends on Phase 3 components touched)
   └─→ Phase 4 (LLM locale awareness, sanitizer, error codes)
        ├─→ Phase 5 (data model uses locale-aware error codes)
        └─→ Phase 6 (chat persists locale, filters context, retry guard)
             └─→ Phase 7 (Arabic content + feature-flagged rollout)
                  └─→ Phase 8 (cleanup, ESLint error, regression tests, docs)
```

## Risk Coverage Final Audit

Every R-N from the audit appears in at least one task's "Risks Resolved" field:

- R-1 → Tasks 2.1, 2.2, 2.3, 2.4, 7.1, 7.4
- R-2 → Tasks 3.2, 3.3, 7.1
- R-3 → Tasks 5.7, 5.8, 7.1, 7.3, 8.3
- R-4 → Tasks 3.5, 3.6, 8.2
- R-5 → Tasks 3.5, 3.6, 6.6
- R-6 → Task 3.6
- R-7 → Tasks 6.8, 8.2
- R-8 → Task 3.6
- R-9 → Tasks 4.3, 4.4, 4.5, 6.4, 7.2
- R-10 → Tasks 1.2, 6.1, 6.2, 6.5
- R-11 → Tasks 6.7
- R-12 → Tasks 5.1, 5.2, 5.3, 5.4, 5.5
- R-13 → Task 4.1
- R-14 → Task 4.2
- R-15 → Tasks 4.6, 7.2
- R-16 → Tasks 4.7, 7.2
- R-17 → Task 4.8
- R-18 → Tasks 2.5
- R-19 → Tasks 2.5, 3.9
- R-20 → Task 2.5
- R-21 → Task 3.9
- R-22 → Tasks 3.6, 3.11
- R-23 → Tasks 3.2, 3.3, 7.1
- R-24 → Tasks 2.6, 3.4, 8.2
- R-25 → Task 2.3
- R-26 → Task 2.3
- R-27 → Task 6.5
- R-28 → Task 6.10
- R-29 → Task 4.8
- R-30 → Tasks 3.2, 7.1
- R-31 → Task 6.8
- R-32 → Tasks 5.3, 5.6
- R-33 → Task 6.7
- R-34 → Tasks 4.5, 7.2
- R-35 → Tasks 1.3, 6.1
- R-36 → Tasks 3.2, 5.7
- R-37 → Tasks 4.5, 6.2
- R-38 → Task 6.2 (filter)
- R-39 → Tasks 3.2, 7.1
- R-40 → Task 2.5
- R-41 → Task 6.7
- R-42 → Task 4.1
- R-43 → Tasks 3.2, 7.1
- R-44 → Tasks 3.2, 3.3, 7.1
- R-45 → Task 4.7
- R-46 → Tasks 2.6, 3.4
- R-47 → Tasks 4.8, 4.9
- R-48 → Tasks 7.3, 8.3
- R-49 → Tasks 5.7, 5.8
- R-50 → Tasks 4.5, 6.2
- R-51 → Tasks 3.2, 7.1
- R-52 → Task 3.9
- R-53 → Tasks 3.2, 3.6, 7.1
- R-54 → Task 5.10
- R-55 → Task 3.11
- R-56 → Tasks 3.2, 7.1
- R-57 → Task 3.10
- R-58 → Tasks 1.2, 6.1
- R-59 → Tasks 1.1, 1.3, 5.9
- R-60 → Task 5.10 (machine keys preserved)
- R-61 → Tasks 3.3, 7.1
- R-62 → Task 8.4 (regression test)
- R-63 → Tasks 5.7, 5.8
- R-64 → Task 6.9
- R-65 → Tasks 6.2, 6.3
- R-66 → Task 3.2 (catalog conversion)
- R-67 → Tasks 1.4, 1.5, 1.7
- R-68 → Task 2.5
- R-69 → Tasks 2.7, 7.5
- R-70 → Task 5.6

**All 70 risks mapped. Plan is complete.**

---

## Self-Review

**Spec coverage:** Every audit risk R-1 through R-70 is mapped to at least one task in the matrix above. The coverage table cross-references both directions (risk → task and task → risk).

**Placeholder scan:** No `TBD`, `TODO`, `implement later`, or "similar to Task N" references. Every task has explicit file paths, change summaries, and verification steps.

**Type consistency:** Enum keys (`good`, `needs_work`, `low_confidence`, `unknown`, `elite`, `great`, `fair`, `poor`) used consistently across Tasks 5.1–5.6. Locale type `Literal['en','ar']` consistent across Tasks 1.4, 1.6, 4.2, 4.4, 4.5, 4.6, 4.7. `LocaleProvider` API (`{language, dir, isRTL, setLanguage}`) consistent across Tasks 2.3, 2.4, 7.4.

**Scope check:** This is a single coherent migration project. While large, it is sequential and each phase delivers shippable progress. Decomposition into smaller plans would create cross-cutting dependencies that are harder to manage than phases within one plan.

**Ambiguity check:** Action verbs are concrete ("rename", "add column", "set header"). No "improve", "enhance", "consider" language. File paths are exact.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-28-bilingual-arabic-rtl-rollout.md`.

Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task in the order shown above (Phase 0 mapping is non-implementation, start with Task 1.1). Review between tasks, fast iteration. Best for a 60+-task plan because each subagent has the right narrow context.

**2. Inline Execution** — Execute tasks in this session in batches with checkpoints (e.g., Phase 1 in one batch, then review).

Which approach?
