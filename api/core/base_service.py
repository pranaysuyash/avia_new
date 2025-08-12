"""
Base service class with common patterns for authentication, validation, and error handling
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type, TypeVar, Generic
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import asyncio
from contextlib import asynccontextmanager

from .logging import get_logger
from .metrics import MetricsCollector
from .exceptions import ServiceError, ValidationError

T = TypeVar('T', bound=BaseModel)
R = TypeVar('R', bound=BaseModel)

class ServiceConfig(BaseModel):
    """Base configuration for services"""
    name: str
    version: str = "1.0.0"
    debug: bool = False
    timeout: int = 30
    max_retries: int = 3
    enable_metrics: bool = True
    enable_logging: bool = True
    
    class Config:
        extra = "allow"

class ServiceRequest(BaseModel):
    """Base service request model"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ServiceResponse(BaseModel):
    """Base service response model"""
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    success: bool = True
    message: str = "Success"
    data: Optional[Any] = None
    errors: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class BaseService(ABC, Generic[T, R]):
    """
    Base service class with common patterns for:
    - Authentication and authorization
    - Request/response validation
    - Error handling and logging
    - Metrics collection
    - Retry logic
    """
    
    def __init__(self, config: ServiceConfig):
        self.config = config
        self.logger = get_logger(f"service.{config.name}")
        self.metrics = MetricsCollector(config.name) if config.enable_metrics else None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize service resources"""
        if self._initialized:
            return
        
        self.logger.info(f"Initializing service: {self.config.name} v{self.config.version}")
        await self._initialize_service()
        self._initialized = True
        self.logger.info(f"Service {self.config.name} initialized successfully")
    
    async def shutdown(self) -> None:
        """Cleanup service resources"""
        if not self._initialized:
            return
        
        self.logger.info(f"Shutting down service: {self.config.name}")
        await self._shutdown_service()
        self._initialized = False
        self.logger.info(f"Service {self.config.name} shutdown complete")
    
    @abstractmethod
    async def _initialize_service(self) -> None:
        """Service-specific initialization logic"""
        pass
    
    @abstractmethod
    async def _shutdown_service(self) -> None:
        """Service-specific shutdown logic"""
        pass
    
    @abstractmethod
    async def _process_request(self, request: T) -> R:
        """Service-specific request processing logic"""
        pass
    
    async def process(self, request: T, user_context: Optional[Dict[str, Any]] = None) -> ServiceResponse:
        """
        Main processing method with common patterns applied
        """
        if not self._initialized:
            await self.initialize()
        
        start_time = datetime.utcnow()
        request_id = getattr(request, 'request_id', str(uuid.uuid4()))
        
        # Start metrics collection
        if self.metrics:
            self.metrics.increment_counter(f"{self.config.name}.requests.total")
            self.metrics.start_timer(f"{self.config.name}.requests.duration")
        
        try:
            # Log request
            self.logger.info(
                f"Processing request {request_id}",
                extra={
                    "request_id": request_id,
                    "service": self.config.name,
                    "user_id": user_context.get("user_id") if user_context else None
                }
            )
            
            # Validate authentication if user context provided
            if user_context:
                await self._validate_authentication(user_context)
            
            # Validate request
            await self._validate_request(request)
            
            # Process with retry logic
            result = await self._process_with_retry(request)
            
            # Create success response
            response = ServiceResponse(
                request_id=request_id,
                data=result,
                metadata={
                    "processing_time": (datetime.utcnow() - start_time).total_seconds(),
                    "service": self.config.name,
                    "version": self.config.version
                }
            )
            
            # Log success
            self.logger.info(
                f"Request {request_id} processed successfully",
                extra={
                    "request_id": request_id,
                    "processing_time": response.metadata["processing_time"]
                }
            )
            
            # Update metrics
            if self.metrics:
                self.metrics.increment_counter(f"{self.config.name}.requests.success")
                self.metrics.record_histogram(
                    f"{self.config.name}.requests.duration",
                    response.metadata["processing_time"]
                )
            
            return response
            
        except Exception as e:
            # Handle errors
            error_response = await self._handle_error(e, request_id, start_time)
            
            # Update error metrics
            if self.metrics:
                self.metrics.increment_counter(f"{self.config.name}.requests.error")
                self.metrics.increment_counter(
                    f"{self.config.name}.errors.{type(e).__name__.lower()}"
                )
            
            return error_response
    
    async def _validate_authentication(self, user_context: Dict[str, Any]) -> None:
        """Validate user authentication and authorization"""
        if not user_context.get("authenticated", False):
            raise ServiceError("Authentication required", status_code=401)
        
        # Check if user is active
        if not user_context.get("is_active", True):
            raise ServiceError("User account is inactive", status_code=403)
        
        # Service-specific authorization can be implemented in subclasses
        await self._validate_authorization(user_context)
    
    async def _validate_authorization(self, user_context: Dict[str, Any]) -> None:
        """Service-specific authorization validation"""
        # Override in subclasses for specific authorization logic
        pass
    
    async def _validate_request(self, request: T) -> None:
        """Validate request data"""
        # Pydantic validation is automatic, but we can add custom validation here
        if hasattr(request, 'validate_business_rules'):
            await request.validate_business_rules()
    
    async def _process_with_retry(self, request: T) -> R:
        """Process request with retry logic"""
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    # Exponential backoff
                    delay = min(2 ** attempt, 30)  # Max 30 seconds
                    self.logger.warning(
                        f"Retrying request (attempt {attempt + 1}/{self.config.max_retries + 1}) "
                        f"after {delay}s delay"
                    )
                    await asyncio.sleep(delay)
                
                # Set timeout for processing
                return await asyncio.wait_for(
                    self._process_request(request),
                    timeout=self.config.timeout
                )
                
            except asyncio.TimeoutError as e:
                last_exception = ServiceError(
                    f"Request timeout after {self.config.timeout}s",
                    status_code=408
                )
                self.logger.warning(f"Request timeout on attempt {attempt + 1}")
                
            except ServiceError as e:
                # Don't retry service errors (business logic errors)
                raise e
                
            except Exception as e:
                last_exception = e
                self.logger.warning(
                    f"Request failed on attempt {attempt + 1}: {str(e)}",
                    exc_info=True
                )
        
        # All retries exhausted
        if isinstance(last_exception, ServiceError):
            raise last_exception
        else:
            raise ServiceError(
                f"Request failed after {self.config.max_retries + 1} attempts: {str(last_exception)}",
                status_code=500
            )
    
    async def _handle_error(
        self, 
        error: Exception, 
        request_id: str, 
        start_time: datetime
    ) -> ServiceResponse:
        """Handle and format errors"""
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        if isinstance(error, ServiceError):
            status_code = error.status_code
            message = error.message
            error_details = error.details
        elif isinstance(error, ValidationError):
            status_code = 422
            message = "Validation error"
            error_details = {"validation_errors": str(error)}
        else:
            status_code = 500
            message = "Internal server error"
            error_details = {"error_type": type(error).__name__}
            
            # Log unexpected errors
            self.logger.error(
                f"Unexpected error in request {request_id}: {str(error)}",
                extra={"request_id": request_id},
                exc_info=True
            )
        
        return ServiceResponse(
            request_id=request_id,
            success=False,
            message=message,
            errors=error_details,
            metadata={
                "processing_time": processing_time,
                "service": self.config.name,
                "error_type": type(error).__name__,
                "status_code": status_code
            }
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        try:
            # Basic health check
            health_status = {
                "service": self.config.name,
                "version": self.config.version,
                "status": "healthy" if self._initialized else "initializing",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime": self._get_uptime() if self._initialized else 0
            }
            
            # Service-specific health checks
            service_health = await self._service_health_check()
            health_status.update(service_health)
            
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                "service": self.config.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _service_health_check(self) -> Dict[str, Any]:
        """Service-specific health check logic"""
        # Override in subclasses
        return {}
    
    def _get_uptime(self) -> float:
        """Get service uptime in seconds"""
        if not hasattr(self, '_start_time'):
            self._start_time = datetime.utcnow()
        return (datetime.utcnow() - self._start_time).total_seconds()
    
    @asynccontextmanager
    async def service_context(self):
        """Context manager for service lifecycle"""
        try:
            await self.initialize()
            yield self
        finally:
            await self.shutdown()

class ServiceError(Exception):
    """Service-specific error"""
    
    def __init__(self, message: str, status_code: int = 500, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)