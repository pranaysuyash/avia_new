#!/usr/bin/env python3
"""
NLP Model Configurations - Advanced Configuration Management
Provides comprehensive model configurations for different spaCy model sizes and use cases
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict, field
from enum import Enum
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModelSize(Enum):
    """Model size classifications"""
    TINY = "tiny"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    EXTRA_LARGE = "extra_large"

class ModelType(Enum):
    """Model type classifications"""
    SPACY_STATISTICAL = "spacy_statistical"
    SPACY_TRANSFORMER = "spacy_transformer"
    HUGGINGFACE_TRANSFORMER = "huggingface_transformer"
    OPENAI_API = "openai_api"
    LOCAL_CUSTOM = "local_custom"

class ProcessingMode(Enum):
    """Processing mode preferences"""
    SPEED_OPTIMIZED = "speed_optimized"
    ACCURACY_OPTIMIZED = "accuracy_optimized"
    BALANCED = "balanced"
    RESOURCE_CONSTRAINED = "resource_constrained"

@dataclass
class ResourceRequirements:
    """Resource requirements for a model"""
    memory_mb: int
    cpu_cores: int
    gpu_required: bool = False
    gpu_memory_mb: int = 0
    disk_space_mb: int = 0
    network_required: bool = False
    
    def meets_constraints(self, available_resources: Dict[str, Any]) -> bool:
        """Check if available resources meet requirements"""
        if self.memory_mb > available_resources.get('max_memory_mb', float('inf')):
            return False
        if self.cpu_cores > available_resources.get('max_cpu_cores', float('inf')):
            return False
        if self.gpu_required and not available_resources.get('gpu_available', False):
            return False
        if self.gpu_memory_mb > available_resources.get('max_gpu_memory_mb', float('inf')):
            return False
        if self.network_required and not available_resources.get('network_available', True):
            return False
        return True

@dataclass
class PerformanceMetrics:
    """Performance metrics for a model"""
    accuracy_score: float  # 0.0 to 1.0
    speed_score: float     # 0.0 to 1.0 (higher is faster)
    memory_efficiency: float  # 0.0 to 1.0
    cpu_efficiency: float     # 0.0 to 1.0
    
    # Specific NLP task performance
    ner_accuracy: float = 0.0
    sentiment_accuracy: float = 0.0
    pos_tagging_accuracy: float = 0.0
    dependency_parsing_accuracy: float = 0.0
    
    # Processing speed metrics (words per second)
    processing_speed_wps: float = 0.0
    
    def overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate overall performance score"""
        if weights is None:
            weights = {
                'accuracy': 0.4,
                'speed': 0.3,
                'memory_efficiency': 0.15,
                'cpu_efficiency': 0.15
            }
        
        return (
            self.accuracy_score * weights.get('accuracy', 0.4) +
            self.speed_score * weights.get('speed', 0.3) +
            self.memory_efficiency * weights.get('memory_efficiency', 0.15) +
            self.cpu_efficiency * weights.get('cpu_efficiency', 0.15)
        )

@dataclass
class ModelCapabilities:
    """Capabilities supported by a model"""
    named_entity_recognition: bool = False
    part_of_speech_tagging: bool = False
    dependency_parsing: bool = False
    sentence_segmentation: bool = False
    tokenization: bool = False
    lemmatization: bool = False
    word_vectors: bool = False
    sentiment_analysis: bool = False
    text_classification: bool = False
    similarity_matching: bool = False
    entity_linking: bool = False
    coreference_resolution: bool = False
    
    # Advanced capabilities
    transformer_embeddings: bool = False
    multilingual_support: bool = False
    custom_components: bool = False
    
    def supports_capability(self, capability: str) -> bool:
        """Check if model supports a specific capability"""
        return getattr(self, capability, False)
    
    def get_supported_capabilities(self) -> List[str]:
        """Get list of supported capabilities"""
        return [
            field_name for field_name, field_value in asdict(self).items()
            if field_value is True
        ]

