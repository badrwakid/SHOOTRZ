"""
Inference package init.

Exposes key modules for import via absolute paths to avoid relative import issues
when loaded from different contexts (e.g., FastAPI routers).
"""

from inference.phase_detector import PhaseDetector, ShootingPhase  # noqa: F401
from inference.motion_analyzer import MotionSignals  # noqa: F401

