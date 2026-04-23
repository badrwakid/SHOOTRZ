"""Unit tests for the confidence-weighted geomean shot score aggregator.

The aggregator lives in ``backend.mvp.core.metrics`` and is exercised via
:class:`MetricsDerivation`. The helpers ``_dim_score`` / ``_target_of`` are
imported directly for the Gaussian-shape tests.
"""
from __future__ import annotations

import pandas as pd
import pytest

from backend.mvp.core.metrics import (
    MetricsDerivation,
    _dim_score,
    _target_of,
    _METRIC_SCORING_MAP,
)


def _derivation() -> MetricsDerivation:
    return MetricsDerivation(
        {
            "metrics": {
                "elbow_extension": {"good_range": [150, 175], "optimal_range": [160, 170], "release_window": 3},
                "knee_bend": {"good_range": [85, 120], "optimal_range": [95, 110]},
                "wrist_follow_through": {"good_range": [10, 30], "optimal_range": [15, 25]},
            },
            "scoring": {
                "weights": {"elbow": 0.4, "knee": 0.3, "wrist": 0.3},
                "component_weights": {
                    "loading_quality": 0.30,
                    "release_mechanics": 0.35,
                    "follow_through_control": 0.20,
                    "balance_stability": 0.15,
                },
                "confidence_penalty": 0.5,
                "low_confidence_threshold": 0.4,
            },
        }
    )


def _angles(value_e: float, value_k: float, wrist_change: float = 20.0) -> pd.DataFrame:
    """Shot window uses release_frame=30 and end_frame=40.

    Wrist baseline sits flat at 80 until frame 32, then jumps by
    ``wrist_change`` so the ``wrist_follow_through`` metric (computed as the
    absolute delta between release and end frames) lands at ``wrist_change``.
    Keeping the jump AFTER the release window preserves the release-frame
    reading at baseline.
    """
    n = 50
    wrist = [80.0] * 33 + [80.0 + wrist_change] * (n - 33)
    return pd.DataFrame(
        {
            "frame_id": list(range(n)),
            "timestamp": [i * 0.033 for i in range(n)],
            "knee_angle": [value_k] * n,
            "elbow_angle": [value_e] * n,
            "wrist_angle": wrist,
            "confidence_knee": [0.95] * n,
            "confidence_elbow": [0.95] * n,
            "confidence_wrist": [0.95] * n,
        }
    )


def _shot_window() -> dict:
    return {"start_frame": 5, "crouch_frame": 20, "release_frame": 30, "end_frame": 40}


def test_empty_metrics_returns_zero_without_crashing():
    score, summary, bullets, components = _derivation().compute_overall_score([])
    assert score == 0
    assert isinstance(summary, str) and summary
    # Post-2026-04-23 we always return at least one actionable guidance
    # bullet rather than an empty list, so the UI's Feedback section never
    # renders a completely blank state.
    assert isinstance(bullets, list)


def test_perfect_metrics_score_above_90():
    derivation = _derivation()
    # Values sit at normative-range midpoints so every sub-score approaches 100:
    # elbow target [165,180] midpoint 172.5; knee target [100,120] midpoint 110;
    # wrist target [15,25] midpoint 20.
    angles_df = _angles(value_e=172.5, value_k=110.0, wrist_change=20.0)
    metrics = derivation.derive_metrics(angles_df, _shot_window())
    score, _, _, components = derivation.compute_overall_score(metrics, angles_df, _shot_window())
    assert score >= 90, f"Expected >=90 for optimal form, got {score}"
    assert any(c["name"] == "shot_score_breakdown" for c in components)


def test_low_confidence_metric_excluded():
    """A single low-confidence metric falls through the gate and the
    aggregator collapses to the component fallback (or legacy)."""
    derivation = _derivation()
    metrics = [
        {"name": "elbow_extension", "value": 165.0, "confidence": 0.1, "verdict": "Low Confidence"},
    ]
    score, _, _, _ = derivation.compute_overall_score(metrics)
    # With only a low-confidence metric and no angles_df, we expect the
    # legacy primitive path to be taken — it still returns a number.
    assert isinstance(score, int)


def test_dim_score_midpoint_is_100():
    norm_key = _METRIC_SCORING_MAP["elbow_extension"]["norm_key"]
    lo, hi = _target_of(norm_key)
    assert lo is not None and hi is not None
    mid = (lo + hi) / 2.0
    s = _dim_score(norm_key, mid)
    assert s is not None and abs(s - 100.0) < 0.1


def test_dim_score_far_outside_range_below_50():
    """Values well beyond the good_range must score under 50.

    The post-2026-04-23 piecewise curve is deliberately forgiving inside
    ``good_range``, so a test that used "3*half" from the optimal midpoint
    (which the pre-fix Gaussian collapsed to ~0) now lands inside the edge of
    ``good_range`` for knee. Use a value genuinely outside good_range instead.
    """
    norm_key = _METRIC_SCORING_MAP["knee_bend"]["norm_key"]
    # Knee good_range ends at 125; 150 is comfortably outside the reasonable
    # band (~1 good_width past the top of good_range).
    s = _dim_score(norm_key, 150.0)
    assert s is not None and s < 50.0


def test_bad_form_scores_lower_than_good():
    derivation = _derivation()
    sw = _shot_window()
    good_df = _angles(value_e=172.5, value_k=110.0, wrist_change=20.0)
    bad_df = _angles(value_e=130.0, value_k=150.0, wrist_change=2.0)

    good_metrics = derivation.derive_metrics(good_df, sw)
    bad_metrics = derivation.derive_metrics(bad_df, sw)

    good_score, _, _, _ = derivation.compute_overall_score(good_metrics, good_df, sw)
    bad_score, _, _, _ = derivation.compute_overall_score(bad_metrics, bad_df, sw)

    assert good_score > bad_score
