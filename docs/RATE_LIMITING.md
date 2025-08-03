# Rate Limiting Documentation

## Overview

The API implements comprehensive rate limiting to ensure fair usage and protect against abuse. The system uses a token bucket algorithm with support for both local (in-memory) and distributed (Redis-based) rate limiting.

## Features

- **Token Bucket Algorithm**: Smooth rate limiting with burst capacity
- **Distributed Rate Limiting**: Redis support for multi-instance deployments
- **Flexible Configuration**: Per-endpoint and per-user tier limits
- **Graceful Degradation**: Falls back to local limiting if Redis is unavailable
- **Detailed Headers**: Standard rate limit headers in responses
- **Cost-based Limiting**: Different operations consume different amounts from quota

## Configuration

### Environment Variables

```bash
# Redis configuration for distributed rate limiting
REDIS_URL=redis://localhost:6379/0

# Default rate limits
DEFAULT_RATE_LIMIT=100        # Requests per window
DEFAULT_RATE_WINDOW=3600      # Window in seconds (1 hour)

# Enable/disable rate limiting
ENABLE_RATE_LIMITING=true
```

### Endpoint-Specific Limits

Different endpoints have different rate limits based on their resource intensity:

| Endpoint | Limit | Window | Notes |
|----------|-------|---------|-------|
| `/api/health` | 1000 | 60s | Health checks |
| `/api/auth/login` | 10 | 5 min | Prevent brute force |
| `/api/auth/register` | 5 | 1 hour | Prevent spam accounts |
| `/api/transcription/upload` | 50 | 1 hour | File upload limit |
| `/api/transcription/process` | 20 | 1 hour | CPU-intensive |
| `/api/export` | 30 | 1 hour | Resource-intensive |
| `/api/search` | 100 | 5 min | Database queries |

### User Tier Limits

Different subscription tiers have different overall limits:

| Tier | Requests/Hour | Notes |
|------|---------------|-------|
| Free | 100 | Basic usage |
| Basic | 500 | Small projects |
| Pro | 2,000 | Professional use |
| Enterprise | 10,000 | High-volume usage |

## Implementation

### Basic Setup

```python
from api.middleware.rate_limiter import RateLimitMiddleware, create_rate_limiter

# Create rate limiter
rate_limiter = create_rate_limiter(redis_url=os.getenv("REDIS_URL"))

# Add middleware to FastAPI app
app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=rate_limiter,
    skip_paths=["/docs", "/redoc", "/openapi.json"]
)
```

### Custom Endpoint Limits

```python
from api.middleware.rate_limiter import rate_limit

@app.post("/api/expensive-operation")
@rate_limit(limit=10, window=3600)  # 10 requests per hour
async def expensive_operation(request: Request):
    # Your endpoint logic
    return {"status": "completed"}
```

### Request Cost Calculation

Some operations consume more from the rate limit quota:

```python
# Default cost calculation
async def calculate_cost(request: Request) -> int:
    if request.url.path.startswith("/api/transcription/process"):
        return 5  # Heavy operation
    elif request.url.path.startswith("/api/export"):
        return 3  # Medium operation
    elif request.method == "POST":
        return 2  # Write operation
    return 1  # Default cost
```

## Response Headers

All rate-limited responses include standard headers:

```http
X-RateLimit-Limit: 100      # Total allowed requests
X-RateLimit-Remaining: 45   # Remaining requests in window
X-RateLimit-Reset: 1640995200  # Unix timestamp when limit resets
Retry-After: 3600           # Seconds until retry (only on 429)
```

## Error Responses

When rate limit is exceeded:

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 3600
Content-Type: application/json

{
  "error": "Rate limit exceeded",
  "retry_after": 3600,
  "limit": 100,
  "reset": 1640995200
}
```

## Client Implementation

### Python Example

```python
import requests
import time

def make_request_with_retry(url, **kwargs):
    while True:
        response = requests.get(url, **kwargs)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
            
        return response

