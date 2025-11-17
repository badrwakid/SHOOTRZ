"""
Create YOLOv8-pose dataset from DeepSport images using MediaPipe pseudo-labels.

Extracts 2D pose keypoints from DeepSport images and converts to YOLO-pose format
for fine-tuning YOLOv8-pose on basketball-specific poses.
"""

import argparse
import json
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil
import random
from PIL import Image

# Add project root to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.inference.pose_2d import MediaPipePoseDetector


# YOLO-pose format: class_id x y w h kpt1_x kpt1_y kpt1_v kpt2_x kpt2_y kpt2_v ...
# MediaPipe 33 landmarks → YOLO 17 keypoints mapping
MEDIAPIPE_TO_COCO = {
	# COCO keypoint indices (0-16)
	0: 0,   # nose
	1: 11,  # left_eye (use left_shoulder as approximation)
	2: 12,  # right_eye (use right_shoulder as approximation)
	3: 11,  # left_ear (use left_shoulder)
	4: 12,  # right_ear (use right_shoulder)
	5: 11,  # left_shoulder
	6: 12,  # right_shoulder
	7: 13,  # left_elbow
	8: 14,  # right_elbow
	9: 15,  # left_wrist
	10: 16, # right_wrist
	11: 23, # left_hip
	12: 24, # right_hip
	13: 25, # left_knee
	14: 26, # right_knee
	15: 27, # left_ankle
	16: 28, # right_ankle
}

# COCO keypoint visibility mapping (MediaPipe provides visibility scores)
def get_keypoint_visibility(mediapipe_visibility: float) -> int:
	"""
	Convert MediaPipe visibility (0-1) to COCO visibility (0, 1, 2).
	
	0 = not labeled, 1 = labeled but not visible, 2 = labeled and visible
	"""
	if mediapipe_visibility > 0.5:
		return 2  # Visible
	elif mediapipe_visibility > 0.1:
		return 1  # Occluded
	else:
		return 0  # Not visible


def extract_pose_keypoints(
	image_path: Path,
	pose_detector: MediaPipePoseDetector,
) -> Optional[Tuple[np.ndarray, np.ndarray, np.ndarray]]:
	"""
	Extract pose keypoints from image using MediaPipe.
	
	Args:
		image_path: Path to image file
		pose_detector: MediaPipe pose detector instance
		
	Returns:
		Tuple of (keypoints [17, 2], visibility [17], bbox [4]) or None
	"""
	# Load image
	image = cv2.imread(str(image_path))
	if image is None:
		return None
	
	image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
	img_height, img_width = image_rgb.shape[:2]
	
	# Run MediaPipe detection
	pose_result = pose_detector.process_frame(image_rgb)
	
	if pose_result is None:
		return None
	
	landmarks = pose_result['landmarks']  # [33, 3]
	confidences = pose_result['confidence']  # [33]
	
	# Convert MediaPipe 33 landmarks to COCO 17 keypoints
	coco_keypoints = np.zeros((17, 2))  # [x, y] normalized
	coco_visibility = np.zeros(17, dtype=int)
	
	for coco_idx, mediapipe_idx in MEDIAPIPE_TO_COCO.items():
		if mediapipe_idx < len(landmarks):
			# MediaPipe provides normalized coordinates [0, 1]
			x_norm = landmarks[mediapipe_idx, 0]
			y_norm = landmarks[mediapipe_idx, 1]
			
			coco_keypoints[coco_idx, 0] = x_norm
			coco_keypoints[coco_idx, 1] = y_norm
			
			# Convert visibility
			vis_score = confidences[mediapipe_idx] if mediapipe_idx < len(confidences) else 0.0
			coco_visibility[coco_idx] = get_keypoint_visibility(vis_score)
	
	# Calculate bounding box from keypoints
	valid_keypoints = coco_keypoints[coco_visibility > 0]
	if len(valid_keypoints) == 0:
		return None
	
	x_min = np.min(valid_keypoints[:, 0])
	x_max = np.max(valid_keypoints[:, 0])
	y_min = np.min(valid_keypoints[:, 1])
	y_max = np.max(valid_keypoints[:, 1])
	
	# Add padding
	padding = 0.1
	width = x_max - x_min
	height = y_max - y_min
	x_min = max(0, x_min - width * padding)
	y_min = max(0, y_min - height * padding)
	x_max = min(1, x_max + width * padding)
	y_max = min(1, y_max + height * padding)
	
	# Bounding box: center_x, center_y, width, height (normalized)
	bbox = np.array([
		(x_min + x_max) / 2.0,  # center_x
		(y_min + y_max) / 2.0,  # center_y
		x_max - x_min,          # width
		y_max - y_min,          # height
	])
	
	return coco_keypoints, coco_visibility, bbox


