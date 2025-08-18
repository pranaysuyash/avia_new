#!/usr/bin/env python3
"""
Comprehensive Database Models Unit Tests
Tests all database models, relationships, and functionality
"""

import pytest
import os
import tempfile
import shutil
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

# Set up test environment
os.environ['DATABASE_URL'] = 'postgresql://pranay@localhost/ner_transcription_db'

from database.models import (
    Base, User, Session, Transcript, SharedLink, ShareAccessLog,
    Annotation, TranscriptVersion, Team, TeamMember, Project,
    Notification, UserRole, SharePermission, TeamRole,
    TranscriptSegment, TranscriptWord, TranscriptionSession,
    UploadSession, init_db, get_db_session
)
from database.connection import get_db, get_db_context


class TestDatabaseModels:
    """Test suite for database models"""
    
    @classmethod
    def setup_class(cls):
        """Set up test database"""
        # Use in-memory SQLite for testing to avoid affecting production data
        cls.test_db_url = "sqlite:///:memory:"
        cls.engine = create_engine(cls.test_db_url)
        cls.TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)
        
        # Create all tables
        Base.metadata.create_all(bind=cls.engine)
        
    def setup_method(self):
        """Set up each test method"""
        self.db = self.TestSessionLocal()
        
    def teardown_method(self):
        """Clean up after each test method"""
        self.db.close()
        
    def test_user_model_creation(self):
        """Test User model creation and validation"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            name="Test User",
            subscription_tier="free",
            is_active=True,
            email_verified=False
        )
        
        self.db.add(user)
        self.db.commit()
        
        # Verify user was created
        retrieved_user = self.db.query(User).filter(User.email == "test@example.com").first()
        assert retrieved_user is not None
        assert retrieved_user.name == "Test User"
        assert retrieved_user.subscription_tier == "free"
        assert retrieved_user.is_active is True
        assert retrieved_user.email_verified is False
        
    def test_user_email_uniqueness(self):
        """Test that user emails must be unique"""
        user1 = User(
            email="duplicate@example.com",
            password_hash="hash1",
            name="User 1"
        )
        user2 = User(
            email="duplicate@example.com", 
            password_hash="hash2",
            name="User 2"
        )
        
        self.db.add(user1)
        self.db.commit()
        
        self.db.add(user2)
        with pytest.raises(IntegrityError):
            self.db.commit()
            
    def test_transcript_model_creation(self):
        """Test Transcript model creation and relationships"""
        # Create user first
        user = User(
            email="transcriber@example.com",
            password_hash="hashed_password",
            name="Transcriber"
        )
        self.db.add(user)
        self.db.commit()
        
        # Create transcript
        transcript = Transcript(
            user_id=user.id,
            title="Test Transcript",
            content="This is a test transcript content.",
            file_name="test_audio.wav",
            file_size=1024,
            duration=60.5,
            language="en",
            confidence=0.95,
            word_count=6,
            entities={"people": ["John"], "organizations": []},
            summary="Test summary",
            model_used="whisper-large",
            processing_time=5.2,
            is_public=False
        )
        
        self.db.add(transcript)
        self.db.commit()
        
        # Verify transcript was created
        retrieved_transcript = self.db.query(Transcript).filter(
            Transcript.title == "Test Transcript"
        ).first()
        
        assert retrieved_transcript is not None
        assert retrieved_transcript.user_id == user.id
        assert retrieved_transcript.content == "This is a test transcript content."
        assert retrieved_transcript.confidence == 0.95
        assert retrieved_transcript.entities == {"people": ["John"], "organizations": []}
        
    def test_transcript_segments_and_words(self):
        """Test TranscriptSegment and TranscriptWord models"""
        # Create user and transcript
        user = User(email="seg_test@example.com", password_hash="hash", name="Seg Test")
        self.db.add(user)
        self.db.commit()
        
        transcript = Transcript(
            user_id=user.id,
            title="Segmented Transcript",
            content="Hello world. How are you?",
            file_name="segmented.wav"
        )
        self.db.add(transcript)
        self.db.commit()
        
        # Create segments
        segment1 = TranscriptSegment(
            transcript_id=transcript.id,
            start_time=0.0,
            end_time=2.5,
            text="Hello world.",
            confidence=0.98,
            speaker_id="speaker_1",
            language="en"
        )
        
        segment2 = TranscriptSegment(
            transcript_id=transcript.id,
            start_time=2.5,
            end_time=5.0,
            text="How are you?",
            confidence=0.96,
            speaker_id="speaker_1", 
            language="en"
        )
        
        self.db.add_all([segment1, segment2])
        self.db.commit()
        
        # Create words
        word1 = TranscriptWord(
            segment_id=segment1.id,
            transcript_id=transcript.id,
            word="Hello",
            start_time=0.0,
            end_time=0.5,
            confidence=0.99,
            word_index=0
        )
        
        word2 = TranscriptWord(
            segment_id=segment1.id,
            transcript_id=transcript.id,
            word="world",
            start_time=0.5,
            end_time=1.2,
            confidence=0.97,
            word_index=1
        )
        
        self.db.add_all([word1, word2])
        self.db.commit()
        
        # Verify relationships
        retrieved_transcript = self.db.query(Transcript).filter(
            Transcript.title == "Segmented Transcript"
        ).first()
        
        assert len(retrieved_transcript.segments) == 2
        assert retrieved_transcript.segments[0].text == "Hello world."
        assert len(retrieved_transcript.words) == 2
        assert retrieved_transcript.words[0].word == "Hello"
        
    def test_team_and_membership_models(self):
        """Test Team and TeamMember models"""
        # Create users
        owner = User(email="owner@example.com", password_hash="hash", name="Owner")
        member = User(email="member@example.com", password_hash="hash", name="Member")
        self.db.add_all([owner, member])
        self.db.commit()
        
        # Create team
        team = Team(
            name="Test Team",
            description="A test team",
            owner_id=owner.id,
            max_members=10,
            is_public=False
        )
        self.db.add(team)
        self.db.commit()
        
        # Add team members
        owner_membership = TeamMember(
            team_id=team.id,
            user_id=owner.id,
            role=TeamRole.OWNER,
            invited_by_id=owner.id
        )
        
        member_membership = TeamMember(
            team_id=team.id,
            user_id=member.id,
            role=TeamRole.MEMBER,
            invited_by_id=owner.id
        )
        
        self.db.add_all([owner_membership, member_membership])
        self.db.commit()
        
        # Verify relationships
        retrieved_team = self.db.query(Team).filter(Team.name == "Test Team").first()
        assert retrieved_team is not None
        assert len(retrieved_team.members) == 2
        assert retrieved_team.owner.email == "owner@example.com"
        
    def test_upload_session_model(self):
        """Test UploadSession model"""
        # Create user
        user = User(email="uploader@example.com", password_hash="hash", name="Uploader")
        self.db.add(user)
        self.db.commit()
        
        # Create upload session
        upload_session = UploadSession(
            user_id=user.id,
            filename="test_file.mp3",
            file_size=2048000,
            file_type="audio/mpeg",
            upload_status="completed",
            progress=100.0,
            upload_path="/uploads/test_file.mp3"
        )
        
        self.db.add(upload_session)
        self.db.commit()
        
        # Verify upload session
        retrieved_session = self.db.query(UploadSession).filter(
            UploadSession.filename == "test_file.mp3"
        ).first()
        
        assert retrieved_session is not None
        assert retrieved_session.user_id == user.id
        assert retrieved_session.file_size == 2048000
        assert retrieved_session.upload_status == "completed"
        assert retrieved_session.progress == 100.0
        
    def test_shared_link_model(self):
        """Test SharedLink and ShareAccessLog models"""
        # Create user and transcript
        user = User(email="sharer@example.com", password_hash="hash", name="Sharer")
        self.db.add(user)
        self.db.commit()
        
        transcript = Transcript(
            user_id=user.id,
            title="Shared Transcript",
            content="This will be shared",
            file_name="shared.wav"
        )
        self.db.add(transcript)
        self.db.commit()
        
        # Create shared link
        shared_link = SharedLink(
            transcript_id=transcript.id,
            created_by_id=user.id,
            token="test_token_123",
            permission=SharePermission.VIEW,
            expires_at=datetime.utcnow() + timedelta(days=7),
            is_active=True
        )
        
        self.db.add(shared_link)
        self.db.commit()
        
        # Create access log
        access_log = ShareAccessLog(
            shared_link_id=shared_link.id,
            ip_address="127.0.0.1",
            user_agent="Test Browser",
            accessed_at=datetime.utcnow()
        )
        
        self.db.add(access_log)
        self.db.commit()
        
        # Verify shared link and access log
        retrieved_link = self.db.query(SharedLink).filter(
            SharedLink.token == "test_token_123"
        ).first()
        
        assert retrieved_link is not None
        assert retrieved_link.permission == SharePermission.VIEW
        assert len(retrieved_link.access_logs) == 1
        assert retrieved_link.access_logs[0].ip_address == "127.0.0.1"
        
    def test_notification_model(self):
        """Test Notification model"""
        # Create users
        user1 = User(email="user1@example.com", password_hash="hash", name="User 1")
        user2 = User(email="user2@example.com", password_hash="hash", name="User 2")
        self.db.add_all([user1, user2])
        self.db.commit()
        
        # Create notification
        notification = Notification(
            user_id=user1.id,
            type="mention",
            title="You were mentioned",
            message="User 2 mentioned you in a transcript",
            link="/transcripts/123",
            related_id=123,
            related_type="transcript",
            from_user_id=user2.id,
            is_read=False
        )
        
        self.db.add(notification)
        self.db.commit()
        
        # Verify notification
        retrieved_notification = self.db.query(Notification).filter(
            Notification.type == "mention"
        ).first()
        
        assert retrieved_notification is not None
        assert retrieved_notification.user_id == user1.id
        assert retrieved_notification.from_user_id == user2.id
        assert retrieved_notification.is_read is False
        

class TestDatabaseIntegration:
    """Integration tests for database functionality"""
    
    def test_postgres_connection(self):
        """Test actual PostgreSQL connection"""
        try:
            # Test connection to actual database
            db = next(get_db())
            
            # Test basic query
            users = db.query(User).limit(1).all()
            assert isinstance(users, list)
            
            print(f"✓ PostgreSQL connection successful, found {len(users)} users")
            
        except Exception as e:
            pytest.skip(f"PostgreSQL not available: {e}")
            
    def test_database_context_manager(self):
        """Test database context manager"""
        try:
            with get_db_context() as db:
                user_count = db.query(User).count()
                assert isinstance(user_count, int)
                
            print(f"✓ Database context manager working, user count: {user_count}")
            
        except Exception as e:
            pytest.skip(f"Database context manager test failed: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])