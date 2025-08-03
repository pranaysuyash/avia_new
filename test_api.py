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
