"""
Test all backend Python files can import successfully
"""

import sys

files_to_test = [
    # Core backend (already tested 1-10, but including for completeness)
    ('app', 'Flask app'),
    ('video_processor', 'VideoProcessor'),
    ('angle_calculator', 'AngleAnalyzer'),
    ('pose_detector', 'PoseDetector'),
    ('tip_generator', 'generate_tips'),
    ('privacy', 'PrivacyManager'),
    ('evaluator', 'PerformanceEvaluator'),
    ('professional_benchmarks', 'PROFESSIONAL_PLAYERS'),
    ('comparison_engine', 'ComparisonEngine'),
    ('scoring_system', 'EnhancedScoringSystem'),
    
    # Advanced AI (11-20)
    ('enhanced_video_processor', 'EnhancedVideoProcessor'),
    ('ball_detector', 'BallDetector'),
    ('trajectory_analyzer', 'TrajectoryAnalyzer'),
    ('kalman_filter', 'KeypointKalmanFilter'),
    ('temporal_smoother', 'TemporalSmoother'),
    ('camera_analyzer', 'CameraAnalyzer'),
    ('ml_predictor', 'ShotPredictor'),
    ('ml_model_trainer', 'MLModelTrainer'),
    ('data_collector', 'DataCollector'),
    ('phase_detector', 'PhaseDetector'),
    
    # New accuracy components (21-28)
    ('motion_based_phase_detector', 'MotionBasedPhaseDetector'),
    ('precise_measurement_system', 'PreciseMeasurementSystem'),
    ('shooting_motion_validator', 'ShootingMotionValidator'),
    ('accurate_video_processor', 'AccurateVideoProcessor'),
    ('research_config', 'SIMPLIFIED_IDEAL_VALUES'),
    ('progress_analyzer', 'ProgressAnalyzer'),
    ('session_analyzer', 'SessionAnalyzer'),
    
    # Support (29-30)
    ('advanced_metrics', 'AdvancedMetricsCalculator'),
    ('hand_detector', 'HandDetector'),
]

def test_all():
    print("\n" + "="*80)
    print("🔍 TESTING ALL BACKEND IMPORTS")
    print("="*80 + "\n")
    
    passed = []
    failed = []
    
    for module_name, class_name in files_to_test:
        try:
            # Try to import
            module = __import__(module_name, fromlist=[class_name])
            
            # Try to get the class/function
            getattr(module, class_name)
            
            print(f"✅ {module_name}.py")
            passed.append(module_name)
        except Exception as e:
            print(f"❌ {module_name}.py: {str(e)[:60]}")
            failed.append((module_name, str(e)))
    
    # Summary
    print("\n" + "="*80)
    print(f"📊 IMPORT TEST RESULTS")
    print("="*80)
    print(f"\n✅ Passed: {len(passed)}/{len(files_to_test)}")
    print(f"❌ Failed: {len(failed)}/{len(files_to_test)}")
    
    if failed:
        print(f"\n❌ Files with import errors:")
        for module, error in failed:
            print(f"   • {module}.py: {error[:80]}")
    
    print("\n" + "="*80 + "\n")
    
    return passed, failed

if __name__ == "__main__":
    passed, failed = test_all()
    
    if not failed:
        print("✅ ALL FILES IMPORT SUCCESSFULLY!\n")
        sys.exit(0)
    else:
        print(f"⚠️ {len(failed)} files need fixing\n")
        sys.exit(1)

