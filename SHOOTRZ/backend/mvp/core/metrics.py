"""
Metric derivation and explainable MVP scoring.

Primitive metrics: elbow extension, knee bend, wrist follow-through.
Component scores (0-100): loading_quality, release_mechanics,
follow_through_control, balance_stability — kept for frontend display.
Overall score now uses a confidence-weighted geometric mean of primitive
sub-scores against ``backend/metrics/normative_ranges.json``.
"""

import json
import math
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Minimum per-joint visibility for a row in the release/crouch window to be
# eligible for selection as the metric's ``selected_frame``. Rows below this
# are excluded rather than silently averaged, which previously caused a single
# low-visibility frame to nuke an otherwise valid metric.
MIN_JOINT_CONF_FOR_METRIC = 0.50

# Widened search windows. The detected release / crouch frame does not have to
# coincide with the biomechanical peak (peak extension / deepest knee / end of
# follow-through) — so we look around it and pick the best-confidence frame
# that matches the expected semantic.
RELEASE_SEARCH = 10
CROUCH_SEARCH = 6
END_SEARCH = 6


# Load the research-backed normative ranges ONCE at import. Fall back silently
# if the file is missing so tests and minimal deployments still work.
_NORMATIVE_PATH = Path(__file__).parent.parent.parent / "metrics" / "normative_ranges.json"
try:
    with open(_NORMATIVE_PATH, "r", encoding="utf-8") as _f:
        _NORMATIVE_RANGES: Dict[str, Any] = json.load(_f)
except Exception:
    _NORMATIVE_RANGES = {}


# Hard-coded fallbacks so the aggregator never silently collapses to zero when
# ``normative_ranges.json`` is missing in stripped deployments.
_FALLBACK_RANGES: Dict[str, Tuple[float, float]] = {
    "elbow_flexion_release": (165.0, 180.0),
    "elbow_flexion_preparatory": (70.0, 85.0),
    "knee_flexion": (100.0, 120.0),
    "forearm_verticality": (0.0, 10.0),
    "release_angle": (50.0, 65.0),
    "entry_angle": (45.0, 55.0),
    "wrist_angular_velocity": (2.5, 6.0),
    "wrist_follow_through": (15.0, 25.0),
}


# Maps primitive metric names (as produced by ``derive_metrics``) to the
# normative-range key that should be used for scoring. The weight is the
# relative importance of this dimension in the geomean (weights need not sum
# to 1 — they are re-normalised per-request from the metrics actually present).
_METRIC_SCORING_MAP: Dict[str, Dict[str, Any]] = {
    "elbow_extension": {"norm_key": "elbow_flexion_release", "weight": 0.32},
    "knee_bend": {"norm_key": "knee_flexion", "weight": 0.24},
    "wrist_follow_through": {"norm_key": "wrist_follow_through", "weight": 0.14},
    "release_angle": {"norm_key": "release_angle_4.6m", "weight": 0.20},
    "forearm_verticality": {"norm_key": "forearm_verticality", "weight": 0.10},
}


def _target_of(norm_key: str) -> Tuple[Optional[float], Optional[float]]:
    """Return the `(lo, hi)` optimal range for a normative key, with fallback.

    We prefer ``optimal_range`` (the tight biomech-ideal band) when present
    because the softened ``_dim_score`` uses ``good_range`` as the outer band
    on top of that. Falls back to ``target_range`` when only one is defined.
    """
    cfg = _NORMATIVE_RANGES.get(norm_key, {})
    tr = cfg.get("optimal_range") or cfg.get("target_range")
    if isinstance(tr, list) and len(tr) == 2:
        return float(tr[0]), float(tr[1])
    # Tolerate metric-name keys in the fallback (e.g. "release_angle" vs
    # "release_angle_4.6m").
    if norm_key in _FALLBACK_RANGES:
        lo, hi = _FALLBACK_RANGES[norm_key]
        return lo, hi
    simple = norm_key.split("_")[0] if "_" in norm_key else norm_key
    if simple in _FALLBACK_RANGES:
        lo, hi = _FALLBACK_RANGES[simple]
        return lo, hi
    return None, None


def _good_range_of(norm_key: str) -> Optional[Tuple[float, float]]:
    """Return ``good_range`` for ``norm_key`` if defined in the JSON.

    ``good_range`` is intentionally WIDER than ``optimal_range``. When absent,
    ``_dim_score`` derives a synthetic good-range by widening the optimal
    range by 50% each side so the scoring shape still has a "close-enough"
    band instead of collapsing outside optimal.
    """
    cfg = _NORMATIVE_RANGES.get(norm_key, {})
    gr = cfg.get("good_range")
    if isinstance(gr, list) and len(gr) == 2:
        return float(gr[0]), float(gr[1])
    return None


