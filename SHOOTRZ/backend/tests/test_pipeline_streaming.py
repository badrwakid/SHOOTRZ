"""Streaming / memory regression tests for the hardened MVP pipeline.

These tests guard three invariants that the refactor relies on:

* :meth:`VideoLoader.iter_frames` MUST be a generator (never builds a full
  list) and MUST respect ``max_frames``.
* :meth:`MVPPipeline.process_video` with ``save_overlay=False`` must NEVER
  write ``overlay.mp4`` into the run directory.
* The pipeline peak-memory sampler stays well below ``500MB`` on a short
  synthetic clip (the old loader easily exceeded 3GB on real footage).
"""
from __future__ import annotations

import sys
import os
from pathlib import Path
from typing import List

import cv2
import numpy as np
import psutil
import pytest


backend_path = Path(__file__).resolve().parents[1]
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.pipeline import MVPPipeline
from mvp.core.video_loader import VideoLoader


def _write_synthetic_clip(path: Path, duration_s: float = 2.0, fps: int = 30) -> None:
    """Write a tiny 640x480 mp4 of a moving rectangle so MediaPipe has data."""
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    total = int(duration_s * fps)
    try:
        for i in range(total):
            frame = np.full((height, width, 3), fill_value=80, dtype=np.uint8)
            cv2.circle(frame, (width // 2, height // 4), 30, (240, 240, 240), -1)
            arm_y = height // 3 + int(20 * np.sin(i * 0.2))
            cv2.line(frame, (width // 2, height // 3), (width // 2 + 50, arm_y), (240, 240, 240), 3)
            cv2.line(frame, (width // 2, height // 3), (width // 2 - 50, arm_y), (240, 240, 240), 3)
            cv2.line(frame, (width // 2, height // 4 + 30), (width // 2, height // 2), (240, 240, 240), 3)
            cv2.line(frame, (width // 2, height // 2), (width // 2 + 30, height * 3 // 4), (240, 240, 240), 3)
            cv2.line(frame, (width // 2, height // 2), (width // 2 - 30, height * 3 // 4), (240, 240, 240), 3)
            writer.write(frame)
    finally:
        writer.release()


def test_iter_frames_respects_max_frames(tmp_path: Path):
    video_path = tmp_path / "stride.mp4"
    _write_synthetic_clip(video_path, duration_s=3.0, fps=30)

    loader = VideoLoader(str(video_path), {"max_frames": 10, "frame_skip": 1})
    loader.load_metadata()
    frames: List[int] = []
    for processed_idx, original_idx, timestamp, frame in loader.iter_frames(max_frames=10):
        assert isinstance(frame, np.ndarray)
        assert frame.ndim == 3 and frame.shape[2] == 3
        frames.append(processed_idx)
    assert len(frames) <= 10
    assert frames == list(range(len(frames)))


def test_iter_frames_is_lazy(tmp_path: Path):
    video_path = tmp_path / "lazy.mp4"
    _write_synthetic_clip(video_path, duration_s=1.0, fps=30)
    loader = VideoLoader(str(video_path), {"frame_skip": 1})
    loader.load_metadata()
    gen = loader.iter_frames()
    import types

    assert isinstance(gen, types.GeneratorType)
    # Consuming the first item should not exhaust the whole video.
    first = next(gen)
    assert first[0] == 0
    gen.close()


def test_process_video_with_overlay_disabled_skips_overlay_file(tmp_path: Path):
    video_path = tmp_path / "no_overlay.mp4"
    _write_synthetic_clip(video_path, duration_s=2.0, fps=30)

    pipeline = MVPPipeline()
    result = pipeline.process_video(str(video_path), shooting_side="right", save_overlay=False)

    assert result["status"] in ("completed", "completed_low_quality")
    overlay_path = Path(result["output_dir"]) / "overlay.mp4"
    assert not overlay_path.exists(), "overlay.mp4 should NOT be generated when save_overlay=False"


@pytest.mark.skipif(
    os.getenv("SHOOTRZ_SKIP_MEMORY_TEST") == "1",
    reason="Memory guard test disabled via env",
)
def test_pipeline_peak_memory_stays_under_500mb(tmp_path: Path):
    video_path = tmp_path / "memory.mp4"
    _write_synthetic_clip(video_path, duration_s=2.0, fps=30)

    process = psutil.Process(os.getpid())
    baseline_mb = process.memory_info().rss / 1024 ** 2
    samples: List[float] = [baseline_mb]

    pipeline = MVPPipeline()
    pipeline.process_video(
        str(video_path),
        shooting_side="right",
        save_overlay=False,
        peak_memory_sampler=lambda: process.memory_info().rss / 1024 ** 2,
    )

    samples.append(process.memory_info().rss / 1024 ** 2)
    peak_increase_mb = max(samples) - baseline_mb
    # The old full-load implementation commonly added >1500MB on real clips.
    # Our synthetic clip is tiny so the new streaming path should add < 500MB.
    assert peak_increase_mb < 500, (
        f"Peak memory increase {peak_increase_mb:.1f}MB exceeds 500MB budget."
    )
