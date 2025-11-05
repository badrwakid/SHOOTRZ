"""
Camera Angle Analyzer

Detects camera position, angle, and distance to provide:
- Recording quality assessment
- Optimal angle recommendations
- Angle-specific accuracy adjustments
"""

import numpy as np
import cv2
from typing import Dict, Tuple, Optional, List

class CameraAnalyzer:
    def __init__(self):
        """Initialize camera analyzer"""
        self.camera_angle = None
        self.camera_distance = None
        self.reliability_score = None
        
        # Reference proportions for human body (approximate)
        self.shoulder_to_hip_ratio = 0.52  # Shoulder width / torso height
        self.arm_to_body_ratio = 0.75  # Arm length / body height
        
    def analyze_camera_setup(self, keypoints: Dict, frame_shape: Tuple[int, int]) -> Dict:
        """
        Analyze camera setup from pose keypoints
        
        Args:
            keypoints: Detected pose keypoints {name: (x, y)}
            frame_shape: (height, width) of frame
            
        Returns:
            Dict with camera analysis results
        """
        try:
            if not keypoints or len(keypoints) < 8:
                return self._get_default_analysis()
            
            # Detect camera angle (front, side, 45°)
            camera_angle = self._detect_camera_angle(keypoints)
            
            # Estimate distance from camera
            camera_distance = self._estimate_distance(keypoints, frame_shape)
            
            # Calculate viewing angle reliability
            reliability_score = self._calculate_reliability(camera_angle, camera_distance, keypoints)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(camera_angle, camera_distance, reliability_score)
            
            # Calculate metric confidence adjustments
            metric_adjustments = self._calculate_metric_adjustments(camera_angle)
            
            self.camera_angle = camera_angle
            self.camera_distance = camera_distance
            self.reliability_score = reliability_score
            
            return {
                'success': True,
                'camera_angle': camera_angle['type'],
                'angle_degrees': camera_angle['degrees'],
                'camera_distance': camera_distance['category'],
                'distance_meters': camera_distance['estimated_meters'],
                'reliability_score': round(reliability_score, 1),
                'recommendations': recommendations,
                'metric_adjustments': metric_adjustments,
                'is_optimal': reliability_score >= 80.0
            }
            
        except Exception as e:
            print(f"Error analyzing camera setup: {e}")
            return self._get_default_analysis()
    
    def _detect_camera_angle(self, keypoints: Dict) -> Dict:
        """
        Detect camera viewing angle
        
        Args:
            keypoints: Pose keypoints
            
        Returns:
            Dict with angle information
        """
        try:
            # Calculate shoulder width vs body depth indicators
            left_shoulder = keypoints.get('left_shoulder')
            right_shoulder = keypoints.get('right_shoulder')
            left_hip = keypoints.get('left_hip')
            right_hip = keypoints.get('right_hip')
            
            if not all([left_shoulder, right_shoulder, left_hip, right_hip]):
                return {'type': 'unknown', 'degrees': 0, 'confidence': 0.0}
            
            # Calculate shoulder width
            shoulder_width = np.linalg.norm(
                np.array(left_shoulder) - np.array(right_shoulder)
            )
            
            # Calculate hip width
            hip_width = np.linalg.norm(
                np.array(left_hip) - np.array(right_hip)
            )
            
            # Calculate body center alignment
            shoulder_center_x = (left_shoulder[0] + right_shoulder[0]) / 2
            hip_center_x = (left_hip[0] + right_hip[0]) / 2
            center_offset = abs(shoulder_center_x - hip_center_x)
            
            # Shoulder asymmetry (indicator of angle)
            shoulder_asymmetry = abs(left_shoulder[1] - right_shoulder[1])
            
            # Determine angle type
            if shoulder_width < 50 or hip_width < 40:
                # Very narrow - likely front view
                angle_type = 'front'
                estimated_degrees = 0
                confidence = 0.8
            elif center_offset > 30 or shoulder_asymmetry > 20:
                # Significant offset - likely side view
                angle_type = 'side'
                estimated_degrees = 90
                confidence = 0.85
            elif shoulder_width > 80 and center_offset < 20:
                # Wide and aligned - likely 45° view (optimal)
                angle_type = '45_degree'
                estimated_degrees = 45
                confidence = 0.9
            else:
                # Default to 45° with lower confidence
                angle_type = '45_degree'
                estimated_degrees = 45
                confidence = 0.6
            
            return {
                'type': angle_type,
                'degrees': estimated_degrees,
                'confidence': confidence,
                'shoulder_width': float(shoulder_width),
                'hip_width': float(hip_width),
                'center_offset': float(center_offset)
            }
            
        except Exception as e:
            print(f"Error detecting camera angle: {e}")
            return {'type': 'unknown', 'degrees': 0, 'confidence': 0.0}
    
    def _estimate_distance(self, keypoints: Dict, frame_shape: Tuple[int, int]) -> Dict:
        """
        Estimate distance from camera
        
        Args:
            keypoints: Pose keypoints
            frame_shape: (height, width) of frame
            
        Returns:
            Dict with distance information
        """
        try:
            frame_height, frame_width = frame_shape
            
            # Calculate person height in frame
            head_y = min(
                keypoints.get('left_shoulder', (0, frame_height))[1],
                keypoints.get('right_shoulder', (0, frame_height))[1]
            )
            
            feet_y = max(
                keypoints.get('left_ankle', (0, 0))[1],
                keypoints.get('right_ankle', (0, 0))[1]
            )
            
            person_height_pixels = feet_y - head_y
            
            if person_height_pixels <= 0:
                return {'category': 'unknown', 'estimated_meters': 0, 'confidence': 0.0}
            
            # Calculate what percentage of frame the person occupies
            frame_coverage = person_height_pixels / frame_height
            
            # Estimate distance category
            # Assuming average person height ~1.75m and typical camera FOV
            if frame_coverage > 0.8:
                category = 'too_close'
                estimated_meters = 2.0
                confidence = 0.7
            elif frame_coverage > 0.6:
                category = 'close'
                estimated_meters = 3.0
                confidence = 0.8
            elif frame_coverage > 0.4:
                category = 'optimal'
                estimated_meters = 4.5
                confidence = 0.9
            elif frame_coverage > 0.25:
                category = 'far'
                estimated_meters = 6.0
                confidence = 0.8
            else:
                category = 'too_far'
                estimated_meters = 8.0
                confidence = 0.7
            
            return {
                'category': category,
                'estimated_meters': estimated_meters,
                'frame_coverage': float(frame_coverage),
                'person_height_pixels': float(person_height_pixels),
                'confidence': confidence
            }
            
        except Exception as e:
            print(f"Error estimating distance: {e}")
            return {'category': 'unknown', 'estimated_meters': 0, 'confidence': 0.0}
    
    def _calculate_reliability(self, camera_angle: Dict, camera_distance: Dict, 
                              keypoints: Dict) -> float:
        """
        Calculate overall recording reliability score
        
        Args:
            camera_angle: Camera angle dict
            camera_distance: Camera distance dict
            keypoints: Pose keypoints
            
        Returns:
            Reliability score (0-100)
        """
        try:
            score = 100.0
            
            # Angle scoring (45° is optimal)
            if camera_angle['type'] == '45_degree':
                angle_score = 100
            elif camera_angle['type'] == 'side':
                angle_score = 80
            elif camera_angle['type'] == 'front':
                angle_score = 60
            else:
                angle_score = 50
            
            score = (score + angle_score) / 2
            
            # Distance scoring (optimal range is best)
            distance_category = camera_distance['category']
            if distance_category == 'optimal':
                distance_score = 100
            elif distance_category in ['close', 'far']:
                distance_score = 80
            elif distance_category in ['too_close', 'too_far']:
                distance_score = 60
            else:
                distance_score = 50
            
            score = (score + distance_score) / 2
            
            # Keypoint visibility (all key points should be visible)
            required_keypoints = [
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
                'left_knee', 'right_knee'
            ]
            
            visible_count = sum(1 for kp in required_keypoints if kp in keypoints and keypoints[kp] is not None)
            visibility_score = (visible_count / len(required_keypoints)) * 100
            
            score = (score + visibility_score) / 2
            
            # Apply confidence weights
            angle_confidence = camera_angle.get('confidence', 0.5)
            distance_confidence = camera_distance.get('confidence', 0.5)
            avg_confidence = (angle_confidence + distance_confidence) / 2
            
            score = score * avg_confidence
            
            return max(0, min(100, score))
            
        except Exception as e:
            print(f"Error calculating reliability: {e}")
            return 50.0
    
    def _generate_recommendations(self, camera_angle: Dict, camera_distance: Dict,
                                 reliability_score: float) -> List[str]:
        """
        Generate recording setup recommendations
        
        Args:
            camera_angle: Camera angle dict
            camera_distance: Camera distance dict
            reliability_score: Overall reliability score
            
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        # Angle recommendations
        if camera_angle['type'] == 'front':
            recommendations.append("⚠️ Move camera to 45° angle from the side for better depth perception")
        elif camera_angle['type'] == 'side':
            recommendations.append("💡 Good side angle! For optimal results, try 45° angle for both form and shot arc")
        elif camera_angle['type'] == '45_degree':
            recommendations.append("✓ Excellent camera angle! This is optimal for shooting analysis")
        
        # Distance recommendations
        distance_cat = camera_distance['category']
        if distance_cat == 'too_close':
            recommendations.append("⚠️ Camera is too close. Move back 1-2 meters for full body capture")
        elif distance_cat == 'too_far':
            recommendations.append("⚠️ Camera is too far. Move closer by 2-3 meters for better detail")
        elif distance_cat in ['close', 'far']:
            recommendations.append("💡 Good distance, but could be optimized")
        elif distance_cat == 'optimal':
            recommendations.append("✓ Perfect camera distance!")
        
        # Overall recommendations
        if reliability_score >= 90:
            recommendations.append("✓ Excellent setup! Your recordings will provide highly accurate analysis")
        elif reliability_score >= 75:
            recommendations.append("👍 Good setup! Minor improvements could increase accuracy")
        elif reliability_score >= 60:
            recommendations.append("💡 Decent setup, but improvements recommended for better accuracy")
        else:
            recommendations.append("⚠️ Suboptimal setup. Please adjust camera angle and distance")
        
        # Technical recommendations
        recommendations.append("📹 Recommended: 720p or higher, 30+ fps, good lighting")
        recommendations.append("📐 Camera height: Chest level, 10-15 feet away")
        
        return recommendations
    
    def _calculate_metric_adjustments(self, camera_angle: Dict) -> Dict:
        """
        Calculate confidence adjustments for metrics based on camera angle
        
        Args:
            camera_angle: Camera angle dict
            
        Returns:
            Dict of adjustment factors for each metric
        """
        angle_type = camera_angle['type']
        
        # Different angles provide different quality for different metrics
        if angle_type == '45_degree':
            # Optimal angle - best for all metrics
            adjustments = {
                'elbow_angle': 1.0,
                'knee_angle': 1.0,
                'release_angle': 1.0,
                'body_alignment': 1.0,
                'follow_through': 1.0,
                'shot_arc': 1.0
            }
        elif angle_type == 'side':
            # Side view - excellent for angles, less for alignment
            adjustments = {
                'elbow_angle': 0.95,
                'knee_angle': 0.95,
                'release_angle': 1.0,
                'body_alignment': 0.7,
                'follow_through': 0.95,
                'shot_arc': 1.0
            }
        elif angle_type == 'front':
            # Front view - good for alignment, poor for depth metrics
            adjustments = {
                'elbow_angle': 0.6,
                'knee_angle': 0.7,
                'release_angle': 0.5,
                'body_alignment': 1.0,
                'follow_through': 0.6,
                'shot_arc': 0.5
            }
        else:
            # Unknown angle - conservative adjustments
            adjustments = {
                'elbow_angle': 0.7,
                'knee_angle': 0.7,
                'release_angle': 0.7,
                'body_alignment': 0.7,
                'follow_through': 0.7,
                'shot_arc': 0.7
            }
        
        return adjustments
    
    def _get_default_analysis(self) -> Dict:
        """Get default analysis when calculation fails"""
        return {
            'success': False,
            'camera_angle': 'unknown',
            'angle_degrees': 0,
            'camera_distance': 'unknown',
            'distance_meters': 0,
            'reliability_score': 50.0,
            'recommendations': [
                "⚠️ Could not analyze camera setup",
                "📹 Recommended: 45° angle, 10-15 feet away, chest height",
                "📐 Ensure full body is visible in frame"
            ],
            'metric_adjustments': {
                'elbow_angle': 0.7,
                'knee_angle': 0.7,
                'release_angle': 0.7,
                'body_alignment': 0.7,
                'follow_through': 0.7,
                'shot_arc': 0.7
            },
            'is_optimal': False
        }
    
    def get_optimal_setup_guide(self) -> Dict:
        """
        Get comprehensive guide for optimal recording setup
        
        Returns:
            Dict with setup guidelines
        """
        return {
            'camera_angle': {
                'recommended': '45 degrees from side',
                'acceptable': ['Side view (90°)', '30-60° from side'],
                'avoid': ['Front view (0°)', 'Back view (180°)']
            },
            'camera_distance': {
                'recommended': '10-15 feet (3-4.5 meters)',
                'minimum': '8 feet (2.5 meters)',
                'maximum': '20 feet (6 meters)'
            },
            'camera_height': {
                'recommended': 'Chest height',
                'acceptable': 'Waist to shoulder height',
                'avoid': 'Ground level or overhead'
            },
            'video_quality': {
                'resolution': '720p minimum, 1080p recommended',
                'framerate': '30 fps minimum, 60 fps ideal',
                'lighting': 'Even lighting, avoid backlighting'
            },
            'framing': {
                'body_coverage': 'Full body visible from head to feet',
                'margin': 'Some space above head and below feet',
                'centering': 'Player centered in frame'
            }
        }

