"""SQLAlchemy engine, session, and schema initialization boundary."""

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.config import get_database_url


class Base(DeclarativeBase):
    """Base class for all ORM models."""


DATABASE_URL = get_database_url()
_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
from backend.models import database as _database  # noqa: F401


def init_db() -> None:
    """Create ORM-managed tables when the configured database is first used."""
    Base.metadata.create_all(bind=engine)
    columns = {column["name"] for column in inspect(engine).get_columns("reports")}
    if "source_text" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE reports ADD COLUMN source_text TEXT NOT NULL DEFAULT ''")
            )


def get_db() -> Generator[Session, None, None]:
    """Provide one request-scoped database session."""
    init_db()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
