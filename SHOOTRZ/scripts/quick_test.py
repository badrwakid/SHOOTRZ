"""
Quick functionality test after setup.

Tests core functionality without requiring a video upload.
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from backend.metrics.biomechanics import (
	compute_elbow_angle,
	compute_knee_angle,
	compute_forearm_verticality,
)
from backend.inference.pose_2d import MediaPipePoseDetector
import numpy as np


def test_biomechanics():
	"""Test biomechanics calculations."""
	print("🧪 Testing biomechanics calculations...")
	
	# Create test joint positions
	shoulder = np.array([0.5, 0.5, 0.0])
	elbow = np.array([0.6, 0.7, 0.0])
	wrist = np.array([0.7, 0.9, 0.0])
	
	hip = np.array([0.5, 0.8, 0.0])
	knee = np.array([0.5, 1.0, 0.0])
	ankle = np.array([0.5, 1.2, 0.0])
	
	# Test elbow angle
	elbow_result = compute_elbow_angle(shoulder, elbow, wrist)
	assert "angle_degrees" in elbow_result
	assert elbow_result["angle_degrees"] > 0
	print(f"  ✓ Elbow angle calculation: {elbow_result['angle_degrees']:.1f}°")
	
	# Test knee angle
	knee_result = compute_knee_angle(hip, knee, ankle)
	assert "angle_degrees" in knee_result
	assert knee_result["angle_degrees"] > 0
	print(f"  ✓ Knee angle calculation: {knee_result['angle_degrees']:.1f}°")
	
	# Test forearm verticality
	forearm_result = compute_forearm_verticality(elbow, wrist)
	assert "angle_degrees" in forearm_result
	print(f"  ✓ Forearm verticality calculation: {forearm_result['angle_degrees']:.1f}°")
	
	print("  ✅ All biomechanics tests passed!\n")


def test_pose_detector():
	"""Test MediaPipe pose detector initialization."""
	print("🧪 Testing MediaPipe pose detector...")
	
	try:
		detector = MediaPipePoseDetector()
		print("  ✓ MediaPipe Pose detector initialized")
		detector.close()
		print("  ✅ Pose detector test passed!\n")
	except Exception as e:
		print(f"  ✗ Pose detector failed: {e}\n")
		raise


def test_imports():
	"""Test that all critical modules can be imported."""
	print("🧪 Testing module imports...")
	
	modules = [
		"backend.processing.pipeline",
		"backend.metrics.calculator",
		"backend.feedback.rules",
		"backend.inference.phase_detector",
	]
	
	for module_name in modules:
		try:
			__import__(module_name)
			print(f"  ✓ {module_name}")
		except ImportError as e:
			print(f"  ✗ {module_name}: {e}")
			raise
	
	print("  ✅ All imports successful!\n")


def main():
	"""Run all quick tests."""
	print("\n" + "=" * 60)
	print("SHOOTRZ Quick Functionality Test")
	print("=" * 60 + "\n")
	
	try:
		test_imports()
		test_biomechanics()
		test_pose_detector()
		
		print("=" * 60)
		print("✅ All quick tests passed!")
		print("=" * 60)
		print("\n🚀 System is ready to use!")
		print("\nNext: Start the backend and try uploading a video.")
		return 0
	except Exception as e:
		print("=" * 60)
		print(f"❌ Test failed: {e}")
		print("=" * 60)
		return 1


if __name__ == "__main__":
	sys.exit(main())



