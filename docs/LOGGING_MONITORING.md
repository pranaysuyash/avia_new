# Comprehensive Logging and Monitoring Guide

## Overview

This document describes the comprehensive logging and monitoring system implemented for the Audio/Video Transcription API. The system provides structured logging, metrics collection, audit trails, and real-time monitoring capabilities.

## Architecture

### Components

1. **Structured Logger** (`monitoring/logger_config.py`)
   - JSON-formatted logs for machine parsing
   - Correlation ID tracking across requests
   - Context-aware logging with extra fields
   - Multiple handler support (console, file, error tracking)

2. **Metrics Collector** (`monitoring/metrics_collector.py`)
   - Application and system metrics
   - Counter, gauge, histogram, and summary metrics
   - Prometheus export format support
   - Real-time performance tracking

3. **Audit Logger** (`monitoring/audit_logger.py`)
   - Compliance-ready audit trails
   - User action tracking
   - Security event logging
   - Query and reporting capabilities

4. **Monitoring Middleware** (`api/middleware/monitoring_middleware.py`)
   - Automatic request/response logging
   - Performance measurement
   - Error tracking
   - Security event detection

5. **Monitoring API** (`api/endpoints/monitoring.py`)
   - Health check endpoints
   - Metrics export
   - Audit log queries
   - Performance statistics

## Features

### 1. Structured Logging

All logs are output in structured JSON format for easy parsing:

```json
{
  "timestamp": "2024-01-01T12:00:00.000Z",
  "level": "INFO",
  "logger": "api.endpoints.transcription",
  "module": "transcription",
  "function": "process_transcription",
  "line": 145,
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 123,
  "message": "Processing transcription request",
  "method": "POST",
  "path": "/api/transcription/process",
  "duration_ms": 1234.56
}
```

### 2. Correlation IDs

Every request is assigned a correlation ID that follows it through the entire request lifecycle:

- Generated automatically or accepted from `X-Correlation-ID` header
- Added to all log entries
- Returned in response headers
- Stored in audit logs

### 3. Metrics Collection

#### Metric Types

**Counters** - Cumulative values that only increase
```python
app_metrics.track_request(method="POST", path="/api/transcription", status_code=200, duration_ms=1234)
```

**Gauges** - Point-in-time measurements
```python
metrics_collector.record_gauge('websocket.connections.active', 45)
```

**Histograms** - Distribution of values
```python
metrics_collector.record_histogram('http.request.duration_ms', 234.5, labels={'path': '/api/transcription'})
```

**Summaries** - Statistical summaries over time windows
```python
metrics_collector.record_summary('transcription.processing_time', 120.5)
```

#### System Metrics

Automatically collected every minute:
- CPU usage (process and system-wide)
- Memory usage (RSS, VMS, percentage)
- Disk I/O statistics
- Network connections
- Thread count

### 4. Audit Logging

Comprehensive audit trail for compliance and security:

```python
audit_logger.log_event(
    event_type=AuditEventType.DATA_ACCESS,
    user_id=123,
    username="johndoe",
    resource_type="transcript",
    resource_id="456",
    action="view",
    result="success",
    details={"exported_format": "pdf"}
)
```

#### Audit Event Types

- **Authentication**: login, logout, register, password changes
- **Data Access**: view, create, update, delete, export, share
- **Security**: access denied, suspicious activity, rate limits
- **System**: settings changes, permission updates, API key management

### 5. Error Tracking

Automatic error tracking with categorization:

- Error counts by logger and function
- Recent error history with full context
- Exception type tracking
- Stack trace preservation

### 6. Performance Monitoring

Request performance tracking:

- Average, min, max response times
- 95th and 99th percentile latencies
- Slow request identification
- Endpoint-specific metrics

## Configuration

### Environment Variables

