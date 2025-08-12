#!/usr/bin/env python3
"""
Unit Tests for Enhanced NLP Model Manager
Tests model selection logic, caching, and fallback mechanisms
"""

import pytest
import asyncio
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import numpy as np

from enhanced_nlp_model_manager import (
    EnhancedNLPModelManager,
    NLPModelType,
    ModelConfig,
    ProcessingContext,
    create_processing_context,
    estimate_text_complexity
)
from unified_nlp_foundation import NLPCapability, NLPResult

class TestNLPModelType:
    """Test NLP model type enumeration"""
    
    def test_model_properties(self):
        """Test model type properties"""
        model = NLPModelType.SPACY_LARGE
        
        assert "Large" in model.model_size
        assert model.accuracy_level in ["Basic", "Good", "High", "Highest", "Very High"]
        assert model.processing_speed in ["Very Fast", "Fast", "Medium", "Slow"]
        assert isinstance(model.use_cases, list)
        assert len(model.use_cases) > 0
    
    def test_all_models_have_properties(self):
        """Test that all model types have required properties"""
        for model_type in NLPModelType:
            assert model_type.model_size
            assert model_type.accuracy_level
            assert model_type.processing_speed
            assert model_type.use_cases

class TestModelConfig:
    """Test model configuration"""
    
    def test_model_config_creation(self):
        """Test model configuration creation"""
        config = ModelConfig(
            model_type=NLPModelType.SPACY_MEDIUM,
            model_name="en_core_web_md",
            capabilities=[NLPCapability.BASIC_NER, NLPCapability.SENTIMENT_ANALYSIS],
            resource_requirements={'memory_mb': 50, 'cpu_cores': 1}
        )
        
        assert config.model_type == NLPModelType.SPACY_MEDIUM
        assert config.model_name == "en_core_web_md"
        assert len(config.capabilities) == 2
        assert config.resource_requirements['memory_mb'] == 50
    
    def test_fallback_models_auto_generation(self):
        """Test automatic fallback model generation"""
        config = ModelConfig(
            model_type=NLPModelType.SPACY_TRANSFORMER,
            model_name="en_core_web_trf",
            capabilities=[NLPCapability.ADVANCED_NER],
            resource_requirements={'memory_mb': 560}
        )
        
        # Should have fallback chain
        assert len(config.fallback_models) > 0
        assert NLPModelType.SPACY_LARGE in config.fallback_models
        assert NLPModelType.SPACY_SMALL in config.fallback_models

class TestProcessingContext:
    """Test processing context"""
    
    def test_processing_context_creation(self):
        """Test processing context creation"""
        context = ProcessingContext(
            content_type="meeting",
            content_length=1000,
            complexity_estimate=0.7,
            quality_target="accuracy"
        )
        
        assert context.content_type == "meeting"
        assert context.content_length == 1000
        assert context.complexity_estimate == 0.7
        assert context.quality_target == "accuracy"
    
    def test_create_processing_context_utility(self):
        """Test utility function for creating processing context"""
        text = "This is a sample meeting transcript with technical terms like algorithm and implementation."
        
        context = create_processing_context(
            content_type="meeting",
            text=text,
            quality_target="balanced"
        )
        
        assert context.content_type == "meeting"
        assert context.content_length == len(text)
        assert 0.0 <= context.complexity_estimate <= 1.0
        assert context.quality_target == "balanced"

class TestTextComplexityEstimation:
    """Test text complexity estimation"""
    
    def test_simple_text_complexity(self):
        """Test complexity estimation for simple text"""
        simple_text = "This is a simple sentence. It has basic words."
        complexity = estimate_text_complexity(simple_text)
        
        assert 0.0 <= complexity <= 1.0
        assert complexity < 0.5  # Should be relatively low complexity
    
    def test_complex_text_complexity(self):
        """Test complexity estimation for complex text"""
        complex_text = """
        The implementation of advanced machine learning algorithms requires careful consideration 
        of architectural patterns and optimization methodologies. The evaluation framework must 
        incorporate comprehensive analysis techniques to ensure robust performance metrics.
        """
        complexity = estimate_text_complexity(complex_text)
        
        assert 0.0 <= complexity <= 1.0
        assert complexity > 0.5  # Should be higher complexity due to technical terms
    
    def test_empty_text_complexity(self):
        """Test complexity estimation for empty text"""
        complexity = estimate_text_complexity("")
        assert complexity == 0.5  # Default to medium complexity

