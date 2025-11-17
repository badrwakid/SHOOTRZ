"""
Comprehensive evaluation suite for all models in SHOOTRZ pipeline.

Tests fine-tuned models against test sets from DeepSport and UCF Sports.
Generates detailed performance reports.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Any
import numpy as np
import cv2

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.inference.model_loader import get_model_loader
from backend.inference.ball_tracker import detect_and_track_ball
from backend.inference.pose_2d import MediaPipePoseDetector
from backend.inference.yolo_pose_detector import YOLOv8PoseDetector
from backend.inference.lift_3d import lift_3d_pose


def load_test_videos(dataset_path: Path) -> List[Path]:
	"""
	Load test videos from dataset.
	
	Args:
		dataset_path: Path to dataset root
		
	Returns:
		List of video file paths
	"""
	videos = []
	
	# Check for test split
	test_dirs = [
		dataset_path / "test" / "videos",
		dataset_path / "test",
		dataset_path / "val" / "videos",  # Use val if test not available
	]
	
	for test_dir in test_dirs:
		if test_dir.exists():
			for ext in ["*.mp4", "*.avi", "*.mov"]:
				videos.extend(test_dir.rglob(ext))
			break
	
	return videos


def evaluate_ball_detection(
	videos: List[Path],
	loader: Any,
) -> Dict[str, Any]:
	"""
	Evaluate ball detection accuracy.
	
	Args:
		videos: List of test video paths
		loader: ModelLoader instance
		
	Returns:
		Dict with evaluation metrics
	"""
	print("\n=== Evaluating Ball Detection ===")
	
	# Load model
	model = loader.load_yolov8_ball(prefer_finetuned=True)
	if model is None:
		return {"error": "Could not load YOLOv8 ball model"}
	
	results = {
		"total_videos": len(videos),
		"processed": 0,
		"detections": [],
		"avg_confidence": 0.0,
	}
	
	for video_path in videos[:10]:  # Limit to 10 for testing
		try:
			# Load video frames
			cap = cv2.VideoCapture(str(video_path))
			frames = []
			while cap.isOpened():
				ret, frame = cap.read()
				if not ret:
					break
				frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
			cap.release()
			
			if not frames:
				continue
			
			# Run detection
			ball_result = detect_and_track_ball(frames)
			
			if ball_result and "trajectory" in ball_result:
				trajectory = ball_result["trajectory"]
				if trajectory:
					results["detections"].append({
						"video": video_path.name,
						"num_detections": len(trajectory),
						"frames": len(frames),
					})
					results["processed"] += 1
		
		except Exception as e:
			print(f"Error processing {video_path.name}: {e}")
	
	# Calculate average
	if results["detections"]:
		results["avg_detections_per_video"] = np.mean([
			d["num_detections"] for d in results["detections"]
		])
	
	return results


def evaluate_pose_detection(
	videos: List[Path],
	loader: Any,
) -> Dict[str, Any]:
	"""
	Evaluate pose detection accuracy.
	
	Args:
		videos: List of test video paths
		loader: ModelLoader instance
		
	Returns:
		Dict with evaluation metrics
	"""
	print("\n=== Evaluating Pose Detection ===")
	
	# Initialize detectors
	mp_detector = MediaPipePoseDetector()
	
	yolo_detector = None
	try:
		yolo_model = loader.load_yolov8_pose(prefer_finetuned=True)
		if yolo_model:
			yolo_detector = YOLOv8PoseDetector(use_finetuned=True)
	except Exception as e:
		print(f"YOLOv8-pose not available: {e}")
	
	results = {
		"total_videos": len(videos),
		"mediapipe": {"processed": 0, "avg_confidence": 0.0},
		"yolo": {"processed": 0, "avg_confidence": 0.0} if yolo_detector else None,
	}
	
	for video_path in videos[:10]:  # Limit to 10
		try:
			# Load frames
			cap = cv2.VideoCapture(str(video_path))
			frames = []
			while cap.isOpened():
				ret, frame = cap.read()
				if not ret:
					break
				frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
			cap.release()
			
			if not frames:
				continue
			
			# Test MediaPipe
			mp_detections = 0
			mp_confidences = []
			for frame in frames[:30]:  # Sample first 30 frames
				result = mp_detector.process_frame(frame)
				if result:
					mp_detections += 1
					mp_confidences.append(np.mean(result["confidence"]))
			
			if mp_detections > 0:
				results["mediapipe"]["processed"] += 1
				results["mediapipe"]["avg_confidence"] = np.mean(mp_confidences) if mp_confidences else 0.0
			
			# Test YOLOv8-pose if available
			if yolo_detector:
				yolo_detections = 0
				yolo_confidences = []
				for frame in frames[:30]:
					result = yolo_detector.process_frame(frame)
					if result:
						yolo_detections += 1
						yolo_confidences.append(np.mean(result["confidence"]))
				
				if yolo_detections > 0:
					results["yolo"]["processed"] += 1
					results["yolo"]["avg_confidence"] = np.mean(yolo_confidences) if yolo_confidences else 0.0
		
		except Exception as e:
			print(f"Error processing {video_path.name}: {e}")
	
	mp_detector.close()
	if yolo_detector:
		yolo_detector.close()
	
	return results


def evaluate_3d_lifting(
	videos: List[Path],
) -> Dict[str, Any]:
	"""
	Evaluate 3D pose lifting.
	
	Args:
		videos: List of test video paths
		
	Returns:
		Dict with evaluation metrics
	"""
	print("\n=== Evaluating 3D Lifting ===")
	
	mp_detector = MediaPipePoseDetector()
	
	results = {
		"total_videos": len(videos),
		"processed": 0,
		"posemagic": {"success": 0, "avg_confidence": 0.0},
		"hybrik": {"success": 0, "avg_confidence": 0.0},
	}
	
	for video_path in videos[:5]:  # Limit to 5 (3D is slower)
		try:
			# Load frames
			cap = cv2.VideoCapture(str(video_path))
			frames = []
			while cap.isOpened():
				ret, frame = cap.read()
				if not ret:
					break
				frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
			cap.release()
			
			if len(frames) < 10:
				continue
			
			# Extract 2D poses
			pose_2d_series = []
			for frame in frames[:50]:  # Sample 50 frames
				result = mp_detector.process_frame(frame)
				if result:
					pose_2d_series.append(result["landmarks"])
			
			if len(pose_2d_series) < 10:
				continue
			
			# Test PoseMagic
			try:
				lift_result = lift_3d_pose(pose_2d_series, method="posemagic")
				if lift_result and "keypoints_3d" in lift_result:
					results["posemagic"]["success"] += 1
					results["posemagic"]["avg_confidence"] = lift_result.get("confidence", 0.0)
			except Exception as e:
				print(f"PoseMagic error: {e}")
			
			# Test HybrIK
			try:
				lift_result = lift_3d_pose(pose_2d_series, method="hybrik")
				if lift_result and "keypoints_3d" in lift_result:
					results["hybrik"]["success"] += 1
					results["hybrik"]["avg_confidence"] = lift_result.get("confidence", 0.0)
			except Exception as e:
				print(f"HybrIK error: {e}")
			
			results["processed"] += 1
		
		except Exception as e:
			print(f"Error processing {video_path.name}: {e}")
	
	mp_detector.close()
	
	return results


def generate_report(
	ball_results: Dict[str, Any],
	pose_results: Dict[str, Any],
	pose3d_results: Dict[str, Any],
	output_path: Path,
):
	"""
	Generate comprehensive evaluation report.
	
	Args:
		ball_results: Ball detection evaluation results
		pose_results: Pose detection evaluation results
		pose3d_results: 3D lifting evaluation results
		output_path: Path to save report
	"""
	report = {
		"evaluation_summary": {
			"ball_detection": ball_results,
			"pose_detection": pose_results,
			"3d_lifting": pose3d_results,
		},
		"recommendations": [],
	}
	
	# Generate recommendations
	if "error" not in ball_results:
		if ball_results.get("processed", 0) < ball_results.get("total_videos", 0) * 0.5:
			report["recommendations"].append(
				"Ball detection: Low detection rate. Consider fine-tuning on more diverse data."
			)
	
	if pose_results.get("mediapipe", {}).get("processed", 0) > 0:
		mp_conf = pose_results["mediapipe"].get("avg_confidence", 0.0)
		if mp_conf < 0.7:
			report["recommendations"].append(
				"Pose detection: Low MediaPipe confidence. Consider using YOLOv8-pose fine-tuned model."
			)
	
	# Save report
	with open(output_path, 'w') as f:
		json.dump(report, f, indent=2)
	
	print(f"\n=== Evaluation Report Saved ===")
	print(f"Report: {output_path}")
	print(f"\nSummary:")
	print(f"  Ball Detection: {ball_results.get('processed', 0)}/{ball_results.get('total_videos', 0)} videos")
	print(f"  Pose Detection (MP): {pose_results.get('mediapipe', {}).get('processed', 0)} videos")
	if pose_results.get("yolo"):
		print(f"  Pose Detection (YOLO): {pose_results['yolo'].get('processed', 0)} videos")
	print(f"  3D Lifting: {pose3d_results.get('processed', 0)} videos")
	
	if report["recommendations"]:
		print(f"\nRecommendations:")
		for rec in report["recommendations"]:
			print(f"  - {rec}")


def main():
	parser = argparse.ArgumentParser(description="Comprehensive model evaluation")
	parser.add_argument(
		"--deepsport-path",
		type=str,
		default="data/ball/deepsport",
		help="Path to DeepSport dataset",
	)
	parser.add_argument(
		"--ucf-path",
		type=str,
		default="data/pose/ucf_sports",
		help="Path to UCF Sports dataset",
	)
	parser.add_argument(
		"--output",
		type=str,
		default="evaluation_report.json",
		help="Output report path",
	)
	
	args = parser.parse_args()
	
	# Initialize model loader
	loader = get_model_loader()
	
	# Load test videos
	deepsport_path = Path(args.deepsport_path)
	ucf_path = Path(args.ucf_path)
	
	test_videos = []
	if deepsport_path.exists():
		test_videos.extend(load_test_videos(deepsport_path))
	if ucf_path.exists():
		test_videos.extend(load_test_videos(ucf_path))
	
	if not test_videos:
		print("No test videos found. Please check dataset paths.")
		return
	
	print(f"Found {len(test_videos)} test videos")
	
	# Run evaluations
	ball_results = evaluate_ball_detection(test_videos, loader)
	pose_results = evaluate_pose_detection(test_videos, loader)
	pose3d_results = evaluate_3d_lifting(test_videos)
	
	# Generate report
	output_path = Path(args.output)
	generate_report(ball_results, pose_results, pose3d_results, output_path)


if __name__ == "__main__":
	main()

