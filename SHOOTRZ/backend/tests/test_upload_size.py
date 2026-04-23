"""Test that /mvp/analyze enforces the SHOOTRZ_MAX_UPLOAD_MB file-size cap.

Design notes
------------
- Uses a module-scoped TestClient fixture (same pattern as test_concurrency_smoke.py)
  so the FastAPI lifespan / ProcessPool is not started during pytest collection.
- monkeypatch.setenv alone would not work because _MAX_UPLOAD_BYTES is computed at
  import time in the original plan. We instead use approach (a) from the audit notes:
  _max_upload_bytes() is a per-request helper that reads the env var on every call,
  so monkeypatch.setenv takes effect without needing importlib.reload.
- We only send two requests — well under the 30/minute rate limit — so we don't
  need to set SHOOTRZ_DISABLE_RATE_LIMIT (but we set it anyway to match the
  established pattern and be future-proof).
"""
from __future__ import annotations

import io
import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


@pytest.fixture(scope="module")
def test_client():
    """Stand up a TestClient against the real FastAPI app.

    Defers import to avoid eagerly spinning up the ProcessPool during
    pytest collection (same rationale as test_concurrency_smoke.py).
    """
    os.environ["SHOOTRZ_DISABLE_RATE_LIMIT"] = "1"
    from backend.main import app  # noqa: WPS433

    with TestClient(app) as client:
        yield client


def test_upload_rejects_oversized_file(test_client, monkeypatch):
    """A file that exceeds the cap must return HTTP 413."""
    monkeypatch.setenv("SHOOTRZ_MAX_UPLOAD_MB", "10")
    # 11 MB of zeros — 1 MB over the 10 MB cap.
    big_fake_video = io.BytesIO(b"\x00" * (11 * 1024 * 1024))
    resp = test_client.post(
        "/mvp/analyze",
        files={"file": ("big.mp4", big_fake_video, "video/mp4")},
        params={"shooting_side": "auto"},
    )
    assert resp.status_code == 413, (
        f"Expected 413 for oversized file, got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert "10" in body.get("detail", ""), (
        f"Detail should mention the MB limit, got: {body.get('detail')}"
    )


def test_upload_accepts_undersized_file_reaches_preflight(test_client, monkeypatch):
    """A file under the cap must NOT be rejected with 413.

    We send 1 MB of zeros — valid size but not a real video, so preflight
    will reject with 400 ('Video file could not be opened' or similar).
    This proves the cap does not false-positive on small files.
    """
    monkeypatch.setenv("SHOOTRZ_MAX_UPLOAD_MB", "10")
    small_fake_video = io.BytesIO(b"\x00" * (1 * 1024 * 1024))
    resp = test_client.post(
        "/mvp/analyze",
        files={"file": ("small.mp4", small_fake_video, "video/mp4")},
        params={"shooting_side": "auto"},
    )
    # Must reach preflight (400) rather than be blocked by the size cap (413).
    assert resp.status_code == 400, (
        f"Expected 400 (preflight reject), got {resp.status_code}: {resp.text}"
    )
    assert resp.status_code != 413, "Size cap must not false-positive on a 1 MB file"
