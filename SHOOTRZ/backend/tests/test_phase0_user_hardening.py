from __future__ import annotations

from typing import Any, Dict, List, Optional
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app
from backend.storage.db import SupabaseDB
from backend.utils.supabase_auth import AuthenticatedUser, get_authenticated_user


client = TestClient(app)


class _FakeResponse:
    def __init__(self, data: Optional[List[Dict[str, Any]]] = None):
        self.data = data or []


class _FakeRPCQuery:
    def __init__(self, fake_db: "_FakeSupabase", rpc_name: str, payload: Dict[str, Any]):
        self.fake_db = fake_db
        self.rpc_name = rpc_name
        self.payload = payload

    def execute(self) -> _FakeResponse:
        self.fake_db.calls.append(
            {
                "rpc": self.rpc_name,
                "payload": dict(self.payload),
            },
        )
        if self.fake_db.raise_rpc:
            raise RuntimeError("rpc failed")
        return _FakeResponse(self.fake_db.rpc_data)


class _FakeQuery:
    def __init__(self, fake_db: "_FakeSupabase", table_name: str):
        self.fake_db = fake_db
        self.table_name = table_name
        self.action = "select"
        self.payload: Dict[str, Any] = {}

    def update(self, payload: Dict[str, Any]) -> "_FakeQuery":
        self.action = "update"
        self.payload = payload
        return self

    def upsert(self, payload: Dict[str, Any], on_conflict: str) -> "_FakeQuery":
        self.action = "upsert"
        self.payload = payload
        return self

    def select(self, _fields: str) -> "_FakeQuery":
        self.action = "select"
        return self

    def eq(self, _k: str, _v: Any) -> "_FakeQuery":
        return self

    def order(self, _k: str, desc: bool = False) -> "_FakeQuery":
        return self

    def limit(self, _n: int) -> "_FakeQuery":
        return self

    def execute(self) -> _FakeResponse:
        self.fake_db.calls.append(
            {
                "table": self.table_name,
                "action": self.action,
                "payload": dict(self.payload),
            },
        )
        if self.table_name == "user_profiles" and self.action == "upsert" and self.fake_db.raise_profile:
            raise RuntimeError("profile write failed")
        if self.table_name == "users" and self.action == "update":
            return _FakeResponse([{"id": "user-1", **self.payload}])
        if self.table_name == "sessions" and self.action == "select":
            return _FakeResponse(self.fake_db.sessions_rows)
        if self.table_name == "chat_history" and self.action == "select":
            return _FakeResponse(self.fake_db.chat_rows)
        if self.table_name == "analysis_summaries" and self.action == "select":
            return _FakeResponse(self.fake_db.summaries_rows)
        if self.table_name == "user_profiles" and self.action == "upsert":
            return _FakeResponse([self.payload])
        return _FakeResponse([])


class _FakeSupabase:
    def __init__(
        self,
        *,
        raise_profile: bool = False,
        raise_rpc: bool = False,
        sessions_rows: Optional[List[Dict[str, Any]]] = None,
        chat_rows: Optional[List[Dict[str, Any]]] = None,
        summaries_rows: Optional[List[Dict[str, Any]]] = None,
        rpc_data: Optional[Dict[str, Any]] = None,
    ):
        self.raise_profile = raise_profile
        self.raise_rpc = raise_rpc
        self.sessions_rows = sessions_rows or []
        self.chat_rows = chat_rows or []
        self.summaries_rows = summaries_rows or []
        self.rpc_data = rpc_data or {"user": {"id": "user-1"}, "profile": {}}
        self.calls: List[Dict[str, Any]] = []

    def table(self, table_name: str) -> _FakeQuery:
        return _FakeQuery(self, table_name)

    def rpc(self, rpc_name: str, payload: Dict[str, Any]) -> _FakeRPCQuery:
        return _FakeRPCQuery(self, rpc_name, payload)


