from __future__ import annotations

from sqlmodel import SQLModel, create_engine, Session

from app import models  # noqa: F401

DATABASE_URL = "sqlite:///./eyetracker.db"

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def create_db_and_tables() -> None:
    """Create database and tables."""
    SQLModel.metadata.create_all(engine)
    migrate_database()


def migrate_database() -> None:
    """Migrate database schema by adding new columns if they don't exist."""
    from sqlalchemy import inspect, text

    try:
        inspector = inspect(engine)
        if "users" in inspector.get_table_names():
            existing_columns = [col["name"] for col in inspector.get_columns("users")]
            with engine.begin() as conn:
                if "gender" not in existing_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN gender VARCHAR(50)"))
                if "age" not in existing_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN age INTEGER"))
                if "voice" not in existing_columns:
                    conn.execute(text("ALTER TABLE users ADD COLUMN voice VARCHAR(100)"))
    except Exception:
        pass


def get_session():
    """Get database session."""
    with Session(engine) as session:
        yield session
