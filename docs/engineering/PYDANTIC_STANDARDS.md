# Pydantic & FastAPI Standards — Improving Reliability and Developer Velocity

This guide outlines how to leverage Pydantic (v2) and related tooling to improve validation, documentation, and correctness across the app.

## Core Patterns
- Use Pydantic BaseModel for request/response DTOs; avoid dicts in controller signatures
- Annotate everything: typing + Pydantic Field constraints (min/max, regex, enums)
- Prefer `Annotated` types and Pydantic validators over ad-hoc checks in handlers
- Separate persistence models from API models; use conversion functions or ORM mode

## Request/Response Models (Example)
```python
from typing import List, Annotated
from pydantic import BaseModel, Field, HttpUrl, conlist, conint

class OCRJobCreate(BaseModel):
    sampling_mode: Annotated[str, Field(pattern=r"^(interval|keyframe)$")] = "interval"
    interval_s: Annotated[float, Field(ge=0.2, le=10.0)] = 1.0
    lang: str | None = None

class OCRHit(BaseModel):
    t_start: float
    t_end: float
    text: Annotated[str, Field(min_length=1, max_length=2000)]
    confidence: Annotated[float, Field(ge=0, le=1)]
    lang: str | None = None

class OCRResults(BaseModel):
    total: conint(ge=0)
    hits: conlist(OCRHit, min_length=0)
```

## Settings & Configuration
- Use `pydantic-settings` for environment configuration with types and defaults
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    api_url: HttpUrl = "http://localhost:8000"
    rate_limit_per_minute: int = 60
    enable_request_logging: bool = True

    model_config = {
        "env_prefix": "APP_",
        "env_file": ".env",
    }

settings = Settings()
```

## Validation & Business Rules
- Prefer model validators (Pydantic v2: `@field_validator`, `@model_validator`) for cross-field checks
```python
from pydantic import BaseModel, field_validator

class CreatorPackParams(BaseModel):
    target_platforms: list[str]
    caption_burn_in: bool = True
    hashtags_count: int = 10

    @field_validator("target_platforms")
    @classmethod
    def at_least_one_platform(cls, v):
        if not v:
            raise ValueError("Select at least one platform")
        return v
```

## Serialization & JSON Schema
- Expose structured models to FastAPI; OpenAPI is auto-generated with examples
- Use `model_json_schema()` to produce contract docs or for clients

## Error Handling
- Raise HTTPException with Pydantic model payloads for consistent error shape
- Consider custom exception handlers that return structured error models

## Strict Types & Performance
- Use `Strict*` types (e.g., `StrictInt`) when coercion is harmful
- Pydantic v2 is faster; avoid heavy nested validation in hot paths
- Consider `TypeAdapter` for ad-hoc validation of plain data structures

## DB Layer
- Keep Pydantic models at API boundary; use SQLAlchemy/SQLModel (Pydantic integrated) for DB
- Convert ORM entities to API models explicitly for clarity

## Testing & Tooling
- Add mypy + ruff; run typing checks in CI
- Use Hypothesis for property-based tests on validation-heavy models
- Generate example payloads via `model_construct` with factories

## Migration Tips (v1 → v2)
- Replace `@validator` with `@field_validator` and `@model_validator`
- Update `Config` to `model_config`
- Use `RootModel` for wrapper types; `TypeAdapter` for free-form validation

## Example FastAPI Endpoint Using Models
```python
from fastapi import APIRouter, Query, Body

router = APIRouter(prefix="/api/v1/ocr")

@router.post("/index/{media_id}")
async def start_ocr_job(media_id: str, job: OCRJobCreate = Body(None)):
    # job has validated fields; implement orchestration here
    return {"job_id": "job_01..."}

@router.get("/results", response_model=OCRResults)
async def query_results(media_id: str, q: str | None = Query(None), offset: int = 0, limit: int = 50):
    # fetch and return structured OCR hits
    return OCRResults(total=0, hits=[])
```

## Advanced Patterns
- Generics for paginated results: `Page[T]`
- Custom types: `ConstrainedStr` for IDs; regex-based validators
- Field serialization aliases for external contracts

## Summary
Adopting Pydantic pervasively yields:
- Safer inputs/outputs, clearer contracts, better docs
- Less boilerplate validation code
- Easier client integrations via generated schemas

