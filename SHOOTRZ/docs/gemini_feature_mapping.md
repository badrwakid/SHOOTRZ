# Gemini Feature Mapping

Status table of all features using Gemini, with file locations and fallback logic.

## Feature Status

| Feature | Status | Service Method | Files | Fallback |
|---------|--------|---------------|-------|----------|
| Coach J Chat | Active | `llm_service.chat()` | `routers/chat.py`, `prompt_builders.py` | Canned text |
| Coach J Streaming | Active | `llm_service.chat_stream()` | `routers/chat.py`, `prompt_builders.py` | Canned text delta |
| Shot Feedback Enrichment | Active | `llm_service.get_shot_feedback()` | `services/mvp_job_service.py` | Rule-based `metrics.py` text |
| Drill Recommendation Explanation | Active | `llm_service.get_drill_recommendation()` | `recommender/recommend_service.py` | Generic explanation |
| Session Summary | Active | `llm_service.get_session_summary()` | `services/mvp_job_service.py` | Template summary |
| Progress Insight | Active | `llm_service.get_progress_insight()` | `routers/user.py` | Stat comparison |
| Feedback Rephrasing | Active | `llm_service.rephrase_feedback()` | `feedback/rules.py` | Original rule text |

## File Location Map

### New Files (created)

| File | Purpose |
|------|---------|
| `backend/services/llm/__init__.py` | Package init, exports `llm_service` |
| `backend/services/llm/gemini_client.py` | `GeminiService` class wrapping `google-genai` SDK |
| `backend/services/llm/output_schemas.py` | Pydantic v2 models for all structured outputs |
| `backend/services/llm/prompt_builders.py` | Prompt template functions for each use case |
| `backend/services/llm/fallbacks.py` | Deterministic fallback generators |
| `backend/services/llm/llm_router.py` | `LLMService` unified entrypoint |

### Modified Files

| File | Changes |
|------|---------|
| `backend/routers/chat.py` | Uses `llm_service` instead of `llm_provider`, prompt moved to `prompt_builders` |
| `backend/services/mvp_job_service.py` | Added `_enrich_with_gemini()`, Gemini session summary in `_save_to_supabase()` |
| `backend/recommender/recommend_service.py` | Added Gemini explanation after FAISS+bandit selection |
| `backend/routers/recommendation_routes.py` | Passes `weak_areas`/`user_level` to recommend |
| `backend/routers/user.py` | New `GET /api/user/progress-insight` endpoint |
| `backend/feedback/rules.py` | Added `enrich` param + `_enrich_with_llm()` helper |
| `backend/feedback/engine.py` | Passes `enrich` param through |
| `backend/routers/feedback.py` | Exposes `enrich` query parameter |
| `backend/utils/config.py` | Removed OpenAI vars, added `GEMINI_TIMEOUT`, `GEMINI_MAX_RETRIES` |
| `backend/main.py` | Health endpoint includes Gemini status |
| `backend/requirements.txt` | Added `google-genai`, removed `openai` |
| `backend/.env` | Updated model, removed OpenAI keys |

### Deleted Files

| File | Reason |
|------|--------|
| `backend/chat/gemini_client.py` | Replaced by `services/llm/gemini_client.py` |
| `backend/chat/openai_client.py` | OpenAI path removed |
| `backend/chat/llm_provider.py` | Replaced by `services/llm/llm_router.py` |

## Fallback Logic Detail

Every `LLMService` method follows this pattern:

```python
def method(self, **kwargs):
    try:
        # 1. Build prompt via prompt_builders
        # 2. Call GeminiService.generate_structured()
        # 3. Return validated Pydantic model
    except Exception:
        # 4. Log error
        # 5. Return deterministic fallback (same Pydantic type)
```

The caller never needs to handle the Gemini/fallback branching — the return type
is always the same Pydantic model regardless of whether Gemini succeeded.
