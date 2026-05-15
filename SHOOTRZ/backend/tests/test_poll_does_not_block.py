"""Regression guard for the 2026-04-23 "AxiosError: timeout of 30000ms exceeded"
bug on ``GET /api/mvp/result/{jobId}``.

Root cause was that :meth:`MVPJobService._process_video_job_async` ran the
post-pipeline work (Gemini enrichment + Supabase persist) INLINE on the
FastAPI event loop. Each of those calls is a synchronous HTTP request that
blocks for 2-30 seconds; while they ran, every concurrent poll timed out.

This test sends an analysis request and then hammers ``/mvp/result/<job>``
using a FastAPI ``TestClient`` (single event loop). If any call returns
slower than ``MAX_POLL_S`` or the status never reaches a terminal state,
the event loop is still being blocked somewhere.

We use a fake pipeline to avoid the 10-15s real MediaPipe run — the goal
is to prove the **framework** doesn't block polls, not to re-benchmark
the pipeline itself.
"""
from __future__ import annotations

import asyncio
import statistics
import time
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


MAX_POLL_S = 1.0  # Every poll must return in under 1 second.


def _fake_pipeline_result(
    video_path: str,
    shooting_side: str,
    save_overlay: bool,
    _skill_level: str = "intermediate",
) -> Dict[str, Any]:
    """Picklable stand-in for ``_run_pipeline_sync`` that simulates a 3s job."""
    time.sleep(3.0)
    return {
        "run_id": "test-run-0001",
        "status": "completed",
        "overall_score": 72,
        "feedback_summary": "stub",
        "feedback_bullets": ["a", "b"],
        "score_components": [],
        "metrics": [],
        "phases": [],
        "shot_window": {},
        "events": {},
        "shooting_side": shooting_side,
        "video_metadata": {},
        "quality_warnings": [],
        "output_dir": "/tmp/fake_run",
        "diagnostics": {},
        "phase_timings_seconds": {},
        "peak_memory_mb": None,
        "pose_overall_confidence": 0.8,
        "low_light": False,
        "ball_trajectory_length": 0,
        "processing_time_seconds": 3.0,
    }


def _slow_sync_enrich(*_a, **_kw) -> None:
    """Simulate the Gemini SDK: 6s blocking HTTP call.

    Pre-fix, this would block the event loop for the full 6s and every poll
    during that window would stall. Post-fix, we offload it via
    ``asyncio.to_thread`` so polls stay responsive.
    """
    time.sleep(6.0)


def _slow_sync_supabase(*_a, **_kw) -> None:
    time.sleep(2.0)


@pytest.mark.anyio
@pytest.mark.asyncio
async def test_poll_never_blocks_on_enrichment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Polls must stay fast while the post-pipeline sync work is running."""
    # Patch BEFORE importing the app so lifespan / executor pick up the stubs.
    from backend.services import mvp_job_service as svc_mod

    monkeypatch.setattr(svc_mod, "_run_pipeline_sync", _fake_pipeline_result)
    monkeypatch.setattr(
        svc_mod.MVPJobService, "_build_completed_payload",
        lambda self, job_id, result: {
            "run_id": result.get("run_id", "r"),
            "status": "completed",
            "overall_score": 72,
            "feedback_summary": "stub",
            "feedback_bullets": [],
            "score_components": [],
            "metrics": [],
            "phases": [],
            "shot_window": {},
            "events": {},
            "angles_data": {"frames": [], "timestamps": [], "elbow": [], "knee": [], "wrist": []},
            "artifacts": {},
            "key_frame_images": {},
            "shooting_side": "right",
            "video_metadata": {},
            "quality_warnings": [],
            "diagnostics": {},
        },
    )
    monkeypatch.setattr(svc_mod.MVPJobService, "_maybe_build_overlay", lambda *a, **kw: None)
    monkeypatch.setattr(svc_mod.MVPJobService, "_enrich_with_gemini", _slow_sync_enrich)
    monkeypatch.setattr(svc_mod.MVPJobService, "_save_to_supabase", _slow_sync_supabase)

    from backend.main import app

    # Use a tiny fake upload so preflight passes.
    import cv2
    import numpy as np
    import tempfile

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.close()
    writer = cv2.VideoWriter(tmp.name, cv2.VideoWriter_fourcc(*"mp4v"), 30, (320, 240))
    for _ in range(60):
        writer.write(np.zeros((240, 320, 3), dtype=np.uint8))
    writer.release()

    with TestClient(app) as client:
        with open(tmp.name, "rb") as fh:
            resp = client.post(
                "/mvp/analyze",
                files={"file": ("clip.mp4", fh, "video/mp4")},
                params={"shooting_side": "right"},
            )
        if resp.status_code == 429:
            pytest.skip("Another test left the semaphore locked")
        assert resp.status_code == 200, resp.text
        job_id = resp.json()["job_id"]

        latencies: List[float] = []
        final_status: str | None = None
        start = time.perf_counter()
        # Keep polling for up to 25s (3s pipeline + 6s enrich + 2s supabase + safety).
        while time.perf_counter() - start < 25.0:
            t0 = time.perf_counter()
            r = client.get(f"/mvp/result/{job_id}")
            elapsed = time.perf_counter() - t0
            latencies.append(elapsed)
            assert r.status_code == 200
            status = r.json().get("status")
            if status in {"completed", "completed_low_quality", "failed"}:
                final_status = status
                # Poll a few more times to catch any blocking during the
                # fire-and-forget enrichment task.
                for _ in range(10):
                    t_after = time.perf_counter()
                    r2 = client.get(f"/mvp/result/{job_id}")
                    latencies.append(time.perf_counter() - t_after)
                    assert r2.status_code == 200
                    await asyncio.sleep(0.3)
                break
            await asyncio.sleep(0.2)

    assert final_status == "completed", f"final_status={final_status}, polls={len(latencies)}"
    worst = max(latencies)
    p95 = sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)]
    # Most polls should be <100ms; the worst case must not exceed 1s.
    assert worst < MAX_POLL_S, (
        f"Worst poll took {worst:.2f}s (>{MAX_POLL_S}s). Event loop is blocking. "
        f"polls={len(latencies)} p50={statistics.median(latencies):.3f}s p95={p95:.3f}s"
    )
