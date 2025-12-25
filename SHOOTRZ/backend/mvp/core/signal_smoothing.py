"""
Signal cleaning and smoothing for pose keypoints.

Handles missing data interpolation and applies Savitzky-Golay filter
for stable trajectories suitable for kinematic analysis.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from scipy.signal import savgol_filter
from scipy.interpolate import interp1d


class SignalSmoother:
    """Handles missing data and smoothing for pose keypoints."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize signal smoother.
        
        Args:
            config: Smoothing config from MVPConfig
        """
        self.config = config
        self.window_length = config.get("window_length", 5)
        self.polyorder = config.get("polyorder", 2)
        self.max_gap_frames = config.get("max_gap_frames", 10)
        self.confidence_threshold = config.get("confidence_threshold", 0.3)
    
    def smooth_keypoints(
        self,
        pose_keypoints_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Clean and smooth pose keypoints.
        
        Args:
            pose_keypoints_df: Raw pose keypoints DataFrame
        
        Returns:
            DataFrame with smoothed coordinates and interpolation flags
        """
        # Group by joint
        smoothed_rows = []
        
        for joint in pose_keypoints_df["joint"].unique():
            joint_df = pose_keypoints_df[pose_keypoints_df["joint"] == joint].copy()
            joint_df = joint_df.sort_values("frame_id")
            
            # Handle missing data and smooth
            joint_smoothed = self._process_joint_timeseries(joint_df)
            smoothed_rows.append(joint_smoothed)
        
        # Concatenate all joints
        result_df = pd.concat(smoothed_rows, ignore_index=True)
        return result_df.sort_values(["frame_id", "joint"])
    
    def _process_joint_timeseries(self, joint_df: pd.DataFrame) -> pd.DataFrame:
        """
        Process timeseries for a single joint.
        
        Args:
            joint_df: DataFrame for single joint
        
        Returns:
            Smoothed DataFrame with interpolation flags
        """
        joint_df = joint_df.copy()
        
        # Mark low-confidence points as missing
        joint_df["is_missing"] = joint_df["confidence"] < self.confidence_threshold
        
        # Interpolate missing data
        joint_df = self._interpolate_missing(joint_df)
        
        # Apply Savitzky-Golay filter
        joint_df = self._apply_savgol(joint_df)
        
        return joint_df
    
    def _interpolate_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Interpolate missing data for gaps smaller than max_gap_frames.
        
        Args:
            df: Joint dataframe
        
        Returns:
            DataFrame with interpolated values
        """
        df = df.copy()
        df["interpolated"] = False
        
        # Find gaps
        missing_indices = df[df["is_missing"]].index.tolist()
        
        if not missing_indices:
            return df
        
        # Group consecutive missing indices into gaps
        gaps = []
        current_gap = [missing_indices[0]]
        
        for idx in missing_indices[1:]:
            if idx == current_gap[-1] + 1:
                current_gap.append(idx)
            else:
                gaps.append(current_gap)
                current_gap = [idx]
        gaps.append(current_gap)
        
        # Interpolate small gaps
        for gap in gaps:
            gap_size = len(gap)
            
            if gap_size <= self.max_gap_frames:
                # Get valid points before and after gap
                start_idx = gap[0] - 1
                end_idx = gap[-1] + 1
                
                if start_idx >= 0 and end_idx < len(df):
                    # Linear interpolation
                    for coord in ["x_norm", "y_norm", "z_norm", "x_px", "y_px"]:
                        start_val = df.loc[start_idx, coord]
                        end_val = df.loc[end_idx, coord]
                        
                        interpolated_vals = np.linspace(
                            start_val,
                            end_val,
                            gap_size + 2
                        )[1:-1]
                        
                        df.loc[gap, coord] = interpolated_vals
                    
                    df.loc[gap, "interpolated"] = True
                    df.loc[gap, "is_missing"] = False
        
        return df
    
    def _apply_savgol(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply Savitzky-Golay filter to smooth coordinates.
        
        Args:
            df: Joint dataframe
        
        Returns:
            DataFrame with smoothed coordinates
        """
        df = df.copy()
        
        # Need enough points for filter
        if len(df) < self.window_length:
            # Too few points, just copy raw values
            for coord in ["x_norm", "y_norm", "z_norm", "x_px", "y_px"]:
                df[f"{coord}_smooth"] = df[coord]
            return df
        
        # Apply filter only to non-missing segments
        for coord in ["x_norm", "y_norm", "z_norm", "x_px", "y_px"]:
            values = df[coord].values
            
            # Only smooth if we have valid data
            valid_mask = ~df["is_missing"].values
            
            if np.sum(valid_mask) >= self.window_length:
                try:
                    smoothed = savgol_filter(
                        values,
                        window_length=self.window_length,
                        polyorder=self.polyorder,
                        mode='nearest'
                    )
                    df[f"{coord}_smooth"] = smoothed
                except (ValueError, np.linalg.LinAlgError):
                    # Filter failed, use raw values
                    df[f"{coord}_smooth"] = values
            else:
                # Not enough valid data, use raw values
                df[f"{coord}_smooth"] = values
        
        return df
    
    def export_smoothed_csv(self, smoothed_df: pd.DataFrame, output_path: Path):
        """
        Export smoothed keypoints to CSV.
        
        Args:
            smoothed_df: Smoothed DataFrame
            output_path: Path to save CSV
        """
        # Reorder columns for clarity
        columns = [
            "run_id", "frame_id", "timestamp", "joint",
            "x_norm", "y_norm", "z_norm",
            "x_norm_smooth", "y_norm_smooth", "z_norm_smooth",
            "x_px", "y_px",
            "x_px_smooth", "y_px_smooth",
            "confidence", "interpolated", "is_missing"
        ]
        
        # Only include columns that exist
        available_columns = [col for col in columns if col in smoothed_df.columns]
        
        smoothed_df[available_columns].to_csv(output_path, index=False)


def smooth_pose_keypoints(
    pose_keypoints_csv: Path,
    config: Dict[str, Any],
    output_path: Path
) -> pd.DataFrame:
    """
    Convenience function to smooth pose keypoints.
    
    Args:
        pose_keypoints_csv: Path to raw pose keypoints CSV
        config: Smoothing config
        output_path: Path to save smoothed CSV
    
    Returns:
        Smoothed DataFrame
    """
    # Load raw keypoints
    df = pd.read_csv(pose_keypoints_csv)
    
    # Create smoother and process
    smoother = SignalSmoother(config)
    smoothed_df = smoother.smooth_keypoints(df)
    
    # Save
    smoother.export_smoothed_csv(smoothed_df, output_path)
    
    return smoothed_df
