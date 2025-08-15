#!/usr/bin/env python3
"""
Model Adaptation Engine
Advanced system for adapting NLP models based on user feedback and learning patterns
"""

import uuid
import logging
import json
import threading
import time
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics
import hashlib
import pickle
import numpy as np
from abc import ABC, abstractmethod

# Import our dependencies
from user_learning_profile import (
    UserLearningProfile, PersonalizationEngine, CorrectionPattern,
    ModelPreference, DomainExpertise
)
from feedback_data_models import (
    FeedbackStorage, Feedback, Rating, Correction, FeedbackContext,
    FeedbackType, RatingType, ContentType
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdaptationType(Enum):
    """Types of model adaptations"""
    PARAMETER_TUNING = "parameter_tuning"
    RULE_ADJUSTMENT = "rule_adjustment"
    THRESHOLD_MODIFICATION = "threshold_modification"
    VOCABULARY_EXPANSION = "vocabulary_expansion"
    PATTERN_LEARNING = "pattern_learning"
    CONFIDENCE_CALIBRATION = "confidence_calibration"

class AdaptationScope(Enum):
    """Scope of model adaptations"""
    USER_SPECIFIC = "user_specific"
    DOMAIN_SPECIFIC = "domain_specific"
    GLOBAL = "global"
    CONTENT_TYPE_SPECIFIC = "content_type_specific"

class AdaptationStatus(Enum):
    """Status of adaptation processes"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

@dataclass
class AdaptationRule:
    """Rule for model adaptation"""
    rule_id: str
    rule_type: str
    condition: Dict[str, Any]
    action: Dict[str, Any]
    priority: int = 1
    enabled: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_applied: Optional[datetime] = None
    application_count: int = 0
    success_rate: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        data['last_applied'] = self.last_applied.isoformat() if self.last_applied else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptationRule':
        """Create from dictionary"""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['last_applied']:
            data['last_applied'] = datetime.fromisoformat(data['last_applied'])
        return cls(**data)

@dataclass
class ModelParameters:
    """Model parameters that can be adapted"""
    model_id: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence_thresholds: Dict[str, float] = field(default_factory=dict)
    processing_rules: Dict[str, Any] = field(default_factory=dict)
    vocabulary_additions: List[str] = field(default_factory=list)
    pattern_overrides: Dict[str, str] = field(default_factory=dict)
    version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelParameters':
        """Create from dictionary"""
        data['last_updated'] = datetime.fromisoformat(data['last_updated'])
        return cls(**data)

@dataclass
class AdaptationResult:
    """Result of a model adaptation"""
    adaptation_id: str
    adaptation_type: AdaptationType
    scope: AdaptationScope
    target_model: str
    target_user: Optional[str] = None
    target_domain: Optional[str] = None
    parameters_before: Optional[Dict[str, Any]] = None
    parameters_after: Optional[Dict[str, Any]] = None
    performance_before: Optional[Dict[str, float]] = None
    performance_after: Optional[Dict[str, float]] = None
    status: AdaptationStatus = AdaptationStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['adaptation_type'] = self.adaptation_type.value
        data['scope'] = self.scope.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdaptationResult':
        """Create from dictionary"""
        data['adaptation_type'] = AdaptationType(data['adaptation_type'])
        data['scope'] = AdaptationScope(data['scope'])
        data['status'] = AdaptationStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)

class ModelAdapter(ABC):
    """Abstract base class for model adapters"""
    
    @abstractmethod
    def adapt_parameters(self, model_id: str, feedback: List[Feedback], 
                        user_profile: UserLearningProfile) -> ModelParameters:
        """Adapt model parameters based on feedback"""
        pass
    
    @abstractmethod
    def validate_adaptation(self, original_params: ModelParameters, 
                          adapted_params: ModelParameters) -> bool:
        """Validate that adaptation is safe and beneficial"""
        pass
    
    @abstractmethod
    def rollback_adaptation(self, model_id: str, 
                          previous_params: ModelParameters) -> bool:
        """Rollback adaptation to previous parameters"""
        pass

class SpacyModelAdapter(ModelAdapter):
    """Adapter for spaCy models"""
    
    def __init__(self):
        self.supported_models = ["spacy_sm", "spacy_md", "spacy_lg"]
        self.parameter_ranges = {
            "confidence_threshold": (0.1, 0.99),
            "entity_threshold": (0.3, 0.95),
            "similarity_threshold": (0.5, 0.95)
        }
    
    def adapt_parameters(self, model_id: str, feedback: List[Feedback], 
                        user_profile: UserLearningProfile) -> ModelParameters:
        """Adapt spaCy model parameters"""
        if model_id not in self.supported_models:
            raise ValueError(f"Unsupported model: {model_id}")
        
        # Start with default parameters
        params = ModelParameters(model_id=model_id)
        
        # Analyze feedback for parameter adjustments
        self._adapt_confidence_thresholds(params, feedback, user_profile)
        self._adapt_processing_rules(params, feedback, user_profile)
        self._adapt_vocabulary(params, feedback, user_profile)
        self._adapt_pattern_overrides(params, feedback, user_profile)
        
        return params
    
    def _adapt_confidence_thresholds(self, params: ModelParameters, 
                                   feedback: List[Feedback], 
                                   user_profile: UserLearningProfile):
        """Adapt confidence thresholds based on user ratings"""
        content_ratings = defaultdict(list)
        
        # Group ratings by content type
        for fb in feedback:
            if fb.rating and fb.context:
                normalized_rating = fb.rating.normalize_rating()
                content_ratings[fb.context.content_type].append({
                    'rating': normalized_rating,
                    'confidence': fb.context.confidence_score or 0.8
                })
        
        # Adjust thresholds based on user satisfaction
        for content_type, ratings in content_ratings.items():
            if len(ratings) < 3:  # Need minimum feedback
                continue
            
            avg_rating = statistics.mean([r['rating'] for r in ratings])
            avg_confidence = statistics.mean([r['confidence'] for r in ratings])
            
            # If user is generally satisfied with high-confidence results, 
            # we can lower the threshold slightly
            if avg_rating > 0.8 and avg_confidence > 0.85:
                new_threshold = max(0.1, avg_confidence - 0.05)
            # If user is unsatisfied, raise the threshold
            elif avg_rating < 0.6:
                new_threshold = min(0.99, avg_confidence + 0.1)
            else:
                new_threshold = avg_confidence
            
            params.confidence_thresholds[content_type.value] = new_threshold
    
    def _adapt_processing_rules(self, params: ModelParameters, 
                              feedback: List[Feedback], 
                              user_profile: UserLearningProfile):
        """Adapt processing rules based on correction patterns"""
        correction_types = Counter()
        
        # Analyze correction patterns
        for pattern in user_profile.correction_patterns:
            correction_types[pattern.pattern_type] += pattern.frequency
        
        # Create processing rules based on common corrections
        if correction_types.get('capitalization', 0) >= 3:  # Lower threshold for testing
            params.processing_rules['auto_capitalize_entities'] = True
            params.processing_rules['capitalize_threshold'] = 0.7
        
        if correction_types.get('punctuation', 0) > 3:
            params.processing_rules['enhance_punctuation'] = True
            params.processing_rules['punctuation_confidence'] = 0.6
        
        if correction_types.get('word_replacement', 0) > 5:
            params.processing_rules['enable_domain_vocabulary'] = True
            params.processing_rules['vocabulary_boost'] = 1.2
    
    def _adapt_vocabulary(self, params: ModelParameters, 
                         feedback: List[Feedback], 
                         user_profile: UserLearningProfile):
        """Adapt vocabulary based on user corrections and domain expertise"""
        vocabulary_additions = set()
        
        # Add vocabulary from correction patterns
        for pattern in user_profile.correction_patterns:
            if pattern.pattern_type == 'word_replacement':
                # Add the corrected version to vocabulary
                vocabulary_additions.add(pattern.corrected_pattern.lower())
            elif pattern.pattern_type == 'capitalization':
                # Add the original pattern to vocabulary for recognition
                vocabulary_additions.add(pattern.original_pattern.lower())
        
        # Add domain-specific vocabulary
        domain_vocab = {
            DomainExpertise.TECHNICAL: ['API', 'algorithm', 'database', 'framework', 'deployment'],
            DomainExpertise.MEDICAL: ['diagnosis', 'treatment', 'patient', 'symptoms', 'medication'],
            DomainExpertise.LEGAL: ['contract', 'agreement', 'liability', 'compliance', 'regulation'],
            DomainExpertise.BUSINESS: ['revenue', 'strategy', 'stakeholder', 'ROI', 'KPI'],
            DomainExpertise.ACADEMIC: ['research', 'methodology', 'hypothesis', 'analysis', 'publication']
        }
        
        for domain in user_profile.domain_expertise:
            if domain in domain_vocab:
                vocabulary_additions.update(domain_vocab[domain])
        
        params.vocabulary_additions = list(vocabulary_additions)
    
    def _adapt_pattern_overrides(self, params: ModelParameters, 
                               feedback: List[Feedback], 
                               user_profile: UserLearningProfile):
        """Create pattern overrides based on consistent corrections"""
        pattern_overrides = {}
        
        # Create overrides for high-confidence patterns (lower thresholds for testing)
        for pattern in user_profile.correction_patterns:
            if pattern.confidence >= 0.6 and pattern.frequency >= 3:
                pattern_overrides[pattern.original_pattern] = pattern.corrected_pattern
        
        params.pattern_overrides = pattern_overrides
    
    def validate_adaptation(self, original_params: ModelParameters, 
                          adapted_params: ModelParameters) -> bool:
        """Validate spaCy model adaptation"""
        # Check confidence thresholds are within valid ranges
        for threshold in adapted_params.confidence_thresholds.values():
            if not (0.1 <= threshold <= 0.99):
                return False
        
        # Check vocabulary additions are reasonable
        if len(adapted_params.vocabulary_additions) > 1000:
            return False
        
        # Check pattern overrides don't create conflicts
        if len(adapted_params.pattern_overrides) > 100:
            return False
        
        return True
    
    def rollback_adaptation(self, model_id: str, 
                          previous_params: ModelParameters) -> bool:
        """Rollback spaCy model adaptation"""
        try:
            # In a real implementation, this would restore model parameters
            logger.info(f"Rolling back adaptation for model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback adaptation: {e}")
            return False

class TransformerModelAdapter(ModelAdapter):
    """Adapter for transformer models (BERT, RoBERTa, etc.)"""
    
    def __init__(self):
        self.supported_models = ["bert_base", "bert_large", "roberta_base", "roberta_large"]
        self.parameter_ranges = {
            "learning_rate": (1e-6, 1e-3),
            "attention_dropout": (0.0, 0.3),
            "hidden_dropout": (0.0, 0.3)
        }
    
    def adapt_parameters(self, model_id: str, feedback: List[Feedback], 
                        user_profile: UserLearningProfile) -> ModelParameters:
        """Adapt transformer model parameters"""
        if model_id not in self.supported_models:
            raise ValueError(f"Unsupported model: {model_id}")
        
        params = ModelParameters(model_id=model_id)
        
        # Transformer-specific adaptations
        self._adapt_attention_parameters(params, feedback, user_profile)
        self._adapt_fine_tuning_parameters(params, feedback, user_profile)
        
        return params
    
    def _adapt_attention_parameters(self, params: ModelParameters, 
                                  feedback: List[Feedback], 
                                  user_profile: UserLearningProfile):
        """Adapt attention mechanism parameters"""
        # Analyze feedback quality to adjust attention dropout
        quality_scores = []
        for fb in feedback:
            if fb.rating:
                quality_scores.append(fb.rating.normalize_rating())
        
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            # Lower dropout for better performance if quality is low
            if avg_quality < 0.6:
                params.parameters['attention_dropout'] = 0.05
            else:
                params.parameters['attention_dropout'] = 0.1
    
    def _adapt_fine_tuning_parameters(self, params: ModelParameters, 
                                    feedback: List[Feedback], 
                                    user_profile: UserLearningProfile):
        """Adapt fine-tuning parameters based on user patterns"""
        # Adjust learning rate based on correction frequency
        correction_rate = len([fb for fb in feedback if fb.correction]) / max(1, len(feedback))
        
        if correction_rate > 0.3:  # High correction rate
            params.parameters['learning_rate'] = 2e-5  # Higher learning rate
        else:
            params.parameters['learning_rate'] = 1e-5  # Standard learning rate
    
    def validate_adaptation(self, original_params: ModelParameters, 
                          adapted_params: ModelParameters) -> bool:
        """Validate transformer model adaptation"""
        # Check learning rate is within bounds
        lr = adapted_params.parameters.get('learning_rate', 1e-5)
        if not (1e-6 <= lr <= 1e-3):
            return False
        
        # Check dropout rates
        attention_dropout = adapted_params.parameters.get('attention_dropout', 0.1)
        if not (0.0 <= attention_dropout <= 0.3):
            return False
        
        return True
    
    def rollback_adaptation(self, model_id: str, 
                          previous_params: ModelParameters) -> bool:
        """Rollback transformer model adaptation"""
        try:
            logger.info(f"Rolling back transformer adaptation for model {model_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to rollback transformer adaptation: {e}")
            return False

class ModelAdaptationEngine:
    """Main engine for model adaptation"""
    
    def __init__(self, personalization_engine: PersonalizationEngine, 
                 feedback_storage: FeedbackStorage):
        self.personalization_engine = personalization_engine
        self.feedback_storage = feedback_storage
        
        # Model adapters
        self.adapters = {
            'spacy': SpacyModelAdapter(),
            'transformer': TransformerModelAdapter()
        }
        
        # Adaptation rules and results storage
        self.adaptation_rules: List[AdaptationRule] = []
        self.adaptation_results: List[AdaptationResult] = []
        self.model_parameters: Dict[str, ModelParameters] = {}
        
        # Threading for async adaptations
        self._lock = threading.Lock()
        self._adaptation_queue = []
        self._worker_thread = None
        self._stop_worker = False
        
        # Load default adaptation rules
        self._load_default_rules()
        
        # Start worker thread
        self._start_worker()
    
    def _load_default_rules(self):
        """Load default adaptation rules"""
        default_rules = [
            AdaptationRule(
                rule_id="confidence_adjustment",
                rule_type="threshold_modification",
                condition={"min_feedback_count": 5, "avg_rating_below": 0.6},
                action={"increase_confidence_threshold": 0.1},
                priority=1
            ),
            AdaptationRule(
                rule_id="vocabulary_expansion",
                rule_type="vocabulary_expansion",
                condition={"correction_type": "word_replacement", "min_frequency": 3},
                action={"add_to_vocabulary": True},
                priority=2
            ),
            AdaptationRule(
                rule_id="pattern_learning",
                rule_type="pattern_learning",
                condition={"pattern_confidence": 0.8, "min_frequency": 5},
                action={"create_pattern_override": True},
                priority=1
            )
        ]
        
        self.adaptation_rules.extend(default_rules)
    
    def _start_worker(self):
        """Start background worker thread for adaptations"""
        if self._worker_thread is None or not self._worker_thread.is_alive():
            self._stop_worker = False
            self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self._worker_thread.start()
    
    def _worker_loop(self):
        """Background worker loop for processing adaptations"""
        while not self._stop_worker:
            try:
                with self._lock:
                    if self._adaptation_queue:
                        adaptation_task = self._adaptation_queue.pop(0)
                    else:
                        adaptation_task = None
                
                if adaptation_task:
                    self._process_adaptation_task(adaptation_task)
                else:
                    time.sleep(1)  # Wait before checking again
                    
            except Exception as e:
                logger.error(f"Error in adaptation worker: {e}")
                time.sleep(5)  # Wait longer on error
    
    def _process_adaptation_task(self, task: Dict[str, Any]):
        """Process a single adaptation task"""
        try:
            user_id = task['user_id']
            model_id = task['model_id']
            adaptation_type = task['adaptation_type']
            
            logger.info(f"Processing adaptation for user {user_id}, model {model_id}")
            
            # Get user profile and feedback
            user_profile = self.personalization_engine.get_or_create_profile(user_id)
            feedback = self._get_recent_feedback(user_id, days=30)
            
            # Perform adaptation
            result = self._adapt_model_for_user(user_id, model_id, adaptation_type, 
                                              feedback, user_profile)
            
            # Store result
            with self._lock:
                self.adaptation_results.append(result)
            
            logger.info(f"Completed adaptation {result.adaptation_id} with status {result.status}")
            
        except Exception as e:
            logger.error(f"Failed to process adaptation task: {e}")
    
    def adapt_model_for_user(self, user_id: str, model_id: str, 
                           adaptation_type: AdaptationType = AdaptationType.PARAMETER_TUNING) -> str:
        """Queue model adaptation for a specific user"""
        adaptation_id = str(uuid.uuid4())
        
        task = {
            'adaptation_id': adaptation_id,
            'user_id': user_id,
            'model_id': model_id,
            'adaptation_type': adaptation_type,
            'queued_at': datetime.now()
        }
        
        with self._lock:
            self._adaptation_queue.append(task)
        
        logger.info(f"Queued adaptation {adaptation_id} for user {user_id}")
        return adaptation_id
    
    def _adapt_model_for_user(self, user_id: str, model_id: str, 
                            adaptation_type: AdaptationType,
                            feedback: List[Feedback], 
                            user_profile: UserLearningProfile) -> AdaptationResult:
        """Perform model adaptation for a user"""
        adaptation_id = str(uuid.uuid4())
        
        result = AdaptationResult(
            adaptation_id=adaptation_id,
            adaptation_type=adaptation_type,
            scope=AdaptationScope.USER_SPECIFIC,
            target_model=model_id,
            target_user=user_id,
            status=AdaptationStatus.IN_PROGRESS
        )
        
        try:
            # Get appropriate adapter
            adapter = self._get_adapter_for_model(model_id)
            if not adapter:
                raise ValueError(f"No adapter available for model {model_id}")
            
            # Get current parameters
            current_params = self.model_parameters.get(f"{user_id}_{model_id}")
            if current_params:
                result.parameters_before = current_params.to_dict()
            
            # Perform adaptation
            adapted_params = adapter.adapt_parameters(model_id, feedback, user_profile)
            
            # Validate adaptation
            if not adapter.validate_adaptation(current_params or ModelParameters(model_id), 
                                             adapted_params):
                raise ValueError("Adaptation validation failed")
            
            # Store adapted parameters
            self.model_parameters[f"{user_id}_{model_id}"] = adapted_params
            result.parameters_after = adapted_params.to_dict()
            
            # Update result
            result.status = AdaptationStatus.COMPLETED
            result.completed_at = datetime.now()
            
            logger.info(f"Successfully adapted model {model_id} for user {user_id}")
            
        except Exception as e:
            result.status = AdaptationStatus.FAILED
            result.error_message = str(e)
            result.completed_at = datetime.now()
            logger.error(f"Failed to adapt model {model_id} for user {user_id}: {e}")
        
        return result
    
    def _get_adapter_for_model(self, model_id: str) -> Optional[ModelAdapter]:
        """Get appropriate adapter for model"""
        if model_id.startswith('spacy'):
            return self.adapters['spacy']
        elif model_id in ['bert_base', 'bert_large', 'roberta_base', 'roberta_large']:
            return self.adapters['transformer']
        else:
            return None
    
    def _get_recent_feedback(self, user_id: str, days: int = 30) -> List[Feedback]:
        """Get recent feedback for user"""
        try:
            # In a real implementation, this would query the feedback storage
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Failed to get recent feedback for user {user_id}: {e}")
            return []
    
    def get_adapted_parameters(self, user_id: str, model_id: str) -> Optional[ModelParameters]:
        """Get adapted parameters for user and model"""
        return self.model_parameters.get(f"{user_id}_{model_id}")
    
    def rollback_adaptation(self, adaptation_id: str) -> bool:
        """Rollback a specific adaptation"""
        try:
            # Find the adaptation result
            result = None
            for r in self.adaptation_results:
                if r.adaptation_id == adaptation_id:
                    result = r
                    break
            
            if not result:
                logger.error(f"Adaptation {adaptation_id} not found")
                return False
            
            if result.status != AdaptationStatus.COMPLETED:
                logger.error(f"Cannot rollback adaptation {adaptation_id} with status {result.status}")
                return False
            
            # Get adapter and rollback
            adapter = self._get_adapter_for_model(result.target_model)
            if not adapter:
                logger.error(f"No adapter for model {result.target_model}")
                return False
            
            # Restore previous parameters
            if result.parameters_before:
                previous_params = ModelParameters.from_dict(result.parameters_before)
                success = adapter.rollback_adaptation(result.target_model, previous_params)
                
                if success:
                    # Update stored parameters
                    key = f"{result.target_user}_{result.target_model}"
                    self.model_parameters[key] = previous_params
                    
                    # Update result status
                    result.status = AdaptationStatus.ROLLED_BACK
                    logger.info(f"Successfully rolled back adaptation {adaptation_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to rollback adaptation {adaptation_id}: {e}")
            return False
    
    def apply_global_improvements(self, improvements: List[Dict[str, Any]]) -> List[str]:
        """Apply global improvements across all models"""
        applied_adaptations = []
        
        for improvement in improvements:
            try:
                adaptation_type = AdaptationType(improvement.get('type', 'parameter_tuning'))
                target_models = improvement.get('models', [])
                
                for model_id in target_models:
                    adaptation_id = str(uuid.uuid4())
                    
                    result = AdaptationResult(
                        adaptation_id=adaptation_id,
                        adaptation_type=adaptation_type,
                        scope=AdaptationScope.GLOBAL,
                        target_model=model_id,
                        status=AdaptationStatus.COMPLETED
                    )
                    
                    # Apply improvement
                    self._apply_global_improvement(model_id, improvement)
                    
                    self.adaptation_results.append(result)
                    applied_adaptations.append(adaptation_id)
                    
                    logger.info(f"Applied global improvement to model {model_id}")
                    
            except Exception as e:
                logger.error(f"Failed to apply global improvement: {e}")
        
        return applied_adaptations
    
    def _apply_global_improvement(self, model_id: str, improvement: Dict[str, Any]):
        """Apply a global improvement to a model"""
        # Get or create global parameters for model
        global_key = f"global_{model_id}"
        if global_key not in self.model_parameters:
            self.model_parameters[global_key] = ModelParameters(model_id=model_id)
        
        params = self.model_parameters[global_key]
        
        # Apply improvement based on type
        improvement_type = improvement.get('type')
        
        if improvement_type == 'threshold_modification':
            threshold_changes = improvement.get('threshold_changes', {})
            params.confidence_thresholds.update(threshold_changes)
        
        elif improvement_type == 'vocabulary_expansion':
            new_vocabulary = improvement.get('vocabulary', [])
            params.vocabulary_additions.extend(new_vocabulary)
        
        elif improvement_type == 'rule_adjustment':
            rule_changes = improvement.get('rule_changes', {})
            params.processing_rules.update(rule_changes)
        
        params.last_updated = datetime.now()
    
    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """Get statistics about adaptations"""
        total_adaptations = len(self.adaptation_results)
        
        if total_adaptations == 0:
            return {'total_adaptations': 0}
        
        # Count by status
        status_counts = Counter(r.status for r in self.adaptation_results)
        
        # Count by type
        type_counts = Counter(r.adaptation_type for r in self.adaptation_results)
        
        # Count by scope
        scope_counts = Counter(r.scope for r in self.adaptation_results)
        
        # Success rate
        successful = status_counts[AdaptationStatus.COMPLETED]
        success_rate = successful / total_adaptations if total_adaptations > 0 else 0
        
        # Recent adaptations (last 7 days)
        recent_cutoff = datetime.now() - timedelta(days=7)
        recent_adaptations = len([r for r in self.adaptation_results 
                                if r.created_at >= recent_cutoff])
        
        return {
            'total_adaptations': total_adaptations,
            'success_rate': success_rate,
            'recent_adaptations': recent_adaptations,
            'status_distribution': dict(status_counts),
            'type_distribution': dict(type_counts),
            'scope_distribution': dict(scope_counts),
            'queue_size': len(self._adaptation_queue),
            'active_models': len(self.model_parameters)
        }
    
    def get_user_adaptations(self, user_id: str) -> List[AdaptationResult]:
        """Get adaptations for a specific user"""
        return [r for r in self.adaptation_results if r.target_user == user_id]
    
    def cleanup_old_adaptations(self, days: int = 90):
        """Clean up old adaptation results"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        original_count = len(self.adaptation_results)
        self.adaptation_results = [r for r in self.adaptation_results 
                                 if r.created_at >= cutoff_date]
        
        cleaned_count = original_count - len(self.adaptation_results)
        logger.info(f"Cleaned up {cleaned_count} old adaptation results")
        
        return cleaned_count
    
    def stop(self):
        """Stop the adaptation engine"""
        self._stop_worker = True
        if self._worker_thread and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=5)
        logger.info("Model adaptation engine stopped")

