"""
Inference package init.

Re-exports for `from backend.inference import ...` when the app runs as package
`backend` (e.g. uvicorn backend.main:app). Use relative imports here — top-level
`inference` is not on sys.path in that layout.
"""

from .phase_detector import PhaseDetector, ShootingPhase  # noqa: F401
from .motion_analyzer import MotionSignals  # noqa: F401

