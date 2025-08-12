# FastAPI Service Architecture Foundation

A comprehensive, production-ready FastAPI service architecture with enterprise-grade patterns for authentication, validation, error handling, monitoring, and observability.

## 🏗️ Architecture Overview

This service architecture provides a solid foundation for building scalable, maintainable, and observable microservices with FastAPI. It implements industry best practices and common patterns used in production environments.

### Core Components

```
api/core/
├── __init__.py              # Public API exports
├── base_service.py          # Base service class with common patterns
├── api_gateway.py           # Unified API gateway with middleware
├── middleware.py            # Authentication, validation, error handling
├── health.py                # Health checking system
├── metrics.py               # Metrics collection and monitoring
├── logging.py               # Structured logging configuration
├── openapi.py               # OpenAPI documentation generation
├── exceptions.py            # Custom exception classes
└── tests/                   # Comprehensive test suite
```

## 🚀 Key Features

### 1. Base Service Architecture
- **Common Patterns**: Authentication, validation, error handling
- **Retry Logic**: Configurable retry with exponential backoff
- **Lifecycle Management**: Proper initialization and shutdown
- **Context Management**: Request context and user authentication
- **Health Checks**: Service-specific health monitoring

### 2. API Gateway
- **Unified Entry Point**: Single point for all API requests
- **Middleware Stack**: Configurable middleware pipeline
- **Request Routing**: Dynamic route registration
- **Error Handling**: Consistent error responses
- **CORS Support**: Cross-origin resource sharing

### 3. Comprehensive Middleware
- **Authentication**: JWT tokens and API key validation
- **Rate Limiting**: Sliding window algorithm with Redis support
- **Request Validation**: Size limits and content type validation
- **Metrics Collection**: Automatic request/response metrics
- **Error Handling**: Structured error responses with request IDs

### 4. Health Monitoring
- **Multi-level Checks**: Service, database, external dependencies
- **Configurable Timeouts**: Per-check timeout configuration
- **Critical vs Non-critical**: Different handling for different check types
- **History Tracking**: Health check result history
- **System Metrics**: CPU, memory, disk usage monitoring

### 5. Metrics & Observability
- **Multiple Metric Types**: Counters, gauges, histograms, timers
- **Prometheus Export**: Native Prometheus format support
- **Performance Tracking**: Request duration and throughput
- **Custom Metrics**: Easy addition of business-specific metrics
- **Context Managers**: Convenient timing utilities

### 6. Structured Logging
- **JSON Format**: Machine-readable log format
- **Context Enrichment**: Request IDs, user IDs, service context
- **Multiple Handlers**: Console, file, error-specific logging
- **Log Rotation**: Automatic log file rotation
- **Performance Logging**: Operation timing and slow query detection

### 7. OpenAPI Documentation
- **Auto-generation**: Automatic schema generation
- **Authentication Docs**: JWT and API key documentation
- **Response Examples**: Comprehensive request/response examples
- **Error Documentation**: Detailed error response schemas
- **Interactive UI**: Swagger UI and ReDoc integration

## 📦 Installation & Setup

### Prerequisites
```bash
pip install fastapi uvicorn pydantic sqlalchemy redis aiohttp psutil
```

### Basic Usage

```python
from api.core import APIGateway, setup_logging

# Setup logging
logger = setup_logging(
    service_name="my_service",
    log_level="INFO",
    log_format="json"
)

# Create API Gateway
gateway = APIGateway(
    title="My Production API",
    description="Enterprise-grade API",
    version="1.0.0"
)

# Get FastAPI app
app = gateway.get_app()

# Add custom endpoints
@app.get("/custom")
async def custom_endpoint():
    return {"message": "Hello World!"}
```

### Production Application

```python
from api.production_app import create_production_app

# Create production-ready app with all middleware
app = create_production_app()

# Run with: uvicorn api.production_app:app --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

```bash
# Logging
LOG_LEVEL=INFO
DEBUG=false

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# Request Validation
MAX_REQUEST_SIZE=104857600  # 100MB

# Database
DATABASE_URL=postgresql://user:pass@localhost/db

# Redis (for rate limiting)
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key

# Environment
ENVIRONMENT=production
```

### Service Configuration

```python
from api.core import ServiceConfig, BaseService

config = ServiceConfig(
    name="transcription_service",
    version="1.0.0",
    debug=False,
    timeout=30,
    max_retries=3,
    enable_metrics=True,
    enable_logging=True
)

