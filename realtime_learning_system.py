#!/usr/bin/env python3
"""
Real-Time Learning and Adjustment System
Advanced system for immediate model parameter adjustments and continuous learning
"""

import uuid
import logging
import json
import threading
import time
import asyncio
from typing import Dict, List, Optional, Any, Union, Tuple, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, deque
import statistics
import hashlib
from abc import ABC, abstractmethod
import weakref

# Import our dependencies
from model_adaptation_engine import (
    ModelAdaptationEngine, AdaptationType, AdaptationScope, AdaptationStatus,
    ModelParameters, AdaptationResult
)
from user_learning_profile import (
    UserLearningProfile, PersonalizationEngine, CorrectionPattern
)
from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningTrigger(Enum):
    """Triggers for real-time learning"""
    IMMEDIATE = "immediate"           # Immediate upon feedback
    THRESHOLD_BASED = "threshold"     # When threshold is reached
    TIME_BASED = "time_based"         # At regular intervals
    PATTERN_DETECTED = "pattern"      # When pattern is detected
    QUALITY_DROP = "quality_drop"     # When quality drops
    USER_REQUEST = "user_request"     # User-initiated learning

class LearningMode(Enum):
    """Modes of real-time learning"""
    AGGRESSIVE = "aggressive"         # Immediate adjustments
    CONSERVATIVE = "conservative"     # Careful, validated adjustments
    BALANCED = "balanced"            # Balanced approach
    EXPERIMENTAL = "experimental"    # Experimental features enabled

class AdjustmentType(Enum):
    """Types of real-time adjustments"""
    PARAMETER_TWEAK = "parameter_tweak"
    THRESHOLD_ADJUST = "threshold_adjust"
    RULE_MODIFY = "rule_modify"
    PATTERN_ADD = "pattern_add"
    CONFIDENCE_CALIBRATE = "confidence_calibrate"
    VOCABULARY_UPDATE = "vocabulary_update"

@dataclass
class LearningEvent:
    """Event that triggers learning"""
    event_id: str
    trigger: LearningTrigger
    user_id: str
    model_id: str
    feedback: Optional[Feedback] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)
    processed: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['trigger'] = self.trigger.value
        data['timestamp'] = self.timestamp.isoformat()
        if self.feedback:
            data['feedback'] = self.feedback.to_dict() if hasattr(self.feedback, 'to_dict') else str(self.feedback)
        return data

