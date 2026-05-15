"""Tests for authenticated MVP analysis persistence (POST /api/analysis/complete)."""

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


def test_complete_analysis_calls_save_result_for_user():
    uid = "11111111-1111-1111-1111-111111111111"
    with patch("backend.routers.analysis.mvp_service") as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            "success": True,
            "session_id": "sess-1",
            "video_id": "vid-1",
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
