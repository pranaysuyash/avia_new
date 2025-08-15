#!/usr/bin/env python3
"""
Feedback Collection Interfaces
Comprehensive system for collecting user feedback through multiple input methods
"""

import uuid
import logging
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
import difflib
from abc import ABC, abstractmethod

# Import our data models
from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, FeedbackStatus, ContentType,
    generate_feedback_id, generate_rating_id, generate_correction_id
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CollectionMethod(Enum):
    """Methods for collecting feedback"""
    INLINE = "inline"           # Inline with content
    POPUP = "popup"             # Modal/popup interface
    SIDEBAR = "sidebar"         # Side panel interface
    OVERLAY = "overlay"         # Overlay interface
    CONTEXTUAL = "contextual"   # Context menu
    BATCH = "batch"             # Batch collection

class FeedbackTrigger(Enum):
    """Events that can trigger feedback collection"""
    USER_INITIATED = "user_initiated"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    ERROR_DETECTED = "error_detected"
    QUALITY_THRESHOLD = "quality_threshold"
    SESSION_END = "session_end"

@dataclass
class CollectionConfig:
    """Configuration for feedback collection"""
    method: CollectionMethod = CollectionMethod.INLINE
    trigger: FeedbackTrigger = FeedbackTrigger.USER_INITIATED
    auto_save: bool = True
    require_confirmation: bool = False
    allow_anonymous: bool = True
    max_rating_value: int = 5
    enable_comments: bool = True
    enable_corrections: bool = True
    enable_suggestions: bool = True
    collection_timeout: int = 300  # seconds
    metadata: Dict[str, Any] = field(default_factory=dict)

class FeedbackValidator:
    """Validates feedback before collection"""
    
    @staticmethod
    def validate_rating(rating_type: RatingType, value: Any, max_value: Optional[int] = None) -> bool:
        """Validate rating value based on type"""
        try:
            if rating_type == RatingType.THUMBS:
                return isinstance(value, bool)
            elif rating_type == RatingType.BINARY:
                return str(value).lower() in ['good', 'bad', 'true', 'false', '1', '0']
            elif rating_type in [RatingType.STARS, RatingType.SCALE]:
                if not isinstance(value, (int, float)):
                    return False
                max_val = max_value or (5 if rating_type == RatingType.STARS else 10)
                return 0 <= value <= max_val
            return False
        except Exception:
            return False
    
    @staticmethod
    def validate_correction(original: str, corrected: str) -> bool:
        """Validate correction text"""
        if not isinstance(original, str) or not isinstance(corrected, str):
            return False
        if len(original.strip()) == 0 or len(corrected.strip()) == 0:
            return False
        return original.strip() != corrected.strip()
    
    @staticmethod
    def validate_suggestion(suggestion: str) -> bool:
        """Validate suggestion text"""
        if not isinstance(suggestion, str):
            return False
        return len(suggestion.strip()) >= 10  # Minimum meaningful suggestion length

class ChangeDetector:
    """Detects and analyzes changes in text for corrections"""
    
    @staticmethod
    def detect_changes(original: str, modified: str) -> List[Dict[str, Any]]:
        """Detect changes between original and modified text"""
        changes = []
        
        # Use difflib to find differences
        differ = difflib.SequenceMatcher(None, original, modified)
        
        for tag, i1, i2, j1, j2 in differ.get_opcodes():
            if tag != 'equal':
                change = {
                    'type': tag,  # 'replace', 'delete', 'insert'
                    'original_start': i1,
                    'original_end': i2,
                    'original_text': original[i1:i2],
                    'modified_start': j1,
                    'modified_end': j2,
                    'modified_text': modified[j1:j2],
                    'change_length': abs((i2 - i1) - (j2 - j1))
                }
                changes.append(change)
        
        return changes
    
    @staticmethod
    def categorize_change(change: Dict[str, Any]) -> str:
        """Categorize the type of change"""
        change_type = change['type']
        original_text = change['original_text']
        modified_text = change['modified_text']
        
        if change_type == 'replace':
            # Analyze what kind of replacement
            if len(original_text) == len(modified_text) == 1:
                if original_text.isalpha() and modified_text.isalpha():
                    return 'character_substitution'
                elif original_text.isdigit() and modified_text.isdigit():
                    return 'number_correction'
                else:
                    return 'punctuation_correction'
            elif original_text.lower() != modified_text.lower():
                if original_text.lower() == modified_text.lower():
                    return 'capitalization'
                else:
                    return 'word_replacement'
            else:
                return 'case_change'
        elif change_type == 'insert':
            if modified_text.isspace():
                return 'spacing_addition'
            elif len(modified_text) == 1 and not modified_text.isalnum():
                return 'punctuation_addition'
            else:
                return 'text_insertion'
        elif change_type == 'delete':
            if original_text.isspace():
                return 'spacing_removal'
            elif len(original_text) == 1 and not original_text.isalnum():
                return 'punctuation_removal'
            else:
                return 'text_deletion'
        
        return 'unknown'

