"""
Motion-Based Phase Detection

Detects shooting phases using actual motion analysis instead of time-based guessing.
Analyzes wrist velocity, acceleration, and multi-joint coordination.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from scipy.signal import find_peaks, savgol_filter

class MotionBasedPhaseDetector:
    """
    Detect shooting phases based on actual motion patterns
    """
    
    def __init__(self):
        """Initialize motion-based phase detector"""
        self.wrist_positions = []
        self.wrist_velocities = []
        self.wrist_accelerations = []
        
        # Key frame indices
        self.dip_start_frame = None
        self.dip_bottom_frame = None
        self.release_frame = None
        self.peak_frame = None
        self.follow_through_end_frame = None
        
        # Phase boundaries
        self.phases = {
            'setup': {'start': 0, 'end': 0},
            'dip': {'start': 0, 'end': 0},
            'release': {'start': 0, 'end': 0},
            'follow_through': {'start': 0, 'end': 0}
        }
        
        self.is_valid_shooting_motion = False
    
    def analyze_motion(self, keypoints_sequence: List[Dict]) -> Dict:
        """
        Analyze complete motion sequence to detect phases
        
        Args:
            keypoints_sequence: List of keypoint dicts for each frame
            
        Returns:
            Dict with phase information and key frames
        """
        try:
            if not keypoints_sequence or len(keypoints_sequence) < 10:
                return self._get_default_phases()
            
            # Extract wrist trajectory
            self._extract_wrist_trajectory(keypoints_sequence)
            
            if len(self.wrist_positions) < 10:
                return self._get_default_phases()
            
            # Calculate motion characteristics
            self._calculate_velocities()
            self._calculate_accelerations()
            
            # Detect key moments
            self._detect_key_moments()
            
            # Validate shooting motion
            self.is_valid_shooting_motion = self._validate_shooting_motion()
            
            if not self.is_valid_shooting_motion:
                print("⚠️ Warning: Motion pattern doesn't match typical shooting form")
            
            # Define phase boundaries
            self._define_phase_boundaries(len(keypoints_sequence))
            
            # Convert numpy types to Python native types for JSON serialization
            result = {
                'success': True,
                'is_valid_shooting_motion': self.is_valid_shooting_motion,
                'key_frames': {
                    'dip_start': int(self.dip_start_frame) if self.dip_start_frame is not None else None,
                    'dip_bottom': int(self.dip_bottom_frame) if self.dip_bottom_frame is not None else None,
                    'release': int(self.release_frame) if self.release_frame is not None else None,
                    'peak': int(self.peak_frame) if self.peak_frame is not None else None,
                    'follow_through_end': int(self.follow_through_end_frame) if self.follow_through_end_frame is not None else None
                },
                'phases': self.phases,
                'motion_stats': {
                    'max_velocity': float(np.max([v['magnitude'] for v in self.wrist_velocities])) if self.wrist_velocities else 0,
                    'max_acceleration': float(np.max([a['magnitude'] for a in self.wrist_accelerations])) if self.wrist_accelerations else 0,
                    'total_frames': len(keypoints_sequence)
                }
            }
            
            print(f"✅ Phase detection successful:")
            print(f"   Dip bottom: Frame {result['key_frames']['dip_bottom']}")
            print(f"   Release: Frame {result['key_frames']['release']}")
            
            return result
            
        except Exception as e:
            print(f"Error analyzing motion: {e}")
            return self._get_default_phases()
    
    def _extract_wrist_trajectory(self, keypoints_sequence: List[Dict]):
        """Extract wrist positions from keypoint sequence"""
        for i, keypoints in enumerate(keypoints_sequence):
            if not keypoints:
                continue
            
            # Try both hands, use the one that moves more (shooting hand)
            right_wrist = keypoints.get('right_wrist')
            left_wrist = keypoints.get('left_wrist')
            
            if right_wrist:
                self.wrist_positions.append({
                    'frame': i,
                    'x': right_wrist[0],
                    'y': right_wrist[1],
                    'hand': 'right'
                })
            elif left_wrist:
                self.wrist_positions.append({
                    'frame': i,
                    'x': left_wrist[0],
                    'y': left_wrist[1],
                    'hand': 'left'
                })
    
    def _calculate_velocities(self):
        """Calculate wrist velocities (change in position per frame)"""
        if len(self.wrist_positions) < 2:
            return
        
        for i in range(1, len(self.wrist_positions)):
            prev = self.wrist_positions[i-1]
            curr = self.wrist_positions[i]
            
            # Vertical velocity (y-direction, inverted coordinates)
            vy = prev['y'] - curr['y']  # Positive = upward
            
            # Horizontal velocity
            vx = curr['x'] - prev['x']
            
            # Total velocity magnitude
            v_mag = np.sqrt(vx**2 + vy**2)
            
            self.wrist_velocities.append({
                'frame': curr['frame'],
                'vx': vx,
                'vy': vy,
                'magnitude': v_mag
            })
    
    def _calculate_accelerations(self):
        """Calculate wrist accelerations (change in velocity per frame)"""
        if len(self.wrist_velocities) < 2:
            return
        
        for i in range(1, len(self.wrist_velocities)):
            prev_v = self.wrist_velocities[i-1]
            curr_v = self.wrist_velocities[i]
            
            # Acceleration
            ay = curr_v['vy'] - prev_v['vy']
            ax = curr_v['vx'] - prev_v['vx']
            
            a_mag = np.sqrt(ax**2 + ay**2)
            
            self.wrist_accelerations.append({
                'frame': curr_v['frame'],
                'ax': ax,
                'ay': ay,
                'magnitude': a_mag
            })
    
    def _detect_key_moments(self):
        """Detect key moments in the shooting motion"""
        if not self.wrist_positions:
            return
        
        # Extract y-positions (vertical movement)
        y_positions = np.array([p['y'] for p in self.wrist_positions])
        frames = np.array([p['frame'] for p in self.wrist_positions])
        
        # Smooth the trajectory to reduce noise
        if len(y_positions) >= 5:
            window_length = min(11, len(y_positions) if len(y_positions) % 2 == 1 else len(y_positions) - 1)
            if window_length >= 5:
                y_smooth = savgol_filter(y_positions, window_length, 3)
            else:
                y_smooth = y_positions
        else:
            y_smooth = y_positions
        
        # Find dip bottom (highest y value = lowest point in image coordinates)
        dip_idx = np.argmax(y_smooth)
        self.dip_bottom_frame = int(frames[dip_idx])
        
        # Find release/peak (lowest y value = highest point in image coordinates)
        peak_idx = np.argmin(y_smooth)
        self.peak_frame = int(frames[peak_idx])
        self.release_frame = self.peak_frame  # Release happens at peak
        
        # Find dip start (first significant downward movement before dip)
        if dip_idx > 0:
            # Look backwards from dip for start of downward movement
            for i in range(dip_idx - 1, max(0, dip_idx - 20), -1):
                if y_smooth[i] < y_smooth[dip_idx] - 20:  # 20 pixels above dip
                    self.dip_start_frame = int(frames[i])
                    break
            
            if self.dip_start_frame is None:
                self.dip_start_frame = int(frames[max(0, dip_idx - 10)])
        
        # Find follow-through end (when motion stabilizes)
        if peak_idx < len(frames) - 5:
            self.follow_through_end_frame = int(frames[min(len(frames) - 1, peak_idx + 15)])
        else:
            self.follow_through_end_frame = int(frames[-1])
        
        print(f"🎯 Key frames detected:")
        print(f"   Dip start: {self.dip_start_frame}")
        print(f"   Dip bottom: {self.dip_bottom_frame}")
        print(f"   Release/Peak: {self.release_frame}")
        print(f"   Follow-through end: {self.follow_through_end_frame}")
    
    def _validate_shooting_motion(self) -> bool:
        """
        Validate that the motion pattern matches a basketball shot
        
        Returns:
            True if valid shooting motion detected
        """
        if not self.wrist_positions or len(self.wrist_positions) < 10:
            return False
        
        # Check 1: Must have dip and release
        if self.dip_bottom_frame is None or self.release_frame is None:
            return False
        
        # Check 2: Dip must come before release
        if self.dip_bottom_frame >= self.release_frame:
            return False
        
        # Check 3: Must have significant vertical movement
        y_positions = [p['y'] for p in self.wrist_positions]
        total_range = max(y_positions) - min(y_positions)
        
        if total_range < 50:  # Less than 50 pixels = probably not shooting
            print(f"⚠️ Low vertical movement ({total_range:.1f}px) - may not be shooting")
            return False
        
        # Check 4: Motion should be relatively quick (not slow walking)
        motion_duration = len(self.wrist_positions)
        if motion_duration > 120:  # More than 4 seconds at 30fps = probably not shooting
            print(f"⚠️ Long motion duration ({motion_duration} frames) - may not be shooting")
            return False
        
        # Check 5: Release should be higher than dip
        dip_y = self.wrist_positions[self.dip_bottom_frame]['y']
        release_y = self.wrist_positions[self.release_frame]['y']
        
        if dip_y <= release_y:  # Release should be higher (lower y value)
            print(f"⚠️ Release not higher than dip - unusual motion pattern")
            return False
        
        return True
    
    def _define_phase_boundaries(self, total_frames: int):
        """Define precise phase boundaries based on detected key moments"""
        # Setup phase: Start to dip start
        self.phases['setup'] = {
            'start': 0,
            'end': self.dip_start_frame if self.dip_start_frame else int(total_frames * 0.3)
        }
        
        # Dip phase: Dip start to dip bottom
        self.phases['dip'] = {
            'start': self.dip_start_frame if self.dip_start_frame else int(total_frames * 0.3),
            'end': self.dip_bottom_frame if self.dip_bottom_frame else int(total_frames * 0.5)
        }
        
        # Release phase: Dip bottom to peak
        self.phases['release'] = {
            'start': self.dip_bottom_frame if self.dip_bottom_frame else int(total_frames * 0.5),
            'end': self.peak_frame if self.peak_frame else int(total_frames * 0.8)
        }
        
        # Follow-through phase: Peak to end
        self.phases['follow_through'] = {
            'start': self.peak_frame if self.peak_frame else int(total_frames * 0.8),
            'end': self.follow_through_end_frame if self.follow_through_end_frame else total_frames - 1
        }
    
    def get_phase_at_frame(self, frame_number: int) -> str:
        """
        Get the shooting phase for a specific frame
        
        Args:
            frame_number: Frame index
            
        Returns:
            Phase name
        """
        for phase_name, boundaries in self.phases.items():
            if boundaries['start'] <= frame_number <= boundaries['end']:
                return phase_name
        
        return 'unknown'
    
    def get_measurement_frames(self) -> Dict:
        """
        Get the specific frames where measurements should be taken
        
        Returns:
            Dict with measurement frames for each angle
        """
        return {
            'elbow_at_cocking': self.dip_bottom_frame,  # Measure elbow when wrist is lowest
            'elbow_at_release': self.release_frame,     # Measure elbow when wrist is highest
            'knee_at_loading': self.dip_bottom_frame,   # Measure knee at maximum flexion
            'knee_at_release': self.release_frame,      # Measure knee at release
            'shoulder_at_cocking': self.dip_bottom_frame,
            'shoulder_at_release': self.release_frame,
            'wrist_at_release': self.release_frame,
            'wrist_at_follow_through': min(self.follow_through_end_frame, self.release_frame + 10) if self.release_frame else None,
            'release_trajectory_frame': self.release_frame
        }
    
    def _get_default_phases(self) -> Dict:
        """Return default phase structure when detection fails"""
        return {
            'success': False,
            'is_valid_shooting_motion': False,
            'key_frames': {
                'dip_start': None,
                'dip_bottom': None,
                'release': None,
                'peak': None,
                'follow_through_end': None
            },
            'phases': {
                'setup': {'start': 0, 'end': 0},
                'dip': {'start': 0, 'end': 0},
                'release': {'start': 0, 'end': 0},
                'follow_through': {'start': 0, 'end': 0}
            },
            'motion_stats': {}
        }
    
    def visualize_motion(self) -> str:
        """
        Create text visualization of detected motion
        
        Returns:
            String representation of motion pattern
        """
        if not self.wrist_positions:
            return "No motion data"
        
        viz = "\n📊 Motion Pattern Detected:\n"
        viz += "="*60 + "\n"
        
        for i, pos in enumerate(self.wrist_positions):
            frame = pos['frame']
            phase = self.get_phase_at_frame(frame)
            
            marker = ""
            if frame == self.dip_start_frame:
                marker = " ← DIP START"
            elif frame == self.dip_bottom_frame:
                marker = " ← DIP BOTTOM (measure cocking angles)"
            elif frame == self.release_frame:
                marker = " ← RELEASE (measure release angles)"
            elif frame == self.follow_through_end_frame:
                marker = " ← FOLLOW-THROUGH END"
            
            if marker or i % 10 == 0:
                viz += f"Frame {frame:3d}: y={pos['y']:6.1f}px | {phase:15s} {marker}\n"
        
        viz += "="*60 + "\n"
        return viz
    
    def reset(self):
        """Reset detector"""
        self.wrist_positions = []
        self.wrist_velocities = []
        self.wrist_accelerations = []
        self.dip_start_frame = None
        self.dip_bottom_frame = None
        self.release_frame = None
        self.peak_frame = None
        self.follow_through_end_frame = None
        self.is_valid_shooting_motion = False


class JointCoordinationAnalyzer:
    """
    Analyze coordination between multiple joints during shooting motion
    """
    
    def __init__(self):
        """Initialize coordination analyzer"""
        self.joint_trajectories = {}
    
    def analyze_coordination(self, keypoints_sequence: List[Dict], 
                           key_frames: Dict) -> Dict:
        """
        Analyze multi-joint coordination
        
        Args:
            keypoints_sequence: Sequence of keypoints
            key_frames: Key frames from phase detection
            
        Returns:
            Coordination analysis results
        """
        try:
            if not keypoints_sequence or not key_frames:
                return {}
            
            # Extract joint angles over time
            self._extract_joint_trajectories(keypoints_sequence)
            
            # Analyze timing
            timing_analysis = self._analyze_timing(key_frames)
            
            # Analyze power transfer
            power_transfer = self._analyze_power_transfer(key_frames)
            
            return {
                'success': True,
                'timing': timing_analysis,
                'power_transfer': power_transfer,
                'coordination_score': self._calculate_coordination_score(timing_analysis, power_transfer)
            }
            
        except Exception as e:
            print(f"Error analyzing coordination: {e}")
            return {'success': False}
    
    def _extract_joint_trajectories(self, keypoints_sequence: List[Dict]):
        """Extract position trajectories for key joints"""
        joints = ['wrist', 'elbow', 'shoulder', 'hip', 'knee', 'ankle']
        sides = ['right', 'left']
        
        for joint in joints:
            for side in sides:
                key = f'{side}_{joint}'
                self.joint_trajectories[key] = []
                
                for i, keypoints in enumerate(keypoints_sequence):
                    if keypoints and key in keypoints and keypoints[key]:
                        pos = keypoints[key]
                        self.joint_trajectories[key].append({
                            'frame': i,
                            'x': pos[0],
                            'y': pos[1]
                        })
    
    def _analyze_timing(self, key_frames: Dict) -> Dict:
        """Analyze timing of joint movements"""
        release_frame = key_frames.get('release')
        dip_frame = key_frames.get('dip_bottom')
        
        if not release_frame or not dip_frame:
            return {}
        
        # Calculate time from dip to release
        dip_to_release_frames = release_frame - dip_frame
        
        return {
            'dip_to_release_frames': dip_to_release_frames,
            'dip_to_release_ms': dip_to_release_frames * 33.3,  # Assume 30fps
            'is_quick_release': dip_to_release_frames < 20  # Less than 0.66 seconds
        }
    
    def _analyze_power_transfer(self, key_frames: Dict) -> Dict:
        """Analyze kinetic chain power transfer"""
        # Check if knee extends before/during elbow extension
        # Good shot: knee → hip → shoulder → elbow → wrist (bottom-up)
        
        return {
            'kinetic_chain': 'bottom_up',  # Placeholder
            'efficiency': 85.0  # Placeholder
        }
    
    def _calculate_coordination_score(self, timing: Dict, power: Dict) -> float:
        """Calculate overall coordination score"""
        if not timing:
            return 0.0
        
        score = 70.0  # Base score
        
        # Quick release bonus
        if timing.get('is_quick_release'):
            score += 15
        
        # Smooth power transfer bonus
        if power.get('efficiency', 0) > 80:
            score += 15
        
        return min(100, score)