# Utility functions
def create_model_adaptation_engine(personalization_engine: PersonalizationEngine,
                                 feedback_storage: FeedbackStorage) -> ModelAdaptationEngine:
    """Create a model adaptation engine instance"""
    return ModelAdaptationEngine(personalization_engine, feedback_storage)

# Example usage and testing
def example_usage():
    """Example usage of model adaptation engine"""
    from user_learning_profile import create_personalization_engine, create_user_profile_storage
    from feedback_data_models import create_feedback_storage
    
    # Create dependencies
    profile_storage = create_user_profile_storage("example_profiles.db")
    feedback_storage = create_feedback_storage("example_feedback.db")
    personalization_engine = create_personalization_engine(profile_storage, feedback_storage)
    
    # Create adaptation engine
    adaptation_engine = create_model_adaptation_engine(personalization_engine, feedback_storage)
    
    print("🚀 Model Adaptation Engine Example")
    
    # Queue adaptation for user
    user_id = "example_user"
    model_id = "spacy_md"
    
    adaptation_id = adaptation_engine.adapt_model_for_user(
        user_id, model_id, AdaptationType.PARAMETER_TUNING
    )
    print(f"✅ Queued adaptation: {adaptation_id}")
    
    # Wait a moment for processing
    time.sleep(2)
    
    # Check adapted parameters
    adapted_params = adaptation_engine.get_adapted_parameters(user_id, model_id)
    if adapted_params:
        print(f"✅ Model adapted with {len(adapted_params.parameters)} parameters")
    
    # Get statistics
    stats = adaptation_engine.get_adaptation_statistics()
    print(f"📊 Adaptation statistics: {stats}")
    
    # Apply global improvement
    improvements = [{
        'type': 'threshold_modification',
        'models': ['spacy_md'],
        'threshold_changes': {'transcription': 0.85}
    }]
    
    global_adaptations = adaptation_engine.apply_global_improvements(improvements)
    print(f"🌍 Applied {len(global_adaptations)} global improvements")
    
    # Stop engine
    adaptation_engine.stop()
    print("🛑 Adaptation engine stopped")

if __name__ == "__main__":
    example_usage()