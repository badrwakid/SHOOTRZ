#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def _collect_overalls(group_dir: Path) -> list[float]:
    values = []
    for run_dir in sorted(group_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        summary_path = run_dir / "confidence_summary.json"
        if not summary_path.exists():
            continue
        data = json.loads(summary_path.read_text(encoding="utf-8"))
        values.append(float(data.get("overall", 0.0)))
    return values


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--good-light-dir", type=Path, required=True)
    parser.add_argument("--low-light-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=Path("backend/outputs/low_light_comparison.json"))
    args = parser.parse_args()

    good = _collect_overalls(args.good_light_dir)
    low = _collect_overalls(args.low_light_dir)
    if not good or not low:
        raise SystemExit("Need at least one confidence_summary.json in each group")

    good_mean = statistics.fmean(good)
    low_mean = statistics.fmean(low)
    report = {
        "good_light": {
            "n": len(good),
            "mean": round(good_mean, 6),
            "std": round(statistics.pstdev(good), 6) if len(good) > 1 else 0.0,
        },
        "low_light": {
            "n": len(low),
            "mean": round(low_mean, 6),
            "std": round(statistics.pstdev(low), 6) if len(low) > 1 else 0.0,
        },
        "accuracy_drop_pct": round(((good_mean - low_mean) / good_mean) * 100, 2),
        "low_light_accuracy_pct": round(low_mean * 100, 2),
    }
    args.out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
