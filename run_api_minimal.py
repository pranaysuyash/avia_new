#!/usr/bin/env python3
"""
Minimal API server for testing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="Video NER API - Minimal", version="1.0.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API is running", "status": "ok"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/api/test")
def test_endpoint():
    return {"message": "Test endpoint working"}

if __name__ == "__main__":
    print("Starting minimal API server on http://localhost:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)