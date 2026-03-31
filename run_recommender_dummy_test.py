#!/usr/bin/env python3
"""
Run the recommender dummy test without cd'ing into backend.

Usage (from repo root, or any folder that contains this file):
  python run_recommender_dummy_test.py

Or:
  python SHOOTRZ/run_recommender_dummy_test.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _find_backend() -> Path | None:
    here = Path(__file__).resolve().parent
    candidates = [
        here / "SHOOTRZ" / "backend",
        here / "backend",
    ]
    for b in candidates:
        if (b / "recommender" / "run_dummy_test.py").is_file():
            return b
    return None


def main() -> int:
    backend = _find_backend()
    if backend is None:
        print(
            "Could not find backend/recommender/run_dummy_test.py.\n"
            "Run this script from the repo folder that contains SHOOTRZ/backend "
            "or SHOOTRZ/SHOOTRZ/backend.",
            file=sys.stderr,
        )
        return 1
    return subprocess.call(
        [sys.executable, "-m", "recommender.run_dummy_test"],
        cwd=str(backend),
    )


if __name__ == "__main__":
    raise SystemExit(main())
