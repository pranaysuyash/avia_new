"""
Main FastAPI application setup
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import os
import asyncio
from typing import Dict, Any

from .auth_router import auth_router
from .transcripts import transcripts_router
from .teams import teams_router
from .media import media_router
from .users import users_router
from .websocket_routes import websocket_router
from .middleware import RateLimitMiddleware, create_rate_limiter
from .middleware.monitoring_middleware import (
    MonitoringMiddleware,
    ErrorLoggingMiddleware,
    SlowRequestLoggingMiddleware,
    SecurityLoggingMiddleware
)
from .middleware.audit_middleware import AuditMiddleware
from .middleware.api_auth_middleware import APIAuthMiddleware
from .exceptions import APIException
from database import init_db

# Import new endpoint routers
from .endpoints.transcription import router as transcription_router
from .endpoints.analytics import router as analytics_router
from .endpoints.history import router as history_router
from .endpoints.queue import router as queue_router
from .endpoints.settings import router as settings_router
from .endpoints.export import router as export_router
from .endpoints.search import router as search_router
from .endpoints.files import router as files_router
from .endpoints.auth_endpoints import router as auth_endpoints_router
from .endpoints.monitoring import router as monitoring_router
from .endpoints.subscription import router as subscription_router
from .endpoints.transcription_rbac import router as transcription_rbac_router
from .endpoints.usage_analytics import router as usage_analytics_router
from .endpoints.admin import router as admin_router
from .endpoints.audit import router as audit_router
from .endpoints.developers import router as developers_router
from .endpoints.structured_analysis import router as structured_analysis_router
from .endpoints.content_insights import router as content_insights_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting API server...")
    init_db()
    
    # Initialize pricing plans
    try:
        from services.subscription_service import SubscriptionService
        from database.connection import get_db
        subscription_service = SubscriptionService(get_db)
        subscription_service.initialize_pricing_plans()
        logger.info("Pricing plans initialized")
    except Exception as e:
        logger.error(f"Failed to initialize pricing plans: {e}")
    
    # Start WebSocket manager if using enhanced version
    if os.getenv('USE_ENHANCED_WEBSOCKET', 'true').lower() == 'true':
        from websocket.enhanced_server import enhanced_websocket_manager
        await enhanced_websocket_manager.start()
        logger.info("Enhanced WebSocket manager started")
    
    # Start monitoring services
    try:
        from services.system_monitoring_service import monitoring_service
        asyncio.create_task(monitoring_service.monitor_continuously())
        logger.info("System monitoring service started")
    except Exception as e:
        logger.error(f"Failed to start monitoring service: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down API server...")
    
    # Stop monitoring services
    logger.info("Monitoring services stopped")
    
    # Stop WebSocket manager
    if os.getenv('USE_ENHANCED_WEBSOCKET', 'true').lower() == 'true':
        from websocket.enhanced_server import enhanced_websocket_manager
        await enhanced_websocket_manager.stop()
        logger.info("Enhanced WebSocket manager stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Audio/Video Transcription API",
        description="REST API for audio/video transcription with collaboration features",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan
    )
    
    # Add middlewares
    # Enhanced CORS configuration with specific origins for different environments
    origins = [
        "http://localhost:3000",      # React development
        "http://localhost:3001",      # React development alt
        "http://localhost:8000",      # FastAPI
        "http://localhost:5173",      # Vite development
        "http://127.0.0.1:3000",      # Alternative localhost
        "http://127.0.0.1:8000",      # Alternative API
        "file://",                    # Electron file protocol
        "capacitor://localhost",       # Capacitor for mobile
        "ionic://localhost",          # Ionic for mobile
        "http://localhost",           # Generic localhost
    ]
    
    # Add production origins if in production environment
    if os.getenv("ENVIRONMENT") == "production":
        origins.extend([
            "https://yourdomain.com",  # Replace with actual domain
            "https://www.yourdomain.com",
        ])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Access-Control-Allow-Origin"],
    )
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure based on environment
    )
    
    # Monitoring middleware (added first to capture all requests)
    app.add_middleware(
        MonitoringMiddleware,
        skip_paths=['/health', '/metrics', '/docs', '/openapi.json'],
        log_request_body=False,
        log_response_body=True,
        max_body_log_size=1024
    )
    
    # Error and security logging
    app.add_middleware(ErrorLoggingMiddleware)
    app.add_middleware(SlowRequestLoggingMiddleware, threshold_ms=1000)
    app.add_middleware(SecurityLoggingMiddleware)
    
    # Custom middlewares - Use advanced rate limiting
    from api.middleware.advanced_rate_limit_middleware import create_advanced_rate_limit_middleware
    app.add_middleware(create_advanced_rate_limit_middleware(enabled=True))
    app.add_middleware(AuditMiddleware)
    app.add_middleware(APIAuthMiddleware)
    
    # Exception handlers
    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.error_code,
                "message": exc.message,
                "details": exc.details
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An internal error occurred"
            }
        )
    
    # Root endpoint
    @app.get("/api/v1")
    async def root():
        return {
            "name": "Audio/Video Transcription API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/api/docs"
        }
    
    # Health check (accessible from both v1 and direct API routes)
    @app.get("/api/v1/health")
    @app.get("/api/health")
    async def health_check():
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "service": "api"
        }
    
    # Include routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
    app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
    app.include_router(transcripts_router, prefix="/api/v1/transcripts", tags=["Transcripts"])
    app.include_router(teams_router, prefix="/api/v1/teams", tags=["Teams"])
    app.include_router(media_router, prefix="/api/v1/media", tags=["Media"])
    
    # Use enhanced WebSocket if enabled
    if os.getenv('USE_ENHANCED_WEBSOCKET', 'true').lower() == 'true':
        from .websocket_routes_enhanced import websocket_router as enhanced_ws_router
        app.include_router(enhanced_ws_router, prefix="/api/v1", tags=["WebSocket"])
    else:
        app.include_router(websocket_router, prefix="/api/v1", tags=["WebSocket"])
    
    # Include new endpoint routers
    app.include_router(auth_endpoints_router, prefix="/api", tags=["Authentication"])
    app.include_router(transcription_router, prefix="/api")
    app.include_router(analytics_router, prefix="/api")
    app.include_router(history_router, prefix="/api")
    app.include_router(queue_router, prefix="/api")
    app.include_router(settings_router, prefix="/api")
    app.include_router(export_router, prefix="/api")
    app.include_router(search_router, prefix="/api")
    app.include_router(files_router, prefix="/api")
    app.include_router(monitoring_router, prefix="/api", tags=["Monitoring"])
    app.include_router(subscription_router, tags=["Subscriptions"])
    app.include_router(transcription_rbac_router, tags=["Transcripts"])
    app.include_router(usage_analytics_router, tags=["Usage Analytics"])
    app.include_router(admin_router, tags=["Admin"])
    app.include_router(audit_router, tags=["Audit"])
    app.include_router(developers_router, tags=["Developers"])
    app.include_router(structured_analysis_router, prefix="/api", tags=["Structured Analysis"])
    app.include_router(content_insights_router, prefix="/api", tags=["Content Insights"])
    
    # Include new feature routers
    from .endpoints.enterprise_sales import router as sales_router
    from .endpoints.customer_support import router as support_router
    from .endpoints.compliance_security import router as compliance_router
    from .endpoints.api_platform import router as api_platform_router
    from .endpoints.marketing_growth import router as marketing_router
    
    app.include_router(sales_router, tags=["Enterprise Sales"])
    app.include_router(support_router, tags=["Customer Support"])
    app.include_router(compliance_router, tags=["Compliance & Security"])
    app.include_router(api_platform_router, tags=["API Platform"])
    app.include_router(marketing_router, tags=["Marketing & Growth"])
    
    # Include core functionality routers
    from .endpoints.tts import router as tts_router
    from .endpoints.audio_enhancement import router as audio_router
    from .endpoints.ocr import router as ocr_router
    from .endpoints.collaboration import router as collaboration_router
    from .endpoints.ner import router as ner_router
    from .endpoints.ai_customization import router as ai_customization_router
    from .endpoints.usage import router as usage_router
    from .endpoints.data_retention import router as data_retention_router
    
    app.include_router(tts_router, tags=["Text-to-Speech"])
    app.include_router(audio_router, tags=["Audio Enhancement"])
    app.include_router(ocr_router, tags=["OCR"])
    app.include_router(collaboration_router, tags=["Collaboration"])
    app.include_router(ner_router, tags=["Named Entity Recognition"])
    app.include_router(ai_customization_router, tags=["AI Customization"])
    app.include_router(usage_router, tags=["Usage Tracking"])
    app.include_router(data_retention_router, tags=["Data Retention"])
    
    # Include image annotation router
    from .endpoints.annotation import router as annotation_router
    app.include_router(annotation_router, prefix="/api", tags=["Image Annotation"])
    
    # Include entity extraction router
    from .endpoints.entity_extraction import router as entity_extraction_router
    app.include_router(entity_extraction_router, tags=["Entity Extraction"])
    
    # Include document analysis router
    from .endpoints.document_analysis import router as document_analysis_router
    app.include_router(document_analysis_router, tags=["Document Analysis"])
    
    # Include notifications router
    from .endpoints.notifications import router as notifications_router
    app.include_router(notifications_router, tags=["Notifications"])
    
    # Include LLM providers router
    from .endpoints.llm_providers import router as llm_providers_router
    app.include_router(llm_providers_router, tags=["LLM Providers"])
    
    # Include marketplace router
    from .endpoints.marketplace import router as marketplace_router
    app.include_router(marketplace_router, tags=["Marketplace"])
    
    # Include AI dubbing router
    from .endpoints.ai_dubbing import router as ai_dubbing_router
    app.include_router(ai_dubbing_router, tags=["AI Dubbing"])
    
    # Include unified media router
    from .endpoints.unified_media import router as unified_media_router
    app.include_router(unified_media_router, prefix="/api", tags=["Unified Media"])
    
    # Include backup management router
    from api.endpoints.backup import router as backup_router
    app.include_router(backup_router, tags=["Backup"])
    
    # Include rate limiting management router
    from api.endpoints.rate_limiting import router as rate_limiting_router
    app.include_router(rate_limiting_router, tags=["Rate Limiting"])
    
    # Include GraphQL endpoint
    from api.endpoints.graphql_endpoint import router as graphql_router
    app.include_router(graphql_router, tags=["GraphQL"])
    
    # Include GDPR compliance router
    from api.endpoints.gdpr_compliance import router as gdpr_router
    app.include_router(gdpr_router, tags=["GDPR Compliance"])
    
    # Include comprehensive search router
    from api.endpoints.comprehensive_search import router as comprehensive_search_router
    app.include_router(comprehensive_search_router, tags=["Comprehensive Search"])
    
    # Include real-time collaboration router
    from api.endpoints.realtime_collaboration import router as realtime_collaboration_router
    app.include_router(realtime_collaboration_router, tags=["Real-time Collaboration"])
    
    # Include advanced analytics router
    from api.endpoints.advanced_analytics import router as advanced_analytics_router
    app.include_router(advanced_analytics_router, tags=["Advanced Analytics"])
    
    # Include AI suggestions router
    from api.endpoints.ai_suggestions import router as ai_suggestions_router
    app.include_router(ai_suggestions_router, tags=["AI Suggestions"])
    
    # Include hybrid summarization router
    from api.endpoints.hybrid_summarization import router as hybrid_summarization_router
    app.include_router(hybrid_summarization_router, prefix="/api/v1", tags=["Hybrid Summarization"])
    
    # Include real-time transcription router
    from api.endpoints.realtime_transcription import router as realtime_transcription_router
    app.include_router(realtime_transcription_router, prefix="/api/v1", tags=["Real-time Transcription"])
    
    # Include voice activity detection router
    from api.endpoints.voice_activity_detection import router as vad_router
    app.include_router(vad_router, prefix="/api/v1", tags=["Voice Activity Detection"])
    
    # Include advanced timestamping router
    from api.endpoints.advanced_timestamping import router as timestamping_router
    app.include_router(timestamping_router, prefix="/api/v1", tags=["Advanced Timestamping"])
    
    # Include emotion/sentiment detection router
    from api.endpoints.emotion_sentiment_detection import router as emotion_sentiment_router
    app.include_router(emotion_sentiment_router, prefix="/api/v1", tags=["Emotion & Sentiment Detection"])
    
    # Include speech pattern analysis router
    from api.endpoints.speech_pattern_analysis import router as speech_pattern_router
    app.include_router(speech_pattern_router, prefix="/api/v1", tags=["Speech Pattern Analysis"])
    
    # Include custom vocabulary router
    from api.endpoints.custom_vocabulary import router as custom_vocabulary_router
    app.include_router(custom_vocabulary_router, prefix="/api/v1", tags=["Custom Vocabulary"])
    
    # Include audio enhancement router
    from api.endpoints.audio_enhancement import router as audio_enhancement_router
    app.include_router(audio_enhancement_router, prefix="/api/v1", tags=["Audio Enhancement"])
    
    # Include Whisper advanced router
    from api.endpoints.whisper_advanced import router as whisper_advanced_router
    app.include_router(whisper_advanced_router, prefix="/api/v1", tags=["Whisper Advanced"])
    
    # Include internationalization router
    from api.endpoints.internationalization import router as i18n_router
    app.include_router(i18n_router, tags=["Internationalization"])
    
    # Include audio enhancement router
    from api.endpoints.audio_enhancement import router as audio_enhancement_router
    app.include_router(audio_enhancement_router, prefix="/api/v1", tags=["Audio Enhancement"])
    
    # Include Smart B-Roll router
    from api.endpoints.smart_broll import router as smart_broll_router
    app.include_router(smart_broll_router, tags=["Smart B-Roll"])
    
    # Admin monitoring WebSocket
    from api.websocket.admin_monitoring_ws import admin_monitoring_endpoint
    app.websocket("/api/ws/admin/monitoring")(admin_monitoring_endpoint)
    
    # Add OpenAPI documentation enhancements
    from api.openapi_schema import add_api_documentation
    app = add_api_documentation(app)
    
    return app


# Create app instance
app = create_app()