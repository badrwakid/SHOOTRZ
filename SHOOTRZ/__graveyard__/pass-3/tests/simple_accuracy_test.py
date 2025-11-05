"""
Simple test to verify the system works - step by step debugging
"""

from accurate_video_processor import AccurateVideoProcessor
import json

def main():
    print("\n🎯 SIMPLE ACCURACY TEST\n")
    
    # Initialize
    print("1. Initializing processor...")
    try:
        processor = AccurateVideoProcessor(use_ball_detection=False, use_ml_prediction=False)
        print("   ✅ Processor initialized\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        return
    
    # Process video
    print("2. Processing video...")
    try:
        result = processor.process_video('uploads/shot.mp4')
        print(f"   ✅ Processing complete\n")
    except Exception as e:
        print(f"   ❌ Failed: {e}\n")
        import traceback
        traceback.print_exc()
        return
    
    # Check results
    print("3. Checking results...\n")
    
    if not result['success']:
        print(f"   ❌ Processing failed: {result.get('error')}\n")
        return
    
    # Display key information
    print(f"📊 Results:")
    print(f"   Success: {result['success']}")
    print(f"   Score: {result['scores']['total']}/100")
    print(f"   Elbow: {result['metrics'].get('elbow_angle', 0):.1f}°")
    print(f"   Knee: {result['metrics'].get('knee_angle', 0):.1f}°")
    print(f"   Release: {result['metrics'].get('release_angle', 0):.1f}°")
    print(f"   Alignment: {result['metrics'].get('body_alignment', 0):.1f}")
    
    # Check if motion was validated
    if 'validation' in result:
        val = result['validation']
        print(f"\n📋 Motion Validation:")
        print(f"   Valid: {val.get('is_valid')}")
        print(f"   Confidence: {val.get('confidence')}%")
    
    # Check if phases were detected
    if 'phase_detection' in result:
        phases = result['phase_detection']
        if phases.get('success'):
            key_frames = phases.get('key_frames', {})
            print(f"\n🎯 Key Frames:")
            print(f"   Dip: {key_frames.get('dip_bottom')}")
            print(f"   Release: {key_frames.get('release')}")
    
    # Save full results
    with open('simple_test_results.json', 'w') as f:
        json.dump({
            'metrics': result['metrics'],
            'scores': result['scores'],
            'validation': result.get('validation'),
            'phase_key_frames': result.get('phase_detection', {}).get('key_frames', {})
        }, f, indent=2)
    
    print(f"\n✅ Test complete! Results saved to simple_test_results.json\n")
    
    # Final verdict
    if result['scores']['total'] > 0:
        print("✅ SYSTEM IS WORKING - Scores are being calculated!")
    else:
        print("❌ PROBLEM - All scores are 0")

if __name__ == "__main__":
    main()

