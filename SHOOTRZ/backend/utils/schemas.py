from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class FeedbackItem(BaseModel):
    metric_id: Optional[str] = None
    message: str
    severity: Optional[str] = "info"


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


