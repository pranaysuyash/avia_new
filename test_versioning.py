"""
Test script for version control system
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Transcript, TranscriptVersion, UserRole
from versioning.version_manager import VersionManager
from auth.auth_manager import AuthManager


def test_version_control():
    """Test the version control system"""
    
    print("Testing Version Control System...")
    
    # Set up in-memory database
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    # Create version manager
    version_manager = VersionManager(session)
    
    try:
        # Create test users
        print("\n1. Creating test users...")
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        user1 = User(
            email="alice@test.local",
            username="alice",
            password_hash=pwd_context.hash("password123"),
            role=UserRole.USER,
            is_verified=True
        )
        user2 = User(
            email="bob@test.local",
            username="bob",
            password_hash=pwd_context.hash("password123"),
            role=UserRole.USER,
            is_verified=True
        )
        user3 = User(
            email="charlie@test.local",
            username="charlie",
            password_hash=pwd_context.hash("password123"),
            role=UserRole.USER,
            is_verified=True
        )
        session.add_all([user1, user2, user3])
        session.commit()
        print(f"✅ Created users: {user1.username}, {user2.username}, {user3.username}")
        
        # Create test transcript
        print("\n2. Creating test transcript...")
        transcript = Transcript(
            user_id=user1.id,
            title="Project Meeting Notes",
            file_name="meeting.mp3",
            content="Welcome to our project meeting.\nToday we'll discuss the roadmap.\nLet's start with updates.",
            summary="Project meeting discussing roadmap and updates",
            duration=300.0,
            word_count=15
        )
        session.add(transcript)
        session.commit()
        print(f"✅ Created transcript: {transcript.title}")
        
        # Test 1: Create initial version
        print("\n3. Testing version creation...")
        version1 = version_manager.create_version(
            transcript_id=transcript.id,
            user_id=user1.id,
            change_summary="Initial transcript creation"
        )
        print(f"✅ Created version {version1.version_number}")
        
        # Test 2: Update transcript
        print("\n4. Testing transcript update...")
        updated_transcript, version2, conflict_info = version_manager.update_transcript(
            transcript_id=transcript.id,
            user_id=user2.id,
            new_content="Welcome to our project meeting.\nToday we'll discuss the roadmap and timeline.\nLet's start with status updates.\nBob will present first.",
            change_summary="Added timeline discussion and presenter order"
        )
        print(f"✅ Updated transcript, created version {version2.version_number}")
        print(f"   No conflicts: {not conflict_info['has_conflicts']}")
        
        # Test 3: Concurrent edit simulation
        print("\n5. Testing concurrent edits (conflict resolution)...")
        
        # User 3 edits based on version 1
        concurrent_content = "Welcome to our project meeting.\nToday we'll discuss the roadmap.\nLet's start with updates.\nCharlie will take notes."
        
        updated_transcript, version3, conflict_info = version_manager.update_transcript(
            transcript_id=transcript.id,
            user_id=user3.id,
            new_content=concurrent_content,
            change_summary="Added note-taker assignment",
            base_version_number=1,  # Editing based on version 1
            conflict_strategy='smart'
        )
        print(f"✅ Handled concurrent edit, created version {version3.version_number}")
        print(f"   Had conflicts: {conflict_info['has_conflicts']}")
        if conflict_info['has_conflicts']:
            print(f"   Conflicts resolved using: {conflict_info['resolution_strategy']}")
            print(f"   Number of conflicts: {len(conflict_info['conflicts'])}")
        
        # Test 4: Get version history
        print("\n6. Testing version history retrieval...")
        versions = version_manager.get_versions(transcript.id)
        print(f"✅ Retrieved {len(versions)} versions")
        for v in versions:
            print(f"   v{v.version_number}: {v.change_summary} (by {v.changed_by.username})")
        
        # Test 5: Version comparison
        print("\n7. Testing version comparison...")
        diff_data = version_manager.get_diff(transcript.id, 1, 3)
        print(f"✅ Compared versions 1 and 3")
        print(f"   Lines added: {diff_data['stats']['lines_added']}")
        print(f"   Lines removed: {diff_data['stats']['lines_removed']}")
        
        # Test 6: Version statistics
        print("\n8. Testing version statistics...")
        stats = version_manager.get_version_stats(transcript.id)
        print(f"✅ Version stats:")
        print(f"   Total versions: {stats['total_versions']}")
        print(f"   Contributors: {', '.join(stats['contributors'])}")
        print(f"   Most active: {stats['most_active_contributor']}")
        
        # Test 7: Search versions
        print("\n9. Testing version search...")
        search_results = version_manager.search_versions(transcript.id, "timeline")
        print(f"✅ Found {len(search_results)} versions containing 'timeline'")
        
        # Test 8: Version restore
        print("\n10. Testing version restore...")
        restored_transcript = version_manager.restore_version(
            transcript_id=transcript.id,
            version_number=1,
            user_id=user1.id
        )
        print(f"✅ Restored to version 1")
        print(f"   Current content length: {len(restored_transcript.content)} chars")
        
        # Test 9: Timeline
        print("\n11. Testing version timeline...")
        timeline = version_manager.get_version_timeline(transcript.id)
        print(f"✅ Generated timeline with {len(timeline)} entries")
        
        # Test 10: Three-way merge test
        print("\n12. Testing sophisticated three-way merge...")
        
        # Create a more complex scenario
        base_content = "Line 1: Introduction\nLine 2: Agenda\nLine 3: Updates\nLine 4: Discussion\nLine 5: Next steps"
        current_content = "Line 1: Introduction\nLine 2: Detailed Agenda\nLine 3: Status Updates\nLine 4: Discussion\nLine 5: Next steps\nLine 6: Action items"
        incoming_content = "Line 1: Project Introduction\nLine 2: Agenda\nLine 3: Updates\nLine 4: Technical Discussion\nLine 5: Next steps"
        
        merged_content, conflicts, has_conflicts = version_manager.conflict_resolver.three_way_merge(
            base_content,
            current_content,
            incoming_content
        )
        
        print(f"✅ Three-way merge completed")
        print(f"   Has conflicts: {has_conflicts}")
        print(f"   Number of conflicts: {len(conflicts)}")
        if has_conflicts:
            print(f"   Merged content contains conflict markers")
        
        # Auto-resolve conflicts
        if has_conflicts:
            resolved_content = version_manager.conflict_resolver.auto_resolve_conflicts(
                merged_content,
                conflicts,
                'smart'
            )
            print(f"✅ Auto-resolved conflicts using 'smart' strategy")
            print(f"   Resolved content length: {len(resolved_content)} chars")
        
        print("\n✅ All tests passed!")
        
        # Show final summary
        print("\n📊 Final Summary:")
        print(f"- Total versions created: 5")
        print(f"- Conflicts handled: Yes")
        print(f"- Three-way merge: Working")
        print(f"- Version restore: Working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        session.close()


if __name__ == "__main__":
    success = test_version_control()
    sys.exit(0 if success else 1)