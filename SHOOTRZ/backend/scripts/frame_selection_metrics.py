#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

TOLERANCE_FRAMES = 5


def compute(outputs_dir: Path) -> dict:
    logs = sorted(outputs_dir.glob("*/frame_selection_log.json"))
    if not logs:
        raise SystemExit(f"No frame_selection_log.json files found under {outputs_dir}")

    deviations = []
    eligible = []
    per_run = []

    for log_path in logs:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        run_id = log_path.parent.name
        heuristics_n = int(data.get("heuristics_n", 0))
        dev = int(data.get("heuristic_deviation", 0))
        row = {
            "run_id": run_id,
            "chosen": data.get("chosen_release"),
            "consensus": data.get("consensus_frame"),
            "deviation": dev,
            "heuristics_n": heuristics_n,
            "within_tolerance": dev <= TOLERANCE_FRAMES,
            "eligible": heuristics_n >= 2,
        }
        per_run.append(row)
        if heuristics_n >= 2:
            deviations.append(dev)
            eligible.append(row)

    if not deviations:
        raise SystemExit("No eligible runs with heuristics_n >= 2")

    within = sum(1 for d in deviations if d <= TOLERANCE_FRAMES)
    return {
        "tolerance_frames": TOLERANCE_FRAMES,
        "n_runs_total": len(per_run),
        "n_runs_eligible": len(eligible),
        "frame_selection_accuracy_pct": round((within / len(deviations)) * 100, 2),
        "frame_deviation_error": {
            "mean": round(statistics.fmean(deviations), 3),
            "std": round(statistics.pstdev(deviations), 3) if len(deviations) > 1 else 0.0,
            "min": min(deviations),
            "max": max(deviations),
        },
        "per_run": per_run,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs-dir", type=Path, default=Path("backend/outputs"))
    parser.add_argument("--out", type=Path, default=Path("backend/outputs/frame_selection_metrics.json"))
    args = parser.parse_args()

    result = compute(args.outputs_dir)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
