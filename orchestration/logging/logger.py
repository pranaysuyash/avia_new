"""Structured logging system with correlation IDs."""

import logging
import logging.config
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from pythonjsonlogger import jsonlogger

from .correlation import CorrelationIDFilter, get_correlation_id


class StructuredFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add correlation ID
        log_record['correlation_id'] = get_correlation_id() or "N/A"
        
        # Add service information
        log_record['service'] = getattr(record, 'service', 'orchestration')
        log_record['component'] = getattr(record, 'component', record.name)
        
        # Add level name
        log_record['level'] = record.levelname
        
        # Add extra fields if present
        for key, value in message_dict.items():
            if key not in log_record:
                log_record[key] = value


class StructuredLogger:
    """Structured logger with correlation ID support."""
    
    def __init__(self, name: str, service: str = "orchestration"):
        self.logger = logging.getLogger(name)
        self.service = service
        
    def _log(self, level: int, message: str, **kwargs):
        """Internal logging method with structured data."""
        extra = {
            'service': self.service,
            'component': self.logger.name,
            **kwargs
        }
        self.logger.log(level, message, extra=extra)
        
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self._log(logging.DEBUG, message, **kwargs)
        
    def info(self, message: str, **kwargs):
        """Log info message."""
        self._log(logging.INFO, message, **kwargs)
        
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._log(logging.WARNING, message, **kwargs)
        
    def error(self, message: str, **kwargs):
        """Log error message."""
        self._log(logging.ERROR, message, **kwargs)
        
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._log(logging.CRITICAL, message, **kwargs)
        
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self._log(logging.ERROR, message, exc_info=True, **kwargs)


class LogManager:
    """Manages logging configuration for all application components."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.log_dir = Path(config.get('log_dir', 'logs'))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
    def setup_logging(self) -> None:
        """Setup logging configuration."""
        log_level = self.config.get('level', 'INFO').upper()
        log_format = self.config.get('format', 
            '%(asctime)s - %(name)s - %(levelname)s - %(correlation_id)s - %(message)s'
        )
        
        # Create formatters
        console_formatter = logging.Formatter(log_format)
        json_formatter = StructuredFormatter(
            '%(timestamp)s %(level)s %(service)s %(component)s %(correlation_id)s %(message)s'
        )
        
        # Create handlers
        handlers = []
        
        # Console handler
        if 'console' in self.config.get('handlers', ['console']):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(console_formatter)
            console_handler.addFilter(CorrelationIDFilter())
            handlers.append(console_handler)
            
        # File handler
        if 'file' in self.config.get('handlers', []):
            file_path = self.log_dir / self.config.get('file_name', 'orchestration.log')
            file_handler = logging.FileHandler(file_path)
            file_handler.setFormatter(json_formatter)
            file_handler.addFilter(CorrelationIDFilter())
            handlers.append(file_handler)
            
        # Error file handler
        if 'error_file' in self.config.get('handlers', []):
            error_file_path = self.log_dir / self.config.get('error_file_name', 'errors.log')
            error_handler = logging.FileHandler(error_file_path)
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(json_formatter)
            error_handler.addFilter(CorrelationIDFilter())
            handlers.append(error_handler)
            
        # Configure root logger
        logging.basicConfig(
            level=getattr(logging, log_level),
            handlers=handlers,
            force=True
        )
        
        # Configure specific loggers
        self._configure_component_loggers()
        
    def _configure_component_loggers(self) -> None:
        """Configure loggers for specific components."""
        component_configs = self.config.get('components', {})
        
        for component, config in component_configs.items():
            logger = logging.getLogger(component)
            if 'level' in config:
                logger.setLevel(getattr(logging, config['level'].upper()))
                
    def get_logger(self, name: str, service: str = "orchestration") -> StructuredLogger:
        """Get a structured logger instance."""
        return StructuredLogger(name, service)
        
    def create_service_logger(self, service_name: str) -> StructuredLogger:
        """Create a logger for a specific service."""
        return StructuredLogger(f"service.{service_name}", service_name)
        
    def get_log_files(self) -> List[Path]:
        """Get list of all log files."""
        return list(self.log_dir.glob("*.log"))
        
    def get_log_stats(self) -> Dict[str, Any]:
        """Get logging statistics."""
        stats = {
            'log_directory': str(self.log_dir),
            'log_files': [],
            'total_size': 0
        }
        
        for log_file in self.get_log_files():
            file_stats = log_file.stat()
            stats['log_files'].append({
                'name': log_file.name,
                'size': file_stats.st_size,
                'modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat()
            })
            stats['total_size'] += file_stats.st_size
            
        return stats