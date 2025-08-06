"""
Comprehensive API and Developer Platform System
This module provides a complete API ecosystem with developer tools,
SDK generation, documentation, and analytics.
"""

import os
import json
import uuid
import hashlib
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import yaml
import sqlite3
from pathlib import Path
import jwt
import httpx
from fastapi import FastAPI, HTTPException, Depends, Security, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import redis
from collections import defaultdict
import time
import re
from jinja2 import Template
import zipfile
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enums
class APIKeyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    REVOKED = "revoked"
    EXPIRED = "expired"

class APIKeyScope(str, Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    ADMIN = "admin"

class WebhookEventType(str, Enum):
    TRANSCRIPTION_COMPLETED = "transcription.completed"
    TRANSCRIPTION_FAILED = "transcription.failed"
    ANALYSIS_COMPLETED = "analysis.completed"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    RATE_LIMIT_EXCEEDED = "rate_limit.exceeded"
    USAGE_LIMIT_REACHED = "usage_limit.reached"

class SDKLanguage(str, Enum):
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUBY = "ruby"
    PHP = "php"
    CSHARP = "csharp"

class APIVersion(str, Enum):
    V1 = "v1"
    V2 = "v2"
    V3 = "v3"

# Data Models
@dataclass
class APIKey:
    key: str
    key_hash: str
    name: str
    user_id: str
    status: APIKeyStatus
    scopes: List[APIKeyScope]
    rate_limit: int  # requests per minute
    usage_limit: Optional[int]  # total requests allowed
    usage_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Webhook:
    id: str
    url: str
    events: List[WebhookEventType]
    api_key_id: str
    secret: str
    active: bool = True
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_triggered_at: Optional[datetime] = None
    failure_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIUsageMetrics:
    api_key_id: str
    endpoint: str
    method: str
    status_code: int
    response_time_ms: float
    timestamp: datetime
    ip_address: str
    user_agent: str
    request_size: int
    response_size: int
    error_message: Optional[str] = None

@dataclass
class DeveloperApp:
    id: str
    name: str
    description: str
    user_id: str
    api_keys: List[str] = field(default_factory=list)
    webhooks: List[str] = field(default_factory=list)
    redirect_uris: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class APIEndpoint:
    path: str
    method: str
    description: str
    parameters: List[Dict[str, Any]]
    request_body: Optional[Dict[str, Any]]
    responses: Dict[str, Dict[str, Any]]
    scopes_required: List[APIKeyScope]
    rate_limit_override: Optional[int] = None
    deprecated: bool = False
    version: APIVersion = APIVersion.V1

# OpenAPI Specification Generator
class OpenAPIGenerator:
    def __init__(self):
        self.spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "Audio/Video Transcription API",
                "description": "Comprehensive API for audio/video transcription and analysis",
                "version": "3.0.0",
                "contact": {
                    "name": "API Support",
                    "email": "api@transcription-platform.com",
                    "url": "https://docs.transcription-platform.com"
                }
            },
            "servers": [
                {
                    "url": "https://api.transcription-platform.com/v3",
                    "description": "Production server"
                },
                {
                    "url": "https://sandbox.transcription-platform.com/v3",
                    "description": "Sandbox server"
                }
            ],
            "paths": {},
            "components": {
                "securitySchemes": {
                    "ApiKeyAuth": {
                        "type": "apiKey",
                        "in": "header",
                        "name": "X-API-Key"
                    },
                    "BearerAuth": {
                        "type": "http",
                        "scheme": "bearer",
                        "bearerFormat": "JWT"
                    }
                },
                "schemas": {}
            },
            "security": [
                {"ApiKeyAuth": []},
                {"BearerAuth": []}
            ]
        }
        
    def add_endpoint(self, endpoint: APIEndpoint):
        """Add an endpoint to the OpenAPI specification"""
        path_item = self.spec["paths"].get(endpoint.path, {})
        
        operation = {
            "summary": endpoint.description,
            "description": endpoint.description,
            "operationId": f"{endpoint.method.lower()}_{endpoint.path.replace('/', '_').strip('_')}",
            "tags": [endpoint.version],
            "parameters": endpoint.parameters,
            "responses": endpoint.responses
        }
        
        if endpoint.request_body:
            operation["requestBody"] = endpoint.request_body
            
        if endpoint.deprecated:
            operation["deprecated"] = True
            
        if endpoint.scopes_required:
            operation["security"] = [{
                "ApiKeyAuth": [scope.value for scope in endpoint.scopes_required]
            }]
            
        path_item[endpoint.method.lower()] = operation
        self.spec["paths"][endpoint.path] = path_item
        
    def add_schema(self, name: str, schema: Dict[str, Any]):
        """Add a schema to the OpenAPI specification"""
        self.spec["components"]["schemas"][name] = schema
        
    def generate_yaml(self) -> str:
        """Generate YAML representation of the OpenAPI spec"""
        return yaml.dump(self.spec, sort_keys=False)
        
    def generate_json(self) -> str:
        """Generate JSON representation of the OpenAPI spec"""
        return json.dumps(self.spec, indent=2)

