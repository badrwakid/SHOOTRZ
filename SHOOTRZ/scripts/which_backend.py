"""
Print which backend.main Python would load. Run from SHOOTRZ repo root:

  cd D:\\Users\\Badr\\Grad\\SHOOTRZ
  python scripts/which_backend.py

Expect: version 0.2.0, api_build_id present, file ending in ...\\SHOOTRZ\\backend\\main.py
If version is 0.1.0 or ImportError, your cwd or PYTHONPATH is wrong.
"""
from __future__ import annotations

import sys


def main() -> None:
    try:
        import backend.main as m
    except Exception as e:
        print("FAILED to import backend.main:", e)
        print("cwd should be the SHOOTRZ folder that contains the `backend` package.")
        sys.exit(1)
    print("backend.main.__file__:", getattr(m, "__file__", "?"))
    print("backend.main.__version__:", getattr(m, "__version__", "?"))
    print("API_BUILD_ID:", getattr(m, "API_BUILD_ID", "(missing — old main.py on disk?)"))


if __name__ == "__main__":
    main()
