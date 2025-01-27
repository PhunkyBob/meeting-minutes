from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column
import os


class Base(DeclarativeBase):
    pass


# Database configuration
DB_PATH = os.getenv("DB_PATH", "meetings.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)  # `echo=True` pour le débogage
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Create databases if not exists."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Dependency for database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
