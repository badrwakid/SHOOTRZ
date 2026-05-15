"""MVP history API shape (``/api/user/analysis-history``) must stay aligned with the mobile contract."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.contracts.history import (  # noqa: E402
    HISTORY_API_SOURCE,
    HistoryResponse,
    session_from_db_row,
)


def test_session_from_db_row_has_stable_required_fields():
    row = {
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "video_id": "v1",
        "timestamp": "2026-04-20T10:00:00+00:00",
        "date": "2026-04-20",
        "title": "Morning shots",
        "shot_count": 5,
        "average_score": 72.0,
        "overall_score": 72.0,
        "score_tier": "good",
        "top_strengths": ["release"],
        "top_improvements": ["arc"],
        "metrics": [
            {
                "metric_name": "elbow",
                "value": 0.9,
            },
        ],
    }
    s = session_from_db_row(row)
    d = s.model_dump(exclude_none=False)
    assert set(d.keys()) >= {"session_id", "timestamp", "overall_score", "metrics"}
    assert d["session_id"] == "550e8400-e29b-41d4-a716-446655440000"
    assert d["metrics"][0]["metric_name"] == "elbow"


def test_history_response_includes_source_and_matches_constant():
    r = HistoryResponse(
        user_id="u-1",
        sessions=[],
        total=0,
        limit=20,
        offset=0,
        source=HISTORY_API_SOURCE,
    )
    dumped = r.model_dump(exclude_none=False)
    assert dumped["source"] == "analysis_summaries_v1"
    assert dumped["user_id"] == "u-1"
    assert dumped["total"] == 0
