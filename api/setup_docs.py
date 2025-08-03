"""
Setup script to integrate OpenAPI documentation with FastAPI app
Run this to configure comprehensive API documentation
"""

import os
import sys
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api.docs.openapi_config import configure_swagger_ui, custom_openapi
from api.docs.endpoint_docs import (
    AUTH_DOCS, TRANSCRIPTION_DOCS, SEARCH_DOCS, 
    EXPORT_DOCS, TEAM_DOCS, ANALYTICS_DOCS,
    RESPONSE_EXAMPLES, WEBSOCKET_EVENTS
)
from api.docs.api_examples import get_all_examples


def setup_api_documentation(app: FastAPI):
    """
    Configure comprehensive API documentation for the FastAPI app
    
    Args:
        app: FastAPI application instance
    """
    # Configure OpenAPI schema
    configure_swagger_ui(app)
    
    # Add custom documentation page
    @app.get("/api-docs", include_in_schema=False, response_class=HTMLResponse)
    async def custom_docs():
        """Serve custom API documentation page"""
        examples = get_all_examples()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Transcription API Documentation</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
            <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
                .sidebar {{ position: sticky; top: 20px; }}
                .code-block {{ position: relative; }}
                .copy-button {{
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    padding: 5px 10px;
                    font-size: 12px;
                }}
                .endpoint-card {{ margin-bottom: 20px; }}
                .method-badge {{ font-weight: bold; padding: 5px 10px; }}
                .method-get {{ background-color: #61affe; color: white; }}
                .method-post {{ background-color: #49cc90; color: white; }}
                .method-put {{ background-color: #fca130; color: white; }}
                .method-delete {{ background-color: #f93e3e; color: white; }}
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
                <div class="container-fluid">
                    <a class="navbar-brand" href="#">📼 Transcription API v2.0</a>
                    <div class="navbar-nav ms-auto">
                        <a class="nav-link" href="/docs">Swagger UI</a>
                        <a class="nav-link" href="/redoc">ReDoc</a>
                        <a class="nav-link" href="https://github.com/yourusername/transcription-api">GitHub</a>
                    </div>
                </div>
            </nav>
            
            <div class="container-fluid mt-4">
                <div class="row">
                    <!-- Sidebar -->
                    <div class="col-md-3">
                        <div class="sidebar">
                            <h5>Quick Links</h5>
                            <ul class="nav flex-column">
                                <li class="nav-item"><a class="nav-link" href="#getting-started">Getting Started</a></li>
                                <li class="nav-item"><a class="nav-link" href="#authentication">Authentication</a></li>
                                <li class="nav-item"><a class="nav-link" href="#endpoints">Endpoints</a></li>
                                <li class="nav-item"><a class="nav-link" href="#examples">Code Examples</a></li>
                                <li class="nav-item"><a class="nav-link" href="#websockets">WebSockets</a></li>
                                <li class="nav-item"><a class="nav-link" href="#errors">Error Handling</a></li>
                                <li class="nav-item"><a class="nav-link" href="#rate-limits">Rate Limits</a></li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- Main Content -->
                    <div class="col-md-9">
                        <h1>API Documentation</h1>
                        
                        <section id="getting-started" class="mb-5">
                            <h2>Getting Started</h2>
                            <p>Welcome to the Transcription API! This API provides powerful audio and video transcription capabilities with advanced features.</p>
                            
                            <div class="alert alert-info">
                                <h5>Base URL</h5>
                                <code>https://api.transcription.com</code>
                            </div>
                            
                            <h3>Quick Start</h3>
                            <ol>
                                <li>Register for an account</li>
                                <li>Obtain your API credentials</li>
                                <li>Make your first API call</li>
                            </ol>
                        </section>
                        
                        <section id="authentication" class="mb-5">
                            <h2>Authentication</h2>
                            <p>The API uses JWT (JSON Web Token) authentication. Include your token in the Authorization header:</p>
                            <pre><code>Authorization: Bearer YOUR_ACCESS_TOKEN</code></pre>
                            
                            <h3>Getting a Token</h3>
                            <div class="endpoint-card card">
                                <div class="card-header">
                                    <span class="method-badge method-post">POST</span>
                                    <code>/api/auth/login</code>
                                </div>
                                <div class="card-body">
                                    <pre><code class="language-json">{{
  "username": "your_username",
  "password": "your_password"
}}</code></pre>
                                </div>
                            </div>
                        </section>
                        
                        <section id="endpoints" class="mb-5">
                            <h2>API Endpoints</h2>
                            
                            <h3>Transcription</h3>
                            <div class="endpoint-card card">
                                <div class="card-header">
                                    <span class="method-badge method-post">POST</span>
                                    <code>/api/transcription/upload</code>
                                </div>
                                <div class="card-body">
                                    <p>Upload an audio or video file for transcription.</p>
                                    <p><strong>Rate Limit:</strong> 50 uploads per hour</p>
                                </div>
                            </div>
                            
                            <h3>Search</h3>
                            <div class="endpoint-card card">
                                <div class="card-header">
                                    <span class="method-badge method-get">GET</span>
                                    <code>/api/search</code>
                                </div>
                                <div class="card-body">
                                    <p>Search through your transcripts with advanced filtering.</p>
                                    <p><strong>Rate Limit:</strong> 100 searches per 5 minutes</p>
                                </div>
                            </div>
                        </section>
                        
                        <section id="examples" class="mb-5">
                            <h2>Code Examples</h2>
                            
                            <ul class="nav nav-tabs" role="tablist">
                                <li class="nav-item">
                                    <a class="nav-link active" data-bs-toggle="tab" href="#python-examples">Python</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" data-bs-toggle="tab" href="#js-examples">JavaScript</a>
                                </li>
                                <li class="nav-item">
                                    <a class="nav-link" data-bs-toggle="tab" href="#curl-examples">cURL</a>
                                </li>
                            </ul>
                            
                            <div class="tab-content mt-3">
                                <div id="python-examples" class="tab-pane fade show active">
                                    <h3>Authentication</h3>
                                    <div class="code-block">
                                        <button class="btn btn-sm btn-secondary copy-button" onclick="copyCode(this)">Copy</button>
                                        <pre><code class="language-python">{examples['python']['authentication']}</code></pre>
                                    </div>
                                </div>
                                
                                <div id="js-examples" class="tab-pane fade">
                                    <h3>Authentication</h3>
                                    <div class="code-block">
                                        <button class="btn btn-sm btn-secondary copy-button" onclick="copyCode(this)">Copy</button>
                                        <pre><code class="language-javascript">{examples['javascript']['authentication']}</code></pre>
                                    </div>
                                </div>
                                
                                <div id="curl-examples" class="tab-pane fade">
                                    <h3>Authentication</h3>
                                    <div class="code-block">
                                        <button class="btn btn-sm btn-secondary copy-button" onclick="copyCode(this)">Copy</button>
                                        <pre><code class="language-bash">{examples['curl']['authentication']}</code></pre>
                                    </div>
                                </div>
                            </div>
                        </section>
                        
                        <section id="websockets" class="mb-5">
                            <h2>WebSocket Events</h2>
                            <p>Connect to real-time updates via WebSocket:</p>
                            <pre><code>wss://api.transcription.com/ws?token=YOUR_TOKEN</code></pre>
                            
                            <h3>Available Events</h3>
                            <ul>
                                <li><code>transcription.progress</code> - Transcription progress updates</li>
                                <li><code>transcription.complete</code> - Transcription completed</li>
                                <li><code>collaboration.comment</code> - New comment added</li>
                                <li><code>notification.new</code> - New notification</li>
                            </ul>
                        </section>
                        
                        <section id="errors" class="mb-5">
                            <h2>Error Handling</h2>
                            <p>All errors follow a consistent format:</p>
                            <pre><code class="language-json">{{
  "error": "Error message",
  "detail": "Detailed error information",
  "status_code": 400,
  "timestamp": "2024-01-01T12:00:00Z"
}}</code></pre>
                            
                            <h3>Common Error Codes</h3>
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Code</th>
                                        <th>Description</th>
                                        <th>Resolution</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>400</td>
                                        <td>Bad Request</td>
                                        <td>Check your request parameters</td>
                                    </tr>
                                    <tr>
                                        <td>401</td>
                                        <td>Unauthorized</td>
                                        <td>Provide valid authentication</td>
                                    </tr>
                                    <tr>
                                        <td>429</td>
                                        <td>Rate Limited</td>
                                        <td>Wait for rate limit reset</td>
                                    </tr>
                                </tbody>
                            </table>
                        </section>
                        
                        <section id="rate-limits" class="mb-5">
                            <h2>Rate Limits</h2>
                            <p>API rate limits are enforced to ensure fair usage:</p>
                            
                            <table class="table">
                                <thead>
                                    <tr>
                                        <th>Endpoint</th>
                                        <th>Limit</th>
                                        <th>Window</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>/api/auth/login</td>
                                        <td>10 requests</td>
                                        <td>5 minutes</td>
                                    </tr>
                                    <tr>
                                        <td>/api/transcription/upload</td>
                                        <td>50 requests</td>
                                        <td>1 hour</td>
                                    </tr>
                                    <tr>
                                        <td>/api/search</td>
                                        <td>100 requests</td>
                                        <td>5 minutes</td>
                                    </tr>
                                </tbody>
                            </table>
                            
                            <p>Rate limit information is included in response headers:</p>
                            <ul>
                                <li><code>X-RateLimit-Limit</code> - Total allowed requests</li>
                                <li><code>X-RateLimit-Remaining</code> - Remaining requests</li>
                                <li><code>X-RateLimit-Reset</code> - Reset timestamp</li>
                            </ul>
                        </section>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-javascript.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
            <script>
                function copyCode(button) {{
                    const code = button.parentElement.querySelector('code').textContent;
                    navigator.clipboard.writeText(code).then(() => {{
                        button.textContent = 'Copied!';
                        setTimeout(() => {{
                            button.textContent = 'Copy';
                        }}, 2000);
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        return html_content
    
    # Add endpoint-specific documentation
    for path_operation in app.routes:
        if hasattr(path_operation, "endpoint"):
            endpoint = path_operation.endpoint
            path = path_operation.path
            
            # Match documentation to endpoints
            if "/auth/register" in path:
                endpoint.__doc__ = AUTH_DOCS["register"]["description"]
            elif "/auth/login" in path:
                endpoint.__doc__ = AUTH_DOCS["login"]["description"]
            elif "/transcription/upload" in path:
                endpoint.__doc__ = TRANSCRIPTION_DOCS["upload"]["description"]
            elif "/search" in path and "semantic" not in path:
                endpoint.__doc__ = SEARCH_DOCS["search"]["description"]
    
    print("✅ API documentation configured successfully!")
    print("📚 Access documentation at:")
    print("   - Swagger UI: http://localhost:8000/docs")
    print("   - ReDoc: http://localhost:8000/redoc")
    print("   - Custom Docs: http://localhost:8000/api-docs")
    
    return app


def generate_postman_collection(app: FastAPI) -> Dict[str, Any]:
    """
    Generate Postman collection from FastAPI app
    """
    collection = {
        "info": {
            "name": "Transcription API",
            "description": "Audio/Video Transcription API Collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "variable": [
            {
                "key": "baseUrl",
                "value": "https://api.transcription.com",
                "type": "string"
            },
            {
                "key": "accessToken",
                "value": "",
                "type": "string"
            }
        ],
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{accessToken}}",
                    "type": "string"
                }
            ]
        }
    }
    
    # Group endpoints by tags
    endpoints_by_tag = {}
    
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "endpoint"):
            for method in route.methods:
                if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    # Extract tag from endpoint
                    tags = getattr(route.endpoint, "tags", ["General"])
                    tag = tags[0] if tags else "General"
                    
                    if tag not in endpoints_by_tag:
                        endpoints_by_tag[tag] = []
                    
                    endpoints_by_tag[tag].append({
                        "name": route.endpoint.__name__,
                        "request": {
                            "method": method,
                            "url": {
                                "raw": "{{baseUrl}}" + route.path,
                                "host": ["{{baseUrl}}"],
                                "path": route.path.split("/")[1:]
                            },
                            "header": [
                                {
                                    "key": "Content-Type",
                                    "value": "application/json"
                                }
                            ]
                        }
                    })
    
    # Create folders for each tag
    for tag, requests in endpoints_by_tag.items():
        collection["item"].append({
            "name": tag,
            "item": requests
        })
    
    return collection


if __name__ == "__main__":
    # Example usage
    from api.app import create_app
    
    app = create_app()
    setup_api_documentation(app)
    
    # Generate Postman collection
    import json
    postman_collection = generate_postman_collection(app)
    
    with open("transcription_api.postman_collection.json", "w") as f:
        json.dump(postman_collection, f, indent=2)
    
    print("\n📮 Postman collection generated: transcription_api.postman_collection.json")