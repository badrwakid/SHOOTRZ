# Gemini Prompt System

All prompt templates used by the SHOOTRZ Gemini integration. Each prompt is defined in
`backend/services/llm/prompt_builders.py`.

---

## Shared Coach Persona

All prompts share a common persona prefix:

```
You are Coach J, an elite basketball shooting coach inside the SHOOTRZ app.
You draw on sports-science research and NBA coaching methods.
Be concise, encouraging, and actionable. Use bullet points when listing.
Never invent numbers that aren't in the data provided.
Speak in second person ('you') directly to the player.
```

---

## 1. Chat Prompt — `build_chat_prompt()`

**Purpose**: System prompt for the Coach J chatbot.

**Inputs**:
- `user_context`: Dict with profile, stats, recent sessions, goals

**System Prompt**:
```
{COACH_PERSONA}
You MUST personalize advice using the player data below.
Rules:
- Be concise and actionable. Prefer bullet points.
- If the user asks about progress, reference trends from history.
- If data is missing, ask 1 clarifying question.
- When suggesting drills, give sets/reps and a 7-day plan.

PLAYER_DATA_JSON:
{context_json}
```

**Output**: Free text (not structured)

**Safety Notes**: Context is sanitized by `sanitize_context_for_llm()` to cap token usage.

---

## 2. Shot Feedback Prompt — `build_shot_feedback_prompt()`

**Purpose**: Generate rich, coach-style analysis of a single shot.

**Inputs**:
- `metrics`: List of metric dicts (name, value, verdict, explanation)
- `score_components`: List of component scores
- `overall_score`: 0-100 integer
- `score_tier`: elite/great/good/fair/poor
- `user_profile`: Optional player profile dict

**Output Schema**: `ShotFeedbackOutput`
- `overall_explanation`: 2-3 sentence summary
- `metric_explanations`: Per-metric explanations
- `strengths`: Top 2-3 positives
- `improvements`: Top 2-3 areas to work on
- `feedback_bullets`: 3-5 concise bullets
- `drill_suggestions`: Optional drill names
- `score_tier`: Tier classification

**Safety Notes**: Prompt explicitly states "The data below is factual — do NOT contradict it."

---

## 3. Drill Recommendation Prompt — `build_drill_recommendation_prompt()`

**Purpose**: Explain why a drill was recommended and how to perform it.

**Inputs**:
- `drill_metadata`: Dict with drill info
- `weak_areas`: List of area strings
- `user_level`: Optional skill level string

**Output Schema**: `DrillRecommendationOutput`
- `drill_name`, `why`, `how`, `sets_reps`

---

## 4. Session Summary Prompt — `build_session_summary_prompt()`

**Purpose**: Generate a concise post-session summary.

**Inputs**:
- `session_data`: Dict with score, strengths, improvements, metrics
- `history_summary`: Optional list of previous sessions

**Output Schema**: `SessionSummaryOutput`
- `summary`, `key_takeaway`, `comparison_to_previous`

---

## 5. Progress Insight Prompt — `build_progress_insight_prompt()`

**Purpose**: Analyze performance trends over multiple sessions.

**Inputs**:
- `stats`: Dict with aggregate stats
- `recent_summaries`: List of recent session dicts

**Output Schema**: `ProgressInsightOutput`
- `insight`, `highlights`, `next_focus`

---

## 6. Metric Explanation Prompt — `build_metric_explanation_prompt()`

**Purpose**: Explain a single metric to a player.

**Inputs**:
- `metric_name`, `value`, `verdict`, `good_range`, `optimal_range`

**Output**: Free text (can be used with structured output if needed)

---

## 7. Feedback Rephrase Prompt — `build_feedback_rephrase_prompt()`

**Purpose**: Rephrase rule-based feedback into conversational coaching language.

**Inputs**:
- `feedback_items`: List of dicts with message, severity, details

**Output Schema**: `RephrasedFeedbackOutput`
- `items`: List of `RephrasedFeedbackItem` (metric_name, message, details, severity)

**Safety Notes**: "Do NOT change or contradict any numbers or recommendations."

---

## Design Principles

1. **Grounded in data**: Every prompt includes factual data and instructs the model not to hallucinate.
2. **Coach persona**: Warm, encouraging, actionable — like a real basketball coach.
3. **Concise**: Prompts request brevity. Mobile users don't want paragraphs.
4. **Basketball-specific**: Language and recommendations are specific to shooting mechanics.
5. **Fallback-safe**: If the LLM fails, rule-based text fills every field.
