"""
Test Suite for AI Model Selection Engine

Comprehensive tests for model selection logic, performance tracking,
fallback strategies, and user preference handling.
"""

import pytest
import asyncio
import tempfile
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from ai_model_selection_engine import (
    ModelSelectionEngine, AIModel, AIRequest, UserPreferences, RequestContext,
    ModelCapability, ModelProvider, SelectionCriteria, ModelMetrics, ModelScore
)

class TestModelSelectionEngine:
    """Test cases for Model Selection Engine"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing"""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        temp_file.close()
        yield temp_file.name
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def engine(self, temp_db):
        """Create test engine instance"""
        return ModelSelectionEngine(db_path=temp_db)
    
    @pytest.fixture
    def sample_request(self):
        """Create sample AI request"""
        user_prefs = UserPreferences(
            preferred_providers=[ModelProvider.OPENAI],
            quality_threshold=0.8,
            max_latency_ms=3000.0,
            max_cost_per_request=0.02,
            privacy_required=False
        )
        
        context = RequestContext(
            user_id="test_user",
            request_type=ModelCapability.TRANSCRIPTION,
            content_size=1024,
            urgency="normal",
            quality_requirement="standard"
        )
        
        return AIRequest(
            id="test_req_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="test_audio.wav",
            context=context,
            preferences=user_prefs
        )
    
    def test_engine_initialization(self, engine):
        """Test engine initialization"""
        assert engine is not None
        assert len(engine.models) > 0
        assert os.path.exists(engine.db_path)
        
        # Check default models are loaded
        model_names = [model.name for model in engine.models.values()]
        assert "OpenAI Whisper-1" in model_names
        assert "Local Whisper" in model_names
    
    def test_database_initialization(self, engine):
        """Test database tables are created"""
        import sqlite3
        
        conn = sqlite3.connect(engine.db_path)
        cursor = conn.cursor()
        
        # Check tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        assert "model_metrics" in tables
        assert "selection_history" in tables
        
        conn.close()
    
    @pytest.mark.asyncio
    async def test_basic_model_selection(self, engine, sample_request):
        """Test basic model selection functionality"""
        selection = await engine.select_model(sample_request)
        
        assert selection is not None
        assert selection.primary_model is not None
        assert selection.primary_model.name is not None
        assert ModelCapability.TRANSCRIPTION in selection.primary_model.capabilities
        assert len(selection.fallback_models) >= 0
        assert selection.confidence_score > 0
        assert selection.estimated_cost >= 0
        assert selection.estimated_latency > 0
    
    @pytest.mark.asyncio
    async def test_model_selection_with_preferences(self, engine):
        """Test model selection respects user preferences"""
        # Test with OpenAI preference
        user_prefs = UserPreferences(
            preferred_providers=[ModelProvider.OPENAI],
            quality_threshold=0.9,
            max_latency_ms=2500.0,
            max_cost_per_request=0.01
        )
        
        context = RequestContext(
            user_id="test_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="normal",
            quality_requirement="high"
        )
        
        request = AIRequest(
            id="test_pref_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="test_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await engine.select_model(request)
        
        # Should prefer OpenAI model if available and meets criteria
        assert selection.primary_model.provider in [ModelProvider.OPENAI, ModelProvider.LOCAL_WHISPER]
        assert selection.estimated_latency <= user_prefs.max_latency_ms
        assert selection.estimated_cost <= user_prefs.max_cost_per_request
    
    @pytest.mark.asyncio
    async def test_privacy_preference(self, engine):
        """Test privacy preference prioritizes local models"""
        user_prefs = UserPreferences(
            privacy_required=True,
            quality_threshold=0.7,
            max_latency_ms=10000.0,
            max_cost_per_request=0.05
        )
        
        context = RequestContext(
            user_id="privacy_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="normal",
            quality_requirement="standard"
        )
        
        request = AIRequest(
            id="privacy_req_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="sensitive_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await engine.select_model(request)
        
        # Should prefer local models for privacy
        local_providers = [ModelProvider.LOCAL_WHISPER, ModelProvider.LOCAL_SPACY]
        assert selection.primary_model.provider in local_providers
    
    @pytest.mark.asyncio
    async def test_urgency_prioritizes_speed(self, engine):
        """Test high urgency prioritizes speed over other factors"""
        user_prefs = UserPreferences(
            quality_threshold=0.8,
            max_latency_ms=5000.0,
            max_cost_per_request=0.1
        )
        
        context = RequestContext(
            user_id="urgent_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="high",  # High urgency
            quality_requirement="standard"
        )
        
        request = AIRequest(
            id="urgent_req_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="urgent_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        # Custom weights that prioritize speed
        criteria_weights = {
            SelectionCriteria.SPEED: 0.5,
            SelectionCriteria.QUALITY: 0.2,
            SelectionCriteria.COST: 0.15,
            SelectionCriteria.AVAILABILITY: 0.1,
            SelectionCriteria.PRIVACY: 0.05
        }
        
        selection = await engine.select_model(request, criteria_weights)
        
        # Should select model with good speed characteristics
        assert selection.estimated_latency <= user_prefs.max_latency_ms
    
    @pytest.mark.asyncio
    async def test_quality_requirement_prioritizes_accuracy(self, engine):
        """Test high quality requirement prioritizes accuracy"""
        user_prefs = UserPreferences(
            quality_threshold=0.9,
            max_latency_ms=10000.0,
            max_cost_per_request=0.1
        )
        
        context = RequestContext(
            user_id="quality_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="low",
            quality_requirement="high"  # High quality
        )
        
        request = AIRequest(
            id="quality_req_001",
            capability=ModelCapability.TRANSCRIPTION,
            content="important_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        selection = await engine.select_model(request)
        
        # Should select high-accuracy model
        assert selection.primary_model.metrics.accuracy_score >= user_prefs.quality_threshold
    
    def test_get_available_models(self, engine):
        """Test getting available models for capability"""
        # Test transcription capability
        transcription_models = engine._get_available_models(ModelCapability.TRANSCRIPTION)
        assert len(transcription_models) > 0
        
        for model in transcription_models:
            assert ModelCapability.TRANSCRIPTION in model.capabilities
            assert model.is_available
            assert model.metrics.availability_percent > 50.0
        
        # Test text-to-speech capability
        tts_models = engine._get_available_models(ModelCapability.TEXT_TO_SPEECH)
        assert len(tts_models) > 0
        
        for model in tts_models:
            assert ModelCapability.TEXT_TO_SPEECH in model.capabilities
    
    def test_fallback_models(self, engine):
        """Test fallback model selection"""
        primary_model = list(engine.models.values())[0]
        fallback_models = engine.get_fallback_models(
            primary_model, 
            ModelCapability.TRANSCRIPTION
        )
        
        # Should return alternative models
        assert len(fallback_models) >= 0
        
        for fallback in fallback_models:
            assert fallback.id != primary_model.id
            assert ModelCapability.TRANSCRIPTION in fallback.capabilities
            assert fallback.is_available
    
    @pytest.mark.asyncio
    async def test_metrics_update(self, engine):
        """Test model metrics update functionality"""
        model_id = list(engine.models.keys())[0]
        original_model = engine.models[model_id]
        original_latency = original_model.metrics.latency_ms
        original_cost = original_model.metrics.cost_per_request
        
        # Update with new metrics
        new_latency = 1500.0
        new_cost = 0.008
        
        await engine.update_model_metrics(model_id, new_latency, new_cost, True)
        
        # Check metrics were updated (exponential moving average)
        updated_model = engine.models[model_id]
        assert updated_model.metrics.latency_ms != original_latency
        assert updated_model.metrics.cost_per_request != original_cost
        
        # Should be between original and new values due to EMA
        assert min(original_latency, new_latency) <= updated_model.metrics.latency_ms <= max(original_latency, new_latency)
    
    @pytest.mark.asyncio
    async def test_selection_logging(self, engine, sample_request):
        """Test selection history logging"""
        initial_history_length = len(engine.selection_history)
        
        selection = await engine.select_model(sample_request)
        
        # Check history was updated
        assert len(engine.selection_history) == initial_history_length + 1
        
        # Check history entry
        latest_entry = engine.selection_history[-1]
        assert latest_entry["request_id"] == sample_request.id
        assert latest_entry["selected_model_id"] == selection.primary_model.id
        assert "selection_score" in latest_entry
        assert "timestamp" in latest_entry
    
    def test_performance_summary(self, engine):
        """Test performance summary generation"""
        summary = engine.get_model_performance_summary()
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        
        for model_id, info in summary.items():
            assert "name" in info
            assert "provider" in info
            assert "capabilities" in info
            assert "metrics" in info
            assert "is_available" in info
            assert "priority" in info
            
            # Check metrics structure
            metrics = info["metrics"]
            assert "latency_ms" in metrics
            assert "accuracy_score" in metrics
            assert "cost_per_request" in metrics
            assert "availability_percent" in metrics
    
    @pytest.mark.asyncio
    async def test_no_available_models_error(self, engine):
        """Test error handling when no models are available"""
        # Disable all models
        for model in engine.models.values():
            model.is_available = False
        
        user_prefs = UserPreferences()
        context = RequestContext(
            user_id="test_user",
            request_type=ModelCapability.TRANSCRIPTION
        )
        
        request = AIRequest(
            id="no_models_req",
            capability=ModelCapability.TRANSCRIPTION,
            content="test_audio.wav",
            context=context,
            preferences=user_prefs
        )
        
        with pytest.raises(ValueError, match="No available models"):
            await engine.select_model(request)
    
    @pytest.mark.asyncio
    async def test_custom_criteria_weights(self, engine, sample_request):
        """Test model selection with custom criteria weights"""
        # Heavily weight cost
        cost_focused_weights = {
            SelectionCriteria.COST: 0.7,
            SelectionCriteria.QUALITY: 0.1,
            SelectionCriteria.SPEED: 0.1,
            SelectionCriteria.AVAILABILITY: 0.05,
            SelectionCriteria.PRIVACY: 0.05
        }
        
        selection = await engine.select_model(sample_request, cost_focused_weights)
        
        # Should select cost-effective model
        assert selection.primary_model.metrics.cost_per_request <= sample_request.preferences.max_cost_per_request
    
    def test_model_scoring_logic(self, engine):
        """Test model scoring algorithm"""
        # Create test models with different characteristics
        fast_model = AIModel(
            id="fast_model",
            name="Fast Model",
            provider=ModelProvider.LOCAL_WHISPER,
            capabilities=[ModelCapability.TRANSCRIPTION],
            metrics=ModelMetrics(
                latency_ms=500.0,
                accuracy_score=0.8,
                cost_per_request=0.0,
                availability_percent=100.0
            )
        )
        
        accurate_model = AIModel(
            id="accurate_model",
            name="Accurate Model",
            provider=ModelProvider.OPENAI,
            capabilities=[ModelCapability.TRANSCRIPTION],
            metrics=ModelMetrics(
                latency_ms=3000.0,
                accuracy_score=0.95,
                cost_per_request=0.01,
                availability_percent=99.0
            )
        )
        
        models = [fast_model, accurate_model]
        
        user_prefs = UserPreferences(
            quality_threshold=0.8,
            max_latency_ms=5000.0,
            max_cost_per_request=0.02
        )
        
        context = RequestContext(
            user_id="test_user",
            request_type=ModelCapability.TRANSCRIPTION
        )
        
        request = AIRequest(
            id="scoring_test",
            capability=ModelCapability.TRANSCRIPTION,
            content="test",
            context=context,
            preferences=user_prefs
        )
        
        # Test speed-focused weights
        speed_weights = {
            SelectionCriteria.SPEED: 0.6,
            SelectionCriteria.QUALITY: 0.2,
            SelectionCriteria.COST: 0.1,
            SelectionCriteria.AVAILABILITY: 0.05,
            SelectionCriteria.PRIVACY: 0.05
        }
        
        # Run scoring (synchronous version for testing)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        scores = loop.run_until_complete(
            engine._score_models(models, request, speed_weights)
        )
        loop.close()
        
        # Fast model should score higher with speed-focused weights
        fast_score = next(s for s in scores if s.model.id == "fast_model")
        accurate_score = next(s for s in scores if s.model.id == "accurate_model")
        
        assert fast_score.criteria_scores[SelectionCriteria.SPEED] > accurate_score.criteria_scores[SelectionCriteria.SPEED]
    
    def test_criteria_weights_normalization(self, engine):
        """Test that criteria weights are properly handled"""
        user_prefs = UserPreferences()
        context = RequestContext(
            user_id="test_user",
            request_type=ModelCapability.TRANSCRIPTION,
            urgency="high"
        )
        
        # Test high urgency adjusts weights
        weights = engine._get_default_criteria_weights(
            AIRequest(
                id="test",
                capability=ModelCapability.TRANSCRIPTION,
                content="test",
                context=context,
                preferences=user_prefs
            )
        )
        
        # High urgency should increase speed weight
        assert weights[SelectionCriteria.SPEED] > 0.3
        
        # Test privacy requirement
        user_prefs.privacy_required = True
        context.urgency = "normal"
        
        weights = engine._get_default_criteria_weights(
            AIRequest(
                id="test",
                capability=ModelCapability.TRANSCRIPTION,
                content="test",
                context=context,
                preferences=user_prefs
            )
        )
        
        # Privacy required should increase privacy weight
        assert weights[SelectionCriteria.PRIVACY] > 0.2

@pytest.mark.asyncio
async def test_concurrent_selections(temp_db):
    """Test concurrent model selections"""
    engine = ModelSelectionEngine(db_path=temp_db)
    
    # Create multiple requests
    requests = []
    for i in range(5):
        user_prefs = UserPreferences()
        context = RequestContext(
            user_id=f"user_{i}",
            request_type=ModelCapability.TRANSCRIPTION
        )
        
        request = AIRequest(
            id=f"concurrent_req_{i}",
            capability=ModelCapability.TRANSCRIPTION,
            content=f"audio_{i}.wav",
            context=context,
            preferences=user_prefs
        )
        requests.append(request)
    
    # Run concurrent selections
    tasks = [engine.select_model(req) for req in requests]
    selections = await asyncio.gather(*tasks)
    
    # All selections should succeed
    assert len(selections) == 5
    for selection in selections:
        assert selection is not None
        assert selection.primary_model is not None

def test_model_registration():
    """Test adding custom models to the engine"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_file:
        temp_db = temp_file.name
    
    try:
        engine = ModelSelectionEngine(db_path=temp_db)
        initial_count = len(engine.models)
        
        # Add custom model
        custom_model = AIModel(
            id="custom_test_model",
            name="Custom Test Model",
            provider=ModelProvider.CUSTOM,
            capabilities=[ModelCapability.TEXT_GENERATION],
            metrics=ModelMetrics(
                latency_ms=1000.0,
                accuracy_score=0.85,
                cost_per_request=0.005,
                availability_percent=95.0
            )
        )
        
        engine.models[custom_model.id] = custom_model
        
        # Verify model was added
        assert len(engine.models) == initial_count + 1
        assert custom_model.id in engine.models
        assert engine.models[custom_model.id].name == "Custom Test Model"
        
    finally:
        os.unlink(temp_db)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])