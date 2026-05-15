"""
Regression tests for backend/recommender/recommend_service.py.

Run from SHOOTRZ/:
    python -m pytest backend/recommender/ -v
"""
import numpy as np
import pytest

from backend.recommender.recommend_service import recommend_drill


def test_recommend_drill_accepts_weak_areas_and_user_level(dummy_recommender):
    """Regression: weak_areas and user_level must not raise TypeError."""
    result = recommend_drill(
        user_vec=np.random.rand(64).tolist(),
        user_context=np.random.rand(8).tolist(),
        drills=dummy_recommender["metadata"],
        labels=dummy_recommender["labels"],
        tiers=dummy_recommender["tiers"],
        faiss_index=dummy_recommender["faiss_index"],
        bandit=dummy_recommender["bandit"],
        weak_areas=["elbow"],
        user_level="beginner",
    )
    assert "drill_id" in result


def test_recommend_drill_works_without_optional_kwargs(dummy_recommender):
    """Backward-compat: calling without the new kwargs must still work."""
    result = recommend_drill(
        user_vec=np.random.rand(64).tolist(),
        user_context=np.random.rand(8).tolist(),
        drills=dummy_recommender["metadata"],
        labels=dummy_recommender["labels"],
        tiers=dummy_recommender["tiers"],
        faiss_index=dummy_recommender["faiss_index"],
        bandit=dummy_recommender["bandit"],
    )
    assert "drill_id" in result


def test_recommend_drill_returns_expected_shape(dummy_recommender):
    """Result must include all documented top-level keys."""
    result = recommend_drill(
        user_vec=np.random.rand(64).tolist(),
        user_context=np.random.rand(8).tolist(),
        drills=dummy_recommender["metadata"],
        labels=dummy_recommender["labels"],
        tiers=dummy_recommender["tiers"],
        faiss_index=dummy_recommender["faiss_index"],
        bandit=dummy_recommender["bandit"],
        weak_areas=None,
        user_level=None,
    )
    for key in ("drill_id", "cluster", "tier", "predicted_score", "bandit_arm"):
        assert key in result, f"Missing key: {key}"
