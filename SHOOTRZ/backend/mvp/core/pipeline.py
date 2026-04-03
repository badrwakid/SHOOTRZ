"""
Main MVP pipeline orchestrator.

Coordinates all processing steps from video ingestion to final report.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import sys
import shutil
import json

import pandas as pd

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

        # Save input video into run folder for reproducibility (and reliable overlay generation)
        try:
            input_video_path = self.run_tracker.get_output_path("input_video.mp4")
            shutil.copy2(video_path, input_video_path)
            self.run_tracker.add_metadata("input_video", str(input_video_path))
        except Exception:
            # Best-effort only; pipeline can still run without copying
            pass
        
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

        diag = shot_window.get("diagnostics") or {}
        with open(self.run_tracker.get_output_path("event_candidates.json"), "w") as ef:
            json.dump(diag.get("candidates", {}), ef, indent=2)
        warnings_list = list(diag.get("warnings", []))
        warnings_list.extend(
            quality_warnings_list(shot_window, angles_df, video_metadata)
        )
        with open(self.run_tracker.get_output_path("warnings.json"), "w") as wf:
            json.dump({"warnings": warnings_list}, wf, indent=2)

        with open(self.run_tracker.get_output_path("event_confidence.json"), "w") as cf:
            json.dump(shot_window.get("events") or {}, cf, indent=2)
        build_feature_table(
            angles_df,
            smoothed_df,
            self.run_tracker.get_output_path("feature_table.csv"),
        )
        export_smoothed_signals(
            smoothed_df,
            self.run_tracker.get_output_path("signals_smoothed.csv"),
        )

        self.run_tracker.add_metadata("shot_window", shot_window)
        
        # PHASE 6: Metrics Derivation
        metrics_derivation = MetricsDerivation({
            "metrics": self.config.get("metrics", {}),
            "scoring": self.config.get("scoring", {})
        })
        metrics = metrics_derivation.derive_metrics(angles_df, shot_window)
        overall_score, feedback_summary, feedback_bullets, score_components = (
            metrics_derivation.compute_overall_score(metrics, angles_df, shot_window)
        )
        
        metrics_derivation.export_report_json(
            metrics,
            overall_score,
            feedback_summary,
            self.run_tracker.get_output_path("report.json"),
            score_components=score_components,
            feedback_bullets=feedback_bullets,
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
            "feedback_bullets": feedback_bullets,
            "score_components": score_components,
            "metrics": metrics,
            "shot_window": shot_window,
            "shooting_side": detected_side,
            "video_metadata": video_metadata,
            "quality_warnings": video_loader.quality_warnings,
            "output_dir": str(self.run_tracker.get_run_dir()),
            "diagnostics": build_pipeline_diagnostics(shot_window, score_components),
        }


def quality_warnings_list(
    shot_window: Dict[str, Any],
    angles_df,
    video_metadata: Optional[Dict[str, Any]] = None,
) -> list:
    out = []
    sw = shot_window.get("confidence_score", 1.0) or 0.0
    if sw < 0.45:
        out.append("low_event_confidence")
    if angles_df is not None and len(angles_df) < 15:
        out.append("few_angle_frames")
    if video_metadata:
        fps = float(video_metadata.get("fps") or 0.0)
        if 0 < fps < 24:
            out.append("low_fps")
        if fps > 60:
            out.append("high_fps_unusual")
    seen = set()
    uniq = []
    for w in out:
        if w not in seen:
            uniq.append(w)
            seen.add(w)
    return uniq


def export_smoothed_signals(smoothed_df: pd.DataFrame, output_path: Path) -> None:
    cols = [
        "frame_id",
        "joint",
        "x_norm_smooth",
        "y_norm_smooth",
        "confidence",
        "interpolated",
    ]
    available = [c for c in cols if c in smoothed_df.columns]
    if not available:
        return
    smoothed_df[available].to_csv(output_path, index=False)


def build_feature_table(
    angles_df: pd.DataFrame,
    smoothed_df: pd.DataFrame,
    output_path: Path,
) -> None:
    rows: List[Dict[str, Any]] = []
    for _, row in angles_df.iterrows():
        rows.append(
            {
                "frame_id": int(row["frame_id"]),
                "timestamp": float(row["timestamp"]),
                "knee_angle": None
                if pd.isna(row["knee_angle"])
                else float(row["knee_angle"]),
                "elbow_angle": None
                if pd.isna(row["elbow_angle"])
                else float(row["elbow_angle"]),
                "wrist_angle": None
                if pd.isna(row["wrist_angle"])
                else float(row["wrist_angle"]),
                "confidence_knee": float(row.get("confidence_knee", 0.0)),
                "confidence_elbow": float(row.get("confidence_elbow", 0.0)),
                "confidence_wrist": float(row.get("confidence_wrist", 0.0)),
            }
        )
    feature_df = pd.DataFrame(rows)
    if "joint" in smoothed_df.columns and "y_norm_smooth" in smoothed_df.columns:
        hips = smoothed_df[smoothed_df["joint"].str.contains("_hip", na=False)][
            ["frame_id", "y_norm_smooth"]
        ].groupby("frame_id", as_index=False).mean().rename(
            columns={"y_norm_smooth": "hip_y_smooth"}
        )
        wrists = smoothed_df[smoothed_df["joint"].str.contains("_wrist", na=False)][
            ["frame_id", "y_norm_smooth"]
        ].groupby("frame_id", as_index=False).mean().rename(
            columns={"y_norm_smooth": "wrist_y_smooth"}
        )
        feature_df = feature_df.merge(hips, on="frame_id", how="left").merge(
            wrists, on="frame_id", how="left"
        )
    feature_df.to_csv(output_path, index=False)


def build_pipeline_diagnostics(
    shot_window: Dict[str, Any],
    score_components: list,
) -> Dict[str, Any]:
    """Compact diagnostics for API consumers."""
    diag = shot_window.get("diagnostics") or {}
    return {
        "event_method": shot_window.get("method"),
        "event_confidence_score": shot_window.get("confidence_score"),
        "event_warnings": diag.get("warnings", []),
        "score_component_summary": [
            {"name": c["name"], "value": c["value"], "weight": c["weight"]}
            for c in (score_components or [])
        ],
    }
