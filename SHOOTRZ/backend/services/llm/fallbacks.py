"""Deterministic fallback generators for when Gemini is unreachable.

Every fallback returns the same Pydantic model as the corresponding
structured-output call, so the caller never needs branching logic.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .output_schemas import (
    DrillRecommendationOutput,
    MetricExplanation,
    ProgressInsightOutput,
    RephrasedFeedbackItem,
    RephrasedFeedbackOutput,
    SessionSummaryOutput,
    ShotFeedbackOutput,
)

logger = logging.getLogger(__name__)


def _score_tier(score: int) -> str:
    if score >= 90:
        return "elite"
    if score >= 75:
        return "great"
    if score >= 60:
        return "good"
    if score >= 40:
        return "fair"
    return "poor"


# ------------------------------------------------------------------
# Shot Feedback fallback
# ------------------------------------------------------------------

def fallback_shot_feedback(
    metrics: List[Dict[str, Any]],
    score_components: List[Dict[str, Any]],
    overall_score: int,
    feedback_summary: str,
    feedback_bullets: List[str],
) -> ShotFeedbackOutput:
    """Use the existing rule-based explanations as a fallback."""
    logger.warning("Using fallback shot feedback (Gemini unavailable)")

    metric_explanations = [
        MetricExplanation(
            metric_name=m.get("name", "unknown"),
            value=float(m.get("value", 0)),
            verdict=m.get("verdict", "Unknown"),
            explanation=m.get("explanation", "No data available."),
        )
        for m in metrics
    ]

    strengths = [b for b in feedback_bullets if "strength" in b.lower() or "solid" in b.lower()]
    improvements = [b for b in feedback_bullets if "prioritize" in b.lower() or "focus" in b.lower()]
    if not strengths:
        strengths = ["Keep filming with good lighting for better tracking."]
    if not improvements:
        improvements = feedback_bullets[:2] if feedback_bullets else ["Record another shot to track progress."]

    return ShotFeedbackOutput(
        overall_explanation=feedback_summary or f"Your shot scored {overall_score}/100.",
        metric_explanations=metric_explanations,
        strengths=strengths[:3],
        improvements=improvements[:3],
        feedback_bullets=feedback_bullets[:5],
        drill_suggestions=[],
        score_tier=_score_tier(overall_score),
        # Echo the rule-based score so the schema stays populated; the
        # caller (``llm_service.get_shot_feedback``) returns a tuple whose
        # second element tells consumers this is a fallback, not a real AI
        # grade.
        ai_overall_score=int(overall_score),
        ai_score_rationale=(
            feedback_summary
            or f"Rule-based score {overall_score}/100 (AI coach unavailable)."
        ),
    )


# ------------------------------------------------------------------
# Drill Recommendation fallback
# ------------------------------------------------------------------

def fallback_drill_recommendation(
    drill_metadata: Dict[str, Any],
) -> DrillRecommendationOutput:
    logger.warning("Using fallback drill recommendation (Gemini unavailable)")
    name = drill_metadata.get("drill_name") or drill_metadata.get("drill_id", "Selected drill")
    return DrillRecommendationOutput(
        drill_name=str(name),
        why="This drill was selected based on your shooting profile and recent performance.",
        how="Follow the standard drill instructions for best results.",
        sets_reps="3 sets of 10 reps",
    )


# ------------------------------------------------------------------
# Session Summary fallback
# ------------------------------------------------------------------

def fallback_session_summary(
    session_data: Dict[str, Any],
) -> SessionSummaryOutput:
    logger.warning("Using fallback session summary (Gemini unavailable)")
    score = session_data.get("overall_score", 0)
    tier = session_data.get("score_tier") or _score_tier(score)
    return SessionSummaryOutput(
        summary=f"You completed a session with an overall score of {score}/100 ({tier}).",
        key_takeaway="Keep recording consistently to track your improvement over time.",
        comparison_to_previous=None,
    )


# ------------------------------------------------------------------
# Progress Insight fallback
# ------------------------------------------------------------------

def fallback_progress_insight(
    stats: Dict[str, Any],
    recent_summaries: List[Dict[str, Any]],
) -> ProgressInsightOutput:
    logger.warning("Using fallback progress insight (Gemini unavailable)")
    total = stats.get("total_sessions", len(recent_summaries))
    avg = stats.get("average_score")
    avg_str = f"{avg:.0f}" if avg is not None else "N/A"
    return ProgressInsightOutput(
        insight=f"You've completed {total} sessions with an average score of {avg_str}/100.",
        highlights=["Keep recording to build more data for trend analysis."],
        next_focus="Focus on your lowest-scoring component from the last session.",
    )


# ------------------------------------------------------------------
# Chat fallback
# ------------------------------------------------------------------

CHAT_FALLBACK_TEXT = (
    "I'm having trouble connecting right now — try again in a moment. "
    "In the meantime, keep working on the drills from your last session!"
)


# ------------------------------------------------------------------
# Feedback Rephrase fallback
# ------------------------------------------------------------------

def fallback_feedback_rephrase(
    feedback_items: List[Dict[str, Any]],
) -> RephrasedFeedbackOutput:
    """Return the original rule-based text as-is."""
    logger.warning("Using fallback feedback rephrase (Gemini unavailable)")
    return RephrasedFeedbackOutput(
        items=[
            RephrasedFeedbackItem(
                metric_name=item.get("metric_name", "unknown"),
                message=item.get("message", ""),
                details=item.get("details", ""),
                severity=item.get("severity", "info"),
            )
            for item in feedback_items
        ]
    )