@dataclass
class ModelConfiguration:
    """Comprehensive model configuration"""
    # Basic identification
    model_id: str
    model_name: str
    model_type: ModelType
    model_size: ModelSize
    version: str = "latest"
    
    # Model details
    description: str = ""
    language: str = "en"
    pipeline_components: List[str] = field(default_factory=list)
    
    # Requirements and performance
    resource_requirements: ResourceRequirements = field(default_factory=lambda: ResourceRequirements(50, 1))
    performance_metrics: PerformanceMetrics = field(default_factory=lambda: PerformanceMetrics(0.7, 0.7, 0.7, 0.7))
    capabilities: ModelCapabilities = field(default_factory=ModelCapabilities)
    
    # Installation and usage
    installation_command: Optional[str] = None
    model_path: Optional[str] = None
    download_url: Optional[str] = None
    license: str = "MIT"
    
    # Processing preferences
    recommended_for: List[str] = field(default_factory=list)
    not_recommended_for: List[str] = field(default_factory=list)
    processing_modes: List[ProcessingMode] = field(default_factory=list)
    
    # Fallback configuration
    fallback_models: List[str] = field(default_factory=list)
    fallback_priority: int = 5  # 1 = highest priority, 10 = lowest
    
    # Additional metadata
    created_date: Optional[str] = None
    last_updated: Optional[str] = None
    maintainer: str = "spaCy"
    documentation_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        # Convert enums to strings
        result['model_type'] = self.model_type.value
        result['model_size'] = self.model_size.value
        result['processing_modes'] = [mode.value for mode in self.processing_modes]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelConfiguration':
        """Create from dictionary"""
        # Convert string enums back to enum objects
        if 'model_type' in data:
            data['model_type'] = ModelType(data['model_type'])
        if 'model_size' in data:
            data['model_size'] = ModelSize(data['model_size'])
        if 'processing_modes' in data:
            data['processing_modes'] = [ProcessingMode(mode) for mode in data['processing_modes']]
        
        # Handle nested dataclasses
        if 'resource_requirements' in data and isinstance(data['resource_requirements'], dict):
            data['resource_requirements'] = ResourceRequirements(**data['resource_requirements'])
        if 'performance_metrics' in data and isinstance(data['performance_metrics'], dict):
            data['performance_metrics'] = PerformanceMetrics(**data['performance_metrics'])
        if 'capabilities' in data and isinstance(data['capabilities'], dict):
            data['capabilities'] = ModelCapabilities(**data['capabilities'])
        
        return cls(**data)

