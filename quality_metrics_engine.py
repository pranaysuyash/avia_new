"""
Advanced Quality Metrics Engine
Sophisticated scoring algorithms and metric calculations for quality assessment
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import statistics
from collections import defaultdict, Counter
import json

from quality_assessment_system import QualityAssessmentResult, QualityDimension, QualityLevel

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of quality metrics"""
    ACCURACY_SCORE = "accuracy_score"
    COMPLETENESS_RATIO = "completeness_ratio"
    CONSISTENCY_INDEX = "consistency_index"
    MEDICAL_COMPLIANCE = "medical_compliance"
    SEMANTIC_QUALITY = "semantic_quality"
    ENGAGEMENT_SCORE = "engagement_score"
    SAFETY_INDICATOR = "safety_indicator"
    EFFICIENCY_METRIC = "efficiency_metric"
    PATIENT_SATISFACTION = "patient_satisfaction"
    CLINICAL_RELEVANCE = "clinical_relevance"


class TrendDirection(Enum):
    """Quality trend directions"""
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    VOLATILE = "volatile"


@dataclass
class QualityTrend:
    """Quality trend analysis result"""
    dimension: QualityDimension
    trend_direction: TrendDirection
    trend_strength: float  # 0-1, how strong the trend is
    slope: float  # Rate of change
    r_squared: float  # Correlation coefficient
    prediction_confidence: float
    projected_score_30_days: float
    analysis_period_days: int
    data_points: int


@dataclass
class BenchmarkComparison:
    """Comparison against benchmarks"""
    dimension: QualityDimension
    current_score: float
    industry_benchmark: float
    percentile_rank: float
    gap_analysis: str
    improvement_potential: float
    competitive_position: str  # "leading", "competitive", "lagging"


