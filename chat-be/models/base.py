"""
Base model configuration for SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URLs
DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@postgres:5432/postgres"
)
TARGET_DATABASE_URL = (
    "postgresql+psycopg://postgres:postgres@postgres:5432/threads_db"
)

# Create engines
default_engine = create_engine(DEFAULT_DATABASE_URL, future=True)
target_engine = create_engine(TARGET_DATABASE_URL, future=True)

# Create base class
Base = declarative_base()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=target_engine)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
