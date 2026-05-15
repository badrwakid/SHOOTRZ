from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import user as user_router
from backend.storage.db import SupabaseDB
from backend.storage.db import USER_PROFILE_ALLOWED_FIELDS
from backend.utils.supabase_auth import AuthenticatedUser, get_authenticated_user


client = TestClient(app)
SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'supabase' / 'schema_complete.sql'


def _override_auth() -> None:
    app.dependency_overrides[get_authenticated_user] = (
        lambda: AuthenticatedUser(user_id='user-1')
    )


def _clear_auth_override() -> None:
    app.dependency_overrides.clear()


class _FakeResponse:
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None):
        self.data = data or []


class _FakeTableQuery:
    def __init__(self, fake_sb: '_FakeSupabase', table_name: str):
        self.fake_sb = fake_sb
        self.table_name = table_name
        self.action = 'select'
        self.payload: Dict[str, Any] = {}
        self._limit: Optional[int] = None

    def update(self, payload: Dict[str, Any]) -> '_FakeTableQuery':
        self.action = 'update'
        self.payload = payload
        return self

    def select(self, _fields: str) -> '_FakeTableQuery':
        self.action = 'select'
        return self

    def eq(self, _k: str, _v: Any) -> '_FakeTableQuery':
        return self

    def order(self, _k: str, desc: bool = False) -> '_FakeTableQuery':
        return self

    def limit(self, n: int) -> '_FakeTableQuery':
        self._limit = n
        return self

    def execute(self) -> _FakeResponse:
        self.fake_sb.calls.append(
            {
                'table': self.table_name,
                'action': self.action,
                'payload': dict(self.payload),
                'limit': self._limit,
            },
        )
        if self.table_name == 'sessions' and self.action == 'select':
            return _FakeResponse(self.fake_sb.sessions_rows)
        if self.table_name == 'chat_history' and self.action == 'select':
            return _FakeResponse(self.fake_sb.chat_rows)
        if self.table_name == 'analysis_summaries' and self.action == 'select':
            return _FakeResponse(self.fake_sb.summaries_rows)
        if self.table_name == 'users' and self.action == 'update':
            return _FakeResponse([{'id': 'user-1'}])
        return _FakeResponse([])


class _FakeSupabase:
    def __init__(
        self,
        *,
        sessions_rows: Optional[List[Dict[str, Any]]] = None,
        chat_rows: Optional[List[Dict[str, Any]]] = None,
        summaries_rows: Optional[List[Dict[str, Any]]] = None,
    ):
        self.calls: List[Dict[str, Any]] = []
        self.sessions_rows = sessions_rows or []
        self.chat_rows = chat_rows or []
        self.summaries_rows = summaries_rows or []

    def table(self, table_name: str) -> _FakeTableQuery:
        return _FakeTableQuery(self, table_name)


def test_update_user_sends_only_allowed_columns_to_users_table(monkeypatch):
    mock_sb = MagicMock(name='SupabaseClient')
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
        data=[{'id': 'u1'}],
    )
    monkeypatch.setattr('backend.storage.db.get_service_client', lambda: mock_sb)
    db = SupabaseDB()

    db.update_user(
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        {
            'name': 'Badr',
            'position': 'Guard',
            'skill_level': 'beginner',
            'evil': 'drop-me',
        },
    )

    mock_sb.table.assert_called_with('users')
    call_payload = mock_sb.table.return_value.update.call_args[0][0]
    assert call_payload == {'name': 'Badr', 'position': 'Guard', 'skill_level': 'beginner'}
    assert 'evil' not in call_payload


def test_put_profile_returns_same_shape_as_get_profile(monkeypatch):
    _override_auth()
    try:
        base_user = {
            'id': 'user-1',
            'name': 'Coach B',
            'username': 'coachb',
            'position': 'Guard',
            'skill_level': 'Beginner',
        }
        profile = {'user_id': 'user-1', 'primary_goal': 'consistency'}

        monkeypatch.setattr(
            'backend.routers.user.db.update_user_full_atomic', lambda **kwargs: {'ok': True},
        )
        monkeypatch.setattr('backend.routers.user.db.get_user', lambda _uid: base_user)
        monkeypatch.setattr('backend.routers.user.db.get_user_profile', lambda _uid: profile)

        put_resp = client.put(
            '/api/user/profile',
            json={
                'name': 'Coach B',
                'position': 'Guard',
                'skill_level': 'Beginner',
                'primary_goal': 'consistency',
            },
        )
        get_resp = client.get('/api/user/profile')
    finally:
        _clear_auth_override()

    assert put_resp.status_code == 200
    assert get_resp.status_code == 200
    assert put_resp.json() == get_resp.json()
    assert put_resp.json()['profile']['primary_goal'] == 'consistency'


