#!/usr/bin/env python3
"""
Test Suite: User Confidence Engine - Intent-First Transformation
Comprehensive tests for the user confidence engine functionality
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from user_confidence_engine import (
    UserConfidenceEngine, UserConfidence, UserImpact, PredictiveAlert,
    ConfidenceLevel, ImpactLevel
)

class TestUserConfidenceEngine:
    """Test cases for User Confidence Engine"""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance for testing"""
        return UserConfidenceEngine()
    
    @pytest.mark.asyncio
    async def test_confidence_indicators_generation(self, engine):
        """Test generation of user confidence indicators"""
        confidence = await engine.get_user_confidence_indicators()
        
        assert isinstance(confidence, UserConfidence)
        assert 0.0 <= confidence.reliability_score <= 1.0
        assert isinstance(confidence.confidence_level, ConfidenceLevel)
        assert isinstance(confidence.user_message, str)
        assert len(confidence.user_message) > 0
        assert isinstance(confidence.estimated_processing_time, str)
        assert isinstance(confidence.proactive_alerts, list)
    
    @pytest.mark.asyncio
    async def test_impact_analysis_cpu(self, engine):
        """Test CPU usage impact analysis"""
        
        # Test normal CPU usage
        impact_normal = await engine.predict_user_impact("cpu_usage", 50.0)
        assert impact_normal.impact_level == ImpactLevel.NONE
        assert "smoothly" in impact_normal.user_message.lower()
        
        # Test high CPU usage
        impact_high = await engine.predict_user_impact("cpu_usage", 85.0)
        assert impact_high.impact_level == ImpactLevel.MODERATE
        assert len(impact_high.affected_features) > 0
        assert impact_high.estimated_delay is not None
        
        # Test critical CPU usage
        impact_critical = await engine.predict_user_impact("cpu_usage", 95.0)
        assert impact_critical.impact_level == ImpactLevel.SIGNIFICANT
        assert impact_critical.recommendation is not None
        assert impact_critical.workaround is not None
    
    @pytest.mark.asyncio
    async def test_impact_analysis_memory(self, engine):
        """Test memory usage impact analysis"""
        
        # Test normal memory usage
        impact_normal = await engine.predict_user_impact("memory_usage", 60.0)
        assert impact_normal.impact_level == ImpactLevel.NONE
        
        # Test high memory usage
        impact_high = await engine.predict_user_impact("memory_usage", 90.0)
        assert impact_high.impact_level == ImpactLevel.MODERATE
        assert "large_file_processing" in impact_high.affected_features
        
        # Test critical memory usage
        impact_critical = await engine.predict_user_impact("memory_usage", 98.0)
        assert impact_critical.impact_level == ImpactLevel.SIGNIFICANT
        assert impact_critical.workaround is not None
    
    @pytest.mark.asyncio
    async def test_impact_analysis_disk(self, engine):
        """Test disk usage impact analysis"""
        
        # Test normal disk usage
        impact_normal = await engine.predict_user_impact("disk_usage", 50.0)
        assert impact_normal.impact_level == ImpactLevel.NONE
        
        # Test high disk usage
        impact_high = await engine.predict_user_impact("disk_usage", 92.0)
        assert impact_high.impact_level == ImpactLevel.MODERATE
        
        # Test critical disk usage
        impact_critical = await engine.predict_user_impact("disk_usage", 98.0)
        assert impact_critical.impact_level == ImpactLevel.SIGNIFICANT
        assert "file_upload" in impact_critical.affected_features
    
    @pytest.mark.asyncio
    async def test_impact_analysis_error_rate(self, engine):
        """Test error rate impact analysis"""
        
        # Test normal error rate
        impact_normal = await engine.predict_user_impact("error_rate", 0.5)
        assert impact_normal.impact_level == ImpactLevel.NONE
        
        # Test moderate error rate
        impact_moderate = await engine.predict_user_impact("error_rate", 3.0)
        assert impact_moderate.impact_level == ImpactLevel.MODERATE
        
        # Test high error rate
        impact_high = await engine.predict_user_impact("error_rate", 6.0)
        assert impact_high.impact_level == ImpactLevel.SIGNIFICANT
        assert impact_high.workaround is not None
    
    @pytest.mark.asyncio
    async def test_impact_analysis_response_time(self, engine):
        """Test response time impact analysis"""
        
        # Test normal response time
        impact_normal = await engine.predict_user_impact("response_time", 500.0)
        assert impact_normal.impact_level == ImpactLevel.NONE
        
        # Test slow response time
        impact_slow = await engine.predict_user_impact("response_time", 3000.0)
        assert impact_slow.impact_level == ImpactLevel.MODERATE
        
        # Test very slow response time
        impact_very_slow = await engine.predict_user_impact("response_time", 6000.0)
        assert impact_very_slow.impact_level == ImpactLevel.SIGNIFICANT
        assert "ui_responsiveness" in impact_very_slow.affected_features
    
    @pytest.mark.asyncio
    async def test_predictive_alerts_generation(self, engine):
        """Test predictive alerts generation"""
        alerts = await engine.get_predictive_alerts()
        
        assert isinstance(alerts, list)
        
        for alert in alerts:
            assert isinstance(alert, PredictiveAlert)
            assert isinstance(alert.alert_type, str)
            assert isinstance(alert.message, str)
            assert 0.0 <= alert.confidence <= 1.0
            assert isinstance(alert.time_to_impact, str)
            assert isinstance(alert.recommended_action, str)
    
    def test_confidence_level_determination(self, engine):
        """Test confidence level determination from scores"""
        
        # Test excellent confidence
        excellent_level = engine._determine_confidence_level(0.95)
        assert excellent_level == ConfidenceLevel.EXCELLENT
        
        # Test good confidence
        good_level = engine._determine_confidence_level(0.85)
        assert good_level == ConfidenceLevel.GOOD
        
        # Test fair confidence
        fair_level = engine._determine_confidence_level(0.75)
        assert fair_level == ConfidenceLevel.FAIR
        
        # Test poor confidence
        poor_level = engine._determine_confidence_level(0.65)
        assert poor_level == ConfidenceLevel.POOR
    
    def test_user_message_generation(self, engine):
        """Test user message generation"""
        
        # Test excellent score message
        excellent_msg = engine._generate_user_message(0.96, 0.95)
        assert "optimally" in excellent_msg.lower()
        
        # Test good score message
        good_msg = engine._generate_user_message(0.87, 0.85)
        assert "well" in good_msg.lower() or "normal" in good_msg.lower()
        
        # Test fair score message
        fair_msg = engine._generate_user_message(0.77, 0.75)
        assert "stable" in fair_msg.lower()
        
        # Test poor score message
        poor_msg = engine._generate_user_message(0.60, 0.65)
        assert "load" in poor_msg.lower() or "delay" in poor_msg.lower()
    
    def test_processing_time_estimation(self, engine):
        """Test processing time estimation"""
        
        # Test fast processing
        queue_status_fast = {
            'average_processing_time': 60,
            'estimated_wait_time': 30
        }
        fast_time = engine._estimate_processing_time(queue_status_fast, 0.95)
        assert "minute" in fast_time.lower()
        
        # Test slow processing
        queue_status_slow = {
            'average_processing_time': 300,
            'estimated_wait_time': 600
        }
        slow_time = engine._estimate_processing_time(queue_status_slow, 0.60)
        assert "minute" in slow_time.lower()
    
    @pytest.mark.asyncio
    async def test_system_health_score_calculation(self, engine):
        """Test system health score calculation"""
        health_score = await engine._get_system_health_score()
        
        assert isinstance(health_score, float)
        assert 0.0 <= health_score <= 1.0
    
    @pytest.mark.asyncio
    async def test_processing_queue_status(self, engine):
        """Test processing queue status retrieval"""
        queue_status = await engine._get_processing_queue_status()
        
        assert isinstance(queue_status, dict)
        assert 'queue_length' in queue_status
        assert 'average_processing_time' in queue_status
        assert 'current_throughput' in queue_status
        assert 'estimated_wait_time' in queue_status
    
    @pytest.mark.asyncio
    async def test_reliability_score_calculation(self, engine):
        """Test reliability score calculation"""
        reliability_score = await engine._calculate_reliability_score()
        
        assert isinstance(reliability_score, float)
        assert 0.0 <= reliability_score <= 1.0
    
    def test_confidence_score_calculation(self, engine):
        """Test overall confidence score calculation"""
        
        system_health = 0.9
        queue_status = {'queue_length': 5}
        reliability = 0.95
        predictive = {'trend_stability': 0.9, 'capacity_headroom': 0.8}
        
        confidence_score = engine._calculate_confidence_score(
            system_health, queue_status, reliability, predictive
        )
        
        assert isinstance(confidence_score, float)
        assert 0.0 <= confidence_score <= 1.0
    
    def test_unknown_metric_impact(self, engine):
        """Test impact analysis for unknown metrics"""
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        impact = loop.run_until_complete(
            engine.predict_user_impact("unknown_metric", 50.0)
        )
        
        loop.close()
        
        assert impact.impact_level == ImpactLevel.NONE
        assert "normally" in impact.user_message.lower()
        assert len(impact.affected_features) == 0

