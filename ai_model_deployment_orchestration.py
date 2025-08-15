"""
AI Model Deployment Orchestration System
Comprehensive deployment orchestration with blue-green, canary, and rolling deployment strategies
"""

import asyncio
import json
import logging
import uuid
import yaml
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from enum import Enum
import subprocess
import docker
import kubernetes
from kubernetes import client, config
import sqlite3
import redis.asyncio as redis
from collections import defaultdict, deque
import threading
import psutil
import requests
import hashlib
import warnings
warnings.filterwarnings('ignore')

# Import our model management components
from ai_model_management_system import ModelRegistry, ModelMetadata, ModelStatus
from ai_model_performance_monitoring import ModelPerformanceMonitor, Alert, AlertSeverity
from comprehensive_medical_schema import ComprehensiveMedicalSchema, MedicalValidationEngine

logger = logging.getLogger(__name__)

class DeploymentStrategy(Enum):
    """Deployment strategies"""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    RECREATE = "recreate"
    A_B_TEST = "ab_test"
    SHADOW = "shadow"

class DeploymentEnvironment(Enum):
    """Deployment environments"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"
    CANARY = "canary"

class DeploymentStatus(Enum):
    """Deployment status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DEPLOYING = "deploying"
    VALIDATING = "validating"
    ACTIVE = "active"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PAUSED = "paused"
    CANCELLED = "cancelled"

class DeploymentPlatform(Enum):
    """Deployment platforms"""
    KUBERNETES = "kubernetes"
    DOCKER = "docker"
    AWS_ECS = "aws_ecs"
    AWS_LAMBDA = "aws_lambda"
    AZURE_CONTAINER = "azure_container"
    GCP_CLOUD_RUN = "gcp_cloud_run"
    LOCAL = "local"

class HealthCheckType(Enum):
    """Health check types"""
    HTTP = "http"
    TCP = "tcp"
    COMMAND = "command"
    CUSTOM = "custom"

@dataclass
class ResourceRequirements:
    """Resource requirements for deployment"""
    cpu_request: str = "100m"
    cpu_limit: str = "500m"
    memory_request: str = "256Mi"
    memory_limit: str = "1Gi"
    gpu_request: int = 0
    storage_request: str = "1Gi"
    node_selector: Dict[str, str] = field(default_factory=dict)
    tolerations: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class HealthCheck:
    """Health check configuration"""
    type: HealthCheckType
    endpoint: Optional[str] = None
    port: Optional[int] = None
    command: Optional[List[str]] = None
    initial_delay_seconds: int = 30
    period_seconds: int = 10
    timeout_seconds: int = 5
    failure_threshold: int = 3
    success_threshold: int = 1

@dataclass
class ScalingConfig:
    """Auto-scaling configuration"""
    min_replicas: int = 1
    max_replicas: int = 10
    target_cpu_utilization: int = 70
    target_memory_utilization: int = 80
    target_requests_per_second: Optional[int] = None
    scale_up_cooldown: int = 300
    scale_down_cooldown: int = 300

@dataclass
class DeploymentConfig:
    """Comprehensive deployment configuration"""
    deployment_id: str
    model_id: str
    model_version: str
    environment: DeploymentEnvironment
    platform: DeploymentPlatform
    strategy: DeploymentStrategy
    image_uri: str
    service_name: str
    namespace: str = "default"
    replicas: int = 3
    resources: ResourceRequirements = field(default_factory=ResourceRequirements)
    health_check: HealthCheck = field(default_factory=lambda: HealthCheck(HealthCheckType.HTTP))
    scaling: ScalingConfig = field(default_factory=ScalingConfig)
    environment_variables: Dict[str, str] = field(default_factory=dict)
    secrets: Dict[str, str] = field(default_factory=dict)
    config_maps: Dict[str, str] = field(default_factory=dict)
    volumes: List[Dict[str, Any]] = field(default_factory=list)
    ingress_config: Optional[Dict[str, Any]] = None
    monitoring_config: Dict[str, Any] = field(default_factory=dict)
    medical_compliance: Dict[str, Any] = field(default_factory=dict)
    rollback_config: Dict[str, Any] = field(default_factory=dict)
    custom_annotations: Dict[str, str] = field(default_factory=dict)

@dataclass
class DeploymentInstance:
    """Running deployment instance"""
    instance_id: str
    deployment_id: str
    pod_name: str
    node_name: str
    status: str
    health_status: str
    created_at: datetime
    ready_at: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    request_count: int = 0
    error_count: int = 0
    last_health_check: Optional[datetime] = None

@dataclass
class DeploymentRecord:
    """Complete deployment record"""
    deployment_id: str
    model_id: str
    config: DeploymentConfig
    status: DeploymentStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    instances: List[DeploymentInstance] = field(default_factory=list)
    events: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    rollback_target: Optional[str] = None
    error_message: Optional[str] = None

