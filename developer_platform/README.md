# Developer Platform

A comprehensive API and developer platform for the transcription service, providing REST and GraphQL APIs, SDKs, documentation, and monitoring capabilities.

## Features

### 1. **API Gateway**
- Complete API authentication and authorization system
- API key management with different tiers (Development, Production, Sandbox)
- Token bucket rate limiting with configurable plans
- IP and origin whitelisting
- Request/response logging and tracking
- Webhook management for event notifications

### 2. **GraphQL API**
- Flexible data queries with GraphQL
- Real-time subscriptions for live updates
- Type-safe schema with comprehensive types
- Efficient data fetching with minimal requests
- Support for complex queries and mutations

### 3. **SDK Generator**
- Automatic SDK generation for 8 languages:
  - Python
  - JavaScript/Node.js
  - TypeScript
  - Go
  - Java
  - C#/.NET
  - Ruby
  - PHP
- Type-safe clients with full API coverage
- Built-in error handling and retry logic
- Comprehensive documentation and examples

### 4. **API Documentation**
- Multi-format documentation generation:
  - Markdown
  - HTML with syntax highlighting
  - OpenAPI 3.0 specification
  - Postman collection
- Interactive API explorer for testing
- Code examples in multiple languages
- Webhook event documentation

### 5. **API Monitoring & Analytics**
- Real-time performance metrics
- Usage analytics and quotas
- SLA compliance reporting
- Alert system with configurable rules
- Geographic usage distribution
- Cost estimation and billing insights

## Installation

```bash
# The developer platform is included with the main application
pip install -r requirements.txt
```

## Quick Start

### Setting Up API Gateway

```python
from developer_platform import APIGateway, RateLimitPlan

# Initialize gateway
gateway = APIGateway(secret_key="your-secret-key")

# Generate API key
raw_key, api_key = gateway.generate_api_key(
    organization_id="org_123",
    user_id="user_456",
    name="Production API Key",
    key_type=APIKeyType.PRODUCTION,
    rate_limit_plan=RateLimitPlan.GROWTH,
    permissions=[
        "transcription.create",
        "transcription.read",
        "entities.read"
    ]
)

print(f"API Key: {raw_key}")
```

### Using GraphQL API

```python
from developer_platform import GraphQLHandler, graphql_schema

# Initialize handler
handler = GraphQLHandler(graphql_schema)

# Execute query
query = """
    query GetTranscription($id: ID!) {
        transcription(id: $id) {
            id
            status
            text
            entities {
                text
                type
                confidence
            }
        }
    }
"""

result = await handler.handle_request(
    query,
    variables={"id": "trans_123"}
)
```

### Generating SDKs

```python
from developer_platform import SDKGenerator, SDKLanguage, SDKConfig

# Configure SDK
config = SDKConfig(
    api_name="TranscriptionAPI",
    api_version="v1",
    base_url="https://api.transcription.io",
    package_name="transcription-sdk"
)

# Generate SDK
generator = SDKGenerator(config)
python_sdk = generator.generate_sdk(SDKLanguage.PYTHON)

# Save files
for filename, content in python_sdk.items():
    with open(f"sdk/python/{filename}", "w") as f:
        f.write(content)
```

### Creating API Documentation

```python
from developer_platform import APIDocumentationGenerator

# Initialize generator
doc_gen = APIDocumentationGenerator(
    api_title="Transcription API",
    api_version="v1",
    base_url="https://api.transcription.io"
)

# Generate documentation
markdown_docs = doc_gen.generate_markdown_docs()
openapi_spec = doc_gen.generate_openapi_spec()
postman_collection = doc_gen.generate_postman_collection()

# Save documentation
with open("API.md", "w") as f:
    f.write(markdown_docs)
```

### Monitoring API Usage

```python
from developer_platform import APIMonitor, AlertSeverity, MetricType

# Initialize monitor
monitor = APIMonitor()

# Set quotas
monitor.set_quota("org_123", "requests", 10000, "monthly")

# Create alert rules
monitor.create_alert_rule(
    name="High Response Time",
    metric_type=MetricType.RESPONSE_TIME,
    condition="gt",
    threshold=1000,
    severity=AlertSeverity.WARNING
)

# Record requests
monitor.record_request(
    api_key_id="key_abc",
    endpoint="/api/v1/transcriptions",
    method="POST",
    status_code=200,
    response_time_ms=150
)

# Get analytics
analytics = monitor.get_usage_analytics(
    organization_id="org_123",
    start_date=date.today() - timedelta(days=30),
    end_date=date.today()
)
```

## API Endpoints

### REST API

#### Authentication
All requests require an API key in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

#### Transcription Endpoints

- `POST /api/v1/transcriptions` - Create new transcription
- `GET /api/v1/transcriptions/{id}` - Get transcription details
- `GET /api/v1/transcriptions` - List transcriptions
- `DELETE /api/v1/transcriptions/{id}` - Delete transcription

#### Entity Extraction

- `GET /api/v1/transcriptions/{id}/entities` - Get entities
- `POST /api/v1/transcriptions/{id}/entities/extract` - Extract entities

#### Summary Generation

- `POST /api/v1/transcriptions/{id}/summary` - Generate summary
- `GET /api/v1/transcriptions/{id}/summary` - Get summary

### GraphQL API

Single endpoint: `POST /api/graphql`

