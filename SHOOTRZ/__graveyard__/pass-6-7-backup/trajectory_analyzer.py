"""
Basketball Trajectory Analyzer

Analyzes ball trajectory to predict shot success and calculate:
- Shot arc angle
- Release velocity
- Entry angle
- Peak height
- Make/miss prediction
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from scipy.optimize import curve_fit
from scipy.signal import savgol_filter

class TrajectoryAnalyzer:
    def __init__(self):
        """Initialize trajectory analyzer"""
        self.trajectory_points = []
        self.release_point = None
        self.peak_point = None
        self.entry_point = None
        
        # Physics constants (approximate)
        self.gravity = 9.8  # m/s^2
        self.pixels_per_meter = 100  # Approximate conversion
        
        # Ideal trajectory parameters
        self.ideal_arc_angle = 45.0  # degrees
        self.ideal_entry_angle = 45.0  # degrees
        self.ideal_peak_height_ratio = 1.5  # Peak height / hoop height
        
    def analyze_trajectory(self, ball_positions: List[Tuple[int, int]], 
                          fps: float = 30.0) -> Dict:
        """
        Analyze complete ball trajectory
        
        Args:
            ball_positions: List of (x, y) ball center positions
            fps: Video frames per second
            
        Returns:
            Dict with trajectory analysis results
        """
        try:
            if not ball_positions or len(ball_positions) < 5:
                return self._get_default_analysis()
            
            self.trajectory_points = ball_positions
            
            # Smooth trajectory to reduce noise
            smoothed_trajectory = self._smooth_trajectory(ball_positions)
            
            # Find critical points
            self._find_critical_points(smoothed_trajectory)
            
            # Fit parabolic trajectory
            trajectory_params = self._fit_parabola(smoothed_trajectory)
            
            # Calculate trajectory metrics
            arc_angle = self._calculate_arc_angle(smoothed_trajectory)
            release_velocity = self._calculate_release_velocity(smoothed_trajectory, fps)
            peak_height = self._calculate_peak_height(smoothed_trajectory)
            entry_angle = self._calculate_entry_angle(smoothed_trajectory)
            
            # Predict shot success
            make_probability = self._predict_shot_success(
                arc_angle, entry_angle, peak_height, trajectory_params
            )
            
            # Calculate trajectory quality score
            quality_score = self._calculate_trajectory_quality(
                arc_angle, entry_angle, peak_height
            )
            
            return {
                'success': True,
                'arc_angle': round(arc_angle, 1),
                'release_velocity': round(release_velocity, 2),
                'peak_height': round(peak_height, 1),
                'entry_angle': round(entry_angle, 1),
                'make_probability': round(make_probability, 1),
                'quality_score': round(quality_score, 1),
                'trajectory_params': trajectory_params,
                'release_point': self.release_point,
                'peak_point': self.peak_point,
                'entry_point': self.entry_point,
                'trajectory_length': len(ball_positions),
                'smoothed_trajectory': smoothed_trajectory
            }
            
        except Exception as e:
            print(f"Error analyzing trajectory: {e}")
            return self._get_default_analysis()
    
    def _smooth_trajectory(self, positions: List[Tuple[int, int]]) -> np.ndarray:
        """
        Smooth trajectory using Savitzky-Golay filter
        
        Args:
            positions: List of (x, y) positions
            
        Returns:
            Smoothed trajectory as numpy array
        """
        try:
            if len(positions) < 5:
                return np.array(positions)
            
            # Convert to numpy array
            trajectory = np.array(positions)
            
            # Apply Savitzky-Golay filter to smooth trajectory
            window_length = min(11, len(positions) if len(positions) % 2 == 1 else len(positions) - 1)
            if window_length < 5:
                return trajectory
            
            smoothed_x = savgol_filter(trajectory[:, 0], window_length, 3)
            smoothed_y = savgol_filter(trajectory[:, 1], window_length, 3)
            
            return np.column_stack((smoothed_x, smoothed_y))
            
        except Exception as e:
            print(f"Error smoothing trajectory: {e}")
            return np.array(positions)
    
    def _find_critical_points(self, trajectory: np.ndarray):
        """
        Find release, peak, and entry points
        
        Args:
            trajectory: Smoothed trajectory array
        """
        try:
            if len(trajectory) < 3:
                return
            
            # Release point: first point (assumed)
            self.release_point = tuple(trajectory[0].astype(int))
            
            # Peak point: highest point (lowest y value in image coordinates)
            peak_idx = np.argmin(trajectory[:, 1])
            self.peak_point = tuple(trajectory[peak_idx].astype(int))
            
            # Entry point: last point (assumed)
            self.entry_point = tuple(trajectory[-1].astype(int))
            
        except Exception as e:
            print(f"Error finding critical points: {e}")
    
    def _fit_parabola(self, trajectory: np.ndarray) -> Optional[Dict]:
        """
        Fit parabolic curve to trajectory
        
        Args:
            trajectory: Trajectory points
            
        Returns:
            Dict with parabola parameters or None
        """
        try:
            if len(trajectory) < 5:
                return None
            
            x = trajectory[:, 0]
            y = trajectory[:, 1]
            
            # Fit quadratic: y = ax^2 + bx + c
            coeffs = np.polyfit(x, y, 2)
            a, b, c = coeffs
            
            # Calculate R-squared to measure fit quality
            y_pred = np.polyval(coeffs, x)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            
            return {
                'a': float(a),
                'b': float(b),
                'c': float(c),
                'r_squared': float(r_squared)
            }
            
        except Exception as e:
            print(f"Error fitting parabola: {e}")
            return None
    
    def _calculate_arc_angle(self, trajectory: np.ndarray) -> float:
        """
        Calculate shot arc angle at release
        
        Args:
            trajectory: Trajectory points
            
        Returns:
            Arc angle in degrees
        """
        try:
            if len(trajectory) < 3:
                return 0.0
            
            # Use first few points to calculate initial angle
            start_point = trajectory[0]
            mid_point = trajectory[min(3, len(trajectory) - 1)]
            
            dx = mid_point[0] - start_point[0]
            dy = start_point[1] - mid_point[1]  # Inverted y-axis
            
            if dx == 0:
                return 90.0
            
            angle_rad = np.arctan2(dy, dx)
            angle_deg = np.degrees(angle_rad)
            
            return max(0, min(90, angle_deg))
            
        except Exception as e:
            print(f"Error calculating arc angle: {e}")
            return 0.0
    
    def _calculate_release_velocity(self, trajectory: np.ndarray, fps: float) -> float:
        """
        Calculate initial release velocity
        
        Args:
            trajectory: Trajectory points
            fps: Frames per second
            
        Returns:
            Velocity in m/s
        """
        try:
            if len(trajectory) < 3:
                return 0.0
            
            # Calculate velocity from first few points
            start_point = trajectory[0]
            end_point = trajectory[min(3, len(trajectory) - 1)]
            
            # Distance in pixels
            dx = end_point[0] - start_point[0]
            dy = start_point[1] - end_point[1]  # Inverted y-axis
            distance_pixels = np.sqrt(dx**2 + dy**2)
            
            # Convert to meters
            distance_meters = distance_pixels / self.pixels_per_meter
            
            # Time elapsed
            time_seconds = min(3, len(trajectory) - 1) / fps
            
            if time_seconds == 0:
                return 0.0
            
            # Velocity
            velocity = distance_meters / time_seconds
            
            return max(0, velocity)
            
        except Exception as e:
            print(f"Error calculating release velocity: {e}")
            return 0.0
    
    def _calculate_peak_height(self, trajectory: np.ndarray) -> float:
        """
        Calculate peak height above release point
        
        Args:
            trajectory: Trajectory points
            
        Returns:
            Peak height in pixels
        """
        try:
            if len(trajectory) < 2:
                return 0.0
            
            release_y = trajectory[0, 1]
            peak_y = np.min(trajectory[:, 1])
            
            # Height difference (inverted y-axis)
            height = release_y - peak_y
            
            return max(0, height)
            
        except Exception as e:
            print(f"Error calculating peak height: {e}")
            return 0.0
    
    def _calculate_entry_angle(self, trajectory: np.ndarray) -> float:
        """
        Calculate entry angle at basket
        
        Args:
            trajectory: Trajectory points
            
        Returns:
            Entry angle in degrees
        """
        try:
            if len(trajectory) < 3:
                return 0.0
            
            # Use last few points to calculate entry angle
            end_point = trajectory[-1]
            mid_point = trajectory[max(0, len(trajectory) - 4)]
            
            dx = end_point[0] - mid_point[0]
            dy = end_point[1] - mid_point[1]  # Descending, so positive dy
            
            if dx == 0:
                return 90.0
            
            angle_rad = np.arctan2(dy, dx)
            angle_deg = np.degrees(angle_rad)
            
            return max(0, min(90, angle_deg))
            
        except Exception as e:
            print(f"Error calculating entry angle: {e}")
            return 0.0
    
    def _predict_shot_success(self, arc_angle: float, entry_angle: float, 
                             peak_height: float, trajectory_params: Optional[Dict]) -> float:
        """
        Predict shot success probability based on trajectory
        
        Args:
            arc_angle: Arc angle in degrees
            entry_angle: Entry angle in degrees
            peak_height: Peak height in pixels
            trajectory_params: Parabola fit parameters
            
        Returns:
            Probability of making the shot (0-100%)
        """
        try:
            # Base probability
            probability = 50.0
            
            # Arc angle scoring (ideal: 45°, acceptable: 40-50°)
            arc_diff = abs(arc_angle - self.ideal_arc_angle)
            if arc_diff < 5:
                probability += 15
            elif arc_diff < 10:
                probability += 10
            elif arc_diff < 15:
                probability += 5
            else:
                probability -= 10
            
            # Entry angle scoring (ideal: 45°, acceptable: 40-50°)
            entry_diff = abs(entry_angle - self.ideal_entry_angle)
            if entry_diff < 5:
                probability += 15
            elif entry_diff < 10:
                probability += 10
            elif entry_diff < 15:
                probability += 5
            else:
                probability -= 10
            
            # Peak height scoring (should be reasonable)
            if peak_height > 50:  # Sufficient arc
                probability += 10
            elif peak_height > 30:
                probability += 5
            else:
                probability -= 5
            
            # Trajectory smoothness (R-squared from parabola fit)
            if trajectory_params and 'r_squared' in trajectory_params:
                r_squared = trajectory_params['r_squared']
                if r_squared > 0.9:
                    probability += 10
                elif r_squared > 0.8:
                    probability += 5
                else:
                    probability -= 5
            
            # Clamp to 0-100 range
            return max(0, min(100, probability))
            
        except Exception as e:
            print(f"Error predicting shot success: {e}")
            return 50.0
    
    def _calculate_trajectory_quality(self, arc_angle: float, entry_angle: float, 
                                     peak_height: float) -> float:
        """
        Calculate overall trajectory quality score
        
        Args:
            arc_angle: Arc angle in degrees
            entry_angle: Entry angle in degrees
            peak_height: Peak height in pixels
            
        Returns:
            Quality score (0-100)
        """
        try:
            # Weighted scoring
            arc_score = max(0, 100 - abs(arc_angle - self.ideal_arc_angle) * 2)
            entry_score = max(0, 100 - abs(entry_angle - self.ideal_entry_angle) * 2)
            height_score = min(100, (peak_height / 100) * 100)  # Normalize to 100
            
            # Weighted average
            quality_score = (
                arc_score * 0.4 +
                entry_score * 0.4 +
                height_score * 0.2
            )
            
            return max(0, min(100, quality_score))
            
        except Exception as e:
            print(f"Error calculating trajectory quality: {e}")
            return 0.0
    
    def _get_default_analysis(self) -> Dict:
        """Get default analysis when calculation fails"""
        return {
            'success': False,
            'arc_angle': 0.0,
            'release_velocity': 0.0,
            'peak_height': 0.0,
            'entry_angle': 0.0,
            'make_probability': 50.0,
            'quality_score': 0.0,
            'trajectory_params': None,
            'release_point': None,
            'peak_point': None,
            'entry_point': None,
            'trajectory_length': 0,
            'smoothed_trajectory': []
        }
    
    def draw_trajectory(self, frame: np.ndarray, trajectory: List[Tuple[int, int]], 
                       color: Tuple[int, int, int] = (0, 255, 255)) -> np.ndarray:
        """
        Draw trajectory on frame
        
        Args:
            frame: OpenCV frame
            trajectory: List of (x, y) points
            color: BGR color tuple
            
        Returns:
            Annotated frame
        """
        if not trajectory or len(trajectory) < 2:
            return frame
        
        annotated = frame.copy()
        
        # Draw trajectory line
        for i in range(len(trajectory) - 1):
            pt1 = tuple(map(int, trajectory[i]))
            pt2 = tuple(map(int, trajectory[i + 1]))
            cv2.line(annotated, pt1, pt2, color, 2)
        
        # Draw critical points
        if self.release_point:
            cv2.circle(annotated, self.release_point, 5, (0, 255, 0), -1)
            cv2.putText(annotated, "Release", (self.release_point[0] + 10, self.release_point[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        if self.peak_point:
            cv2.circle(annotated, self.peak_point, 5, (255, 0, 0), -1)
            cv2.putText(annotated, "Peak", (self.peak_point[0] + 10, self.peak_point[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        if self.entry_point:
            cv2.circle(annotated, self.entry_point, 5, (0, 0, 255), -1)
            cv2.putText(annotated, "Entry", (self.entry_point[0] + 10, self.entry_point[1]),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        return annotated
    
    def reset(self):
        """Reset analyzer"""
        self.trajectory_points = []
        self.release_point = None
        self.peak_point = None
        self.entry_point = None


import cv2  # Import at top for draw_trajectory method

