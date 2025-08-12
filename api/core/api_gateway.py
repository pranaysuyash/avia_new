"""
Unified API Gateway with request routing and middleware
"""

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, List, Optional, Callable, Any
import time
import uuid
from datetime import datetime

from .logging import get_logger
from .metrics import MetricsCollector
from .health import HealthChecker

logger = get_logger("api_gateway")

class APIGateway:
    """
    Unified API Gateway that provides:
    - Request routing
    - Middleware management
    - Authentication and authorization
    - Rate limiting
    - Logging and metrics
    - Error handling
    """
    
    def __init__(
        self,
        title: str = "Production API Gateway",
        description: str = "Enterprise-grade API Gateway with comprehensive middleware",
        version: str = "1.0.0",
        debug: bool = False
    ):
        self.app = FastAPI(
            title=title,
            description=description,
            version=version,
            debug=debug,
            docs_url="/api/docs",
            redoc_url="/api/redoc"
        )
        
        self.metrics = MetricsCollector("api_gateway")
        self.health_checker = HealthChecker()
        self.middleware_stack = []
        self.route_handlers = {}
        
        # Setup core middleware
        self._setup_core_middleware()
        self._setup_error_handlers()
        self._setup_health_endpoints()
    
    def _setup_core_middleware(self):
        """Setup core middleware stack"""
        
        # CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure based on environment
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Request ID middleware
        @self.app.middleware("http")
        async def add_request_id(request: Request, call_next):
            request_id = str(uuid.uuid4())
            request.state.request_id = request_id
            
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Timing middleware
        @self.app.middleware("http")
        async def add_process_time(request: Request, call_next):
            start_time = time.time()
            response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Process-Time"] = str(process_time)
            
            # Record metrics
            self.metrics.record_histogram("request_duration", process_time)
            return response
        
        # Logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.info(
                f"Request started: {request.method} {request.url.path}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "client_ip": request.client.host
                }
            )
            
            response = await call_next(request)
            
            logger.info(
                f"Request completed: {response.status_code}",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code
                }
            )
            
            return response
    
    def _setup_error_handlers(self):
        """Setup global error handlers"""
        
        @self.app.exception_handler(HTTPException)
        async def http_exception_handler(request: Request, exc: HTTPException):
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.warning(
                f"HTTP exception: {exc.status_code} - {exc.detail}",
                extra={"request_id": request_id}
            )
            
            self.metrics.increment_counter(f"http_errors.{exc.status_code}")
            
            return JSONResponse(
                status_code=exc.status_code,
                content={
                    "error": {
                        "code": exc.status_code,
                        "message": exc.detail,
                        "request_id": request_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
        
        @self.app.exception_handler(Exception)
        async def general_exception_handler(request: Request, exc: Exception):
            request_id = getattr(request.state, 'request_id', 'unknown')
            
            logger.error(
                f"Unhandled exception: {str(exc)}",
                extra={"request_id": request_id},
                exc_info=True
            )
            
            self.metrics.increment_counter("internal_errors")
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": 500,
                        "message": "Internal server error",
                        "request_id": request_id,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
            )
    
    def _setup_health_endpoints(self):
        """Setup health check endpoints"""
        
        @self.app.get("/health")
        async def health_check():
            """Basic health check"""
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "version": self.app.version
            }
        
        @self.app.get("/health/detailed")
        async def detailed_health_check():
            """Detailed health check with dependencies"""
            health_status = await self.health_checker.check_all()
            status_code = 200 if health_status["status"] == "healthy" else 503
            
            return JSONResponse(
                status_code=status_code,
                content=health_status
            )
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get application metrics"""
            return self.metrics.get_all_metrics()
    
    def add_middleware(self, middleware_class, **kwargs):
        """Add custom middleware to the stack"""
        self.app.add_middleware(middleware_class, **kwargs)
        self.middleware_stack.append((middleware_class, kwargs))
    
    def include_router(self, router, prefix: str = "", tags: List[str] = None):
        """Include a router with optional prefix and tags"""
        self.app.include_router(router, prefix=prefix, tags=tags)
    
    def add_route_handler(self, path: str, handler: Callable, methods: List[str] = None):
        """Add a custom route handler"""
        methods = methods or ["GET"]
        self.route_handlers[path] = (handler, methods)
        
        for method in methods:
            self.app.add_api_route(
                path=path,
                endpoint=handler,
                methods=[method]
            )
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance"""
        return self.app