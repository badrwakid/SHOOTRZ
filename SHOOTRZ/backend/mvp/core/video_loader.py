"""
Video ingestion and metadata extraction.

Loads videos using OpenCV, extracts metadata, and handles frame sampling.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import pandas as pd


class VideoLoader:
    """Handles video loading, metadata extraction, and frame sampling."""
    
    def __init__(self, video_path: str, config: Dict[str, Any]):
        """
        Initialize video loader.
        
        Args:
            video_path: Path to video file
            config: Video config from MVPConfig (video section)
        """
        self.video_path = Path(video_path)
        if not self.video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        self.config = config
        self.metadata: Dict[str, Any] = {}
        self.frame_mapping: List[Dict[str, Any]] = []
        self.quality_warnings: List[str] = []
    
    def load_metadata(self) -> Dict[str, Any]:
        """
        Extract video metadata using OpenCV.
        
        Returns:
            Metadata dictionary with fps, frame_count, width, height, duration
        """
        cap = cv2.VideoCapture(str(self.video_path))
        
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {self.video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = frame_count / fps if fps > 0 else 0
        
        cap.release()
        
        self.metadata = {
            "video_path": str(self.video_path),
            "fps": fps,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "duration_seconds": duration,
            "resolution": f"{width}x{height}",
        }
        
        # Run quality checks
        self._check_quality()
        
        return self.metadata
    
    def _check_quality(self):
        """Run quality checks on video metadata."""
        min_duration = self.config.get("min_duration", 1.0)
        min_resolution = self.config.get("min_resolution", 480)
        
        # Check duration
        if self.metadata["duration_seconds"] < min_duration:
            self.quality_warnings.append(
                f"Video is very short ({self.metadata['duration_seconds']:.1f}s). "
                f"Minimum recommended: {min_duration}s"
            )
        
        # Check resolution
        if self.metadata["height"] < min_resolution:
            self.quality_warnings.append(
                f"Video resolution is low ({self.metadata['height']}p). "
                f"Minimum recommended: {min_resolution}p"
            )
        
        # Check FPS validity
        if self.metadata["fps"] <= 0 or self.metadata["fps"] > 240:
            self.quality_warnings.append(
                f"Unusual FPS detected: {self.metadata['fps']}. "
                "Timestamps may be inaccurate."
            )
    
    def create_frame_mapping(self) -> pd.DataFrame:
        """
        Create mapping of processed frames to original frames with timestamps.
        
        Returns:
            DataFrame with columns: processed_idx, original_idx, timestamp
        """
        frame_skip = self.config.get("frame_skip", 1)
        max_frames = self.config.get("max_frames")
        
        fps = self.metadata["fps"]
        frame_count = self.metadata["frame_count"]
        
        mapping = []
        processed_idx = 0
        
        for original_idx in range(0, frame_count, frame_skip):
            timestamp = original_idx / fps if fps > 0 else original_idx * 0.033
            
            mapping.append({
                "processed_idx": processed_idx,
                "original_idx": original_idx,
                "timestamp": timestamp,
            })
            
            processed_idx += 1
            
            if max_frames is not None and processed_idx >= max_frames:
                break
        
        self.frame_mapping = mapping
        return pd.DataFrame(mapping)
    
    def load_frames(self) -> Tuple[List[np.ndarray], pd.DataFrame]:
        """
        Load video frames according to frame_skip configuration.
        
        Returns:
            Tuple of (frames list, frame_mapping DataFrame)
        """
        frame_skip = self.config.get("frame_skip", 1)
        max_frames = self.config.get("max_frames")
        
        cap = cv2.VideoCapture(str(self.video_path))
        
        frames = []
        frame_idx = 0
        processed_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Skip frames if needed
            if frame_idx % frame_skip == 0:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(frame_rgb)
                processed_count += 1
            
            frame_idx += 1
            
            if max_frames is not None and processed_count >= max_frames:
                break
        
        cap.release()
        
        if len(frames) == 0:
            raise ValueError("No frames could be extracted from video")
        
        # Create frame mapping
        frame_mapping_df = self.create_frame_mapping()
        
        return frames, frame_mapping_df
    
    def save_metadata(self, output_path: Path):
        """
        Save metadata to JSON file.
        
        Args:
            output_path: Path to save metadata JSON
        """
        metadata_with_warnings = {
            **self.metadata,
            "quality_warnings": self.quality_warnings,
            "frame_sampling": {
                "frame_skip": self.config.get("frame_skip", 1),
                "max_frames": self.config.get("max_frames"),
                "total_processed_frames": len(self.frame_mapping),
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(metadata_with_warnings, f, indent=2)
    
    def save_frame_mapping(self, output_path: Path):
        """
        Save frame mapping to CSV.
        
        Args:
            output_path: Path to save frame mapping CSV
        """
        if not self.frame_mapping:
            self.create_frame_mapping()
        
        df = pd.DataFrame(self.frame_mapping)
        df.to_csv(output_path, index=False)


def load_video(
    video_path: str,
    config: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Tuple[List[np.ndarray], Dict[str, Any], pd.DataFrame]:
    """
    Convenience function to load video with metadata.
    
    Args:
        video_path: Path to video file
        config: Video config dict
        output_dir: Optional directory to save metadata/mapping
    
    Returns:
        Tuple of (frames, metadata, frame_mapping)
    """
    loader = VideoLoader(video_path, config)
    metadata = loader.load_metadata()
    frames, frame_mapping = loader.load_frames()
    
    if output_dir:
        loader.save_metadata(output_dir / "video_metadata.json")
        loader.save_frame_mapping(output_dir / "frame_mapping.csv")
    
    return frames, metadata, frame_mapping
