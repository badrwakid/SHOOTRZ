from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Populated on GET /api/user/analysis-history (MVP / analysis_summaries read path).
HISTORY_API_SOURCE: Literal["analysis_summaries_v1"] = "analysis_summaries_v1"


class HistoryMetric(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: Optional[str] = None
    metric_name: str
    value: float
    unit: Optional[str] = None
    confidence: Optional[float] = None
    phase: Optional[str] = None
    frame_idx: Optional[int] = None
    created_at: Optional[str] = None


class HistorySession(BaseModel):
    """One row in analysis history: stable keys for the mobile client."""

    model_config = ConfigDict(extra="ignore")

    session_id: str
    video_id: Optional[str] = None
    timestamp: str
    title: Optional[str] = None
    date: str
    shot_count: int = 0
    average_score: Optional[float] = None
    overall_score: Optional[float] = None
    score_tier: Optional[str] = None
    top_strengths: List[str] = Field(default_factory=list)
    top_improvements: List[str] = Field(default_factory=list)
    metrics: List[HistoryMetric] = Field(default_factory=list)
    angle: Optional[str] = None
    fps: Optional[int] = None
    device: Optional[str] = None


class HistoryResponse(BaseModel):
    user_id: str
    sessions: List[HistorySession]
    total: int
    limit: Optional[int] = None
    offset: Optional[int] = None
    source: Optional[Literal["analysis_summaries_v1"]] = None


class HistoryStatsResponse(BaseModel):
    total_sessions: int
    total_shots: int
    average_score: Optional[float] = None
    best_score: Optional[float] = None
    improvement_percentage: Optional[float] = None
    consistency_score: Optional[float] = None


def session_from_db_row(row: Dict[str, Any]) -> HistorySession:
    """Normalize a raw ``db.get_user_analysis_history`` row into the public contract."""
    raw_metrics = row.get("metrics")
    if not isinstance(raw_metrics, list):
        raw_metrics = []
    metrics: List[HistoryMetric] = []
    for m in raw_metrics:
        if not isinstance(m, dict):
            continue
        try:
            metrics.append(HistoryMetric.model_validate(m))
        except Exception:
            continue
    return HistorySession(
        session_id=str(row.get("session_id") or ""),
        video_id=row.get("video_id"),
        timestamp=str(row.get("timestamp") or ""),
        title=row.get("title"),
        date=str(row.get("date") or ""),
        shot_count=int(row.get("shot_count") or 0),
        average_score=row.get("average_score"),
        overall_score=row.get("overall_score"),
        score_tier=row.get("score_tier"),
        top_strengths=list(row.get("top_strengths") or [])
        if isinstance(row.get("top_strengths"), list)
        else [],
        top_improvements=list(row.get("top_improvements") or [])
        if isinstance(row.get("top_improvements"), list)
        else [],
        metrics=metrics,
        angle=row.get("angle"),
        fps=row.get("fps"),
        device=row.get("device"),
    )
