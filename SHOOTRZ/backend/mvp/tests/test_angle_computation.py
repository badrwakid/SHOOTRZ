"""
Unit tests for angle computation.

Tests joint_angle() function with known inputs and edge cases.
"""

import pytest
import numpy as np
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from metrics.biomechanics import joint_angle


class TestJointAngle:
    """Test joint angle computation."""
    
    def test_right_angle(self):
        """Test 90-degree angle (perpendicular vectors)."""
        point_a = np.array([1.0, 0.0, 0.0])
        point_b = np.array([0.0, 0.0, 0.0])
        point_c = np.array([0.0, 1.0, 0.0])
        
        angle = joint_angle(point_a, point_b, point_c)
        assert abs(angle - 90.0) < 0.1, f"Expected 90°, got {angle}°"
    
    def test_straight_line(self):
        """Test 180-degree angle (straight line)."""
        point_a = np.array([-1.0, 0.0, 0.0])
        point_b = np.array([0.0, 0.0, 0.0])
        point_c = np.array([1.0, 0.0, 0.0])
        
        angle = joint_angle(point_a, point_b, point_c)
        assert abs(angle - 180.0) < 0.1, f"Expected 180°, got {angle}°"
    
    def test_acute_angle(self):
        """Test 45-degree angle."""
        point_a = np.array([1.0, 0.0, 0.0])
        point_b = np.array([0.0, 0.0, 0.0])
        point_c = np.array([1.0, 1.0, 0.0])
        
        angle = joint_angle(point_a, point_b, point_c)
        assert abs(angle - 45.0) < 1.0, f"Expected ~45°, got {angle}°"
    
    def test_zero_length_vector(self):
        """Test edge case with zero-length vector."""
        point_a = np.array([0.0, 0.0, 0.0])
        point_b = np.array([0.0, 0.0, 0.0])
        point_c = np.array([1.0, 0.0, 0.0])
        
        angle = joint_angle(point_a, point_b, point_c)
        assert angle == 0.0, "Zero-length vector should return 0°"
    
    def test_angle_range(self):
        """Test that angles are always in [0, 180] range."""
        # Random test cases
        for _ in range(100):
            point_a = np.random.randn(3)
            point_b = np.random.randn(3)
            point_c = np.random.randn(3)
            
            angle = joint_angle(point_a, point_b, point_c)
            assert 0 <= angle <= 180, f"Angle {angle}° outside valid range"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])


