from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app import models  # noqa: F401
from app.utils.logging import get_logger

logger = get_logger()

DATABASE_URL = "sqlite+aiosqlite:///./eyetracker.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with async_session_factory() as session:
        yield session


def _migrate_schema(sync_conn) -> None:
    """Sync migration: add new columns if missing."""
    from sqlalchemy import inspect

    inspector = inspect(sync_conn)
    tables = inspector.get_table_names()

    if "users" in tables:
        existing = [col["name"] for col in inspector.get_columns("users")]
        if "gender" not in existing:
            sync_conn.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR(50)"))
        if "age" not in existing:
            sync_conn.execute(text("ALTER TABLE users ADD COLUMN age INTEGER"))
        if "voice" not in existing:
            sync_conn.execute(text("ALTER TABLE users ADD COLUMN voice VARCHAR(100)"))

    if "communication_sessions" in tables:
        existing = [col["name"] for col in inspector.get_columns("communication_sessions")]
        if "session_type" not in existing:
            sync_conn.execute(
                text(
                    "ALTER TABLE communication_sessions ADD COLUMN session_type VARCHAR(50) "
                    "DEFAULT 'communication'"
                )
            )


async def create_db_and_tables() -> None:
    """Create database and tables (async)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL"))
        await conn.run_sync(_migrate_schema)
