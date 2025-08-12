#!/usr/bin/env python3
"""
Unit Tests for NLP Model Configurations
Tests configuration management, model selection, and resource constraint handling
"""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, patch

from nlp_model_configurations import (
    ModelSize,
    ModelType,
    ProcessingMode,
    ResourceRequirements,
    PerformanceMetrics,
    ModelCapabilities,
    ModelConfiguration,
    ModelConfigurationManager
)

class TestResourceRequirements:
    """Test resource requirements functionality"""
    
    def test_resource_requirements_creation(self):
        """Test creating resource requirements"""
        req = ResourceRequirements(
            memory_mb=500,
            cpu_cores=2,
            gpu_required=True,
            gpu_memory_mb=1000
        )
        
        assert req.memory_mb == 500
        assert req.cpu_cores == 2
        assert req.gpu_required is True
        assert req.gpu_memory_mb == 1000
    
    def test_meets_constraints_success(self):
        """Test constraint checking - success case"""
        req = ResourceRequirements(
            memory_mb=500,
            cpu_cores=2,
            gpu_required=True,
            gpu_memory_mb=1000
        )
        
        available = {
            'max_memory_mb': 1000,
            'max_cpu_cores': 4,
            'gpu_available': True,
            'max_gpu_memory_mb': 2000
        }
        
        assert req.meets_constraints(available) is True
    
    def test_meets_constraints_failure(self):
        """Test constraint checking - failure cases"""
        req = ResourceRequirements(
            memory_mb=500,
            cpu_cores=2,
            gpu_required=True,
            gpu_memory_mb=1000
        )
        
        # Insufficient memory
        available1 = {
            'max_memory_mb': 300,
            'max_cpu_cores': 4,
            'gpu_available': True,
            'max_gpu_memory_mb': 2000
        }
        assert req.meets_constraints(available1) is False
        
        # No GPU available
        available2 = {
            'max_memory_mb': 1000,
            'max_cpu_cores': 4,
            'gpu_available': False
        }
        assert req.meets_constraints(available2) is False
        
        # Insufficient CPU cores
        available3 = {
            'max_memory_mb': 1000,
            'max_cpu_cores': 1,
            'gpu_available': True,
            'max_gpu_memory_mb': 2000
        }
        assert req.meets_constraints(available3) is False

class TestPerformanceMetrics:
    """Test performance metrics functionality"""
    
    def test_performance_metrics_creation(self):
        """Test creating performance metrics"""
        metrics = PerformanceMetrics(
            accuracy_score=0.85,
            speed_score=0.7,
            memory_efficiency=0.8,
            cpu_efficiency=0.75,
            ner_accuracy=0.9,
            processing_speed_wps=5000
        )
        
        assert metrics.accuracy_score == 0.85
        assert metrics.speed_score == 0.7
        assert metrics.ner_accuracy == 0.9
        assert metrics.processing_speed_wps == 5000
    
    def test_overall_score_default_weights(self):
        """Test overall score calculation with default weights"""
        metrics = PerformanceMetrics(
            accuracy_score=0.8,
            speed_score=0.6,
            memory_efficiency=0.7,
            cpu_efficiency=0.9
        )
        
        expected_score = (0.8 * 0.4) + (0.6 * 0.3) + (0.7 * 0.15) + (0.9 * 0.15)
        assert abs(metrics.overall_score() - expected_score) < 0.001
    
    def test_overall_score_custom_weights(self):
        """Test overall score calculation with custom weights"""
        metrics = PerformanceMetrics(
            accuracy_score=0.8,
            speed_score=0.6,
            memory_efficiency=0.7,
            cpu_efficiency=0.9
        )
        
        custom_weights = {
            'accuracy': 0.5,
            'speed': 0.5,
            'memory_efficiency': 0.0,
            'cpu_efficiency': 0.0
        }
        
        expected_score = (0.8 * 0.5) + (0.6 * 0.5)
        assert abs(metrics.overall_score(custom_weights) - expected_score) < 0.001

