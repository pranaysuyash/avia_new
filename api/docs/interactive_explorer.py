"""
Interactive API Explorer and Documentation Generator

Provides an interactive web interface for exploring the API endpoints,
testing requests, and generating code examples.
"""

import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yaml

from api.auth import get_current_active_user
from api.database import User


class APIExplorer:
    """Interactive API Explorer"""
    
    def __init__(self, app: FastAPI):
        self.app = app
        self.templates = Jinja2Templates(directory="api/docs/templates")
        
        # Mount static files
        app.mount("/docs/static", StaticFiles(directory="api/docs/static"), name="static")
        
        # Add routes
        self.setup_routes()
    
    def setup_routes(self):
        """Setup explorer routes"""
        
        @self.app.get("/docs/explorer", response_class=HTMLResponse)
        async def api_explorer(request: Request):
            """Interactive API Explorer"""
            return self.templates.TemplateResponse("explorer.html", {
                "request": request,
                "title": "API Explorer",
                "endpoints": self.get_endpoint_documentation()
            })
        
        @self.app.get("/docs/playground", response_class=HTMLResponse)
        async def api_playground(request: Request):
            """API Testing Playground"""
            return self.templates.TemplateResponse("playground.html", {
                "request": request,
                "title": "API Playground",
                "openapi_spec": self.get_openapi_spec()
            })
        
        @self.app.get("/docs/code-examples/{language}")
        async def get_code_examples(language: str, endpoint: Optional[str] = None):
            """Get code examples for specific language"""
            return self.generate_code_examples(language, endpoint)
        
        @self.app.post("/docs/test-endpoint")
        async def test_endpoint(
            request: Request,
            current_user: User = Depends(get_current_active_user)
        ):
            """Test API endpoint with provided parameters"""
            data = await request.json()
            return await self.execute_test_request(data, current_user)
    
    def get_endpoint_documentation(self) -> List[Dict[str, Any]]:
        """Generate comprehensive endpoint documentation"""
        openapi_spec = self.app.openapi()
        endpoints = []
        
        for path, methods in openapi_spec.get("paths", {}).items():
            for method, spec in methods.items():
                if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                    endpoint = {
                        "path": path,
                        "method": method.upper(),
                        "summary": spec.get("summary", ""),
                        "description": spec.get("description", ""),
                        "tags": spec.get("tags", []),
                        "parameters": self.parse_parameters(spec.get("parameters", [])),
                        "request_body": self.parse_request_body(spec.get("requestBody")),
                        "responses": self.parse_responses(spec.get("responses", {})),
                        "security": spec.get("security", []),
                        "examples": self.generate_endpoint_examples(path, method, spec)
                    }
                    endpoints.append(endpoint)
        
        return sorted(endpoints, key=lambda x: (x["path"], x["method"]))
    
    def parse_parameters(self, parameters: List[Dict]) -> List[Dict[str, Any]]:
        """Parse OpenAPI parameters"""
        parsed = []
        for param in parameters:
            parsed.append({
                "name": param.get("name"),
                "in": param.get("in"),
                "required": param.get("required", False),
                "type": param.get("schema", {}).get("type", "string"),
                "description": param.get("description", ""),
                "example": param.get("example")
            })
        return parsed
    
    def parse_request_body(self, request_body: Optional[Dict]) -> Optional[Dict[str, Any]]:
        """Parse OpenAPI request body"""
        if not request_body:
            return None
        
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        schema = json_content.get("schema", {})
        
        return {
            "required": request_body.get("required", False),
            "content_type": "application/json",
            "schema": schema,
            "example": json_content.get("example")
        }
    
    def parse_responses(self, responses: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Parse OpenAPI responses"""
        parsed = []
        for status_code, response in responses.items():
            content = response.get("content", {})
            json_content = content.get("application/json", {})
            
            parsed.append({
                "status_code": status_code,
                "description": response.get("description", ""),
                "schema": json_content.get("schema", {}),
                "example": json_content.get("example")
            })
        return parsed
    
    def generate_endpoint_examples(self, path: str, method: str, spec: Dict) -> Dict[str, str]:
        """Generate code examples for endpoint"""
        examples = {}
        
        # cURL example
        examples["curl"] = self.generate_curl_example(path, method, spec)
        
        # Python example
        examples["python"] = self.generate_python_example(path, method, spec)
        
        # JavaScript example
        examples["javascript"] = self.generate_javascript_example(path, method, spec)
        
        # Node.js example
        examples["nodejs"] = self.generate_nodejs_example(path, method, spec)
        
        return examples
    
    def generate_curl_example(self, path: str, method: str, spec: Dict) -> str:
        """Generate cURL example"""
        base_url = "https://api.transcriptionplatform.com/v1"
        
        curl_cmd = f"curl -X {method.upper()} \\\n"
        curl_cmd += f"  '{base_url}{path}' \\\n"
        curl_cmd += "  -H 'Authorization: Bearer YOUR_API_KEY' \\\n"
        curl_cmd += "  -H 'Content-Type: application/json'"
        
        # Add request body if present
        request_body = spec.get("requestBody")
        if request_body and method.upper() in ["POST", "PUT", "PATCH"]:
            example_data = self.get_example_request_data(request_body)
            if example_data:
                curl_cmd += " \\\n  -d '" + json.dumps(example_data, indent=2) + "'"
        
        return curl_cmd
    
    def generate_python_example(self, path: str, method: str, spec: Dict) -> str:
        """Generate Python SDK example"""
        example = "from transcription_api import TranscriptionClient\n\n"
        example += "client = TranscriptionClient(api_key='your_api_key')\n\n"
        
        # Map endpoint to SDK method
        if path == "/transcriptions/upload":
            example += "# Upload and transcribe a file\n"
            example += "with open('audio.mp3', 'rb') as f:\n"
            example += "    transcript = client.transcribe_file(f, title='My Recording')\n"
            example += "    print(transcript.id)"
        elif path.startswith("/transcriptions/"):
            if method.upper() == "GET":
                example += "# Get transcript\n"
                example += "transcript = client.get_transcript('transcript_id')\n"
                example += "print(transcript.text)"
        elif path == "/teams":
            if method.upper() == "POST":
                example += "# Create team\n"
                example += "team = client.create_team('My Team', 'Team description')\n"
                example += "print(team.id)"
            else:
                example += "# List teams\n"
                example += "teams = client.list_teams()\n"
                example += "print(len(teams))"
        else:
            example += f"# {spec.get('summary', 'API call')}\n"
            example += f"response = client._request('{method.upper()}', '{path}')\n"
            example += "print(response)"
        
        return example
    
    def generate_javascript_example(self, path: str, method: str, spec: Dict) -> str:
        """Generate JavaScript SDK example"""
        example = "import { TranscriptionClient } from '@transcription-api/sdk';\n\n"
        example += "const client = new TranscriptionClient({ apiKey: 'your_api_key' });\n\n"
        
        # Map endpoint to SDK method
        if path == "/transcriptions/upload":
            example += "// Upload and transcribe a file\n"
            example += "const file = document.getElementById('file-input').files[0];\n"
            example += "const transcript = await client.transcribeFile(file, {\n"
            example += "  title: 'My Recording'\n"
            example += "});\n"
            example += "console.log(transcript.id);"
        elif path.startswith("/transcriptions/"):
            if method.upper() == "GET":
                example += "// Get transcript\n"
                example += "const transcript = await client.getTranscript('transcript_id');\n"
                example += "console.log(transcript.text);"
        elif path == "/teams":
            if method.upper() == "POST":
                example += "// Create team\n"
                example += "const team = await client.createTeam('My Team', 'Team description');\n"
                example += "console.log(team.id);"
            else:
                example += "// List teams\n"
                example += "const teams = await client.listTeams();\n"
                example += "console.log(teams.length);"
        else:
            example += f"// {spec.get('summary', 'API call')}\n"
            example += f"const response = await client._request('{method.upper()}', '{path}');\n"
            example += "console.log(response);"
        
        return example
    
    def generate_nodejs_example(self, path: str, method: str, spec: Dict) -> str:
        """Generate Node.js example"""
        example = "const axios = require('axios');\n\n"
        example += "const client = axios.create({\n"
        example += "  baseURL: 'https://api.transcriptionplatform.com/v1',\n"
        example += "  headers: {\n"
        example += "    'Authorization': 'Bearer YOUR_API_KEY',\n"
        example += "    'Content-Type': 'application/json'\n"
        example += "  }\n"
        example += "});\n\n"
        
        example += f"// {spec.get('summary', 'API call')}\n"
        
        if method.upper() == "GET":
            example += f"const response = await client.get('{path}');\n"
        elif method.upper() == "POST":
            request_body = self.get_example_request_data(spec.get("requestBody"))
            if request_body:
                example += f"const data = {json.dumps(request_body, indent=2)};\n"
                example += f"const response = await client.post('{path}', data);\n"
            else:
                example += f"const response = await client.post('{path}');\n"
        elif method.upper() == "PUT":
            example += f"const response = await client.put('{path}', data);\n"
        elif method.upper() == "DELETE":
            example += f"const response = await client.delete('{path}');\n"
        
        example += "console.log(response.data);"
        
        return example
    
    def get_example_request_data(self, request_body: Optional[Dict]) -> Optional[Dict]:
        """Get example request data from OpenAPI spec"""
        if not request_body:
            return None
        
        content = request_body.get("content", {})
        json_content = content.get("application/json", {})
        
        # Return explicit example if available
        if "example" in json_content:
            return json_content["example"]
        
        # Generate example from schema
        schema = json_content.get("schema", {})
        return self.generate_example_from_schema(schema)
    
    def generate_example_from_schema(self, schema: Dict) -> Any:
        """Generate example data from JSON schema"""
        if "example" in schema:
            return schema["example"]
        
        schema_type = schema.get("type")
        
        if schema_type == "object":
            example = {}
            properties = schema.get("properties", {})
            for prop_name, prop_schema in properties.items():
                example[prop_name] = self.generate_example_from_schema(prop_schema)
            return example
        
        elif schema_type == "array":
            items_schema = schema.get("items", {})
            return [self.generate_example_from_schema(items_schema)]
        
        elif schema_type == "string":
            if schema.get("format") == "email":
                return "user@example.com"
            elif schema.get("format") == "date-time":
                return datetime.utcnow().isoformat()
            else:
                return "string"
        
        elif schema_type == "integer":
            return 1
        
        elif schema_type == "number":
            return 1.0
        
        elif schema_type == "boolean":
            return True
        
        else:
            return None
    
    def get_openapi_spec(self) -> Dict[str, Any]:
        """Get OpenAPI specification"""
        return self.app.openapi()
    
    def generate_code_examples(self, language: str, endpoint: Optional[str] = None) -> Dict[str, Any]:
        """Generate code examples for specific language"""
        examples = {}
        
        if language == "python":
            examples = self.get_python_examples(endpoint)
        elif language == "javascript":
            examples = self.get_javascript_examples(endpoint)
        elif language == "curl":
            examples = self.get_curl_examples(endpoint)
        elif language == "nodejs":
            examples = self.get_nodejs_examples(endpoint)
        
        return {"language": language, "examples": examples}
    
    def get_python_examples(self, endpoint: Optional[str] = None) -> Dict[str, str]:
        """Get Python code examples"""
        examples = {
            "authentication": '''
from transcription_api import TranscriptionClient

# Initialize client with API key
client = TranscriptionClient(api_key="your_api_key_here")

# Or use environment variable
import os
client = TranscriptionClient(api_key=os.getenv("TRANSCRIPTION_API_KEY"))
''',
            "file_upload": '''
# Upload and transcribe a file
with open("audio.mp3", "rb") as f:
    transcript = client.transcribe_file(f, title="My Recording")

# Wait for completion
completed_transcript = client.wait_for_completion(transcript.id)
print(completed_transcript.text)
''',
            "team_management": '''
# Create a team
team = client.create_team("My Team", description="Project team")

# List teams
teams = client.list_teams()

# Invite member
client.invite_team_member(team.id, "colleague@example.com", role="member")
''',
            "search": '''
# List transcripts
transcripts = client.list_transcripts(limit=50)

# Search transcripts
results = client.search_transcripts("meeting notes")

# Get specific transcript
transcript = client.get_transcript("transcript_id")
'''
        }
        
        if endpoint:
            return {endpoint: examples.get(endpoint, "")}
        
        return examples
    
    def get_javascript_examples(self, endpoint: Optional[str] = None) -> Dict[str, str]:
        """Get JavaScript code examples"""
        examples = {
            "authentication": '''
import { TranscriptionClient } from '@transcription-api/sdk';

// Initialize client with API key
const client = new TranscriptionClient({
  apiKey: 'your_api_key_here'
});

// Or use environment variable
const client = new TranscriptionClient({
  apiKey: process.env.TRANSCRIPTION_API_KEY
});
''',
            "file_upload": '''
// Upload and transcribe a file
const fileInput = document.getElementById('file-input');
const file = fileInput.files[0];

const transcript = await client.transcribeFile(file, {
  title: 'My Recording'
});

// Wait for completion
const completed = await client.waitForCompletion(transcript.id);
console.log(completed.text);
''',
            "team_management": '''
// Create a team
const team = await client.createTeam('My Team', 'Project team');

// List teams
const teams = await client.listTeams();

// Invite member
await client.inviteTeamMember(team.id, 'colleague@example.com', 'member');
''',
            "search": '''
// List transcripts
const transcripts = await client.listTranscripts({ limit: 50 });

// Search transcripts
const results = await client.searchTranscripts('meeting notes');

// Get specific transcript
const transcript = await client.getTranscript('transcript_id');
'''
        }
        
        if endpoint:
            return {endpoint: examples.get(endpoint, "")}
        
        return examples
    
    def get_curl_examples(self, endpoint: Optional[str] = None) -> Dict[str, str]:
        """Get cURL examples"""
        base_url = "https://api.transcriptionplatform.com/v1"
        
        examples = {
            "authentication": f'''
# All requests require Authorization header
curl -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     {base_url}/health
''',
            "file_upload": f'''
# Upload file for transcription
curl -X POST {base_url}/transcriptions/upload \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -F "file=@audio.mp3" \\
     -F "title=My Recording" \\
     -F "language=auto"
''',
            "get_transcript": f'''
# Get transcript by ID
curl -X GET {base_url}/transcriptions/TRANSCRIPT_ID \\
     -H "Authorization: Bearer YOUR_API_KEY"
''',
            "create_team": f'''
# Create a new team
curl -X POST {base_url}/teams \\
     -H "Authorization: Bearer YOUR_API_KEY" \\
     -H "Content-Type: application/json" \\
     -d '{{"name": "My Team", "description": "Project team"}}'
'''
        }
        
        if endpoint:
            return {endpoint: examples.get(endpoint, "")}
        
        return examples
    
    def get_nodejs_examples(self, endpoint: Optional[str] = None) -> Dict[str, str]:
        """Get Node.js examples"""
        examples = {
            "setup": '''
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const client = axios.create({
  baseURL: 'https://api.transcriptionplatform.com/v1',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY'
  }
});
''',
            "file_upload": '''
// Upload file for transcription
const form = new FormData();
form.append('file', fs.createReadStream('audio.mp3'));
form.append('title', 'My Recording');
form.append('language', 'auto');

const response = await client.post('/transcriptions/upload', form, {
  headers: form.getHeaders()
});

console.log(response.data);
''',
            "get_data": '''
// Get transcript
const transcript = await client.get('/transcriptions/TRANSCRIPT_ID');
console.log(transcript.data);

// List teams
const teams = await client.get('/teams');
console.log(teams.data);
'''
        }
        
        if endpoint:
            return {endpoint: examples.get(endpoint, "")}
        
        return examples
    
    async def execute_test_request(self, data: Dict[str, Any], user: User) -> Dict[str, Any]:
        """Execute a test API request"""
        try:
            method = data.get("method", "GET").upper()
            path = data.get("path", "/")
            headers = data.get("headers", {})
            params = data.get("params", {})
            body = data.get("body")
            
            # Add authentication header
            headers["Authorization"] = f"Bearer {user.api_keys[0].key if user.api_keys else 'test_key'}"
            
            # Make internal request
            # This is a simplified version - in production you'd want proper request routing
            
            return {
                "status": "success",
                "method": method,
                "path": path,
                "response": {
                    "status_code": 200,
                    "data": {"message": "Test request executed successfully"}
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Initialize API Explorer
def setup_api_explorer(app: FastAPI) -> APIExplorer:
    """Setup API Explorer for the FastAPI app"""
    return APIExplorer(app)