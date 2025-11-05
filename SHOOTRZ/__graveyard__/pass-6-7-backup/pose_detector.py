import cv2
import numpy as np
import mediapipe as mp

class PoseDetector:
    def __init__(self):
        """Initialize MediaPipe Pose for basketball pose detection"""
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,  # 0=fast, 1=balanced, 2=accurate
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
    def detect_poses(self, frame):
        """
        Detect pose landmarks in frame using MediaPipe
        
        Args:
            frame: OpenCV frame (numpy array)
            
        Returns:
            landmarks: MediaPipe pose landmarks or None
        """
        try:
            # Convert BGR to RGB for MediaPipe
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Process the frame
            results = self.pose.process(rgb_frame)
            
            if results.pose_landmarks:
                return results.pose_landmarks
            else:
                return None
                
        except Exception as e:
            print(f"Error in pose detection: {e}")
            return None
    
    def draw_pose(self, frame, landmarks):
        """
        Draw pose skeleton on frame
        
        Args:
            frame: OpenCV frame
            landmarks: MediaPipe pose landmarks
            
        Returns:
            annotated_frame: Frame with pose skeleton drawn
        """
        try:
            annotated_frame = frame.copy()
            self.mp_drawing.draw_landmarks(
                annotated_frame,
                landmarks,
                self.mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(0, 255, 0), thickness=2, circle_radius=2
                ),
                connection_drawing_spec=self.mp_drawing.DrawingSpec(
                    color=(255, 0, 0), thickness=2
                )
            )
            return annotated_frame
        except Exception as e:
            print(f"Error drawing pose: {e}")
            return frame
    
    def get_basketball_keypoints(self, landmarks, frame_shape):
        """
        Extract basketball-relevant keypoints from MediaPipe landmarks
        
        Args:
            landmarks: MediaPipe pose landmarks
            frame_shape: Shape of the frame (height, width, channels)
            
        Returns:
            dict: Basketball-specific keypoints with pixel coordinates
        """
        try:
            h, w = frame_shape[:2]
            
            # MediaPipe landmark indices for basketball analysis
            # MediaPipe uses 33 landmarks, we need specific ones for basketball
            keypoints = {
                'left_shoulder': (landmarks.landmark[11].x * w, landmarks.landmark[11].y * h),
                'right_shoulder': (landmarks.landmark[12].x * w, landmarks.landmark[12].y * h),
                'left_elbow': (landmarks.landmark[13].x * w, landmarks.landmark[13].y * h),
                'right_elbow': (landmarks.landmark[14].x * w, landmarks.landmark[14].y * h),
                'left_wrist': (landmarks.landmark[15].x * w, landmarks.landmark[15].y * h),
                'right_wrist': (landmarks.landmark[16].x * w, landmarks.landmark[16].y * h),
                'left_hip': (landmarks.landmark[23].x * w, landmarks.landmark[23].y * h),
                'right_hip': (landmarks.landmark[24].x * w, landmarks.landmark[24].y * h),
                'left_knee': (landmarks.landmark[25].x * w, landmarks.landmark[25].y * h),
                'right_knee': (landmarks.landmark[26].x * w, landmarks.landmark[26].y * h),
                'left_ankle': (landmarks.landmark[27].x * w, landmarks.landmark[27].y * h),
                'right_ankle': (landmarks.landmark[28].x * w, landmarks.landmark[28].y * h),
            }
            
            return keypoints
            
        except Exception as e:
            print(f"Error extracting keypoints: {e}")
            return None
    
    def get_landmark_confidence(self, landmarks, landmark_index):
        """
        Get confidence score for a specific landmark
        
        Args:
            landmarks: MediaPipe pose landmarks
            landmark_index: Index of the landmark
            
        Returns:
            float: Confidence score (0-1)
        """
        try:
            if landmarks and landmark_index < len(landmarks.landmark):
                return landmarks.landmark[landmark_index].visibility
            return 0.0
        except Exception as e:
            print(f"Error getting landmark confidence: {e}")
            return 0.0
    
    def is_pose_visible(self, landmarks, min_confidence=0.5):
        """
        Check if pose is visible enough for analysis
        
        Args:
            landmarks: MediaPipe pose landmarks
            min_confidence: Minimum confidence threshold
            
        Returns:
            bool: True if pose is visible enough
        """
        try:
            if not landmarks:
                return False
            
            # Check key landmarks for basketball analysis
            key_landmarks = [11, 12, 13, 14, 15, 16, 23, 24, 25, 26]  # shoulders, elbows, wrists, hips, knees
            
            visible_count = 0
            for landmark_idx in key_landmarks:
                if self.get_landmark_confidence(landmarks, landmark_idx) >= min_confidence:
                    visible_count += 1
            
            # Require at least 70% of key landmarks to be visible
            return visible_count >= len(key_landmarks) * 0.7
            
        except Exception as e:
            print(f"Error checking pose visibility: {e}")
            return False