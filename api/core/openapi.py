"""
OpenAPI documentation generation with examples and authentication
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.responses import HTMLResponse
from typing import Dict, Any, Optional, List
import json

def setup_openapi_docs(
    app: FastAPI,
    title: str = "Production API",
    description: str = "Enterprise-grade API with comprehensive documentation",
    version: str = "1.0.0",
    contact: Optional[Dict[str, str]] = None,
    license_info: Optional[Dict[str, str]] = None,
    servers: Optional[List[Dict[str, str]]] = None,
    tags_metadata: Optional[List[Dict[str, Any]]] = None
) -> FastAPI:
    """
    Setup comprehensive OpenAPI documentation with:
    - Custom schemas and examples
    - Authentication documentation
    - Response examples
    - Error documentation
    """
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        
        # Generate base OpenAPI schema
        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
        )
        
        # Add contact information
        if contact:
            openapi_schema["info"]["contact"] = contact
        
        # Add license information
        if license_info:
            openapi_schema["info"]["license"] = license_info
        
        # Add servers
        if servers:
            openapi_schema["servers"] = servers
        else:
            openapi_schema["servers"] = [
                {"url": "/", "description": "Current server"}
            ]
        
        # Add tags metadata
        if tags_metadata:
            openapi_schema["tags"] = tags_metadata
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token obtained from /api/auth/login"
            },
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for service-to-service authentication"
            }
        }
        
        # Add global security requirement
        openapi_schema["security"] = [
            {"BearerAuth": []},
            {"ApiKeyAuth": []}
        ]
        
        # Add common response schemas
        openapi_schema["components"]["schemas"].update({
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {"type": "integer", "example": 400},
                            "message": {"type": "string", "example": "Bad request"},
                            "request_id": {"type": "string", "example": "req_123456"},
                            "timestamp": {"type": "string", "format": "date-time"}
                        }
                    }
                }
            },
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "enum": ["healthy", "unhealthy", "degraded"]},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "version": {"type": "string"},
                    "checks": {"type": "object"},
                    "summary": {"type": "object"}
                }
            },
            "MetricsResponse": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"},
                    "uptime": {"type": "number"},
                    "counters": {"type": "object"},
                    "gauges": {"type": "object"},
                    "histograms": {"type": "object"}
                }
            }
        })
        
        # Add common response examples
        _add_response_examples(openapi_schema)
        
        # Add rate limiting documentation
        _add_rate_limiting_docs(openapi_schema)
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi
    
    # Custom documentation endpoints
    @app.get("/api/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/openapi.json",
            title=f"{title} - Swagger UI",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_ui_parameters={
                "deepLinking": True,
                "displayRequestDuration": True,
                "docExpansion": "none",
                "operationsSorter": "alpha",
                "filter": True,
                "tryItOutEnabled": True
            }
        )
    
    @app.get("/api/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/openapi.json",
            title=f"{title} - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js"
        )
    
    @app.get("/api/openapi.json", include_in_schema=False)
    async def get_openapi_json():
        return app.openapi()
    
    return app

def _add_response_examples(openapi_schema: Dict[str, Any]):
    """Add common response examples to the schema"""
    
    # Add examples to paths
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            
            responses = operation["responses"]
            
            # Add error response examples
            for status_code in ["400", "401", "403", "404", "422", "429", "500"]:
                if status_code in responses:
                    responses[status_code]["content"] = {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                            "examples": {
                                "error": {
                                    "summary": f"HTTP {status_code} Error",
                                    "value": {
                                        "error": {
                                            "code": int(status_code),
                                            "message": _get_error_message(status_code),
                                            "request_id": "req_123456789",
                                            "timestamp": "2024-01-01T12:00:00Z"
                                        }
                                    }
                                }
                            }
                        }
                    }

def _add_rate_limiting_docs(openapi_schema: Dict[str, Any]):
    """Add rate limiting documentation"""
    
    # Add rate limiting headers to responses
    rate_limit_headers = {
        "X-RateLimit-Limit": {
            "description": "Request limit per time window",
            "schema": {"type": "integer"}
        },
        "X-RateLimit-Remaining": {
            "description": "Remaining requests in current window",
            "schema": {"type": "integer"}
        },
        "X-RateLimit-Reset": {
            "description": "Time when the rate limit resets (Unix timestamp)",
            "schema": {"type": "integer"}
        }
    }
    
    # Add to all successful responses
    for path_item in openapi_schema.get("paths", {}).values():
        for operation in path_item.values():
            if not isinstance(operation, dict) or "responses" not in operation:
                continue
            
            for status_code, response in operation["responses"].items():
                if status_code.startswith("2"):  # 2xx responses
                    if "headers" not in response:
                        response["headers"] = {}
                    response["headers"].update(rate_limit_headers)

def _get_error_message(status_code: str) -> str:
    """Get appropriate error message for status code"""
    messages = {
        "400": "Bad request - invalid input parameters",
        "401": "Unauthorized - authentication required",
        "403": "Forbidden - insufficient permissions",
        "404": "Not found - resource does not exist",
        "422": "Validation error - request data is invalid",
        "429": "Rate limit exceeded - too many requests",
        "500": "Internal server error - something went wrong"
    }
    return messages.get(status_code, "An error occurred")

def add_endpoint_examples(
    app: FastAPI,
    path: str,
    method: str,
    request_examples: Optional[Dict[str, Any]] = None,
    response_examples: Optional[Dict[str, Dict[str, Any]]] = None
):
    """
    Add examples to a specific endpoint
    
    Args:
        app: FastAPI application
        path: API path (e.g., "/api/users")
        method: HTTP method (e.g., "post")
        request_examples: Request body examples
        response_examples: Response examples by status code
    """
    
    def update_openapi():
        if not app.openapi_schema:
            app.openapi()
        
        schema = app.openapi_schema
        
        if path in schema["paths"] and method.lower() in schema["paths"][path]:
            operation = schema["paths"][path][method.lower()]
            
            # Add request examples
            if request_examples and "requestBody" in operation:
                content = operation["requestBody"]["content"]
                for content_type in content:
                    if "examples" not in content[content_type]:
                        content[content_type]["examples"] = {}
                    content[content_type]["examples"].update(request_examples)
            
            # Add response examples
            if response_examples:
                for status_code, examples in response_examples.items():
                    if status_code in operation["responses"]:
                        response = operation["responses"][status_code]
                        if "content" in response:
                            for content_type in response["content"]:
                                if "examples" not in response["content"][content_type]:
                                    response["content"][content_type]["examples"] = {}
                                response["content"][content_type]["examples"].update(examples)
    
    # Update schema after app startup
    app.add_event_handler("startup", update_openapi)

def create_example_responses() -> Dict[str, Dict[str, Any]]:
    """Create common example responses"""
    return {
        "200": {
            "success": {
                "summary": "Successful response",
                "value": {
                    "status": "success",
                    "data": {},
                    "message": "Operation completed successfully"
                }
            }
        },
        "201": {
            "created": {
                "summary": "Resource created",
                "value": {
                    "status": "success",
                    "data": {"id": "123"},
                    "message": "Resource created successfully"
                }
            }
        },
        "400": {
            "bad_request": {
                "summary": "Bad request",
                "value": {
                    "error": {
                        "code": 400,
                        "message": "Invalid request parameters",
                        "request_id": "req_123456789",
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                }
            }
        },
        "401": {
            "unauthorized": {
                "summary": "Unauthorized",
                "value": {
                    "error": {
                        "code": 401,
                        "message": "Authentication required",
                        "request_id": "req_123456789",
                        "timestamp": "2024-01-01T12:00:00Z"
                    }
                }
            }
        }
    }