"""
TaskPilot — FastAPI application factory.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.router import api_router
from app.config import get_settings
from app.core.database import close_db, init_db
from app.core.logging import get_logger, setup_logging
from app.services.scheduler import setup_scheduler, shutdown_scheduler

settings = get_settings()

async def polling_task():
    from app.services.telegram import get_telegram_service
    from app.services.telegram_commands import process_telegram_command
    from app.services.orchestrator import OrchestrationService
    from app.core.database import async_session_factory
    
    logger = get_logger("taskpilot.polling")
    telegram = get_telegram_service()
    logger.info("starting_telegram_polling")
    
    offset = None
    while True:
        try:
            updates = await telegram.get_updates(offset=offset)
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" in update:
                    message = update["message"]
                    chat_id = message.get("chat", {}).get("id")
                    text = message.get("text", "")
                    
                    if not chat_id or not text:
                        continue
                        
                    async with async_session_factory() as db:
                        command_response = await process_telegram_command(str(chat_id), text, db)
                        if command_response:
                            await telegram.send_message(str(chat_id), command_response)
                        else:
                            service = OrchestrationService(db)
                            await service.handle_incoming_message(str(chat_id), text)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error("polling_error", error=str(e))
            await asyncio.sleep(5)
        await asyncio.sleep(1)


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

    polling_job = None
    if settings.telegram_mode == "polling":
        polling_job = asyncio.create_task(polling_task())

    yield

    if polling_job:
        polling_job.cancel()

    # Shutdown
    shutdown_scheduler()
    await close_db()
    logger.info("shutdown_complete")


def create_app() -> FastAPI:
    """Application factory."""
    app = FastAPI(
        title=settings.app_name,
        description=(
            "🚀 TaskPilot — AI-Powered Task Scheduler for Telegram & WhatsApp. "
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
        allow_origins=settings.cors_origins,
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
