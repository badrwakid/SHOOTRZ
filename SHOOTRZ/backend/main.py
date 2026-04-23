from __future__ import annotations

import logging
import multiprocessing
import time
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# IMPORTANT: Force ``spawn`` BEFORE any ProcessPoolExecutor is created.
# MediaPipe's TFLite runtime is not fork-safe on Linux/macOS — fork leads to
# deadlocks on the first pipeline call in a worker. Windows already defaults
# to spawn so this is a no-op there.
try:
    multiprocessing.set_start_method("spawn", force=True)
except RuntimeError:
    # Context already set (e.g. during hot reload in dev) — harmless.
    pass

from .routers import history, feedback, db_test, db_integration_test, sessions, mvp, user
from .routers import analysis
from .routers import chat
from .routers.recommendation_routes import router as recommendation_router


logger = logging.getLogger(__name__)

# Bump when API surface changes (visible in GET /health — if this stays 0.1.0, wrong code is running).
__version__ = "0.2.0"
# Human-readable marker for support / debugging (must appear in /health JSON).
API_BUILD_ID = "shootrz-main-2026-04-analysis-routes"
# Track server start time for health endpoint
_start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup is a no-op — the ProcessPool is lazy-initialised on first job.

    On shutdown we stop accepting new work and let in-flight jobs finish;
    without ``cancel_futures=True`` in-flight subprocesses would hang the
    server on Ctrl-C.
    """
    yield
    try:
        mvp.service.shutdown()
        logger.info("MVPJobService executor shut down")
    except Exception:
        logger.exception("Error shutting down MVPJobService executor")


def create_app() -> FastAPI:
    app = FastAPI(title="SHOOTRZ API", version=__version__, lifespan=lifespan)

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
    app.include_router(analysis.router)
    app.include_router(recommendation_router, prefix="/api")
    app.state.limiter = mvp.limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
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
    
    @app.get("/health", tags=["health"], summary="Health check", response_description="API health status")
    async def health_check():
        """Health check endpoint to verify API is running."""
        gemini_ok = False
        try:
            from .utils import config
            gemini_ok = bool(config.GEMINI_API_KEY)
        except Exception:
            pass

        route_paths = {getattr(r, "path", "") for r in app.routes}
        # Absolute path of this module — if this doesn't match your repo, the wrong `backend` is imported.
        try:
            main_file = Path(__file__).resolve()
        except Exception:
            main_file = None

        return {
            "status": "healthy",
            "service": "SHOOTRZ FastAPI Backend",
            "version": __version__,
            "api_build_id": API_BUILD_ID,
            "main_file": str(main_file) if main_file is not None else None,
            "timestamp": datetime.now().isoformat(),
            "uptime": round(time.time() - _start_time, 2),
            "gemini_configured": gemini_ok,
            "gemini_model": getattr(__import__("os"), "getenv")("GEMINI_MODEL", "gemini-2.5-flash"),
            "has_analysis_history_route": "/api/user/analysis-history" in route_paths,
            "has_analysis_complete_route": "/api/analysis/complete" in route_paths,
            "has_delete_account_route": "/api/user/account" in route_paths,
            "route_count": len(app.routes),
        }

    return app


app = create_app()

