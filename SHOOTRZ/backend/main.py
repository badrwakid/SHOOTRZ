from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time
import json

from .routers import history, feedback, db_test, db_integration_test, sessions, mvp
from .routers import chat
from .routers.recommendation_routes import router as recommendation_router
# Track server start time for health endpoint
_start_time = time.time()


def create_app() -> FastAPI:
    # #region agent log
    log_data = {
        "location": "main.py:12",
        "message": "create_app called",
        "data": {},
        "timestamp": int(time.time() * 1000),
        "sessionId": "debug-session",
        "runId": "run1",
        "hypothesisId": "E"
    }
    try:
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    
    app = FastAPI(title="SHOOTRZ API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers first
    # #region agent log
    try:
        log_data = {
            "location": "main.py:24",
            "message": "Registering mvp router",
            "data": {"router_prefix": mvp.router.prefix if hasattr(mvp.router, 'prefix') else None},
            "timestamp": int(time.time() * 1000),
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": "E"
        }
        with open(r"d:\Users\Badr\myprojects\Grad\.cursor\debug.log", "a") as f:
            f.write(json.dumps(log_data) + "\n")
    except:
        pass
    # #endregion
    app.include_router(mvp.router)  # MVP analysis endpoints
    app.include_router(chat.router)  # AI coach chat
    app.include_router(history.router)
    app.include_router(feedback.router)
    app.include_router(sessions.router)
    app.include_router(db_test.router)  # Database test endpoint
    app.include_router(db_integration_test.router)  # Integration test endpoint
    app.include_router(recommendation_router, prefix="/api")
    
    # Root endpoint - redirect to docs
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint - redirects to API documentation"""
        return {
            "message": "SHOOTRZ API",
            "version": "1.0.0",
            "docs": "/docs",
            "health": "/health"
        }
    
    # Health endpoint - defined AFTER routers to ensure proper registration
    @app.get("/health", tags=["health"], summary="Health check", response_description="API health status")
    async def health_check():
        """Health check endpoint to verify API is running"""
        return {
            "status": "healthy",
            "service": "SHOOTRZ FastAPI Backend",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "uptime": round(time.time() - _start_time, 2),
        }

    return app


app = create_app()

