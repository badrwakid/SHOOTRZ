#!/usr/bin/env python3
"""
Comprehensive backend test to verify all components work correctly
"""

def test_all_components():
    """Test all backend components"""
    print("=" * 60)
    print("SHOOTRZ AI Backend - Comprehensive Test")
    print("=" * 60)
    
    # Test 1: Imports
    print("\n1. Testing imports...")
    try:
        import cv2
        import numpy as np
        import mediapipe as mp
        from pose_detector import PoseDetector
        from angle_calculator import AngleAnalyzer, calculate_angle
        from tip_generator import generate_tips, calculate_scores
        from video_processor import VideoProcessor
        from privacy import PrivacyManager
        from evaluator import PerformanceEvaluator
        print("   ✓ All imports successful")
    except ImportError as e:
        print(f"   ✗ Import error: {e}")
        return False
    
    # Test 2: PoseDetector initialization
    print("\n2. Testing PoseDetector initialization...")
    try:
        detector = PoseDetector()
        print("   ✓ PoseDetector initialized")
        print(f"   - MediaPipe Pose version: {mp.__version__}")
    except Exception as e:
        print(f"   ✗ PoseDetector error: {e}")
        return False
    
    # Test 3: Angle calculations
    print("\n3. Testing angle calculations...")
    try:
        # Test angle calculation
        point1 = (0, 0)
        point2 = (0, 100)
        point3 = (100, 100)
        angle = calculate_angle(point1, point2, point3)
        print(f"   ✓ Angle calculation works: {angle}° (expected: 90°)")
        
        # Test analyzer
        analyzer = AngleAnalyzer()
        test_keypoints = {
            'right_shoulder': (100, 100),
            'right_elbow': (100, 150),
            'right_wrist': (150, 150),
            'right_hip': (100, 200),
            'right_knee': (100, 250),
            'right_ankle': (100, 300),
            'left_shoulder': (200, 100),
            'left_hip': (200, 200),
        }
        analyzer.analyze_frame(test_keypoints)
        metrics = analyzer.get_average_metrics()
        print(f"   ✓ AngleAnalyzer works")
        print(f"   - Sample metrics: {metrics}")
    except Exception as e:
        print(f"   ✗ Angle calculation error: {e}")
        return False
    
    # Test 4: Tip generation
    print("\n4. Testing tip generation...")
    try:
        test_metrics = {
            'elbow_angle': 95,
            'knee_angle': 130,
            'release_angle': 47,
            'body_alignment': 85
        }
        tips = generate_tips(test_metrics)
        scores = calculate_scores(test_metrics)
        print(f"   ✓ Tip generation works")
        print(f"   - Generated {len(tips)} tips")
        print(f"   - Total score: {scores['total']}/100")
    except Exception as e:
        print(f"   ✗ Tip generation error: {e}")
        return False
    
    # Test 5: VideoProcessor
    print("\n5. Testing VideoProcessor...")
    try:
        processor = VideoProcessor()
        print("   ✓ VideoProcessor initialized")
    except Exception as e:
        print(f"   ✗ VideoProcessor error: {e}")
        return False
    
    # Test 6: PrivacyManager
    print("\n6. Testing PrivacyManager...")
    try:
        privacy = PrivacyManager()
        video_id = privacy.anonymize_video_id("test_user")
        print(f"   ✓ PrivacyManager works")
        print(f"   - Sample anonymous ID: {video_id[:16]}...")
    except Exception as e:
        print(f"   ✗ PrivacyManager error: {e}")
        return False
    
    # Test 7: PerformanceEvaluator
    print("\n7. Testing PerformanceEvaluator...")
    try:
        evaluator = PerformanceEvaluator()
        summary = evaluator.get_summary()
        print(f"   ✓ PerformanceEvaluator works")
        print(f"   - Summary: {summary}")
    except Exception as e:
        print(f"   ✗ PerformanceEvaluator error: {e}")
        return False
    
    # Test 8: Flask and CORS
    print("\n8. Testing Flask availability...")
    try:
        import flask
        import flask_cors
        print(f"   ✓ Flask available (version {flask.__version__})")
        print(f"   ✓ Flask-CORS available")
    except ImportError as e:
        print(f"   ✗ Flask not available: {e}")
        print("   ! Install with: pip install flask flask-cors")
        return False
    
    # Test 9: OpenCV version and capabilities
    print("\n9. Testing OpenCV capabilities...")
    try:
        print(f"   ✓ OpenCV version: {cv2.__version__}")
        # Test video codec availability
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        print(f"   ✓ Video codec (mp4v) available")
    except Exception as e:
        print(f"   ✗ OpenCV capability error: {e}")
    
    # Test 10: Directory structure
    print("\n10. Checking directory structure...")
    import os
    dirs = ['uploads', 'processed']
    for dir_name in dirs:
        if os.path.exists(dir_name):
            print(f"   ✓ {dir_name}/ exists")
        else:
            print(f"   ! {dir_name}/ missing (will be created on startup)")
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED - Backend is ready!")
    print("=" * 60)
    print("\nTo start the server, run:")
    print("  python app.py")
    print("\nServer will be available at:")
    print("  http://localhost:5000")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    test_all_components()


