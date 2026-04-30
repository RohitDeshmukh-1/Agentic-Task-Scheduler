"""
Database configuration tests.

Validates that the engine is correctly configured from DATABASE_URL in .env.
Password is compared against the live settings so the test doesn't need to be
updated each time the password changes.
"""

from urllib.parse import urlparse

from app.config import get_settings
from app.core.database import engine


def test_database_url_uses_postgres_when_configured():
    settings = get_settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_engine_url_matches_settings():
    settings = get_settings()

    # Parse expected values directly from the configured DATABASE_URL
    parsed = urlparse(settings.database_url)

    assert engine.url.drivername == "postgresql+asyncpg"
    assert engine.url.username == parsed.username
    assert engine.url.password == parsed.password
    assert engine.url.host == parsed.hostname
    assert engine.url.port == (parsed.port or 5432)
    assert engine.url.database == parsed.path.lstrip("/")
