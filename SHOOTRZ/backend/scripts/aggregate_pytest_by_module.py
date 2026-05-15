"""Group pytest-json-report results into the presentation's test modules.

Reads ``outputs/_pytest_report.json`` and maps every ``nodeid`` into one of
the seven buckets the deck uses (Authentication, Video & AI Engine, etc).
Emits ``outputs/presentation_test_breakdown.json``.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
REPORT = BACKEND_ROOT / "outputs" / "_pytest_report.json"
OUT = BACKEND_ROOT / "outputs" / "presentation_test_breakdown.json"


# Map (substring -> module bucket). First match wins.
BUCKETS: list[tuple[str, str]] = [
    ("test_analysis_complete", "Video & AI Engine"),
    ("test_api_contracts", "Video & AI Engine"),
    ("test_concurrency_smoke", "Performance"),
    ("test_poll_does_not_block", "Performance"),
    ("test_pipeline_streaming", "Performance"),
    ("test_real_clip_pose", "Video & AI Engine"),
    ("test_ai_score_override", "Feedback & Chatbot"),
    ("test_shot_score", "Video & AI Engine"),
    ("test_metric_frame_selection", "Video & AI Engine"),
    ("test_metric_scoring", "Video & AI Engine"),
    ("test_shot_detection", "Video & AI Engine"),
    ("test_angle_computation", "Video & AI Engine"),
    ("test_integration", "Video & AI Engine"),
    ("test_biomechanics", "Video & AI Engine"),
    ("test_phase_detector", "Video & AI Engine"),
    ("test_frame_selection", "Video & AI Engine"),
    ("test_job_store", "Data & Dashboard"),
]


def _bucket(nodeid: str) -> str:
    lower = nodeid.lower()
    for key, bucket in BUCKETS:
        if key in lower:
            return bucket
    return "Other"


def main() -> int:
    if not REPORT.exists():
        raise SystemExit(f"Missing {REPORT} (run pytest --json-report first)")
    data = json.loads(REPORT.read_text(encoding="utf-8"))
    counts: dict[str, dict[str, int]] = defaultdict(lambda: {"total": 0, "passed": 0, "failed": 0, "skipped": 0})
    for t in data.get("tests") or []:
        nodeid = t.get("nodeid", "")
        outcome = t.get("outcome", "unknown")
        b = _bucket(nodeid)
        counts[b]["total"] += 1
        if outcome == "passed":
            counts[b]["passed"] += 1
        elif outcome == "failed":
            counts[b]["failed"] += 1
        elif outcome in {"skipped", "xfailed"}:
            counts[b]["skipped"] += 1

    summary = data.get("summary") or {}
    out = {
        "summary": {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "duration_s": round(float(data.get("duration") or 0.0), 2),
            "pass_rate_pct": round(
                summary.get("passed", 0) * 100 / max(summary.get("total", 1), 1), 1
            ),
        },
        "by_module": dict(counts),
    }
    OUT.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    print(f"\nWrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
