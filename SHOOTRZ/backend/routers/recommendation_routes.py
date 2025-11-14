from fastapi import APIRouter, HTTPException
import numpy as np
from ..recommender.model_loader import load_recommender
from ..recommender.recommend_service import recommend_drill

router = APIRouter()
_rec = None

def get_recommender():
    """Lazy load recommender to avoid import-time errors if files are missing"""
    global _rec
    if _rec is None:
        _rec = load_recommender()
    return _rec

@router.post("/recommend")
def recommend(payload: dict):
    try:
        user_vec = payload["user_vec"]
        user_context = payload["user_context"]
    except Exception:
        raise HTTPException(400, "Payload must include 'user_vec' and 'user_context'")

    rec = get_recommender()
    result = recommend_drill(
        user_vec=user_vec,
        user_context=user_context,
        drills=rec["metadata"],
        labels=rec["labels"],
        tiers=rec["tiers"],
        faiss_index=rec["faiss_index"],
        bandit=rec["bandit"]
    )

    return result
