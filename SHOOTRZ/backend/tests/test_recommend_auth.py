from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_recommend_requires_auth():
    resp = client.post("/api/recommend", json={"user_vec": [], "user_context": []})
    assert resp.status_code == 401