# SDK Generator
class SDKGenerator:
    def __init__(self, openapi_spec: Dict[str, Any]):
        self.spec = openapi_spec
        self.templates = {
            SDKLanguage.PYTHON: self._python_template(),
            SDKLanguage.JAVASCRIPT: self._javascript_template(),
            SDKLanguage.TYPESCRIPT: self._typescript_template(),
            SDKLanguage.GO: self._go_template(),
            SDKLanguage.JAVA: self._java_template(),
        }
        
    def generate_sdk(self, language: SDKLanguage, output_dir: str) -> str:
        """Generate SDK for the specified language"""
        os.makedirs(output_dir, exist_ok=True)
        
        if language == SDKLanguage.PYTHON:
            return self._generate_python_sdk(output_dir)
        elif language == SDKLanguage.JAVASCRIPT:
            return self._generate_javascript_sdk(output_dir)
        elif language == SDKLanguage.TYPESCRIPT:
            return self._generate_typescript_sdk(output_dir)
        elif language == SDKLanguage.GO:
            return self._generate_go_sdk(output_dir)
        elif language == SDKLanguage.JAVA:
            return self._generate_java_sdk(output_dir)
        else:
            raise ValueError(f"Unsupported language: {language}")
            
    def _python_template(self) -> str:
        return '''"""
Audio/Video Transcription API Python SDK
Generated from OpenAPI specification
"""

import requests
from typing import Dict, List, Optional, Any
import json
from datetime import datetime

class TranscriptionAPIClient:
    def __init__(self, api_key: str, base_url: str = "https://api.transcription-platform.com/v3"):
        self.api_key = api_key
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        })
        
    def transcribe_audio(self, file_path: str, language: str = "en", **kwargs) -> Dict[str, Any]:
        """Transcribe an audio file"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {'language': language, **kwargs}
            response = self.session.post(f"{self.base_url}/transcriptions", files=files, data=data)
            response.raise_for_status()
            return response.json()
            
    def get_transcription(self, transcription_id: str) -> Dict[str, Any]:
        """Get transcription details"""
        response = self.session.get(f"{self.base_url}/transcriptions/{transcription_id}")
        response.raise_for_status()
        return response.json()
        
    def analyze_entities(self, transcription_id: str, model: str = "advanced") -> Dict[str, Any]:
        """Analyze entities in a transcription"""
        data = {"model": model}
        response = self.session.post(f"{self.base_url}/transcriptions/{transcription_id}/analyze", json=data)
        response.raise_for_status()
        return response.json()
        
    def create_webhook(self, url: str, events: List[str]) -> Dict[str, Any]:
        """Create a webhook"""
        data = {"url": url, "events": events}
        response = self.session.post(f"{self.base_url}/webhooks", json=data)
        response.raise_for_status()
        return response.json()
'''
        
    def _javascript_template(self) -> str:
        return '''/**
 * Audio/Video Transcription API JavaScript SDK
 * Generated from OpenAPI specification
 */

class TranscriptionAPIClient {
    constructor(apiKey, baseUrl = 'https://api.transcription-platform.com/v3') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }
    
    async transcribeAudio(filePath, language = 'en', options = {}) {
        const formData = new FormData();
        formData.append('file', filePath);
        formData.append('language', language);
        Object.keys(options).forEach(key => formData.append(key, options[key]));
        
        const response = await fetch(`${this.baseUrl}/transcriptions`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    }
    
    async getTranscription(transcriptionId) {
        const response = await fetch(`${this.baseUrl}/transcriptions/${transcriptionId}`, {
            headers: {
                'X-API-Key': this.apiKey
            }
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    }
}

module.exports = TranscriptionAPIClient;
'''
        
    def _typescript_template(self) -> str:
        return '''/**
 * Audio/Video Transcription API TypeScript SDK
 * Generated from OpenAPI specification
 */

export interface TranscriptionOptions {
    language?: string;
    model?: string;
    speakerDiarization?: boolean;
}

export interface Transcription {
    id: string;
    text: string;
    language: string;
    duration: number;
    createdAt: string;
}

export class TranscriptionAPIClient {
    private apiKey: string;
    private baseUrl: string;
    
    constructor(apiKey: string, baseUrl: string = 'https://api.transcription-platform.com/v3') {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
    }
    
    async transcribeAudio(file: File, options: TranscriptionOptions = {}): Promise<Transcription> {
        const formData = new FormData();
        formData.append('file', file);
        Object.entries(options).forEach(([key, value]) => {
            formData.append(key, String(value));
        });
        
        const response = await fetch(`${this.baseUrl}/transcriptions`, {
            method: 'POST',
            headers: {
                'X-API-Key': this.apiKey
            },
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.statusText}`);
        }
        
        return await response.json();
    }
}
'''
        
    def _go_template(self) -> str:
        return '''// Audio/Video Transcription API Go SDK
// Generated from OpenAPI specification

package transcriptionapi

import (
    "bytes"
    "encoding/json"
    "fmt"
    "io"
    "mime/multipart"
    "net/http"
    "os"
)

type Client struct {
    APIKey  string
    BaseURL string
    client  *http.Client
}

func NewClient(apiKey string) *Client {
    return &Client{
        APIKey:  apiKey,
        BaseURL: "https://api.transcription-platform.com/v3",
        client:  &http.Client{},
    }
}

func (c *Client) TranscribeAudio(filePath string, language string) (map[string]interface{}, error) {
    file, err := os.Open(filePath)
    if err != nil {
        return nil, err
    }
    defer file.Close()
    
    body := &bytes.Buffer{}
    writer := multipart.NewWriter(body)
    
    part, err := writer.CreateFormFile("file", filePath)
    if err != nil {
        return nil, err
    }
    io.Copy(part, file)
    
    writer.WriteField("language", language)
    writer.Close()
    
    req, err := http.NewRequest("POST", c.BaseURL+"/transcriptions", body)
    if err != nil {
        return nil, err
    }
    
    req.Header.Set("X-API-Key", c.APIKey)
    req.Header.Set("Content-Type", writer.FormDataContentType())
    
    resp, err := c.client.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()
    
    var result map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&result)
    return result, nil
}
'''
        
    def _java_template(self) -> str:
        return '''/**
 * Audio/Video Transcription API Java SDK
 * Generated from OpenAPI specification
 */

package com.transcriptionapi.sdk;

import java.io.*;
import java.net.http.*;
import java.nio.file.*;
import java.util.*;
import com.google.gson.Gson;

public class TranscriptionAPIClient {
    private final String apiKey;
    private final String baseUrl;
    private final HttpClient httpClient;
    private final Gson gson;
    
    public TranscriptionAPIClient(String apiKey) {
        this(apiKey, "https://api.transcription-platform.com/v3");
    }
    
    public TranscriptionAPIClient(String apiKey, String baseUrl) {
        this.apiKey = apiKey;
        this.baseUrl = baseUrl;
        this.httpClient = HttpClient.newHttpClient();
        this.gson = new Gson();
    }
    
    public Map<String, Object> transcribeAudio(String filePath, String language) throws IOException, InterruptedException {
        Path path = Paths.get(filePath);
        byte[] fileBytes = Files.readAllBytes(path);
        
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(baseUrl + "/transcriptions"))
            .header("X-API-Key", apiKey)
            .header("Content-Type", "multipart/form-data")
            .POST(HttpRequest.BodyPublishers.ofByteArray(fileBytes))
            .build();
            
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        
        if (response.statusCode() != 200) {
            throw new RuntimeException("API Error: " + response.statusCode());
        }
        
        return gson.fromJson(response.body(), Map.class);
    }
}
'''
        
    def _generate_python_sdk(self, output_dir: str) -> str:
        """Generate Python SDK"""
        # Main SDK file
        sdk_path = os.path.join(output_dir, "transcription_api.py")
        with open(sdk_path, 'w') as f:
            f.write(self.templates[SDKLanguage.PYTHON])
            
        # Setup file
        setup_content = '''from setuptools import setup, find_packages

setup(
    name="transcription-api-sdk",
    version="1.0.0",
    description="Audio/Video Transcription API Python SDK",
    author="API Team",
    author_email="api@transcription-platform.com",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
    ],
    python_requires=">=3.7",
)
'''
        setup_path = os.path.join(output_dir, "setup.py")
        with open(setup_path, 'w') as f:
            f.write(setup_content)
            
        # README
        readme_content = '''# Audio/Video Transcription API Python SDK

## Installation

```bash
pip install transcription-api-sdk
```

## Usage

```python
from transcription_api import TranscriptionAPIClient

client = TranscriptionAPIClient("your-api-key")

# Transcribe audio
result = client.transcribe_audio("audio.mp3", language="en")
print(result["transcription_id"])

# Get transcription
transcription = client.get_transcription(result["transcription_id"])
print(transcription["text"])
```

## Documentation

Full documentation available at: https://docs.transcription-platform.com
'''
        readme_path = os.path.join(output_dir, "README.md")
        with open(readme_path, 'w') as f:
            f.write(readme_content)
            
        return output_dir
        
    def _generate_javascript_sdk(self, output_dir: str) -> str:
        """Generate JavaScript SDK"""
        # Main SDK file
        sdk_path = os.path.join(output_dir, "index.js")
        with open(sdk_path, 'w') as f:
            f.write(self.templates[SDKLanguage.JAVASCRIPT])
            
        # Package.json
        package_content = '''{
  "name": "transcription-api-sdk",
  "version": "1.0.0",
  "description": "Audio/Video Transcription API JavaScript SDK",
  "main": "index.js",
  "scripts": {
    "test": "jest"
  },
  "keywords": ["transcription", "api", "sdk"],
  "author": "API Team",
  "license": "MIT",
  "dependencies": {
    "node-fetch": "^3.0.0"
  },
  "devDependencies": {
    "jest": "^27.0.0"
  }
}
'''
        package_path = os.path.join(output_dir, "package.json")
        with open(package_path, 'w') as f:
            f.write(package_content)
            
        return output_dir
        
    def _generate_typescript_sdk(self, output_dir: str) -> str:
        """Generate TypeScript SDK"""
        # Main SDK file
        sdk_path = os.path.join(output_dir, "index.ts")
        with open(sdk_path, 'w') as f:
            f.write(self.templates[SDKLanguage.TYPESCRIPT])
            
        # Package.json
        package_content = '''{
  "name": "transcription-api-sdk",
  "version": "1.0.0",
  "description": "Audio/Video Transcription API TypeScript SDK",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "test": "jest"
  },
  "keywords": ["transcription", "api", "sdk", "typescript"],
  "author": "API Team",
  "license": "MIT",
  "devDependencies": {
    "@types/node": "^16.0.0",
    "typescript": "^4.5.0",
    "jest": "^27.0.0"
  }
}
'''
        package_path = os.path.join(output_dir, "package.json")
        with open(package_path, 'w') as f:
            f.write(package_content)
            
        # tsconfig.json
        tsconfig_content = '''{
  "compilerOptions": {
    "target": "ES2020",
    "module": "commonjs",
    "lib": ["ES2020"],
    "outDir": "./dist",
    "rootDir": "./",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true
  }
}
'''
        tsconfig_path = os.path.join(output_dir, "tsconfig.json")
        with open(tsconfig_path, 'w') as f:
            f.write(tsconfig_content)
            
        return output_dir
        
    def _generate_go_sdk(self, output_dir: str) -> str:
        """Generate Go SDK"""
        # Main SDK file
        sdk_path = os.path.join(output_dir, "client.go")
        with open(sdk_path, 'w') as f:
            f.write(self.templates[SDKLanguage.GO])
            
        # go.mod
        gomod_content = '''module github.com/transcription-api/go-sdk

go 1.19

require (
    github.com/go-resty/resty/v2 v2.7.0
)
'''
        gomod_path = os.path.join(output_dir, "go.mod")
        with open(gomod_path, 'w') as f:
            f.write(gomod_content)
            
        return output_dir
        
    def _generate_java_sdk(self, output_dir: str) -> str:
        """Generate Java SDK"""
        # Create directory structure
        java_dir = os.path.join(output_dir, "src/main/java/com/transcriptionapi/sdk")
        os.makedirs(java_dir, exist_ok=True)
        
        # Main SDK file
        sdk_path = os.path.join(java_dir, "TranscriptionAPIClient.java")
        with open(sdk_path, 'w') as f:
            f.write(self.templates[SDKLanguage.JAVA])
            
        # pom.xml
        pom_content = '''<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0
         http://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <groupId>com.transcriptionapi</groupId>
    <artifactId>transcription-api-sdk</artifactId>
    <version>1.0.0</version>
    
    <properties>
        <maven.compiler.source>11</maven.compiler.source>
        <maven.compiler.target>11</maven.compiler.target>
    </properties>
    
    <dependencies>
        <dependency>
            <groupId>com.google.code.gson</groupId>
            <artifactId>gson</artifactId>
            <version>2.9.0</version>
        </dependency>
    </dependencies>
</project>
'''
        pom_path = os.path.join(output_dir, "pom.xml")
        with open(pom_path, 'w') as f:
            f.write(pom_content)
            
        return output_dir

