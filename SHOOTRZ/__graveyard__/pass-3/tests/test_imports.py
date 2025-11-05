#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

def test_imports():
    """Test all required imports"""
    try:
        print("Testing imports...")
        
        # Test basic imports
        import cv2
        print("✓ OpenCV imported successfully")
        
        import numpy as np
        print("✓ NumPy imported successfully")
        
        import mediapipe as mp
        print("✓ MediaPipe imported successfully")
        
        # Test our custom modules
        from pose_detector import PoseDetector
        print("✓ PoseDetector imported successfully")
        
        from angle_calculator import AngleAnalyzer
        print("✓ AngleAnalyzer imported successfully")
        
        from tip_generator import generate_tips, calculate_scores
        print("✓ Tip generator functions imported successfully")
        
        from video_processor import VideoProcessor
        print("✓ VideoProcessor imported successfully")
        
        from privacy import PrivacyManager
        print("✓ PrivacyManager imported successfully")
        
        from evaluator import PerformanceEvaluator
        print("✓ PerformanceEvaluator imported successfully")
        
        print("\n✅ All imports successful! The backend is ready.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_imports()


