"""
Kalman Filter for Pose Keypoint Smoothing

Reduces jitter and noise in pose detection for more stable measurements.
"""

import numpy as np
from filterpy.kalman import KalmanFilter
from typing import Dict, Tuple, Optional

class KeypointKalmanFilter:
    """
    Kalman filter for a single 2D keypoint
    """
    
    def __init__(self, process_noise=0.01, measurement_noise=0.1):
        """
        Initialize Kalman filter for 2D position tracking
        
        Args:
            process_noise: Process noise covariance (lower = trust model more)
            measurement_noise: Measurement noise covariance (lower = trust measurements more)
        """
        # Create 4-state Kalman filter (x, y, vx, vy)
        self.kf = KalmanFilter(dim_x=4, dim_z=2)
        
        # State transition matrix (constant velocity model)
        self.kf.F = np.array([
            [1, 0, 1, 0],  # x = x + vx
            [0, 1, 0, 1],  # y = y + vy
            [0, 0, 1, 0],  # vx = vx
            [0, 0, 0, 1]   # vy = vy
        ])
        
        # Measurement matrix (we only observe position)
        self.kf.H = np.array([
            [1, 0, 0, 0],  # Observe x
            [0, 1, 0, 0]   # Observe y
        ])
        
        # Process noise covariance
        self.kf.Q = np.eye(4) * process_noise
        
        # Measurement noise covariance
        self.kf.R = np.eye(2) * measurement_noise
        
        # Initial state covariance
        self.kf.P *= 1000
        
        # Track if initialized
        self.initialized = False
        self.last_measurement = None
    
    def predict(self) -> Tuple[float, float]:
        """
        Predict next state
        
        Returns:
            Predicted (x, y) position
        """
        self.kf.predict()
        return (self.kf.x[0], self.kf.x[1])
    
    def update(self, measurement: Optional[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Update filter with new measurement
        
        Args:
            measurement: Measured (x, y) position or None
            
        Returns:
            Filtered (x, y) position
        """
        if measurement is None:
            # No measurement, just predict
            return self.predict()
        
        if not self.initialized:
            # Initialize state with first measurement
            self.kf.x = np.array([measurement[0], measurement[1], 0, 0])
            self.initialized = True
            self.last_measurement = measurement
            return measurement
        
        # Update with measurement
        self.kf.update(np.array([measurement[0], measurement[1]]))
        
        self.last_measurement = measurement
        return (self.kf.x[0], self.kf.x[1])
    
    def get_velocity(self) -> Tuple[float, float]:
        """
        Get estimated velocity
        
        Returns:
            (vx, vy) velocity
        """
        return (self.kf.x[2], self.kf.x[3])
    
    def reset(self):
        """Reset filter"""
        self.kf.x = np.zeros(4)
        self.kf.P = np.eye(4) * 1000
        self.initialized = False
        self.last_measurement = None


class PoseKalmanFilter:
    """
    Kalman filters for all pose keypoints
    """
    
    def __init__(self, keypoint_names: list, process_noise=0.01, measurement_noise=0.1):
        """
        Initialize Kalman filters for all keypoints
        
        Args:
            keypoint_names: List of keypoint names
            process_noise: Process noise covariance
            measurement_noise: Measurement noise covariance
        """
        self.keypoint_names = keypoint_names
        self.filters = {}
        
        # Create a filter for each keypoint
        for name in keypoint_names:
            self.filters[name] = KeypointKalmanFilter(process_noise, measurement_noise)
    
    def filter_keypoints(self, keypoints: Optional[Dict]) -> Dict:
        """
        Apply Kalman filtering to all keypoints
        
        Args:
            keypoints: Dict of keypoint positions {name: (x, y)}
            
        Returns:
            Dict of filtered keypoint positions
        """
        filtered_keypoints = {}
        
        for name in self.keypoint_names:
            if keypoints and name in keypoints and keypoints[name] is not None:
                # We have a measurement
                measurement = keypoints[name]
                filtered_pos = self.filters[name].update(measurement)
            else:
                # No measurement, just predict
                filtered_pos = self.filters[name].predict()
            
            filtered_keypoints[name] = filtered_pos
        
        return filtered_keypoints
    
    def get_velocities(self) -> Dict:
        """
        Get estimated velocities for all keypoints
        
        Returns:
            Dict of velocities {name: (vx, vy)}
        """
        velocities = {}
        for name in self.keypoint_names:
            velocities[name] = self.filters[name].get_velocity()
        return velocities
    
    def reset(self):
        """Reset all filters"""
        for filter in self.filters.values():
            filter.reset()


class AdaptiveKalmanFilter:
    """
    Adaptive Kalman filter that adjusts noise parameters based on detection confidence
    """
    
    def __init__(self, keypoint_names: list):
        """
        Initialize adaptive Kalman filters
        
        Args:
            keypoint_names: List of keypoint names
        """
        self.keypoint_names = keypoint_names
        self.filters = {}
        
        # Default noise parameters
        self.default_process_noise = 0.01
        self.default_measurement_noise = 0.1
        
        # Confidence history for adaptive adjustment
        self.confidence_history = {name: [] for name in keypoint_names}
        self.confidence_window = 10
        
        # Create filters
        for name in keypoint_names:
            self.filters[name] = KeypointKalmanFilter(
                self.default_process_noise,
                self.default_measurement_noise
            )
    
    def filter_keypoints(self, keypoints: Optional[Dict], 
                        confidence_scores: Optional[Dict] = None) -> Dict:
        """
        Apply adaptive Kalman filtering
        
        Args:
            keypoints: Dict of keypoint positions {name: (x, y)}
            confidence_scores: Dict of confidence scores {name: 0.0-1.0}
            
        Returns:
            Dict of filtered keypoint positions
        """
        filtered_keypoints = {}
        
        for name in self.keypoint_names:
            # Get confidence score
            confidence = 0.5  # Default
            if confidence_scores and name in confidence_scores:
                confidence = confidence_scores[name]
            
            # Update confidence history
            if name in self.confidence_history:
                self.confidence_history[name].append(confidence)
                if len(self.confidence_history[name]) > self.confidence_window:
                    self.confidence_history[name].pop(0)
            
            # Calculate average confidence
            avg_confidence = np.mean(self.confidence_history[name]) if self.confidence_history[name] else 0.5
            
            # Adjust measurement noise based on confidence
            # Lower confidence = higher measurement noise (trust measurements less)
            measurement_noise = self.default_measurement_noise * (2.0 - avg_confidence)
            self.filters[name].kf.R = np.eye(2) * measurement_noise
            
            # Filter keypoint
            if keypoints and name in keypoints and keypoints[name] is not None:
                measurement = keypoints[name]
                filtered_pos = self.filters[name].update(measurement)
            else:
                filtered_pos = self.filters[name].predict()
            
            filtered_keypoints[name] = filtered_pos
        
        return filtered_keypoints
    
    def reset(self):
        """Reset all filters and history"""
        for filter in self.filters.values():
            filter.reset()
        self.confidence_history = {name: [] for name in self.keypoint_names}

