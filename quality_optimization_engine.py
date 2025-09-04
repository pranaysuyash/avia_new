#!/usr/bin/env python3
"""
Quality Optimization Engine - Intent-First Transformation
Transforms multi-LLM provider management into quality-focused user experience
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics

# Import existing multi-LLM system
try:
    from multi_llm_provider_system import (
        MultiLLMProviderSystem, LLMProvider, LLMRequest, LLMResponse, TaskType
    )
    MULTI_LLM_AVAILABLE = True
except ImportError:
    MULTI_LLM_AVAILABLE = False
    logging.warning("Multi-LLM provider system not available")

logger = logging.getLogger(__name__)

class QualityTier(Enum):
    """Quality tiers for user selection"""
    PREMIUM = "premium"
    STANDARD = "standard"
    ECONOMY = "economy"

class TaskComplexity(Enum):
    """Task complexity levels"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"

@dataclass
class QualityScore:
    """Quality scoring for providers by task type"""
    accuracy: float  # 0.0 to 1.0
    consistency: float  # 0.0 to 1.0
    speed: float  # 0.0 to 1.0
    cost_efficiency: float  # 0.0 to 1.0
    overall_score: float  # 0.0 to 1.0
    confidence_interval: float = 0.95
    sample_size: int = 0

@dataclass
class CostQualityOption:
    """Cost-quality trade-off option"""
    provider: LLMProvider
    quality_score: float
    cost_estimate: float
    speed_estimate: str
    description: str
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)

@dataclass
class ProviderRecommendation:
    """Provider recommendation with reasoning"""
    recommended_provider: LLMProvider
    quality_tier: QualityTier
    reasoning: str
    cost_estimate: float
    quality_score: float
    alternatives: List[CostQualityOption] = field(default_factory=list)
    user_choice_required: bool = False
    confidence: float = 0.9

@dataclass
class UserFeedback:
    """User feedback on provider performance"""
    user_id: str
    provider: LLMProvider
    task_type: TaskType
    quality_rating: float  # 1.0 to 5.0
    speed_rating: float  # 1.0 to 5.0
    satisfaction_rating: float  # 1.0 to 5.0
    text_feedback: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class UserPreferences:
    """User preferences for provider selection"""
    user_id: str
    quality_priority: float = 0.7  # 0.0 to 1.0
    cost_sensitivity: float = 0.3  # 0.0 to 1.0
    speed_priority: float = 0.5  # 0.0 to 1.0
    preferred_providers: List[LLMProvider] = field(default_factory=list)
    avoided_providers: List[LLMProvider] = field(default_factory=list)
    task_preferences: Dict[TaskType, Dict[str, float]] = field(default_factory=dict)