```bash
# Logging configuration
LOG_LEVEL=INFO                    # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE=logs/app.log             # Log file path
ENABLE_JSON_LOGGING=true          # Enable structured JSON logs

# Monitoring
ENABLE_ERROR_TRACKING=true        # Track errors for analysis
ENABLE_PERFORMANCE_TRACKING=true  # Track performance metrics
SLOW_REQUEST_THRESHOLD_MS=1000    # Threshold for slow request warnings

# Audit logging
AUDIT_LOG_RETENTION_DAYS=365      # How long to keep audit logs
AUDIT_BUFFER_SIZE=100             # Batch size for audit log writes
```

### Middleware Configuration

```python
app.add_middleware(
    MonitoringMiddleware,
    skip_paths=['/health', '/metrics'],  # Paths to skip
    log_request_body=False,               # Log request bodies
    log_response_body=True,               # Log error response bodies
    max_body_log_size=1024                # Max body size to log
)
```

## Usage

### 1. Basic Logging

```python
from monitoring.logger_config import get_logger

logger = get_logger(__name__)

# Simple logging
logger.info("Processing started")

# With context
logger.info(
    "User action performed",
    extra={
        'user_id': 123,
        'action': 'transcript_create',
        'duration_ms': 456
    }
)

# Error logging with exception
try:
    process_data()
except Exception as e:
    logger.exception("Processing failed", extra={'user_id': 123})
```

### 2. Metrics Tracking

```python
from monitoring.metrics_collector import app_metrics

# Track API request
app_metrics.track_request(
    method="POST",
    path="/api/transcription",
    status_code=200,
    duration_ms=1234.5
)

# Track transcription
app_metrics.track_transcription(
    duration_seconds=120.5,
    word_count=1500,
    language="en",
    success=True
)

# Track WebSocket event
app_metrics.track_websocket_event(
    event_type="transcript.updated",
    success=True
)

# Update active connections
app_metrics.update_active_connections(45)
```

### 3. Audit Logging

```python
from monitoring.audit_logger import audit_logger, AuditEventType

# Log authentication
audit_logger.log_authentication(
    user_id=123,
    username="johndoe",
    action="login",
    success=True,
    ip_address="192.168.1.1"
)

# Log data access
audit_logger.log_data_access(
    user_id=123,
    username="johndoe",
    action="export",
    resource_type="transcript",
    resource_id="456",
    success=True,
    details={"format": "pdf", "pages": 10}
)

# Log security event
audit_logger.log_security_event(
    event_type="suspicious",
    user_id=123,
    ip_address="192.168.1.1",
    details={"reason": "Multiple failed login attempts"}
)
```

### 4. Custom Context Logger

```python
from monitoring.logger_config import create_logger

# Create logger with default context
user_logger = create_logger(
    "user_actions",
    user_id=123,
    session_id="abc123"
)

# All logs will include user_id and session_id
user_logger.info("Action performed")  # Includes context automatically
```

## API Endpoints

### Health Check

```http
GET /api/monitoring/health

Response:
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "checks": {
    "database": "healthy",
    "api": "healthy"
  },
  "system": {
    "cpu_percent": 45.2,
    "memory_percent": 62.1,
    "disk_percent": 35.8
  }
}
```

### Metrics Export

```http
GET /api/monitoring/metrics?format=json

Response:
{
  "uptime_seconds": 3600,
  "counters": {
    "http.requests.total": 15000,
    "http.errors.total": 45
  },
  "gauges": {
    "websocket.connections.active": 123,
    "system.memory.rss": 512.5
  },
  "histograms": {
    "http.request.duration_ms": {
      "count": 15000,
      "min": 10.5,
      "max": 5000.2,
      "avg": 125.3,
      "p50": 95.0,
      "p95": 450.5,
      "p99": 1200.8
    }
  }
}
```

### Prometheus Format

```http
GET /api/monitoring/metrics?format=prometheus

Response:
# TYPE http_requests_total counter
http_requests_total{method="GET",path="/api/transcription",status="200"} 5000
http_requests_total{method="POST",path="/api/transcription",status="200"} 3000

# TYPE http_request_duration_ms histogram
http_request_duration_ms_bucket{le="10"} 100
http_request_duration_ms_bucket{le="50"} 5000
http_request_duration_ms_bucket{le="100"} 12000
http_request_duration_ms_bucket{le="+Inf"} 15000
http_request_duration_ms_sum 1879500
http_request_duration_ms_count 15000
```

