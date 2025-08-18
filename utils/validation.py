"""
Validation utilities
"""

import re
from typing import Optional

def validate_email(email: str) -> bool:
    """
    Validate email address format using regex
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid email format, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    try:
        return bool(re.match(pattern, email.strip()))
    except Exception:
        return False

def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number string to validate
        
    Returns:
        bool: True if valid phone format, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove all non-digit characters
    digits_only = re.sub(r'\D', '', phone)
    
    # Check if it's a valid length (10-15 digits)
    return len(digits_only) >= 10 and len(digits_only) <= 15

def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL format, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url_pattern = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}.*$'
    
    try:
        return bool(re.match(url_pattern, url.strip()))
    except Exception:
        return False

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file system usage
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    if not filename or not isinstance(filename, str):
        return "untitled"
    
    # Remove or replace invalid characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure it's not empty
    return sanitized if sanitized else "untitled"