class QualityOptimizationEngine:
    """
    Intent-First transformation of multi-LLM provider system
    Focuses on quality outcomes and user transparency
    """
    
    def __init__(self):
        self.multi_llm_system = MultiLLMProviderSystem() if MULTI_LLM_AVAILABLE else None
        
        # Quality scoring database
        self.quality_scores: Dict[Tuple[LLMProvider, TaskType], QualityScore] = {}
        
        # User preferences and feedback
        self.user_preferences: Dict[str, UserPreferences] = {}
        self.user_feedback_history: List[UserFeedback] = []
        
        # Provider performance tracking
        self.provider_performance_history = {}
        
        # Initialize quality scores with baseline data
        self._initialize_quality_scores()
        
        # Task complexity analysis
        self.task_complexity_analyzer = TaskComplexityAnalyzer()
    
    async def get_optimal_provider_recommendation(
        self, 
        request: LLMRequest, 
        user_id: str,
        cost_preference: str = "balanced"  # "premium", "balanced", "economy"
    ) -> ProviderRecommendation:
        """Get optimal provider recommendation with quality focus"""
        
        # Analyze task requirements
        task_analysis = await self._analyze_task_requirements(request)
        
        # Get user preferences
        user_prefs = self._get_user_preferences(user_id)
        
        # Calculate quality scores for available providers
        provider_scores = await self._calculate_provider_quality_scores(
            request.task_type, task_analysis
        )
        
        # Generate cost-quality options
        options = self._generate_cost_quality_options(
            provider_scores, request, cost_preference
        )
        
        # Select optimal provider
        recommended_option = self._select_optimal_provider(
            options, user_prefs, cost_preference
        )
        
        # Generate reasoning
        reasoning = self._generate_recommendation_reasoning(
            recommended_option, task_analysis, provider_scores
        )
        
        return ProviderRecommendation(
            recommended_provider=recommended_option.provider,
            quality_tier=self._determine_quality_tier(recommended_option.quality_score),
            reasoning=reasoning,
            cost_estimate=recommended_option.cost_estimate,
            quality_score=recommended_option.quality_score,
            alternatives=options[:3],  # Top 3 alternatives
            user_choice_required=cost_preference == "user_choice",
            confidence=self._calculate_recommendation_confidence(recommended_option)
        )
    
    async def get_quality_comparison(
        self, 
        request: LLMRequest,
        providers: List[LLMProvider] = None
    ) -> Dict[LLMProvider, Dict[str, Any]]:
        """Get quality comparison across providers"""
        
        if providers is None:
            providers = list(LLMProvider)
        
        comparison = {}
        
        for provider in providers:
            if not self.multi_llm_system or provider not in self.multi_llm_system.providers:
                continue
            
            quality_score = self.quality_scores.get(
                (provider, request.task_type), 
                self._get_default_quality_score()
            )
            
            # Estimate cost and speed
            cost_estimate = self._estimate_cost(provider, request)
            speed_estimate = self._estimate_speed(provider, request)
            
            comparison[provider] = {
                'quality_score': quality_score.overall_score,
                'accuracy': quality_score.accuracy,
                'consistency': quality_score.consistency,
                'speed_score': quality_score.speed,
                'cost_efficiency': quality_score.cost_efficiency,
                'cost_estimate': cost_estimate,
                'speed_estimate': speed_estimate,
                'sample_size': quality_score.sample_size,
                'confidence': quality_score.confidence_interval,
                'recommendation': self._get_provider_recommendation_text(
                    provider, quality_score, cost_estimate
                )
            }
        
        return comparison
    
    async def record_user_feedback(self, feedback: UserFeedback):
        """Record user feedback to improve recommendations"""
        
        self.user_feedback_history.append(feedback)
        
        # Update quality scores based on feedback
        await self._update_quality_scores_from_feedback(feedback)
        
        # Update user preferences
        self._update_user_preferences_from_feedback(feedback)
        
        logger.info(f"Recorded feedback for {feedback.provider.value} from user {feedback.user_id}")
    
    async def get_user_quality_insights(self, user_id: str) -> Dict[str, Any]:
        """Get personalized quality insights for user"""
        
        user_feedback = [f for f in self.user_feedback_history if f.user_id == user_id]
        
        if not user_feedback:
            return {
                'total_interactions': 0,
                'average_satisfaction': 0.0,
                'preferred_providers': [],
                'quality_trends': {},
                'recommendations': []
            }
        
        # Calculate user-specific metrics
        avg_satisfaction = statistics.mean([f.satisfaction_rating for f in user_feedback])
        avg_quality = statistics.mean([f.quality_rating for f in user_feedback])
        
        # Find preferred providers
        provider_satisfaction = {}
        for feedback in user_feedback:
            if feedback.provider not in provider_satisfaction:
                provider_satisfaction[feedback.provider] = []
            provider_satisfaction[feedback.provider].append(feedback.satisfaction_rating)
        
        preferred_providers = sorted(
            provider_satisfaction.items(),
            key=lambda x: statistics.mean(x[1]),
            reverse=True
        )[:3]
        
        # Generate personalized recommendations
        recommendations = self._generate_personalized_recommendations(user_id, user_feedback)
        
        return {
            'total_interactions': len(user_feedback),
            'average_satisfaction': avg_satisfaction,
            'average_quality_rating': avg_quality,
            'preferred_providers': [
                {
                    'provider': provider.value,
                    'satisfaction': statistics.mean(ratings),
                    'usage_count': len(ratings)
                }
                for provider, ratings in preferred_providers
            ],
            'quality_trends': self._analyze_quality_trends(user_feedback),
            'recommendations': recommendations
        }
    
    def _initialize_quality_scores(self):
        """Initialize baseline quality scores for providers"""
        
        # Baseline quality scores based on general performance characteristics
        baseline_scores = {
            # OpenAI GPT models - high quality, moderate cost
            (LLMProvider.OPENAI, TaskType.TEXT_GENERATION): QualityScore(0.92, 0.90, 0.85, 0.75, 0.86, sample_size=1000),
            (LLMProvider.OPENAI, TaskType.SUMMARIZATION): QualityScore(0.94, 0.92, 0.85, 0.75, 0.87, sample_size=800),
            (LLMProvider.OPENAI, TaskType.CODE_GENERATION): QualityScore(0.90, 0.88, 0.85, 0.75, 0.85, sample_size=600),
            (LLMProvider.OPENAI, TaskType.ANALYSIS): QualityScore(0.91, 0.89, 0.85, 0.75, 0.85, sample_size=500),
            
            # Claude - highest quality, higher cost
            (LLMProvider.CLAUDE, TaskType.TEXT_GENERATION): QualityScore(0.95, 0.94, 0.80, 0.70, 0.85, sample_size=800),
            (LLMProvider.CLAUDE, TaskType.SUMMARIZATION): QualityScore(0.96, 0.95, 0.80, 0.70, 0.86, sample_size=700),
            (LLMProvider.CLAUDE, TaskType.ANALYSIS): QualityScore(0.97, 0.95, 0.80, 0.70, 0.86, sample_size=600),
            (LLMProvider.CLAUDE, TaskType.CODE_GENERATION): QualityScore(0.88, 0.86, 0.80, 0.70, 0.81, sample_size=400),
            
            # Gemini - good quality, competitive cost
            (LLMProvider.GEMINI, TaskType.TEXT_GENERATION): QualityScore(0.88, 0.86, 0.90, 0.85, 0.87, sample_size=600),
            (LLMProvider.GEMINI, TaskType.SUMMARIZATION): QualityScore(0.89, 0.87, 0.90, 0.85, 0.88, sample_size=500),
            (LLMProvider.GEMINI, TaskType.ANALYSIS): QualityScore(0.87, 0.85, 0.90, 0.85, 0.87, sample_size=400),
            
            # Groq - fast processing, good cost efficiency
            (LLMProvider.GROQ, TaskType.TEXT_GENERATION): QualityScore(0.85, 0.83, 0.95, 0.90, 0.88, sample_size=400),
            (LLMProvider.GROQ, TaskType.CODE_GENERATION): QualityScore(0.87, 0.85, 0.95, 0.90, 0.89, sample_size=300),
            
            # HuggingFace - variable quality, best cost
            (LLMProvider.HUGGINGFACE, TaskType.TEXT_GENERATION): QualityScore(0.75, 0.70, 0.70, 0.95, 0.78, sample_size=200),
            (LLMProvider.HUGGINGFACE, TaskType.CLASSIFICATION): QualityScore(0.80, 0.75, 0.70, 0.95, 0.80, sample_size=300),
        }
        
        self.quality_scores.update(baseline_scores)
    
    async def _analyze_task_requirements(self, request: LLMRequest) -> Dict[str, Any]:
        """Analyze task requirements for optimal provider selection"""
        
        complexity = self.task_complexity_analyzer.analyze_complexity(request)
        
        return {
            'task_type': request.task_type,
            'complexity': complexity,
            'prompt_length': len(request.prompt),
            'requires_accuracy': complexity in [TaskComplexity.COMPLEX, TaskComplexity.EXPERT],
            'requires_speed': request.max_tokens < 500,
            'context_dependent': bool(request.context),
            'specialized_domain': self._detect_specialized_domain(request.prompt)
        }
    
    def _get_user_preferences(self, user_id: str) -> UserPreferences:
        """Get or create user preferences"""
        
        if user_id not in self.user_preferences:
            self.user_preferences[user_id] = UserPreferences(user_id=user_id)
        
        return self.user_preferences[user_id]
    
    async def _calculate_provider_quality_scores(
        self, 
        task_type: TaskType, 
        task_analysis: Dict[str, Any]
    ) -> Dict[LLMProvider, QualityScore]:
        """Calculate quality scores for providers based on task"""
        
        provider_scores = {}
        
        for provider in LLMProvider:
            base_score = self.quality_scores.get(
                (provider, task_type),
                self._get_default_quality_score()
            )
            
            # Adjust score based on task analysis
            adjusted_score = self._adjust_score_for_task(base_score, task_analysis)
            provider_scores[provider] = adjusted_score
        
        return provider_scores
    
    def _generate_cost_quality_options(
        self,
        provider_scores: Dict[LLMProvider, QualityScore],
        request: LLMRequest,
        cost_preference: str
    ) -> List[CostQualityOption]:
        """Generate cost-quality trade-off options"""
        
        options = []
        
        for provider, quality_score in provider_scores.items():
            if not self.multi_llm_system or provider not in self.multi_llm_system.providers:
                continue
            
            cost_estimate = self._estimate_cost(provider, request)
            speed_estimate = self._estimate_speed(provider, request)
            
            # Generate pros and cons
            pros, cons = self._generate_pros_cons(provider, quality_score, cost_estimate)
            
            option = CostQualityOption(
                provider=provider,
                quality_score=quality_score.overall_score,
                cost_estimate=cost_estimate,
                speed_estimate=speed_estimate,
                description=self._generate_option_description(provider, quality_score),
                pros=pros,
                cons=cons
            )
            
            options.append(option)
        
        # Sort by quality score (descending)
        options.sort(key=lambda x: x.quality_score, reverse=True)
        
        return options
    
    def _select_optimal_provider(
        self,
        options: List[CostQualityOption],
        user_prefs: UserPreferences,
        cost_preference: str
    ) -> CostQualityOption:
        """Select optimal provider based on preferences"""
        
        if not options:
            return options[0] if options else None
        
        # Calculate weighted scores
        scored_options = []
        
        for option in options:
            # Normalize cost (lower is better)
            max_cost = max(opt.cost_estimate for opt in options)
            min_cost = min(opt.cost_estimate for opt in options)
            cost_score = 1 - ((option.cost_estimate - min_cost) / (max_cost - min_cost)) if max_cost > min_cost else 1.0
            
            # Calculate weighted score
            if cost_preference == "premium":
                weighted_score = option.quality_score * 0.8 + cost_score * 0.2
            elif cost_preference == "economy":
                weighted_score = option.quality_score * 0.4 + cost_score * 0.6
            else:  # balanced
                weighted_score = option.quality_score * 0.6 + cost_score * 0.4
            
            # Apply user preferences
            if option.provider in user_prefs.preferred_providers:
                weighted_score *= 1.1
            elif option.provider in user_prefs.avoided_providers:
                weighted_score *= 0.9
            
            scored_options.append((option, weighted_score))
        
        # Return highest scoring option
        scored_options.sort(key=lambda x: x[1], reverse=True)
        return scored_options[0][0]
    
    def _generate_recommendation_reasoning(
        self,
        recommended_option: CostQualityOption,
        task_analysis: Dict[str, Any],
        provider_scores: Dict[LLMProvider, QualityScore]
    ) -> str:
        """Generate human-readable reasoning for recommendation"""
        
        provider = recommended_option.provider
        quality_score = recommended_option.quality_score
        
        # Base reasoning
        if quality_score >= 0.9:
            quality_desc = "excellent quality"
        elif quality_score >= 0.8:
            quality_desc = "high quality"
        elif quality_score >= 0.7:
            quality_desc = "good quality"
        else:
            quality_desc = "acceptable quality"
        
        # Task-specific reasoning
        task_specific = ""
        if task_analysis['task_type'] == TaskType.CODE_GENERATION:
            task_specific = " for code generation tasks"
        elif task_analysis['task_type'] == TaskType.ANALYSIS:
            task_specific = " for analytical tasks"
        elif task_analysis['specialized_domain']:
            task_specific = f" for {task_analysis['specialized_domain']} content"
        
        # Cost reasoning
        cost_desc = ""
        if recommended_option.cost_estimate < 0.10:
            cost_desc = " with excellent cost efficiency"
        elif recommended_option.cost_estimate < 0.25:
            cost_desc = " at a reasonable cost"
        else:
            cost_desc = " (premium pricing for premium quality)"
        
        return f"Recommended {provider.value} for {quality_desc}{task_specific}{cost_desc}. " \
               f"Quality score: {quality_score:.1%}, estimated cost: ${recommended_option.cost_estimate:.2f}"
    
    def _determine_quality_tier(self, quality_score: float) -> QualityTier:
        """Determine quality tier from score"""
        if quality_score >= 0.9:
            return QualityTier.PREMIUM
        elif quality_score >= 0.8:
            return QualityTier.STANDARD
        else:
            return QualityTier.ECONOMY
    
    def _calculate_recommendation_confidence(self, option: CostQualityOption) -> float:
        """Calculate confidence in recommendation"""
        
        # Base confidence from quality score
        base_confidence = option.quality_score
        
        # Adjust based on sample size (if available)
        quality_key = (option.provider, TaskType.TEXT_GENERATION)  # Default task type
        if quality_key in self.quality_scores:
            sample_size = self.quality_scores[quality_key].sample_size
            if sample_size > 500:
                base_confidence *= 1.1
            elif sample_size < 100:
                base_confidence *= 0.9
        
        return min(1.0, base_confidence)
    
    def _get_default_quality_score(self) -> QualityScore:
        """Get default quality score for unknown provider-task combinations"""
        return QualityScore(0.75, 0.70, 0.75, 0.80, 0.75, sample_size=0)
    
    def _adjust_score_for_task(self, base_score: QualityScore, task_analysis: Dict[str, Any]) -> QualityScore:
        """Adjust quality score based on specific task requirements"""
        
        # Create adjusted score
        adjusted = QualityScore(
            accuracy=base_score.accuracy,
            consistency=base_score.consistency,
            speed=base_score.speed,
            cost_efficiency=base_score.cost_efficiency,
            overall_score=base_score.overall_score,
            confidence_interval=base_score.confidence_interval,
            sample_size=base_score.sample_size
        )
        
        # Adjust for complexity
        if task_analysis['complexity'] == TaskComplexity.EXPERT:
            adjusted.accuracy *= 1.1  # Boost accuracy importance
            adjusted.overall_score = (adjusted.accuracy * 0.5 + adjusted.consistency * 0.3 + 
                                    adjusted.speed * 0.1 + adjusted.cost_efficiency * 0.1)
        elif task_analysis['complexity'] == TaskComplexity.SIMPLE:
            adjusted.speed *= 1.1  # Boost speed importance
            adjusted.cost_efficiency *= 1.1  # Boost cost efficiency
            adjusted.overall_score = (adjusted.accuracy * 0.3 + adjusted.consistency * 0.2 + 
                                    adjusted.speed * 0.3 + adjusted.cost_efficiency * 0.2)
        
        # Adjust for specialized domains
        if task_analysis['specialized_domain']:
            adjusted.accuracy *= 1.05  # Slight accuracy boost for specialized content
        
        return adjusted
    
    def _estimate_cost(self, provider: LLMProvider, request: LLMRequest) -> float:
        """Estimate cost for provider and request"""
        
        # Base cost per 1000 tokens (approximate)
        base_costs = {
            LLMProvider.OPENAI: 0.002,
            LLMProvider.CLAUDE: 0.003,
            LLMProvider.GEMINI: 0.001,
            LLMProvider.GROQ: 0.0005,
            LLMProvider.HUGGINGFACE: 0.0001
        }
        
        base_cost = base_costs.get(provider, 0.002)
        estimated_tokens = len(request.prompt.split()) * 1.3 + request.max_tokens
        
        return (estimated_tokens / 1000) * base_cost
    
    def _estimate_speed(self, provider: LLMProvider, request: LLMRequest) -> str:
        """Estimate processing speed for provider"""
        
        # Speed estimates based on provider characteristics
        speed_estimates = {
            LLMProvider.GROQ: "Very Fast (1-2 seconds)",
            LLMProvider.GEMINI: "Fast (2-5 seconds)",
            LLMProvider.OPENAI: "Moderate (5-10 seconds)",
            LLMProvider.CLAUDE: "Moderate (5-15 seconds)",
            LLMProvider.HUGGINGFACE: "Variable (10-30 seconds)"
        }
        
        return speed_estimates.get(provider, "Moderate (5-10 seconds)")
    
    def _generate_pros_cons(
        self, 
        provider: LLMProvider, 
        quality_score: QualityScore, 
        cost_estimate: float
    ) -> Tuple[List[str], List[str]]:
        """Generate pros and cons for provider option"""
        
        pros = []
        cons = []
        
        # Quality-based pros/cons
        if quality_score.accuracy >= 0.9:
            pros.append("Excellent accuracy and reliability")
        elif quality_score.accuracy < 0.8:
            cons.append("Lower accuracy compared to premium options")
        
        if quality_score.speed >= 0.9:
            pros.append("Very fast processing")
        elif quality_score.speed < 0.7:
            cons.append("Slower processing times")
        
        # Cost-based pros/cons
        if cost_estimate < 0.10:
            pros.append("Excellent cost efficiency")
        elif cost_estimate > 0.25:
            cons.append("Higher cost per request")
        
        # Provider-specific characteristics
        provider_characteristics = {
            LLMProvider.CLAUDE: {
                'pros': ["Best for complex reasoning", "Excellent safety measures"],
                'cons': ["Higher cost", "Slower processing"]
            },
            LLMProvider.OPENAI: {
                'pros': ["Well-balanced performance", "Reliable and consistent"],
                'cons': ["Moderate cost", "Not the fastest option"]
            },
            LLMProvider.GROQ: {
                'pros': ["Extremely fast processing", "Good cost efficiency"],
                'cons': ["Limited model selection", "Newer provider"]
            },
            LLMProvider.GEMINI: {
                'pros': ["Good balance of speed and quality", "Competitive pricing"],
                'cons': ["Newer model", "Less specialized for some tasks"]
            },
            LLMProvider.HUGGINGFACE: {
                'pros': ["Open source models", "Very low cost"],
                'cons': ["Variable quality", "Requires more setup"]
            }
        }
        
        if provider in provider_characteristics:
            pros.extend(provider_characteristics[provider]['pros'])
            cons.extend(provider_characteristics[provider]['cons'])
        
        return pros, cons
    
    def _generate_option_description(self, provider: LLMProvider, quality_score: QualityScore) -> str:
        """Generate description for provider option"""
        
        descriptions = {
            LLMProvider.CLAUDE: f"Premium AI with {quality_score.accuracy:.1%} accuracy - best for complex analysis and reasoning tasks",
            LLMProvider.OPENAI: f"Reliable AI with {quality_score.accuracy:.1%} accuracy - well-balanced performance for most tasks",
            LLMProvider.GROQ: f"High-speed AI with {quality_score.accuracy:.1%} accuracy - optimized for fast processing",
            LLMProvider.GEMINI: f"Efficient AI with {quality_score.accuracy:.1%} accuracy - good balance of speed and quality",
            LLMProvider.HUGGINGFACE: f"Open-source AI with {quality_score.accuracy:.1%} accuracy - most cost-effective option"
        }
        
        return descriptions.get(provider, f"AI provider with {quality_score.accuracy:.1%} accuracy")
    
    def _detect_specialized_domain(self, prompt: str) -> Optional[str]:
        """Detect if prompt is from a specialized domain"""
        
        prompt_lower = prompt.lower()
        
        # Legal domain
        if any(term in prompt_lower for term in ['contract', 'legal', 'court', 'lawsuit', 'attorney', 'jurisdiction']):
            return "legal"
        
        # Medical domain
        if any(term in prompt_lower for term in ['patient', 'medical', 'diagnosis', 'treatment', 'symptoms', 'medication']):
            return "medical"
        
        # Technical domain
        if any(term in prompt_lower for term in ['code', 'programming', 'software', 'algorithm', 'database', 'api']):
            return "technical"
        
        # Financial domain
        if any(term in prompt_lower for term in ['financial', 'investment', 'revenue', 'profit', 'budget', 'accounting']):
            return "financial"
        
        return None
    
    async def _update_quality_scores_from_feedback(self, feedback: UserFeedback):
        """Update quality scores based on user feedback"""
        
        quality_key = (feedback.provider, feedback.task_type)
        
        if quality_key in self.quality_scores:
            current_score = self.quality_scores[quality_key]
            
            # Convert 1-5 rating to 0-1 score
            feedback_accuracy = (feedback.quality_rating - 1) / 4
            feedback_speed = (feedback.speed_rating - 1) / 4
            
            # Update with weighted average (give more weight to recent feedback)
            weight = 0.1  # 10% weight to new feedback
            
            current_score.accuracy = (current_score.accuracy * (1 - weight) + 
                                    feedback_accuracy * weight)
            current_score.speed = (current_score.speed * (1 - weight) + 
                                 feedback_speed * weight)
            
            # Recalculate overall score
            current_score.overall_score = (
                current_score.accuracy * 0.4 +
                current_score.consistency * 0.3 +
                current_score.speed * 0.2 +
                current_score.cost_efficiency * 0.1
            )
            
            current_score.sample_size += 1
    
    def _update_user_preferences_from_feedback(self, feedback: UserFeedback):
        """Update user preferences based on feedback"""
        
        user_prefs = self._get_user_preferences(feedback.user_id)
        
        # If user rates quality highly, increase quality priority
        if feedback.quality_rating >= 4.0:
            user_prefs.quality_priority = min(1.0, user_prefs.quality_priority + 0.05)
            user_prefs.cost_sensitivity = max(0.0, user_prefs.cost_sensitivity - 0.05)
        
        # If user rates speed highly, increase speed priority
        if feedback.speed_rating >= 4.0:
            user_prefs.speed_priority = min(1.0, user_prefs.speed_priority + 0.05)
        
        # Track preferred providers
        if feedback.satisfaction_rating >= 4.0:
            if feedback.provider not in user_prefs.preferred_providers:
                user_prefs.preferred_providers.append(feedback.provider)
        elif feedback.satisfaction_rating <= 2.0:
            if feedback.provider not in user_prefs.avoided_providers:
                user_prefs.avoided_providers.append(feedback.provider)
    
    def _generate_personalized_recommendations(
        self, 
        user_id: str, 
        user_feedback: List[UserFeedback]
    ) -> List[str]:
        """Generate personalized recommendations based on user history"""
        
        recommendations = []
        
        # Analyze user patterns
        avg_quality_rating = statistics.mean([f.quality_rating for f in user_feedback])
        avg_speed_rating = statistics.mean([f.speed_rating for f in user_feedback])
        
        if avg_quality_rating >= 4.0:
            recommendations.append("You value high quality - consider using Claude for important tasks")
        
        if avg_speed_rating >= 4.0:
            recommendations.append("You prefer fast processing - Groq is optimized for speed")
        
        # Provider-specific recommendations
        provider_ratings = {}
        for feedback in user_feedback:
            if feedback.provider not in provider_ratings:
                provider_ratings[feedback.provider] = []
            provider_ratings[feedback.provider].append(feedback.satisfaction_rating)
        
        for provider, ratings in provider_ratings.items():
            avg_rating = statistics.mean(ratings)
            if avg_rating >= 4.0:
                recommendations.append(f"You've had great results with {provider.value} - consider it for similar tasks")
        
        return recommendations
    
    def _analyze_quality_trends(self, user_feedback: List[UserFeedback]) -> Dict[str, Any]:
        """Analyze quality trends from user feedback"""
        
        if len(user_feedback) < 2:
            return {}
        
        # Sort by timestamp
        sorted_feedback = sorted(user_feedback, key=lambda x: x.timestamp)
        
        # Calculate trends
        recent_feedback = sorted_feedback[-5:]  # Last 5 interactions
        older_feedback = sorted_feedback[:-5] if len(sorted_feedback) > 5 else []
        
        if older_feedback:
            recent_quality = statistics.mean([f.quality_rating for f in recent_feedback])
            older_quality = statistics.mean([f.quality_rating for f in older_feedback])
            
            quality_trend = "improving" if recent_quality > older_quality else "stable" if recent_quality == older_quality else "declining"
        else:
            quality_trend = "stable"
        
        return {
            'quality_trend': quality_trend,
            'recent_average_quality': statistics.mean([f.quality_rating for f in recent_feedback]),
            'recent_average_satisfaction': statistics.mean([f.satisfaction_rating for f in recent_feedback])
        }
    
    def _get_provider_recommendation_text(
        self, 
        provider: LLMProvider, 
        quality_score: QualityScore, 
        cost_estimate: float
    ) -> str:
        """Get recommendation text for provider"""
        
        if quality_score.overall_score >= 0.9 and cost_estimate <= 0.15:
            return "Excellent choice - high quality at reasonable cost"
        elif quality_score.overall_score >= 0.9:
            return "Premium option - highest quality available"
        elif cost_estimate <= 0.10:
            return "Budget-friendly option - good value for money"
        elif quality_score.speed >= 0.9:
            return "Speed-optimized option - fastest processing"
        else:
            return "Balanced option - good all-around performance"