### Audit Log Query

```http
GET /api/monitoring/logs/audit?event_type=user.login&limit=50

Response:
{
  "total": 45,
  "logs": [
    {
      "id": 123,
      "event_type": "user.login",
      "user_id": 456,
      "username": "johndoe",
      "ip_address": "192.168.1.1",
      "result": "success",
      "created_at": "2024-01-01T12:00:00Z"
    }
  ]
}
```

### Compliance Report

```http
GET /api/monitoring/logs/compliance-report?start_date=2024-01-01&end_date=2024-01-31

Response:
{
  "period": {
    "start": "2024-01-01T00:00:00Z",
    "end": "2024-01-31T23:59:59Z"
  },
  "statistics": {
    "total_events": 15234,
    "events_by_type": {
      "user.login": 523,
      "data.view": 8934,
      "data.export": 234
    },
    "unique_users": 156,
    "authentication_events": 789,
    "data_access_events": 12456,
    "security_events": 23
  }
}
```

## Monitoring Dashboard

### Grafana Integration

1. Add Prometheus data source:
   ```
   URL: http://your-api:8000/api/monitoring/metrics?format=prometheus
   ```

2. Import dashboard JSON from `monitoring/grafana-dashboard.json`

3. Key panels:
   - Request rate and latency
   - Error rate by endpoint
   - Active connections
   - System resources
   - Top slow endpoints

### Alerting Rules

Example Prometheus alerts:

```yaml
groups:
  - name: api_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowRequests
        expr: histogram_quantile(0.95, http_request_duration_ms) > 1000
        for: 5m
        annotations:
          summary: "95th percentile latency above 1s"
          
      - alert: HighMemoryUsage
        expr: system_memory_percent > 90
        for: 5m
        annotations:
          summary: "Memory usage above 90%"
```

## Best Practices

### 1. Logging

- Use appropriate log levels (DEBUG for development, INFO for production)
- Always include context (user_id, resource_id, etc.)
- Don't log sensitive data (passwords, tokens, PII)
- Use structured logging for machine parsing
- Include correlation IDs for request tracing

### 2. Metrics

- Track key business metrics (transcriptions, exports, shares)
- Monitor performance at multiple percentiles
- Set up alerting for anomalies
- Regular cleanup of old metrics data
- Use labels sparingly to avoid cardinality explosion

### 3. Audit Logging

- Log all security-relevant events
- Include enough context for investigation
- Implement retention policies
- Regular audit log reviews
- Export for compliance reporting

### 4. Performance

- Use buffered writing for high-volume logs
- Async processing where possible
- Implement log rotation
- Monitor logging overhead
- Use sampling for very high-traffic endpoints

## Troubleshooting

### Common Issues

1. **High disk usage from logs**
   - Check log rotation settings
   - Reduce log level if too verbose
   - Implement cleanup policies

2. **Performance impact**
   - Disable request body logging
   - Use sampling for metrics
   - Increase buffer sizes

3. **Missing logs**
   - Check correlation ID
   - Verify log level settings
   - Check middleware skip paths

### Debug Mode

Enable debug logging:

```python
# Environment variable
LOG_LEVEL=DEBUG

# Or programmatically
import logging
logging.getLogger('api').setLevel(logging.DEBUG)
```

## Security Considerations

1. **Log Sanitization**
   - Never log passwords or tokens
   - Mask sensitive fields
   - Implement PII detection

2. **Access Control**
   - Restrict monitoring endpoints to admins
   - Audit log access to audit logs
   - Implement role-based access

3. **Data Retention**
   - Define retention policies
   - Implement automatic cleanup
   - Secure log storage

4. **Compliance**
   - Meet regulatory requirements
   - Regular audit reviews
   - Incident investigation support