class TestModelCapabilities:
    """Test model capabilities functionality"""
    
    def test_capabilities_creation(self):
        """Test creating model capabilities"""
        caps = ModelCapabilities(
            named_entity_recognition=True,
            part_of_speech_tagging=True,
            dependency_parsing=False,
            word_vectors=True
        )
        
        assert caps.named_entity_recognition is True
        assert caps.part_of_speech_tagging is True
        assert caps.dependency_parsing is False
        assert caps.word_vectors is True
    
    def test_supports_capability(self):
        """Test capability checking"""
        caps = ModelCapabilities(
            named_entity_recognition=True,
            sentiment_analysis=False
        )
        
        assert caps.supports_capability('named_entity_recognition') is True
        assert caps.supports_capability('sentiment_analysis') is False
        assert caps.supports_capability('nonexistent_capability') is False
    
    def test_get_supported_capabilities(self):
        """Test getting list of supported capabilities"""
        caps = ModelCapabilities(
            named_entity_recognition=True,
            part_of_speech_tagging=True,
            dependency_parsing=False,
            tokenization=True
        )
        
        supported = caps.get_supported_capabilities()
        
        assert 'named_entity_recognition' in supported
        assert 'part_of_speech_tagging' in supported
        assert 'tokenization' in supported
        assert 'dependency_parsing' not in supported

class TestModelConfiguration:
    """Test model configuration functionality"""
    
    def test_configuration_creation(self):
        """Test creating model configuration"""
        config = ModelConfiguration(
            model_id="test_model",
            model_name="Test Model",
            model_type=ModelType.SPACY_STATISTICAL,
            model_size=ModelSize.MEDIUM,
            description="A test model"
        )
        
        assert config.model_id == "test_model"
        assert config.model_name == "Test Model"
        assert config.model_type == ModelType.SPACY_STATISTICAL
        assert config.model_size == ModelSize.MEDIUM
        assert config.description == "A test model"
    
    def test_to_dict_conversion(self):
        """Test converting configuration to dictionary"""
        config = ModelConfiguration(
            model_id="test_model",
            model_name="Test Model",
            model_type=ModelType.SPACY_STATISTICAL,
            model_size=ModelSize.MEDIUM,
            processing_modes=[ProcessingMode.BALANCED, ProcessingMode.SPEED_OPTIMIZED]
        )
        
        config_dict = config.to_dict()
        
        assert config_dict['model_id'] == "test_model"
        assert config_dict['model_type'] == "spacy_statistical"
        assert config_dict['model_size'] == "medium"
        assert "balanced" in config_dict['processing_modes']
        assert "speed_optimized" in config_dict['processing_modes']
    
    def test_from_dict_conversion(self):
        """Test creating configuration from dictionary"""
        config_dict = {
            'model_id': 'test_model',
            'model_name': 'Test Model',
            'model_type': 'spacy_statistical',
            'model_size': 'medium',
            'processing_modes': ['balanced', 'speed_optimized'],
            'resource_requirements': {
                'memory_mb': 100,
                'cpu_cores': 2,
                'gpu_required': False
            },
            'performance_metrics': {
                'accuracy_score': 0.8,
                'speed_score': 0.7,
                'memory_efficiency': 0.9,
                'cpu_efficiency': 0.8
            },
            'capabilities': {
                'named_entity_recognition': True,
                'part_of_speech_tagging': True
            }
        }
        
        config = ModelConfiguration.from_dict(config_dict)
        
        assert config.model_id == "test_model"
        assert config.model_type == ModelType.SPACY_STATISTICAL
        assert config.model_size == ModelSize.MEDIUM
        assert ProcessingMode.BALANCED in config.processing_modes
        assert config.resource_requirements.memory_mb == 100
        assert config.performance_metrics.accuracy_score == 0.8
        assert config.capabilities.named_entity_recognition is True

