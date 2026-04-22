import logging

import numpy as np

logger = logging.getLogger(__name__)


def recommend_drill(
    user_vec,
    user_context,
    drills,
    labels,
    tiers,
    faiss_index,
    bandit,
    weak_areas=None,
    user_level=None,
):
    """Main recommendation function combining FAISS nearest drills + bandit scoring.

    When ``weak_areas`` is provided the result is enriched with a Gemini-generated
    natural-language explanation of why the drill was chosen and how to do it.
    """

    ue = np.array(user_vec, dtype="float32").reshape(1, -1)
    ue = ue / (np.linalg.norm(ue, axis=1, keepdims=True) + 1e-9)

    _, I = faiss_index.search(ue, 10)
    neighbor_ids = I[0]

    ctx = np.array([user_context], dtype="float32")
    expectations = bandit.predict_expectations(ctx)

    best_arm = max(expectations, key=expectations.get)
    best_score = expectations[best_arm]

    cluster, tier = map(int, best_arm.replace("C", "").split("_T"))

    pool = [i for i in neighbor_ids if labels[i] == cluster and tiers[i] == tier]
    pick = int(pool[0]) if pool else int(neighbor_ids[0])

    result = {
        "drill_id": str(drills.loc[pick, "drill_id"]),
        "cluster": int(cluster),
        "tier": int(tier),
        "predicted_score": float(best_score),
    }

    try:
        from ..services.llm import llm_service

        drill_meta = drills.loc[pick].to_dict() if hasattr(drills.loc[pick], "to_dict") else {}
        explanation = llm_service.get_drill_recommendation(
            drill_metadata=drill_meta,
            weak_areas=weak_areas or [],
            user_level=user_level,
        )
        result["explanation"] = {
            "drill_name": explanation.drill_name,
            "why": explanation.why,
            "how": explanation.how,
            "sets_reps": explanation.sets_reps,
        }
    except Exception:
        logger.warning("Drill explanation generation failed", exc_info=True)

    return result
