from typing import List, Optional

from pydantic import BaseModel


class HistoryMetric(BaseModel):
    id: Optional[str] = None
    metric_name: str
    value: float
    unit: Optional[str] = None
    confidence: Optional[float] = None
    phase: Optional[str] = None
    frame_idx: Optional[int] = None
    created_at: Optional[str] = None


class HistorySession(BaseModel):
    session_id: str
    timestamp: str
    title: Optional[str] = None
    date: str
    shot_count: int
    average_score: Optional[float] = None
    metrics: List[HistoryMetric] = []
    angle: Optional[str] = None
    fps: Optional[int] = None
    device: Optional[str] = None


class HistoryResponse(BaseModel):
    user_id: str
    sessions: List[HistorySession]
    total: int
    limit: Optional[int] = None
    offset: Optional[int] = None


class HistoryStatsResponse(BaseModel):
    total_sessions: int
    total_shots: int
    average_score: Optional[float] = None
    best_score: Optional[float] = None
    improvement_percentage: Optional[float] = None
    consistency_score: Optional[float] = None