def test_put_preferences_updates_profile_preferences(monkeypatch):
    _override_auth()
    try:
        base_user = {'id': 'user-1', 'name': 'Coach B'}
        updated_profile = {
            'user_id': 'user-1',
            'notifications_enabled': False,
            'dark_mode_enabled': True,
            'analytics_enabled': False,
        }

        monkeypatch.setattr('backend.routers.user.db.get_user', lambda _uid: base_user)
        monkeypatch.setattr(
            'backend.routers.user.db.upsert_user_profile',
            lambda _uid, payload: {**updated_profile, **payload},
        )

        resp = client.put(
            '/api/user/preferences',
            json={
                'notifications_enabled': False,
                'dark_mode_enabled': True,
                'analytics_enabled': False,
            },
        )
    finally:
        _clear_auth_override()

    assert resp.status_code == 200
    body = resp.json()
    assert body['id'] == 'user-1'
    assert body['profile']['notifications_enabled'] is False
    assert body['profile']['dark_mode_enabled'] is True
    assert body['profile']['analytics_enabled'] is False


def test_put_profile_splits_users_core_and_user_profiles_payloads(monkeypatch):
    _override_auth()
    try:
        base_user = {
            'id': 'user-1',
            'name': 'Coach B',
            'username': 'coachb',
            'position': 'Guard',
            'skill_level': 'Beginner',
        }
        profile = {
            'user_id': 'user-1',
            'primary_goal': 'consistency',
            'notifications_enabled': False,
        }
        captured: Dict[str, Dict[str, Any]] = {}

        def _capture_update(*, user_id: str, core_fields: Dict[str, Any], profile_fields: Dict[str, Any]):
            captured['user_id'] = {'value': user_id}
            captured['core_fields'] = core_fields
            captured['profile_fields'] = profile_fields
            return {'ok': True}

        monkeypatch.setattr('backend.routers.user.db.update_user_full_atomic', _capture_update)
        monkeypatch.setattr('backend.routers.user.db.get_user', lambda _uid: base_user)
        monkeypatch.setattr('backend.routers.user.db.get_user_profile', lambda _uid: profile)

        resp = client.put(
            '/api/user/profile',
            json={
                'name': 'Coach B',
                'username': 'coachb',
                'position': 'Guard',
                'skill_level': 'Beginner',
                'primary_goal': 'consistency',
                'notifications_enabled': False,
            },
        )
    finally:
        _clear_auth_override()

    assert resp.status_code == 200
    assert captured['user_id']['value'] == 'user-1'
    assert captured['core_fields'] == {
        'name': 'Coach B',
        'username': 'coachb',
        'position': 'Guard',
        'skill_level': 'Beginner',
    }
    assert captured['profile_fields'] == {
        'primary_goal': 'consistency',
        'notifications_enabled': False,
    }


