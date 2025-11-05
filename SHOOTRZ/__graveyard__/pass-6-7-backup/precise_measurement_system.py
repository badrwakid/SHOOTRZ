"""
Precise Measurement System

Measures angles at EXACT moments defined by research:
- Elbow at cocking (dip bottom)
- Elbow at release (peak)
- Knee at loading (dip bottom)
- Knee at release (peak)
- All other angles at research-defined moments
"""

import numpy as np
from typing import Dict, List, Optional, Tuple

class PreciseMeasurementSystem:
    """
    Take measurements at exact frames instead of averaging
    """
    
    def __init__(self):
        """Initialize precise measurement system"""
        self.measurements = {}
        self.confidence_scores = {}
    
    def measure_at_key_frames(self, keypoints_sequence: List[Dict], 
                              key_frames: Dict,
                              measurement_frames: Dict) -> Dict:
        """
        Measure angles at specific key frames
        
        Args:
            keypoints_sequence: All keypoints for each frame
            key_frames: Key moments (dip, release, etc.)
            measurement_frames: Specific frames to measure each angle
            
        Returns:
            Dict with precise measurements
        """
        try:
            measurements = {}
            
            # Detect shooting hand
            shooting_hand = self._detect_shooting_hand(keypoints_sequence)
            measurements['shooting_hand'] = shooting_hand
            
            print(f"   Shooting hand detected: {shooting_hand} (type: {type(shooting_hand)})")
            
            # Ensure shooting_hand is a string
            if not isinstance(shooting_hand, str):
                print(f"   ⚠️ Warning: shooting_hand is not a string, converting...")
                shooting_hand = str(shooting_hand)
            
            # Helper function to validate frame number
            def is_valid_frame(frame_num):
                if frame_num is None:
                    return False
                try:
                    frame_int = int(frame_num)
                    return 0 <= frame_int < len(keypoints_sequence)
                except (ValueError, TypeError):
                    return False
            
            # Measure elbow at cocking (dip bottom)
            elbow_cocking_frame = measurement_frames.get('elbow_at_cocking')
            if is_valid_frame(elbow_cocking_frame):
                elbow_cocking = self._measure_elbow_at_frame(
                    keypoints_sequence, int(elbow_cocking_frame), shooting_hand
                )
                measurements['elbow_at_cocking'] = elbow_cocking
            
            # Measure elbow at release (peak)
            elbow_release_frame = measurement_frames.get('elbow_at_release')
            if is_valid_frame(elbow_release_frame):
                elbow_release = self._measure_elbow_at_frame(
                    keypoints_sequence, int(elbow_release_frame), shooting_hand
                )
                measurements['elbow_at_release'] = elbow_release
                measurements['elbow_angle'] = elbow_release  # Primary measurement
            
            # Measure knee at loading (dip bottom)
            knee_loading_frame = measurement_frames.get('knee_at_loading')
            if is_valid_frame(knee_loading_frame):
                knee_loading = self._measure_knee_at_frame(
                    keypoints_sequence, int(knee_loading_frame), shooting_hand
                )
                measurements['knee_at_loading'] = knee_loading
            
            # Measure knee at release (peak)
            knee_release_frame = measurement_frames.get('knee_at_release')
            if is_valid_frame(knee_release_frame):
                knee_release = self._measure_knee_at_frame(
                    keypoints_sequence, int(knee_release_frame), shooting_hand
                )
                measurements['knee_at_release'] = knee_release
                measurements['knee_angle'] = knee_release  # Primary measurement
            
            # Measure release trajectory
            release_frame = measurement_frames.get('release_trajectory_frame')
            if is_valid_frame(release_frame):
                release_angle = self._measure_release_angle_at_frame(
                    keypoints_sequence, int(release_frame), shooting_hand
                )
                measurements['release_angle'] = release_angle
            
            # Measure shoulder at release
            shoulder_release_frame = measurement_frames.get('shoulder_at_release')
            if is_valid_frame(shoulder_release_frame):
                shoulder_angle = self._measure_shoulder_at_frame(
                    keypoints_sequence, int(shoulder_release_frame), shooting_hand
                )
                measurements['shoulder_at_release'] = shoulder_angle
            
            # Measure body alignment (average across all frames for stability)
            body_alignment = self._measure_body_alignment_average(keypoints_sequence)
            measurements['body_alignment'] = body_alignment
            
            # Calculate confidence scores
            self.confidence_scores = self._calculate_confidence_scores(
                measurements, keypoints_sequence, key_frames
            )
            
            measurements['confidence_scores'] = self.confidence_scores
            
            return measurements
            
        except Exception as e:
            print(f"Error in precise measurements: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _detect_shooting_hand(self, keypoints_sequence: List[Dict]) -> str:
        """Detect which hand is shooting based on movement"""
        right_movement = 0
        left_movement = 0
        
        for i in range(1, min(len(keypoints_sequence), 20)):
            prev_kp = keypoints_sequence[i-1]
            curr_kp = keypoints_sequence[i]
            
            if prev_kp and curr_kp:
                # Check right wrist movement
                if 'right_wrist' in prev_kp and 'right_wrist' in curr_kp:
                    if prev_kp['right_wrist'] and curr_kp['right_wrist']:
                        right_dist = np.linalg.norm(
                            np.array(curr_kp['right_wrist']) - np.array(prev_kp['right_wrist'])
                        )
                        right_movement += right_dist
                
                # Check left wrist movement
                if 'left_wrist' in prev_kp and 'left_wrist' in curr_kp:
                    if prev_kp['left_wrist'] and curr_kp['left_wrist']:
                        left_dist = np.linalg.norm(
                            np.array(curr_kp['left_wrist']) - np.array(prev_kp['left_wrist'])
                        )
                        left_movement += left_dist
        
        return 'right' if right_movement > left_movement else 'left'
    
    def _measure_elbow_at_frame(self, keypoints_sequence: List[Dict], 
                                frame: int, hand: str) -> Optional[float]:
        """Measure elbow angle at specific frame"""
        if frame >= len(keypoints_sequence):
            return None
        
        keypoints = keypoints_sequence[frame]
        if not keypoints:
            return None
        
        # Get landmarks for shooting hand
        shoulder_key = f'{hand}_shoulder'
        elbow_key = f'{hand}_elbow'
        wrist_key = f'{hand}_wrist'
        
        if not all(k in keypoints and keypoints[k] for k in [shoulder_key, elbow_key, wrist_key]):
            return None
        
        shoulder = np.array(keypoints[shoulder_key])
        elbow = np.array(keypoints[elbow_key])
        wrist = np.array(keypoints[wrist_key])
        
        # Calculate angle
        v1 = shoulder - elbow
        v2 = wrist - elbow
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle = np.degrees(np.arccos(cos_angle))
        return float(angle)
    
    def _measure_knee_at_frame(self, keypoints_sequence: List[Dict], 
                               frame: int, hand: str) -> Optional[float]:
        """Measure knee angle at specific frame"""
        if frame >= len(keypoints_sequence):
            return None
        
        keypoints = keypoints_sequence[frame]
        if not keypoints:
            return None
        
        # Get landmarks for shooting side
        hip_key = f'{hand}_hip'
        knee_key = f'{hand}_knee'
        ankle_key = f'{hand}_ankle'
        
        if not all(k in keypoints and keypoints[k] for k in [hip_key, knee_key, ankle_key]):
            return None
        
        hip = np.array(keypoints[hip_key])
        knee = np.array(keypoints[knee_key])
        ankle = np.array(keypoints[ankle_key])
        
        # Calculate angle
        v1 = hip - knee
        v2 = ankle - knee
        
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle = np.degrees(np.arccos(cos_angle))
        return float(angle)
    
    def _measure_shoulder_at_frame(self, keypoints_sequence: List[Dict],
                                   frame: int, hand: str) -> Optional[float]:
        """Measure shoulder elevation at specific frame"""
        if frame >= len(keypoints_sequence):
            return None
        
        keypoints = keypoints_sequence[frame]
        if not keypoints:
            return None
        
        # Calculate shoulder elevation relative to trunk
        shoulder_key = f'{hand}_shoulder'
        elbow_key = f'{hand}_elbow'
        hip_key = f'{hand}_hip'
        
        if not all(k in keypoints and keypoints[k] for k in [shoulder_key, elbow_key, hip_key]):
            return None
        
        shoulder = np.array(keypoints[shoulder_key])
        elbow = np.array(keypoints[elbow_key])
        hip = np.array(keypoints[hip_key])
        
        # Vector from hip to shoulder (trunk)
        trunk_vector = shoulder - hip
        # Vector from shoulder to elbow (upper arm)
        arm_vector = elbow - shoulder
        
        # Calculate angle
        cos_angle = np.dot(trunk_vector, arm_vector) / (
            np.linalg.norm(trunk_vector) * np.linalg.norm(arm_vector)
        )
        cos_angle = np.clip(cos_angle, -1.0, 1.0)
        
        angle = np.degrees(np.arccos(cos_angle))
        return float(angle)
    
    def _measure_release_angle_at_frame(self, keypoints_sequence: List[Dict],
                                       frame: int, hand: str) -> Optional[float]:
        """
        Measure release trajectory angle at specific frame
        Uses velocity direction if available, otherwise wrist-elbow angle
        """
        if frame >= len(keypoints_sequence) or frame < 2:
            return None
        
        keypoints = keypoints_sequence[frame]
        if not keypoints:
            return None
        
        wrist_key = f'{hand}_wrist'
        elbow_key = f'{hand}_elbow'
        
        if wrist_key not in keypoints or not keypoints[wrist_key]:
            return None
        
        # Method 1: Use velocity direction (more accurate)
        if frame >= 2:
            prev_wrist = keypoints_sequence[frame-2].get(wrist_key)
            curr_wrist = keypoints[wrist_key]
            
            if prev_wrist and curr_wrist:
                # Calculate velocity vector
                vx = curr_wrist[0] - prev_wrist[0]
                vy = prev_wrist[1] - curr_wrist[1]  # Inverted y-axis
                
                # Calculate angle from horizontal
                angle = np.degrees(np.arctan2(vy, abs(vx)))
                
                if 30 <= angle <= 70:  # Sanity check
                    return float(angle)
        
        # Method 2: Fallback to wrist-elbow angle
        if elbow_key in keypoints and keypoints[elbow_key]:
            wrist = np.array(keypoints[wrist_key])
            elbow = np.array(keypoints[elbow_key])
            
            vector = wrist - elbow
            angle = np.degrees(np.arctan2(-vector[1], abs(vector[0])))
            
            return float(abs(angle))
        
        return None
    
    def _measure_body_alignment_average(self, keypoints_sequence: List[Dict]) -> float:
        """Measure average body alignment across valid frames"""
        alignments = []
        
        for keypoints in keypoints_sequence:
            if not keypoints:
                continue
            
            required = ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
            if not all(k in keypoints and keypoints[k] for k in required):
                continue
            
            # Calculate alignment for this frame
            shoulder_mid_x = (keypoints['left_shoulder'][0] + keypoints['right_shoulder'][0]) / 2
            hip_mid_x = (keypoints['left_hip'][0] + keypoints['right_hip'][0]) / 2
            
            deviation = abs(shoulder_mid_x - hip_mid_x)
            
            # Score alignment
            max_acceptable = 150
            max_deviation = 500
            
            if deviation <= max_acceptable:
                alignment = 100 - (deviation / max_acceptable * 30)
            elif deviation <= max_deviation:
                excess = deviation - max_acceptable
                alignment = 70 - (excess / (max_deviation - max_acceptable) * 70)
            else:
                alignment = 0
            
            alignments.append(max(0, min(100, alignment)))
        
        if alignments:
            return float(np.median(alignments))  # Use median for robustness
        
        return 70.0  # Default
    
    def _calculate_confidence_scores(self, measurements: Dict, 
                                     keypoints_sequence: List[Dict],
                                     key_frames: Dict) -> Dict:
        """Calculate confidence for each measurement"""
        confidence = {}
        
        # Base confidence from measurement availability
        for key, value in measurements.items():
            if value is not None and value > 0:
                confidence[f'{key}_confidence'] = 85.0  # High - measured at specific frame
            else:
                confidence[f'{key}_confidence'] = 0.0
        
        # Boost confidence if key frames detected
        if key_frames.get('release') and key_frames.get('dip_bottom'):
            confidence['phase_detection_confidence'] = 90.0
        else:
            confidence['phase_detection_confidence'] = 50.0
        
        return confidence
    
    def get_comprehensive_measurements(self, keypoints_sequence: List[Dict],
                                      phase_detection_result: Dict) -> Dict:
        """
        Get all measurements with proper phase-specific timing
        
        Args:
            keypoints_sequence: All frame keypoints
            phase_detection_result: Results from motion-based phase detector
            
        Returns:
            Complete measurements dict
        """
        key_frames = phase_detection_result.get('key_frames', {})
        
        # Get measurement frames
        measurement_frames = {
            'elbow_at_cocking': key_frames.get('dip_bottom'),
            'elbow_at_release': key_frames.get('release'),
            'knee_at_loading': key_frames.get('dip_bottom'),
            'knee_at_release': key_frames.get('release'),
            'shoulder_at_release': key_frames.get('release'),
            'release_trajectory_frame': key_frames.get('release'),
            'wrist_at_release': key_frames.get('release')
        }
        
        # Take measurements
        measurements = self.measure_at_key_frames(
            keypoints_sequence,
            key_frames,
            measurement_frames
        )
        
        # Add metadata
        measurements['measurement_method'] = 'precise_frame'
        measurements['key_frames_used'] = key_frames
        measurements['is_valid_motion'] = phase_detection_result.get('is_valid_shooting_motion', False)
        
        return measurements
    
    def compare_with_research(self, measurements: Dict) -> Dict:
        """
        Compare measurements to research-based ideal values
        
        Args:
            measurements: Measured angles
            
        Returns:
            Comparison with research ideals
        """
        from research_config import IDEAL_VALUES_BY_PHASE, TOLERANCE_RANGES
        
        comparison = {}
        
        # Elbow at release
        if 'elbow_at_release' in measurements and measurements['elbow_at_release']:
            ideal = IDEAL_VALUES_BY_PHASE['release']['elbow']
            tolerance = TOLERANCE_RANGES['elbow']
            measured = measurements['elbow_at_release']
            
            deviation = abs(measured - ideal)
            in_range = deviation <= tolerance
            
            comparison['elbow_at_release'] = {
                'measured': measured,
                'ideal': ideal,
                'deviation': deviation,
                'in_ideal_range': in_range,
                'assessment': 'Excellent' if in_range else 'Needs work'
            }
        
        # Knee at release
        if 'knee_at_release' in measurements and measurements['knee_at_release']:
            ideal = IDEAL_VALUES_BY_PHASE['release']['knee']
            tolerance = TOLERANCE_RANGES['knee']
            measured = measurements['knee_at_release']
            
            deviation = abs(measured - ideal)
            in_range = deviation <= tolerance
            
            comparison['knee_at_release'] = {
                'measured': measured,
                'ideal': ideal,
                'deviation': deviation,
                'in_ideal_range': in_range,
                'assessment': 'Excellent' if in_range else 'Needs work'
            }
        
        # Release trajectory
        if 'release_angle' in measurements and measurements['release_angle']:
            ideal = IDEAL_VALUES_BY_PHASE['release']['release_trajectory']
            tolerance = TOLERANCE_RANGES['release_trajectory']
            measured = measurements['release_angle']
            
            deviation = abs(measured - ideal)
            in_range = deviation <= tolerance
            
            comparison['release_trajectory'] = {
                'measured': measured,
                'ideal': ideal,
                'deviation': deviation,
                'in_ideal_range': in_range,
                'assessment': 'Excellent' if in_range else 'Needs work'
            }
        
        return comparison

