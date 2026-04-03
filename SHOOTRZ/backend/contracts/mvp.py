from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel


class MVPAnalyzeQueuedResponse(BaseModel):
    job_id: str
    status: Literal["queued"]


class MVPAlternativeEvent(BaseModel):
    frame_id: int
    score: float
    kind: str


class MVPEvent(BaseModel):
    frame: Optional[int] = None
    timestamp: Optional[float] = None
    status: Optional[str] = None
    confidence: Optional[float] = None
    reason_codes: List[str] = []
    alternatives: List[MVPAlternativeEvent] = []


class MVPMetric(BaseModel):
    name: str
    value: float
    unit: str
    verdict: str
    explanation: str
    confidence: float
    frame_range: Optional[List[int]] = None


class MVPScoreComponent(BaseModel):
    name: str
    value: float
    unit: str
    weight: float
    explanation: str


class MVPShotWindow(BaseModel):
    start_frame: Optional[int] = None
    crouch_frame: Optional[int] = None
    release_frame: Optional[int] = None
    end_frame: Optional[int] = None
    confidence: Optional[str] = None
    confidence_score: Optional[float] = None
    method: Optional[str] = None


class MVPArtifacts(BaseModel):
    overlay_video: Optional[str] = None
    angles_csv: Optional[str] = None
    report_json: Optional[str] = None
    event_candidates: Optional[str] = None
    event_confidence: Optional[str] = None
    feature_table: Optional[str] = None
    signals_smoothed: Optional[str] = None
    warnings: Optional[str] = None


class MVPCompletedResult(BaseModel):
    status: Literal["completed"]
    contract_version: str
    run_id: str
    metrics: List[MVPMetric]
    overall_score: int
    feedback_summary: str
    feedback_bullets: List[str] = []
    score_components: List[MVPScoreComponent] = []
    shot_window: MVPShotWindow
    events: Dict[str, MVPEvent] = {}
    shooting_side: str
    angles_data: Dict[str, Any]
    artifacts: MVPArtifacts
    key_frame_images: Dict[str, str] = {}
    quality_warnings: List[str] = []
    diagnostics: Dict[str, Any] = {}


class MVPFailedResult(BaseModel):
    status: Literal["failed"]
    error: str
    error_detail: Optional[str] = None
    error_type: Optional[str] = None


class MVPQueuedResult(BaseModel):
    status: Literal["queued", "processing"]


class MVPResultResponse(BaseModel):
    status: str
    contract_version: Optional[str] = None
    run_id: Optional[str] = None
    metrics: Optional[List[MVPMetric]] = None
    overall_score: Optional[int] = None
    feedback_summary: Optional[str] = None
    feedback_bullets: Optional[List[str]] = None
    score_components: Optional[List[MVPScoreComponent]] = None
    shot_window: Optional[MVPShotWindow] = None
    events: Optional[Dict[str, MVPEvent]] = None
    shooting_side: Optional[str] = None
    angles_data: Optional[Dict[str, Any]] = None
    artifacts: Optional[MVPArtifacts] = None
    key_frame_images: Optional[Dict[str, str]] = None
    quality_warnings: Optional[List[str]] = None
    diagnostics: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    error_detail: Optional[str] = None
    error_type: Optional[str] = None