def test_put_profile_forwards_bio_and_avatar_url_to_profile_fields(monkeypatch):
    _override_auth()
    try:
        base_user = {
            'id': 'user-1',
            'name': 'Coach B',
            'username': 'coachb',
            'position': 'Guard',
            'skill_level': 'Beginner',
        }
        profile = {
            'user_id': 'user-1',
            'bio': 'Shooter from Cairo',
            'avatar_url': 'https://cdn.example.com/avatar.png',
        }
        captured: Dict[str, Dict[str, Any]] = {}

        def _capture_update(*, user_id: str, core_fields: Dict[str, Any], profile_fields: Dict[str, Any]):
            captured['user_id'] = {'value': user_id}
            captured['core_fields'] = core_fields
            captured['profile_fields'] = profile_fields
            return {'ok': True}

        monkeypatch.setattr('backend.routers.user.db.update_user_full_atomic', _capture_update)
        monkeypatch.setattr('backend.routers.user.db.get_user', lambda _uid: base_user)
        monkeypatch.setattr('backend.routers.user.db.get_user_profile', lambda _uid: profile)

        resp = client.put(
            '/api/user/profile',
            json={
                'name': 'Coach B',
                'bio': 'Shooter from Cairo',
                'avatar_url': 'https://cdn.example.com/avatar.png',
            },
        )
    finally:
        _clear_auth_override()

    assert resp.status_code == 200
    assert captured['user_id']['value'] == 'user-1'
    assert captured['core_fields'] == {
        'name': 'Coach B',
    }
    assert captured['profile_fields'] == {
        'bio': 'Shooter from Cairo',
        'avatar_url': 'https://cdn.example.com/avatar.png',
    }


def test_router_and_db_profile_field_sets_are_aligned():
    assert user_router.USER_PROFILE_FIELDS == USER_PROFILE_ALLOWED_FIELDS


def test_upsert_user_profile_filters_unknown_columns(monkeypatch):
    mock_sb = MagicMock(name='SupabaseClient')
    mock_sb.table.return_value.upsert.return_value.execute.return_value = MagicMock(
        data=[{'user_id': 'u1'}],
    )
    monkeypatch.setattr('backend.storage.db.get_service_client', lambda: mock_sb)
    db = SupabaseDB()

    db.upsert_user_profile(
        'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        {
            'primary_goal': 'consistency',
            'notifications_enabled': True,
            'skill_level': 'must-not-live-in-profile-table',
            'unknown_key': 'drop-me',
        },
    )

    mock_sb.table.assert_called_with('user_profiles')
    call_payload = mock_sb.table.return_value.upsert.call_args[0][0]
    assert call_payload == {
        'user_id': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
        'primary_goal': 'consistency',
        'notifications_enabled': True,
    }
    assert 'skill_level' not in call_payload
    assert 'unknown_key' not in call_payload


def test_get_user_export_returns_bounded_payload_metadata(monkeypatch):
    _override_auth()
    try:
        payload = {
            'user': {'id': 'user-1'},
            'profile': {'user_id': 'user-1'},
            'sessions': [{'id': 's1'}],
            'chat_history': [{'id': 'c1', 'role': 'user', 'content': 'x'}],
            'analysis_summaries': [{'id': 'a1', 'session_id': 's1'}],
            'metrics': [{'id': 'm1', 'video_id': 'v1', 'metric_name': 'elbow_angle', 'value': 90}],
            'metadata': {
                'truncated': False,
                'limits': {
                    'sessions': 100,
                    'chat_messages': 200,
                    'analysis_summaries': 100,
                    'metrics': 500,
                },
                'counts': {
                    'sessions_returned': 1,
                    'chat_messages_returned': 1,
                    'analysis_summaries_returned': 1,
                    'metrics_returned': 1,
                },
            },
        }
        monkeypatch.setattr('backend.routers.user.db.build_user_export_payload', lambda **kwargs: payload)
        resp = client.get('/api/user/export')
    finally:
        _clear_auth_override()

    assert resp.status_code == 200
    body = resp.json()
    assert body['metadata']['limits'] == {
        'sessions': 100,
        'chat_messages': 200,
        'analysis_summaries': 100,
        'metrics': 500,
    }
    assert body['metadata']['truncated'] is False
    assert len(body['sessions']) == 1
    assert len(body['chat_history']) == 1
    assert len(body['analysis_summaries']) == 1
    assert len(body['metrics']) == 1


