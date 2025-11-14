import numpy as np

def recommend_drill(user_vec, user_context, drills, labels, tiers, faiss_index, bandit):
    """
    Main recommendation function combining FAISS nearest drills + bandit scoring.
    """

    # Normalize embedding
    ue = np.array(user_vec, dtype="float32").reshape(1, -1)
    ue = ue / (np.linalg.norm(ue, axis=1, keepdims=True) + 1e-9)

    # FAISS top-10 nearest drills
    _, I = faiss_index.search(ue, 10)
    neighbor_ids = I[0]

    # Bandit prediction → expected reward for each arm
    ctx = np.array([user_context], dtype="float32")
    expectations = bandit.predict_expectations(ctx)

    # Best arm (C#_T#)
    best_arm = max(expectations, key=expectations.get)
    best_score = expectations[best_arm]

    # Parse arm label
    cluster, tier = map(int, best_arm.replace("C", "").split("_T"))

    # Pick a drill that fits cluster & tier
    pool = [i for i in neighbor_ids if labels[i] == cluster and tiers[i] == tier]
    pick = int(pool[0]) if pool else int(neighbor_ids[0])

    return {
        "drill_id": str(drills.loc[pick, "drill_id"]),
        "cluster": int(cluster),
        "tier": int(tier),
        "predicted_score": float(best_score)
    }
