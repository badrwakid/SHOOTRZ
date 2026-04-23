"""
Pytest fixtures for backend/recommender/ tests.

Uses a fully in-memory mock fixture (Option 2 from the plan) so that no
filesystem access, no FAISS binary, and no network are needed.  The mock
faiss_index satisfies the exact interface that recommend_drill calls:

    scores, indices = faiss_index.search(query_vec, k)

where indices[0] is an array of non-negative int drill indices.
"""
# run_dummy_test.py is a dev/integration script (no test_ functions).
# It uses relative imports that break pytest collection when running the
# recommender/ directory directly, so we exclude it from discovery.
collect_ignore = ["run_dummy_test.py"]
import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def dummy_recommender():
    """
    Minimal in-memory recommender components for unit-testing recommend_drill
    without touching the filesystem or importing faiss.

    Constructs:
    - 8 drills across 2 clusters (C0, C1) and 2 tiers (T1, T2), ensuring
      every combination (C0_T1, C0_T2, C1_T1, C1_T2) is present.
    - A mock faiss_index whose .search() returns stable neighbour indices.
    - labels / tiers numpy arrays aligned to the metadata DataFrame.
    - A mock bandit whose predict_expectations returns a deterministic dict
      so the real recommend_drill body completes without TypeError.
    """
    n_drills = 8

    # Two drills per (cluster, tier) combination
    clusters = [0, 0, 0, 0, 1, 1, 1, 1]
    tiers    = [1, 1, 2, 2, 1, 1, 2, 2]

    metadata = pd.DataFrame({
        "drill_id": [f"D{i:03d}" for i in range(n_drills)],
        "cluster":  clusters,
        "tier":     tiers,
    })

    labels    = np.array(clusters)
    tiers_arr = np.array(tiers)

    # Mock FAISS index: search() returns (scores, indices) as numpy arrays.
    # Return the first 8 drill indices (all valid, none are -1).
    neighbour_indices = np.array([[0, 1, 2, 3, 4, 5, 6, 7]], dtype="int64")
    neighbour_scores  = np.ones((1, n_drills), dtype="float32")

    faiss_index = MagicMock(name="MockFaissIndex")
    faiss_index.search.return_value = (neighbour_scores, neighbour_indices)

    # Mock bandit: C0_T1 is highest, so drills 0/1 form the match pool.
    bandit = MagicMock(name="MockBandit")
    bandit.predict_expectations.return_value = {
        "C0_T1": 0.9,
        "C0_T2": 0.6,
        "C1_T1": 0.5,
        "C1_T2": 0.4,
    }

    return {
        "metadata":   metadata,
        "labels":     labels,
        "tiers":      tiers_arr,
        "faiss_index": faiss_index,
        "bandit":     bandit,
    }
