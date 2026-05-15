"""Test auto-persist: save_result_for_user is called when user_id flows through pipeline."""
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio
import pytest

from backend.services.mvp_job_service import MVPJobService


@pytest.fixture
def service(tmp_path):
    svc = MVPJobService.__new__(MVPJobService)
    svc.backend_dir = tmp_path
    svc.outputs_dir = tmp_path / "outputs"
    svc.outputs_dir.mkdir()
    from backend.services.job_store import DurableJobStore
    svc.job_store = DurableJobStore(tmp_path / "jobs.sqlite3", retention_hours=1)
    svc._executor = None
    svc._running_tasks = set()
    return svc


def test_persist_supabase_calls_save_result_for_user_when_user_id_present(service, tmp_path):
    """When user_id is set, auto-persist should call save_result_for_user."""
    job_id = "test-job-123"
    job_result = {"status": "completed", "overall_score": 75}
    video_path = str(tmp_path / "video.mp4")

    with patch.object(service, "_save_to_supabase"), \
         patch.object(service, "_set_status"), \
         patch.object(service, "save_result_for_user", return_value={"success": True}) as mock_save:
        asyncio.get_event_loop().run_until_complete(
            service._persist_supabase_and_cleanup(job_id, job_result, video_path, user_id="user-abc")
        )

    mock_save.assert_called_once_with(job_id, "user-abc")


def test_persist_supabase_skips_save_when_no_user_id(service, tmp_path):
    """When user_id is None, auto-persist should NOT call save_result_for_user."""
    job_id = "test-job-456"
    job_result = {"status": "completed", "overall_score": 60}
    video_path = str(tmp_path / "video.mp4")

    with patch.object(service, "_save_to_supabase"), \
         patch.object(service, "_set_status"), \
         patch.object(service, "save_result_for_user") as mock_save:
        asyncio.get_event_loop().run_until_complete(
            service._persist_supabase_and_cleanup(job_id, job_result, video_path, user_id=None)
        )

    mock_save.assert_not_called()


def test_persist_supabase_skips_save_when_not_completed(service, tmp_path):
    """When status != completed, auto-persist should NOT call save_result_for_user."""
    job_id = "test-job-789"
    job_result = {"status": "failed"}
    video_path = str(tmp_path / "video.mp4")

    with patch.object(service, "_save_to_supabase"), \
         patch.object(service, "_set_status"), \
         patch.object(service, "save_result_for_user") as mock_save:
        asyncio.get_event_loop().run_until_complete(
            service._persist_supabase_and_cleanup(job_id, job_result, video_path, user_id="user-abc")
        )

    mock_save.assert_not_called()
