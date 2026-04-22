import os
from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _set_test_env(monkeypatch):
    """Ensure tests run with deterministic local env values."""
    monkeypatch.setenv("SUPABASE_URL", "http://localhost:54321")
    monkeypatch.setenv("SUPABASE_KEY", "test-anon-key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test-service-role-key")
    monkeypatch.setenv("SHOOTRZ_ENV", "test")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")


@pytest.fixture
def mock_supabase_client():
    """In-memory stand-in for chained Supabase client calls."""
    client = MagicMock(name="SupabaseClient")

    table = MagicMock(name="Table")
    table.insert.return_value.execute.return_value.data = [{"id": "mock-id"}]
    table.select.return_value.eq.return_value.execute.return_value.data = []
    table.update.return_value.eq.return_value.execute.return_value.data = [{"id": "mock-id"}]
    table.delete.return_value.eq.return_value.execute.return_value.data = [{"id": "mock-id"}]
    client.table.return_value = table

    client.auth.sign_in_with_password.return_value = MagicMock(
        user=MagicMock(id="user-1"),
        session=MagicMock(access_token="jwt-mock"),
    )
    return client


def pytest_collection_modifyitems(config, items):
    """Skip live DB tests when live credentials are missing."""
    skip_live_db = pytest.mark.skip(reason="Live Supabase credentials not configured")
    for item in items:
        if "live_db" in item.keywords and not os.getenv("SUPABASE_LIVE_URL"):
            item.add_marker(skip_live_db)
