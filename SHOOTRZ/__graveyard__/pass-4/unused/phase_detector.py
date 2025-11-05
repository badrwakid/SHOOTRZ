"""
Shooting Phase Detection System

Detects and analyzes the four critical phases of a basketball shot:
1. Setup (0-30%): Initial stance and alignment
2. Dip (30-50%): Knee bend and ball positioning
3. Release (50-80%): Release angle and follow-through start
4. Follow-Through (80-100%): Wrist snap and arm extension
"""

import numpy as np

class PhaseDetector:
    def __init__(self):
        """Initialize phase detection system"""
        self.phases = {
            'setup': {'start': 0.0, 'end': 0.3, 'frames': [], 'metrics': {}},
            'dip': {'start': 0.3, 'end': 0.5, 'frames': [], 'metrics': {}},
            'release': {'start': 0.5, 'end': 0.8, 'frames': [], 'metrics': {}},
            'follow_through': {'start': 0.8, 'end': 1.0, 'frames': [], 'metrics': {}}
        }
        self.total_frames = 0
        self.phase_boundaries = []
        
    def detect_phases(self, keypoints_list):
        """
        Detect shooting phases from keypoints sequence
        
        Args:
            keypoints_list: List of keypoint dictionaries from video frames
            
        Returns:
            dict: Phase analysis results
        """
        try:
            if not keypoints_list or len(keypoints_list) < 10:
                return self._get_default_phases()
            
            self.total_frames = len(keypoints_list)
            
            # Detect key moments in the shot
            key_moments = self._detect_key_moments(keypoints_list)
            
            # Adjust phase boundaries based on key moments
            adjusted_phases = self._adjust_phase_boundaries(key_moments)
            
            # Analyze each phase
            phase_results = {}
            for phase_name, phase_info in adjusted_phases.items():
                phase_frames = self._get_phase_frames(keypoints_list, phase_info)
                phase_metrics = self._analyze_phase_metrics(phase_frames, phase_name)
                
                phase_results[phase_name] = {
                    'start_frame': phase_info['start_frame'],
                    'end_frame': phase_info['end_frame'],
                    'duration': phase_info['end_frame'] - phase_info['start_frame'],
                    'metrics': phase_metrics,
                    'score': self._calculate_phase_score(phase_metrics, phase_name),
                    'feedback': self._generate_phase_feedback(phase_metrics, phase_name)
                }
            
            return phase_results
            
        except Exception as e:
            print(f"Error detecting phases: {e}")
            return self._get_default_phases()
    
    def _detect_key_moments(self, keypoints_list):
        """Detect key moments in the shooting sequence"""
        try:
            key_moments = {
                'ball_dip_start': 0,
                'ball_dip_end': 0,
                'release_start': 0,
                'release_peak': 0,
                'follow_through_start': 0
            }
            
            # Track ball position (wrist) over time
            wrist_positions = []
            for keypoints in keypoints_list:
                if keypoints and 'right_wrist' in keypoints and keypoints['right_wrist']:
                    wrist_positions.append(keypoints['right_wrist'][1])  # Y position
                else:
                    wrist_positions.append(None)
            
            # Find ball dip (lowest point)
            valid_positions = [(i, pos) for i, pos in enumerate(wrist_positions) if pos is not None]
            if valid_positions:
                # Find the lowest point (highest Y value in image coordinates)
                lowest_point = max(valid_positions, key=lambda x: x[1])
                key_moments['ball_dip_end'] = lowest_point[0]
                
                # Find dip start (where ball starts going down)
                for i in range(lowest_point[0]):
                    if wrist_positions[i] is not None and wrist_positions[i] < lowest_point[1] - 20:
                        key_moments['ball_dip_start'] = i
                        break
            
            # Find release start (ball starts going up from dip)
            for i in range(key_moments['ball_dip_end'], len(wrist_positions)):
                if wrist_positions[i] is not None and wrist_positions[i] < lowest_point[1] - 10:
                    key_moments['release_start'] = i
                    break
            
            # Find release peak (highest point)
            if key_moments['release_start'] > 0:
                release_phase = wrist_positions[key_moments['release_start']:]
                valid_release = [(i + key_moments['release_start'], pos) for i, pos in enumerate(release_phase) if pos is not None]
                if valid_release:
                    highest_point = min(valid_release, key=lambda x: x[1])  # Lowest Y value (highest in image)
                    key_moments['release_peak'] = highest_point[0]
            
            # Find follow-through start (after release peak)
            key_moments['follow_through_start'] = key_moments['release_peak'] + 5
            
            return key_moments
            
        except Exception as e:
            print(f"Error detecting key moments: {e}")
            return {
                'ball_dip_start': 0,
                'ball_dip_end': int(len(keypoints_list) * 0.3),
                'release_start': int(len(keypoints_list) * 0.5),
                'release_peak': int(len(keypoints_list) * 0.7),
                'follow_through_start': int(len(keypoints_list) * 0.8)
            }
    
    def _adjust_phase_boundaries(self, key_moments):
        """Adjust phase boundaries based on detected key moments"""
        try:
            total_frames = self.total_frames
            
            # Setup: 0 to dip start
            setup_end = key_moments['ball_dip_start'] if key_moments['ball_dip_start'] > 0 else int(total_frames * 0.3)
            
            # Dip: dip start to release start
            dip_start = setup_end
            dip_end = key_moments['release_start'] if key_moments['release_start'] > 0 else int(total_frames * 0.5)
            
            # Release: release start to follow-through start
            release_start = dip_end
            release_end = key_moments['follow_through_start'] if key_moments['follow_through_start'] > 0 else int(total_frames * 0.8)
            
            # Follow-through: follow-through start to end
            follow_through_start = release_end
            follow_through_end = total_frames - 1
            
            return {
                'setup': {'start_frame': 0, 'end_frame': setup_end},
                'dip': {'start_frame': dip_start, 'end_frame': dip_end},
                'release': {'start_frame': release_start, 'end_frame': release_end},
                'follow_through': {'start_frame': follow_through_start, 'end_frame': follow_through_end}
            }
            
        except Exception as e:
            print(f"Error adjusting phase boundaries: {e}")
            return self._get_default_phase_boundaries()
    
    def _get_phase_frames(self, keypoints_list, phase_info):
        """Get frames for a specific phase"""
        try:
            start_frame = max(0, phase_info['start_frame'])
            end_frame = min(len(keypoints_list), phase_info['end_frame'])
            
            return keypoints_list[start_frame:end_frame]
            
        except Exception as e:
            print(f"Error getting phase frames: {e}")
            return []
    
    def _analyze_phase_metrics(self, phase_frames, phase_name):
        """Analyze metrics for a specific phase"""
        try:
            if not phase_frames:
                return {}
            
            # Calculate basic metrics for this phase
            elbow_angles = []
            knee_angles = []
            release_angles = []
            body_alignments = []
            
            for keypoints in phase_frames:
                if not keypoints:
                    continue
                
                # Calculate angles for this frame
                elbow_angle = self._calculate_elbow_angle(keypoints)
                knee_angle = self._calculate_knee_angle(keypoints)
                release_angle = self._calculate_release_angle(keypoints)
                body_alignment = self._calculate_body_alignment(keypoints)
                
                if elbow_angle is not None:
                    elbow_angles.append(elbow_angle)
                if knee_angle is not None:
                    knee_angles.append(knee_angle)
                if release_angle is not None:
                    release_angles.append(release_angle)
                if body_alignment is not None:
                    body_alignments.append(body_alignment)
            
            # Calculate phase-specific metrics
            metrics = {
                'elbow_angle': np.mean(elbow_angles) if elbow_angles else 0,
                'knee_angle': np.mean(knee_angles) if knee_angles else 0,
                'release_angle': np.mean(release_angles) if release_angles else 0,
                'body_alignment': np.mean(body_alignments) if body_alignments else 0,
                'frame_count': len(phase_frames)
            }
            
            # Add phase-specific metrics
            if phase_name == 'setup':
                metrics['stance_stability'] = self._calculate_stance_stability(phase_frames)
                metrics['initial_alignment'] = metrics['body_alignment']
            elif phase_name == 'dip':
                metrics['dip_depth'] = self._calculate_dip_depth(phase_frames)
                metrics['knee_bend_consistency'] = self._calculate_knee_consistency(knee_angles)
            elif phase_name == 'release':
                metrics['release_consistency'] = self._calculate_release_consistency(release_angles)
                metrics['power_transfer'] = self._calculate_power_transfer(phase_frames)
            elif phase_name == 'follow_through':
                metrics['follow_through_extension'] = self._calculate_follow_through_extension(phase_frames)
                metrics['wrist_snap'] = self._calculate_wrist_snap(phase_frames)
            
            return metrics
            
        except Exception as e:
            print(f"Error analyzing phase metrics: {e}")
            return {}
    
    def _calculate_elbow_angle(self, keypoints):
        """Calculate elbow angle for a frame"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['right_shoulder', 'right_elbow', 'right_wrist']):
                return None
            
            shoulder = np.array(keypoints['right_shoulder'])
            elbow = np.array(keypoints['right_elbow'])
            wrist = np.array(keypoints['right_wrist'])
            
            # Calculate angle using vector math
            v1 = shoulder - elbow
            v2 = wrist - elbow
            
            cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            
            return np.degrees(np.arccos(cos_angle))
        except:
            return None
    
    def _calculate_knee_angle(self, keypoints):
        """Calculate knee angle for a frame"""
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
    
    def _calculate_release_angle(self, keypoints):
        """Calculate release angle for a frame"""
        try:
            if not all(k in keypoints and keypoints[k] for k in ['right_shoulder', 'right_elbow', 'right_wrist']):
                return None
            
            shoulder = np.array(keypoints['right_shoulder'])
            elbow = np.array(keypoints['right_elbow'])
            wrist = np.array(keypoints['right_wrist'])
            
            # Calculate angle relative to horizontal
            vector = wrist - elbow
            angle_rad = np.arctan2(vector[1], vector[0])
            return abs(np.degrees(angle_rad))
        except:
            return None
    
    def _calculate_body_alignment(self, keypoints):
        """Calculate body alignment for a frame"""
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
    
    def _calculate_stance_stability(self, phase_frames):
        """Calculate stance stability during setup phase"""
        try:
            if len(phase_frames) < 2:
                return 0.0
            
            # Track hip position stability
            hip_positions = []
            for keypoints in phase_frames:
                if keypoints and 'right_hip' in keypoints and keypoints['right_hip']:
                    hip_positions.append(keypoints['right_hip'])
            
            if len(hip_positions) < 2:
                return 0.0
            
            # Calculate position variance
            hip_array = np.array(hip_positions)
            variance = np.var(hip_array, axis=0)
            stability = max(0, 100 - np.mean(variance))
            
            return round(stability, 1)
        except:
            return 0.0
    
    def _calculate_dip_depth(self, phase_frames):
        """Calculate ball dip depth during dip phase"""
        try:
            if not phase_frames:
                return 0.0
            
            # Track wrist (ball) position
            wrist_positions = []
            for keypoints in phase_frames:
                if keypoints and 'right_wrist' in keypoints and keypoints['right_wrist']:
                    wrist_positions.append(keypoints['right_wrist'][1])  # Y position
            
            if len(wrist_positions) < 2:
                return 0.0
            
            # Calculate dip depth (how much the ball went down)
            start_y = wrist_positions[0]
            min_y = min(wrist_positions)
            dip_depth = start_y - min_y
            
            return round(dip_depth, 1)
        except:
            return 0.0
    
    def _calculate_knee_consistency(self, knee_angles):
        """Calculate knee bend consistency during dip phase"""
        try:
            if len(knee_angles) < 2:
                return 0.0
            
            # Calculate coefficient of variation
            mean_angle = np.mean(knee_angles)
            std_angle = np.std(knee_angles)
            cv = std_angle / mean_angle if mean_angle > 0 else 1
            
            consistency = max(0, 100 - (cv * 100))
            return round(consistency, 1)
        except:
            return 0.0
    
    def _calculate_release_consistency(self, release_angles):
        """Calculate release angle consistency during release phase"""
        try:
            if len(release_angles) < 2:
                return 0.0
            
            # Calculate standard deviation
            std_angle = np.std(release_angles)
            consistency = max(0, 100 - (std_angle * 2))  # Scale std to 0-100
            
            return round(consistency, 1)
        except:
            return 0.0
    
    def _calculate_power_transfer(self, phase_frames):
        """Calculate power transfer efficiency during release phase"""
        try:
            if len(phase_frames) < 3:
                return 0.0
            
            # Track knee and elbow coordination
            knee_angles = []
            elbow_angles = []
            
            for keypoints in phase_frames:
                knee_angle = self._calculate_knee_angle(keypoints)
                elbow_angle = self._calculate_elbow_angle(keypoints)
                
                if knee_angle is not None:
                    knee_angles.append(knee_angle)
                if elbow_angle is not None:
                    elbow_angles.append(elbow_angle)
            
            if len(knee_angles) < 2 or len(elbow_angles) < 2:
                return 0.0
            
            # Calculate correlation between knee extension and elbow extension
            # Good power transfer = knee extends as elbow extends
            knee_change = np.diff(knee_angles)
            elbow_change = np.diff(elbow_angles)
            
            if len(knee_change) > 0 and len(elbow_change) > 0:
                correlation = np.corrcoef(knee_change, elbow_change)[0, 1]
                power_transfer = max(0, (correlation + 1) * 50)  # Convert to 0-100
                return round(power_transfer, 1)
            
            return 0.0
        except:
            return 0.0
    
    def _calculate_follow_through_extension(self, phase_frames):
        """Calculate follow-through arm extension"""
        try:
            if not phase_frames:
                return 0.0
            
            # Track elbow angle during follow-through
            elbow_angles = []
            for keypoints in phase_frames:
                elbow_angle = self._calculate_elbow_angle(keypoints)
                if elbow_angle is not None:
                    elbow_angles.append(elbow_angle)
            
            if len(elbow_angles) < 2:
                return 0.0
            
            # Good follow-through = elbow extends (angle increases)
            start_angle = elbow_angles[0]
            end_angle = elbow_angles[-1]
            extension = end_angle - start_angle
            
            # Score based on extension (more extension = better)
            extension_score = min(100, max(0, extension * 2))
            return round(extension_score, 1)
        except:
            return 0.0
    
    def _calculate_wrist_snap(self, phase_frames):
        """Calculate wrist snap quality during follow-through"""
        try:
            if len(phase_frames) < 3:
                return 0.0
            
            # Track wrist position relative to elbow
            wrist_elbow_distances = []
            for keypoints in phase_frames:
                if all(k in keypoints and keypoints[k] for k in ['right_wrist', 'right_elbow']):
                    wrist = np.array(keypoints['right_wrist'])
                    elbow = np.array(keypoints['right_elbow'])
                    distance = np.linalg.norm(wrist - elbow)
                    wrist_elbow_distances.append(distance)
            
            if len(wrist_elbow_distances) < 3:
                return 0.0
            
            # Good wrist snap = increasing distance (arm extending)
            distance_change = np.diff(wrist_elbow_distances)
            positive_changes = sum(1 for change in distance_change if change > 0)
            snap_quality = (positive_changes / len(distance_change)) * 100
            
            return round(snap_quality, 1)
        except:
            return 0.0
    
    def _calculate_phase_score(self, metrics, phase_name):
        """Calculate overall score for a phase"""
        try:
            if not metrics:
                return 0.0
            
            # Base score from angle quality
            base_score = 0.0
            angle_count = 0
            
            if 'elbow_angle' in metrics and metrics['elbow_angle'] > 0:
                # Elbow angle scoring (ideal: 90°)
                elbow_score = max(0, 100 - abs(metrics['elbow_angle'] - 90) * 2)
                base_score += elbow_score
                angle_count += 1
            
            if 'knee_angle' in metrics and metrics['knee_angle'] > 0:
                # Knee angle scoring (ideal: 120-140°)
                knee_angle = metrics['knee_angle']
                if 120 <= knee_angle <= 140:
                    knee_score = 100
                else:
                    knee_score = max(0, 100 - abs(knee_angle - 130) * 1.5)
                base_score += knee_score
                angle_count += 1
            
            if 'release_angle' in metrics and metrics['release_angle'] > 0:
                # Release angle scoring (ideal: 45-50°)
                release_angle = metrics['release_angle']
                if 45 <= release_angle <= 50:
                    release_score = 100
                else:
                    release_score = max(0, 100 - abs(release_angle - 47.5) * 3)
                base_score += release_score
                angle_count += 1
            
            if 'body_alignment' in metrics:
                base_score += metrics['body_alignment']
                angle_count += 1
            
            # Average base score
            if angle_count > 0:
                base_score = base_score / angle_count
            
            # Add phase-specific bonuses
            phase_bonus = 0.0
            if phase_name == 'setup' and 'stance_stability' in metrics:
                phase_bonus += metrics['stance_stability'] * 0.1
            elif phase_name == 'dip' and 'dip_depth' in metrics:
                phase_bonus += min(10, metrics['dip_depth'] * 0.1)
            elif phase_name == 'release' and 'power_transfer' in metrics:
                phase_bonus += metrics['power_transfer'] * 0.1
            elif phase_name == 'follow_through' and 'follow_through_extension' in metrics:
                phase_bonus += metrics['follow_through_extension'] * 0.1
            
            final_score = min(100, base_score + phase_bonus)
            return round(final_score, 1)
            
        except Exception as e:
            print(f"Error calculating phase score: {e}")
            return 0.0
    
    def _generate_phase_feedback(self, metrics, phase_name):
        """Generate feedback for a specific phase"""
        try:
            feedback = []
            
            if phase_name == 'setup':
                if 'stance_stability' in metrics and metrics['stance_stability'] < 70:
                    feedback.append("Work on maintaining a stable stance throughout your setup")
                if 'body_alignment' in metrics and metrics['body_alignment'] < 80:
                    feedback.append("Keep your shoulders aligned with your hips for better balance")
            
            elif phase_name == 'dip':
                if 'dip_depth' in metrics and metrics['dip_depth'] < 20:
                    feedback.append("Add more dip to generate power for your shot")
                if 'knee_consistency' in metrics and metrics['knee_consistency'] < 70:
                    feedback.append("Maintain consistent knee bend throughout the dip")
            
            elif phase_name == 'release':
                if 'release_consistency' in metrics and metrics['release_consistency'] < 80:
                    feedback.append("Focus on consistent release angle for better accuracy")
                if 'power_transfer' in metrics and metrics['power_transfer'] < 70:
                    feedback.append("Coordinate your knee extension with your arm movement")
            
            elif phase_name == 'follow_through':
                if 'follow_through_extension' in metrics and metrics['follow_through_extension'] < 60:
                    feedback.append("Extend your arm fully through the shot for better follow-through")
                if 'wrist_snap' in metrics and metrics['wrist_snap'] < 70:
                    feedback.append("Add more wrist snap to your follow-through")
            
            return feedback if feedback else ["Good form in this phase!"]
            
        except Exception as e:
            print(f"Error generating phase feedback: {e}")
            return ["Phase analysis completed"]
    
    def _get_default_phases(self):
        """Get default phase structure when detection fails"""
        return {
            'setup': {
                'start_frame': 0,
                'end_frame': 0,
                'duration': 0,
                'metrics': {},
                'score': 0.0,
                'feedback': ['Phase detection failed']
            },
            'dip': {
                'start_frame': 0,
                'end_frame': 0,
                'duration': 0,
                'metrics': {},
                'score': 0.0,
                'feedback': ['Phase detection failed']
            },
            'release': {
                'start_frame': 0,
                'end_frame': 0,
                'duration': 0,
                'metrics': {},
                'score': 0.0,
                'feedback': ['Phase detection failed']
            },
            'follow_through': {
                'start_frame': 0,
                'end_frame': 0,
                'duration': 0,
                'metrics': {},
                'score': 0.0,
                'feedback': ['Phase detection failed']
            }
        }
    
    def _get_default_phase_boundaries(self):
        """Get default phase boundaries when detection fails"""
        total_frames = self.total_frames
        return {
            'setup': {'start_frame': 0, 'end_frame': int(total_frames * 0.3)},
            'dip': {'start_frame': int(total_frames * 0.3), 'end_frame': int(total_frames * 0.5)},
            'release': {'start_frame': int(total_frames * 0.5), 'end_frame': int(total_frames * 0.8)},
            'follow_through': {'start_frame': int(total_frames * 0.8), 'end_frame': total_frames - 1}
        }