Example query:
```graphql
query {
  transcriptions(first: 10, filter: {status: COMPLETED}) {
    id
    fileName
    text
    entities {
      text
      type
    }
  }
}
```

## Rate Limiting

Rate limits are enforced based on subscription plan:

| Plan | Requests/Hour | Burst Size |
|------|--------------|------------|
| Free | 100 | 10 |
| Starter | 1,000 | 50 |
| Growth | 10,000 | 200 |
| Scale | 100,000 | 1,000 |
| Enterprise | Custom | Custom |

Rate limit headers:
- `X-RateLimit-Limit`: Your rate limit
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Webhooks

### Registering Webhooks

```python
webhook = gateway.register_webhook(
    organization_id="org_123",
    url="https://your-app.com/webhooks",
    events=[
        WebhookEvent.TRANSCRIPTION_COMPLETED,
        WebhookEvent.ENTITY_EXTRACTION_COMPLETED
    ]
)
```

### Webhook Events

- `transcription.started` - Processing started
- `transcription.completed` - Processing completed
- `transcription.failed` - Processing failed
- `entity_extraction.completed` - Entities extracted
- `summary.generated` - Summary created
- `quota.warning` - 80% quota reached
- `quota.exceeded` - Quota exceeded

### Webhook Security

Verify webhook signatures:

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

## SDK Examples

### Python
```python
from transcription_sdk import TranscriptionClient

client = TranscriptionClient("your-api-key")

# Create transcription
result = client.create_transcription(
    file_url="https://example.com/audio.mp3",
    language="en-US"
)

# Get status
transcription = client.get_transcription(result["id"])
print(transcription["text"])
```

### JavaScript
```javascript
const { TranscriptionClient } = require('transcription-sdk');

const client = new TranscriptionClient('your-api-key');

async function transcribe() {
  const result = await client.createTranscription({
    fileUrl: 'https://example.com/audio.mp3',
    language: 'en-US'
  });
  
  const transcription = await client.getTranscription(result.id);
  console.log(transcription.text);
}
```

### Go
```go
import "github.com/transcription/sdk-go"

client := sdk.NewClient("your-api-key")

result, err := client.CreateTranscription(sdk.TranscriptionOptions{
    FileURL: "https://example.com/audio.mp3",
})

transcription, err := client.GetTranscription(result.ID)
fmt.Println(transcription.Text)
```

## Monitoring & Analytics

### Performance Metrics
- Average response time
- P95/P99 latency
- Error rates
- Request throughput
- Data transfer volumes

### Usage Analytics
- API calls by endpoint
- Geographic distribution
- Top users and API keys
- Feature adoption rates
- Cost analysis

### SLA Reporting
- Monthly uptime percentage
- Response time compliance
- Error rate tracking
- SLA credit calculation

## Best Practices

1. **API Keys**
   - Use separate keys for development and production
   - Rotate keys regularly
   - Restrict keys by IP when possible
   - Monitor key usage for anomalies

2. **Rate Limiting**
   - Implement exponential backoff on 429 errors
   - Cache responses when appropriate
   - Use batch endpoints for bulk operations
   - Monitor your usage to avoid limits

3. **Webhooks**
   - Implement idempotent webhook handlers
   - Verify webhook signatures
   - Respond quickly (< 5 seconds)
   - Implement retry logic for failures

4. **Error Handling**
   - Check response status codes
   - Parse error messages for details
   - Implement appropriate retry strategies
   - Log errors for debugging

5. **Performance**
   - Use GraphQL for complex queries
   - Paginate large result sets
   - Compress request/response bodies
   - Use appropriate caching strategies

## Troubleshooting

### Common Issues

1. **Authentication Errors (401)**
   - Verify API key is correct
   - Check key hasn't expired
   - Ensure proper Authorization header format

2. **Rate Limit Errors (429)**
   - Check Retry-After header
   - Implement exponential backoff
   - Consider upgrading plan

3. **Server Errors (500)**
   - Retry with exponential backoff
   - Check service status page
   - Contact support if persistent

4. **Timeout Errors**
   - Increase client timeout settings
   - Use webhooks for long operations
   - Check file sizes and formats

## Architecture

```
developer_platform/
├── api_gateway.py      # Authentication, rate limiting, routing
├── graphql_api.py      # GraphQL schema and resolvers
├── sdk_generator.py    # Multi-language SDK generation
├── api_documentation.py # Documentation and explorer
├── api_monitoring.py   # Usage tracking and analytics
├── __init__.py        # Package exports
└── README.md          # This file

Integration Points:
├── Database          # API keys, usage metrics
├── Message Queue     # Webhook delivery
├── Cache            # Rate limiting, responses
├── Object Storage   # SDK downloads
└── Monitoring       # Metrics and alerts
```

## Future Enhancements

- [ ] OAuth 2.0 authentication support
- [ ] API versioning with deprecation notices
- [ ] Client SDK package managers (npm, pip, etc.)
- [ ] Advanced analytics dashboards
- [ ] API marketplace for third-party integrations
- [ ] Batch API endpoints
- [ ] WebSocket support for real-time updates
- [ ] Custom webhook transformations

## Support

For API support:
- Documentation: https://docs.transcription.io/api
- Status page: https://status.transcription.io
- Support email: api-support@transcription.io
- Community forum: https://community.transcription.io

## License

The developer platform is part of the Transcription Platform and follows the same license terms.