class TaskComplexityAnalyzer:
    """Analyzes task complexity to inform provider selection"""
    
    def analyze_complexity(self, request: LLMRequest) -> TaskComplexity:
        """Analyze the complexity of a task"""
        
        prompt = request.prompt.lower()
        
        # Expert level indicators
        expert_indicators = [
            'analyze', 'evaluate', 'compare', 'critique', 'synthesize',
            'research', 'investigate', 'complex', 'detailed analysis'
        ]
        
        # Complex level indicators
        complex_indicators = [
            'explain', 'describe', 'summarize', 'create', 'generate',
            'write', 'compose', 'develop'
        ]
        
        # Simple level indicators
        simple_indicators = [
            'list', 'name', 'what is', 'define', 'translate', 'convert'
        ]
        
        # Count indicators
        expert_count = sum(1 for indicator in expert_indicators if indicator in prompt)
        complex_count = sum(1 for indicator in complex_indicators if indicator in prompt)
        simple_count = sum(1 for indicator in simple_indicators if indicator in prompt)
        
        # Consider prompt length
        prompt_length = len(request.prompt.split())
        
        # Determine complexity
        if expert_count > 0 or prompt_length > 200:
            return TaskComplexity.EXPERT
        elif complex_count > 0 or prompt_length > 100:
            return TaskComplexity.COMPLEX
        elif simple_count > 0 or prompt_length < 50:
            return TaskComplexity.SIMPLE
        else:
            return TaskComplexity.MODERATE


