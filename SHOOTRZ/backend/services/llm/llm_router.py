"""Unified LLM service — single entrypoint for all AI-generated content.

Usage::

    from backend.services.llm import llm_service

    # Chat (free text)
    resp = llm_service.chat(system_prompt=..., messages=...)

    # Structured output
    feedback = llm_service.get_shot_feedback(metrics=..., ...)
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List, Optional, Tuple

from .gemini_client import GeminiService, LlmResponse, gemini_service
from .output_schemas import (
    DrillRecommendationOutput,
    ProgressInsightOutput,
    RephrasedFeedbackOutput,
    SessionSummaryOutput,
    ShotFeedbackOutput,
)
from . import prompt_builders, fallbacks

logger = logging.getLogger(__name__)


class LLMService:
    """High-level AI service wrapping Gemini + prompt builders + validation + fallbacks."""

    def __init__(self, gemini: GeminiService) -> None:
        self._gemini = gemini

    # ------------------------------------------------------------------
    # Chat (free-text)
    # ------------------------------------------------------------------

    def chat(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> LlmResponse:
        try:
            return self._gemini.generate(
                system_prompt=system_prompt,
                messages=messages,
                model=model,
            )
        except Exception:
            logger.exception("Gemini chat failed, returning fallback")
            return LlmResponse(
                text=fallbacks.CHAT_FALLBACK_TEXT,
                model=model or "fallback",
                usage=None,
            )

    def chat_stream(
        self,
        *,
        system_prompt: str,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
    ) -> Generator[Tuple[str, Any], None, None]:
        try:
            yield from self._gemini.stream(
                system_prompt=system_prompt,
                messages=messages,
                model=model,
            )
        except Exception:
            logger.exception("Gemini stream failed, yielding fallback")
            yield ("delta", {"text": fallbacks.CHAT_FALLBACK_TEXT})
            yield ("done", {"model": model or "fallback", "usage": None})

    # ------------------------------------------------------------------
    # Shot Feedback (structured)
    # ------------------------------------------------------------------

    def get_shot_feedback(
        self,
        *,
        metrics: List[Dict[str, Any]],
        score_components: List[Dict[str, Any]],
        overall_score: int,
        score_tier: str,
        feedback_summary: str,
        feedback_bullets: List[str],
        user_profile: Optional[Dict[str, Any]] = None,
    ) -> ShotFeedbackOutput:
        try:
            system, user = prompt_builders.build_shot_feedback_prompt(
                metrics=metrics,
                score_components=score_components,
                overall_score=overall_score,
                score_tier=score_tier,
                user_profile=user_profile,
            )
            return self._gemini.generate_structured(
                system_prompt=system,
                user_prompt=user,
                schema=ShotFeedbackOutput,
            )
        except Exception:
            logger.exception("Gemini shot feedback failed, using fallback")
            return fallbacks.fallback_shot_feedback(
                metrics=metrics,
                score_components=score_components,
                overall_score=overall_score,
                feedback_summary=feedback_summary,
                feedback_bullets=feedback_bullets,
            )

    # ------------------------------------------------------------------
    # Drill Recommendation (structured)
    # ------------------------------------------------------------------

    def get_drill_recommendation(
        self,
        *,
        drill_metadata: Dict[str, Any],
        weak_areas: List[str],
        user_level: Optional[str] = None,
    ) -> DrillRecommendationOutput:
        try:
            system, user = prompt_builders.build_drill_recommendation_prompt(
                drill_metadata=drill_metadata,
                weak_areas=weak_areas,
                user_level=user_level,
            )
            return self._gemini.generate_structured(
                system_prompt=system,
                user_prompt=user,
                schema=DrillRecommendationOutput,
            )
        except Exception:
            logger.exception("Gemini drill recommendation failed, using fallback")
            return fallbacks.fallback_drill_recommendation(drill_metadata)

    # ------------------------------------------------------------------
    # Session Summary (structured)
    # ------------------------------------------------------------------

    def get_session_summary(
        self,
        *,
        session_data: Dict[str, Any],
        history_summary: Optional[List[Dict[str, Any]]] = None,
    ) -> SessionSummaryOutput:
        try:
            system, user = prompt_builders.build_session_summary_prompt(
                session_data=session_data,
                history_summary=history_summary,
            )
            return self._gemini.generate_structured(
                system_prompt=system,
                user_prompt=user,
                schema=SessionSummaryOutput,
            )
        except Exception:
            logger.exception("Gemini session summary failed, using fallback")
            return fallbacks.fallback_session_summary(session_data)

    # ------------------------------------------------------------------
    # Progress Insight (structured)
    # ------------------------------------------------------------------

    def get_progress_insight(
        self,
        *,
        stats: Dict[str, Any],
        recent_summaries: List[Dict[str, Any]],
    ) -> ProgressInsightOutput:
        try:
            system, user = prompt_builders.build_progress_insight_prompt(
                stats=stats,
                recent_summaries=recent_summaries,
            )
            return self._gemini.generate_structured(
                system_prompt=system,
                user_prompt=user,
                schema=ProgressInsightOutput,
            )
        except Exception:
            logger.exception("Gemini progress insight failed, using fallback")
            return fallbacks.fallback_progress_insight(stats, recent_summaries)

    # ------------------------------------------------------------------
    # Feedback Rephrase (structured)
    # ------------------------------------------------------------------

    def rephrase_feedback(
        self,
        *,
        feedback_items: List[Dict[str, Any]],
    ) -> RephrasedFeedbackOutput:
        if not feedback_items:
            return RephrasedFeedbackOutput(items=[])
        try:
            system, user = prompt_builders.build_feedback_rephrase_prompt(feedback_items)
            return self._gemini.generate_structured(
                system_prompt=system,
                user_prompt=user,
                schema=RephrasedFeedbackOutput,
            )
        except Exception:
            logger.exception("Gemini feedback rephrase failed, using fallback")
            return fallbacks.fallback_feedback_rephrase(feedback_items)


llm_service = LLMService(gemini_service)