class TestModelConfigurationManager:
    """Test model configuration manager"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ModelConfigurationManager(config_dir=self.temp_dir)
    
    def test_manager_initialization(self):
        """Test manager initialization"""
        assert len(self.manager.configurations) > 0
        assert "en_core_web_sm" in self.manager.configurations
        assert "en_core_web_md" in self.manager.configurations
        assert "en_core_web_lg" in self.manager.configurations
        assert "en_core_web_trf" in self.manager.configurations
    
    def test_get_configuration(self):
        """Test getting specific configuration"""
        config = self.manager.get_configuration("en_core_web_sm")
        
        assert config is not None
        assert config.model_id == "en_core_web_sm"
        assert config.model_type == ModelType.SPACY_STATISTICAL
        assert config.model_size == ModelSize.SMALL
    
    def test_get_nonexistent_configuration(self):
        """Test getting non-existent configuration"""
        config = self.manager.get_configuration("nonexistent_model")
        assert config is None
    
    def test_list_configurations_no_filter(self):
        """Test listing all configurations"""
        configs = self.manager.list_configurations()
        assert len(configs) >= 4  # At least the default models
    
    def test_list_configurations_by_type(self):
        """Test listing configurations by type"""
        statistical_configs = self.manager.list_configurations(
            model_type=ModelType.SPACY_STATISTICAL
        )
        transformer_configs = self.manager.list_configurations(
            model_type=ModelType.SPACY_TRANSFORMER
        )
        
        assert len(statistical_configs) >= 3  # sm, md, lg
        assert len(transformer_configs) >= 1  # trf
        
        for config in statistical_configs:
            assert config.model_type == ModelType.SPACY_STATISTICAL
        
        for config in transformer_configs:
            assert config.model_type == ModelType.SPACY_TRANSFORMER
    
    def test_list_configurations_by_size(self):
        """Test listing configurations by size"""
        small_configs = self.manager.list_configurations(model_size=ModelSize.SMALL)
        large_configs = self.manager.list_configurations(model_size=ModelSize.LARGE)
        
        assert len(small_configs) >= 1
        assert len(large_configs) >= 1
        
        for config in small_configs:
            assert config.model_size == ModelSize.SMALL
    
    def test_list_configurations_by_processing_mode(self):
        """Test listing configurations by processing mode"""
        speed_configs = self.manager.list_configurations(
            processing_mode=ProcessingMode.SPEED_OPTIMIZED
        )
        accuracy_configs = self.manager.list_configurations(
            processing_mode=ProcessingMode.ACCURACY_OPTIMIZED
        )
        
        assert len(speed_configs) >= 1
        assert len(accuracy_configs) >= 1
        
        for config in speed_configs:
            assert ProcessingMode.SPEED_OPTIMIZED in config.processing_modes
    
    def test_select_optimal_model_basic(self):
        """Test basic optimal model selection"""
        requirements = {
            'capabilities': ['named_entity_recognition'],
            'processing_mode': 'speed_optimized'
        }
        
        optimal_config = self.manager.select_optimal_model(requirements)
        
        assert optimal_config is not None
        assert optimal_config.capabilities.named_entity_recognition is True
        assert ProcessingMode.SPEED_OPTIMIZED in optimal_config.processing_modes
    
    def test_select_optimal_model_with_resources(self):
        """Test optimal model selection with resource constraints"""
        requirements = {
            'capabilities': ['named_entity_recognition'],
            'processing_mode': 'balanced'
        }
        
        # Very limited resources
        available_resources = {
            'max_memory_mb': 100,
            'max_cpu_cores': 1,
            'gpu_available': False
        }
        
        optimal_config = self.manager.select_optimal_model(requirements, available_resources)
        
        assert optimal_config is not None
        assert optimal_config.resource_requirements.meets_constraints(available_resources)
    
    def test_select_optimal_model_no_suitable(self):
        """Test model selection when no suitable model exists"""
        requirements = {
            'capabilities': ['nonexistent_capability'],
            'processing_mode': 'balanced'
        }
        
        optimal_config = self.manager.select_optimal_model(requirements)
        assert optimal_config is None
    
    def test_add_configuration(self):
        """Test adding new configuration"""
        new_config = ModelConfiguration(
            model_id="custom_model",
            model_name="Custom Model",
            model_type=ModelType.LOCAL_CUSTOM,
            model_size=ModelSize.MEDIUM
        )
        
        initial_count = len(self.manager.configurations)
        self.manager.add_configuration(new_config)
        
        assert len(self.manager.configurations) == initial_count + 1
        assert "custom_model" in self.manager.configurations
        assert self.manager.get_configuration("custom_model") == new_config
    
    def test_get_fallback_chain(self):
        """Test getting fallback chain"""
        # Large model should have fallbacks to medium and small
        fallback_chain = self.manager.get_fallback_chain("en_core_web_lg")
        
        assert len(fallback_chain) > 0
        fallback_ids = [config.model_id for config in fallback_chain]
        assert "en_core_web_md" in fallback_ids or "en_core_web_sm" in fallback_ids
    
    def test_get_fallback_chain_nonexistent(self):
        """Test getting fallback chain for non-existent model"""
        fallback_chain = self.manager.get_fallback_chain("nonexistent_model")
        assert len(fallback_chain) == 0
    
    def test_save_and_load_configuration(self):
        """Test saving and loading configuration"""
        # Create a custom configuration
        custom_config = ModelConfiguration(
            model_id="save_test_model",
            model_name="Save Test Model",
            model_type=ModelType.LOCAL_CUSTOM,
            model_size=ModelSize.SMALL,
            description="Test configuration for save/load"
        )
        
        # Save configuration
        filename = "test_config.json"
        self.manager.save_configuration(custom_config, filename)
        
        # Verify file was created
        config_file = Path(self.temp_dir) / filename
        assert config_file.exists()
        
        # Create new manager and verify it loads the configuration
        new_manager = ModelConfigurationManager(config_dir=self.temp_dir)
        loaded_config = new_manager.get_configuration("save_test_model")
        
        assert loaded_config is not None
        assert loaded_config.model_id == custom_config.model_id
        assert loaded_config.model_name == custom_config.model_name
        assert loaded_config.description == custom_config.description
    
    def test_get_statistics(self):
        """Test getting configuration statistics"""
        stats = self.manager.get_statistics()
        
        assert 'total_configurations' in stats
        assert 'by_type' in stats
        assert 'by_size' in stats
        assert 'by_processing_mode' in stats
        assert 'average_performance' in stats
        
        assert stats['total_configurations'] > 0
        assert 'spacy_statistical' in stats['by_type']
        assert 'small' in stats['by_size']
        
        # Check average performance structure
        avg_perf = stats['average_performance']
        assert 'accuracy' in avg_perf
        assert 'speed' in avg_perf
        assert 'memory_efficiency' in avg_perf
        assert 'cpu_efficiency' in avg_perf
        
        # Values should be between 0 and 1
        for value in avg_perf.values():
            assert 0 <= value <= 1

class TestModelSelectionScoring:
    """Test model selection scoring logic"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.manager = ModelConfigurationManager()
    
    def test_scoring_accuracy_preference(self):
        """Test scoring with accuracy preference"""
        requirements = {
            'capabilities': ['named_entity_recognition'],
            'processing_mode': 'accuracy_optimized',
            'complexity_estimate': 0.8
        }
        
        preferences = {
            'performance_weights': {
                'accuracy': 0.8,
                'speed': 0.1,
                'memory_efficiency': 0.05,
                'cpu_efficiency': 0.05
            }
        }
        
        optimal_config = self.manager.select_optimal_model(requirements, preferences=preferences)
        
        # Should prefer high-accuracy models
        assert optimal_config is not None
        assert optimal_config.performance_metrics.accuracy_score >= 0.8
    
    def test_scoring_speed_preference(self):
        """Test scoring with speed preference"""
        requirements = {
            'capabilities': ['named_entity_recognition'],
            'processing_mode': 'speed_optimized',
            'complexity_estimate': 0.2
        }
        
        preferences = {
            'performance_weights': {
                'accuracy': 0.1,
                'speed': 0.8,
                'memory_efficiency': 0.05,
                'cpu_efficiency': 0.05
            }
        }
        
        optimal_config = self.manager.select_optimal_model(requirements, preferences=preferences)
        
        # Should prefer fast models
        assert optimal_config is not None
        assert optimal_config.performance_metrics.speed_score >= 0.8
    
    def test_caching_behavior(self):
        """Test that model selection results are cached"""
        requirements = {
            'capabilities': ['named_entity_recognition'],
            'processing_mode': 'balanced'
        }
        
        # First selection
        config1 = self.manager.select_optimal_model(requirements)
        
        # Second selection with same requirements
        config2 = self.manager.select_optimal_model(requirements)
        
        # Should return the same model (from cache)
        assert config1 is not None
        assert config2 is not None
        assert config1.model_id == config2.model_id
        
        # Cache should have entries
        assert len(self.manager.selection_cache) > 0

