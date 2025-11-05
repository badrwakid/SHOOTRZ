import numpy as np

def calculate_angle(point1, point2, point3):
    """
    Calculate angle between three points using vector mathematics
    point2 is the vertex of the angle
    
    Args:
        point1: First point (x, y)
        point2: Vertex point (x, y) 
        point3: Third point (x, y)
        
    Returns:
        float: Angle in degrees
    """
    try:
        # Convert to numpy arrays
        p1 = np.array(point1, dtype=np.float64)
        p2 = np.array(point2, dtype=np.float64)
        p3 = np.array(point3, dtype=np.float64)
        
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
        
        # Validate angle is reasonable (should be 0-180 degrees for joint angles)
        if angle_degrees < 0 or angle_degrees > 180:
            print(f"⚠️ Warning: Unusual three-point angle {angle_degrees}° - possible calculation error")
        
        return angle_degrees
        
    except Exception as e:
        print(f"Error calculating angle: {e}")
        return 0.0

def calculate_elbow_angle(shoulder, elbow, wrist):
    """
    Calculate shooting elbow angle (ideal: 95° for professionals)
    
    Args:
        shoulder: Shoulder coordinates (x, y)
        elbow: Elbow coordinates (x, y)
        wrist: Wrist coordinates (x, y)
        
    Returns:
        float: Elbow angle in degrees
    """
    angle = calculate_angle(shoulder, elbow, wrist)
    print(f"Elbow angle: {angle}° (shoulder: {shoulder}, elbow: {elbow}, wrist: {wrist})")
    
    # Validate angle is reasonable for basketball shooting
    if angle < 60 or angle > 150:
        print(f"⚠️ Warning: Unusual elbow angle {angle}° - possible detection error")
    
    return angle

def calculate_knee_angle(hip, knee, ankle):
    """
    Calculate knee bend angle (ideal: 130° for professionals)
    
    Args:
        hip: Hip coordinates (x, y)
        knee: Knee coordinates (x, y)
        ankle: Ankle coordinates (x, y)
        
    Returns:
        float: Knee angle in degrees
    """
    angle = calculate_angle(hip, knee, ankle)
    print(f"Knee angle: {angle}° (hip: {hip}, knee: {knee}, ankle: {ankle})")
    
    # Validate angle is reasonable for basketball shooting
    if angle < 90 or angle > 180:
        print(f"⚠️ Warning: Unusual knee angle {angle}° - possible detection error")
    
    return angle

def calculate_release_angle(shoulder, elbow, wrist):
    """
    Calculate release angle relative to horizontal (ground) (ideal: 45-60°)
    
    Args:
        shoulder: Shoulder coordinates (x, y)
        elbow: Elbow coordinates (x, y)
        wrist: Wrist coordinates (x, y)
        
    Returns:
        float: Release angle in degrees
    """
    try:
        # Calculate vector from elbow to wrist (shooting direction)
        wrist_elbow_vector = np.array(wrist) - np.array(elbow)
        
        # Debug logging
        print(f"Release angle calculation:")
        print(f"  Elbow: {elbow}")
        print(f"  Wrist: {wrist}")
        print(f"  Vector: {wrist_elbow_vector}")
        
        # For basketball, we want the angle relative to horizontal (ground level)
        # In computer vision coordinates: Y increases downward, so negative Y means upward
        # We want the angle from horizontal (0 degrees = horizontal, 90 degrees = straight up)
        
        # Calculate the angle from horizontal
        # arctan2(dy, dx) gives angle from horizontal axis
        # Since Y increases downward, we need to negate the Y component
        angle_radians = np.arctan2(-wrist_elbow_vector[1], wrist_elbow_vector[0])
        angle_degrees = np.degrees(angle_radians)
        
        # Convert to positive angle (0-180 degrees)
        if angle_degrees < 0:
            angle_degrees += 180
        
        # For basketball shooting, we want the acute angle (0-90 degrees)
        if angle_degrees > 90:
            angle_degrees = 180 - angle_degrees
        
        # Clamp to realistic basketball shooting range (30-90 degrees)
        angle_degrees = max(30, min(90, angle_degrees))
        
        print(f"  Raw angle: {angle_degrees}°")
        
        return angle_degrees
        
    except Exception as e:
        print(f"Error calculating release angle: {e}")
        return 50.0  # Return a reasonable default

