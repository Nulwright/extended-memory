"""Database Connection and Session Management"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator
from contextlib import contextmanager

from esm.config import get_settings
from esm.models import Base

logger = logging.getLogger(__name__)

# Get settings
settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
    # For SQLite compatibility
    poolclass=StaticPool if "sqlite" in settings.database_url else None,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def drop_tables():
    """Drop all database tables (use with caution!)"""
    logger.warning("Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)
    logger.info("Database tables dropped")


def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Database session context manager
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database context error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


# Event listeners for database optimization
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance"""
    if "sqlite" in settings.database_url:
        cursor = dbapi_connection.cursor()
        # Enable foreign key constraints
        cursor.execute("PRAGMA foreign_keys=ON")
        # Optimize for better performance
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.execute("PRAGMA mmap_size=268435456")  # 256MB
        cursor.close()


class DatabaseHealthCheck:
    """Database health check utilities"""
    
    @staticmethod
    def check_connection() -> bool:
        """Check if database connection is healthy"""
        try:
            with get_db_context() as db:
                # Simple query to test connection
                db.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    @staticmethod
    def get_table_counts() -> dict:
        """Get record counts for all tables"""
        try:
            with get_db_context() as db:
                from esm.models import Assistant, Memory, MemoryEmbedding, SharedMemory, MemoryStats
                
                counts = {
                    "assistants": db.query(Assistant).count(),
                    "memories": db.query(Memory).count(),
                    "memory_embeddings": db.query(MemoryEmbedding).count(),
                    "shared_memories": db.query(SharedMemory).count(),
                    "memory_stats": db.query(MemoryStats).count(),
                }
                return counts
        except Exception as e:
            logger.error(f"Failed to get table counts: {e}")
            return {}


# Initialize database
def init_db():
    """Initialize database with default data"""
    logger.info("Initializing database...")
    
    # Create tables
    create_tables()
    
    # Create default assistants
    with get_db_context() as db:
        from esm.models import Assistant
        
        # Check if assistants already exist
        existing_assistants = db.query(Assistant).count()
        if existing_assistants == 0:
            logger.info("Creating default assistants...")
            
            sienna = Assistant(
                name="Sienna",
                personality="Dry, sharp, sarcastic, cutting truth-teller who doesn't sugarcoat anything",
                is_active=True
            )
            
            vale = Assistant(
                name="Vale",
                personality="Quieter, reflective, precise assistant who thinks deeply before speaking",
                is_active=True
            )
            
            db.add(sienna)
            db.add(vale)
            db.commit()
            
            logger.info("Default assistants created: Sienna and Vale")
        else:
            logger.info("Assistants already exist, skipping creation")
    
    logger.info("Database initialization complete")


if __name__ == "__main__":
    init_db()