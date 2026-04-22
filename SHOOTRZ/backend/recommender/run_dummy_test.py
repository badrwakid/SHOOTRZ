# recommender/run_dummy_test.py
import numpy as np

from .model_loader import load_recommender
from .recommend_service import (
    faiss_search_neighbors,
    linucb_expectation_scores,
    recommend_drill,
)


def _print_drill_embeddings(embeddings, metadata, preview: int = 3):
    print("\n--- Drill embeddings ---")
    print(f"  shape: {embeddings.shape}  dtype: {embeddings.dtype}")
    norms = np.linalg.norm(embeddings, axis=1)
    print(
        f"  row L2 norm - min: {norms.min():.6f}  max: {norms.max():.6f}  mean: {norms.mean():.6f}"
    )
    print(f"  first {preview} drills (drill_id, cluster, tier, first 8 dims):")
    for i in range(min(preview, len(metadata))):
        row = metadata.iloc[i]
        snippet = embeddings[i, :8]
        print(
            f"    {row['drill_id']}  cluster={row['cluster']}  tier={row['tier']}  "
            f"vec[:8]={np.array2string(snippet, precision=4, floatmode='fixed')}"
        )


def _print_faiss_neighbors(neighbors):
    print("\n--- FAISS top neighbors (inner product on normalized vectors) ---")
    for n in neighbors:
        print(
            f"  #{n['rank']}  {n['drill_id']}  idx={n['drill_index']}  "
            f"cluster={n['cluster']}  tier={n['tier']}  score={n['inner_product']:.6f}"
        )


def _print_linucb(expectations):
    print("\n--- LinUCB (expected reward per arm) ---")
    sorted_arms = sorted(expectations.items(), key=lambda x: x[1], reverse=True)
    for arm, score in sorted_arms:
        print(f"  {arm}: {score:.6f}")
    if sorted_arms:
        best = sorted_arms[0]
        print(f"  -> best arm: {best[0]}  (expected reward {best[1]:.6f})")


def main():
    rec = load_recommender()
    embeddings = rec["embeddings"]
    metadata = rec["metadata"]
    faiss_index = rec["faiss_index"]
    bandit = rec["bandit"]

    # Dummy user embedding matches embeddings dim
    dim = embeddings.shape[1]
    user_vec = np.random.default_rng(42).standard_normal(dim).astype("float32")

    # Dummy user context: [skill, fatigue, accuracy, form_error, minutes]
    user_context = [3, 0.5, 0.7, 0.3, 15]

    _print_drill_embeddings(embeddings, metadata, preview=3)

    neighbors = faiss_search_neighbors(
        user_vec, faiss_index, metadata, k=10
    )
    _print_faiss_neighbors(neighbors)

    expectations = linucb_expectation_scores(bandit, user_context)
    _print_linucb(expectations)

    result = recommend_drill(
        user_vec=user_vec,
        user_context=user_context,
        drills=metadata,
        labels=rec["labels"],
        tiers=rec["tiers"],
        faiss_index=faiss_index,
        bandit=bandit,
    )

    print("\n--- Final recommendation (FAISS shortlist + LinUCB arm filter) ---")
    print(f"  {result}")


if __name__ == "__main__":
    main()