def calculate_body_alignment(left_shoulder, right_shoulder, left_hip, right_hip):
    """
    Calculate body alignment percentage (straight = 100%)
    
    Args:
        left_shoulder: Left shoulder coordinates (x, y)
        right_shoulder: Right shoulder coordinates (x, y)
        left_hip: Left hip coordinates (x, y)
        right_hip: Right hip coordinates (x, y)
        
    Returns:
        float: Body alignment percentage (0-100)
    """
    try:
        # Calculate midpoints
        shoulder_midpoint = np.array([
            (left_shoulder[0] + right_shoulder[0]) / 2,
            (left_shoulder[1] + right_shoulder[1]) / 2
        ])
        hip_midpoint = np.array([
            (left_hip[0] + right_hip[0]) / 2,
            (left_hip[1] + right_hip[1]) / 2
        ])
        
        # Calculate horizontal deviation
        deviation = abs(shoulder_midpoint[0] - hip_midpoint[0])
        
        # Use ABSOLUTE deviation method with realistic threshold
        # Basketball shooting typically has some lateral deviation
        max_acceptable_deviation = 150  # pixels - good alignment
        max_deviation = 500  # pixels - maximum before critical misalignment
        
        if deviation <= max_acceptable_deviation:
            # Excellent to good alignment
            alignment = 100 - (deviation / max_acceptable_deviation * 30)  # 70-100 range
        elif deviation <= max_deviation:
            # Fair to poor alignment
            excess = deviation - max_acceptable_deviation
            alignment = 70 - (excess / (max_deviation - max_acceptable_deviation) * 70)  # 0-70 range
        else:
            # Critical misalignment
            alignment = 0
        
        # Clamp between 0 and 100
        alignment = max(0, min(100, alignment))
        
        print(f"Body alignment: deviation={deviation:.1f}px, alignment={alignment:.1f}%")
        
        return alignment
        
    except Exception as e:
        print(f"Error calculating body alignment: {e}")
        return 70.0  # Return a reasonable default instead of 0