# Integration tests
def test_end_to_end_model_selection():
    """Test complete end-to-end model selection workflow"""
    manager = ModelConfigurationManager()
    
    # Scenario 1: Quick processing for simple text
    requirements1 = {
        'capabilities': ['tokenization', 'named_entity_recognition'],
        'processing_mode': 'speed_optimized',
        'content_type': 'quick_processing',
        'complexity_estimate': 0.2
    }
    
    resources1 = {
        'max_memory_mb': 100,
        'max_cpu_cores': 2,
        'gpu_available': False
    }
    
    model1 = manager.select_optimal_model(requirements1, resources1)
    assert model1 is not None
    assert model1.model_size in [ModelSize.SMALL, ModelSize.TINY]
    
    # Scenario 2: High accuracy for complex analysis
    requirements2 = {
        'capabilities': ['named_entity_recognition', 'dependency_parsing', 'entity_linking'],
        'processing_mode': 'accuracy_optimized',
        'content_type': 'research',
        'complexity_estimate': 0.9
    }
    
    resources2 = {
        'max_memory_mb': 2000,
        'max_cpu_cores': 8,
        'gpu_available': True,
        'max_gpu_memory_mb': 4000
    }
    
    model2 = manager.select_optimal_model(requirements2, resources2)
    assert model2 is not None
    assert model2.model_size in [ModelSize.LARGE, ModelSize.EXTRA_LARGE]
    assert model2.performance_metrics.accuracy_score >= 0.85

if __name__ == "__main__":
    pytest.main([__file__, "-v"])