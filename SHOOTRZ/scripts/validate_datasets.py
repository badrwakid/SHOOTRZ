"""
Validate dataset integrity, annotation format, and file structure.

Checks DeepSport and UCF Sports datasets for:
- File structure consistency
- Annotation format validity
- Image/label pairing
- Dataset statistics
"""

import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
from collections import defaultdict
import cv2
import numpy as np
from PIL import Image


def validate_deepsport_dataset(deepsport_path: Path) -> Dict:
	"""
	Validate DeepSport dataset structure and annotations.
	
	Args:
		deepsport_path: Path to DeepSport dataset root
		
	Returns:
		Dict with validation results and statistics
	"""
	results = {
		'valid': True,
		'errors': [],
		'warnings': [],
		'statistics': {
			'total_json_files': 0,
			'total_images': 0,
			'valid_pairs': 0,
			'players_count': 0,
			'balls_count': 0,
			'arenas': set(),
		}
	}
	
	# Find all JSON files
	json_files = list(deepsport_path.rglob("*.json"))
	results['statistics']['total_json_files'] = len(json_files)
	
	# Count images
	image_files = list(deepsport_path.rglob("*.png"))
	results['statistics']['total_images'] = len(image_files)
	
	# Validate JSON/image pairs
	valid_pairs = 0
	for json_file in json_files:
		if json_file.name == "deepsport_dataset_dataset.json":
			continue
		
		# Check if corresponding image exists
		base_name = json_file.stem
		parent_dir = json_file.parent
		
		image_found = False
		for pattern in [f"{base_name}_0.png", f"{base_name}.png", f"{base_name}_40.png"]:
			image_path = parent_dir / pattern
			if image_path.exists():
				image_found = True
				valid_pairs += 1
				
				# Validate JSON structure
				try:
					with open(json_file, 'r') as f:
						data = json.load(f)
					
					# Check for required fields
					if 'calibration' in data:
						cal = data['calibration']
						if 'img_width' not in cal or 'img_height' not in cal:
							results['warnings'].append(f"Missing image dimensions in {json_file}")
					
					# Count annotations
					if 'players' in data:
						players = data['players']
						valid_players = sum(1 for p in players if p.get('status') == 1)
						results['statistics']['players_count'] += valid_players
					
					# Extract arena name
					if 'prefix' in data:
						prefix = data['prefix']
						if 'arena' in prefix.lower():
							arena = prefix.split('_')[0] if '_' in prefix else prefix
							results['statistics']['arenas'].add(arena)
					
				except json.JSONDecodeError as e:
					results['errors'].append(f"Invalid JSON in {json_file}: {e}")
					results['valid'] = False
				except Exception as e:
					results['warnings'].append(f"Error processing {json_file}: {e}")
				
				break
		
		if not image_found:
			results['warnings'].append(f"No matching image for {json_file}")
	
	results['statistics']['valid_pairs'] = valid_pairs
	results['statistics']['arenas'] = len(results['statistics']['arenas'])
	
	# Check main dataset JSON
	main_json = deepsport_path / "deepsport_dataset_dataset.json"
	if main_json.exists():
		try:
			with open(main_json, 'r') as f:
				# Read first line to check format
				first_line = f.readline()
				if first_line.strip().startswith('['):
					# It's a JSON array
					f.seek(0)
					data = json.load(f)
					if isinstance(data, list) and len(data) > 0:
						# Count balls in main dataset
						for item in data:
							if 'annotations' in item:
								for ann in item.get('annotations', []):
									if ann.get('type') == 'ball' and ann.get('visible', False):
										results['statistics']['balls_count'] += 1
		except Exception as e:
			results['warnings'].append(f"Could not parse main dataset JSON: {e}")
	
	return results


def validate_ucf_sports_dataset(ucf_path: Path) -> Dict:
	"""
	Validate UCF Sports dataset structure.
	
	Args:
		ucf_path: Path to UCF Sports dataset root
		
	Returns:
		Dict with validation results and statistics
	"""
	results = {
		'valid': True,
		'errors': [],
		'warnings': [],
		'statistics': {
			'total_videos': 0,
			'basketball_videos': 0,
			'action_classes': defaultdict(int),
			'total_frames': 0,
		}
	}
	
	# Find all video files
	video_extensions = ['.avi', '.mp4', '.mov', '.mkv']
	video_files = []
	for ext in video_extensions:
		video_files.extend(ucf_path.rglob(f"*{ext}"))
	
	results['statistics']['total_videos'] = len(video_files)
	
	# Find basketball-related videos
	basketball_keywords = ['basketball', 'basket', 'ball', 'shoot', 'shot']
	basketball_videos = []
	
	for video_file in video_files:
		# Check filename and path for basketball keywords
		path_lower = str(video_file).lower()
		if any(keyword in path_lower for keyword in basketball_keywords):
			basketball_videos.append(video_file)
			results['statistics']['basketball_videos'] += 1
		
		# Extract action class from path
		parts = video_file.parts
		for part in parts:
			if part.lower() in ['basketball', 'diving', 'golf', 'kicking', 'riding', 'running', 'skating', 'swing', 'walking']:
				results['statistics']['action_classes'][part.lower()] += 1
	
	# Count frames in basketball videos
	total_frames = 0
	for video_file in basketball_videos[:10]:  # Sample first 10
		try:
			cap = cv2.VideoCapture(str(video_file))
			if cap.isOpened():
				frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
				total_frames += frame_count
				cap.release()
		except Exception as e:
			results['warnings'].append(f"Could not read {video_file}: {e}")
	
	results['statistics']['total_frames'] = total_frames
	
	# Check for annotation files
	annotation_files = list(ucf_path.rglob("*.txt"))
	if not annotation_files:
		results['warnings'].append("No annotation files (.txt) found in UCF Sports dataset")
	
	return results


