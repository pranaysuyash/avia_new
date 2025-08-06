"""
Developer Platform Package

Comprehensive API and developer tools for the transcription platform including:
- API Gateway with authentication and rate limiting
- GraphQL API for flexible queries
- SDK generation for multiple languages
- API documentation and interactive explorer
- Usage monitoring and analytics
"""

from .api_gateway import (
    APIGateway,
    APIKey,
    APIKeyType,
    APIKeyStatus,
    RateLimitPlan,
    WebhookEvent,
    WebhookEndpoint,
    RateLimiter,
    api_key_required
)

from .graphql_api import (
    schema as graphql_schema,
    Query,
    Mutations,
    Subscription,
    GraphQLHandler,
    TranscriptionObject,
    EntityObject,
    SummaryObject,
    UsageStatistics
)

from .sdk_generator import (
    SDKGenerator,
    SDKLanguage,
    SDKConfig,
    APIEndpoint
)

from .api_documentation import (
    APIDocumentationGenerator,
    APIExplorer,
    DocFormat,
    APIEndpointDoc,
    APIParameter,
    APIResponse
)

from .api_monitoring import (
    APIMonitor,
    APIMetric,
    MetricType,
    PerformanceMetrics,
    UsageQuota,
    Alert,
    AlertRule,
    AlertSeverity,
    TimeGranularity
)

__version__ = "1.0.0"

__all__ = [
    # API Gateway
    "APIGateway",
    "APIKey",
    "APIKeyType",
    "APIKeyStatus",
    "RateLimitPlan",
    "WebhookEvent",
    "WebhookEndpoint",
    "RateLimiter",
    "api_key_required",
    
    # GraphQL
    "graphql_schema",
    "Query",
    "Mutations",
    "Subscription",
    "GraphQLHandler",
    "TranscriptionObject",
    "EntityObject",
    "SummaryObject",
    "UsageStatistics",
    
    # SDK Generator
    "SDKGenerator",
    "SDKLanguage",
    "SDKConfig",
    "APIEndpoint",
    
    # Documentation
    "APIDocumentationGenerator",
    "APIExplorer",
    "DocFormat",
    "APIEndpointDoc",
    "APIParameter",
    "APIResponse",
    
    # Monitoring
    "APIMonitor",
    "APIMetric",
    "MetricType",
    "PerformanceMetrics",
    "UsageQuota",
    "Alert",
    "AlertRule",
    "AlertSeverity",
    "TimeGranularity"
]