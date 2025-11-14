import faiss
import numpy as np
from pathlib import Path

# Get the directory containing this file, then navigate to storage
_BASE_DIR = Path(__file__).parent.parent
FAISS_PATH = _BASE_DIR / "storage" / "faiss_index.bin"

def load_faiss_index():
    if not FAISS_PATH.exists():
        raise FileNotFoundError(f"FAISS index not found: {FAISS_PATH}")
    index = faiss.read_index(str(FAISS_PATH))
    return index