def validate_yolo_dataset(yolo_path: Path) -> Dict:
	"""
	Validate YOLO format dataset structure.
	
	Args:
		yolo_path: Path to YOLO dataset root
		
	Returns:
		Dict with validation results
	"""
	results = {
		'valid': True,
		'errors': [],
		'warnings': [],
		'statistics': {
			'train_images': 0,
			'val_images': 0,
			'test_images': 0,
			'train_labels': 0,
			'val_labels': 0,
			'test_labels': 0,
		}
	}
	
	splits = ['train', 'val', 'test']
	
	for split in splits:
		images_dir = yolo_path / split / "images"
		labels_dir = yolo_path / split / "labels"
		
		if not images_dir.exists():
			results['errors'].append(f"Missing {split}/images directory")
			results['valid'] = False
			continue
		
		if not labels_dir.exists():
			results['errors'].append(f"Missing {split}/labels directory")
			results['valid'] = False
			continue
		
		# Count images and labels
		image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg"))
		label_files = list(labels_dir.glob("*.txt"))
		
		results['statistics'][f'{split}_images'] = len(image_files)
		results['statistics'][f'{split}_labels'] = len(label_files)
		
		# Check for matching pairs
		image_names = {f.stem for f in image_files}
		label_names = {f.stem for f in label_files}
		
		missing_labels = image_names - label_names
		missing_images = label_names - image_names
		
		if missing_labels:
			results['warnings'].append(f"{split}: {len(missing_labels)} images without labels")
		
		if missing_images:
			results['warnings'].append(f"{split}: {len(missing_images)} labels without images")
		
		# Validate label format
		for label_file in label_files[:10]:  # Sample first 10
			try:
				with open(label_file, 'r') as f:
					lines = f.readlines()
					for line_num, line in enumerate(lines, 1):
						parts = line.strip().split()
						if len(parts) < 5:
							results['errors'].append(f"Invalid label format in {label_file}:{line_num}")
							results['valid'] = False
							continue
						
						class_id = int(parts[0])
						coords = [float(x) for x in parts[1:5]]
						
						# Check if coordinates are normalized [0, 1]
						if any(c < 0 or c > 1 for c in coords):
							results['warnings'].append(f"Non-normalized coordinates in {label_file}:{line_num}")
			except Exception as e:
				results['errors'].append(f"Error reading {label_file}: {e}")
				results['valid'] = False
	
	# Check for data.yaml
	yaml_file = yolo_path / "data.yaml"
	if not yaml_file.exists():
		results['warnings'].append("Missing data.yaml file")
	
	return results


def print_validation_report(results: Dict, dataset_name: str):
	"""Print formatted validation report."""
	print(f"\n{'='*60}")
	print(f"Validation Report: {dataset_name}")
	print(f"{'='*60}")
	
	if results['valid']:
		print("Status: [OK] VALID")
	else:
		print("Status: [ERROR] INVALID")
	
	if results['errors']:
		print(f"\nErrors ({len(results['errors'])}):")
		for error in results['errors'][:10]:  # Show first 10
			print(f"  [ERROR] {error}")
		if len(results['errors']) > 10:
			print(f"  ... and {len(results['errors']) - 10} more errors")
	
	if results['warnings']:
		print(f"\nWarnings ({len(results['warnings'])}):")
		for warning in results['warnings'][:10]:  # Show first 10
			print(f"  [WARN] {warning}")
		if len(results['warnings']) > 10:
			print(f"  ... and {len(results['warnings']) - 10} more warnings")
	
	if 'statistics' in results:
		print(f"\nStatistics:")
		for key, value in results['statistics'].items():
			if isinstance(value, (int, float)):
				print(f"  {key}: {value}")
			elif isinstance(value, dict):
				print(f"  {key}:")
				for k, v in value.items():
					print(f"    {k}: {v}")


def main():
	parser = argparse.ArgumentParser(description="Validate dataset integrity and structure")
	parser.add_argument(
		"--deepsport-path",
		type=str,
		default="data/pose/deepsport",
		help="Path to DeepSport dataset",
	)
	parser.add_argument(
		"--ucf-path",
		type=str,
		default="data/pose/ucf_sports",
		help="Path to UCF Sports dataset",
	)
	parser.add_argument(
		"--yolo-path",
		type=str,
		default="data/ball/deepsport_yolo",
		help="Path to YOLO format dataset",
	)
	parser.add_argument(
		"--all",
		action="store_true",
		help="Validate all datasets",
	)
	
	args = parser.parse_args()
	
	if args.all or args.deepsport_path:
		deepsport_path = Path(args.deepsport_path)
		if deepsport_path.exists():
			results = validate_deepsport_dataset(deepsport_path)
			print_validation_report(results, "DeepSport")
		else:
			print(f"DeepSport path does not exist: {deepsport_path}")
	
	if args.all or args.ucf_path:
		ucf_path = Path(args.ucf_path)
		if ucf_path.exists():
			results = validate_ucf_sports_dataset(ucf_path)
			print_validation_report(results, "UCF Sports")
		else:
			print(f"UCF Sports path does not exist: {ucf_path}")
	
	if args.all or args.yolo_path:
		yolo_path = Path(args.yolo_path)
		if yolo_path.exists():
			results = validate_yolo_dataset(yolo_path)
			print_validation_report(results, "YOLO Dataset")
		else:
			print(f"YOLO path does not exist: {yolo_path}")


if __name__ == "__main__":
	main()

