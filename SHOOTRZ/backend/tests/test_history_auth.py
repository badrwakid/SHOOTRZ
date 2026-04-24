import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_history_requires_auth():
    resp = client.get("/history/some-fake-user-id")
    assert resp.status_code in (401, 403)


def test_history_stats_requires_auth():
    resp = client.get("/history/some-fake-user-id/stats")
    assert resp.status_code in (401, 403)


def test_history_own_user_with_valid_token():
    pytest.skip("Requires live Supabase JWT")
