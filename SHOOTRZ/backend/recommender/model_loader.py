from .drill_clustering import load_drill_embeddings, load_drill_metadata
from .faiss_index import load_faiss_index
from .bandit_model import initialize_bandit

def load_recommender():
    """
    Loads everything required for serving recommendations.
    """
    embeddings = load_drill_embeddings()
    metadata = load_drill_metadata()
    faiss_index = load_faiss_index()

    labels = metadata["cluster"].to_numpy()
    tiers = metadata["tier"].to_numpy()
    arms = [f"C{c}_T{t}" for c, t in zip(labels, tiers)]

    bandit = initialize_bandit(arms)

    return {
        "embeddings": embeddings,
        "metadata": metadata,
        "labels": labels,
        "tiers": tiers,
        "faiss_index": faiss_index,
        "bandit": bandit
    }
