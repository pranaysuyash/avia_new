"""
Test script for annotation system
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Transcript, Annotation, UserRole
from annotations.annotation_manager import AnnotationManager
from auth.auth_manager import AuthManager


def test_annotation_system():
    """Test the annotation system functionality"""
    
    print("Testing Annotation System...")
    
    # Set up in-memory database for testing
    from sqlalchemy import create_engine
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    # Create session
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create managers
    auth_manager = AuthManager()  # Uses its own session
    annotation_manager = AnnotationManager(session)
    
    try:
        # Create test users directly (bypass email validation for testing)
        print("\n1. Creating test users...")
        
        # Create users directly
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user1 = User(
            email="alice@test.local",
            username="alice",
            password_hash=pwd_context.hash("password123"),
            role=UserRole.USER,
            is_verified=True
        )
        session.add(user1)
        
        user2 = User(
            email="bob@test.local",
            username="bob", 
            password_hash=pwd_context.hash("password123"),
            role=UserRole.USER,
            is_verified=True
        )
        session.add(user2)
        session.commit()
        
        print(f"✅ Created users: {user1.username}, {user2.username}")
        
        # Create test transcript
        print("\n2. Creating test transcript...")
        transcript = Transcript(
            user_id=user1.id,
            title="Test Meeting Transcript",
            file_name="test_meeting.mp3",
            content="Hello everyone, welcome to our meeting.\nToday we'll discuss the new features.\nLet's start with the roadmap.",
            summary="Meeting about new features and roadmap",
            duration=180.0,
            word_count=20
        )
        session.add(transcript)
        session.commit()
        print(f"✅ Created transcript: {transcript.title}")
        
        # Test 1: Create annotation without position
        print("\n3. Testing annotation creation...")
        ann1 = annotation_manager.create_annotation(
            transcript_id=transcript.id,
            user_id=user1.id,
            content="This is a great introduction!"
        )
        print(f"✅ Created annotation {ann1.id} by {ann1.user.username}")
        
        # Test 2: Create annotation with highlighted text
        print("\n4. Testing annotation with highlight...")
        ann2 = annotation_manager.create_annotation(
            transcript_id=transcript.id,
            user_id=user2.id,
            content="Should we elaborate on which features?",
            position_start=48,
            position_end=68,
            highlighted_text="new features"
        )
        print(f"✅ Created annotation {ann2.id} with highlight: '{ann2.highlighted_text}'")
        
        # Test 3: Create reply
        print("\n5. Testing replies...")
        reply1 = annotation_manager.create_annotation(
            transcript_id=transcript.id,
            user_id=user1.id,
            content="Yes, let me list them in the next section",
            parent_id=ann2.id
        )
        print(f"✅ Created reply {reply1.id} to annotation {ann2.id}")
        
        # Test 4: Get annotations
        print("\n6. Testing annotation retrieval...")
        annotations = annotation_manager.get_transcript_annotations(transcript.id)
        print(f"✅ Retrieved {len(annotations)} annotations")
        for ann in annotations:
            prefix = "  ↳ " if ann.parent_id else ""
            print(f"{prefix}[{ann.user.username}]: {ann.content[:50]}...")
        
        # Test 5: Update annotation
        print("\n7. Testing annotation update...")
        updated = annotation_manager.update_annotation(
            ann1.id,
            user1.id,
            content="This is a great introduction! Looking forward to the details."
        )
        print(f"✅ Updated annotation content")
        
        # Test 6: Resolve annotation
        print("\n8. Testing annotation resolution...")
        resolved = annotation_manager.resolve_annotation(ann2.id, user2.id)
        print(f"✅ Marked annotation as resolved: {resolved.is_resolved}")
        
        # Test 7: Get stats
        print("\n9. Testing annotation statistics...")
        stats = annotation_manager.get_annotation_stats(transcript.id)
        print(f"✅ Stats: {stats}")
        
        # Test 8: Search annotations
        print("\n10. Testing annotation search...")
        search_results = annotation_manager.search_annotations(
            transcript.id, "features"
        )
        print(f"✅ Found {len(search_results)} annotations containing 'features'")
        
        # Test 9: Export annotations
        print("\n11. Testing annotation export...")
        markdown_export = annotation_manager.export_annotations(
            transcript.id, format='markdown'
        )
        print(f"✅ Exported to markdown ({len(markdown_export)} chars)")
        print("\nMarkdown preview:")
        print(markdown_export[:200] + "...")
        
        # Test 10: Test with mentions
        print("\n12. Testing mentions...")
        ann_with_mention = annotation_manager.create_annotation(
            transcript_id=transcript.id,
            user_id=user1.id,
            content="@bob what do you think about this approach?"
        )
        print(f"✅ Created annotation with mention to @bob")
        
        # Test 11: Get thread context
        print("\n13. Testing thread context...")
        thread = annotation_manager.get_thread_context(reply1.id)
        print(f"✅ Thread has {len(thread)} messages")
        
        # Test 12: Merge with transcript
        print("\n14. Testing transcript merge...")
        merged = annotation_manager.merge_annotations_with_transcript(
            transcript.id, transcript.content
        )
        print(f"✅ Merged transcript length: {len(merged)} chars (original: {len(transcript.content)})")
        
        print("\n✅ All tests passed!")
        
        # Show final summary
        print("\n📊 Final Summary:")
        print(f"- Total annotations: {stats['total_annotations']}")
        print(f"- Resolved: {stats['resolved_count']}")
        print(f"- Users involved: {stats['unique_users']}")
        print(f"- Top contributor: {stats['top_contributor']}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()


if __name__ == "__main__":
    success = test_annotation_system()
    sys.exit(0 if success else 1)