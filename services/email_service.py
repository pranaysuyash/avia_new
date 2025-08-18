"""
Email Service
Adapter for the auth email service to be available in services package
"""

# Import the existing EmailService from auth module
from auth.email_service import EmailService

# Re-export for services package compatibility
__all__ = ['EmailService']