#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def aggregate(outputs_dir: Path) -> dict:
    files = sorted(outputs_dir.glob("*/confidence_summary.json"))
    if not files:
        raise SystemExit(f"No confidence_summary.json files found under {outputs_dir}")

    overalls = []
    per_joint_runs = []
    per_run = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        run_id = f.parent.name
        overall = float(data.get("overall", 0.0))
        overalls.append(overall)
        per_joint = data.get("per_joint", {}) or {}
        per_joint_runs.append(per_joint)
        per_run.append(
            {
                "run_id": run_id,
                "overall": overall,
                "total_frames": data.get("total_frames"),
            }
        )

    def stats(values: list[float]) -> dict:
        if not values:
            return {"n": 0, "mean": None, "std": None, "min": None, "max": None}
        return {
            "n": len(values),
            "mean": round(statistics.fmean(values), 6),
            "std": round(statistics.pstdev(values), 6) if len(values) > 1 else 0.0,
            "min": round(min(values), 6),
            "max": round(max(values), 6),
        }

    all_joint_names = sorted({k for item in per_joint_runs for k in item.keys()})
    per_joint_stats = {}
    for name in all_joint_names:
        vals = [float(run[name]) for run in per_joint_runs if name in run]
        per_joint_stats[name] = stats(vals)

    return {
        "overall": stats(overalls),
        "per_joint": per_joint_stats,
        "per_run": per_run,
        "n_distinct_videos": len({r["run_id"] for r in per_run}),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs-dir", type=Path, default=Path("backend/outputs"))
    parser.add_argument("--out", type=Path, default=Path("backend/outputs/pose_accuracy_stats.json"))
    args = parser.parse_args()

    result = aggregate(args.outputs_dir)
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