class TestEnhancedNLPModelManager:
    """Test Enhanced NLP Model Manager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock the UnifiedNLPFoundation to avoid dependency issues
        with patch('enhanced_nlp_model_manager.UnifiedNLPFoundation') as mock_nlp:
            mock_nlp.return_value = Mock()
            self.manager = EnhancedNLPModelManager(cache_dir=self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        assert os.path.exists(self.manager.cache_dir)
        assert hasattr(self.manager, 'model_configs')
        assert hasattr(self.manager, 'nlp_stats')
        assert hasattr(self.manager, 'selection_cache')
    
    def test_model_configs_initialization(self):
        """Test model configurations are properly initialized"""
        configs = self.manager.model_configs
        
        # Check that all model types have configurations
        assert len(configs) == len(NLPModelType)
        
        for model_type in NLPModelType:
            assert model_type in configs
            config = configs[model_type]
            assert isinstance(config, ModelConfig)
            assert config.model_type == model_type
            assert len(config.capabilities) > 0
            assert 'memory_mb' in config.resource_requirements
    
    def test_model_selection_speed_target(self):
        """Test model selection with speed target"""
        context = ProcessingContext(
            content_type="conversation",
            content_length=500,
            complexity_estimate=0.3,
            quality_target="speed"
        )
        
        capabilities = [NLPCapability.BASIC_NER, NLPCapability.SENTIMENT_ANALYSIS]
        selected_model = self.manager.select_optimal_nlp_model(context, capabilities)
        
        # Should prefer faster models
        assert selected_model in [NLPModelType.SPACY_SMALL, NLPModelType.SPACY_MEDIUM]
    
    def test_model_selection_accuracy_target(self):
        """Test model selection with accuracy target"""
        context = ProcessingContext(
            content_type="document",
            content_length=2000,
            complexity_estimate=0.8,
            quality_target="accuracy"
        )
        
        capabilities = [NLPCapability.ADVANCED_NER, NLPCapability.ENTITY_LINKING]
        selected_model = self.manager.select_optimal_nlp_model(context, capabilities)
        
        # Should prefer more accurate models
        assert selected_model in [
            NLPModelType.SPACY_TRANSFORMER, 
            NLPModelType.ROBERTA_BASE, 
            NLPModelType.BERT_BASE,
            NLPModelType.SPACY_LARGE
        ]
    
    def test_model_selection_balanced_target(self):
        """Test model selection with balanced target"""
        context = ProcessingContext(
            content_type="meeting",
            content_length=1500,
            complexity_estimate=0.5,
            quality_target="balanced"
        )
        
        capabilities = [NLPCapability.ADVANCED_NER, NLPCapability.SENTIMENT_ANALYSIS]
        selected_model = self.manager.select_optimal_nlp_model(context, capabilities)
        
        # Should select a balanced model
        assert selected_model in [
            NLPModelType.SPACY_MEDIUM,
            NLPModelType.SPACY_LARGE,
            NLPModelType.DISTILBERT
        ]
    
    def test_model_selection_with_resource_constraints(self):
        """Test model selection with resource constraints"""
        context = ProcessingContext(
            content_type="document",
            content_length=1000,
            complexity_estimate=0.6,
            quality_target="accuracy",
            resource_constraints={
                'max_memory_mb': 100,
                'gpu_available': False
            }
        )
        
        capabilities = [NLPCapability.ADVANCED_NER]
        selected_model = self.manager.select_optimal_nlp_model(context, capabilities)
        
        # Should respect resource constraints
        config = self.manager.model_configs[selected_model]
        assert config.resource_requirements['memory_mb'] <= 100
        assert not config.resource_requirements.get('gpu_required', False)
    
    def test_model_selection_caching(self):
        """Test model selection caching"""
        context = ProcessingContext(
            content_type="meeting",
            content_length=1000,
            complexity_estimate=0.5,
            quality_target="balanced"
        )
        
        capabilities = [NLPCapability.BASIC_NER]
        
        # First selection
        model1 = self.manager.select_optimal_nlp_model(context, capabilities)
        
        # Second selection should use cache
        model2 = self.manager.select_optimal_nlp_model(context, capabilities)
        
        assert model1 == model2
        assert len(self.manager.selection_cache) > 0
    
    def test_model_selection_no_suitable_models(self):
        """Test model selection when no models support required capabilities"""
        context = ProcessingContext(
            content_type="test",
            content_length=100,
            complexity_estimate=0.5,
            quality_target="balanced"
        )
        
        # Request capabilities that no model supports (hypothetical)
        capabilities = []  # Empty capabilities should work with any model
        selected_model = self.manager.select_optimal_nlp_model(context, capabilities)
        
        # Should return a valid model
        assert isinstance(selected_model, NLPModelType)
    
    @pytest.mark.asyncio
    async def test_process_with_optimal_model_success(self):
        """Test successful processing with optimal model"""
        # Mock the NLP foundation
        mock_result = NLPResult(
            text="test text",
            capabilities_used=["basic_ner"],
            entities=[],
            sentiment={},
            emotions={},
            topics=[],
            summary=None,
            questions=[],
            intent=None,
            confidence_scores={'ner': 0.8},
            processing_time=0.1,
            model_info={'ner': 'spacy_small'}
        )
        
        self.manager.nlp_foundation.process_text = AsyncMock(return_value=mock_result)
        
        context = ProcessingContext(
            content_type="test",
            content_length=100,
            complexity_estimate=0.3,
            quality_target="speed"
        )
        
        capabilities = [NLPCapability.BASIC_NER]
        result = await self.manager.process_with_optimal_model("test text", context, capabilities)
        
        assert result == mock_result
        assert len(self.manager.nlp_stats['processing_times_by_model']) > 0
    
    @pytest.mark.asyncio
    async def test_process_with_optimal_model_fallback(self):
        """Test processing with fallback when primary model fails"""
        # Mock the NLP foundation to fail first, then succeed
        mock_result = NLPResult(
            text="test text",
            capabilities_used=["basic_ner"],
            entities=[],
            sentiment={},
            emotions={},
            topics=[],
            summary=None,
            questions=[],
            intent=None,
            confidence_scores={'ner': 0.7},
            processing_time=0.2,
            model_info={'ner': 'spacy_small'}
        )
        
        # First call fails, second succeeds (simulating fallback)
        self.manager.nlp_foundation.process_text = AsyncMock(side_effect=[Exception("Model failed"), mock_result])
        
        context = ProcessingContext(
            content_type="test",
            content_length=100,
            complexity_estimate=0.3,
            quality_target="speed"
        )
        
        capabilities = [NLPCapability.BASIC_NER]
        result = await self.manager.process_with_optimal_model("test text", context, capabilities)
        
        assert result == mock_result
        # Should have recorded fallback usage
        assert sum(self.manager.nlp_stats['fallback_usage'].values()) > 0
    
    def test_resource_constraint_checking(self):
        """Test resource constraint checking"""
        config = ModelConfig(
            model_type=NLPModelType.SPACY_LARGE,
            model_name="en_core_web_lg",
            capabilities=[NLPCapability.ADVANCED_NER],
            resource_requirements={
                'memory_mb': 750,
                'cpu_cores': 2,
                'gpu_required': False
            }
        )
        
        # Should pass with sufficient resources
        constraints1 = {
            'max_memory_mb': 1000,
            'max_cpu_cores': 4,
            'gpu_available': True
        }
        assert self.manager._check_resource_constraints(config, constraints1)
        
        # Should fail with insufficient memory
        constraints2 = {
            'max_memory_mb': 500,
            'max_cpu_cores': 4
        }
        assert not self.manager._check_resource_constraints(config, constraints2)
        
        # Should fail with insufficient CPU cores
        constraints3 = {
            'max_memory_mb': 1000,
            'max_cpu_cores': 1
        }
        assert not self.manager._check_resource_constraints(config, constraints3)
    
    def test_statistics_collection(self):
        """Test statistics collection"""
        # Simulate some model selections
        context = ProcessingContext(
            content_type="test",
            content_length=100,
            complexity_estimate=0.5,
            quality_target="balanced"
        )
        
        capabilities = [NLPCapability.BASIC_NER]
        
        # Make several selections
        for _ in range(3):
            self.manager.select_optimal_nlp_model(context, capabilities)
        
        stats = self.manager.get_nlp_statistics()
        
        assert 'model_selections' in stats
        assert 'fallback_usage' in stats
        assert 'content_type_preferences' in stats
        assert 'model_configurations' in stats
        
        # Should have recorded selections
        assert sum(stats['model_selections'].values()) > 0
    
    def test_cache_clearing(self):
        """Test cache clearing functionality"""
        # Add something to cache
        context = ProcessingContext(
            content_type="test",
            content_length=100,
            complexity_estimate=0.5,
            quality_target="balanced"
        )
        
        capabilities = [NLPCapability.BASIC_NER]
        self.manager.select_optimal_nlp_model(context, capabilities)
        
        assert len(self.manager.selection_cache) > 0
        
        # Clear cache
        self.manager.clear_nlp_caches()
        
        assert len(self.manager.selection_cache) == 0

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_processing_context_with_defaults(self):
        """Test creating processing context with default values"""
        text = "Sample text for testing"
        context = create_processing_context("meeting", text)
        
        assert context.content_type == "meeting"
        assert context.content_length == len(text)
        assert context.quality_target == "balanced"
        assert isinstance(context.user_preferences, dict)
        assert isinstance(context.resource_constraints, dict)
    
    def test_create_processing_context_with_custom_values(self):
        """Test creating processing context with custom values"""
        text = "Sample text"
        user_prefs = {"model_preference": "accuracy"}
        constraints = {"max_memory_mb": 500}
        
        context = create_processing_context(
            "document", 
            text, 
            "accuracy",
            user_prefs,
            constraints
        )
        
        assert context.content_type == "document"
        assert context.quality_target == "accuracy"
        assert context.user_preferences == user_prefs
        assert context.resource_constraints == constraints

# Integration test
@pytest.mark.asyncio
async def test_end_to_end_processing():
    """Test end-to-end processing workflow"""
    with patch('enhanced_nlp_model_manager.UnifiedNLPFoundation') as mock_nlp_class:
        # Mock the NLP foundation
        mock_nlp = Mock()
        mock_result = NLPResult(
            text="Meeting transcript",
            capabilities_used=["advanced_ner", "sentiment_analysis"],
            entities=[
                {"text": "John", "label": "PERSON", "start": 0, "end": 4, "confidence": 0.9}
            ],
            sentiment={"polarity": 0.2, "subjectivity": 0.5},
            emotions={"neutral": 0.7, "joy": 0.3},
            topics=[],
            summary=None,
            questions=[],
            intent="meeting_discussion",
            confidence_scores={"ner": 0.9, "sentiment": 0.8},
            processing_time=0.15,
            model_info={"ner": "spacy_large", "sentiment": "transformer"}
        )
        
        mock_nlp.process_text = AsyncMock(return_value=mock_result)
        mock_nlp_class.return_value = mock_nlp
        
        # Initialize manager
        manager = EnhancedNLPModelManager()
        
        # Process text
        text = "In today's meeting, John discussed the quarterly results and expressed optimism about future growth."
        context = create_processing_context("meeting", text, "balanced")
        capabilities = [NLPCapability.ADVANCED_NER, NLPCapability.SENTIMENT_ANALYSIS]
        
        result = await manager.process_with_optimal_model(text, context, capabilities)
        
        # Verify result
        assert result.text == "Meeting transcript"
        assert len(result.entities) == 1
        assert result.entities[0]["text"] == "John"
        assert result.sentiment["polarity"] == 0.2
        assert result.intent == "meeting_discussion"
        
        # Verify statistics were updated
        stats = manager.get_nlp_statistics()
        assert sum(stats['model_selections'].values()) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])