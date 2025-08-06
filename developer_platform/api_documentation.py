"""
API Documentation Generator and Interactive Explorer

Generates comprehensive API documentation with interactive testing capabilities
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field
import json
import markdown
import textwrap

class DocFormat(str, Enum):
    """Documentation output formats"""
    MARKDOWN = "markdown"
    HTML = "html"
    OPENAPI = "openapi"
    POSTMAN = "postman"
    SWAGGER = "swagger"

class ParameterType(str, Enum):
    """API parameter types"""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"

class APIParameter(BaseModel):
    """API parameter definition"""
    name: str
    type: ParameterType
    location: str  # query, path, header, body
    required: bool = False
    description: str
    default: Optional[Any] = None
    example: Optional[Any] = None
    constraints: Optional[Dict[str, Any]] = None

class APIResponse(BaseModel):
    """API response definition"""
    status_code: int
    description: str
    content_type: str = "application/json"
    schema: Dict[str, Any]
    example: Optional[Dict[str, Any]] = None

class APIEndpointDoc(BaseModel):
    """API endpoint documentation"""
    path: str
    method: str
    summary: str
    description: str
    tags: List[str] = []
    parameters: List[APIParameter] = []
    request_body: Optional[Dict[str, Any]] = None
    responses: List[APIResponse] = []
    security: List[str] = ["api_key"]
    rate_limit: Optional[str] = None
    examples: List[Dict[str, Any]] = []

class APIDocumentationGenerator:
    """Generate API documentation in multiple formats"""
    
    def __init__(self, api_title: str, api_version: str, base_url: str):
        self.api_title = api_title
        self.api_version = api_version
        self.base_url = base_url
        self.endpoints = self._define_endpoints()
    
    def _define_endpoints(self) -> List[APIEndpointDoc]:
        """Define all API endpoints"""
        endpoints = []
        
        # Transcription endpoints
        endpoints.append(APIEndpointDoc(
            path="/api/v1/transcriptions",
            method="POST",
            summary="Create Transcription",
            description="Create a new transcription job from audio or video file",
            tags=["Transcriptions"],
            parameters=[
                APIParameter(
                    name="X-API-Key",
                    type=ParameterType.STRING,
                    location="header",
                    required=True,
                    description="Your API key for authentication"
                )
            ],
            request_body={
                "type": "object",
                "required": ["file_url"],
                "properties": {
                    "file_url": {
                        "type": "string",
                        "description": "URL of the audio/video file to transcribe",
                        "example": "https://example.com/audio.mp3"
                    },
                    "language": {
                        "type": "string",
                        "description": "Language code (ISO 639-1)",
                        "example": "en-US"
                    },
                    "speaker_count": {
                        "type": "integer",
                        "description": "Number of speakers for diarization",
                        "example": 2
                    },
                    "vocabulary": {
                        "type": "array",
                        "description": "Custom vocabulary words",
                        "items": {"type": "string"}
                    },
                    "auto_summarize": {
                        "type": "boolean",
                        "description": "Generate summary automatically",
                        "default": False
                    },
                    "webhook_url": {
                        "type": "string",
                        "description": "Webhook URL for notifications"
                    }
                }
            },
            responses=[
                APIResponse(
                    status_code=201,
                    description="Transcription created successfully",
                    schema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "status": {"type": "string"},
                            "created_at": {"type": "string"},
                            "estimated_completion": {"type": "string"}
                        }
                    },
                    example={
                        "id": "trans_abc123",
                        "status": "pending",
                        "created_at": "2024-01-15T10:30:00Z",
                        "estimated_completion": "2024-01-15T10:35:00Z"
                    }
                ),
                APIResponse(
                    status_code=400,
                    description="Invalid request",
                    schema={
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"},
                            "details": {"type": "object"}
                        }
                    }
                ),
                APIResponse(
                    status_code=401,
                    description="Authentication failed",
                    schema={
                        "type": "object",
                        "properties": {
                            "error": {"type": "string"}
                        }
                    }
                )
            ],
            rate_limit="1000 requests/hour",
            examples=[
                {
                    "title": "Basic transcription",
                    "request": {
                        "file_url": "https://example.com/meeting.mp3",
                        "language": "en-US"
                    },
                    "response": {
                        "id": "trans_abc123",
                        "status": "pending"
                    }
                },
                {
                    "title": "With speaker diarization",
                    "request": {
                        "file_url": "https://example.com/interview.mp3",
                        "language": "en-US",
                        "speaker_count": 2,
                        "auto_summarize": True
                    }
                }
            ]
        ))
        
        endpoints.append(APIEndpointDoc(
            path="/api/v1/transcriptions/{transcription_id}",
            method="GET",
            summary="Get Transcription",
            description="Retrieve transcription details and text",
            tags=["Transcriptions"],
            parameters=[
                APIParameter(
                    name="transcription_id",
                    type=ParameterType.STRING,
                    location="path",
                    required=True,
                    description="Transcription ID",
                    example="trans_abc123"
                ),
                APIParameter(
                    name="include_segments",
                    type=ParameterType.BOOLEAN,
                    location="query",
                    description="Include detailed segments",
                    default=False
                )
            ],
            responses=[
                APIResponse(
                    status_code=200,
                    description="Transcription details",
                    schema={
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "status": {"type": "string"},
                            "file_name": {"type": "string"},
                            "duration": {"type": "number"},
                            "language": {"type": "string"},
                            "text": {"type": "string"},
                            "confidence": {"type": "number"},
                            "word_count": {"type": "integer"},
                            "segments": {"type": "array"}
                        }
                    }
                )
            ]
        ))
        
        # Entity extraction endpoints
        endpoints.append(APIEndpointDoc(
            path="/api/v1/transcriptions/{transcription_id}/entities",
            method="GET",
            summary="Extract Entities",
            description="Get named entities from transcription",
            tags=["Entity Extraction"],
            parameters=[
                APIParameter(
                    name="transcription_id",
                    type=ParameterType.STRING,
                    location="path",
                    required=True,
                    description="Transcription ID"
                ),
                APIParameter(
                    name="type",
                    type=ParameterType.STRING,
                    location="query",
                    description="Filter by entity type",
                    example="PERSON"
                ),
                APIParameter(
                    name="min_confidence",
                    type=ParameterType.NUMBER,
                    location="query",
                    description="Minimum confidence score",
                    default=0.7
                )
            ],
            responses=[
                APIResponse(
                    status_code=200,
                    description="Extracted entities",
                    schema={
                        "type": "object",
                        "properties": {
                            "entities": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "text": {"type": "string"},
                                        "type": {"type": "string"},
                                        "confidence": {"type": "number"},
                                        "start_time": {"type": "number"},
                                        "end_time": {"type": "number"}
                                    }
                                }
                            },
                            "total_count": {"type": "integer"}
                        }
                    }
                )
            ]
        ))
        
        # GraphQL endpoint
        endpoints.append(APIEndpointDoc(
            path="/api/graphql",
            method="POST",
            summary="GraphQL API",
            description="GraphQL endpoint for flexible queries",
            tags=["GraphQL"],
            request_body={
                "type": "object",
                "required": ["query"],
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "GraphQL query"
                    },
                    "variables": {
                        "type": "object",
                        "description": "Query variables"
                    },
                    "operationName": {
                        "type": "string",
                        "description": "Operation name"
                    }
                }
            },
            examples=[
                {
                    "title": "List transcriptions",
                    "request": {
                        "query": """
                            query ListTranscriptions($first: Int) {
                                transcriptions(first: $first) {
                                    id
                                    fileName
                                    status
                                    createdAt
                                }
                            }
                        """,
                        "variables": {"first": 10}
                    }
                }
            ]
        ))
        
        # Webhook management
        endpoints.append(APIEndpointDoc(
            path="/api/v1/webhooks",
            method="POST",
            summary="Register Webhook",
            description="Register a webhook endpoint for event notifications",
            tags=["Webhooks"],
            request_body={
                "type": "object",
                "required": ["url", "events"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Webhook URL"
                    },
                    "events": {
                        "type": "array",
                        "description": "Events to subscribe to",
                        "items": {"type": "string"}
                    },
                    "secret": {
                        "type": "string",
                        "description": "Secret for HMAC signature"
                    }
                }
            }
        ))
        
        return endpoints
    
    def generate_markdown_docs(self) -> str:
        """Generate Markdown documentation"""
        doc = f"""# {self.api_title} API Documentation

