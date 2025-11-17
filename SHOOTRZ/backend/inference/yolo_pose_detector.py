"""
YOLOv8-pose detector for 2D pose estimation.

Provides alternative to MediaPipe with 17 COCO keypoints.
Can use fine-tuned basketball-specific model if available.
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


class YOLOv8PoseDetector:
	"""
	YOLOv8-pose detector for extracting 17 COCO keypoints per frame.
	
	Can use fine-tuned basketball-specific model if available.
	"""
	
	def __init__(
		self,
		model_path: Optional[str] = None,
		conf_threshold: float = 0.5,
		use_finetuned: bool = True,
	):
		"""
		Initialize YOLOv8-pose detector.
		
		Args:
			model_path: Path to YOLOv8-pose model (None = auto-detect)
			conf_threshold: Detection confidence threshold
			use_finetuned: Whether to prefer fine-tuned model
		"""
		self.conf_threshold = conf_threshold
		self.model = None
		
		if not YOLO_AVAILABLE:
			raise ImportError("ultralytics not available. Install with: pip install ultralytics")
		
		# Use model loader for automatic fallback
		from .model_loader import get_model_loader
		
		loader = get_model_loader()
		
		if model_path and Path(model_path).exists():
			self.model = YOLO(model_path)
		else:
			loaded_model = loader.load_yolov8_pose(prefer_finetuned=use_finetuned)
			if loaded_model is not None:
				self.model = loaded_model
			else:
				# Fallback to pretrained
				self.model = YOLO("yolov8n-pose.pt")
	
	def process_frame(
		self,
		frame: np.ndarray,
	) -> Optional[Dict[str, Any]]:
		"""
		Process single frame and extract pose keypoints.
		
		Args:
			frame: RGB frame [H, W, 3]
			
		Returns:
			Dict with 'landmarks' [17, 2], 'confidence' [17], or None if no detection
		"""
		if self.model is None:
			return None
		
		# Convert RGB to BGR for YOLO
		frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
		
		# Run detection
		results = self.model(
			frame_bgr,
			conf=self.conf_threshold,
			verbose=False,
		)
		
		if not results or len(results) == 0:
			return None
		
		result = results[0]
		
		# Get keypoints (YOLOv8-pose returns [N, 17, 2] for N persons)
		if result.keypoints is None or len(result.keypoints.data) == 0:
			return None
		
		# Get first person (largest confidence or first detection)
		keypoints_data = result.keypoints.data[0]  # [17, 2] or [17, 3]
		
		# Extract 2D coordinates (first 2 dimensions)
		if keypoints_data.shape[1] >= 2:
			keypoints_2d = keypoints_data[:, :2].cpu().numpy()
		else:
			keypoints_2d = keypoints_data.cpu().numpy()
		
		# Extract confidence (3rd dimension if available, else use detection conf)
		if keypoints_data.shape[1] >= 3:
			confidences = keypoints_data[:, 2].cpu().numpy()
		else:
			# Use detection confidence for all keypoints
			det_conf = result.boxes.conf[0].item() if result.boxes is not None else 0.5
			confidences = np.full(17, det_conf)
		
		# Normalize to [0, 1] if needed (YOLO returns pixel coordinates)
		img_height, img_width = frame.shape[:2]
		if np.max(keypoints_2d) > 1.0:
			keypoints_2d[:, 0] /= img_width
			keypoints_2d[:, 1] /= img_height
		
		return {
			"landmarks": keypoints_2d,  # [17, 2] normalized
			"confidence": confidences,  # [17]
			"detection_confidence": result.boxes.conf[0].item() if result.boxes is not None else 0.5,
		}
	
	def process_video(
		self,
		frames: List[np.ndarray],
	) -> List[Optional[Dict[str, Any]]]:
		"""
		Process video frames and extract pose keypoints.
		
		Args:
			frames: List of RGB frames
			
		Returns:
			List of pose results (one per frame, None if no detection)
		"""
		return [self.process_frame(frame) for frame in frames]
	
	def close(self):
		"""Clean up resources."""
		self.model = None


def detect_pose_yolo(
	frames: List[np.ndarray],
	model_path: Optional[str] = None,
	conf_threshold: float = 0.5,
) -> List[Optional[Dict[str, Any]]]:
	"""
	Detect pose using YOLOv8-pose (convenience function).
	
	Args:
		frames: List of RGB frames
		model_path: Path to YOLOv8-pose model
		conf_threshold: Detection confidence threshold
		
	Returns:
		List of pose results per frame
	"""
	detector = YOLOv8PoseDetector(
		model_path=model_path,
		conf_threshold=conf_threshold,
	)
	
	try:
		return detector.process_video(frames)
	finally:
		detector.close()

