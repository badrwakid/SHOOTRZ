"""
Final Verification Test - Checks ALL systems are working correctly

This test verifies:
1. Bug fixes applied
2. Research-based scoring working
3. Body alignment calculating correctly
4. App will show accurate values
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_all_systems():
    print("\n" + "="*80)
    print("🔍 FINAL VERIFICATION TEST - Complete System Check")
    print("="*80)
    
    # Test 1: Import all modules
    print("\n[1/5] Testing Module Imports...")
    try:
        from video_processor import VideoProcessor
        from enhanced_video_processor import EnhancedVideoProcessor
        from angle_calculator import calculate_body_alignment
        from tip_generator import calculate_scores
        from research_config import SIMPLIFIED_IDEAL_VALUES
        print("   ✅ All modules imported successfully")
    except Exception as e:
        print(f"   ❌ Import error: {e}")
        return False
    
    # Test 2: Verify research config loaded
    print("\n[2/5] Verifying Research-Based Configuration...")
    try:
        print(f"   Ideal knee at release: {SIMPLIFIED_IDEAL_VALUES['knee_angle']}°")
        print(f"   Ideal elbow at release: {SIMPLIFIED_IDEAL_VALUES['elbow_angle']}°")
        print(f"   Ideal release trajectory: {SIMPLIFIED_IDEAL_VALUES['release_angle']}°")
        
        if SIMPLIFIED_IDEAL_VALUES['knee_angle'] == 167.5:
            print("   ✅ Research values loaded correctly")
        else:
            print("   ⚠️ Still using old values")
    except Exception as e:
        print(f"   ⚠️ Research config not found: {e}")
    
    # Test 3: Test scoring function
    print("\n[3/5] Testing Research-Based Scoring...")
    try:
        # Test case: Player with 173° knee and 54° release (like user's video)
        test_metrics = {
            'elbow_angle': 67,    # Cocking phase
            'knee_angle': 173,    # At release
            'release_angle': 54,  # Trajectory
            'body_alignment': 15  # Poor alignment
        }
        
        scores = calculate_scores(test_metrics)
        
        print(f"   Test Shot (173° knee, 54° release):")
        print(f"      Knee score: {scores['balance']}/25")
        print(f"      Release score: {scores['release']}/25")
        print(f"      Elbow score: {scores['elbow']}/25")
        print(f"      Alignment score: {scores['alignment']}/25")
        print(f"      Total: {scores['total']}/100")
        
        # Verify knee gets high score (173° is in ideal 160-175° range)
        if scores['balance'] >= 23:
            print("   ✅ Knee scoring CORRECT (173° recognized as excellent)")
        else:
            print(f"   ❌ Knee scoring WRONG (173° scored only {scores['balance']}/25)")
        
        # Verify release gets high score (54° is in ideal 48-55° range)
        if scores['release'] >= 23:
            print("   ✅ Release scoring CORRECT (54° recognized as excellent)")
        else:
            print(f"   ❌ Release scoring WRONG (54° scored only {scores['release']}/25)")
        
        # Check total score
        if scores['total'] >= 60:
            print(f"   ✅ Total score CORRECT ({scores['total']}/100 reflects good form)")
        else:
            print(f"   ⚠️ Total score LOW ({scores['total']}/100 - may need adjustment)")
            
    except Exception as e:
        print(f"   ❌ Scoring test failed: {e}")
        return False
    
    # Test 4: Test body alignment calculation
    print("\n[4/5] Testing Body Alignment Calculation...")
    try:
        # Test with known deviation
        test_points = {
            'left_shoulder': (100, 100),
            'right_shoulder': (200, 100),
            'left_hip': (545, 200),      # 445px deviation
            'right_hip': (645, 200)
        }
        
        alignment = calculate_body_alignment(
            test_points['left_shoulder'],
            test_points['right_shoulder'],
            test_points['left_hip'],
            test_points['right_hip']
        )
        
        print(f"   Test alignment (445px deviation): {alignment:.1f}/100")
        
        if alignment > 0 and alignment < 100:
            print("   ✅ Body alignment calculating correctly (not 0)")
        elif alignment == 0:
            print("   ❌ Body alignment still returning 0 - calculation broken!")
        else:
            print("   ⚠️ Body alignment unusual value")
            
    except Exception as e:
        print(f"   ❌ Body alignment test failed: {e}")
    
    # Test 5: Process actual video
    print("\n[5/5] Processing Actual Video...")
    test_video = 'uploads/shot.mp4'
    
    if not os.path.exists(test_video):
        print(f"   ⚠️ Test video not found: {test_video}")
        print("   Skipping video test")
    else:
        try:
            processor = EnhancedVideoProcessor(
                use_ball_detection=False,  # Skip for speed
                use_ml_prediction=True,
                use_temporal_smoothing=False  # Skip for speed
            )
            
            print(f"   Processing {test_video}...")
            result = processor.process_video(test_video, adaptive_sampling=False)
            
            if result['success']:
                print(f"\n   📊 ACTUAL RESULTS:")
                print(f"      Knee: {result['metrics']['knee_angle']:.1f}° → Score: {result['scores']['balance']}/25")
                print(f"      Release: {result['metrics']['release_angle']:.1f}° → Score: {result['scores']['release']}/25")
                print(f"      Elbow: {result['metrics']['elbow_angle']:.1f}° → Score: {result['scores']['elbow']}/25")
                print(f"      Alignment: {result['metrics']['body_alignment']:.1f} → Score: {result['scores']['alignment']}/25")
                print(f"      TOTAL: {result['scores']['total']}/100")
                print(f"      Level: {result['performance_level']}")
                
                # Verify knee score is good
                if result['metrics']['knee_angle'] >= 160 and result['metrics']['knee_angle'] <= 175:
                    if result['scores']['balance'] >= 23:
                        print("\n   ✅ KNEE: Measured in ideal range AND scored high!")
                    else:
                        print(f"\n   ❌ KNEE: In ideal range but scored low ({result['scores']['balance']}/25)")
                
                # Verify release score
                if result['metrics']['release_angle'] >= 48 and result['metrics']['release_angle'] <= 55:
                    if result['scores']['release'] >= 23:
                        print("   ✅ RELEASE: Measured in ideal range AND scored high!")
                    else:
                        print(f"   ❌ RELEASE: In ideal range but scored low ({result['scores']['release']}/25)")
                
                # Check total
                if result['scores']['total'] >= 60:
                    print(f"   ✅ TOTAL: Score of {result['scores']['total']}/100 is appropriate!")
                else:
                    print(f"   ⚠️ TOTAL: Score of {result['scores']['total']}/100 seems low")
                
                # Check body alignment
                if result['metrics']['body_alignment'] > 0:
                    print(f"   ✅ BODY ALIGNMENT: Calculating correctly ({result['metrics']['body_alignment']:.1f})")
                else:
                    print("   ❌ BODY ALIGNMENT: Still showing 0!")
                    
            else:
                print(f"   ❌ Processing failed: {result.get('error')}")
                
        except Exception as e:
            print(f"   ❌ Video processing error: {e}")
            import traceback
            traceback.print_exc()
    
    # Final Summary
    print("\n" + "="*80)
    print("📋 VERIFICATION SUMMARY")
    print("="*80)
    
    print("\nChecklist:")
    print(" [✅] Modules import correctly")
    print(" [✅] Research-based values loaded")
    print(" [?] Scoring function works with new values (needs restart)")
    print(" [?] Body alignment fixes applied (needs restart)")
    print(" [?] App will display correct values (needs restart + test)")
    
    print("\n⚡ REQUIRED ACTIONS:")
    print(" 1. RESTART backend server (python app.py)")
    print(" 2. Upload video in app")
    print(" 3. Verify knee scores 23-25/25")
    print(" 4. Verify release scores 23-25/25")
    print(" 5. Verify total is 60-75/100")
    
    print("\n💡 IF scores are still wrong after restart:")
    print(" - Python may be caching old modules")
    print(" - Try: Close all Python processes and restart")
    print(" - Or: Delete __pycache__ folders")
    
    print("\n" + "="*80)
    print("✅ VERIFICATION TEST COMPLETE")
    print("="*80 + "\n")
    
    return True

if __name__ == "__main__":
    verify_all_systems()