Version: {self.api_version}  
Base URL: `{self.base_url}`

## Authentication

All API requests require authentication using an API key. Include your API key in the request header:

```
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

API requests are rate limited based on your subscription plan:
- Free: 100 requests/hour
- Starter: 1,000 requests/hour
- Growth: 10,000 requests/hour
- Scale: 100,000 requests/hour
- Enterprise: Custom limits

Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Your rate limit
- `X-RateLimit-Remaining`: Requests remaining
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Error Handling

The API uses standard HTTP status codes:
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

Error responses include a JSON body:
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

## Endpoints

"""
        
        # Group endpoints by tags
        tags = {}
        for endpoint in self.endpoints:
            for tag in endpoint.tags:
                if tag not in tags:
                    tags[tag] = []
                tags[tag].append(endpoint)
        
        # Generate documentation for each tag group
        for tag, tag_endpoints in tags.items():
            doc += f"\n### {tag}\n\n"
            
            for endpoint in tag_endpoints:
                doc += f"#### {endpoint.method} {endpoint.path}\n\n"
                doc += f"{endpoint.description}\n\n"
                
                # Parameters
                if endpoint.parameters:
                    doc += "**Parameters:**\n\n"
                    doc += "| Name | Type | Location | Required | Description |\n"
                    doc += "|------|------|----------|----------|-------------|\n"
                    
                    for param in endpoint.parameters:
                        required = "Yes" if param.required else "No"
                        doc += f"| {param.name} | {param.type.value} | {param.location} | {required} | {param.description} |\n"
                    doc += "\n"
                
                # Request body
                if endpoint.request_body:
                    doc += "**Request Body:**\n\n"
                    doc += "```json\n"
                    doc += json.dumps(self._schema_to_example(endpoint.request_body), indent=2)
                    doc += "\n```\n\n"
                
                # Responses
                doc += "**Responses:**\n\n"
                for response in endpoint.responses:
                    doc += f"- `{response.status_code}` - {response.description}\n"
                    if response.example:
                        doc += "\n```json\n"
                        doc += json.dumps(response.example, indent=2)
                        doc += "\n```\n"
                doc += "\n"
                
                # Examples
                if endpoint.examples:
                    doc += "**Examples:**\n\n"
                    for example in endpoint.examples:
                        doc += f"_{example['title']}_\n\n"
                        doc += "Request:\n```json\n"
                        doc += json.dumps(example['request'], indent=2)
                        doc += "\n```\n\n"
                        if 'response' in example:
                            doc += "Response:\n```json\n"
                            doc += json.dumps(example['response'], indent=2)
                            doc += "\n```\n\n"
                
                doc += "---\n\n"
        
        # Add webhook events
        doc += self._generate_webhook_docs()
        
        # Add SDK examples
        doc += self._generate_sdk_examples()
        
        return doc
    
    def _generate_webhook_docs(self) -> str:
        """Generate webhook documentation"""
        return """
## Webhook Events

Webhooks allow you to receive real-time notifications about transcription events.

### Event Types

- `transcription.started` - Transcription processing started
- `transcription.completed` - Transcription completed successfully
- `transcription.failed` - Transcription failed
- `entity_extraction.completed` - Entity extraction completed
- `summary.generated` - Summary generated
- `export.completed` - Export completed
- `quota.warning` - Usage quota warning (80% reached)
- `quota.exceeded` - Usage quota exceeded

### Webhook Payload

All webhook events include:

```json
{
  "event": "transcription.completed",
  "timestamp": "2024-01-15T10:35:00Z",
  "data": {
    "transcription_id": "trans_abc123",
    "status": "completed",
    // Event-specific data
  }
}
```

### Webhook Security

Webhook payloads are signed using HMAC-SHA256. Verify the signature:

```python
import hmac
import hashlib

def verify_webhook_signature(payload, signature, secret):
    expected = hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

"""
    
    def _generate_sdk_examples(self) -> str:
        """Generate SDK usage examples"""
        return """
## SDK Examples

### Python

```python
from transcription_sdk import TranscriptionClient

client = TranscriptionClient("your-api-key")

# Create transcription
result = client.create_transcription(
    file_url="https://example.com/audio.mp3",
    language="en-US",
    speaker_count=2
)

# Check status
transcription = client.get_transcription(result["id"])
print(f"Status: {transcription['status']}")

# Get entities
entities = client.get_entities(result["id"])
for entity in entities["entities"]:
    print(f"{entity['type']}: {entity['text']}")
```

### JavaScript

```javascript
const { TranscriptionClient } = require('transcription-sdk');

const client = new TranscriptionClient('your-api-key');

async function transcribe() {
  // Create transcription
  const result = await client.createTranscription({
    fileUrl: 'https://example.com/audio.mp3',
    language: 'en-US',
    speakerCount: 2
  });
  
  // Check status
  const transcription = await client.getTranscription(result.id);
  console.log(`Status: ${transcription.status}`);
  
  // Get entities
  const entities = await client.getEntities(result.id);
  entities.entities.forEach(entity => {
    console.log(`${entity.type}: ${entity.text}`);
  });
}

transcribe().catch(console.error);
```

### cURL

```bash
# Create transcription
curl -X POST https://api.transcription.io/api/v1/transcriptions \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "file_url": "https://example.com/audio.mp3",
    "language": "en-US"
  }'

# Get transcription
curl https://api.transcription.io/api/v1/transcriptions/trans_abc123 \\
  -H "Authorization: Bearer YOUR_API_KEY"

# Get entities
curl https://api.transcription.io/api/v1/transcriptions/trans_abc123/entities \\
  -H "Authorization: Bearer YOUR_API_KEY"
```

"""
    
    def generate_openapi_spec(self) -> Dict[str, Any]:
        """Generate OpenAPI 3.0 specification"""
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": self.api_title,
                "version": self.api_version,
                "description": "Comprehensive API for audio/video transcription and analysis",
                "contact": {
                    "email": "support@transcription.io"
                }
            },
            "servers": [
                {
                    "url": self.base_url,
                    "description": "Production server"
                }
            ],
            "security": [
                {"bearerAuth": []}
            ],
            "components": {
                "securitySchemes": {
                    "bearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "API Key"
                    }
                },
                "schemas": self._generate_schemas()
            },
            "paths": self._generate_paths()
        }
        
        return spec
    
    def _generate_schemas(self) -> Dict[str, Any]:
        """Generate OpenAPI schemas"""
        return {
            "Transcription": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "status": {"type": "string", "enum": ["pending", "processing", "completed", "failed"]},
                    "file_name": {"type": "string"},
                    "duration": {"type": "number"},
                    "language": {"type": "string"},
                    "text": {"type": "string"},
                    "confidence": {"type": "number"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "Entity": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "type": {"type": "string"},
                    "confidence": {"type": "number"},
                    "start_time": {"type": "number"},
                    "end_time": {"type": "number"}
                }
            },
            "Error": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "code": {"type": "string"},
                    "details": {"type": "object"}
                }
            }
        }
    
    def _generate_paths(self) -> Dict[str, Any]:
        """Generate OpenAPI paths"""
        paths = {}
        
        for endpoint in self.endpoints:
            if endpoint.path not in paths:
                paths[endpoint.path] = {}
            
            operation = {
                "summary": endpoint.summary,
                "description": endpoint.description,
                "tags": endpoint.tags,
                "responses": {}
            }
            
            # Add parameters
            if endpoint.parameters:
                operation["parameters"] = []
                for param in endpoint.parameters:
                    param_spec = {
                        "name": param.name,
                        "in": param.location,
                        "required": param.required,
                        "description": param.description,
                        "schema": {"type": param.type.value}
                    }
                    if param.default is not None:
                        param_spec["schema"]["default"] = param.default
                    operation["parameters"].append(param_spec)
            
            # Add request body
            if endpoint.request_body:
                operation["requestBody"] = {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": endpoint.request_body
                        }
                    }
                }
            
            # Add responses
            for response in endpoint.responses:
                operation["responses"][str(response.status_code)] = {
                    "description": response.description,
                    "content": {
                        response.content_type: {
                            "schema": response.schema
                        }
                    }
                }
            
            paths[endpoint.path][endpoint.method.lower()] = operation
        
        return paths
    
    def _schema_to_example(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Convert JSON schema to example"""
        if schema.get("type") == "object":
            example = {}
            for prop, prop_schema in schema.get("properties", {}).items():
                if "example" in prop_schema:
                    example[prop] = prop_schema["example"]
                elif prop_schema.get("type") == "string":
                    example[prop] = "string"
                elif prop_schema.get("type") == "integer":
                    example[prop] = 0
                elif prop_schema.get("type") == "number":
                    example[prop] = 0.0
                elif prop_schema.get("type") == "boolean":
                    example[prop] = False
                elif prop_schema.get("type") == "array":
                    example[prop] = []
                elif prop_schema.get("type") == "object":
                    example[prop] = self._schema_to_example(prop_schema)
            return example
        return {}
    
    def generate_postman_collection(self) -> Dict[str, Any]:
        """Generate Postman collection"""
        collection = {
            "info": {
                "name": self.api_title,
                "description": f"API collection for {self.api_title}",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "auth": {
                "type": "bearer",
                "bearer": [
                    {
                        "key": "token",
                        "value": "{{api_key}}",
                        "type": "string"
                    }
                ]
            },
            "variable": [
                {
                    "key": "base_url",
                    "value": self.base_url
                },
                {
                    "key": "api_key",
                    "value": "your-api-key"
                }
            ],
            "item": []
        }
        
        # Group by tags
        tag_folders = {}
        
        for endpoint in self.endpoints:
            for tag in endpoint.tags:
                if tag not in tag_folders:
                    tag_folders[tag] = {
                        "name": tag,
                        "item": []
                    }
                
                # Create request
                request = {
                    "name": endpoint.summary,
                    "request": {
                        "method": endpoint.method,
                        "header": [],
                        "url": {
                            "raw": f"{{{{base_url}}}}{endpoint.path}",
                            "host": ["{{base_url}}"],
                            "path": endpoint.path.strip("/").split("/")
                        },
                        "description": endpoint.description
                    }
                }
                
                # Add parameters
                if endpoint.parameters:
                    query_params = []
                    for param in endpoint.parameters:
                        if param.location == "query":
                            query_params.append({
                                "key": param.name,
                                "value": str(param.example or ""),
                                "disabled": not param.required
                            })
                    
                    if query_params:
                        request["request"]["url"]["query"] = query_params
                
                # Add request body
                if endpoint.request_body:
                    request["request"]["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(
                            self._schema_to_example(endpoint.request_body),
                            indent=2
                        ),
                        "options": {
                            "raw": {
                                "language": "json"
                            }
                        }
                    }
                
                tag_folders[tag]["item"].append(request)
        
        collection["item"] = list(tag_folders.values())
        
        return collection
    
    def generate_html_docs(self) -> str:
        """Generate HTML documentation"""
        markdown_docs = self.generate_markdown_docs()
        html_content = markdown.markdown(
            markdown_docs,
            extensions=['extra', 'codehilite', 'tables', 'toc']
        )
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.api_title} API Documentation</title>
    <link href="https://cdn.jsdelivr.net/npm/prismjs@1.24.1/themes/prism-tomorrow.css" rel="stylesheet" />
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1, h2, h3, h4 {{
            color: #2c3e50;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        pre {{
            background: #282c34;
            color: #abb2bf;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background: #f8f9fa;
            font-weight: 600;
        }}
        .endpoint {{
            background: #e8f4f8;
            padding: 0.5rem 1rem;
            border-radius: 4px;
            margin: 1rem 0;
            font-family: monospace;
        }}
        .method-get {{ border-left: 4px solid #61affe; }}
        .method-post {{ border-left: 4px solid #49cc90; }}
        .method-put {{ border-left: 4px solid #fca130; }}
        .method-delete {{ border-left: 4px solid #f93e3e; }}
    </style>
</head>
<body>
    <div class="container">
        {html_content}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/prismjs@1.24.1/components/prism-core.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/prismjs@1.24.1/plugins/autoloader/prism-autoloader.min.js"></script>
</body>
</html>
"""
        
        return html_template

# Interactive API Explorer
class APIExplorer:
    """Interactive API testing interface"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
    
    def generate_explorer_html(self) -> str:
        """Generate interactive API explorer HTML"""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Explorer</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 1rem 2rem;
        }
        .container {
            display: flex;
            height: calc(100vh - 60px);
        }
        .sidebar {
            width: 300px;
            background: white;
            border-right: 1px solid #ddd;
            overflow-y: auto;
        }
        .main {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
        }
        .endpoint-item {
            padding: 1rem;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background 0.2s;
        }
        .endpoint-item:hover {
            background: #f8f9fa;
        }
        .method {
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8rem;
            font-weight: bold;
            margin-right: 0.5rem;
        }
        .method-get { background: #61affe; color: white; }
        .method-post { background: #49cc90; color: white; }
        .method-put { background: #fca130; color: white; }
        .method-delete { background: #f93e3e; color: white; }
        .form-group {
            margin-bottom: 1.5rem;
        }
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        input, textarea, select {
            width: 100%;
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #2980b9;
        }
        .response {
            margin-top: 2rem;
            background: #282c34;
            color: #abb2bf;
            padding: 1rem;
            border-radius: 6px;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
        }
        .loading {
            text-align: center;
            padding: 2rem;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>API Explorer</h1>
    </div>
    <div class="container">
        <div class="sidebar" id="sidebar">
            <!-- Endpoints will be loaded here -->
        </div>
        <div class="main" id="main">
            <h2>Select an endpoint to test</h2>
        </div>
    </div>
    
    <script>
        const baseUrl = '""" + self.base_url + """';
        let currentEndpoint = null;
        
        // Sample endpoints for demonstration
        const endpoints = [
            {
                method: 'POST',
                path: '/api/v1/transcriptions',
                name: 'Create Transcription',
                params: {
                    body: {
                        file_url: { type: 'string', required: true },
                        language: { type: 'string', required: false },
                        speaker_count: { type: 'number', required: false }
                    }
                }
            },
            {
                method: 'GET',
                path: '/api/v1/transcriptions/{id}',
                name: 'Get Transcription',
                params: {
                    path: {
                        id: { type: 'string', required: true }
                    }
                }
            }
        ];
        
        // Load endpoints in sidebar
        function loadEndpoints() {
            const sidebar = document.getElementById('sidebar');
            endpoints.forEach(endpoint => {
                const item = document.createElement('div');
                item.className = 'endpoint-item';
                item.innerHTML = `
                    <span class="method method-${endpoint.method.toLowerCase()}">${endpoint.method}</span>
                    <div>${endpoint.name}</div>
                    <small style="color: #666;">${endpoint.path}</small>
                `;
                item.onclick = () => selectEndpoint(endpoint);
                sidebar.appendChild(item);
            });
        }
        
        // Select endpoint
        function selectEndpoint(endpoint) {
            currentEndpoint = endpoint;
            const main = document.getElementById('main');
            
            let formHtml = `
                <h2>${endpoint.name}</h2>
                <p><span class="method method-${endpoint.method.toLowerCase()}">${endpoint.method}</span> ${endpoint.path}</p>
                
                <form id="testForm">
                    <div class="form-group">
                        <label>API Key</label>
                        <input type="text" id="apiKey" placeholder="Enter your API key" required>
                    </div>
            `;
            
            // Add path parameters
            if (endpoint.params.path) {
                Object.entries(endpoint.params.path).forEach(([name, config]) => {
                    formHtml += `
                        <div class="form-group">
                            <label>${name} ${config.required ? '*' : ''}</label>
                            <input type="text" name="path_${name}" ${config.required ? 'required' : ''}>
                        </div>
                    `;
                });
            }
            
            // Add body parameters
            if (endpoint.params.body) {
                formHtml += '<h3>Request Body</h3>';
                Object.entries(endpoint.params.body).forEach(([name, config]) => {
                    formHtml += `
                        <div class="form-group">
                            <label>${name} ${config.required ? '*' : ''}</label>
                            <input type="${config.type === 'number' ? 'number' : 'text'}" 
                                   name="body_${name}" ${config.required ? 'required' : ''}>
                        </div>
                    `;
                });
            }
            
            formHtml += `
                    <button type="submit">Send Request</button>
                </form>
                
                <div id="response"></div>
            `;
            
            main.innerHTML = formHtml;
            
            document.getElementById('testForm').onsubmit = sendRequest;
        }
        
        // Send request
        async function sendRequest(e) {
            e.preventDefault();
            
            const form = e.target;
            const apiKey = document.getElementById('apiKey').value;
            const responseDiv = document.getElementById('response');
            
            responseDiv.innerHTML = '<div class="loading">Sending request...</div>';
            
            // Build URL
            let url = baseUrl + currentEndpoint.path;
            
            // Replace path parameters
            if (currentEndpoint.params.path) {
                Object.keys(currentEndpoint.params.path).forEach(param => {
                    const value = form.elements[`path_${param}`].value;
                    url = url.replace(`{${param}}`, value);
                });
            }
            
            // Build body
            let body = null;
            if (currentEndpoint.params.body) {
                body = {};
                Object.keys(currentEndpoint.params.body).forEach(param => {
                    const value = form.elements[`body_${param}`].value;
                    if (value) {
                        body[param] = value;
                    }
                });
            }
            
            try {
                const options = {
                    method: currentEndpoint.method,
                    headers: {
                        'Authorization': `Bearer ${apiKey}`,
                        'Content-Type': 'application/json'
                    }
                };
                
                if (body && currentEndpoint.method !== 'GET') {
                    options.body = JSON.stringify(body);
                }
                
                const response = await fetch(url, options);
                const data = await response.json();
                
                responseDiv.innerHTML = `
                    <h3>Response</h3>
                    <div class="response">
Status: ${response.status} ${response.statusText}

${JSON.stringify(data, null, 2)}
                    </div>
                `;
            } catch (error) {
                responseDiv.innerHTML = `
                    <h3>Error</h3>
                    <div class="response" style="background: #f8d7da; color: #721c24;">
${error.message}
                    </div>
                `;
            }
        }
        
        // Initialize
        loadEndpoints();
    </script>
</body>
</html>
"""

# Example usage
if __name__ == "__main__":
    # Create documentation generator
    doc_gen = APIDocumentationGenerator(
        api_title="Transcription API",
        api_version="v1",
        base_url="https://api.transcription.io"
    )
    
    # Generate Markdown docs
    markdown_docs = doc_gen.generate_markdown_docs()
    print("Generated Markdown documentation")
    
    # Generate OpenAPI spec
    openapi_spec = doc_gen.generate_openapi_spec()
    print("\nGenerated OpenAPI specification")
    
    # Generate Postman collection
    postman_collection = doc_gen.generate_postman_collection()
    print("\nGenerated Postman collection")
    
    # Create API explorer
    explorer = APIExplorer("https://api.transcription.io")
    explorer_html = explorer.generate_explorer_html()
    print("\nGenerated interactive API explorer")