from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from .models.job import Base
from .utils.settings import get_settings
from .utils.logging import get_logger

settings = get_settings()
logger = get_logger("db")

# Create database engine
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Check connection before use
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database by creating all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("database_initialized", message="Database tables created successfully")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))
        raise


def get_db() -> Session:
    """Get database session for dependency injection"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def db_transaction():
    """Context manager for database transactions with safe commit/rollback
    
    Usage:
        with db_transaction() as session:
            session.add(some_object)
            # If no exception occurs, changes are committed
            # If an exception occurs, transaction is rolled back
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error("transaction_failed", error=str(e))
        raise
    finally:
        session.close()