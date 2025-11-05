from fastapi import APIRouter
from datetime import datetime
import time

router = APIRouter(prefix="", tags=["health"])

start_time = time.time()

@router.get("/health", summary="Health check endpoint", response_description="Returns API health status")
async def health_check():
    """Health check endpoint to verify API is running"""
    return {
        "status": "healthy",
        "service": "SHOOTRZ FastAPI Backend",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": round(time.time() - start_time, 2),
    }

