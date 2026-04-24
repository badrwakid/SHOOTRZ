"""Tests for Supabase client singleton caching via lru_cache."""
import sys
from unittest.mock import MagicMock

import pytest

# Mock dotenv and supabase before any imports
sys.modules['dotenv'] = MagicMock()
sys.modules['supabase'] = MagicMock()


def test_service_client_is_singleton(mock_supabase_client):
    """Service client should be cached as singleton via lru_cache."""
    from backend.storage.supabase_client import get_service_client

    c1 = get_service_client()
    c2 = get_service_client()
    assert c1 is c2, "get_service_client() must return the same object each call"


def test_anon_client_is_singleton(mock_supabase_client):
    """Anon client should be cached as singleton via lru_cache."""
    from backend.storage.supabase_client import get_anon_client

    c1 = get_anon_client()
    c2 = get_anon_client()
    assert c1 is c2, "get_anon_client() must return the same object each call"
