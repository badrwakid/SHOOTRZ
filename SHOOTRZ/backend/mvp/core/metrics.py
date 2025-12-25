"""
Metric derivation and scoring for MVP pipeline.

Extracts three core metrics:
1. Elbow extension at release
2. Knee bend depth
3. Wrist follow-through

Assigns verdicts and computes overall score.
"""

import numpy as np
import pandas as pd
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple


class MetricsDerivation:
    """Derives metrics from angles and shot window."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize metrics derivation.
        
        Args:
            config: Metrics and scoring config from MVPConfig
        """
        self.config = config
        self.metrics_config = config.get("metrics", {})
        self.scoring_config = config.get("scoring", {})
    
    def derive_metrics(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Derive three core metrics from angles.
        
        Args:
            angles_df: Angles DataFrame
            shot_window: Shot window with frame indices
        
        Returns:
            List of metric dicts
        """
        metrics = []
        
        # 1. Elbow extension at release
        elbow_metric = self._compute_elbow_extension(angles_df, shot_window)
        metrics.append(elbow_metric)
        
        # 2. Knee bend depth
        knee_metric = self._compute_knee_bend(angles_df, shot_window)
        metrics.append(knee_metric)
        
        # 3. Wrist follow-through
        wrist_metric = self._compute_wrist_followthrough(angles_df, shot_window)
        metrics.append(wrist_metric)
        
        return metrics
    
    def _compute_elbow_extension(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute elbow extension at release."""
        release_frame = shot_window["release_frame"]
        release_window = self.metrics_config.get("elbow_extension", {}).get("release_window", 3)
        
        # Get frames around release
        window_frames = angles_df[
            (angles_df["frame_id"] >= release_frame - release_window) &
            (angles_df["frame_id"] <= release_frame + release_window)
        ]
        
        if len(window_frames) == 0:
            return self._create_low_confidence_metric("elbow_extension")
        
        # Average elbow angle in window
        elbow_angles = window_frames["elbow_angle"].dropna()
        elbow_confidences = window_frames["confidence_elbow"].dropna()
        
        if len(elbow_angles) == 0:
            return self._create_low_confidence_metric("elbow_extension")
        
        value = float(np.mean(elbow_angles))
        confidence = float(np.mean(elbow_confidences))
        
        # Assign verdict
        good_range = self.metrics_config.get("elbow_extension", {}).get("good_range", [150, 175])
        optimal_range = self.metrics_config.get("elbow_extension", {}).get("optimal_range", [160, 170])
        verdict = self._assign_verdict(value, good_range, optimal_range, confidence)
        
        # Generate explanation
        explanation = self._generate_elbow_explanation(value, verdict)
        
        return {
            "name": "elbow_extension",
            "value": value,
            "unit": "degrees",
            "verdict": verdict,
            "explanation": explanation,
            "confidence": confidence,
            "frame_range": [
                int(release_frame - release_window),
                int(release_frame + release_window)
            ]
        }
    
    def _compute_knee_bend(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute knee bend depth at crouch."""
        crouch_frame = shot_window["crouch_frame"]
        
        # Get crouch frame data
        crouch_data = angles_df[angles_df["frame_id"] == crouch_frame]
        
        if len(crouch_data) == 0:
            return self._create_low_confidence_metric("knee_bend")
        
        value = float(crouch_data.iloc[0]["knee_angle"])
        confidence = float(crouch_data.iloc[0]["confidence_knee"])
        
        if np.isnan(value):
            return self._create_low_confidence_metric("knee_bend")
        
        # Assign verdict
        good_range = self.metrics_config.get("knee_bend", {}).get("good_range", [85, 120])
        optimal_range = self.metrics_config.get("knee_bend", {}).get("optimal_range", [95, 110])
        verdict = self._assign_verdict(value, good_range, optimal_range, confidence)
        
        # Generate explanation
        explanation = self._generate_knee_explanation(value, verdict)
        
        return {
            "name": "knee_bend",
            "value": value,
            "unit": "degrees",
            "verdict": verdict,
            "explanation": explanation,
            "confidence": confidence,
            "frame_range": [int(crouch_frame), int(crouch_frame)]
        }
    
    def _compute_wrist_followthrough(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compute wrist follow-through (angle change from release to end)."""
        release_frame = shot_window["release_frame"]
        end_frame = shot_window["end_frame"]
        
        # Get release and end data
        release_data = angles_df[angles_df["frame_id"] == release_frame]
        end_data = angles_df[angles_df["frame_id"] == end_frame]
        
        if len(release_data) == 0 or len(end_data) == 0:
            return self._create_low_confidence_metric("wrist_follow_through")
        
        release_angle = release_data.iloc[0]["wrist_angle"]
        end_angle = end_data.iloc[0]["wrist_angle"]
        
        if np.isnan(release_angle) or np.isnan(end_angle):
            return self._create_low_confidence_metric("wrist_follow_through")
        
        # Compute angle change
        value = float(abs(end_angle - release_angle))
        confidence = float(min(
            release_data.iloc[0]["confidence_wrist"],
            end_data.iloc[0]["confidence_wrist"]
        ))
        
        # Assign verdict
        good_range = self.metrics_config.get("wrist_follow_through", {}).get("good_range", [10, 30])
        optimal_range = self.metrics_config.get("wrist_follow_through", {}).get("optimal_range", [15, 25])
        verdict = self._assign_verdict(value, good_range, optimal_range, confidence)
        
        # Generate explanation
        explanation = self._generate_wrist_explanation(value, verdict)
        
        return {
            "name": "wrist_follow_through",
            "value": value,
            "unit": "degrees",
            "verdict": verdict,
            "explanation": explanation,
            "confidence": confidence,
            "frame_range": [int(release_frame), int(end_frame)]
        }
    
    def _assign_verdict(
        self,
        value: float,
        good_range: List[float],
        optimal_range: List[float],
        confidence: float
    ) -> str:
        """Assign verdict based on value and ranges."""
        low_conf_threshold = self.scoring_config.get("low_confidence_threshold", 0.4)
        
        if confidence < low_conf_threshold:
            return "Low Confidence"
        
        # Check if in optimal range
        if optimal_range[0] <= value <= optimal_range[1]:
            return "Good"
        
        # Check if in good range
        if good_range[0] <= value <= good_range[1]:
            return "Good"
        
        return "Needs Work"
    
    def _create_low_confidence_metric(self, name: str) -> Dict[str, Any]:
        """Create a low-confidence metric placeholder."""
        return {
            "name": name,
            "value": 0.0,
            "unit": "N/A",
            "verdict": "Low Confidence",
            "explanation": "Insufficient data to compute this metric reliably.",
            "confidence": 0.0,
            "frame_range": [0, 0]
        }
    
    def _generate_elbow_explanation(self, value: float, verdict: str) -> str:
        """Generate explanation for elbow metric."""
        if verdict == "Good":
            return f"Elbow at {value:.1f}° provides optimal power transfer and release mechanics."
        elif verdict == "Needs Work":
            if value < 150:
                return f"Elbow at {value:.1f}° is too bent. Extend more for better power and arc."
            else:
                return f"Elbow at {value:.1f}° is over-extended. Maintain slight flexion for control."
        else:
            return "Insufficient data to evaluate elbow extension."
    
    def _generate_knee_explanation(self, value: float, verdict: str) -> str:
        """Generate explanation for knee metric."""
        if verdict == "Good":
            return f"Knee bend at {value:.1f}° provides good balance and power generation."
        elif verdict == "Needs Work":
            if value > 120:
                return f"Knee bend at {value:.1f}° is too shallow. Bend more for better leg drive."
            else:
                return f"Knee bend at {value:.1f}° is too deep. May compromise balance and timing."
        else:
            return "Insufficient data to evaluate knee bend."
    
    def _generate_wrist_explanation(self, value: float, verdict: str) -> str:
        """Generate explanation for wrist metric."""
        if verdict == "Good":
            return f"Wrist follow-through of {value:.1f}° shows good snap and rotation."
        elif verdict == "Needs Work":
            if value < 10:
                return f"Wrist follow-through of {value:.1f}° is minimal. Snap through more for backspin."
            else:
                return f"Wrist follow-through of {value:.1f}° may be excessive. Focus on controlled snap."
        else:
            return "Insufficient data to evaluate wrist follow-through."
    
    def compute_overall_score(self, metrics: List[Dict[str, Any]]) -> Tuple[int, str]:
        """
        Compute overall score from metrics.
        
        Returns:
            Tuple of (score 0-100, feedback_summary)
        """
        weights = self.scoring_config.get("weights", {
            "elbow": 0.40,
            "knee": 0.30,
            "wrist": 0.30
        })
        
        confidence_penalty = self.scoring_config.get("confidence_penalty", 0.5)
        
        # Compute individual scores
        metric_scores = {}
        
        for metric in metrics:
            name = metric["name"]
            verdict = metric["verdict"]
            confidence = metric["confidence"]
            
            # Base score
            if verdict == "Good":
                base_score = 33.33
            elif verdict == "Needs Work":
                base_score = 16.67
            else:  # Low Confidence
                base_score = 8.33
            
            # Apply confidence penalty
            if confidence < self.scoring_config.get("low_confidence_threshold", 0.4):
                base_score *= confidence_penalty
            
            metric_scores[name] = base_score
        
        # Weighted sum
        total_score = (
            metric_scores.get("elbow_extension", 0) * weights.get("elbow", 0.4) / 0.4 +
            metric_scores.get("knee_bend", 0) * weights.get("knee", 0.3) / 0.3 +
            metric_scores.get("wrist_follow_through", 0) * weights.get("wrist", 0.3) / 0.3
        ) / 3
        
        # Normalize to 0-100
        overall_score = int(min(100, max(0, total_score * 3)))
        
        # Generate feedback summary
        feedback_summary = self._generate_feedback_summary(metrics, overall_score)
        
        return overall_score, feedback_summary
    
    def _generate_feedback_summary(self, metrics: List[Dict[str, Any]], score: int) -> str:
        """Generate overall feedback summary."""
        # Identify weakest metric
        needs_work = [m for m in metrics if m["verdict"] == "Needs Work"]
        
        if score >= 80:
            if needs_work:
                focus = needs_work[0]["name"].replace("_", " ")
                return f"Excellent form overall! Fine-tune your {focus} for even better consistency."
            return "Excellent shooting form! All metrics show strong technique."
        elif score >= 60:
            if needs_work:
                focus = needs_work[0]["name"].replace("_", " ")
                return f"Good shooting form with focus needed on {focus}."
            return "Good shooting form. Continue refining your technique."
        else:
            if needs_work:
                focus = needs_work[0]["name"].replace("_", " ")
                return f"Form needs improvement. Start by focusing on your {focus}."
            return "Focus on fundamentals: balance, elbow position, and follow-through."
    
    def export_report_json(
        self,
        metrics: List[Dict[str, Any]],
        overall_score: int,
        feedback_summary: str,
        output_path: Path
    ):
        """
        Export comprehensive report to JSON.
        
        Args:
            metrics: List of metric dicts
            overall_score: Overall score 0-100
            feedback_summary: Summary feedback text
            output_path: Path to save report JSON
        """
        report = {
            "overall_score": overall_score,
            "feedback_summary": feedback_summary,
            "metrics": metrics,
            "scoring_method": "weighted_sum",
            "weights": self.scoring_config.get("weights", {}),
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)


def derive_metrics_and_score(
    angles_csv: Path,
    shot_window_json: Path,
    config: Dict[str, Any],
    output_path: Path
) -> Dict[str, Any]:
    """
    Convenience function to derive metrics and compute score.
    
    Args:
        angles_csv: Path to angles CSV
        shot_window_json: Path to shot window JSON
        config: Metrics and scoring config
        output_path: Path to save report JSON
    
    Returns:
        Report dict
    """
    # Load data
    angles_df = pd.read_csv(angles_csv)
    with open(shot_window_json, 'r') as f:
        shot_window = json.load(f)
    
    # Create derivation and process
    derivation = MetricsDerivation(config)
    metrics = derivation.derive_metrics(angles_df, shot_window)
    overall_score, feedback_summary = derivation.compute_overall_score(metrics)
    
    # Export report
    derivation.export_report_json(metrics, overall_score, feedback_summary, output_path)
    
    return {
        "overall_score": overall_score,
        "feedback_summary": feedback_summary,
        "metrics": metrics
    }
