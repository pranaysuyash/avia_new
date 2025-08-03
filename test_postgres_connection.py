#!/usr/bin/env python3
"""Test PostgreSQL connection"""

import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database credentials
db_config = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'ner_transcription_db'),
    'user': os.getenv('POSTGRES_USER', 'transcription_user'),
    'password': os.getenv('POSTGRES_PASSWORD', 'transcription_pass')
}

print("Testing PostgreSQL connection...")
print(f"Host: {db_config['host']}")
print(f"Port: {db_config['port']}")
print(f"Database: {db_config['database']}")
print(f"User: {db_config['user']}")

try:
    # Connect to PostgreSQL
    conn = psycopg2.connect(**db_config)
    cursor = conn.cursor()
    
    # Test query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n✅ Connection successful!")
    print(f"PostgreSQL version: {version}")
    
    # Check tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    
    tables = cursor.fetchall()
    print(f"\nFound {len(tables)} tables:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  - {table[0]}: {count} rows")
    
    # Close connection
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ Connection failed: {e}")