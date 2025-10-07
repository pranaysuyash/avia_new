#!/usr/bin/env python3
"""
Test script to verify environment variable loading and CORS configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== Environment Variable Test ===")
print(f"ALLOWED_ORIGINS: {os.getenv('ALLOWED_ORIGINS')}")

# Test CORS origins parsing
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:3003,http://localhost:3005,http://localhost:5173").split(",")
print(f"Parsed origins: {origins}")
print(f"Port 3005 included: {'http://localhost:3005' in origins}")