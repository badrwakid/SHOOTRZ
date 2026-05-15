# recommender/faiss_index.py
import logging
from pathlib import Path
from .drill_clustering import FAISS_PATH, load_drill_metadata, _ensure_artifacts_exist

logger = logging.getLogger(__name__)


def load_faiss_index():
    import faiss

    drills = load_drill_metadata()
    _ensure_artifacts_exist(drills)
    return faiss.read_index(str(FAISS_PATH))
