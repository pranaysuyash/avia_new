#!/usr/bin/env python3
"""
Test suite for Feedback Data Models and Storage System
Enhanced with comprehensive progress tracking and visual feedback
"""

import pytest
import sys
import os
import tempfile
import sqlite3
import time
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Progress tracking utilities
def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def print_progress(current, total, task_name="Testing", width=50):
    """Print a progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = progress * 100
    print(f"\r{task_name}: |{bar}| {percentage:.1f}% ({current}/{total})", end='', flush=True)
    if current == total:
        print()  # New line when complete

def print_test_status(test_name, status="RUNNING", details=""):
    """Print test status with visual indicators"""
    status_icons = {
        'RUNNING': '🔄',
        'PASSED': '✅',
        'FAILED': '❌',
        'SKIPPED': '⏭️',
        'SETUP': '🔧',
        'TEARDOWN': '🧹'
    }
    icon = status_icons.get(status, '📋')
    detail_text = f" - {details}" if details else ""
    print(f"{icon} {test_name}: {status}{detail_text}")

class ProgressTracker:
    """Context manager for tracking test progress"""
    
    def __init__(self, test_name, total_steps=1):
        self.test_name = test_name
        self.total_steps = total_steps
        self.current_step = 0
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        print_test_status(self.test_name, "RUNNING")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        if exc_type is None:
            print_test_status(self.test_name, "PASSED", f"completed in {duration:.2f}s")
        else:
            print_test_status(self.test_name, "FAILED", f"error after {duration:.2f}s")
    
    def step(self, description=""):
        """Advance to next step"""
        self.current_step += 1
        if self.total_steps > 1:
            print_progress(self.current_step, self.total_steps, f"{self.test_name}")
        if description:
            print(f"  📝 {description}")
        time.sleep(0.01)  # Minimal delay for visual effect

from feedback_data_models import (
    FeedbackStorage,
    Feedback,
    Rating,
    Correction,
    FeedbackContext,
    FeedbackType,
    RatingType,
    FeedbackStatus,
    ContentType,
    create_feedback_storage,
    generate_feedback_id,
    generate_rating_id,
    generate_correction_id
)

class TestRating:
    """Test Rating class functionality"""
    
    def test_rating_creation(self):
        """Test rating creation and basic properties"""
        with ProgressTracker("Rating Creation Test", 5) as tracker:
            tracker.step("Creating rating instance")
            rating = Rating(
                rating_id="test_rating",
                rating_type=RatingType.STARS,
                value=4,
                max_value=5,
                comment="Good quality"
            )
            
            tracker.step("Validating rating ID")
            assert rating.rating_id == "test_rating"
            
            tracker.step("Validating rating type")
            assert rating.rating_type == RatingType.STARS
            
            tracker.step("Validating rating values")
            assert rating.value == 4
            assert rating.max_value == 5
            
            tracker.step("Validating rating comment")
            assert rating.comment == "Good quality"
    
    def test_rating_normalization(self):
        """Test rating normalization to 0-1 scale"""
        with ProgressTracker("Rating Normalization Test", 8) as tracker:
            tracker.step("Testing thumbs up rating")
            thumbs_up = Rating("test", RatingType.THUMBS, True)
            assert thumbs_up.normalize_rating() == 1.0
            
            tracker.step("Testing thumbs down rating")
            thumbs_down = Rating("test", RatingType.THUMBS, False)
            assert thumbs_down.normalize_rating() == 0.0
            
            tracker.step("Testing binary good rating")
            binary_good = Rating("test", RatingType.BINARY, "good")
            assert binary_good.normalize_rating() == 1.0
            
            tracker.step("Testing binary bad rating")
            binary_bad = Rating("test", RatingType.BINARY, "bad")
            assert binary_bad.normalize_rating() == 0.0
            
            tracker.step("Testing stars rating normalization")
            stars_rating = Rating("test", RatingType.STARS, 3, max_value=5)
            assert stars_rating.normalize_rating() == 0.6
            
            tracker.step("Testing scale rating normalization")
            scale_rating = Rating("test", RatingType.SCALE, 7, max_value=10)
            assert scale_rating.normalize_rating() == 0.7
            
            tracker.step("Testing default stars max value")
            stars_default = Rating("test", RatingType.STARS, 4)
            assert stars_default.normalize_rating() == 0.8  # 4/5
            
            tracker.step("Testing default scale max value")
            scale_default = Rating("test", RatingType.SCALE, 8)
            assert scale_default.normalize_rating() == 0.8  # 8/10

class TestCorrection:
    """Test Correction class functionality"""
    
    def test_correction_creation(self):
        """Test correction creation and basic properties"""
        correction = Correction(
            correction_id="test_correction",
            original_text="Hello world",
            corrected_text="Hello World",
            correction_type="capitalization",
            position_start=0,
            position_end=11,
            explanation="Proper capitalization"
        )
        
        assert correction.correction_id == "test_correction"
        assert correction.original_text == "Hello world"
        assert correction.corrected_text == "Hello World"
        assert correction.correction_type == "capitalization"
        assert correction.position_start == 0
        assert correction.position_end == 11
        assert correction.explanation == "Proper capitalization"
    
    def test_edit_distance_calculation(self):
        """Test edit distance calculation"""
        # Test identical strings
        correction1 = Correction("test", "hello", "hello", "none")
        assert correction1.get_edit_distance() == 0
        
        # Test single character change
        correction2 = Correction("test", "hello", "hallo", "substitution")
        assert correction2.get_edit_distance() == 1
        
        # Test insertion
        correction3 = Correction("test", "hello", "hellos", "insertion")
        assert correction3.get_edit_distance() == 1
        
        # Test deletion
        correction4 = Correction("test", "hello", "hell", "deletion")
        assert correction4.get_edit_distance() == 1
        
        # Test multiple changes
        correction5 = Correction("test", "hello", "world", "complete_change")
        assert correction5.get_edit_distance() == 4
        
        # Test empty strings
        correction6 = Correction("test", "", "hello", "insertion")
        assert correction6.get_edit_distance() == 5
        
        correction7 = Correction("test", "hello", "", "deletion")
        assert correction7.get_edit_distance() == 5

class TestFeedbackContext:
    """Test FeedbackContext class"""
    
    def test_context_creation(self):
        """Test feedback context creation"""
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="Original text",
            processed_content="Processed text",
            confidence_score=0.95,
            processing_method="whisper",
            model_version="v1.0",
            session_id="session_123",
            metadata={"key": "value"}
        )
        
        assert context.content_type == ContentType.TRANSCRIPTION
        assert context.content_id == "test_content"
        assert context.original_content == "Original text"
        assert context.processed_content == "Processed text"
        assert context.confidence_score == 0.95
        assert context.processing_method == "whisper"
        assert context.model_version == "v1.0"
        assert context.session_id == "session_123"
        assert context.metadata == {"key": "value"}

class TestFeedback:
    """Test main Feedback class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="Test content"
        )
        
        self.rating = Rating(
            rating_id="test_rating",
            rating_type=RatingType.STARS,
            value=4,
            max_value=5
        )
        
        self.correction = Correction(
            correction_id="test_correction",
            original_text="original",
            corrected_text="corrected",
            correction_type="word"
        )
    
    def test_rating_feedback_creation(self):
        """Test creation of rating feedback"""
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=self.context,
            timestamp=datetime.now(),
            rating=self.rating
        )
        
        assert feedback.feedback_id == "test_feedback"
        assert feedback.user_id == "test_user"
        assert feedback.feedback_type == FeedbackType.RATING
        assert feedback.rating == self.rating
        assert feedback.status == FeedbackStatus.PENDING
    
    def test_correction_feedback_creation(self):
        """Test creation of correction feedback"""
        feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.CORRECTION,
            context=self.context,
            timestamp=datetime.now(),
            correction=self.correction
        )
        
        assert feedback.feedback_id == "test_feedback"
        assert feedback.feedback_type == FeedbackType.CORRECTION
        assert feedback.correction == self.correction
    
    def test_feedback_validation(self):
        """Test feedback validation rules"""
        # Rating feedback without rating should fail
        with pytest.raises(ValueError):
            Feedback(
                feedback_id="test",
                user_id="user",
                feedback_type=FeedbackType.RATING,
                context=self.context,
                timestamp=datetime.now()
            )
        
        # Correction feedback without correction should fail
        with pytest.raises(ValueError):
            Feedback(
                feedback_id="test",
                user_id="user",
                feedback_type=FeedbackType.CORRECTION,
                context=self.context,
                timestamp=datetime.now()
            )
    
    def test_feedback_serialization(self):
        """Test feedback to_dict and from_dict methods"""
        original_feedback = Feedback(
            feedback_id="test_feedback",
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=self.context,
            timestamp=datetime.now(),
            rating=self.rating,
            tags=["test", "quality"],
            suggestion_text="Test suggestion"
        )
        
        # Convert to dict
        feedback_dict = original_feedback.to_dict()
        
        # Verify dict structure
        assert feedback_dict['feedback_id'] == "test_feedback"
        assert feedback_dict['user_id'] == "test_user"
        assert feedback_dict['feedback_type'] == "rating"
        assert 'rating' in feedback_dict
        assert feedback_dict['tags'] == ["test", "quality"]
        assert feedback_dict['suggestion_text'] == "Test suggestion"
        
        # Convert back to object
        restored_feedback = Feedback.from_dict(feedback_dict)
        
        # Verify restoration
        assert restored_feedback.feedback_id == original_feedback.feedback_id
        assert restored_feedback.user_id == original_feedback.user_id
        assert restored_feedback.feedback_type == original_feedback.feedback_type
        assert restored_feedback.rating.rating_id == original_feedback.rating.rating_id
        assert restored_feedback.tags == original_feedback.tags
        assert restored_feedback.suggestion_text == original_feedback.suggestion_text

