from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    angle: Optional[str] = None
    fps: Optional[int] = None
    device: Optional[str] = None
    user_id: Optional[str] = None
    file_url: Optional[str] = None


class AnalyzeResponse(BaseModel):
    job_id: str
    status: str


class Metric(BaseModel):
    metric_name: str
    value: float
    confidence: float
    metric_id: Optional[str] = None


class FeedbackItem(BaseModel):
    metric_id: Optional[str] = None
    message: str
    severity: Optional[str] = "info"


class ResultResponse(BaseModel):
    job_id: str
    status: str
    metrics: List[Metric]
    feedback: List[FeedbackItem]
    overlays: Dict[str, Any]


class SessionSummary(BaseModel):
    session_id: str
    timestamp: str
    avg_score: Optional[float] = None


class HistoryResponse(BaseModel):
    user_id: str
    sessions: List[SessionSummary]


class FeedbackRequest(BaseModel):
    feedback: List[FeedbackItem]


class FeedbackResponse(BaseModel):
    feedback: List[FeedbackItem]