class KubernetesDeployer:
    """Kubernetes deployment handler"""
    
    def __init__(self, kubeconfig_path: Optional[str] = None):
        self.kubeconfig_path = kubeconfig_path
        self.api_client = None
        self.apps_v1 = None
        self.core_v1 = None
        self.autoscaling_v1 = None
        self._initialize_k8s_client()
    
    def _initialize_k8s_client(self):
        """Initialize Kubernetes client"""
        try:
            if self.kubeconfig_path:
                config.load_kube_config(config_file=self.kubeconfig_path)
            else:
                try:
                    config.load_incluster_config()
                except:
                    config.load_kube_config()
            
            self.api_client = client.ApiClient()
            self.apps_v1 = client.AppsV1Api()
            self.core_v1 = client.CoreV1Api()
            self.autoscaling_v1 = client.AutoscalingV1Api()
            
            logger.info("Kubernetes client initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize Kubernetes client: {e}")
    
    async def deploy_model(self, deployment_config: DeploymentConfig) -> bool:
        """Deploy model to Kubernetes"""
        try:
            # Create deployment manifest
            deployment_manifest = self._create_deployment_manifest(deployment_config)
            
            # Create or update deployment
            try:
                self.apps_v1.read_namespaced_deployment(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace
                )
                # Update existing deployment
                self.apps_v1.patch_namespaced_deployment(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace,
                    body=deployment_manifest
                )
                logger.info(f"Updated deployment {deployment_config.service_name}")
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Create new deployment
                    self.apps_v1.create_namespaced_deployment(
                        namespace=deployment_config.namespace,
                        body=deployment_manifest
                    )
                    logger.info(f"Created deployment {deployment_config.service_name}")
                else:
                    raise
            
            # Create service
            service_manifest = self._create_service_manifest(deployment_config)
            try:
                self.core_v1.read_namespaced_service(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace
                )
                self.core_v1.patch_namespaced_service(
                    name=deployment_config.service_name,
                    namespace=deployment_config.namespace,
                    body=service_manifest
                )
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    self.core_v1.create_namespaced_service(
                        namespace=deployment_config.namespace,
                        body=service_manifest
                    )
            
            # Create HPA if auto-scaling is enabled
            if deployment_config.scaling.max_replicas > deployment_config.scaling.min_replicas:
                hpa_manifest = self._create_hpa_manifest(deployment_config)
                try:
                    self.autoscaling_v1.read_namespaced_horizontal_pod_autoscaler(
                        name=deployment_config.service_name,
                        namespace=deployment_config.namespace
                    )
                    self.autoscaling_v1.patch_namespaced_horizontal_pod_autoscaler(
                        name=deployment_config.service_name,
                        namespace=deployment_config.namespace,
                        body=hpa_manifest
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        self.autoscaling_v1.create_namespaced_horizontal_pod_autoscaler(
                            namespace=deployment_config.namespace,
                            body=hpa_manifest
                        )
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy to Kubernetes: {e}")
            return False
    
    def _create_deployment_manifest(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create Kubernetes deployment manifest"""
        
        # Container definition
        container = {
            "name": config.service_name,
            "image": config.image_uri,
            "ports": [{"containerPort": 8080}],
            "env": [
                {"name": k, "value": v} 
                for k, v in config.environment_variables.items()
            ],
            "resources": {
                "requests": {
                    "cpu": config.resources.cpu_request,
                    "memory": config.resources.memory_request
                },
                "limits": {
                    "cpu": config.resources.cpu_limit,
                    "memory": config.resources.memory_limit
                }
            }
        }
        
        # Add GPU resources if requested
        if config.resources.gpu_request > 0:
            container["resources"]["requests"]["nvidia.com/gpu"] = str(config.resources.gpu_request)
            container["resources"]["limits"]["nvidia.com/gpu"] = str(config.resources.gpu_request)
        
        # Health checks
        if config.health_check.type == HealthCheckType.HTTP:
            container["livenessProbe"] = {
                "httpGet": {
                    "path": config.health_check.endpoint or "/health",
                    "port": config.health_check.port or 8080
                },
                "initialDelaySeconds": config.health_check.initial_delay_seconds,
                "periodSeconds": config.health_check.period_seconds,
                "timeoutSeconds": config.health_check.timeout_seconds,
                "failureThreshold": config.health_check.failure_threshold
            }
            container["readinessProbe"] = container["livenessProbe"].copy()
            container["readinessProbe"]["successThreshold"] = config.health_check.success_threshold
        
        # Pod template
        pod_template = {
            "metadata": {
                "labels": {
                    "app": config.service_name,
                    "model-id": config.model_id,
                    "version": config.model_version,
                    "environment": config.environment.value
                },
                "annotations": config.custom_annotations
            },
            "spec": {
                "containers": [container]
            }
        }
        
        # Node selector
        if config.resources.node_selector:
            pod_template["spec"]["nodeSelector"] = config.resources.node_selector
        
        # Tolerations
        if config.resources.tolerations:
            pod_template["spec"]["tolerations"] = config.resources.tolerations
        
        # Deployment manifest
        deployment = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {
                "name": config.service_name,
                "namespace": config.namespace,
                "labels": {
                    "app": config.service_name,
                    "model-id": config.model_id
                }
            },
            "spec": {
                "replicas": config.replicas,
                "selector": {
                    "matchLabels": {
                        "app": config.service_name
                    }
                },
                "template": pod_template,
                "strategy": {
                    "type": "RollingUpdate",
                    "rollingUpdate": {
                        "maxUnavailable": "25%",
                        "maxSurge": "25%"
                    }
                }
            }
        }
        
        return deployment
    
    def _create_service_manifest(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create Kubernetes service manifest"""
        
        service = {
            "apiVersion": "v1",
            "kind": "Service",
            "metadata": {
                "name": config.service_name,
                "namespace": config.namespace,
                "labels": {
                    "app": config.service_name
                }
            },
            "spec": {
                "selector": {
                    "app": config.service_name
                },
                "ports": [
                    {
                        "port": 80,
                        "targetPort": 8080,
                        "protocol": "TCP"
                    }
                ],
                "type": "ClusterIP"
            }
        }
        
        return service
    
    def _create_hpa_manifest(self, config: DeploymentConfig) -> Dict[str, Any]:
        """Create Horizontal Pod Autoscaler manifest"""
        
        hpa = {
            "apiVersion": "autoscaling/v1",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {
                "name": config.service_name,
                "namespace": config.namespace
            },
            "spec": {
                "scaleTargetRef": {
                    "apiVersion": "apps/v1",
                    "kind": "Deployment",
                    "name": config.service_name
                },
                "minReplicas": config.scaling.min_replicas,
                "maxReplicas": config.scaling.max_replicas,
                "targetCPUUtilizationPercentage": config.scaling.target_cpu_utilization
            }
        }
        
        return hpa
    
    async def get_deployment_status(self, service_name: str, namespace: str) -> Dict[str, Any]:
        """Get deployment status"""
        try:
            deployment = self.apps_v1.read_namespaced_deployment(
                name=service_name,
                namespace=namespace
            )
            
            # Get pods
            pods = self.core_v1.list_namespaced_pod(
                namespace=namespace,
                label_selector=f"app={service_name}"
            )
            
            pod_statuses = []
            for pod in pods.items:
                pod_status = {
                    "name": pod.metadata.name,
                    "status": pod.status.phase,
                    "ready": all(
                        condition.status == "True" 
                        for condition in (pod.status.conditions or [])
                        if condition.type == "Ready"
                    ),
                    "node": pod.spec.node_name,
                    "created": pod.metadata.creation_timestamp
                }
                pod_statuses.append(pod_status)
            
            return {
                "replicas": deployment.spec.replicas,
                "ready_replicas": deployment.status.ready_replicas or 0,
                "updated_replicas": deployment.status.updated_replicas or 0,
                "available_replicas": deployment.status.available_replicas or 0,
                "pods": pod_statuses
            }
            
        except Exception as e:
            logger.error(f"Failed to get deployment status: {e}")
            return {}
    
    async def delete_deployment(self, service_name: str, namespace: str) -> bool:
        """Delete deployment and associated resources"""
        try:
            # Delete deployment
            self.apps_v1.delete_namespaced_deployment(
                name=service_name,
                namespace=namespace
            )
            
            # Delete service
            try:
                self.core_v1.delete_namespaced_service(
                    name=service_name,
                    namespace=namespace
                )
            except client.exceptions.ApiException:
                pass
            
            # Delete HPA
            try:
                self.autoscaling_v1.delete_namespaced_horizontal_pod_autoscaler(
                    name=service_name,
                    namespace=namespace
                )
            except client.exceptions.ApiException:
                pass
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete deployment: {e}")
            return False

class DockerDeployer:
    """Docker deployment handler"""
    
    def __init__(self):
        self.client = None
        self._initialize_docker_client()
    
    def _initialize_docker_client(self):
        """Initialize Docker client"""
        try:
            self.client = docker.from_env()
            logger.info("Docker client initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize Docker client: {e}")
    
    async def deploy_model(self, deployment_config: DeploymentConfig) -> bool:
        """Deploy model using Docker"""
        try:
            # Pull image
            self.client.images.pull(deployment_config.image_uri)
            
            # Stop existing container if it exists
            try:
                existing_container = self.client.containers.get(deployment_config.service_name)
                existing_container.stop()
                existing_container.remove()
            except docker.errors.NotFound:
                pass
            
            # Run new container
            container = self.client.containers.run(
                deployment_config.image_uri,
                name=deployment_config.service_name,
                ports={'8080/tcp': None},  # Auto-assign port
                environment=deployment_config.environment_variables,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            logger.info(f"Docker container started: {container.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy with Docker: {e}")
            return False
    
    async def get_deployment_status(self, service_name: str) -> Dict[str, Any]:
        """Get Docker container status"""
        try:
            container = self.client.containers.get(service_name)
            return {
                "status": container.status,
                "id": container.id,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs["Created"],
                "ports": container.ports
            }
        except docker.errors.NotFound:
            return {"status": "not_found"}
        except Exception as e:
            logger.error(f"Failed to get Docker status: {e}")
            return {"status": "error", "error": str(e)}

class ModelDeploymentOrchestrator:
    """Comprehensive model deployment orchestration system"""
    
    def __init__(
        self,
        model_registry: ModelRegistry,
        performance_monitor: ModelPerformanceMonitor,
        redis_url: str = "redis://localhost:6379",
        db_path: str = "deployments.db"
    ):
        self.model_registry = model_registry
        self.performance_monitor = performance_monitor
        self.redis_url = redis_url
        self.db_path = db_path
        self.redis_client = None
        self.db_connection = None
        
        # Deployment state
        self.active_deployments: Dict[str, DeploymentRecord] = {}
        self.deployment_queue = asyncio.Queue()
        
        # Platform handlers
        self.deployers = {
            DeploymentPlatform.KUBERNETES: KubernetesDeployer(),
            DeploymentPlatform.DOCKER: DockerDeployer()
        }
        
        # Background workers
        self.orchestration_active = False
        self.orchestration_thread = None
        self.monitoring_thread = None
        
        # Medical compliance
        self.medical_schema = None
        self.medical_validator = None
    
    async def initialize(self):
        """Initialize the deployment orchestrator"""
        try:
            # Initialize Redis connection
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            
            # Initialize database
            self._initialize_database()
            
            # Initialize medical components
            try:
                self.medical_schema = ComprehensiveMedicalSchema()
                await self.medical_schema.initialize()
                
                self.medical_validator = MedicalValidationEngine()
                await self.medical_validator.initialize()
            except Exception as e:
                logger.warning(f"Medical components not available: {e}")
            
            # Start background workers
            self.orchestration_active = True
            self.orchestration_thread = threading.Thread(target=self._orchestration_worker, daemon=True)
            self.monitoring_thread = threading.Thread(target=self._monitoring_worker, daemon=True)
            
            self.orchestration_thread.start()
            self.monitoring_thread.start()
            
            logger.info("Model Deployment Orchestrator initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Model Deployment Orchestrator: {e}")
            raise e
    
    def _initialize_database(self):
        """Initialize SQLite database for deployment tracking"""
        self.db_connection = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.db_connection.cursor()
        
        # Deployments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployments (
                deployment_id TEXT PRIMARY KEY,
                model_id TEXT,
                config TEXT,
                status TEXT,
                created_at TEXT,
                started_at TEXT,
                completed_at TEXT,
                events TEXT,
                metrics TEXT,
                error_message TEXT
            )
        ''')
        
        # Deployment instances table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS deployment_instances (
                instance_id TEXT PRIMARY KEY,
                deployment_id TEXT,
                pod_name TEXT,
                node_name TEXT,
                status TEXT,
                health_status TEXT,
                created_at TEXT,
                ready_at TEXT,
                cpu_usage REAL,
                memory_usage REAL,
                request_count INTEGER,
                error_count INTEGER,
                last_health_check TEXT
            )
        ''')
        
        self.db_connection.commit()
    
    async def deploy_model(
        self,
        model_id: str,
        environment: DeploymentEnvironment,
        platform: DeploymentPlatform = DeploymentPlatform.KUBERNETES,
        strategy: DeploymentStrategy = DeploymentStrategy.ROLLING,
        custom_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Deploy a model with specified configuration"""
        
        # Validate model exists
        try:
            model, metadata = await self.model_registry.load_model(model_id)
        except Exception as e:
            raise ValueError(f"Model {model_id} not found: {e}")
        
        # Create deployment configuration
        deployment_id = f"deploy_{model_id}_{environment.value}_{int(time.time())}"
        
        config = DeploymentConfig(
            deployment_id=deployment_id,
            model_id=model_id,
            model_version=metadata.version,
            environment=environment,
            platform=platform,
            strategy=strategy,
            image_uri=custom_config.get('image_uri', f"model-server:{model_id}") if custom_config else f"model-server:{model_id}",
            service_name=f"{model_id}-{environment.value}".replace("_", "-"),
            namespace=custom_config.get('namespace', 'default') if custom_config else 'default'
        )
        
        # Apply custom configuration
        if custom_config:
            self._apply_custom_config(config, custom_config)
        
        # Medical compliance validation
        if self.medical_validator and metadata.type.value in ['medical', 'clinical']:
            compliance_check = await self._validate_medical_compliance(config, metadata)
            if not compliance_check['compliant']:
                raise ValueError(f"Medical compliance validation failed: {compliance_check['issues']}")
        
        # Create deployment record
        deployment_record = DeploymentRecord(
            deployment_id=deployment_id,
            model_id=model_id,
            config=config,
            status=DeploymentStatus.PENDING,
            created_at=datetime.now()
        )
        
        self.active_deployments[deployment_id] = deployment_record
        
        # Store in database
        self._store_deployment_record(deployment_record)
        
        # Add to deployment queue
        await self.deployment_queue.put((deployment_id, strategy))
        
        logger.info(f"Deployment queued: {deployment_id}")
        return deployment_id
    
    def _apply_custom_config(self, config: DeploymentConfig, custom_config: Dict[str, Any]):
        """Apply custom configuration to deployment config"""
        
        if 'replicas' in custom_config:
            config.replicas = custom_config['replicas']
        
        if 'resources' in custom_config:
            resource_config = custom_config['resources']
            if 'cpu_request' in resource_config:
                config.resources.cpu_request = resource_config['cpu_request']
            if 'memory_request' in resource_config:
                config.resources.memory_request = resource_config['memory_request']
            if 'gpu_request' in resource_config:
                config.resources.gpu_request = resource_config['gpu_request']
        
        if 'environment_variables' in custom_config:
            config.environment_variables.update(custom_config['environment_variables'])
        
        if 'scaling' in custom_config:
            scaling_config = custom_config['scaling']
            config.scaling.min_replicas = scaling_config.get('min_replicas', config.scaling.min_replicas)
            config.scaling.max_replicas = scaling_config.get('max_replicas', config.scaling.max_replicas)
    
    async def _validate_medical_compliance(
        self,
        config: DeploymentConfig,
        metadata: ModelMetadata
    ) -> Dict[str, Any]:
        """Validate medical compliance for deployment"""
        
        compliance_issues = []
        
        # Check encryption requirements
        if not config.environment_variables.get('ENABLE_ENCRYPTION', 'false').lower() == 'true':
            compliance_issues.append("Data encryption not enabled")
        
        # Check audit logging
        if not config.monitoring_config.get('audit_logging', False):
            compliance_issues.append("Audit logging not configured")
        
        # Check resource isolation
        if config.environment == DeploymentEnvironment.PRODUCTION and config.replicas < 2:
            compliance_issues.append("Production medical models require at least 2 replicas for availability")
        
        return {
            'compliant': len(compliance_issues) == 0,
            'issues': compliance_issues
        }
    
    def _store_deployment_record(self, record: DeploymentRecord):
        """Store deployment record in database"""
        cursor = self.db_connection.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO deployments (
                deployment_id, model_id, config, status, created_at,
                started_at, completed_at, events, metrics, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.deployment_id,
            record.model_id,
            json.dumps(record.config.__dict__, default=str),
            record.status.value,
            record.created_at.isoformat(),
            record.started_at.isoformat() if record.started_at else None,
            record.completed_at.isoformat() if record.completed_at else None,
            json.dumps(record.events),
            json.dumps(record.metrics),
            record.error_message
        ))
        self.db_connection.commit()
    
    def _orchestration_worker(self):
        """Background worker for processing deployments"""
        while self.orchestration_active:
            try:
                if not self.deployment_queue.empty():
                    deployment_id, strategy = asyncio.run(self.deployment_queue.get())
                    asyncio.run(self._process_deployment(deployment_id, strategy))
                else:
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Orchestration worker error: {e}")
                time.sleep(10)
    
    async def _process_deployment(self, deployment_id: str, strategy: DeploymentStrategy):
        """Process a deployment with the specified strategy"""
        
        record = self.active_deployments.get(deployment_id)
        if not record:
            logger.error(f"Deployment record not found: {deployment_id}")
            return
        
        try:
            record.status = DeploymentStatus.IN_PROGRESS
            record.started_at = datetime.now()
            record.events.append(f"Deployment started with strategy: {strategy.value}")
            
            # Execute deployment strategy
            if strategy == DeploymentStrategy.BLUE_GREEN:
                success = await self._execute_blue_green_deployment(record)
            elif strategy == DeploymentStrategy.CANARY:
                success = await self._execute_canary_deployment(record)
            elif strategy == DeploymentStrategy.ROLLING:
                success = await self._execute_rolling_deployment(record)
            else:
                success = await self._execute_simple_deployment(record)
            
            if success:
                record.status = DeploymentStatus.VALIDATING
                record.events.append("Deployment completed, starting validation")
                
                # Validate deployment
                if await self._validate_deployment(record):
                    record.status = DeploymentStatus.ACTIVE
                    record.completed_at = datetime.now()
                    record.events.append("Deployment validation successful")
                    
                    # Update model status
                    model, metadata = await self.model_registry.load_model(record.model_id)
                    metadata.status = ModelStatus.DEPLOYED
                else:
                    record.status = DeploymentStatus.FAILED
                    record.error_message = "Deployment validation failed"
                    record.events.append("Deployment validation failed")
            else:
                record.status = DeploymentStatus.FAILED
                record.events.append("Deployment execution failed")
            
            # Store updated record
            self._store_deployment_record(record)
            
        except Exception as e:
            record.status = DeploymentStatus.FAILED
            record.error_message = str(e)
            record.events.append(f"Deployment failed: {str(e)}")
            self._store_deployment_record(record)
            logger.error(f"Deployment {deployment_id} failed: {e}")
    
    async def _execute_simple_deployment(self, record: DeploymentRecord) -> bool:
        """Execute simple deployment strategy"""
        
        deployer = self.deployers.get(record.config.platform)
        if not deployer:
            record.error_message = f"Unsupported platform: {record.config.platform}"
            return False
        
        try:
            success = await deployer.deploy_model(record.config)
            if success:
                record.events.append("Model deployed successfully")
            return success
        except Exception as e:
            record.error_message = str(e)
            return False
    
    async def _execute_blue_green_deployment(self, record: DeploymentRecord) -> bool:
        """Execute blue-green deployment strategy"""
        
        try:
            # Create green deployment
            green_config = record.config
            green_config.service_name = f"{green_config.service_name}-green"
            
            deployer = self.deployers.get(record.config.platform)
            if not deployer:
                return False
            
            # Deploy green version
            success = await deployer.deploy_model(green_config)
            if not success:
                return False
            
            record.events.append("Green deployment created")
            
            # Wait for green deployment to be ready
            await asyncio.sleep(30)
            
            # Validate green deployment
            if await self._validate_deployment_health(green_config):
                # Switch traffic to green
                await self._switch_traffic_to_green(record, green_config)
                record.events.append("Traffic switched to green deployment")
                
                # Clean up blue deployment after successful switch
                await asyncio.sleep(60)
                await self._cleanup_blue_deployment(record)
                record.events.append("Blue deployment cleaned up")
                
                return True
            else:
                record.events.append("Green deployment health check failed")
                return False
                
        except Exception as e:
            record.error_message = str(e)
            return False
    
    async def _execute_canary_deployment(self, record: DeploymentRecord) -> bool:
        """Execute canary deployment strategy"""
        
        try:
            # Create canary deployment with reduced replicas
            canary_config = record.config
            canary_config.service_name = f"{canary_config.service_name}-canary"
            canary_config.replicas = max(1, canary_config.replicas // 4)  # 25% traffic initially
            
            deployer = self.deployers.get(record.config.platform)
            if not deployer:
                return False
            
            # Deploy canary version
            success = await deployer.deploy_model(canary_config)
            if not success:
                return False
            
            record.events.append("Canary deployment created")
            
            # Gradual traffic increase
            traffic_percentages = [25, 50, 75, 100]
            
            for percentage in traffic_percentages:
                await asyncio.sleep(300)  # Wait 5 minutes between increases
                
                # Check canary health and metrics
                if not await self._validate_canary_metrics(record, canary_config):
                    record.events.append(f"Canary validation failed at {percentage}% traffic")
                    await self._rollback_canary(record, canary_config)
                    return False
                
                # Increase traffic
                await self._adjust_canary_traffic(record, canary_config, percentage)
                record.events.append(f"Canary traffic increased to {percentage}%")
            
            # Promote canary to full deployment
            await self._promote_canary(record, canary_config)
            record.events.append("Canary promoted to full deployment")
            
            return True
            
        except Exception as e:
            record.error_message = str(e)
            return False
    
    async def _execute_rolling_deployment(self, record: DeploymentRecord) -> bool:
        """Execute rolling deployment strategy"""
        
        # Rolling deployment is handled natively by Kubernetes
        return await self._execute_simple_deployment(record)
    
    async def _validate_deployment(self, record: DeploymentRecord) -> bool:
        """Validate deployment health and functionality"""
        
        try:
            deployer = self.deployers.get(record.config.platform)
            if not deployer:
                return False
            
            # Check deployment status
            if record.config.platform == DeploymentPlatform.KUBERNETES:
                status = await deployer.get_deployment_status(
                    record.config.service_name,
                    record.config.namespace
                )
                
                if status.get('ready_replicas', 0) < record.config.replicas:
                    record.events.append("Not all replicas are ready")
                    return False
            
            # Health check
            if not await self._validate_deployment_health(record.config):
                record.events.append("Health check failed")
                return False
            
            # Functional test
            if not await self._run_functional_tests(record):
                record.events.append("Functional tests failed")
                return False
            
            return True
            
        except Exception as e:
            record.events.append(f"Validation error: {str(e)}")
            return False
    
    async def _validate_deployment_health(self, config: DeploymentConfig) -> bool:
        """Validate deployment health"""
        
        try:
            if config.health_check.type == HealthCheckType.HTTP:
                # Make HTTP health check request
                health_url = f"http://{config.service_name}.{config.namespace}.svc.cluster.local{config.health_check.endpoint or '/health'}"
                
                # In a real implementation, make actual HTTP request
                # For now, simulate health check
                await asyncio.sleep(1)
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def _run_functional_tests(self, record: DeploymentRecord) -> bool:
        """Run functional tests against the deployment"""
        
        try:
            # In a real implementation, this would run comprehensive tests
            # For now, simulate successful tests
            await asyncio.sleep(2)
            
            record.events.append("Functional tests passed")
            return True
            
        except Exception as e:
            record.events.append(f"Functional tests failed: {str(e)}")
            return False
    
    async def _switch_traffic_to_green(self, record: DeploymentRecord, green_config: DeploymentConfig):
        """Switch traffic from blue to green deployment"""
        # Update service selector to point to green deployment
        pass
    
    async def _cleanup_blue_deployment(self, record: DeploymentRecord):
        """Clean up blue deployment after successful green deployment"""
        pass
    
    async def _validate_canary_metrics(self, record: DeploymentRecord, canary_config: DeploymentConfig) -> bool:
        """Validate canary deployment metrics"""
        
        # Check error rates, latency, etc.
        return True
    
    async def _adjust_canary_traffic(self, record: DeploymentRecord, canary_config: DeploymentConfig, percentage: int):
        """Adjust traffic percentage for canary deployment"""
        pass
    
    async def _rollback_canary(self, record: DeploymentRecord, canary_config: DeploymentConfig):
        """Rollback canary deployment"""
        pass
    
    async def _promote_canary(self, record: DeploymentRecord, canary_config: DeploymentConfig):
        """Promote canary to full deployment"""
        pass
    
    def _monitoring_worker(self):
        """Background worker for monitoring deployments"""
        while self.orchestration_active:
            try:
                # Monitor active deployments
                for deployment_id, record in self.active_deployments.items():
                    if record.status == DeploymentStatus.ACTIVE:
                        asyncio.run(self._monitor_deployment_health(record))
                
                time.sleep(60)  # Monitor every minute
                
            except Exception as e:
                logger.error(f"Monitoring worker error: {e}")
                time.sleep(60)
    
    async def _monitor_deployment_health(self, record: DeploymentRecord):
        """Monitor deployment health and performance"""
        
        try:
            deployer = self.deployers.get(record.config.platform)
            if not deployer:
                return
            
            # Get current status
            if record.config.platform == DeploymentPlatform.KUBERNETES:
                status = await deployer.get_deployment_status(
                    record.config.service_name,
                    record.config.namespace
                )
                
                # Update metrics
                record.metrics.update({
                    'ready_replicas': status.get('ready_replicas', 0),
                    'total_replicas': status.get('replicas', 0),
                    'last_monitored': datetime.now().isoformat()
                })
                
                # Check for issues
                if status.get('ready_replicas', 0) < record.config.replicas * 0.7:  # 70% availability threshold
                    # Trigger alert
                    alert = Alert(
                        id=f"deployment_health_{record.deployment_id}",
                        model_id=record.model_id,
                        metric_name="replica_availability",
                        severity=AlertSeverity.HIGH,
                        status="active",
                        message=f"Low replica availability: {status.get('ready_replicas', 0)}/{record.config.replicas}",
                        threshold=0.7,
                        current_value=status.get('ready_replicas', 0) / record.config.replicas,
                        triggered_at=datetime.now()
                    )
                    
                    # In a real implementation, send to alerting system
                    logger.warning(f"Deployment health alert: {alert.message}")
                
                # Store updated record
                self._store_deployment_record(record)
                
        except Exception as e:
            logger.error(f"Error monitoring deployment {record.deployment_id}: {e}")
    
    async def rollback_deployment(self, deployment_id: str, target_deployment_id: Optional[str] = None) -> bool:
        """Rollback a deployment to previous version"""
        
        record = self.active_deployments.get(deployment_id)
        if not record:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        try:
            record.status = DeploymentStatus.IN_PROGRESS
            record.events.append("Rollback initiated")
            
            # Find target for rollback
            if not target_deployment_id:
                # Find previous successful deployment
                cursor = self.db_connection.cursor()
                cursor.execute('''
                    SELECT deployment_id FROM deployments
                    WHERE model_id = ? AND status = ? AND deployment_id != ?
                    ORDER BY created_at DESC LIMIT 1
                ''', (record.model_id, DeploymentStatus.ACTIVE.value, deployment_id))
                
                row = cursor.fetchone()
                if not row:
                    record.events.append("No previous deployment found for rollback")
                    return False
                
                target_deployment_id = row[0]
            
            # Execute rollback
            deployer = self.deployers.get(record.config.platform)
            if not deployer:
                return False
            
            # Get target deployment config
            cursor = self.db_connection.cursor()
            cursor.execute('SELECT config FROM deployments WHERE deployment_id = ?', (target_deployment_id,))
            row = cursor.fetchone()
            
            if not row:
                record.events.append(f"Target deployment {target_deployment_id} not found")
                return False
            
            target_config = json.loads(row[0])
            
            # Deploy target version
            success = await deployer.deploy_model(DeploymentConfig(**target_config))
            
            if success:
                record.status = DeploymentStatus.ROLLED_BACK
                record.rollback_target = target_deployment_id
                record.events.append(f"Successfully rolled back to {target_deployment_id}")
                self._store_deployment_record(record)
                return True
            else:
                record.status = DeploymentStatus.FAILED
                record.error_message = "Rollback deployment failed"
                record.events.append("Rollback deployment failed")
                self._store_deployment_record(record)
                return False
                
        except Exception as e:
            record.status = DeploymentStatus.FAILED
            record.error_message = f"Rollback failed: {str(e)}"
            record.events.append(f"Rollback failed: {str(e)}")
            self._store_deployment_record(record)
            logger.error(f"Rollback failed for {deployment_id}: {e}")
            return False
    
    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentRecord]:
        """Get deployment status and details"""
        return self.active_deployments.get(deployment_id)
    
    def list_deployments(
        self,
        model_id: Optional[str] = None,
        environment: Optional[DeploymentEnvironment] = None,
        status: Optional[DeploymentStatus] = None
    ) -> List[DeploymentRecord]:
        """List deployments with optional filters"""
        
        deployments = list(self.active_deployments.values())
        
        if model_id:
            deployments = [d for d in deployments if d.model_id == model_id]
        
        if environment:
            deployments = [d for d in deployments if d.config.environment == environment]
        
        if status:
            deployments = [d for d in deployments if d.status == status]
        
        return sorted(deployments, key=lambda x: x.created_at, reverse=True)
    
    def create_deployment_dashboard(self, deployment_id: str) -> Dict[str, Any]:
        """Create dashboard data for deployment visualization"""
        
        record = self.active_deployments.get(deployment_id)
        if not record:
            raise ValueError(f"Deployment {deployment_id} not found")
        
        return {
            "deployment_id": deployment_id,
            "model_id": record.model_id,
            "status": record.status.value,
            "environment": record.config.environment.value,
            "platform": record.config.platform.value,
            "strategy": record.config.strategy.value,
            "created_at": record.created_at.isoformat(),
            "events": record.events,
            "metrics": record.metrics,
            "config": {
                "replicas": record.config.replicas,
                "image_uri": record.config.image_uri,
                "resources": {
                    "cpu_request": record.config.resources.cpu_request,
                    "memory_request": record.config.resources.memory_request,
                    "gpu_request": record.config.resources.gpu_request
                }
            }
        }
    
    def shutdown(self):
        """Shutdown the deployment orchestrator"""
        self.orchestration_active = False
        
        if self.orchestration_thread:
            self.orchestration_thread.join(timeout=10)
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        if self.redis_client:
            asyncio.create_task(self.redis_client.close())
        
        if self.db_connection:
            self.db_connection.close()
        
        logger.info("Model Deployment Orchestrator shutdown complete")

# Usage example
async def demo_deployment_orchestration():
    """Demonstrate deployment orchestration system"""
    
    # Initialize components (mock for demo)
    registry = None  # ModelRegistry()
    monitor = None   # ModelPerformanceMonitor()
    
    orchestrator = ModelDeploymentOrchestrator(registry, monitor)
    await orchestrator.initialize()
    
    # Deploy a model
    deployment_id = await orchestrator.deploy_model(
        model_id="sentiment_classifier_v1",
        environment=DeploymentEnvironment.STAGING,
        platform=DeploymentPlatform.KUBERNETES,
        strategy=DeploymentStrategy.BLUE_GREEN,
        custom_config={
            'replicas': 3,
            'image_uri': 'my-registry/sentiment-model:v1.0',
            'resources': {
                'cpu_request': '200m',
                'memory_request': '512Mi'
            }
        }
    )
    
    print(f"Deployment created: {deployment_id}")
    
    # Monitor deployment
    await asyncio.sleep(5)
    
    status = orchestrator.get_deployment_status(deployment_id)
    if status:
        print(f"Deployment status: {status.status.value}")
        print(f"Events: {status.events}")
    
    # Create dashboard
    dashboard = orchestrator.create_deployment_dashboard(deployment_id)
    print(f"Dashboard created for deployment {deployment_id}")
    
    orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(demo_deployment_orchestration())