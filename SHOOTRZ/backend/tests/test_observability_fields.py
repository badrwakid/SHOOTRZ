"""Structured log tokens for the analysis commit and history read paths (ops / diagnostics)."""

import logging
import sys
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app
from backend.utils.supabase_auth import AuthenticatedUser, get_authenticated_user

client = TestClient(app)


def test_complete_analysis_logs_stage_fields(caplog):
    caplog.set_level(logging.INFO, logger="backend.routers.analysis")
    with patch("backend.routers.analysis.mvp_service") as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            "success": True,
            "session_id": "sess-obs",
            "video_id": "vid-obs",
            "summary_persisted": True,
            "history_visible": True,
            "already_persisted": False,
        }
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        )
        try:
            r = client.post("/api/analysis/complete", json={"job_id": "job-obs-1"})
            assert r.status_code == 200
        finally:
            app.dependency_overrides.clear()
    text = caplog.text
    assert "commit_attempt" in text
    assert "commit_success" in text


def test_analysis_history_logs_history_query(caplog):
    caplog.set_level(logging.INFO, logger="backend.routers.user")
    with patch("backend.routers.user.db") as mock_db:
        mock_db.get_user_analysis_history.return_value = []
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        )
        try:
            r = client.get("/api/user/analysis-history?limit=10&offset=0")
            assert r.status_code == 200
        finally:
            app.dependency_overrides.clear()
    assert "history_query" in caplog.text
    user_recs = [r for r in caplog.records if r.name == "backend.routers.user" and r.getMessage() == "history_query"]
    assert user_recs
    assert getattr(user_recs[0], "history_source", None) == "analysis_summaries_v1"


def test_save_result_for_user_logs_persist_commit_stage(caplog):
    caplog.set_level(logging.INFO, logger="backend.services.mvp_job_service")
    from backend.services.mvp_job_service import MVPJobService

    svc = MVPJobService()
    out = svc.save_result_for_user("definitely-missing-job-id-12345", "cccccccc-cccc-cccc-cccc-cccccccccccc")
    assert out is None
    assert "persist_commit_stage" in caplog.text
