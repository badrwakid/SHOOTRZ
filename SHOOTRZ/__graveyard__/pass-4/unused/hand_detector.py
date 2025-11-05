"""
Shooting Hand Detection System

Automatically detects whether the user is left-handed or right-handed
based on pose analysis and shooting mechanics.
"""

import numpy as np

class HandDetector:
    def __init__(self):
        """Initialize hand detection system"""
        self.detection_confidence = 0.0
        self.detected_hand = None
        self.analysis_frames = []
        
    def analyze_shooting_hand(self, keypoints_list):
        """
        Analyze multiple frames to determine shooting hand
        
        Args:
            keypoints_list: List of keypoint dictionaries from multiple frames
            
        Returns:
            dict: Hand detection results with confidence
        """
        try:
            if not keypoints_list or len(keypoints_list) < 5:
                return {
                    'detected_hand': 'right',  # Default fallback
                    'confidence': 50.0,
                    'reasoning': 'Insufficient frames for analysis'
                }
            
            # Analyze each frame
            frame_analyses = []
            for keypoints in keypoints_list:
                if keypoints:
                    analysis = self._analyze_single_frame(keypoints)
                    frame_analyses.append(analysis)
            
            if not frame_analyses:
                return {
                    'detected_hand': 'right',
                    'confidence': 50.0,
                    'reasoning': 'No valid frames for analysis'
                }
            
            # Combine frame analyses
            result = self._combine_frame_analyses(frame_analyses)
            return result
            
        except Exception as e:
            print(f"Error in hand detection: {e}")
            return {
                'detected_hand': 'right',
                'confidence': 50.0,
                'reasoning': f'Analysis error: {str(e)}'
            }
    
    def _analyze_single_frame(self, keypoints):
        """Analyze a single frame for hand detection"""
        try:
            # Check if required landmarks are present
            required_landmarks = [
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_hip', 'right_hip'
            ]
            
            missing_landmarks = [lm for lm in required_landmarks if lm not in keypoints or keypoints[lm] is None]
            if missing_landmarks:
                return {
                    'hand': None,
                    'confidence': 0.0,
                    'reasoning': f'Missing landmarks: {missing_landmarks}'
                }
            
            # Method 1: Wrist height comparison during release
            left_wrist_y = keypoints['left_wrist'][1]
            right_wrist_y = keypoints['right_wrist'][1]
            wrist_height_diff = right_wrist_y - left_wrist_y
            
            # Method 2: Elbow extension (shooting arm typically more extended)
            left_elbow_angle = self._calculate_elbow_angle(
                keypoints['left_shoulder'],
                keypoints['left_elbow'],
                keypoints['left_wrist']
            )
            right_elbow_angle = self._calculate_elbow_angle(
                keypoints['right_shoulder'],
                keypoints['right_elbow'],
                keypoints['right_wrist']
            )
            
            # Method 3: Shoulder alignment (shooting shoulder typically higher)
            left_shoulder_y = keypoints['left_shoulder'][1]
            right_shoulder_y = keypoints['right_shoulder'][1]
            shoulder_height_diff = right_shoulder_y - left_shoulder_y
            
            # Method 4: Body positioning (shooting side typically more forward)
            left_shoulder_x = keypoints['left_shoulder'][0]
            right_shoulder_x = keypoints['right_shoulder'][0]
            shoulder_forward_diff = right_shoulder_x - left_shoulder_x
            
            # Analyze results
            right_hand_indicators = 0
            left_hand_indicators = 0
            total_confidence = 0.0
            
            # Wrist height analysis
            if abs(wrist_height_diff) > 10:  # Significant difference
                if wrist_height_diff < 0:  # Right wrist higher
                    right_hand_indicators += 1
                    total_confidence += 0.3
                else:  # Left wrist higher
                    left_hand_indicators += 1
                    total_confidence += 0.3
            
            # Elbow extension analysis
            if abs(left_elbow_angle - right_elbow_angle) > 10:  # Significant difference
                if right_elbow_angle > left_elbow_angle:  # Right arm more extended
                    right_hand_indicators += 1
                    total_confidence += 0.25
                else:  # Left arm more extended
                    left_hand_indicators += 1
                    total_confidence += 0.25
            
            # Shoulder height analysis
            if abs(shoulder_height_diff) > 5:  # Significant difference
                if shoulder_height_diff < 0:  # Right shoulder higher
                    right_hand_indicators += 1
                    total_confidence += 0.2
                else:  # Left shoulder higher
                    left_hand_indicators += 1
                    total_confidence += 0.2
            
            # Body positioning analysis
            if abs(shoulder_forward_diff) > 5:  # Significant difference
                if shoulder_forward_diff > 0:  # Right shoulder more forward
                    right_hand_indicators += 1
                    total_confidence += 0.25
                else:  # Left shoulder more forward
                    left_hand_indicators += 1
                    total_confidence += 0.25
            
            # Determine result
            if right_hand_indicators > left_hand_indicators:
                detected_hand = 'right'
                confidence = min(100, total_confidence * 100)
            elif left_hand_indicators > right_hand_indicators:
                detected_hand = 'left'
                confidence = min(100, total_confidence * 100)
            else:
                detected_hand = 'right'  # Default fallback
                confidence = 50.0
            
            return {
                'hand': detected_hand,
                'confidence': confidence,
                'reasoning': f'Right indicators: {right_hand_indicators}, Left indicators: {left_hand_indicators}',
                'metrics': {
                    'wrist_height_diff': wrist_height_diff,
                    'elbow_angle_diff': right_elbow_angle - left_elbow_angle,
                    'shoulder_height_diff': shoulder_height_diff,
                    'shoulder_forward_diff': shoulder_forward_diff
                }
            }
            
        except Exception as e:
            print(f"Error analyzing single frame: {e}")
            return {
                'hand': None,
                'confidence': 0.0,
                'reasoning': f'Frame analysis error: {str(e)}'
            }
    
    def _calculate_elbow_angle(self, shoulder, elbow, wrist):
        """Calculate elbow angle for hand detection"""
        try:
            # Convert to numpy arrays
            p1 = np.array(shoulder, dtype=np.float64)
            p2 = np.array(elbow, dtype=np.float64)
            p3 = np.array(wrist, dtype=np.float64)
            
            # Calculate vectors
            vector1 = p1 - p2
            vector2 = p3 - p2
            
            # Calculate dot product
            dot_product = np.dot(vector1, vector2)
            
            # Calculate magnitudes
            magnitude1 = np.linalg.norm(vector1)
            magnitude2 = np.linalg.norm(vector2)
            
            # Avoid division by zero
            if magnitude1 == 0 or magnitude2 == 0:
                return 0.0
            
            # Calculate cosine of angle
            cosine_angle = dot_product / (magnitude1 * magnitude2)
            
            # Clamp to valid range for arccos
            cosine_angle = np.clip(cosine_angle, -1.0, 1.0)
            
            # Calculate angle in radians and convert to degrees
            angle_radians = np.arccos(cosine_angle)
            angle_degrees = np.degrees(angle_radians)
            
            return angle_degrees
            
        except Exception as e:
            print(f"Error calculating elbow angle: {e}")
            return 0.0
    
    def _combine_frame_analyses(self, frame_analyses):
        """Combine multiple frame analyses into final result"""
        try:
            # Filter out invalid analyses
            valid_analyses = [a for a in frame_analyses if a['hand'] is not None]
            
            if not valid_analyses:
                return {
                    'detected_hand': 'right',
                    'confidence': 50.0,
                    'reasoning': 'No valid frame analyses'
                }
            
            # Count hand preferences
            right_count = sum(1 for a in valid_analyses if a['hand'] == 'right')
            left_count = sum(1 for a in valid_analyses if a['hand'] == 'left')
            
            # Calculate average confidence
            avg_confidence = np.mean([a['confidence'] for a in valid_analyses])
            
            # Determine final result
            if right_count > left_count:
                detected_hand = 'right'
                final_confidence = avg_confidence * (right_count / len(valid_analyses))
            elif left_count > right_count:
                detected_hand = 'left'
                final_confidence = avg_confidence * (left_count / len(valid_analyses))
            else:
                # Tie - use confidence-weighted decision
                right_confidence = np.mean([a['confidence'] for a in valid_analyses if a['hand'] == 'right'])
                left_confidence = np.mean([a['confidence'] for a in valid_analyses if a['hand'] == 'left'])
                
                if right_confidence > left_confidence:
                    detected_hand = 'right'
                    final_confidence = right_confidence
                else:
                    detected_hand = 'left'
                    final_confidence = left_confidence
            
            return {
                'detected_hand': detected_hand,
                'confidence': round(final_confidence, 1),
                'reasoning': f'Based on {len(valid_analyses)} frames: {right_count} right, {left_count} left',
                'frame_analyses': valid_analyses
            }
            
        except Exception as e:
            print(f"Error combining frame analyses: {e}")
            return {
                'detected_hand': 'right',
                'confidence': 50.0,
                'reasoning': f'Combination error: {str(e)}'
            }
    
    def get_hand_detection_summary(self):
        """Get summary of hand detection analysis"""
        return {
            'detected_hand': self.detected_hand,
            'confidence': self.detection_confidence,
            'analysis_frames': len(self.analysis_frames)
        }