class FeedbackCollectionInterface(ABC):
    """Abstract base class for feedback collection interfaces"""
    
    @abstractmethod
    def collect_rating(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Rating]:
        """Collect rating feedback"""
        pass
    
    @abstractmethod
    def collect_correction(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Correction]:
        """Collect correction feedback"""
        pass
    
    @abstractmethod
    def collect_suggestion(self, context: FeedbackContext, config: CollectionConfig) -> Optional[str]:
        """Collect suggestion feedback"""
        pass

class InlineFeedbackInterface(FeedbackCollectionInterface):
    """Inline feedback collection interface"""
    
    def __init__(self):
        self.validator = FeedbackValidator()
        self.change_detector = ChangeDetector()
    
    def collect_rating(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Rating]:
        """Collect rating through inline interface"""
        try:
            # Simulate inline rating collection
            # In a real implementation, this would interact with UI components
            
            rating_type = RatingType.STARS  # Default to stars
            max_value = config.max_rating_value
            
            # For demo purposes, we'll create a sample rating
            # In real implementation, this would come from user interaction
            rating_value = 4  # Sample value
            
            if not self.validator.validate_rating(rating_type, rating_value, max_value):
                logger.warning(f"Invalid rating value: {rating_value}")
                return None
            
            rating = Rating(
                rating_id=generate_rating_id(),
                rating_type=rating_type,
                value=rating_value,
                max_value=max_value,
                comment="Collected via inline interface"
            )
            
            logger.info(f"Collected inline rating: {rating_value}/{max_value}")
            return rating
            
        except Exception as e:
            logger.error(f"Error collecting inline rating: {e}")
            return None
    
    def collect_correction(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Correction]:
        """Collect correction through inline interface"""
        try:
            original_text = context.processed_content or context.original_content
            
            # In real implementation, this would come from user editing
            # For demo, we'll simulate a correction
            corrected_text = original_text.replace("today's", "today's")  # Sample correction
            
            if not self.validator.validate_correction(original_text, corrected_text):
                logger.info("No valid correction detected")
                return None
            
            # Detect changes
            changes = self.change_detector.detect_changes(original_text, corrected_text)
            
            if not changes:
                logger.info("No changes detected")
                return None
            
            # Create correction for the first significant change
            primary_change = changes[0]
            correction_type = self.change_detector.categorize_change(primary_change)
            
            correction = Correction(
                correction_id=generate_correction_id(),
                original_text=primary_change['original_text'],
                corrected_text=primary_change['modified_text'],
                correction_type=correction_type,
                position_start=primary_change['original_start'],
                position_end=primary_change['original_end'],
                explanation=f"Inline correction: {correction_type}"
            )
            
            logger.info(f"Collected inline correction: {correction_type}")
            return correction
            
        except Exception as e:
            logger.error(f"Error collecting inline correction: {e}")
            return None
    
    def collect_suggestion(self, context: FeedbackContext, config: CollectionConfig) -> Optional[str]:
        """Collect suggestion through inline interface"""
        try:
            # In real implementation, this would come from user input
            # For demo, we'll create a sample suggestion
            suggestion = "Consider improving the accuracy of technical terms recognition"
            
            if not self.validator.validate_suggestion(suggestion):
                logger.warning("Invalid suggestion provided")
                return None
            
            logger.info("Collected inline suggestion")
            return suggestion
            
        except Exception as e:
            logger.error(f"Error collecting inline suggestion: {e}")
            return None

