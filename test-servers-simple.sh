#!/bin/bash

echo "Starting servers for testing..."

# Kill any existing servers
lsof -ti:3000 | xargs kill -9 2>/dev/null || true
lsof -ti:8000 | xargs kill -9 2>/dev/null || true

# Start React frontend in background
echo "Starting React frontend..."
cd /Users/pranay/Projects/LLM/video/ner/desktop_app/src/renderer
BROWSER=none npm start &
FRONTEND_PID=$!

# Start simple FastAPI test server
echo "Starting simple FastAPI test server..."
cd /Users/pranay/Projects/LLM/video/ner
cat > test_api.py << 'EOF'
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "FastAPI backend is running"
    }

@app.get("/api/auth/me")
async def get_current_user():
    return {
        "id": "1",
        "username": "test_user",
        "email": "test@example.com",
        "full_name": "Test User",
        "role": "user"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
EOF

python test_api.py &
BACKEND_PID=$!

echo "Waiting for servers to start..."
sleep 10

echo "Servers should be running:"
echo "Frontend: http://localhost:3000"
echo "Backend: http://localhost:8000"
echo ""
echo "To stop servers, run:"
echo "kill $FRONTEND_PID $BACKEND_PID"
echo "lsof -ti:3000 | xargs kill -9"
echo "lsof -ti:8000 | xargs kill -9"