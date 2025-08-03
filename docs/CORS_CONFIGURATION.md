# CORS Configuration Guide

## Overview

Cross-Origin Resource Sharing (CORS) is configured to allow secure communication between the API and frontend applications from different origins. The implementation provides environment-specific configurations with sensible defaults for development, staging, and production.

## Quick Start

### Basic Setup

```python
from fastapi import FastAPI
from api.middleware.cors_config import setup_cors

app = FastAPI()

# Use default configuration based on environment
setup_cors(app)
```

### Custom Configuration

```python
from api.middleware.cors_config import create_cors_config, setup_cors

# Create custom configuration
cors_config = create_cors_config(
    allowed_origins=["https://app.yourdomain.com"],
    allow_credentials=True,
    max_age=86400  # 24 hours
)

setup_cors(app, cors_config)
```

## Environment Configuration

### Environment Variables

Configure CORS behavior through environment variables:

```bash
# Basic Configuration
ENVIRONMENT=production              # development, staging, production

# Allowed Origins (comma-separated)
CORS_ALLOWED_ORIGINS=https://app.example.com,https://admin.example.com

# HTTP Methods (comma-separated)
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS

# Request Headers (comma-separated)
CORS_ALLOWED_HEADERS=Content-Type,Authorization,X-API-Key

# Response Headers exposed to client (comma-separated)
CORS_EXPOSED_HEADERS=X-Request-ID,X-RateLimit-Limit,X-RateLimit-Remaining

# Allow credentials (cookies, auth headers)
CORS_ALLOW_CREDENTIALS=true

# Preflight cache duration in seconds
CORS_MAX_AGE=3600
```

### Default Configurations by Environment

#### Development
- **Origins**: All localhost ports (3000, 3001, 5173, 8080, 8501)
- **Credentials**: Allowed
- **Methods**: All standard methods
- **Headers**: Common headers
- **Max Age**: 1 hour

#### Staging
- **Origins**: Staging domains + localhost for testing
- **Credentials**: Allowed
- **Methods**: All standard methods
- **Headers**: Common headers
- **Max Age**: 1 hour

#### Production
- **Origins**: Specific production domains only
- **Credentials**: Allowed
- **Methods**: Standard methods
- **Headers**: Security-conscious set
- **Max Age**: 24 hours

## Configuration Examples

### Public API (No Authentication)

```python
from api.middleware.cors_config import CORSPresets

# Allow all origins, no credentials
cors_config = CORSPresets.public_api()
setup_cors(app, cors_config)
```

### Private API (Authentication Required)

```python
from api.middleware.cors_config import CORSPresets

# Strict origins, allow credentials
cors_config = CORSPresets.private_api()
setup_cors(app, cors_config)
```

### Mobile Application

```python
from api.middleware.cors_config import CORSPresets

# Mobile apps don't have origin restrictions
cors_config = CORSPresets.mobile_app()
setup_cors(app, cors_config)
```

### Multi-Domain Setup

```python
cors_config = create_cors_config(
    allowed_origins=[
        "https://app.example.com",
        "https://admin.example.com",
        "https://mobile.example.com",
        "https://*.partners.example.com"  # Wildcard subdomain
    ],
    allow_credentials=True
)
```

## Advanced Configuration

### Dynamic CORS for Multi-Tenant Applications

```python
from api.middleware.cors_config import DynamicCORSConfig

# Define tenant resolver
def resolve_tenant(request):
    # Extract tenant from subdomain, header, or JWT
    return request.headers.get("X-Tenant-ID", "default")

# Create dynamic configuration
dynamic_cors = DynamicCORSConfig(resolve_tenant)

# Add tenant-specific configurations
dynamic_cors.add_tenant_config("tenant1", create_cors_config(
    allowed_origins=["https://tenant1.app.com"]
))

dynamic_cors.add_tenant_config("tenant2", create_cors_config(
    allowed_origins=["https://tenant2.app.com"]
))
```