def create_yolo_pose_label(
	keypoints: np.ndarray,
	visibility: np.ndarray,
	bbox: np.ndarray,
) -> str:
	"""
	Create YOLO-pose format label string.
	
	Format: class_id x y w h kpt1_x kpt1_y kpt1_v kpt2_x kpt2_y kpt2_v ...
	
	Args:
		keypoints: [17, 2] normalized keypoint coordinates
		visibility: [17] visibility flags (0, 1, 2)
		bbox: [4] bounding box [center_x, center_y, width, height] normalized
		
	Returns:
		YOLO-pose format label string
	"""
	# Class 0 = person (only one class for pose estimation)
	label_parts = ["0"]
	
	# Bounding box
	label_parts.extend([f"{bbox[0]:.6f}", f"{bbox[1]:.6f}", f"{bbox[2]:.6f}", f"{bbox[3]:.6f}"])
	
	# Keypoints: x y v for each of 17 keypoints
	for i in range(17):
		label_parts.append(f"{keypoints[i, 0]:.6f}")  # x
		label_parts.append(f"{keypoints[i, 1]:.6f}")  # y
		label_parts.append(str(visibility[i]))        # visibility
	
	return " ".join(label_parts) + "\n"


def create_pose_dataset(
	deepsport_path: Path,
	output_path: Path,
	train_ratio: float = 0.7,
	val_ratio: float = 0.2,
	test_ratio: float = 0.1,
	max_samples: Optional[int] = None,
):
	"""
	Create YOLOv8-pose dataset from DeepSport images.
	
	Args:
		deepsport_path: Path to DeepSport dataset root
		output_path: Path to output YOLO-pose dataset
		train_ratio: Ratio for training set
		val_ratio: Ratio for validation set
		test_ratio: Ratio for test set
		max_samples: Maximum number of samples to process (None = all)
	"""
	print(f"Creating YOLOv8-pose dataset from {deepsport_path}")
	
	# Initialize pose detector
	pose_detector = MediaPipePoseDetector()
	
	# Find all images
	image_files = []
	for pattern in ["*_0.png", "*.png"]:
		image_files.extend(deepsport_path.rglob(pattern))
	
	# Remove duplicates and filter
	image_files = list(set(image_files))
	image_files = [f for f in image_files if f.name != "deepsport_dataset_dataset.json"]
	
	if max_samples:
		image_files = image_files[:max_samples]
	
	print(f"Found {len(image_files)} images")
	
	if not image_files:
		print("No images found")
		return
	
	# Process images and extract keypoints
	valid_samples = []
	
	for i, image_path in enumerate(image_files):
		if (i + 1) % 50 == 0:
			print(f"Processing {i+1}/{len(image_files)} images...")
		
		result = extract_pose_keypoints(image_path, pose_detector)
		
		if result is not None:
			keypoints, visibility, bbox = result
			valid_samples.append((image_path, keypoints, visibility, bbox))
	
	print(f"Extracted pose from {len(valid_samples)}/{len(image_files)} images")
	
	if not valid_samples:
		print("No valid pose detections found")
		return
	
	# Shuffle for random split
	random.seed(42)
	random.shuffle(valid_samples)
	
	# Split dataset
	n_total = len(valid_samples)
	n_train = int(n_total * train_ratio)
	n_val = int(n_total * val_ratio)
	
	train_samples = valid_samples[:n_train]
	val_samples = valid_samples[n_train:n_train + n_val]
	test_samples = valid_samples[n_train + n_val:]
	
	print(f"Split: {len(train_samples)} train, {len(val_samples)} val, {len(test_samples)} test")
	
	# Create output directories
	splits = {
		'train': train_samples,
		'val': val_samples,
		'test': test_samples,
	}
	
	stats = {'train': 0, 'val': 0, 'test': 0}
	
	for split_name, samples in splits.items():
		images_dir = output_path / split_name / "images"
		labels_dir = output_path / split_name / "labels"
		images_dir.mkdir(parents=True, exist_ok=True)
		labels_dir.mkdir(parents=True, exist_ok=True)
		
		for image_path, keypoints, visibility, bbox in samples:
			# Copy image
			image_filename = image_path.name
			output_image_path = images_dir / image_filename
			shutil.copy2(image_path, output_image_path)
			
			# Create label file
			label_filename = image_filename.rsplit('.', 1)[0] + '.txt'
			output_label_path = labels_dir / label_filename
			
			label_str = create_yolo_pose_label(keypoints, visibility, bbox)
			with open(output_label_path, 'w') as f:
				f.write(label_str)
			
			stats[split_name] += 1
	
	# Create dataset YAML
	yaml_content = f"""# Basketball Pose Dataset - YOLO-Pose Format
path: {output_path.absolute()}
train: train/images
val: val/images
test: test/images

# Classes (person only for pose estimation)
nc: 1
names:
  0: person

# Keypoints (COCO format: 17 keypoints)
kpt_shape: [17, 3]  # [x, y, visibility]
"""
	
	yaml_path = output_path / "data.yaml"
	with open(yaml_path, 'w') as f:
		f.write(yaml_content)
	
	pose_detector.close()
	
	print(f"\n=== Dataset Creation Complete ===")
	print(f"Dataset saved to: {output_path}")
	print(f"Train: {stats['train']} samples")
	print(f"Val: {stats['val']} samples")
	print(f"Test: {stats['test']} samples")
	print(f"Dataset YAML: {yaml_path}")


