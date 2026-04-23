"""
Main MVP pipeline orchestrator.

Coordinates all processing steps from video ingestion to final report.
"""

import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import os
import sys
import shutil
import json
import time
from contextlib import contextmanager


logger = logging.getLogger(__name__)

import cv2
import numpy as np
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


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _try_ball_tracking(video_path: str) -> Optional[Dict[str, Any]]:
    """Run the optional YOLO ball tracker, swallowing any failure."""
    try:
        from backend.inference.ball_tracker import detect_and_track_ball

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            return None
        frames_rgb: List[np.ndarray] = []
        total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
        stride = max(1, total // 60) if total > 0 else 1
        try:
            i = 0
            while len(frames_rgb) < 60:
                ok, frame_bgr = cap.read()
                if not ok:
                    break
                if i % stride == 0:
                    frames_rgb.append(cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB))
                i += 1
        finally:
            cap.release()
        if not frames_rgb:
            return None
        return detect_and_track_ball(frames_rgb)
    except Exception as exc:
        print(f"Ball tracking unavailable: {exc}")
        return None


def _release_angle_from_trajectory(
    trajectory: Optional[List[Dict[str, Any]]],
) -> Optional[Dict[str, Any]]:
    """Derive a single ``release_angle`` metric from the first 3 trajectory points."""
    if not trajectory or len(trajectory) < 3:
        return None
    try:
        from backend.metrics.biomechanics import compute_release_angle

        points = []
        confs = []
        for det in trajectory[:3]:
            center = det.get("center") if isinstance(det, dict) else None
            if not center or len(center) < 2:
                return None
            points.append([float(center[0]), float(center[1]), float(center[2]) if len(center) >= 3 else 0.0])
            confs.append(float(det.get("confidence", 0.5) if isinstance(det, dict) else 0.5))
        result = compute_release_angle(np.asarray(points, dtype=float))
        confidence = float(min(confs)) * float(result.get("confidence", 1.0))
        return {
            "name": "release_angle",
            "value": float(result.get("angle_degrees", 0.0)),
            "unit": "degrees",
            "verdict": "Good" if 45.0 <= float(result.get("angle_degrees", 0.0)) <= 70.0 else "Needs Work",
            "explanation": "Ball release angle estimated from YOLO trajectory.",
            "confidence": max(0.0, min(1.0, confidence)),
            "frame_range": [0, 0],
        }
    except Exception as exc:
        print(f"Release-angle metric skipped: {exc}")
        return None