### Custom Origin Validation

```python
from api.middleware.cors_config import validate_origin

# Define allowed patterns
allowed_patterns = [
    "https://*.example.com",              # Wildcard subdomain
    "^https://app-[0-9]+\\.example\\.com$"  # Regex pattern
]

# Validate origin
origin = "https://app-123.example.com"
if validate_origin(origin, allowed_patterns):
    # Origin is allowed
    pass
```

### Conditional CORS Based on Request

```python
def get_cors_config(request):
    # Different CORS for different API versions
    if request.url.path.startswith("/api/v2"):
        return create_cors_config(
            allowed_origins=["https://v2.app.com"],
            allow_credentials=True
        )
    else:
        return create_cors_config(
            allowed_origins=["https://legacy.app.com"],
            allow_credentials=False
        )
```

## Security Best Practices

### 1. Restrict Origins in Production

Never use wildcard origins (`*`) in production when credentials are allowed:

```python
# ❌ Bad - Security vulnerability
cors_config = create_cors_config(
    allowed_origins=["*"],
    allow_credentials=True  # Dangerous combination!
)

# ✅ Good - Explicit origins
cors_config = create_cors_config(
    allowed_origins=["https://app.example.com"],
    allow_credentials=True
)
```

### 2. Validate Dynamic Origins

When accepting dynamic origins, always validate:

```python
def is_origin_trusted(origin: str) -> bool:
    # Implement your validation logic
    trusted_domains = ["example.com", "trusted-partner.com"]
    
    from urllib.parse import urlparse
    parsed = urlparse(origin)
    
    # Check if domain is trusted
    for domain in trusted_domains:
        if parsed.netloc.endswith(domain):
            return True
    
    return False
```

### 3. Limit Exposed Headers

Only expose necessary headers to the client:

```python
cors_config = create_cors_config(
    exposed_headers=[
        "X-Request-ID",      # For debugging
        "X-RateLimit-Limit", # Rate limit info
        "X-RateLimit-Remaining"
        # Don't expose: X-Internal-User-ID, X-Database-Query-Time
    ]
)
```

### 4. Use Appropriate Max Age

Balance between performance and security:

```python
# Development - Short cache for quick changes
max_age=3600  # 1 hour

# Production - Longer cache for performance
max_age=86400  # 24 hours

# Sensitive operations - No cache
max_age=0
```

## Client-Side Implementation

### JavaScript/Fetch API

```javascript
// Simple request
fetch('https://api.example.com/data', {
    method: 'GET',
    credentials: 'include',  // Include cookies
    headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }
})
.then(response => response.json())
.then(data => console.log(data));

// Handle CORS errors
fetch('https://api.example.com/data')
    .catch(error => {
        if (error.message.includes('CORS')) {
            console.error('CORS error - check allowed origins');
        }
    });
```

### Axios Configuration

```javascript
import axios from 'axios';

// Configure axios defaults
axios.defaults.withCredentials = true;
axios.defaults.headers.common['Content-Type'] = 'application/json';

// Create instance with CORS config
const api = axios.create({
    baseURL: 'https://api.example.com',
    withCredentials: true,
    headers: {
        'Content-Type': 'application/json'
    }
});
```

### React Example

