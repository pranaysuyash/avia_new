#!/usr/bin/env python3
"""
Simple API runner without Redis dependency for development
"""
import os
import sys

# Set environment variables
os.environ['JWT_SECRET_KEY'] = 'development-secret-key-change-in-production'
os.environ['DISABLE_REDIS'] = 'true'  # Disable Redis for development

# Change to the project directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Run uvicorn
os.system("uvicorn api.app:app --reload --host 127.0.0.1 --port 8000")