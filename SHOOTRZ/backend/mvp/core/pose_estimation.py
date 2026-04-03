"""
Pose estimation adapter for MVP pipeline.

Wraps MediaPipePoseDetector with config-driven initialization and
provides coordinate normalization, shooting-side detection, and persistence.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from backend.inference.pose_2d import MediaPipePoseDetector, BASKETBALL_KEYPOINTS


class MVPPoseEstimator:
    """Config-driven pose estimation for MVP pipeline."""
    
    def __init__(self, config: Dict[str, Any], video_metadata: Dict[str, Any]):
        """
        Initialize pose estimator.
        
        Args:
            config: Pose detection config from MVPConfig
            video_metadata: Video metadata (width, height, fps)
        """
        self.config = config
        self.video_metadata = video_metadata
        
        # Initialize MediaPipe detector
        self.detector = MediaPipePoseDetector(
            static_image_mode=False,
            model_complexity=config.get("model_complexity", 1),
            smooth_landmarks=config.get("smooth_landmarks", True),
            min_detection_confidence=config.get("min_detection_confidence", 0.5),
            min_tracking_confidence=config.get("min_tracking_confidence", 0.5),
        )
        
        self.confidence_threshold = config.get("confidence_threshold", 0.3)
        self.width = video_metadata["width"]
        self.height = video_metadata["height"]
        self.fps = video_metadata["fps"]
        
        self.pose_results: List[Dict[str, Any]] = []
        self.shooting_side: Optional[str] = None
    
    def process_frames(
        self,
        frames: List[np.ndarray],
        frame_mapping: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Process all frames to extract pose landmarks.
        
        Args:
            frames: List of RGB frames
            frame_mapping: DataFrame with frame indices and timestamps
        
        Returns:
            List of pose results per frame
        """
        self.pose_results = []
        
        for processed_idx, frame in enumerate(frames):
            # VideoLoader passes RGB frames; avoid double BGR->RGB in pose_2d
            result = self.detector.process_frame(frame, input_is_rgb=True)

            # Get timestamp from mapping
            timestamp = frame_mapping.loc[
                frame_mapping["processed_idx"] == processed_idx,
                "timestamp"
            ].values[0]

            original_idx = frame_mapping.loc[
                frame_mapping["processed_idx"] == processed_idx,
                "original_idx"
            ].values[0]

            if result is None:
                # Keep timeline dense to avoid downstream frame-index drift.
                self.pose_results.append({
                    "frame_idx": int(original_idx),
                    "processed_idx": processed_idx,
                    "timestamp": float(timestamp),
                    "landmarks": np.zeros((33, 3), dtype=np.float32),
                    "confidence": np.zeros((33,), dtype=np.float32),
                })
            else:
                self.pose_results.append({
                    "frame_idx": int(original_idx),
                    "processed_idx": processed_idx,
                    "timestamp": float(timestamp),
                    "landmarks": result["landmarks"],
                    "confidence": result["confidence"],
                })
        
        return self.pose_results
    
    def determine_shooting_side(
        self,
        shooting_side: str = "auto"
    ) -> str:
        """
        Determine shooting side (left/right).
        
        Args:
            shooting_side: "auto", "left", or "right"
        
        Returns:
            Detected or specified shooting side
        """
        if shooting_side in ["left", "right"]:
            self.shooting_side = shooting_side
            return shooting_side
        
        # Auto-detect: which wrist reaches higher peak?
        if not self.pose_results:
            self.shooting_side = "right"  # Default
            return "right"
        
        left_wrist_peaks = []
        right_wrist_peaks = []
        
        for result in self.pose_results:
            landmarks = result["landmarks"]
            confidence = result["confidence"]
            
            # Left wrist (index 15)
            if len(landmarks) > 15 and confidence[15] > self.confidence_threshold:
                left_wrist_peaks.append(landmarks[15][1])  # Y coordinate (lower = higher)
            
            # Right wrist (index 16)
            if len(landmarks) > 16 and confidence[16] > self.confidence_threshold:
                right_wrist_peaks.append(landmarks[16][1])
        
        # Lower Y = higher position (inverted coordinates)
        left_max_height = min(left_wrist_peaks) if left_wrist_peaks else 1.0
        right_max_height = min(right_wrist_peaks) if right_wrist_peaks else 1.0
        
        self.shooting_side = "left" if left_max_height < right_max_height else "right"
        return self.shooting_side
    
    def export_pose_keypoints_csv(self, output_path: Path, run_id: str):
        """
        Export pose keypoints to CSV with both normalized and pixel coordinates.
        
        Args:
            output_path: Path to save CSV
            run_id: Run ID for tracking
        """
        rows = []
        
        for result in self.pose_results:
            frame_idx = result["frame_idx"]
            timestamp = result["timestamp"]
            landmarks = result["landmarks"]
            confidence = result["confidence"]
            
            for joint_name, joint_idx in BASKETBALL_KEYPOINTS.items():
                if joint_idx < len(landmarks):
                    x_norm, y_norm, z_norm = landmarks[joint_idx]
                    x_px = x_norm * self.width
                    y_px = y_norm * self.height
                    conf = confidence[joint_idx]
                    
                    rows.append({
                        "run_id": run_id,
                        "frame_id": frame_idx,
                        "timestamp": timestamp,
                        "joint": joint_name,
                        "x_norm": x_norm,
                        "y_norm": y_norm,
                        "z_norm": z_norm,
                        "x_px": x_px,
                        "y_px": y_px,
                        "confidence": conf,
                    })
        
        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
    
    def export_pose_keypoints_json(self, output_path: Path):
        """
        Export pose keypoints to JSON (structured format).
        
        Args:
            output_path: Path to save JSON
        """
        export_data = {
            "video_metadata": self.video_metadata,
            "shooting_side": self.shooting_side,
            "total_frames": len(self.pose_results),
            "frames": []
        }
        
        for result in self.pose_results:
            frame_data = {
                "frame_idx": result["frame_idx"],
                "timestamp": result["timestamp"],
                "joints": {}
            }
            
            landmarks = result["landmarks"]
            confidence = result["confidence"]
            
            for joint_name, joint_idx in BASKETBALL_KEYPOINTS.items():
                if joint_idx < len(landmarks):
                    x_norm, y_norm, z_norm = landmarks[joint_idx]
                    frame_data["joints"][joint_name] = {
                        "x_norm": float(x_norm),
                        "y_norm": float(y_norm),
                        "z_norm": float(z_norm),
                        "x_px": float(x_norm * self.width),
                        "y_px": float(y_norm * self.height),
                        "confidence": float(confidence[joint_idx]),
                    }
            
            export_data["frames"].append(frame_data)
        
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
    
    def compute_confidence_summary(self) -> Dict[str, Any]:
        """
        Compute confidence statistics across all frames.
        
        Returns:
            Dictionary with per-joint and overall confidence stats
        """
        if not self.pose_results:
            return {"overall": 0.0, "per_joint": {}, "low_confidence_frames": []}
        
        # Aggregate confidence per joint
        joint_confidences = {name: [] for name in BASKETBALL_KEYPOINTS.keys()}
        low_confidence_frames = []
        
        for result in self.pose_results:
            confidence = result["confidence"]
            frame_avg_confidence = np.mean(confidence)
            
            if frame_avg_confidence < self.confidence_threshold:
                low_confidence_frames.append({
                    "frame_idx": result["frame_idx"],
                    "confidence": float(frame_avg_confidence)
                })
            
            for joint_name, joint_idx in BASKETBALL_KEYPOINTS.items():
                if joint_idx < len(confidence):
                    joint_confidences[joint_name].append(confidence[joint_idx])
        
        # Compute averages
        per_joint_avg = {
            joint: float(np.mean(confs)) if confs else 0.0
            for joint, confs in joint_confidences.items()
        }
        
        overall_avg = float(np.mean([conf for confs in joint_confidences.values() for conf in confs]))
        
        return {
            "overall": overall_avg,
            "per_joint": per_joint_avg,
            "low_confidence_frames": low_confidence_frames,
            "total_frames": len(self.pose_results),
            "confidence_threshold": self.confidence_threshold,
        }
    
    def export_confidence_summary(self, output_path: Path):
        """
        Export confidence summary to JSON.
        
        Args:
            output_path: Path to save JSON
        """
        summary = self.compute_confidence_summary()
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
    
    def close(self):
        """Release MediaPipe resources."""
        self.detector.close()
