# recommender/dummy_data.py
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

# Human-readable drill families (for realism / debugging)
CLUSTERS = {
    0: "Form Shooting",
    1: "Catch & Shoot",
    2: "Off-Dribble",
    3: "Stepback / Advanced"
}

def generate_dummy_storage(
    storage_dir: Path,
    n_drills: int = 60,
    dim: int = 64,
    seed: int = 42
):
    """
    Generates realistic basketball-like dummy data:
    - drill_embeddings.npy
    - drills_metadata.csv
    - faiss_index.bin
    """
    import faiss

    storage_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)

    # -------------------------
    # 1️⃣ Realistic cluster distribution
    # -------------------------
    cluster_probs = {
        0: 0.35,  # Form Shooting (most common)
        1: 0.30,  # Catch & Shoot
        2: 0.22,  # Off-Dribble
        3: 0.13   # Stepback (rare)
    }

    cluster_ids = list(cluster_probs.keys())
    cluster_weights = list(cluster_probs.values())

    clusters = rng.choice(
        cluster_ids,
        size=n_drills,
        p=cluster_weights
    )

    # -------------------------
    # 2️⃣ Realistic tier distribution (difficulty)
    # -------------------------
    def sample_tier(cluster):
        """
        Harder clusters skew towards higher tiers,
        but advanced drills are always rarer.
        """
        if cluster == 0:      # Form shooting
            return rng.choice([1, 2], p=[0.75, 0.25])
        elif cluster == 1:    # Catch & shoot
            return rng.choice([1, 2, 3], p=[0.45, 0.40, 0.15])
        elif cluster == 2:    # Off-dribble
            return rng.choice([2, 3], p=[0.55, 0.45])
        else:                 # Stepback
            return rng.choice([3], p=[1.0])

    tiers = np.array([sample_tier(c) for c in clusters])

    # -------------------------
    # 3️⃣ Generate structured embeddings
    # -------------------------
    # Each cluster has a "movement centroid"
    cluster_centroids = {
        c: rng.normal(0, 1, size=dim)
        for c in CLUSTERS
    }

    embeddings = np.zeros((n_drills, dim), dtype="float32")

    for i, (c, t) in enumerate(zip(clusters, tiers)):
        base = cluster_centroids[c]

        # Noise increases with tier (harder drills = more variation)
        noise_scale = 0.15 + (t * 0.1)

        embeddings[i] = base + rng.normal(0, noise_scale, size=dim)

    # Normalize for cosine similarity
    embeddings /= (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9)

    # -------------------------
    # 4️⃣ Metadata
    # -------------------------
    metadata = pd.DataFrame({
        "drill_id": [f"D{i:03d}" for i in range(n_drills)],
        "cluster": clusters,
        "tier": tiers,
        "family": [CLUSTERS[c] for c in clusters]
    })

    # Save files
    np.save(storage_dir / "drill_embeddings.npy", embeddings)
    metadata.to_csv(storage_dir / "drills_metadata.csv", index=False)

    # -------------------------
    # 5️⃣ FAISS index (cosine similarity)
    # -------------------------
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, str(storage_dir / "faiss_index.bin"))

    logger.info("[OK] Realistic basketball dummy data generated")
    logger.info("Dummy data family distribution:\n%s", metadata["family"].value_counts())
    logger.info("Dummy data tier distribution:\n%s", metadata["tier"].value_counts())

    return embeddings, metadata
