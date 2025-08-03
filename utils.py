# Utilities Module
# Shared utilities for file management and caching

import os
import tempfile
import logging
import time
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

def create_temp_file(suffix: str = ".tmp") -> str:
    """Create a temporary file and return its path"""
    try:
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        logger.debug(f"Created temporary file: {temp_file.name}")
        return temp_file.name
    except Exception as e:
        logger.error(f"Failed to create temporary file: {e}")
        raise

def cleanup_temp_files(file_paths: List[str]) -> None:
    """Clean up temporary files"""
    for file_path in file_paths:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug(f"Cleaned up temporary file: {file_path}")
        except Exception as e:
            logger.warning(f"Failed to clean up file {file_path}: {e}")

def validate_file_size(file_path: str, max_size_mb: int = 2048) -> bool:
    """Validate file size is within limits"""
    try:
        if not os.path.exists(file_path):
            return False
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        is_valid = file_size_mb <= max_size_mb
        
        if not is_valid:
            logger.warning(f"File {file_path} size ({file_size_mb:.2f}MB) exceeds limit ({max_size_mb}MB)")
        
        return is_valid
    except Exception as e:
        logger.error(f"Failed to validate file size for {file_path}: {e}")
        return False

def get_file_info(file_path: str) -> dict:
    """Get detailed file information for validation and display"""
    try:
        if not os.path.exists(file_path):
            return {}
        
        file_stats = os.stat(file_path)
        file_size_bytes = file_stats.st_size
        file_size_mb = file_size_bytes / (1024 * 1024)
        
        return {
            'size_bytes': file_size_bytes,
            'size_mb': file_size_mb,
            'size_formatted': format_file_size(file_size_bytes),
            'modified_time': file_stats.st_mtime,
            'exists': True
        }
    except Exception as e:
        logger.error(f"Failed to get file info for {file_path}: {e}")
        return {'exists': False, 'error': str(e)}

def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    try:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    except Exception:
        return "Unknown size"

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format"""
    try:
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.0f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    except Exception:
        return "Unknown duration"

def get_timestamp() -> str:
    """Get current timestamp for file naming"""
    import datetime
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def setup_enhanced_logging(log_level: str = "INFO", log_file: str = "app.log") -> None:
    """Enhanced logging configuration with file rotation and structured logging for production"""
    import logging.handlers
    import json
    from datetime import datetime
    
    try:
        # Convert string level to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Create custom JSON formatter for structured logging
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_entry = {
                    'timestamp': datetime.utcnow().isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno,
                    'process_id': record.process,
                    'thread_id': record.thread
                }
                
                # Add exception info if present
                if record.exc_info:
                    log_entry['exception'] = self.formatException(record.exc_info)
                
                # Add extra fields if present
                if hasattr(record, 'user_id'):
                    log_entry['user_id'] = record.user_id
                if hasattr(record, 'request_id'):
                    log_entry['request_id'] = record.request_id
                if hasattr(record, 'duration'):
                    log_entry['duration'] = record.duration
                
                return json.dumps(log_entry)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        json_formatter = JSONFormatter()
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(numeric_level)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Console handler with simple format for development, JSON for production
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        
        # Use JSON format in production (when LOG_LEVEL is INFO or higher)
        if numeric_level <= logging.INFO and os.getenv('ENVIRONMENT') == 'production':
            console_handler.setFormatter(json_formatter)
        else:
            console_handler.setFormatter(simple_formatter)
        
        root_logger.addHandler(console_handler)
        
        # Ensure logs directory exists
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else './logs'
        os.makedirs(log_dir, exist_ok=True)
        
        # Main application log file with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file, 
            maxBytes=50*1024*1024,  # 50MB
            backupCount=10
        )
        file_handler.setLevel(logging.DEBUG)  # Always log debug to file
        file_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(file_handler)
        
        # Separate error log file for critical issues
        error_log_file = log_file.replace('.log', '_errors.log')
        error_handler = logging.handlers.RotatingFileHandler(
            error_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        root_logger.addHandler(error_handler)
        
        # JSON log file for structured logging (production monitoring)
        if os.getenv('ENVIRONMENT') == 'production':
            json_log_file = log_file.replace('.log', '_structured.log')
            json_handler = logging.handlers.RotatingFileHandler(
                json_log_file,
                maxBytes=100*1024*1024,  # 100MB
                backupCount=5
            )
            json_handler.setLevel(logging.INFO)
            json_handler.setFormatter(json_formatter)
            root_logger.addHandler(json_handler)
        
        # Performance log for monitoring response times
        perf_log_file = log_file.replace('.log', '_performance.log')
        perf_handler = logging.handlers.RotatingFileHandler(
            perf_log_file,
            maxBytes=20*1024*1024,  # 20MB
            backupCount=3
        )
        perf_handler.setLevel(logging.INFO)
        perf_handler.setFormatter(detailed_formatter)
        
        # Create performance logger
        perf_logger = logging.getLogger('performance')
        perf_logger.addHandler(perf_handler)
        perf_logger.setLevel(logging.INFO)
        perf_logger.propagate = False
        
        # Set specific loggers to appropriate levels
        logging.getLogger("openai").setLevel(logging.WARNING)
        logging.getLogger("elevenlabs").setLevel(logging.WARNING)
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("requests").setLevel(logging.WARNING)
        logging.getLogger("streamlit").setLevel(logging.WARNING)
        
        # Security logger for audit trails
        security_logger = logging.getLogger('security')
        security_handler = logging.handlers.RotatingFileHandler(
            log_file.replace('.log', '_security.log'),
            maxBytes=10*1024*1024,
            backupCount=10
        )
        security_handler.setFormatter(json_formatter)
        security_logger.addHandler(security_handler)
        security_logger.setLevel(logging.INFO)
        security_logger.propagate = False
        
        logger.info(f"Enhanced logging configured: level={log_level}, file={log_file}")
        logger.info(f"Log files: main={log_file}, errors={error_log_file}, performance={perf_log_file}")
        
    except Exception as e:
        print(f"Failed to configure enhanced logging: {e}")
        # Fall back to basic configuration
        logging.basicConfig(level=logging.INFO)

def ensure_temp_directory() -> str:
    """Ensure temp directory exists and return its path"""
    temp_dir = os.getenv("TEMP_DIR", "./temp")
    try:
        os.makedirs(temp_dir, exist_ok=True)
        logger.debug(f"Ensured temp directory exists: {temp_dir}")
        return temp_dir
    except Exception as e:
        logger.error(f"Failed to create temp directory {temp_dir}: {e}")
        raise

def cleanup_file(file_path: str) -> None:
    """Clean up a single file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.debug(f"Cleaned up file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up file {file_path}: {e}")