@contextmanager
def _timed(store: Dict[str, float], phase: str, mem_sampler=None):
    t0 = time.perf_counter()
    try:
        yield
    finally:
        store[phase] = round(time.perf_counter() - t0, 4)
        if mem_sampler:
            store.setdefault("_mem_samples", []).append(float(mem_sampler()))


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
        run_id: Optional[str] = None,
        peak_memory_sampler=None,
        save_overlay: Optional[bool] = None,
        outputs_base_dir: Optional[Path] = None,
    ) -> Dict[str, Any]:
        """
        Process video through complete pipeline.

        Args:
            video_path: Path to video file
            shooting_side: "auto", "left", or "right"
            run_id: Optional existing run_id (for reprocessing)
            peak_memory_sampler: Optional callable returning current RSS in MB.
            save_overlay: When True the pipeline snapshots the first sampled
                RGB frame into the run dir so the overlay builder can run
                without re-decoding the clip. Defaults to the config value
                (``output.save_overlay_video``) ORed with the
                ``SHOOTRZ_SAVE_OVERLAY`` env flag.

            outputs_base_dir: If set, write run artifacts under this directory
                (useful for benchmarks so ``backend/outputs/`` is not mixed
                with unrelated runs).

        Returns:
            Complete results dict including pre-computed ``phases`` so the
            caller never needs to re-run :class:`PhaseDetector`.
        """
        phase_timings: Dict[str, float] = {}
        total_start = time.perf_counter()

        if save_overlay is None:
            save_overlay = bool(self.config.get("output.save_overlay_video", False)) or _env_flag(
                "SHOOTRZ_SAVE_OVERLAY", False
            )

        # Create or restore run
        out_base = Path(outputs_base_dir) if outputs_base_dir is not None else None
        if run_id is None:
            self.run_tracker = create_run_tracker(out_base)
            run_id = self.run_tracker.run_id
        else:
            # Use existing run_id (for reprocessing)
            from mvp.core.run_tracker import RunTracker
            self.run_tracker = RunTracker(out_base)
            self.run_tracker.run_id = run_id
            self.run_tracker.run_dir = self.run_tracker.outputs_base_dir / run_id
            self.run_tracker.run_dir.mkdir(parents=True, exist_ok=True)

        # Save config snapshot
        self.config.save_snapshot(self.run_tracker.get_run_dir())

        # Only copy the source video when overlay generation is requested — the
        # copy on a 50MB clip dominates cold-start latency otherwise.
        if save_overlay:
            try:
                input_video_path = self.run_tracker.get_output_path("input_video.mp4")
                shutil.copy2(video_path, input_video_path)
                self.run_tracker.add_metadata("input_video", str(input_video_path))
            except Exception:
                pass

        # PHASE 1+2 fused: stream-decode frames and run pose in a single pass
        # so we never hold the whole clip in RAM.
        with _timed(phase_timings, "ingestion", peak_memory_sampler):
            video_loader = VideoLoader(video_path, self.config.get("video", {}))
            video_metadata = video_loader.load_metadata()

        self.run_tracker.add_metadata("video_path", video_path)
        self.run_tracker.add_metadata("video_metadata", video_metadata)
        self.run_tracker.add_metadata("quality_warnings", video_loader.quality_warnings)

        pose_estimator = MVPPoseEstimator(
            self.config.get("pose_detection", {}),
            video_metadata,
        )

        first_rgb_frame: Optional[np.ndarray] = None
        low_light = False
        low_light_threshold = float(self.config.get("video.low_light_threshold", 50.0))

        def _instrumented_iter():
            nonlocal first_rgb_frame, low_light
            frame_iter = video_loader.iter_frames()
            for processed_idx, original_idx, timestamp, frame_rgb in frame_iter:
                if first_rgb_frame is None:
                    first_rgb_frame = frame_rgb
                    try:
                        luminance = float(
                            np.mean(cv2.cvtColor(frame_rgb, cv2.COLOR_RGB2GRAY))
                        )
                        low_light = luminance < low_light_threshold
                    except Exception:
                        low_light = False
                yield processed_idx, original_idx, timestamp, frame_rgb

        with _timed(phase_timings, "pose_estimation", peak_memory_sampler):
            pose_results = pose_estimator.process_frame_stream(_instrumented_iter())
            detected_side = pose_estimator.determine_shooting_side(shooting_side)

            # Persist artefacts AFTER the stream so frame_mapping is built.
            video_loader.save_metadata(self.run_tracker.get_output_path("video_metadata.json"))
            video_loader.save_frame_mapping(self.run_tracker.get_output_path("frame_mapping.csv"))

            pose_estimator.export_pose_keypoints_csv(
                self.run_tracker.get_output_path("pose_keypoints.csv"),
                run_id,
            )
            pose_estimator.export_pose_keypoints_json(
                self.run_tracker.get_output_path("pose_keypoints.json")
            )
            pose_estimator.export_confidence_summary(
                self.run_tracker.get_output_path("confidence_summary.json")
            )
            confidence_summary = pose_estimator.compute_confidence_summary()

        if save_overlay and first_rgb_frame is not None:
            try:
                preview_path = self.run_tracker.get_output_path("first_frame.png")
                cv2.imwrite(str(preview_path), cv2.cvtColor(first_rgb_frame, cv2.COLOR_RGB2BGR))
            except Exception:
                pass

        if low_light and "low_light" not in video_loader.quality_warnings:
            video_loader.quality_warnings.append("low_light")

        self.run_tracker.add_metadata("shooting_side", detected_side)
        self.run_tracker.add_metadata("pose_frames_detected", len(pose_results))
        self.run_tracker.add_metadata("low_light", low_light)

        pose_estimator.close()

        # Pose quality guardrails. There are two failure modes the original
        # implementation silently ate:
        #   (1) too few frames with visible landmarks (low light, occlusion, the
        #       user filmed their ceiling, etc.)
        #   (2) every frame landed on the (0.5, 0.5, conf=0.5) placeholder
        #       emitted by the MediaPipe fallback when it cannot initialise. The
        #       fallback path is now gated by ``SHOOTRZ_POSE_FALLBACK`` but we
        #       defensively detect "all keypoints identical" anyway so a future
        #       regression cannot ship a bogus 0/100 score to the client.
        pose_placeholder = False
        if len(pose_results) >= 5:
            try:
                stacked = np.stack(
                    [np.asarray(r["landmarks"], dtype=np.float32) for r in pose_results]
                )
                xy = stacked[..., :2]
                per_joint_std = xy.reshape(xy.shape[0], -1).std(axis=0)
                if float(np.max(per_joint_std)) < 1e-3:
                    pose_placeholder = True
            except Exception:
                pose_placeholder = False

        if len(pose_results) < 5 or pose_placeholder:
            status = "completed_low_quality"
            quality_warnings = list(video_loader.quality_warnings)
            marker = (
                "pose_placeholder_keypoints"
                if pose_placeholder
                else "insufficient_pose_frames"
            )
            if marker not in quality_warnings:
                quality_warnings.append(marker)
            self.run_tracker.add_metadata("status", status)
            self.run_tracker.add_metadata("phase_timings_seconds", phase_timings)
            self.run_tracker.add_metadata(
                "processing_time_seconds",
                round(time.perf_counter() - total_start, 4),
            )
            self.run_tracker.save_metadata()
            return {
                "run_id": run_id,
                "status": status,
                "processing_time_seconds": self.run_tracker.metadata.get("processing_time_seconds"),
                "overall_score": 0,
                "feedback_summary": (
                    "Could not see the shooter clearly enough to analyse. "
                    "Re-record with better lighting and a full-body side view."
                    if not pose_placeholder
                    else (
                        "Pose detection is unavailable on this server "
                        "(MediaPipe failed to initialise). Contact support or "
                        "check the backend logs."
                    )
                ),
                "feedback_bullets": [],
                "score_components": [],
                "metrics": [],
                "phases": [],
                "shot_window": {},
                "events": {},
                "shooting_side": detected_side,
                "video_metadata": video_metadata,
                "quality_warnings": quality_warnings,
                "output_dir": str(self.run_tracker.get_run_dir()),
                "diagnostics": {
                    "event_method": None,
                    "event_confidence_score": 0.0,
                    "event_warnings": quality_warnings,
                    "score_component_summary": [],
                },
                "phase_timings_seconds": {
                    k: v for k, v in phase_timings.items() if k != "_mem_samples"
                },
                "peak_memory_mb": None,
                "pose_overall_confidence": confidence_summary.get("overall"),
                "low_light": low_light,
            }

        # PHASE 3: Signal Smoothing
        with _timed(phase_timings, "smoothing", peak_memory_sampler):
            smoother = SignalSmoother(self.config.get("smoothing", {}))
            pose_df = pd.read_csv(self.run_tracker.get_output_path("pose_keypoints.csv"))
            smoothed_df = smoother.smooth_keypoints(pose_df)
            smoother.export_smoothed_csv(
                smoothed_df,
                self.run_tracker.get_output_path("pose_keypoints_smoothed.csv")
            )

        # Helper: run angles + shot-detection + metrics for a given side.
        # Used for the initial pass and (optionally) a retry on the opposite
        # side when auto-detection misclassifies. Artefacts are only written
        # to disk for the FINAL winning side to avoid leaving stale CSVs.
        def _run_side(
            side: str,
            *,
            persist: bool,
        ) -> Tuple["pd.DataFrame", Dict[str, Any], List[Dict[str, Any]]]:
            ac = AngleComputer(
                side, self.config.get("pose_detection.confidence_threshold", 0.3)
            )
            df_out = ac.compute_angles_per_frame(smoothed_df)
            if persist:
                ac.export_angles_csv(df_out, self.run_tracker.get_output_path("angles.csv"))
            sd = ShotDetector(self.config.get("shot_detection", {}))
            sw = sd.detect_shot_window(
                df_out, smoothed_df, side, output_dir=self.run_tracker.get_run_dir()
            )
            if persist:
                sd.export_shot_window_json(sw, self.run_tracker.get_output_path("shot_window.json"))
            md = MetricsDerivation({
                "metrics": self.config.get("metrics", {}),
                "scoring": self.config.get("scoring", {}),
            })
            ms = md.derive_metrics(df_out, sw)
            return df_out, sw, ms

        # PHASE 4+5 (and a first metrics pass for side evaluation)
        with _timed(phase_timings, "angle_computation", peak_memory_sampler):
            angles_df, shot_window, preview_metrics = _run_side(detected_side, persist=True)

        # Auto-side retry: when the user asked for "auto" AND pose quality is
        # comfortably high AND none of the primitive metrics cleared the
        # confidence gate, the shot-detector almost certainly landed on the
        # wrong arm. Try the opposite side and keep whichever produced more
        # high-confidence primitives.
        md_preview = MetricsDerivation({
            "metrics": self.config.get("metrics", {}),
            "scoring": self.config.get("scoring", {}),
        })
        pose_overall_conf = float(confidence_summary.get("overall") or 0.0)
        auto_was_requested = shooting_side == "auto"
        all_low = md_preview.all_primitives_low_confidence(preview_metrics)

        if auto_was_requested and all_low and pose_overall_conf > 0.6:
            other_side = "left" if detected_side == "right" else "right"
            try:
                alt_df, alt_sw, alt_metrics = _run_side(other_side, persist=False)
                alt_low = md_preview.all_primitives_low_confidence(alt_metrics)
                if not alt_low:
                    logger.info(
                        "auto-side retry: flipped %s -> %s (original side had all low-confidence metrics)",
                        detected_side,
                        other_side,
                    )
                    # Commit the flipped side's artefacts to disk and adopt them.
                    detected_side = other_side
                    angles_df = alt_df
                    shot_window = alt_sw
                    pose_estimator.shooting_side = other_side
                    AngleComputer(
                        other_side,
                        self.config.get("pose_detection.confidence_threshold", 0.3),
                    ).export_angles_csv(
                        alt_df, self.run_tracker.get_output_path("angles.csv")
                    )
                    ShotDetector(self.config.get("shot_detection", {})).export_shot_window_json(
                        alt_sw, self.run_tracker.get_output_path("shot_window.json")
                    )
                    video_loader.quality_warnings.append("auto_side_retry_flipped")
            except Exception as retry_err:
                logger.warning(
                    "auto-side retry failed on opposite side: %s", retry_err, exc_info=True
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
        
        # PHASE 5b: Motion-based phase detection (pre-computed ONCE so the job
        # service never needs to re-open pose_keypoints.json + re-run this.)
        phases_payload: List[Dict[str, Any]] = []
        with _timed(phase_timings, "phase_detection", peak_memory_sampler):
            try:
                from backend.inference.phase_detector import PhaseDetector
                fps_hint = float(video_metadata.get("fps") or 30.0)
                phase_detector = PhaseDetector(fps=fps_hint, shooting_side=detected_side)
                raw_phases = phase_detector.detect_phases(pose_results)
                for phase in raw_phases or []:
                    start_idx = int(phase.get("start_frame", 0))
                    end_idx = int(phase.get("end_frame", start_idx))
                    start_idx = max(0, min(start_idx, len(pose_results) - 1))
                    end_idx = max(0, min(end_idx, len(pose_results) - 1))
                    mapped = dict(phase)
                    mapped["start_frame"] = int(pose_results[start_idx]["frame_idx"])
                    mapped["end_frame"] = int(pose_results[end_idx]["frame_idx"])
                    peak_idx = phase.get("peak_frame")
                    if isinstance(peak_idx, int) and pose_results:
                        peak_idx = max(0, min(peak_idx, len(pose_results) - 1))
                        mapped["peak_frame"] = int(pose_results[peak_idx]["frame_idx"])
                    phase_obj = mapped.get("phase")
                    if phase_obj is not None and not isinstance(phase_obj, str):
                        try:
                            mapped["phase"] = (
                                phase_obj.value if hasattr(phase_obj, "value")
                                else str(phase_obj).lower().split(".")[-1]
                            )
                        except Exception:
                            mapped["phase"] = str(phase_obj)
                    phases_payload.append(mapped)
            except Exception as phase_err:
                print(f"Phase detection skipped: {phase_err}")

        # Optional ball tracking (env-gated; failures swallowed).
        ball_trajectory: Optional[List[Dict[str, Any]]] = None
        ball_release_metric: Optional[Dict[str, Any]] = None
        if _env_flag("SHOOTRZ_ENABLE_BALL", False):
            ball_result = _try_ball_tracking(video_path)
            if ball_result:
                ball_trajectory = ball_result.get("trajectory")
                ball_release_metric = _release_angle_from_trajectory(ball_trajectory)

        # PHASE 6: Metrics Derivation
        with _timed(phase_timings, "metrics_scoring", peak_memory_sampler):
            metrics_derivation = MetricsDerivation({
                "metrics": self.config.get("metrics", {}),
                "scoring": self.config.get("scoring", {})
            })
            metrics = metrics_derivation.derive_metrics(angles_df, shot_window)
            if ball_release_metric is not None:
                metrics.append(ball_release_metric)
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
            all_low_conf = metrics_derivation.all_primitives_low_confidence(metrics)

        self.run_tracker.add_metadata("overall_score", overall_score)
        self.run_tracker.add_metadata("metrics_count", len(metrics))
        self.run_tracker.add_metadata("phase_timings_seconds", phase_timings)
        self.run_tracker.add_metadata("processing_time_seconds", round(time.perf_counter() - total_start, 4))
        self.run_tracker.add_metadata("pose_overall_confidence", confidence_summary.get("overall"))
        mem_samples = phase_timings.get("_mem_samples", [])
        self.run_tracker.add_metadata("peak_memory_mb", round(max(mem_samples), 1) if mem_samples else None)
        
        # Save final metadata
        self.run_tracker.save_metadata()
        
        # If every primitive metric fell below the confidence gate, there is
        # no honest signal left to score. Flip status so the client shows the
        # "re-record" banner instead of a fabricated number.
        final_status = "completed"
        quality_warnings_out = list(video_loader.quality_warnings)
        final_feedback_summary = feedback_summary
        if all_low_conf:
            final_status = "completed_low_quality"
            if "insufficient_metric_confidence" not in quality_warnings_out:
                quality_warnings_out.append("insufficient_metric_confidence")
            final_feedback_summary = (
                "We tracked your body but could not measure the key angles "
                "with enough confidence. Re-record side-on with good lighting "
                "and your full body in the frame."
            )

        # Return results
        return {
            "run_id": run_id,
            "status": final_status,
            "processing_time_seconds": self.run_tracker.metadata.get("processing_time_seconds"),
            "overall_score": overall_score,
            "feedback_summary": final_feedback_summary,
            "feedback_bullets": feedback_bullets,
            "score_components": score_components,
            "metrics": metrics,
            "phases": phases_payload,
            "shot_window": shot_window,
            "shooting_side": detected_side,
            "video_metadata": video_metadata,
            "quality_warnings": quality_warnings_out,
            "output_dir": str(self.run_tracker.get_run_dir()),
            "diagnostics": build_pipeline_diagnostics(shot_window, score_components),
            "phase_timings_seconds": {k: v for k, v in phase_timings.items() if k != "_mem_samples"},
            "peak_memory_mb": round(max(mem_samples), 1) if mem_samples else None,
            "pose_overall_confidence": confidence_summary.get("overall"),
            "low_light": low_light,
            "ball_trajectory_length": len(ball_trajectory) if ball_trajectory else 0,
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
