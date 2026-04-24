"""Tests for backend/chat/context_builder.py — sanitize_context_for_llm."""
import json
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Ensure the project root (parent of backend/) is on sys.path so that the
# relative imports inside context_builder.py resolve correctly.
# ---------------------------------------------------------------------------
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _stub_supabase_imports():
    """Inject lightweight stubs for the supabase SDK and its transitive deps
    so that context_builder can be imported without a real Supabase installation.
    This only patches *before* the first import of backend.chat.context_builder.
    """
    # Stub the 'supabase' package so supabase_client.py can import from it
    if "supabase" not in sys.modules:
        supabase_stub = types.ModuleType("supabase")
        supabase_stub.create_client = MagicMock(return_value=MagicMock())
        supabase_stub.Client = MagicMock
        sys.modules["supabase"] = supabase_stub

    # Stub backend.storage.supabase_client before db.py imports it
    if "backend.storage.supabase_client" not in sys.modules:
        sc_stub = types.ModuleType("backend.storage.supabase_client")
        sc_stub.get_service_client = MagicMock(return_value=MagicMock())
        sc_stub.get_anon_client = MagicMock(return_value=MagicMock())
        sc_stub.NotConfiguredError = RuntimeError
        sys.modules["backend.storage.supabase_client"] = sc_stub

    # Stub backend.storage.db so context_builder's `from ..storage.db import db` works
    if "backend.storage.db" not in sys.modules:
        db_stub = types.ModuleType("backend.storage.db")
        db_stub.db = MagicMock()
        sys.modules["backend.storage.db"] = db_stub

    # Ensure the backend.storage package itself is registered
    if "backend.storage" not in sys.modules:
        pkg = types.ModuleType("backend.storage")
        sys.modules["backend.storage"] = pkg


_stub_supabase_imports()


def test_sanitize_caps_context_size():
    from backend.chat.context_builder import sanitize_context_for_llm

    big_context = {
        "recent_sessions": [{"summary": "x" * 5000}] * 20,
    }
    result = sanitize_context_for_llm(big_context)
    assert len(json.dumps(result)) <= 32_000 + 100  # small tolerance


def test_sanitize_trims_sessions_to_five_by_default():
    """Pre-existing behaviour: sessions are capped at 5 before the hard limit."""
    from backend.chat.context_builder import sanitize_context_for_llm

    context = {
        "recent_sessions": [{"score": i} for i in range(10)],
        "goals": list(range(20)),
    }
    result = sanitize_context_for_llm(context)
    assert len(result["recent_sessions"]) <= 5
    assert len(result["goals"]) <= 10


def test_sanitize_small_context_unchanged():
    """A context well under 32 K must pass through without modification."""
    from backend.chat.context_builder import sanitize_context_for_llm

    context = {
        "user": {"name": "Test Player"},
        "recent_sessions": [{"score": 85}],
        "goals": ["shoot better"],
        "stats": {},
    }
    result = sanitize_context_for_llm(context)
    assert len(json.dumps(result)) <= 32_000 + 100
    assert result["user"]["name"] == "Test Player"
