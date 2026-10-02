"""
Database connection management for FastAPI backend.
Provides SQLAlchemy engine, session maker, declarative base, and dependency generator.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.config import settings

# SQLite requires check_same_thread=False for concurrent FastAPI requests
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    FastAPI dependency yielding a database session per request.
    Closes the session cleanly upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initializes database tables defined in models if they do not exist."""
    # Import models so that Base.metadata knows about them
    from backend.database import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
