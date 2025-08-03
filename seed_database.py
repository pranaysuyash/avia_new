#!/usr/bin/env python3
"""Seed the database with test data"""

from database_config import SessionLocal, init_database
from database.models import User, Transcript
from datetime import datetime, timedelta
import bcrypt

def seed_database():
    # Initialize database
    init_database()
    
    db = SessionLocal()
    
    try:
        # Check if test user exists
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        
        if not test_user:
            # Create test user
            password_hash = bcrypt.hashpw("password".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            test_user = User(
                email="test@example.com",
                username="testuser",
                password_hash=password_hash,
                full_name="Test User",
                is_active=True,
                is_verified=True
            )
            db.add(test_user)
            db.commit()
            print("✅ Created test user")
        
        # Check if we have transcripts
        transcript_count = db.query(Transcript).count()
        
        if transcript_count == 0:
            # Create sample transcripts
            transcripts = [
                Transcript(
                    user_id=test_user.id,
                    title="Q4 2023 Earnings Call",
                    original_filename="earnings_call_q4_2023.mp4",
                    file_path="/uploads/earnings_call_q4_2023.mp4",
                    file_size=52428800,  # 50MB
                    duration=3600,  # 1 hour
                    language="en",
                    status="completed",
                    transcription_text="Welcome to our Q4 2023 earnings call. We had an exceptional quarter with revenue growth of 25%...",
                    confidence_score=0.96,
                    processing_time=120.5,
                    created_at=datetime.now() - timedelta(days=7)
                ),
                Transcript(
                    user_id=test_user.id,
                    title="Product Demo - AI Assistant",
                    original_filename="product_demo_ai_assistant.mp4",
                    file_path="/uploads/product_demo_ai_assistant.mp4",
                    file_size=31457280,  # 30MB
                    duration=1800,  # 30 minutes
                    language="en",
                    status="completed",
                    transcription_text="Today we're excited to show you our new AI assistant. It features natural language processing...",
                    confidence_score=0.98,
                    processing_time=85.3,
                    created_at=datetime.now() - timedelta(days=3)
                ),
                Transcript(
                    user_id=test_user.id,
                    title="Team Standup - March 15",
                    original_filename="standup_03_15_2024.mp3",
                    file_path="/uploads/standup_03_15_2024.mp3",
                    file_size=10485760,  # 10MB
                    duration=900,  # 15 minutes
                    language="en",
                    status="completed",
                    transcription_text="Good morning team. Let's go around and share our updates. John, would you like to start?...",
                    confidence_score=0.94,
                    processing_time=45.2,
                    created_at=datetime.now() - timedelta(days=1)
                ),
                Transcript(
                    user_id=test_user.id,
                    title="Customer Interview - Feedback Session",
                    original_filename="customer_interview_march_2024.mp4",
                    file_path="/uploads/customer_interview_march_2024.mp4", 
                    file_size=41943040,  # 40MB
                    duration=2400,  # 40 minutes
                    language="en",
                    status="processing",
                    processing_time=0,
                    created_at=datetime.now() - timedelta(hours=2)
                ),
                Transcript(
                    user_id=test_user.id,
                    title="Board Meeting Recording",
                    original_filename="board_meeting_q1_2024.mp4",
                    file_path="/uploads/board_meeting_q1_2024.mp4",
                    file_size=104857600,  # 100MB
                    duration=7200,  # 2 hours
                    language="en",
                    status="completed",
                    transcription_text="The board meeting is now in session. First item on the agenda is the financial review...",
                    confidence_score=0.95,
                    processing_time=240.8,
                    created_at=datetime.now() - timedelta(days=14)
                )
            ]
            
            for transcript in transcripts:
                db.add(transcript)
            
            db.commit()
            print(f"✅ Created {len(transcripts)} sample transcripts")
        else:
            print(f"ℹ️  Database already has {transcript_count} transcripts")
            
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()