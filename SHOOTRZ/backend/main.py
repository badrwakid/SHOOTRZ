from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time

from .routers import history, feedback, db_test, db_integration_test, sessions, mvp, user
from .routers import chat
from .routers.recommendation_routes import router as recommendation_router

# BUG FIX: Single source of truth for version (was 0.1.0 in app metadata, 1.0.0 in endpoints)
__version__ = "0.1.0"
# Track server start time for health endpoint
_start_time = time.time()


def create_app() -> FastAPI:
    app = FastAPI(title="SHOOTRZ API", version=__version__)

    # BUG FIX: allow_origins=["*"] with allow_credentials=True is invalid per CORS spec
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers first
    app.include_router(mvp.router)  # MVP analysis endpoints
    app.include_router(chat.router)  # AI coach chat
    app.include_router(history.router)
    app.include_router(feedback.router)
    app.include_router(sessions.router)
    app.include_router(db_test.router)  # Database test endpoint
    app.include_router(db_integration_test.router)  # Integration test endpoint
    app.include_router(user.router)
    app.include_router(recommendation_router, prefix="/api")
    
    # Root endpoint - redirect to docs
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint - redirects to API documentation"""
        return {
            "message": "SHOOTRZ API",
            "version": __version__,
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
            "version": __version__,
            "timestamp": datetime.now().isoformat(),
            "uptime": round(time.time() - _start_time, 2),
        }

    return app


app = create_app()

