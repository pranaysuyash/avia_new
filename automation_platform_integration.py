"""
Automation Platform Integration
Integrations with Zapier, Make.com, IFTTT, and other automation platforms
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
import httpx
import redis.asyncio as redis
from pydantic import BaseModel, Field, HttpUrl, validator
import jwt
import hmac
import hashlib
import logging
from abc import ABC, abstractmethod
import xml.etree.ElementTree as ET
from urllib.parse import urlencode, parse_qs

logger = logging.getLogger(__name__)

class PlatformType(str, Enum):
    """Supported automation platforms"""
    ZAPIER = "zapier"
    MAKE = "make"
    IFTTT = "ifttt"
    N8N = "n8n"
    INTEGROMAT = "integromat"
    PABBLY = "pabbly"
    AUTOMATE_IO = "automate_io"
    MICROSOFT_FLOW = "microsoft_flow"

class TriggerType(str, Enum):
    """Trigger types for automation"""
    INSTANT = "instant"  # Webhook-based
    POLLING = "polling"  # REST API polling

class AuthMethod(str, Enum):
    """Authentication methods"""
    API_KEY = "api_key"
    OAUTH2 = "oauth2"
    SESSION = "session"
    BASIC = "basic"
    DIGEST = "digest"

@dataclass
class TriggerDefinition:
    """Defines a trigger for automation platforms"""
    id: str
    name: str
    description: str
    type: TriggerType
    sample_data: Dict[str, Any]
    input_fields: List[Dict[str, Any]]
    output_fields: List[Dict[str, Any]]
    perform_method: str  # Function name to execute
    
    def to_zapier_format(self) -> Dict:
        """Convert to Zapier trigger format"""
        return {
            'key': self.id,
            'noun': self.name.split()[-1],
            'display': {
                'label': self.name,
                'description': self.description
            },
            'operation': {
                'type': 'hook' if self.type == TriggerType.INSTANT else 'polling',
                'inputFields': self.input_fields,
                'outputFields': self.output_fields,
                'perform': self.perform_method,
                'sample': self.sample_data
            }
        }
    
    def to_make_format(self) -> Dict:
        """Convert to Make.com trigger format"""
        return {
            'name': self.id,
            'label': self.name,
            'description': self.description,
            'type': 'trigger',
            'webhook': self.type == TriggerType.INSTANT,
            'parameters': self.input_fields,
            'interface': self.output_fields,
            'samples': [self.sample_data]
        }

@dataclass
class ActionDefinition:
    """Defines an action for automation platforms"""
    id: str
    name: str
    description: str
    input_fields: List[Dict[str, Any]]
    output_fields: List[Dict[str, Any]]
    perform_method: str
    sample_input: Dict[str, Any]
    sample_output: Dict[str, Any]
    
    def to_zapier_format(self) -> Dict:
        """Convert to Zapier action format"""
        return {
            'key': self.id,
            'noun': self.name.split()[-1],
            'display': {
                'label': self.name,
                'description': self.description
            },
            'operation': {
                'inputFields': self.input_fields,
                'outputFields': self.output_fields,
                'perform': self.perform_method,
                'sample': self.sample_output
            }
        }
    
    def to_make_format(self) -> Dict:
        """Convert to Make.com action format"""
        return {
            'name': self.id,
            'label': self.name,
            'description': self.description,
            'type': 'action',
            'parameters': self.input_fields,
            'interface': self.output_fields,
            'samples': {
                'input': self.sample_input,
                'output': self.sample_output
            }
        }

@dataclass
class IntegrationApp:
    """Represents an integration app"""
    id: str
    name: str
    description: str
    platform: PlatformType
    version: str
    auth_method: AuthMethod
    base_url: str
    triggers: List[TriggerDefinition] = field(default_factory=list)
    actions: List[ActionDefinition] = field(default_factory=list)
    searches: List[ActionDefinition] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_platform_format(self) -> Dict:
        """Convert to platform-specific format"""
        if self.platform == PlatformType.ZAPIER:
            return self._to_zapier_app()
        elif self.platform == PlatformType.MAKE:
            return self._to_make_app()
        else:
            return self._to_generic_app()
    
    def _to_zapier_app(self) -> Dict:
        """Convert to Zapier app format"""
        return {
            'version': self.version,
            'platformVersion': '2.0.0',
            'authentication': self._get_zapier_auth(),
            'triggers': {t.id: t.to_zapier_format() for t in self.triggers},
            'creates': {a.id: a.to_zapier_format() for a in self.actions},
            'searches': {s.id: s.to_zapier_format() for s in self.searches}
        }
    
    def _to_make_app(self) -> Dict:
        """Convert to Make.com app format"""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'base': self.base_url,
            'auth': self._get_make_auth(),
            'modules': [
                *[t.to_make_format() for t in self.triggers],
                *[a.to_make_format() for a in self.actions],
                *[s.to_make_format() for s in self.searches]
            ]
        }
    
    def _to_generic_app(self) -> Dict:
        """Convert to generic app format"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'auth': {
                'method': self.auth_method.value,
                'config': self.metadata.get('auth_config', {})
            },
            'triggers': [asdict(t) for t in self.triggers],
            'actions': [asdict(a) for a in self.actions],
            'searches': [asdict(s) for s in self.searches]
        }
    
    def _get_zapier_auth(self) -> Dict:
        """Get Zapier authentication configuration"""
        if self.auth_method == AuthMethod.API_KEY:
            return {
                'type': 'custom',
                'fields': [
                    {
                        'key': 'api_key',
                        'label': 'API Key',
                        'required': True,
                        'type': 'string',
                        'helpText': 'Your API key from the dashboard'
                    }
                ],
                'test': '/api/v1/me',
                'connectionLabel': '{{bundle.authData.email}}'
            }
        elif self.auth_method == AuthMethod.OAUTH2:
            return {
                'type': 'oauth2',
                'oauth2Config': {
                    'authorizeUrl': f'{self.base_url}/oauth/authorize',
                    'accessTokenUrl': f'{self.base_url}/oauth/token',
                    'scope': 'read write',
                    'autoRefresh': True
                }
            }
        else:
            return {'type': 'session'}
    
    def _get_make_auth(self) -> Dict:
        """Get Make.com authentication configuration"""
        if self.auth_method == AuthMethod.API_KEY:
            return {
                'type': 'apiKey',
                'parameters': [
                    {
                        'name': 'apiKey',
                        'type': 'text',
                        'label': 'API Key',
                        'required': True
                    }
                ]
            }
        elif self.auth_method == AuthMethod.OAUTH2:
            return {
                'type': 'oauth2',
                'parameters': {
                    'authorize': f'{self.base_url}/oauth/authorize',
                    'token': f'{self.base_url}/oauth/token',
                    'scope': ['read', 'write']
                }
            }
        else:
            return {'type': 'basic'}

