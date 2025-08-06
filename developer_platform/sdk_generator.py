"""
SDK Generator for Multiple Programming Languages

Automatically generates client SDKs for popular programming languages
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import textwrap
import json

class SDKLanguage(str, Enum):
    """Supported SDK languages"""
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    CSHARP = "csharp"
    RUBY = "ruby"
    PHP = "php"

class APIEndpoint(BaseModel):
    """API endpoint definition"""
    path: str
    method: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    response: Dict[str, Any]
    requires_auth: bool = True

class SDKConfig(BaseModel):
    """SDK generation configuration"""
    api_name: str = "TranscriptionAPI"
    api_version: str = "v1"
    base_url: str = "https://api.transcription.io"
    package_name: str
    author: str = "Transcription Platform"
    license: str = "MIT"
    description: str = "Official SDK for Transcription API"

class SDKGenerator:
    """Generate SDKs for multiple languages"""
    
    def __init__(self, config: SDKConfig):
        self.config = config
        self.endpoints = self._define_endpoints()
    
    def _define_endpoints(self) -> List[APIEndpoint]:
        """Define API endpoints"""
        return [
            APIEndpoint(
                path="/transcriptions",
                method="POST",
                description="Create a new transcription",
                parameters=[],
                request_body={
                    "file_url": "string",
                    "language": "string?",
                    "speaker_count": "integer?"
                },
                response={"id": "string", "status": "string"}
            ),
            APIEndpoint(
                path="/transcriptions/{id}",
                method="GET",
                description="Get transcription details",
                parameters=[{"name": "id", "type": "string", "required": True}],
                request_body=None,
                response={
                    "id": "string",
                    "status": "string",
                    "text": "string?",
                    "segments": "array"
                }
            ),
            APIEndpoint(
                path="/transcriptions/{id}/entities",
                method="GET",
                description="Get entities from transcription",
                parameters=[
                    {"name": "id", "type": "string", "required": True},
                    {"name": "type", "type": "string", "required": False}
                ],
                request_body=None,
                response={"entities": "array"}
            ),
            APIEndpoint(
                path="/transcriptions/{id}/summary",
                method="POST",
                description="Generate summary",
                parameters=[{"name": "id", "type": "string", "required": True}],
                request_body={"type": "string?"},
                response={"summary": "string", "key_points": "array"}
            )
        ]
    
    def generate_sdk(self, language: SDKLanguage) -> Dict[str, str]:
        """Generate SDK for specified language"""
        generators = {
            SDKLanguage.PYTHON: self._generate_python_sdk,
            SDKLanguage.JAVASCRIPT: self._generate_javascript_sdk,
            SDKLanguage.TYPESCRIPT: self._generate_typescript_sdk,
            SDKLanguage.GO: self._generate_go_sdk,
            SDKLanguage.JAVA: self._generate_java_sdk,
            SDKLanguage.CSHARP: self._generate_csharp_sdk,
            SDKLanguage.RUBY: self._generate_ruby_sdk,
            SDKLanguage.PHP: self._generate_php_sdk
        }
        
        generator = generators.get(language)
        if not generator:
            raise ValueError(f"Unsupported language: {language}")
        
        return generator()
    
    def _generate_python_sdk(self) -> Dict[str, str]:
        """Generate Python SDK"""
        # Main client file
        client_code = textwrap.dedent(f'''
            """
            {self.config.description}
            
            Version: {self.config.api_version}
            """
            
            import requests
            from typing import Dict, List, Optional, Any
            from datetime import datetime
            import json
            
            
            class TranscriptionError(Exception):
                """Base exception for Transcription API errors"""
                pass
            
            
            class AuthenticationError(TranscriptionError):
                """Authentication failed"""
                pass
            
            
            class RateLimitError(TranscriptionError):
                """Rate limit exceeded"""
                pass
            
            
            class {self.config.api_name}Client:
                """Client for {self.config.api_name}"""
                
                def __init__(self, api_key: str, base_url: str = "{self.config.base_url}"):
                    """
                    Initialize the client.
                    
                    Args:
                        api_key: Your API key
                        base_url: Base URL for the API
                    """
                    self.api_key = api_key
                    self.base_url = base_url.rstrip('/')
                    self.session = requests.Session()
                    self.session.headers.update({{
                        'Authorization': f'Bearer {{api_key}}',
                        'Content-Type': 'application/json',
                        'User-Agent': f'{self.config.package_name}/{self.config.api_version}'
                    }})
                
                def _request(
                    self,
                    method: str,
                    path: str,
                    params: Optional[Dict[str, Any]] = None,
                    json_data: Optional[Dict[str, Any]] = None
                ) -> Dict[str, Any]:
                    """Make HTTP request to API"""
                    url = f"{{self.base_url}}{{path}}"
                    
                    try:
                        response = self.session.request(
                            method=method,
                            url=url,
                            params=params,
                            json=json_data,
                            timeout=30
                        )
                        
                        # Handle rate limiting
                        if response.status_code == 429:
                            retry_after = response.headers.get('Retry-After', '60')
                            raise RateLimitError(f"Rate limit exceeded. Retry after {{retry_after}} seconds")
                        
                        # Handle authentication errors
                        if response.status_code == 401:
                            raise AuthenticationError("Invalid API key")
                        
                        response.raise_for_status()
                        
                        return response.json()
                        
                    except requests.exceptions.RequestException as e:
                        raise TranscriptionError(f"Request failed: {{str(e)}}")
                
                # Transcription methods
                def create_transcription(
                    self,
                    file_url: str,
                    language: Optional[str] = None,
                    speaker_count: Optional[int] = None,
                    auto_summarize: bool = False,
                    webhook_url: Optional[str] = None
                ) -> Dict[str, Any]:
                    """
                    Create a new transcription.
                    
                    Args:
                        file_url: URL of the audio/video file
                        language: Language code (e.g., 'en-US')
                        speaker_count: Number of speakers (for diarization)
                        auto_summarize: Automatically generate summary
                        webhook_url: URL for webhook notifications
                    
                    Returns:
                        Dict containing transcription ID and status
                    """
                    data = {{"file_url": file_url}}
                    if language:
                        data["language"] = language
                    if speaker_count:
                        data["speaker_count"] = speaker_count
                    if auto_summarize:
                        data["auto_summarize"] = auto_summarize
                    if webhook_url:
                        data["webhook_url"] = webhook_url
                    
                    return self._request("POST", "/transcriptions", json_data=data)
                
                def get_transcription(self, transcription_id: str) -> Dict[str, Any]:
                    """
                    Get transcription details.
                    
                    Args:
                        transcription_id: ID of the transcription
                    
                    Returns:
                        Dict containing transcription details
                    """
                    return self._request("GET", f"/transcriptions/{{transcription_id}}")
                
                def list_transcriptions(
                    self,
                    status: Optional[str] = None,
                    limit: int = 50,
                    offset: int = 0
                ) -> Dict[str, Any]:
                    """
                    List transcriptions.
                    
                    Args:
                        status: Filter by status
                        limit: Maximum number of results
                        offset: Offset for pagination
                    
                    Returns:
                        Dict containing list of transcriptions
                    """
                    params = {{"limit": limit, "offset": offset}}
                    if status:
                        params["status"] = status
                    
                    return self._request("GET", "/transcriptions", params=params)
                
                def get_entities(
                    self,
                    transcription_id: str,
                    entity_type: Optional[str] = None
                ) -> Dict[str, Any]:
                    """
                    Get entities from transcription.
                    
                    Args:
                        transcription_id: ID of the transcription
                        entity_type: Filter by entity type
                    
                    Returns:
                        Dict containing extracted entities
                    """
                    params = {{}}
                    if entity_type:
                        params["type"] = entity_type
                    
                    return self._request(
                        "GET",
                        f"/transcriptions/{{transcription_id}}/entities",
                        params=params
                    )
                
                def generate_summary(
                    self,
                    transcription_id: str,
                    summary_type: str = "general"
                ) -> Dict[str, Any]:
                    """
                    Generate summary for transcription.
                    
                    Args:
                        transcription_id: ID of the transcription
                        summary_type: Type of summary to generate
                    
                    Returns:
                        Dict containing summary
                    """
                    return self._request(
                        "POST",
                        f"/transcriptions/{{transcription_id}}/summary",
                        json_data={{"type": summary_type}}
                    )
                
                def export_transcription(
                    self,
                    transcription_id: str,
                    format: str = "txt"
                ) -> bytes:
                    """
                    Export transcription in specified format.
                    
                    Args:
                        transcription_id: ID of the transcription
                        format: Export format (txt, srt, vtt, json)
                    
                    Returns:
                        Exported content as bytes
                    """
                    response = self.session.get(
                        f"{{self.base_url}}/transcriptions/{{transcription_id}}/export",
                        params={{"format": format}},
                        stream=True
                    )
                    response.raise_for_status()
                    return response.content
            
            
            # Convenience functions
            def create_client(api_key: str) -> {self.config.api_name}Client:
                """Create a new API client"""
                return {self.config.api_name}Client(api_key)
        ''').strip()
        
        # Setup.py file
        setup_code = textwrap.dedent(f'''
            from setuptools import setup, find_packages
            
            with open("README.md", "r", encoding="utf-8") as fh:
                long_description = fh.read()
            
            setup(
                name="{self.config.package_name}",
                version="{self.config.api_version}.0",
                author="{self.config.author}",
                author_email="support@transcription.io",
                description="{self.config.description}",
                long_description=long_description,
                long_description_content_type="text/markdown",
                url="https://github.com/transcription/{self.config.package_name}",
                packages=find_packages(),
                classifiers=[
                    "Programming Language :: Python :: 3",
                    "License :: OSI Approved :: MIT License",
                    "Operating System :: OS Independent",
                ],
                python_requires=">=3.7",
                install_requires=[
                    "requests>=2.25.0",
                ],
            )
        ''').strip()
        
        # Example usage
        example_code = textwrap.dedent(f'''
            from {self.config.package_name} import create_client
            
            # Initialize client
            client = create_client("your-api-key")
            
            # Create transcription
            result = client.create_transcription(
                file_url="https://example.com/audio.mp3",
                language="en-US",
                speaker_count=2
            )
            
            transcription_id = result["id"]
            print(f"Transcription created: {{transcription_id}}")
            
            # Check status
            status = client.get_transcription(transcription_id)
            print(f"Status: {{status['status']}}")
            
            # Get entities
            entities = client.get_entities(transcription_id)
            for entity in entities["entities"]:
                print(f"Found {{entity['type']}}: {{entity['text']}}")
            
            # Generate summary
            summary = client.generate_summary(transcription_id)
            print(f"Summary: {{summary['summary']}}")
        ''').strip()
        
        return {
            f"{self.config.package_name}.py": client_code,
            "setup.py": setup_code,
            "example.py": example_code
        }
    
    def _generate_javascript_sdk(self) -> Dict[str, str]:
        """Generate JavaScript SDK"""
        # Main client file
        client_code = textwrap.dedent(f'''
            /**
             * {self.config.description}
             * @version {self.config.api_version}
             */
            
            class TranscriptionError extends Error {{
                constructor(message, code = null) {{
                    super(message);
                    this.name = 'TranscriptionError';
                    this.code = code;
                }}
            }}
            
            class {self.config.api_name}Client {{
                /**
                 * Initialize the client
                 * @param {{string}} apiKey - Your API key
                 * @param {{string}} [baseUrl={self.config.base_url}] - Base URL for the API
                 */
                constructor(apiKey, baseUrl = '{self.config.base_url}') {{
                    this.apiKey = apiKey;
                    this.baseUrl = baseUrl.replace(/\/$/, '');
                }}
                
                /**
                 * Make HTTP request to API
                 * @private
                 */
                async _request(method, path, options = {{}}) {{
                    const url = `${{this.baseUrl}}${{path}}`;
                    
                    const headers = {{
                        'Authorization': `Bearer ${{this.apiKey}}`,
                        'Content-Type': 'application/json',
                        'User-Agent': '{self.config.package_name}/{self.config.api_version}'
                    }};
                    
                    const config = {{
                        method,
                        headers,
                        ...options
                    }};
                    
                    if (options.params) {{
                        const params = new URLSearchParams(options.params);
                        config.url = `${{url}}?${{params}}`;
                    }}
                    
                    if (options.data) {{
                        config.body = JSON.stringify(options.data);
                    }}
                    
                    try {{
                        const response = await fetch(url, config);
                        
                        if (response.status === 429) {{
                            const retryAfter = response.headers.get('Retry-After') || '60';
                            throw new TranscriptionError(
                                `Rate limit exceeded. Retry after ${{retryAfter}} seconds`,
                                'RATE_LIMIT'
                            );
                        }}
                        
                        if (response.status === 401) {{
                            throw new TranscriptionError('Invalid API key', 'AUTH_ERROR');
                        }}
                        
                        if (!response.ok) {{
                            const error = await response.json().catch(() => ({{}}));
                            throw new TranscriptionError(
                                error.message || `HTTP ${{response.status}}`,
                                error.code
                            );
                        }}
                        
                        return await response.json();
                    }} catch (error) {{
                        if (error instanceof TranscriptionError) {{
                            throw error;
                        }}
                        throw new TranscriptionError(`Request failed: ${{error.message}}`);
                    }}
                }}
                
                /**
                 * Create a new transcription
                 * @param {{Object}} options - Transcription options
                 * @param {{string}} options.fileUrl - URL of the audio/video file
                 * @param {{string}} [options.language] - Language code
                 * @param {{number}} [options.speakerCount] - Number of speakers
                 * @returns {{Promise<Object>}} Transcription details
                 */
                async createTranscription(options) {{
                    return this._request('POST', '/transcriptions', {{
                        data: {{
                            file_url: options.fileUrl,
                            language: options.language,
                            speaker_count: options.speakerCount,
                            auto_summarize: options.autoSummarize,
                            webhook_url: options.webhookUrl
                        }}
                    }});
                }}
                
                /**
                 * Get transcription details
                 * @param {{string}} transcriptionId - Transcription ID
                 * @returns {{Promise<Object>}} Transcription details
                 */
                async getTranscription(transcriptionId) {{
                    return this._request('GET', `/transcriptions/${{transcriptionId}}`);
                }}
                
                /**
                 * List transcriptions
                 * @param {{Object}} [options] - List options
                 * @returns {{Promise<Object>}} List of transcriptions
                 */
                async listTranscriptions(options = {{}}) {{
                    return this._request('GET', '/transcriptions', {{
                        params: {{
                            status: options.status,
                            limit: options.limit || 50,
                            offset: options.offset || 0
                        }}
                    }});
                }}
                
                /**
                 * Get entities from transcription
                 * @param {{string}} transcriptionId - Transcription ID
                 * @param {{string}} [entityType] - Filter by entity type
                 * @returns {{Promise<Object>}} Extracted entities
                 */
                async getEntities(transcriptionId, entityType = null) {{
                    const params = {{}};
                    if (entityType) params.type = entityType;
                    
                    return this._request(
                        'GET',
                        `/transcriptions/${{transcriptionId}}/entities`,
                        {{ params }}
                    );
                }}
                
                /**
                 * Generate summary for transcription
                 * @param {{string}} transcriptionId - Transcription ID
                 * @param {{string}} [summaryType='general'] - Type of summary
                 * @returns {{Promise<Object>}} Summary details
                 */
                async generateSummary(transcriptionId, summaryType = 'general') {{
                    return this._request(
                        'POST',
                        `/transcriptions/${{transcriptionId}}/summary`,
                        {{ data: {{ type: summaryType }} }}
                    );
                }}
            }}
            
            // Export for different environments
            if (typeof module !== 'undefined' && module.exports) {{
                module.exports = {{ {self.config.api_name}Client, TranscriptionError }};
            }} else {{
                window.{self.config.api_name}Client = {self.config.api_name}Client;
                window.TranscriptionError = TranscriptionError;
            }}
        ''').strip()
        
        # Package.json
        package_json = json.dumps({
            "name": f"@transcription/{self.config.package_name}",
            "version": f"{self.config.api_version}.0.0",
            "description": self.config.description,
            "main": "index.js",
            "scripts": {
                "test": "jest"
            },
            "keywords": ["transcription", "api", "sdk", "speech-to-text"],
            "author": self.config.author,
            "license": self.config.license,
            "dependencies": {
                "node-fetch": "^2.6.1"
            },
            "devDependencies": {
                "jest": "^27.0.0"
            }
        }, indent=2)
        
        # Example usage
        example_code = textwrap.dedent(f'''
            const {{ {self.config.api_name}Client }} = require('{self.config.package_name}');
            
            // Initialize client
            const client = new {self.config.api_name}Client('your-api-key');
            
            async function example() {{
                try {{
                    // Create transcription
                    const result = await client.createTranscription({{
                        fileUrl: 'https://example.com/audio.mp3',
                        language: 'en-US',
                        speakerCount: 2
                    }});
                    
                    const transcriptionId = result.id;
                    console.log(`Transcription created: ${{transcriptionId}}`);
                    
                    // Check status
                    const status = await client.getTranscription(transcriptionId);
                    console.log(`Status: ${{status.status}}`);
                    
                    // Get entities
                    const entities = await client.getEntities(transcriptionId);
                    entities.entities.forEach(entity => {{
                        console.log(`Found ${{entity.type}}: ${{entity.text}}`);
                    }});
                    
                    // Generate summary
                    const summary = await client.generateSummary(transcriptionId);
                    console.log(`Summary: ${{summary.summary}}`);
                    
                }} catch (error) {{
                    console.error('Error:', error.message);
                }}
            }}
            
            example();
        ''').strip()
        
        return {
            "index.js": client_code,
            "package.json": package_json,
            "example.js": example_code
        }
    
    def _generate_typescript_sdk(self) -> Dict[str, str]:
        """Generate TypeScript SDK"""
        # Type definitions
        types_code = textwrap.dedent(f'''
            /**
             * Type definitions for {self.config.api_name}
             */
            
            export interface TranscriptionOptions {{
                fileUrl: string;
                language?: string;
                speakerCount?: number;
                autoSummarize?: boolean;
                webhookUrl?: string;
            }}
            
            export interface Transcription {{
                id: string;
                status: 'pending' | 'processing' | 'completed' | 'failed';
                fileName: string;
                duration?: number;
                createdAt: string;
                completedAt?: string;
                text?: string;
                segments?: TranscriptionSegment[];
            }}
            
            export interface TranscriptionSegment {{
                speakerId: string;
                text: string;
                startTime: number;
                endTime: number;
                confidence: number;
            }}
            
            export interface Entity {{
                id: string;
                text: string;
                type: 'PERSON' | 'ORG' | 'LOC' | 'DATE' | 'TIME' | 'MONEY' | 'PRODUCT' | 'EVENT';
                confidence: number;
                startTime?: number;
                endTime?: number;
            }}
            
            export interface Summary {{
                id: string;
                summary: string;
                keyPoints: string[];
                actionItems?: string[];
                topics?: string[];
            }}
            
            export interface ListOptions {{
                status?: string;
                limit?: number;
                offset?: number;
            }}
            
            export interface RateLimitInfo {{
                remaining: number;
                limit: number;
                reset: number;
            }}
        ''').strip()
        
        # Main client file
        client_code = textwrap.dedent(f'''
            /**
             * {self.config.description}
             * @version {self.config.api_version}
             */
            
            import {{
                TranscriptionOptions,
                Transcription,
                Entity,
                Summary,
                ListOptions,
                RateLimitInfo
            }} from './types';
            
            export class TranscriptionError extends Error {{
                constructor(
                    message: string,
                    public code?: string,
                    public statusCode?: number
                ) {{
                    super(message);
                    this.name = 'TranscriptionError';
                }}
            }}
            
            export class {self.config.api_name}Client {{
                private apiKey: string;
                private baseUrl: string;
                
                constructor(apiKey: string, baseUrl: string = '{self.config.base_url}') {{
                    this.apiKey = apiKey;
                    this.baseUrl = baseUrl.replace(/\/$/, '');
                }}
                
                private async request<T>(
                    method: string,
                    path: string,
                    options: {{
                        params?: Record<string, any>;
                        data?: any;
                    }} = {{}}
                ): Promise<T> {{
                    const url = new URL(`${{this.baseUrl}}${{path}}`);
                    
                    if (options.params) {{
                        Object.entries(options.params).forEach(([key, value]) => {{
                            if (value !== undefined) {{
                                url.searchParams.append(key, value.toString());
                            }}
                        }});
                    }}
                    
                    const headers: HeadersInit = {{
                        'Authorization': `Bearer ${{this.apiKey}}`,
                        'Content-Type': 'application/json',
                        'User-Agent': '{self.config.package_name}/{self.config.api_version}'
                    }};
                    
                    const config: RequestInit = {{
                        method,
                        headers,
                    }};
                    
                    if (options.data) {{
                        config.body = JSON.stringify(options.data);
                    }}
                    
                    const response = await fetch(url.toString(), config);
                    
                    if (response.status === 429) {{
                        const retryAfter = response.headers.get('Retry-After') || '60';
                        throw new TranscriptionError(
                            `Rate limit exceeded. Retry after ${{retryAfter}} seconds`,
                            'RATE_LIMIT',
                            429
                        );
                    }}
                    
                    if (response.status === 401) {{
                        throw new TranscriptionError('Invalid API key', 'AUTH_ERROR', 401);
                    }}
                    
                    if (!response.ok) {{
                        const error = await response.json().catch(() => ({{}}));
                        throw new TranscriptionError(
                            error.message || `HTTP ${{response.status}}`,
                            error.code,
                            response.status
                        );
                    }}
                    
                    return response.json();
                }}
                
                async createTranscription(
                    options: TranscriptionOptions
                ): Promise<{{ id: string; status: string }}> {{
                    return this.request('POST', '/transcriptions', {{
                        data: {{
                            file_url: options.fileUrl,
                            language: options.language,
                            speaker_count: options.speakerCount,
                            auto_summarize: options.autoSummarize,
                            webhook_url: options.webhookUrl
                        }}
                    }});
                }}
                
                async getTranscription(transcriptionId: string): Promise<Transcription> {{
                    return this.request('GET', `/transcriptions/${{transcriptionId}}`);
                }}
                
                async listTranscriptions(
                    options: ListOptions = {{}}
                ): Promise<{{ transcriptions: Transcription[]; total: number }}> {{
                    return this.request('GET', '/transcriptions', {{
                        params: {{
                            status: options.status,
                            limit: options.limit || 50,
                            offset: options.offset || 0
                        }}
                    }});
                }}
                
                async getEntities(
                    transcriptionId: string,
                    entityType?: string
                ): Promise<{{ entities: Entity[] }}> {{
                    return this.request('GET', `/transcriptions/${{transcriptionId}}/entities`, {{
                        params: {{ type: entityType }}
                    }});
                }}
                
                async generateSummary(
                    transcriptionId: string,
                    summaryType: string = 'general'
                ): Promise<Summary> {{
                    return this.request('POST', `/transcriptions/${{transcriptionId}}/summary`, {{
                        data: {{ type: summaryType }}
                    }});
                }}
                
                async deleteTranscription(transcriptionId: string): Promise<void> {{
                    await this.request('DELETE', `/transcriptions/${{transcriptionId}}`);
                }}
            }}
        ''').strip()
        
        # tsconfig.json
        tsconfig = json.dumps({
            "compilerOptions": {
                "target": "ES2018",
                "module": "commonjs",
                "lib": ["ES2018"],
                "declaration": True,
                "outDir": "./dist",
                "strict": True,
                "esModuleInterop": True,
                "skipLibCheck": True,
                "forceConsistentCasingInFileNames": True
            },
            "include": ["src/**/*"],
            "exclude": ["node_modules", "dist"]
        }, indent=2)
        
        return {
            "src/types.ts": types_code,
            "src/client.ts": client_code,
            "tsconfig.json": tsconfig
        }
    
    def _generate_go_sdk(self) -> Dict[str, str]:
        """Generate Go SDK"""
        # Main client
        client_code = textwrap.dedent(f'''
            // Package {self.config.package_name} provides a client for the Transcription API
            package {self.config.package_name}
            
            import (
                "bytes"
                "encoding/json"
                "fmt"
                "io"
                "net/http"
                "net/url"
                "time"
            )
            
            const (
                defaultBaseURL = "{self.config.base_url}"
                userAgent      = "{self.config.package_name}/{self.config.api_version}"
            )
            
            // Client represents a Transcription API client
            type Client struct {{
                APIKey     string
                BaseURL    string
                HTTPClient *http.Client
            }}
            
            // NewClient creates a new API client
            func NewClient(apiKey string) *Client {{
                return &Client{{
                    APIKey:     apiKey,
                    BaseURL:    defaultBaseURL,
                    HTTPClient: &http.Client{{Timeout: 30 * time.Second}},
                }}
            }}
            
            // TranscriptionOptions represents options for creating a transcription
            type TranscriptionOptions struct {{
                FileURL        string  `json:"file_url"`
                Language       *string `json:"language,omitempty"`
                SpeakerCount   *int    `json:"speaker_count,omitempty"`
                AutoSummarize  bool    `json:"auto_summarize,omitempty"`
                WebhookURL     *string `json:"webhook_url,omitempty"`
            }}
            
            // Transcription represents a transcription
            type Transcription struct {{
                ID          string    `json:"id"`
                Status      string    `json:"status"`
                FileName    string    `json:"file_name"`
                Duration    *float64  `json:"duration,omitempty"`
                CreatedAt   time.Time `json:"created_at"`
                CompletedAt *time.Time `json:"completed_at,omitempty"`
                Text        *string   `json:"text,omitempty"`
            }}
            
            // Entity represents an extracted entity
            type Entity struct {{
                ID         string   `json:"id"`
                Text       string   `json:"text"`
                Type       string   `json:"type"`
                Confidence float64  `json:"confidence"`
                StartTime  *float64 `json:"start_time,omitempty"`
                EndTime    *float64 `json:"end_time,omitempty"`
            }}
            
            // Error represents an API error
            type Error struct {{
                Message    string `json:"message"`
                Code       string `json:"code"`
                StatusCode int    `json:"-"`
            }}
            
            func (e *Error) Error() string {{
                return fmt.Sprintf("%s (code: %s, status: %d)", e.Message, e.Code, e.StatusCode)
            }}
            
            // doRequest performs an HTTP request
            func (c *Client) doRequest(method, path string, params url.Values, body interface{{}}) ([]byte, error) {{
                u, err := url.Parse(c.BaseURL + path)
                if err != nil {{
                    return nil, err
                }}
                
                if params != nil {{
                    u.RawQuery = params.Encode()
                }}
                
                var bodyReader io.Reader
                if body != nil {{
                    jsonBody, err := json.Marshal(body)
                    if err != nil {{
                        return nil, err
                    }}
                    bodyReader = bytes.NewReader(jsonBody)
                }}
                
                req, err := http.NewRequest(method, u.String(), bodyReader)
                if err != nil {{
                    return nil, err
                }}
                
                req.Header.Set("Authorization", "Bearer "+c.APIKey)
                req.Header.Set("Content-Type", "application/json")
                req.Header.Set("User-Agent", userAgent)
                
                resp, err := c.HTTPClient.Do(req)
                if err != nil {{
                    return nil, err
                }}
                defer resp.Body.Close()
                
                respBody, err := io.ReadAll(resp.Body)
                if err != nil {{
                    return nil, err
                }}
                
                if resp.StatusCode >= 400 {{
                    var apiErr Error
                    if err := json.Unmarshal(respBody, &apiErr); err != nil {{
                        apiErr.Message = string(respBody)
                    }}
                    apiErr.StatusCode = resp.StatusCode
                    return nil, &apiErr
                }}
                
                return respBody, nil
            }}
            
            // CreateTranscription creates a new transcription
            func (c *Client) CreateTranscription(opts TranscriptionOptions) (*Transcription, error) {{
                body, err := c.doRequest("POST", "/transcriptions", nil, opts)
                if err != nil {{
                    return nil, err
                }}
                
                var result Transcription
                if err := json.Unmarshal(body, &result); err != nil {{
                    return nil, err
                }}
                
                return &result, nil
            }}
            
            // GetTranscription retrieves a transcription by ID
            func (c *Client) GetTranscription(id string) (*Transcription, error) {{
                body, err := c.doRequest("GET", "/transcriptions/"+id, nil, nil)
                if err != nil {{
                    return nil, err
                }}
                
                var result Transcription
                if err := json.Unmarshal(body, &result); err != nil {{
                    return nil, err
                }}
                
                return &result, nil
            }}
            
            // GetEntities retrieves entities from a transcription
            func (c *Client) GetEntities(transcriptionID string, entityType *string) ([]Entity, error) {{
                params := url.Values{{}}
                if entityType != nil {{
                    params.Set("type", *entityType)
                }}
                
                body, err := c.doRequest("GET", "/transcriptions/"+transcriptionID+"/entities", params, nil)
                if err != nil {{
                    return nil, err
                }}
                
                var result struct {{
                    Entities []Entity `json:"entities"`
                }}
                if err := json.Unmarshal(body, &result); err != nil {{
                    return nil, err
                }}
                
                return result.Entities, nil
            }}
        ''').strip()
        
        # Example usage
        example_code = textwrap.dedent(f'''
            package main
            
            import (
                "fmt"
                "log"
                
                "{self.config.package_name}"
            )
            
            func main() {{
                // Initialize client
                client := {self.config.package_name}.NewClient("your-api-key")
                
                // Create transcription
                opts := {self.config.package_name}.TranscriptionOptions{{
                    FileURL: "https://example.com/audio.mp3",
                }}
                
                transcription, err := client.CreateTranscription(opts)
                if err != nil {{
                    log.Fatal(err)
                }}
                
                fmt.Printf("Transcription created: %s\\n", transcription.ID)
                
                // Get transcription details
                details, err := client.GetTranscription(transcription.ID)
                if err != nil {{
                    log.Fatal(err)
                }}
                
                fmt.Printf("Status: %s\\n", details.Status)
                
                // Get entities
                entities, err := client.GetEntities(transcription.ID, nil)
                if err != nil {{
                    log.Fatal(err)
                }}
                
                for _, entity := range entities {{
                    fmt.Printf("Found %s: %s\\n", entity.Type, entity.Text)
                }}
            }}
        ''').strip()
        
        # go.mod
        go_mod = textwrap.dedent(f'''
            module github.com/transcription/{self.config.package_name}
            
            go 1.18
        ''').strip()
        
        return {
            "client.go": client_code,
            "example/main.go": example_code,
            "go.mod": go_mod
        }
    
    def _generate_java_sdk(self) -> Dict[str, str]:
        """Generate Java SDK"""
        # Main client
        client_code = textwrap.dedent(f'''
            package io.transcription.sdk;
            
            import com.fasterxml.jackson.databind.ObjectMapper;
            import okhttp3.*;
            
            import java.io.IOException;
            import java.util.Map;
            import java.util.HashMap;
            import java.util.concurrent.TimeUnit;
            
            /**
             * {self.config.description}
             * @version {self.config.api_version}
             */
            public class TranscriptionClient {{
                private static final String DEFAULT_BASE_URL = "{self.config.base_url}";
                private static final String USER_AGENT = "{self.config.package_name}/{self.config.api_version}";
                
                private final String apiKey;
                private final String baseUrl;
                private final OkHttpClient httpClient;
                private final ObjectMapper objectMapper;
                
                public TranscriptionClient(String apiKey) {{
                    this(apiKey, DEFAULT_BASE_URL);
                }}
                
                public TranscriptionClient(String apiKey, String baseUrl) {{
                    this.apiKey = apiKey;
                    this.baseUrl = baseUrl.replaceAll("/$", "");
                    this.httpClient = new OkHttpClient.Builder()
                        .connectTimeout(30, TimeUnit.SECONDS)
                        .readTimeout(30, TimeUnit.SECONDS)
                        .build();
                    this.objectMapper = new ObjectMapper();
                }}
                
                /**
                 * Create a new transcription
                 */
                public Transcription createTranscription(TranscriptionRequest request) 
                        throws TranscriptionException {{
                    String json = toJson(request);
                    RequestBody body = RequestBody.create(
                        json, MediaType.parse("application/json")
                    );
                    
                    Request httpRequest = new Request.Builder()
                        .url(baseUrl + "/transcriptions")
                        .post(body)
                        .header("Authorization", "Bearer " + apiKey)
                        .header("User-Agent", USER_AGENT)
                        .build();
                    
                    return executeRequest(httpRequest, Transcription.class);
                }}
                
                /**
                 * Get transcription details
                 */
                public Transcription getTranscription(String transcriptionId) 
                        throws TranscriptionException {{
                    Request request = new Request.Builder()
                        .url(baseUrl + "/transcriptions/" + transcriptionId)
                        .get()
                        .header("Authorization", "Bearer " + apiKey)
                        .header("User-Agent", USER_AGENT)
                        .build();
                    
                    return executeRequest(request, Transcription.class);
                }}
                
                /**
                 * Get entities from transcription
                 */
                public EntityResponse getEntities(String transcriptionId, String entityType) 
                        throws TranscriptionException {{
                    HttpUrl.Builder urlBuilder = HttpUrl.parse(
                        baseUrl + "/transcriptions/" + transcriptionId + "/entities"
                    ).newBuilder();
                    
                    if (entityType != null) {{
                        urlBuilder.addQueryParameter("type", entityType);
                    }}
                    
                    Request request = new Request.Builder()
                        .url(urlBuilder.build())
                        .get()
                        .header("Authorization", "Bearer " + apiKey)
                        .header("User-Agent", USER_AGENT)
                        .build();
                    
                    return executeRequest(request, EntityResponse.class);
                }}
                
                private <T> T executeRequest(Request request, Class<T> responseType) 
                        throws TranscriptionException {{
                    try (Response response = httpClient.newCall(request).execute()) {{
                        String responseBody = response.body().string();
                        
                        if (!response.isSuccessful()) {{
                            throw new TranscriptionException(
                                "API request failed: " + response.code() + " " + responseBody
                            );
                        }}
                        
                        return objectMapper.readValue(responseBody, responseType);
                    }} catch (IOException e) {{
                        throw new TranscriptionException("Request failed: " + e.getMessage(), e);
                    }}
                }}
                
                private String toJson(Object obj) throws TranscriptionException {{
                    try {{
                        return objectMapper.writeValueAsString(obj);
                    }} catch (Exception e) {{
                        throw new TranscriptionException("JSON serialization failed", e);
                    }}
                }}
                
                // Data classes
                public static class TranscriptionRequest {{
                    private String fileUrl;
                    private String language;
                    private Integer speakerCount;
                    private Boolean autoSummarize;
                    private String webhookUrl;
                    
                    // Getters and setters...
                    public String getFileUrl() {{ return fileUrl; }}
                    public void setFileUrl(String fileUrl) {{ this.fileUrl = fileUrl; }}
                    
                    public String getLanguage() {{ return language; }}
                    public void setLanguage(String language) {{ this.language = language; }}
                    
                    public Integer getSpeakerCount() {{ return speakerCount; }}
                    public void setSpeakerCount(Integer speakerCount) {{ 
                        this.speakerCount = speakerCount; 
                    }}
                }}
                
                public static class Transcription {{
                    private String id;
                    private String status;
                    private String fileName;
                    private Double duration;
                    private String createdAt;
                    private String text;
                    
                    // Getters and setters...
                    public String getId() {{ return id; }}
                    public String getStatus() {{ return status; }}
                    public String getFileName() {{ return fileName; }}
                    public Double getDuration() {{ return duration; }}
                    public String getCreatedAt() {{ return createdAt; }}
                    public String getText() {{ return text; }}
                }}
                
                public static class Entity {{
                    private String id;
                    private String text;
                    private String type;
                    private Double confidence;
                    
                    // Getters...
                    public String getId() {{ return id; }}
                    public String getText() {{ return text; }}
                    public String getType() {{ return type; }}
                    public Double getConfidence() {{ return confidence; }}
                }}
                
                public static class EntityResponse {{
                    private List<Entity> entities;
                    
                    public List<Entity> getEntities() {{ return entities; }}
                }}
                
                public static class TranscriptionException extends Exception {{
                    public TranscriptionException(String message) {{
                        super(message);
                    }}
                    
                    public TranscriptionException(String message, Throwable cause) {{
                        super(message, cause);
                    }}
                }}
            }}
        ''').strip()
        
        # pom.xml
        pom_xml = textwrap.dedent(f'''
            <?xml version="1.0" encoding="UTF-8"?>
            <project xmlns="http://maven.apache.org/POM/4.0.0"
                     xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                     xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
                     http://maven.apache.org/xsd/maven-4.0.0.xsd">
                <modelVersion>4.0.0</modelVersion>
                
                <groupId>io.transcription</groupId>
                <artifactId>{self.config.package_name}</artifactId>
                <version>{self.config.api_version}.0</version>
                <packaging>jar</packaging>
                
                <name>{self.config.api_name} Java SDK</name>
                <description>{self.config.description}</description>
                
                <properties>
                    <maven.compiler.source>11</maven.compiler.source>
                    <maven.compiler.target>11</maven.compiler.target>
                    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
                </properties>
                
                <dependencies>
                    <dependency>
                        <groupId>com.squareup.okhttp3</groupId>
                        <artifactId>okhttp</artifactId>
                        <version>4.10.0</version>
                    </dependency>
                    <dependency>
                        <groupId>com.fasterxml.jackson.core</groupId>
                        <artifactId>jackson-databind</artifactId>
                        <version>2.13.0</version>
                    </dependency>
                </dependencies>
            </project>
        ''').strip()
        
        return {
            "src/main/java/io/transcription/sdk/TranscriptionClient.java": client_code,
            "pom.xml": pom_xml
        }
    
    def _generate_csharp_sdk(self) -> Dict[str, str]:
        """Generate C# SDK"""
        # Main client
        client_code = textwrap.dedent(f'''
            using System;
            using System.Net.Http;
            using System.Net.Http.Headers;
            using System.Text;
            using System.Threading.Tasks;
            using Newtonsoft.Json;
            
            namespace Transcription.SDK
            {{
                /// <summary>
                /// {self.config.description}
                /// </summary>
                public class TranscriptionClient
                {{
                    private const string DefaultBaseUrl = "{self.config.base_url}";
                    private readonly HttpClient httpClient;
                    private readonly string apiKey;
                    private readonly string baseUrl;
                    
                    public TranscriptionClient(string apiKey) : this(apiKey, DefaultBaseUrl)
                    {{
                    }}
                    
                    public TranscriptionClient(string apiKey, string baseUrl)
                    {{
                        this.apiKey = apiKey;
                        this.baseUrl = baseUrl.TrimEnd('/');
                        
                        httpClient = new HttpClient();
                        httpClient.DefaultRequestHeaders.Authorization = 
                            new AuthenticationHeaderValue("Bearer", apiKey);
                        httpClient.DefaultRequestHeaders.UserAgent.ParseAdd(
                            "{self.config.package_name}/{self.config.api_version}"
                        );
                    }}
                    
                    /// <summary>
                    /// Create a new transcription
                    /// </summary>
                    public async Task<TranscriptionResponse> CreateTranscriptionAsync(
                        TranscriptionRequest request)
                    {{
                        var json = JsonConvert.SerializeObject(request);
                        var content = new StringContent(json, Encoding.UTF8, "application/json");
                        
                        var response = await httpClient.PostAsync(
                            $"{{baseUrl}}/transcriptions", content
                        );
                        
                        await EnsureSuccessStatusCode(response);
                        
                        var responseContent = await response.Content.ReadAsStringAsync();
                        return JsonConvert.DeserializeObject<TranscriptionResponse>(responseContent);
                    }}
                    
                    /// <summary>
                    /// Get transcription details
                    /// </summary>
                    public async Task<Transcription> GetTranscriptionAsync(string transcriptionId)
                    {{
                        var response = await httpClient.GetAsync(
                            $"{{baseUrl}}/transcriptions/{{transcriptionId}}"
                        );
                        
                        await EnsureSuccessStatusCode(response);
                        
                        var content = await response.Content.ReadAsStringAsync();
                        return JsonConvert.DeserializeObject<Transcription>(content);
                    }}
                    
                    /// <summary>
                    /// Get entities from transcription
                    /// </summary>
                    public async Task<EntityResponse> GetEntitiesAsync(
                        string transcriptionId, 
                        string entityType = null)
                    {{
                        var url = $"{{baseUrl}}/transcriptions/{{transcriptionId}}/entities";
                        if (!string.IsNullOrEmpty(entityType))
                        {{
                            url += $"?type={{entityType}}";
                        }}
                        
                        var response = await httpClient.GetAsync(url);
                        await EnsureSuccessStatusCode(response);
                        
                        var content = await response.Content.ReadAsStringAsync();
                        return JsonConvert.DeserializeObject<EntityResponse>(content);
                    }}
                    
                    private async Task EnsureSuccessStatusCode(HttpResponseMessage response)
                    {{
                        if (!response.IsSuccessStatusCode)
                        {{
                            var content = await response.Content.ReadAsStringAsync();
                            throw new TranscriptionException(
                                $"API request failed: {{response.StatusCode}} {{content}}"
                            );
                        }}
                    }}
                }}
                
                // Data models
                public class TranscriptionRequest
                {{
                    [JsonProperty("file_url")]
                    public string FileUrl {{ get; set; }}
                    
                    [JsonProperty("language")]
                    public string Language {{ get; set; }}
                    
                    [JsonProperty("speaker_count")]
                    public int? SpeakerCount {{ get; set; }}
                    
                    [JsonProperty("auto_summarize")]
                    public bool AutoSummarize {{ get; set; }}
                    
                    [JsonProperty("webhook_url")]
                    public string WebhookUrl {{ get; set; }}
                }}
                
                public class TranscriptionResponse
                {{
                    public string Id {{ get; set; }}
                    public string Status {{ get; set; }}
                }}
                
                public class Transcription
                {{
                    public string Id {{ get; set; }}
                    public string Status {{ get; set; }}
                    
                    [JsonProperty("file_name")]
                    public string FileName {{ get; set; }}
                    
                    public double? Duration {{ get; set; }}
                    
                    [JsonProperty("created_at")]
                    public DateTime CreatedAt {{ get; set; }}
                    
                    public string Text {{ get; set; }}
                }}
                
                public class Entity
                {{
                    public string Id {{ get; set; }}
                    public string Text {{ get; set; }}
                    public string Type {{ get; set; }}
                    public double Confidence {{ get; set; }}
                }}
                
                public class EntityResponse
                {{
                    public List<Entity> Entities {{ get; set; }}
                }}
                
                public class TranscriptionException : Exception
                {{
                    public TranscriptionException(string message) : base(message)
                    {{
                    }}
                }}
            }}
        ''').strip()
        
        # .csproj file
        csproj = textwrap.dedent(f'''
            <Project Sdk="Microsoft.NET.Sdk">
              <PropertyGroup>
                <TargetFramework>netstandard2.0</TargetFramework>
                <PackageId>{self.config.package_name}</PackageId>
                <Version>{self.config.api_version}.0</Version>
                <Authors>{self.config.author}</Authors>
                <Description>{self.config.description}</Description>
                <PackageLicenseExpression>MIT</PackageLicenseExpression>
              </PropertyGroup>
              
              <ItemGroup>
                <PackageReference Include="Newtonsoft.Json" Version="13.0.1" />
              </ItemGroup>
            </Project>
        ''').strip()
        
        return {
            "TranscriptionClient.cs": client_code,
            f"{self.config.package_name}.csproj": csproj
        }
    
    def _generate_ruby_sdk(self) -> Dict[str, str]:
        """Generate Ruby SDK"""
        # Main client
        client_code = textwrap.dedent(f'''
            # frozen_string_literal: true
            
            require 'net/http'
            require 'json'
            require 'uri'
            
            module Transcription
              # {self.config.description}
              class Client
                DEFAULT_BASE_URL = '{self.config.base_url}'
                USER_AGENT = '{self.config.package_name}/{self.config.api_version}'
                
                attr_accessor :api_key, :base_url
                
                def initialize(api_key, base_url: DEFAULT_BASE_URL)
                  @api_key = api_key
                  @base_url = base_url.chomp('/')
                end
                
                # Create a new transcription
                def create_transcription(file_url:, language: nil, speaker_count: nil, 
                                       auto_summarize: false, webhook_url: nil)
                  data = {{
                    file_url: file_url,
                    language: language,
                    speaker_count: speaker_count,
                    auto_summarize: auto_summarize,
                    webhook_url: webhook_url
                  }}.compact
                  
                  request(:post, '/transcriptions', data: data)
                end
                
                # Get transcription details
                def get_transcription(transcription_id)
                  request(:get, "/transcriptions/#{{transcription_id}}")
                end
                
                # List transcriptions
                def list_transcriptions(status: nil, limit: 50, offset: 0)
                  params = {{ limit: limit, offset: offset }}
                  params[:status] = status if status
                  
                  request(:get, '/transcriptions', params: params)
                end
                
                # Get entities from transcription
                def get_entities(transcription_id, entity_type: nil)
                  params = {{}}
                  params[:type] = entity_type if entity_type
                  
                  request(:get, "/transcriptions/#{{transcription_id}}/entities", params: params)
                end
                
                # Generate summary
                def generate_summary(transcription_id, summary_type: 'general')
                  request(:post, "/transcriptions/#{{transcription_id}}/summary",
                         data: {{ type: summary_type }})
                end
                
                private
                
                def request(method, path, params: nil, data: nil)
                  uri = URI("#{{@base_url}}#{{path}}")
                  uri.query = URI.encode_www_form(params) if params
                  
                  http = Net::HTTP.new(uri.host, uri.port)
                  http.use_ssl = uri.scheme == 'https'
                  
                  request_class = case method
                                  when :get then Net::HTTP::Get
                                  when :post then Net::HTTP::Post
                                  when :delete then Net::HTTP::Delete
                                  else raise ArgumentError, "Unsupported method: #{{method}}"
                                  end
                  
                  request = request_class.new(uri)
                  request['Authorization'] = "Bearer #{{@api_key}}"
                  request['Content-Type'] = 'application/json'
                  request['User-Agent'] = USER_AGENT
                  
                  request.body = data.to_json if data
                  
                  response = http.request(request)
                  
                  handle_response(response)
                end
                
                def handle_response(response)
                  case response.code.to_i
                  when 200..299
                    JSON.parse(response.body, symbolize_names: true)
                  when 401
                    raise AuthenticationError, 'Invalid API key'
                  when 429
                    retry_after = response['Retry-After'] || '60'
                    raise RateLimitError, "Rate limit exceeded. Retry after #{{retry_after}} seconds"
                  else
                    error = JSON.parse(response.body) rescue {{ message: response.body }}
                    raise APIError, error[:message] || "HTTP #{{response.code}}"
                  end
                end
              end
              
              # Exceptions
              class APIError < StandardError; end
              class AuthenticationError < APIError; end
              class RateLimitError < APIError; end
            end
        ''').strip()
        
        # Gemspec
        gemspec = textwrap.dedent(f'''
            Gem::Specification.new do |spec|
              spec.name          = "{self.config.package_name}"
              spec.version       = "{self.config.api_version}.0"
              spec.authors       = ["{self.config.author}"]
              spec.email         = ["support@transcription.io"]
              
              spec.summary       = "{self.config.description}"
              spec.homepage      = "https://github.com/transcription/{self.config.package_name}"
              spec.license       = "MIT"
              
              spec.files         = Dir["lib/**/*.rb"]
              spec.require_paths = ["lib"]
              
              spec.required_ruby_version = ">= 2.5.0"
              
              spec.add_development_dependency "rspec", "~> 3.0"
            end
        ''').strip()
        
        return {
            "lib/transcription.rb": client_code,
            f"{self.config.package_name}.gemspec": gemspec
        }
    
    def _generate_php_sdk(self) -> Dict[str, str]:
        """Generate PHP SDK"""
        # Main client
        client_code = textwrap.dedent(f'''
            <?php
            
            namespace Transcription\\SDK;
            
            use GuzzleHttp\\Client as HttpClient;
            use GuzzleHttp\\Exception\\RequestException;
            
            /**
             * {self.config.description}
             * @version {self.config.api_version}
             */
            class TranscriptionClient
            {{
                const DEFAULT_BASE_URL = '{self.config.base_url}';
                const USER_AGENT = '{self.config.package_name}/{self.config.api_version}';
                
                private $apiKey;
                private $baseUrl;
                private $httpClient;
                
                public function __construct($apiKey, $baseUrl = self::DEFAULT_BASE_URL)
                {{
                    $this->apiKey = $apiKey;
                    $this->baseUrl = rtrim($baseUrl, '/');
                    
                    $this->httpClient = new HttpClient([
                        'base_uri' => $this->baseUrl,
                        'timeout' => 30,
                        'headers' => [
                            'Authorization' => 'Bearer ' . $this->apiKey,
                            'Content-Type' => 'application/json',
                            'User-Agent' => self::USER_AGENT
                        ]
                    ]);
                }}
                
                /**
                 * Create a new transcription
                 */
                public function createTranscription(array $options)
                {{
                    $data = [
                        'file_url' => $options['file_url'],
                        'language' => $options['language'] ?? null,
                        'speaker_count' => $options['speaker_count'] ?? null,
                        'auto_summarize' => $options['auto_summarize'] ?? false,
                        'webhook_url' => $options['webhook_url'] ?? null
                    ];
                    
                    return $this->request('POST', '/transcriptions', ['json' => $data]);
                }}
                
                /**
                 * Get transcription details
                 */
                public function getTranscription($transcriptionId)
                {{
                    return $this->request('GET', '/transcriptions/' . $transcriptionId);
                }}
                
                /**
                 * List transcriptions
                 */
                public function listTranscriptions($status = null, $limit = 50, $offset = 0)
                {{
                    $params = [
                        'limit' => $limit,
                        'offset' => $offset
                    ];
                    
                    if ($status) {{
                        $params['status'] = $status;
                    }}
                    
                    return $this->request('GET', '/transcriptions', ['query' => $params]);
                }}
                
                /**
                 * Get entities from transcription
                 */
                public function getEntities($transcriptionId, $entityType = null)
                {{
                    $params = [];
                    if ($entityType) {{
                        $params['type'] = $entityType;
                    }}
                    
                    return $this->request(
                        'GET',
                        '/transcriptions/' . $transcriptionId . '/entities',
                        ['query' => $params]
                    );
                }}
                
                /**
                 * Generate summary
                 */
                public function generateSummary($transcriptionId, $summaryType = 'general')
                {{
                    return $this->request(
                        'POST',
                        '/transcriptions/' . $transcriptionId . '/summary',
                        ['json' => ['type' => $summaryType]]
                    );
                }}
                
                private function request($method, $path, array $options = [])
                {{
                    try {{
                        $response = $this->httpClient->request($method, $path, $options);
                        return json_decode($response->getBody()->getContents(), true);
                    }} catch (RequestException $e) {{
                        if ($e->hasResponse()) {{
                            $response = $e->getResponse();
                            $statusCode = $response->getStatusCode();
                            $body = json_decode($response->getBody()->getContents(), true);
                            
                            if ($statusCode === 401) {{
                                throw new AuthenticationException('Invalid API key');
                            }} elseif ($statusCode === 429) {{
                                $retryAfter = $response->getHeader('Retry-After')[0] ?? '60';
                                throw new RateLimitException(
                                    "Rate limit exceeded. Retry after $retryAfter seconds"
                                );
                            }}
                            
                            throw new ApiException(
                                $body['message'] ?? "HTTP $statusCode error",
                                $statusCode
                            );
                        }}
                        
                        throw new ApiException('Request failed: ' . $e->getMessage());
                    }}
                }}
            }}
            
            class ApiException extends \\Exception {{}}
            class AuthenticationException extends ApiException {{}}
            class RateLimitException extends ApiException {{}}
        ''').strip()
        
        # composer.json
        composer_json = json.dumps({
            "name": f"transcription/{self.config.package_name}",
            "description": self.config.description,
            "version": f"{self.config.api_version}.0",
            "type": "library",
            "license": "MIT",
            "authors": [{
                "name": self.config.author,
                "email": "support@transcription.io"
            }],
            "require": {
                "php": ">=7.2",
                "guzzlehttp/guzzle": "^7.0"
            },
            "autoload": {
                "psr-4": {
                    "Transcription\\SDK\\": "src/"
                }
            }
        }, indent=2)
        
        return {
            "src/TranscriptionClient.php": client_code,
            "composer.json": composer_json
        }

# Example usage
if __name__ == "__main__":
    # Create SDK configuration
    config = SDKConfig(
        api_name="TranscriptionAPI",
        api_version="v1",
        base_url="https://api.transcription.io",
        package_name="transcription-sdk"
    )
    
    # Initialize generator
    generator = SDKGenerator(config)
    
    # Generate Python SDK
    python_sdk = generator.generate_sdk(SDKLanguage.PYTHON)
    print("Python SDK files:")
    for filename, content in python_sdk.items():
        print(f"  - {filename}")
    
    # Generate JavaScript SDK
    js_sdk = generator.generate_sdk(SDKLanguage.JAVASCRIPT)
    print("\nJavaScript SDK files:")
    for filename, content in js_sdk.items():
        print(f"  - {filename}")
    
    # Generate TypeScript SDK
    ts_sdk = generator.generate_sdk(SDKLanguage.TYPESCRIPT)
    print("\nTypeScript SDK files:")
    for filename, content in ts_sdk.items():
        print(f"  - {filename}")