```jsx
import { useEffect, useState } from 'react';

function DataComponent() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        fetch('https://api.example.com/data', {
            credentials: 'include',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('token')}`
            }
        })
        .then(res => {
            if (!res.ok) throw new Error('Failed to fetch');
            return res.json();
        })
        .then(setData)
        .catch(err => {
            if (err.name === 'TypeError' && err.message === 'Failed to fetch') {
                setError('CORS error or network issue');
            } else {
                setError(err.message);
            }
        });
    }, []);
    
    return (
        <div>
            {error && <div>Error: {error}</div>}
            {data && <div>Data: {JSON.stringify(data)}</div>}
        </div>
    );
}
```

## Troubleshooting

### Common Issues

#### 1. "No 'Access-Control-Allow-Origin' header"

**Problem**: Origin not in allowed list
```
Access to fetch at 'https://api.example.com' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header
```

**Solution**: Add origin to allowed list
```bash
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://app.example.com
```

#### 2. "Credentials flag is true, but 'Access-Control-Allow-Credentials' is not"

**Problem**: Credentials not allowed
```javascript
// Client sends credentials
fetch(url, { credentials: 'include' })
```

**Solution**: Enable credentials
```bash
CORS_ALLOW_CREDENTIALS=true
```

#### 3. "Request header field X-Custom is not allowed"

**Problem**: Custom header not in allowed list

**Solution**: Add header to allowed list
```bash
CORS_ALLOWED_HEADERS=Content-Type,Authorization,X-Custom
```

#### 4. Preflight Request Fails

**Problem**: OPTIONS request blocked

**Solution**: Ensure OPTIONS is in allowed methods
```bash
CORS_ALLOWED_METHODS=GET,POST,PUT,DELETE,OPTIONS
```

### Debug Mode

Enable CORS debugging:

```python
import logging

# Enable debug logging
logging.getLogger("fastapi.middleware.cors").setLevel(logging.DEBUG)

# Custom debug middleware
@app.middleware("http")
async def cors_debug_middleware(request: Request, call_next):
    origin = request.headers.get("origin")
    method = request.method
    
    logger.info(f"CORS Request: {method} from {origin}")
    logger.info(f"Headers: {dict(request.headers)}")
    
    response = await call_next(request)
    
    logger.info(f"CORS Response Headers: {dict(response.headers)}")
    
    return response
```

### Testing CORS

#### Using curl

```bash
# Test preflight request
curl -X OPTIONS https://api.example.com/data \
  -H "Origin: https://app.example.com" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Content-Type" \
  -v

# Test actual request
curl -X POST https://api.example.com/data \
  -H "Origin: https://app.example.com" \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' \
  -v
```

#### Browser DevTools

1. Open Network tab
2. Look for OPTIONS requests (preflight)
3. Check response headers:
   - `Access-Control-Allow-Origin`
   - `Access-Control-Allow-Credentials`
   - `Access-Control-Allow-Methods`
   - `Access-Control-Allow-Headers`

## Migration Guide

### From Manual CORS Headers

```python
# Old approach
@app.get("/data")
async def get_data(response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    return {"data": "value"}

# New approach
setup_cors(app)  # Configure once for all endpoints

@app.get("/data")
async def get_data():
    return {"data": "value"}
```

### From Other CORS Libraries

```python
# From flask-cors
from flask_cors import CORS
CORS(app, origins=["https://example.com"])

# To FastAPI
from api.middleware.cors_config import setup_cors, create_cors_config
cors_config = create_cors_config(allowed_origins=["https://example.com"])
setup_cors(app, cors_config)
```

## Performance Considerations

1. **Preflight Caching**: Use appropriate `max_age` to reduce preflight requests
2. **Simple Requests**: Design APIs to use simple requests when possible
3. **Origin Validation**: Use exact matches instead of wildcards for better performance
4. **Header Minimization**: Only allow/expose necessary headers

## Monitoring

Track CORS-related metrics:

```python
# Log CORS requests
@app.middleware("http")
async def cors_metrics(request: Request, call_next):
    origin = request.headers.get("origin", "no-origin")
    
    # Track metrics
    metrics.increment("cors.requests", tags={"origin": origin})
    
    if request.method == "OPTIONS":
        metrics.increment("cors.preflight_requests", tags={"origin": origin})
    
    response = await call_next(request)
    
    if response.status_code == 403 and "CORS" in response.body:
        metrics.increment("cors.blocked_requests", tags={"origin": origin})
    
    return response
```