class ModelConfigurationManager:
    """Manages model configurations and provides selection logic"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager"""
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent / "configs"
        self.config_dir.mkdir(exist_ok=True)
        
        self.configurations: Dict[str, ModelConfiguration] = {}
        self.selection_cache: Dict[str, str] = {}
        
        # Load default configurations
        self._load_default_configurations()
        
        # Load custom configurations if they exist
        self._load_custom_configurations()
        
        logger.info(f"Loaded {len(self.configurations)} model configurations")
    
    def _load_default_configurations(self):
        """Load default spaCy model configurations"""
        
        # spaCy Small Model
        small_config = ModelConfiguration(
            model_id="en_core_web_sm",
            model_name="English Core Web Small",
            model_type=ModelType.SPACY_STATISTICAL,
            model_size=ModelSize.SMALL,
            description="Small English model with basic NLP capabilities",
            pipeline_components=["tok2vec", "tagger", "parser", "senter", "ner", "attribute_ruler", "lemmatizer"],
            resource_requirements=ResourceRequirements(
                memory_mb=50,
                cpu_cores=1,
                disk_space_mb=50
            ),
            performance_metrics=PerformanceMetrics(
                accuracy_score=0.75,
                speed_score=0.95,
                memory_efficiency=0.9,
                cpu_efficiency=0.9,
                ner_accuracy=0.85,
                sentiment_accuracy=0.7,
                pos_tagging_accuracy=0.97,
                dependency_parsing_accuracy=0.92,
                processing_speed_wps=15000
            ),
            capabilities=ModelCapabilities(
                named_entity_recognition=True,
                part_of_speech_tagging=True,
                dependency_parsing=True,
                sentence_segmentation=True,
                tokenization=True,
                lemmatization=True,
                word_vectors=False
            ),
            installation_command="python -m spacy download en_core_web_sm",
            recommended_for=["quick_processing", "real_time_analysis", "resource_constrained"],
            processing_modes=[ProcessingMode.SPEED_OPTIMIZED, ProcessingMode.RESOURCE_CONSTRAINED],
            fallback_priority=1,
            maintainer="spaCy",
            documentation_url="https://spacy.io/models/en#en_core_web_sm"
        )
        
        # spaCy Medium Model
        medium_config = ModelConfiguration(
            model_id="en_core_web_md",
            model_name="English Core Web Medium",
            model_type=ModelType.SPACY_STATISTICAL,
            model_size=ModelSize.MEDIUM,
            description="Medium English model with word vectors",
            pipeline_components=["tok2vec", "tagger", "parser", "senter", "ner", "attribute_ruler", "lemmatizer"],
            resource_requirements=ResourceRequirements(
                memory_mb=50,
                cpu_cores=1,
                disk_space_mb=50
            ),
            performance_metrics=PerformanceMetrics(
                accuracy_score=0.8,
                speed_score=0.85,
                memory_efficiency=0.8,
                cpu_efficiency=0.85,
                ner_accuracy=0.87,
                sentiment_accuracy=0.75,
                pos_tagging_accuracy=0.97,
                dependency_parsing_accuracy=0.92,
                processing_speed_wps=12000
            ),
            capabilities=ModelCapabilities(
                named_entity_recognition=True,
                part_of_speech_tagging=True,
                dependency_parsing=True,
                sentence_segmentation=True,
                tokenization=True,
                lemmatization=True,
                word_vectors=True,
                similarity_matching=True
            ),
            installation_command="python -m spacy download en_core_web_md",
            recommended_for=["general_nlp", "similarity_tasks", "balanced_performance"],
            processing_modes=[ProcessingMode.BALANCED],
            fallback_models=["en_core_web_sm"],
            fallback_priority=2,
            maintainer="spaCy",
            documentation_url="https://spacy.io/models/en#en_core_web_md"
        )
        
        # spaCy Large Model
        large_config = ModelConfiguration(
            model_id="en_core_web_lg",
            model_name="English Core Web Large",
            model_type=ModelType.SPACY_STATISTICAL,
            model_size=ModelSize.LARGE,
            description="Large English model with comprehensive word vectors",
            pipeline_components=["tok2vec", "tagger", "parser", "senter", "ner", "attribute_ruler", "lemmatizer"],
            resource_requirements=ResourceRequirements(
                memory_mb=750,
                cpu_cores=2,
                disk_space_mb=750
            ),
            performance_metrics=PerformanceMetrics(
                accuracy_score=0.85,
                speed_score=0.7,
                memory_efficiency=0.6,
                cpu_efficiency=0.75,
                ner_accuracy=0.89,
                sentiment_accuracy=0.8,
                pos_tagging_accuracy=0.97,
                dependency_parsing_accuracy=0.93,
                processing_speed_wps=8000
            ),
            capabilities=ModelCapabilities(
                named_entity_recognition=True,
                part_of_speech_tagging=True,
                dependency_parsing=True,
                sentence_segmentation=True,
                tokenization=True,
                lemmatization=True,
                word_vectors=True,
                similarity_matching=True,
                entity_linking=True
            ),
            installation_command="python -m spacy download en_core_web_lg",
            recommended_for=["high_accuracy", "research", "production_quality"],
            processing_modes=[ProcessingMode.ACCURACY_OPTIMIZED, ProcessingMode.BALANCED],
            fallback_models=["en_core_web_md", "en_core_web_sm"],
            fallback_priority=3,
            maintainer="spaCy",
            documentation_url="https://spacy.io/models/en#en_core_web_lg"
        )
        
        # spaCy Transformer Model
        transformer_config = ModelConfiguration(
            model_id="en_core_web_trf",
            model_name="English Core Web Transformer",
            model_type=ModelType.SPACY_TRANSFORMER,
            model_size=ModelSize.EXTRA_LARGE,
            description="Transformer-based English model with state-of-the-art accuracy",
            pipeline_components=["transformer", "tagger", "parser", "ner", "attribute_ruler", "lemmatizer"],
            resource_requirements=ResourceRequirements(
                memory_mb=560,
                cpu_cores=4,
                gpu_required=True,
                gpu_memory_mb=2000,
                disk_space_mb=560
            ),
            performance_metrics=PerformanceMetrics(
                accuracy_score=0.95,
                speed_score=0.3,
                memory_efficiency=0.4,
                cpu_efficiency=0.5,
                ner_accuracy=0.94,
                sentiment_accuracy=0.9,
                pos_tagging_accuracy=0.98,
                dependency_parsing_accuracy=0.96,
                processing_speed_wps=2000
            ),
            capabilities=ModelCapabilities(
                named_entity_recognition=True,
                part_of_speech_tagging=True,
                dependency_parsing=True,
                sentence_segmentation=True,
                tokenization=True,
                lemmatization=True,
                transformer_embeddings=True,
                similarity_matching=True,
                entity_linking=True,
                coreference_resolution=True
            ),
            installation_command="python -m spacy download en_core_web_trf",
            recommended_for=["maximum_accuracy", "research", "critical_applications"],
            processing_modes=[ProcessingMode.ACCURACY_OPTIMIZED],
            fallback_models=["en_core_web_lg", "en_core_web_md", "en_core_web_sm"],
            fallback_priority=4,
            maintainer="spaCy",
            documentation_url="https://spacy.io/models/en#en_core_web_trf"
        )
        
        # Store configurations
        self.configurations[small_config.model_id] = small_config
        self.configurations[medium_config.model_id] = medium_config
        self.configurations[large_config.model_id] = large_config
        self.configurations[transformer_config.model_id] = transformer_config
    
    def _load_custom_configurations(self):
        """Load custom configurations from files"""
        config_files = list(self.config_dir.glob("*.json")) + list(self.config_dir.glob("*.yaml"))
        
        for config_file in config_files:
            try:
                if config_file.suffix == '.json':
                    with open(config_file, 'r') as f:
                        data = json.load(f)
                elif config_file.suffix in ['.yaml', '.yml']:
                    with open(config_file, 'r') as f:
                        data = yaml.safe_load(f)
                else:
                    continue
                
                if isinstance(data, list):
                    for config_data in data:
                        config = ModelConfiguration.from_dict(config_data)
                        self.configurations[config.model_id] = config
                else:
                    config = ModelConfiguration.from_dict(data)
                    self.configurations[config.model_id] = config
                
                logger.info(f"Loaded custom configuration from {config_file}")
                
            except Exception as e:
                logger.error(f"Failed to load configuration from {config_file}: {e}")
    
    def get_configuration(self, model_id: str) -> Optional[ModelConfiguration]:
        """Get configuration for a specific model"""
        return self.configurations.get(model_id)
    
    def list_configurations(self, 
                          model_type: Optional[ModelType] = None,
                          model_size: Optional[ModelSize] = None,
                          processing_mode: Optional[ProcessingMode] = None) -> List[ModelConfiguration]:
        """List configurations with optional filtering"""
        configs = list(self.configurations.values())
        
        if model_type:
            configs = [c for c in configs if c.model_type == model_type]
        
        if model_size:
            configs = [c for c in configs if c.model_size == model_size]
        
        if processing_mode:
            configs = [c for c in configs if processing_mode in c.processing_modes]
        
        return configs
    
    def select_optimal_model(self,
                           requirements: Dict[str, Any],
                           available_resources: Optional[Dict[str, Any]] = None,
                           preferences: Optional[Dict[str, Any]] = None) -> Optional[ModelConfiguration]:
        """Select optimal model based on requirements and constraints"""
        
        # Generate cache key
        cache_key = self._generate_cache_key(requirements, available_resources, preferences)
        if cache_key in self.selection_cache:
            cached_model_id = self.selection_cache[cache_key]
            if cached_model_id in self.configurations:
                return self.configurations[cached_model_id]
        
        # Filter configurations based on requirements
        candidates = []
        
        for config in self.configurations.values():
            # Check resource constraints
            if available_resources and not config.resource_requirements.meets_constraints(available_resources):
                continue
            
            # Check required capabilities
            required_capabilities = requirements.get('capabilities', [])
            if not all(config.capabilities.supports_capability(cap) for cap in required_capabilities):
                continue
            
            # Check processing mode preference
            preferred_mode = requirements.get('processing_mode')
            if preferred_mode and ProcessingMode(preferred_mode) not in config.processing_modes:
                continue
            
            candidates.append(config)
        
        if not candidates:
            logger.warning("No models meet the specified requirements")
            return None
        
        # Score candidates
        scored_candidates = []
        for config in candidates:
            score = self._calculate_model_score(config, requirements, preferences or {})
            scored_candidates.append((score, config))
        
        # Sort by score (highest first)
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        
        # Select best candidate
        best_config = scored_candidates[0][1]
        
        # Cache the result
        self.selection_cache[cache_key] = best_config.model_id
        
        logger.info(f"Selected optimal model: {best_config.model_id} (score: {scored_candidates[0][0]:.2f})")
        return best_config
    
    def _calculate_model_score(self, config: ModelConfiguration, 
                              requirements: Dict[str, Any], 
                              preferences: Dict[str, Any]) -> float:
        """Calculate score for a model configuration"""
        score = 0.0
        
        # Base performance score
        performance_weights = preferences.get('performance_weights', {
            'accuracy': 0.4,
            'speed': 0.3,
            'memory_efficiency': 0.15,
            'cpu_efficiency': 0.15
        })
        
        score += config.performance_metrics.overall_score(performance_weights) * 50
        
        # Processing mode alignment
        preferred_mode = requirements.get('processing_mode')
        if preferred_mode and ProcessingMode(preferred_mode) in config.processing_modes:
            score += 20
        
        # Content type preferences
        content_type = requirements.get('content_type', '')
        if content_type in config.recommended_for:
            score += 15
        elif content_type in config.not_recommended_for:
            score -= 10
        
        # Capability bonus
        required_capabilities = requirements.get('capabilities', [])
        supported_capabilities = config.capabilities.get_supported_capabilities()
        capability_coverage = len(set(required_capabilities) & set(supported_capabilities)) / max(len(required_capabilities), 1)
        score += capability_coverage * 10
        
        # Fallback priority (lower is better)
        score += (10 - config.fallback_priority) * 2
        
        # Text complexity consideration
        complexity = requirements.get('complexity_estimate', 0.5)
        if complexity > 0.7 and config.model_size in [ModelSize.LARGE, ModelSize.EXTRA_LARGE]:
            score += 10
        elif complexity < 0.3 and config.model_size in [ModelSize.SMALL, ModelSize.TINY]:
            score += 10
        
        return score
    
    def _generate_cache_key(self, requirements: Dict[str, Any], 
                           available_resources: Optional[Dict[str, Any]], 
                           preferences: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for model selection"""
        key_data = {
            'requirements': sorted(requirements.items()) if requirements else [],
            'resources': sorted(available_resources.items()) if available_resources else [],
            'preferences': sorted(preferences.items()) if preferences else []
        }
        return str(hash(str(key_data)))
    
    def save_configuration(self, config: ModelConfiguration, filename: Optional[str] = None):
        """Save a configuration to file"""
        if filename is None:
            filename = f"{config.model_id}.json"
        
        filepath = self.config_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(config.to_dict(), f, indent=2)
        
        logger.info(f"Saved configuration to {filepath}")
    
    def add_configuration(self, config: ModelConfiguration):
        """Add a new configuration"""
        self.configurations[config.model_id] = config
        logger.info(f"Added configuration for {config.model_id}")
    
    def get_fallback_chain(self, model_id: str) -> List[ModelConfiguration]:
        """Get fallback chain for a model"""
        config = self.configurations.get(model_id)
        if not config:
            return []
        
        fallback_chain = []
        for fallback_id in config.fallback_models:
            fallback_config = self.configurations.get(fallback_id)
            if fallback_config:
                fallback_chain.append(fallback_config)
        
        return fallback_chain
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        stats = {
            'total_configurations': len(self.configurations),
            'by_type': {},
            'by_size': {},
            'by_processing_mode': {},
            'average_performance': {
                'accuracy': 0.0,
                'speed': 0.0,
                'memory_efficiency': 0.0,
                'cpu_efficiency': 0.0
            }
        }
        
        # Count by type and size
        for config in self.configurations.values():
            type_key = config.model_type.value
            size_key = config.model_size.value
            
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1
            stats['by_size'][size_key] = stats['by_size'].get(size_key, 0) + 1
            
            # Count processing modes
            for mode in config.processing_modes:
                mode_key = mode.value
                stats['by_processing_mode'][mode_key] = stats['by_processing_mode'].get(mode_key, 0) + 1
        
        # Calculate average performance
        if self.configurations:
            total_configs = len(self.configurations)
            for config in self.configurations.values():
                stats['average_performance']['accuracy'] += config.performance_metrics.accuracy_score
                stats['average_performance']['speed'] += config.performance_metrics.speed_score
                stats['average_performance']['memory_efficiency'] += config.performance_metrics.memory_efficiency
                stats['average_performance']['cpu_efficiency'] += config.performance_metrics.cpu_efficiency
            
            for key in stats['average_performance']:
                stats['average_performance'][key] /= total_configs
        
        return stats

# Example usage and utility functions
def create_default_config_manager() -> ModelConfigurationManager:
    """Create a default configuration manager with standard models"""
    return ModelConfigurationManager()

def example_model_selection():
    """Example of model selection"""
    manager = create_default_config_manager()
    
    # Example requirements
    requirements = {
        'capabilities': ['named_entity_recognition', 'part_of_speech_tagging'],
        'processing_mode': 'balanced',
        'content_type': 'general_nlp',
        'complexity_estimate': 0.6
    }
    
    # Example resource constraints
    available_resources = {
        'max_memory_mb': 1000,
        'max_cpu_cores': 4,
        'gpu_available': False
    }
    
    # Select optimal model
    optimal_config = manager.select_optimal_model(requirements, available_resources)
    
    if optimal_config:
        print(f"Selected model: {optimal_config.model_name}")
        print(f"Model ID: {optimal_config.model_id}")
        print(f"Performance score: {optimal_config.performance_metrics.overall_score():.2f}")
        print(f"Capabilities: {optimal_config.capabilities.get_supported_capabilities()}")
    else:
        print("No suitable model found")

if __name__ == "__main__":
    example_model_selection()