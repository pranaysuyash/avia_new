"""
Email Service Module
Handles sending verification and password reset emails
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    def __init__(self):
        # Get email configuration from environment
        self.smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.from_email = os.getenv('FROM_EMAIL', self.smtp_username)
        self.from_name = os.getenv('FROM_NAME', 'Audio/Video NER App')
        self.app_url = os.getenv('APP_URL', 'http://localhost:8501')
        
        # Check if email is configured
        self.is_configured = bool(self.smtp_username and self.smtp_password)
        
        if not self.is_configured:
            logger.warning("Email service not configured. Set SMTP_USERNAME and SMTP_PASSWORD environment variables.")
    
    def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = "") -> Tuple[bool, Optional[str]]:
        """Send an email"""
        if not self.is_configured:
            logger.warning(f"Email service not configured. Would have sent email to {to_email}")
            return True, "Email service not configured (development mode)"
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Create text and HTML parts
            if text_content:
                text_part = MIMEText(text_content, 'plain')
                msg.attach(text_part)
            
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            return True, None
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False, str(e)
    
    def send_verification_email(self, to_email: str, username: str, verification_token: str) -> Tuple[bool, Optional[str]]:
        """Send account verification email"""
        subject = "Verify Your Account - Audio/Video NER App"
        
        verification_link = f"{self.app_url}/verify?token={verification_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #007bff; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 30px; margin-top: 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #007bff; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Audio/Video NER App!</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>Thank you for signing up! Please verify your email address to complete your registration.</p>
                    <p style="text-align: center;">
                        <a href="{verification_link}" class="button">Verify Email Address</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #e9ecef; padding: 10px;">
                        {verification_link}
                    </p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Audio/Video NER App. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Audio/Video NER App!
        
        Hi {username},
        
        Thank you for signing up! Please verify your email address by clicking the link below:
        
        {verification_link}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, you can safely ignore this email.
        
        © {datetime.now().year} Audio/Video NER App. All rights reserved.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)
    
    def send_password_reset_email(self, to_email: str, username: str, reset_token: str) -> Tuple[bool, Optional[str]]:
        """Send password reset email"""
        subject = "Password Reset Request - Audio/Video NER App"
        
        reset_link = f"{self.app_url}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #dc3545; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 30px; margin-top: 0; }}
                .button {{ display: inline-block; padding: 12px 30px; background-color: #dc3545; 
                          color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
                .warning {{ background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 10px; 
                           margin: 15px 0; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Password Reset Request</h1>
                </div>
                <div class="content">
                    <h2>Hi {username},</h2>
                    <p>We received a request to reset your password. Click the button below to create a new password:</p>
                    <p style="text-align: center;">
                        <a href="{reset_link}" class="button">Reset Password</a>
                    </p>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; background-color: #e9ecef; padding: 10px;">
                        {reset_link}
                    </p>
                    <div class="warning">
                        <strong>⚠️ Important:</strong> This link will expire in 24 hours for security reasons.
                    </div>
                    <p>If you didn't request a password reset, please ignore this email. Your password won't be changed.</p>
                    <p>For security reasons, this link can only be used once.</p>
                </div>
                <div class="footer">
                    <p>© {datetime.now().year} Audio/Video NER App. All rights reserved.</p>
                    <p>This is an automated message, please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Password Reset Request
        
        Hi {username},
        
        We received a request to reset your password. Click the link below to create a new password:
        
        {reset_link}
        
        This link will expire in 24 hours for security reasons.
        
        If you didn't request a password reset, please ignore this email. Your password won't be changed.
        
        For security reasons, this link can only be used once.
        
        © {datetime.now().year} Audio/Video NER App. All rights reserved.
        """
        
        return self.send_email(to_email, subject, html_content, text_content)


# Global email service instance
email_service = EmailService()