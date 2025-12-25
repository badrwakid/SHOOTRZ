"""
Main MVP pipeline orchestrator.

Coordinates all processing steps from video ingestion to final report.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.config_loader import load_config
from mvp.core.run_tracker import create_run_tracker
from mvp.core.video_loader import VideoLoader
from mvp.core.pose_estimation import MVPPoseEstimator
from mvp.core.signal_smoothing import SignalSmoother
from mvp.core.angle_computation import AngleComputer
from mvp.core.shot_detection import ShotDetector
from mvp.core.metrics import MetricsDerivation


class MVPPipeline:
    """Orchestrates complete MVP analysis pipeline."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize pipeline.
        
        Args:
            config_path: Optional path to config YAML
        """
        self.config = load_config(config_path)
        self.run_tracker = None
    
    def process_video(
        self,
        video_path: str,
        shooting_side: str = "auto",
        run_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process video through complete pipeline.
        
        Args:
            video_path: Path to video file
            shooting_side: "auto", "left", or "right"
            run_id: Optional existing run_id (for reprocessing)
        
        Returns:
            Complete results dict
        """
        # Create or restore run
        if run_id is None:
            self.run_tracker = create_run_tracker()
            run_id = self.run_tracker.run_id
        else:
            # Use existing run_id (for reprocessing)
            from mvp.core.run_tracker import RunTracker
            self.run_tracker = RunTracker()
            self.run_tracker.run_id = run_id
            self.run_tracker.run_dir = self.run_tracker.outputs_base_dir / run_id
            self.run_tracker.run_dir.mkdir(parents=True, exist_ok=True)
        
        # Save config snapshot
        self.config.save_snapshot(self.run_tracker.get_run_dir())
        
        # PHASE 1: Video Ingestion
        video_loader = VideoLoader(video_path, self.config.get("video", {}))
        video_metadata = video_loader.load_metadata()
        frames, frame_mapping = video_loader.load_frames()
        
        video_loader.save_metadata(self.run_tracker.get_output_path("video_metadata.json"))
        video_loader.save_frame_mapping(self.run_tracker.get_output_path("frame_mapping.csv"))
        
        self.run_tracker.add_metadata("video_path", video_path)
        self.run_tracker.add_metadata("video_metadata", video_metadata)
        self.run_tracker.add_metadata("quality_warnings", video_loader.quality_warnings)
        
        # PHASE 2: Pose Estimation
        pose_estimator = MVPPoseEstimator(
            self.config.get("pose_detection", {}),
            video_metadata
        )
        pose_results = pose_estimator.process_frames(frames, frame_mapping)
        detected_side = pose_estimator.determine_shooting_side(shooting_side)
        
        pose_estimator.export_pose_keypoints_csv(
            self.run_tracker.get_output_path("pose_keypoints.csv"),
            run_id
        )
        pose_estimator.export_pose_keypoints_json(
            self.run_tracker.get_output_path("pose_keypoints.json")
        )
        pose_estimator.export_confidence_summary(
            self.run_tracker.get_output_path("confidence_summary.json")
        )
        
        self.run_tracker.add_metadata("shooting_side", detected_side)
        self.run_tracker.add_metadata("pose_frames_detected", len(pose_results))
        
        pose_estimator.close()
        
        # PHASE 3: Signal Smoothing
        smoother = SignalSmoother(self.config.get("smoothing", {}))
        import pandas as pd
        pose_df = pd.read_csv(self.run_tracker.get_output_path("pose_keypoints.csv"))
        smoothed_df = smoother.smooth_keypoints(pose_df)
        smoother.export_smoothed_csv(
            smoothed_df,
            self.run_tracker.get_output_path("pose_keypoints_smoothed.csv")
        )
        
        # PHASE 4: Angle Computation
        angle_computer = AngleComputer(
            detected_side,
            self.config.get("pose_detection.confidence_threshold", 0.3)
        )
        angles_df = angle_computer.compute_angles_per_frame(smoothed_df)
        angle_computer.export_angles_csv(
            angles_df,
            self.run_tracker.get_output_path("angles.csv")
        )
        
        # PHASE 5: Shot Detection
        shot_detector = ShotDetector(self.config.get("shot_detection", {}))
        shot_window = shot_detector.detect_shot_window(angles_df, smoothed_df, detected_side)
        shot_detector.export_shot_window_json(
            shot_window,
            self.run_tracker.get_output_path("shot_window.json")
        )
        
        self.run_tracker.add_metadata("shot_window", shot_window)
        
        # PHASE 6: Metrics Derivation
        metrics_derivation = MetricsDerivation({
            "metrics": self.config.get("metrics", {}),
            "scoring": self.config.get("scoring", {})
        })
        metrics = metrics_derivation.derive_metrics(angles_df, shot_window)
        overall_score, feedback_summary = metrics_derivation.compute_overall_score(metrics)
        
        metrics_derivation.export_report_json(
            metrics,
            overall_score,
            feedback_summary,
            self.run_tracker.get_output_path("report.json")
        )
        
        self.run_tracker.add_metadata("overall_score", overall_score)
        self.run_tracker.add_metadata("metrics_count", len(metrics))
        
        # Save final metadata
        self.run_tracker.save_metadata()
        
        # Return results
        return {
            "run_id": run_id,
            "status": "completed",
            "overall_score": overall_score,
            "feedback_summary": feedback_summary,
            "metrics": metrics,
            "shot_window": shot_window,
            "shooting_side": detected_side,
            "video_metadata": video_metadata,
            "quality_warnings": video_loader.quality_warnings,
            "output_dir": str(self.run_tracker.get_run_dir()),
        }
