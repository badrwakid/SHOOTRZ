"""E2E-style consistency checks across analysis commit and authenticated history."""

from pathlib import Path
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app
from backend.utils.supabase_auth import AuthenticatedUser, get_authenticated_user


client = TestClient(app)


def test_analysis_commit_surfaces_in_history_in_order():
    user_id = "d4cae36b-a8c3-49b1-a7f6-e2a7a2e14d10"
    committed_session_id = "sess-e2e-latest"
    committed_video_id = "vid-e2e-latest"

    with patch("backend.routers.analysis.mvp_service") as mock_svc, patch("backend.routers.user.db") as mock_db:
        mock_svc.save_result_for_user.return_value = {
            "success": True,
            "session_id": committed_session_id,
            "video_id": committed_video_id,
            "summary_persisted": True,
            "history_visible": True,
            "already_persisted": False,
        }
        mock_db.get_user_analysis_history.return_value = [
            {
                "session_id": committed_session_id,
                "video_id": committed_video_id,
                "timestamp": "2026-04-25T18:00:00+00:00",
                "date": "2026-04-25",
                "shot_count": 1,
                "average_score": 86.0,
                "overall_score": 86.0,
                "score_tier": "great",
                "top_strengths": ["release"],
                "top_improvements": ["arc"],
                "metrics": [{"metric_name": "knee_flex", "value": 0.91}],
            },
            {
                "session_id": "sess-e2e-older",
                "video_id": "vid-e2e-older",
                "timestamp": "2026-04-24T18:00:00+00:00",
                "date": "2026-04-24",
                "shot_count": 1,
                "average_score": 74.0,
                "overall_score": 74.0,
                "score_tier": "good",
                "top_strengths": ["balance"],
                "top_improvements": ["follow-through"],
                "metrics": [{"metric_name": "elbow_extension", "value": 0.74}],
            },
        ]

        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(user_id=user_id)
        try:
            complete = client.post("/api/analysis/complete", json={"job_id": "job-e2e-persist"})
            assert complete.status_code == 200
            complete_body = complete.json()
            assert complete_body["session_id"] == committed_session_id
            assert complete_body["video_id"] == committed_video_id

            history = client.get("/api/user/analysis-history?limit=20&offset=0")
            assert history.status_code == 200
            history_body = history.json()
        finally:
            app.dependency_overrides.clear()

    assert history_body["source"] == "analysis_summaries_v1"
    assert history_body["sessions"][0]["session_id"] == committed_session_id
    assert history_body["sessions"][0]["video_id"] == committed_video_id
    assert history_body["sessions"][0]["metrics"][0]["metric_name"] == "knee_flex"
