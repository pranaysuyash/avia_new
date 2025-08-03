#!/usr/bin/env python3
"""
Configuration management for Audio/Video Transcription App
Handles environment variables, API key validation, and application settings
"""

import os
import logging
from typing import Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up comprehensive logging
from monitoring.logger_config import setup_logging, get_logger

# Initialize logging based on environment
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_file = os.getenv("LOG_FILE", "logs/app.log")
enable_json_logging = os.getenv("ENABLE_JSON_LOGGING", "true").lower() == "true"

logging_handlers = setup_logging(
    log_level=log_level,
    log_file=log_file,
    enable_json_logging=enable_json_logging,
    enable_error_tracking=True,
    enable_performance_tracking=True
)

logger = get_logger(__name__)

class Config:
    """Application configuration management"""
    
    # API Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    
    # Application Settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "2048"))  # 2GB default
    TEMP_DIR = os.getenv("TEMP_DIR", "./temp")
    
    # Admin Configuration
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    
    # Processing Settings
    WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
    SPACY_MODEL = os.getenv("SPACY_MODEL", "en_core_web_sm")
    
    # Performance Settings
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "5"))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "300"))
    
    @classmethod
    def validate_api_keys(cls) -> Dict[str, bool]:
        """Validate API key configuration"""
        # List of placeholder values that indicate unconfigured keys
        placeholder_values = [
            "",
            "your_openai_api_key_here", 
            "your_elevenlabs_api_key_here",
            "sk-your-openai-key-here",
            "your-elevenlabs-key-here"
        ]
        
        return {
            "openai": bool(cls.OPENAI_API_KEY and cls.OPENAI_API_KEY not in placeholder_values),
            "elevenlabs": bool(cls.ELEVENLABS_API_KEY and cls.ELEVENLABS_API_KEY not in placeholder_values)
        }
    
    @classmethod
    def get_missing_api_keys(cls) -> list:
        """Get list of missing API keys"""
        validation = cls.validate_api_keys()
        missing = []
        
        if not validation["openai"]:
            missing.append("OPENAI_API_KEY")
        if not validation["elevenlabs"]:
            missing.append("ELEVENLABS_API_KEY")
            
        return missing
    
    @classmethod
    def validate_configuration(cls) -> Tuple[bool, list]:
        """Validate complete configuration and return status with issues"""
        issues = []
        warnings = []
        
        # Check critical API keys (OpenAI is required for core functionality)
        api_status = cls.validate_api_keys()
        if not api_status["openai"]:
            issues.append("Missing OPENAI_API_KEY (required for transcription)")
        
        # Check optional API keys (ElevenLabs only needed for admin features)
        if not api_status["elevenlabs"]:
            warnings.append("Missing ELEVENLABS_API_KEY (admin TTS features disabled)")
        
        # Check file size limit
        if cls.MAX_FILE_SIZE_MB <= 0 or cls.MAX_FILE_SIZE_MB > 5120:
            issues.append("MAX_FILE_SIZE_MB should be between 1 and 5120 (5GB)")
        
        # Check log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if cls.LOG_LEVEL not in valid_log_levels:
            issues.append(f"LOG_LEVEL must be one of: {', '.join(valid_log_levels)}")
        
        # Check temp directory
        if not cls.TEMP_DIR:
            issues.append("TEMP_DIR cannot be empty")
        
        # Combine issues and warnings
        all_issues = issues + [f"Warning: {w}" for w in warnings]
        
        # Configuration is valid if no critical issues (warnings are OK)
        return len(issues) == 0, all_issues
    
    @classmethod
    def setup_logging(cls):
        """Configure enhanced application logging"""
        from utils import setup_enhanced_logging
        setup_enhanced_logging(cls.LOG_LEVEL, 'app.log')
    
    @classmethod
    def get_configuration_guide(cls) -> str:
        """Get configuration setup guide"""
        return """
# Configuration Setup Guide

## Required API Keys

1. **OpenAI API Key** (Required for transcription and advanced analysis)
   - Sign up at: https://platform.openai.com/
   - Create API key in your dashboard
   - Add to .env file: OPENAI_API_KEY=your_key_here

2. **ElevenLabs API Key** (Required for text-to-speech features)
   - Sign up at: https://elevenlabs.io/
   - Get API key from your profile
   - Add to .env file: ELEVENLABS_API_KEY=your_key_here

## Optional Configuration

- LOG_LEVEL: Set to DEBUG, INFO, WARNING, ERROR, or CRITICAL (default: INFO)
- MAX_FILE_SIZE_MB: Maximum upload size in MB (default: 2048, max: 5120)
- TEMP_DIR: Directory for temporary files (default: ./temp)
- ADMIN_PASSWORD: Password for admin panel access (optional)
- WHISPER_MODEL: Whisper model size - tiny, base, small, medium, large (default: base)
- SPACY_MODEL: spaCy model name (default: en_core_web_sm)

## Example .env file:

```
OPENAI_API_KEY=sk-your-openai-key-here
ELEVENLABS_API_KEY=your-elevenlabs-key-here
LOG_LEVEL=INFO
MAX_FILE_SIZE_MB=2048
TEMP_DIR=./temp
ADMIN_PASSWORD=your-secure-password
WHISPER_MODEL=base
SPACY_MODEL=en_core_web_sm
```
"""

