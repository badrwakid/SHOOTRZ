import numpy as np

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

    # Context must be 2D
    ctx = np.asarray([user_context], dtype="float32")

    # Bandit expected rewards (dict: arm -> score)
    expectations = bandit.predict_expectations(ctx)
    if not expectations:
        raise RuntimeError("Bandit returned empty expectations")

    best_arm = max(expectations, key=expectations.get)
    best_score = expectations[best_arm]

    # Parse arm: C{cluster}_T{tier}
    cluster, tier = map(int, best_arm.replace("C", "").split("_T"))

    # Filter FAISS neighbors by cluster & tier
    pool = [
        i for i in neighbor_ids
        if labels[i] == cluster and tiers[i] == tier
    ]

    # Fallback logic
    pick = int(pool[0]) if pool else int(neighbor_ids[0])

    return {
        "drill_id": str(drills.loc[pick, "drill_id"]),
        "cluster": cluster,
        "tier": tier,
        "predicted_score": float(best_score)
    }
