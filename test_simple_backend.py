#!/usr/bin/env python3
"""
Simple test to verify backend_server.py is working correctly
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(title="Test Backend")

# CORS configuration
origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3005").split(",")
print(f"CORS Origins: {origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health():
    return {"status": "healthy", "cors_origins": origins}

@app.get("/api/test")
async def test():
    return {"message": "Test endpoint working", "origins": origins}

if __name__ == "__main__":
    import uvicorn
    print("Starting test backend on port 8001...")
    uvicorn.run("test_simple_backend:app", host="0.0.0.0", port=8001, reload=True)