import numpy as np


def faiss_search_neighbors(user_vec, faiss_index, metadata, k: int = 10):
    """
    Run FAISS search (IndexFlatIP on L2-normalized vectors → inner product ≈ cosine similarity).
    Returns one row per neighbor with drill metadata and similarity score.
    """
    ue = np.asarray(user_vec, dtype="float32").reshape(1, -1)
    ue /= np.linalg.norm(ue, axis=1, keepdims=True) + 1e-9

    scores, indices = faiss_index.search(ue, k)
    rows = []
    rank = 1
    for idx, sim in zip(indices[0].tolist(), scores[0].tolist()):
        if idx < 0:
            # Skip invalid entries without advancing the visible rank counter
            continue
        row = metadata.iloc[int(idx)]
        rows.append(
            {
                "rank": rank,
                "drill_index": int(idx),
                "drill_id": str(row["drill_id"]),
                "cluster": int(row["cluster"]),
                "tier": int(row["tier"]),
                "inner_product": float(sim),
            }
        )
        rank += 1
    return rows


def linucb_expectation_scores(bandit, user_context):
    """LinUCB expected reward per arm for the given context vector."""
    ctx = np.asarray([user_context], dtype="float32")
    return bandit.predict_expectations(ctx)


def recommend_drill(user_vec, user_context, drills, labels, tiers, faiss_index, bandit):
    """
    Recommend a drill using FAISS + LinUCB.
    """

    # Normalize user embedding
    ue = np.asarray(user_vec, dtype="float32").reshape(1, -1)
    ue /= (np.linalg.norm(ue, axis=1, keepdims=True) + 1e-9)

    # FAISS search
    _, indices = faiss_index.search(ue, 10)
    neighbor_ids = indices[0]

    # Bandit expected rewards (dict: arm -> score)
    expectations = linucb_expectation_scores(bandit, user_context)
    if not expectations:
        raise RuntimeError("Bandit returned empty expectations")

    best_arm = max(expectations, key=expectations.get)
    best_score = expectations[best_arm]

    # Parse arm: C{cluster}_T{tier}
    target_cluster, target_tier = map(int, best_arm.replace("C", "").split("_T"))

    # Filter FAISS neighbors by the bandit's chosen cluster & tier
    pool = [
        i for i in neighbor_ids
        if labels[i] == target_cluster and tiers[i] == target_tier
    ]

    # Choose drill index:
    # - If pool is non-empty, we respect the bandit's arm (matching cluster/tier).
    # - If pool is empty, we fall back to the nearest FAISS neighbor and
    #   treat THAT drill's cluster/tier as the effective arm for this recommendation.
    faiss_fallback = not pool
    if pool:
        pick = int(pool[0])
        effective_arm = best_arm
    else:
        pick = int(neighbor_ids[0])
        drill_cluster = int(drills.loc[pick, "cluster"])
        drill_tier = int(drills.loc[pick, "tier"])
        effective_arm = f"C{drill_cluster}_T{drill_tier}"

    return {
        "drill_id": str(drills.loc[pick, "drill_id"]),
        "cluster": int(drills.loc[pick, "cluster"]),
        "tier": int(drills.loc[pick, "tier"]),
        "predicted_score": float(best_score),
        # Arm actually associated with the returned drill (always consistent with cluster/tier)
        "bandit_arm": effective_arm,
        # Original bandit choice before FAISS alignment (for debugging/analysis)
        "original_bandit_arm": best_arm,
        # True when we had to ignore the original arm because no FAISS neighbor matched it
        "faiss_fallback": faiss_fallback,
    }
