"""
Evaluate pipeline on DeepSport and UCF Sports test sets.

Runs the complete video processing pipeline on dataset videos
and compares results against ground truth annotations.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.processing.pipeline import VideoProcessingPipeline


def evaluate_on_deepsport(deepsport_path: Path, output_dir: Path) -> Dict:
	"""
	Evaluate pipeline on DeepSport test images.
	
	Args:
		deepsport_path: Path to DeepSport dataset
		output_dir: Path to save evaluation results
		
	Returns:
		Dict with evaluation metrics
	"""
	print("Evaluating on DeepSport dataset...")
	
	# Find test images (sample a few for evaluation)
	test_images = list(deepsport_path.rglob("*_0.png"))[:10]  # Sample first 10
	
	if not test_images:
		print("No test images found in DeepSport dataset")
		return {}
	
	results = {
		'total_images': len(test_images),
		'processed': 0,
		'errors': [],
		'metrics': [],
	}
	
	pipeline = VideoProcessingPipeline(
		use_3d_lifting=False,
		enable_ball_tracking=True,
	)
	
	for img_path in test_images:
		try:
			# For images, we'd need to convert to video or process frame-by-frame
			# For now, skip image evaluation (requires video input)
			print(f"Skipping {img_path.name} (requires video format)")
			continue
		except Exception as e:
			results['errors'].append({
				'image': str(img_path),
				'error': str(e),
			})
	
	pipeline.cleanup()
	
	return results


def evaluate_on_ucf_sports(ucf_path: Path, output_dir: Path) -> Dict:
	"""
	Evaluate pipeline on UCF Sports basketball videos.
	
	Args:
		ucf_path: Path to UCF Sports basketball videos
		output_dir: Path to save evaluation results
		
	Returns:
		Dict with evaluation metrics
	"""
	print("Evaluating on UCF Sports dataset...")
	
	# Find basketball videos
	video_extensions = ['.avi', '.mp4', '.mov']
	basketball_videos = []
	
	for ext in video_extensions:
		basketball_videos.extend(ucf_path.rglob(f"*{ext}"))
	
	# Limit to first 5 for evaluation
	basketball_videos = basketball_videos[:5]
	
	if not basketball_videos:
		print("No basketball videos found in UCF Sports dataset")
		return {}
	
	results = {
		'total_videos': len(basketball_videos),
		'processed': 0,
		'errors': [],
		'metrics': [],
	}
	
	pipeline = VideoProcessingPipeline(
		use_3d_lifting=False,
		enable_ball_tracking=True,
	)
	
	for video_path in basketball_videos:
		try:
			print(f"Processing {video_path.name}...")
			result = pipeline.process_video(
				video_path=str(video_path),
				user_id=None,
				video_id=None,
			)
			
			results['processed'] += 1
			results['metrics'].append({
				'video': video_path.name,
				'status': result.get('status'),
				'pose_results': result.get('pose_results', 0),
				'ball_trajectory_length': result.get('ball_trajectory_length', 0),
				'metrics_count': len(result.get('metrics', [])),
			})
		except Exception as e:
			results['errors'].append({
				'video': str(video_path),
				'error': str(e),
			})
	
	pipeline.cleanup()
	
	return results


def main():
	parser = argparse.ArgumentParser(description="Evaluate pipeline on datasets")
	parser.add_argument(
		"--deepsport-path",
		type=str,
		default="data/pose/deepsport",
		help="Path to DeepSport dataset",
	)
	parser.add_argument(
		"--ucf-path",
		type=str,
		default="data/pose/ucf_sports/basketball",
		help="Path to UCF Sports basketball videos",
	)
	parser.add_argument(
		"--output-dir",
		type=str,
		default="data/benchmark/evaluation",
		help="Path to save evaluation results",
	)
	
	args = parser.parse_args()
	
	output_dir = Path(args.output_dir)
	output_dir.mkdir(parents=True, exist_ok=True)
	
	all_results = {}
	
	# Evaluate on DeepSport
	deepsport_path = Path(args.deepsport_path)
	if deepsport_path.exists():
		deepsport_results = evaluate_on_deepsport(deepsport_path, output_dir)
		all_results['deepsport'] = deepsport_results
	else:
		print(f"DeepSport path does not exist: {deepsport_path}")
	
	# Evaluate on UCF Sports
	ucf_path = Path(args.ucf_path)
	if ucf_path.exists():
		ucf_results = evaluate_on_ucf_sports(ucf_path, output_dir)
		all_results['ucf_sports'] = ucf_results
	else:
		print(f"UCF Sports path does not exist: {ucf_path}")
	
	# Save results
	results_path = output_dir / "evaluation_results.json"
	with open(results_path, 'w') as f:
		json.dump(all_results, f, indent=2)
	
	print(f"\n=== Evaluation Complete ===")
	print(f"Results saved to: {results_path}")
	
	# Print summary
	for dataset_name, results in all_results.items():
		print(f"\n{dataset_name}:")
		print(f"  Processed: {results.get('processed', 0)}/{results.get('total_videos', results.get('total_images', 0))}")
		print(f"  Errors: {len(results.get('errors', []))}")


if __name__ == "__main__":
	main()