# Check remaining quota
response = make_request_with_retry("https://api.example.com/endpoint")
remaining = response.headers.get('X-RateLimit-Remaining')
print(f"Remaining requests: {remaining}")
```

### JavaScript Example

```javascript
async function fetchWithRateLimit(url, options = {}) {
  while (true) {
    const response = await fetch(url, options);
    
    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
      console.log(`Rate limited. Waiting ${retryAfter} seconds...`);
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      continue;
    }
    
    // Log remaining quota
    const remaining = response.headers.get('X-RateLimit-Remaining');
    console.log(`Remaining requests: ${remaining}`);
    
    return response;
  }
}
```

## Monitoring

### Metrics

The rate limiter exposes metrics for monitoring:

- `rate_limit.requests.allowed` - Successful requests
- `rate_limit.requests.denied` - Rate-limited requests
- `rate_limit.requests.cost` - Total cost consumed
- `rate_limit.buckets.active` - Active rate limit buckets

### Logging

Rate limit events are logged for analysis:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "WARNING",
  "logger": "api.middleware.rate_limiter",
  "message": "Rate limit exceeded",
  "user_id": 123,
  "endpoint": "/api/transcription/process",
  "limit": 20,
  "window": 3600
}
```

## Best Practices

### For API Providers

1. **Set Reasonable Limits**: Balance between preventing abuse and allowing legitimate usage
2. **Use Redis for Production**: Ensures consistent limits across multiple instances
3. **Monitor Usage**: Track rate limit metrics to adjust limits
4. **Provide Clear Documentation**: Help users understand limits and implement retry logic
5. **Implement Graceful Degradation**: Service should work even if rate limiter fails

### For API Consumers

1. **Implement Retry Logic**: Handle 429 responses gracefully
2. **Respect Retry-After**: Don't retry before the specified time
3. **Monitor Your Usage**: Track remaining quota from headers
4. **Cache Responses**: Reduce unnecessary API calls
5. **Use Webhooks**: For long-running operations instead of polling

## Advanced Configuration

### Custom Identifier Extraction

```python
async def extract_api_key(request: Request) -> str:
    # Extract from header
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api_key:{api_key}"
    
    # Extract from query parameter
    api_key = request.query_params.get("api_key")
    if api_key:
        return f"api_key:{api_key}"
    
    # Fall back to IP
    return f"ip:{request.client.host}"

app.add_middleware(
    RateLimitMiddleware,
    rate_limiter=rate_limiter,
    identifier_extractor=extract_api_key
)
```

### Dynamic Rate Limits

```python
class DynamicRateLimiter(RateLimiter):
    async def get_user_limit(self, user_id: int) -> dict:
        # Fetch from database
        user = await get_user(user_id)
        
        # Custom limits based on user status
        if user.is_premium:
            return {"limit": 5000, "window": 3600}
        elif user.is_verified:
            return {"limit": 1000, "window": 3600}
        else:
            return {"limit": 100, "window": 3600}
```

## Troubleshooting

### Common Issues

1. **Rate limit hit immediately**
   - Check if identifier is correctly extracted
   - Verify Redis connection is working
   - Check for shared IP addresses (corporate networks)

2. **Inconsistent limits across instances**
   - Ensure all instances use same Redis
   - Check Redis connectivity
   - Verify time synchronization

3. **Performance impact**
   - Use Redis pipeline for batch operations
   - Implement local caching for read-heavy operations
   - Consider increasing rate limit windows

### Debug Mode

Enable debug logging for rate limiter:

```python
import logging

logging.getLogger("api.middleware.rate_limiter").setLevel(logging.DEBUG)
```

This will log:
- Identifier extraction
- Rate limit checks
- Redis operations
- Fallback to local limiting

## Security Considerations

1. **Prevent Bypass Attempts**
   - Validate all identifiers
   - Don't expose internal limits in errors
   - Log suspicious patterns

2. **DDoS Protection**
   - Rate limiter is first line of defense
   - Combine with firewall rules
   - Use CDN for static content

3. **API Key Security**
   - Hash API keys before using as identifiers
   - Rotate keys regularly
   - Monitor for leaked keys