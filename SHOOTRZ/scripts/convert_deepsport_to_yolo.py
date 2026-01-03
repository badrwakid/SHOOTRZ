"""
Convert DeepSport dataset JSON annotations to YOLO format.

Reads DeepSport JSON files with player and ball annotations,
converts them to YOLO format (normalized bounding boxes),
and organizes into train/val/test splits.
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import shutil
import random
from PIL import Image
import numpy as np


# YOLO class mapping
CLASS_MAP = {
	"ball": 0,
	"player": 1,
	# "hoop": 2,  # Not in DeepSport, can be added later
}

# Estimated sizes for objects (in pixels, will be normalized)
BALL_SIZE = 30  # Approximate ball diameter in pixels
PLAYER_MIN_SIZE = 80  # Minimum player bounding box size


def parse_deepsport_json(json_path: Path) -> Dict:
	"""
	Parse DeepSport JSON annotation file.
	
	Args:
		json_path: Path to JSON file
		
	Returns:
		Dict with annotations: {
			'image_width': int,
			'image_height': int,
			'players': List[Dict],
			'balls': List[Dict]
		}
	"""
	with open(json_path, 'r') as f:
		data = json.load(f)
	
	# Get image dimensions from calibration
	calibration = data.get('calibration', {})
	img_width = calibration.get('img_width', 1624)
	img_height = calibration.get('img_height', 1234)
	
	# Extract players and balls from annotations
	players = []
	balls = []
	
	# Check if this is the main dataset JSON or a frame JSON
	if 'annotations' in data:
		# Main dataset JSON format
		annotations = data.get('annotations', [])
		for ann in annotations:
			if ann.get('type') == 'player':
				players.append(ann)
			elif ann.get('type') == 'ball' and ann.get('visible', False):
				balls.append(ann)
	else:
		# Frame JSON format (from individual JSON files)
		# Players are in 'players' array with pos_feet
		players_data = data.get('players', [])
		for player in players_data:
			if player.get('status') == 1:  # Only valid players
				players.append({
					'pos_feet': player.get('pos_feet', [0, 0]),
					'level': player.get('level', 0.0)
				})
	
	return {
		'image_width': img_width,
		'image_height': img_height,
		'players': players,
		'balls': balls,
	}


def create_ball_bbox(center: List[float], img_width: int, img_height: int) -> Tuple[float, float, float, float]:
	"""
	Create bounding box for ball from center position.
	
	Args:
		center: [x, y, z] ball center in world/image coordinates
		img_width: Image width
		img_height: Image height
		
	Returns:
		Normalized YOLO format: (center_x, center_y, width, height)
	"""
	x, y = center[0], center[1]
	
	# Clamp to image bounds
	x = max(0, min(x, img_width))
	y = max(0, min(y, img_height))
	
	# Create bounding box around center
	half_size = BALL_SIZE / 2
	x1 = max(0, x - half_size)
	y1 = max(0, y - half_size)
	x2 = min(img_width, x + half_size)
	y2 = min(img_height, y + half_size)
	
	# Convert to YOLO format (normalized center, width, height)
	center_x = ((x1 + x2) / 2) / img_width
	center_y = ((y1 + y2) / 2) / img_height
	width = (x2 - x1) / img_width
	height = (y2 - y1) / img_height
	
	return center_x, center_y, width, height


def create_player_bbox(player: Dict, img_width: int, img_height: int) -> Optional[Tuple[float, float, float, float]]:
	"""
	Create bounding box for player from annotation.
	
	Args:
		player: Player annotation dict
		img_width: Image width
		img_height: Image height
		
	Returns:
		Normalized YOLO format: (center_x, center_y, width, height) or None
	"""
	# Try different annotation formats
	if 'pos_feet' in player:
		# Frame JSON format: use foot position as base
		feet_pos = player['pos_feet']
		if len(feet_pos) < 2:
			return None
		x, y = feet_pos[0], feet_pos[1]
		
		# Estimate player bounding box (feet at bottom, head at top)
		# Assume average player height is ~200 pixels
		player_height = 200
		player_width = 80
		
		# Center is at mid-height
		center_x = x / img_width
		center_y = (y - player_height / 2) / img_height
		width = player_width / img_width
		height = player_height / img_height
		
		# Clamp to [0, 1]
		center_x = max(0, min(1, center_x))
		center_y = max(0, min(1, center_y))
		width = max(0.01, min(1, width))
		height = max(0.01, min(1, height))
		
		return center_x, center_y, width, height
		
	elif 'head' in player and 'hips' in player:
		# Main dataset JSON format: use head and hips
		head = player['head']
		hips = player['hips']
		
		if len(head) < 2 or len(hips) < 2:
			return None
		
		head_x, head_y = head[0], head[1]
		hips_x, hips_y = hips[0], hips[1]
		
		# Create bounding box from head to feet (estimate feet below hips)
		# Estimate feet position (hips to feet is roughly same as head to hips)
		head_hips_dist = abs(head_y - hips_y)
		feet_y = hips_y + head_hips_dist
		
		# Bounding box
		x_min = min(head_x, hips_x) - 40  # Add padding
		x_max = max(head_x, hips_x) + 40
		y_min = head_y - 20
		y_max = feet_y + 20
		
		# Clamp to image bounds
		x_min = max(0, min(x_min, img_width))
		x_max = max(0, min(x_max, img_width))
		y_min = max(0, min(y_min, img_height))
		y_max = max(0, min(y_max, img_height))
		
		# Convert to YOLO format
		center_x = ((x_min + x_max) / 2) / img_width
		center_y = ((y_min + y_max) / 2) / img_height
		width = (x_max - x_min) / img_width
		height = (y_max - y_min) / img_height
		
		return center_x, center_y, width, height
	
	return None


def convert_to_yolo_format(
	annotations: Dict,
	image_path: Path,
	output_label_path: Path,
) -> bool:
	"""
	Convert annotations to YOLO format and save label file.
	
	Args:
		annotations: Parsed annotations dict
		image_path: Path to image file
		output_label_path: Path to save YOLO label file
		
	Returns:
		True if conversion successful, False otherwise
	"""
	# Verify image exists and get actual dimensions
	if not image_path.exists():
		return False
	
	try:
		with Image.open(image_path) as img:
			actual_width, actual_height = img.size
	except Exception:
		return False
	
	# Use actual image dimensions if available
	img_width = actual_width if actual_width > 0 else annotations['image_width']
	img_height = actual_height if actual_height > 0 else annotations['image_height']
	
	# Collect all bounding boxes
	yolo_lines = []
	
	# Process balls
	for ball in annotations['balls']:
		if 'center' in ball:
			center = ball['center']
			if len(center) >= 2:
				bbox = create_ball_bbox(center, img_width, img_height)
				if bbox:
					center_x, center_y, width, height = bbox
					yolo_lines.append(f"{CLASS_MAP['ball']} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
	
	# Process players
	for player in annotations['players']:
		bbox = create_player_bbox(player, img_width, img_height)
		if bbox:
			center_x, center_y, width, height = bbox
			# Only add if size is reasonable
			if width > 0.01 and height > 0.01:
				yolo_lines.append(f"{CLASS_MAP['player']} {center_x:.6f} {center_y:.6f} {width:.6f} {height:.6f}\n")
	
	# Write label file
	if yolo_lines:
		output_label_path.parent.mkdir(parents=True, exist_ok=True)
		with open(output_label_path, 'w') as f:
			f.writelines(yolo_lines)
		return True
	
	return False


def find_deepsport_files(base_path: Path) -> List[Tuple[Path, Path]]:
	"""
	Find all DeepSport image/JSON pairs.
	
	Args:
		base_path: Base path to DeepSport dataset
		
	Returns:
		List of (image_path, json_path) tuples
	"""
	image_json_pairs = []
	
	# Search for JSON files and matching images
	for json_file in base_path.rglob("*.json"):
		if json_file.name == "deepsport_dataset_dataset.json":
			continue  # Skip main dataset file
		
		# Look for corresponding image files
		base_name = json_file.stem
		parent_dir = json_file.parent
		
		# Try different image naming patterns
		image_patterns = [
			f"{base_name}_0.png",
			f"{base_name}.png",
			f"{base_name}_40.png",
		]
		
		for pattern in image_patterns:
			image_path = parent_dir / pattern
			if image_path.exists():
				image_json_pairs.append((image_path, json_file))
				break
	
	return image_json_pairs


def convert_dataset(
	deepsport_path: Path,
	output_path: Path,
	train_ratio: float = 0.7,
	val_ratio: float = 0.2,
	test_ratio: float = 0.1,
):
	"""
	Convert entire DeepSport dataset to YOLO format.
	
	Args:
		deepsport_path: Path to DeepSport dataset root
		output_path: Path to output YOLO dataset
		train_ratio: Ratio for training set
		val_ratio: Ratio for validation set
		test_ratio: Ratio for test set
	"""
	print(f"Converting DeepSport dataset from {deepsport_path} to {output_path}")
	
	# Find all image/JSON pairs
	image_json_pairs = find_deepsport_files(deepsport_path)
	print(f"Found {len(image_json_pairs)} image/JSON pairs")
	
	if not image_json_pairs:
		print("No image/JSON pairs found. Check dataset path.")
		return
	
	# Shuffle for random split
	random.seed(42)
	random.shuffle(image_json_pairs)
	
	# Split dataset
	n_total = len(image_json_pairs)
	n_train = int(n_total * train_ratio)
	n_val = int(n_total * val_ratio)
	
	train_pairs = image_json_pairs[:n_train]
	val_pairs = image_json_pairs[n_train:n_train + n_val]
	test_pairs = image_json_pairs[n_train + n_val:]
	
	print(f"Split: {len(train_pairs)} train, {len(val_pairs)} val, {len(test_pairs)} test")
	
	# Create output directories
	splits = {
		'train': train_pairs,
		'val': val_pairs,
		'test': test_pairs,
	}
	
	stats = {'train': {'images': 0, 'labels': 0}, 'val': {'images': 0, 'labels': 0}, 'test': {'images': 0, 'labels': 0}}
	
	for split_name, pairs in splits.items():
		images_dir = output_path / split_name / "images"
		labels_dir = output_path / split_name / "labels"
		images_dir.mkdir(parents=True, exist_ok=True)
		labels_dir.mkdir(parents=True, exist_ok=True)
		
		for image_path, json_path in pairs:
			# Parse annotations
			try:
				annotations = parse_deepsport_json(json_path)
			except Exception as e:
				print(f"Error parsing {json_path}: {e}")
				continue
			
			# Copy image
			image_filename = image_path.name
			output_image_path = images_dir / image_filename
			shutil.copy2(image_path, output_image_path)
			stats[split_name]['images'] += 1
			
			# Convert and save label
			label_filename = image_filename.rsplit('.', 1)[0] + '.txt'
			output_label_path = labels_dir / label_filename
			
			if convert_to_yolo_format(annotations, image_path, output_label_path):
				stats[split_name]['labels'] += 1
	
	# Create dataset YAML
	yaml_content = f"""# DeepSport Basketball Dataset - YOLO Format
