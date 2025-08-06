"""
Comprehensive Third-Party Ecosystem Integration
Implements plugin architecture, webhook marketplace, automation integrations,
browser extensions, and native CRM integrations with extensive external API support
"""

import os
import json
import logging
import asyncio
import hashlib
import hmac
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from pathlib import Path
import importlib.util
import inspect
import requests
import aiohttp
from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
import jwt
from cryptography.fernet import Fernet

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationType(Enum):
    PLUGIN = "plugin"
    WEBHOOK = "webhook"
    ZAPIER = "zapier"
    IFTTT = "ifttt"
    CRM = "crm"
    BROWSER_EXTENSION = "browser_extension"
    API = "api"
    LLM_MODEL = "llm_model"
    HUGGINGFACE = "huggingface"
    GITHUB = "github"

class IntegrationStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    ERROR = "error"
    DEPRECATED = "deprecated"

@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str
    author: str
    category: str
    permissions: List[str]
    dependencies: List[str]
    entry_point: str
    config_schema: Dict[str, Any]
    supported_formats: List[str]
    min_api_version: str

@dataclass
class WebhookConfig:
    url: str
    events: List[str]
    secret: Optional[str]
    headers: Dict[str, str]
    retry_count: int = 3
    timeout: int = 30
    active: bool = True

@dataclass
class ExternalAPIConfig:
    name: str
    base_url: str
    api_key: Optional[str]
    auth_type: str  # "bearer", "api_key", "oauth2", "basic"
    rate_limit: int
    endpoints: Dict[str, str]
    models: List[str] = None
    capabilities: List[str] = None

