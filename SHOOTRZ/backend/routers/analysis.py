"""Authenticated endpoints to commit MVP job results to Supabase."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from ..utils.supabase_auth import AuthenticatedUser, get_authenticated_user
from .mvp import service as mvp_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class CompleteAnalysisRequest(BaseModel):
    job_id: str = Field(..., min_length=4, description="MVP job id from POST /mvp/analyze")


class CompleteAnalysisResponse(BaseModel):
    success: bool
    session_id: Optional[str] = None
    video_id: Optional[str] = None
    already_persisted: bool = False
    message: Optional[str] = None


@router.post("/complete", response_model=CompleteAnalysisResponse)
async def complete_analysis(
    body: CompleteAnalysisRequest,
    user: AuthenticatedUser = Depends(get_authenticated_user),
) -> Dict[str, Any]:
    """Attach a completed MVP job to the authenticated user in Supabase."""
    try:
        result = mvp_service.save_result_for_user(body.job_id, user.user_id)
    except Exception as exc:
        logger.exception(
            "complete_analysis failed",
            extra={"job_id": body.job_id, "user_id": user.user_id},
        )
        raise HTTPException(status_code=500, detail="Failed to persist analysis") from exc

    if result is None:
        logger.warning(
            "complete_analysis: job missing or not completed",
            extra={"job_id": body.job_id, "user_id": user.user_id},
        )
        raise HTTPException(
            status_code=400,
            detail="Job not found or analysis not finished yet. Poll GET /mvp/result/{job_id} first.",
        )

    logger.info(
        "complete_analysis ok",
        extra={
            "job_id": body.job_id,
            "user_id": user.user_id,
            "session_id": result.get("session_id"),
            "already_persisted": result.get("already_persisted"),
        },
    )
    return {
        "success": True,
        "session_id": result.get("session_id"),
        "video_id": result.get("video_id"),
        "already_persisted": bool(result.get("already_persisted")),
        "message": None,
    }
