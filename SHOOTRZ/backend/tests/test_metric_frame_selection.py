"""Unit coverage for the peak-in-window metric selection introduced 2026-04-23.

Previously every primitive averaged over a fixed +/- 3 frame window and emitted
NaN whenever a single frame's joint confidence dropped. The peak-search
rewrite must:

  * Find the elbow peak even when it sits a few frames away from release_frame.
  * Ignore rows whose per-joint confidence falls below ``MIN_JOINT_CONF_FOR_METRIC``.
  * Gracefully fall back to ``Low Confidence`` when no row in the window clears
    the confidence gate.
  * Populate ``selected_frame`` with the exact source frame picked.
"""
from __future__ import annotations

import pandas as pd

from backend.mvp.core.metrics import (
    MIN_JOINT_CONF_FOR_METRIC,
    MetricsDerivation,
    _dim_score,
)


def _angles_df(rows):
    """Build a minimal angles dataframe from ``(frame_id, elbow, knee, wrist, conf)`` tuples."""
    return pd.DataFrame(
        [
            {
                "frame_id": r[0],
                "timestamp": r[0] / 30.0,
                "elbow_angle": r[1],
                "knee_angle": r[2],
                "wrist_angle": r[3],
                "confidence_elbow": r[4],
                "confidence_knee": r[4],
                "confidence_wrist": r[4],
            }
            for r in rows
        ]
    )


def _derivation() -> MetricsDerivation:
    return MetricsDerivation({"metrics": {}, "scoring": {"low_confidence_threshold": 0.5}})


def test_elbow_peak_picked_even_when_release_frame_is_off_by_a_few_frames():
    # Release_frame=45 but peak extension lives at frame 50.
    rows = [(f, 100 + (f - 40) * 3, 100, 10, 0.9) for f in range(35, 55)]
    # Guarantee frame 50 has the explicit peak (170 deg).
    rows = [(r[0], 170.0 if r[0] == 50 else r[1], r[2], r[3], r[4]) for r in rows]
    df = _angles_df(rows)
    deriv = _derivation()

    m = deriv._compute_elbow_extension(df, {"release_frame": 45})

    assert m["verdict"] != "Low Confidence", m
    assert m["selected_frame"] == 50
    assert m["value"] == 170.0
    assert m["confidence"] >= MIN_JOINT_CONF_FOR_METRIC


def test_elbow_ignores_low_confidence_rows_even_if_angle_is_higher():
    # Frame 50 has an attractive 180 deg angle but confidence=0.2 -- must be
    # skipped. Best eligible row at frame 48 at 165 deg and conf 0.8.
    rows = []
    for f in range(35, 55):
        if f == 50:
            rows.append((f, 180.0, 100, 10, 0.2))
        elif f == 48:
            rows.append((f, 165.0, 100, 10, 0.8))
        else:
            rows.append((f, 100.0, 100, 10, 0.8))
    df = _angles_df(rows)
    deriv = _derivation()

    m = deriv._compute_elbow_extension(df, {"release_frame": 45})

    assert m["selected_frame"] == 48
    assert m["value"] == 165.0


def test_knee_bend_picks_minimum_angle_at_crouch():
    # Crouch frame is 20 but the real min is at frame 22.
    rows = [(f, 150, 140, 10, 0.9) for f in range(10, 30)]
    rows = [(r[0], r[1], 95.0 if r[0] == 22 else r[2], r[3], r[4]) for r in rows]
    df = _angles_df(rows)
    deriv = _derivation()

    m = deriv._compute_knee_bend(df, {"crouch_frame": 20})

    assert m["selected_frame"] == 22
    assert m["value"] == 95.0
    assert m["verdict"] != "Low Confidence"


def test_all_rows_low_confidence_yields_low_confidence_metric():
    rows = [(f, 170.0, 100, 10, 0.2) for f in range(35, 55)]  # conf below gate
    df = _angles_df(rows)
    deriv = _derivation()

    m = deriv._compute_elbow_extension(df, {"release_frame": 45})

    assert m["verdict"] == "Low Confidence"
    assert m["selected_frame"] is None
    assert m["unit"] == "N/A"


def test_dim_score_is_forgiving_for_slightly_bent_elbow():
    """Pre-2026-04-23 the Gaussian-shaped ``_dim_score`` would collapse to
    ~3/100 when an elbow was measured at 152 deg vs a target of 165-180 deg.

    The new piecewise scoring must recognise that 152 deg is inside the
    ``good_range`` [150, 175] and therefore deserves a sub-score >= 60 -
    closer to how a coach would grade "close but not quite".
    """
    score = _dim_score("elbow_flexion_release", 152.0)
    assert score is not None
    assert score >= 60.0, (
        f"Expected a forgiving elbow score >= 60 for 152 deg (in good_range), got {score:.1f}"
    )


def test_dim_score_still_low_for_far_out_values():
    """A knee of 32 deg vs a 100-120 target is genuinely poor; the softer
    scoring still reflects that honestly (<25/100)."""
    score = _dim_score("knee_flexion", 32.0)
    assert score is not None
    assert score <= 25.0, f"Knee 32 deg should stay honestly low, got {score:.1f}"


def test_dim_score_returns_100_in_optimal_range():
    """Textbook-ideal values remain 100/100."""
    score = _dim_score("elbow_flexion_release", 172.5)
    assert score == 100.0


def test_wrist_followthrough_uses_release_and_end_windows():
    rows = []
    for f in range(45, 90):
        rows.append((f, 170.0, 100, 20.0 if f < 60 else 45.0, 0.8))
    df = _angles_df(rows)
    deriv = _derivation()

    m = deriv._compute_wrist_followthrough(df, {"release_frame": 50, "end_frame": 80})

    assert m["verdict"] != "Low Confidence"
    assert m["value"] >= 10.0  # end - release change is measurable
    assert m["selected_frame"] is not None
