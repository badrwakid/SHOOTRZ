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
    # Exact frame the metric was measured at (peak extension for elbow,
    # deepest knee flex for knee_bend, etc). ``None`` when the metric is
    # Low Confidence.
    selected_frame: Optional[int] = None


class MVPScoreComponent(BaseModel):
    name: str
    # ``None`` when the underlying primitive is Low Confidence. Previously the
    # backend substituted a plausible default which shipped misleading
    # "Strength: leg load looks solid (71/100)" copy next to an Elbow N/A card.
    value: Optional[float] = None
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
    # Mean landmark visibility across kept frames (0..1). Drives the UI
    # tracking-quality chip. Added 2026-04-23 with the angle/overlay fix.
    pose_overall_confidence: Optional[float] = None
    # Deterministic rule-based score from the geomean path. Preserved even
    # after the Gemini override so UI / debugging tooling can compare.
    rule_based_score: Optional[int] = None
    # Whether ``overall_score`` was produced by the AI coach (Gemini).
    # ``False`` means rule-based only (fallback or Gemini disabled).
    ai_scored: Optional[bool] = None
    # One-line justification emitted by Gemini alongside its score.
    ai_score_rationale: Optional[str] = None
    error: Optional[str] = None
    error_detail: Optional[str] = None
    error_type: Optional[str] = None