# API Platform Manager
class APIPlatformManager:
    def __init__(self, db_path: str = "api_platform.db", redis_url: str = "redis://localhost:6379"):
        self.db_path = db_path
        self.redis_url = redis_url
        self.redis_client = None
        self.openapi_generator = OpenAPIGenerator()
        self._init_database()
        self._init_redis()
        self._init_endpoints()
        
    def _init_database(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # API Keys table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_keys (
                key_hash TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                user_id TEXT NOT NULL,
                status TEXT NOT NULL,
                scopes TEXT NOT NULL,
                rate_limit INTEGER NOT NULL,
                usage_limit INTEGER,
                usage_count INTEGER DEFAULT 0,
                created_at TEXT NOT NULL,
                expires_at TEXT,
                last_used_at TEXT,
                metadata TEXT
            )
        ''')
        
        # Webhooks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                events TEXT NOT NULL,
                api_key_id TEXT NOT NULL,
                secret TEXT NOT NULL,
                active INTEGER DEFAULT 1,
                created_at TEXT NOT NULL,
                last_triggered_at TEXT,
                failure_count INTEGER DEFAULT 0,
                metadata TEXT,
                FOREIGN KEY (api_key_id) REFERENCES api_keys (key_hash)
            )
        ''')
        
        # Usage metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_usage_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                api_key_id TEXT NOT NULL,
                endpoint TEXT NOT NULL,
                method TEXT NOT NULL,
                status_code INTEGER NOT NULL,
                response_time_ms REAL NOT NULL,
                timestamp TEXT NOT NULL,
                ip_address TEXT NOT NULL,
                user_agent TEXT NOT NULL,
                request_size INTEGER NOT NULL,
                response_size INTEGER NOT NULL,
                error_message TEXT,
                FOREIGN KEY (api_key_id) REFERENCES api_keys (key_hash)
            )
        ''')
        
        # Developer apps table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS developer_apps (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                user_id TEXT NOT NULL,
                api_keys TEXT,
                webhooks TEXT,
                redirect_uris TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                metadata TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def _init_redis(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            self.redis_client.ping()
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Rate limiting will be disabled.")
            self.redis_client = None
            
    def _init_endpoints(self):
        """Initialize API endpoints for OpenAPI spec"""
        endpoints = [
            APIEndpoint(
                path="/transcriptions",
                method="POST",
                description="Create a new transcription",
                parameters=[],
                request_body={
                    "content": {
                        "multipart/form-data": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "file": {"type": "string", "format": "binary"},
                                    "language": {"type": "string", "default": "en"},
                                    "model": {"type": "string", "enum": ["base", "large", "turbo"]}
                                }
                            }
                        }
                    }
                },
                responses={
                    "200": {
                        "description": "Transcription created successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Transcription"}
                            }
                        }
                    }
                },
                scopes_required=[APIKeyScope.WRITE]
            ),
            APIEndpoint(
                path="/transcriptions/{id}",
                method="GET",
                description="Get transcription details",
                parameters=[{
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }],
                request_body=None,
                responses={
                    "200": {
                        "description": "Transcription details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Transcription"}
                            }
                        }
                    }
                },
                scopes_required=[APIKeyScope.READ]
            ),
            APIEndpoint(
                path="/transcriptions/{id}/analyze",
                method="POST",
                description="Analyze entities in a transcription",
                parameters=[{
                    "name": "id",
                    "in": "path",
                    "required": True,
                    "schema": {"type": "string"}
                }],
                request_body={
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "model": {"type": "string", "enum": ["basic", "advanced"]}
                                }
                            }
                        }
                    }
                },
                responses={
                    "200": {
                        "description": "Analysis results",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/AnalysisResult"}
                            }
                        }
                    }
                },
                scopes_required=[APIKeyScope.WRITE]
            )
        ]
        
        # Add endpoints to OpenAPI spec
        for endpoint in endpoints:
            self.openapi_generator.add_endpoint(endpoint)
            
        # Add schemas
        self.openapi_generator.add_schema("Transcription", {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "text": {"type": "string"},
                "language": {"type": "string"},
                "duration": {"type": "number"},
                "created_at": {"type": "string", "format": "date-time"}
            }
        })
        
        self.openapi_generator.add_schema("AnalysisResult", {
            "type": "object",
            "properties": {
                "entities": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "type": {"type": "string"},
                            "confidence": {"type": "number"}
                        }
                    }
                },
                "summary": {"type": "string"}
            }
        })
        
    def create_api_key(self, name: str, user_id: str, scopes: List[APIKeyScope],
                      rate_limit: int = 60, usage_limit: Optional[int] = None,
                      expires_in_days: Optional[int] = None) -> Tuple[str, APIKey]:
        """Create a new API key"""
        # Generate key
        key_prefix = "sk_"
        if expires_in_days:
            key_prefix = "sk_temp_"
        key = key_prefix + secrets.token_urlsafe(32)
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
            
        # Create API key object
        api_key = APIKey(
            key=key,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            status=APIKeyStatus.ACTIVE,
            scopes=scopes,
            rate_limit=rate_limit,
            usage_limit=usage_limit,
            expires_at=expires_at
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO api_keys (key_hash, name, user_id, status, scopes, rate_limit,
                                usage_limit, created_at, expires_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            api_key.key_hash,
            api_key.name,
            api_key.user_id,
            api_key.status.value,
            json.dumps([scope.value for scope in api_key.scopes]),
            api_key.rate_limit,
            api_key.usage_limit,
            api_key.created_at.isoformat(),
            api_key.expires_at.isoformat() if api_key.expires_at else None,
            json.dumps(api_key.metadata)
        ))
        conn.commit()
        conn.close()
        
        return key, api_key
        
    def validate_api_key(self, key: str) -> Optional[APIKey]:
        """Validate an API key"""
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM api_keys WHERE key_hash = ?
        ''', (key_hash,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        # Parse API key from row
        api_key = APIKey(
            key=key,
            key_hash=row[0],
            name=row[1],
            user_id=row[2],
            status=APIKeyStatus(row[3]),
            scopes=[APIKeyScope(scope) for scope in json.loads(row[4])],
            rate_limit=row[5],
            usage_limit=row[6],
            usage_count=row[7],
            created_at=datetime.fromisoformat(row[8]),
            expires_at=datetime.fromisoformat(row[9]) if row[9] else None,
            last_used_at=datetime.fromisoformat(row[10]) if row[10] else None,
            metadata=json.loads(row[11]) if row[11] else {}
        )
        
        # Check if key is valid
        if api_key.status != APIKeyStatus.ACTIVE:
            return None
            
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            # Update status to expired
            self._update_api_key_status(key_hash, APIKeyStatus.EXPIRED)
            return None
            
        if api_key.usage_limit and api_key.usage_count >= api_key.usage_limit:
            return None
            
        return api_key
        
    def check_rate_limit(self, api_key: APIKey) -> bool:
        """Check if API key has exceeded rate limit"""
        if not self.redis_client:
            return True  # No rate limiting if Redis is not available
            
        key = f"rate_limit:{api_key.key_hash}"
        current = self.redis_client.incr(key)
        
        if current == 1:
            self.redis_client.expire(key, 60)  # 1 minute window
            
        return current <= api_key.rate_limit
        
    def record_usage(self, api_key: APIKey, endpoint: str, method: str,
                    status_code: int, response_time_ms: float, request: Request,
                    request_size: int, response_size: int, error_message: Optional[str] = None):
        """Record API usage metrics"""
        metrics = APIUsageMetrics(
            api_key_id=api_key.key_hash,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            timestamp=datetime.utcnow(),
            ip_address=request.client.host,
            user_agent=request.headers.get("User-Agent", ""),
            request_size=request_size,
            response_size=response_size,
            error_message=error_message
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO api_usage_metrics (api_key_id, endpoint, method, status_code,
                                         response_time_ms, timestamp, ip_address, user_agent,
                                         request_size, response_size, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            metrics.api_key_id,
            metrics.endpoint,
            metrics.method,
            metrics.status_code,
            metrics.response_time_ms,
            metrics.timestamp.isoformat(),
            metrics.ip_address,
            metrics.user_agent,
            metrics.request_size,
            metrics.response_size,
            metrics.error_message
        ))
        
        # Update usage count and last used
        cursor.execute('''
            UPDATE api_keys
            SET usage_count = usage_count + 1,
                last_used_at = ?
            WHERE key_hash = ?
        ''', (datetime.utcnow().isoformat(), api_key.key_hash))
        
        conn.commit()
        conn.close()
        
    def create_webhook(self, api_key_id: str, url: str, events: List[WebhookEventType]) -> Webhook:
        """Create a new webhook"""
        webhook = Webhook(
            id=str(uuid.uuid4()),
            url=url,
            events=events,
            api_key_id=api_key_id,
            secret=secrets.token_urlsafe(32)
        )
        
        # Save to database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO webhooks (id, url, events, api_key_id, secret, active,
                                created_at, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            webhook.id,
            webhook.url,
            json.dumps([event.value for event in webhook.events]),
            webhook.api_key_id,
            webhook.secret,
            1 if webhook.active else 0,
            webhook.created_at.isoformat(),
            json.dumps(webhook.metadata)
        ))
        conn.commit()
        conn.close()
        
        return webhook
        
    async def trigger_webhook(self, event_type: WebhookEventType, api_key_id: str, data: Dict[str, Any]):
        """Trigger webhooks for an event"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM webhooks
            WHERE api_key_id = ? AND active = 1
        ''', (api_key_id,))
        rows = cursor.fetchall()
        conn.close()
        
        for row in rows:
            events = json.loads(row[2])
            if event_type.value not in events:
                continue
                
            webhook_id = row[0]
            url = row[1]
            secret = row[4]
            
            # Prepare webhook payload
            payload = {
                "event": event_type.value,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Generate signature
            signature = self._generate_webhook_signature(secret, payload)
            
            # Send webhook
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={
                            "X-Webhook-Signature": signature,
                            "X-Webhook-Event": event_type.value
                        },
                        timeout=10.0
                    )
                    
                    if response.status_code >= 400:
                        self._handle_webhook_failure(webhook_id)
                    else:
                        self._update_webhook_triggered(webhook_id)
                        
            except Exception as e:
                logger.error(f"Webhook delivery failed: {e}")
                self._handle_webhook_failure(webhook_id)
                
    def _generate_webhook_signature(self, secret: str, payload: Dict[str, Any]) -> str:
        """Generate webhook signature"""
        payload_str = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(f"{secret}{payload_str}".encode()).hexdigest()
        
    def _update_api_key_status(self, key_hash: str, status: APIKeyStatus):
        """Update API key status"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE api_keys SET status = ? WHERE key_hash = ?
        ''', (status.value, key_hash))
        conn.commit()
        conn.close()
        
    def _update_webhook_triggered(self, webhook_id: str):
        """Update webhook last triggered time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE webhooks
            SET last_triggered_at = ?, failure_count = 0
            WHERE id = ?
        ''', (datetime.utcnow().isoformat(), webhook_id))
        conn.commit()
        conn.close()
        
    def _handle_webhook_failure(self, webhook_id: str):
        """Handle webhook delivery failure"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE webhooks
            SET failure_count = failure_count + 1
            WHERE id = ?
        ''', (webhook_id,))
        
        # Disable webhook after 5 failures
        cursor.execute('''
            UPDATE webhooks
            SET active = 0
            WHERE id = ? AND failure_count >= 5
        ''', (webhook_id,))
        
        conn.commit()
        conn.close()
        
    def get_api_usage_stats(self, api_key_id: str, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get API usage statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total requests
        cursor.execute('''
            SELECT COUNT(*) FROM api_usage_metrics
            WHERE api_key_id = ? AND timestamp BETWEEN ? AND ?
        ''', (api_key_id, start_date.isoformat(), end_date.isoformat()))
        total_requests = cursor.fetchone()[0]
        
        # Requests by endpoint
        cursor.execute('''
            SELECT endpoint, method, COUNT(*) as count
            FROM api_usage_metrics
            WHERE api_key_id = ? AND timestamp BETWEEN ? AND ?
            GROUP BY endpoint, method
            ORDER BY count DESC
        ''', (api_key_id, start_date.isoformat(), end_date.isoformat()))
        requests_by_endpoint = [
            {"endpoint": row[0], "method": row[1], "count": row[2]}
            for row in cursor.fetchall()
        ]
        
        # Average response time
        cursor.execute('''
            SELECT AVG(response_time_ms) FROM api_usage_metrics
            WHERE api_key_id = ? AND timestamp BETWEEN ? AND ?
        ''', (api_key_id, start_date.isoformat(), end_date.isoformat()))
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Error rate
        cursor.execute('''
            SELECT COUNT(*) FROM api_usage_metrics
            WHERE api_key_id = ? AND timestamp BETWEEN ? AND ? AND status_code >= 400
        ''', (api_key_id, start_date.isoformat(), end_date.isoformat()))
        error_count = cursor.fetchone()[0]
        error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
        
        conn.close()
        
        return {
            "total_requests": total_requests,
            "requests_by_endpoint": requests_by_endpoint,
            "average_response_time_ms": avg_response_time,
            "error_rate": error_rate,
            "error_count": error_count
        }
        
    def generate_sdk(self, language: SDKLanguage) -> str:
        """Generate SDK for specified language"""
        output_dir = f"sdks/{language.value}"
        os.makedirs(output_dir, exist_ok=True)
        
        sdk_generator = SDKGenerator(self.openapi_generator.spec)
        sdk_path = sdk_generator.generate_sdk(language, output_dir)
        
        # Create zip file
        zip_path = f"{output_dir}.zip"
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(sdk_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, os.path.dirname(sdk_path))
                    zipf.write(file_path, arcname)
                    
        return zip_path
        
    def get_openapi_spec(self, format: str = "yaml") -> str:
        """Get OpenAPI specification"""
        if format == "yaml":
            return self.openapi_generator.generate_yaml()
        else:
            return self.openapi_generator.generate_json()


# FastAPI middleware for API key authentication
class APIKeyAuth:
    def __init__(self, platform_manager: APIPlatformManager):
        self.platform_manager = platform_manager
        self.security = HTTPBearer()
        
    async def __call__(self, request: Request, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())):
        # Check for API key in header
        api_key = request.headers.get("X-API-Key")
        if not api_key:
            # Check for Bearer token
            if credentials:
                api_key = credentials.credentials
                
        if not api_key:
            raise HTTPException(status_code=401, detail="API key required")
            
        # Validate API key
        api_key_obj = self.platform_manager.validate_api_key(api_key)
        if not api_key_obj:
            raise HTTPException(status_code=401, detail="Invalid API key")
            
        # Check rate limit
        if not self.platform_manager.check_rate_limit(api_key_obj):
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
            
        return api_key_obj


# Example usage
if __name__ == "__main__":
    # Initialize platform manager
    platform_manager = APIPlatformManager()
    
    # Create API key
    key, api_key = platform_manager.create_api_key(
        name="Test Application",
        user_id="user_123",
        scopes=[APIKeyScope.READ, APIKeyScope.WRITE],
        rate_limit=100,
        usage_limit=10000,
        expires_in_days=30
    )
    
    print(f"API Key created: {key}")
    print(f"Key ID: {api_key.key_hash}")
    
    # Create webhook
    webhook = platform_manager.create_webhook(
        api_key_id=api_key.key_hash,
        url="https://example.com/webhook",
        events=[WebhookEventType.TRANSCRIPTION_COMPLETED]
    )
    
    print(f"Webhook created: {webhook.id}")
    print(f"Webhook secret: {webhook.secret}")
    
    # Generate SDKs
    for language in [SDKLanguage.PYTHON, SDKLanguage.JAVASCRIPT, SDKLanguage.TYPESCRIPT]:
        sdk_path = platform_manager.generate_sdk(language)
        print(f"{language.value} SDK generated: {sdk_path}")
        
    # Get OpenAPI spec
    openapi_yaml = platform_manager.get_openapi_spec("yaml")
    with open("openapi.yaml", "w") as f:
        f.write(openapi_yaml)
    print("OpenAPI specification saved to openapi.yaml")