class TestUserConfidenceIntegration:
    """Integration tests for User Confidence Engine"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_confidence_flow(self):
        """Test complete confidence assessment flow"""
        engine = UserConfidenceEngine()
        
        # Get confidence indicators
        confidence = await engine.get_user_confidence_indicators()
        
        # Verify all components are present
        assert confidence.reliability_score is not None
        assert confidence.confidence_level is not None
        assert confidence.user_message is not None
        assert confidence.estimated_processing_time is not None
        assert confidence.system_status_summary is not None
        
        # Test impact analysis for current state
        impact = await engine.predict_user_impact("cpu_usage", 75.0)
        assert impact is not None
        
        # Test predictive alerts
        alerts = await engine.get_predictive_alerts()
        assert isinstance(alerts, list)
    
    @pytest.mark.asyncio
    async def test_confidence_consistency(self):
        """Test that confidence indicators are consistent"""
        engine = UserConfidenceEngine()
        
        # Get confidence multiple times
        confidence1 = await engine.get_user_confidence_indicators()
        confidence2 = await engine.get_user_confidence_indicators()
        
        # Scores should be similar (within reasonable range)
        score_diff = abs(confidence1.reliability_score - confidence2.reliability_score)
        assert score_diff < 0.1  # Allow for small variations
        
        # Confidence levels should be consistent for similar scores
        if abs(confidence1.reliability_score - confidence2.reliability_score) < 0.05:
            assert confidence1.confidence_level == confidence2.confidence_level

def test_confidence_engine_initialization():
    """Test engine initialization"""
    engine = UserConfidenceEngine()
    
    assert engine is not None
    assert hasattr(engine, 'confidence_weights')
    assert hasattr(engine, 'performance_history')
    assert hasattr(engine, 'user_impact_patterns')

def test_confidence_weights_sum():
    """Test that confidence weights sum to 1.0"""
    engine = UserConfidenceEngine()
    
    total_weight = sum(engine.confidence_weights.values())
    assert abs(total_weight - 1.0) < 0.001  # Allow for floating point precision

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])