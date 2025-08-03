#!/usr/bin/env python3
"""
Run the API server with JWT authentication enabled
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Run the API server"""
    # Set JWT secret key if not already set
    if not os.getenv('JWT_SECRET_KEY'):
        import secrets
        jwt_secret = secrets.token_urlsafe(32)
        os.environ['JWT_SECRET_KEY'] = jwt_secret
        print(f"⚠️  Generated JWT secret key. Add to .env file:")
        print(f"JWT_SECRET_KEY={jwt_secret}")
        print()
    
    # Check PostgreSQL configuration
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        print("⚠️  DATABASE_URL not set. Using default PostgreSQL configuration.")
        print("Add to .env file:")
        print("DATABASE_URL=postgresql://ner_user:ner_password@localhost:5432/ner_db")
        print()
    
    print("🚀 Starting API server with JWT authentication...")
    print("📍 API URL: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/api/docs")
    print("🔐 Authentication: JWT tokens + API keys")
    print()
    
    try:
        # Run the server
        uvicorn.run(
            "api.app:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n✋ Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()