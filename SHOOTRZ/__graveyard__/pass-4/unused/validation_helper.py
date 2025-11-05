"""
Validation Helper - Tools to validate scoring accuracy

Use this to test if the app's scoring correlates with actual shot outcomes.
"""

import numpy as np
from enhanced_video_processor import EnhancedVideoProcessor
from data_collector import DataCollector
from comparison_engine import ComparisonEngine
import json
from datetime import datetime

class ValidationHelper:
    def __init__(self):
        """Initialize validation helper"""
        self.processor = EnhancedVideoProcessor()
        self.collector = DataCollector()
        self.engine = ComparisonEngine()
        self.results = []
    
    def validate_shot(self, video_path: str, actual_outcome: str, notes: str = ""):
        """
        Process and validate a single shot
        
        Args:
            video_path: Path to video file
            actual_outcome: 'make' or 'miss'
            notes: Optional notes about the shot
            
        Returns:
            Dict with validation results
        """
        print(f"\n🎥 Processing: {video_path}")
        
        # Process video
        result = self.processor.process_video(video_path)
        
        if not result['success']:
            print(f"❌ Processing failed: {result.get('error')}")
            return None
        
        # Store with outcome
        self.collector.add_shot(result, actual_outcome)
        
        # Get ML prediction if available
        ml_prediction = result.get('ml_prediction', {})
        predicted_make_prob = ml_prediction.get('probability_make', None)
        
        # Create validation record
        validation_record = {
            'video': video_path,
            'timestamp': datetime.now().isoformat(),
            'actual_outcome': actual_outcome,
            'form_score': result['scores']['total'],
            'elbow_angle': result['metrics'].get('elbow_angle', 0),
            'knee_angle': result['metrics'].get('knee_angle', 0),
            'release_angle': result['metrics'].get('release_angle', 0),
            'body_alignment': result['metrics'].get('body_alignment', 0),
            'performance_level': result['performance_level'],
            'predicted_make_prob': predicted_make_prob,
            'trajectory_prob': result.get('trajectory', {}).get('make_probability', None),
            'camera_reliability': result.get('camera_analysis', {}).get('reliability_score', 0),
            'notes': notes
        }
        
        self.results.append(validation_record)
        
        # Display results
        print(f"✅ Shot validated: {actual_outcome.upper()}")
        print(f"   Form Score: {result['scores']['total']:.1f}")
        print(f"   Performance Level: {result['performance_level']}")
        
        if predicted_make_prob:
            print(f"   ML Prediction: {predicted_make_prob:.1f}% make probability")
        
        if result.get('trajectory'):
            print(f"   Trajectory: {result['trajectory']['make_probability']:.1f}% (physics-based)")
        
        return validation_record
    
    def validate_batch(self, shot_list: list):
        """
        Validate multiple shots at once
        
        Args:
            shot_list: List of (video_path, outcome, notes) tuples
        """
        print(f"\n📊 Validating {len(shot_list)} shots...\n")
        print("=" * 60)
        
        for i, shot_info in enumerate(shot_list, 1):
            video_path, outcome, notes = shot_info if len(shot_info) == 3 else (*shot_info, "")
            
            print(f"\nShot {i}/{len(shot_list)}")
            self.validate_shot(video_path, outcome, notes)
        
        print("\n" + "=" * 60)
        print(f"✅ Batch validation complete!")
        
        # Show quick summary
        report = self.get_validation_report()
        print(f"\n📈 Quick Summary:")
        print(f"   Total: {report['total_shots']} shots")
        print(f"   Makes: {report['makes']} ({report['make_percentage']:.1f}%)")
        print(f"   Misses: {report['misses']}")
        print(f"   Score Separation: {report['score_separation']:.1f} points")
        print(f"   Quality: {report['validation_quality']}")
    
    def get_validation_report(self) -> dict:
        """
        Generate comprehensive validation accuracy report
        
        Returns:
            Dict with validation statistics
        """
        if not self.results:
            return {
                'error': 'No validation data yet',
                'recommendation': 'Use validate_shot() to add data'
            }
        
        # Separate makes and misses
        makes = [r for r in self.results if r['actual_outcome'] == 'make']
        misses = [r for r in self.results if r['actual_outcome'] == 'miss']
        
        # Calculate score statistics
        make_scores = [r['form_score'] for r in makes]
        miss_scores = [r['form_score'] for r in misses]
        
        make_avg_score = np.mean(make_scores) if make_scores else 0
        miss_avg_score = np.mean(miss_scores) if miss_scores else 0
        
        all_scores = make_scores + miss_scores
        score_variance = np.var(all_scores) if all_scores else 0
        
        # Score separation (key metric!)
        separation = make_avg_score - miss_avg_score
        
        # ML predictions (if available)
        ml_makes = [r['predicted_make_prob'] for r in makes if r['predicted_make_prob']]
        ml_misses = [r['predicted_make_prob'] for r in misses if r['predicted_make_prob']]
        
        ml_separation = 0
        if ml_makes and ml_misses:
            ml_separation = np.mean(ml_makes) - np.mean(ml_misses)
        
        # Quality assessment
        if separation > 15:
            quality = 'Excellent'
        elif separation > 10:
            quality = 'Good'
        elif separation > 5:
            quality = 'Fair'
        else:
            quality = 'Needs Improvement'
        
        report = {
            'total_shots': len(self.results),
            'makes': len(makes),
            'misses': len(misses),
            'make_percentage': (len(makes) / len(self.results) * 100) if self.results else 0,
            'make_avg_score': round(make_avg_score, 2),
            'miss_avg_score': round(miss_avg_score, 2),
            'score_separation': round(separation, 2),
            'score_variance': round(score_variance, 2),
            'validation_quality': quality,
            'ml_prediction_separation': round(ml_separation, 2) if ml_separation else None,
            'recommendations': self._generate_recommendations(separation, len(self.results))
        }
        
        return report
    
    def _generate_recommendations(self, separation: float, sample_size: int) -> list:
        """Generate recommendations based on validation results"""
        recs = []
        
        if sample_size < 20:
            recs.append(f"📊 Collect more data: You have {sample_size} shots, recommend 50+ for reliable validation")
        
        if separation > 15:
            recs.append("✅ Excellent separation! Scoring is highly correlated with shot success")
        elif separation > 10:
            recs.append("👍 Good separation. Scoring reliably predicts shot outcomes")
        elif separation > 5:
            recs.append("⚠️ Fair separation. Consider collecting more diverse shots or training ML model")
        else:
            recs.append("❌ Poor separation. Review camera setup and collect more varied shots")
        
        if sample_size >= 50:
            recs.append("🎯 Ready to train ML model! Use ml_model_trainer.py")
        
        return recs
    
    def check_consistency(self, video_path: str, n_runs: int = 3) -> dict:
        """
        Test consistency by processing same video multiple times
        
        Args:
            video_path: Path to video
            n_runs: Number of times to process
            
        Returns:
            Dict with consistency metrics
        """
        print(f"\n🔄 Consistency Test: Processing {video_path} {n_runs} times...\n")
        
        scores = []
        processing_times = []
        
        for i in range(n_runs):
            print(f"Run {i+1}/{n_runs}...", end=" ")
            result = self.processor.process_video(video_path)
            
            if result['success']:
                scores.append(result['scores']['total'])
                processing_times.append(result['processing_time'])
                print(f"✅ Score: {result['scores']['total']:.1f}")
            else:
                print(f"❌ Failed")
        
        if not scores:
            return {'error': 'All runs failed'}
        
        variance = np.var(scores)
        std_dev = np.std(scores)
        avg_score = np.mean(scores)
        avg_time = np.mean(processing_times)
        
        # Quality assessment
        if variance < 2:
            quality = 'Excellent'
        elif variance < 5:
            quality = 'Good'
        elif variance < 10:
            quality = 'Fair'
        else:
            quality = 'Poor'
        
        print(f"\n📊 Consistency Results:")
        print(f"   Average Score: {avg_score:.2f}")
        print(f"   Variance: {variance:.2f}")
        print(f"   Std Dev: {std_dev:.2f}")
        print(f"   Quality: {quality}")
        print(f"   Avg Processing Time: {avg_time:.2f}s")
        
        return {
            'scores': scores,
            'average': avg_score,
            'variance': variance,
            'std_dev': std_dev,
            'quality': quality,
            'avg_processing_time': avg_time
        }
    
    def compare_camera_angles(self, video_paths: dict) -> dict:
        """
        Compare same shot from different camera angles
        
        Args:
            video_paths: Dict like {'45_degree': 'path1.mp4', 'side': 'path2.mp4'}
            
        Returns:
            Dict with comparison results
        """
        print(f"\n📹 Camera Angle Comparison Test\n")
        print("=" * 60)
        
        results = {}
        
        for angle_name, video_path in video_paths.items():
            print(f"\nProcessing {angle_name} angle...")
            result = self.processor.process_video(video_path)
            
            if result['success']:
                camera_analysis = result.get('camera_analysis', {})
                
                results[angle_name] = {
                    'score': result['scores']['total'],
                    'camera_angle': camera_analysis.get('camera_angle', 'unknown'),
                    'reliability': camera_analysis.get('reliability_score', 0),
                    'is_optimal': camera_analysis.get('is_optimal', False)
                }
                
                print(f"   Score: {result['scores']['total']:.1f}")
                print(f"   Detected Angle: {camera_analysis.get('camera_angle', 'unknown')}")
                print(f"   Reliability: {camera_analysis.get('reliability_score', 0):.1f}")
        
        if len(results) >= 2:
            scores = [r['score'] for r in results.values()]
            score_range = max(scores) - min(scores)
            
            print(f"\n📊 Comparison Results:")
            print(f"   Score Range: {score_range:.1f} points")
            print(f"   Status: {'✅ Consistent' if score_range < 10 else '⚠️ Variable'}")
        
        print("\n" + "=" * 60)
        
        return results
    
    def export_validation_data(self, filename: str = 'validation_results.json'):
        """Export validation results to JSON file"""
        try:
            data = {
                'export_date': datetime.now().isoformat(),
                'total_shots': len(self.results),
                'validation_report': self.get_validation_report(),
                'shot_details': self.results
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✅ Validation data exported to {filename}")
            return True
        except Exception as e:
            print(f"❌ Export failed: {e}")
            return False
    
    def print_summary(self):
        """Print formatted validation summary"""
        report = self.get_validation_report()
        
        print("\n" + "=" * 60)
        print("📊 VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"\n📈 Dataset:")
        print(f"   Total Shots: {report['total_shots']}")
        print(f"   Makes: {report['makes']} ({report['make_percentage']:.1f}%)")
        print(f"   Misses: {report['misses']}")
        
        print(f"\n🎯 Scoring Accuracy:")
        print(f"   Made Shots Avg Score: {report['make_avg_score']:.1f}")
        print(f"   Missed Shots Avg Score: {report['miss_avg_score']:.1f}")
        print(f"   Score Separation: {report['score_separation']:.1f} points")
        print(f"   Overall Quality: {report['validation_quality']}")
        
        if report['ml_prediction_separation']:
            print(f"\n🤖 ML Prediction:")
            print(f"   Prediction Separation: {report['ml_prediction_separation']:.1f}%")
        
        print(f"\n💡 Recommendations:")
        for rec in report['recommendations']:
            print(f"   {rec}")
        
        print("\n" + "=" * 60 + "\n")


# Quick test function
def quick_validation_test(test_video: str):
    """Run a quick validation test on a single video"""
    print("\n🎯 QUICK VALIDATION TEST")
    print("=" * 60)
    
    validator = ValidationHelper()
    
    # Test 1: Consistency
    print("\n📊 Test 1: Consistency Check")
    consistency = validator.check_consistency(test_video, n_runs=3)
    
    # Test 2: Professional comparison
    print("\n🏀 Test 2: Professional Comparison")
    result = validator.processor.process_video(test_video)
    
    if result['success']:
        comparison = validator.engine.find_best_matches(result['metrics'])
        print(f"   Similar to: {comparison['best_match']['name']}")
        print(f"   Similarity: {comparison['best_match']['similarity']:.1f}%")
    
    print("\n" + "=" * 60)
    print("✅ Quick validation complete!\n")


if __name__ == "__main__":
    # Example usage
    print("\n💡 Validation Helper - Usage Examples:\n")
    print("1. Single shot validation:")
    print("   validator = ValidationHelper()")
    print("   validator.validate_shot('shot1.mp4', 'make', 'Good form')")
    print()
    print("2. Batch validation:")
    print("   shots = [")
    print("       ('shot1.mp4', 'make', 'Perfect elbow'),")
    print("       ('shot2.mp4', 'miss', 'Poor knee bend'),")
    print("   ]")
    print("   validator.validate_batch(shots)")
    print()
    print("3. Get report:")
    print("   report = validator.get_validation_report()")
    print("   validator.print_summary()")
    print()
    print("4. Consistency test:")
    print("   validator.check_consistency('shot.mp4', n_runs=5)")
    print()