class MyService(BaseService):
    async def _initialize_service(self):
        # Service-specific initialization
        pass
    
    async def _shutdown_service(self):
        # Service-specific cleanup
        pass
    
    async def _process_request(self, request):
        # Business logic implementation
        return {"result": "success"}
```

## 🏥 Health Checks

### Adding Health Checks

```python
from api.core import HealthChecker

health_checker = HealthChecker()

# Database health check
async def database_health():
    try:
        # Test database connection
        return {"status": "healthy", "connections": "5/10"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

health_checker.add_check(
    "database", 
    database_health, 
    timeout=5, 
    critical=True
)

# Check all health
result = await health_checker.check_all()
```

### Health Endpoints

- `GET /health` - Basic health check
- `GET /health/detailed` - Comprehensive health with dependencies
- `GET /info` - Service information

## 📊 Metrics

### Using Metrics

```python
from api.core import MetricsCollector, timer

metrics = MetricsCollector("my_service")

# Counters
metrics.increment_counter("requests_total")
metrics.increment_counter("errors_total", labels={"type": "validation"})

# Gauges
metrics.set_gauge("active_connections", 25)

# Histograms
metrics.record_histogram("response_time", 0.150)

# Timers
with timer(metrics, "operation_duration"):
    # Your operation here
    pass
```

### Metrics Endpoints

- `GET /metrics` - JSON format metrics
- `GET /metrics/prometheus` - Prometheus format

## 🔐 Authentication

### JWT Authentication

```python
# Token validation function
def jwt_validator(token: str) -> Dict[str, Any]:
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401)
    
    return {
        "user_id": payload.get("sub"),
        "authenticated": True,
        "is_active": True
    }

# Add to middleware
gateway.add_middleware(
    AuthenticationMiddleware,
    token_validator=jwt_validator,
    exclude_paths=["/health", "/docs"]
)
```

### API Key Authentication

```python
def api_key_validator(api_key: str) -> Dict[str, Any]:
    user = validate_api_key(api_key)
    if not user:
        raise HTTPException(status_code=401)
    
    return {
        "user_id": str(user.id),
        "authenticated": True,
        "auth_method": "api_key"
    }
```

## 🛡️ Error Handling

### Custom Exceptions

```python
from api.core.exceptions import ServiceError, ValidationError

# Business logic error
raise ServiceError("Processing failed", status_code=422)

# Validation error
raise ValidationError("Invalid input", field="email")
```

### Error Response Format

```json
{
  "error": {
    "code": 400,
    "message": "Validation error",
    "request_id": "req_123456789",
    "timestamp": "2024-01-01T12:00:00Z",
    "details": {
      "field": "email",
      "validation_errors": ["Invalid email format"]
    }
  }
}
```

## 🧪 Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest api/core/tests/ -v

# Run with coverage
pytest api/core/tests/ --cov=api.core --cov-report=html
```

### Test Examples

```python
import pytest
from fastapi.testclient import TestClient
from api.core import APIGateway

@pytest.fixture
def client():
    gateway = APIGateway()
    return TestClient(gateway.get_app())

def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
```

## 📈 Monitoring & Observability

### Structured Logging

```python
from api.core import get_logger

logger = get_logger("my_module")

# Structured logging with context
logger.info(
    "Processing request",
    extra={
        "request_id": "req_123",
        "user_id": "user_456",
        "operation": "transcription"
    }
)
```

### Performance Monitoring

```python
from api.core.logging import PerformanceLogger

perf_logger = PerformanceLogger(logger)

# Log operation timing
perf_logger.log_operation_time("transcription", 2.5)

# Log slow operations
perf_logger.log_slow_operation("database_query", 5.2, threshold=1.0)
```

### Security Logging

```python
from api.core.logging import SecurityLogger

security_logger = SecurityLogger(logger)

# Log authentication attempts
security_logger.log_authentication_attempt("user_123", True, "192.168.1.1")

# Log authorization failures
security_logger.log_authorization_failure("user_123", "admin_panel", "access")
```

## 🚀 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "api.production_app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Environment variables configured
- [ ] Database connections tested
- [ ] Redis configured for rate limiting
- [ ] Log aggregation setup (ELK, Fluentd)
- [ ] Metrics collection (Prometheus)
- [ ] Health check endpoints accessible
- [ ] SSL/TLS certificates configured
- [ ] Rate limiting thresholds set
- [ ] Error alerting configured

## 📚 API Documentation

Once running, access the interactive documentation:

- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Check the documentation
- Review the test examples
- Run the demo script: `python demo_service_architecture.py`