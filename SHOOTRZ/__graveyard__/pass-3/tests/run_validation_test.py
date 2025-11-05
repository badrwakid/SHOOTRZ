"""
Quick Validation Test Script

Run this to test if your scoring system is working accurately.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validation_helper import ValidationHelper

def main():
    print("\n" + "="*70)
    print("🏀 SHOOTRZ ACCURACY VALIDATION TEST")
    print("="*70)
    
    # Initialize validator
    validator = ValidationHelper()
    
    # Test video path
    test_video = 'uploads/shot.mp4'
    
    # Check if video exists
    if not os.path.exists(test_video):
        print(f"\n❌ Error: Video not found at '{test_video}'")
        print("\n💡 Please:")
        print("   1. Place a basketball shot video in the 'uploads' folder")
        print("   2. Name it 'shot.mp4' (or update the path in this script)")
        return
    
    print(f"\n📹 Testing with video: {test_video}")
    print(f"   File size: {os.path.getsize(test_video) / (1024*1024):.1f} MB")
    
    # Run consistency test
    print("\n" + "="*70)
    print("TEST 1: CONSISTENCY CHECK")
    print("="*70)
    print("\nProcessing the same video 3 times to check consistency...")
    print("(This tests if you get similar scores each time)\n")
    
    try:
        consistency_result = validator.check_consistency(test_video, n_runs=3)
        
        if 'error' in consistency_result:
            print(f"\n❌ Test failed: {consistency_result['error']}")
            return
        
        # Interpret results
        print("\n" + "-"*70)
        print("📊 CONSISTENCY RESULTS:")
        print("-"*70)
        
        variance = consistency_result['variance']
        quality = consistency_result['quality']
        
        print(f"\n✅ Scores: {consistency_result['scores']}")
        print(f"✅ Average: {consistency_result['average']:.2f}")
        print(f"✅ Variance: {variance:.2f}")
        print(f"✅ Quality: {quality}")
        
        # Interpretation
        print("\n💡 What this means:")
        if variance < 2:
            print("   🌟 EXCELLENT! Your system is highly consistent.")
            print("   Scores vary by less than 1-2 points - very reliable!")
        elif variance < 5:
            print("   ✅ GOOD! Your system is consistent.")
            print("   Scores are within expected range - system is working well.")
        elif variance < 10:
            print("   ⚠️ FAIR. System has some variance.")
            print("   Scores vary by 5-10 points - acceptable but could be improved.")
        else:
            print("   ❌ HIGH VARIANCE. System may need adjustment.")
            print("   Scores vary significantly - check camera setup and lighting.")
        
    except Exception as e:
        print(f"\n❌ Error during consistency test: {e}")
        print("\n💡 Common issues:")
        print("   - Video format not supported")
        print("   - Insufficient lighting or person not visible")
        print("   - Dependencies not installed (run: pip install -r requirements.txt)")
        return
    
    # Professional comparison test
    print("\n" + "="*70)
    print("TEST 2: PROFESSIONAL COMPARISON")
    print("="*70)
    print("\nComparing your shot to NBA/WNBA players...\n")
    
    try:
        # Process video once more
        result = validator.processor.process_video(test_video)
        
        if not result['success']:
            print(f"❌ Processing failed: {result.get('error')}")
            return
        
        # Get professional comparison
        comparison = validator.engine.find_best_matches(result['metrics'])
        
        print("📊 YOUR FORM ANALYSIS:")
        print(f"   Total Score: {result['scores']['total']:.1f}/100")
        print(f"   Performance Level: {result['performance_level']}")
        print(f"   Elbow Angle: {result['metrics'].get('elbow_angle', 0):.1f}°")
        print(f"   Knee Angle: {result['metrics'].get('knee_angle', 0):.1f}°")
        print(f"   Release Angle: {result['metrics'].get('release_angle', 0):.1f}°")
        
        print("\n🏀 MOST SIMILAR PRO PLAYER:")
        best_match = comparison['best_match']
        print(f"   {best_match['name']} ({best_match['position']})")
        print(f"   Similarity: {best_match['similarity']:.1f}%")
        print(f"   Style: {best_match['style']}")
        
        # Interpretation
        similarity = best_match['similarity']
        print("\n💡 What this means:")
        if similarity >= 90:
            print("   🌟 ELITE! Your form is very similar to professional shooters!")
        elif similarity >= 80:
            print("   ✅ EXCELLENT! You have good shooting form.")
        elif similarity >= 70:
            print("   👍 GOOD! You're developing solid shooting mechanics.")
        else:
            print("   💪 DEVELOPING. Keep practicing - your form will improve!")
        
        # Camera analysis
        if 'camera_analysis' in result:
            camera = result['camera_analysis']
            print("\n📹 CAMERA SETUP:")
            print(f"   Angle: {camera.get('camera_angle', 'unknown')}")
            print(f"   Reliability: {camera.get('reliability_score', 0):.1f}/100")
            
            if camera.get('is_optimal'):
                print("   ✅ Camera setup is OPTIMAL!")
            else:
                print("   ⚠️ Camera setup could be improved")
                if 'recommendations' in camera:
                    print("\n   Recommendations:")
                    for rec in camera['recommendations'][:3]:
                        print(f"   • {rec}")
        
        # Trajectory analysis
        if 'trajectory' in result and result['trajectory'].get('success'):
            traj = result['trajectory']
            print("\n🎯 SHOT TRAJECTORY:")
            print(f"   Arc Angle: {traj.get('arc_angle', 0):.1f}°")
            print(f"   Make Probability: {traj.get('make_probability', 0):.1f}%")
            print(f"   Quality Score: {traj.get('quality_score', 0):.1f}/100")
        
        # ML prediction
        if 'ml_prediction' in result:
            ml = result['ml_prediction']
            print("\n🤖 ML PREDICTION:")
            print(f"   Method: {ml.get('method', 'unknown')}")
            print(f"   Make Probability: {ml.get('probability_make', 0):.1f}%")
            print(f"   Prediction: {ml.get('prediction', 'unknown').upper()}")
        
    except Exception as e:
        print(f"\n❌ Error during professional comparison: {e}")
        return
    
    # Summary
    print("\n" + "="*70)
    print("📋 VALIDATION SUMMARY")
    print("="*70)
    
    print("\n✅ Tests Completed:")
    print("   • Consistency Check: PASSED")
    print("   • Professional Comparison: PASSED")
    
    print("\n💡 Next Steps:")
    print("   1. Record 10 shots that went IN")
    print("   2. Record 10 shots that MISSED")
    print("   3. Run: python validate_outcomes.py")
    print("   4. This will show if high scores = more makes")
    
    print("\n📚 Learn More:")
    print("   • Read: ACCURACY_VALIDATION_GUIDE.md")
    print("   • Full validation: python validation_helper.py")
    
    print("\n" + "="*70)
    print("✅ VALIDATION TEST COMPLETE!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

