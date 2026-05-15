"""Regression: RPC fallback must be explicitly surfaced in chat context metadata."""

import importlib
import re
from pathlib import Path
import sys
from unittest.mock import MagicMock


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import backend.chat.context_builder as context_builder


def _build_table_router(*, fail_tables=None):
    fail = set(fail_tables or [])

    def _table(name):
        t = MagicMock()
        if name in fail:
            t.select.return_value.eq.return_value.maybe_single.return_value.execute.side_effect = Exception(
                f'{name} query failed',
            )
            t.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.side_effect = Exception(
                f'{name} query failed',
            )
            return t

        if name == 'users':
            t.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
                'id': 'u1',
                'name': 'Fallback User',
                'skill_level': 'beginner',
            }
        elif name == 'user_profiles':
            t.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {
                'coaching_style': 'motivational',
                'primary_goal': 'improve consistency',
                'dominant_hand': 'right',
            }
        elif name == 'analysis_summaries':
            t.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {
                    'created_at': '2026-04-20T10:00:00+00:00',
                    'overall_score': 68,
                    'score_tier': 'good',
                    'top_improvements': ['arc'],
                    'top_strengths': ['follow-through'],
                },
            ]
        elif name == 'chat_history':
            t.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = [
                {'role': 'assistant', 'content': 'Keep your elbow in.', 'created_at': '2026-04-20T10:00:00+00:00'},
                {'role': 'user', 'content': 'How was my release?', 'created_at': '2026-04-20T09:59:00+00:00'},
            ]
        else:
            t.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = None
        return t

    return _table


def test_missing_get_coach_context_rpc_sets_fallback_marker():
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.side_effect = Exception(
        'function public.get_coach_context(uuid, integer) does not exist',
    )
    mock_client.table.return_value.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = {}
    mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []

    importlib.reload(context_builder)
    original = context_builder.get_service_client
    context_builder.get_service_client = lambda: mock_client
    try:
        context, context_used = context_builder.build_user_context(
            user_id='11111111-1111-1111-1111-111111111111',
            user_local_context=None,
            options=context_builder.ContextBuildOptions(max_recent_summaries=3),
        )
    finally:
        context_builder.get_service_client = original

    assert context['recent_sessions'] == []
    assert context['recent_chat'] == []
    assert context_used.get('rpc_fallback_reason') == 'missing_get_coach_context'


def test_rpc_fallback_recovers_recent_summaries_and_chat():
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.side_effect = Exception(
        'function public.get_coach_context(uuid, integer) does not exist',
    )

    mock_client.table.side_effect = _build_table_router()

    importlib.reload(context_builder)
    original = context_builder.get_service_client
    context_builder.get_service_client = lambda: mock_client
    try:
        context, context_used = context_builder.build_user_context(
            user_id='u1',
            user_local_context=None,
            options=context_builder.ContextBuildOptions(max_recent_summaries=3, max_chat_history=5),
        )
    finally:
        context_builder.get_service_client = original

    assert context_used.get('rpc_fallback_reason') == 'missing_get_coach_context'
    assert context_used.get('recent_summaries_count') == 1
    assert context_used.get('recent_chat_count') == 2
    assert context['user']['name'] == 'Fallback User'
    assert context['user']['dominant_hand'] == 'right'
    assert len(context['recent_sessions']) == 1
    assert len(context['recent_chat']) == 2
    assert context['recent_chat'][0]['role'] == 'user'


def test_get_coach_context_users_subquery_does_not_reference_missing_columns():
    """users has no dominant_hand or goals; they come from user_profiles (see schema_complete)."""
    ddl = (project_root / "supabase" / "schema_complete.sql").read_text(encoding="utf-8")
    start = ddl.index("CREATE OR REPLACE FUNCTION public.get_coach_context")
    end = ddl.index("END;", start)
    block = ddl[start:end]
    m = re.search(r"SELECT\s+([^)]+?)\s+FROM\s+users", block, re.IGNORECASE | re.DOTALL)
    assert m is not None
    user_proj = m.group(1).replace("\n", " ")
    assert "dominant_hand" not in user_proj
    assert "goals" not in user_proj
    m_profile = re.search(r"SELECT\s+([^)]+?)\s+FROM\s+user_profiles", block, re.IGNORECASE | re.DOTALL)
    assert m_profile is not None
    profile_proj = m_profile.group(1).replace("\n", " ")
    assert "dominant_hand" in profile_proj


def test_generic_rpc_failure_sets_generic_fallback_reason():
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.side_effect = Exception('temporary rpc outage')
    mock_client.table.side_effect = _build_table_router()

    importlib.reload(context_builder)
    original = context_builder.get_service_client
    context_builder.get_service_client = lambda: mock_client
    try:
        context, context_used = context_builder.build_user_context(
            user_id='u1',
            user_local_context=None,
            options=context_builder.ContextBuildOptions(max_recent_summaries=3, max_chat_history=5),
        )
    finally:
        context_builder.get_service_client = original

    assert context_used.get('rpc_fallback_reason') == 'rpc_get_coach_context_failed'
    assert len(context['recent_sessions']) == 1
    assert len(context['recent_chat']) == 2


def test_service_client_unavailable_sets_specific_reason():
    importlib.reload(context_builder)
    original = context_builder.get_service_client
    context_builder.get_service_client = lambda: (_ for _ in ()).throw(RuntimeError('no supabase env'))
    try:
        context, context_used = context_builder.build_user_context(
            user_id='u1',
            user_local_context=None,
            options=context_builder.ContextBuildOptions(max_recent_summaries=3, max_chat_history=5),
        )
    finally:
        context_builder.get_service_client = original

    assert context_used.get('rpc_fallback_reason') == 'service_client_unavailable'
    assert context['recent_sessions'] == []
    assert context['recent_chat'] == []


def test_fallback_query_failures_still_return_valid_context():
    mock_client = MagicMock()
    mock_client.rpc.return_value.execute.side_effect = Exception(
        'function public.get_coach_context(uuid, integer) does not exist',
    )
    mock_client.table.side_effect = _build_table_router(fail_tables={'analysis_summaries', 'chat_history'})

    importlib.reload(context_builder)
    original = context_builder.get_service_client
    context_builder.get_service_client = lambda: mock_client
    try:
        context, context_used = context_builder.build_user_context(
            user_id='u1',
            user_local_context=None,
            options=context_builder.ContextBuildOptions(max_recent_summaries=3, max_chat_history=5),
        )
    finally:
        context_builder.get_service_client = original

    assert context_used.get('rpc_fallback_reason') == 'missing_get_coach_context'
    assert isinstance(context, dict)
    assert isinstance(context_used, dict)
    assert context['user']['name'] == 'Fallback User'
    assert context['recent_sessions'] == []
    assert context['recent_chat'] == []
    assert context_used.get('recent_summaries_count') == 0
    assert context_used.get('recent_chat_count') == 0