class AngleAnalyzer:
    def __init__(self, frame_window=5):
        """Initialize angle analyzer for basketball pose analysis"""
        self.frame_window = frame_window  # frames for averaging
        self.elbow_angles = []
        self.knee_angles = []
        self.release_angles = []
        self.body_alignments = []
        self.frame_count = 0
        
        # Confidence tracking
        self.elbow_confidence = []
        self.knee_confidence = []
        self.release_confidence = []
        self.alignment_confidence = []
        
        # Landmark visibility tracking
        self.landmark_visibility = []
    
    def detect_outliers(self, data):
        """Remove outliers using IQR method"""
        if len(data) < 3:
            return data
        
        try:
            q1, q3 = np.percentile(data, [25, 75])
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            return [x for x in data if lower_bound <= x <= upper_bound]
        except:
            return data
    
    def calculate_confidence(self, landmark_visibility, angle_std, frame_count):
        """Calculate confidence score 0-100%"""
        try:
            # Base confidence from landmark visibility
            visibility_score = np.mean(landmark_visibility) if landmark_visibility else 0.5
            
            # Stability bonus (lower variance = higher confidence)
            stability_score = max(0, 1 - (angle_std / 30))  # Normalize std to 0-1
            
            # Frame count bonus (more frames = higher confidence)
            frame_score = min(1, frame_count / 30)  # Max confidence at 30+ frames
            
            # Weighted combination
            confidence = (visibility_score * 0.5 + stability_score * 0.3 + frame_score * 0.2) * 100
            
            return max(0, min(100, round(confidence, 1)))
        except:
            return 50.0  # Default confidence
    
    def get_landmark_visibility(self, keypoints):
        """Extract landmark visibility scores from MediaPipe results"""
        try:
            # MediaPipe provides visibility scores (0-1) for each landmark
            # We'll estimate based on landmark presence and quality
            visibility = []
            
            # Key landmarks for shooting analysis
            key_landmarks = [
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
                'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
            ]
            
            for landmark in key_landmarks:
                if landmark in keypoints and keypoints[landmark] is not None:
                    # Estimate visibility based on landmark quality
                    # In a real implementation, this would use MediaPipe's visibility scores
                    visibility.append(0.8)  # Default high visibility
                else:
                    visibility.append(0.2)  # Low visibility if missing
            
            return visibility
        except:
            return [0.5] * 12  # Default visibility
    
    def detect_shooting_hand(self, keypoints):
        """
        Detect which hand is being used for shooting based on pose analysis
        
        Args:
            keypoints: Dictionary of basketball keypoints
            
        Returns:
            str: 'left' or 'right'
        """
        try:
            # Check if all required keypoints exist
            required_keypoints = ['left_wrist', 'right_wrist', 'left_elbow', 'right_elbow', 'left_shoulder', 'right_shoulder']
            for key in required_keypoints:
                if key not in keypoints:
                    print(f"Missing keypoint: {key}")
                    return 'right'  # Default to right-handed
            
            # Compare wrist positions - shooting hand typically higher
            left_wrist_y = keypoints['left_wrist'][1]
            right_wrist_y = keypoints['right_wrist'][1]
            
            # Compare elbow positions - shooting elbow typically more extended
            left_elbow_y = keypoints['left_elbow'][1]
            right_elbow_y = keypoints['right_elbow'][1]
            
            # Compare shoulder positions - shooting side typically more forward
            left_shoulder_x = keypoints['left_shoulder'][0]
            right_shoulder_x = keypoints['right_shoulder'][0]
            
            # Scoring system for hand detection
            right_score = 0
            left_score = 0
            
            # Wrist height (shooting hand is higher)
            if right_wrist_y < left_wrist_y:
                right_score += 1
            else:
                left_score += 1
            
            # Elbow extension (shooting elbow is more extended)
            if right_elbow_y > left_elbow_y:
                right_score += 1
            else:
                left_score += 1
            
            # Shoulder forward position (shooting side is more forward)
            if right_shoulder_x > left_shoulder_x:
                right_score += 1
            else:
                left_score += 1
            
            # Return the side with higher score
            detected_hand = 'right' if right_score > left_score else 'left'
            print(f"Hand detection: Right score={right_score}, Left score={left_score}, Detected={detected_hand}")
            
            return detected_hand
            
        except Exception as e:
            print(f"Error detecting shooting hand: {e}")
            return 'right'  # Default to right-handed
    
    def detect_shot_phase(self, keypoints, frame_number, total_frames):
        """
        Detect the current phase of the basketball shot
        
        Args:
            keypoints: Dictionary of basketball keypoints
            frame_number: Current frame number
            total_frames: Total frames in video
            
        Returns:
            str: 'setup', 'dip', 'release', 'follow_through', or 'unknown'
        """
        try:
            # Calculate frame percentage
            frame_percentage = frame_number / total_frames if total_frames > 0 else 0
            
            # Basic phase detection based on frame position
            if frame_percentage < 0.3:
                return 'setup'
            elif frame_percentage < 0.5:
                return 'dip'
            elif frame_percentage < 0.8:
                return 'release'
            else:
                return 'follow_through'
                
        except Exception as e:
            print(f"Error detecting shot phase: {e}")
            return 'unknown'
    
    def analyze_frame(self, keypoints, frame_number=0, total_frames=0):
        """
        Analyze angles for a single frame with confidence scoring and phase detection
        
        Args:
            keypoints: Dictionary of basketball keypoints
            frame_number: Current frame number
            total_frames: Total frames in video
        """
        try:
            if not keypoints:
                return
            
            # Get landmark visibility for confidence calculation
            visibility = self.get_landmark_visibility(keypoints)
            self.landmark_visibility.append(visibility)
            
            # Detect shooting hand based on wrist position and arm extension
            shooting_side = self.detect_shooting_hand(keypoints)
            
            # Determine shot phase based on frame position and pose analysis
            shot_phase = self.detect_shot_phase(keypoints, frame_number, total_frames)
            
            print(f"Frame {frame_number}: Phase = {shot_phase}, Shooting hand = {shooting_side}")
            
            # Only calculate angles during appropriate phases
            elbow_angle = 0  # Initialize to avoid scope error
            if shot_phase in ['dip', 'release']:
                # Elbow angle is most important during dip and release phases
                if shooting_side == 'right':
                    elbow_angle = calculate_elbow_angle(
                        keypoints['right_shoulder'],
                        keypoints['right_elbow'],
                        keypoints['right_wrist']
                    )
                else:
                    elbow_angle = calculate_elbow_angle(
                        keypoints['left_shoulder'],
                        keypoints['left_elbow'],
                        keypoints['left_wrist']
                    )
                self.elbow_angles.append(elbow_angle)
                print(f"  Elbow angle measured: {elbow_angle}° (Phase: {shot_phase})")
            else:
                # Don't measure elbow angle during setup or follow-through
                self.elbow_angles.append(0)  # Placeholder
            
            # Initialize knee_angle to avoid scope error
            knee_angle = 0
            if shot_phase in ['setup', 'dip']:
                # Knee angle is most important during setup and dip phases
                if shooting_side == 'right':
                    knee_angle = calculate_knee_angle(
                        keypoints['right_hip'],
                        keypoints['right_knee'],
                        keypoints['right_ankle']
                    )
                else:
                    knee_angle = calculate_knee_angle(
                        keypoints['left_hip'],
                        keypoints['left_knee'],
                        keypoints['left_ankle']
                    )
                self.knee_angles.append(knee_angle)
                print(f"  Knee angle measured: {knee_angle}° (Phase: {shot_phase})")
            else:
                # Don't measure knee angle during release or follow-through
                self.knee_angles.append(0)  # Placeholder
            
            # Initialize release_angle to avoid scope error
            release_angle = 0
            if shot_phase == 'release':
                # Release angle should ONLY be measured during release phase
                if shooting_side == 'right':
                    release_angle = calculate_release_angle(
                        keypoints['right_shoulder'],
                        keypoints['right_elbow'],
                        keypoints['right_wrist']
                    )
                else:
                    release_angle = calculate_release_angle(
                        keypoints['left_shoulder'],
                        keypoints['left_elbow'],
                        keypoints['left_wrist']
                    )
                self.release_angles.append(release_angle)
                print(f"  Release angle measured: {release_angle}° (Phase: {shot_phase})")
            else:
                # Don't measure release angle during other phases
                self.release_angles.append(0)  # Placeholder
            
            # Calculate body alignment (uses both sides)
            body_alignment = calculate_body_alignment(
                keypoints['left_shoulder'],
                keypoints['right_shoulder'],
                keypoints['left_hip'],
                keypoints['right_hip']
            )
            
            # Store body alignment only (angles already appended above)
            self.body_alignments.append(body_alignment)
            self.frame_count += 1
            
            # Calculate confidence scores for this frame
            elbow_std = np.std(self.elbow_angles) if len(self.elbow_angles) > 1 else 0
            knee_std = np.std(self.knee_angles) if len(self.knee_angles) > 1 else 0
            release_std = np.std(self.release_angles) if len(self.release_angles) > 1 else 0
            alignment_std = np.std(self.body_alignments) if len(self.body_alignments) > 1 else 0
            
            # Store confidence scores
            self.elbow_confidence.append(
                self.calculate_confidence(visibility, elbow_std, self.frame_count)
            )
            self.knee_confidence.append(
                self.calculate_confidence(visibility, knee_std, self.frame_count)
            )
            self.release_confidence.append(
                self.calculate_confidence(visibility, release_std, self.frame_count)
            )
            self.alignment_confidence.append(
                self.calculate_confidence(visibility, alignment_std, self.frame_count)
            )
            
        except Exception as e:
            print(f"Error analyzing frame: {e}")
    
    def get_average_metrics(self):
        """
        Calculate average metrics with outlier detection and confidence scores
        
        Returns:
            dict: Average metrics with confidence scores
        """
        try:
            metrics = {
                'elbow_angle': 0.0,
                'knee_angle': 0.0,
                'release_angle': 0.0,
                'body_alignment': 0.0,
                'elbow_confidence': 0.0,
                'knee_confidence': 0.0,
                'release_confidence': 0.0,
                'alignment_confidence': 0.0,
            }
            
            # Filter out placeholder zeros (frames where angles weren't measured)
            valid_elbow = [angle for angle in self.elbow_angles if angle > 0]
            valid_knee = [angle for angle in self.knee_angles if angle > 0]
            valid_release = [angle for angle in self.release_angles if angle > 0]
            valid_alignment = [angle for angle in self.body_alignments if angle > 0]
            
            print(f"Valid measurements - Elbow: {len(valid_elbow)}, Knee: {len(valid_knee)}, Release: {len(valid_release)}, Alignment: {len(valid_alignment)}")
            
            # Apply outlier detection and calculate averages
            if valid_elbow:
                clean_elbow = self.detect_outliers(valid_elbow)
                metrics['elbow_angle'] = round(np.mean(clean_elbow), 2)
                # Handle NaN in confidence calculation
                elbow_conf = np.mean(self.elbow_confidence) if self.elbow_confidence else 0.5
                metrics['elbow_confidence'] = round(elbow_conf if not np.isnan(elbow_conf) else 0.5, 1)
            
            if valid_knee:
                clean_knee = self.detect_outliers(valid_knee)
                metrics['knee_angle'] = round(np.mean(clean_knee), 2)
                # Handle NaN in confidence calculation
                knee_conf = np.mean(self.knee_confidence) if self.knee_confidence else 0.5
                metrics['knee_confidence'] = round(knee_conf if not np.isnan(knee_conf) else 0.5, 1)
            
            if valid_release:
                clean_release = self.detect_outliers(valid_release)
                metrics['release_angle'] = round(np.mean(clean_release), 2)
                # Handle NaN in confidence calculation
                release_conf = np.mean(self.release_confidence) if self.release_confidence else 0.5
                metrics['release_confidence'] = round(release_conf if not np.isnan(release_conf) else 0.5, 1)
            
            if valid_alignment:
                clean_alignment = self.detect_outliers(valid_alignment)
                metrics['body_alignment'] = round(np.mean(clean_alignment), 2)
                # Handle NaN in confidence calculation
                alignment_conf = np.mean(self.alignment_confidence) if self.alignment_confidence else 0.5
                metrics['alignment_confidence'] = round(alignment_conf if not np.isnan(alignment_conf) else 0.5, 1)
            
            return metrics
            
        except Exception as e:
            print(f"Error calculating average metrics: {e}")
            return {
                'elbow_angle': 0.0,
                'knee_angle': 0.0,
                'release_angle': 0.0,
                'body_alignment': 0.0,
                'elbow_confidence': 0.0,
                'knee_confidence': 0.0,
                'release_confidence': 0.0,
                'alignment_confidence': 0.0,
            }
    
    def get_metrics_variance(self):
        """
        Calculate variance in metrics to assess consistency
        
        Returns:
            dict: Variance for each metric
        """
        try:
            variance = {
                'elbow_variance': 0.0,
                'knee_variance': 0.0,
                'release_variance': 0.0,
                'alignment_variance': 0.0,
            }
            
            if len(self.elbow_angles) > 1:
                variance['elbow_variance'] = round(np.var(self.elbow_angles), 2)
            if len(self.knee_angles) > 1:
                variance['knee_variance'] = round(np.var(self.knee_angles), 2)
            if len(self.release_angles) > 1:
                variance['release_variance'] = round(np.var(self.release_angles), 2)
            if len(self.body_alignments) > 1:
                variance['alignment_variance'] = round(np.var(self.body_alignments), 2)
            
            return variance
            
        except Exception as e:
            print(f"Error calculating variance: {e}")
            return {
                'elbow_variance': 0.0,
                'knee_variance': 0.0,
                'release_variance': 0.0,
                'alignment_variance': 0.0,
            }
    
    def get_frame_data(self):
        """
        Get frame-by-frame data for angle graphs
        
        Returns:
            list: Frame data with angles for visualization
        """
        try:
            frame_data = []
            for i in range(len(self.elbow_angles)):
                frame_data.append({
                    'frame_number': i,
                    'elbow_angle': self.elbow_angles[i],
                    'knee_angle': self.knee_angles[i],
                    'release_angle': self.release_angles[i],
                    'body_alignment': self.body_alignments[i],
                    'elbow_confidence': self.elbow_confidence[i] if i < len(self.elbow_confidence) else 0,
                    'knee_confidence': self.knee_confidence[i] if i < len(self.knee_confidence) else 0,
                    'release_confidence': self.release_confidence[i] if i < len(self.release_confidence) else 0,
                    'alignment_confidence': self.alignment_confidence[i] if i < len(self.alignment_confidence) else 0,
                })
            return frame_data
        except Exception as e:
            print(f"Error getting frame data: {e}")
            return []
    
    def get_consistency_score(self):
        """
        Calculate overall consistency score (0-100)
        
        Returns:
            float: Consistency score based on angle stability
        """
        try:
            if not self.elbow_angles or len(self.elbow_angles) < 2:
                return 0.0
            
            # Calculate coefficient of variation for each metric
            elbow_cv = np.std(self.elbow_angles) / np.mean(self.elbow_angles) if np.mean(self.elbow_angles) > 0 else 1
            knee_cv = np.std(self.knee_angles) / np.mean(self.knee_angles) if np.mean(self.knee_angles) > 0 else 1
            release_cv = np.std(self.release_angles) / np.mean(self.release_angles) if np.mean(self.release_angles) > 0 else 1
            alignment_cv = np.std(self.body_alignments) / np.mean(self.body_alignments) if np.mean(self.body_alignments) > 0 else 1
            
            # Lower CV = higher consistency
            # Convert to 0-100 scale (lower CV = higher score)
            elbow_consistency = max(0, 100 - (elbow_cv * 100))
            knee_consistency = max(0, 100 - (knee_cv * 100))
            release_consistency = max(0, 100 - (release_cv * 100))
            alignment_consistency = max(0, 100 - (alignment_cv * 100))
            
            # Average consistency across all metrics
            overall_consistency = (elbow_consistency + knee_consistency + release_consistency + alignment_consistency) / 4
            
            return round(overall_consistency, 1)
        except Exception as e:
            print(f"Error calculating consistency score: {e}")
            return 0.0
    
    def reset(self):
        """Reset analyzer for new video"""
        self.elbow_angles = []
        self.knee_angles = []
        self.release_angles = []
        self.body_alignments = []
        self.frame_count = 0
        
        # Reset confidence tracking
        self.elbow_confidence = []
        self.knee_confidence = []
        self.release_confidence = []
        self.alignment_confidence = []
        
        # Reset landmark visibility
        self.landmark_visibility = []