@dataclass
class QualityMetricsSummary:
    """Comprehensive quality metrics summary"""
    overall_quality_index: float
    dimension_scores: Dict[QualityDimension, float]
    trend_analysis: List[QualityTrend]
    benchmark_comparisons: List[BenchmarkComparison]
    risk_indicators: Dict[str, float]
    improvement_opportunities: List[str]
    quality_volatility: float
    metric_reliability_score: float
    assessment_confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class QualityMetricsEngine:
    """Advanced engine for calculating and analyzing quality metrics"""
    
    def __init__(self):
        self.industry_benchmarks = self._load_industry_benchmarks()
        self.weight_configurations = self._load_weight_configurations()
        self.risk_thresholds = self._load_risk_thresholds()
        self.scoring_models = self._initialize_scoring_models()
        
    def _load_industry_benchmarks(self) -> Dict[str, Dict[QualityDimension, float]]:
        """Load industry benchmarks for comparison"""
        return {
            "medical_transcription": {
                QualityDimension.ACCURACY: 92.0,
                QualityDimension.COMPLETENESS: 88.0,
                QualityDimension.CONSISTENCY: 85.0,
                QualityDimension.MEDICAL_ACCURACY: 94.0,
                QualityDimension.CLINICAL_RELEVANCE: 87.0,
                QualityDimension.HIPAA_COMPLIANCE: 98.0,
                QualityDimension.SEMANTIC_COHERENCE: 83.0
            },
            "general_transcription": {
                QualityDimension.ACCURACY: 88.0,
                QualityDimension.COMPLETENESS: 85.0,
                QualityDimension.CONSISTENCY: 82.0,
                QualityDimension.SEMANTIC_COHERENCE: 80.0,
                QualityDimension.CLARITY: 85.0
            },
            "legal_transcription": {
                QualityDimension.ACCURACY: 96.0,
                QualityDimension.COMPLETENESS: 92.0,
                QualityDimension.CONSISTENCY: 90.0,
                QualityDimension.SEMANTIC_COHERENCE: 85.0
            }
        }
    
    def _load_weight_configurations(self) -> Dict[str, Dict[QualityDimension, float]]:
        """Load weight configurations for different contexts"""
        return {
            "medical_critical": {
                QualityDimension.MEDICAL_ACCURACY: 0.35,
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.HIPAA_COMPLIANCE: 0.20,
                QualityDimension.COMPLETENESS: 0.15,
                QualityDimension.CONSISTENCY: 0.05
            },
            "medical_standard": {
                QualityDimension.MEDICAL_ACCURACY: 0.25,
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.COMPLETENESS: 0.20,
                QualityDimension.CONSISTENCY: 0.15,
                QualityDimension.SEMANTIC_COHERENCE: 0.10,
                QualityDimension.HIPAA_COMPLIANCE: 0.05
            },
            "general": {
                QualityDimension.ACCURACY: 0.30,
                QualityDimension.COMPLETENESS: 0.25,
                QualityDimension.SEMANTIC_COHERENCE: 0.20,
                QualityDimension.CONSISTENCY: 0.15,
                QualityDimension.CLARITY: 0.10
            },
            "research": {
                QualityDimension.ACCURACY: 0.40,
                QualityDimension.COMPLETENESS: 0.30,
                QualityDimension.CONSISTENCY: 0.20,
                QualityDimension.SEMANTIC_COHERENCE: 0.10
            }
        }
    
    def _load_risk_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Load risk thresholds for different quality aspects"""
        return {
            "accuracy_risk": {
                "high": 70.0,    # Below 70% is high risk
                "medium": 85.0,  # 70-85% is medium risk
                "low": 90.0      # Above 90% is low risk
            },
            "medical_accuracy_risk": {
                "high": 85.0,
                "medium": 92.0,
                "low": 95.0
            },
            "completeness_risk": {
                "high": 75.0,
                "medium": 85.0,
                "low": 90.0
            },
            "hipaa_compliance_risk": {
                "high": 95.0,
                "medium": 98.0,
                "low": 99.0
            }
        }
    
    def _initialize_scoring_models(self) -> Dict[str, Any]:
        """Initialize advanced scoring models"""
        return {
            "weighted_harmonic_mean": self._weighted_harmonic_mean,
            "gaussian_weighted": self._gaussian_weighted_score,
            "risk_adjusted_score": self._risk_adjusted_score,
            "percentile_based": self._percentile_based_score,
            "composite_index": self._composite_quality_index
        }
    
    def calculate_comprehensive_metrics(
        self,
        quality_results: List[QualityAssessmentResult],
        context: str = "medical_standard",
        industry_type: str = "medical_transcription"
    ) -> QualityMetricsSummary:
        """Calculate comprehensive quality metrics from assessment results"""
        
        if not quality_results:
            raise ValueError("No quality results provided for metrics calculation")
        
        logger.info(f"Calculating metrics for {len(quality_results)} quality assessments")
        
        # Extract dimension scores over time
        dimension_time_series = self._extract_dimension_time_series(quality_results)
        
        # Calculate overall quality index
        overall_index = self._calculate_overall_quality_index(
            quality_results, context
        )
        
        # Calculate dimension averages
        dimension_scores = self._calculate_dimension_averages(dimension_time_series)
        
        # Perform trend analysis
        trend_analysis = self._perform_trend_analysis(dimension_time_series)
        
        # Compare against benchmarks
        benchmark_comparisons = self._compare_against_benchmarks(
            dimension_scores, industry_type
        )
        
        # Calculate risk indicators
        risk_indicators = self._calculate_risk_indicators(
            quality_results, dimension_scores
        )
        
        # Identify improvement opportunities
        improvement_opportunities = self._identify_improvement_opportunities(
            quality_results, benchmark_comparisons, trend_analysis
        )
        
        # Calculate quality volatility
        quality_volatility = self._calculate_quality_volatility(quality_results)
        
        # Calculate metric reliability
        metric_reliability = self._calculate_metric_reliability(quality_results)
        
        # Calculate assessment confidence
        assessment_confidence = self._calculate_assessment_confidence(quality_results)
        
        return QualityMetricsSummary(
            overall_quality_index=overall_index,
            dimension_scores=dimension_scores,
            trend_analysis=trend_analysis,
            benchmark_comparisons=benchmark_comparisons,
            risk_indicators=risk_indicators,
            improvement_opportunities=improvement_opportunities,
            quality_volatility=quality_volatility,
            metric_reliability_score=metric_reliability,
            assessment_confidence=assessment_confidence
        )
    
    def _extract_dimension_time_series(
        self, 
        quality_results: List[QualityAssessmentResult]
    ) -> Dict[QualityDimension, List[Tuple[datetime, float]]]:
        """Extract time series data for each quality dimension"""
        dimension_series = defaultdict(list)
        
        for result in sorted(quality_results, key=lambda x: x.assessment_timestamp):
            timestamp = result.assessment_timestamp
            for dimension, metric in result.dimension_scores.items():
                dimension_series[dimension].append((timestamp, metric.score))
        
        return dict(dimension_series)
    
    def _calculate_overall_quality_index(
        self,
        quality_results: List[QualityAssessmentResult],
        context: str
    ) -> float:
        """Calculate overall quality index using advanced scoring"""
        weights = self.weight_configurations.get(context, self.weight_configurations["general"])
        
        # Use multiple scoring models and combine
        scores = []
        
        for result in quality_results:
            dimension_scores = {dim: metric.score for dim, metric in result.dimension_scores.items()}
            
            # Calculate weighted harmonic mean (penalizes low scores more)
            harmonic_score = self._weighted_harmonic_mean(dimension_scores, weights)
            scores.append(harmonic_score)
            
            # Calculate Gaussian-weighted score (emphasizes consistency)
            gaussian_score = self._gaussian_weighted_score(dimension_scores, weights)
            scores.append(gaussian_score)
            
            # Calculate risk-adjusted score
            risk_adjusted = self._risk_adjusted_score(dimension_scores, weights)
            scores.append(risk_adjusted)
        
        # Combined index using geometric mean for robustness
        if scores:
            # Filter out any invalid scores
            valid_scores = [s for s in scores if s > 0]
            if valid_scores:
                return statistics.geometric_mean(valid_scores)
        
        return 0.0
    
    def _weighted_harmonic_mean(
        self, 
        scores: Dict[QualityDimension, float], 
        weights: Dict[QualityDimension, float]
    ) -> float:
        """Calculate weighted harmonic mean (penalizes low scores)"""
        weighted_sum_reciprocals = 0.0
        total_weight = 0.0
        
        for dimension, score in scores.items():
            if dimension in weights and score > 0:
                weight = weights[dimension]
                weighted_sum_reciprocals += weight / score
                total_weight += weight
        
        if total_weight > 0 and weighted_sum_reciprocals > 0:
            return total_weight / weighted_sum_reciprocals
        
        return 0.0
    
    def _gaussian_weighted_score(
        self,
        scores: Dict[QualityDimension, float],
        weights: Dict[QualityDimension, float]
    ) -> float:
        """Calculate score using Gaussian weighting (emphasizes consistency)"""
        weighted_sum = 0.0
        total_weight = 0.0
        
        # Calculate mean and std of scores
        score_values = list(scores.values())
        if len(score_values) < 2:
            return sum(score_values) if score_values else 0.0
        
        mean_score = statistics.mean(score_values)
        std_score = statistics.stdev(score_values)
        
        for dimension, score in scores.items():
            if dimension in weights:
                weight = weights[dimension]
                
                # Apply Gaussian penalty for scores far from mean
                if std_score > 0:
                    deviation_penalty = np.exp(-((score - mean_score) ** 2) / (2 * std_score ** 2))
                    adjusted_weight = weight * deviation_penalty
                else:
                    adjusted_weight = weight
                
                weighted_sum += score * adjusted_weight
                total_weight += adjusted_weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _risk_adjusted_score(
        self,
        scores: Dict[QualityDimension, float],
        weights: Dict[QualityDimension, float]
    ) -> float:
        """Calculate risk-adjusted quality score"""
        risk_penalties = {}
        
        for dimension, score in scores.items():
            # Apply risk penalties based on thresholds
            penalty = 1.0  # No penalty by default
            
            if dimension == QualityDimension.MEDICAL_ACCURACY:
                thresholds = self.risk_thresholds["medical_accuracy_risk"]
            elif dimension == QualityDimension.HIPAA_COMPLIANCE:
                thresholds = self.risk_thresholds["hipaa_compliance_risk"]
            elif dimension == QualityDimension.ACCURACY:
                thresholds = self.risk_thresholds["accuracy_risk"]
            elif dimension == QualityDimension.COMPLETENESS:
                thresholds = self.risk_thresholds["completeness_risk"]
            else:
                thresholds = self.risk_thresholds["accuracy_risk"]  # Default
            
            if score < thresholds["high"]:
                penalty = 0.7  # High risk penalty
            elif score < thresholds["medium"]:
                penalty = 0.85  # Medium risk penalty
            elif score < thresholds["low"]:
                penalty = 0.95  # Low risk penalty
            
            risk_penalties[dimension] = penalty
        
        # Apply risk-adjusted weights
        weighted_sum = 0.0
        total_weight = 0.0
        
        for dimension, score in scores.items():
            if dimension in weights:
                weight = weights[dimension] * risk_penalties.get(dimension, 1.0)
                weighted_sum += score * weight
                total_weight += weight
        
        return weighted_sum / total_weight if total_weight > 0 else 0.0
    
    def _percentile_based_score(
        self,
        scores: Dict[QualityDimension, float],
        historical_scores: Optional[List[Dict[QualityDimension, float]]] = None
    ) -> float:
        """Calculate percentile-based score relative to historical performance"""
        if not historical_scores:
            return statistics.mean(scores.values()) if scores else 0.0
        
        percentile_scores = {}
        
        for dimension, current_score in scores.items():
            # Get historical scores for this dimension
            historical_dim_scores = [
                hist_scores.get(dimension, 0) for hist_scores in historical_scores
                if dimension in hist_scores
            ]
            
            if historical_dim_scores:
                # Calculate percentile rank
                sorted_scores = sorted(historical_dim_scores)
                rank = sum(1 for score in sorted_scores if score <= current_score)
                percentile = (rank / len(sorted_scores)) * 100
                percentile_scores[dimension] = percentile
            else:
                percentile_scores[dimension] = 50  # Median if no history
        
        return statistics.mean(percentile_scores.values()) if percentile_scores else 0.0
    
    def _composite_quality_index(
        self,
        scores: Dict[QualityDimension, float],
        weights: Dict[QualityDimension, float]
    ) -> float:
        """Calculate composite quality index using multiple methods"""
        # Combine multiple scoring approaches
        weighted_avg = sum(
            scores[dim] * weights.get(dim, 0) 
            for dim in scores if dim in weights
        ) / sum(weights.get(dim, 0) for dim in scores if dim in weights)
        
        harmonic_mean = self._weighted_harmonic_mean(scores, weights)
        risk_adjusted = self._risk_adjusted_score(scores, weights)
        
        # Geometric mean of the three approaches for robustness
        methods = [s for s in [weighted_avg, harmonic_mean, risk_adjusted] if s > 0]
        
        if methods:
            return statistics.geometric_mean(methods)
        
        return 0.0
    
    def _calculate_dimension_averages(
        self,
        dimension_time_series: Dict[QualityDimension, List[Tuple[datetime, float]]]
    ) -> Dict[QualityDimension, float]:
        """Calculate average scores for each dimension"""
        averages = {}
        
        for dimension, time_series in dimension_time_series.items():
            scores = [score for _, score in time_series]
            if scores:
                # Use weighted average, giving more weight to recent scores
                weights = np.linspace(0.5, 1.0, len(scores))  # More recent = higher weight
                averages[dimension] = np.average(scores, weights=weights)
            else:
                averages[dimension] = 0.0
        
        return averages
    
    def _perform_trend_analysis(
        self,
        dimension_time_series: Dict[QualityDimension, List[Tuple[datetime, float]]]
    ) -> List[QualityTrend]:
        """Perform trend analysis for each quality dimension"""
        trends = []
        
        for dimension, time_series in dimension_time_series.items():
            if len(time_series) < 3:
                # Not enough data for trend analysis
                continue
            
            # Extract timestamps and scores
            timestamps = [t.timestamp() for t, _ in time_series]
            scores = [score for _, score in time_series]
            
            # Normalize timestamps to days from first measurement
            min_timestamp = min(timestamps)
            days = [(t - min_timestamp) / 86400 for t in timestamps]  # Convert to days
            
            # Linear regression for trend
            if len(days) >= 2:
                slope, intercept, r_value, _, _ = self._linear_regression(days, scores)
                r_squared = r_value ** 2
                
                # Determine trend direction and strength
                if abs(slope) < 0.1:
                    trend_direction = TrendDirection.STABLE
                    trend_strength = 1 - abs(slope) / 1.0  # Stability strength
                elif slope > 0:
                    trend_direction = TrendDirection.IMPROVING
                    trend_strength = min(slope / 2.0, 1.0)  # Normalize to 0-1
                else:
                    trend_direction = TrendDirection.DECLINING
                    trend_strength = min(abs(slope) / 2.0, 1.0)
                
                # Check for volatility
                score_std = statistics.stdev(scores) if len(scores) > 1 else 0
                if score_std > 10:  # High volatility threshold
                    trend_direction = TrendDirection.VOLATILE
                    trend_strength = score_std / 20.0  # Volatility strength
                
                # Project score 30 days out
                current_day = days[-1]
                projected_score_30_days = slope * (current_day + 30) + intercept
                projected_score_30_days = max(0, min(100, projected_score_30_days))
                
                # Calculate prediction confidence based on R-squared and data points
                base_confidence = r_squared
                data_confidence = min(len(time_series) / 10.0, 1.0)  # More data = higher confidence
                prediction_confidence = (base_confidence + data_confidence) / 2.0
                
                trends.append(QualityTrend(
                    dimension=dimension,
                    trend_direction=trend_direction,
                    trend_strength=trend_strength,
                    slope=slope,
                    r_squared=r_squared,
                    prediction_confidence=prediction_confidence,
                    projected_score_30_days=projected_score_30_days,
                    analysis_period_days=int(max(days) - min(days)),
                    data_points=len(time_series)
                ))
        
        return trends
    
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float, float, float, float]:
        """Simple linear regression implementation"""
        n = len(x)
        if n < 2:
            return 0.0, 0.0, 0.0, 0.0, 0.0
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0, y_mean, 0.0, 0.0, 0.0
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # Calculate correlation coefficient
        y_pred = [slope * x[i] + intercept for i in range(n)]
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        ss_tot = sum((y[i] - y_mean) ** 2 for i in range(n))
        
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        r_value = np.sqrt(max(0, r_squared)) * (1 if slope >= 0 else -1)
        
        return slope, intercept, r_value, 0.0, 0.0  # p_value and std_err not calculated
    
    def _compare_against_benchmarks(
        self,
        dimension_scores: Dict[QualityDimension, float],
        industry_type: str
    ) -> List[BenchmarkComparison]:
        """Compare scores against industry benchmarks"""
        comparisons = []
        benchmarks = self.industry_benchmarks.get(industry_type, {})
        
        for dimension, current_score in dimension_scores.items():
            if dimension not in benchmarks:
                continue
                
            benchmark_score = benchmarks[dimension]
            gap = current_score - benchmark_score
            gap_percentage = (gap / benchmark_score) * 100 if benchmark_score > 0 else 0
            
            # Estimate percentile rank (simplified)
            if gap_percentage > 15:
                percentile_rank = 90.0
                competitive_position = "leading"
            elif gap_percentage > 5:
                percentile_rank = 75.0
                competitive_position = "competitive"
            elif gap_percentage > -5:
                percentile_rank = 50.0
                competitive_position = "competitive"
            elif gap_percentage > -15:
                percentile_rank = 25.0
                competitive_position = "lagging"
            else:
                percentile_rank = 10.0
                competitive_position = "lagging"
            
            # Calculate improvement potential
            max_possible_improvement = 100 - current_score
            improvement_potential = max_possible_improvement * 0.7  # Assume 70% of gap is achievable
            
            # Generate gap analysis
            if gap > 0:
                gap_analysis = f"Exceeds benchmark by {gap:.1f} points ({gap_percentage:.1f}%)"
            else:
                gap_analysis = f"Below benchmark by {abs(gap):.1f} points ({abs(gap_percentage):.1f}%)"
            
            comparisons.append(BenchmarkComparison(
                dimension=dimension,
                current_score=current_score,
                industry_benchmark=benchmark_score,
                percentile_rank=percentile_rank,
                gap_analysis=gap_analysis,
                improvement_potential=improvement_potential,
                competitive_position=competitive_position
            ))
        
        return comparisons
    
    def _calculate_risk_indicators(
        self,
        quality_results: List[QualityAssessmentResult],
        dimension_scores: Dict[QualityDimension, float]
    ) -> Dict[str, float]:
        """Calculate various risk indicators"""
        risk_indicators = {}
        
        # Overall quality risk
        overall_scores = [result.overall_score for result in quality_results]
        if overall_scores:
            avg_overall = statistics.mean(overall_scores)
            if avg_overall < 70:
                risk_indicators["overall_quality_risk"] = 0.9  # High risk
            elif avg_overall < 85:
                risk_indicators["overall_quality_risk"] = 0.6  # Medium risk
            else:
                risk_indicators["overall_quality_risk"] = 0.2  # Low risk
        
        # Medical accuracy risk (critical for medical transcriptions)
        if QualityDimension.MEDICAL_ACCURACY in dimension_scores:
            medical_score = dimension_scores[QualityDimension.MEDICAL_ACCURACY]
            if medical_score < 85:
                risk_indicators["medical_accuracy_risk"] = 0.95
            elif medical_score < 92:
                risk_indicators["medical_accuracy_risk"] = 0.7
            else:
                risk_indicators["medical_accuracy_risk"] = 0.1
        
        # HIPAA compliance risk
        if QualityDimension.HIPAA_COMPLIANCE in dimension_scores:
            hipaa_score = dimension_scores[QualityDimension.HIPAA_COMPLIANCE]
            if hipaa_score < 95:
                risk_indicators["hipaa_compliance_risk"] = 0.9
            elif hipaa_score < 98:
                risk_indicators["hipaa_compliance_risk"] = 0.5
            else:
                risk_indicators["hipaa_compliance_risk"] = 0.1
        
        # Consistency risk (based on score variance)
        all_dimension_scores = []
        for result in quality_results:
            for metric in result.dimension_scores.values():
                all_dimension_scores.append(metric.score)
        
        if len(all_dimension_scores) > 1:
            score_variance = statistics.variance(all_dimension_scores)
            if score_variance > 200:  # High variance
                risk_indicators["consistency_risk"] = 0.8
            elif score_variance > 100:
                risk_indicators["consistency_risk"] = 0.5
            else:
                risk_indicators["consistency_risk"] = 0.2
        
        # Trend risk (declining performance)
        recent_results = sorted(quality_results, key=lambda x: x.assessment_timestamp)[-5:]
        if len(recent_results) >= 3:
            recent_scores = [r.overall_score for r in recent_results]
            if len(recent_scores) >= 2:
                # Simple trend calculation
                first_half = statistics.mean(recent_scores[:len(recent_scores)//2])
                second_half = statistics.mean(recent_scores[len(recent_scores)//2:])
                trend_change = second_half - first_half
                
                if trend_change < -5:  # Declining trend
                    risk_indicators["performance_trend_risk"] = 0.8
                elif trend_change < -2:
                    risk_indicators["performance_trend_risk"] = 0.5
                else:
                    risk_indicators["performance_trend_risk"] = 0.2
        
        return risk_indicators
    
    def _identify_improvement_opportunities(
        self,
        quality_results: List[QualityAssessmentResult],
        benchmark_comparisons: List[BenchmarkComparison],
        trend_analysis: List[QualityTrend]
    ) -> List[str]:
        """Identify specific improvement opportunities"""
        opportunities = []
        
        # Opportunities based on benchmark gaps
        for comparison in benchmark_comparisons:
            if comparison.current_score < comparison.industry_benchmark:
                gap = comparison.industry_benchmark - comparison.current_score
                if gap > 10:
                    opportunities.append(
                        f"High-impact opportunity: Improve {comparison.dimension.value.replace('_', ' ')} "
                        f"by {gap:.1f} points to reach industry benchmark"
                    )
                elif gap > 5:
                    opportunities.append(
                        f"Medium-impact opportunity: Close {gap:.1f} point gap in "
                        f"{comparison.dimension.value.replace('_', ' ')}"
                    )
        
        # Opportunities based on declining trends
        for trend in trend_analysis:
            if trend.trend_direction == TrendDirection.DECLINING and trend.trend_strength > 0.5:
                opportunities.append(
                    f"Urgent: Address declining trend in {trend.dimension.value.replace('_', ' ')} "
                    f"(projected to reach {trend.projected_score_30_days:.1f} in 30 days)"
                )
        
        # Opportunities based on common issues
        all_suggestions = []
        for result in quality_results:
            for metric in result.dimension_scores.values():
                all_suggestions.extend(metric.suggestions)
        
        # Count frequency of suggestions
        suggestion_counts = Counter(all_suggestions)
        common_issues = suggestion_counts.most_common(5)
        
        for suggestion, count in common_issues:
            if count >= len(quality_results) * 0.3:  # Appears in 30% or more of assessments
                opportunities.append(
                    f"Systematic improvement needed: {suggestion} "
                    f"(identified in {count}/{len(quality_results)} assessments)"
                )
        
        # Opportunities based on low-hanging fruit (easy wins)
        dimension_scores = {}
        for result in quality_results:
            for dimension, metric in result.dimension_scores.items():
                if dimension not in dimension_scores:
                    dimension_scores[dimension] = []
                dimension_scores[dimension].append(metric.score)
        
        for dimension, scores in dimension_scores.items():
            avg_score = statistics.mean(scores)
            if 70 < avg_score < 85:  # Moderate performance with improvement potential
                opportunities.append(
                    f"Quick win opportunity: {dimension.value.replace('_', ' ')} "
                    f"currently at {avg_score:.1f}% with potential for significant improvement"
                )
        
        return opportunities[:10]  # Limit to top 10 opportunities
    
    def _calculate_quality_volatility(self, quality_results: List[QualityAssessmentResult]) -> float:
        """Calculate quality volatility (consistency over time)"""
        if len(quality_results) < 2:
            return 0.0
        
        overall_scores = [result.overall_score for result in quality_results]
        
        # Calculate coefficient of variation (CV)
        mean_score = statistics.mean(overall_scores)
        std_score = statistics.stdev(overall_scores)
        
        if mean_score > 0:
            cv = std_score / mean_score
            return min(cv * 100, 100)  # Convert to percentage and cap at 100
        
        return 0.0
    
    def _calculate_metric_reliability_score(self, quality_results: List[QualityAssessmentResult]) -> float:
        """Calculate reliability score for the metrics"""
        if not quality_results:
            return 0.0
        
        # Factors affecting reliability
        reliability_factors = []
        
        # Sample size factor
        sample_size_factor = min(len(quality_results) / 10.0, 1.0)  # More samples = higher reliability
        reliability_factors.append(sample_size_factor)
        
        # Confidence factor (average confidence across assessments)
        confidence_scores = []
        for result in quality_results:
            for metric in result.dimension_scores.values():
                confidence_scores.append(metric.confidence)
        
        if confidence_scores:
            avg_confidence = statistics.mean(confidence_scores)
            reliability_factors.append(avg_confidence)
        
        # Consistency factor (lower volatility = higher reliability)
        volatility = self._calculate_quality_volatility(quality_results)
        consistency_factor = max(0, (100 - volatility) / 100)
        reliability_factors.append(consistency_factor)
        
        # Coverage factor (more dimensions assessed = higher reliability)
        total_dimensions = len(QualityDimension)
        assessed_dimensions = set()
        for result in quality_results:
            assessed_dimensions.update(result.dimension_scores.keys())
        
        coverage_factor = len(assessed_dimensions) / total_dimensions
        reliability_factors.append(coverage_factor)
        
        # Calculate overall reliability as weighted average
        weights = [0.3, 0.3, 0.25, 0.15]  # Sample size, confidence, consistency, coverage
        reliability_score = sum(
            factor * weight for factor, weight in zip(reliability_factors, weights)
        )
        
        return min(reliability_score, 1.0) * 100  # Convert to percentage
    
    def _calculate_assessment_confidence(self, quality_results: List[QualityAssessmentResult]) -> float:
        """Calculate overall confidence in the quality assessment"""
        if not quality_results:
            return 0.0
        
        confidence_factors = []
        
        # Average metric confidence
        all_confidences = []
        for result in quality_results:
            for metric in result.dimension_scores.values():
                all_confidences.append(metric.confidence)
        
        if all_confidences:
            avg_confidence = statistics.mean(all_confidences)
            confidence_factors.append(avg_confidence)
        
        # Data recency factor (more recent data = higher confidence)
        if quality_results:
            most_recent = max(result.assessment_timestamp for result in quality_results)
            time_since_recent = datetime.utcnow() - most_recent
            days_since = time_since_recent.days
            
            recency_factor = max(0, 1 - (days_since / 30))  # Full confidence if < 30 days old
            confidence_factors.append(recency_factor)
        
        # Evidence completeness factor
        total_evidence_points = 0
        for result in quality_results:
            for metric in result.dimension_scores.values():
                total_evidence_points += len(metric.evidence)
        
        evidence_factor = min(total_evidence_points / (len(quality_results) * 20), 1.0)  # 20 evidence points per assessment is ideal
        confidence_factors.append(evidence_factor)
        
        if confidence_factors:
            return statistics.mean(confidence_factors) * 100
        
        return 50.0  # Default moderate confidence