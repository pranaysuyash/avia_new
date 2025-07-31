#!/usr/bin/env python3
"""
Share UI Components for Audio/Video Transcription App
Provides Streamlit UI for creating, managing, and accessing shared transcripts
"""

import streamlit as st
from datetime import datetime, timedelta
import logging
from typing import Optional, Dict

from .share_manager import share_manager
from auth import require_authentication, get_current_user
from database import get_db_session
from database.models import Transcript, SharedLink

logger = logging.getLogger(__name__)

def render_share_dialog(transcript_id: int):
    """Render the share dialog for creating share links"""
    user = get_current_user()
    if not user:
        st.error("You must be logged in to share transcripts")
        return
    
    # Get transcript info
    with get_db_session() as db:
        transcript = db.query(Transcript).filter(
            Transcript.id == transcript_id,
            Transcript.user_id == user.id
        ).first()
        
        if not transcript:
            st.error("Transcript not found or you don't have permission")
            return
    
    st.subheader(f"Share: {transcript.title}")
    
    # Share settings
    col1, col2 = st.columns(2)
    
    with col1:
        # Permission level
        permissions = st.selectbox(
            "Permission Level",
            ["view", "comment", "edit"],
            help="What can people with this link do?"
        )
        
        # Expiration
        expiration_option = st.selectbox(
            "Link Expiration",
            ["Never", "1 day", "7 days", "30 days", "90 days", "Custom"],
            index=3  # Default to 30 days
        )
        
        expires_in_days = None
        if expiration_option == "1 day":
            expires_in_days = 1
        elif expiration_option == "7 days":
            expires_in_days = 7
        elif expiration_option == "30 days":
            expires_in_days = 30
        elif expiration_option == "90 days":
            expires_in_days = 90
        elif expiration_option == "Custom":
            expires_in_days = st.number_input("Days until expiration", min_value=1, max_value=365, value=30)
        
        # View limit
        enable_view_limit = st.checkbox("Limit number of views")
        max_views = None
        if enable_view_limit:
            max_views = st.number_input("Maximum views", min_value=1, max_value=10000, value=100)
    
    with col2:
        # Security options
        st.markdown("**Security Options**")
        
        # Password protection
        enable_password = st.checkbox("Password protect")
        password = None
        if enable_password:
            password = st.text_input("Set password", type="password")
            password_confirm = st.text_input("Confirm password", type="password")
            if password and password != password_confirm:
                st.error("Passwords don't match")
                password = None
        
        # Login requirement
        require_login = st.checkbox("Require login to view")
        
        # Email restriction
        enable_email_restriction = st.checkbox("Restrict to specific emails")
        allowed_emails = None
        if enable_email_restriction:
            email_list = st.text_area(
                "Allowed emails (one per line)",
                help="Only these email addresses can access the link"
            )
            if email_list:
                allowed_emails = [email.strip() for email in email_list.split('\n') if email.strip()]
    
    # Generate button
    if st.button("Generate Share Link", type="primary"):
        # Create share link
        share_link = share_manager.create_share_link(
            transcript_id=transcript_id,
            created_by_user_id=user.id,
            permissions=permissions,
            expires_in_days=expires_in_days,
            password=password,
            max_views=max_views,
            require_login=require_login,
            allowed_emails=allowed_emails
        )
        
        if share_link:
            # Generate full URL (in production, use actual domain)
            base_url = st.session_state.get('base_url', 'http://localhost:8501')
            share_url = f"{base_url}/?share={share_link.share_token}"
            
            st.success("Share link created successfully!")
            
            # Display share link
            st.text_input("Share URL", value=share_url, disabled=True)
            
            # Copy button
            st.code(share_url, language=None)
            
            # Show settings summary
            with st.expander("Share Settings"):
                st.write(f"**Permissions:** {permissions}")
                if expires_in_days:
                    st.write(f"**Expires:** In {expires_in_days} days")
                else:
                    st.write("**Expires:** Never")
                if max_views:
                    st.write(f"**View limit:** {max_views} views")
                if password:
                    st.write("**Password:** Required")
                if require_login:
                    st.write("**Login:** Required")
                if allowed_emails:
                    st.write(f"**Restricted to:** {len(allowed_emails)} email(s)")
        else:
            st.error("Failed to create share link")

