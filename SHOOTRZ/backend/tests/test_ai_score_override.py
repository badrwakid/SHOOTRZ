"""Regression: Gemini ``ai_overall_score`` must override the rule-based score.

Covers the 2026-04-23 scoring-harshness fix where the backend's geomean
``overall_score`` can still collapse to near-zero on a shot with a single
weak axis. Gemini is supposed to grade holistically and push the overall
score back up to coach-grade levels (60-80 for an attempted jumpshot).

Both the happy path and the Gemini-failure fallback are covered.
"""
from __future__ import annotations

from typing import Any, Dict, List
from unittest.mock import patch

from backend.services.llm.output_schemas import (
    MetricExplanation,
    ShotFeedbackOutput,
)
from backend.services.mvp_job_service import MVPJobService


def _job_result(overall_score: int = 30) -> Dict[str, Any]:
    return {
        "status": "completed",
        "overall_score": overall_score,
        "feedback_summary": "Rule-based summary",
        "feedback_bullets": ["Prioritize elbow extension - sub-score 10/100."],
        "metrics": [
            {
                "name": "elbow_extension",
                "value": 152.4,
                "unit": "degrees",
                "verdict": "Needs Work",
                "explanation": "Elbow at 152.4 deg is quite bent.",
                "confidence": 0.98,
                "frame_range": [339, 339],
                "selected_frame": 339,
            },
            {
                "name": "knee_bend",
                "value": 31.9,
                "unit": "degrees",
                "verdict": "Needs Work",
                "explanation": "Knee very deep.",
                "confidence": 0.99,
                "frame_range": [228, 228],
                "selected_frame": 228,
            },
            {
                "name": "wrist_follow_through",
                "value": 32.8,
                "unit": "degrees",
                "verdict": "Good",
                "explanation": "Follow-through solid.",
                "confidence": 0.98,
                "frame_range": [330, 345],
                "selected_frame": 345,
            },
        ],
        "score_components": [],
    }


def _fake_ai_feedback(overall: int = 78) -> ShotFeedbackOutput:
    return ShotFeedbackOutput(
        overall_explanation="Solid attempt at a jumpshot with a slightly shallow crouch.",
        metric_explanations=[
            MetricExplanation(
                metric_name="elbow_extension",
                value=152.4,
                verdict="Close to optimal",
                explanation="Elbow at 152 deg - a little more extension and you'll be textbook.",
            )
        ],
        strengths=["Follow-through snap is solid"],
        improvements=["Bend your knees more on the load"],
        feedback_bullets=[
            "Aim for a knee bend near 105 deg on the load.",
            "Extend the elbow a touch further at release.",
        ],
        drill_suggestions=["Wall squats before shooting reps"],
        score_tier="good",
        ai_overall_score=overall,
        ai_score_rationale="Coach-style 78/100 for a recognisable jumpshot with a shallow knee bend.",
    )


def test_ai_score_overrides_rule_based_when_valid():
    service = MVPJobService()
    job_result = _job_result(overall_score=30)

    with patch(
        "backend.services.mvp_job_service.llm_service.get_shot_feedback",
        return_value=(_fake_ai_feedback(overall=78), False),
    ):
        service._enrich_with_gemini(job_result)

    assert job_result["overall_score"] == 78
    assert job_result["rule_based_score"] == 30
    assert job_result["ai_scored"] is True
    assert "78" in job_result.get("ai_score_rationale", "")
    # Feedback copy must have been rewritten, not a template string.
    assert "shallow crouch" in job_result["feedback_summary"].lower()
    # Metric explanation must have been updated from the Gemini response.
    elbow = next(m for m in job_result["metrics"] if m["name"] == "elbow_extension")
    assert "textbook" in elbow["explanation"].lower()


def test_rule_based_score_preserved_when_ai_out_of_range():
    service = MVPJobService()
    job_result = _job_result(overall_score=30)

    weird = _fake_ai_feedback(overall=78)
    # Bypass Pydantic validation by assigning directly via __dict__ so we can
    # feed ``_enrich_with_gemini`` an out-of-range sentinel.
    object.__setattr__(weird, "ai_overall_score", 250)
    with patch(
        "backend.services.mvp_job_service.llm_service.get_shot_feedback",
        return_value=(weird, False),
    ):
        service._enrich_with_gemini(job_result)

    # Rule-based score must NOT be overwritten when AI returns an invalid int.
    assert job_result["overall_score"] == 30
    assert job_result["ai_scored"] is False


def test_fallback_feedback_does_not_claim_ai_scored():
    """``get_shot_feedback`` returns (output, is_fallback=True) when Gemini
    is unavailable. The service must see that and NOT flip ``ai_scored`` to
    True, so the UI labels the result honestly."""
    service = MVPJobService()
    job_result = _job_result(overall_score=55)

    with patch(
        "backend.services.mvp_job_service.llm_service.get_shot_feedback",
        return_value=(_fake_ai_feedback(overall=55), True),
    ):
        service._enrich_with_gemini(job_result)

    # Score stays the rule-based number.
    assert job_result["overall_score"] == 55
    assert job_result["rule_based_score"] == 55
    # ``ai_scored`` must be False because the output came from the fallback.
    assert job_result["ai_scored"] is False
    assert "unavailable" in (job_result.get("ai_score_rationale") or "").lower()


def test_gemini_failure_keeps_rule_based_score():
    service = MVPJobService()
    job_result = _job_result(overall_score=42)

    def _boom(**_kw) -> Any:
        raise RuntimeError("Gemini outage")

    with patch(
        "backend.services.mvp_job_service.llm_service.get_shot_feedback",
        side_effect=_boom,
    ):
        service._enrich_with_gemini(job_result)

    assert job_result["overall_score"] == 42
    assert job_result["rule_based_score"] == 42
    assert job_result.get("gemini_enriched") is False
