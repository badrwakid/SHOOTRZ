"""
Joint angle computation for MVP pipeline.

Computes elbow flexion, knee flexion, and wrist proxy angles per frame
using existing biomechanics functions.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from metrics.biomechanics import joint_angle
from inference.pose_2d import BASKETBALL_KEYPOINTS


class AngleComputer:
    """Computes biomechanical angles from pose keypoints."""
    
    def __init__(self, shooting_side: str = "right", confidence_threshold: float = 0.3):
        """
        Initialize angle computer.
        
        Args:
            shooting_side: "left" or "right"
            confidence_threshold: Minimum confidence for valid angle
        """
        self.shooting_side = shooting_side
        self.confidence_threshold = confidence_threshold
        
        # Define joint indices based on shooting side
        self.shoulder_idx = BASKETBALL_KEYPOINTS[f"{shooting_side}_shoulder"]
        self.elbow_idx = BASKETBALL_KEYPOINTS[f"{shooting_side}_elbow"]
        self.wrist_idx = BASKETBALL_KEYPOINTS[f"{shooting_side}_wrist"]
        self.hip_idx = BASKETBALL_KEYPOINTS[f"{shooting_side}_hip"]
        self.knee_idx = BASKETBALL_KEYPOINTS[f"{shooting_side}_knee"]
        self.ankle_idx = BASKETBALL_KEYPOINTS[f"{shooting_side}_ankle"]
    
    def compute_angles_per_frame(
        self,
        pose_keypoints_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute angles for each frame.
        
        Args:
            pose_keypoints_df: Smoothed pose keypoints DataFrame
        
        Returns:
            DataFrame with frame_id, timestamp, elbow_angle, knee_angle, wrist_angle, confidences
        """
        # Use smoothed coordinates if available, otherwise raw
        coord_suffix = "_smooth" if "x_norm_smooth" in pose_keypoints_df.columns else ""
        
        frames = pose_keypoints_df["frame_id"].unique()
        angle_rows = []
        
        for frame_id in frames:
            frame_data = pose_keypoints_df[pose_keypoints_df["frame_id"] == frame_id]
            
            # Extract timestamp
            timestamp = frame_data["timestamp"].iloc[0]
            
            # Get joint positions
            joints = self._extract_joints(frame_data, coord_suffix)
            
            if joints is None:
                # Missing critical joints
                angle_rows.append({
                    "frame_id": frame_id,
                    "timestamp": timestamp,
                    "elbow_angle": np.nan,
                    "knee_angle": np.nan,
                    "wrist_angle": np.nan,
                    "confidence_elbow": 0.0,
                    "confidence_knee": 0.0,
                    "confidence_wrist": 0.0,
                })
                continue
            
            # Compute elbow flexion (shoulder-elbow-wrist)
            elbow_angle, elbow_conf = self._compute_elbow_angle(joints)
            
            # Compute knee flexion (hip-knee-ankle)
            knee_angle, knee_conf = self._compute_knee_angle(joints)
            
            # Compute wrist proxy angle (wrist-elbow-vertical)
            wrist_angle, wrist_conf = self._compute_wrist_angle(joints)
            
            angle_rows.append({
                "frame_id": frame_id,
                "timestamp": timestamp,
                "elbow_angle": elbow_angle,
                "knee_angle": knee_angle,
                "wrist_angle": wrist_angle,
                "confidence_elbow": elbow_conf,
                "confidence_knee": knee_conf,
                "confidence_wrist": wrist_conf,
            })
        
        return pd.DataFrame(angle_rows)
    
    def _extract_joints(
        self,
        frame_data: pd.DataFrame,
        coord_suffix: str
    ) -> Dict[str, Any]:
        """Extract joint positions and confidences for one frame."""
        joints = {}
        
        joint_mapping = {
            "shoulder": self.shoulder_idx,
            "elbow": self.elbow_idx,
            "wrist": self.wrist_idx,
            "hip": self.hip_idx,
            "knee": self.knee_idx,
            "ankle": self.ankle_idx,
        }
        
        for joint_name, joint_idx in joint_mapping.items():
            # Find row for this joint
            joint_rows = frame_data[frame_data["joint"].str.contains(joint_name, case=False, na=False)]
            
            if len(joint_rows) == 0:
                return None  # Missing critical joint
            
            row = joint_rows.iloc[0]
            
            joints[joint_name] = {
                "pos": np.array([
                    row[f"x_norm{coord_suffix}"],
                    row[f"y_norm{coord_suffix}"],
                    row.get(f"z_norm{coord_suffix}", 0.0)
                ]),
                "confidence": row["confidence"]
            }
        
        return joints
    
    def _compute_elbow_angle(self, joints: Dict[str, Any]) -> tuple:
        """Compute elbow flexion angle."""
        shoulder = joints["shoulder"]["pos"]
        elbow = joints["elbow"]["pos"]
        wrist = joints["wrist"]["pos"]
        
        # Check confidence
        conf = min(
            joints["shoulder"]["confidence"],
            joints["elbow"]["confidence"],
            joints["wrist"]["confidence"]
        )
        
        if conf < self.confidence_threshold:
            return np.nan, conf
        
        # Compute angle
        angle = joint_angle(shoulder, elbow, wrist)
        return angle, conf
    
    def _compute_knee_angle(self, joints: Dict[str, Any]) -> tuple:
        """Compute knee flexion angle."""
        hip = joints["hip"]["pos"]
        knee = joints["knee"]["pos"]
        ankle = joints["ankle"]["pos"]
        
        # Check confidence
        conf = min(
            joints["hip"]["confidence"],
            joints["knee"]["confidence"],
            joints["ankle"]["confidence"]
        )
        
        if conf < self.confidence_threshold:
            return np.nan, conf
        
        # Compute angle
        angle = joint_angle(hip, knee, ankle)
        return angle, conf
    
    def _compute_wrist_angle(self, joints: Dict[str, Any]) -> tuple:
        """
        Compute wrist proxy angle (wrist-elbow-vertical).
        
        This measures wrist extension relative to forearm.
        """
        elbow = joints["elbow"]["pos"]
        wrist = joints["wrist"]["pos"]
        
        # Check confidence
        conf = min(
            joints["elbow"]["confidence"],
            joints["wrist"]["confidence"]
        )
        
        if conf < self.confidence_threshold:
            return np.nan, conf
        
        # Create vertical reference point above elbow
        vertical_point = elbow.copy()
        vertical_point[1] -= 0.1  # 0.1 units above elbow (Y is inverted)
        
        # Compute angle between wrist-elbow-vertical
        angle = joint_angle(wrist, elbow, vertical_point)
        return angle, conf
    
    def export_angles_csv(self, angles_df: pd.DataFrame, output_path: Path):
        """
        Export angles to CSV.
        
        Args:
            angles_df: Angles DataFrame
            output_path: Path to save CSV
        """
        angles_df.to_csv(output_path, index=False)


def compute_angles(
    pose_keypoints_csv: Path,
    shooting_side: str,
    confidence_threshold: float,
    output_path: Path
) -> pd.DataFrame:
    """
    Convenience function to compute angles.
    
    Args:
        pose_keypoints_csv: Path to smoothed pose keypoints CSV
        shooting_side: "left" or "right"
        confidence_threshold: Minimum confidence
        output_path: Path to save angles CSV
    
    Returns:
        Angles DataFrame
    """
    # Load pose keypoints
    pose_df = pd.read_csv(pose_keypoints_csv)
    
    # Create computer and process
    computer = AngleComputer(shooting_side, confidence_threshold)
    angles_df = computer.compute_angles_per_frame(pose_df)
    
    # Save
    computer.export_angles_csv(angles_df, output_path)
    
    return angles_df