path: {output_path.absolute()}
train: train/images
val: val/images
test: test/images

# Classes
nc: {len(CLASS_MAP)}
names:
"""
	for class_name, class_id in sorted(CLASS_MAP.items(), key=lambda x: x[1]):
		yaml_content += f"  {class_id}: {class_name}\n"
	
	yaml_path = output_path / "data.yaml"
	with open(yaml_path, 'w') as f:
		f.write(yaml_content)
	
	print(f"\n=== Conversion Complete ===")
	print(f"Dataset saved to: {output_path}")
	print(f"Train: {stats['train']['images']} images, {stats['train']['labels']} labels")
	print(f"Val: {stats['val']['images']} images, {stats['val']['labels']} labels")
	print(f"Test: {stats['test']['images']} images, {stats['test']['labels']} labels")
	print(f"Dataset YAML: {yaml_path}")


def main():
	parser = argparse.ArgumentParser(description="Convert DeepSport dataset to YOLO format")
	parser.add_argument(
		"--deepsport-path",
		type=str,
		default="data/pose/deepsport",
		help="Path to DeepSport dataset root",
	)
	parser.add_argument(
		"--output-path",
		type=str,
		default="data/ball/deepsport_yolo",
		help="Path to output YOLO dataset",
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
	
	convert_dataset(
		deepsport_path=deepsport_path,
		output_path=output_path,
		train_ratio=args.train_ratio,
		val_ratio=args.val_ratio,
		test_ratio=args.test_ratio,
	)


if __name__ == "__main__":
	main()

