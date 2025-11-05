"""
Shooting Motion Validator

Validates that a video contains actual basketball shooting motion
before attempting analysis. Prevents false measurements from random movements.
"""

import numpy as np
from typing import Dict, List, Tuple

class ShootingMotionValidator:
    """
    Validate that video contains shooting motion
    """
    
    def __init__(self):
        """Initialize validator"""
        self.validation_results = {}
    
    def validate(self, keypoints_sequence: List[Dict]) -> Dict:
        """
        Validate that sequence contains shooting motion
        
        Args:
            keypoints_sequence: Sequence of keypoints
            
        Returns:
            Dict with validation results
        """
        try:
            if not keypoints_sequence or len(keypoints_sequence) < 10:
                return {
                    'is_valid': False,
                    'reason': 'Insufficient frames (<10)',
                    'confidence': 0.0
                }
            
            # Check 1: Wrist vertical movement pattern
            wrist_check = self._check_wrist_pattern(keypoints_sequence)
            
            # Check 2: Body stability (not walking around)
            stability_check = self._check_body_stability(keypoints_sequence)
            
            # Check 3: Duration reasonable for shot
            duration_check = self._check_duration(keypoints_sequence)
            
            # Check 4: Arm extension pattern
            arm_check = self._check_arm_extension(keypoints_sequence)
            
            # Combine checks
            checks = [wrist_check, stability_check, duration_check, arm_check]
            passed_checks = sum(1 for c in checks if c['passed'])
            
            is_valid = passed_checks >= 3  # At least 3 of 4 must pass
            confidence = (passed_checks / len(checks)) * 100
            
            result = {
                'is_valid': is_valid,
                'confidence': confidence,
                'checks': {
                    'wrist_pattern': wrist_check,
                    'body_stability': stability_check,
                    'duration': duration_check,
                    'arm_extension': arm_check
                },
                'passed_checks': f'{passed_checks}/{len(checks)}'
            }
            
            if not is_valid:
                result['reason'] = self._get_failure_reason(checks)
            
            self.validation_results = result
            return result
            
        except Exception as e:
            print(f"Error validating shooting motion: {e}")
            return {
                'is_valid': False,
                'reason': f'Validation error: {str(e)}',
                'confidence': 0.0
            }
    
    def _check_wrist_pattern(self, keypoints_sequence: List[Dict]) -> Dict:
        """
        Check if wrist shows characteristic shooting pattern:
        Down (dip) → Up (release) → Hold (follow-through)
        """
        wrist_y_positions = []
        
        for keypoints in keypoints_sequence:
            if keypoints:
                # Try both wrists
                wrist = keypoints.get('right_wrist') or keypoints.get('left_wrist')
                if wrist:
                    wrist_y_positions.append(wrist[1])
        
        if len(wrist_y_positions) < 10:
            return {'passed': False, 'reason': 'Insufficient wrist tracking'}
        
        # Check for dip (increase in y) then rise (decrease in y)
        has_dip = False
        has_rise = False
        
        min_y = min(wrist_y_positions)
        max_y = max(wrist_y_positions)
        range_y = max_y - min_y
        
        # Must have significant vertical movement
        if range_y < 50:
            return {'passed': False, 'reason': f'Low vertical movement ({range_y:.0f}px)'}
        
        # Find if there's a dip then rise pattern
        min_idx = wrist_y_positions.index(min_y)
        max_idx = wrist_y_positions.index(max_y)
        
        # Max (dip bottom) should come before min (peak)
        if max_idx < min_idx:
            has_dip = True
            has_rise = True
        
        if has_dip and has_rise:
            return {
                'passed': True,
                'reason': 'Characteristic dip→rise pattern detected',
                'details': {
                    'vertical_range': range_y,
                    'dip_frame': max_idx,
                    'peak_frame': min_idx
                }
            }
        else:
            return {
                'passed': False,
                'reason': 'No dip→rise pattern (may not be shooting)'
            }
    
    def _check_body_stability(self, keypoints_sequence: List[Dict]) -> Dict:
        """
        Check if body is relatively stable (not walking/running)
        """
        hip_positions = []
        
        for keypoints in keypoints_sequence:
            if keypoints:
                left_hip = keypoints.get('left_hip')
                right_hip = keypoints.get('right_hip')
                
                if left_hip and right_hip:
                    mid_hip = ((left_hip[0] + right_hip[0]) / 2,
                              (left_hip[1] + right_hip[1]) / 2)
                    hip_positions.append(mid_hip)
        
        if len(hip_positions) < 5:
            return {'passed': False, 'reason': 'Insufficient hip tracking'}
        
        # Calculate hip movement variance
        hip_array = np.array(hip_positions)
        x_variance = np.var(hip_array[:, 0])
        y_variance = np.var(hip_array[:, 1])
        
        # Low variance = stable (good for shooting)
        # High variance = moving around (not shooting)
        is_stable = x_variance < 5000 and y_variance < 2000
        
        if is_stable:
            return {
                'passed': True,
                'reason': 'Body stable during motion',
                'details': {
                    'x_variance': x_variance,
                    'y_variance': y_variance
                }
            }
        else:
            return {
                'passed': False,
                'reason': f'Body moving too much (x_var={x_variance:.0f}, y_var={y_variance:.0f})'
            }
    
    def _check_duration(self, keypoints_sequence: List[Dict]) -> Dict:
        """
        Check if motion duration is reasonable for a shot
        """
        duration_frames = len(keypoints_sequence)
        
        # Assuming 30 FPS
        duration_seconds = duration_frames / 30.0
        
        # Basketball shot typically takes 0.5-2.5 seconds
        if 0.5 <= duration_seconds <= 3.0:
            return {
                'passed': True,
                'reason': f'Duration appropriate ({duration_seconds:.1f}s)',
                'details': {'duration_seconds': duration_seconds}
            }
        elif duration_seconds < 0.5:
            return {
                'passed': False,
                'reason': f'Too short ({duration_seconds:.1f}s) - may not be complete shot'
            }
        else:
            return {
                'passed': True,  # Still pass but warn
                'reason': f'Long duration ({duration_seconds:.1f}s) - may include extra movement',
                'warning': True
            }
    
    def _check_arm_extension(self, keypoints_sequence: List[Dict]) -> Dict:
        """
        Check for arm extension pattern (elbow extends during shot)
        """
        # Track elbow angles over time
        elbow_angles = []
        
        for keypoints in keypoints_sequence:
            if not keypoints:
                continue
            
            # Try right arm
            if all(k in keypoints and keypoints[k] for k in ['right_shoulder', 'right_elbow', 'right_wrist']):
                shoulder = np.array(keypoints['right_shoulder'])
                elbow = np.array(keypoints['right_elbow'])
                wrist = np.array(keypoints['right_wrist'])
                
                v1 = shoulder - elbow
                v2 = wrist - elbow
                
                cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2))
                cos_angle = np.clip(cos_angle, -1.0, 1.0)
                angle = np.degrees(np.arccos(cos_angle))
                
                elbow_angles.append(angle)
        
        if len(elbow_angles) < 5:
            return {'passed': False, 'reason': 'Insufficient elbow tracking'}
        
        # Check if elbow extends (angle increases from bent to straight)
        min_angle = min(elbow_angles)
        max_angle = max(elbow_angles)
        extension_range = max_angle - min_angle
        
        # Should have at least 40° of extension (e.g., 90° → 130°)
        if extension_range >= 40:
            return {
                'passed': True,
                'reason': f'Arm extends {extension_range:.0f}° (shooting motion)',
                'details': {
                    'min_elbow': min_angle,
                    'max_elbow': max_angle,
                    'extension': extension_range
                }
            }
        else:
            return {
                'passed': False,
                'reason': f'Low arm extension ({extension_range:.0f}°) - may not be shooting'
            }
    
    def _get_failure_reason(self, checks: List[Dict]) -> str:
        """Get primary reason for validation failure"""
        failed = [c for c in checks if not c['passed']]
        
        if not failed:
            return "Unknown"
        
        # Return most critical failure
        reasons = [c['reason'] for c in failed]
        return reasons[0]
    
    def print_validation_report(self):
        """Print detailed validation report"""
        if not self.validation_results:
            print("No validation performed yet")
            return
        
        result = self.validation_results
        
        print("\n" + "="*70)
        print("🔍 SHOOTING MOTION VALIDATION REPORT")
        print("="*70)
        
        print(f"\n✅ Valid Shooting Motion: {result['is_valid']}")
        print(f"📊 Confidence: {result['confidence']:.1f}%")
        print(f"✓ Passed Checks: {result['passed_checks']}")
        
        if not result['is_valid']:
            print(f"\n❌ Reason: {result['reason']}")
        
        print("\n📋 Individual Checks:")
        for check_name, check_result in result['checks'].items():
            status = "✅ PASS" if check_result['passed'] else "❌ FAIL"
            print(f"   {check_name}: {status}")
            print(f"      → {check_result['reason']}")
        
        print("="*70 + "\n")

