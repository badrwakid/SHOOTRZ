"""
Video ingestion and metadata extraction.

Loads videos using OpenCV, extracts metadata, and handles frame sampling.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterator
import json
import pandas as pd


# Target number of pose frames kept for the MVP pipeline. Stride is derived from
# the source clip length so we always land in this range regardless of duration.
DEFAULT_TARGET_FRAMES = 120

# MediaPipe Pose's BlazePose backbone hits diminishing accuracy returns above
# ~720p. Feeding 1080x1920 phone clips at full size just burns CPU on colour
# conversion and model inference without improving keypoint quality, so we
# downscale so the long side is this many pixels before pose runs.
MAX_POSE_INPUT_LONG_SIDE = 720


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
    
    def compute_stride(
        self,
        target_frames: int = DEFAULT_TARGET_FRAMES,
    ) -> int:
        """
        Compute stride so approximately ``target_frames`` are yielded regardless
        of source clip length.

        Respects ``frame_skip`` from config as a minimum stride (so the config
        can still force denser sampling on short clips if explicitly set).
        """
        if not self.metadata:
            self.load_metadata()
        total = int(self.metadata.get("frame_count") or 0)
        frame_skip = int(self.config.get("frame_skip", 1))
        if total <= 0:
            return max(1, frame_skip)
        derived = max(1, total // max(1, target_frames))
        return max(derived, frame_skip)

    def iter_frames(
        self,
        stride: Optional[int] = None,
        max_frames: Optional[int] = None,
        target_frames: int = DEFAULT_TARGET_FRAMES,
    ) -> Iterator[Tuple[int, int, float, np.ndarray]]:
        """
        Stream frames from the source video WITHOUT buffering the whole clip.

        Yields tuples of ``(processed_idx, original_idx, timestamp_s, frame_rgb)``.

        Args:
            stride: Keep every Nth frame. ``None`` triggers auto-stride.
            max_frames: Hard cap on yielded frames (None = use config or unlimited).
            target_frames: Auto-stride target when ``stride`` is None.

        Builds ``self.frame_mapping`` incrementally so callers can persist it
        after the generator is exhausted.

        Raises:
            ValueError: Video cannot be opened or yields zero frames.
        """
        if not self.metadata:
            self.load_metadata()

        effective_stride = int(stride) if stride and stride > 0 else self.compute_stride(target_frames)
        fps = float(self.metadata.get("fps") or 0.0) or 30.0
        cap_limit = int(max_frames) if max_frames else self.config.get("max_frames")
        if cap_limit is None:
            cap_limit = target_frames * 2

        cap = cv2.VideoCapture(str(self.video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {self.video_path}")

        mapping: List[Dict[str, Any]] = []
        raw_idx = 0
        processed_idx = 0

        try:
            while True:
                ok, frame_bgr = cap.read()
                if not ok:
                    break
                if raw_idx % effective_stride != 0:
                    raw_idx += 1
                    continue

                frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)

                # Downscale to ``MAX_POSE_INPUT_LONG_SIDE`` on the long axis.
                # On a 1080x1920 vertical clip this cuts pose inference by ~3x
                # without measurable accuracy loss (landmarks are normalised,
                # so downstream math is resolution-agnostic). Controlled by
                # ``video.max_pose_long_side`` (set to 0 to disable).
                target_long = int(
                    self.config.get("max_pose_long_side", MAX_POSE_INPUT_LONG_SIDE)
                    or 0
                )
                if target_long > 0:
                    h_in, w_in = frame_rgb.shape[:2]
                    long_side = max(h_in, w_in)
                    if long_side > target_long:
                        scale = target_long / float(long_side)
                        new_w = max(1, int(round(w_in * scale)))
                        new_h = max(1, int(round(h_in * scale)))
                        frame_rgb = cv2.resize(
                            frame_rgb, (new_w, new_h), interpolation=cv2.INTER_AREA
                        )

                timestamp = raw_idx / fps if fps > 0 else raw_idx * 0.033

                mapping.append(
                    {
                        "processed_idx": processed_idx,
                        "original_idx": raw_idx,
                        "timestamp": timestamp,
                    }
                )

                yield processed_idx, raw_idx, timestamp, frame_rgb

                processed_idx += 1
                raw_idx += 1
                if cap_limit is not None and processed_idx >= int(cap_limit):
                    break
        finally:
            cap.release()

        if processed_idx == 0:
            raise ValueError("No frames could be extracted from video")

        self.frame_mapping = mapping
        self.metadata.setdefault("frame_sampling", {}).update(
            {"stride": effective_stride, "max_frames": cap_limit, "kept_frames": processed_idx}
        )

    def iter_frame_mapping_df(self) -> pd.DataFrame:
        """Return a DataFrame view of the mapping built during ``iter_frames``."""
        if not self.frame_mapping:
            return pd.DataFrame(columns=["processed_idx", "original_idx", "timestamp"])
        return pd.DataFrame(self.frame_mapping)

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
        
        # BUG FIX: Truncate frame_mapping to match actual loaded frame count
        # CAP_PROP_FRAME_COUNT can over-report, causing IndexError in pose_estimation
        if len(frame_mapping_df) > len(frames):
            frame_mapping_df = frame_mapping_df.iloc[:len(frames)].reset_index(drop=True)
            self.frame_mapping = self.frame_mapping[:len(frames)]
        
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
