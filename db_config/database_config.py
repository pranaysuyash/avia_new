#!/usr/bin/env python3
"""
Database Configuration for Production and Development
Supports PostgreSQL for production and SQLite for development
"""

import os
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Database configuration management"""
    
    @staticmethod
    def get_database_url(environment: str = None) -> str:
        """Get database URL based on environment"""
        if environment is None:
            environment = os.getenv('ENVIRONMENT', 'development')
        
        if environment == 'production':
            # Production PostgreSQL configuration
            db_url = os.getenv('DATABASE_URL')
            
            if not db_url:
                # Build from individual components if DATABASE_URL not set
                db_host = os.getenv('DB_HOST', 'localhost')
                db_port = os.getenv('DB_PORT', '5432')
                db_name = os.getenv('DB_NAME', 'transcription_app')
                db_user = os.getenv('DB_USER', 'postgres')
                db_password = os.getenv('DB_PASSWORD', '')
                
                if db_password:
                    db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                else:
                    db_url = f"postgresql://{db_user}@{db_host}:{db_port}/{db_name}"
            
            # Handle Heroku-style DATABASE_URL (postgres:// -> postgresql://)
            if db_url and db_url.startswith('postgres://'):
                db_url = db_url.replace('postgres://', 'postgresql://', 1)
            
            logger.info(f"Using PostgreSQL database for production")
            return db_url
        
        else:
            # Development SQLite configuration
            db_path = os.getenv('SQLITE_DB_PATH', 'transcription_app.db')
            db_url = f"sqlite:///{db_path}"
            logger.info(f"Using SQLite database for development: {db_path}")
            return db_url
    
    @staticmethod
    def get_database_settings(db_url: str = None) -> dict:
        """Get database-specific settings"""
        if db_url is None:
            db_url = DatabaseConfig.get_database_url()
        
        parsed = urlparse(db_url)
        settings = {
            'echo': os.getenv('DB_ECHO', 'false').lower() == 'true',
            'pool_pre_ping': True,  # Verify connections before using
        }
        
        if parsed.scheme in ['postgresql', 'postgres']:
            # PostgreSQL-specific settings
            settings.update({
                'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
                'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '20')),
                'pool_timeout': int(os.getenv('DB_POOL_TIMEOUT', '30')),
                'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),  # 1 hour
            })
            logger.info("Applied PostgreSQL connection pool settings")
        
        return settings
    
    @staticmethod
    def init_database_tables(engine):
        """Initialize database tables"""
        from database.models import Base
        
        try:
            Base.metadata.create_all(engine)
            logger.info("Database tables initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database tables: {e}")
            raise
    
    @staticmethod
    def verify_database_connection(engine) -> bool:
        """Verify database connection is working"""
        try:
            with engine.connect() as conn:
                # Simple query to test connection
                result = conn.execute("SELECT 1")
                result.fetchone()
            logger.info("Database connection verified successfully")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    @staticmethod
    def get_migration_config() -> dict:
        """Get Alembic migration configuration"""
        return {
            'script_location': 'migrations',
            'prepend_sys_path': '.',
            'version_path_separator': os.pathsep,
            'sqlalchemy.url': DatabaseConfig.get_database_url(),
            'compare_type': True,
            'compare_server_default': True,
        }

# Database connection settings for different environments
DATABASE_SETTINGS = {
    'development': {
        'check_same_thread': False,  # SQLite specific
        'connect_args': {'check_same_thread': False},
    },
    'production': {
        'pool_size': 10,
        'max_overflow': 20,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
    },
    'test': {
        'connect_args': {'check_same_thread': False},
    }
}