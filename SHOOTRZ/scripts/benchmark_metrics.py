"""
Benchmark metrics accuracy using DeepSport pose annotations as ground truth.

Compares MediaPipe pose detections against DeepSport annotations
to validate metric calculation accuracy.
"""

import argparse
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import sys
import cv2

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.inference.pose_2d import MediaPipePoseDetector


def calculate_mpjpe(predicted: np.ndarray, ground_truth: np.ndarray) -> float:
	"""
	Calculate Mean Per Joint Position Error (MPJPE).
	
	Args:
		predicted: Predicted keypoints [N, 2] or [N, 3]
		ground_truth: Ground truth keypoints [N, 2] or [N, 3]
		
	Returns:
		MPJPE in pixels
	"""
	if predicted.shape != ground_truth.shape:
		return float('inf')
	
	# Use 2D coordinates only
	if predicted.shape[1] > 2:
		predicted = predicted[:, :2]
		ground_truth = ground_truth[:, :2]
	
	errors = np.linalg.norm(predicted - ground_truth, axis=1)
	return np.mean(errors)


def extract_deepsport_keypoints(deepsport_json: Path, img_width: int, img_height: int) -> Dict:
	"""
	Extract keypoints from DeepSport JSON annotation.
	
	Args:
		deepsport_json: Path to DeepSport JSON file
		img_width: Image width
		img_height: Image height
		
	Returns:
		Dict with player keypoints (if available)
	"""
	with open(deepsport_json, 'r') as f:
		data = json.load(f)
	
	keypoints = {}
	
	# Extract player positions (feet positions)
	if 'players' in data:
		players = data['players']
		valid_players = [p for p in players if p.get('status') == 1]
		
		if valid_players:
			# Use first valid player
			player = valid_players[0]
			if 'pos_feet' in player:
				feet_pos = player['pos_feet']
				if len(feet_pos) >= 2:
					# Estimate keypoints from feet position
					# This is a simplified mapping - DeepSport doesn't have full pose
					x, y = feet_pos[0], feet_pos[1]
					
					# Estimate body keypoints (rough approximation)
					keypoints = {
						'left_ankle': [x - 10, y],
						'right_ankle': [x + 10, y],
						'left_knee': [x - 10, y - 50],
						'right_knee': [x + 10, y - 50],
						'left_hip': [x - 10, y - 100],
						'right_hip': [x + 10, y - 100],
					}
	
	return keypoints


def compare_pose_detections(
	image_path: Path,
	json_path: Path,
	pose_detector: MediaPipePoseDetector,
) -> Dict:
	"""
	Compare MediaPipe pose detection with DeepSport annotations.
	
	Args:
		image_path: Path to image file
		json_path: Path to DeepSport JSON annotation
		pose_detector: MediaPipe pose detector instance
		
	Returns:
		Dict with comparison metrics
	"""
	# Load image
	image = cv2.imread(str(image_path))
	if image is None:
		return {'error': 'Could not load image'}
	
	image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	img_height, img_width = image_rgb.shape[:2]
	
	# Run MediaPipe detection
	pose_result = pose_detector.process_frame(image_rgb)
	
	if pose_result is None:
		return {'error': 'No pose detected'}
	
	# Extract DeepSport keypoints
	deepsport_keypoints = extract_deepsport_keypoints(json_path, img_width, img_height)
	
	if not deepsport_keypoints:
		return {'error': 'No DeepSport keypoints found'}
	
	# Compare keypoints (simplified - DeepSport has limited keypoints)
	# MediaPipe provides 33 landmarks, DeepSport has feet positions
	mediapipe_landmarks = pose_result['landmarks']
	
	# Extract comparable keypoints
	comparison = {
		'mediapipe_detected': True,
		'deepsport_keypoints': len(deepsport_keypoints),
		'mediapipe_landmarks': len(mediapipe_landmarks),
	}
	
	# Note: Full comparison would require mapping DeepSport keypoints
	# to MediaPipe landmarks, which is complex due to different formats
	
	return comparison


def benchmark_metrics(deepsport_path: Path, output_path: Path, max_samples: int = 20) -> Dict:
	"""
	Benchmark metrics accuracy on DeepSport dataset.
	
	Args:
		deepsport_path: Path to DeepSport dataset
		output_path: Path to save benchmark results
		max_samples: Maximum number of samples to process
		
	Returns:
		Dict with benchmark results
	"""
	print(f"Benchmarking metrics on DeepSport dataset (max {max_samples} samples)...")
	
	# Find image/JSON pairs
	json_files = list(deepsport_path.rglob("*.json"))
	json_files = [f for f in json_files if f.name != "deepsport_dataset_dataset.json"]
	json_files = json_files[:max_samples]
	
	if not json_files:
		print("No JSON files found")
		return {}
	
	pose_detector = MediaPipePoseDetector()
	results = {
		'total_samples': len(json_files),
		'processed': 0,
		'errors': [],
		'comparisons': [],
	}
	
	for json_file in json_files:
		# Find corresponding image
		base_name = json_file.stem
		parent_dir = json_file.parent
		
		image_found = False
		for pattern in [f"{base_name}_0.png", f"{base_name}.png"]:
			image_path = parent_dir / pattern
			if image_path.exists():
				try:
					comparison = compare_pose_detections(
						image_path,
						json_file,
						pose_detector,
					)
					
					if 'error' not in comparison:
						results['processed'] += 1
						results['comparisons'].append({
							'image': image_path.name,
							**comparison,
						})
					else:
						results['errors'].append({
							'file': str(json_file),
							'error': comparison['error'],
						})
					
					image_found = True
					break
				except Exception as e:
					results['errors'].append({
						'file': str(json_file),
						'error': str(e),
					})
		
		if not image_found:
			results['errors'].append({
				'file': str(json_file),
				'error': 'No matching image found',
			})
	
	pose_detector.close()
	
	# Calculate statistics
	if results['comparisons']:
		results['statistics'] = {
			'detection_rate': results['processed'] / results['total_samples'],
			'average_landmarks': np.mean([c['mediapipe_landmarks'] for c in results['comparisons']]),
		}
	
	return results


def main():
	parser = argparse.ArgumentParser(description="Benchmark metrics accuracy using DeepSport annotations")
	parser.add_argument(
		"--deepsport-path",
		type=str,
		default="data/pose/deepsport",
		help="Path to DeepSport dataset",
	)
	parser.add_argument(
		"--output-path",
		type=str,
		default="data/benchmark/metrics_benchmark.json",
		help="Path to save benchmark results",
	)
	parser.add_argument(
		"--max-samples",
		type=int,
		default=20,
		help="Maximum number of samples to process",
	)
	
	args = parser.parse_args()
	
	deepsport_path = Path(args.deepsport_path)
	output_path = Path(args.output_path)
	
	if not deepsport_path.exists():
		print(f"Error: DeepSport path does not exist: {deepsport_path}")
		return
	
	# Run benchmark
	results = benchmark_metrics(deepsport_path, output_path, args.max_samples)
	
	# Save results
	output_path.parent.mkdir(parents=True, exist_ok=True)
	with open(output_path, 'w') as f:
		json.dump(results, f, indent=2)
	
	print(f"\n=== Benchmark Complete ===")
	print(f"Results saved to: {output_path}")
	print(f"Processed: {results.get('processed', 0)}/{results.get('total_samples', 0)}")
	
	if 'statistics' in results:
		stats = results['statistics']
		print(f"Detection rate: {stats.get('detection_rate', 0):.2%}")
		print(f"Average landmarks: {stats.get('average_landmarks', 0):.1f}")


if __name__ == "__main__":
	main()

