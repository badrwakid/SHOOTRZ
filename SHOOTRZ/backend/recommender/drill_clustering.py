import numpy as np
import pandas as pd
from pathlib import Path

# Get the directory containing this file, then navigate to storage
_BASE_DIR = Path(__file__).parent.parent
EMBED_PATH = _BASE_DIR / "storage" / "drill_embeddings.npy"
META_PATH = _BASE_DIR / "storage" / "drills_metadata.csv"

def load_drill_metadata():
    if not META_PATH.exists():
        raise FileNotFoundError(f"Metadata file missing: {META_PATH}")

    drills = pd.read_csv(META_PATH)
    
    if "cluster" not in drills.columns or "tier" not in drills.columns:
        raise ValueError("drills_metadata.csv must contain 'cluster' and 'tier' columns")

    return drills

def load_drill_embeddings():
    if not EMBED_PATH.exists():
        raise FileNotFoundError(f"Embedding file missing: {EMBED_PATH}")

    emb = np.load(EMBED_PATH)
    return emb.astype("float32")