def test_build_user_export_payload_enforces_limits_and_truncation(monkeypatch):
    sessions_rows = [{'id': f's-{i}'} for i in range(101)]
    chat_rows = [{'id': f'c-{i}', 'role': 'user', 'content': 'x'} for i in range(201)]
    summaries_rows = [{'id': f'a-{i}', 'session_id': f's-{i}'} for i in range(101)]
    fake_sb = _FakeSupabase(
        sessions_rows=sessions_rows,
        chat_rows=chat_rows,
        summaries_rows=summaries_rows,
    )
    monkeypatch.setattr('backend.storage.db.get_service_client', lambda: fake_sb)
    db = SupabaseDB()
    monkeypatch.setattr(db, 'get_user', lambda _uid: {'id': 'user-1'})
    monkeypatch.setattr(db, 'get_user_profile', lambda _uid: {'user_id': 'user-1'})
    monkeypatch.setattr(
        db,
        'get_user_analysis_history',
        lambda user_id, limit, offset: [{'metrics': [{'id': f'm-{i}'}]} for i in range(501)],
    )

    result = db.build_user_export_payload(
        'user-1',
        sessions_limit=100,
        chat_messages_limit=200,
    )

    assert result is not None
    assert len(result['sessions']) == 100
    assert len(result['chat_history']) == 200
    assert len(result['analysis_summaries']) == 100
    assert len(result['metrics']) == 500
    assert result['metadata']['truncated'] is True
    assert result['metadata']['counts']['sessions_fetched_before_limit'] == 101
    assert result['metadata']['counts']['chat_messages_fetched_before_limit'] == 201
    assert result['metadata']['counts']['analysis_summaries_fetched_before_limit'] == 101
    assert result['metadata']['counts']['metrics_fetched_before_limit'] == 501


def test_delete_account_route_path_is_stable(monkeypatch):
    _override_auth()
    try:
        class _AuthAdmin:
            @staticmethod
            def delete_user(_uid: str) -> Dict[str, Any]:
                return {'ok': True}

        class _Auth:
            admin = _AuthAdmin()

        class _ServiceClient:
            auth = _Auth()

        monkeypatch.setattr('backend.routers.user.db.delete_all_data_for_user', lambda _uid: True)
        monkeypatch.setattr('backend.routers.user.get_service_client', lambda: _ServiceClient())

        ok_resp = client.delete('/api/user/account')
        wrong_path_resp = client.delete('/api/user')
    finally:
        _clear_auth_override()

    assert ok_resp.status_code == 200
    assert wrong_path_resp.status_code == 404


def test_schema_users_table_owns_core_identity_fields():
    schema = SCHEMA_PATH.read_text(encoding='utf-8').lower()
    users_start = schema.index('create table if not exists users')
    users_end = schema.index(');', users_start)
    users_block = schema[users_start:users_end]

    for required in ('name', 'username', 'position', 'skill_level'):
        assert required in users_block

    for forbidden in ('notifications_enabled', 'dark_mode_enabled', 'analytics_enabled'):
        assert forbidden not in users_block


def test_schema_user_profiles_table_owns_preferences_only():
    schema = SCHEMA_PATH.read_text(encoding='utf-8').lower()
    profiles_start = schema.index('create table if not exists user_profiles')
    profiles_end = schema.index(');', profiles_start)
    profiles_block = schema[profiles_start:profiles_end]

    for required in ('notifications_enabled', 'dark_mode_enabled', 'analytics_enabled'):
        assert required in profiles_block

    for forbidden in ('name', 'username', 'position', 'skill_level'):
        assert forbidden not in profiles_block


def test_get_profile(monkeypatch):
    _override_auth()
    try:
        monkeypatch.setattr(
            'backend.routers.user.db.get_user',
            lambda _uid: {
                'id': 'user-1',
                'name': 'Profile User',
                'username': 'profile-user',
                'position': 'Guard',
                'skill_level': 'beginner',
            },
        )
        monkeypatch.setattr(
            'backend.routers.user.db.get_user_profile',
            lambda _uid: {
                'user_id': 'user-1',
                'notifications_enabled': True,
                'dark_mode_enabled': False,
                'analytics_enabled': True,
            },
        )

        resp = client.get('/api/user/profile')
    finally:
        _clear_auth_override()

    assert resp.status_code == 200
    body = resp.json()
    assert body['id'] == 'user-1'
    assert body['name'] == 'Profile User'
    assert body['profile']['user_id'] == 'user-1'
    assert body['profile']['dark_mode_enabled'] is False


