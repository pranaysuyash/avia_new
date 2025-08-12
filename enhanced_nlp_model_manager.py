#!/usr/bin/env python3
"""
Enhanced NLP Model Manager - Core Infrastructure
Extends existing ModelManager with multi-model NLP support and intelligent selection
"""

import asyncio
import logging
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import json
import hashlib
import tempfile
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import psutil
import gc

# Import existing components to extend
from whisper_advanced_processor import ModelManager as BaseModelManager, WhisperModel
from unified_nlp_foundation import UnifiedNLPFoundation, NLPCapability, NLPResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NLPModelType(Enum):
    """Enhanced NLP model types with specifications"""
    SPACY_SMALL = "en_core_web_sm"
    SPACY_MEDIUM = "en_core_web_md" 
    SPACY_LARGE = "en_core_web_lg"
    SPACY_TRANSFORMER = "en_core_web_trf"
    BERT_BASE = "bert-base-uncased"
    ROBERTA_BASE = "roberta-base"
    DISTILBERT = "distilbert-base-uncased"
    
    @property
    def model_size(self) -> str:
        """Model size classification"""
        size_map = {
            "en_core_web_sm": "Small (50MB)",
            "en_core_web_md": "Medium (50MB)", 
            "en_core_web_lg": "Large (750MB)",
            "en_core_web_trf": "Transformer (560MB)",
            "bert-base-uncased": "Base (440MB)",
            "roberta-base": "Base (500MB)",
            "distilbert-base-uncased": "Distilled (250MB)"
        }
        return size_map.get(self.value, "Unknown")
    
    @property
    def accuracy_level(self) -> str:
        """Relative accuracy level"""
        accuracy_map = {
            "en_core_web_sm": "Basic",
            "en_core_web_md": "Good",
            "en_core_web_lg": "High", 
            "en_core_web_trf": "Highest",
            "bert-base-uncased": "Very High",
            "roberta-base": "Very High",
            "distilbert-base-uncased": "High"
        }
        return accuracy_map.get(self.value, "Unknown")
    
    @property
    def processing_speed(self) -> str:
        """Relative processing speed"""
        speed_map = {
            "en_core_web_sm": "Very Fast",
            "en_core_web_md": "Fast",
            "en_core_web_lg": "Medium",
            "en_core_web_trf": "Slow",
            "bert-base-uncased": "Slow",
            "roberta-base": "Slow", 
            "distilbert-base-uncased": "Medium"
        }
        return speed_map.get(self.value, "Unknown")
    
    @property
    def use_cases(self) -> List[str]:
        """Recommended use cases"""
        cases_map = {
            "en_core_web_sm": ["Quick processing", "Real-time analysis", "Resource-constrained environments"],
            "en_core_web_md": ["General NLP tasks", "Balanced performance", "Production systems"],
            "en_core_web_lg": ["High-quality analysis", "Professional applications", "Research"],
            "en_core_web_trf": ["Maximum accuracy", "Research", "Critical applications"],
            "bert-base-uncased": ["Advanced NLP", "Contextual understanding", "Research"],
            "roberta-base": ["State-of-the-art NLP", "Complex text analysis", "Research"],
            "distilbert-base-uncased": ["Efficient transformers", "Production deployment", "Balanced accuracy/speed"]
        }
        return cases_map.get(self.value, ["General use"])

@dataclass
class ModelConfig:
    """Enhanced model configuration"""
    model_type: NLPModelType
    model_name: str
    capabilities: List[NLPCapability]
    resource_requirements: Dict[str, Any]
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    fallback_models: List[NLPModelType] = field(default_factory=list)
    
    def __post_init__(self):
        """Set default fallback models"""
        if not self.fallback_models:
            # Define intelligent fallback chains
            fallback_chains = {
                NLPModelType.SPACY_TRANSFORMER: [NLPModelType.SPACY_LARGE, NLPModelType.SPACY_MEDIUM, NLPModelType.SPACY_SMALL],
                NLPModelType.SPACY_LARGE: [NLPModelType.SPACY_MEDIUM, NLPModelType.SPACY_SMALL],
                NLPModelType.SPACY_MEDIUM: [NLPModelType.SPACY_SMALL],
                NLPModelType.BERT_BASE: [NLPModelType.DISTILBERT, NLPModelType.SPACY_LARGE],
                NLPModelType.ROBERTA_BASE: [NLPModelType.BERT_BASE, NLPModelType.DISTILBERT],
                NLPModelType.DISTILBERT: [NLPModelType.SPACY_LARGE, NLPModelType.SPACY_MEDIUM]
            }
            self.fallback_models = fallback_chains.get(self.model_type, [NLPModelType.SPACY_SMALL])

