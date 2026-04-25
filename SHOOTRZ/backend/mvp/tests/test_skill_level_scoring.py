"""
Tests for skill-level-aware metric scoring (Task 16).

Verifies that beginner, intermediate, and advanced tiers produce meaningfully
different scores for the same measurement, with beginner accepting wider ranges
and advanced applying the tightest standards.
"""

import sys
from pathlib import Path

import pytest

# Ensure the backend package root is on sys.path so tests can be run from
# SHOOTRZ/ with: python -m pytest backend/mvp/tests/test_skill_level_scoring.py
_backend_root = Path(__file__).parent.parent.parent
if str(_backend_root) not in sys.path:
    sys.path.insert(0, str(_backend_root))

from mvp.core.metrics import MetricsDerivation


def test_beginner_95_degree_knee_is_good():
    """95° knee flexion should score >= 70 for a beginner (wide acceptance band)."""
    md = MetricsDerivation(config={}, skill_level="beginner")
    score = md._dim_score("knee_flexion", 95.0)
    assert score is not None
    assert score >= 70, f"Beginner 95° knee should score >= 70, got {score}"


def test_advanced_95_degree_knee_is_at_boundary():
    """95° knee flexion should score <= 70 for an advanced player (tight target [100, 120]).

    95° sits exactly at the edge of the derived good_range for the advanced tier,
    so the score is at or below 70 — indicating the measurement just barely meets
    (or misses) the stricter standard.
    """
    md = MetricsDerivation(config={}, skill_level="advanced")
    score = md._dim_score("knee_flexion", 95.0)
    assert score is not None
    assert score <= 70, f"Advanced 95° knee should score <= 70, got {score}"


def test_intermediate_is_default():
    """MetricsDerivation with no skill_level kwarg defaults to 'intermediate'."""
    md = MetricsDerivation(config={})
    assert md.skill_level == "intermediate"
    # A mid-range value for knee_flexion should produce a valid score.
    score = md._dim_score("knee_flexion", 110.0)
    assert score is not None
    assert 0 <= score <= 100


def test_beginner_scores_higher_than_advanced_for_borderline_value():
    """For a value just outside the advanced target, beginner must score strictly higher."""
    md_beg = MetricsDerivation(config={}, skill_level="beginner")
    md_adv = MetricsDerivation(config={}, skill_level="advanced")
    score_beg = md_beg._dim_score("knee_flexion", 95.0)
    score_adv = md_adv._dim_score("knee_flexion", 95.0)
    assert score_beg is not None and score_adv is not None
    assert score_beg > score_adv, (
        f"Beginner ({score_beg}) should score higher than advanced ({score_adv}) "
        "for a borderline knee_flexion value"
    )


def test_perfect_value_scores_100_for_all_tiers():
    """A value inside the target range for every tier should score 100 regardless of tier."""
    for skill in ("beginner", "intermediate", "advanced"):
        md = MetricsDerivation(config={}, skill_level=skill)
        # 110° is inside all three knee_flexion target_ranges.
        score = md._dim_score("knee_flexion", 110.0)
        assert score == 100.0, f"Expected 100 for {skill}, got {score}"


def test_unknown_skill_level_falls_back_to_base():
    """An unrecognised skill_level falls back to the base target_range gracefully."""
    md = MetricsDerivation(config={}, skill_level="elite")
    score = md._dim_score("knee_flexion", 110.0)
    # Should still return a valid score, not None.
    assert score is not None
    assert 0 <= score <= 100
