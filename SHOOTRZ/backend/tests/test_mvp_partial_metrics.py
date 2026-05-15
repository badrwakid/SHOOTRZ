"""Regression: low-quality MVP responses must retain partial metric payloads."""

from pathlib import Path
import sys


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.services.mvp_job_service import MVPJobService
from backend.contracts.mvp import MVPResultResponse


def test_low_quality_payload_preserves_partial_metrics():
    """Low-quality status should still expose measured metrics for diagnostics/UI."""
    service = MVPJobService()
    partial_metrics = [
        {
            "name": "elbow_extension",
            "value": 146.2,
            "unit": "degrees",
            "verdict": "Low Confidence",
            "explanation": "Partial visibility at release frame",
            "confidence": 0.22,
            "selected_frame": None,
        },
    ]
    partial_components = [
        {
            "name": "Elbow Extension",
            "value": None,
            "unit": "deg",
            "weight": 0.4,
            "explanation": "Confidence too low to score reliably",
        },
    ]
    result = {
        "status": "completed_low_quality",
        "run_id": "run-low-quality-1",
        "metrics": partial_metrics,
        "score_components": partial_components,
        "feedback_summary": "Tracked body, but confidence too low for full scoring.",
        "feedback_bullets": ["Keep full shooting side visible for all frames."],
        "quality_warnings": ["insufficient_metric_confidence"],
        "shooting_side": "right",
    }

    payload = service._build_completed_payload("job-low-quality-1", result)

    assert payload["status"] == "completed_low_quality"
    assert payload["metrics"] == partial_metrics
    assert payload["score_components"] == partial_components


def test_low_quality_payload_adds_missing_confidence_metadata():
    """Missing confidence metadata should degrade gracefully without dropping metrics."""
    service = MVPJobService()
    result = {
        "status": "completed_low_quality",
        "run_id": "run-low-quality-2",
        "metrics": [
            {
                "name": "knee_bend",
                "value": 101.3,
                "unit": "degrees",
                "verdict": "Good",
                "explanation": "Computed from partial but stable crouch frames.",
            },
        ],
        "quality_warnings": ["insufficient_metric_confidence"],
    }

    payload = service._build_completed_payload("job-low-quality-2", result)
    metric = payload["metrics"][0]

    assert payload["status"] == "completed_low_quality"
    assert metric["name"] == "knee_bend"
    assert metric["value"] == 101.3
    assert metric["confidence"] == 0.0
    assert "confidence_reason" in metric


def test_low_quality_payload_confidence_reason_survives_result_serialization():
    """Confidence fallback metadata should pass MVPResultResponse validation."""
    service = MVPJobService()
    result = {
        "status": "completed_low_quality",
        "run_id": "run-low-quality-3",
        "metrics": [
            {
                "name": "knee_bend",
                "value": 98.0,
                "unit": "degrees",
                "verdict": "Low Confidence",
                "explanation": "Tracking dipped around crouch frame.",
                "confidence": 0.0,
                "confidence_reason": "Tracking unstable near crouch.",
                "frame_range": [42, 42],
                "selected_frame": 42,
            },
        ],
    }

    payload = service._build_completed_payload("job-low-quality-3", result)
    response = MVPResultResponse(**payload)
    metric = response.metrics[0]

    assert metric.confidence == 0.0
    assert metric.confidence_reason == "Tracking unstable near crouch."
