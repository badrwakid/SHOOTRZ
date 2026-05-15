"""Verify build_user_context makes exactly one RPC call (not 4 individual DB calls)."""
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Ensure the project root (parent of backend/) is on sys.path so that the
# relative imports inside context_builder.py resolve correctly.
# ---------------------------------------------------------------------------
project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


def _stub_supabase_imports():
    """Inject lightweight stubs for the supabase SDK and its transitive deps."""
    if "supabase" not in sys.modules:
        supabase_stub = types.ModuleType("supabase")
        supabase_stub.create_client = MagicMock(return_value=MagicMock())
        supabase_stub.Client = MagicMock
        sys.modules["supabase"] = supabase_stub

    if "backend.storage" not in sys.modules:
        pkg = types.ModuleType("backend.storage")
        sys.modules["backend.storage"] = pkg

    if "backend.storage.supabase_client" not in sys.modules:
        sc_stub = types.ModuleType("backend.storage.supabase_client")
        sc_stub.get_service_client = MagicMock(return_value=MagicMock())
        sc_stub.get_anon_client = MagicMock(return_value=MagicMock())
        sc_stub.NotConfiguredError = RuntimeError
        sys.modules["backend.storage.supabase_client"] = sc_stub


@pytest.fixture(autouse=True)
def stub_supabase(monkeypatch):
    """Ensure supabase stubs are in place for every test in this file."""
    _stub_supabase_imports()


def _make_mock_client(rpc_data):
    """Helper: returns a mock Supabase client whose .rpc().execute().data = rpc_data."""
    mock_client = MagicMock()
    mock_rpc_result = MagicMock()
    mock_rpc_result.data = rpc_data
    mock_client.rpc.return_value.execute.return_value = mock_rpc_result
    return mock_client


def _reload_and_call(mock_client, user_id, user_local_context, opts):
    """Reload context_builder with a patched get_service_client, then call
    build_user_context.  We reload FIRST so the from-import runs against our
    stub module, then overwrite the module-level name before calling."""
    import importlib
    import backend.chat.context_builder as ctx_mod

    # Step 1: reload — the from-import will grab get_service_client from the
    # stub we placed in sys.modules["backend.storage.supabase_client"] during
    # _stub_supabase_imports().  That stub's attribute is a plain MagicMock, so
    # we need to overwrite it *after* reload while keeping the module reference.
    importlib.reload(ctx_mod)

    # Step 2: overwrite the module-level name that reload() just re-bound.
    original = ctx_mod.get_service_client
    ctx_mod.get_service_client = lambda: mock_client
    try:
        result = ctx_mod.build_user_context(
            user_id=user_id,
            user_local_context=user_local_context,
            options=opts,
        )
    finally:
        ctx_mod.get_service_client = original  # restore for other tests

    return result, mock_client


def test_build_user_context_makes_single_rpc_call():
    """build_user_context must issue exactly one RPC call, not 4 individual DB queries."""

    class Opts:
        max_recent_summaries = 3
        include_raw_artifacts = False

    mock_client = _make_mock_client({
        "user": {
            "id": "u1",
            "name": "Test User",
            "skill_level": "intermediate",
            "position": "SG",
        },
        "profile": {
            "coaching_style": "motivational",
            "primary_goal": "improve form",
            "training_frequency": 3,
            "years_playing": 5,
            "dominant_hand": "right",
        },
        "stats": {"total_sessions": 5, "avg_score": 72.0},
        "summaries": [
            {
                "summary_text": "Good form",
                "overall_score": 72,
                "score_tier": "good",
                "top_strengths": ["release", "follow-through"],
                "top_improvements": ["arc"],
                "created_at": "2026-01-01T00:00:00+00:00",
            }
        ],
    })

    result, mock_client = _reload_and_call(mock_client, "u1", {}, Opts())

    # --- Verify exactly ONE RPC call was made ---
    mock_client.rpc.assert_called_once_with(
        "get_coach_context",
        {"p_user_id": "u1", "p_summary_limit": 3},
    )

    # --- Verify return shape: (context_dict, context_used_dict) ---
    assert isinstance(result, tuple), "build_user_context must return a 2-tuple"
    assert len(result) == 2, "build_user_context must return exactly 2 elements"

    context, context_used = result

    # context dict keys
    assert "user" in context
    assert "stats" in context
    assert "recent_sessions" in context
    assert "goals" in context
    assert "primary_goal" in context
    assert "generated_at" in context

    # user section populated from RPC data
    assert context["user"]["name"] == "Test User"
    assert context["user"]["skill_level"] == "intermediate"
    assert context["user"]["coaching_style"] == "motivational"
    assert context["user"]["dominant_hand"] == "right"

    # recent_sessions built from summaries
    assert len(context["recent_sessions"]) == 1
    assert context["recent_sessions"][0]["overall_score"] == 72

    # stats forwarded as-is
    assert context["stats"]["total_sessions"] == 5

    # context_used dict keys
    assert "profile" in context_used
    assert "user_profile" in context_used
    assert "recent_summaries_count" in context_used
    assert "stats_available" in context_used
    assert context_used["recent_summaries_count"] == 1
    assert context_used["stats_available"] is True


def test_build_user_context_handles_empty_rpc_response():
    """build_user_context must gracefully handle an RPC returning null/empty data."""

    class Opts:
        max_recent_summaries = 5
        include_raw_artifacts = False

    mock_client = _make_mock_client(None)  # Simulate no data returned

    result, _ = _reload_and_call(mock_client, "u-missing", None, Opts())

    assert isinstance(result, tuple)
    context, context_used = result

    # Everything should degrade gracefully to empty/falsy defaults
    assert context["user"] == {}
    assert context["stats"] == {}
    assert context["recent_sessions"] == []
    assert context["goals"] == []
    assert context["primary_goal"] is None
    assert context_used["profile"] is False
    assert context_used["recent_summaries_count"] == 0
