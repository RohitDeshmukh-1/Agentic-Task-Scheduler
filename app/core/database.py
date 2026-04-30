"""
Async database engine, session factory, and base model.

Supports SQLite (development) and PostgreSQL (production) with
connection pooling and proper lifecycle management.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, func, DateTime, event
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session


# ── Global Timezone Normalization ──────────────────────────────────────────
@event.listens_for(Session, "before_flush")
def strip_tz_before_flush(session, flush_context, instances):
    """
    Global fail-safe: Force all datetimes to be naive before they hit the DB.
    Postgres (via asyncpg) crashes if it receives a timezone-aware datetime
    for a TIMESTAMP WITHOUT TIME ZONE column.
    """
    for obj in session.new | session.dirty:
        for attr in obj.__mapper__.all_orm_descriptors:
            if hasattr(attr, "type") and isinstance(attr.type, (DateTime, TIMESTAMP)):
                val = getattr(obj, attr.key)
                if isinstance(val, datetime) and val.tzinfo is not None:
                    setattr(obj, attr.key, val.replace(tzinfo=None))

from app.config import get_settings

settings = get_settings()

# ── Engine Configuration ─────────────────────────────────────────────────────
db_url = settings.database_url
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://") and "+asyncpg" not in db_url:
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

_engine_kwargs: dict = {
    "echo": False,
    "future": True,
}

if settings.is_sqlite:
    # SQLite-specific: allow async + same-thread check disabled
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    # PostgreSQL connection pool tuning
    _engine_kwargs.update(
        pool_size=20,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

engine = create_async_engine(db_url, **_engine_kwargs)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ───────────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """Shared base with auto-generated UUID primary key and audit timestamps."""
    pass



class TimestampMixin:
    """Mixin to add created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        sort_order=998,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=False),
        server_default=func.now(),
        onupdate=func.now(),
        sort_order=999,
    )


class UUIDMixin:
    """Mixin that adds a UUID primary key."""

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )


# ── Session Dependency ───────────────────────────────────────────────────────
async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async session and handles cleanup."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Create all tables (used at startup)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose engine connections (used at shutdown)."""
    await engine.dispose()
