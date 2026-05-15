"""Authenticated endpoints to commit MVP job results to Supabase."""

from __future__ import annotations

import logging
from typing import Any, Dict

import asyncio

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..contracts.mvp import CompleteAnalysisResponse
from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user
from .mvp import service as mvp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class CompleteAnalysisRequest(BaseModel):
    job_id: str = Field(..., min_length=4, description="MVP job id from POST /mvp/analyze")


@router.post("/complete", response_model=CompleteAnalysisResponse)
async def complete_analysis(
    body: CompleteAnalysisRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    """Attach a completed MVP job to the authenticated user in Supabase."""
    retry_delays_s = [0.15, 0.25, 0.4, 0.6, 0.85, 1.1]
    result = None
    for i in range(len(retry_delays_s) + 1):
        logger.info(
            "commit_attempt",
            extra={
                "job_id": body.job_id,
                "user_id": user.user_id,
                "attempt": i + 1,
                "stage": "complete_analysis",
            },
        )
        try:
            result = mvp_service.save_result_for_user(body.job_id, user.user_id)
        except Exception as exc:
            logger.exception(
                "complete_analysis failed",
                extra={"job_id": body.job_id, "user_id": user.user_id},
            )
            raise HTTPException(status_code=500, detail="Failed to persist analysis") from exc
        if result is not None:
            break
        if i < len(retry_delays_s):
            logger.info(
                "commit_retry",
                extra={
                    "job_id": body.job_id,
                    "user_id": user.user_id,
                    "attempt": i + 1,
                    "delay_s": retry_delays_s[i],
                },
            )
            await asyncio.sleep(retry_delays_s[i])

    if result is None:
        logger.warning(
            "complete_analysis: job missing or not completed",
            extra={"job_id": body.job_id, "user_id": user.user_id},
        )
        raise HTTPException(
            status_code=400,
            detail="Job not found or analysis not finished yet. Poll GET /mvp/result/{job_id} first.",
        )
    session_id = result.get("session_id")
    video_id = result.get("video_id")
    already_persisted = bool(result.get("already_persisted"))
    summary_persisted = result.get("summary_persisted")
    history_visible = result.get("history_visible")
    if already_persisted:
        # Backward compatibility for legacy payloads returned from job store.
        if summary_persisted is None:
            summary_persisted = True
        if history_visible is None:
            history_visible = True
    if (
        not session_id
        or not video_id
        or summary_persisted is not True
        or history_visible is not True
    ):
        logger.error(
            "complete_analysis: persistence visibility contract failed",
            extra={
                "job_id": body.job_id,
                "user_id": user.user_id,
                "session_id": session_id,
                "video_id": video_id,
                "summary_persisted": summary_persisted,
                "history_visible": history_visible,
            },
        )
        raise HTTPException(status_code=500, detail="Failed to persist analysis")

    logger.info(
        "commit_success",
        extra={
            "job_id": body.job_id,
            "user_id": user.user_id,
            "session_id": session_id,
            "already_persisted": already_persisted,
            "stage": "complete_analysis",
        },
    )
    return {
        "success": True,
        "session_id": session_id,
        "video_id": video_id,
        "already_persisted": already_persisted,
        "summary_persisted": True,
        "history_visible": True,
        "message": None,
    }