def render_public_share_page(share_token: str):
    """Render the public page for accessing a shared transcript"""
    # Get share info
    share_info = share_manager.get_share_link_info(share_token)
    
    if not share_info:
        st.error("Invalid or expired share link")
        return
    
    # Check if login required
    user = get_current_user()
    if share_info['require_login'] and not user:
        st.warning("This shared transcript requires you to be logged in")
        st.info("Please log in to continue")
        return
    
    # Password check
    password_verified = False
    if share_info['has_password']:
        if 'share_passwords' not in st.session_state:
            st.session_state.share_passwords = {}
        
        # Check if password already verified for this token
        if share_token in st.session_state.share_passwords:
            password_verified = True
        else:
            st.subheader("Password Required")
            password = st.text_input("Enter password to access this transcript", type="password")
            
            if st.button("Submit"):
                # Validate access with password
                is_valid, error_msg, share_link = share_manager.validate_share_access(
                    share_token=share_token,
                    password=password,
                    user_email=user.email if user else None,
                    user_id=user.id if user else None,
                    ip_address=st.session_state.get('client_ip')
                )
                
                if is_valid:
                    st.session_state.share_passwords[share_token] = True
                    password_verified = True
                    st.rerun()
                else:
                    st.error(error_msg or "Invalid password")
            
            if not password_verified:
                return
    else:
        password_verified = True
    
    # Validate access (without password since already checked)
    is_valid, error_msg, share_link = share_manager.validate_share_access(
        share_token=share_token,
        password=None,  # Already verified above
        user_email=user.email if user else None,
        user_id=user.id if user else None,
        ip_address=st.session_state.get('client_ip')
    )
    
    if not is_valid:
        st.error(error_msg or "Access denied")
        return
    
    # Get transcript
    with get_db_session() as db:
        transcript = db.query(Transcript).filter(
            Transcript.id == share_info['transcript_id']
        ).first()
        
        if not transcript:
            st.error("Transcript not found")
            return
    
    # Display transcript info
    st.title(transcript.title)
    
    # Show metadata
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Created", transcript.created_at.strftime("%Y-%m-%d"))
    with col2:
        st.metric("Duration", f"{transcript.duration_seconds // 60}:{transcript.duration_seconds % 60:02d}")
    with col3:
        st.metric("Shared by", share_info['created_by'])
    
    # Permission indicator
    permission_colors = {
        'view': 'blue',
        'comment': 'orange',
        'edit': 'green'
    }
    st.markdown(
        f"<span style='color: {permission_colors.get(share_info['permissions'], 'gray')}'>Permission: {share_info['permissions'].upper()}</span>",
        unsafe_allow_html=True
    )
    
    # Show transcript content
    st.markdown("---")
    
    if share_info['permissions'] in ['view', 'comment', 'edit']:
        # View permission - show transcript
        if transcript.transcript_data:
            try:
                import json
                data = json.loads(transcript.transcript_data)
                
                # Display segments
                for segment in data.get('segments', []):
                    col1, col2 = st.columns([1, 5])
                    with col1:
                        st.caption(f"{segment.get('start', 0):.1f}s")
                    with col2:
                        st.write(segment.get('text', ''))
                
            except Exception as e:
                st.error("Error displaying transcript")
                logger.error(f"Failed to parse transcript data: {e}")
        else:
            st.info("No transcript content available")
    
    # Comment section (if permission allows)
    if share_info['permissions'] in ['comment', 'edit']:
        st.markdown("---")
        st.subheader("Comments")
        st.info("Comment functionality coming soon")
    
    # Edit section (if permission allows)
    if share_info['permissions'] == 'edit':
        st.markdown("---")
        st.subheader("Edit Transcript")
        st.info("Edit functionality coming soon")
    
    # Footer info
    st.markdown("---")
    st.caption(f"This link has been viewed {share_info['view_count']} time(s)")
    if share_info['expires_at']:
        expires = datetime.fromisoformat(str(share_info['expires_at']))
        if expires > datetime.utcnow():
            days_left = (expires - datetime.utcnow()).days
            st.caption(f"Link expires in {days_left} day(s)")
        else:
            st.caption("This link has expired")

@require_authentication
def render_share_management_page():
    """Render the share management page for users"""
    user = get_current_user()
    
    st.title("Manage Shared Links")
    
    # Get user's share links
    share_links = share_manager.get_user_share_links(user.id)
    
    if not share_links:
        st.info("You haven't created any share links yet")
        return
    
    # Display share links
    for link in share_links:
        with st.expander(f"{link['transcript_title']} - {link['share_token'][:8]}..."):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Views", link['view_count'])
                if link['max_views']:
                    st.caption(f"Max: {link['max_views']}")
            
            with col2:
                st.metric("Permission", link['permissions'].upper())
                
            with col3:
                if link['expires_at']:
                    expires = datetime.fromisoformat(str(link['expires_at']))
                    if expires > datetime.utcnow():
                        days_left = (expires - datetime.utcnow()).days
                        st.metric("Expires", f"{days_left} days")
                    else:
                        st.metric("Status", "EXPIRED")
                else:
                    st.metric("Expires", "Never")
            
            # Status and actions
            col1, col2 = st.columns(2)
            
            with col1:
                if link['is_active']:
                    st.success("Active")
                else:
                    st.error("Revoked")
            
            with col2:
                if link['is_active']:
                    if st.button(f"Revoke", key=f"revoke_{link['id']}"):
                        if share_manager.revoke_share_link(link['id'], user.id):
                            st.success("Link revoked")
                            st.rerun()
                        else:
                            st.error("Failed to revoke link")
            
            # Show full URL
            base_url = st.session_state.get('base_url', 'http://localhost:8501')
            share_url = f"{base_url}/?share={link['share_token']}"
            st.text_input("Share URL", value=share_url, disabled=True, key=f"url_{link['id']}")
            
            # Analytics
            if st.button(f"View Analytics", key=f"analytics_{link['id']}"):
                analytics = share_manager.get_share_analytics(link['id'], user.id)
                if analytics:
                    st.write("**Access Analytics:**")
                    st.write(f"- Total views: {analytics['total_views']}")
                    st.write(f"- Unique visitors: {analytics['unique_visitors']}")
                    st.write(f"- Logged-in users: {analytics['unique_users']}")
                    
                    if analytics['recent_accesses']:
                        st.write("**Recent Access:**")
                        for access in analytics['recent_accesses'][:5]:
                            access_info = f"{access['accessed_at']}"
                            if access['user']:
                                access_info += f" - {access['user']['username']}"
                            elif access['ip_address']:
                                access_info += f" - {access['ip_address']}"
                            st.caption(access_info)