def setup_logging(log_level: str = "INFO") -> None:
    """Configure application logging"""
    try:
        # Convert string level to logging constant
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Configure logging format
        logging.basicConfig(
            level=numeric_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        logger.info(f"Logging configured with level: {log_level}")
    except Exception as e:
        print(f"Failed to configure logging: {e}")
        # Fall back to basic configuration
        logging.basicConfig(level=logging.INFO)
def log_performance(operation: str, duration: float, **kwargs) -> None:
    """Log performance metrics for monitoring"""
    perf_logger = logging.getLogger('performance')
    extra_info = " ".join([f"{k}={v}" for k, v in kwargs.items()])
    perf_logger.info(f"PERFORMANCE: {operation} completed in {duration:.3f}s {extra_info}")

def log_security_event(event_type: str, user_id: str = None, details: dict = None) -> None:
    """Log security events for audit trails"""
    security_logger = logging.getLogger('security')
    log_data = {
        'event_type': event_type,
        'user_id': user_id,
        'timestamp': get_timestamp(),
        'details': details or {}
    }
    security_logger.info(f"SECURITY: {event_type}", extra=log_data)

class PerformanceTimer:
    """Context manager for timing operations"""
    
    def __init__(self, operation_name: str, **kwargs):
        self.operation_name = operation_name
        self.kwargs = kwargs
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            log_performance(self.operation_name, duration, **self.kwargs)

def create_request_id() -> str:
    """Create unique request ID for tracing"""
    import uuid
    return str(uuid.uuid4())[:8]

def get_file_size_limit() -> int:
    """Get the maximum file size limit in MB"""
    return int(os.getenv('MAX_FILE_SIZE_MB', 100))

def setup_production_logging() -> None:
    """Setup logging specifically for production environment"""
    import sys
    
    # Set environment to production
    os.environ['ENVIRONMENT'] = 'production'
    
    # Configure enhanced logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.path.join('./logs', 'app.log')
    
    setup_enhanced_logging(log_level, log_file)
    
    # Add uncaught exception handler
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
    
    sys.excepthook = handle_exception
    
    logger.info("Production logging configured")


# Centralized Validation Functions
def validate_email(email: str) -> bool:
    """Validate email address format"""
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(email_pattern, email))


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format (supports various formats)"""
    import re
    # Remove common separators
    cleaned = re.sub(r'[\s\-\.\(\)]', '', phone)
    # Check if it's a valid phone number (10-15 digits, optionally starting with +)
    phone_pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(phone_pattern, cleaned))


def validate_url(url: str) -> bool:
    """Validate URL format"""
    import re
    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(url_pattern, url, re.IGNORECASE))


def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
    """Validate file extension against allowed list"""
    if not filename:
        return False
    
    # Extract extension (case-insensitive)
    ext = os.path.splitext(filename)[1].lower()
    return ext in [e.lower() if e.startswith('.') else f'.{e.lower()}' for e in allowed_extensions]


def validate_content_type(content_type: str, allowed_types: List[str]) -> bool:
    """Validate content type against allowed list"""
    if not content_type:
        return False
    
    # Normalize content type (remove parameters like charset)
    base_type = content_type.split(';')[0].strip().lower()
    
    # Check exact matches and wildcards
    for allowed in allowed_types:
        allowed_lower = allowed.lower()
        if allowed_lower.endswith('/*'):
            # Wildcard match (e.g., 'audio/*')
            prefix = allowed_lower[:-2]
            if base_type.startswith(prefix):
                return True
        elif base_type == allowed_lower:
            return True
    
    return False


def validate_language_code(language: str, valid_languages: Optional[List[str]] = None) -> bool:
    """Validate language code"""
    if not language:
        return False
    
    # Default supported languages
    if valid_languages is None:
        valid_languages = ['auto', 'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh',
                          'ar', 'hi', 'nl', 'pl', 'tr', 'sv', 'da', 'no', 'fi']
    
    return language.lower() in [lang.lower() for lang in valid_languages]


def validate_model_name(model: str, valid_models: Optional[List[str]] = None) -> bool:
    """Validate AI model name"""
    if not model:
        return False
    
    # Default Whisper models
    if valid_models is None:
        valid_models = ['tiny', 'base', 'small', 'medium', 'large', 'large-v2', 'large-v3']
    
    return model.lower() in [m.lower() for m in valid_models]


def validate_json_structure(data: dict, required_fields: List[str]) -> tuple[bool, Optional[str]]:
    """Validate JSON structure has required fields"""
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, None


def validate_date_range(start_date: str, end_date: str) -> tuple[bool, Optional[str]]:
    """Validate date range"""
    try:
        from datetime import datetime
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if start > end:
            return False, "Start date must be before end date"
        
        return True, None
    except (ValueError, AttributeError) as e:
        return False, f"Invalid date format: {str(e)}"


def validate_pagination_params(page: int, per_page: int, max_per_page: int = 100) -> tuple[bool, Optional[str]]:
    """Validate pagination parameters"""
    if page < 1:
        return False, "Page number must be at least 1"
    
    if per_page < 1:
        return False, "Items per page must be at least 1"
    
    if per_page > max_per_page:
        return False, f"Items per page cannot exceed {max_per_page}"
    
    return True, None


def sanitize_filename(filename: str, max_length: int = 255) -> str:
    """Sanitize filename for safe storage"""
    import re
    
    # Remove directory traversal attempts
    filename = os.path.basename(filename)
    
    # Replace invalid characters
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    
    # Limit length (preserving extension)
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext)
        filename = name[:max_name_length] + ext
    
    # Ensure it's not empty or just dots
    if not filename or filename.replace('.', '') == '':
        filename = 'unnamed_file'
    
    return filename


def validate_sort_parameter(sort_by: str, valid_sorts: List[str]) -> bool:
    """Validate sort parameter against allowed values"""
    return sort_by.lower() in [s.lower() for s in valid_sorts]


def validate_enum_value(value: str, enum_values: List[str], case_sensitive: bool = False) -> bool:
    """Validate value against enum list"""
    if case_sensitive:
        return value in enum_values
    return value.lower() in [v.lower() for v in enum_values]


# File type validation configurations
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.flac', '.aac', '.ogg', '.wma', '.opus']
VIDEO_EXTENSIONS = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv', '.m4v']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.tiff']
DOCUMENT_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']

AUDIO_CONTENT_TYPES = ['audio/mpeg', 'audio/wav', 'audio/mp4', 'audio/flac', 'audio/aac', 
                       'audio/ogg', 'audio/x-ms-wma', 'audio/opus', 'audio/*']
VIDEO_CONTENT_TYPES = ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-matroska',
                       'video/webm', 'video/x-flv', 'video/x-ms-wmv', 'video/*']
IMAGE_CONTENT_TYPES = ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
                       'image/svg+xml', 'image/tiff', 'image/*']
DOCUMENT_CONTENT_TYPES = ['application/pdf', 'application/msword', 
                          'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                          'text/plain', 'text/rtf', 'application/vnd.oasis.opendocument.text']


def validate_audio_file(filename: str, content_type: Optional[str] = None) -> bool:
    """Validate audio file by extension and optionally content type"""
    if not validate_file_extension(filename, AUDIO_EXTENSIONS):
        return False
    
    if content_type:
        return validate_content_type(content_type, AUDIO_CONTENT_TYPES)
    
    return True


def validate_video_file(filename: str, content_type: Optional[str] = None) -> bool:
    """Validate video file by extension and optionally content type"""
    if not validate_file_extension(filename, VIDEO_EXTENSIONS):
        return False
    
    if content_type:
        return validate_content_type(content_type, VIDEO_CONTENT_TYPES)
    
    return True


def validate_image_file(filename: str, content_type: Optional[str] = None) -> bool:
    """Validate image file by extension and optionally content type"""
    if not validate_file_extension(filename, IMAGE_EXTENSIONS):
        return False
    
    if content_type:
        return validate_content_type(content_type, IMAGE_CONTENT_TYPES)
    
    return True


def validate_media_file(filename: str, content_type: Optional[str] = None) -> tuple[bool, Optional[str]]:
    """Validate any media file and return its type"""
    if validate_audio_file(filename, content_type):
        return True, 'audio'
    elif validate_video_file(filename, content_type):
        return True, 'video'
    elif validate_image_file(filename, content_type):
        return True, 'image'
    else:
        return False, None