def get_config() -> Config:
    """Get application configuration instance"""
    return Config

def validate_environment() -> Tuple[bool, str]:
    """Validate environment configuration and return status message"""
    is_valid, issues = Config.validate_configuration()
    
    if is_valid:
        # Check if we have warnings (non-critical issues)
        warnings = [issue for issue in issues if issue.startswith("Warning:")]
        if warnings:
            warning_list = "\n".join([f"• {issue}" for issue in warnings])
            return True, f"✅ Configuration is valid with warnings:\n{warning_list}"
        else:
            return True, "✅ Configuration is valid"
    else:
        # Separate critical issues from warnings
        critical_issues = [issue for issue in issues if not issue.startswith("Warning:")]
        warnings = [issue for issue in issues if issue.startswith("Warning:")]
        
        message_parts = []
        if critical_issues:
            critical_list = "\n".join([f"• {issue}" for issue in critical_issues])
            message_parts.append(f"❌ Critical issues:\n{critical_list}")
        
        if warnings:
            warning_list = "\n".join([f"• {issue}" for issue in warnings])
            message_parts.append(f"⚠️ Warnings:\n{warning_list}")
        
        return False, "\n\n".join(message_parts)

def print_configuration_status():
    """Print current configuration status to console"""
    print("=" * 50)
    print("AUDIO/VIDEO TRANSCRIPTION APP - CONFIGURATION")
    print("=" * 50)
    
    # API Key Status
    api_status = Config.validate_api_keys()
    print("\n🔑 API Key Status:")
    print(f"  OpenAI API:     {'✅ Configured' if api_status['openai'] else '❌ Missing'}")
    print(f"  ElevenLabs API: {'✅ Configured' if api_status['elevenlabs'] else '❌ Missing'}")
    
    # Configuration Status
    is_valid, issues = Config.validate_configuration()
    print(f"\n⚙️ Configuration Status:")
    if is_valid:
        print("  ✅ Configuration is valid")
    else:
        print("  ⚠️ Configuration has issues:")
        for issue in issues:
            if issue.startswith("Warning:"):
                print(f"    🟡 {issue}")
            else:
                print(f"    ❌ {issue}")
    
    # Application Settings
    print(f"\n📊 Application Settings:")
    print(f"  Log Level:        {Config.LOG_LEVEL}")
    print(f"  Max File Size:    {Config.MAX_FILE_SIZE_MB}MB")
    print(f"  Temp Directory:   {Config.TEMP_DIR}")
    print(f"  Whisper Model:    {Config.WHISPER_MODEL}")
    print(f"  spaCy Model:      {Config.SPACY_MODEL}")
    
    # Feature availability
    api_status = Config.validate_api_keys()
    print(f"\n🎯 Feature Availability:")
    print(f"  Basic Transcription:  {'✅ Available' if api_status['openai'] else '❌ Requires OpenAI API'}")
    print(f"  Advanced Analysis:    {'✅ Available' if api_status['openai'] else '❌ Requires OpenAI API'}")
    print(f"  Admin TTS Features:   {'✅ Available' if api_status['elevenlabs'] else '❌ Requires ElevenLabs API'}")
    print(f"  Local NER (Basic):    ✅ Always Available")
    
    # Setup guidance
    if not is_valid:
        print(f"\n💡 Setup Guide:")
        print("  1. Copy .env.example to .env")
        print("  2. Add your API keys to the .env file")
        print("  3. Restart the application")
        print("  4. Run 'python config.py' to verify configuration")
    
    print("=" * 50)

if __name__ == "__main__":
    # Allow running this module directly to check configuration
    print_configuration_status()