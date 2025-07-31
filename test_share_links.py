#!/usr/bin/env python3
"""
Test script for share link functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sharing import share_manager
from database import init_db, get_db_session
from database.models import User, Transcript
import json
from datetime import datetime

def test_share_link_creation():
    """Test creating and validating share links"""
    print("Testing share link functionality...")
    
    # Initialize database
    init_db()
    
    # Create test user and transcript
    with get_db_session() as db:
        # Check if test user exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                username="testuser",
                password_hash="dummy_hash"
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
        
        # Create test transcript
        test_transcript = Transcript(
            user_id=test_user.id,
            title="Test Transcript for Sharing",
            duration=300.0,
            content=json.dumps({
                "segments": [
                    {"start": 0, "end": 5, "text": "Hello world"},
                    {"start": 5, "end": 10, "text": "This is a test"}
                ]
            }),
            language="en",
            word_count=10,
            model_used="test"
        )
        db.add(test_transcript)
        db.commit()
        db.refresh(test_transcript)
        
        print(f"Created test user: {test_user.username} (ID: {test_user.id})")
        print(f"Created test transcript: {test_transcript.title} (ID: {test_transcript.id})")
    
    # Test 1: Create basic share link
    print("\n1. Testing basic share link creation...")
    share_link = share_manager.create_share_link(
        transcript_id=test_transcript.id,
        created_by_id=test_user.id,
        permission='view'
    )
    
    if share_link:
        print(f"✓ Created share link: {share_link.share_token}")
        print(f"  - Permissions: {share_link.permission.value}")
        print(f"  - Expires: {share_link.expires_at}")
    else:
        print("✗ Failed to create share link")
        return
    
    # Test 2: Get share link info
    print("\n2. Testing get share link info...")
    info = share_manager.get_share_link_info(share_link.share_token)
    if info:
        print(f"✓ Retrieved share link info:")
        print(f"  - Token: {info['share_token']}")
        print(f"  - Transcript: {info['transcript_title']}")
        print(f"  - Created by: {info['created_by']}")
        print(f"  - Views: {info['view_count']}")
    else:
        print("✗ Failed to get share link info")
    
    # Test 3: Validate access
    print("\n3. Testing share link access validation...")
    is_valid, error_msg, validated_link = share_manager.validate_share_access(
        share_token=share_link.share_token,
        ip_address="127.0.0.1"
    )
    if is_valid:
        print(f"✓ Share link access validated")
        print(f"  - View count incremented to: {validated_link.view_count}")
    else:
        print(f"✗ Share link validation failed: {error_msg}")
    
    # Test 4: Create share link with password
    print("\n4. Testing password-protected share link...")
    password_link = share_manager.create_share_link(
        transcript_id=test_transcript.id,
        created_by_id=test_user.id,
        permission='comment',
        password='secret123',
        expires_in_days=7
    )
    
    if password_link:
        print(f"✓ Created password-protected link: {password_link.share_token}")
        
        # Try access without password
        is_valid, error_msg, _ = share_manager.validate_share_access(
            share_token=password_link.share_token
        )
        print(f"  - Access without password: {'✓' if is_valid else '✗'} {error_msg or ''}")
        
        # Try access with wrong password
        is_valid, error_msg, _ = share_manager.validate_share_access(
            share_token=password_link.share_token,
            password='wrongpass'
        )
        print(f"  - Access with wrong password: {'✓' if is_valid else '✗'} {error_msg or ''}")
        
        # Try access with correct password
        is_valid, error_msg, _ = share_manager.validate_share_access(
            share_token=password_link.share_token,
            password='secret123'
        )
        print(f"  - Access with correct password: {'✓' if is_valid else '✗'}")
    
    # Test 5: Create share link with view limit
    print("\n5. Testing share link with view limit...")
    limited_link = share_manager.create_share_link(
        transcript_id=test_transcript.id,
        created_by_id=test_user.id,
        permission='view',
        max_views=2
    )
    
    if limited_link:
        print(f"✓ Created view-limited link: {limited_link.share_token} (max 2 views)")
        
        # Access twice
        for i in range(3):
            is_valid, error_msg, _ = share_manager.validate_share_access(
                share_token=limited_link.share_token,
                ip_address=f"127.0.0.{i+1}"
            )
            print(f"  - Access attempt {i+1}: {'✓' if is_valid else '✗'} {error_msg or ''}")
    
    # Test 6: Get user's share links
    print("\n6. Testing get user share links...")
    user_links = share_manager.get_user_share_links(test_user.id)
    print(f"✓ Found {len(user_links)} share links for user")
    for link in user_links:
        print(f"  - {link['transcript_title']}: {link['share_token'][:8]}... ({link['view_count']} views)")
    
    # Test 7: Revoke share link
    print("\n7. Testing share link revocation...")
    revoked = share_manager.revoke_share_link(share_link.id, test_user.id)
    if revoked:
        print(f"✓ Share link revoked")
        
        # Try to access revoked link
        is_valid, error_msg, _ = share_manager.validate_share_access(
            share_token=share_link.share_token
        )
        print(f"  - Access after revocation: {'✓' if is_valid else '✗'} {error_msg or ''}")
    
    print("\n✅ Share link testing completed!")

if __name__ == "__main__":
    test_share_link_creation()