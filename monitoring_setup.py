"""
Monitoring and Observability Setup
Sets up comprehensive monitoring for all production services
"""

import os
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from prometheus_client.core import CollectorRegistry
import sentry_sdk
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

# DataDog integration
try:
    from datadog import initialize, statsd
    HAS_DATADOG = True
except ImportError:
    HAS_DATADOG = False

# OpenTelemetry
from opentelemetry import trace, metrics
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


@dataclass
class MonitoringConfig:
    """Monitoring configuration"""
    sentry_dsn: str = os.getenv('SENTRY_DSN', '')
    datadog_api_key: str = os.getenv('DATADOG_API_KEY', '')
    prometheus_port: int = int(os.getenv('PROMETHEUS_PORT', '9090'))
    otlp_endpoint: str = os.getenv('OTLP_ENDPOINT', 'localhost:4317')
    environment: str = os.getenv('APP_ENV', 'production')


class MonitoringService:
    """Centralized monitoring service"""
    
    def __init__(self, config: MonitoringConfig = None):
        self.config = config or MonitoringConfig()
        self.registry = CollectorRegistry()
        
        # Initialize metrics
        self._init_metrics()
        
        # Initialize error tracking
        self._init_sentry()
        
        # Initialize APM
        self._init_datadog()
        
        # Initialize tracing
        self._init_opentelemetry()
    
    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        
        # Payment metrics
        self.payment_success = Counter(
            'payment_success_total',
            'Total successful payments',
            ['provider', 'currency'],
            registry=self.registry
        )
        
        self.payment_failure = Counter(
            'payment_failure_total',
            'Total failed payments',
            ['provider', 'currency', 'error_type'],
            registry=self.registry
        )
        
        self.payment_latency = Histogram(
            'payment_processing_seconds',
            'Payment processing time',
            ['provider'],
            registry=self.registry
        )
        
        # Transcription metrics
        self.transcription_success = Counter(
            'transcription_success_total',
            'Total successful transcriptions',
            ['engine', 'language'],
            registry=self.registry
        )
        
        self.transcription_failure = Counter(
            'transcription_failure_total',
            'Total failed transcriptions',
            ['engine', 'error_type'],
            registry=self.registry
        )
        
        self.transcription_duration = Histogram(
            'transcription_duration_seconds',
            'Transcription processing time',
            ['engine'],
            buckets=[5, 10, 30, 60, 120, 300, 600],
            registry=self.registry
        )
        
        # Translation metrics
        self.translation_requests = Counter(
            'translation_requests_total',
            'Total translation requests',
            ['provider', 'source_lang', 'target_lang'],
            registry=self.registry
        )
        
        self.translation_latency = Histogram(
            'translation_latency_seconds',
            'Translation API latency',
            ['provider'],
            registry=self.registry
        )
        
        # Cache metrics
        self.cache_hits = Counter(
            'cache_hits_total',
            'Cache hit count',
            ['cache_type', 'namespace'],
            registry=self.registry
        )
        
        self.cache_misses = Counter(
            'cache_misses_total',
            'Cache miss count',
            ['cache_type', 'namespace'],
            registry=self.registry
        )
        
        self.cache_size = Gauge(
            'cache_size_bytes',
            'Current cache size',
            ['cache_type'],
            registry=self.registry
        )
        
        # Storage metrics
        self.storage_usage = Gauge(
            'storage_usage_bytes',
            'Storage usage by provider',
            ['provider', 'bucket'],
            registry=self.registry
        )
        
        self.storage_operations = Counter(
            'storage_operations_total',
            'Storage operations',
            ['provider', 'operation'],
            registry=self.registry
        )
        
        # Support metrics
        self.tickets_created = Counter(
            'support_tickets_created_total',
            'Support tickets created',
            ['priority', 'category'],
            registry=self.registry
        )
        
        self.ticket_resolution_time = Histogram(
            'ticket_resolution_hours',
            'Time to resolve tickets',
            ['priority'],
            buckets=[1, 4, 8, 24, 48, 168],
            registry=self.registry
        )
        
        # GDPR metrics
        self.gdpr_exports = Counter(
            'gdpr_exports_total',
            'GDPR data exports',
            ['export_type'],
            registry=self.registry
        )
        
        self.gdpr_deletions = Counter(
            'gdpr_deletions_total',
            'GDPR data deletions',
            registry=self.registry
        )
        
        # Backup metrics
        self.backup_success = Counter(
            'backup_success_total',
            'Successful backups',
            ['backup_type', 'destination'],
            registry=self.registry
        )
        
        self.backup_failure = Counter(
            'backup_failure_total',
            'Failed backups',
            ['backup_type', 'error_type'],
            registry=self.registry
        )
        
        self.backup_size = Gauge(
            'backup_size_bytes',
            'Backup size',
            ['backup_type'],
            registry=self.registry
        )
    
    def _init_sentry(self):
        """Initialize Sentry error tracking"""
        if self.config.sentry_dsn:
            sentry_sdk.init(
                dsn=self.config.sentry_dsn,
                environment=self.config.environment,
                integrations=[
                    SqlalchemyIntegration(),
                    RedisIntegration()
                ],
                traces_sample_rate=0.1,
                profiles_sample_rate=0.1
            )
    
    def _init_datadog(self):
        """Initialize DataDog APM"""
        if HAS_DATADOG and self.config.datadog_api_key:
            initialize(
                api_key=self.config.datadog_api_key,
                app_key=os.getenv('DATADOG_APP_KEY')
            )
    
    def _init_opentelemetry(self):
        """Initialize OpenTelemetry tracing"""
        # Set up tracer provider
        trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer(__name__)
        
        # Configure OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=self.config.otlp_endpoint,
            insecure=True
        )
        
        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        trace.get_tracer_provider().add_span_processor(span_processor)
        
        self.tracer = tracer
    
    # Payment monitoring
    def record_payment_success(self, provider: str, currency: str, amount: float):
        """Record successful payment"""
        self.payment_success.labels(provider=provider, currency=currency).inc()
        
        if HAS_DATADOG:
            statsd.increment('payment.success', tags=[f'provider:{provider}', f'currency:{currency}'])
            statsd.histogram('payment.amount', amount, tags=[f'provider:{provider}', f'currency:{currency}'])
    
    def record_payment_failure(self, provider: str, currency: str, error_type: str):
        """Record failed payment"""
        self.payment_failure.labels(
            provider=provider,
            currency=currency,
            error_type=error_type
        ).inc()
        
        if HAS_DATADOG:
            statsd.increment('payment.failure', tags=[
                f'provider:{provider}',
                f'currency:{currency}',
                f'error:{error_type}'
            ])
    
    # Transcription monitoring
    def record_transcription_success(self, engine: str, language: str, duration: float):
        """Record successful transcription"""
        self.transcription_success.labels(engine=engine, language=language).inc()
        self.transcription_duration.labels(engine=engine).observe(duration)
        
        if HAS_DATADOG:
            statsd.increment('transcription.success', tags=[f'engine:{engine}', f'language:{language}'])
            statsd.histogram('transcription.duration', duration, tags=[f'engine:{engine}'])
    
    def record_transcription_failure(self, engine: str, error_type: str):
        """Record failed transcription"""
        self.transcription_failure.labels(engine=engine, error_type=error_type).inc()
        
        if HAS_DATADOG:
            statsd.increment('transcription.failure', tags=[f'engine:{engine}', f'error:{error_type}'])
    
    # Cache monitoring
    def record_cache_hit(self, cache_type: str, namespace: str = 'default'):
        """Record cache hit"""
        self.cache_hits.labels(cache_type=cache_type, namespace=namespace).inc()
        
        if HAS_DATADOG:
            statsd.increment('cache.hit', tags=[f'type:{cache_type}', f'namespace:{namespace}'])
    
    def record_cache_miss(self, cache_type: str, namespace: str = 'default'):
        """Record cache miss"""
        self.cache_misses.labels(cache_type=cache_type, namespace=namespace).inc()
        
        if HAS_DATADOG:
            statsd.increment('cache.miss', tags=[f'type:{cache_type}', f'namespace:{namespace}'])
    
    def update_cache_size(self, cache_type: str, size_bytes: int):
        """Update cache size gauge"""
        self.cache_size.labels(cache_type=cache_type).set(size_bytes)
        
        if HAS_DATADOG:
            statsd.gauge('cache.size', size_bytes, tags=[f'type:{cache_type}'])
    
    # Support monitoring
    def record_ticket_created(self, priority: str, category: str):
        """Record support ticket creation"""
        self.tickets_created.labels(priority=priority, category=category).inc()
        
        if HAS_DATADOG:
            statsd.increment('support.ticket.created', tags=[f'priority:{priority}', f'category:{category}'])
    
    def record_ticket_resolved(self, priority: str, resolution_hours: float):
        """Record ticket resolution"""
        self.ticket_resolution_time.labels(priority=priority).observe(resolution_hours)
        
        if HAS_DATADOG:
            statsd.histogram('support.resolution_time', resolution_hours, tags=[f'priority:{priority}'])
    
    # GDPR monitoring
    def record_gdpr_export(self, export_type: str):
        """Record GDPR export"""
        self.gdpr_exports.labels(export_type=export_type).inc()
        
        if HAS_DATADOG:
            statsd.increment('gdpr.export', tags=[f'type:{export_type}'])
    
    def record_gdpr_deletion(self):
        """Record GDPR deletion"""
        self.gdpr_deletions.inc()
        
        if HAS_DATADOG:
            statsd.increment('gdpr.deletion')
    
    # Backup monitoring
    def record_backup_success(self, backup_type: str, destination: str, size_bytes: int):
        """Record successful backup"""
        self.backup_success.labels(backup_type=backup_type, destination=destination).inc()
        self.backup_size.labels(backup_type=backup_type).set(size_bytes)
        
        if HAS_DATADOG:
            statsd.increment('backup.success', tags=[f'type:{backup_type}', f'destination:{destination}'])
            statsd.gauge('backup.size', size_bytes, tags=[f'type:{backup_type}'])
    
    def record_backup_failure(self, backup_type: str, error_type: str):
        """Record failed backup"""
        self.backup_failure.labels(backup_type=backup_type, error_type=error_type).inc()
        
        if HAS_DATADOG:
            statsd.increment('backup.failure', tags=[f'type:{backup_type}', f'error:{error_type}'])
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics"""
        return generate_latest(self.registry)
    
    def create_dashboard_config(self) -> Dict[str, Any]:
        """Create Grafana dashboard configuration"""
        return {
            "dashboard": {
                "title": "Production Services Monitoring",
                "panels": [
                    {
                        "title": "Payment Success Rate",
                        "targets": [{
                            "expr": "rate(payment_success_total[5m]) / (rate(payment_success_total[5m]) + rate(payment_failure_total[5m]))"
                        }]
                    },
                    {
                        "title": "Transcription Processing Time",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, rate(transcription_duration_seconds_bucket[5m]))"
                        }]
                    },
                    {
                        "title": "Cache Hit Ratio",
                        "targets": [{
                            "expr": "sum(rate(cache_hits_total[5m])) / (sum(rate(cache_hits_total[5m])) + sum(rate(cache_misses_total[5m])))"
                        }]
                    },
                    {
                        "title": "Support Ticket SLA",
                        "targets": [{
                            "expr": "histogram_quantile(0.95, rate(ticket_resolution_hours_bucket[1d]))"
                        }]
                    }
                ]
            }
        }


# Global monitoring instance
monitoring = MonitoringService()


# FastAPI middleware for automatic metrics
from fastapi import Request, Response
import time

async def metrics_middleware(request: Request, call_next):
    """Middleware to track API metrics"""
    start_time = time.time()
    
    response = await call_next(request)
    
    # Record request duration
    duration = time.time() - start_time
    
    if HAS_DATADOG:
        statsd.histogram(
            'api.request.duration',
            duration,
            tags=[
                f'method:{request.method}',
                f'path:{request.url.path}',
                f'status:{response.status_code}'
            ]
        )
    
    return response


# Health check endpoint
from fastapi import FastAPI

def add_monitoring_endpoints(app: FastAPI):
    """Add monitoring endpoints to FastAPI app"""
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=monitoring.get_metrics(),
            media_type="text/plain"
        )
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": monitoring.config.environment
        }
    
    @app.get("/ready")
    async def readiness_check():
        """Readiness check endpoint"""
        # Check critical services
        checks = {
            "database": check_database(),
            "redis": check_redis(),
            "storage": check_storage()
        }
        
        all_ready = all(checks.values())
        
        return {
            "ready": all_ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }


def check_database() -> bool:
    """Check database connectivity"""
    try:
        from api.database import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        return True
    except:
        return False


def check_redis() -> bool:
    """Check Redis connectivity"""
    try:
        from api.cache.redis_cache import redis_cache
        return redis_cache.is_connected()
    except:
        return False


def check_storage() -> bool:
    """Check storage availability"""
    try:
        from services.storage_service import StorageService
        storage = StorageService()
        # Try to list files in a test directory
        storage.list_files(prefix="health_check/")
        return True
    except:
        return False