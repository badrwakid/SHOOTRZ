#!/usr/bin/env python3
"""Check a running SHOOTRZ FastAPI instance for analysis-history-related routes.

Usage (from repo root, backend running):
  python backend/scripts/verify_api_routes.py
  python backend/scripts/verify_api_routes.py http://192.168.1.43:8000

Reads GET {base}/health and prints has_*_route flags (requires current main.py).
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

DEFAULT_BASE = "http://127.0.0.1:8000"


def main() -> int:
    base = (sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BASE).rstrip("/")
    url = f"{base}/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as e:
        print(f"ERROR: could not reach {url}: {e}", file=sys.stderr)
        return 1
    keys = (
        "has_analysis_history_route",
        "has_analysis_complete_route",
        "has_delete_account_route",
        "version",
    )
    out = {k: data.get(k) for k in keys}
    print(json.dumps(out, indent=2))
    if not data.get("has_analysis_history_route"):
        print(
            "\nIf has_analysis_history_route is false or missing, this server is an old "
            "build or not backend.main:app — restart: "
            "python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