def _dim_score(norm_key: str, value: float) -> Optional[float]:
    """Piecewise sub-score (100 at ideal, gentle slope elsewhere).

    The pre-2026-04-23 scoring used a tight Gaussian with sigma derived from
    half the optimal range. That collapsed to near-zero for values that were
    still "close" in coaching terms (e.g. elbow 152 deg vs target 165-180 -> ~3/100).
    An amateur shot with one weak axis therefore scored 3/100 instead of
    something that matches how a coach would grade it.

    New shape (symmetric on either side of the optimal band):

    * value in ``optimal`` (tightest band)                         -> 100
    * value in ``good`` but outside ``optimal``                    -> linear 70..100
    * value within one ``good`` width of ``good``                  -> linear 30..70
    * further out                                                  -> linear decay
                                                                     from 30 to 0 over
                                                                     another ``good`` width
    * beyond that                                                  -> 0

    Deliberately forgiving: two small errors shouldn't multiply to zero
    under the geomean. Gemini, when available, still overrides the final
    overall score so this is really the "deterministic floor".
    """
    opt = _target_of(norm_key)
    if opt[0] is None or opt[1] is None or not math.isfinite(value):
        return None
    opt_lo, opt_hi = opt

    gr = _good_range_of(norm_key)
    if gr is None:
        # Synthesise a good_range by widening optimal by 50% each side.
        opt_mid = (opt_lo + opt_hi) / 2.0
        opt_half = max((opt_hi - opt_lo) / 2.0, 1.0)
        good_lo = opt_mid - opt_half * 1.5
        good_hi = opt_mid + opt_half * 1.5
    else:
        good_lo, good_hi = gr
        # Guarantee ``good_range`` strictly contains ``optimal_range``.
        good_lo = min(good_lo, opt_lo)
        good_hi = max(good_hi, opt_hi)

    good_width = max(good_hi - good_lo, 1.0)

    if opt_lo <= value <= opt_hi:
        return 100.0

    if good_lo <= value <= good_hi:
        # Linear 70..100 based on distance from the nearest optimal edge,
        # normalised by the width of the good-but-not-optimal side.
        if value < opt_lo:
            span = max(opt_lo - good_lo, 1e-3)
            frac = (value - good_lo) / span  # 0 at good_lo, 1 at opt_lo
        else:
            span = max(good_hi - opt_hi, 1e-3)
            frac = (good_hi - value) / span
        return 70.0 + 30.0 * max(0.0, min(1.0, frac))

    # Outside good_range - fall smoothly from 70 at the edge to 30 over one
    # good_width, then 30 -> 0 over another good_width.
    if value < good_lo:
        dist = good_lo - value
    else:
        dist = value - good_hi

    if dist <= good_width:
        return 70.0 - 40.0 * (dist / good_width)  # 70 -> 30
    if dist <= 2.0 * good_width:
        return max(0.0, 30.0 - 30.0 * ((dist - good_width) / good_width))  # 30 -> 0
    return 0.0


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

    def _window(
        self,
        angles_df: pd.DataFrame,
        center_frame: int,
        half_window: int,
        angle_col: str,
        conf_col: str,
        min_conf: float = MIN_JOINT_CONF_FOR_METRIC,
    ) -> pd.DataFrame:
        """Return rows near ``center_frame`` where the angle is finite and
        the involved joints pass ``min_conf``.

        Replaces the old "mean-over-window" behaviour: a single low-visibility
        frame would drag NaN into the aggregate or the whole metric. With this
        helper we can instead pick the best-confidence / best-semantic frame.
        """
        lo = center_frame - half_window
        hi = center_frame + half_window
        chunk = angles_df[
            (angles_df["frame_id"] >= lo) & (angles_df["frame_id"] <= hi)
        ].copy()
        if chunk.empty:
            return chunk
        chunk = chunk[chunk[angle_col].notna()]
        chunk = chunk[chunk[conf_col] >= float(min_conf)]
        return chunk

    @staticmethod
    def _pick_peak(
        chunk: pd.DataFrame,
        angle_col: str,
        mode: str,
    ) -> Optional[pd.Series]:
        """Choose the single representative row inside ``chunk``.

        ``mode`` is one of:
          - ``"max"``  -> pick row with the largest angle (elbow extension peak)
          - ``"min"``  -> pick row with the smallest angle (knee flexion peak)
          - ``"last"`` -> pick the temporally last row (wrist follow-through end)
          - ``"first"``-> pick the temporally first row (wrist at release)
        """
        if chunk.empty:
            return None
        if mode == "max":
            idx = chunk[angle_col].astype(float).idxmax()
        elif mode == "min":
            idx = chunk[angle_col].astype(float).idxmin()
        elif mode == "last":
            idx = chunk["frame_id"].astype(int).idxmax()
        elif mode == "first":
            idx = chunk["frame_id"].astype(int).idxmin()
        else:
            idx = chunk.index[0]
        return chunk.loc[idx]

    def _compute_elbow_extension(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> Dict[str, Any]:
        release_frame = int(shot_window["release_frame"])
        search = int(
            self.metrics_config.get("elbow_extension", {}).get(
                "release_search", RELEASE_SEARCH
            )
        )
        chunk = self._window(
            angles_df,
            release_frame,
            search,
            angle_col="elbow_angle",
            conf_col="confidence_elbow",
        )
        if chunk.empty:
            return self._create_low_confidence_metric("elbow_extension")

        row = self._pick_peak(chunk, "elbow_angle", mode="max")
        if row is None:
            return self._create_low_confidence_metric("elbow_extension")

        value = float(row["elbow_angle"])
        confidence = float(row["confidence_elbow"])
        selected_frame = int(row["frame_id"])
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
            "frame_range": [selected_frame, selected_frame],
            "selected_frame": selected_frame,
        }

    def _compute_knee_bend(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> Dict[str, Any]:
        crouch_frame = int(shot_window["crouch_frame"])
        search = int(
            self.metrics_config.get("knee_bend", {}).get("crouch_search", CROUCH_SEARCH)
        )
        chunk = self._window(
            angles_df,
            crouch_frame,
            search,
            angle_col="knee_angle",
            conf_col="confidence_knee",
        )
        if chunk.empty:
            return self._create_low_confidence_metric("knee_bend")

        row = self._pick_peak(chunk, "knee_angle", mode="min")
        if row is None:
            return self._create_low_confidence_metric("knee_bend")

        value = float(row["knee_angle"])
        confidence = float(row["confidence_knee"])
        selected_frame = int(row["frame_id"])
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
            "frame_range": [selected_frame, selected_frame],
            "selected_frame": selected_frame,
        }

    def _compute_wrist_followthrough(
        self,
        angles_df: pd.DataFrame,
        shot_window: Dict[str, Any],
    ) -> Dict[str, Any]:
        release_frame = int(shot_window["release_frame"])
        end_frame = int(shot_window["end_frame"])
        release_search = int(
            self.metrics_config.get("wrist_follow_through", {}).get(
                "release_search", RELEASE_SEARCH
            )
        )
        end_search = int(
            self.metrics_config.get("wrist_follow_through", {}).get(
                "end_search", END_SEARCH
            )
        )
        rel_chunk = self._window(
            angles_df,
            release_frame,
            release_search,
            angle_col="wrist_angle",
            conf_col="confidence_wrist",
        )
        end_chunk = self._window(
            angles_df,
            end_frame,
            end_search,
            angle_col="wrist_angle",
            conf_col="confidence_wrist",
        )
        if rel_chunk.empty or end_chunk.empty:
            return self._create_low_confidence_metric("wrist_follow_through")

        r_row = self._pick_peak(rel_chunk, "wrist_angle", mode="first")
        e_row = self._pick_peak(end_chunk, "wrist_angle", mode="last")
        if r_row is None or e_row is None:
            return self._create_low_confidence_metric("wrist_follow_through")

        release_angle = float(r_row["wrist_angle"])
        end_angle = float(e_row["wrist_angle"])
        value = float(abs(end_angle - release_angle))
        confidence = float(
            min(float(r_row["confidence_wrist"]), float(e_row["confidence_wrist"]))
        )
        selected_frame = int(e_row["frame_id"])
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
            "selected_frame": selected_frame,
        }

    def _assign_verdict(
        self,
        value: float,
        good_range: List[float],
        optimal_range: List[float],
        confidence: float,
    ) -> str:
        low_conf_threshold = self.scoring_config.get("low_confidence_threshold", 0.5)
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
            "selected_frame": None,
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
        low = self.scoring_config.get("low_confidence_threshold", 0.5)
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

        # Loading: knee depth at crouch + smoothness of knee around crouch.
        # NOTE on 2026-04-23: the pre-fix version silently substituted 95.0 /
        # 160.0 / 18.0 when a primitive came back Low Confidence, so the
        # component score would look plausible even when the underlying metric
        # was N/A. That caused the "Strength: leg load looks solid (71/100)"
        # bullet to appear next to an Elbow N/A card. We now return ``None``
        # for the component value whenever the primitive is Low Confidence so
        # downstream aggregation and feedback can honestly exclude it.
        knee_m = next((m for m in primitive_metrics if m["name"] == "knee_bend"), None)
        loading_quality: Optional[float]
        if knee_m is None or knee_m.get("verdict") == "Low Confidence":
            loading_quality = None
        else:
            knee_val = float(knee_m["value"])
            knee_conf = float(knee_m["confidence"])
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
        release_mechanics: Optional[float]
        if elbow_m is None or elbow_m.get("verdict") == "Low Confidence":
            release_mechanics = None
        else:
            elbow_val = float(elbow_m["value"])
            elbow_conf = float(elbow_m["confidence"])
            release_mechanics = self._score_range(
                elbow_val,
                elbow_cfg.get("optimal_range", [160, 170]),
                elbow_cfg.get("good_range", [150, 175]),
            )
            release_mechanics = self._apply_confidence_scale(release_mechanics, elbow_conf)

        # Follow-through: wrist delta primitive
        wrist_m = next((m for m in primitive_metrics if m["name"] == "wrist_follow_through"), None)
        follow_through_control: Optional[float]
        if wrist_m is None or wrist_m.get("verdict") == "Low Confidence":
            follow_through_control = None
        else:
            wrist_val = float(wrist_m["value"])
            wrist_conf = float(wrist_m["confidence"])
            follow_through_control = self._score_range(
                wrist_val,
                wrist_cfg.get("optimal_range", [15, 25]),
                wrist_cfg.get("good_range", [10, 30]),
            )
            follow_through_control = self._apply_confidence_scale(
                follow_through_control, wrist_conf
            )

        # Balance proxy: knee variability around release (no hip in angles table).
        # Only emit a score when knee data is actually present in the window;
        # otherwise mark N/A rather than fabricating 60 from nothing.
        bal_win = angles_df[
            (angles_df["frame_id"] >= max(start_f, release - 12))
            & (angles_df["frame_id"] <= min(end_f, release + 20))
        ]
        balance_stability: Optional[float]
        if len(bal_win) > 2:
            ks = bal_win["knee_angle"].dropna()
            if len(ks) >= 3:
                std_k = float(ks.std())
                balance_stability = float(max(0.0, 100.0 - min(55.0, std_k * 3.5)))
            else:
                balance_stability = None
        else:
            balance_stability = None

        def _emit(name: str, value: Optional[float], weight_key: str, explanation: str) -> Dict[str, Any]:
            return {
                "name": name,
                "value": round(value, 1) if value is not None else None,
                "unit": "score",
                "weight": weights.get(weight_key, 0.0),
                "explanation": explanation,
            }

        components = [
            _emit(
                "loading_quality", loading_quality, "loading_quality",
                "Leg load depth and smoothness into the motion.",
            ),
            _emit(
                "release_mechanics", release_mechanics, "release_mechanics",
                "Elbow extension and timing near release.",
            ),
            _emit(
                "follow_through_control", follow_through_control, "follow_through_control",
                "Controlled wrist movement after release.",
            ),
            _emit(
                "balance_stability", balance_stability, "balance_stability",
                "Stability proxy from knee consistency around release.",
            ),
        ]
        return components

    def compute_overall_score(
        self,
        metrics: List[Dict[str, Any]],
        angles_df: Optional[pd.DataFrame] = None,
        shot_window: Optional[Dict[str, Any]] = None,
    ) -> Tuple[int, str, List[str], List[Dict[str, Any]]]:
        """
        Confidence-weighted geometric-mean aggregator.

        Each primitive metric contributes a sub-score from a Gaussian centred
        on the normative target midpoint. Metrics with confidence below
        ``low_confidence_threshold`` are dropped so noisy frames don't distort
        the mean. The weighted log-mean is exponentiated back to a 0-100 score.

        ``score_components`` (the 4 explainable buckets the frontend renders)
        is still populated whenever ``angles_df`` and ``shot_window`` are
        provided, so no UI change is required.
        """
        low_conf_threshold = float(self.scoring_config.get("low_confidence_threshold", 0.5))

        components: List[Dict[str, Any]] = []
        if angles_df is not None and shot_window is not None:
            try:
                components = self.compute_score_components(angles_df, shot_window, metrics)
            except Exception:
                components = []

        # --- confidence-weighted geometric mean over primitive metrics ------
        breakdown: List[Dict[str, Any]] = []
        log_sum = 0.0
        weight_sum = 0.0
        total_conf = 0.0
        contributing = 0

        for metric in metrics or []:
            name = str(metric.get("name") or "")
            mapping = _METRIC_SCORING_MAP.get(name)
            if mapping is None:
                continue
            try:
                value = float(metric.get("value"))
            except (TypeError, ValueError):
                continue
            confidence = float(metric.get("confidence", 0.0) or 0.0)
            if confidence < low_conf_threshold:
                continue
            sub_score = _dim_score(mapping["norm_key"], value)
            if sub_score is None:
                continue
            weight = float(mapping["weight"]) * confidence
            log_sum += weight * math.log(sub_score + 1.0)
            weight_sum += weight
            total_conf += confidence
            contributing += 1
            lo, hi = _target_of(mapping["norm_key"])
            breakdown.append(
                {
                    "metric": name,
                    "value": round(value, 2),
                    "sub_score": round(sub_score, 1),
                    "weight": round(weight, 3),
                    "target_range": [lo, hi] if lo is not None else None,
                }
            )

        if weight_sum > 0.0 and contributing >= 1:
            geomean = math.exp(log_sum / weight_sum) - 1.0
            overall_score = int(round(min(100.0, max(0.0, geomean))))
        else:
            # Every primitive was dropped (all confidences < threshold). Do
            # NOT fabricate a fake overall by averaging component values that
            # may also be None. Return 0 and let the pipeline surface this as
            # a low-quality result with an honest message.
            overall_score = 0

        # Feedback bullets are sourced ONLY from the primitive breakdown now.
        # Component-score-based bullets previously drew from the 160/95/18
        # defaults we just removed, producing misleading strengths when the
        # primitive was N/A. If no primitive passed the gate, we give a clear
        # recording guidance instead of inventing a strength.
        bullets: List[str] = []
        if breakdown:
            sorted_bd = sorted(breakdown, key=lambda b: b["sub_score"])
            for item in sorted_bd[:2]:
                if item["sub_score"] < 65:
                    bullets.append(
                        f"Prioritize {item['metric'].replace('_', ' ')} — "
                        f"sub-score {item['sub_score']:.0f}/100."
                    )
            best = max(breakdown, key=lambda b: b["sub_score"])
            if best["sub_score"] >= 75:
                bullets.append(
                    f"Strength: {best['metric'].replace('_', ' ')} "
                    f"looks solid ({best['sub_score']:.0f}/100)."
                )
        if not bullets:
            bullets.append("Keep recording side-on with full body in frame for best tracking.")

        needs = [m for m in metrics if m.get("verdict") == "Needs Work"]
        # Summary sort tolerates None values (N/A components go last).
        scored_components = [c for c in components if c.get("value") is not None]
        sorted_components_for_summary = sorted(scored_components, key=lambda c: c["value"])
        summary = self._generate_feedback_summary(metrics, overall_score, needs, sorted_components_for_summary)

        # Surface the breakdown inside the components list so downstream
        # tooling (Gemini, debug endpoints) can see per-metric detail without
        # breaking the MVPScoreComponent schema — hence a dedicated synthetic
        # entry with weight 0.
        if breakdown and components:
            avg_conf = (total_conf / contributing) if contributing else 0.0
            components = list(components) + [
                {
                    "name": "shot_score_breakdown",
                    "value": float(overall_score),
                    "unit": "score",
                    "weight": 0.0,
                    "explanation": (
                        f"Confidence-weighted geomean over {contributing} metric(s), "
                        f"avg confidence {avg_conf:.2f}."
                    ),
                }
            ]
        return overall_score, summary, bullets, components

    def all_primitives_low_confidence(self, metrics: List[Dict[str, Any]]) -> bool:
        """True when every primitive we evaluate is Low Confidence.

        Pipeline uses this to flip status to ``completed_low_quality`` instead
        of shipping an inflated overall_score computed from nothing.
        """
        primitives = [
            m for m in metrics if str(m.get("name")) in _METRIC_SCORING_MAP
        ]
        if not primitives:
            return True
        return all(m.get("verdict") == "Low Confidence" for m in primitives)

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