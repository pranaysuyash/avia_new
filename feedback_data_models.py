#!/usr/bin/env python3
"""
Feedback Data Models and Storage System
Comprehensive system for collecting, storing, and managing user feedback on NLP processing results
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import json
import sqlite3
import hashlib
from pathlib import Path
import threading
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FeedbackType(Enum):
    """Types of feedback that can be collected"""
    RATING = "rating"
    CORRECTION = "correction"
    PREFERENCE = "preference"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    FEATURE_REQUEST = "feature_request"

class RatingType(Enum):
    """Types of rating systems"""
    THUMBS = "thumbs"  # thumbs up/down
    STARS = "stars"    # 1-5 stars
    SCALE = "scale"    # 1-10 scale
    BINARY = "binary"  # good/bad

class FeedbackStatus(Enum):
    """Status of feedback processing"""
    PENDING = "pending"
    PROCESSED = "processed"
    APPLIED = "applied"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class ContentType(Enum):
    """Types of content being rated"""
    TRANSCRIPTION = "transcription"
    MEETING_ELEMENT = "meeting_element"
    ACTION_ITEM = "action_item"
    MOM_DOCUMENT = "mom_document"
    SPEAKER_IDENTIFICATION = "speaker_identification"
    ENTITY_EXTRACTION = "entity_extraction"

@dataclass
class FeedbackContext:
    """Context information for feedback"""
    content_type: ContentType
    content_id: str
    original_content: str
    processed_content: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_method: Optional[str] = None
    model_version: Optional[str] = None
    session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Rating:
    """Rating feedback data"""
    rating_id: str
    rating_type: RatingType
    value: Union[int, float, bool, str]
    max_value: Optional[Union[int, float]] = None
    comment: Optional[str] = None
    
    def normalize_rating(self) -> float:
        """Normalize rating to 0-1 scale"""
        if self.rating_type == RatingType.THUMBS:
            return 1.0 if self.value else 0.0
        elif self.rating_type == RatingType.BINARY:
            return 1.0 if str(self.value).lower() in ['good', 'true', '1'] else 0.0
        elif self.rating_type in [RatingType.STARS, RatingType.SCALE]:
            if self.max_value:
                return float(self.value) / float(self.max_value)
            else:
                # Default max values
                max_val = 5.0 if self.rating_type == RatingType.STARS else 10.0
                return float(self.value) / max_val
        return 0.5  # Default neutral rating

@dataclass
class Correction:
    """Correction feedback data"""
    correction_id: str
    original_text: str
    corrected_text: str
    correction_type: str  # word, phrase, sentence, structure
    position_start: Optional[int] = None
    position_end: Optional[int] = None
    confidence: Optional[float] = None
    explanation: Optional[str] = None
    
    def get_edit_distance(self) -> int:
        """Calculate edit distance between original and corrected text"""
        # Simple Levenshtein distance implementation
        if len(self.original_text) == 0:
            return len(self.corrected_text)
        if len(self.corrected_text) == 0:
            return len(self.original_text)
        
        matrix = [[0] * (len(self.corrected_text) + 1) for _ in range(len(self.original_text) + 1)]
        
        for i in range(len(self.original_text) + 1):
            matrix[i][0] = i
        for j in range(len(self.corrected_text) + 1):
            matrix[0][j] = j
        
        for i in range(1, len(self.original_text) + 1):
            for j in range(1, len(self.corrected_text) + 1):
                if self.original_text[i-1] == self.corrected_text[j-1]:
                    matrix[i][j] = matrix[i-1][j-1]
                else:
                    matrix[i][j] = min(
                        matrix[i-1][j] + 1,    # deletion
                        matrix[i][j-1] + 1,    # insertion
                        matrix[i-1][j-1] + 1   # substitution
                    )
        
        return matrix[len(self.original_text)][len(self.corrected_text)]

@dataclass
class Feedback:
    """Main feedback data structure"""
    feedback_id: str
    user_id: str
    feedback_type: FeedbackType
    context: FeedbackContext
    timestamp: datetime
    rating: Optional[Rating] = None
    correction: Optional[Correction] = None
    suggestion_text: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    status: FeedbackStatus = FeedbackStatus.PENDING
    processing_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Validate feedback data after initialization"""
        if self.feedback_type == FeedbackType.RATING and not self.rating:
            raise ValueError("Rating feedback must include rating data")
        if self.feedback_type == FeedbackType.CORRECTION and not self.correction:
            raise ValueError("Correction feedback must include correction data")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert feedback to dictionary for storage"""
        data = {
            'feedback_id': self.feedback_id,
            'user_id': self.user_id,
            'feedback_type': self.feedback_type.value,
            'context': {
                'content_type': self.context.content_type.value,
                'content_id': self.context.content_id,
                'original_content': self.context.original_content,
                'processed_content': self.context.processed_content,
                'confidence_score': self.context.confidence_score,
                'processing_method': self.context.processing_method,
                'model_version': self.context.model_version,
                'session_id': self.context.session_id,
                'metadata': self.context.metadata
            },
            'timestamp': self.timestamp.isoformat(),
            'tags': self.tags,
            'status': self.status.value,
            'processing_notes': self.processing_notes,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'suggestion_text': self.suggestion_text
        }
        
        if self.rating:
            data['rating'] = {
                'rating_id': self.rating.rating_id,
                'rating_type': self.rating.rating_type.value,
                'value': self.rating.value,
                'max_value': self.rating.max_value,
                'comment': self.rating.comment
            }
        
        if self.correction:
            data['correction'] = {
                'correction_id': self.correction.correction_id,
                'original_text': self.correction.original_text,
                'corrected_text': self.correction.corrected_text,
                'correction_type': self.correction.correction_type,
                'position_start': self.correction.position_start,
                'position_end': self.correction.position_end,
                'confidence': self.correction.confidence,
                'explanation': self.correction.explanation
            }
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Feedback':
        """Create feedback from dictionary"""
        context_data = data['context']
        context = FeedbackContext(
            content_type=ContentType(context_data['content_type']),
            content_id=context_data['content_id'],
            original_content=context_data['original_content'],
            processed_content=context_data.get('processed_content'),
            confidence_score=context_data.get('confidence_score'),
            processing_method=context_data.get('processing_method'),
            model_version=context_data.get('model_version'),
            session_id=context_data.get('session_id'),
            metadata=context_data.get('metadata', {})
        )
        
        rating = None
        if 'rating' in data and data['rating']:
            rating_data = data['rating']
            rating = Rating(
                rating_id=rating_data['rating_id'],
                rating_type=RatingType(rating_data['rating_type']),
                value=rating_data['value'],
                max_value=rating_data.get('max_value'),
                comment=rating_data.get('comment')
            )
        
        correction = None
        if 'correction' in data and data['correction']:
            correction_data = data['correction']
            correction = Correction(
                correction_id=correction_data['correction_id'],
                original_text=correction_data['original_text'],
                corrected_text=correction_data['corrected_text'],
                correction_type=correction_data['correction_type'],
                position_start=correction_data.get('position_start'),
                position_end=correction_data.get('position_end'),
                confidence=correction_data.get('confidence'),
                explanation=correction_data.get('explanation')
            )
        
        return cls(
            feedback_id=data['feedback_id'],
            user_id=data['user_id'],
            feedback_type=FeedbackType(data['feedback_type']),
            context=context,
            timestamp=datetime.fromisoformat(data['timestamp']),
            rating=rating,
            correction=correction,
            suggestion_text=data.get('suggestion_text'),
            tags=data.get('tags', []),
            status=FeedbackStatus(data.get('status', 'pending')),
            processing_notes=data.get('processing_notes'),
            created_at=datetime.fromisoformat(data.get('created_at', data['timestamp'])),
            updated_at=datetime.fromisoformat(data.get('updated_at', data['timestamp']))
        )

class FeedbackStorage:
    """Storage system for feedback data with SQLite backend"""
    
    def __init__(self, db_path: str = "feedback.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize the database schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Create feedback table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback (
                        feedback_id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        content_type TEXT NOT NULL,
                        content_id TEXT NOT NULL,
                        original_content TEXT NOT NULL,
                        processed_content TEXT,
                        confidence_score REAL,
                        processing_method TEXT,
                        model_version TEXT,
                        session_id TEXT,
                        context_metadata TEXT,
                        rating_data TEXT,
                        correction_data TEXT,
                        suggestion_text TEXT,
                        tags TEXT,
                        status TEXT DEFAULT 'pending',
                        processing_notes TEXT,
                        timestamp TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                ''')
                
                # Create indexes for better query performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_id ON feedback(user_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_type ON feedback(content_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_feedback_type ON feedback(feedback_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON feedback(status)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON feedback(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_content_id ON feedback(content_id)')
                
                # Create aggregation table for quick statistics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_stats (
                        stat_id TEXT PRIMARY KEY,
                        content_type TEXT NOT NULL,
                        feedback_type TEXT NOT NULL,
                        user_id TEXT,
                        date_bucket TEXT NOT NULL,
                        count INTEGER DEFAULT 0,
                        avg_rating REAL,
                        total_corrections INTEGER DEFAULT 0,
                        last_updated TEXT NOT NULL
                    )
                ''')
                
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_content_type ON feedback_stats(content_type)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_date ON feedback_stats(date_bucket)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_stats_user ON feedback_stats(user_id)')
                
                conn.commit()
                logger.info("Database schema initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database schema: {e}")
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper locking"""
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def store_feedback(self, feedback: Feedback) -> bool:
        """Store feedback in the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Convert feedback to database format
                cursor.execute('''
                    INSERT OR REPLACE INTO feedback (
                        feedback_id, user_id, feedback_type, content_type, content_id,
                        original_content, processed_content, confidence_score,
                        processing_method, model_version, session_id, context_metadata,
                        rating_data, correction_data, suggestion_text, tags,
                        status, processing_notes, timestamp, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    feedback.feedback_id,
                    feedback.user_id,
                    feedback.feedback_type.value,
                    feedback.context.content_type.value,
                    feedback.context.content_id,
                    feedback.context.original_content,
                    feedback.context.processed_content,
                    feedback.context.confidence_score,
                    feedback.context.processing_method,
                    feedback.context.model_version,
                    feedback.context.session_id,
                    json.dumps(feedback.context.metadata),
                    json.dumps({
                        'rating_id': feedback.rating.rating_id,
                        'rating_type': feedback.rating.rating_type.value,
                        'value': feedback.rating.value,
                        'max_value': feedback.rating.max_value,
                        'comment': feedback.rating.comment
                    }) if feedback.rating else None,
                    json.dumps({
                        'correction_id': feedback.correction.correction_id,
                        'original_text': feedback.correction.original_text,
                        'corrected_text': feedback.correction.corrected_text,
                        'correction_type': feedback.correction.correction_type,
                        'position_start': feedback.correction.position_start,
                        'position_end': feedback.correction.position_end,
                        'confidence': feedback.correction.confidence,
                        'explanation': feedback.correction.explanation
                    }) if feedback.correction else None,
                    feedback.suggestion_text,
                    json.dumps(feedback.tags),
                    feedback.status.value,
                    feedback.processing_notes,
                    feedback.timestamp.isoformat(),
                    feedback.created_at.isoformat(),
                    feedback.updated_at.isoformat()
                ))
                
                conn.commit()
                
                # Update statistics inline to avoid nested connection
                try:
                    date_bucket = feedback.timestamp.strftime('%Y-%m-%d')
                    stat_id = f"{feedback.context.content_type.value}_{feedback.feedback_type.value}_{date_bucket}"
                    
                    # Update or insert statistics using the same connection
                    cursor.execute('''
                        INSERT OR REPLACE INTO feedback_stats (
                            stat_id, content_type, feedback_type, date_bucket,
                            count, avg_rating, total_corrections, last_updated
                        ) VALUES (?, ?, ?, ?, 
                            COALESCE((SELECT count FROM feedback_stats WHERE stat_id = ?), 0) + 1,
                            ?, 
                            COALESCE((SELECT total_corrections FROM feedback_stats WHERE stat_id = ?), 0) + ?,
                            ?
                        )
                    ''', (
                        stat_id,
                        feedback.context.content_type.value,
                        feedback.feedback_type.value,
                        date_bucket,
                        stat_id,  # for count lookup
                        feedback.rating.normalize_rating() if feedback.rating else None,
                        stat_id,  # for corrections lookup
                        1 if feedback.feedback_type == FeedbackType.CORRECTION else 0,
                        datetime.now().isoformat()
                    ))
                    
                    conn.commit()
                except Exception as stats_error:
                    logger.warning(f"Error updating statistics: {stats_error}")
                    # Don't fail the whole operation if statistics update fails
                
                logger.info(f"Stored feedback {feedback.feedback_id} for user {feedback.user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error storing feedback: {e}")
            return False
    
    def get_feedback(self, feedback_id: str) -> Optional[Feedback]:
        """Retrieve feedback by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM feedback WHERE feedback_id = ?', (feedback_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_feedback(row)
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving feedback {feedback_id}: {e}")
            return None
    
    def get_user_feedback(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Feedback]:
        """Get feedback for a specific user"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM feedback 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ? OFFSET ?
                ''', (user_id, limit, offset))
                
                return [self._row_to_feedback(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error retrieving user feedback for {user_id}: {e}")
            return []
    
    def get_content_feedback(self, content_id: str, content_type: ContentType = None) -> List[Feedback]:
        """Get feedback for specific content"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if content_type:
                    cursor.execute('''
                        SELECT * FROM feedback 
                        WHERE content_id = ? AND content_type = ?
                        ORDER BY timestamp DESC
                    ''', (content_id, content_type.value))
                else:
                    cursor.execute('''
                        SELECT * FROM feedback 
                        WHERE content_id = ?
                        ORDER BY timestamp DESC
                    ''', (content_id,))
                
                return [self._row_to_feedback(row) for row in cursor.fetchall()]
                
        except Exception as e:
            logger.error(f"Error retrieving content feedback for {content_id}: {e}")
            return []
    
    def update_feedback_status(self, feedback_id: str, status: FeedbackStatus, notes: str = None) -> bool:
        """Update feedback status"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE feedback 
                    SET status = ?, processing_notes = ?, updated_at = ?
                    WHERE feedback_id = ?
                ''', (status.value, notes, datetime.now().isoformat(), feedback_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Error updating feedback status: {e}")
            return False
    
    def get_feedback_statistics(self, content_type: ContentType = None, 
                              user_id: str = None, 
                              date_range: Tuple[datetime, datetime] = None) -> Dict[str, Any]:
        """Get feedback statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build query conditions
                conditions = []
                params = []
                
                if content_type:
                    conditions.append("content_type = ?")
                    params.append(content_type.value)
                
                if user_id:
                    conditions.append("user_id = ?")
                    params.append(user_id)
                
                if date_range:
                    conditions.append("timestamp BETWEEN ? AND ?")
                    params.extend([date_range[0].isoformat(), date_range[1].isoformat()])
                
                where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                
                # Get basic counts
                cursor.execute(f'''
                    SELECT 
                        feedback_type,
                        COUNT(*) as count,
                        AVG(CASE WHEN rating_data IS NOT NULL THEN 
                            json_extract(rating_data, '$.normalized_rating') 
                            ELSE NULL END) as avg_rating
                    FROM feedback 
                    {where_clause}
                    GROUP BY feedback_type
                ''', params)
                
                type_stats = {row['feedback_type']: {
                    'count': row['count'],
                    'avg_rating': row['avg_rating']
                } for row in cursor.fetchall()}
                
                # Get status distribution
                cursor.execute(f'''
                    SELECT status, COUNT(*) as count
                    FROM feedback 
                    {where_clause}
                    GROUP BY status
                ''', params)
                
                status_stats = {row['status']: row['count'] for row in cursor.fetchall()}
                
                # Get total count
                cursor.execute(f'SELECT COUNT(*) as total FROM feedback {where_clause}', params)
                total_count = cursor.fetchone()['total']
                
                return {
                    'total_feedback': total_count,
                    'by_type': type_stats,
                    'by_status': status_stats,
                    'generated_at': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"Error getting feedback statistics: {e}")
            return {}
    
    def _row_to_feedback(self, row) -> Feedback:
        """Convert database row to Feedback object"""
        # Parse context
        context = FeedbackContext(
            content_type=ContentType(row['content_type']),
            content_id=row['content_id'],
            original_content=row['original_content'],
            processed_content=row['processed_content'],
            confidence_score=row['confidence_score'],
            processing_method=row['processing_method'],
            model_version=row['model_version'],
            session_id=row['session_id'],
            metadata=json.loads(row['context_metadata']) if row['context_metadata'] else {}
        )
        
        # Parse rating
        rating = None
        if row['rating_data']:
            rating_data = json.loads(row['rating_data'])
            rating = Rating(
                rating_id=rating_data['rating_id'],
                rating_type=RatingType(rating_data['rating_type']),
                value=rating_data['value'],
                max_value=rating_data.get('max_value'),
                comment=rating_data.get('comment')
            )
        
        # Parse correction
        correction = None
        if row['correction_data']:
            correction_data = json.loads(row['correction_data'])
            correction = Correction(
                correction_id=correction_data['correction_id'],
                original_text=correction_data['original_text'],
                corrected_text=correction_data['corrected_text'],
                correction_type=correction_data['correction_type'],
                position_start=correction_data.get('position_start'),
                position_end=correction_data.get('position_end'),
                confidence=correction_data.get('confidence'),
                explanation=correction_data.get('explanation')
            )
        
        return Feedback(
            feedback_id=row['feedback_id'],
            user_id=row['user_id'],
            feedback_type=FeedbackType(row['feedback_type']),
            context=context,
            timestamp=datetime.fromisoformat(row['timestamp']),
            rating=rating,
            correction=correction,
            suggestion_text=row['suggestion_text'],
            tags=json.loads(row['tags']) if row['tags'] else [],
            status=FeedbackStatus(row['status']),
            processing_notes=row['processing_notes'],
            created_at=datetime.fromisoformat(row['created_at']),
            updated_at=datetime.fromisoformat(row['updated_at'])
        )
    
    def _update_statistics(self, feedback: Feedback):
        """Update aggregated statistics - deprecated, now done inline in store_feedback"""
        # This method is kept for backward compatibility but should not be used
        # as it can cause deadlocks when called from within another connection context
        logger.warning("_update_statistics called - this method is deprecated and may cause deadlocks")
        pass

