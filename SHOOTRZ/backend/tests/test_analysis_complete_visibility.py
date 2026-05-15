"""Regression: /api/analysis/complete should not report success with missing IDs."""

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


def test_complete_analysis_rejects_success_without_session_or_video_ids():
    uid = '33333333-3333-3333-3333-333333333333'
    original_override = app.dependency_overrides.get(get_authenticated_user)
    with patch('backend.routers.analysis.mvp_service') as mock_svc:
        mock_svc.save_result_for_user.return_value = {
            'success': True,
            'session_id': None,
            'video_id': None,
            'already_persisted': False,
        }
        app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(
            user_id=uid,
        )
        try:
            response = client.post('/api/analysis/complete', json={'job_id': 'job-visibility-1'})
        finally:
            if original_override is None:
                app.dependency_overrides.pop(get_authenticated_user, None)
            else:
                app.dependency_overrides[get_authenticated_user] = original_override

    assert response.status_code == 500
    assert response.json() == {'detail': 'Failed to persist analysis'}