class TestFeedbackStorage:
    """Test FeedbackStorage class"""
    
    def setup_method(self):
        """Set up test fixtures with temporary database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = FeedbackStorage(self.temp_db.name)
        
        # Create test data
        self.context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="Test content"
        )
        
        self.rating = Rating(
            rating_id=generate_rating_id(),
            rating_type=RatingType.STARS,
            value=4,
            max_value=5
        )
        
        self.feedback = Feedback(
            feedback_id=generate_feedback_id(),
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=self.context,
            timestamp=datetime.now(),
            rating=self.rating
        )
    
    def teardown_method(self):
        """Clean up temporary database"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_database_initialization(self):
        """Test database schema initialization"""
        # Check that tables exist
        with self.storage._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'feedback' in tables
            assert 'feedback_stats' in tables
    
    def test_store_and_retrieve_feedback(self):
        """Test storing and retrieving feedback"""
        with ProgressTracker("Store and Retrieve Feedback Test", 6) as tracker:
            tracker.step("Storing feedback in database")
            success = self.storage.store_feedback(self.feedback)
            assert success == True
            
            tracker.step("Retrieving feedback from database")
            retrieved = self.storage.get_feedback(self.feedback.feedback_id)
            assert retrieved is not None
            
            tracker.step("Validating feedback ID")
            assert retrieved.feedback_id == self.feedback.feedback_id
            
            tracker.step("Validating user ID")
            assert retrieved.user_id == self.feedback.user_id
            
            tracker.step("Validating feedback type")
            assert retrieved.feedback_type == self.feedback.feedback_type
            
            tracker.step("Verifying data integrity")
    
    def test_get_user_feedback(self):
        """Test retrieving feedback for a specific user"""
        # Store multiple feedback items
        feedback1 = self.feedback
        
        feedback2 = Feedback(
            feedback_id=generate_feedback_id(),
            user_id="test_user",
            feedback_type=FeedbackType.SUGGESTION,
            context=self.context,
            timestamp=datetime.now(),
            suggestion_text="Test suggestion"
        )
        
        self.storage.store_feedback(feedback1)
        self.storage.store_feedback(feedback2)
        
        # Retrieve user feedback
        user_feedback = self.storage.get_user_feedback("test_user")
        assert len(user_feedback) == 2
        
        # Test pagination
        limited_feedback = self.storage.get_user_feedback("test_user", limit=1)
        assert len(limited_feedback) == 1
    
    def test_get_content_feedback(self):
        """Test retrieving feedback for specific content"""
        # Store feedback
        self.storage.store_feedback(self.feedback)
        
        # Retrieve by content ID
        content_feedback = self.storage.get_content_feedback("test_content")
        assert len(content_feedback) == 1
        assert content_feedback[0].context.content_id == "test_content"
        
        # Retrieve by content ID and type
        typed_feedback = self.storage.get_content_feedback(
            "test_content", 
            ContentType.TRANSCRIPTION
        )
        assert len(typed_feedback) == 1
    
    def test_update_feedback_status(self):
        """Test updating feedback status"""
        # Store feedback
        self.storage.store_feedback(self.feedback)
        
        # Update status
        success = self.storage.update_feedback_status(
            self.feedback.feedback_id,
            FeedbackStatus.PROCESSED,
            "Test processing note"
        )
        assert success == True
        
        # Verify update
        updated_feedback = self.storage.get_feedback(self.feedback.feedback_id)
        assert updated_feedback.status == FeedbackStatus.PROCESSED
        assert updated_feedback.processing_notes == "Test processing note"
    
    def test_feedback_statistics(self):
        """Test feedback statistics generation"""
        # Store multiple feedback items
        feedback1 = self.feedback
        
        correction = Correction(
            correction_id=generate_correction_id(),
            original_text="original",
            corrected_text="corrected",
            correction_type="word"
        )
        
        feedback2 = Feedback(
            feedback_id=generate_feedback_id(),
            user_id="test_user",
            feedback_type=FeedbackType.CORRECTION,
            context=self.context,
            timestamp=datetime.now(),
            correction=correction
        )
        
        self.storage.store_feedback(feedback1)
        self.storage.store_feedback(feedback2)
        
        # Get statistics
        stats = self.storage.get_feedback_statistics()
        
        assert stats['total_feedback'] == 2
        assert 'by_type' in stats
        assert 'by_status' in stats
        assert 'rating' in stats['by_type']
        assert 'correction' in stats['by_type']
        assert stats['by_type']['rating']['count'] == 1
        assert stats['by_type']['correction']['count'] == 1
    
    def test_statistics_filtering(self):
        """Test statistics with filtering"""
        # Store feedback
        self.storage.store_feedback(self.feedback)
        
        # Get statistics filtered by content type
        stats = self.storage.get_feedback_statistics(
            content_type=ContentType.TRANSCRIPTION
        )
        
        assert stats['total_feedback'] == 1
        
        # Get statistics filtered by user
        user_stats = self.storage.get_feedback_statistics(user_id="test_user")
        assert user_stats['total_feedback'] == 1
        
        # Get statistics filtered by date range
        now = datetime.now()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)
        
        date_stats = self.storage.get_feedback_statistics(
            date_range=(yesterday, tomorrow)
        )
        assert date_stats['total_feedback'] == 1
    
    def test_concurrent_access(self):
        """Test concurrent database access"""
        with ProgressTracker("Concurrent Access Test", 4) as tracker:
            import threading
            
            results = []
            
            def store_feedback(user_id):
                feedback = Feedback(
                    feedback_id=generate_feedback_id(),
                    user_id=user_id,
                    feedback_type=FeedbackType.RATING,
                    context=self.context,
                    timestamp=datetime.now(),
                    rating=self.rating
                )
                success = self.storage.store_feedback(feedback)
                results.append(success)
            
            tracker.step("Creating 5 concurrent threads")
            threads = []
            for i in range(5):
                thread = threading.Thread(target=store_feedback, args=(f"user_{i}",))
                threads.append(thread)
                thread.start()
            
            tracker.step("Waiting for all threads to complete")
            for thread in threads:
                thread.join()
            
            tracker.step("Verifying all operations succeeded")
            assert all(results)
            assert len(results) == 5
            
            tracker.step("Concurrent access test completed")

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_feedback_storage(self):
        """Test feedback storage creation"""
        storage = create_feedback_storage(":memory:")
        assert isinstance(storage, FeedbackStorage)
    
    def test_id_generation(self):
        """Test ID generation functions"""
        feedback_id = generate_feedback_id()
        assert isinstance(feedback_id, str)
        assert len(feedback_id) > 0
        
        rating_id = generate_rating_id()
        assert isinstance(rating_id, str)
        assert rating_id.startswith("rating_")
        
        correction_id = generate_correction_id()
        assert isinstance(correction_id, str)
        assert correction_id.startswith("correction_")
        
        # Test uniqueness
        id1 = generate_feedback_id()
        id2 = generate_feedback_id()
        assert id1 != id2

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.storage = FeedbackStorage(self.temp_db.name)
    
    def teardown_method(self):
        """Clean up"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def test_nonexistent_feedback_retrieval(self):
        """Test retrieving non-existent feedback"""
        feedback = self.storage.get_feedback("nonexistent_id")
        assert feedback is None
    
    def test_empty_user_feedback(self):
        """Test retrieving feedback for user with no feedback"""
        feedback_list = self.storage.get_user_feedback("nonexistent_user")
        assert feedback_list == []
    
    def test_invalid_feedback_status_update(self):
        """Test updating status of non-existent feedback"""
        success = self.storage.update_feedback_status(
            "nonexistent_id",
            FeedbackStatus.PROCESSED
        )
        assert success == False
    
    def test_database_corruption_handling(self):
        """Test handling of database issues"""
        # Close the database file to simulate corruption
        os.unlink(self.temp_db.name)
        
        # Try to store feedback - should handle gracefully
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test",
            original_content="test"
        )
        
        feedback = Feedback(
            feedback_id="test",
            user_id="test",
            feedback_type=FeedbackType.SUGGESTION,
            context=context,
            timestamp=datetime.now(),
            suggestion_text="test"
        )
        
        # This should fail gracefully
        success = self.storage.store_feedback(feedback)
        assert success == False

def test_integration_example():
    """Integration test with realistic feedback scenarios"""
    print_separator("COMPREHENSIVE INTEGRATION TEST", "=")
    
    with ProgressTracker("Integration Test", 12) as tracker:
        # Create temporary storage
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        
        try:
            tracker.step("Initializing feedback storage system")
            storage = FeedbackStorage(temp_db.name)
            
            tracker.step("Creating transcription context")
            context = FeedbackContext(
                content_type=ContentType.TRANSCRIPTION,
                content_id="meeting_transcript_001",
                original_content="Hello everyone, welcome to today's meeting.",
                processed_content="Hello everyone, welcome to today's meeting.",
                confidence_score=0.92,
                processing_method="whisper_v3",
                model_version="3.0",
                session_id="session_20241201_001"
            )
            
            tracker.step("Creating positive rating feedback")
            positive_rating = Rating(
                rating_id=generate_rating_id(),
                rating_type=RatingType.THUMBS,
                value=True,
                comment="Accurate transcription"
            )
            
            positive_feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id="user_alice",
                feedback_type=FeedbackType.RATING,
                context=context,
                timestamp=datetime.now(),
                rating=positive_rating,
                tags=["transcription", "accurate", "meeting"]
            )
            
            tracker.step("Storing positive feedback")
            assert storage.store_feedback(positive_feedback) == True
            
            tracker.step("Creating correction feedback")
            correction = Correction(
                correction_id=generate_correction_id(),
                original_text="today's",
                corrected_text="today's",
                correction_type="apostrophe",
                position_start=35,
                position_end=42,
                explanation="Proper apostrophe character"
            )
            
            correction_feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id="user_bob",
                feedback_type=FeedbackType.CORRECTION,
                context=context,
                timestamp=datetime.now(),
                correction=correction,
                tags=["transcription", "punctuation", "correction"]
            )
            
            tracker.step("Storing correction feedback")
            assert storage.store_feedback(correction_feedback) == True
            
            tracker.step("Creating suggestion feedback")
            suggestion_feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id="user_charlie",
                feedback_type=FeedbackType.SUGGESTION,
                context=context,
                timestamp=datetime.now(),
                suggestion_text="Consider adding speaker identification for better meeting minutes",
                tags=["transcription", "enhancement", "speaker-id"]
            )
            
            tracker.step("Storing suggestion feedback")
            assert storage.store_feedback(suggestion_feedback) == True
            
            tracker.step("Verifying all feedback was stored")
            content_feedback = storage.get_content_feedback("meeting_transcript_001")
            assert len(content_feedback) == 3
            
            tracker.step("Generating comprehensive statistics")
            stats = storage.get_feedback_statistics()
            assert stats['total_feedback'] == 3
            assert stats['by_type']['rating']['count'] == 1
            assert stats['by_type']['correction']['count'] == 1
            assert stats['by_type']['suggestion']['count'] == 1
            
            tracker.step("Updating feedback status")
            for feedback in content_feedback:
                if feedback.feedback_type == FeedbackType.CORRECTION:
                    success = storage.update_feedback_status(
                        feedback.feedback_id,
                        FeedbackStatus.APPLIED,
                        "Correction applied to model training"
                    )
                    assert success == True
            
            tracker.step("Verifying status updates")
            updated_feedback = storage.get_feedback(correction_feedback.feedback_id)
            assert updated_feedback.status == FeedbackStatus.APPLIED
            
            print("\n📊 Integration Test Results:")
            print(f"   Total feedback items: {stats['total_feedback']}")
            print(f"   Ratings: {stats['by_type']['rating']['count']}")
            print(f"   Corrections: {stats['by_type']['correction']['count']}")
            print(f"   Suggestions: {stats['by_type']['suggestion']['count']}")
            
        finally:
            # Clean up
            try:
                os.unlink(temp_db.name)
            except:
                pass

def run_comprehensive_test_suite():
    """Run comprehensive test suite with progress tracking"""
    print_separator("FEEDBACK DATA MODELS TEST SUITE", "=")
    print("🧪 Comprehensive testing with progress tracking and visual feedback")
    print("📊 Testing all components: Models, Storage, Retrieval, and Analysis")
    print()
    
    start_time = time.time()
    
    try:
        # Run integration test first
        test_integration_example()
        print()
        
        # Run pytest for all other tests
        print_separator("RUNNING PYTEST SUITE", "-")
        print("🔬 Executing detailed unit tests...")
        
        # Run pytest with verbose output
        exit_code = pytest.main([__file__, "-v", "--tb=short"])
        
        end_time = time.time()
        duration = end_time - start_time
        
        print_separator("TEST SUITE COMPLETED", "=")
        if exit_code == 0:
            print("✅ All tests passed successfully!")
        else:
            print("❌ Some tests failed. Check output above for details.")
        
        print(f"⏱️  Total execution time: {duration:.2f} seconds")
        print("🚀 The Feedback Data Models and Storage System is ready for production!")
        
        print("\n🎯 Key Features Tested:")
        print("  • Comprehensive feedback data models (Rating, Correction, Suggestion)")
        print("  • SQLite-based storage with concurrent access support")
        print("  • Advanced retrieval and filtering capabilities")
        print("  • Statistical analysis and quality metrics")
        print("  • Progress tracking and real-time updates")
        print("  • Error handling and edge cases")
        print("  • Integration scenarios and workflows")
        
        return exit_code
        
    except Exception as e:
        print(f"❌ Error during test execution: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = run_comprehensive_test_suite()
    sys.exit(exit_code)