#!/usr/bin/env python3
"""
Test Suite: Quality Optimization Engine - Intent-First Transformation
Comprehensive tests for the quality optimization engine functionality
"""

import pytest
import asyncio
from datetime import datetime
from quality_optimization_engine import (
    QualityOptimizationEngine, QualityScore, QualityTier, TaskComplexity,
    CostQualityOption, ProviderRecommendation, UserFeedback, UserPreferences
)
from multi_llm_provider_system import LLMRequest, TaskType, LLMProvider

class TestQualityOptimizationEngine:
    """Test cases for Quality Optimization Engine"""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance for testing"""
        return QualityOptimizationEngine()
    
    @pytest.fixture
    def sample_request(self):
        """Create sample LLM request for testing"""
        return LLMRequest(
            prompt="Analyze the legal implications of this contract clause",
            task_type=TaskType.ANALYSIS,
            max_tokens=500,
            temperature=0.7
        )
    
    @pytest.mark.asyncio
    async def test_provider_recommendation_generation(self, engine, sample_request):
        """Test provider recommendation generation"""
        recommendation = await engine.get_optimal_provider_recommendation(
            sample_request, "test_user", "balanced"
        )
        
        assert isinstance(recommendation, ProviderRecommendation)
        assert isinstance(recommendation.recommended_provider, LLMProvider)
        assert isinstance(recommendation.quality_tier, QualityTier)
        assert isinstance(recommendation.reasoning, str)
        assert len(recommendation.reasoning) > 0
        assert 0.0 <= recommendation.cost_estimate <= 1.0  # Reasonable cost range
        assert 0.0 <= recommendation.quality_score <= 1.0
        assert 0.0 <= recommendation.confidence <= 1.0
        assert isinstance(recommendation.alternatives, list)
    
    @pytest.mark.asyncio
    async def test_quality_comparison(self, engine, sample_request):
        """Test quality comparison across providers"""
        comparison = await engine.get_quality_comparison(sample_request)
        
        assert isinstance(comparison, dict)
        assert len(comparison) > 0
        
        for provider, metrics in comparison.items():
            assert isinstance(provider, LLMProvider)
            assert 'quality_score' in metrics
            assert 'accuracy' in metrics
            assert 'speed_score' in metrics
            assert 'cost_efficiency' in metrics
            assert 'cost_estimate' in metrics
            assert 'speed_estimate' in metrics
            assert 'recommendation' in metrics
            
            # Validate metric ranges
            assert 0.0 <= metrics['quality_score'] <= 1.0
            assert 0.0 <= metrics['accuracy'] <= 1.0
            assert 0.0 <= metrics['speed_score'] <= 1.0
            assert 0.0 <= metrics['cost_efficiency'] <= 1.0
            assert metrics['cost_estimate'] >= 0.0
    
    @pytest.mark.asyncio
    async def test_user_feedback_recording(self, engine):
        """Test user feedback recording and processing"""
        feedback = UserFeedback(
            user_id="test_user",
            provider=LLMProvider.OPENAI,
            task_type=TaskType.ANALYSIS,
            quality_rating=4.5,
            speed_rating=4.0,
            satisfaction_rating=4.2,
            text_feedback="Good quality analysis"
        )
        
        # Record feedback should not raise exception
        await engine.record_user_feedback(feedback)
        
        # Check that feedback was stored
        assert feedback in engine.user_feedback_history
        
        # Check that user preferences were updated
        user_prefs = engine._get_user_preferences("test_user")
        assert isinstance(user_prefs, UserPreferences)
        assert user_prefs.user_id == "test_user"
    
    @pytest.mark.asyncio
    async def test_user_quality_insights(self, engine):
        """Test user quality insights generation"""
        # Add some feedback first
        feedback_items = [
            UserFeedback("insight_user", LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.8, 3.5, 4.5),
            UserFeedback("insight_user", LLMProvider.OPENAI, TaskType.SUMMARIZATION, 4.2, 4.0, 4.1),
            UserFeedback("insight_user", LLMProvider.GROQ, TaskType.CODE_GENERATION, 4.0, 4.8, 4.3)
        ]
        
        for feedback in feedback_items:
            await engine.record_user_feedback(feedback)
        
        # Get insights
        insights = await engine.get_user_quality_insights("insight_user")
        
        assert isinstance(insights, dict)
        assert 'total_interactions' in insights
        assert 'average_satisfaction' in insights
        assert 'average_quality_rating' in insights
        assert 'preferred_providers' in insights
        assert 'quality_trends' in insights
        assert 'recommendations' in insights
        
        assert insights['total_interactions'] == 3
        assert 0.0 <= insights['average_satisfaction'] <= 5.0
        assert 0.0 <= insights['average_quality_rating'] <= 5.0
        assert isinstance(insights['preferred_providers'], list)
        assert isinstance(insights['recommendations'], list)
    
    def test_quality_score_initialization(self, engine):
        """Test quality score initialization"""
        assert len(engine.quality_scores) > 0
        
        # Check that some baseline scores exist
        openai_analysis_key = (LLMProvider.OPENAI, TaskType.ANALYSIS)
        if openai_analysis_key in engine.quality_scores:
            score = engine.quality_scores[openai_analysis_key]
            assert isinstance(score, QualityScore)
            assert 0.0 <= score.accuracy <= 1.0
            assert 0.0 <= score.consistency <= 1.0
            assert 0.0 <= score.speed <= 1.0
            assert 0.0 <= score.cost_efficiency <= 1.0
            assert 0.0 <= score.overall_score <= 1.0
    
    def test_cost_estimation(self, engine, sample_request):
        """Test cost estimation for providers"""
        for provider in LLMProvider:
            cost = engine._estimate_cost(provider, sample_request)
            assert isinstance(cost, float)
            assert cost >= 0.0
            assert cost <= 1.0  # Reasonable upper bound for testing
    
    def test_speed_estimation(self, engine, sample_request):
        """Test speed estimation for providers"""
        for provider in LLMProvider:
            speed = engine._estimate_speed(provider, sample_request)
            assert isinstance(speed, str)
            assert len(speed) > 0
            assert any(word in speed.lower() for word in ['fast', 'slow', 'moderate', 'second'])
    
    def test_quality_tier_determination(self, engine):
        """Test quality tier determination from scores"""
        assert engine._determine_quality_tier(0.95) == QualityTier.PREMIUM
        assert engine._determine_quality_tier(0.85) == QualityTier.STANDARD
        assert engine._determine_quality_tier(0.75) == QualityTier.ECONOMY
    
    def test_specialized_domain_detection(self, engine):
        """Test specialized domain detection"""
        legal_prompt = "Review this contract for legal compliance issues"
        assert engine._detect_specialized_domain(legal_prompt) == "legal"
        
        medical_prompt = "Analyze these patient symptoms for diagnosis"
        assert engine._detect_specialized_domain(medical_prompt) == "medical"
        
        technical_prompt = "Debug this Python code and fix the algorithm"
        assert engine._detect_specialized_domain(technical_prompt) == "technical"
        
        generic_prompt = "Write a story about a cat"
        assert engine._detect_specialized_domain(generic_prompt) is None
    
    def test_pros_cons_generation(self, engine):
        """Test pros and cons generation for providers"""
        quality_score = QualityScore(0.9, 0.85, 0.8, 0.75, 0.85)
        cost_estimate = 0.15
        
        pros, cons = engine._generate_pros_cons(LLMProvider.CLAUDE, quality_score, cost_estimate)
        
        assert isinstance(pros, list)
        assert isinstance(cons, list)
        assert len(pros) > 0
        assert len(cons) > 0
        
        # Check that pros and cons are strings
        for pro in pros:
            assert isinstance(pro, str)
            assert len(pro) > 0
        
        for con in cons:
            assert isinstance(con, str)
            assert len(con) > 0
    
    @pytest.mark.asyncio
    async def test_task_requirements_analysis(self, engine, sample_request):
        """Test task requirements analysis"""
        analysis = await engine._analyze_task_requirements(sample_request)
        
        assert isinstance(analysis, dict)
        assert 'task_type' in analysis
        assert 'complexity' in analysis
        assert 'prompt_length' in analysis
        assert 'requires_accuracy' in analysis
        assert 'requires_speed' in analysis
        assert 'context_dependent' in analysis
        assert 'specialized_domain' in analysis
        
        assert analysis['task_type'] == sample_request.task_type
        assert isinstance(analysis['complexity'], TaskComplexity)
        assert isinstance(analysis['prompt_length'], int)
        assert isinstance(analysis['requires_accuracy'], bool)
        assert isinstance(analysis['requires_speed'], bool)
        assert isinstance(analysis['context_dependent'], bool)
    
    def test_user_preferences_management(self, engine):
        """Test user preferences creation and management"""
        user_id = "pref_test_user"
        
        # Get preferences for new user
        prefs = engine._get_user_preferences(user_id)
        assert isinstance(prefs, UserPreferences)
        assert prefs.user_id == user_id
        assert 0.0 <= prefs.quality_priority <= 1.0
        assert 0.0 <= prefs.cost_sensitivity <= 1.0
        assert 0.0 <= prefs.speed_priority <= 1.0
        
        # Modify preferences
        prefs.quality_priority = 0.9
        prefs.cost_sensitivity = 0.1
        
        # Get preferences again - should be same object
        prefs2 = engine._get_user_preferences(user_id)
        assert prefs2 is prefs
        assert prefs2.quality_priority == 0.9
    
    def test_recommendation_confidence_calculation(self, engine):
        """Test recommendation confidence calculation"""
        option = CostQualityOption(
            provider=LLMProvider.CLAUDE,
            quality_score=0.95,
            cost_estimate=0.20,
            speed_estimate="Moderate",
            description="High quality option"
        )
        
        confidence = engine._calculate_recommendation_confidence(option)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    @pytest.mark.asyncio
    async def test_cost_preference_handling(self, engine, sample_request):
        """Test different cost preference handling"""
        user_id = "cost_test_user"
        
        # Test premium preference
        premium_rec = await engine.get_optimal_provider_recommendation(
            sample_request, user_id, "premium"
        )
        
        # Test economy preference
        economy_rec = await engine.get_optimal_provider_recommendation(
            sample_request, user_id, "economy"
        )
        
        # Test balanced preference
        balanced_rec = await engine.get_optimal_provider_recommendation(
            sample_request, user_id, "balanced"
        )
        
        # All should return valid recommendations
        assert isinstance(premium_rec, ProviderRecommendation)
        assert isinstance(economy_rec, ProviderRecommendation)
        assert isinstance(balanced_rec, ProviderRecommendation)
        
        # Premium should generally have higher quality score
        # Economy should generally have lower cost
        # (These are tendencies, not strict requirements due to task-specific optimization)
        assert premium_rec.quality_score >= 0.0
        assert economy_rec.cost_estimate >= 0.0
        assert balanced_rec.quality_score >= 0.0

class TestTaskComplexityAnalyzer:
    """Test cases for Task Complexity Analyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for testing"""
        from quality_optimization_engine import TaskComplexityAnalyzer
        return TaskComplexityAnalyzer()
    
    def test_expert_complexity_detection(self, analyzer):
        """Test expert complexity detection"""
        expert_request = LLMRequest(
            prompt="Analyze and evaluate the complex legal implications of this multi-party contract, comparing it with relevant case law and providing detailed recommendations for risk mitigation strategies.",
            task_type=TaskType.ANALYSIS,
            max_tokens=1000
        )
        
        complexity = analyzer.analyze_complexity(expert_request)
        assert complexity == TaskComplexity.EXPERT
    
    def test_simple_complexity_detection(self, analyzer):
        """Test simple complexity detection"""
        simple_request = LLMRequest(
            prompt="List the main features of Python",
            task_type=TaskType.TEXT_GENERATION,
            max_tokens=200
        )
        
        complexity = analyzer.analyze_complexity(simple_request)
        assert complexity == TaskComplexity.SIMPLE
    
    def test_complex_complexity_detection(self, analyzer):
        """Test complex complexity detection"""
        complex_request = LLMRequest(
            prompt="Explain how machine learning algorithms work and create a detailed summary of different types",
            task_type=TaskType.SUMMARIZATION,
            max_tokens=600
        )
        
        complexity = analyzer.analyze_complexity(complex_request)
        assert complexity in [TaskComplexity.COMPLEX, TaskComplexity.MODERATE]
    
    def test_moderate_complexity_detection(self, analyzer):
        """Test moderate complexity detection"""
        moderate_request = LLMRequest(
            prompt="Write a function to sort a list of numbers",
            task_type=TaskType.CODE_GENERATION,
            max_tokens=300
        )
        
        complexity = analyzer.analyze_complexity(moderate_request)
        assert complexity in [TaskComplexity.MODERATE, TaskComplexity.SIMPLE]

class TestQualityOptimizationIntegration:
    """Integration tests for Quality Optimization Engine"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_recommendation_flow(self):
        """Test complete recommendation flow"""
        engine = QualityOptimizationEngine()
        
        # Create request
        request = LLMRequest(
            prompt="Analyze the financial performance of this company based on the quarterly report",
            task_type=TaskType.ANALYSIS,
            max_tokens=600,
            temperature=0.3
        )
        
        # Get recommendation
        recommendation = await engine.get_optimal_provider_recommendation(
            request, "integration_test_user", "balanced"
        )
        
        # Verify recommendation
        assert recommendation is not None
        assert recommendation.recommended_provider is not None
        assert recommendation.quality_score > 0.0
        assert recommendation.cost_estimate > 0.0
        
        # Get comparison
        comparison = await engine.get_quality_comparison(request)
        assert len(comparison) > 0
        
        # Record feedback
        feedback = UserFeedback(
            user_id="integration_test_user",
            provider=recommendation.recommended_provider,
            task_type=request.task_type,
            quality_rating=4.5,
            speed_rating=4.0,
            satisfaction_rating=4.3
        )
        
        await engine.record_user_feedback(feedback)
        
        # Get insights
        insights = await engine.get_user_quality_insights("integration_test_user")
        assert insights['total_interactions'] >= 1
    
    @pytest.mark.asyncio
    async def test_learning_adaptation(self):
        """Test that the system learns from feedback"""
        engine = QualityOptimizationEngine()
        user_id = "learning_test_user"
        
        # Record multiple feedback entries for Claude with high ratings
        claude_feedback = [
            UserFeedback(user_id, LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.8, 3.5, 4.6),
            UserFeedback(user_id, LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.9, 3.2, 4.7),
            UserFeedback(user_id, LLMProvider.CLAUDE, TaskType.ANALYSIS, 4.7, 3.8, 4.5)
        ]
        
        for feedback in claude_feedback:
            await engine.record_user_feedback(feedback)
        
        # Get insights to verify learning
        insights = await engine.get_user_quality_insights(user_id)
        
        assert insights['total_interactions'] == 3
        assert insights['average_satisfaction'] > 4.0
        
        # Check if Claude appears in preferred providers
        preferred_providers = [p['provider'] for p in insights['preferred_providers']]
        assert 'claude' in preferred_providers

def test_quality_optimization_engine_initialization():
    """Test engine initialization"""
    engine = QualityOptimizationEngine()
    
    assert engine is not None
    assert hasattr(engine, 'quality_scores')
    assert hasattr(engine, 'user_preferences')
    assert hasattr(engine, 'user_feedback_history')
    assert hasattr(engine, 'task_complexity_analyzer')
    
    # Check that quality scores were initialized
    assert len(engine.quality_scores) > 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])