class ThirdPartyEcosystem:
    def __init__(self, db_path: str = "third_party_ecosystem.db"):
        self.db_path = db_path
        self.plugins = {}
        self.webhooks = {}
        self.integrations = {}
        self.external_apis = {}
        self.app = FastAPI(title="Third-Party Ecosystem API")
        self.init_database()
        self.load_external_apis()
        self.setup_routes()
        
    def init_database(self):
        """Initialize the ecosystem database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Plugins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugins (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                version TEXT NOT NULL,
                description TEXT,
                author TEXT,
                category TEXT,
                status TEXT DEFAULT 'inactive',
                metadata TEXT,
                config TEXT,
                installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                usage_count INTEGER DEFAULT 0
            )
        ''')
        
        # Webhooks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                events TEXT,
                secret TEXT,
                headers TEXT,
                status TEXT DEFAULT 'active',
                retry_count INTEGER DEFAULT 3,
                timeout INTEGER DEFAULT 30,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_triggered TIMESTAMP,
                success_count INTEGER DEFAULT 0,
                error_count INTEGER DEFAULT 0
            )
        ''')
        
        # Integrations table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS integrations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                config TEXT,
                status TEXT DEFAULT 'inactive',
                api_key TEXT,
                oauth_token TEXT,
                refresh_token TEXT,
                expires_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_sync TIMESTAMP,
                sync_count INTEGER DEFAULT 0
            )
        ''')
        
        # External APIs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS external_apis (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                api_key TEXT,
                auth_type TEXT DEFAULT 'bearer',
                rate_limit INTEGER DEFAULT 1000,
                endpoints TEXT,
                models TEXT,
                capabilities TEXT,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_used TIMESTAMP,
                request_count INTEGER DEFAULT 0
            )
        ''')
        
        # Plugin marketplace table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plugin_marketplace (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                category TEXT,
                author TEXT,
                version TEXT,
                download_url TEXT,
                github_url TEXT,
                documentation_url TEXT,
                rating REAL DEFAULT 0.0,
                downloads INTEGER DEFAULT 0,
                price REAL DEFAULT 0.0,
                tags TEXT,
                screenshots TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Third-party ecosystem database initialized")

    def load_external_apis(self):
        """Load comprehensive external API configurations"""
        external_apis = {
            # AI/ML APIs
            "openai": ExternalAPIConfig(
                name="OpenAI",
                base_url="https://api.openai.com/v1",
                api_key=os.getenv("OPENAI_API_KEY"),
                auth_type="bearer",
                rate_limit=3000,
                endpoints={
                    "completions": "/completions",
                    "chat": "/chat/completions",
                    "embeddings": "/embeddings",
                    "audio_transcription": "/audio/transcriptions",
                    "audio_translation": "/audio/translations",
                    "images": "/images/generations",
                    "fine_tuning": "/fine_tuning/jobs"
                },
                models=["gpt-4", "gpt-3.5-turbo", "whisper-1", "dall-e-3", "text-embedding-ada-002"],
                capabilities=["text_generation", "audio_transcription", "image_generation", "embeddings"]
            ),
            
            "anthropic": ExternalAPIConfig(
                name="Anthropic Claude",
                base_url="https://api.anthropic.com/v1",
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                auth_type="api_key",
                rate_limit=1000,
                endpoints={
                    "messages": "/messages",
                    "completions": "/complete"
                },
                models=["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"],
                capabilities=["text_generation", "analysis", "reasoning"]
            ),
            
            "huggingface": ExternalAPIConfig(
                name="Hugging Face",
                base_url="https://api-inference.huggingface.co",
                api_key=os.getenv("HUGGINGFACE_API_KEY"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "models": "/models",
                    "inference": "/models/{model_id}",
                    "datasets": "/datasets",
                    "spaces": "/spaces"
                },
                models=[
                    "microsoft/DialoGPT-large",
                    "facebook/bart-large-cnn",
                    "google/flan-t5-large",
                    "microsoft/speecht5_tts",
                    "openai/whisper-large-v2",
                    "sentence-transformers/all-MiniLM-L6-v2"
                ],
                capabilities=["text_generation", "summarization", "translation", "tts", "stt", "embeddings"]
            ),
            
            "cohere": ExternalAPIConfig(
                name="Cohere",
                base_url="https://api.cohere.ai/v1",
                api_key=os.getenv("COHERE_API_KEY"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "generate": "/generate",
                    "embed": "/embed",
                    "classify": "/classify",
                    "summarize": "/summarize",
                    "rerank": "/rerank"
                },
                models=["command", "command-light", "embed-english-v2.0"],
                capabilities=["text_generation", "embeddings", "classification", "summarization"]
            ),
            
            # Speech/Audio APIs
            "elevenlabs": ExternalAPIConfig(
                name="ElevenLabs",
                base_url="https://api.elevenlabs.io/v1",
                api_key=os.getenv("ELEVENLABS_API_KEY"),
                auth_type="api_key",
                rate_limit=500,
                endpoints={
                    "text_to_speech": "/text-to-speech/{voice_id}",
                    "voices": "/voices",
                    "voice_settings": "/voices/{voice_id}/settings",
                    "history": "/history"
                },
                capabilities=["text_to_speech", "voice_cloning", "voice_synthesis"]
            ),
            
            "assemblyai": ExternalAPIConfig(
                name="AssemblyAI",
                base_url="https://api.assemblyai.com/v2",
                api_key=os.getenv("ASSEMBLYAI_API_KEY"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "transcripts": "/transcript",
                    "upload": "/upload",
                    "lemur": "/lemur/v3/generate/summary"
                },
                capabilities=["speech_to_text", "speaker_diarization", "sentiment_analysis", "summarization"]
            ),
            
            # CRM APIs
            "salesforce": ExternalAPIConfig(
                name="Salesforce",
                base_url="https://your-domain.salesforce.com/services/data/v58.0",
                api_key=os.getenv("SALESFORCE_ACCESS_TOKEN"),
                auth_type="bearer",
                rate_limit=5000,
                endpoints={
                    "sobjects": "/sobjects",
                    "query": "/query",
                    "search": "/search",
                    "composite": "/composite"
                },
                capabilities=["crm", "lead_management", "opportunity_tracking", "contact_management"]
            ),
            
            "hubspot": ExternalAPIConfig(
                name="HubSpot",
                base_url="https://api.hubapi.com",
                api_key=os.getenv("HUBSPOT_API_KEY"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "contacts": "/crm/v3/objects/contacts",
                    "companies": "/crm/v3/objects/companies",
                    "deals": "/crm/v3/objects/deals",
                    "tickets": "/crm/v3/objects/tickets"
                },
                capabilities=["crm", "marketing_automation", "sales_pipeline", "customer_service"]
            ),
            
            # Communication APIs
            "slack": ExternalAPIConfig(
                name="Slack",
                base_url="https://slack.com/api",
                api_key=os.getenv("SLACK_BOT_TOKEN"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "chat_post": "/chat.postMessage",
                    "files_upload": "/files.upload",
                    "conversations_list": "/conversations.list",
                    "users_list": "/users.list"
                },
                capabilities=["messaging", "file_sharing", "notifications", "team_communication"]
            ),
            
            "discord": ExternalAPIConfig(
                name="Discord",
                base_url="https://discord.com/api/v10",
                api_key=os.getenv("DISCORD_BOT_TOKEN"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "channels": "/channels/{channel_id}",
                    "messages": "/channels/{channel_id}/messages",
                    "guilds": "/guilds/{guild_id}"
                },
                capabilities=["messaging", "voice_channels", "community_management"]
            ),
            
            # Cloud Storage APIs
            "google_drive": ExternalAPIConfig(
                name="Google Drive",
                base_url="https://www.googleapis.com/drive/v3",
                api_key=os.getenv("GOOGLE_DRIVE_API_KEY"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "files": "/files",
                    "upload": "/upload/drive/v3/files",
                    "permissions": "/files/{fileId}/permissions"
                },
                capabilities=["file_storage", "file_sharing", "collaboration"]
            ),
            
            "dropbox": ExternalAPIConfig(
                name="Dropbox",
                base_url="https://api.dropboxapi.com/2",
                api_key=os.getenv("DROPBOX_ACCESS_TOKEN"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "files_upload": "/files/upload",
                    "files_download": "/files/download",
                    "files_list": "/files/list_folder"
                },
                capabilities=["file_storage", "file_sync", "backup"]
            ),
            
            # Project Management APIs
            "jira": ExternalAPIConfig(
                name="Jira",
                base_url="https://your-domain.atlassian.net/rest/api/3",
                api_key=os.getenv("JIRA_API_TOKEN"),
                auth_type="basic",
                rate_limit=1000,
                endpoints={
                    "issues": "/issue",
                    "projects": "/project",
                    "search": "/search"
                },
                capabilities=["project_management", "issue_tracking", "workflow_automation"]
            ),
            
            "asana": ExternalAPIConfig(
                name="Asana",
                base_url="https://app.asana.com/api/1.0",
                api_key=os.getenv("ASANA_ACCESS_TOKEN"),
                auth_type="bearer",
                rate_limit=1500,
                endpoints={
                    "tasks": "/tasks",
                    "projects": "/projects",
                    "teams": "/teams"
                },
                capabilities=["task_management", "project_tracking", "team_collaboration"]
            ),
            
            "trello": ExternalAPIConfig(
                name="Trello",
                base_url="https://api.trello.com/1",
                api_key=os.getenv("TRELLO_API_KEY"),
                auth_type="api_key",
                rate_limit=300,
                endpoints={
                    "boards": "/boards",
                    "cards": "/cards",
                    "lists": "/lists"
                },
                capabilities=["kanban_boards", "task_organization", "project_visualization"]
            ),
            
            # Video/Media APIs
            "youtube": ExternalAPIConfig(
                name="YouTube Data API",
                base_url="https://www.googleapis.com/youtube/v3",
                api_key=os.getenv("YOUTUBE_API_KEY"),
                auth_type="api_key",
                rate_limit=10000,
                endpoints={
                    "videos": "/videos",
                    "search": "/search",
                    "captions": "/captions"
                },
                capabilities=["video_metadata", "video_search", "caption_extraction"]
            ),
            
            "zoom": ExternalAPIConfig(
                name="Zoom",
                base_url="https://api.zoom.us/v2",
                api_key=os.getenv("ZOOM_JWT_TOKEN"),
                auth_type="bearer",
                rate_limit=1000,
                endpoints={
                    "meetings": "/meetings",
                    "recordings": "/meetings/{meetingId}/recordings",
                    "users": "/users"
                },
                capabilities=["meeting_management", "recording_access", "user_management"]
            ),
            
            # Translation APIs
            "google_translate": ExternalAPIConfig(
                name="Google Translate",
                base_url="https://translation.googleapis.com/language/translate/v2",
                api_key=os.getenv("GOOGLE_TRANSLATE_API_KEY"),
                auth_type="api_key",
                rate_limit=1000,
                endpoints={
                    "translate": "",
                    "detect": "/detect",
                    "languages": "/languages"
                },
                capabilities=["text_translation", "language_detection", "multilingual_support"]
            ),
            
            "deepl": ExternalAPIConfig(
                name="DeepL",
                base_url="https://api-free.deepl.com/v2",
                api_key=os.getenv("DEEPL_API_KEY"),
                auth_type="bearer",
                rate_limit=500,
                endpoints={
                    "translate": "/translate",
                    "usage": "/usage",
                    "languages": "/languages"
                },
                capabilities=["high_quality_translation", "document_translation"]
            )
        }
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for api_id, config in external_apis.items():
            cursor.execute('''
                INSERT OR REPLACE INTO external_apis 
                (id, name, base_url, api_key, auth_type, rate_limit, endpoints, models, capabilities)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                api_id,
                config.name,
                config.base_url,
                config.api_key,
                config.auth_type,
                config.rate_limit,
                json.dumps(config.endpoints),
                json.dumps(config.models or []),
                json.dumps(config.capabilities or [])
            ))
        
        conn.commit()
        conn.close()
        
        self.external_apis = external_apis
        logger.info(f"Loaded {len(external_apis)} external API configurations")

    # Plugin Architecture
    def install_plugin(self, plugin_path: str, config: Dict[str, Any] = None) -> str:
        """Install a plugin from file or URL"""
        try:
            # Load plugin metadata
            if plugin_path.startswith('http'):
                # Download plugin
                response = requests.get(plugin_path)
                plugin_content = response.content
            else:
                # Load local plugin
                with open(plugin_path, 'rb') as f:
                    plugin_content = f.read()
            
            # Extract plugin metadata (assuming it's a Python module)
            plugin_id = hashlib.md5(plugin_content).hexdigest()[:16]
            
            # Store plugin
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO plugins 
                (id, name, version, description, author, category, status, metadata, config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plugin_id,
                config.get('name', 'Unknown Plugin'),
                config.get('version', '1.0.0'),
                config.get('description', ''),
                config.get('author', 'Unknown'),
                config.get('category', 'general'),
                'inactive',
                json.dumps(config or {}),
                json.dumps(config or {})
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Plugin {plugin_id} installed successfully")
            return plugin_id
            
        except Exception as e:
            logger.error(f"Failed to install plugin: {e}")
            raise

    def activate_plugin(self, plugin_id: str) -> bool:
        """Activate an installed plugin"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE plugins SET status = 'active' WHERE id = ?
            ''', (plugin_id,))
            
            conn.commit()
            conn.close()
            
            # Load plugin into memory
            self.plugins[plugin_id] = {'status': 'active'}
            
            logger.info(f"Plugin {plugin_id} activated")
            return True
            
        except Exception as e:
            logger.error(f"Failed to activate plugin {plugin_id}: {e}")
            return False

    def execute_plugin(self, plugin_id: str, method: str, *args, **kwargs) -> Any:
        """Execute a plugin method"""
        try:
            if plugin_id not in self.plugins:
                raise ValueError(f"Plugin {plugin_id} not found or not active")
            
            # Update usage statistics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE plugins 
                SET usage_count = usage_count + 1, last_used = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (plugin_id,))
            
            conn.commit()
            conn.close()
            
            # Execute plugin method (simplified implementation)
            result = f"Plugin {plugin_id} executed method {method} with args {args} and kwargs {kwargs}"
            
            logger.info(f"Plugin {plugin_id} method {method} executed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to execute plugin {plugin_id} method {method}: {e}")
            raise

    # Webhook System
    def register_webhook(self, name: str, url: str, events: List[str], 
                        secret: str = None, headers: Dict[str, str] = None) -> str:
        """Register a new webhook"""
        try:
            webhook_id = hashlib.md5(f"{name}{url}{time.time()}".encode()).hexdigest()[:16]
            
            webhook_config = WebhookConfig(
                url=url,
                events=events,
                secret=secret,
                headers=headers or {},
                retry_count=3,
                timeout=30,
                active=True
            )
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO webhooks 
                (id, name, url, events, secret, headers, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                webhook_id,
                name,
                url,
                json.dumps(events),
                secret,
                json.dumps(headers or {}),
                'active'
            ))
            
            conn.commit()
            conn.close()
            
            self.webhooks[webhook_id] = webhook_config
            
            logger.info(f"Webhook {webhook_id} registered for events: {events}")
            return webhook_id
            
        except Exception as e:
            logger.error(f"Failed to register webhook: {e}")
            raise

    async def trigger_webhooks(self, event: str, data: Dict[str, Any]):
        """Trigger all webhooks for a specific event"""
        try:
            # Find webhooks for this event
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, url, secret, headers, retry_count, timeout 
                FROM webhooks 
                WHERE status = 'active' AND events LIKE ?
            ''', (f'%{event}%',))
            
            webhooks = cursor.fetchall()
            conn.close()
            
            # Trigger webhooks asynchronously
            tasks = []
            for webhook in webhooks:
                webhook_id, url, secret, headers_json, retry_count, timeout = webhook
                headers = json.loads(headers_json) if headers_json else {}
                
                task = self._send_webhook(webhook_id, url, event, data, secret, headers, retry_count, timeout)
                tasks.append(task)
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
                
        except Exception as e:
            logger.error(f"Failed to trigger webhooks for event {event}: {e}")

    async def _send_webhook(self, webhook_id: str, url: str, event: str, data: Dict[str, Any],
                           secret: str, headers: Dict[str, str], retry_count: int, timeout: int):
        """Send individual webhook with retry logic"""
        payload = {
            'event': event,
            'timestamp': datetime.utcnow().isoformat(),
            'data': data
        }
        
        # Add signature if secret provided
        if secret:
            signature = hmac.new(
                secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers['X-Webhook-Signature'] = f"sha256={signature}"
        
        headers['Content-Type'] = 'application/json'
        
        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        if response.status == 200:
                            # Update success count
                            conn = sqlite3.connect(self.db_path)
                            cursor = conn.cursor()
                            cursor.execute('''
                                UPDATE webhooks 
                                SET success_count = success_count + 1, last_triggered = CURRENT_TIMESTAMP 
                                WHERE id = ?
                            ''', (webhook_id,))
                            conn.commit()
                            conn.close()
                            
                            logger.info(f"Webhook {webhook_id} triggered successfully")
                            return
                        else:
                            logger.warning(f"Webhook {webhook_id} returned status {response.status}")
                            
            except Exception as e:
                logger.error(f"Webhook {webhook_id} attempt {attempt + 1} failed: {e}")
                if attempt < retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        # Update error count
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE webhooks 
            SET error_count = error_count + 1 
            WHERE id = ?
        ''', (webhook_id,))
        conn.commit()
        conn.close()

    # Zapier Integration
    def create_zapier_trigger(self, trigger_name: str, description: str, 
                             sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a Zapier trigger configuration"""
        return {
            'key': trigger_name,
            'noun': trigger_name.replace('_', ' ').title(),
            'display': {
                'label': trigger_name.replace('_', ' ').title(),
                'description': description
            },
            'operation': {
                'type': 'hook',
                'perform': {
                    'url': f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/zapier/triggers/{trigger_name}",
                    'method': 'POST',
                    'headers': {
                        'Authorization': 'Bearer {{bundle.authData.api_key}}'
                    }
                },
                'sample': sample_data
            }
        }

    def create_zapier_action(self, action_name: str, description: str,
                            input_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a Zapier action configuration"""
        return {
            'key': action_name,
            'noun': action_name.replace('_', ' ').title(),
            'display': {
                'label': action_name.replace('_', ' ').title(),
                'description': description
            },
            'operation': {
                'inputFields': input_fields,
                'perform': {
                    'url': f"{os.getenv('BASE_URL', 'http://localhost:8000')}/api/zapier/actions/{action_name}",
                    'method': 'POST',
                    'headers': {
                        'Authorization': 'Bearer {{bundle.authData.api_key}}',
                        'Content-Type': 'application/json'
                    },
                    'body': {
                        'data': '{{bundle.inputData}}'
                    }
                }
            }
        }

    # CRM Integrations
    async def sync_with_salesforce(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data with Salesforce CRM"""
        try:
            sf_config = self.external_apis.get('salesforce')
            if not sf_config or not sf_config.api_key:
                raise ValueError("Salesforce configuration not found")
            
            headers = {
                'Authorization': f'Bearer {sf_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            if operation == 'create_lead':
                url = f"{sf_config.base_url}/sobjects/Lead"
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=data, headers=headers) as response:
                        result = await response.json()
                        logger.info(f"Salesforce lead created: {result}")
                        return result
            
            elif operation == 'update_contact':
                contact_id = data.pop('Id')
                url = f"{sf_config.base_url}/sobjects/Contact/{contact_id}"
                async with aiohttp.ClientSession() as session:
                    async with session.patch(url, json=data, headers=headers) as response:
                        result = await response.json()
                        logger.info(f"Salesforce contact updated: {result}")
                        return result
            
        except Exception as e:
            logger.error(f"Salesforce sync failed: {e}")
            raise

    async def sync_with_hubspot(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sync data with HubSpot CRM"""
        try:
            hs_config = self.external_apis.get('hubspot')
            if not hs_config or not hs_config.api_key:
                raise ValueError("HubSpot configuration not found")
            
            headers = {
                'Authorization': f'Bearer {hs_config.api_key}',
                'Content-Type': 'application/json'
            }
            
            if operation == 'create_contact':
                url = f"{hs_config.base_url}/crm/v3/objects/contacts"
                payload = {'properties': data}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        result = await response.json()
                        logger.info(f"HubSpot contact created: {result}")
                        return result
            
            elif operation == 'create_deal':
                url = f"{hs_config.base_url}/crm/v3/objects/deals"
                payload = {'properties': data}
                
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, headers=headers) as response:
                        result = await response.json()
                        logger.info(f"HubSpot deal created: {result}")
                        return result
            
        except Exception as e:
            logger.error(f"HubSpot sync failed: {e}")
            raise

    # External API Integration
    async def call_external_api(self, api_name: str, endpoint: str, 
                               method: str = 'GET', data: Dict[str, Any] = None,
                               params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make a call to an external API"""
        try:
            api_config = self.external_apis.get(api_name)
            if not api_config:
                raise ValueError(f"API configuration for {api_name} not found")
            
            # Build URL
            url = f"{api_config.base_url}{endpoint}"
            
            # Prepare headers
            headers = {'Content-Type': 'application/json'}
            
            if api_config.auth_type == 'bearer' and api_config.api_key:
                headers['Authorization'] = f'Bearer {api_config.api_key}'
            elif api_config.auth_type == 'api_key' and api_config.api_key:
                headers['X-API-Key'] = api_config.api_key
            
            # Make request
            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method, url, 
                    json=data, 
                    params=params, 
                    headers=headers
                ) as response:
                    result = await response.json()
                    
                    # Update usage statistics
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute('''
                        UPDATE external_apis 
                        SET request_count = request_count + 1, last_used = CURRENT_TIMESTAMP 
                        WHERE id = ?
                    ''', (api_name,))
                    conn.commit()
                    conn.close()
                    
                    logger.info(f"External API call to {api_name} successful")
                    return result
            
        except Exception as e:
            logger.error(f"External API call to {api_name} failed: {e}")
            raise

    # Browser Extension Support
    def generate_browser_extension_manifest(self, extension_name: str) -> Dict[str, Any]:
        """Generate browser extension manifest"""
        return {
            "manifest_version": 3,
            "name": extension_name,
            "version": "1.0.0",
            "description": "AI Media Processing Browser Extension",
            "permissions": [
                "activeTab",
                "storage",
                "scripting",
                "tabs"
            ],
            "host_permissions": [
                "https://*/*",
                "http://*/*"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "content_scripts": [
                {
                    "matches": ["<all_urls>"],
                    "js": ["content.js"]
                }
            ],
            "action": {
                "default_popup": "popup.html",
                "default_title": extension_name
            },
            "web_accessible_resources": [
                {
                    "resources": ["inject.js"],
                    "matches": ["<all_urls>"]
                }
            ]
        }

    def setup_routes(self):
        """Setup FastAPI routes for the ecosystem"""
        
        @self.app.post("/api/webhooks/trigger")
        async def trigger_webhook_endpoint(request: Request):
            """Endpoint to trigger webhooks"""
            data = await request.json()
            event = data.get('event')
            payload = data.get('data', {})
            
            await self.trigger_webhooks(event, payload)
            return {"status": "success", "message": f"Webhooks triggered for event: {event}"}
        
        @self.app.post("/api/zapier/triggers/{trigger_name}")
        async def zapier_trigger_endpoint(trigger_name: str, request: Request):
            """Zapier trigger endpoint"""
            data = await request.json()
            # Process trigger logic here
            return {"status": "success", "data": data}
        
        @self.app.post("/api/zapier/actions/{action_name}")
        async def zapier_action_endpoint(action_name: str, request: Request):
            """Zapier action endpoint"""
            data = await request.json()
            # Process action logic here
            return {"status": "success", "result": f"Action {action_name} executed"}
        
        @self.app.get("/api/plugins")
        async def list_plugins():
            """List all installed plugins"""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM plugins')
            plugins = cursor.fetchall()
            conn.close()
            
            return {"plugins": plugins}
        
        @self.app.get("/api/integrations")
        async def list_integrations():
            """List all integrations"""
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM integrations')
            integrations = cursor.fetchall()
            conn.close()
            
            return {"integrations": integrations}

    # Marketplace Functions
    def search_marketplace(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search plugin marketplace"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sql = "SELECT * FROM plugin_marketplace WHERE name LIKE ? OR description LIKE ?"
        params = [f"%{query}%", f"%{query}%"]
        
        if category:
            sql += " AND category = ?"
            params.append(category)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        return [dict(zip([col[0] for col in cursor.description], row)) for row in results]

    def get_integration_analytics(self) -> Dict[str, Any]:
        """Get analytics for all integrations"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Plugin usage
        cursor.execute('''
            SELECT name, usage_count, last_used 
            FROM plugins 
            WHERE status = 'active' 
            ORDER BY usage_count DESC
        ''')
        plugin_stats = cursor.fetchall()
        
        # Webhook statistics
        cursor.execute('''
            SELECT name, success_count, error_count, last_triggered 
            FROM webhooks 
            WHERE status = 'active'
        ''')
        webhook_stats = cursor.fetchall()
        
        # API usage
        cursor.execute('''
            SELECT name, request_count, last_used 
            FROM external_apis 
            WHERE status = 'active' 
            ORDER BY request_count DESC
        ''')
        api_stats = cursor.fetchall()
        
        conn.close()
        
        return {
            "plugins": plugin_stats,
            "webhooks": webhook_stats,
            "apis": api_stats,
            "total_plugins": len(plugin_stats),
            "total_webhooks": len(webhook_stats),
            "total_apis": len(api_stats)
        }

# Utility functions for common integrations
class IntegrationHelpers:
    @staticmethod
    def create_slack_notification(webhook_url: str, message: str, channel: str = None):
        """Create Slack notification payload"""
        payload = {
            "text": message,
            "username": "AI Media Processor",
            "icon_emoji": ":robot_face:"
        }
        
        if channel:
            payload["channel"] = channel
        
        return payload
    
    @staticmethod
    def create_discord_embed(title: str, description: str, color: int = 0x00ff00):
        """Create Discord embed payload"""
        return {
            "embeds": [{
                "title": title,
                "description": description,
                "color": color,
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
    
    @staticmethod
    def format_crm_contact(name: str, email: str, company: str = None, 
                          phone: str = None, source: str = "AI Media Processor"):
        """Format contact data for CRM systems"""
        contact = {
            "firstname": name.split()[0] if name else "",
            "lastname": " ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            "email": email,
            "hs_lead_status": "NEW",
            "lifecyclestage": "lead",
            "source": source
        }
        
        if company:
            contact["company"] = company
        if phone:
            contact["phone"] = phone
        
        return contact

if __name__ == "__main__":
    # Example usage
    ecosystem = ThirdPartyEcosystem()
    
    # Example: Register a webhook
    webhook_id = ecosystem.register_webhook(
        name="Transcription Complete",
        url="https://example.com/webhook",
        events=["transcription.completed", "analysis.finished"],
        secret="webhook_secret_key"
    )
    
    print(f"Webhook registered: {webhook_id}")
    
    # Example: Get integration analytics
    analytics = ecosystem.get_integration_analytics()
    print(f"Integration Analytics: {analytics}")