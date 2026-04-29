"""
Central API router — mounts all endpoint modules.
"""

from fastapi import APIRouter

from app.api.endpoints import health, tasks, users, webhook, memory

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(health.router)
api_router.include_router(webhook.router)
api_router.include_router(tasks.router)
api_router.include_router(users.router)
api_router.include_router(memory.router)
