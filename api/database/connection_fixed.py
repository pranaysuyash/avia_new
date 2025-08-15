"""
Database Connection Fix for Cross-Platform Compatibility
"""
import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

class DatabaseConnectionManager:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self._setup_connection()
        
    def _setup_connection(self):
        """Setup database connection with retry logic and cross-platform support"""
        try:
            # Get database URL from environment
            database_url = os.getenv("DATABASE_URL")
            
            # Fallback URLs for different platforms
            if not database_url:
                if os.name == 'nt':  # Windows
                    database_url = "sqlite:///./app.db"
                elif os.name == 'posix':  # Unix/Linux/macOS
                    database_url = "sqlite:///./app.db"
                else:
                    database_url = "sqlite:///./app.db"
                    
            # Handle SQLite special cases for cross-platform
            if database_url.startswith("sqlite:///"):
                # Ensure the database file exists and is writable
                db_path = database_url.replace("sqlite:///", "")
                if not os.path.exists(db_path):
                    # Create directory if it doesn't exist
                    db_dir = os.path.dirname(db_path)
                    if db_dir and not os.path.exists(db_dir):
                        os.makedirs(db_dir, exist_ok=True)
                        
            # Create engine with proper configuration
            self.engine = create_engine(
                database_url,
                poolclass=QueuePool,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Enable connection health checks
                pool_recycle=3600,   # Recycle connections after 1 hour
                echo=False,          # Disable SQL echo in production
                connect_args={
                    "check_same_thread": False,  # For SQLite
                    "timeout": 30,                # Connection timeout
                } if "sqlite" in database_url else {}
            )
            
            # Create session factory
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
            )
            
            # Test connection
            self._test_connection()
            
            logger.info("Database connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup database connection: {str(e)}")
            # Fallback to in-memory database for development
            if os.getenv("ENVIRONMENT", "development") == "development":
                logger.info("Falling back to in-memory SQLite database for development")
                self.engine = create_engine(
                    "sqlite:///:memory:",
                    poolclass=QueuePool,
                    pool_pre_ping=True,
                    echo=False
                )
                self.SessionLocal = scoped_session(
                    sessionmaker(
                        autocommit=False,
                        autoflush=False,
                        bind=self.engine
                    )
                )
            else:
                raise
                
    def _test_connection(self):
        """Test database connection"""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as connection:
                    result = connection.execute(text("SELECT 1"))
                    if result.fetchone():
                        logger.debug("Database connection test successful")
                        return
            except Exception as e:
                logger.warning(f"Database connection test failed (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise
                    
    @contextmanager
    def get_db_session(self):
        """Get database session with proper cleanup"""
        db = None
        try:
            db = self.SessionLocal()
            yield db
        except Exception as e:
            if db:
                db.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            if db:
                db.close()
                
    def close_connections(self):
        """Close all database connections"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()

# Create global database manager
db_manager = DatabaseConnectionManager()

def get_db():
    """Dependency for FastAPI to get database session"""
    with db_manager.get_db_session() as db:
        yield db

def init_db():
    """Initialize database with proper error handling"""
    try:
        # Import all models to ensure they're registered
        from database.models import Base
        
        # Create tables
        if db_manager.engine:
            Base.metadata.create_all(bind=db_manager.engine)
            logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        # Don't raise in development mode to allow app to start
        if os.getenv("ENVIRONMENT", "development") != "development":
            raise

# Cleanup function for application shutdown
def cleanup_db():
    """Cleanup database connections on application shutdown"""
    try:
        db_manager.close_connections()
        logger.info("Database connections closed successfully")
    except Exception as e:
        logger.error(f"Error closing database connections: {str(e)}")