# Gemini Use Cases — Structured Inventory

All AI output use cases in SHOOTRZ, organized by feature area.

---

## A. Chatbot (Coach J)

- **Type**: Free-text conversational AI
- **Input**: User messages + player context (profile, stats, recent sessions)
- **Output**: Natural language coaching responses
- **Structured Output**: No (free text)
- **Endpoint**: `POST /chat`, `POST /chat/stream`
- **Service Method**: `llm_service.chat()`, `llm_service.chat_stream()`
- **Fallback**: Canned message: "I'm having trouble connecting right now..."

## B. Shot Feedback

- **Type**: Structured analysis of a single shot
- **Input**: Metrics (elbow/knee/wrist), score components, overall score
- **Output**: Coach-style explanations, strengths, improvements, drill suggestions
- **Structured Output**: Yes — `ShotFeedbackOutput` Pydantic schema
- **Integration Point**: `mvp_job_service._enrich_with_gemini()`
- **Service Method**: `llm_service.get_shot_feedback()`
- **Fallback**: Existing rule-based explanations from `metrics.py`

## C. Drill Recommendations

- **Type**: Natural-language explanation of why a drill was recommended
- **Input**: Drill metadata, user weak areas, skill level
- **Output**: Why the drill helps, how to do it, sets/reps
- **Structured Output**: Yes — `DrillRecommendationOutput` Pydantic schema
- **Integration Point**: `recommend_service.recommend_drill()`
- **Service Method**: `llm_service.get_drill_recommendation()`
- **Fallback**: Generic explanation text

## D. Session Summaries

- **Type**: Brief summary of a training session
- **Input**: Session scores, strengths, improvements, metrics
- **Output**: 2-3 sentence summary, key takeaway, comparison to previous
- **Structured Output**: Yes — `SessionSummaryOutput` Pydantic schema
- **Integration Point**: `mvp_job_service._save_to_supabase()`
- **Service Method**: `llm_service.get_session_summary()`
- **Fallback**: Template-based summary

## E. Progress Insights

- **Type**: Trend analysis of recent performance
- **Input**: User stats, recent session summaries
- **Output**: Trend commentary, highlights, next focus area
- **Structured Output**: Yes — `ProgressInsightOutput` Pydantic schema
- **Endpoint**: `GET /api/user/progress-insight`
- **Service Method**: `llm_service.get_progress_insight()`
- **Fallback**: Simple stat comparison text

## F. Feedback Rules Rephrasing

- **Type**: Natural-language rephrasing of rule-based coaching cues
- **Input**: Rule-based feedback items (message, severity, details)
- **Output**: Same structure with warmer, more conversational tone
- **Structured Output**: Yes — `RephrasedFeedbackOutput` Pydantic schema
- **Integration Point**: `feedback/rules.py` with `enrich=True`
- **Service Method**: `llm_service.rephrase_feedback()`
- **Fallback**: Original rule-based text returned as-is

## G. Metric Explanations (Individual)

- **Type**: Explanation of a single metric value
- **Input**: Metric name, value, verdict, normative ranges
- **Output**: 1-2 sentence explanation
- **Structured Output**: Via prompt builders (can be used standalone)
- **Service Method**: Via `prompt_builders.build_metric_explanation_prompt()`
- **Status**: Prompt template ready; not yet wired to a dedicated endpoint

---

## Summary Matrix

| Use Case | Endpoint | Structured Output | Fallback | Status |
|----------|----------|------------------|----------|--------|
| A. Chat | `/chat`, `/chat/stream` | No | Canned text | Active |
| B. Shot Feedback | Internal (MVP pipeline) | Yes | Rule-based | Active |
| C. Drill Recs | `/api/recommend` | Yes | Generic text | Active |
| D. Session Summary | Internal (save to DB) | Yes | Template | Active |
| E. Progress Insight | `/api/user/progress-insight` | Yes | Stat text | Active |
| F. Feedback Rephrase | `/feedback/generate?enrich=true` | Yes | Rule text | Active |
| G. Metric Explanation | Template ready | Yes | — | Ready |
