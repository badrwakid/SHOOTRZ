from pathlib import Path
import sys

import pytest
from fastapi import HTTPException


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.services.job_store import DurableJobStore
from backend.services.mvp_job_service import MVPJobService


def test_job_store_persists_between_instances(tmp_path):
    db_path = tmp_path / "jobs.sqlite3"
    store_a = DurableJobStore(db_path, retention_hours=1)
    store_a.upsert("job-1", {"status": "queued", "value": 1})

    store_b = DurableJobStore(db_path, retention_hours=1)
    payload = store_b.get("job-1")

    assert payload is not None
    assert payload["status"] == "queued"
    assert payload["value"] == 1


def test_job_store_cleanup_expired(tmp_path):
    db_path = tmp_path / "jobs.sqlite3"
    store = DurableJobStore(db_path, retention_hours=-1)
    store.upsert("expired-job", {"status": "queued"})
    deleted = store.cleanup_expired()

    assert deleted >= 1
    assert store.get("expired-job") is None


def test_artifact_path_blocks_traversal():
    service = MVPJobService()
    run_id = "non-existent-run"
    with pytest.raises(HTTPException) as exc_info:
        service.get_artifact_path(run_id, "../secrets.txt")
    assert exc_info.value.status_code == 400