@dataclass
class RealTimeAdjustment:
    """Real-time adjustment made to a model"""
    adjustment_id: str
    user_id: str
    model_id: str
    adjustment_type: AdjustmentType
    parameter_name: str
    old_value: Any
    new_value: Any
    confidence: float
    trigger_event: str
    timestamp: datetime = field(default_factory=datetime.now)
    effectiveness: Optional[float] = None
    reverted: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['adjustment_type'] = self.adjustment_type.value
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RealTimeAdjustment':
        """Create from dictionary"""
        data['adjustment_type'] = AdjustmentType(data['adjustment_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)

@dataclass
class LearningMetrics:
    """Metrics for learning effectiveness"""
    total_adjustments: int = 0
    successful_adjustments: int = 0
    reverted_adjustments: int = 0
    average_effectiveness: float = 0.0
    learning_rate: float = 0.0
    last_adjustment: Optional[datetime] = None
    adjustment_frequency: float = 0.0  # adjustments per hour
    
    def update_metrics(self, adjustment: RealTimeAdjustment):
        """Update metrics with new adjustment"""
        self.total_adjustments += 1
        self.last_adjustment = adjustment.timestamp
        
        if adjustment.effectiveness is not None:
            if adjustment.effectiveness > 0.5:
                self.successful_adjustments += 1
        
        if adjustment.reverted:
            self.reverted_adjustments += 1
        
        # Update success rate
        if self.total_adjustments > 0:
            self.learning_rate = self.successful_adjustments / self.total_adjustments

class RealTimeLearner(ABC):
    """Abstract base class for real-time learners"""
    
    @abstractmethod
    def should_adjust(self, event: LearningEvent) -> bool:
        """Determine if adjustment should be made"""
        pass
    
    @abstractmethod
    def calculate_adjustment(self, event: LearningEvent) -> Optional[RealTimeAdjustment]:
        """Calculate the adjustment to make"""
        pass
    
    @abstractmethod
    def apply_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Apply the adjustment"""
        pass
    
    @abstractmethod
    def validate_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Validate the adjustment before applying"""
        pass

class ConfidenceThresholdLearner(RealTimeLearner):
    """Learner for confidence threshold adjustments"""
    
    def __init__(self, learning_mode: LearningMode = LearningMode.BALANCED):
        self.learning_mode = learning_mode
        self.adjustment_history = defaultdict(list)
        self.min_feedback_count = 3 if learning_mode == LearningMode.AGGRESSIVE else 5
        
    def should_adjust(self, event: LearningEvent) -> bool:
        """Determine if threshold adjustment should be made"""
        if not event.feedback or not event.feedback.rating:
            return False
        
        # Check if we have enough recent feedback
        user_model_key = f"{event.user_id}_{event.model_id}"
        recent_adjustments = [adj for adj in self.adjustment_history[user_model_key] 
                            if adj.timestamp > datetime.now() - timedelta(hours=1)]
        
        # Don't adjust too frequently
        if len(recent_adjustments) > 2:
            return False
        
        return True
    
    def calculate_adjustment(self, event: LearningEvent) -> Optional[RealTimeAdjustment]:
        """Calculate confidence threshold adjustment"""
        if not event.feedback or not event.feedback.rating or not event.feedback.context:
            return None
        
        rating = event.feedback.rating.normalize_rating()
        confidence = event.feedback.context.confidence_score or 0.8
        
        # Calculate adjustment based on rating and current confidence
        if rating < 0.4:  # Low rating - increase threshold
            adjustment_amount = 0.05 if self.learning_mode == LearningMode.CONSERVATIVE else 0.1
            new_threshold = min(0.95, confidence + adjustment_amount)
        elif rating > 0.8:  # High rating - can lower threshold slightly
            adjustment_amount = 0.02 if self.learning_mode == LearningMode.CONSERVATIVE else 0.05
            new_threshold = max(0.3, confidence - adjustment_amount)
        else:
            return None  # No adjustment needed
        
        adjustment = RealTimeAdjustment(
            adjustment_id=str(uuid.uuid4()),
            user_id=event.user_id,
            model_id=event.model_id,
            adjustment_type=AdjustmentType.THRESHOLD_ADJUST,
            parameter_name="confidence_threshold",
            old_value=confidence,
            new_value=new_threshold,
            confidence=0.8 if self.learning_mode == LearningMode.CONSERVATIVE else 0.9,
            trigger_event=event.event_id
        )
        
        return adjustment
    
    def apply_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Apply confidence threshold adjustment"""
        try:
            # In a real implementation, this would update the actual model parameters
            logger.info(f"Applied threshold adjustment: {adjustment.parameter_name} "
                       f"{adjustment.old_value} -> {adjustment.new_value}")
            
            # Store adjustment in history
            user_model_key = f"{adjustment.user_id}_{adjustment.model_id}"
            self.adjustment_history[user_model_key].append(adjustment)
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply threshold adjustment: {e}")
            return False
    
    def validate_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Validate threshold adjustment"""
        if adjustment.adjustment_type != AdjustmentType.THRESHOLD_ADJUST:
            return False
        
        # Check if new value is within valid range
        if not (0.1 <= adjustment.new_value <= 0.99):
            return False
        
        # Check if adjustment is significant enough
        if abs(adjustment.new_value - adjustment.old_value) < 0.01:
            return False
        
        return True

class PatternLearner(RealTimeLearner):
    """Learner for pattern-based adjustments"""
    
    def __init__(self, learning_mode: LearningMode = LearningMode.BALANCED):
        self.learning_mode = learning_mode
        self.pattern_cache = defaultdict(list)
        self.min_pattern_frequency = 2 if learning_mode == LearningMode.AGGRESSIVE else 3
        
    def should_adjust(self, event: LearningEvent) -> bool:
        """Determine if pattern adjustment should be made"""
        if not event.feedback or not event.feedback.correction:
            return False
        
        correction = event.feedback.correction
        pattern_key = f"{correction.correction_type}_{correction.original_text}"
        
        # Check if we've seen this pattern enough times
        user_patterns = self.pattern_cache[event.user_id]
        pattern_count = len([p for p in user_patterns if p == pattern_key])
        
        return pattern_count >= self.min_pattern_frequency
    
    def calculate_adjustment(self, event: LearningEvent) -> Optional[RealTimeAdjustment]:
        """Calculate pattern-based adjustment"""
        if not event.feedback or not event.feedback.correction:
            return None
        
        correction = event.feedback.correction
        
        adjustment = RealTimeAdjustment(
            adjustment_id=str(uuid.uuid4()),
            user_id=event.user_id,
            model_id=event.model_id,
            adjustment_type=AdjustmentType.PATTERN_ADD,
            parameter_name="pattern_override",
            old_value=correction.original_text,
            new_value=correction.corrected_text,
            confidence=0.7 if self.learning_mode == LearningMode.CONSERVATIVE else 0.8,
            trigger_event=event.event_id
        )
        
        return adjustment
    
    def apply_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Apply pattern adjustment"""
        try:
            logger.info(f"Applied pattern adjustment: '{adjustment.old_value}' -> '{adjustment.new_value}'")
            
            # Add to pattern cache
            pattern_key = f"pattern_{adjustment.old_value}"
            self.pattern_cache[adjustment.user_id].append(pattern_key)
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply pattern adjustment: {e}")
            return False
    
    def validate_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Validate pattern adjustment"""
        if adjustment.adjustment_type != AdjustmentType.PATTERN_ADD:
            return False
        
        # Check if pattern is meaningful
        if not adjustment.old_value or not adjustment.new_value:
            return False
        
        if adjustment.old_value == adjustment.new_value:
            return False
        
        return True

class VocabularyLearner(RealTimeLearner):
    """Learner for vocabulary adjustments"""
    
    def __init__(self, learning_mode: LearningMode = LearningMode.BALANCED):
        self.learning_mode = learning_mode
        self.vocabulary_additions = defaultdict(set)
        self.max_additions_per_session = 10 if learning_mode == LearningMode.AGGRESSIVE else 5
        
    def should_adjust(self, event: LearningEvent) -> bool:
        """Determine if vocabulary adjustment should be made"""
        if not event.feedback or not event.feedback.correction:
            return False
        
        # Check if we haven't added too many words recently
        current_additions = len(self.vocabulary_additions[event.user_id])
        return current_additions < self.max_additions_per_session
    
    def calculate_adjustment(self, event: LearningEvent) -> Optional[RealTimeAdjustment]:
        """Calculate vocabulary adjustment"""
        if not event.feedback or not event.feedback.correction:
            return None
        
        correction = event.feedback.correction
        
        # Add corrected word to vocabulary
        new_word = correction.corrected_text.lower()
        
        if new_word in self.vocabulary_additions[event.user_id]:
            return None  # Already added
        
        adjustment = RealTimeAdjustment(
            adjustment_id=str(uuid.uuid4()),
            user_id=event.user_id,
            model_id=event.model_id,
            adjustment_type=AdjustmentType.VOCABULARY_UPDATE,
            parameter_name="vocabulary_addition",
            old_value=None,
            new_value=new_word,
            confidence=0.6,
            trigger_event=event.event_id
        )
        
        return adjustment
    
    def apply_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Apply vocabulary adjustment"""
        try:
            logger.info(f"Applied vocabulary adjustment: added '{adjustment.new_value}'")
            
            # Add to vocabulary
            self.vocabulary_additions[adjustment.user_id].add(adjustment.new_value)
            
            return True
        except Exception as e:
            logger.error(f"Failed to apply vocabulary adjustment: {e}")
            return False
    
    def validate_adjustment(self, adjustment: RealTimeAdjustment) -> bool:
        """Validate vocabulary adjustment"""
        if adjustment.adjustment_type != AdjustmentType.VOCABULARY_UPDATE:
            return False
        
        # Check if word is valid
        if not adjustment.new_value or not isinstance(adjustment.new_value, str):
            return False
        
        if len(adjustment.new_value.strip()) < 2:
            return False
        
        return True

class RealTimeLearningSystem:
    """Main system for real-time learning and adjustment"""
    
    def __init__(self, 
                 personalization_engine: PersonalizationEngine,
                 adaptation_engine: ModelAdaptationEngine,
                 learning_mode: LearningMode = LearningMode.BALANCED):
        
        self.personalization_engine = personalization_engine
        self.adaptation_engine = adaptation_engine
        self.learning_mode = learning_mode
        
        # Learning components
        self.learners = {
            'confidence': ConfidenceThresholdLearner(learning_mode),
            'pattern': PatternLearner(learning_mode),
            'vocabulary': VocabularyLearner(learning_mode)
        }
        
        # Event processing
        self.event_queue = deque()
        self.adjustment_history = []
        self.learning_metrics = defaultdict(LearningMetrics)
        
        # Threading for real-time processing
        self._lock = threading.Lock()
        self._processing_thread = None
        self._stop_processing = False
        
        # Callbacks and observers
        self.adjustment_callbacks = []
        self.learning_observers = []
        
        # Configuration
        self.config = {
            'max_queue_size': 1000,
            'processing_interval': 0.1,  # seconds
            'effectiveness_window': timedelta(minutes=30),
            'revert_threshold': 0.3,  # revert if effectiveness < 30%
            'max_adjustments_per_minute': 10
        }
        
        # Start processing
        self._start_processing()
    
    def _start_processing(self):
        """Start real-time processing thread"""
        if self._processing_thread is None or not self._processing_thread.is_alive():
            self._stop_processing = False
            self._processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
            self._processing_thread.start()
            logger.info("Real-time learning system started")
    
    def _processing_loop(self):
        """Main processing loop for real-time learning"""
        while not self._stop_processing:
            try:
                # Process events from queue
                events_processed = 0
                max_events_per_cycle = 5
                
                while events_processed < max_events_per_cycle:
                    with self._lock:
                        if self.event_queue:
                            event = self.event_queue.popleft()
                        else:
                            event = None
                    
                    if event:
                        self._process_learning_event(event)
                        events_processed += 1
                    else:
                        break
                
                # Check for adjustments to revert
                self._check_adjustment_effectiveness()
                
                # Sleep before next cycle
                time.sleep(self.config['processing_interval'])
                
            except Exception as e:
                logger.error(f"Error in real-time learning processing: {e}")
                time.sleep(1)  # Wait longer on error
    
    def process_feedback(self, feedback: Feedback) -> List[str]:
        """Process feedback for real-time learning"""
        if not feedback.user_id:
            return []
        
        # Create learning event
        event = LearningEvent(
            event_id=str(uuid.uuid4()),
            trigger=LearningTrigger.IMMEDIATE,
            user_id=feedback.user_id,
            model_id=self._infer_model_id(feedback),
            feedback=feedback
        )
        
        # Queue event for processing
        with self._lock:
            if len(self.event_queue) < self.config['max_queue_size']:
                self.event_queue.append(event)
            else:
                logger.warning("Event queue full, dropping event")
        
        return [event.event_id]
    
    def _infer_model_id(self, feedback: Feedback) -> str:
        """Infer model ID from feedback context"""
        if feedback.context and hasattr(feedback.context, 'model_version'):
            return feedback.context.model_version or "default_model"
        return "default_model"
    
    def _process_learning_event(self, event: LearningEvent):
        """Process a single learning event"""
        try:
            adjustments_made = []
            
            # Try each learner
            for learner_name, learner in self.learners.items():
                try:
                    if learner.should_adjust(event):
                        adjustment = learner.calculate_adjustment(event)
                        
                        if adjustment and learner.validate_adjustment(adjustment):
                            # Check rate limiting
                            if self._check_rate_limit(event.user_id, event.model_id):
                                if learner.apply_adjustment(adjustment):
                                    self._record_adjustment(adjustment)
                                    adjustments_made.append(adjustment.adjustment_id)
                                    
                                    # Notify callbacks
                                    self._notify_adjustment_callbacks(adjustment)
                                    
                                    logger.info(f"Applied real-time adjustment: {learner_name} "
                                              f"for {event.user_id}")
                            else:
                                logger.info(f"Rate limit exceeded for {event.user_id}")
                
                except Exception as e:
                    logger.error(f"Error in learner {learner_name}: {e}")
            
            # Mark event as processed
            event.processed = True
            
            # Update learning metrics
            if adjustments_made:
                metrics = self.learning_metrics[f"{event.user_id}_{event.model_id}"]
                for adj_id in adjustments_made:
                    adjustment = next((a for a in self.adjustment_history 
                                    if a.adjustment_id == adj_id), None)
                    if adjustment:
                        metrics.update_metrics(adjustment)
            
        except Exception as e:
            logger.error(f"Error processing learning event {event.event_id}: {e}")
    
    def _check_rate_limit(self, user_id: str, model_id: str) -> bool:
        """Check if rate limit allows new adjustment"""
        now = datetime.now()
        recent_adjustments = [
            adj for adj in self.adjustment_history
            if (adj.user_id == user_id and adj.model_id == model_id and
                adj.timestamp > now - timedelta(minutes=1))
        ]
        
        return len(recent_adjustments) < self.config['max_adjustments_per_minute']
    
    def _record_adjustment(self, adjustment: RealTimeAdjustment):
        """Record adjustment in history"""
        with self._lock:
            self.adjustment_history.append(adjustment)
            
            # Keep history manageable
            if len(self.adjustment_history) > 10000:
                self.adjustment_history = self.adjustment_history[-5000:]
    
    def _check_adjustment_effectiveness(self):
        """Check effectiveness of recent adjustments and revert if needed"""
        now = datetime.now()
        window_start = now - self.config['effectiveness_window']
        
        # Find adjustments to evaluate
        adjustments_to_evaluate = [
            adj for adj in self.adjustment_history
            if (adj.timestamp > window_start and 
                adj.effectiveness is None and 
                not adj.reverted)
        ]
        
        for adjustment in adjustments_to_evaluate:
            effectiveness = self._calculate_adjustment_effectiveness(adjustment)
            adjustment.effectiveness = effectiveness
            
            # Revert if effectiveness is too low
            if effectiveness < self.config['revert_threshold']:
                self._revert_adjustment(adjustment)
    
    def _calculate_adjustment_effectiveness(self, adjustment: RealTimeAdjustment) -> float:
        """Calculate effectiveness of an adjustment"""
        # This is a simplified calculation
        # In a real system, this would analyze subsequent feedback and performance
        
        # For demo purposes, simulate effectiveness based on adjustment type
        base_effectiveness = {
            AdjustmentType.THRESHOLD_ADJUST: 0.7,
            AdjustmentType.PATTERN_ADD: 0.8,
            AdjustmentType.VOCABULARY_UPDATE: 0.6,
            AdjustmentType.PARAMETER_TWEAK: 0.65
        }.get(adjustment.adjustment_type, 0.5)
        
        # Add some randomness and time decay
        import random
        time_factor = max(0.5, 1.0 - (datetime.now() - adjustment.timestamp).total_seconds() / 3600)
        effectiveness = base_effectiveness * time_factor * (0.8 + 0.4 * random.random())
        
        return min(1.0, max(0.0, effectiveness))
    
    def _revert_adjustment(self, adjustment: RealTimeAdjustment):
        """Revert an ineffective adjustment"""
        try:
            logger.info(f"Reverting adjustment {adjustment.adjustment_id} "
                       f"(effectiveness: {adjustment.effectiveness:.2f})")
            
            # Mark as reverted
            adjustment.reverted = True
            
            # In a real implementation, this would restore the previous parameter value
            # For now, just log the reversion
            logger.info(f"Reverted {adjustment.parameter_name}: "
                       f"{adjustment.new_value} -> {adjustment.old_value}")
            
            # Update metrics
            metrics = self.learning_metrics[f"{adjustment.user_id}_{adjustment.model_id}"]
            metrics.reverted_adjustments += 1
            
        except Exception as e:
            logger.error(f"Error reverting adjustment {adjustment.adjustment_id}: {e}")
    
    def register_adjustment_callback(self, callback: Callable[[RealTimeAdjustment], None]):
        """Register callback for adjustment events"""
        self.adjustment_callbacks.append(callback)
    
    def _notify_adjustment_callbacks(self, adjustment: RealTimeAdjustment):
        """Notify registered callbacks of adjustment"""
        for callback in self.adjustment_callbacks:
            try:
                callback(adjustment)
            except Exception as e:
                logger.error(f"Error in adjustment callback: {e}")
    
    def get_learning_statistics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get learning statistics"""
        if user_id:
            # User-specific statistics
            user_adjustments = [adj for adj in self.adjustment_history if adj.user_id == user_id]
            user_metrics = {k: v for k, v in self.learning_metrics.items() if k.startswith(user_id)}
        else:
            # Global statistics
            user_adjustments = self.adjustment_history
            user_metrics = dict(self.learning_metrics)
        
        if not user_adjustments:
            return {'total_adjustments': 0}
        
        # Calculate statistics
        total_adjustments = len(user_adjustments)
        successful_adjustments = len([adj for adj in user_adjustments 
                                    if adj.effectiveness and adj.effectiveness > 0.5])
        reverted_adjustments = len([adj for adj in user_adjustments if adj.reverted])
        
        # Adjustment types
        type_counts = defaultdict(int)
        for adj in user_adjustments:
            type_counts[adj.adjustment_type.value] += 1
        
        # Recent activity
        recent_cutoff = datetime.now() - timedelta(hours=24)
        recent_adjustments = len([adj for adj in user_adjustments 
                                if adj.timestamp > recent_cutoff])
        
        # Average effectiveness
        effectiveness_scores = [adj.effectiveness for adj in user_adjustments 
                              if adj.effectiveness is not None]
        avg_effectiveness = statistics.mean(effectiveness_scores) if effectiveness_scores else 0.0
        
        return {
            'total_adjustments': total_adjustments,
            'successful_adjustments': successful_adjustments,
            'reverted_adjustments': reverted_adjustments,
            'success_rate': successful_adjustments / total_adjustments if total_adjustments > 0 else 0,
            'revert_rate': reverted_adjustments / total_adjustments if total_adjustments > 0 else 0,
            'average_effectiveness': avg_effectiveness,
            'adjustment_types': dict(type_counts),
            'recent_adjustments_24h': recent_adjustments,
            'queue_size': len(self.event_queue),
            'learning_mode': self.learning_mode.value
        }
    
    def get_user_adjustments(self, user_id: str, limit: int = 50) -> List[RealTimeAdjustment]:
        """Get recent adjustments for a user"""
        user_adjustments = [adj for adj in self.adjustment_history if adj.user_id == user_id]
        user_adjustments.sort(key=lambda x: x.timestamp, reverse=True)
        return user_adjustments[:limit]
    
    def force_learning_update(self, user_id: str, model_id: str) -> str:
        """Force a learning update for a user/model combination"""
        event = LearningEvent(
            event_id=str(uuid.uuid4()),
            trigger=LearningTrigger.USER_REQUEST,
            user_id=user_id,
            model_id=model_id,
            context={'forced': True}
        )
        
        with self._lock:
            self.event_queue.append(event)
        
        logger.info(f"Forced learning update queued for {user_id}/{model_id}")
        return event.event_id
    
    def set_learning_mode(self, mode: LearningMode):
        """Set learning mode"""
        self.learning_mode = mode
        
        # Update learners with new mode
        for learner in self.learners.values():
            if hasattr(learner, 'learning_mode'):
                learner.learning_mode = mode
        
        logger.info(f"Learning mode set to: {mode.value}")
    
    def pause_learning(self, user_id: Optional[str] = None):
        """Pause learning for a user or globally"""
        # Implementation would pause learning for specified user or globally
        logger.info(f"Learning paused for user: {user_id or 'all users'}")
    
    def resume_learning(self, user_id: Optional[str] = None):
        """Resume learning for a user or globally"""
        # Implementation would resume learning for specified user or globally
        logger.info(f"Learning resumed for user: {user_id or 'all users'}")
    
    def cleanup_old_adjustments(self, days: int = 30) -> int:
        """Clean up old adjustments"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        original_count = len(self.adjustment_history)
        self.adjustment_history = [adj for adj in self.adjustment_history 
                                 if adj.timestamp >= cutoff_date]
        
        cleaned_count = original_count - len(self.adjustment_history)
        logger.info(f"Cleaned up {cleaned_count} old adjustments")
        
        return cleaned_count
    
    def stop(self):
        """Stop the real-time learning system"""
        self._stop_processing = True
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5)
        logger.info("Real-time learning system stopped")

# Utility functions
def create_realtime_learning_system(personalization_engine: PersonalizationEngine,
                                   adaptation_engine: ModelAdaptationEngine,
                                   learning_mode: LearningMode = LearningMode.BALANCED) -> RealTimeLearningSystem:
    """Create a real-time learning system instance"""
    return RealTimeLearningSystem(personalization_engine, adaptation_engine, learning_mode)

# Example usage and testing
def example_usage():
    """Example usage of real-time learning system"""
    from user_learning_profile import create_personalization_engine, create_user_profile_storage
    from feedback_data_models import create_feedback_storage
    from model_adaptation_engine import create_model_adaptation_engine
    
    # Create dependencies
    profile_storage = create_user_profile_storage("example_profiles.db")
    feedback_storage = create_feedback_storage("example_feedback.db")
    personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
    adaptation_engine = create_model_adaptation_engine(personalization_engine, feedback_storage)
    
    # Create real-time learning system
    learning_system = create_realtime_learning_system(
        personalization_engine, adaptation_engine, LearningMode.BALANCED
    )
    
    print("🚀 Real-Time Learning System Example")
    
    # Create sample feedback
    context = FeedbackContext(
        content_type=ContentType.TRANSCRIPTION,
        content_id="example_content",
        original_content="example transcription",
        confidence_score=0.7
    )
    
    rating = Rating(
        rating_id="example_rating",
        rating_type=RatingType.STARS,
        value=2,  # Low rating to trigger adjustment
        max_value=5
    )
    
    feedback = Feedback(
        feedback_id="example_feedback",
        user_id="example_user",
        feedback_type=FeedbackType.RATING,
        context=context,
        timestamp=datetime.now(),
        rating=rating
    )
    
    # Process feedback for real-time learning
    event_ids = learning_system.process_feedback(feedback)
    print(f"✅ Processed feedback, created events: {event_ids}")
    
    # Wait for processing
    time.sleep(2)
    
    # Get learning statistics
    stats = learning_system.get_learning_statistics()
    print(f"📊 Learning statistics: {stats}")
    
    # Get user adjustments
    adjustments = learning_system.get_user_adjustments("example_user")
    print(f"🔧 User adjustments: {len(adjustments)}")
    
    # Stop system
    learning_system.stop()
    adaptation_engine.stop()
    print("🛑 Systems stopped")

if __name__ == "__main__":
    example_usage()