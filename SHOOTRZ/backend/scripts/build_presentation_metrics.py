#!/usr/bin/env python3
from __future__ import annotations

import json
import statistics
from pathlib import Path


OUT_ROOT = Path("backend/outputs")


def _load(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _safe_mean(values):
    return round(statistics.fmean(values), 3) if values else None


def _safe_std(values):
    if not values:
        return None
    return round(statistics.pstdev(values), 3) if len(values) > 1 else 0.0


def main() -> int:
    run_times = []
    peak_mems = []
    overall_scores = []
    pose_overall = []
    for meta_file in OUT_ROOT.glob("*/run_metadata.json"):
        meta = _load(meta_file, {})
        if meta.get("processing_time_seconds") is not None:
            run_times.append(float(meta["processing_time_seconds"]))
        if meta.get("peak_memory_mb") is not None:
            peak_mems.append(float(meta["peak_memory_mb"]))
        if meta.get("overall_score") is not None:
            overall_scores.append(float(meta["overall_score"]))
        if meta.get("pose_overall_confidence") is not None:
            pose_overall.append(float(meta["pose_overall_confidence"]))

    pose_stats = _load(OUT_ROOT / "pose_accuracy_stats.json", {"overall": {}})
    frame_stats = _load(OUT_ROOT / "frame_selection_metrics.json", {})
    low_light = _load(OUT_ROOT / "low_light_comparison.json", {})
    load_50 = _load(OUT_ROOT / "load" / "load_report_50u.json", {})
    load_100 = _load(OUT_ROOT / "load" / "load_report_100u.json", {})
    tests = _load(Path("test_results.json"), {"summary": {}})

    summary = tests.get("summary", {})
    tests_passed = int(summary.get("passed", 0))
    tests_total = int(summary.get("total", 0))

    pose_overall_stats = pose_stats.get("overall", {})
    pose_accuracy_pct = round(float(pose_overall_stats.get("mean", _safe_mean(pose_overall) or 0.0)) * 100, 2)
    pose_accuracy_std_pct = round(float(pose_overall_stats.get("std", _safe_std(pose_overall) or 0.0)) * 100, 2)

    report = {
        "elbow_release_weight_pct": 35,
        "knee_bend_weight_pct": 30,
        "follow_through_weight_pct": 20,
        "balance_weight_pct": 15,
        "pose_accuracy_pct": pose_accuracy_pct,
        "pose_accuracy_std_pct": pose_accuracy_std_pct,
        "pose_accuracy_n_runs": pose_overall_stats.get("n", len(pose_overall)),
        "processing_time_avg_s": _safe_mean(run_times),
        "processing_time_std_s": _safe_std(run_times),
        "processing_time_n_runs": len(run_times),
        "peak_memory_mb": round(max(peak_mems), 1) if peak_mems else None,
        "peak_memory_avg_mb": round(statistics.fmean(peak_mems), 1) if peak_mems else None,
        "avg_overall_score": round(statistics.fmean(overall_scores), 1) if overall_scores else None,
        "test_pass_rate_pct": round(tests_passed / tests_total * 100, 1) if tests_total else None,
        "tests_passed": tests_passed,
        "tests_total": tests_total,
        "load_50u_queue_p50_ms": load_50.get("queue_p50_ms"),
        "load_50u_queue_p95_ms": load_50.get("queue_p95_ms"),
        "load_50u_e2e_p50_ms": load_50.get("end_to_end_p50_ms", 0.0) or 0.0,
        "load_50u_e2e_p95_ms": load_50.get("end_to_end_p95_ms", 0.0) or 0.0,
        "load_50u_error_rate_pct": load_50.get("error_rate_pct"),
        "load_100u_queue_p50_ms": load_100.get("queue_p50_ms"),
        "load_100u_queue_p95_ms": load_100.get("queue_p95_ms"),
        "load_100u_e2e_p50_ms": load_100.get("end_to_end_p50_ms", 0.0) or 0.0,
        "load_100u_e2e_p95_ms": load_100.get("end_to_end_p95_ms", 0.0) or 0.0,
        "load_100u_error_rate_pct": load_100.get("error_rate_pct"),
        "low_light_accuracy_pct": low_light.get("low_light_accuracy_pct"),
        "low_light_accuracy_drop_pct": low_light.get("accuracy_drop_pct"),
        "frame_selection_accuracy_pct": frame_stats.get("frame_selection_accuracy_pct"),
        "frame_deviation_error_mean": frame_stats.get("frame_deviation_error", {}).get("mean"),
        "frame_deviation_error_std": frame_stats.get("frame_deviation_error", {}).get("std"),
    }

    out_path = OUT_ROOT / "presentation_metrics.json"
    out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
