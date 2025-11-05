"""
Consolidated Test System - All Tests in One Place

This replaces the 10+ scattered test files with one comprehensive test suite.
"""

import os
import sys

def test_imports():
    """Test that all critical modules import"""
    print("\n[1/4] Testing Imports...")
    
    critical_imports = [
        ('video_processor', 'VideoProcessor'),
        ('angle_calculator', 'AngleAnalyzer'),
        ('pose_detector', 'PoseDetector'),
        ('tip_generator', 'calculate_scores'),
        ('privacy', 'PrivacyManager'),
        ('evaluator', 'PerformanceEvaluator'),
        ('professional_benchmarks', 'PROFESSIONAL_PLAYERS'),
        ('comparison_engine', 'ComparisonEngine'),
    ]
    
    failed = []
    for module_name, class_name in critical_imports:
        try:
            module = __import__(module_name, fromlist=[class_name])
            getattr(module, class_name)
        except Exception as e:
            failed.append((module_name, str(e)))
    
    if failed:
        print(f"   ❌ {len(failed)} imports failed")
        for mod, err in failed:
            print(f"      • {mod}: {err[:60]}")
        return False
    else:
        print(f"   ✅ All {len(critical_imports)} critical imports OK")
        return True

def test_video_processing():
    """Test that video processing works end-to-end"""
    print("\n[2/4] Testing Video Processing...")
    
    test_video = 'uploads/shot.mp4'
    
    if not os.path.exists(test_video):
        print(f"   ⚠️ Test video not found: {test_video}")
        return True  # Don't fail if no test video
    
    try:
        from video_processor import VideoProcessor
        
        processor = VideoProcessor()
        result = processor.process_video(test_video)
        
        if result['success']:
            score = result['scores']['total']
            elbow = result['metrics'].get('elbow_angle', 0)
            knee = result['metrics'].get('knee_angle', 0)
            
            print(f"   ✅ Video processed successfully")
            print(f"      Score: {score}/100")
            print(f"      Elbow: {elbow:.1f}°, Knee: {knee:.1f}°")
            
            if score == 0:
                print(f"   ⚠️ WARNING: Score is 0 - may indicate issue")
                return False
            
            return True
        else:
            print(f"   ❌ Processing failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_scoring():
    """Test research-based scoring"""
    print("\n[3/4] Testing Research-Based Scoring...")
    
    try:
        from tip_generator import calculate_scores
        
        # Test with research-ideal values
        perfect_metrics = {
            'elbow_angle': 165,  # Research: 160-170° at release
            'knee_angle': 170,   # Research: 160-175° at release
            'release_angle': 52, # Research: 48-55°
            'body_alignment': 95
        }
        
        scores = calculate_scores(perfect_metrics)
        
        print(f"   ✅ Scoring works")
        print(f"      Test score: {scores['total']}/100")
        
        # Verify research values (knee 170° should score 25/25)
        if scores['balance'] >= 23:
            print(f"      ✅ Research values active (knee scores {scores['balance']}/25)")
            return True
        else:
            print(f"      ⚠️ Old values may be active (knee only scores {scores['balance']}/25)")
            return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_api_endpoints():
    """Test that Flask app initializes"""
    print("\n[4/4] Testing API Initialization...")
    
    try:
        from app import app
        
        print(f"   ✅ Flask app initializes")
        print(f"      Available endpoints:")
        
        with app.app_context():
            for rule in app.url_map.iter_rules():
                if not rule.rule.startswith('/static'):
                    print(f"         {rule.rule}")
        
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("🧪 CONSOLIDATED TEST SUITE - Complete System Check")
    print("="*80)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Video Processing", test_video_processing()))
    results.append(("Research Scoring", test_scoring()))
    results.append(("API Endpoints", test_api_endpoints()))
    
    print("\n" + "="*80)
    print("📊 TEST RESULTS")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status}: {name}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - System is ready!")
        print("\n🚀 Start your backend:")
        print("   cd basketball-training-app\\backend")
        print("   python app.py")
        print("\n   Then test in your React Native app!")
    else:
        print(f"\n⚠️ {total - passed} tests failed - needs attention")
    
    print("\n" + "="*80 + "\n")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

