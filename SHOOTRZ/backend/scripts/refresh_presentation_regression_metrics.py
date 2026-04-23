#!/usr/bin/env python3
"""
Re-aggregate ``processing_time_*`` / ``peak_memory_*`` / ``avg_overall_score`` for
``outputs/presentation_metrics.json``.

The original slide numbers (~130s wall time, ~3.3GB RSS) came from a batch of
``run_metadata.json`` files that referenced **local training videos** not
checked into git.  This script uses a **long 720p synthetic clip** as a
stress proxy (side-view--like motion + visible limbs) and writes bench runs
into a disposable directory so ``backend/outputs/*`` is not further polluted.

Usage (from repo)::

  cd backend
  set PYTHONPATH=%REPO_ROOT%;%REPO_ROOT%\\backend
  python scripts/refresh_presentation_regression_metrics.py --n-runs 22

Omitting ``--apply`` only prints the computed JSON patch (dry run).

Use ``--video path/to/file.mp4`` to benchmark a **real** clip (e.g. a saved
``input_video.mp4`` under ``outputs/<run_id>/``) instead of generating a
synthetic stress video.
"""
from __future__ import annotations

import argparse
from typing import Optional
import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

import cv2
import numpy as np
import psutil

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = Path(__file__).resolve().parents[1]
for _p in (REPO_ROOT, BACKEND_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from mvp.core.pipeline import MVPPipeline  # noqa: E402

PRESENTATION_PATH = BACKEND_ROOT / "outputs" / "presentation_metrics.json"


def _write_synthetic_stress_clip(
    path: Path, *, duration_s: float, width: int, height: int, fps: int
) -> None:
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(path), fourcc, float(fps), (width, height))
    n = int(duration_s * fps)
    try:
        for i in range(n):
            frame = np.full((height, width, 3), 80, dtype=np.uint8)
            cv2.circle(frame, (width // 2, height // 4), min(width, height) // 18, (240, 240, 240), -1)
            arm_y = height // 3 + int(0.04 * min(width, height) * np.sin(i * 0.1))
            cv2.line(
                frame,
                (width // 2, height // 3),
                (width // 2 + width // 12, arm_y),
                (240, 240, 240),
                max(2, min(width, height) // 200),
            )
            cv2.line(
                frame,
                (width // 2, height // 3),
                (width // 2 - width // 12, arm_y),
                (240, 240, 240),
                max(2, min(width, height) // 200),
            )
            cv2.line(
                frame,
                (width // 2, height // 4 + 30 * height // 480),
                (width // 2, height // 2),
                (240, 240, 240),
                max(2, min(width, height) // 200),
            )
            cv2.line(
                frame,
                (width // 2, height // 2),
                (width // 2 + width // 20, height * 3 // 4),
                (240, 240, 240),
                max(2, min(width, height) // 200),
            )
            cv2.line(
                frame,
                (width // 2, height // 2),
                (width // 2 - width // 20, height * 3 // 4),
                (240, 240, 240),
                max(2, min(width, height) // 200),
            )
            out.write(frame)
    finally:
        out.release()


def _round3(x: float) -> float:
    return round(float(x), 3)


def _round1(x: float) -> float:
    return round(float(x), 1)


def _probe_video(path: Path) -> dict:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise SystemExit(f"Could not open video: {path}")
    try:
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) or 0
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 0
        fps = float(cap.get(cv2.CAP_PROP_FPS)) or 0.0
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        duration_s = (n / fps) if fps > 0 and n > 0 else 0.0
        return {
            "width": w,
            "height": h,
            "fps": round(fps, 3) if fps else 0.0,
            "frame_count": n,
            "duration_s": round(duration_s, 2),
            "resolution": f"{w}x{h}" if w and h else None,
        }
    finally:
        cap.release()


def run_benchmark(
    *,
    n_runs: int,
    external_video: Optional[Path],
    duration_s: float,
    width: int,
    height: int,
    fps: int,
) -> dict:
    os.environ.pop("SHOOTRZ_ENABLE_BALL", None)

    with tempfile.TemporaryDirectory() as tmp:
        if external_video is not None:
            if not external_video.is_file():
                raise SystemExit(f"Video not found: {external_video}")
            video_path = external_video.resolve()
            probe = _probe_video(video_path)
            is_synth = False
        else:
            video_path = Path(tmp) / "regression_stress.mp4"
            _write_synthetic_stress_clip(video_path, duration_s=duration_s, width=width, height=height, fps=fps)
            probe = {
                "width": width,
                "height": height,
                "fps": float(fps),
                "frame_count": int(duration_s * fps),
                "duration_s": float(duration_s),
                "resolution": f"{width}x{height}",
            }
            is_synth = True

        out_base = Path(tmp) / "bench_out"
        out_base.mkdir(parents=True, exist_ok=True)

        proc = psutil.Process(os.getpid())
        times: list[float] = []
        peaks: list[float] = []
        scores: list[float] = []

        t0_suite = time.perf_counter()
        for _ in range(n_runs):
            pl = MVPPipeline()

            def sampler() -> float:
                return proc.memory_info().rss / 1024**2

            r = pl.process_video(
                str(video_path),
                shooting_side="right",
                save_overlay=False,
                peak_memory_sampler=sampler,
                outputs_base_dir=out_base,
            )
            pt = r.get("processing_time_seconds")
            if pt is not None:
                times.append(float(pt))
            pm = r.get("peak_memory_mb")
            if pm is not None:
                peaks.append(float(pm))
            scores.append(float(r.get("overall_score") or 0.0))
        wall_total_s = time.perf_counter() - t0_suite

    if len(times) != n_runs:
        raise SystemExit(
            f"Expected {n_runs} timing samples, got {len(times)}. "
            "Check pipeline return / early-exit path."
        )
    if not peaks:
        raise SystemExit("No peak_memory_mb samples (all runs low-quality exit?). Use a longer/brighter clip.")

    if is_synth:
        res_note = (
            "720p synthetic stress clip (no real project .mp4 path given); "
            "replaces the historical ~22-run lab batch used for 129.962s / 3435MB baselines."
        )
    else:
        res_note = (
            f"Real file benchmark: {video_path.name}. Not checked into git as stable asset; "
            "path is local to the machine that ran the script."
        )

    return {
        "processing_time_avg_s": _round3(statistics.fmean(times)),
        "processing_time_std_s": _round3(statistics.pstdev(times)) if len(times) > 1 else 0.0,
        "processing_time_n_runs": n_runs,
        "wall_clock_total_s": _round3(wall_total_s),
        "peak_memory_mb": _round1(max(peaks)) if peaks else None,
        "peak_memory_avg_mb": _round1(statistics.fmean(peaks)) if peaks else None,
        "avg_overall_score": _round1(statistics.fmean(scores)) if scores else None,
        "regression_bench_synthetic_720p": is_synth,
        "regression_bench_source_video": str(video_path) if not is_synth else None,
        "regression_bench_video_duration_s": probe.get("duration_s", duration_s),
        "regression_bench_video_resolution": probe.get("resolution") or f"{width}x{height}",
        "regression_bench_video_fps": probe.get("fps", fps) if not is_synth else fps,
        "regression_bench_note": res_note,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--n-runs", type=int, default=22, help="Match legacy processing_time_n_runs when possible.")
    p.add_argument(
        "--video",
        type=Path,
        default=None,
        help="Path to a real .mp4 (e.g. outputs/…/input_video.mp4). Omit to generate synthetic 720p.",
    )
    p.add_argument("--duration", type=float, default=20.0)
    p.add_argument("--width", type=int, default=1280)
    p.add_argument("--height", type=int, default=720)
    p.add_argument("--fps", type=int, default=30)
    p.add_argument(
        "--apply",
        action="store_true",
        help=f"Merge into {PRESENTATION_PATH} (otherwise print JSON only).",
    )
    args = p.parse_args()

    stats = run_benchmark(
        n_runs=args.n_runs,
        external_video=args.video,
        duration_s=args.duration,
        width=args.width,
        height=args.height,
        fps=args.fps,
    )
    if not args.apply:
        print(json.dumps(stats, indent=2))
        return 0

    existing = json.loads(PRESENTATION_PATH.read_text(encoding="utf-8"))
    for k, v in stats.items():
        existing[k] = v
    from datetime import datetime, timezone

    existing["regression_bench_utc"] = datetime.now(timezone.utc).isoformat()
    PRESENTATION_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    print(f"Updated {PRESENTATION_PATH}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
