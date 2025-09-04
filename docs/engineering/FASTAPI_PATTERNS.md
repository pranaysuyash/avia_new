# FastAPI Patterns — DI, Background Tasks, Middleware

## Dependency Injection (DI)
- Use dependency functions for shared resources (DB sessions, settings, auth)
```python
from fastapi import Depends
from sqlalchemy.orm import Session

def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
async def list_items(db: Session = Depends(get_db), user: User = Depends(require_auth)):
    return svc.list_items(db, user.id)
```

## Background Tasks
- Offload non-critical work to background tasks; for heavier work, enqueue to job system
```python
from fastapi import BackgroundTasks

def after_publish(asset_id: str):
    analytics.track_publish(asset_id)

@router.post("/publish")
async def publish(body: PublishRequest, bt: BackgroundTasks):
    result = svc.publish(body)
    bt.add_task(after_publish, result.asset_id)
    return result
```

## Middleware
- Add logging, timing, and correlation IDs; security headers; rate limits (where applicable)
```python
from starlette.middleware.base import BaseHTTPMiddleware

class TimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Response-Time"] = str((time.perf_counter()-start)*1000)
        return response

app.add_middleware(TimingMiddleware)
```

## Error Handling
- Use global exception handlers for consistency; return structured error models
```python
from fastapi.responses import JSONResponse

@app.exception_handler(MyAppError)
async def my_error_handler(request, exc: MyAppError):
    return JSONResponse(status_code=exc.status_code, content={"code": exc.code, "message": exc.message})
```

## Security & Auth
- OAuth2/JWT via FastAPI security utilities; inject current user via dependencies
- Scope-based checks in handlers or dedicate decorator-like helpers

## Response Models & Caching
- Annotate `response_model` for all GETs for schema and validation
- Consider `Cache-Control` headers and ETags for read-heavy endpoints

## Streaming & WS
- Use `StreamingResponse` for large exports; chunked responses
- For WS, standardize paths and auth via query param or header token

## Testing
- Use `TestClient` with dependency overrides; fixture-inject DB/Settings; property-based tests for validators
