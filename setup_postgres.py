#!/usr/bin/env python3
"""
PostgreSQL Database Setup Script
Sets up the database, creates tables, and runs migrations
"""

import os
import sys
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_database():
    """Create the database if it doesn't exist"""
    # Connection parameters for postgres admin database
    admin_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'user': 'postgres',  # Admin user
        'password': os.getenv('POSTGRES_ADMIN_PASSWORD', os.getenv('POSTGRES_PASSWORD', 'postgres'))
    }
    
    db_name = os.getenv('POSTGRES_DB', 'ner_transcription_db')
    db_user = os.getenv('POSTGRES_USER', 'transcription_user')
    db_password = os.getenv('POSTGRES_PASSWORD', 'transcription_pass')
    
    try:
        # Connect to postgres database
        logger.info("Connecting to PostgreSQL server...")
        conn = psycopg2.connect(database='postgres', **admin_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,))
        exists = cursor.fetchone()
        
        if not exists:
            logger.info(f"Creating database '{db_name}'...")
            cursor.execute(f'CREATE DATABASE "{db_name}"')
            logger.info("Database created successfully!")
        else:
            logger.info(f"Database '{db_name}' already exists")
        
        # Check if user exists
        cursor.execute("SELECT 1 FROM pg_user WHERE usename = %s", (db_user,))
        user_exists = cursor.fetchone()
        
        if not user_exists:
            logger.info(f"Creating user '{db_user}'...")
            cursor.execute(f"CREATE USER {db_user} WITH PASSWORD %s", (db_password,))
            logger.info("User created successfully!")
        else:
            logger.info(f"User '{db_user}' already exists")
            # Update password
            cursor.execute(f"ALTER USER {db_user} WITH PASSWORD %s", (db_password,))
        
        # Grant privileges
        logger.info(f"Granting privileges to user '{db_user}'...")
        cursor.execute(f'GRANT ALL PRIVILEGES ON DATABASE "{db_name}" TO {db_user}')
        cursor.execute(f'ALTER DATABASE "{db_name}" OWNER TO {db_user}')
        
        cursor.close()
        conn.close()
        logger.info("Database setup completed!")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
        return False


def test_connection():
    """Test the database connection"""
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'ner_transcription_db'),
        'user': os.getenv('POSTGRES_USER', 'transcription_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'transcription_pass')
    }
    
    try:
        logger.info("Testing database connection...")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        logger.info(f"Connected successfully! PostgreSQL version: {version}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False


def create_extensions():
    """Create required PostgreSQL extensions"""
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'ner_transcription_db'),
        'user': os.getenv('POSTGRES_USER', 'transcription_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'transcription_pass')
    }
    
    try:
        logger.info("Creating PostgreSQL extensions...")
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        extensions = ['uuid-ossp', 'pg_trgm', 'pgcrypto', 'btree_gin']
        
        for ext in extensions:
            try:
                cursor.execute(f'CREATE EXTENSION IF NOT EXISTS "{ext}"')
                logger.info(f"Extension '{ext}' created/verified")
            except Exception as e:
                logger.warning(f"Could not create extension '{ext}': {e}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating extensions: {e}")
        return False


def run_schema_script():
    """Run the comprehensive schema SQL script"""
    db_config = {
        'host': os.getenv('POSTGRES_HOST', 'localhost'),
        'port': os.getenv('POSTGRES_PORT', '5432'),
        'database': os.getenv('POSTGRES_DB', 'ner_transcription_db'),
        'user': os.getenv('POSTGRES_USER', 'transcription_user'),
        'password': os.getenv('POSTGRES_PASSWORD', 'transcription_pass')
    }
    
    schema_file = 'database/schema_comprehensive.sql'
    
    if not os.path.exists(schema_file):
        logger.error(f"Schema file not found: {schema_file}")
        return False
    
    try:
        logger.info("Running comprehensive schema script...")
        
        # Use psql to run the script
        env = os.environ.copy()
        env['PGPASSWORD'] = db_config['password']
        
        cmd = [
            'psql',
            '-h', db_config['host'],
            '-p', str(db_config['port']),
            '-U', db_config['user'],
            '-d', db_config['database'],
            '-f', schema_file
        ]
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Schema script executed successfully!")
            return True
        else:
            logger.error(f"Schema script failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running schema script: {e}")
        return False


def run_alembic_migrations():
    """Run Alembic migrations"""
    try:
        logger.info("Running Alembic migrations...")
        
        # Check current revision
        result = subprocess.run(['alembic', 'current'], capture_output=True, text=True)
        logger.info(f"Current revision: {result.stdout.strip()}")
        
        # Generate initial migration if needed
        result = subprocess.run(['alembic', 'revision', '--autogenerate', '-m', 'Initial migration'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Generated initial migration")
        else:
            logger.warning(f"Could not generate migration: {result.stderr}")
        
        # Run migrations
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("Migrations completed successfully!")
            return True
        else:
            logger.error(f"Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Error running migrations: {e}")
        return False


def main():
    """Main setup function"""
    logger.info("=== PostgreSQL Database Setup ===")
    
    # Check if we're using PostgreSQL
    db_url = os.getenv('DATABASE_URL', '')
    if 'sqlite' in db_url.lower():
        logger.warning("DATABASE_URL is set to SQLite. Update your .env file to use PostgreSQL.")
        logger.info("Example: DATABASE_URL=postgresql://user:password@localhost:5432/dbname")
        return
    
    # Step 1: Create database
    if not create_database():
        logger.error("Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Test connection
    if not test_connection():
        logger.error("Failed to connect to database. Check your credentials.")
        sys.exit(1)
    
    # Step 3: Create extensions
    if not create_extensions():
        logger.warning("Some extensions could not be created. This might be okay.")
    
    # Step 4: Run schema script
    choice = input("\nRun comprehensive schema script? This will create all tables. (y/n): ")
    if choice.lower() == 'y':
        if not run_schema_script():
            logger.error("Failed to run schema script.")
            sys.exit(1)
    
    # Step 5: Run Alembic migrations
    choice = input("\nSet up Alembic migrations? (y/n): ")
    if choice.lower() == 'y':
        if not run_alembic_migrations():
            logger.warning("Alembic migrations had issues. You may need to run them manually.")
    
    logger.info("\n=== Setup Complete! ===")
    logger.info("You can now start using PostgreSQL with your application.")
    logger.info("\nNext steps:")
    logger.info("1. Update your .env file with the correct DATABASE_URL")
    logger.info("2. Run: python test_postgres_connection.py")
    logger.info("3. Start your application!")


if __name__ == "__main__":
    main()