def main():
	parser = argparse.ArgumentParser(description="Create YOLOv8-pose dataset from DeepSport")
	parser.add_argument(
		"--deepsport-path",
		type=str,
		default="data/pose/deepsport",
		help="Path to DeepSport dataset root",
	)
	parser.add_argument(
		"--output-path",
		type=str,
		default="data/pose/basketball_pose_yolo",
		help="Path to output YOLO-pose dataset",
	)
	parser.add_argument(
		"--train-ratio",
		type=float,
		default=0.7,
		help="Training set ratio",
	)
	parser.add_argument(
		"--val-ratio",
		type=float,
		default=0.2,
		help="Validation set ratio",
	)
	parser.add_argument(
		"--test-ratio",
		type=float,
		default=0.1,
		help="Test set ratio",
	)
	parser.add_argument(
		"--max-samples",
		type=int,
		default=None,
		help="Maximum number of samples to process (None = all)",
	)
	
	args = parser.parse_args()
	
	# Validate ratios
	total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
	if abs(total_ratio - 1.0) > 0.01:
		print(f"Warning: Ratios sum to {total_ratio}, not 1.0. Normalizing...")
		args.train_ratio /= total_ratio
		args.val_ratio /= total_ratio
		args.test_ratio /= total_ratio
	
	deepsport_path = Path(args.deepsport_path)
	output_path = Path(args.output_path)
	
	if not deepsport_path.exists():
		print(f"Error: DeepSport path does not exist: {deepsport_path}")
		return
	
	create_pose_dataset(
		deepsport_path=deepsport_path,
		output_path=output_path,
		train_ratio=args.train_ratio,
		val_ratio=args.val_ratio,
		test_ratio=args.test_ratio,
		max_samples=args.max_samples,
	)


if __name__ == "__main__":
	main()

