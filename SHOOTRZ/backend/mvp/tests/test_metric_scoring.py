"""
Unit tests for metric scoring and verdict assignment.
"""

import pytest
import pandas as pd
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from mvp.core.metrics import MetricsDerivation


class TestMetricScoring:
    """Test verdict assignment logic."""
    
    def setup_method(self):
        """Setup test configuration."""
        self.config = {
            "metrics": {
                "elbow_extension": {
                    "good_range": [150, 175],
                    "optimal_range": [160, 170],
                    "release_window": 3
                },
                "knee_bend": {
                    "good_range": [85, 120],
                    "optimal_range": [95, 110]
                },
                "wrist_follow_through": {
                    "good_range": [10, 30],
                    "optimal_range": [15, 25]
                }
            },
            "scoring": {
                "weights": {"elbow": 0.40, "knee": 0.30, "wrist": 0.30},
                "confidence_penalty": 0.5,
                "low_confidence_threshold": 0.4
            }
        }
        self.derivation = MetricsDerivation(self.config)
    
    def test_verdict_good_in_optimal_range(self):
        """Test that optimal values get 'Good' verdict."""
        verdict = self.derivation._assign_verdict(
            value=165.0,  # In optimal range [160, 170]
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.9
        )
        assert verdict == "Good"
    
    def test_verdict_good_in_good_range(self):
        """Test that good range values get 'Good' verdict."""
        verdict = self.derivation._assign_verdict(
            value=155.0,  # In good range but not optimal
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.9
        )
        assert verdict == "Good"
    
    def test_verdict_needs_work_outside_range(self):
        """Test that values outside range get 'Needs Work'."""
        verdict = self.derivation._assign_verdict(
            value=140.0,  # Outside good range
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.9
        )
        assert verdict == "Needs Work"
    
    def test_verdict_low_confidence(self):
        """Test that low confidence returns 'Low Confidence'."""
        verdict = self.derivation._assign_verdict(
            value=165.0,
            good_range=[150, 175],
            optimal_range=[160, 170],
            confidence=0.2  # Below threshold
        )
        assert verdict == "Low Confidence"
    
    def test_score_range(self):
        """Test that overall score is in [0, 100] range."""
        # Create synthetic angles data
        angles_df = pd.DataFrame({
            "frame_id": list(range(60)),
            "timestamp": [i * 0.033 for i in range(60)],
            "knee_angle": [100.0] * 60,
            "elbow_angle": [165.0] * 60,
            "wrist_angle": [85.0] * 60,
            "confidence_knee": [0.9] * 60,
            "confidence_elbow": [0.9] * 60,
            "confidence_wrist": [0.9] * 60,
        })
        
        shot_window = {
            "start_frame": 10,
            "crouch_frame": 30,
            "release_frame": 40,
            "end_frame": 50
        }
        
        metrics = self.derivation.derive_metrics(angles_df, shot_window)
        score, feedback, _, _ = self.derivation.compute_overall_score(metrics)
        
        assert 0 <= score <= 100, f"Score {score} outside [0, 100] range"
    
    def test_good_form_high_score(self):
        """Good form — values at normative midpoints — produces a high score.

        The post-refactor aggregator centres sub-scores on the RESEARCH-BACKED
        midpoint (``elbow_flexion_release`` target [165,180] midpoint 172.5,
        ``knee_flexion`` [100,120] midpoint 110). The old test sat at 165/105
        which is 1+ sigma off — legitimately not "optimal" under the new
        scoring. We bump to the normative midpoints and add a real wrist
        follow-through delta (previously masked as 0 by a framing bug).
        """
        n = 60
        wrist = [80.0] * 42 + [100.0] * (n - 42)
        angles_df = pd.DataFrame({
            "frame_id": list(range(n)),
            "timestamp": [i * 0.033 for i in range(n)],
            "knee_angle": [110.0] * n,
            "elbow_angle": [172.5] * n,
            "wrist_angle": wrist,
            "confidence_knee": [0.95] * n,
            "confidence_elbow": [0.95] * n,
            "confidence_wrist": [0.95] * n,
        })

        shot_window = {
            "start_frame": 10,
            "crouch_frame": 30,
            "release_frame": 40,
            "end_frame": 50
        }
        
        metrics = self.derivation.derive_metrics(angles_df, shot_window)
        score, feedback, bullets, components = self.derivation.compute_overall_score(
            metrics,
            angles_df,
            shot_window,
        )

        # Optimal primitives should produce a high geomean score.
        assert score >= 80, f"Expected score >= 80 for optimal form, got {score}"
        assert isinstance(bullets, list)
        # Aggregator now appends a synthetic `shot_score_breakdown` entry when
        # breakdown metrics are present, so the list grows by ONE.
        assert len(components) in (4, 5)
        component_names = {c["name"] for c in components}
        assert {"loading_quality", "release_mechanics", "follow_through_control", "balance_stability"}.issubset(
            component_names
        )

    def test_feedback_changes_when_metrics_change(self):
        """Feedback should differ when quality degrades."""
        good_df = pd.DataFrame({
            "frame_id": list(range(50)),
            "timestamp": [i * 0.033 for i in range(50)],
            "knee_angle": [105.0] * 50,
            "elbow_angle": [165.0] * 50,
            "wrist_angle": [80.0] * 25 + [100.0] * 25,
            "confidence_knee": [0.95] * 50,
            "confidence_elbow": [0.95] * 50,
            "confidence_wrist": [0.95] * 50,
        })
        bad_df = pd.DataFrame({
            "frame_id": list(range(50)),
            "timestamp": [i * 0.033 for i in range(50)],
            "knee_angle": [135.0] * 50,
            "elbow_angle": [135.0] * 50,
            "wrist_angle": [88.0] * 50,
            "confidence_knee": [0.95] * 50,
            "confidence_elbow": [0.95] * 50,
            "confidence_wrist": [0.95] * 50,
        })
        shot_window = {"start_frame": 5, "crouch_frame": 20, "release_frame": 30, "end_frame": 40}

        good_metrics = self.derivation.derive_metrics(good_df, shot_window)
        bad_metrics = self.derivation.derive_metrics(bad_df, shot_window)
        good_score, good_feedback, _, _ = self.derivation.compute_overall_score(
            good_metrics, good_df, shot_window
        )
        bad_score, bad_feedback, _, _ = self.derivation.compute_overall_score(
            bad_metrics, bad_df, shot_window
        )

        assert good_score > bad_score
        assert good_feedback != bad_feedback


if __name__ == "__main__":
    pytest.main([__file__, "-v"])




