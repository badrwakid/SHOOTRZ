"""
Contract-level API tests to guard frontend/backend shape drift.
"""

from pathlib import Path
import sys

from fastapi.testclient import TestClient


project_root = Path(__file__).parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.main import app


client = TestClient(app)


def _openapi() -> dict:
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    return resp.json()


def test_mvp_analyze_contract_schema_present():
    doc = _openapi()
    path_item = doc["paths"]["/mvp/analyze"]["post"]
    response_200 = path_item["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" in response_200
    assert response_200["$ref"].endswith("MVPAnalyzeQueuedResponse")


def test_mvp_result_contract_fields_present():
    doc = _openapi()
    schema = doc["components"]["schemas"]["MVPResultResponse"]
    props = schema["properties"]

    assert "status" in props
    assert "contract_version" in props
    assert "run_id" in props
    assert "metrics" in props
    assert "overall_score" in props
    assert "events" in props
    assert "artifacts" in props
    assert "error" in props


def test_history_contract_schema_present():
    doc = _openapi()
    path_item = doc["paths"]["/history/{user_id}"]["get"]
    response_200 = path_item["responses"]["200"]["content"]["application/json"]["schema"]
    assert "$ref" in response_200
    assert response_200["$ref"].endswith("HistoryResponse")

