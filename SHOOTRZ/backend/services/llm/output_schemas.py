"""Pydantic v2 schemas for all Gemini structured-output responses.

Every non-chat Gemini call returns JSON validated against one of these models.
"""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Shot Feedback (Phase 3)
# ------------------------------------------------------------------

class MetricExplanation(BaseModel):
    metric_name: str = Field(description="e.g. elbow_extension, knee_bend")
    value: float
    verdict: str
    explanation: str = Field(description="1-2 sentence coach-style explanation")


class ShotFeedbackOutput(BaseModel):
    overall_explanation: str = Field(
        description="2-3 sentence coach summary of the shot"
    )
    metric_explanations: List[MetricExplanation] = Field(
        description="Per-metric natural-language explanations"
    )
    strengths: List[str] = Field(
        description="Top 2-3 things the player did well"
    )
    improvements: List[str] = Field(
        description="Top 2-3 areas to improve, with actionable cue"
    )
    feedback_bullets: List[str] = Field(
        description="3-5 concise coaching bullets"
    )
    drill_suggestions: List[str] = Field(
        default_factory=list,
        description="Optional drill names that address weak areas",
    )
    score_tier: str = Field(description="elite / great / good / fair / poor")
    # Holistic coach-style score. The rule-based geomean on the backend is
    # deliberately conservative (it collapses when any single axis is off).
    # Gemini looks at the whole motion and returns what an amateur coach
    # would actually grade this attempt, so a "decent looking jumpshot with
    # one weak axis" lands 60-80 instead of 3.
    ai_overall_score: int = Field(
        ge=0,
        le=100,
        description=(
            "Holistic 0-100 score. An attempted jumpshot with one weak axis "
            "but overall reasonable form should score 60-80. Textbook form "
            "scores 85-100. Motion that doesn't resemble a shot scores 0-20."
        ),
    )
    ai_score_rationale: str = Field(
        description="One sentence explaining the score (cited to angle values)."
    )

    # NOTE: ``ShotFeedbackOutput`` is sent verbatim to Gemini as the
    # ``response_schema``; Gemini rejects JSON schemas containing default
    # values, so "did this come from the fallback?" is signalled via the
    # ``get_shot_feedback`` return type, NOT a model field. See
    # ``backend/services/llm/llm_router.py``.


# ------------------------------------------------------------------
# Drill Recommendation (Phase 4)
# ------------------------------------------------------------------

class DrillRecommendationOutput(BaseModel):
    drill_name: str = Field(description="Name of the recommended drill")
    why: str = Field(
        description="1-2 sentences explaining why this drill was chosen"
    )
    how: str = Field(
        description="Brief instructions on how to perform the drill"
    )
    sets_reps: str = Field(
        description="Suggested sets and reps, e.g. '3 sets of 10 reps'"
    )


# ------------------------------------------------------------------
# Session Summary (Phase 5)
# ------------------------------------------------------------------

class SessionSummaryOutput(BaseModel):
    summary: str = Field(
        description="2-3 sentence session summary for the player"
    )
    key_takeaway: str = Field(
        description="Single most important takeaway from the session"
    )
    comparison_to_previous: Optional[str] = Field(
        default=None,
        description="How this session compares to recent sessions, if data available",
    )


# ------------------------------------------------------------------
# Progress Insight (Phase 5)
# ------------------------------------------------------------------

class ProgressInsightOutput(BaseModel):
    insight: str = Field(
        description="2-4 sentence trend analysis of recent performance"
    )
    highlights: List[str] = Field(
        description="Key stat changes worth calling out"
    )
    next_focus: str = Field(
        description="Recommended area to focus on next"
    )


# ------------------------------------------------------------------
# Feedback Rule Rephrasing (Phase 6)
# ------------------------------------------------------------------

class RephrasedFeedbackItem(BaseModel):
    metric_name: str
    message: str = Field(description="Rephrased coaching cue")
    details: str = Field(description="Rephrased detailed explanation")
    severity: str


class RephrasedFeedbackOutput(BaseModel):
    items: List[RephrasedFeedbackItem]