def test_update_profile(monkeypatch):
    _override_auth()
    try:
        captured: Dict[str, Dict[str, Any]] = {}

        def _capture_update(*, user_id: str, core_fields: Dict[str, Any], profile_fields: Dict[str, Any]):
            captured['user_id'] = {'value': user_id}
            captured['core_fields'] = core_fields
            captured['profile_fields'] = profile_fields
            return {'ok': True}

        monkeypatch.setattr('backend.routers.user.db.update_user_full_atomic', _capture_update)
        monkeypatch.setattr(
            'backend.routers.user.db.get_user',
            lambda _uid: {
                'id': 'user-1',
                'name': 'Updated Name',
                'username': 'updated-user',
                'position': 'Forward',
                'skill_level': 'advanced',
            },
        )
        monkeypatch.setattr(
            'backend.routers.user.db.get_user_profile',
            lambda _uid: {
                'user_id': 'user-1',
                'primary_goal': 'consistency',
                'notifications_enabled': False,
            },
        )

        resp = client.put(
            '/api/user/profile',
            json={
                'name': 'Updated Name',
                'username': 'updated-user',
                'position': 'Forward',
                'skill_level': 'advanced',
                'primary_goal': 'consistency',
                'notifications_enabled': False,
            },
        )
    finally:
        _clear_auth_override()

    assert resp.status_code == 200
    assert captured['user_id']['value'] == 'user-1'
    assert captured['core_fields'] == {
        'name': 'Updated Name',
        'username': 'updated-user',
        'position': 'Forward',
        'skill_level': 'advanced',
    }
    assert captured['profile_fields'] == {
        'primary_goal': 'consistency',
        'notifications_enabled': False,
    }
    assert resp.json()['profile']['primary_goal'] == 'consistency'


def test_delete_user_cascade(monkeypatch):
    class _CascadeResponse:
        def __init__(self, data: Optional[List[Dict[str, Any]]] = None):
            self.data = data or []

    class _CascadeQuery:
        def __init__(self, fake_sb: '_CascadeSupabase', table_name: str):
            self.fake_sb = fake_sb
            self.table_name = table_name
            self.action = 'select'
            self.filters: Dict[str, Any] = {}

        def select(self, _fields: str) -> '_CascadeQuery':
            self.action = 'select'
            return self

        def delete(self) -> '_CascadeQuery':
            self.action = 'delete'
            return self

        def eq(self, key: str, value: Any) -> '_CascadeQuery':
            self.filters[key] = value
            return self

        def in_(self, key: str, value: Any) -> '_CascadeQuery':
            self.filters[key] = list(value)
            return self

        def execute(self) -> _CascadeResponse:
            self.fake_sb.calls.append({
                'table': self.table_name,
                'action': self.action,
                'filters': dict(self.filters),
            })
            if self.table_name == 'videos' and self.action == 'select':
                return _CascadeResponse([{'id': 'vid-1'}])
            if self.table_name == 'metrics' and self.action == 'select':
                return _CascadeResponse([{'id': 'metric-1'}])
            if self.table_name == 'sessions' and self.action == 'select':
                return _CascadeResponse([{'id': 'session-1'}])
            return _CascadeResponse([])

    class _CascadeSupabase:
        def __init__(self):
            self.calls: List[Dict[str, Any]] = []

        def table(self, table_name: str) -> _CascadeQuery:
            return _CascadeQuery(self, table_name)

    fake_sb = _CascadeSupabase()
    monkeypatch.setattr('backend.storage.db.get_service_client', lambda: fake_sb)
    db = SupabaseDB()

    ok = db.delete_all_data_for_user('user-1')

    assert ok is True
    cascade_pairs = [(c['table'], c['action']) for c in fake_sb.calls]
    assert ('chat_history', 'delete') in cascade_pairs
    assert ('feedback', 'delete') in cascade_pairs
    assert ('metrics', 'delete') in cascade_pairs
    assert ('session_videos', 'delete') in cascade_pairs
    assert ('analysis_summaries', 'delete') in cascade_pairs
    assert ('videos', 'delete') in cascade_pairs
    assert ('sessions', 'delete') in cascade_pairs
    assert ('drill_completions', 'delete') in cascade_pairs
    assert ('workout_progress', 'delete') in cascade_pairs
    assert ('user_streaks', 'delete') in cascade_pairs
    assert ('user_profiles', 'delete') in cascade_pairs
    assert ('users', 'delete') in cascade_pairs
