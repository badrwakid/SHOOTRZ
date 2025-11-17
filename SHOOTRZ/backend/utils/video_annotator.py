"""
Video annotation module for drawing skeleton overlays on video frames.

Draws MediaPipe pose skeleton, ball trajectory, and phase labels on video.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
import os


# MediaPipe pose connections (33 keypoints)
POSE_CONNECTIONS = [
	# Face
	(0, 1), (1, 2), (2, 3), (3, 7),
	(0, 4), (4, 5), (5, 6), (6, 8),
	# Upper body
	(9, 10),  # Shoulders
	(11, 12),  # Shoulders
	(11, 13), (13, 15),  # Left arm
	(12, 14), (14, 16),  # Right arm
	# Torso
	(11, 23), (12, 24),  # Shoulder to hip
	(23, 24),  # Hips
	# Lower body
	(23, 25), (25, 27),  # Left leg
	(24, 26), (26, 28),  # Right leg
]


def draw_skeleton(
	frame: np.ndarray,
	landmarks: np.ndarray,
	confidence: Optional[np.ndarray] = None,
	confidence_threshold: float = 0.5,
) -> np.ndarray:
	"""
	Draw MediaPipe pose skeleton on frame.
	
	Args:
		frame: Video frame (RGB or BGR)
		landmarks: Pose landmarks [33, 2] or [33, 3] (normalized 0-1)
		confidence: Optional confidence array [33]
		confidence_threshold: Minimum confidence to draw landmark
		
	Returns:
		Annotated frame
	"""
	frame = frame.copy()
	h, w = frame.shape[:2]
	
	# Convert landmarks from normalized to pixel coordinates
	if landmarks.shape[1] >= 2:
		landmarks_px = landmarks[:, :2].copy()
		landmarks_px[:, 0] *= w  # X coordinate
		landmarks_px[:, 1] *= h  # Y coordinate
		landmarks_px = landmarks_px.astype(int)
	else:
		return frame
	
	# Draw connections
	for connection in POSE_CONNECTIONS:
		idx1, idx2 = connection
		
		# Check if both landmarks are valid
		if idx1 >= len(landmarks_px) or idx2 >= len(landmarks_px):
			continue
		
		# Check confidence if provided
		if confidence is not None:
			if idx1 >= len(confidence) or idx2 >= len(confidence):
				continue
			if confidence[idx1] < confidence_threshold or confidence[idx2] < confidence_threshold:
				continue
		
		pt1 = tuple(landmarks_px[idx1])
		pt2 = tuple(landmarks_px[idx2])
		
		# Draw line
		cv2.line(frame, pt1, pt2, (0, 255, 0), 2)
	
	# Draw keypoints
	for i, landmark in enumerate(landmarks_px):
		# Check confidence if provided
		if confidence is not None and i < len(confidence):
			if confidence[i] < confidence_threshold:
				continue
		
		pt = tuple(landmark)
		# Draw circle for keypoint
		cv2.circle(frame, pt, 4, (0, 0, 255), -1)
	
	return frame


def draw_ball_trajectory(
	frame: np.ndarray,
	ball_trajectory: List[np.ndarray],
	color: Tuple[int, int, int] = (255, 0, 0),
	thickness: int = 2,
) -> np.ndarray:
	"""
	Draw ball trajectory on frame.
	
	Args:
		frame: Video frame
		ball_trajectory: List of ball positions [[x, y, z], ...] (normalized 0-1)
		color: Trajectory color (BGR)
		thickness: Line thickness
		
	Returns:
		Annotated frame
	"""
	if not ball_trajectory:
		return frame
	
	frame = frame.copy()
	h, w = frame.shape[:2]
	
	# Convert normalized coordinates to pixel coordinates
	points = []
	for pos in ball_trajectory:
		if len(pos) >= 2:
			x = int(pos[0] * w)
			y = int(pos[1] * h)
			points.append((x, y))
	
	# Draw trajectory as connected line
	if len(points) > 1:
		for i in range(len(points) - 1):
			cv2.line(frame, points[i], points[i + 1], color, thickness)
	
	# Draw ball position as circle
	if points:
		last_point = points[-1]
		cv2.circle(frame, last_point, 8, color, -1)
	
	return frame


def draw_phase_label(
	frame: np.ndarray,
	phase: str,
	position: Tuple[int, int] = (10, 30),
	font_scale: float = 0.7,
	thickness: int = 2,
) -> np.ndarray:
	"""
	Draw phase label on frame.
	
	Args:
		frame: Video frame
		phase: Phase name (stance, crouch, release, landing)
		position: Text position (x, y)
		font_scale: Font scale
		thickness: Text thickness
		
	Returns:
		Annotated frame
	"""
	frame = frame.copy()
	
	# Phase colors
	phase_colors = {
		"stance": (255, 255, 0),  # Yellow
		"crouch": (0, 255, 255),  # Cyan
		"release": (0, 255, 0),   # Green
		"landing": (255, 0, 255), # Magenta
	}
	
	color = phase_colors.get(phase.lower(), (255, 255, 255))
	
	# Draw text with background
	text = f"Phase: {phase.upper()}"
	(text_width, text_height), baseline = cv2.getTextSize(
		text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, thickness
	)
	
	# Draw background rectangle
	cv2.rectangle(
		frame,
		(position[0] - 5, position[1] - text_height - 5),
		(position[0] + text_width + 5, position[1] + baseline + 5),
		(0, 0, 0),
		-1,
	)
	
	# Draw text
	cv2.putText(
		frame,
		text,
		position,
		cv2.FONT_HERSHEY_SIMPLEX,
		font_scale,
		color,
		thickness,
	)
	
	return frame


def annotate_video(
	video_path: str,
	pose_results: List[Dict[str, Any]],
	phases: Optional[List[Dict[str, Any]]] = None,
	ball_trajectory: Optional[List[np.ndarray]] = None,
	output_path: Optional[str] = None,
	fps: float = 30.0,
) -> str:
	"""
	Annotate video with skeleton overlay, ball trajectory, and phase labels.
	
	Args:
		video_path: Input video path
		pose_results: List of pose detection results with landmarks
		phases: Optional list of phase detections
		ball_trajectory: Optional ball trajectory positions
		output_path: Output video path (default: input_path + "_annotated.mp4")
		fps: Video FPS
		
	Returns:
		Path to annotated video
	"""
	# Open input video
	cap = cv2.VideoCapture(video_path)
	if not cap.isOpened():
		raise ValueError(f"Could not open video: {video_path}")
	
	# Get video properties
	width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
	height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
	video_fps = cap.get(cv2.CAP_PROP_FPS)
	if video_fps > 0:
		fps = video_fps
	
	# Set output path
	if output_path is None:
		video_path_obj = Path(video_path)
		output_path = str(video_path_obj.parent / f"{video_path_obj.stem}_annotated.mp4")
	
	# Create output directory if needed
	output_path_obj = Path(output_path)
	output_path_obj.parent.mkdir(parents=True, exist_ok=True)
	
	# Create video writer
	fourcc = cv2.VideoWriter_fourcc(*'mp4v')
	out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
	
	frame_idx = 0
	
	# Create phase map for quick lookup
	phase_map = {}
	if phases:
		for phase in phases:
			phase_name = phase.get("phase")
			if isinstance(phase_name, str):
				phase_name = phase_name.lower()
			else:
				# Handle enum
				phase_name = str(phase_name).lower().split('.')[-1]
			
			start_frame = phase.get("start_frame", 0)
			end_frame = phase.get("end_frame", len(pose_results) - 1)
			
			for f in range(start_frame, end_frame + 1):
				phase_map[f] = phase_name
	
	# Process frames
	while True:
		ret, frame = cap.read()
		if not ret:
			break
		
		# Convert BGR to RGB for processing
		frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
		
		# Get pose result for this frame
		if frame_idx < len(pose_results):
			pose_result = pose_results[frame_idx]
			landmarks = pose_result.get("landmarks")
			confidence = pose_result.get("confidence")
			
			if landmarks is not None:
				# Convert landmarks to numpy array if needed
				if not isinstance(landmarks, np.ndarray):
					landmarks = np.array(landmarks)
				
				# Draw skeleton
				frame_rgb = draw_skeleton(frame_rgb, landmarks, confidence)
		
		# Draw ball trajectory (if available and frame is in trajectory range)
		if ball_trajectory:
			# Draw full trajectory up to current frame
			trajectory_up_to_frame = ball_trajectory[:frame_idx + 1] if frame_idx < len(ball_trajectory) else ball_trajectory
			if trajectory_up_to_frame:
				frame_rgb = draw_ball_trajectory(frame_rgb, trajectory_up_to_frame)
		
		# Draw phase label
		current_phase = phase_map.get(frame_idx)
		if current_phase:
			frame_rgb = draw_phase_label(frame_rgb, current_phase)
		
		# Convert back to BGR for writing
		frame_bgr = cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2BGR)
		
		# Write frame
		out.write(frame_bgr)
		
		frame_idx += 1
	
	# Cleanup
	cap.release()
	out.release()
	
	return output_path

