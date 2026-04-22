"""
Metric derivation and explainable MVP scoring.

Primitive metrics: elbow extension, knee bend, wrist follow-through.
Component scores (0-100): loading_quality, release_mechanics,
follow_through_control, balance_stability — weighted into overall score.
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class MetricsDerivation:
    """Derives metrics from angles and shot window."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.metrics_config = config.get("metrics", {})
        self.scoring_config = config.get("scoring", {})

    def derive_metrics(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        metrics = []
        metrics.append(self._compute_elbow_extension(angles_df, shot_window))
        metrics.append(self._compute_knee_bend(angles_df, shot_window))
        metrics.append(self._compute_wrist_followthrough(angles_df, shot_window))
        return metrics

    def _nearest_rows(
        self,
        angles_df: pd.DataFrame,
        frame_id: int,
        half_window: int = 3,
    ) -> pd.DataFrame:
        lo = frame_id - half_window
        hi = frame_id + half_window
        return angles_df[
            (angles_df["frame_id"] >= lo) & (angles_df["frame_id"] <= hi)
        ]

    def _compute_elbow_extension(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> Dict[str, Any]:
        release_frame = int(shot_window["release_frame"])
        release_window = self.metrics_config.get("elbow_extension", {}).get("release_window", 3)
        window_frames = angles_df[
            (angles_df["frame_id"] >= release_frame - release_window)
            & (angles_df["frame_id"] <= release_frame + release_window)
        ]
        if len(window_frames) == 0:
            return self._create_low_confidence_metric("elbow_extension")
        elbow_angles = window_frames["elbow_angle"].dropna()
        elbow_confidences = window_frames["confidence_elbow"].dropna()
        if len(elbow_angles) == 0:
            return self._create_low_confidence_metric("elbow_extension")
        value = float(np.mean(elbow_angles))
        confidence = float(np.mean(elbow_confidences))
        good_range = self.metrics_config.get("elbow_extension", {}).get("good_range", [150, 175])
        optimal_range = self.metrics_config.get("elbow_extension", {}).get("optimal_range", [160, 170])
        verdict = self._assign_verdict(value, good_range, optimal_range, confidence)
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
                int(release_frame + release_window),
            ],
        }

    def _compute_knee_bend(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> Dict[str, Any]:
        crouch_frame = int(shot_window["crouch_frame"])
        near = self._nearest_rows(angles_df, crouch_frame, half_window=2)
        if near.empty:
            return self._create_low_confidence_metric("knee_bend")
        knee_vals = near["knee_angle"].dropna()
        if knee_vals.empty:
            return self._create_low_confidence_metric("knee_bend")
        idx = (near["knee_angle"] - knee_vals.min()).abs().idxmin()
        row = near.loc[idx]
        value = float(row["knee_angle"])
        confidence = float(row["confidence_knee"])
        if np.isnan(value):
            return self._create_low_confidence_metric("knee_bend")
        good_range = self.metrics_config.get("knee_bend", {}).get("good_range", [85, 120])
        optimal_range = self.metrics_config.get("knee_bend", {}).get("optimal_range", [95, 110])
        verdict = self._assign_verdict(value, good_range, optimal_range, confidence)
        explanation = self._generate_knee_explanation(value, verdict)
        return {
            "name": "knee_bend",
            "value": value,
            "unit": "degrees",
            "verdict": verdict,
            "explanation": explanation,
            "confidence": confidence,
            "frame_range": [int(crouch_frame), int(crouch_frame)],
        }

    def _compute_wrist_followthrough(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> Dict[str, Any]:
        release_frame = int(shot_window["release_frame"])
        end_frame = int(shot_window["end_frame"])
        rel_near = self._nearest_rows(angles_df, release_frame, half_window=2)
        end_near = self._nearest_rows(angles_df, end_frame, half_window=2)
        if rel_near.empty or end_near.empty:
            return self._create_low_confidence_metric("wrist_follow_through")
        r_row = rel_near.iloc[(rel_near["frame_id"] - release_frame).mul(1).abs().argmin()]
        e_row = end_near.iloc[(end_near["frame_id"] - end_frame).mul(1).abs().argmin()]
        release_angle = r_row["wrist_angle"]
        end_angle = e_row["wrist_angle"]
        if np.isnan(release_angle) or np.isnan(end_angle):
            return self._create_low_confidence_metric("wrist_follow_through")
        value = float(abs(end_angle - release_angle))
        confidence = float(
            min(float(r_row["confidence_wrist"]), float(e_row["confidence_wrist"]))
        )
        good_range = self.metrics_config.get("wrist_follow_through", {}).get("good_range", [10, 30])
        optimal_range = self.metrics_config.get("wrist_follow_through", {}).get("optimal_range", [15, 25])
        verdict = self._assign_verdict(value, good_range, optimal_range, confidence)
        explanation = self._generate_wrist_explanation(value, verdict)
        return {
            "name": "wrist_follow_through",
            "value": value,
            "unit": "degrees",
            "verdict": verdict,
            "explanation": explanation,
            "confidence": confidence,
            "frame_range": [int(r_row["frame_id"]), int(e_row["frame_id"])],
        }

    def _assign_verdict(
        self,
        value: float,
        good_range: List[float],
        optimal_range: List[float],
        confidence: float,
    ) -> str:
        low_conf_threshold = self.scoring_config.get("low_confidence_threshold", 0.4)
        if confidence < low_conf_threshold:
            return "Low Confidence"
        if optimal_range[0] <= value <= optimal_range[1]:
            return "Good"
        if good_range[0] <= value <= good_range[1]:
            return "Good"
        return "Needs Work"

    def _create_low_confidence_metric(self, name: str) -> Dict[str, Any]:
        reason = (
            "Insufficient joint visibility or unstable tracking. "
            "Re-record with better lighting and full-body view."
        )
        return {
            "name": name,
            "value": 0.0,
            "unit": "N/A",
            "verdict": "Low Confidence",
            "explanation": reason,
            "confidence": 0.0,
            "frame_range": [0, 0],
        }

    def _generate_elbow_explanation(self, value: float, verdict: str) -> str:
        if verdict == "Good":
            return f"Elbow at {value:.1f}° supports solid release mechanics."
        if verdict == "Needs Work":
            if value < 150:
                return f"Elbow at {value:.1f}° is quite bent — extend more through release."
            return f"Elbow at {value:.1f}° looks over-extended — keep a bit more flex for control."
        return "Insufficient data to evaluate elbow extension."

    def _generate_knee_explanation(self, value: float, verdict: str) -> str:
        if verdict == "Good":
            return f"Knee bend near {value:.1f}° shows a usable load for leg drive."
        if verdict == "Needs Work":
            if value > 120:
                return f"Knee bend at {value:.1f}° is shallow — load a bit more if you can."
            return f"Knee bend at {value:.1f}° is very deep — watch balance and timing."
        return "Insufficient data to evaluate knee bend."

    def _generate_wrist_explanation(self, value: float, verdict: str) -> str:
        if verdict == "Good":
            return f"Wrist change of {value:.1f}° suggests a clear follow-through."
        if verdict == "Needs Work":
            if value < 10:
                return f"Wrist change of {value:.1f}° is small — add more snap through the ball."
            return f"Wrist change of {value:.1f}° is large — aim for a controlled snap."
        return "Insufficient data to evaluate wrist follow-through."

    def _score_range(self, value: float, optimal: List[float], good: List[float]) -> float:
        opt_min, opt_max = optimal
        good_min, good_max = good
        if opt_min <= value <= opt_max:
            return 100.0
        if good_min <= value <= good_max:
            if value < opt_min:
                return 70 + 30 * (value - good_min) / (opt_min - good_min + 1e-6)
            return 70 + 30 * (good_max - value) / (good_max - opt_max + 1e-6)
        if value < good_min:
            distance = good_min - value
            span = max(good_min - opt_min, 1.0)
            return max(0.0, 70 - 30 * (distance / span))
        distance = value - good_max
        span = max(opt_max - good_max, 1.0)
        return max(0.0, 70 - 30 * (distance / span))

    def _apply_confidence_scale(self, base: float, confidence: float) -> float:
        low = self.scoring_config.get("low_confidence_threshold", 0.4)
        floor = self.scoring_config.get("confidence_penalty", 0.5)
        if confidence < low:
            scale = floor + (confidence / max(low, 1e-6)) * (1 - floor)
            return base * scale
        return base

    def compute_score_components(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
        primitive_metrics: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Explainable 0-100 component scores mapped from measurable features."""
        weights = self.scoring_config.get(
            "component_weights",
            {
                "loading_quality": 0.30,
                "release_mechanics": 0.35,
                "follow_through_control": 0.20,
                "balance_stability": 0.15,
            },
        )
        crouch = int(shot_window["crouch_frame"])
        release = int(shot_window["release_frame"])
        end_f = int(shot_window["end_frame"])
        start_f = int(shot_window.get("start_frame", max(0, crouch - 15)))

        knee_cfg = self.metrics_config.get("knee_bend", {})
        elbow_cfg = self.metrics_config.get("elbow_extension", {})
        wrist_cfg = self.metrics_config.get("wrist_follow_through", {})

        # Loading: knee depth at crouch + smoothness of knee around crouch
        knee_m = next((m for m in primitive_metrics if m["name"] == "knee_bend"), None)
        knee_val = (
            float(knee_m["value"])
            if knee_m is not None and knee_m.get("verdict") != "Low Confidence"
            else 95.0
        )
        knee_conf = float(knee_m["confidence"]) if knee_m is not None else 0.5
        knee_base = self._score_range(
            knee_val,
            knee_cfg.get("optimal_range", [95, 110]),
            knee_cfg.get("good_range", [85, 120]),
        )
        knee_base = self._apply_confidence_scale(knee_base, knee_conf)
        win = angles_df[
            (angles_df["frame_id"] >= crouch - 5) & (angles_df["frame_id"] <= crouch + 5)
        ]
        if len(win) > 2:
            kd = win["knee_angle"].diff().abs().dropna()
            jitter = float(kd.mean()) if not kd.empty else 0.0
            smooth_score = max(0.0, 100.0 - min(60.0, jitter * 4.0))
        else:
            smooth_score = 65.0
        loading_quality = float(0.65 * knee_base + 0.35 * smooth_score)

        # Release: elbow window (same as primitive)
        elbow_m = next((m for m in primitive_metrics if m["name"] == "elbow_extension"), None)
        elbow_val = (
            float(elbow_m["value"])
            if elbow_m is not None and elbow_m.get("verdict") != "Low Confidence"
            else 160.0
        )
        elbow_conf = float(elbow_m["confidence"]) if elbow_m is not None else 0.5
        release_mechanics = self._score_range(
            elbow_val,
            elbow_cfg.get("optimal_range", [160, 170]),
            elbow_cfg.get("good_range", [150, 175]),
        )
        release_mechanics = self._apply_confidence_scale(release_mechanics, elbow_conf)

        # Follow-through: wrist delta primitive
        wrist_m = next((m for m in primitive_metrics if m["name"] == "wrist_follow_through"), None)
        wrist_val = (
            float(wrist_m["value"])
            if wrist_m is not None and wrist_m.get("verdict") != "Low Confidence"
            else 18.0
        )
        wrist_conf = float(wrist_m["confidence"]) if wrist_m is not None else 0.5
        follow_through_control = self._score_range(
            wrist_val,
            wrist_cfg.get("optimal_range", [15, 25]),
            wrist_cfg.get("good_range", [10, 30]),
        )
        follow_through_control = self._apply_confidence_scale(
            follow_through_control, wrist_conf
        )

        # Balance proxy: knee variability around release (no hip in angles table)
        bal_win = angles_df[
            (angles_df["frame_id"] >= max(start_f, release - 12))
            & (angles_df["frame_id"] <= min(end_f, release + 20))
        ]
        if len(bal_win) > 2:
            ks = bal_win["knee_angle"].dropna()
            std_k = float(ks.std()) if len(ks) else 8.0
            balance_stability = float(max(0.0, 100.0 - min(55.0, std_k * 3.5)))
        else:
            balance_stability = 60.0

        components = [
            {
                "name": "loading_quality",
                "value": round(loading_quality, 1),
                "unit": "score",
                "weight": weights.get("loading_quality", 0.30),
                "explanation": "Leg load depth and smoothness into the motion.",
            },
            {
                "name": "release_mechanics",
                "value": round(release_mechanics, 1),
                "unit": "score",
                "weight": weights.get("release_mechanics", 0.35),
                "explanation": "Elbow extension and timing near release.",
            },
            {
                "name": "follow_through_control",
                "value": round(follow_through_control, 1),
                "unit": "score",
                "weight": weights.get("follow_through_control", 0.20),
                "explanation": "Controlled wrist movement after release.",
            },
            {
                "name": "balance_stability",
                "value": round(balance_stability, 1),
                "unit": "score",
                "weight": weights.get("balance_stability", 0.15),
                "explanation": "Stability proxy from knee consistency around release.",
            },
        ]
        return components

    def compute_overall_score(
        self,
        metrics: List[Dict[str, Any]],
        angles_df: Optional[pd.DataFrame] = None,
        shot_window: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, str, List[str], List[Dict[str, Any]]]:
        """
        Weighted component score -> overall + summary + feedback bullets.
        """
        if angles_df is None or shot_window is None:
            # Backward-compatible path
            return self._legacy_overall_from_primitives(metrics)

        components = self.compute_score_components(angles_df, shot_window, metrics)
        tw = sum(float(c["weight"]) for c in components) or 1.0
        weighted = sum(float(c["value"]) * float(c["weight"]) for c in components) / tw
        overall_score = int(round(min(100.0, max(0.0, weighted))))

        # Feedback bullets: two lowest components + one strength
        sorted_c = sorted(components, key=lambda c: c["value"])
        bullets: List[str] = []
        comp_labels = {
            "loading_quality": "leg load",
            "release_mechanics": "release mechanics",
            "follow_through_control": "follow-through",
            "balance_stability": "balance",
        }
        for c in sorted_c[:2]:
            if c["value"] < 65:
                label = comp_labels.get(c["name"], c["name"])
                bullets.append(f"Prioritize {label} — component score {c['value']:.0f}/100.")
        best = max(components, key=lambda c: c["value"])
        if best["value"] >= 70:
            label = comp_labels.get(best["name"], best["name"])
            bullets.append(f"Strength: {label} looks solid ({best['value']:.0f}/100).")
        if not bullets:
            bullets.append("Keep recording side-on with full body in frame for best tracking.")

        needs = [m for m in metrics if m.get("verdict") == "Needs Work"]
        summary = self._generate_feedback_summary(metrics, overall_score, needs, sorted_c)
        return overall_score, summary, bullets, components

    def _legacy_overall_from_primitives(
        self,
        metrics: List[Dict[str, Any]],
    ) -> Tuple[int, str, List[str], List[Dict[str, Any]]]:
        weights = self.scoring_config.get(
            "weights",
            {"elbow": 0.40, "knee": 0.30, "wrist": 0.30},
        )
        low_conf_threshold = self.scoring_config.get("low_confidence_threshold", 0.4)
        confidence_floor = self.scoring_config.get("confidence_penalty", 0.5)
        metric_scores: Dict[str, float] = {}
        for metric in metrics:
            name = metric["name"]
            confidence = float(metric.get("confidence", 0.0))
            value = float(metric.get("value", 0.0))
            if name == "elbow_extension":
                good = self.metrics_config.get("elbow_extension", {}).get("good_range", [150, 175])
                optimal = self.metrics_config.get("elbow_extension", {}).get("optimal_range", [160, 170])
            elif name == "knee_bend":
                good = self.metrics_config.get("knee_bend", {}).get("good_range", [85, 120])
                optimal = self.metrics_config.get("knee_bend", {}).get("optimal_range", [95, 110])
            elif name == "wrist_follow_through":
                good = self.metrics_config.get("wrist_follow_through", {}).get("good_range", [10, 30])
                optimal = self.metrics_config.get("wrist_follow_through", {}).get("optimal_range", [15, 25])
            else:
                metric_scores[name] = 0.0
                continue
            base = self._score_range(value, optimal, good)
            if confidence < low_conf_threshold:
                scale = confidence_floor + (confidence / max(low_conf_threshold, 1e-6)) * (
                    1 - confidence_floor
                )
                base *= scale
            metric_scores[name] = base
        total_weight = (
            weights.get("elbow", 0.4) + weights.get("knee", 0.3) + weights.get("wrist", 0.3)
        )
        weighted_score = (
            metric_scores.get("elbow_extension", 0.0) * weights.get("elbow", 0.4)
            + metric_scores.get("knee_bend", 0.0) * weights.get("knee", 0.3)
            + metric_scores.get("wrist_follow_through", 0.0) * weights.get("wrist", 0.3)
        ) / max(total_weight, 1e-6)
        overall_score = int(round(min(100.0, max(0.0, weighted_score))))
        summary = self._generate_feedback_summary(metrics, overall_score, [], [])
        return overall_score, summary, [], []

    def _generate_feedback_summary(
        self,
        metrics: List[Dict[str, Any]],
        score: int,
        needs_work: List[Dict[str, Any]],
        sorted_components: List[Dict[str, Any]],
    ) -> str:
        """One-line summary; bullets live in feedback_bullets field on API."""
        if sorted_components:
            weakest = sorted_components[0]
            if weakest["value"] < 60:
                return (
                    f"Overall {score}/100 — biggest gap: "
                    f"{weakest['name'].replace('_', ' ')} ({weakest['value']:.0f}/100)."
                )
        if score >= 80:
            if needs_work:
                focus = needs_work[0]["name"].replace("_", " ")
                return f"Strong form overall; refine {focus}."
            return "Strong shooting mechanics across tracked signals."
        if score >= 60:
            if needs_work:
                focus = needs_work[0]["name"].replace("_", " ")
                return f"Good base — focus next on {focus}."
            return "Good foundation; keep refining consistency."
        if needs_work:
            focus = needs_work[0]["name"].replace("_", " ")
            return f"Focus on {focus} and re-record with clear side view."
        return "Review component scores and capture a clearer full-body clip."

    def export_report_json(
        self,
        metrics: List[Dict[str, Any]],
        overall_score: int,
        feedback_summary: str,
        output_path: Path,
        score_components: Optional[List[Dict[str, Any]]] = None,
        feedback_bullets: Optional[List[str]] = None,
    ):
        report: Dict[str, Any] = {
            "overall_score": overall_score,
            "feedback_summary": feedback_summary,
            "metrics": metrics,
            "scoring_method": "component_weighted",
            "component_weights": self.scoring_config.get("component_weights", {}),
            "legacy_weights": self.scoring_config.get("weights", {}),
        }
        if score_components is not None:
            report["score_components"] = score_components
        if feedback_bullets is not None:
            report["feedback_bullets"] = feedback_bullets
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)


def derive_metrics_and_score(
    angles_csv: Path,
    shot_window_json: Path,
    config: Dict[str, Any],
    output_path: Path,
) -> Dict[str, Any]:
    angles_df = pd.read_csv(angles_csv)
    with open(shot_window_json, "r") as f:
        shot_window = json.load(f)
    derivation = MetricsDerivation(config)
    metrics = derivation.derive_metrics(angles_df, shot_window)
    overall_score, feedback_summary, bullets, components = derivation.compute_overall_score(
        metrics, angles_df, shot_window
    )
    derivation.export_report_json(
        metrics,
        overall_score,
        feedback_summary,
        output_path,
        score_components=components,
        feedback_bullets=bullets,
    )
    return {
        "overall_score": overall_score,
        "feedback_summary": feedback_summary,
        "feedback_bullets": bullets,
        "metrics": metrics,
        "score_components": components,
    }