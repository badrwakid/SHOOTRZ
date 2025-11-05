"""
Test script to verify all AI components are installed and working
"""

def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        import flask
        print("✅ Flask")
    except ImportError as e:
        print(f"❌ Flask: {e}")
    
    try:
        import cv2
        print("✅ OpenCV")
    except ImportError as e:
        print(f"❌ OpenCV: {e}")
    
    try:
        import mediapipe
        print(f"✅ MediaPipe (version {mediapipe.__version__})")
    except ImportError as e:
        print(f"❌ MediaPipe: {e}")
    
    try:
        import numpy as np
        print(f"✅ NumPy (version {np.__version__})")
    except ImportError as e:
        print(f"❌ NumPy: {e}")
    
    try:
        from ultralytics import YOLO
        print("✅ Ultralytics (YOLOv8)")
    except ImportError as e:
        print(f"❌ Ultralytics: {e}")
    
    try:
        import lightgbm as lgb
        print(f"✅ LightGBM (version {lgb.__version__})")
    except ImportError as e:
        print(f"❌ LightGBM: {e}")
    
    try:
        from filterpy.kalman import KalmanFilter
        print("✅ FilterPy")
    except ImportError as e:
        print(f"❌ FilterPy: {e}")
    
    try:
        import sklearn
        print(f"✅ Scikit-learn (version {sklearn.__version__})")
    except ImportError as e:
        print(f"❌ Scikit-learn: {e}")
    
    try:
        import scipy
        print(f"✅ SciPy (version {scipy.__version__})")
    except ImportError as e:
        print(f"❌ SciPy: {e}")
    
    try:
        import joblib
        print(f"✅ Joblib")
    except ImportError as e:
        print(f"❌ Joblib: {e}")
    
    print("\n" + "="*50)


def test_components():
    """Test that custom components can be imported"""
    print("\nTesting custom components...")
    
    try:
        from ball_detector import BallDetector, BallTracker
        print("✅ Ball Detection & Tracking")
    except Exception as e:
        print(f"❌ Ball Detection: {e}")
    
    try:
        from trajectory_analyzer import TrajectoryAnalyzer
        print("✅ Trajectory Analyzer")
    except Exception as e:
        print(f"❌ Trajectory Analyzer: {e}")
    
    try:
        from kalman_filter import KeypointKalmanFilter, PoseKalmanFilter
        print("✅ Kalman Filtering")
    except Exception as e:
        print(f"❌ Kalman Filtering: {e}")
    
    try:
        from temporal_smoother import TemporalSmoother, AngleSmoother
        print("✅ Temporal Smoothing")
    except Exception as e:
        print(f"❌ Temporal Smoothing: {e}")
    
    try:
        from camera_analyzer import CameraAnalyzer
        print("✅ Camera Analyzer")
    except Exception as e:
        print(f"❌ Camera Analyzer: {e}")
    
    try:
        from data_collector import DataCollector
        print("✅ Data Collector")
    except Exception as e:
        print(f"❌ Data Collector: {e}")
    
    try:
        from ml_model_trainer import MLModelTrainer
        print("✅ ML Model Trainer")
    except Exception as e:
        print(f"❌ ML Model Trainer: {e}")
    
    try:
        from ml_predictor import ShotPredictor, EnsemblePredictor
        print("✅ ML Predictor")
    except Exception as e:
        print(f"❌ ML Predictor: {e}")
    
    try:
        from enhanced_video_processor import EnhancedVideoProcessor
        print("✅ Enhanced Video Processor")
    except Exception as e:
        print(f"❌ Enhanced Video Processor: {e}")
    
    try:
        from database.progress_db import ProgressDatabase
        print("✅ Progress Database")
    except Exception as e:
        print(f"❌ Progress Database: {e}")
    
    try:
        from progress_analyzer import ProgressAnalyzer
        print("✅ Progress Analyzer")
    except Exception as e:
        print(f"❌ Progress Analyzer: {e}")
    
    try:
        from session_analyzer import SessionAnalyzer
        print("✅ Session Analyzer")
    except Exception as e:
        print(f"❌ Session Analyzer: {e}")
    
    print("\n" + "="*50)


def test_initialization():
    """Test that components can be initialized"""
    print("\nTesting component initialization...")
    
    try:
        from enhanced_video_processor import EnhancedVideoProcessor
        processor = EnhancedVideoProcessor(
            use_ball_detection=False,  # Skip YOLOv8 download for now
            use_ml_prediction=False,
            use_temporal_smoothing=True
        )
        print("✅ Enhanced Video Processor initialized")
    except Exception as e:
        print(f"❌ Enhanced Video Processor init: {e}")
    
    try:
        from database.progress_db import ProgressDatabase
        db = ProgressDatabase()
        print("✅ Progress Database initialized")
    except Exception as e:
        print(f"❌ Progress Database init: {e}")
    
    try:
        from session_analyzer import SessionAnalyzer
        session = SessionAnalyzer()
        print("✅ Session Analyzer initialized")
    except Exception as e:
        print(f"❌ Session Analyzer init: {e}")
    
    print("\n" + "="*50)


def main():
    print("\n🏀 SHOOTRZ Advanced AI - Installation Test\n")
    print("="*50)
    
    test_imports()
    test_components()
    test_initialization()
    
    print("\n✅ Installation test complete!")
    print("\nNext steps:")
    print("1. Test with a sample video: python test_sample_video.py")
    print("2. Read QUICK_START_AI.md for usage examples")
    print("3. Review AI_IMPLEMENTATION_SUMMARY.md for features")
    print("\n🚀 Ready to analyze basketball shots!\n")


if __name__ == "__main__":
    main()

