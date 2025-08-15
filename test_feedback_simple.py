#!/usr/bin/env python3
"""
Simple test for Feedback Data Models with progress tracking
"""

import sys
import os
import tempfile
import time
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_progress(current, total, task_name="Testing", width=50):
    """Print a progress bar"""
    progress = current / total
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)
    percentage = progress * 100
    print(f"\r{task_name}: |{bar}| {percentage:.1f}% ({current}/{total})", end='', flush=True)
    if current == total:
        print()  # New line when complete

def test_simple_feedback():
    """Simple test with progress tracking"""
    print("🧪 Running Simple Feedback Test")
    
    try:
        from feedback_data_models import (
            FeedbackStorage, Feedback, Rating, FeedbackContext,
            FeedbackType, RatingType, ContentType,
            generate_feedback_id, generate_rating_id
        )
        
        total_steps = 8
        
        # Step 1: Create storage
        print_progress(1, total_steps, "Simple Test")
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_db.close()
        storage = FeedbackStorage(temp_db.name)
        time.sleep(0.1)
        
        # Step 2: Create context
        print_progress(2, total_steps, "Simple Test")
        context = FeedbackContext(
            content_type=ContentType.TRANSCRIPTION,
            content_id="test_content",
            original_content="Test content"
        )
        time.sleep(0.1)
        
        # Step 3: Create rating
        print_progress(3, total_steps, "Simple Test")
        rating = Rating(
            rating_id=generate_rating_id(),
            rating_type=RatingType.STARS,
            value=4,
            max_value=5
        )
        time.sleep(0.1)
        
        # Step 4: Create feedback
        print_progress(4, total_steps, "Simple Test")
        feedback = Feedback(
            feedback_id=generate_feedback_id(),
            user_id="test_user",
            feedback_type=FeedbackType.RATING,
            context=context,
            timestamp=datetime.now(),
            rating=rating
        )
        time.sleep(0.1)
        
        # Step 5: Store feedback (this might be where it hangs)
        print_progress(5, total_steps, "Simple Test")
        print("\n  📝 Attempting to store feedback...")
        success = storage.store_feedback(feedback)
        print(f"  📝 Storage result: {success}")
        time.sleep(0.1)
        
        # Step 6: Retrieve feedback
        print_progress(6, total_steps, "Simple Test")
        retrieved = storage.get_feedback(feedback.feedback_id)
        assert retrieved is not None
        time.sleep(0.1)
        
        # Step 7: Verify data
        print_progress(7, total_steps, "Simple Test")
        assert retrieved.feedback_id == feedback.feedback_id
        assert retrieved.user_id == feedback.user_id
        time.sleep(0.1)
        
        # Step 8: Complete
        print_progress(8, total_steps, "Simple Test")
        
        print("\n✅ Simple test completed successfully!")
        
        # Clean up
        try:
            os.unlink(temp_db.name)
        except:
            pass
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error in simple test: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_simple_feedback()
    if success:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("💥 Tests failed!")
        sys.exit(1)