"""
Ball detection and tracking using YOLOv8 and ByteTrack.

Detects basketball and tracks trajectory across frames.
"""

import numpy as np
import cv2
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
	from ultralytics import YOLO
	YOLO_AVAILABLE = True
except ImportError:
	YOLO_AVAILABLE = False
	print("Warning: ultralytics not available. Ball tracking will use placeholder.")


def detect_and_track_ball(
	frames: List[np.ndarray],
	model_path: Optional[str] = None,
	conf_threshold: float = 0.5,
	track_threshold: float = 0.7,
) -> Dict[str, Any]:
	"""
	Detect and track ball across video frames.
	
	Args:
		frames: List of RGB frames [H, W, 3]
		model_path: Path to YOLOv8 model (None = auto-detect fine-tuned model)
		conf_threshold: Detection confidence threshold
		track_threshold: Tracking IOU threshold
	
	Returns:
		Dict with 'trajectory' (list of detections), 'detections' (all detections)
	"""
	if not YOLO_AVAILABLE:
		# Return placeholder for development/testing
		return {
			"trajectory": [],
			"detections": [],
			"warning": "YOLOv8 not available - using placeholder",
		}

	# Use model loader for automatic fallback
	from .model_loader import get_model_loader
	
	loader = get_model_loader()
	
	if model_path and Path(model_path).exists():
		model = YOLO(model_path)
		using_finetuned = True
		ball_class_id = 0  # Fine-tuned model: class 0 is ball
	else:
		# Try to load via model loader
		loaded_model = loader.load_yolov8_ball(prefer_finetuned=True)
		
		if loaded_model is not None:
			model = loaded_model
			# Check if fine-tuned was loaded
			model_path_obj = loader.get_model_path("yolov8_ball", prefer_finetuned=True)
			using_finetuned = (
				model_path_obj is not None and
				isinstance(model_path_obj, Path) and
				"basketball" in model_path_obj.name
			)
			ball_class_id = 0 if using_finetuned else 37
		else:
			# Final fallback
			model = YOLO("yolov8n.pt")
			using_finetuned = False
			ball_class_id = 37  # COCO class 37 is "sports ball"

	trajectory = []
	all_detections = []
	track_history = {}

	for frame_idx, frame in enumerate(frames):
		# Convert RGB to BGR for YOLO
		frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

		# Run detection
		results = model.track(
			source=frame_bgr,
			conf=conf_threshold,
			iou=0.45,
			persist=True,
			tracker="bytetrack.yaml",
			verbose=False,
		)

		# Process detections
		if results and len(results) > 0:
			result = results[0]
			
			# Get boxes and track IDs
			if result.boxes is not None:
				boxes = result.boxes
				track_ids = boxes.id.int().cpu().tolist() if boxes.id is not None else []
				classes = boxes.cls.int().cpu().tolist()
				confidences = boxes.conf.cpu().tolist()
				
				# Find ball detections
				# ball_class_id is set above based on model type
				for i, (box, class_id, conf, track_id) in enumerate(
					zip(boxes.xyxy.cpu(), classes, confidences, track_ids)
				):
					if class_id == ball_class_id and conf >= conf_threshold:
						x1, y1, x2, y2 = box.tolist()
						center_x = (x1 + x2) / 2.0
						center_y = (y1 + y2) / 2.0
						width = x2 - x1
						height = y2 - y1

						# Normalize coordinates (0-1)
						frame_h, frame_w = frame.shape[:2]
						center_x_norm = center_x / frame_w
						center_y_norm = center_y / frame_h

						detection = {
							"frame": frame_idx,
							"track_id": track_id if track_id is not None else -1,
							"center": [center_x_norm, center_y_norm, 0.0],  # Z=0 for 2D
							"bbox": [x1, y1, x2, y2],
							"confidence": conf,
							"width": width,
							"height": height,
						}

						all_detections.append(detection)

						# Add to trajectory (maintain track)
						if track_id is not None:
							if track_id not in track_history:
								track_history[track_id] = []
							track_history[track_id].append(detection)

	# Get longest track as primary trajectory
	if track_history:
		longest_track_id = max(track_history.keys(), key=lambda k: len(track_history[k]))
		trajectory = track_history[longest_track_id]
	else:
		# Fallback: use all detections if no tracking
		trajectory = all_detections

	return {
		"trajectory": trajectory,
		"detections": all_detections,
		"track_history": track_history,
		"model_type": "finetuned" if using_finetuned else "pretrained",
	}


def detect_hoop(
	frames: List[np.ndarray],
	model_path: Optional[str] = None,
	conf_threshold: float = 0.5,
) -> Optional[Dict[str, Any]]:
	"""
	Detect basketball hoop/rim in frames.
	
	Args:
		frames: List of RGB frames
		model_path: Path to YOLOv8 model (fine-tuned for hoop detection)
		conf_threshold: Detection confidence threshold
	
	Returns:
		Dict with hoop position or None if not detected
	"""
	if not YOLO_AVAILABLE:
		return None

	# Load model
	if model_path and Path(model_path).exists():
		model = YOLO(model_path)
	else:
		# Use pretrained (hoop detection requires fine-tuning)
		model = YOLO("yolov8n.pt")

	# Process first frame (hoop is stationary)
	if not frames:
		return None

	frame = frames[0]
	frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

	results = model(frame_bgr, conf=conf_threshold, verbose=False)

	if results and len(results) > 0:
		result = results[0]
		if result.boxes is not None:
			# Look for rectangular/backboard-like detections
			# (This would need custom classes after fine-tuning)
			boxes = result.boxes
			# For now, return None - requires fine-tuned model
			pass

	return None
