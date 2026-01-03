# recommender/run_dummy_test.py
import numpy as np
from .model_loader import load_recommender
from .recommender_service import recommend_drill

def main():
    rec = load_recommender()

    # Dummy user embedding matches embeddings dim
    dim = rec["embeddings"].shape[1]
    user_vec = np.random.randn(dim).astype("float32")

    # Dummy user context: [skill, fatigue, accuracy, form_error, minutes]
    user_context = [3, 0.5, 0.7, 0.3, 15]

    result = recommend_drill(
        user_vec=user_vec,
        user_context=user_context,
        drills=rec["metadata"],
        labels=rec["labels"],
        tiers=rec["tiers"],
        faiss_index=rec["faiss_index"],
        bandit=rec["bandit"],
    )

    print("✅ Recommendation Result:")
    print(result)

if __name__ == "__main__":
    main()