class PopupFeedbackInterface(FeedbackCollectionInterface):
    """Popup/modal feedback collection interface"""
    
    def __init__(self):
        self.validator = FeedbackValidator()
    
    def collect_rating(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Rating]:
        """Collect rating through popup interface"""
        try:
            # Simulate popup rating collection with different rating types
            rating_types = [RatingType.THUMBS, RatingType.STARS, RatingType.SCALE]
            rating_type = rating_types[0]  # For demo, use thumbs
            
            # Sample popup interaction
            if rating_type == RatingType.THUMBS:
                rating_value = True  # Thumbs up
                max_value = None
            elif rating_type == RatingType.STARS:
                rating_value = 4
                max_value = config.max_rating_value
            else:  # SCALE
                rating_value = 8
                max_value = 10
            
            if not self.validator.validate_rating(rating_type, rating_value, max_value):
                return None
            
            rating = Rating(
                rating_id=generate_rating_id(),
                rating_type=rating_type,
                value=rating_value,
                max_value=max_value,
                comment="Collected via popup interface"
            )
            
            logger.info(f"Collected popup rating: {rating_type.value}")
            return rating
            
        except Exception as e:
            logger.error(f"Error collecting popup rating: {e}")
            return None
    
    def collect_correction(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Correction]:
        """Collect correction through popup interface"""
        try:
            # Simulate popup correction interface
            original_text = "machine learning"
            corrected_text = "Machine Learning"
            
            if not self.validator.validate_correction(original_text, corrected_text):
                return None
            
            correction = Correction(
                correction_id=generate_correction_id(),
                original_text=original_text,
                corrected_text=corrected_text,
                correction_type="capitalization",
                explanation="Popup correction: proper noun capitalization"
            )
            
            logger.info("Collected popup correction")
            return correction
            
        except Exception as e:
            logger.error(f"Error collecting popup correction: {e}")
            return None
    
    def collect_suggestion(self, context: FeedbackContext, config: CollectionConfig) -> Optional[str]:
        """Collect suggestion through popup interface"""
        try:
            suggestion = "Add support for domain-specific terminology in transcription processing"
            
            if not self.validator.validate_suggestion(suggestion):
                return None
            
            logger.info("Collected popup suggestion")
            return suggestion
            
        except Exception as e:
            logger.error(f"Error collecting popup suggestion: {e}")
            return None

class BatchFeedbackInterface(FeedbackCollectionInterface):
    """Batch feedback collection interface"""
    
    def __init__(self):
        self.validator = FeedbackValidator()
    
    def collect_rating(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Rating]:
        """Collect rating through batch interface"""
        try:
            # For batch processing, use a simple star rating
            rating = Rating(
                rating_id=generate_rating_id(),
                rating_type=RatingType.STARS,
                value=4,  # Default batch rating
                max_value=config.max_rating_value,
                comment="Collected via batch interface"
            )
            
            logger.info("Collected batch rating")
            return rating
            
        except Exception as e:
            logger.error(f"Error collecting batch rating: {e}")
            return None
    
    def collect_correction(self, context: FeedbackContext, config: CollectionConfig) -> Optional[Correction]:
        """Collect correction through batch interface"""
        try:
            # For batch processing, create a simple correction
            correction = Correction(
                correction_id=generate_correction_id(),
                original_text="batch",
                corrected_text="Batch",
                correction_type="capitalization",
                explanation="Batch correction: capitalization"
            )
            
            logger.info("Collected batch correction")
            return correction
            
        except Exception as e:
            logger.error(f"Error collecting batch correction: {e}")
            return None
    
    def collect_suggestion(self, context: FeedbackContext, config: CollectionConfig) -> Optional[str]:
        """Collect suggestion through batch interface"""
        try:
            suggestion = "Batch processing suggestion for system improvement"
            
            if not self.validator.validate_suggestion(suggestion):
                return None
            
            logger.info("Collected batch suggestion")
            return suggestion
            
        except Exception as e:
            logger.error(f"Error collecting batch suggestion: {e}")
            return None

