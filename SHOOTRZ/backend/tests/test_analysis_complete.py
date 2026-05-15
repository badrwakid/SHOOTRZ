"""Tests for authenticated MVP analysis persistence (POST /api/analysis/complete)."""

from pathlib import Path
import sys
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app
from backend.utils.supabase_auth import AuthenticatedUser, get_authenticated_user


client = TestClient(app)


def test_complete_analysis_calls_save_result_for_user():
    uid = "11111111-1111-1111-1111-111111111111"
    with patch("backend.routers.analysis.mvp_service") as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            "success": True,
            "session_id": "sess-1",
            "video_id": "vid-1",
            "summary_persisted": True,
            "history_visible": True,
            "already_persisted": False,
        }
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id=uid,
        )
        try:
            r = client.post("/api/analysis/complete", json={"job_id": "job-xyz"})
            assert r.status_code == 200
            body = r.json()
            assert body["success"] is True
            assert body["session_id"] == "sess-1"
            assert body["video_id"] == "vid-1"
            mock_svc.save_result_for_user.assert_called_once_with("job-xyz", uid)
        finally:
            app.dependency_overrides.clear()


def test_complete_analysis_400_when_job_not_ready():
    with patch("backend.routers.analysis.mvp_service") as mock_svc:
        mock_svc.save_result_for_user.return_value = None
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id="22222222-2222-2222-2222-222222222222",
        )
        try:
            r = client.post("/api/analysis/complete", json={"job_id": "missing-job"})
            assert r.status_code == 400
        finally:
            app.dependency_overrides.clear()


def test_complete_analysis_500_when_visibility_flags_missing():
    with patch("backend.routers.analysis.mvp_service") as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            "success": True,
            "session_id": "sess-2",
            "video_id": "vid-2",
            "already_persisted": False,
        }
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id="33333333-3333-3333-3333-333333333333",
        )
        try:
            r = client.post("/api/analysis/complete", json={"job_id": "job-missing-flags"})
            assert r.status_code == 500
            assert r.json() == {"detail": "Failed to persist analysis"}
        finally:
            app.dependency_overrides.clear()


def test_complete_analysis_accepts_legacy_already_persisted_payload():
    with patch("backend.routers.analysis.mvp_service") as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            "success": True,
            "session_id": "sess-legacy",
            "video_id": "vid-legacy",
            "already_persisted": True,
        }
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id="44444444-4444-4444-4444-444444444444",
        )
        try:
            r = client.post("/api/analysis/complete", json={"job_id": "job-legacy"})
            assert r.status_code == 200
            body = r.json()
            assert body["success"] is True
            assert body["already_persisted"] is True
            assert body["session_id"] == "sess-legacy"
            assert body["video_id"] == "vid-legacy"
        finally:
            app.dependency_overrides.clear()


def test_reused_partial_restores_missing_link_and_metrics():
    from backend.services.mvp_job_service import MVPJobService

    user_id = "55555555-5555-5555-5555-555555555555"
    session_id = "sess-partial-1"
    video_id = "vid-partial-1"
    payload = {
        "status": "completed",
        "run_id": "run-1",
        "overall_score": 88,
        "metrics": [
            {
                "name": "elbow_extension",
                "value": 77,
                "confidence": 0.81,
                "unit": "deg",
            },
        ],
        "supabase_summary": {"overall_score": 88, "score_tier": "great"},
        "supabase_persisting": {
            "user_id": user_id,
            "session_id": session_id,
            "video_id": video_id,
        },
    }

    service = MVPJobService.__new__(MVPJobService)
    service.job_store = MagicMock()
    service.job_store.get.return_value = payload
    service._set_status = MagicMock()

    with patch("backend.services.mvp_job_service.db") as mock_db:
        mock_db.get_session.return_value = {"id": session_id}
        mock_db.get_video.return_value = {"id": video_id}
        mock_db.session_video_exists.return_value = False
        mock_db.video_metrics_exist.return_value = False
        mock_db.persist_analysis_summary.return_value = True
        mock_db.update_streak.return_value = {"current_streak": 1}

        out = service.save_result_for_user("job-partial-recovery", user_id)

    assert out is not None
    assert out["success"] is True
    assert out["session_id"] == session_id
    assert out["video_id"] == video_id
    mock_db.add_video_to_session.assert_called_once_with(session_id, video_id)
    mock_db.save_metrics.assert_called_once()
