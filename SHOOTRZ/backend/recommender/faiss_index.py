# recommender/faiss_index.py
from pathlib import Path
from .dummy_data import generate_dummy_storage

_BASE_DIR = Path(__file__).parent.parent
STORAGE_DIR = _BASE_DIR / "storage"
FAISS_PATH = STORAGE_DIR / "faiss_index.bin"

def load_faiss_index():
    import faiss

    if not FAISS_PATH.exists():
        # generate dummy data (includes FAISS index)
        generate_dummy_storage(STORAGE_DIR)

    return faiss.read_index(str(FAISS_PATH))
