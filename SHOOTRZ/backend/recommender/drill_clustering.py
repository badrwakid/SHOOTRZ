# recommender/drill_clustering.py
import logging
import numpy as np
import pandas as pd
from pathlib import Path

logger = logging.getLogger(__name__)

_BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = _BASE_DIR / "storage"

EMBED_PATH = STORAGE_DIR / "drill_embeddings.npy"
META_PATH = STORAGE_DIR / "drills_metadata.csv"
FAISS_PATH = STORAGE_DIR / "faiss_index.bin"

# Embedding dimension — must match whatever was used to build the index.
_DIM = 64


def _build_embeddings_from_metadata(drills: pd.DataFrame) -> np.ndarray:
    """
    Build deterministic, cluster-aware embeddings directly from the tracked
    drills_metadata.csv.  Each drill gets a vector whose centroid is shared
    within its cluster/tier group so that semantically similar drills end up
    near each other in the FAISS index.  Uses a fixed seed so the output is
    identical on every fresh clone.
    """
    import faiss

    n = len(drills)
    rng = np.random.default_rng(42)

    n_clusters = drills["cluster"].nunique()
    cluster_centroids = {
        c: rng.standard_normal(_DIM).astype("float32")
        for c in range(n_clusters)
    }

    embeddings = np.zeros((n, _DIM), dtype="float32")
    for i, row in drills.iterrows():
        c = int(row["cluster"])
        t = int(row["tier"])
        base = cluster_centroids.get(c, rng.standard_normal(_DIM).astype("float32"))
        noise_scale = 0.15 + t * 0.1
        embeddings[i] = base + rng.standard_normal(_DIM).astype("float32") * noise_scale

    # L2-normalise for cosine similarity via IndexFlatIP
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-9
    embeddings /= norms

    np.save(EMBED_PATH, embeddings)

    index = faiss.IndexFlatIP(_DIM)
    index.add(embeddings)
    faiss.write_index(index, str(FAISS_PATH))

    logger.info(
        "Built FAISS index from drills_metadata.csv: %d drills, dim=%d", n, _DIM
    )
    return embeddings


def _ensure_artifacts_exist(drills: pd.DataFrame) -> None:
    """
    Rebuild the binary artifacts (embeddings + FAISS index) from the tracked
    metadata CSV if they are missing or corrupt.  The metadata CSV itself is
    never overwritten here — it is the source of truth.
    """
    if EMBED_PATH.exists() and FAISS_PATH.exists():
        return
    logger.warning(
        "Recommender artifacts missing (%s, %s) — rebuilding from %s",
        EMBED_PATH.name, FAISS_PATH.name, META_PATH.name,
    )
    _build_embeddings_from_metadata(drills)


def load_drill_metadata() -> pd.DataFrame:
    if not META_PATH.exists():
        raise FileNotFoundError(
            f"drills_metadata.csv not found at {META_PATH}. "
            "Ensure the file is present in backend/storage/."
        )
    drills = pd.read_csv(META_PATH)
    required = {"drill_id", "cluster", "tier"}
    if not required.issubset(drills.columns):
        raise ValueError(
            f"drills_metadata.csv must contain columns: {required}. "
            f"Found: {set(drills.columns)}"
        )
    return drills


def load_drill_embeddings() -> np.ndarray:
    drills = load_drill_metadata()
    _ensure_artifacts_exist(drills)
    try:
        emb = np.load(EMBED_PATH, allow_pickle=False)
        if emb.ndim != 2 or emb.size == 0:
            raise ValueError("Corrupt drill_embeddings array — rebuilding")
        return emb.astype("float32")
    except (OSError, ValueError, EOFError) as exc:
        logger.warning("Reloading embeddings after error: %s", exc)
        return _build_embeddings_from_metadata(drills)