class FeedbackCollector:
    """Main feedback collection system with multiple interfaces"""
    
    def __init__(self, storage: FeedbackStorage, config: CollectionConfig = None):
        self.storage = storage
        self.config = config or CollectionConfig()
        self.validator = FeedbackValidator()
        self.change_detector = ChangeDetector()
        
        # Initialize collection interfaces
        self.interfaces = {
            CollectionMethod.INLINE: InlineFeedbackInterface(),
            CollectionMethod.POPUP: PopupFeedbackInterface(),
            CollectionMethod.BATCH: BatchFeedbackInterface(),
            # Add more interfaces as needed
        }
        
        # Callback functions for different events
        self.callbacks = {
            'on_feedback_collected': [],
            'on_feedback_validated': [],
            'on_feedback_stored': [],
            'on_collection_error': []
        }
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for feedback collection events"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
    
    def _trigger_callbacks(self, event: str, *args, **kwargs):
        """Trigger registered callbacks for an event"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in callback for {event}: {e}")
    
    def collect_rating_feedback(self, 
                              user_id: str, 
                              context: FeedbackContext,
                              rating_type: RatingType = RatingType.STARS,
                              method: CollectionMethod = None) -> Optional[str]:
        """Collect rating feedback from user"""
        try:
            method = method or self.config.method
            interface = self.interfaces.get(method)
            
            if not interface:
                logger.error(f"No interface available for method: {method}")
                return None
            
            # Collect rating through interface
            rating = interface.collect_rating(context, self.config)
            
            if not rating:
                logger.info("No rating collected")
                return None
            
            self._trigger_callbacks('on_feedback_collected', 'rating', rating)
            
            # Create feedback object
            feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id=user_id,
                feedback_type=FeedbackType.RATING,
                context=context,
                timestamp=datetime.now(),
                rating=rating,
                tags=[method.value, rating_type.value]
            )
            
            # Validate and store
            if self._validate_and_store_feedback(feedback):
                return feedback.feedback_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error collecting rating feedback: {e}")
            self._trigger_callbacks('on_collection_error', 'rating', e)
            return None
    
    def collect_correction_feedback(self,
                                  user_id: str,
                                  context: FeedbackContext,
                                  original_text: str = None,
                                  corrected_text: str = None,
                                  method: CollectionMethod = None) -> Optional[str]:
        """Collect correction feedback from user"""
        try:
            method = method or self.config.method
            interface = self.interfaces.get(method)
            
            if not interface:
                logger.error(f"No interface available for method: {method}")
                return None
            
            # If texts provided, create correction directly
            if original_text and corrected_text:
                if not self.validator.validate_correction(original_text, corrected_text):
                    logger.warning("Invalid correction provided")
                    return None
                
                changes = self.change_detector.detect_changes(original_text, corrected_text)
                correction_type = "manual_correction"
                
                if changes:
                    correction_type = self.change_detector.categorize_change(changes[0])
                
                correction = Correction(
                    correction_id=generate_correction_id(),
                    original_text=original_text,
                    corrected_text=corrected_text,
                    correction_type=correction_type,
                    explanation=f"User correction: {correction_type}"
                )
            else:
                # Collect through interface
                correction = interface.collect_correction(context, self.config)
            
            if not correction:
                logger.info("No correction collected")
                return None
            
            self._trigger_callbacks('on_feedback_collected', 'correction', correction)
            
            # Create feedback object
            feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id=user_id,
                feedback_type=FeedbackType.CORRECTION,
                context=context,
                timestamp=datetime.now(),
                correction=correction,
                tags=[method.value, "correction", correction.correction_type]
            )
            
            # Validate and store
            if self._validate_and_store_feedback(feedback):
                return feedback.feedback_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error collecting correction feedback: {e}")
            self._trigger_callbacks('on_collection_error', 'correction', e)
            return None
    
    def collect_suggestion_feedback(self,
                                  user_id: str,
                                  context: FeedbackContext,
                                  suggestion_text: str = None,
                                  method: CollectionMethod = None) -> Optional[str]:
        """Collect suggestion feedback from user"""
        try:
            method = method or self.config.method
            interface = self.interfaces.get(method)
            
            if not interface:
                logger.error(f"No interface available for method: {method}")
                return None
            
            # Use provided suggestion or collect through interface
            if suggestion_text:
                if not self.validator.validate_suggestion(suggestion_text):
                    logger.warning("Invalid suggestion provided")
                    return None
                suggestion = suggestion_text
            else:
                suggestion = interface.collect_suggestion(context, self.config)
            
            if not suggestion:
                logger.info("No suggestion collected")
                return None
            
            self._trigger_callbacks('on_feedback_collected', 'suggestion', suggestion)
            
            # Create feedback object
            feedback = Feedback(
                feedback_id=generate_feedback_id(),
                user_id=user_id,
                feedback_type=FeedbackType.SUGGESTION,
                context=context,
                timestamp=datetime.now(),
                suggestion_text=suggestion,
                tags=[method.value, "suggestion"]
            )
            
            # Validate and store
            if self._validate_and_store_feedback(feedback):
                return feedback.feedback_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error collecting suggestion feedback: {e}")
            self._trigger_callbacks('on_collection_error', 'suggestion', e)
            return None
    
    def collect_batch_feedback(self,
                             user_id: str,
                             feedback_items: List[Dict[str, Any]]) -> List[str]:
        """Collect multiple feedback items in batch"""
        collected_ids = []
        
        for item in feedback_items:
            try:
                feedback_type = item.get('type')
                context = item.get('context')
                
                if not isinstance(context, FeedbackContext):
                    logger.warning("Invalid context in batch item")
                    continue
                
                feedback_id = None
                
                if feedback_type == 'rating':
                    rating_type = RatingType(item.get('rating_type', 'stars'))
                    feedback_id = self.collect_rating_feedback(
                        user_id, context, rating_type, CollectionMethod.BATCH
                    )
                elif feedback_type == 'correction':
                    feedback_id = self.collect_correction_feedback(
                        user_id, context,
                        item.get('original_text'),
                        item.get('corrected_text'),
                        CollectionMethod.BATCH
                    )
                elif feedback_type == 'suggestion':
                    feedback_id = self.collect_suggestion_feedback(
                        user_id, context,
                        item.get('suggestion_text'),
                        CollectionMethod.BATCH
                    )
                
                if feedback_id:
                    collected_ids.append(feedback_id)
                    
            except Exception as e:
                logger.error(f"Error in batch feedback item: {e}")
                continue
        
        logger.info(f"Collected {len(collected_ids)} feedback items in batch")
        return collected_ids
    
    def _validate_and_store_feedback(self, feedback: Feedback) -> bool:
        """Validate and store feedback"""
        try:
            # Additional validation
            if not feedback.user_id or not feedback.context:
                logger.warning("Invalid feedback: missing required fields")
                return False
            
            self._trigger_callbacks('on_feedback_validated', feedback)
            
            # Store feedback
            success = self.storage.store_feedback(feedback)
            
            if success:
                self._trigger_callbacks('on_feedback_stored', feedback)
                logger.info(f"Stored feedback: {feedback.feedback_id}")
            else:
                logger.error(f"Failed to store feedback: {feedback.feedback_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error validating/storing feedback: {e}")
            return False
    
    def get_collection_statistics(self) -> Dict[str, Any]:
        """Get statistics about feedback collection"""
        try:
            stats = self.storage.get_feedback_statistics()
            
            # Add collection-specific statistics
            collection_stats = {
                'total_collected': stats.get('total_feedback', 0),
                'by_method': {},
                'by_interface': {},
                'validation_success_rate': 0.95,  # Would track this in real implementation
                'collection_methods_available': list(self.interfaces.keys())
            }
            
            return {**stats, **collection_stats}
            
        except Exception as e:
            logger.error(f"Error getting collection statistics: {e}")
            return {}

# Utility functions
def create_feedback_collector(storage: FeedbackStorage, 
                            config: CollectionConfig = None) -> FeedbackCollector:
    """Create a feedback collector instance"""
    return FeedbackCollector(storage, config)

def create_collection_config(**kwargs) -> CollectionConfig:
    """Create a collection configuration"""
    return CollectionConfig(**kwargs)

# Example usage and testing
def example_usage():
    """Example usage of feedback collection system"""
    from feedback_data_models import create_feedback_storage
    
    # Create storage and collector
    storage = create_feedback_storage("feedback_collection_example.db")
    config = create_collection_config(
        method=CollectionMethod.INLINE,
        auto_save=True,
        enable_comments=True
    )
    collector = create_feedback_collector(storage, config)
    
    # Create sample context
    context = FeedbackContext(
        content_type=ContentType.TRANSCRIPTION,
        content_id="example_transcript",
        original_content="Hello world, this is a test transcription.",
        processed_content="Hello world, this is a test transcription.",
        confidence_score=0.95,
        processing_method="whisper",
        model_version="v1.0"
    )
    
    # Collect different types of feedback
    print("Collecting rating feedback...")
    rating_id = collector.collect_rating_feedback("user_123", context)
    print(f"Rating feedback ID: {rating_id}")
    
    print("Collecting correction feedback...")
    correction_id = collector.collect_correction_feedback(
        "user_123", context,
        "Hello world",
        "Hello World"
    )
    print(f"Correction feedback ID: {correction_id}")
    
    print("Collecting suggestion feedback...")
    suggestion_id = collector.collect_suggestion_feedback(
        "user_123", context,
        "Consider adding punctuation detection improvements"
    )
    print(f"Suggestion feedback ID: {suggestion_id}")
    
    # Get statistics
    stats = collector.get_collection_statistics()
    print(f"Collection statistics: {stats}")

if __name__ == "__main__":
    example_usage()