# Example usage and testing
async def demo_quality_optimization_engine():
    """Demonstrate the quality optimization engine"""
    print("🎯 Quality Optimization Engine Demo")
    print("=" * 50)
    
    engine = QualityOptimizationEngine()
    
    # Create sample request
    request = LLMRequest(
        prompt="Analyze the legal implications of this contract clause and provide recommendations for improvement.",
        task_type=TaskType.ANALYSIS,
        max_tokens=500
    )
    
    print(f"\n📝 Sample Request:")
    print(f"   Task: {request.task_type.value}")
    print(f"   Prompt: {request.prompt[:80]}...")
    
    # Get recommendation
    print(f"\n🎯 Provider Recommendation:")
    recommendation = await engine.get_optimal_provider_recommendation(
        request, "demo_user", "balanced"
    )
    
    print(f"   Recommended: {recommendation.recommended_provider.value}")
    print(f"   Quality Tier: {recommendation.quality_tier.value}")
    print(f"   Quality Score: {recommendation.quality_score:.1%}")
    print(f"   Cost Estimate: ${recommendation.cost_estimate:.3f}")
    print(f"   Reasoning: {recommendation.reasoning}")
    
    # Show alternatives
    if recommendation.alternatives:
        print(f"\n🔄 Alternative Options:")
        for i, alt in enumerate(recommendation.alternatives[:2], 1):
            print(f"   {i}. {alt.provider.value}: {alt.quality_score:.1%} quality, ${alt.cost_estimate:.3f}")
            print(f"      {alt.description}")
    
    # Get quality comparison
    print(f"\n📊 Quality Comparison:")
    comparison = await engine.get_quality_comparison(request)
    
    for provider, metrics in comparison.items():
        print(f"   {provider.value}:")
        print(f"     Quality: {metrics['quality_score']:.1%}")
        print(f"     Cost: ${metrics['cost_estimate']:.3f}")
        print(f"     Speed: {metrics['speed_estimate']}")
        print(f"     Recommendation: {metrics['recommendation']}")

if __name__ == "__main__":
    asyncio.run(demo_quality_optimization_engine())