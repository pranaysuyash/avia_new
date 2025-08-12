"""
Comprehensive logging setup with structured logging and multiple handlers
"""

import logging
import logging.handlers
import json
import sys
import os
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging
    """
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields if present
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
        
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        
        if hasattr(record, 'service'):
            log_entry["service"] = record.service
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add any additional fields from extra
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname',
                          'filename', 'module', 'lineno', 'funcName', 'created',
                          'msecs', 'relativeCreated', 'thread', 'threadName',
                          'processName', 'process', 'getMessage', 'exc_info',
                          'exc_text', 'stack_info']:
                if not key.startswith('_'):
                    log_entry[key] = value
        
        return json.dumps(log_entry)

class ContextFilter(logging.Filter):
    """
    Filter to add context information to log records
    """
    
    def __init__(self, service_name: str = "api"):
        super().__init__()
        self.service_name = service_name
    
    def filter(self, record: logging.LogRecord) -> bool:
        record.service = self.service_name
        record.hostname = os.uname().nodename if hasattr(os, 'uname') else 'unknown'
        record.pid = os.getpid()
        return True

def setup_logging(
    service_name: str = "api",
    log_level: str = "INFO",
    log_format: str = "json",
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_console: bool = True
) -> logging.Logger:
    """
    Setup comprehensive logging configuration
    
    Args:
        service_name: Name of the service for logging context
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Format type ('json' or 'text')
        log_file: Path to log file (optional)
        max_file_size: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        enable_console: Whether to enable console logging
    
    Returns:
        Configured logger instance
    """
    
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Create formatters
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Create context filter
    context_filter = ContextFilter(service_name)
    
    # Console handler
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(context_filter)
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)
    
    # Error file handler (separate file for errors)
    if log_file:
        error_file = log_file.replace('.log', '_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        error_handler.addFilter(context_filter)
        root_logger.addHandler(error_handler)
    
    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    
    logger = logging.getLogger(service_name)
    logger.info(f"Logging configured for service: {service_name}")
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name
    """
    return logging.getLogger(name)

class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context to all log messages
    """
    
    def __init__(self, logger: logging.Logger, extra: Dict[str, Any]):
        super().__init__(logger, extra)
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Merge extra context with any additional context in kwargs
        if 'extra' in kwargs:
            kwargs['extra'].update(self.extra)
        else:
            kwargs['extra'] = self.extra.copy()
        
        return msg, kwargs

def get_context_logger(name: str, **context) -> LoggerAdapter:
    """
    Get a logger with additional context that will be included in all log messages
    
    Args:
        name: Logger name
        **context: Additional context to include in all log messages
    
    Returns:
        LoggerAdapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)

# Performance logging utilities
class PerformanceLogger:
    """
    Utility class for performance logging
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_operation_time(self, operation: str, duration: float, **context):
        """Log operation timing"""
        self.logger.info(
            f"Operation '{operation}' completed in {duration:.3f}s",
            extra={
                "operation": operation,
                "duration": duration,
                "performance": True,
                **context
            }
        )
    
    def log_slow_operation(self, operation: str, duration: float, threshold: float = 1.0, **context):
        """Log slow operations that exceed threshold"""
        if duration > threshold:
            self.logger.warning(
                f"Slow operation '{operation}' took {duration:.3f}s (threshold: {threshold}s)",
                extra={
                    "operation": operation,
                    "duration": duration,
                    "threshold": threshold,
                    "slow_operation": True,
                    **context
                }
            )

# Security logging utilities
class SecurityLogger:
    """
    Utility class for security-related logging
    """
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def log_authentication_attempt(self, user_id: str, success: bool, ip_address: str, **context):
        """Log authentication attempts"""
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for user {user_id}"
        
        self.logger.log(
            level,
            message,
            extra={
                "user_id": user_id,
                "authentication_success": success,
                "ip_address": ip_address,
                "security_event": True,
                **context
            }
        )
    
    def log_authorization_failure(self, user_id: str, resource: str, action: str, **context):
        """Log authorization failures"""
        self.logger.warning(
            f"Authorization failed: user {user_id} attempted {action} on {resource}",
            extra={
                "user_id": user_id,
                "resource": resource,
                "action": action,
                "authorization_failure": True,
                "security_event": True,
                **context
            }
        )
    
    def log_suspicious_activity(self, description: str, **context):
        """Log suspicious activities"""
        self.logger.error(
            f"Suspicious activity detected: {description}",
            extra={
                "suspicious_activity": True,
                "security_event": True,
                **context
            }
        )