class AutomationPlatformIntegration:
    """Main automation platform integration system"""
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.apps: Dict[str, IntegrationApp] = {}
        self.subscriptions: Dict[str, List[str]] = {}  # webhook_id -> [subscriber_ids]
        self.poll_schedules: Dict[str, datetime] = {}  # trigger_id -> next_poll_time
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._running = False
        self._polling_task = None
        
        # Initialize default apps
        self._initialize_default_apps()
        
    def _initialize_default_apps(self):
        """Initialize default integration apps"""
        # Transcription app
        transcription_app = IntegrationApp(
            id="transcription_app",
            name="Transcription Service",
            description="Automated transcription and analysis",
            platform=PlatformType.ZAPIER,
            version="1.0.0",
            auth_method=AuthMethod.API_KEY,
            base_url="https://api.example.com",
            triggers=[
                TriggerDefinition(
                    id="new_transcription",
                    name="New Transcription",
                    description="Triggers when a new transcription is completed",
                    type=TriggerType.INSTANT,
                    sample_data={
                        'id': 'trans_123',
                        'text': 'Sample transcription text',
                        'duration': 120,
                        'language': 'en'
                    },
                    input_fields=[],
                    output_fields=[
                        {'key': 'id', 'label': 'Transcription ID'},
                        {'key': 'text', 'label': 'Text'},
                        {'key': 'duration', 'label': 'Duration'},
                        {'key': 'language', 'label': 'Language'}
                    ],
                    perform_method='trigger_new_transcription'
                ),
                TriggerDefinition(
                    id="analysis_complete",
                    name="Analysis Complete",
                    description="Triggers when content analysis is complete",
                    type=TriggerType.INSTANT,
                    sample_data={
                        'id': 'analysis_123',
                        'sentiment': 'positive',
                        'keywords': ['AI', 'technology'],
                        'score': 0.85
                    },
                    input_fields=[
                        {'key': 'types', 'label': 'Analysis Types', 'list': True}
                    ],
                    output_fields=[
                        {'key': 'id', 'label': 'Analysis ID'},
                        {'key': 'sentiment', 'label': 'Sentiment'},
                        {'key': 'keywords', 'label': 'Keywords', 'list': True},
                        {'key': 'score', 'label': 'Quality Score'}
                    ],
                    perform_method='trigger_analysis_complete'
                )
            ],
            actions=[
                ActionDefinition(
                    id="start_transcription",
                    name="Start Transcription",
                    description="Start a new transcription job",
                    input_fields=[
                        {'key': 'file_url', 'label': 'File URL', 'required': True},
                        {'key': 'language', 'label': 'Language', 'default': 'auto'},
                        {'key': 'speaker_detection', 'label': 'Enable Speaker Detection', 'type': 'boolean'}
                    ],
                    output_fields=[
                        {'key': 'job_id', 'label': 'Job ID'},
                        {'key': 'status', 'label': 'Status'},
                        {'key': 'estimated_time', 'label': 'Estimated Time'}
                    ],
                    perform_method='action_start_transcription',
                    sample_input={'file_url': 'https://example.com/audio.mp3'},
                    sample_output={'job_id': 'job_123', 'status': 'processing', 'estimated_time': 120}
                ),
                ActionDefinition(
                    id="analyze_content",
                    name="Analyze Content",
                    description="Analyze text content",
                    input_fields=[
                        {'key': 'text', 'label': 'Text', 'required': True, 'type': 'text'},
                        {'key': 'analysis_types', 'label': 'Analysis Types', 'list': True}
                    ],
                    output_fields=[
                        {'key': 'sentiment', 'label': 'Sentiment'},
                        {'key': 'keywords', 'label': 'Keywords', 'list': True},
                        {'key': 'summary', 'label': 'Summary'}
                    ],
                    perform_method='action_analyze_content',
                    sample_input={'text': 'Sample text for analysis'},
                    sample_output={'sentiment': 'positive', 'keywords': ['sample'], 'summary': 'Brief summary'}
                )
            ],
            searches=[
                ActionDefinition(
                    id="find_transcription",
                    name="Find Transcription",
                    description="Search for a transcription",
                    input_fields=[
                        {'key': 'query', 'label': 'Search Query', 'required': True}
                    ],
                    output_fields=[
                        {'key': 'id', 'label': 'Transcription ID'},
                        {'key': 'text', 'label': 'Text'},
                        {'key': 'created_at', 'label': 'Created At'}
                    ],
                    perform_method='search_transcription',
                    sample_input={'query': 'meeting'},
                    sample_output={'id': 'trans_123', 'text': 'Meeting transcript', 'created_at': '2024-01-01'}
                )
            ]
        )
        
        self.apps[transcription_app.id] = transcription_app
        
    async def initialize(self):
        """Initialize the integration system"""
        if not self.redis_client:
            self.redis_client = await redis.from_url("redis://localhost:6379")
            
        self._running = True
        self._polling_task = asyncio.create_task(self._process_polling_triggers())
        
        logger.info("Automation platform integration initialized")
        
    async def shutdown(self):
        """Shutdown the integration system"""
        self._running = False
        
        if self._polling_task:
            self._polling_task.cancel()
            
        await self.http_client.aclose()
        
        if self.redis_client:
            await self.redis_client.close()
            
        logger.info("Automation platform integration shutdown")
        
    async def register_app(self, app: IntegrationApp) -> str:
        """Register a new integration app"""
        self.apps[app.id] = app
        
        # Store in Redis
        if self.redis_client:
            await self.redis_client.hset(
                f"integration:app:{app.id}",
                mapping={
                    'name': app.name,
                    'platform': app.platform.value,
                    'version': app.version,
                    'data': json.dumps(app.to_platform_format())
                }
            )
            
        logger.info(f"Registered integration app: {app.id}")
        return app.id
        
    async def subscribe_to_trigger(
        self,
        app_id: str,
        trigger_id: str,
        subscriber_id: str,
        webhook_url: Optional[str] = None,
        config: Optional[Dict] = None
    ) -> str:
        """Subscribe to a trigger"""
        if app_id not in self.apps:
            raise ValueError(f"App {app_id} not found")
            
        app = self.apps[app_id]
        trigger = next((t for t in app.triggers if t.id == trigger_id), None)
        
        if not trigger:
            raise ValueError(f"Trigger {trigger_id} not found")
            
        subscription_id = str(uuid.uuid4())
        
        if trigger.type == TriggerType.INSTANT:
            # Store webhook subscription
            if not webhook_url:
                raise ValueError("Webhook URL required for instant triggers")
                
            if self.redis_client:
                await self.redis_client.hset(
                    f"integration:subscription:{subscription_id}",
                    mapping={
                        'app_id': app_id,
                        'trigger_id': trigger_id,
                        'subscriber_id': subscriber_id,
                        'webhook_url': webhook_url,
                        'config': json.dumps(config or {}),
                        'created_at': datetime.utcnow().isoformat()
                    }
                )
                
            # Add to subscriptions
            key = f"{app_id}:{trigger_id}"
            if key not in self.subscriptions:
                self.subscriptions[key] = []
            self.subscriptions[key].append(subscriber_id)
            
        else:  # POLLING
            # Schedule polling
            self.poll_schedules[subscription_id] = datetime.utcnow()
            
        logger.info(f"Created subscription {subscription_id} for {trigger_id}")
        return subscription_id
        
    async def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from a trigger"""
        if self.redis_client:
            deleted = await self.redis_client.delete(f"integration:subscription:{subscription_id}")
            
            if deleted:
                # Remove from local subscriptions
                # This would need more sophisticated tracking in production
                logger.info(f"Unsubscribed: {subscription_id}")
                return True
                
        return False
        
    async def trigger_webhook(
        self,
        app_id: str,
        trigger_id: str,
        data: Dict[str, Any]
    ):
        """Trigger a webhook for subscribers"""
        key = f"{app_id}:{trigger_id}"
        
        if key not in self.subscriptions:
            return
            
        # Get all subscriptions from Redis
        if self.redis_client:
            for subscriber_id in self.subscriptions[key]:
                # Get subscription details
                pattern = f"integration:subscription:*"
                async for sub_key in self.redis_client.scan_iter(pattern):
                    sub_data = await self.redis_client.hgetall(sub_key)
                    
                    if (sub_data.get(b'subscriber_id', b'').decode() == subscriber_id and
                        sub_data.get(b'trigger_id', b'').decode() == trigger_id):
                        
                        webhook_url = sub_data.get(b'webhook_url', b'').decode()
                        
                        # Send webhook
                        await self._send_webhook(webhook_url, {
                            'app_id': app_id,
                            'trigger_id': trigger_id,
                            'data': data,
                            'timestamp': datetime.utcnow().isoformat()
                        })
                        
    async def _send_webhook(self, url: str, data: Dict):
        """Send webhook to subscriber"""
        try:
            response = await self.http_client.post(
                url,
                json=data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code >= 400:
                logger.error(f"Webhook failed: {url} - {response.status_code}")
                
        except Exception as e:
            logger.error(f"Webhook error: {url} - {e}")
            
    async def execute_action(
        self,
        app_id: str,
        action_id: str,
        input_data: Dict[str, Any],
        auth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an action"""
        if app_id not in self.apps:
            raise ValueError(f"App {app_id} not found")
            
        app = self.apps[app_id]
        action = next((a for a in app.actions if a.id == action_id), None)
        
        if not action:
            raise ValueError(f"Action {action_id} not found")
            
        # Execute the action
        result = await self._perform_action(app, action, input_data, auth_data)
        
        # Log execution
        if self.redis_client:
            await self.redis_client.lpush(
                f"integration:executions:{app_id}:{action_id}",
                json.dumps({
                    'timestamp': datetime.utcnow().isoformat(),
                    'input': input_data,
                    'output': result,
                    'success': True
                })
            )
            
        return result
        
    async def _perform_action(
        self,
        app: IntegrationApp,
        action: ActionDefinition,
        input_data: Dict[str, Any],
        auth_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform the actual action"""
        # This would call the actual API endpoint
        # For now, return sample output
        return action.sample_output
        
    async def _process_polling_triggers(self):
        """Process polling triggers"""
        while self._running:
            try:
                await asyncio.sleep(10)  # Check every 10 seconds
                
                current_time = datetime.utcnow()
                
                for subscription_id, next_poll in list(self.poll_schedules.items()):
                    if next_poll <= current_time:
                        # Perform polling
                        await self._poll_trigger(subscription_id)
                        
                        # Schedule next poll (every 5 minutes)
                        self.poll_schedules[subscription_id] = current_time + timedelta(minutes=5)
                        
            except Exception as e:
                logger.error(f"Polling error: {e}")
                
    async def _poll_trigger(self, subscription_id: str):
        """Poll a trigger for new data"""
        # Get subscription details from Redis
        if not self.redis_client:
            return
            
        sub_data = await self.redis_client.hgetall(f"integration:subscription:{subscription_id}")
        
        if not sub_data:
            # Remove from schedules if subscription doesn't exist
            del self.poll_schedules[subscription_id]
            return
            
        app_id = sub_data.get(b'app_id', b'').decode()
        trigger_id = sub_data.get(b'trigger_id', b'').decode()
        webhook_url = sub_data.get(b'webhook_url', b'').decode()
        
        # Get new data (this would call the actual API)
        # For now, we'll simulate
        new_data = {
            'items': [
                {'id': str(uuid.uuid4()), 'data': 'New item'}
            ]
        }
        
        if new_data['items']:
            # Send to webhook
            await self._send_webhook(webhook_url, {
                'app_id': app_id,
                'trigger_id': trigger_id,
                'data': new_data,
                'timestamp': datetime.utcnow().isoformat()
            })
            
    async def export_app_definition(
        self,
        app_id: str,
        platform: PlatformType
    ) -> Dict:
        """Export app definition for a specific platform"""
        if app_id not in self.apps:
            raise ValueError(f"App {app_id} not found")
            
        app = self.apps[app_id]
        
        # Convert to platform format
        if platform == PlatformType.ZAPIER:
            return self._export_zapier_cli(app)
        elif platform == PlatformType.MAKE:
            return self._export_make_definition(app)
        elif platform == PlatformType.N8N:
            return self._export_n8n_node(app)
        else:
            return app.to_platform_format()
            
    def _export_zapier_cli(self, app: IntegrationApp) -> Dict:
        """Export as Zapier CLI app"""
        return {
            'name': app.name,
            'version': app.version,
            'description': app.description,
            'app': app._to_zapier_app(),
            'cli_config': {
                'beforeRequest': ['addAuthToRequest'],
                'afterResponse': ['handleErrors']
            }
        }
        
    def _export_make_definition(self, app: IntegrationApp) -> Dict:
        """Export as Make.com app definition"""
        return {
            'name': app.name,
            'version': app.version,
            'description': app.description,
            'base': app.base_url,
            'modules': app._to_make_app()['modules'],
            'common': {
                'auth': app._to_make_app()['auth']
            }
        }
        
    def _export_n8n_node(self, app: IntegrationApp) -> Dict:
        """Export as n8n node"""
        return {
            'displayName': app.name,
            'name': app.id.replace('_', ''),
            'group': ['transform'],
            'version': 1,
            'description': app.description,
            'defaults': {
                'name': app.name
            },
            'inputs': ['main'],
            'outputs': ['main'],
            'credentials': [
                {
                    'name': f'{app.id}Api',
                    'required': True
                }
            ],
            'properties': self._generate_n8n_properties(app)
        }
        
    def _generate_n8n_properties(self, app: IntegrationApp) -> List[Dict]:
        """Generate n8n node properties"""
        properties = [
            {
                'displayName': 'Resource',
                'name': 'resource',
                'type': 'options',
                'options': [
                    {'name': 'Trigger', 'value': 'trigger'},
                    {'name': 'Action', 'value': 'action'}
                ],
                'default': 'action'
            }
        ]
        
        # Add trigger options
        if app.triggers:
            properties.append({
                'displayName': 'Trigger',
                'name': 'trigger',
                'type': 'options',
                'displayOptions': {
                    'show': {
                        'resource': ['trigger']
                    }
                },
                'options': [
                    {'name': t.name, 'value': t.id}
                    for t in app.triggers
                ]
            })
            
        # Add action options
        if app.actions:
            properties.append({
                'displayName': 'Action',
                'name': 'action',
                'type': 'options',
                'displayOptions': {
                    'show': {
                        'resource': ['action']
                    }
                },
                'options': [
                    {'name': a.name, 'value': a.id}
                    for a in app.actions
                ]
            })
            
        return properties

# Platform-specific connectors
class ZapierConnector:
    """Zapier-specific connector"""
    
    @staticmethod
    async def validate_subscription(request_data: Dict) -> bool:
        """Validate Zapier subscription request"""
        # Zapier sends a specific format for subscription validation
        return 'subscription_url' in request_data and 'target_url' in request_data
        
    @staticmethod
    async def format_response(data: Any) -> List[Dict]:
        """Format response for Zapier"""
        # Zapier expects an array of objects
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            return [{'data': str(data)}]

class MakeConnector:
    """Make.com (Integromat) specific connector"""
    
    @staticmethod
    async def validate_webhook(headers: Dict, body: str, secret: str) -> bool:
        """Validate Make.com webhook signature"""
        signature = headers.get('x-make-signature', '')
        expected = hmac.new(
            secret.encode(),
            body.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(signature, expected)
        
    @staticmethod
    async def format_response(data: Any) -> Dict:
        """Format response for Make.com"""
        return {
            'data': data if isinstance(data, (dict, list)) else {'value': data},
            'metadata': {
                'timestamp': datetime.utcnow().isoformat()
            }
        }

# Usage example
async def demo_automation():
    """Demonstrate automation platform integration"""
    system = AutomationPlatformIntegration()
    await system.initialize()
    
    # Get app
    app = system.apps['transcription_app']
    
    # Export for Zapier
    zapier_def = await system.export_app_definition('transcription_app', PlatformType.ZAPIER)
    print(f"Zapier app definition: {json.dumps(zapier_def, indent=2)}")
    
    # Subscribe to trigger
    subscription_id = await system.subscribe_to_trigger(
        'transcription_app',
        'new_transcription',
        'user_123',
        'https://hooks.zapier.com/hook/123'
    )
    
    print(f"Created subscription: {subscription_id}")
    
    # Trigger webhook
    await system.trigger_webhook(
        'transcription_app',
        'new_transcription',
        {
            'id': 'trans_456',
            'text': 'New transcription completed',
            'duration': 180
        }
    )
    
    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_automation())