"""
Test that core system actually WORKS (not just imports)
"""

import os

def test_core_system():
    print("\n" + "="*80)
    print("🧪 CORE FUNCTIONALITY TEST")
    print("="*80 + "\n")
    
    test_video = 'uploads/shot.mp4'
    
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        print("   Please ensure uploads/shot.mp4 exists\n")
        return False
    
    # Test 1: VideoProcessor
    print("[1/5] Testing VideoProcessor...")
    try:
        from video_processor import VideoProcessor
        processor = VideoProcessor()
        result = processor.process_video(test_video)
        
        if result['success']:
            print(f"   ✅ VideoProcessor WORKS")
            print(f"      Score: {result['scores']['total']}/100")
            print(f"      Elbow: {result['metrics'].get('elbow_angle', 0):.1f}°")
            print(f"      Knee: {result['metrics'].get('elbow_angle', 0):.1f}°")
        else:
            print(f"   ❌ VideoProcessor failed: {result.get('error')}")
            return False
    except Exception as e:
        print(f"   ❌ VideoProcessor error: {e}")
        return False
    
    # Test 2: Scoring
    print("\n[2/5] Testing Scoring System...")
    try:
        from tip_generator import calculate_scores
        
        test_metrics = {
            'elbow_angle': 165,
            'knee_angle': 170,
            'release_angle': 52,
            'body_alignment': 85
        }
        
        scores = calculate_scores(test_metrics)
        
        print(f"   ✅ Scoring WORKS")
        print(f"      Test metrics score: {scores['total']}/100")
        
        # Verify research-based scoring (knee 170° should score well)
        if scores['balance'] >= 20:
            print(f"      ✅ Research values applied (knee 170° scores {scores['balance']}/25)")
        else:
            print(f"      ⚠️ May still use old values (knee 170° only scores {scores['balance']}/25)")
            
    except Exception as e:
        print(f"   ❌ Scoring error: {e}")
        return False
    
    # Test 3: Professional Comparison
    print("\n[3/5] Testing Professional Comparison...")
    try:
        from comparison_engine import ComparisonEngine
        
        engine = ComparisonEngine()
        result = engine.find_best_matches(test_metrics)
        
        print(f"   ✅ Comparison WORKS")
        print(f"      Best match: {result['best_match']['name']}")
        print(f"      Similarity: {result['best_match']['similarity']:.1f}%")
    except Exception as e:
        print(f"   ❌ Comparison error: {e}")
        return False
    
    # Test 4: Privacy Manager
    print("\n[4/5] Testing Privacy Manager...")
    try:
        from privacy import PrivacyManager
        
        pm = PrivacyManager()
        status = pm.get_deletion_queue_status()
        
        print(f"   ✅ Privacy WORKS")
        print(f"      Queue size: {status.get('queue_size', 0)}")
    except Exception as e:
        print(f"   ❌ Privacy error: {e}")
        return False
    
    # Test 5: Evaluator
    print("\n[5/5] Testing Performance Evaluator...")
    try:
        from evaluator import PerformanceEvaluator
        
        evaluator = PerformanceEvaluator()
        summary = evaluator.get_summary()
        
        print(f"   ✅ Evaluator WORKS")
        print(f"      Total evaluations: {summary.get('total_evaluations', 0)}")
    except Exception as e:
        print(f"   ❌ Evaluator error: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ ALL CORE SYSTEMS FUNCTIONAL!")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    success = test_core_system()
    
    if success:
        print("🎉 Your backend is WORKING and READY!\n")
        print("Next steps:")
        print("  1. Start backend: python app.py")
        print("  2. Test in your app")
        print("  3. Verify scores are NOT 0\n")
    else:
        print("⚠️ Some systems need attention\n")

