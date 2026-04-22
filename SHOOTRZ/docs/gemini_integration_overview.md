# Gemini Integration Overview

## Architecture

All AI-generated content in SHOOTRZ flows through a single service layer at
`backend/services/llm/`. No other file in the codebase calls the Gemini API directly.

```
┌─────────────────────────────────────────────────────────────────┐
│                     backend/services/llm/                       │
│                                                                 │
│  ┌───────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │ gemini_client  │  │ prompt_builders  │  │ output_schemas │  │
│  │ (google-genai) │  │ (7 builders)     │  │ (7 Pydantic)   │  │
│  └───────┬───────┘  └────────┬─────────┘  └───────┬────────┘  │
│          │                   │                     │            │
│  ┌───────┴───────────────────┴─────────────────────┴────────┐  │
│  │                    llm_router.py                          │  │
│  │                   (LLMService class)                      │  │
│  └────────────────────────┬──────────────────────────────────┘  │
│                           │                                     │
│  ┌────────────────────────┴──────────────────────────────────┐  │
│  │                    fallbacks.py                            │  │
│  │           (deterministic fallback generators)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

Consumers:
  routers/chat.py ──────────────► llm_service.chat() / chat_stream()
  services/mvp_job_service.py ──► llm_service.get_shot_feedback()
                                  llm_service.get_session_summary()
  recommender/recommend_service ► llm_service.get_drill_recommendation()
  routers/user.py ──────────────► llm_service.get_progress_insight()
  feedback/rules.py ────────────► llm_service.rephrase_feedback()
```

## Data Flow

### Chat Flow
```
User message → routers/chat.py
  → build_chat_prompt(context)
  → llm_service.chat(system_prompt, messages)
    → GeminiService.generate() [google-genai SDK]
    → On failure: return CHAT_FALLBACK_TEXT
  → ChatResponse to mobile app
```

### Shot Feedback Flow
```
Video upload → MVPPipeline → MetricsDerivation (rule-based scores)
  → mvp_job_service._enrich_with_gemini(job_result)
    → llm_service.get_shot_feedback(metrics, scores, ...)
      → GeminiService.generate_structured(ShotFeedbackOutput)
      → On failure: fallback_shot_feedback() uses rule-based text
  → Enriched job_result stored and returned
```

### Drill Recommendation Flow
```
POST /api/recommend → recommend_service.recommend_drill()
  → FAISS + LinUCB selects drill
  → llm_service.get_drill_recommendation(drill_meta, weak_areas)
    → GeminiService.generate_structured(DrillRecommendationOutput)
    → On failure: result returned without explanation
  → Response includes structured explanation
```

### Progress Insight Flow
```
GET /api/user/progress-insight → routers/user.py
  → Fetch stats + recent summaries from Supabase
  → llm_service.get_progress_insight(stats, summaries)
    → GeminiService.generate_structured(ProgressInsightOutput)
    → On failure: fallback_progress_insight()
  → Response with trend analysis
```

## Model Configuration

| Setting | Value | Source |
|---------|-------|--------|
| Model | `gemini-2.5-flash` | `GEMINI_MODEL` env var |
| Temperature | 0.4 | Hardcoded default |
| Timeout | 60s | `GEMINI_TIMEOUT` env var |
| Max Retries | 3 | `GEMINI_MAX_RETRIES` env var |
| SDK | `google-genai` | `requirements.txt` |

## Key Design Decisions

1. **Rule-based scoring is the foundation.** Gemini adds NL explanations on top.
2. **Every Gemini call has a fallback.** The app never crashes if Gemini is down.
3. **Structured outputs via Pydantic.** Non-chat calls use JSON schema validation.
4. **Single service layer.** All consumers import from `services.llm`.
5. **No mobile changes needed.** The mobile app reads JSON responses.
