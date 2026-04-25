"""
Pose estimation adapter for MVP pipeline.

Wraps MediaPipePoseDetector with config-driven initialization and
provides coordinate normalization, shooting-side detection, and persistence.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, Iterable, List, Optional, Tuple

from backend.inference.pose_2d import MediaPipePoseDetector, BASKETBALL_KEYPOINTS


# Minimum mean landmark visibility for a frame to be kept. Low-visibility frames
# are dropped rather than filled with zeros so downstream averaging stays honest.
MIN_MEAN_VISIBILITY = 0.40


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
        Process pre-buffered frames to extract pose landmarks.

        Prefer :meth:`process_frame_stream` in the new streaming pipeline to
        avoid holding the whole clip in memory. This path is kept for
        backward-compatible callers.

        Args:
            frames: List of RGB frames
            frame_mapping: DataFrame with frame indices and timestamps

        Returns:
            List of pose results per frame (low-visibility frames dropped).
        """
        iterator = (
            (
                int(row["processed_idx"]),
                int(row["original_idx"]),
                float(row["timestamp"]),
                frames[int(row["processed_idx"])],
            )
            for _, row in frame_mapping.iterrows()
            if int(row["processed_idx"]) < len(frames)
        )
        return self.process_frame_stream(iterator)

    def process_frame_stream(
        self,
        frame_iter: Iterable[Tuple[int, int, float, np.ndarray]],
    ) -> List[Dict[str, Any]]:
        """
        Consume a ``(processed_idx, original_idx, timestamp_s, frame_rgb)`` iterator.

        Builds ``self.pose_results`` incrementally. Frames whose mean landmark
        visibility is below :data:`MIN_MEAN_VISIBILITY` are dropped entirely
        rather than padded with zeros — this keeps aggregate stats honest and
        cuts memory usage dramatically on low-quality clips.
        """
        self.pose_results = []

        for processed_idx, original_idx, timestamp, frame in frame_iter:
            result = self.detector.process_frame(frame, input_is_rgb=True)
            if result is None:
                continue
            confidence = result["confidence"]
            try:
                mean_conf = float(np.mean(confidence))
            except Exception:
                mean_conf = 0.0
            if mean_conf < MIN_MEAN_VISIBILITY:
                continue
            self.pose_results.append(
                {
                    "frame_idx": int(original_idx),
                    "processed_idx": int(processed_idx),
                    "timestamp": float(timestamp),
                    "landmarks": result["landmarks"],
                    "confidence": confidence,
                }
            )

        # Apply multi-frame confidence calibration now that the full frame
        # list is available.  This penalises joints whose x-position has high
        # variance over a local window, reducing noise from flicker artefacts.
        self.apply_multiframe_calibration()

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
    
    def apply_multiframe_calibration(
        self,
        joints: List[str] = None,
        window: int = 5,
    ) -> None:
        """
        Apply multi-frame confidence calibration to self.pose_results in-place.

        For each joint in *joints*, penalises confidence for frames where the
        joint's x-position has high variance across the surrounding window.

        Note:
            This method is called automatically at the end of
            :meth:`process_frame_stream`.  If ``pose_results`` is populated by
            any other means (e.g. direct assignment in tests or alternative
            ingestion paths), callers must invoke this method explicitly to
            apply calibration before reading confidence values.

        Args:
            joints: Joint names (keys in BASKETBALL_KEYPOINTS) to calibrate.
                    Defaults to the eight primary shooting joints.
            window: Window size passed to calibrate_confidence_multiframe.
        """
        if joints is None:
            joints = [
                "right_elbow", "left_elbow",
                "right_knee", "left_knee",
                "right_wrist", "left_wrist",
                "right_shoulder", "left_shoulder",
            ]

        for joint_name in joints:
            joint_idx = BASKETBALL_KEYPOINTS.get(joint_name)
            if joint_idx is None:
                continue  # Unknown joint — skip gracefully

            # Build the per-frame dicts expected by calibrate_confidence_multiframe
            frame_dicts = []
            for result in self.pose_results:
                landmarks = result["landmarks"]
                confidence = result["confidence"]
                if joint_idx < len(landmarks) and joint_idx < len(confidence):
                    x, y, z = landmarks[joint_idx]
                    frame_dicts.append(
                        {joint_name: {"x": float(x), "y": float(y), "z": float(z),
                                      "conf": float(confidence[joint_idx])}}
                    )
                else:
                    frame_dicts.append({})  # Missing joint — pass through

            calibrated = calibrate_confidence_multiframe(frame_dicts, joint=joint_name, window=window)

            # Write adjusted confidences back into pose_results
            for result, cal_frame in zip(self.pose_results, calibrated):
                joint_data = cal_frame.get(joint_name)
                if joint_data is None:
                    continue
                # confidence may be a list or numpy array; normalise to list
                conf_list = list(result["confidence"])
                conf_list[joint_idx] = joint_data["conf"]
                result["confidence"] = conf_list

    def close(self):
        """Release MediaPipe resources."""
        self.detector.close()


# ---------------------------------------------------------------------------
# Standalone multi-frame confidence calibration
# ---------------------------------------------------------------------------

def calibrate_confidence_multiframe(
    frames: list,
    joint: str,
    window: int = 5,
) -> list:
    """
    Penalize confidence for joints with high positional variance in a local window.

    For each frame i, compute std of the joint's x-position over frames
    [i-half, i+half].  Adjusted confidence::

        adj_conf = original_conf * exp(-10 * local_std)

    Args:
        frames: List of per-frame dicts, each containing joint data like
                ``{joint_name: {"x": float, "y": float, "conf": float}, ...}``.
        joint:  The joint key to calibrate (e.g. ``"right_elbow"``).
        window: Number of surrounding frames for std computation (default 5).

    Returns:
        New list of frame dicts with adjusted confidence for the specified
        joint.  Frames missing the joint key are returned unchanged.
    """
    if not frames:
        return frames

    positions = np.array([f.get(joint, {}).get("x", np.nan) for f in frames], dtype=float)
    half = window // 2
    calibrated = []
    for i, frame in enumerate(frames):
        lo, hi = max(0, i - half), min(len(frames), i + half + 1)
        local_std = float(np.nanstd(positions[lo:hi]))
        if np.isnan(local_std):  # entire window is missing frames → no penalty
            local_std = 0.0
        joint_data = frame.get(joint)
        if joint_data is None:
            calibrated.append(frame)
            continue
        original_conf = float(joint_data.get("conf", 0.0))
        adj_conf = original_conf * float(np.exp(-10.0 * local_std))
        new_joint = {**joint_data, "conf": max(0.0, adj_conf)}
        calibrated.append({**frame, joint: new_joint})
    return calibrated
