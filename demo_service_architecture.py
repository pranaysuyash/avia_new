"""
Demo script showcasing the FastAPI service architecture foundation
"""

import asyncio
import time
import json
from typing import Dict, Any

# Import core components
from api.core import (
    BaseService,
    ServiceConfig,
    ServiceRequest,
    APIGateway,
    HealthChecker,
    MetricsCollector,
    setup_logging,
    get_logger
)

# Setup logging
logger = setup_logging(
    service_name="demo_service",
    log_level="INFO",
    log_format="json",
    enable_console=True
)

class DemoTranscriptionService(BaseService):
    """
    Demo transcription service showcasing the base service patterns
    """
    
    def __init__(self, config: ServiceConfig):
        super().__init__(config)
        self.processed_requests = 0
        self.mock_models = ["whisper-base", "whisper-large"]
    
    async def _initialize_service(self):
        """Initialize the transcription service"""
        self.logger.info("Initializing transcription models...")
        await asyncio.sleep(1)  # Simulate model loading
        self.logger.info("Transcription service initialized successfully")
    
    async def _shutdown_service(self):
        """Cleanup transcription service"""
        self.logger.info("Shutting down transcription service...")
        await asyncio.sleep(0.5)  # Simulate cleanup
        self.logger.info("Transcription service shutdown complete")
    
    async def _process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process transcription request"""
        # Simulate transcription processing
        audio_file = request.get("audio_file", "unknown.wav")
        model = request.get("model", "whisper-base")
        language = request.get("language", "auto")
        
        self.logger.info(
            f"Processing transcription request",
            extra={
                "audio_file": audio_file,
                "model": model,
                "language": language
            }
        )
        
        # Simulate processing time based on file size
        processing_time = request.get("file_size", 1000) / 1000  # seconds
        await asyncio.sleep(min(processing_time, 3))  # Max 3 seconds for demo
        
        # Generate mock transcription result
        result = {
            "transcription": f"This is a mock transcription of {audio_file}",
            "confidence": 0.95,
            "language_detected": language if language != "auto" else "en",
            "model_used": model,
            "processing_time": processing_time,
            "word_count": 42,
            "segments": [
                {
                    "start": 0.0,
                    "end": 2.5,
                    "text": "This is a mock transcription",
                    "confidence": 0.96
                },
                {
                    "start": 2.5,
                    "end": 4.0,
                    "text": f"of {audio_file}",
                    "confidence": 0.94
                }
            ]
        }
        
        self.processed_requests += 1
        return result
    
    async def _service_health_check(self) -> Dict[str, Any]:
        """Service-specific health check"""
        return {
            "models_loaded": len(self.mock_models),
            "requests_processed": self.processed_requests,
            "available_models": self.mock_models
        }

async def demo_base_service():
    """Demonstrate base service functionality"""
    print("\n" + "="*60)
    print("DEMO: Base Service Architecture")
    print("="*60)
    
    # Create service configuration
    config = ServiceConfig(
        name="demo_transcription_service",
        version="1.0.0",
        debug=True,
        timeout=10,
        max_retries=2,
        enable_metrics=True,
        enable_logging=True
    )
    
    # Create service instance
    service = DemoTranscriptionService(config)
    
    # Use service context manager
    async with service.service_context():
        print("✅ Service initialized successfully")
        
        # Create sample requests
        requests = [
            {
                "audio_file": "meeting_recording.wav",
                "model": "whisper-large",
                "language": "en",
                "file_size": 2000
            },
            {
                "audio_file": "interview.mp3",
                "model": "whisper-base",
                "language": "auto",
                "file_size": 1500
            },
            {
                "audio_file": "podcast.wav",
                "model": "whisper-large",
                "language": "es",
                "file_size": 3000
            }
        ]
        
        # Process requests
        for i, req_data in enumerate(requests, 1):
            print(f"\n📝 Processing request {i}/3...")
            
            # Create service request
            request = ServiceRequest(
                user_id=f"user_{i}",
                metadata=req_data
            )
            
            # Mock user context
            user_context = {
                "user_id": f"user_{i}",
                "authenticated": True,
                "is_active": True,
                "role": "premium"
            }
            
            # Process request
            start_time = time.time()
            response = await service.process(request, user_context)
            duration = time.time() - start_time
            
            # Display results
            if response.success:
                print(f"✅ Request processed successfully in {duration:.2f}s")
                print(f"   Transcription: {response.data['transcription'][:50]}...")
                print(f"   Confidence: {response.data['confidence']}")
                print(f"   Language: {response.data['language_detected']}")
            else:
                print(f"❌ Request failed: {response.message}")
        
        # Check service health
        print(f"\n🏥 Service Health Check:")
        health = await service.health_check()
        print(f"   Status: {health['status']}")
        print(f"   Models loaded: {health.get('models_loaded', 'N/A')}")
        print(f"   Requests processed: {health.get('requests_processed', 'N/A')}")

def demo_api_gateway():
    """Demonstrate API Gateway functionality"""
    print("\n" + "="*60)
    print("DEMO: API Gateway")
    print("="*60)
    
    # Create API Gateway
    gateway = APIGateway(
        title="Demo Transcription API",
        description="Demo API showcasing comprehensive middleware",
        version="1.0.0",
        debug=True
    )
    
    # Add custom route
    async def demo_endpoint():
        return {
            "message": "Hello from demo endpoint!",
            "timestamp": time.time(),
            "features": [
                "Authentication middleware",
                "Rate limiting",
                "Metrics collection",
                "Error handling",
                "Request validation"
            ]
        }
    
    gateway.add_route_handler("/demo", demo_endpoint, ["GET"])
    
    print("✅ API Gateway created with middleware stack:")
    print("   - CORS middleware")
    print("   - Request ID middleware")
    print("   - Timing middleware")
    print("   - Logging middleware")
    print("   - Error handling")
    
    print(f"\n📚 Available endpoints:")
    print("   GET /health - Basic health check")
    print("   GET /health/detailed - Detailed health check")
    print("   GET /metrics - Application metrics")
    print("   GET /demo - Demo endpoint")
    
    # Get FastAPI app
    app = gateway.get_app()
    print(f"\n🚀 FastAPI app ready: {app.title} v{app.version}")

def demo_health_checker():
    """Demonstrate health checking system"""
    print("\n" + "="*60)
    print("DEMO: Health Checker")
    print("="*60)
    
    # Create health checker
    health_checker = HealthChecker()
    
    # Add mock health checks
    async def database_check():
        await asyncio.sleep(0.1)  # Simulate DB query
        return {
            "status": "healthy",
            "connection_pool": "5/10 connections",
            "query_time": "0.05s"
        }
    
    async def redis_check():
        await asyncio.sleep(0.05)
        return {
            "status": "healthy",
            "memory_usage": "45MB",
            "connected_clients": 12
        }
    
    async def external_api_check():
        await asyncio.sleep(0.2)
        # Simulate occasional failure
        import random
        if random.random() > 0.8:
            return {
                "status": "unhealthy",
                "error": "Connection timeout"
            }
        return {
            "status": "healthy",
            "response_time": "0.15s"
        }
    
    # Add health checks
    health_checker.add_check("database", database_check, timeout=5, critical=True)
    health_checker.add_check("redis", redis_check, timeout=3, critical=False)
    health_checker.add_check("external_api", external_api_check, timeout=10, critical=False)
    
    print("✅ Health checks configured:")
    print("   - Database (critical)")
    print("   - Redis (non-critical)")
    print("   - External API (non-critical)")
    
    return health_checker

def demo_metrics_collector():
    """Demonstrate metrics collection"""
    print("\n" + "="*60)
    print("DEMO: Metrics Collector")
    print("="*60)
    
    # Create metrics collector
    metrics = MetricsCollector("demo_service")
    
    # Simulate some metrics
    print("📊 Collecting sample metrics...")
    
    # Counters
    for i in range(10):
        metrics.increment_counter("requests_total")
        metrics.increment_counter("requests_by_method.get", 1)
        if i % 3 == 0:
            metrics.increment_counter("requests_by_method.post", 1)
    
    # Gauges
    metrics.set_gauge("active_connections", 25)
    metrics.set_gauge("memory_usage_mb", 512.5)
    metrics.set_gauge("cpu_usage_percent", 45.2)
    
    # Histograms (response times)
    import random
    for _ in range(20):
        response_time = random.uniform(0.1, 2.0)
        metrics.record_histogram("response_time_seconds", response_time)
    
    # Timer example
    from api.core.metrics import timer
    with timer(metrics, "operation_duration"):
        time.sleep(0.1)  # Simulate operation
    
    print("✅ Metrics collected successfully")
    
    # Display metrics summary
    all_metrics = metrics.get_all_metrics()
    print(f"\n📈 Metrics Summary:")
    print(f"   Service: {all_metrics['service']}")
    print(f"   Uptime: {all_metrics['uptime']:.2f}s")
    print(f"   Total requests: {all_metrics['counters'].get('requests_total', 0)}")
    print(f"   Active connections: {all_metrics['gauges'].get('active_connections', 0)}")
    print(f"   Memory usage: {all_metrics['gauges'].get('memory_usage_mb', 0)}MB")
    
    # Response time statistics
    response_stats = metrics.get_histogram_stats("response_time_seconds")
    print(f"   Response time avg: {response_stats['avg']:.3f}s")
    print(f"   Response time p95: {response_stats['p95']:.3f}s")
    
    return metrics

async def demo_complete_integration():
    """Demonstrate complete service integration"""
    print("\n" + "="*60)
    print("DEMO: Complete Integration")
    print("="*60)
    
    # Setup health checker
    health_checker = demo_health_checker()
    
    # Setup metrics
    metrics = demo_metrics_collector()
    
    # Run health checks
    print(f"\n🏥 Running comprehensive health check...")
    health_result = await health_checker.check_all()
    
    print(f"   Overall status: {health_result['status']}")
    print(f"   Checks completed: {health_result['summary']['total_checks']}")
    print(f"   Success rate: {health_result['summary']['success_rate']:.1f}%")
    
    # Display individual check results
    for check_name, result in health_result['checks'].items():
        status_emoji = "✅" if result['status'] == 'healthy' else "❌"
        print(f"   {status_emoji} {check_name}: {result['status']}")
    
    print(f"\n📊 Final metrics snapshot:")
    final_metrics = metrics.get_all_metrics()
    print(f"   Total counters: {len(final_metrics['counters'])}")
    print(f"   Total gauges: {len(final_metrics['gauges'])}")
    print(f"   Total histograms: {len(final_metrics['histograms'])}")

async def main():
    """Run all demos"""
    print("🚀 FastAPI Service Architecture Foundation Demo")
    print("=" * 80)
    
    try:
        # Run individual demos
        await demo_base_service()
        demo_api_gateway()
        demo_health_checker()
        demo_metrics_collector()
        
        # Run integration demo
        await demo_complete_integration()
        
        print("\n" + "="*80)
        print("✅ All demos completed successfully!")
        print("="*80)
        
        print(f"\n📋 Summary of implemented features:")
        features = [
            "✅ Base service class with common patterns",
            "✅ Unified API gateway with middleware",
            "✅ Comprehensive authentication & validation",
            "✅ Error handling with structured responses",
            "✅ Health checking system",
            "✅ Metrics collection & monitoring",
            "✅ Structured logging with JSON format",
            "✅ OpenAPI documentation generation",
            "✅ Rate limiting middleware",
            "✅ Request/response validation"
        ]
        
        for feature in features:
            print(f"   {feature}")
        
        print(f"\n🔗 Next steps:")
        print("   1. Run the production app: uvicorn api.production_app:app --reload")
        print("   2. View API docs: http://localhost:8000/api/docs")
        print("   3. Check health: http://localhost:8000/health/detailed")
        print("   4. View metrics: http://localhost:8000/metrics")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}", exc_info=True)
        print(f"\n❌ Demo failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())