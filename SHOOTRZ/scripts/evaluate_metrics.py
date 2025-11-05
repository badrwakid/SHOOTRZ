"""
Evaluation script for metric computation accuracy.

Compares computed angles with manual annotations, reports MAE per joint,
measures inference latency, and generates evaluation report.
"""

import argparse
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple
import time

from backend.metrics.biomechanics import (
	compute_elbow_flexion,
	compute_knee_flexion,
	compute_forearm_verticality,
	compute_release_angle,
)
from backend.inference.pose_2d import MediaPipePoseDetector
from backend.inference.hands_2d import MediaPipeHandsDetector
from backend.inference.ball_tracker import detect_and_track_ball
from backend.metrics.calculator import MetricsCalculator


def load_annotations(annotations_path: Path) -> Dict:
	"""Load manual annotations from JSON file."""
	with open(annotations_path, "r") as f:
		return json.load(f)


def compute_mae(
	computed_values: List[float],
	annotated_values: List[float],
) -> float:
	"""Compute Mean Absolute Error."""
	if len(computed_values) != len(annotated_values):
		raise ValueError("Computed and annotated values must have same length")
	
	errors = [abs(c - a) for c, a in zip(computed_values, annotated_values)]
	return sum(errors) / len(errors) if errors else 0.0


def evaluate_joint_angles(
	computed_metrics: List[Dict],
	annotations: Dict,
) -> Dict[str, float]:
	"""
	Evaluate accuracy of joint angle computations.
	
	Returns MAE for each joint angle type.
	"""
	mae_results = {}

	# Extract annotated angles
	annotated_elbow = annotations.get("elbow_angles", [])
	annotated_knee = annotations.get("knee_angles", [])
	annotated_forearm = annotations.get("forearm_verticality", [])

	# Extract computed angles
	computed_elbow = [
		m["value"]
		for m in computed_metrics
		if "elbow_flexion" in m["metric_name"]
	]
	computed_knee = [
		m["value"]
		for m in computed_metrics
		if m["metric_name"] == "knee_flexion"
	]
	computed_forearm = [
		m["value"]
		for m in computed_metrics
		if m["metric_name"] == "forearm_verticality"
	]

	# Compute MAE for each
	if annotated_elbow and computed_elbow:
		min_len = min(len(annotated_elbow), len(computed_elbow))
		mae_results["elbow_flexion"] = compute_mae(
			computed_elbow[:min_len],
			annotated_elbow[:min_len],
		)

	if annotated_knee and computed_knee:
		min_len = min(len(annotated_knee), len(computed_knee))
		mae_results["knee_flexion"] = compute_mae(
			computed_knee[:min_len],
			annotated_knee[:min_len],
		)

	if annotated_forearm and computed_forearm:
		min_len = min(len(annotated_forearm), len(computed_forearm))
		mae_results["forearm_verticality"] = compute_mae(
			computed_forearm[:min_len],
			annotated_forearm[:min_len],
		)

	return mae_results


def measure_inference_latency(
	video_path: str,
	num_iterations: int = 5,
) -> Dict[str, float]:
	"""
	Measure inference latency for different components.
	
	Returns average latency per component in milliseconds.
	"""
	pose_detector = MediaPipePoseDetector()
	hands_detector = MediaPipeHandsDetector()

	# Load video frames
	import cv2
	cap = cv2.VideoCapture(video_path)
	frames = []
	while cap.isOpened():
		ret, frame = cap.read()
		if not ret:
			break
		frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
	cap.release()

	if not frames:
		return {}

	# Measure pose detection latency
	pose_times = []
	for _ in range(num_iterations):
		start = time.time()
		for frame in frames[:10]:  # Test with first 10 frames
			pose_detector.process_frame(frame)
		pose_times.append((time.time() - start) * 1000 / len(frames[:10]))

	# Measure hands detection latency
	hands_times = []
	for _ in range(num_iterations):
		start = time.time()
		for frame in frames[:10]:
			hands_detector.process_frame(frame)
		hands_times.append((time.time() - start) * 1000 / len(frames[:10]))

	# Measure ball tracking latency
	ball_times = []
	for _ in range(num_iterations):
		start = time.time()
		detect_and_track_ball(frames[:10])
		ball_times.append((time.time() - start) * 1000 / len(frames[:10]))

	pose_detector.close()
	hands_detector.close()

	return {
		"pose_detection_ms": np.mean(pose_times),
		"hands_detection_ms": np.mean(hands_times),
		"ball_tracking_ms": np.mean(ball_times),
		"total_per_frame_ms": np.mean(pose_times) + np.mean(hands_times) + np.mean(ball_times),
	}


def generate_report(
	mae_results: Dict[str, float],
	latency_results: Dict[str, float],
	output_path: Path,
):
	"""Generate evaluation report."""
	report = {
		"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
		"accuracy": {
			"mean_absolute_error": mae_results,
			"overall_mae": np.mean(list(mae_results.values())) if mae_results else None,
		},
		"performance": {
			"latency_ms": latency_results,
			"fps_estimate": 1000 / latency_results.get("total_per_frame_ms", 100) if latency_results else None,
		},
	}

	with open(output_path, "w") as f:
		json.dump(report, f, indent=2)

	print("\n=== Evaluation Report ===")
	print(f"Timestamp: {report['timestamp']}")
	print("\nAccuracy (MAE in degrees):")
	for metric, mae in mae_results.items():
		print(f"  {metric}: {mae:.2f}°")
	if mae_results:
		print(f"\nOverall MAE: {report['accuracy']['overall_mae']:.2f}°")
	
	print("\nPerformance:")
	for component, latency in latency_results.items():
		print(f"  {component}: {latency:.2f} ms")
	if latency_results.get("fps_estimate"):
		print(f"\nEstimated FPS: {report['performance']['fps_estimate']:.1f}")


def main():
	parser = argparse.ArgumentParser(description="Evaluate metric computation accuracy")
	parser.add_argument("--video", type=str, required=True, help="Path to test video")
	parser.add_argument("--annotations", type=str, help="Path to manual annotations JSON")
	parser.add_argument("--output", type=str, default="evaluation_report.json", help="Output report path")
	parser.add_argument("--iterations", type=int, default=5, help="Number of latency measurement iterations")

	args = parser.parse_args()

	# Load annotations if provided
	annotations = {}
	if args.annotations:
		annotations = load_annotations(Path(args.annotations))

	# Process video and compute metrics
	print("Processing video...")
	calculator = MetricsCalculator(use_3d=False)
	
	# Load pose results (simplified for evaluation)
	pose_detector = MediaPipePoseDetector()
	pose_results = pose_detector.process_video(args.video, max_frames=30)
	
	computed_metrics = calculator.compute_all_metrics(pose_results=pose_results)
	pose_detector.close()

	# Evaluate accuracy
	mae_results = {}
	if annotations:
		print("Evaluating accuracy...")
		mae_results = evaluate_joint_angles(computed_metrics, annotations)
	else:
		print("No annotations provided, skipping accuracy evaluation")

	# Measure latency
	print("Measuring inference latency...")
	latency_results = measure_inference_latency(args.video, args.iterations)

	# Generate report
	output_path = Path(args.output)
	generate_report(mae_results, latency_results, output_path)
	print(f"\nReport saved to: {output_path}")


if __name__ == "__main__":
	main()



