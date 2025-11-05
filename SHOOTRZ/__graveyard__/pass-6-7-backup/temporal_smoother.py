"""
Temporal Smoothing and Outlier Detection

Combines Kalman filtering, outlier detection, and multi-frame analysis
to improve reliability of pose and ball tracking.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
from kalman_filter import AdaptiveKalmanFilter
from scipy.stats import zscore
from collections import deque

class TemporalSmoother:
    """
    Advanced temporal smoothing with outlier detection
    """
    
    def __init__(self, window_size=5, outlier_threshold=3.0):
        """
        Initialize temporal smoother
        
        Args:
            window_size: Number of frames for moving window analysis
            outlier_threshold: Z-score threshold for outlier detection
        """
        self.window_size = window_size
        self.outlier_threshold = outlier_threshold
        
        # Basketball-specific keypoints
        self.keypoint_names = [
            'left_shoulder', 'right_shoulder',
            'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist',
            'left_hip', 'right_hip',
            'left_knee', 'right_knee',
            'left_ankle', 'right_ankle'
        ]
        
        # Initialize Kalman filters
        self.kalman_filter = AdaptiveKalmanFilter(self.keypoint_names)
        
        # Frame history for multi-frame analysis
        self.frame_history = deque(maxlen=window_size)
        
        # Outlier statistics
        self.outlier_count = 0
        self.total_frames = 0
        self.outlier_frames = set()
    
    def smooth_keypoints(self, keypoints: Optional[Dict], 
                        confidence_scores: Optional[Dict] = None,
                        frame_number: int = 0) -> Tuple[Dict, Dict]:
        """
        Apply temporal smoothing to keypoints
        
        Args:
            keypoints: Raw keypoint dict {name: (x, y)}
            confidence_scores: Confidence scores {name: 0.0-1.0}
            frame_number: Current frame number
            
        Returns:
            Tuple of (smoothed_keypoints, reliability_scores)
        """
        self.total_frames += 1
        
        # Apply Kalman filtering
        smoothed = self.kalman_filter.filter_keypoints(keypoints, confidence_scores)
        
        # Update frame history
        self.frame_history.append({
            'frame': frame_number,
            'keypoints': smoothed,
            'raw_keypoints': keypoints,
            'confidence': confidence_scores
        })
        
        # Detect outliers
        is_outlier, outlier_keypoints = self._detect_outliers(smoothed, frame_number)
        
        if is_outlier:
            self.outlier_count += 1
            self.outlier_frames.add(frame_number)
            
            # Use predicted values for outlier keypoints
            smoothed = self._handle_outliers(smoothed, outlier_keypoints)
        
        # Calculate reliability scores
        reliability_scores = self._calculate_reliability(smoothed, confidence_scores, is_outlier)
        
        return smoothed, reliability_scores
    
    def _detect_outliers(self, keypoints: Dict, frame_number: int) -> Tuple[bool, List[str]]:
        """
        Detect outlier keypoints using statistical methods
        
        Args:
            keypoints: Keypoint positions
            frame_number: Current frame number
            
        Returns:
            Tuple of (is_outlier_frame, list_of_outlier_keypoints)
        """
        if len(self.frame_history) < 3:
            return False, []
        
        outlier_keypoints = []
        
        for name in self.keypoint_names:
            # Collect recent positions
            recent_positions = []
            for frame_data in self.frame_history:
                if name in frame_data['keypoints']:
                    pos = frame_data['keypoints'][name]
                    if pos is not None:
                        recent_positions.append(pos)
            
            if len(recent_positions) < 3:
                continue
            
            # Calculate position change
            current_pos = np.array(keypoints.get(name, (0, 0)))
            prev_positions = np.array(recent_positions[:-1])
            
            # Calculate distances from recent positions
            distances = np.linalg.norm(prev_positions - current_pos, axis=1)
            
            # Check if current position is an outlier
            if len(distances) >= 3:
                try:
                    z_scores = np.abs(zscore(distances))
                    if z_scores[-1] > self.outlier_threshold:
                        outlier_keypoints.append(name)
                except:
                    pass
        
        is_outlier_frame = len(outlier_keypoints) >= len(self.keypoint_names) * 0.3  # 30% threshold
        
        return is_outlier_frame, outlier_keypoints
    
    def _handle_outliers(self, keypoints: Dict, outlier_keypoints: List[str]) -> Dict:
        """
        Replace outlier keypoints with predicted values
        
        Args:
            keypoints: Current keypoints
            outlier_keypoints: List of outlier keypoint names
            
        Returns:
            Corrected keypoints
        """
        corrected = keypoints.copy()
        
        # For each outlier keypoint, use median of recent valid values
        for name in outlier_keypoints:
            recent_positions = []
            for frame_data in list(self.frame_history)[:-1]:  # Exclude current frame
                if name in frame_data['keypoints']:
                    pos = frame_data['keypoints'][name]
                    if pos is not None:
                        recent_positions.append(pos)
            
            if recent_positions:
                # Use median position
                median_pos = np.median(recent_positions, axis=0)
                corrected[name] = tuple(median_pos)
        
        return corrected
    
    def _calculate_reliability(self, keypoints: Dict, confidence_scores: Optional[Dict],
                              is_outlier: bool) -> Dict:
        """
        Calculate reliability scores for each keypoint
        
        Args:
            keypoints: Smoothed keypoints
            confidence_scores: Raw confidence scores
            is_outlier: Whether frame is outlier
            
        Returns:
            Dict of reliability scores {name: 0.0-1.0}
        """
        reliability = {}
        
        for name in self.keypoint_names:
            score = 1.0  # Start with perfect reliability
            
            # Factor 1: Raw confidence
            if confidence_scores and name in confidence_scores:
                score *= confidence_scores[name]
            else:
                score *= 0.5  # Default
            
            # Factor 2: Temporal consistency
            if len(self.frame_history) >= 3:
                recent_positions = []
                for frame_data in self.frame_history:
                    if name in frame_data['keypoints']:
                        pos = frame_data['keypoints'][name]
                        if pos is not None:
                            recent_positions.append(pos)
                
                if len(recent_positions) >= 3:
                    # Calculate variance
                    positions_array = np.array(recent_positions)
                    variance = np.var(positions_array, axis=0).mean()
                    
                    # Lower variance = higher consistency
                    consistency_score = np.exp(-variance / 1000)  # Normalize
                    score *= consistency_score
            
            # Factor 3: Outlier penalty
            if is_outlier:
                score *= 0.7
            
            reliability[name] = max(0.0, min(1.0, score))
        
        return reliability
    
    def get_multi_frame_average(self, keypoint_name: str, 
                               weighted: bool = True) -> Optional[Tuple[float, float]]:
        """
        Get multi-frame average for a keypoint
        
        Args:
            keypoint_name: Name of keypoint
            weighted: Whether to use confidence weighting
            
        Returns:
            Average (x, y) position or None
        """
        if not self.frame_history:
            return None
        
        positions = []
        weights = []
        
        for frame_data in self.frame_history:
            if keypoint_name in frame_data['keypoints']:
                pos = frame_data['keypoints'][keypoint_name]
                if pos is not None:
                    positions.append(pos)
                    
                    if weighted and frame_data['confidence'] and keypoint_name in frame_data['confidence']:
                        weights.append(frame_data['confidence'][keypoint_name])
                    else:
                        weights.append(1.0)
        
        if not positions:
            return None
        
        positions_array = np.array(positions)
        weights_array = np.array(weights)
        
        if weighted and len(weights_array) > 0:
            # Weighted average
            avg_pos = np.average(positions_array, axis=0, weights=weights_array)
        else:
            # Simple average
            avg_pos = np.mean(positions_array, axis=0)
        
        return tuple(avg_pos)
    
    def get_outlier_rate(self) -> float:
        """
        Get outlier detection rate
        
        Returns:
            Percentage of outlier frames (0-100)
        """
        if self.total_frames == 0:
            return 0.0
        return (self.outlier_count / self.total_frames) * 100
    
    def get_statistics(self) -> Dict:
        """
        Get smoothing statistics
        
        Returns:
            Dict with statistics
        """
        return {
            'total_frames': self.total_frames,
            'outlier_frames': self.outlier_count,
            'outlier_rate': self.get_outlier_rate(),
            'window_size': self.window_size,
            'outlier_threshold': self.outlier_threshold
        }
    
    def reset(self):
        """Reset smoother"""
        self.kalman_filter.reset()
        self.frame_history.clear()
        self.outlier_count = 0
        self.total_frames = 0
        self.outlier_frames.clear()


class AngleSmoother:
    """
    Specialized smoother for angle measurements
    """
    
    def __init__(self, window_size=5):
        """
        Initialize angle smoother
        
        Args:
            window_size: Window size for moving average
        """
        self.window_size = window_size
        self.angle_history = {}
    
    def smooth_angle(self, angle_name: str, angle_value: float, 
                    confidence: float = 1.0) -> float:
        """
        Smooth angle measurement
        
        Args:
            angle_name: Name of angle (e.g., 'elbow_angle')
            angle_value: Measured angle in degrees
            confidence: Confidence score (0-1)
            
        Returns:
            Smoothed angle
        """
        if angle_name not in self.angle_history:
            self.angle_history[angle_name] = deque(maxlen=self.window_size)
        
        # Add to history with confidence weight
        self.angle_history[angle_name].append({
            'value': angle_value,
            'confidence': confidence
        })
        
        # Calculate weighted average
        if len(self.angle_history[angle_name]) == 0:
            return angle_value
        
        values = np.array([item['value'] for item in self.angle_history[angle_name]])
        weights = np.array([item['confidence'] for item in self.angle_history[angle_name]])
        
        if weights.sum() == 0:
            return angle_value
        
        smoothed = np.average(values, weights=weights)
        
        return float(smoothed)
    
    def get_angle_variance(self, angle_name: str) -> float:
        """
        Get variance of angle measurements
        
        Args:
            angle_name: Name of angle
            
        Returns:
            Variance in degrees^2
        """
        if angle_name not in self.angle_history or len(self.angle_history[angle_name]) < 2:
            return 0.0
        
        values = np.array([item['value'] for item in self.angle_history[angle_name]])
        return float(np.var(values))
    
    def reset(self):
        """Reset all angle histories"""
        self.angle_history.clear()

