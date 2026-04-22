# recommender/drill_clustering.py
import numpy as np
import pandas as pd
from pathlib import Path
from .dummy_data import generate_dummy_storage

_BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = _BASE_DIR / "storage"

EMBED_PATH = STORAGE_DIR / "drill_embeddings.npy"
META_PATH = STORAGE_DIR / "drills_metadata.csv"
FAISS_PATH = STORAGE_DIR / "faiss_index.bin"

def _ensure_storage_exists():
    """
    If any storage artifact is missing, generate all dummy artifacts once.
    """
    if not (EMBED_PATH.exists() and META_PATH.exists() and FAISS_PATH.exists()):
        generate_dummy_storage(STORAGE_DIR)

def load_drill_metadata():
    _ensure_storage_exists()

    drills = pd.read_csv(META_PATH)
    required = {"drill_id", "cluster", "tier"}
    if not required.issubset(drills.columns):
        raise ValueError(f"drills_metadata.csv must contain columns: {required}")

    return drills

def _load_embeddings_or_regenerate():
    emb = np.load(EMBED_PATH, allow_pickle=False)
    if emb.ndim != 2 or emb.size == 0:
        raise ValueError("Invalid drill_embeddings array")
    return emb.astype("float32")


def load_drill_embeddings():
    _ensure_storage_exists()

    try:
        return _load_embeddings_or_regenerate()
    except (OSError, ValueError, EOFError):
        generate_dummy_storage(STORAGE_DIR)
        return _load_embeddings_or_regenerate()
