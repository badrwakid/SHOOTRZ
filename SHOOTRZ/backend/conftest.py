"""Backend-wide pytest bootstrap.

Runs BEFORE any test module is imported so all test suites (``backend/tests``,
``backend/mvp/tests``, ``backend/inference/tests``) share the same environment.

The most important thing we set here is ``SHOOTRZ_POSE_FALLBACK=1``. Without
it, ``MediaPipePoseDetector.__init__`` now raises on environments where
mediapipe cannot initialise; synthetic-video tests would then fail. In
production, ``SHOOTRZ_POSE_FALLBACK`` is never set, so the detector refuses
to emit the (0.5, 0.5) placeholder landmarks that previously produced the
"0 POOR" shot score bug.
"""
from __future__ import annotations

import os

os.environ.setdefault("SHOOTRZ_POSE_FALLBACK", "1")
