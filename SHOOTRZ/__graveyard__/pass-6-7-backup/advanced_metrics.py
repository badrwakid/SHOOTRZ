"""
Advanced Basketball Shooting Metrics

Calculates 6 additional premium metrics beyond basic angles:
1. Follow-through angle (wrist snap consistency)
2. Shot arc trajectory (calculated from release angle + velocity)
3. Release point height (vertical position of release)
4. Jump timing (knee extension coordination with release)
5. Shot consistency score (variance across all metrics)
6. Body sway (lateral movement during shot)
"""

import numpy as np

class AdvancedMetricsCalculator:
    def __init__(self):
        """Initialize advanced metrics calculator"""
        self.frame_data = []
        self.release_frame = None
        self.dip_frame = None
        
    def calculate_advanced_metrics(self, keypoints_list, basic_metrics):
        """
        Calculate all 6 advanced metrics
        
        Args:
            keypoints_list: List of keypoint dictionaries from video frames
            basic_metrics: Basic metrics (elbow, knee, release, alignment)
            
        Returns:
            dict: Advanced metrics with scores and explanations
        """
        try:
            if not keypoints_list or len(keypoints_list) < 10:
                return self._get_default_advanced_metrics()
            
            self.frame_data = self._prepare_frame_data(keypoints_list)
            self._detect_critical_frames()
            
            metrics = {}
            
            # 1. Follow-through angle
            metrics['follow_through_angle'] = self._calculate_follow_through_angle()
            
            # 2. Shot arc trajectory
            metrics['shot_arc'] = self._calculate_shot_arc()
            
            # 3. Release point height
            metrics['release_height'] = self._calculate_release_height()
            
            # 4. Jump timing
            metrics['jump_timing'] = self._calculate_jump_timing()
            
            # 5. Shot consistency score
            metrics['consistency_score'] = self._calculate_consistency_score(basic_metrics)
            
            # 6. Body sway
            metrics['body_sway'] = self._calculate_body_sway()
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating advanced metrics: {e}")
            return self._get_default_advanced_metrics()
    
    def _prepare_frame_data(self, keypoints_list):
        """Prepare frame data for analysis"""
        try:
            frame_data = []
            for i, keypoints in enumerate(keypoints_list):
                if not keypoints:
                    continue
                
                frame_info = {
                    'frame_number': i,
                    'keypoints': keypoints,
                    'timestamp': i / 30.0,  # Assuming 30 FPS
                }
                
                # Calculate basic metrics for this frame
                frame_info['elbow_angle'] = self._calculate_frame_elbow_angle(keypoints)
                frame_info['knee_angle'] = self._calculate_frame_knee_angle(keypoints)
                frame_info['release_angle'] = self._calculate_frame_release_angle(keypoints)
                frame_info['body_alignment'] = self._calculate_frame_body_alignment(keypoints)
                
                frame_data.append(frame_info)
            
            return frame_data
        except Exception as e:
            print(f"Error preparing frame data: {e}")
            return []
    
    def _detect_critical_frames(self):
        """Detect critical frames in the shooting sequence"""
        try:
            if not self.frame_data:
                return
            
            # Find release frame (highest ball position)
            ball_positions = []
            for frame in self.frame_data:
                if 'right_wrist' in frame['keypoints'] and frame['keypoints']['right_wrist']:
                    ball_positions.append((frame['frame_number'], frame['keypoints']['right_wrist'][1]))
            
            if ball_positions:
                # Find the highest point (lowest Y value in image coordinates)
                self.release_frame = min(ball_positions, key=lambda x: x[1])[0]
            
            # Find dip frame (lowest ball position)
            if ball_positions:
                self.dip_frame = max(ball_positions, key=lambda x: x[1])[0]
            
        except Exception as e:
            print(f"Error detecting critical frames: {e}")
    
    def _calculate_follow_through_angle(self):
        """Calculate follow-through angle consistency"""
        try:
            if not self.frame_data or self.release_frame is None:
                return 0.0
            
            # Get frames after release
            follow_through_frames = [f for f in self.frame_data if f['frame_number'] > self.release_frame]
            
            if len(follow_through_frames) < 3:
                return 0.0
            
            # Calculate wrist-to-elbow angle during follow-through
            follow_through_angles = []
            for frame in follow_through_frames:
                angle = self._calculate_wrist_elbow_angle(frame['keypoints'])
                if angle is not None:
                    follow_through_angles.append(angle)
            
            if len(follow_through_angles) < 2:
                return 0.0
            
            # Calculate consistency (lower variance = better)
            angle_variance = np.var(follow_through_angles)
            consistency = max(0, 100 - (angle_variance * 2))
            
            return round(consistency, 1)
            
        except Exception as e:
            print(f"Error calculating follow-through angle: {e}")
            return 0.0
    
    def _calculate_shot_arc(self):
        """Calculate shot arc trajectory"""
        try:
            if not self.frame_data or self.release_frame is None:
                return 0.0
            
            # Get ball trajectory from dip to release
            dip_to_release = [f for f in self.frame_data 
                            if self.dip_frame <= f['frame_number'] <= self.release_frame]
            
            if len(dip_to_release) < 5:
                return 0.0
            
            # Calculate trajectory points
            trajectory_points = []
            for frame in dip_to_release:
                if 'right_wrist' in frame['keypoints'] and frame['keypoints']['right_wrist']:
                    pos = frame['keypoints']['right_wrist']
                    trajectory_points.append([pos[0], pos[1]])  # x, y coordinates
            
            if len(trajectory_points) < 3:
                return 0.0
            
            # Fit a parabola to the trajectory
            trajectory_array = np.array(trajectory_points)
            x = trajectory_array[:, 0]
            y = trajectory_array[:, 1]
            
            # Fit quadratic curve: y = ax² + bx + c
            try:
                coeffs = np.polyfit(x, y, 2)
                a, b, c = coeffs
                
                # Calculate arc height (vertex of parabola)
                vertex_x = -b / (2 * a) if a != 0 else 0
                vertex_y = a * vertex_x**2 + b * vertex_x + c
                
                # Calculate arc angle (steepness)
                if len(trajectory_points) >= 2:
                    start_y = trajectory_points[0][1]
                    end_y = trajectory_points[-1][1]
                    height_diff = start_y - end_y
                    horizontal_dist = abs(trajectory_points[-1][0] - trajectory_points[0][0])
                    
                    if horizontal_dist > 0:
                        arc_angle = np.degrees(np.arctan(height_diff / horizontal_dist))
                        return round(abs(arc_angle), 1)
                
                return 0.0
                
            except:
                return 0.0
            
        except Exception as e:
            print(f"Error calculating shot arc: {e}")
            return 0.0
    
    def _calculate_release_height(self):
        """Calculate release point height"""
        try:
            if not self.frame_data or self.release_frame is None:
                return 0.0
            
            # Find release frame
            release_frame = next((f for f in self.frame_data if f['frame_number'] == self.release_frame), None)
            if not release_frame:
                return 0.0
            
            # Get release point (wrist position at release)
            if 'right_wrist' in release_frame['keypoints'] and release_frame['keypoints']['right_wrist']:
                release_y = release_frame['keypoints']['right_wrist'][1]
                
                # Get reference point (ankle) for relative height
                if 'right_ankle' in release_frame['keypoints'] and release_frame['keypoints']['right_ankle']:
                    ankle_y = release_frame['keypoints']['right_ankle'][1]
                    relative_height = ankle_y - release_y  # Higher release = lower Y value
                    return round(relative_height, 1)
            
            return 0.0
            
        except Exception as e:
            print(f"Error calculating release height: {e}")
            return 0.0
    
    def _calculate_jump_timing(self):
        """Calculate jump timing coordination"""
        try:
            if not self.frame_data or self.release_frame is None:
                return 0.0
            
            # Track knee extension timing relative to release
            knee_angles = []
            frame_numbers = []
            
            for frame in self.frame_data:
                if frame['knee_angle'] is not None:
                    knee_angles.append(frame['knee_angle'])
                    frame_numbers.append(frame['frame_number'])
            
            if len(knee_angles) < 5:
                return 0.0
            
            # Find when knee starts extending (angle increases)
            knee_changes = np.diff(knee_angles)
            extension_start = None
            
            for i, change in enumerate(knee_changes):
                if change > 2:  # Significant knee extension
                    extension_start = frame_numbers[i]
                    break
            
            if extension_start is None:
                return 0.0
            
            # Calculate timing relative to release
            timing_diff = self.release_frame - extension_start
            
            # Optimal timing: knee extension starts 2-5 frames before release
            if 2 <= timing_diff <= 5:
                timing_score = 100
            elif timing_diff < 2:
                timing_score = max(0, 100 - (2 - timing_diff) * 20)  # Too late
            else:
                timing_score = max(0, 100 - (timing_diff - 5) * 10)  # Too early
            
            return round(timing_score, 1)
            
        except Exception as e:
            print(f"Error calculating jump timing: {e}")
            return 0.0
    
    def _calculate_consistency_score(self, basic_metrics):
        """Calculate overall shot consistency"""
        try:
            if not self.frame_data:
                return 0.0
            
            # Calculate variance for each metric across all frames
            metrics_variance = {}
            
            for metric in ['elbow_angle', 'knee_angle', 'release_angle', 'body_alignment']:
                values = [f[metric] for f in self.frame_data if f[metric] is not None]
                if len(values) > 1:
                    metrics_variance[metric] = np.var(values)
                else:
                    metrics_variance[metric] = 0
            
            # Calculate consistency score (lower variance = higher consistency)
            if metrics_variance:
                avg_variance = np.mean(list(metrics_variance.values()))
                consistency = max(0, 100 - (avg_variance * 0.5))  # Scale variance to 0-100
                return round(consistency, 1)
            
            return 0.0
            
        except Exception as e:
            print(f"Error calculating consistency score: {e}")
            return 0.0
    
    def _calculate_body_sway(self):
        """Calculate lateral body sway during shot"""
        try:
            if not self.frame_data:
                return 0.0
            
            # Track hip center position over time
            hip_centers = []
            for frame in self.frame_data:
                if all(k in frame['keypoints'] and frame['keypoints'][k] for k in ['left_hip', 'right_hip']):
                    left_hip = frame['keypoints']['left_hip']
                    right_hip = frame['keypoints']['right_hip']
                    center_x = (left_hip[0] + right_hip[0]) / 2
                    hip_centers.append(center_x)
            
            if len(hip_centers) < 3:
                return 0.0
            
            # Calculate lateral movement (sway)
            hip_variance = np.var(hip_centers)
            sway_score = max(0, 100 - (hip_variance * 0.1))  # Lower variance = better stability
            
            return round(sway_score, 1)
            
        except Exception as e:
            print(f"Error calculating body sway: {e}")
            return 0.0
    
    def _calculate_wrist_elbow_angle(self, keypoints):
        """Calculate angle between wrist and elbow for follow-through analysis"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['right_wrist', 'right_elbow', 'right_shoulder']):
                return None
            
            wrist = np.array(keypoints['right_wrist'])
            elbow = np.array(keypoints['right_elbow'])
            shoulder = np.array(keypoints['right_shoulder'])
            
            # Calculate angle at elbow
            v1 = shoulder - elbow
            v2 = wrist - elbow
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            
            return np.degrees(np.arccos(cos_angle))
        except:
            return None
    
    def _calculate_frame_elbow_angle(self, keypoints):
        """Calculate elbow angle for a single frame"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['right_shoulder', 'right_elbow', 'right_wrist']):
                return None
            
            shoulder = np.array(keypoints['right_shoulder'])
            elbow = np.array(keypoints['right_elbow'])
            wrist = np.array(keypoints['right_wrist'])
            
            v1 = shoulder - elbow
            v2 = wrist - elbow
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            
            return np.degrees(np.arccos(cos_angle))
        except:
            return None
    
    def _calculate_frame_knee_angle(self, keypoints):
        """Calculate knee angle for a single frame"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['right_hip', 'right_knee', 'right_ankle']):
                return None
            
            hip = np.array(keypoints['right_hip'])
            knee = np.array(keypoints['right_knee'])
            ankle = np.array(keypoints['right_ankle'])
            
            v1 = hip - knee
            v2 = ankle - knee
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            
            return np.degrees(np.arccos(cos_angle))
        except:
            return None
    
    def _calculate_frame_release_angle(self, keypoints):
        """Calculate release angle for a single frame"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['right_shoulder', 'right_elbow', 'right_wrist']):
                return None
            
            shoulder = np.array(keypoints['right_shoulder'])
            elbow = np.array(keypoints['right_elbow'])
            wrist = np.array(keypoints['right_wrist'])
            
            vector = wrist - elbow
            angle_rad = np.arctan2(vector[1], vector[0])
            return abs(np.degrees(angle_rad))
        except:
            return None
    
    def _calculate_frame_body_alignment(self, keypoints):
        """Calculate body alignment for a single frame"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']):
                return None
            
            left_shoulder = np.array(keypoints['left_shoulder'])
            right_shoulder = np.array(keypoints['right_shoulder'])
            left_hip = np.array(keypoints['left_hip'])
            right_hip = np.array(keypoints['right_hip'])
            
            shoulder_mid = (left_shoulder + right_shoulder) / 2
            hip_mid = (left_hip + right_hip) / 2
            
            deviation = abs(shoulder_mid[0] - hip_mid[0])
            max_deviation = 50  # pixels
            
            alignment = max(0, 100 - (deviation / max_deviation * 100))
            return alignment
        except:
            return None
    
    def _get_default_advanced_metrics(self):
        """Get default advanced metrics when calculation fails"""
        return {
            'follow_through_angle': 0.0,
            'shot_arc': 0.0,
            'release_height': 0.0,
            'jump_timing': 0.0,
            'consistency_score': 0.0,
            'body_sway': 0.0
        }