def test_update_user_full_atomic_uses_rpc_successfully():
    fake_sb = _FakeSupabase(rpc_data={"user": {"id": "user-1", "name": "new-name"}, "profile": {"user_id": "user-1"}})
    db = SupabaseDB()

    with patch("backend.storage.db.get_service_client", return_value=fake_sb):
        result = db.update_user_full_atomic(
            user_id="user-1",
            core_fields={"name": "new-name"},
            profile_fields={"primary_goal": "improve release"},
        )

    assert result is not None
    assert result["user"]["name"] == "new-name"
    rpc_calls = [c for c in fake_sb.calls if c.get("rpc") == "update_user_full_atomic"]
    assert len(rpc_calls) == 1
    assert rpc_calls[0]["payload"]["p_user_id"] == "user-1"
    assert rpc_calls[0]["payload"]["p_core"] == {"name": "new-name"}
    assert rpc_calls[0]["payload"]["p_profile"] == {"primary_goal": "improve release"}


def test_update_user_full_atomic_returns_none_when_rpc_fails():
    fake_sb = _FakeSupabase(raise_rpc=True)
    db = SupabaseDB()

    with patch("backend.storage.db.get_service_client", return_value=fake_sb):
        result = db.update_user_full_atomic(
            user_id="user-1",
            core_fields={"name": "new-name"},
            profile_fields={"primary_goal": "improve release"},
        )

    assert result is None


def test_get_user_export_data_enforces_limits_and_metadata():
    sessions_rows = [{"id": f"s-{i}"} for i in range(101)]
    chat_rows = [{"id": f"c-{i}", "role": "user", "content": "x"} for i in range(201)]
    summaries_rows = [{"id": f"a-{i}", "session_id": f"s-{i}"} for i in range(101)]
    fake_sb = _FakeSupabase(
        sessions_rows=sessions_rows,
        chat_rows=chat_rows,
        summaries_rows=summaries_rows,
    )
    db = SupabaseDB()

    with patch("backend.storage.db.get_service_client", return_value=fake_sb):
        with patch.object(db, "get_user", return_value={"id": "user-1"}):
            with patch.object(db, "get_user_profile", return_value={"user_id": "user-1"}):
                with patch.object(
                    db,
                    "get_user_analysis_history",
                    return_value=[{"metrics": [{"id": f"m-{i}"}]} for i in range(501)],
                ):
                    result = db.get_user_export_data("user-1", sessions_limit=100, chat_messages_limit=200)

    assert result is not None
    assert result["metadata"]["truncated"] is True
    assert result["metadata"]["limits"] == {
        "sessions": 100,
        "chat_messages": 200,
        "analysis_summaries": 100,
        "metrics": 500,
    }
    assert result["metadata"]["counts"]["sessions_returned"] == 100
    assert result["metadata"]["counts"]["chat_messages_returned"] == 200
    assert result["metadata"]["counts"]["analysis_summaries_returned"] == 100
    assert result["metadata"]["counts"]["metrics_returned"] == 500


def test_profile_endpoint_uses_atomic_update_path():
    app.dependency_overrides[get_authenticated_user] = lambda: AuthenticatedUser(user_id="user-1")
    try:
        with patch(
            "backend.routers.user.db.update_user_full_atomic",
            return_value={"user": {"id": "user-1"}, "profile": {}},
        ) as update_user_full_atomic:
            with patch(
                "backend.routers.user.db.get_user",
                return_value={"id": "user-1", "name": "Coach B", "username": "coachb"},
            ):
                with patch(
                    "backend.routers.user.db.get_user_profile",
                    return_value={"user_id": "user-1", "primary_goal": "consistency"},
                ):
                    resp = client.put(
                        "/api/user/profile",
                        json={
                            "name": "Coach B",
                            "username": "coachb",
                            "primary_goal": "consistency",
                        },
                    )
                    assert resp.status_code == 200
                    update_user_full_atomic.assert_called_once()
    finally:
        app.dependency_overrides.clear()
