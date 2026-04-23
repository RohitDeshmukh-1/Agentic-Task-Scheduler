"""
TaskPilot — FastAPI application factory.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import get_settings
from app.core.database import close_db, init_db
from app.core.logging import get_logger, setup_logging
from app.services.scheduler import setup_scheduler, shutdown_scheduler

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    setup_logging()
    logger = get_logger("taskpilot")
    logger.info("starting", app=settings.app_name, env=settings.app_env)

    # Initialize database
    await init_db()
    logger.info("database_ready")

    # Start background scheduler
    setup_scheduler()
    logger.info("scheduler_ready")

    yield

    # Shutdown
    shutdown_scheduler()
    await close_db()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "🚀 TaskPilot — AI-Powered WhatsApp Task Scheduler. "
            "Manage tasks, build streaks, and get intelligent insights."
        ),
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins + ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API routes
    app.include_router(api_router)

    # Serve dashboard static files
    import os
    dashboard_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
    if os.path.exists(dashboard_dir) and settings.dashboard_enabled:
        app.mount("/dashboard", StaticFiles(directory=dashboard_dir, html=True), name="dashboard")

    return app


app = create_app()
