"""
Advanced Basketball Detection System

Uses dual detection methods:
1. YOLOv8-nano for ML-based detection (primary)
2. Color-based + Hough Circle detection (fallback)

Optimized for laptop CPU performance.
"""

import cv2
import numpy as np
from typing import Optional, Tuple, List, Dict
import os

class BallDetector:
    def __init__(self, use_yolo=True, use_color_fallback=True):
        """
        Initialize basketball detector
        
        Args:
            use_yolo: Whether to use YOLOv8 detection
            use_color_fallback: Whether to use color-based fallback
        """
        self.use_yolo = use_yolo
        self.use_color_fallback = use_color_fallback
        self.yolo_model = None
        self.detection_history = []
        
        # Color ranges for basketball (orange)
        self.orange_lower = np.array([5, 100, 100], dtype=np.uint8)
        self.orange_upper = np.array([25, 255, 255], dtype=np.uint8)
        
        # Detection confidence thresholds
        self.yolo_confidence_threshold = 0.3
        self.color_confidence_threshold = 0.5
        
        # Ball size constraints (pixels)
        self.min_radius = 10
        self.max_radius = 150
        
        # Initialize YOLO if requested
        if self.use_yolo:
            self._initialize_yolo()
    
    def _initialize_yolo(self):
        """Initialize YOLOv8-nano model for ball detection"""
        try:
            from ultralytics import YOLO
            
            # Use YOLOv8-nano (fastest, most CPU-friendly)
            # Will download on first use
            model_path = 'yolov8n.pt'
            self.yolo_model = YOLO(model_path)
            
            # Optimize for CPU inference
            self.yolo_model.to('cpu')
            
            print("✓ YOLOv8-nano loaded successfully")
            
        except ImportError:
            print("⚠ ultralytics not installed, YOLO detection disabled")
            self.use_yolo = False
        except Exception as e:
            print(f"⚠ Could not initialize YOLO: {e}")
            self.use_yolo = False
    
    def detect_ball(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect basketball in frame using multi-method approach
        
        Args:
            frame: OpenCV frame (BGR format)
            
        Returns:
            Dict with ball detection info or None if not detected
            {
                'center': (x, y),
                'radius': r,
                'confidence': 0.0-1.0,
                'method': 'yolo' or 'color',
                'bbox': (x1, y1, x2, y2)
            }
        """
        if frame is None or frame.size == 0:
            return None
        
        detection = None
        
        # Try YOLO detection first (more accurate)
        if self.use_yolo and self.yolo_model is not None:
            detection = self._detect_yolo(frame)
        
        # Fallback to color-based detection
        if detection is None and self.use_color_fallback:
            detection = self._detect_color(frame)
        
        # Update detection history
        if detection is not None:
            self.detection_history.append(detection)
            if len(self.detection_history) > 30:  # Keep last 30 detections
                self.detection_history.pop(0)
        
        return detection
    
    def _detect_yolo(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect ball using YOLOv8
        
        Args:
            frame: OpenCV frame
            
        Returns:
            Detection dict or None
        """
        try:
            # Run inference with reduced image size for speed
            results = self.yolo_model(
                frame,
                imgsz=320,  # Smaller image size for faster inference
                conf=self.yolo_confidence_threshold,
                classes=[32],  # Class 32 is 'sports ball' in COCO
                verbose=False
            )
            
            if len(results) == 0 or len(results[0].boxes) == 0:
                return None
            
            # Get the detection with highest confidence
            boxes = results[0].boxes
            confidences = boxes.conf.cpu().numpy()
            best_idx = np.argmax(confidences)
            
            # Extract bounding box
            bbox = boxes.xyxy[best_idx].cpu().numpy()
            x1, y1, x2, y2 = bbox
            
            # Calculate center and radius
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            radius = int(max(x2 - x1, y2 - y1) / 2)
            
            # Validate size
            if radius < self.min_radius or radius > self.max_radius:
                return None
            
            return {
                'center': (center_x, center_y),
                'radius': radius,
                'confidence': float(confidences[best_idx]),
                'method': 'yolo',
                'bbox': (int(x1), int(y1), int(x2), int(y2))
            }
            
        except Exception as e:
            print(f"YOLO detection error: {e}")
            return None
    
    def _detect_color(self, frame: np.ndarray) -> Optional[Dict]:
        """
        Detect ball using color-based method + Hough circles
        
        Args:
            frame: OpenCV frame
            
        Returns:
            Detection dict or None
        """
        try:
            # Convert to HSV for color detection
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # Create mask for orange color
            mask = cv2.inRange(hsv, self.orange_lower, self.orange_upper)
            
            # Apply morphological operations to remove noise
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            
            # Apply Gaussian blur
            mask = cv2.GaussianBlur(mask, (9, 9), 2)
            
            # Detect circles using Hough Circle Transform
            circles = cv2.HoughCircles(
                mask,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=50,
                param1=50,
                param2=30,
                minRadius=self.min_radius,
                maxRadius=self.max_radius
            )
            
            if circles is None or len(circles[0]) == 0:
                return None
            
            # Get the circle with best score (highest accumulator value)
            circles = np.uint16(np.around(circles))
            best_circle = circles[0][0]
            
            center_x, center_y, radius = best_circle
            
            # Calculate confidence based on color coverage
            roi_mask = np.zeros_like(mask)
            cv2.circle(roi_mask, (center_x, center_y), radius, 255, -1)
            
            # Calculate percentage of orange pixels in circle
            orange_pixels = cv2.countNonZero(cv2.bitwise_and(mask, roi_mask))
            total_pixels = cv2.countNonZero(roi_mask)
            
            if total_pixels == 0:
                confidence = 0.0
            else:
                confidence = orange_pixels / total_pixels
            
            # Check if confidence meets threshold
            if confidence < self.color_confidence_threshold:
                return None
            
            # Calculate bounding box
            x1 = max(0, center_x - radius)
            y1 = max(0, center_y - radius)
            x2 = min(frame.shape[1], center_x + radius)
            y2 = min(frame.shape[0], center_y + radius)
            
            return {
                'center': (int(center_x), int(center_y)),
                'radius': int(radius),
                'confidence': float(confidence),
                'method': 'color',
                'bbox': (int(x1), int(y1), int(x2), int(y2))
            }
            
        except Exception as e:
            print(f"Color detection error: {e}")
            return None
    
    def draw_detection(self, frame: np.ndarray, detection: Dict) -> np.ndarray:
        """
        Draw ball detection on frame
        
        Args:
            frame: OpenCV frame
            detection: Detection dict
            
        Returns:
            Annotated frame
        """
        if detection is None:
            return frame
        
        annotated = frame.copy()
        center = detection['center']
        radius = detection['radius']
        confidence = detection['confidence']
        method = detection['method']
        
        # Choose color based on method
        if method == 'yolo':
            color = (0, 255, 0)  # Green for YOLO
        else:
            color = (255, 165, 0)  # Orange for color detection
        
        # Draw circle
        cv2.circle(annotated, center, radius, color, 2)
        
        # Draw center point
        cv2.circle(annotated, center, 3, color, -1)
        
        # Draw bounding box
        if 'bbox' in detection:
            x1, y1, x2, y2 = detection['bbox']
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1)
        
        # Add label
        label = f"Ball ({method}): {confidence:.2f}"
        cv2.putText(
            annotated,
            label,
            (center[0] - radius, center[1] - radius - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )
        
        return annotated
    
    def get_detection_stats(self) -> Dict:
        """
        Get statistics about recent detections
        
        Returns:
            Dict with detection statistics
        """
        if not self.detection_history:
            return {
                'total_detections': 0,
                'avg_confidence': 0.0,
                'yolo_detections': 0,
                'color_detections': 0,
                'detection_rate': 0.0
            }
        
        yolo_count = sum(1 for d in self.detection_history if d['method'] == 'yolo')
        color_count = sum(1 for d in self.detection_history if d['method'] == 'color')
        avg_confidence = np.mean([d['confidence'] for d in self.detection_history])
        
        return {
            'total_detections': len(self.detection_history),
            'avg_confidence': float(avg_confidence),
            'yolo_detections': yolo_count,
            'color_detections': color_count,
            'detection_rate': len(self.detection_history) / 30.0  # Assuming 30 frame window
        }
    
    def reset(self):
        """Reset detection history"""
        self.detection_history = []


class BallTracker:
    """
    Track basketball across frames with motion prediction
    """
    
    def __init__(self, max_lost_frames=10):
        """
        Initialize ball tracker
        
        Args:
            max_lost_frames: Maximum frames to maintain tracking without detection
        """
        self.max_lost_frames = max_lost_frames
        self.track_history = []
        self.lost_frames = 0
        self.is_tracking = False
        
        # Motion prediction
        self.velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 9.8])  # Gravity (pixels per frame^2)
        
    def update(self, detection: Optional[Dict], frame_number: int):
        """
        Update tracker with new detection
        
        Args:
            detection: Detection dict or None
            frame_number: Current frame number
        """
        if detection is not None:
            # Update track history
            self.track_history.append({
                'frame': frame_number,
                'position': detection['center'],
                'radius': detection['radius'],
                'confidence': detection['confidence'],
                'method': detection['method']
            })
            
            # Calculate velocity if we have previous position
            if len(self.track_history) >= 2:
                prev_pos = np.array(self.track_history[-2]['position'])
                curr_pos = np.array(detection['center'])
                self.velocity = curr_pos - prev_pos
            
            self.lost_frames = 0
            self.is_tracking = True
            
            # Keep only recent history
            if len(self.track_history) > 100:
                self.track_history = self.track_history[-100:]
        else:
            self.lost_frames += 1
            
            # Stop tracking if lost for too long
            if self.lost_frames >= self.max_lost_frames:
                self.is_tracking = False
    
    def predict_position(self) -> Optional[Tuple[int, int]]:
        """
        Predict ball position based on motion
        
        Returns:
            Predicted (x, y) position or None
        """
        if not self.track_history:
            return None
        
        last_pos = np.array(self.track_history[-1]['position'])
        
        # Simple linear prediction with gravity
        predicted_pos = last_pos + self.velocity + 0.5 * self.acceleration
        
        return (int(predicted_pos[0]), int(predicted_pos[1]))
    
    def get_trajectory(self) -> List[Tuple[int, int]]:
        """
        Get ball trajectory (list of positions)
        
        Returns:
            List of (x, y) positions
        """
        return [track['position'] for track in self.track_history]
    
    def get_velocity(self) -> Tuple[float, float]:
        """
        Get current velocity
        
        Returns:
            (vx, vy) velocity in pixels per frame
        """
        return tuple(self.velocity)
    
    def get_speed(self) -> float:
        """
        Get current speed (magnitude of velocity)
        
        Returns:
            Speed in pixels per frame
        """
        return float(np.linalg.norm(self.velocity))
    
    def reset(self):
        """Reset tracker"""
        self.track_history = []
        self.lost_frames = 0
        self.is_tracking = False
        self.velocity = np.array([0.0, 0.0])

