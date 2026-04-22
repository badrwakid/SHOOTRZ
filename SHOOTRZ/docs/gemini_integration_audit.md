# Gemini Integration Audit

File-by-file map of AI-related outputs, rule-based generators, and Gemini integration status.

## Files Using AI / LLM

| File | Before | After | Notes |
|------|--------|-------|-------|
| `backend/chat/gemini_client.py` | Raw REST calls to Gemini API | **Deleted** | Replaced by `services/llm/gemini_client.py` |
| `backend/chat/openai_client.py` | OpenAI SDK fallback | **Deleted** | OpenAI path removed per requirement |
| `backend/chat/llm_provider.py` | Thin facade switching providers | **Deleted** | Replaced by `services/llm/llm_router.py` |
| `backend/routers/chat.py` | Hardcoded Coach J system prompt, used `llm_provider` | Uses `llm_service.chat()` / `chat_stream()`, prompt moved to `prompt_builders` | Clean separation |
| `backend/services/llm/gemini_client.py` | N/A (new) | Official `google-genai` SDK, `GeminiService` class | Batch, structured, streaming |
| `backend/services/llm/llm_router.py` | N/A (new) | Unified `LLMService` entrypoint | Single import for all consumers |
| `backend/services/llm/prompt_builders.py` | N/A (new) | All prompt templates in one place | 7 builder functions |
| `backend/services/llm/output_schemas.py` | N/A (new) | Pydantic v2 models for structured output | 7 schema classes |
| `backend/services/llm/fallbacks.py` | N/A (new) | Deterministic fallbacks for every output type | Zero-downtime guarantee |

## Files Using Rule-Based Text Generation

| File | What It Generates | Gemini Integration |
|------|-------------------|-------------------|
| `backend/mvp/core/metrics.py` | `explanation`, `feedback_summary`, `feedback_bullets`, `score_components[].explanation` | Enriched via `llm_service.get_shot_feedback()` in `mvp_job_service.py` |
| `backend/feedback/rules.py` | `message`, `severity`, `details` per metric | Optional `enrich=True` param rephrases via Gemini |
| `backend/feedback/engine.py` | Delegates to `rules.py` | Passes `enrich` param through |
| `backend/services/mvp_job_service.py` | `strengths`, `improvements` via keyword heuristic | Uses Gemini-generated strengths/improvements when available |
| `backend/mvp/core/video_loader.py` | `quality_warnings` based on video properties | Not integrated (low priority, internal warnings) |
| `backend/inference/phase_detector.py` | Short `reason` strings for internal logic | Not integrated (not user-facing) |

## Files With Hardcoded User-Facing Text

| File | Content | Gemini Integration |
|------|---------|-------------------|
| `backend/routers/chat.py` | Coach J system prompt | Moved to `prompt_builders.build_chat_prompt()` |
| `src/screens/ChatScreen.tsx` | Greeting text, quick chips | Not changed (mobile-side UX copy) |
| `src/constants/drills.ts` | Drill definitions | Not changed (static data, not AI output) |
| `src/services/email.service.ts` | Marketing text | Not changed (static marketing copy) |

## Recommendation System

| File | Current State | Gemini Integration |
|------|--------------|-------------------|
| `backend/recommender/recommend_service.py` | FAISS + LinUCB, returns structured data only | Gemini explanation added after drill selection |
| `backend/routers/recommendation_routes.py` | Returns raw result | Passes `weak_areas`/`user_level`, includes explanation |

## New Endpoints

| Endpoint | File | Purpose |
|----------|------|---------|
| `GET /api/user/progress-insight` | `backend/routers/user.py` | Gemini-powered trend analysis |
| `POST /feedback/generate?enrich=true` | `backend/routers/feedback.py` | LLM-rephrased feedback |

## Migration Priority Summary

1. **Critical (Done)**: Chat system migrated to new Gemini SDK
2. **High (Done)**: Shot feedback enriched with Gemini explanations
3. **Medium (Done)**: Drill recommendations, session summaries, progress insights
4. **Low (Done)**: Feedback rule rephrasing (optional `enrich` flag)
5. **Not Integrated**: Internal warnings, static mobile copy, marketing text
