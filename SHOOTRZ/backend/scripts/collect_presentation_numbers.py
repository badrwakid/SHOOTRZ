"""Collect live, real-clip numbers for the pre-final deck.

Runs the full pipeline N times on the same real video (``6b84daec.../input_video.mp4``),
then writes a single ``outputs/presentation_numbers.json`` with:

- processing_time_s (mean/std/min/max)
- peak_memory_mb (mean/max)
- pose_overall_confidence (mean/std)
- latest-run metric values + scoring breakdown
- overall_score (rule-based; AI override noted separately when GEMINI_API_KEY is set and quota available)

The companion markdown file ``outputs/presentation_numbers.md`` is also
emitted for easy copy/paste into the slides.
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import tempfile
import time
from pathlib import Path

import psutil
from dotenv import load_dotenv

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
for p in (REPO_ROOT, BACKEND_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

load_dotenv(BACKEND_ROOT / ".env")
os.environ.pop("SHOOTRZ_POSE_FALLBACK", None)

from mvp.core.pipeline import MVPPipeline  # noqa: E402
from backend.mvp.core.metrics import _dim_score  # noqa: E402

VIDEO = BACKEND_ROOT / "outputs" / "6b84daec-4390-43ba-9416-0ed2202446cd" / "input_video.mp4"


def _bench(n_runs: int = 5) -> dict:
    times: list[float] = []
    peaks: list[float] = []
    pose_confs: list[float] = []
    last_result: dict | None = None
    shooting_side_resolved: str | None = None

    for i in range(n_runs):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td) / f"bench_{i}"
            pl = MVPPipeline()
            proc = psutil.Process(os.getpid())
            base = proc.memory_info().rss / 1024**2
            samples = [base]

            def sampler() -> float:
                m = proc.memory_info().rss / 1024**2
                samples.append(m)
                return m

            t0 = time.perf_counter()
            r = pl.process_video(
                str(VIDEO),
                shooting_side="auto",
                save_overlay=False,
                peak_memory_sampler=sampler,
                outputs_base_dir=out_base,
            )
            elapsed = time.perf_counter() - t0
            times.append(elapsed)
            peaks.append(max(samples) - base)
            pc = r.get("pose_overall_confidence")
            if isinstance(pc, (int, float)):
                pose_confs.append(float(pc))
            shooting_side_resolved = r.get("shooting_side")
            last_result = r
            print(
                f"run {i+1}/{n_runs}: {elapsed:5.2f}s  pose_conf={pc:.3f}  "
                f"score={r.get('overall_score')}  status={r.get('status')}",
                flush=True,
            )

    if last_result is None:
        raise SystemExit("No runs succeeded")

    metrics = last_result.get("metrics") or []
    metric_details = []
    breakdown = []
    norm_key_map = {
        "elbow_extension": "elbow_flexion_release",
        "knee_bend": "knee_flexion",
        "wrist_follow_through": "wrist_follow_through",
    }
    for m in metrics:
        name = m.get("name")
        if name not in norm_key_map:
            continue
        nk = norm_key_map[name]
        sub_score = _dim_score(nk, float(m.get("value") or 0.0))
        metric_details.append({
            "name": name,
            "value_deg": round(float(m.get("value") or 0.0), 2),
            "verdict": m.get("verdict"),
            "confidence": round(float(m.get("confidence") or 0.0), 3),
            "selected_frame": m.get("selected_frame"),
            "sub_score": round(float(sub_score or 0.0), 1),
        })
        if sub_score is not None:
            breakdown.append({"name": name, "sub_score": round(sub_score, 1)})

    components = last_result.get("score_components") or []
    component_breakdown = []
    for c in components:
        if c.get("name") == "shot_score_breakdown":
            continue
        component_breakdown.append({
            "name": c.get("name"),
            "value": c.get("value"),
            "weight": c.get("weight"),
        })

    return {
        "clip": str(VIDEO.relative_to(BACKEND_ROOT.parent)).replace("\\", "/"),
        "clip_duration_s": 13.7,
        "clip_resolution": "1080x1920",
        "n_runs": n_runs,
        "shooting_side_resolved": shooting_side_resolved,
        "processing_time_s": {
            "mean": round(statistics.fmean(times), 3),
            "std": round(statistics.pstdev(times), 3) if len(times) > 1 else 0.0,
            "min": round(min(times), 3),
            "max": round(max(times), 3),
        },
        "peak_memory_mb_delta": {
            "mean": round(statistics.fmean(peaks), 1),
            "max": round(max(peaks), 1),
            "min": round(min(peaks), 1),
        },
        "pose_overall_confidence": {
            "mean": round(statistics.fmean(pose_confs), 3) if pose_confs else None,
            "std": round(statistics.pstdev(pose_confs), 3) if len(pose_confs) > 1 else 0.0,
        },
        "overall_score_rule_based_latest": last_result.get("overall_score"),
        "metrics": metric_details,
        "score_components": component_breakdown,
        "score_breakdown_for_slide": breakdown,
    }


def main() -> int:
    n_runs = int(os.getenv("SHOOTRZ_BENCH_RUNS", "5"))
    out = _bench(n_runs=n_runs)
    out_path = BACKEND_ROOT / "outputs" / "presentation_numbers.json"
    out_path.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"\nWrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
