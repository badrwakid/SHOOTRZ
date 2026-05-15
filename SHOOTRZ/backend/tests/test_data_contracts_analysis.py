"""Contract invariants for POST /api/analysis/complete."""

from pathlib import Path
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app
from backend.utils.supabase_auth import AuthenticatedUser, get_authenticated_user


client = TestClient(app)


def _set_user(user_id: str):
    original_override = app.dependency_overrides.get(get_authenticated_user)
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
        user_id=user_id,
    )
    return original_override


def _restore_user(original_override):
    if original_override is None:
        app.dependency_overrides.pop(get_authenticated_user, None)
    else:
        app.dependency_overrides[get_authenticated_user] = original_override


def test_complete_analysis_rejects_success_without_persisted_ids():
    original_override = _set_user('55555555-5555-5555-5555-555555555555')
    with patch('backend.routers.analysis.mvp_service') as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            'success': True,
            'session_id': None,
            'video_id': 'vid-1',
            'summary_persisted': True,
            'history_visible': True,
            'already_persisted': False,
        }
        try:
            response = client.post('/api/analysis/complete', json={'job_id': 'job-contract-ids'})
        finally:
            _restore_user(original_override)

    assert response.status_code == 500
    assert response.json() == {'detail': 'Failed to persist analysis'}


def test_complete_analysis_rejects_success_when_visibility_flags_missing():
    original_override = _set_user('66666666-6666-6666-6666-666666666666')
    with patch('backend.routers.analysis.mvp_service') as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            'success': True,
            'session_id': 'sess-1',
            'video_id': 'vid-1',
            'already_persisted': False,
        }
        try:
            response = client.post('/api/analysis/complete', json={'job_id': 'job-contract-flags'})
        finally:
            _restore_user(original_override)

    assert response.status_code == 500
    assert response.json() == {'detail': 'Failed to persist analysis'}


def test_complete_analysis_rejects_success_when_visibility_flags_false():
    original_override = _set_user('77777777-7777-7777-7777-777777777777')
    with patch('backend.routers.analysis.mvp_service') as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            'success': True,
            'session_id': 'sess-2',
            'video_id': 'vid-2',
            'summary_persisted': True,
            'history_visible': False,
            'already_persisted': False,
        }
        try:
            response = client.post('/api/analysis/complete', json={'job_id': 'job-contract-false'})
        finally:
            _restore_user(original_override)

    assert response.status_code == 500
    assert response.json() == {'detail': 'Failed to persist analysis'}


def test_complete_analysis_returns_contract_fields_on_success():
    original_override = _set_user('88888888-8888-8888-8888-888888888888')
    with patch('backend.routers.analysis.mvp_service') as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            'success': True,
            'session_id': 'sess-ok',
            'video_id': 'vid-ok',
            'summary_persisted': True,
            'history_visible': True,
            'already_persisted': False,
        }
        try:
            response = client.post('/api/analysis/complete', json={'job_id': 'job-contract-pass'})
        finally:
            _restore_user(original_override)

    assert response.status_code == 200
    assert response.json() == {
        'success': True,
        'session_id': 'sess-ok',
        'video_id': 'vid-ok',
        'already_persisted': False,
        'summary_persisted': True,
        'history_visible': True,
        'message': None,
    }
