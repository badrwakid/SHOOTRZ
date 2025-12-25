"""
Shot event and window detection for MVP pipeline.

Detects crouch phase (knee minimum) and release point (wrist peak)
to define the shot window for metric extraction.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from scipy.signal import find_peaks


class ShotDetector:
    """Detects shot phases and defines shot window."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize shot detector.
        
        Args:
            config: Shot detection config from MVPConfig
        """
        self.config = config
        self.knee_flexion_threshold = config.get("knee_flexion_threshold", 100.0)
        self.wrist_peak_window = config.get("wrist_peak_window", 15)
        self.pre_frames = config.get("pre_frames", 10)
        self.post_frames = config.get("post_frames", 20)
    
    def detect_shot_window(
        self,
        angles_df: pd.DataFrame,
        pose_keypoints_df: pd.DataFrame,
        shooting_side: str
    ) -> Dict[str, Any]:
        """
        Detect shot window (start, crouch, release, end).
        
        Args:
            angles_df: Angles DataFrame with knee_angle, elbow_angle, wrist_angle
            pose_keypoints_df: Pose keypoints for wrist position
            shooting_side: "left" or "right"
        
        Returns:
            Dict with start_frame, crouch_frame, release_frame, end_frame, confidence, method
        """
        # Sort by frame_id
        angles_df = angles_df.sort_values("frame_id")
        
        # Detect crouch (knee angle minimum)
        crouch_frame, crouch_confidence = self._detect_crouch(angles_df)
        
        # Detect release (wrist y-position peak after crouch)
        release_frame, release_confidence = self._detect_release(
            pose_keypoints_df,
            shooting_side,
            crouch_frame
        )
        
        # Define shot window
        start_frame = max(0, crouch_frame - self.pre_frames)
        end_frame = min(
            angles_df["frame_id"].max(),
            release_frame + self.post_frames
        )
        
        # Overall confidence
        overall_confidence = min(crouch_confidence, release_confidence)
        
        shot_window = {
            "start_frame": int(start_frame),
            "crouch_frame": int(crouch_frame),
            "release_frame": int(release_frame),
            "end_frame": int(end_frame),
            "confidence": "high" if overall_confidence > 0.7 else "medium" if overall_confidence > 0.4 else "low",
            "confidence_score": float(overall_confidence),
            "method": "knee_minimum_wrist_peak",
            "crouch_confidence": float(crouch_confidence),
            "release_confidence": float(release_confidence),
        }
        
        return shot_window
    
    def _detect_crouch(self, angles_df: pd.DataFrame) -> Tuple[int, float]:
        """
        Detect crouch phase as knee angle minimum.
        
        Returns:
            Tuple of (crouch_frame, confidence)
        """
        knee_angles = angles_df["knee_angle"].values
        knee_confidence = angles_df["confidence_knee"].values
        frame_ids = angles_df["frame_id"].values
        
        # Remove NaN values
        valid_mask = ~np.isnan(knee_angles)
        knee_angles = knee_angles[valid_mask]
        knee_confidence = knee_confidence[valid_mask]
        frame_ids = frame_ids[valid_mask]
        
        if len(knee_angles) == 0:
            # No valid data, return middle frame
            middle_idx = len(angles_df) // 2
            return int(angles_df.iloc[middle_idx]["frame_id"]), 0.2
        
        # Find minimum knee angle (maximum flexion)
        min_idx = np.argmin(knee_angles)
        crouch_frame = frame_ids[min_idx]
        confidence = knee_confidence[min_idx]
        
        # Check if minimum is below threshold
        if knee_angles[min_idx] > self.knee_flexion_threshold:
            # Not a clear crouch, reduce confidence
            confidence *= 0.5
        
        return int(crouch_frame), float(confidence)
    
    def _detect_release(
        self,
        pose_keypoints_df: pd.DataFrame,
        shooting_side: str,
        crouch_frame: int
    ) -> Tuple[int, float]:
        """
        Detect release as wrist y-position peak after crouch.
        
        Returns:
            Tuple of (release_frame, confidence)
        """
        # Get wrist joint name
        wrist_joint = f"{shooting_side}_wrist"
        
        # Filter to wrist only
        wrist_df = pose_keypoints_df[
            pose_keypoints_df["joint"] == wrist_joint
        ].sort_values("frame_id")
        
        # Use smoothed coordinates if available
        y_col = "y_norm_smooth" if "y_norm_smooth" in wrist_df.columns else "y_norm"
        
        # Get frames after crouch
        after_crouch = wrist_df[wrist_df["frame_id"] >= crouch_frame]
        
        if len(after_crouch) == 0:
            # No data after crouch, use crouch as release
            return int(crouch_frame), 0.3
        
        # Find peaks in wrist trajectory (lower Y = higher position)
        # Invert Y so peaks become valleys
        wrist_y = -after_crouch[y_col].values
        
        # Find peaks with minimum distance
        peaks, properties = find_peaks(
            wrist_y,
            distance=self.wrist_peak_window,
            prominence=0.01
        )
        
        if len(peaks) > 0:
            # Use first peak after crouch
            peak_idx = peaks[0]
            release_frame = after_crouch.iloc[peak_idx]["frame_id"]
            confidence = after_crouch.iloc[peak_idx]["confidence"]
        else:
            # No clear peak, use highest point after crouch
            max_idx = np.argmax(wrist_y)
            release_frame = after_crouch.iloc[max_idx]["frame_id"]
            confidence = after_crouch.iloc[max_idx]["confidence"] * 0.7
        
        return int(release_frame), float(confidence)
    
    def export_shot_window_json(self, shot_window: Dict[str, Any], output_path: Path):
        """
        Export shot window to JSON.
        
        Args:
            shot_window: Shot window dict
            output_path: Path to save JSON
        """
        with open(output_path, 'w') as f:
            json.dump(shot_window, f, indent=2)


def detect_shot_window(
    angles_csv: Path,
    pose_keypoints_csv: Path,
    shooting_side: str,
    config: Dict[str, Any],
    output_path: Path
) -> Dict[str, Any]:
    """
    Convenience function to detect shot window.
    
    Args:
        angles_csv: Path to angles CSV
        pose_keypoints_csv: Path to pose keypoints CSV
        shooting_side: "left" or "right"
        config: Shot detection config
        output_path: Path to save shot_window.json
    
    Returns:
        Shot window dict
    """
    # Load data
    angles_df = pd.read_csv(angles_csv)
    pose_df = pd.read_csv(pose_keypoints_csv)
    
    # Create detector and process
    detector = ShotDetector(config)
    shot_window = detector.detect_shot_window(angles_df, pose_df, shooting_side)
    
    # Save
    detector.export_shot_window_json(shot_window, output_path)
    
    return shot_window
