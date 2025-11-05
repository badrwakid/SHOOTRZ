"""
Test the new accurate measurement system

This tests:
1. Motion-based phase detection
2. Precise frame measurements
3. Research-based scoring
4. Shooting motion validation
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from accurate_video_processor import AccurateVideoProcessor

def test_accurate_system():
    print("\n" + "="*80)
    print("🎯 TESTING ACCURATE VIDEO PROCESSOR")
    print("="*80)
    print("\nThis uses:")
    print("  ✓ Motion-based phase detection (not time-based)")
    print("  ✓ Precise measurements at exact moments")
    print("  ✓ Research-validated ideal values")
    print("  ✓ Shooting motion validation")
    print()
    
    test_video = 'uploads/shot.mp4'
    
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        return
    
    # Initialize processor
    print("Initializing AccurateVideoProcessor...")
    processor = AccurateVideoProcessor(
        use_ball_detection=False,  # Skip ball for speed in testing
        use_ml_prediction=True
    )
    
    # Process video
    print(f"\n{'='*80}")
    result = processor.process_video(test_video)
    print("="*80)
    
    if not result['success']:
        print(f"\n❌ Processing failed: {result.get('error')}")
        return
    
    # Display results
    print("\n" + "="*80)
    print("📊 ACCURATE MEASUREMENT RESULTS")
    print("="*80)
    
    # Validation results
    validation = result.get('validation', {})
    print(f"\n✓ Shooting Motion Validation:")
    print(f"   Valid: {validation.get('is_valid', False)}")
    print(f"   Confidence: {validation.get('confidence', 0):.1f}%")
    if not validation.get('is_valid'):
        print(f"   Reason: {validation.get('reason', 'Unknown')}")
    
    # Phase detection
    phase_detection = result.get('phase_detection', {})
    if phase_detection.get('success'):
        key_frames = phase_detection.get('key_frames', {})
        print(f"\n✓ Motion-Based Phase Detection:")
        print(f"   Dip Bottom: Frame {key_frames.get('dip_bottom', 'N/A')}")
        print(f"   Release Point: Frame {key_frames.get('release', 'N/A')}")
        print(f"   Valid Motion: {phase_detection.get('is_valid_shooting_motion', False)}")
    
    # Measurements
    metrics = result['metrics']
    detailed = result.get('detailed_measurements', {})
    
    print(f"\n✓ Precise Measurements:")
    print(f"   ┌─────────────────────────┬───────────┬──────────────┬────────────┐")
    print(f"   │ Measurement             │  Value    │  Ideal       │  Status    │")
    print(f"   ├─────────────────────────┼───────────┼──────────────┼────────────┤")
    
    # Elbow at release
    elbow_release = detailed.get('elbow_at_release', metrics.get('elbow_angle', 0))
    elbow_ideal = 165.0
    elbow_status = "✅" if 155 <= elbow_release <= 175 else "⚠️"
    print(f"   │ Elbow at Release        │ {elbow_release:>6.1f}°  │  160-170°    │    {elbow_status}      │")
    
    # Knee at release
    knee_release = detailed.get('knee_at_release', metrics.get('knee_angle', 0))
    knee_ideal = 167.5
    knee_status = "✅" if 160 <= knee_release <= 175 else "⚠️"
    print(f"   │ Knee at Release         │ {knee_release:>6.1f}°  │  160-175°    │    {knee_status}      │")
    
    # Release trajectory
    release_angle = metrics.get('release_angle', 0)
    release_status = "✅" if 48 <= release_angle <= 55 else "⚠️"
    print(f"   │ Release Trajectory      │ {release_angle:>6.1f}°  │   48-55°     │    {release_status}      │")
    
    # Body alignment
    alignment = metrics.get('body_alignment', 0)
    alignment_status = "✅" if alignment >= 70 else "⚠️"
    print(f"   │ Body Alignment          │ {alignment:>6.1f}   │   90-100     │    {alignment_status}      │")
    
    print(f"   └─────────────────────────┴───────────┴──────────────┴────────────┘")
    
    # Scores
    scores = result['scores']
    print(f"\n✓ Research-Based Scores:")
    print(f"   Elbow: {scores['elbow']}/25")
    print(f"   Knee: {scores['balance']}/25")
    print(f"   Release: {scores['release']}/25")
    print(f"   Alignment: {scores['alignment']}/25")
    print(f"   ───────────────────")
    print(f"   TOTAL: {scores['total']}/100")
    print(f"   Level: {result['performance_level']}")
    
    # Research comparison
    if 'research_comparison' in result:
        print(f"\n✓ Research Comparison:")
        comparison = result['research_comparison']
        
        for metric, data in comparison.items():
            if isinstance(data, dict):
                status = "✅" if data.get('in_ideal_range') else "⚠️"
                print(f"   {metric}: {data.get('measured', 0):.1f}° vs {data.get('ideal', 0):.1f}° "
                      f"({data.get('assessment', 'Unknown')}) {status}")
    
    # Camera setup
    if 'camera_analysis' in result and result['camera_analysis']:
        camera = result['camera_analysis']
        print(f"\n✓ Camera Setup:")
        print(f"   Angle: {camera.get('camera_angle', 'unknown')}")
        print(f"   Reliability: {camera.get('reliability_score', 0):.1f}/100")
        print(f"   Optimal: {'Yes ✅' if camera.get('is_optimal') else 'No ⚠️'}")
    
    # Final assessment
    print("\n" + "="*80)
    print("📋 ACCURACY ASSESSMENT")
    print("="*80)
    
    # Check if measurements are in research ranges
    in_range_count = 0
    total_checks = 0
    
    if 160 <= knee_release <= 175:
        print(f"✅ Knee at release ({knee_release:.1f}°) is in research range (160-175°)")
        in_range_count += 1
    else:
        print(f"⚠️ Knee at release ({knee_release:.1f}°) is outside research range (160-175°)")
    total_checks += 1
    
    if 48 <= release_angle <= 55:
        print(f"✅ Release angle ({release_angle:.1f}°) is in research range (48-55°)")
        in_range_count += 1
    else:
        print(f"⚠️ Release angle ({release_angle:.1f}°) is outside research range (48-55°)")
    total_checks += 1
    
    if elbow_release > 120:  # If measured at release
        if 160 <= elbow_release <= 170:
            print(f"✅ Elbow at release ({elbow_release:.1f}°) is in research range (160-170°)")
            in_range_count += 1
        else:
            print(f"⚠️ Elbow at release ({elbow_release:.1f}°) is outside research range (160-170°)")
        total_checks += 1
    
    accuracy_percent = (in_range_count / total_checks * 100) if total_checks > 0 else 0
    
    print(f"\n📊 Measurement Accuracy: {in_range_count}/{total_checks} in research ranges ({accuracy_percent:.0f}%)")
    
    if accuracy_percent >= 75:
        print("✅ System is measuring accurately!")
    elif accuracy_percent >= 50:
        print("⚠️ Some measurements may need refinement")
    else:
        print("❌ System may have accuracy issues")
    
    print("\n" + "="*80)
    print("✅ ACCURATE SYSTEM TEST COMPLETE")
    print("="*80 + "\n")
    
    # Save results
    import json
    with open('accurate_system_results.json', 'w') as f:
        # Convert to serializable format
        serializable_result = {
            'metrics': result['metrics'],
            'scores': result['scores'],
            'validation': result.get('validation'),
            'phase_detection': {
                'key_frames': result.get('phase_detection', {}).get('key_frames', {})
            },
            'research_comparison': result.get('research_comparison', {})
        }
        json.dump(serializable_result, f, indent=2, default=str)
    
    print("📁 Results saved to: accurate_system_results.json\n")

if __name__ == "__main__":
    test_accurate_system()

