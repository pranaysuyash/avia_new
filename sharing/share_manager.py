#!/usr/bin/env python3
"""
Share Link Management for Audio/Video Transcription App
Handles creation, validation, and management of shareable transcript links
"""

import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from database.models import SharedLink, ShareAccessLog, Transcript, User, SharePermission
from database import get_db_session

logger = logging.getLogger(__name__)

class ShareManager:
    """Manages transcript sharing functionality"""
    
    def __init__(self):
        self.token_length = 32
        self.default_expiration_days = 30
        
    def generate_share_token(self) -> str:
        """Generate a secure, unique share token"""
        # Use URL-safe characters for the token
        alphabet = string.ascii_letters + string.digits + '-_'
        token = ''.join(secrets.choice(alphabet) for _ in range(self.token_length))
        
        # Ensure uniqueness by checking database
        with get_db_session() as db:
            while db.query(SharedLink).filter(SharedLink.share_token == token).first():
                token = ''.join(secrets.choice(alphabet) for _ in range(self.token_length))
        
        return token
    
    def create_share_link(
        self,
        transcript_id: int,
        created_by_id: int,
        permission: str = 'view',
        expires_in_days: Optional[int] = None,
        password: Optional[str] = None,
        max_views: Optional[int] = None
    ) -> Optional[SharedLink]:
        """
        Create a new share link for a transcript
        
        Args:
            transcript_id: ID of the transcript to share
            created_by_id: ID of the user creating the share
            permission: Permission level ('view', 'comment', 'edit')
            expires_in_days: Number of days until link expires
            password: Optional password protection
            max_views: Maximum number of times link can be accessed
        
        Returns:
            SharedLink object or None if creation failed
        """
        try:
            with get_db_session() as db:
                # Verify transcript exists and user has permission
                transcript = db.query(Transcript).filter(
                    Transcript.id == transcript_id,
                    Transcript.user_id == created_by_id
                ).first()
                
                if not transcript:
                    logger.error(f"Transcript {transcript_id} not found or user {created_by_id} lacks permission")
                    return None
                
                # Generate unique token
                share_token = self.generate_share_token()
                
                # Calculate expiration
                if expires_in_days is None:
                    expires_in_days = self.default_expiration_days
                
                expires_at = None
                if expires_in_days > 0:
                    expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
                
                # Hash password if provided
                password_hash = None
                if password:
                    import bcrypt
                    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Convert permission string to enum
                permission_enum = SharePermission.VIEW
                if permission.lower() == 'comment':
                    permission_enum = SharePermission.COMMENT
                elif permission.lower() == 'edit':
                    permission_enum = SharePermission.EDIT
                
                # Create share link
                share_link = SharedLink(
                    transcript_id=transcript_id,
                    share_token=share_token,
                    created_by_id=created_by_id,
                    permission=permission_enum,
                    expires_at=expires_at,
                    password_hash=password_hash,
                    max_views=max_views,
                    is_active=True
                )
                
                db.add(share_link)
                db.commit()
                db.refresh(share_link)
                
                logger.info(f"Created share link {share_token} for transcript {transcript_id}")
                return share_link
                
        except Exception as e:
            logger.error(f"Failed to create share link: {e}")
            return None
    
    def get_share_link_info(self, share_token: str) -> Optional[Dict]:
        """Get information about a share link"""
        try:
            with get_db_session() as db:
                share_link = db.query(SharedLink).filter(
                    SharedLink.share_token == share_token
                ).first()
                
                if not share_link:
                    return None
                
                # Get transcript info
                transcript = db.query(Transcript).filter(
                    Transcript.id == share_link.transcript_id
                ).first()
                
                # Get creator info
                creator = db.query(User).filter(
                    User.id == share_link.created_by_id
                ).first()
                
                return {
                    'id': share_link.id,
                    'share_token': share_link.share_token,
                    'transcript_id': share_link.transcript_id,
                    'transcript_title': transcript.title if transcript else 'Unknown',
                    'created_by': creator.username if creator else 'Unknown',
                    'permissions': share_link.permission.value if share_link.permission else 'view',
                    'created_at': share_link.created_at,
                    'expires_at': share_link.expires_at,
                    'is_active': share_link.is_active,
                    'view_count': share_link.view_count,
                    'max_views': share_link.max_views,
                    'has_password': bool(share_link.password_hash),
                    'require_login': False,
                    'allowed_emails': []
                }
                
        except Exception as e:
            logger.error(f"Failed to get share link info: {e}")
            return None
    
    def validate_share_access(
        self,
        share_token: str,
        password: Optional[str] = None,
        user_email: Optional[str] = None,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[SharedLink]]:
        """
        Validate access to a shared link
        
        Returns:
            (is_valid, error_message, share_link)
        """
        try:
            with get_db_session() as db:
                # Get share link
                share_link = db.query(SharedLink).filter(
                    SharedLink.share_token == share_token
                ).first()
                
                if not share_link:
                    return False, "Invalid share link", None
                
                # Check if active
                if not share_link.is_active:
                    return False, "This share link has been disabled", None
                
                # Check expiration
                if share_link.expires_at and datetime.utcnow() > share_link.expires_at:
                    return False, "This share link has expired", None
                
                # Check view count limit
                if share_link.max_views and share_link.view_count >= share_link.max_views:
                    return False, "This share link has reached its view limit", None
                
                # Check password
                if share_link.password_hash:
                    if not password:
                        return False, "Password required", None
                    
                    import bcrypt
                    if not bcrypt.checkpw(password.encode('utf-8'), share_link.password_hash.encode('utf-8')):
                        return False, "Incorrect password", None
                
                
                # Log access
                access_log = ShareAccessLog(
                    shared_link_id=share_link.id,
                    ip_address=ip_address
                )
                db.add(access_log)
                
                # Increment view count
                share_link.view_count += 1
                share_link.last_accessed = datetime.utcnow()
                
                db.commit()
                db.refresh(share_link)
                
                return True, None, share_link
                
        except Exception as e:
            logger.error(f"Failed to validate share access: {e}")
            return False, "An error occurred validating access", None
    
    def get_user_share_links(self, user_id: int) -> List[Dict]:
        """Get all share links created by a user"""
        try:
            with get_db_session() as db:
                share_links = db.query(SharedLink).filter(
                    SharedLink.created_by_id == user_id
                ).order_by(SharedLink.created_at.desc()).all()
                
                results = []
                for link in share_links:
                    transcript = db.query(Transcript).filter(
                        Transcript.id == link.transcript_id
                    ).first()
                    
                    results.append({
                        'id': link.id,
                        'share_token': link.share_token,
                        'transcript_title': transcript.title if transcript else 'Unknown',
                        'permissions': link.permission.value if link.permission else 'view',
                        'created_at': link.created_at,
                        'expires_at': link.expires_at,
                        'is_active': link.is_active,
                        'view_count': link.view_count,
                        'max_views': link.max_views,
                        'last_accessed': link.last_accessed
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to get user share links: {e}")
            return []
    
    def update_share_permissions(
        self,
        share_id: int,
        user_id: int,
        permission: Optional[str] = None,
        is_active: Optional[bool] = None,
        expires_at: Optional[datetime] = None,
        max_views: Optional[int] = None
    ) -> bool:
        """Update share link permissions"""
        try:
            with get_db_session() as db:
                share_link = db.query(SharedLink).filter(
                    SharedLink.id == share_id,
                    SharedLink.created_by_id == user_id
                ).first()
                
                if not share_link:
                    logger.error(f"Share link {share_id} not found or user {user_id} lacks permission")
                    return False
                
                # Update fields
                if permission is not None:
                    permission_enum = SharePermission.VIEW
                    if permission.lower() == 'comment':
                        permission_enum = SharePermission.COMMENT
                    elif permission.lower() == 'edit':
                        permission_enum = SharePermission.EDIT
                    share_link.permission = permission_enum
                if is_active is not None:
                    share_link.is_active = is_active
                if expires_at is not None:
                    share_link.expires_at = expires_at
                if max_views is not None:
                    share_link.max_views = max_views
                
                db.commit()
                logger.info(f"Updated share link {share_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update share permissions: {e}")
            return False
    
    def revoke_share_link(self, share_id: int, user_id: int) -> bool:
        """Revoke (disable) a share link"""
        return self.update_share_permissions(share_id, user_id, is_active=False)
    
    def get_share_analytics(self, share_id: int, user_id: int) -> Optional[Dict]:
        """Get analytics for a share link"""
        try:
            with get_db_session() as db:
                # Verify ownership
                share_link = db.query(SharedLink).filter(
                    SharedLink.id == share_id,
                    SharedLink.created_by_id == user_id
                ).first()
                
                if not share_link:
                    return None
                
                # Get access logs
                access_logs = db.query(ShareAccessLog).filter(
                    ShareAccessLog.shared_link_id == share_id
                ).order_by(ShareAccessLog.accessed_at.desc()).limit(100).all()
                
                # Get unique visitors
                unique_ips = set()
                unique_users = set()
                
                access_details = []
                for log in access_logs:
                    if log.ip_address:
                        unique_ips.add(log.ip_address)
                    
                    access_details.append({
                        'accessed_at': log.accessed_at,
                        'ip_address': log.ip_address,
                        'user': None
                    })
                
                return {
                    'total_views': share_link.view_count,
                    'unique_visitors': len(unique_ips),
                    'unique_users': len(unique_users),
                    'last_accessed': share_link.last_accessed,
                    'recent_accesses': access_details
                }
                
        except Exception as e:
            logger.error(f"Failed to get share analytics: {e}")
            return None

# Global share manager instance
share_manager = ShareManager()

# Convenience functions
def create_share_link(transcript_id: int, user_id: int, **kwargs) -> Optional[SharedLink]:
    """Create a new share link"""
    return share_manager.create_share_link(transcript_id, user_id, **kwargs)

def get_share_info(share_token: str) -> Optional[Dict]:
    """Get share link information"""
    return share_manager.get_share_link_info(share_token)

def validate_share_access(share_token: str, **kwargs) -> Tuple[bool, Optional[str], Optional[SharedLink]]:
    """Validate access to a share link"""
    return share_manager.validate_share_access(share_token, **kwargs)

def revoke_share_link(share_id: int, user_id: int) -> bool:
    """Revoke a share link"""
    return share_manager.revoke_share_link(share_id, user_id)

def update_share_permissions(share_id: int, user_id: int, **kwargs) -> bool:
    """Update share link permissions"""
    return share_manager.update_share_permissions(share_id, user_id, **kwargs)