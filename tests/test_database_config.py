"""
Database configuration tests.
"""

from app.config import get_settings
from app.core.database import engine


def test_database_url_uses_postgres_when_configured():
    settings = get_settings()
    assert settings.database_url.startswith("postgresql+asyncpg://")


def test_engine_url_matches_settings():
    settings = get_settings()
    assert engine.url.drivername == "postgresql+asyncpg"
    assert engine.url.username == "taskpilot"
    assert engine.url.password == "strong_password"
    assert engine.url.host == "localhost"
    assert engine.url.port == 5432
    assert engine.url.database == "taskpilot"