# Utility functions
def create_feedback_storage(db_path: str = "feedback.db") -> FeedbackStorage:
    """Create a feedback storage instance"""
    return FeedbackStorage(db_path)

def generate_feedback_id() -> str:
    """Generate a unique feedback ID"""
    return str(uuid.uuid4())

def generate_rating_id() -> str:
    """Generate a unique rating ID"""
    return f"rating_{uuid.uuid4().hex[:8]}"

def generate_correction_id() -> str:
    """Generate a unique correction ID"""
    return f"correction_{uuid.uuid4().hex[:8]}"

# Example usage
def example_usage():
    """Example usage of feedback data models and storage"""
    
    # Create storage
    storage = create_feedback_storage("example_feedback.db")
    
    # Create sample feedback context
    context = FeedbackContext(
        content_type=ContentType.TRANSCRIPTION,
        content_id="transcript_123",
        original_content="Hello world, this is a test transcription.",
        processed_content="Hello world, this is a test transcription.",
        confidence_score=0.95,
        processing_method="whisper",
        model_version="v1.0",
        session_id="session_456"
    )
    
    # Create rating feedback
    rating = Rating(
        rating_id=generate_rating_id(),
        rating_type=RatingType.STARS,
        value=4,
        max_value=5,
        comment="Good transcription, minor errors"
    )
    
    rating_feedback = Feedback(
        feedback_id=generate_feedback_id(),
        user_id="user_123",
        feedback_type=FeedbackType.RATING,
        context=context,
        timestamp=datetime.now(),
        rating=rating,
        tags=["transcription", "quality"]
    )
    
    # Store feedback
    success = storage.store_feedback(rating_feedback)
    print(f"Rating feedback stored: {success}")
    
    # Create correction feedback
    correction = Correction(
        correction_id=generate_correction_id(),
        original_text="Hello world",
        corrected_text="Hello World",
        correction_type="capitalization",
        position_start=0,
        position_end=11,
        explanation="Proper capitalization needed"
    )
    
    correction_feedback = Feedback(
        feedback_id=generate_feedback_id(),
        user_id="user_123",
        feedback_type=FeedbackType.CORRECTION,
        context=context,
        timestamp=datetime.now(),
        correction=correction,
        tags=["transcription", "correction", "capitalization"]
    )
    
    # Store correction feedback
    success = storage.store_feedback(correction_feedback)
    print(f"Correction feedback stored: {success}")
    
    # Retrieve user feedback
    user_feedback = storage.get_user_feedback("user_123")
    print(f"Retrieved {len(user_feedback)} feedback items for user")
    
    # Get statistics
    stats = storage.get_feedback_statistics()
    print(f"Feedback statistics: {stats}")
    
    # Update feedback status
    if user_feedback:
        feedback_id = user_feedback[0].feedback_id
        updated = storage.update_feedback_status(
            feedback_id, 
            FeedbackStatus.PROCESSED, 
            "Processed successfully"
        )
        print(f"Feedback status updated: {updated}")

if __name__ == "__main__":
    example_usage()