@dataclass
class ProcessingContext:
    """Context for NLP processing requests"""
    content_type: str  # "meeting", "document", "conversation", etc.
    content_length: int
    complexity_estimate: float  # 0.0 to 1.0
    quality_target: str  # "speed", "balanced", "accuracy"
    user_preferences: Dict[str, Any] = field(default_factory=dict)
    resource_constraints: Dict[str, Any] = field(default_factory=dict)

class EnhancedNLPModelManager(BaseModelManager):
    """Enhanced model manager extending the existing Whisper ModelManager"""
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize enhanced NLP model manager"""
        super().__init__(cache_dir)
        
        # Initialize NLP foundation
        self.nlp_foundation = UnifiedNLPFoundation()
        
        # Model configurations
        self.model_configs = self._initialize_model_configs()
        
        # Processing statistics specific to NLP
        self.nlp_stats = {
            'model_selections': defaultdict(int),
            'fallback_usage': defaultdict(int),
            'processing_times_by_model': defaultdict(list),
            'accuracy_scores': defaultdict(list),
            'content_type_preferences': defaultdict(lambda: defaultdict(int))
        }
        
        # Model selection cache
        self.selection_cache = {}
        self.cache_ttl = 3600  # 1 hour
        
        logger.info("Enhanced NLP Model Manager initialized successfully")
    
    def _initialize_model_configs(self) -> Dict[NLPModelType, ModelConfig]:
        """Initialize model configurations"""
        configs = {}
        
        # spaCy models
        configs[NLPModelType.SPACY_SMALL] = ModelConfig(
            model_type=NLPModelType.SPACY_SMALL,
            model_name="en_core_web_sm",
            capabilities=[
                NLPCapability.BASIC_NER,
                NLPCapability.DEPENDENCY_PARSING,
                NLPCapability.SENTIMENT_ANALYSIS
            ],
            resource_requirements={
                'memory_mb': 50,
                'cpu_cores': 1,
                'gpu_required': False
            }
        )
        
        configs[NLPModelType.SPACY_MEDIUM] = ModelConfig(
            model_type=NLPModelType.SPACY_MEDIUM,
            model_name="en_core_web_md",
            capabilities=[
                NLPCapability.ADVANCED_NER,
                NLPCapability.DEPENDENCY_PARSING,
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.ENTITY_LINKING
            ],
            resource_requirements={
                'memory_mb': 50,
                'cpu_cores': 1,
                'gpu_required': False
            }
        )
        
        configs[NLPModelType.SPACY_LARGE] = ModelConfig(
            model_type=NLPModelType.SPACY_LARGE,
            model_name="en_core_web_lg",
            capabilities=[
                NLPCapability.ADVANCED_NER,
                NLPCapability.DEPENDENCY_PARSING,
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.ENTITY_LINKING,
                NLPCapability.TOPIC_MODELING
            ],
            resource_requirements={
                'memory_mb': 750,
                'cpu_cores': 2,
                'gpu_required': False
            }
        )
        
        configs[NLPModelType.SPACY_TRANSFORMER] = ModelConfig(
            model_type=NLPModelType.SPACY_TRANSFORMER,
            model_name="en_core_web_trf",
            capabilities=[
                NLPCapability.ADVANCED_NER,
                NLPCapability.DEPENDENCY_PARSING,
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.ENTITY_LINKING,
                NLPCapability.TOPIC_MODELING,
                NLPCapability.COREFERENCE_RESOLUTION
            ],
            resource_requirements={
                'memory_mb': 560,
                'cpu_cores': 4,
                'gpu_required': True,
                'gpu_memory_mb': 2000
            }
        )
        
        # Transformer models
        configs[NLPModelType.BERT_BASE] = ModelConfig(
            model_type=NLPModelType.BERT_BASE,
            model_name="bert-base-uncased",
            capabilities=[
                NLPCapability.ADVANCED_NER,
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.EMOTION_DETECTION,
                NLPCapability.INTENT_CLASSIFICATION,
                NLPCapability.TOPIC_MODELING
            ],
            resource_requirements={
                'memory_mb': 440,
                'cpu_cores': 4,
                'gpu_required': True,
                'gpu_memory_mb': 1500
            }
        )
        
        configs[NLPModelType.ROBERTA_BASE] = ModelConfig(
            model_type=NLPModelType.ROBERTA_BASE,
            model_name="roberta-base",
            capabilities=[
                NLPCapability.ADVANCED_NER,
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.EMOTION_DETECTION,
                NLPCapability.INTENT_CLASSIFICATION,
                NLPCapability.TOPIC_MODELING,
                NLPCapability.SUMMARIZATION
            ],
            resource_requirements={
                'memory_mb': 500,
                'cpu_cores': 4,
                'gpu_required': True,
                'gpu_memory_mb': 1800
            }
        )
        
        configs[NLPModelType.DISTILBERT] = ModelConfig(
            model_type=NLPModelType.DISTILBERT,
            model_name="distilbert-base-uncased",
            capabilities=[
                NLPCapability.ADVANCED_NER,
                NLPCapability.SENTIMENT_ANALYSIS,
                NLPCapability.EMOTION_DETECTION,
                NLPCapability.INTENT_CLASSIFICATION
            ],
            resource_requirements={
                'memory_mb': 250,
                'cpu_cores': 2,
                'gpu_required': False
            }
        )
        
        return configs
    
    def select_optimal_nlp_model(self, context: ProcessingContext, 
                                requested_capabilities: List[NLPCapability]) -> NLPModelType:
        """Select optimal NLP model based on context and requirements"""
        
        # Check cache first
        cache_key = self._generate_cache_key(context, requested_capabilities)
        if cache_key in self.selection_cache:
            cached_result = self.selection_cache[cache_key]
            if time.time() - cached_result['timestamp'] < self.cache_ttl:
                logger.info(f"Using cached model selection: {cached_result['model'].value}")
                return cached_result['model']
        
        # Get available models that support required capabilities
        candidate_models = []
        for model_type, config in self.model_configs.items():
            if all(cap in config.capabilities for cap in requested_capabilities):
                candidate_models.append((model_type, config))
        
        if not candidate_models:
            logger.warning("No models support all requested capabilities, using fallback")
            return NLPModelType.SPACY_SMALL
        
        # Score models based on context
        scored_models = []
        for model_type, config in candidate_models:
            score = self._calculate_model_score(model_type, config, context)
            scored_models.append((score, model_type, config))
        
        # Sort by score (higher is better)
        scored_models.sort(reverse=True)
        
        # Select best model that meets resource constraints
        for score, model_type, config in scored_models:
            if self._check_resource_constraints(config, context.resource_constraints):
                # Cache the selection
                self.selection_cache[cache_key] = {
                    'model': model_type,
                    'timestamp': time.time(),
                    'score': score
                }
                
                # Update statistics
                self.nlp_stats['model_selections'][model_type.value] += 1
                self.nlp_stats['content_type_preferences'][context.content_type][model_type.value] += 1
                
                logger.info(f"Selected optimal model: {model_type.value} (score: {score:.2f})")
                return model_type
        
        # If no model meets constraints, use fallback
        logger.warning("No models meet resource constraints, using fallback")
        fallback_model = NLPModelType.SPACY_SMALL
        self.nlp_stats['fallback_usage'][fallback_model.value] += 1
        return fallback_model
    
    def _calculate_model_score(self, model_type: NLPModelType, config: ModelConfig, 
                              context: ProcessingContext) -> float:
        """Calculate model score based on context requirements"""
        score = 0.0
        
        # Quality target scoring
        if context.quality_target == "accuracy":
            accuracy_scores = {
                NLPModelType.SPACY_SMALL: 0.6,
                NLPModelType.SPACY_MEDIUM: 0.7,
                NLPModelType.SPACY_LARGE: 0.8,
                NLPModelType.SPACY_TRANSFORMER: 0.95,
                NLPModelType.BERT_BASE: 0.9,
                NLPModelType.ROBERTA_BASE: 0.92,
                NLPModelType.DISTILBERT: 0.85
            }
            score += accuracy_scores.get(model_type, 0.5) * 40
            
        elif context.quality_target == "speed":
            speed_scores = {
                NLPModelType.SPACY_SMALL: 0.95,
                NLPModelType.SPACY_MEDIUM: 0.85,
                NLPModelType.SPACY_LARGE: 0.7,
                NLPModelType.SPACY_TRANSFORMER: 0.3,
                NLPModelType.BERT_BASE: 0.25,
                NLPModelType.ROBERTA_BASE: 0.2,
                NLPModelType.DISTILBERT: 0.6
            }
            score += speed_scores.get(model_type, 0.5) * 40
            
        else:  # balanced
            # Balanced scoring considers both accuracy and speed
            accuracy_scores = {
                NLPModelType.SPACY_SMALL: 0.6,
                NLPModelType.SPACY_MEDIUM: 0.7,
                NLPModelType.SPACY_LARGE: 0.8,
                NLPModelType.SPACY_TRANSFORMER: 0.95,
                NLPModelType.BERT_BASE: 0.9,
                NLPModelType.ROBERTA_BASE: 0.92,
                NLPModelType.DISTILBERT: 0.85
            }
            speed_scores = {
                NLPModelType.SPACY_SMALL: 0.95,
                NLPModelType.SPACY_MEDIUM: 0.85,
                NLPModelType.SPACY_LARGE: 0.7,
                NLPModelType.SPACY_TRANSFORMER: 0.3,
                NLPModelType.BERT_BASE: 0.25,
                NLPModelType.ROBERTA_BASE: 0.2,
                NLPModelType.DISTILBERT: 0.6
            }
            accuracy = accuracy_scores.get(model_type, 0.5)
            speed = speed_scores.get(model_type, 0.5)
            score += (accuracy * 0.6 + speed * 0.4) * 40
        
        # Content complexity scoring
        if context.complexity_estimate > 0.7:  # High complexity
            # Prefer more powerful models
            complexity_bonus = {
                NLPModelType.SPACY_TRANSFORMER: 20,
                NLPModelType.ROBERTA_BASE: 18,
                NLPModelType.BERT_BASE: 15,
                NLPModelType.SPACY_LARGE: 10,
                NLPModelType.DISTILBERT: 8,
                NLPModelType.SPACY_MEDIUM: 5,
                NLPModelType.SPACY_SMALL: 0
            }
            score += complexity_bonus.get(model_type, 0)
        
        # Content length scoring
        if context.content_length > 10000:  # Long content
            # Consider processing efficiency
            length_scores = {
                NLPModelType.SPACY_SMALL: 15,
                NLPModelType.SPACY_MEDIUM: 12,
                NLPModelType.DISTILBERT: 10,
                NLPModelType.SPACY_LARGE: 8,
                NLPModelType.BERT_BASE: 5,
                NLPModelType.ROBERTA_BASE: 3,
                NLPModelType.SPACY_TRANSFORMER: 0
            }
            score += length_scores.get(model_type, 0)
        
        # Content type preferences
        content_type_preferences = {
            "meeting": {
                NLPModelType.SPACY_LARGE: 10,
                NLPModelType.SPACY_TRANSFORMER: 15,
                NLPModelType.BERT_BASE: 12
            },
            "document": {
                NLPModelType.SPACY_TRANSFORMER: 15,
                NLPModelType.ROBERTA_BASE: 12,
                NLPModelType.SPACY_LARGE: 10
            },
            "conversation": {
                NLPModelType.SPACY_MEDIUM: 10,
                NLPModelType.DISTILBERT: 8,
                NLPModelType.SPACY_SMALL: 5
            }
        }
        
        type_bonus = content_type_preferences.get(context.content_type, {}).get(model_type, 0)
        score += type_bonus
        
        # Historical performance bonus
        if model_type.value in self.nlp_stats['accuracy_scores']:
            avg_accuracy = np.mean(self.nlp_stats['accuracy_scores'][model_type.value])
            score += avg_accuracy * 10
        
        return score
    
    def _check_resource_constraints(self, config: ModelConfig, 
                                  constraints: Dict[str, Any]) -> bool:
        """Check if model meets resource constraints"""
        if not constraints:
            return True
        
        # Check memory constraint
        if 'max_memory_mb' in constraints:
            if config.resource_requirements['memory_mb'] > constraints['max_memory_mb']:
                return False
        
        # Check CPU constraint
        if 'max_cpu_cores' in constraints:
            if config.resource_requirements['cpu_cores'] > constraints['max_cpu_cores']:
                return False
        
        # Check GPU requirement
        if 'gpu_available' in constraints:
            if config.resource_requirements.get('gpu_required', False) and not constraints['gpu_available']:
                return False
        
        # Check GPU memory constraint
        if 'max_gpu_memory_mb' in constraints and config.resource_requirements.get('gpu_required', False):
            gpu_memory_required = config.resource_requirements.get('gpu_memory_mb', 0)
            if gpu_memory_required > constraints['max_gpu_memory_mb']:
                return False
        
        return True
    
    def _generate_cache_key(self, context: ProcessingContext, 
                           capabilities: List[NLPCapability]) -> str:
        """Generate cache key for model selection"""
        key_data = {
            'content_type': context.content_type,
            'content_length_bucket': self._get_length_bucket(context.content_length),
            'complexity_bucket': self._get_complexity_bucket(context.complexity_estimate),
            'quality_target': context.quality_target,
            'capabilities': sorted([cap.value for cap in capabilities]),
            'resource_constraints': sorted(context.resource_constraints.items()) if context.resource_constraints else []
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_length_bucket(self, length: int) -> str:
        """Get content length bucket for caching"""
        if length < 1000:
            return "short"
        elif length < 10000:
            return "medium"
        else:
            return "long"
    
    def _get_complexity_bucket(self, complexity: float) -> str:
        """Get complexity bucket for caching"""
        if complexity < 0.3:
            return "low"
        elif complexity < 0.7:
            return "medium"
        else:
            return "high"
    
    async def process_with_optimal_model(self, text: str, context: ProcessingContext,
                                       requested_capabilities: List[NLPCapability]) -> NLPResult:
        """Process text using optimal model selection"""
        start_time = time.time()
        
        # Select optimal model
        optimal_model = self.select_optimal_nlp_model(context, requested_capabilities)
        
        try:
            # Process using NLP foundation with selected model preference
            result = await self.nlp_foundation.process_text(
                text, 
                requested_capabilities,
                context={'preferred_model': optimal_model.value}
            )
            
            processing_time = time.time() - start_time
            
            # Update statistics
            self.nlp_stats['processing_times_by_model'][optimal_model.value].append(processing_time)
            
            # Estimate accuracy based on model and result confidence
            estimated_accuracy = self._estimate_accuracy(optimal_model, result)
            self.nlp_stats['accuracy_scores'][optimal_model.value].append(estimated_accuracy)
            
            logger.info(f"Processed text with {optimal_model.value} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            # Try fallback models
            config = self.model_configs[optimal_model]
            for fallback_model in config.fallback_models:
                try:
                    logger.warning(f"Trying fallback model: {fallback_model.value}")
                    result = await self.nlp_foundation.process_text(
                        text,
                        requested_capabilities,
                        context={'preferred_model': fallback_model.value}
                    )
                    
                    self.nlp_stats['fallback_usage'][fallback_model.value] += 1
                    return result
                    
                except Exception as fallback_error:
                    logger.error(f"Fallback model {fallback_model.value} failed: {fallback_error}")
                    continue
            
            # If all models fail, raise the original error
            logger.error(f"All models failed for processing: {e}")
            raise
    
    def _estimate_accuracy(self, model_type: NLPModelType, result: NLPResult) -> float:
        """Estimate processing accuracy based on model and result"""
        base_accuracy = {
            NLPModelType.SPACY_SMALL: 0.6,
            NLPModelType.SPACY_MEDIUM: 0.7,
            NLPModelType.SPACY_LARGE: 0.8,
            NLPModelType.SPACY_TRANSFORMER: 0.95,
            NLPModelType.BERT_BASE: 0.9,
            NLPModelType.ROBERTA_BASE: 0.92,
            NLPModelType.DISTILBERT: 0.85
        }.get(model_type, 0.7)
        
        # Adjust based on confidence scores in result
        if result.confidence_scores:
            avg_confidence = np.mean(list(result.confidence_scores.values()))
            # Blend base accuracy with actual confidence
            return (base_accuracy * 0.7) + (avg_confidence * 0.3)
        
        return base_accuracy
    
    def get_nlp_statistics(self) -> Dict[str, Any]:
        """Get comprehensive NLP processing statistics"""
        stats = {
            'model_selections': dict(self.nlp_stats['model_selections']),
            'fallback_usage': dict(self.nlp_stats['fallback_usage']),
            'content_type_preferences': {
                content_type: dict(prefs) 
                for content_type, prefs in self.nlp_stats['content_type_preferences'].items()
            },
            'average_processing_times': {},
            'average_accuracy_scores': {},
            'model_configurations': {
                model_type.value: {
                    'size': model_type.model_size,
                    'accuracy_level': model_type.accuracy_level,
                    'processing_speed': model_type.processing_speed,
                    'use_cases': model_type.use_cases
                }
                for model_type in NLPModelType
            }
        }
        
        # Calculate averages
        for model, times in self.nlp_stats['processing_times_by_model'].items():
            if times:
                stats['average_processing_times'][model] = np.mean(times)
        
        for model, scores in self.nlp_stats['accuracy_scores'].items():
            if scores:
                stats['average_accuracy_scores'][model] = np.mean(scores)
        
        return stats
    
    def clear_nlp_caches(self) -> None:
        """Clear NLP-specific caches"""
        self.selection_cache.clear()
        logger.info("NLP model selection cache cleared")

# Utility functions
def create_processing_context(content_type: str, text: str, 
                            quality_target: str = "balanced",
                            user_preferences: Optional[Dict[str, Any]] = None,
                            resource_constraints: Optional[Dict[str, Any]] = None) -> ProcessingContext:
    """Create processing context from text and parameters"""
    
    # Estimate complexity based on text characteristics
    complexity = estimate_text_complexity(text)
    
    return ProcessingContext(
        content_type=content_type,
        content_length=len(text),
        complexity_estimate=complexity,
        quality_target=quality_target,
        user_preferences=user_preferences or {},
        resource_constraints=resource_constraints or {}
    )

def estimate_text_complexity(text: str) -> float:
    """Estimate text complexity (0.0 to 1.0)"""
    # Simple heuristic-based complexity estimation
    factors = []
    
    # Sentence length variance
    sentences = text.split('.')
    if len(sentences) > 1:
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if sentence_lengths:
            length_variance = np.var(sentence_lengths) / np.mean(sentence_lengths)
            factors.append(min(1.0, length_variance / 10))
    
    # Vocabulary diversity
    words = text.lower().split()
    if words:
        unique_words = len(set(words))
        vocab_diversity = unique_words / len(words)
        factors.append(vocab_diversity)
    
    # Average word length
    if words:
        avg_word_length = np.mean([len(word) for word in words])
        factors.append(min(1.0, (avg_word_length - 4) / 6))  # Normalize around 4-char average
    
    # Technical terms (simple heuristic)
    technical_indicators = ['algorithm', 'implementation', 'configuration', 'optimization', 
                          'architecture', 'methodology', 'analysis', 'evaluation']
    technical_count = sum(1 for word in words if word in technical_indicators)
    if words:
        technical_ratio = technical_count / len(words)
        factors.append(min(1.0, technical_ratio * 20))
    
    # Return average of factors, defaulting to medium complexity
    return np.mean(factors) if factors else 0.5

# Example usage
async def example_usage():
    """Example usage of Enhanced NLP Model Manager"""
    try:
        # Initialize manager
        manager = EnhancedNLPModelManager()
        
        # Example text
        sample_text = """
        In today's meeting, we discussed the quarterly revenue projections and decided to 
        implement a new customer acquisition strategy. John will lead the marketing initiative, 
        and Sarah will handle the technical implementation. The deadline is set for next month.
        """
        
        # Create processing context
        context = create_processing_context(
            content_type="meeting",
            text=sample_text,
            quality_target="balanced"
        )
        
        # Request capabilities
        capabilities = [
            NLPCapability.ADVANCED_NER,
            NLPCapability.SENTIMENT_ANALYSIS,
            NLPCapability.INTENT_CLASSIFICATION
        ]
        
        # Process with optimal model selection
        result = await manager.process_with_optimal_model(sample_text, context, capabilities)
        
        print(f"Processing completed with capabilities: {result.capabilities_used}")
        print(f"Entities found: {len(result.entities)}")
        print(f"Processing time: {result.processing_time:.2f}s")
        
        # Get statistics
        stats = manager.get_nlp_statistics()
        print(f"Model selection statistics: {stats['model_selections']}")
        
        print("Enhanced NLP Model Manager example completed successfully!")
        
    except Exception as e:
        print(f"Example failed: {str(e)}")

if __name__ == "__main__":
    # Import numpy for statistics
    import numpy as np
    from collections import defaultdict
    
    # Run example
    asyncio.run(example_usage())