from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import time

from .routers import analyze, results, history, feedback, db_test, db_integration_test, sessions

# Track server start time for health endpoint
_start_time = time.time()


def create_app() -> FastAPI:
    app = FastAPI(title="SHOOTRZ API", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers first
    app.include_router(analyze.router)
    app.include_router(results.router)
    app.include_router(history.router)
    app.include_router(feedback.router)
    app.include_router(sessions.router)
    app.include_router(db_test.router)  # Database test endpoint
    app.include_router(db_integration_test.router)  # Integration test endpoint
    
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

