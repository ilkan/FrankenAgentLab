"""Database connection and session management."""

import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from frankenagent.db.base import Base

def _build_database_url() -> str:
    """Resolve the database URL for the current environment."""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    database_url = os.getenv("DATABASE_URL")

    if environment in ("development", "test"):
        if database_url:
            return database_url
        local_url = os.getenv("LOCAL_DATABASE_URL")
        return local_url or "sqlite:///./frankenagent.db"

    # Production
    if database_url:
        return database_url

    production_url = os.getenv("PRODUCTION_DATABASE_URL")
    if production_url:
        return production_url

    instance = os.getenv("CLOUD_SQL_CONNECTION_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_name = os.getenv("DB_NAME", "frankenagent")

    if instance and db_user and db_password:
        return (
            f"postgresql+psycopg2://{db_user}:{db_password}@/{db_name}"
            f"?host=/cloudsql/{instance}"
        )

    raise RuntimeError(
        "Database configuration missing. "
        "Set LOCAL_DATABASE_URL for development or PRODUCTION_DATABASE_URL / "
        "Cloud SQL env vars (CLOUD_SQL_CONNECTION_NAME, DB_USER, DB_PASSWORD) for production."
    )


# Get database URL from environment
DATABASE_URL = _build_database_url()

# Configure engine options based on backend
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}

if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs.update({"pool_size": 5, "max_overflow": 10})

# Create engine with connection pooling
engine = create_engine(DATABASE_URL, **engine_kwargs)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI to get database session.
    
    Usage:
        @app.get("/endpoint")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database by creating all tables."""
    Base.metadata.create_all(bind=engine)
