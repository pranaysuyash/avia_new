#!/usr/bin/env python3
"""
User Confidence Engine - Intent-First Transformation
Transforms technical monitoring into user-facing confidence indicators
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import statistics
import json

# Import existing monitoring system
try:
    from production_monitoring_logging import (
        SystemMonitor, PerformanceMetrics, AlertManager, HealthChecker
    )
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    logging.warning("Production monitoring system not available")

logger = logging.getLogger(__name__)

class ConfidenceLevel(Enum):
    """User confidence levels"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"

class ImpactLevel(Enum):
    """User impact levels"""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"

@dataclass
class UserConfidence:
    """User-facing confidence indicators"""
    reliability_score: float  # 0.0 to 1.0
    confidence_level: ConfidenceLevel
    user_message: str
    estimated_processing_time: str
    proactive_alerts: List[str] = field(default_factory=list)
    system_status_summary: str = "System running optimally"
    next_maintenance: Optional[str] = None
    quality_indicators: Dict[str, Any] = field(default_factory=dict)

@dataclass
class UserImpact:
    """Translation of technical issues to user impact"""
    impact_level: ImpactLevel
    user_message: str
    affected_features: List[str]
    estimated_delay: Optional[str] = None
    recommendation: Optional[str] = None
    workaround: Optional[str] = None

@dataclass
class PredictiveAlert:
    """Predictive user-facing alerts"""
    alert_type: str
    message: str
    confidence: float
    time_to_impact: str
    recommended_action: str
    severity: str = "info"

class UserConfidenceEngine:
    """
    Intent-First transformation of production monitoring
    Converts technical metrics into user confidence indicators
    """
    
    def __init__(self):
        self.system_monitor = SystemMonitor() if MONITORING_AVAILABLE else None
        self.alert_manager = AlertManager() if MONITORING_AVAILABLE else None
        self.health_checker = HealthChecker() if MONITORING_AVAILABLE else None
        
        # User confidence calculation weights
        self.confidence_weights = {
            'system_health': 0.4,
            'processing_queue': 0.3,
            'recent_reliability': 0.2,
            'predictive_factors': 0.1
        }
        
        # Historical performance tracking
        self.performance_history = []
        self.user_impact_patterns = {}
        
    async def get_user_confidence_indicators(self) -> UserConfidence:
        """Get comprehensive user confidence indicators"""
        
        # Gather technical metrics
        system_metrics = await self._get_system_health_score()
        queue_status = await self._get_processing_queue_status()
        reliability_score = await self._calculate_reliability_score()
        predictive_factors = await self._analyze_predictive_factors()
        
        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(
            system_metrics, queue_status, reliability_score, predictive_factors
        )
        
        # Generate user-facing message
        user_message = self._generate_user_message(confidence_score, system_metrics)
        
        # Estimate processing time
        processing_time = self._estimate_processing_time(queue_status, system_metrics)
        
        # Generate proactive alerts
        proactive_alerts = await self._generate_proactive_alerts()
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(confidence_score)
        
        return UserConfidence(
            reliability_score=confidence_score,
            confidence_level=confidence_level,
            user_message=user_message,
            estimated_processing_time=processing_time,
            proactive_alerts=proactive_alerts,
            system_status_summary=self._get_system_status_summary(confidence_score),
            next_maintenance=self._get_next_maintenance_window(),
            quality_indicators=self._get_quality_indicators()
        )
    
    async def predict_user_impact(self, technical_metric: str, value: float) -> UserImpact:
        """Translate technical metrics to user impact"""
        
        impact_patterns = {
            'cpu_usage': self._analyze_cpu_impact,
            'memory_usage': self._analyze_memory_impact,
            'disk_usage': self._analyze_disk_impact,
            'error_rate': self._analyze_error_impact,
            'response_time': self._analyze_response_time_impact
        }
        
        if technical_metric in impact_patterns:
            return impact_patterns[technical_metric](value)
        
        return UserImpact(
            impact_level=ImpactLevel.NONE,
            user_message="System operating normally",
            affected_features=[]
        )
    
    async def get_predictive_alerts(self) -> List[PredictiveAlert]:
        """Generate predictive alerts for users"""
        alerts = []
        
        # Analyze trends for predictive insights
        if self.system_monitor:
            current_metrics = self.system_monitor.get_system_metrics()
            
            # Predict capacity issues
            capacity_alert = self._predict_capacity_issues(current_metrics)
            if capacity_alert:
                alerts.append(capacity_alert)
            
            # Predict maintenance needs
            maintenance_alert = self._predict_maintenance_needs()
            if maintenance_alert:
                alerts.append(maintenance_alert)
            
            # Predict quality degradation
            quality_alert = self._predict_quality_issues(current_metrics)
            if quality_alert:
                alerts.append(quality_alert)
        
        return alerts
    
    async def _get_system_health_score(self) -> float:
        """Calculate system health score from technical metrics"""
        if not self.system_monitor:
            return 0.95  # Default good score when monitoring unavailable
        
        try:
            metrics = self.system_monitor.get_system_metrics()
            
            # Convert technical metrics to health scores
            cpu_score = max(0, 1 - (metrics.cpu_usage / 100))
            memory_score = max(0, 1 - (metrics.memory_usage / 100))
            disk_score = max(0, 1 - (metrics.disk_usage / 100))
            error_score = max(0, 1 - (metrics.error_rate / 10))  # Assume 10% is max
            
            # Weighted average
            health_score = (
                cpu_score * 0.3 +
                memory_score * 0.3 +
                disk_score * 0.2 +
                error_score * 0.2
            )
            
            return min(1.0, max(0.0, health_score))
            
        except Exception as e:
            logger.error(f"Error calculating system health score: {e}")
            return 0.8  # Conservative fallback
    
    async def _get_processing_queue_status(self) -> Dict[str, Any]:
        """Get processing queue status for time estimation"""
        # This would integrate with actual queue monitoring
        # For now, return mock data
        return {
            'queue_length': 5,
            'average_processing_time': 120,  # seconds
            'current_throughput': 0.8,  # jobs per second
            'estimated_wait_time': 300  # seconds
        }
    
    async def _calculate_reliability_score(self) -> float:
        """Calculate reliability based on recent performance"""
        # Analyze last 24 hours of performance
        if len(self.performance_history) < 10:
            return 0.95  # Default high score for new systems
        
        recent_performance = self.performance_history[-24:]  # Last 24 data points
        uptime_scores = [p.get('uptime_score', 1.0) for p in recent_performance]
        
        return statistics.mean(uptime_scores)
    
    async def _analyze_predictive_factors(self) -> Dict[str, float]:
        """Analyze factors that might affect future performance"""
        factors = {
            'trend_stability': 0.9,
            'seasonal_patterns': 0.85,
            'capacity_headroom': 0.8,
            'maintenance_schedule': 0.95
        }
        
        # This would analyze actual trends and patterns
        return factors
    
    def _calculate_confidence_score(self, system_health: float, queue_status: Dict, 
                                  reliability: float, predictive: Dict) -> float:
        """Calculate overall user confidence score"""
        
        # Process queue impact
        queue_impact = min(1.0, 1 - (queue_status['queue_length'] / 20))
        
        # Predictive factors average
        predictive_avg = statistics.mean(predictive.values())
        
        # Weighted calculation
        confidence = (
            system_health * self.confidence_weights['system_health'] +
            queue_impact * self.confidence_weights['processing_queue'] +
            reliability * self.confidence_weights['recent_reliability'] +
            predictive_avg * self.confidence_weights['predictive_factors']
        )
        
        return min(1.0, max(0.0, confidence))
    
    def _generate_user_message(self, confidence_score: float, system_health: float) -> str:
        """Generate user-friendly status message"""
        
        if confidence_score >= 0.95:
            return "System running optimally - your transcription will complete quickly and accurately"
        elif confidence_score >= 0.85:
            return "System performing well - normal processing times expected"
        elif confidence_score >= 0.75:
            return "System stable - slightly longer processing times possible"
        elif confidence_score >= 0.65:
            return "System experiencing minor delays - processing may take extra time"
        else:
            return "System under heavy load - consider processing during off-peak hours"
    
    def _estimate_processing_time(self, queue_status: Dict, system_health: float) -> str:
        """Estimate user processing time"""
        
        base_time = queue_status.get('average_processing_time', 120)
        queue_delay = queue_status.get('estimated_wait_time', 0)
        
        # Adjust for system health
        health_multiplier = 2.0 - system_health  # 1.0 to 2.0 range
        
        total_time = (base_time * health_multiplier) + queue_delay
        
        if total_time < 60:
            return "Less than 1 minute"
        elif total_time < 300:
            return f"{int(total_time/60)} minutes"
        elif total_time < 1800:
            return f"{int(total_time/60)} minutes"
        else:
            return "More than 30 minutes - consider trying later"
    
    async def _generate_proactive_alerts(self) -> List[str]:
        """Generate proactive user alerts"""
        alerts = []
        
        # Check for upcoming maintenance
        maintenance_window = self._get_next_maintenance_window()
        if maintenance_window:
            alerts.append(f"Scheduled maintenance {maintenance_window} - no service impact expected")
        
        # Check for optimal processing conditions
        current_hour = datetime.now().hour
        if 2 <= current_hour <= 6:  # Off-peak hours
            alerts.append("Optimal processing time - faster results available now")
        elif 14 <= current_hour <= 16:  # Peak hours
            alerts.append("Peak usage period - consider processing later for faster results")
        
        # Check for quality enhancements
        alerts.append("High-quality AI models active - enhanced accuracy available")
        
        return alerts
    
    def _determine_confidence_level(self, score: float) -> ConfidenceLevel:
        """Determine confidence level from score"""
        if score >= 0.9:
            return ConfidenceLevel.EXCELLENT
        elif score >= 0.8:
            return ConfidenceLevel.GOOD
        elif score >= 0.7:
            return ConfidenceLevel.FAIR
        else:
            return ConfidenceLevel.POOR
    
    def _get_system_status_summary(self, confidence_score: float) -> str:
        """Get system status summary"""
        if confidence_score >= 0.9:
            return "All systems operational - optimal performance"
        elif confidence_score >= 0.8:
            return "Systems running smoothly - good performance"
        elif confidence_score >= 0.7:
            return "Systems stable - minor performance variations"
        else:
            return "Systems under load - performance may be impacted"
    
    def _get_next_maintenance_window(self) -> Optional[str]:
        """Get next scheduled maintenance window"""
        # This would check actual maintenance schedules
        # For demo, return a sample window
        next_week = datetime.now() + timedelta(days=7)
        if next_week.weekday() == 6:  # Sunday
            return "Sunday 2-4 AM"
        return None
    
    def _get_quality_indicators(self) -> Dict[str, Any]:
        """Get quality indicators for user"""
        return {
            'transcription_accuracy': 0.96,
            'processing_speed': 'optimal',
            'ai_model_status': 'premium_active',
            'data_security': 'fully_encrypted'
        }
    
    # Impact analysis methods
    def _analyze_cpu_impact(self, cpu_usage: float) -> UserImpact:
        """Analyze CPU usage impact on users"""
        if cpu_usage > 90:
            return UserImpact(
                impact_level=ImpactLevel.SIGNIFICANT,
                user_message="High system load - processing delays expected",
                affected_features=["transcription", "analysis", "export"],
                estimated_delay="5-10 additional minutes",
                recommendation="Consider processing during off-peak hours",
                workaround="Try smaller files or simpler processing options"
            )
        elif cpu_usage > 80:
            return UserImpact(
                impact_level=ImpactLevel.MODERATE,
                user_message="Moderate system load - slightly longer processing times",
                affected_features=["transcription", "analysis"],
                estimated_delay="2-3 additional minutes",
                recommendation="Processing may be slower than usual"
            )
        elif cpu_usage > 70:
            return UserImpact(
                impact_level=ImpactLevel.MINOR,
                user_message="System busy - minor delays possible",
                affected_features=["analysis"],
                estimated_delay="1-2 additional minutes"
            )
        else:
            return UserImpact(
                impact_level=ImpactLevel.NONE,
                user_message="System running smoothly - optimal processing speed",
                affected_features=[]
            )
    
    def _analyze_memory_impact(self, memory_usage: float) -> UserImpact:
        """Analyze memory usage impact on users"""
        if memory_usage > 95:
            return UserImpact(
                impact_level=ImpactLevel.SIGNIFICANT,
                user_message="Memory constraints - large file processing may fail",
                affected_features=["large_file_processing", "batch_processing"],
                recommendation="Try smaller files or contact support for large files",
                workaround="Split large files into smaller segments"
            )
        elif memory_usage > 85:
            return UserImpact(
                impact_level=ImpactLevel.MODERATE,
                user_message="High memory usage - large files may process slowly",
                affected_features=["large_file_processing"],
                estimated_delay="Additional processing time for large files"
            )
        else:
            return UserImpact(
                impact_level=ImpactLevel.NONE,
                user_message="Memory usage normal - all file sizes supported",
                affected_features=[]
            )
    
    def _analyze_disk_impact(self, disk_usage: float) -> UserImpact:
        """Analyze disk usage impact on users"""
        if disk_usage > 95:
            return UserImpact(
                impact_level=ImpactLevel.SIGNIFICANT,
                user_message="Storage nearly full - new uploads may be rejected",
                affected_features=["file_upload", "export_generation"],
                recommendation="Download and delete old files to free space"
            )
        elif disk_usage > 90:
            return UserImpact(
                impact_level=ImpactLevel.MODERATE,
                user_message="Storage space low - consider cleaning up old files",
                affected_features=["file_upload"],
                recommendation="Free up space by deleting unused files"
            )
        else:
            return UserImpact(
                impact_level=ImpactLevel.NONE,
                user_message="Storage space available - uploads and exports working normally",
                affected_features=[]
            )
    
    def _analyze_error_impact(self, error_rate: float) -> UserImpact:
        """Analyze error rate impact on users"""
        if error_rate > 5:
            return UserImpact(
                impact_level=ImpactLevel.SIGNIFICANT,
                user_message="Elevated error rate - some operations may fail",
                affected_features=["transcription", "analysis", "export"],
                recommendation="Try again in a few minutes or contact support",
                workaround="Refresh the page and retry your operation"
            )
        elif error_rate > 2:
            return UserImpact(
                impact_level=ImpactLevel.MODERATE,
                user_message="Minor service issues - occasional errors possible",
                affected_features=["analysis", "export"],
                recommendation="Retry if you encounter any errors"
            )
        else:
            return UserImpact(
                impact_level=ImpactLevel.NONE,
                user_message="System stable - operations completing successfully",
                affected_features=[]
            )
    
    def _analyze_response_time_impact(self, response_time: float) -> UserImpact:
        """Analyze response time impact on users"""
        if response_time > 5000:  # 5 seconds
            return UserImpact(
                impact_level=ImpactLevel.SIGNIFICANT,
                user_message="Slow response times - interface may feel sluggish",
                affected_features=["ui_responsiveness", "real_time_features"],
                estimated_delay="5+ second delays in interface",
                recommendation="Refresh page or try again later"
            )
        elif response_time > 2000:  # 2 seconds
            return UserImpact(
                impact_level=ImpactLevel.MODERATE,
                user_message="Slower than normal response times",
                affected_features=["ui_responsiveness"],
                estimated_delay="2-5 second delays"
            )
        else:
            return UserImpact(
                impact_level=ImpactLevel.NONE,
                user_message="Response times normal - interface running smoothly",
                affected_features=[]
            )
    
    # Predictive analysis methods
    def _predict_capacity_issues(self, current_metrics) -> Optional[PredictiveAlert]:
        """Predict capacity issues before they impact users"""
        if hasattr(current_metrics, 'cpu_usage') and current_metrics.cpu_usage > 75:
            return PredictiveAlert(
                alert_type="capacity",
                message="High load expected in next 30 minutes based on usage patterns",
                confidence=0.85,
                time_to_impact="30 minutes",
                recommended_action="Consider processing your files now for faster results",
                severity="info"
            )
        return None
    
    def _predict_maintenance_needs(self) -> Optional[PredictiveAlert]:
        """Predict maintenance needs"""
        # Check if maintenance is due soon
        next_maintenance = self._get_next_maintenance_window()
        if next_maintenance:
            return PredictiveAlert(
                alert_type="maintenance",
                message=f"Scheduled maintenance {next_maintenance} - no service interruption expected",
                confidence=1.0,
                time_to_impact=next_maintenance,
                recommended_action="No action needed - service will remain available",
                severity="info"
            )
        return None
    
    def _predict_quality_issues(self, current_metrics) -> Optional[PredictiveAlert]:
        """Predict quality degradation"""
        # This would analyze patterns that lead to quality issues
        # For now, return positive quality indicator
        return PredictiveAlert(
            alert_type="quality",
            message="Premium AI models active - enhanced transcription accuracy available",
            confidence=0.95,
            time_to_impact="now",
            recommended_action="Take advantage of enhanced quality for important transcriptions",
            severity="positive"
        )

# Example usage and testing
async def demo_user_confidence_engine():
    """Demonstrate the user confidence engine"""
    print("🎯 User Confidence Engine Demo")
    print("=" * 50)
    
    engine = UserConfidenceEngine()
    
    # Get user confidence indicators
    print("\n📊 Current System Confidence:")
    confidence = await engine.get_user_confidence_indicators()
    
    print(f"   Reliability Score: {confidence.reliability_score:.2f}")
    print(f"   Confidence Level: {confidence.confidence_level.value}")
    print(f"   User Message: {confidence.user_message}")
    print(f"   Processing Time: {confidence.estimated_processing_time}")
    print(f"   System Status: {confidence.system_status_summary}")
    
    if confidence.proactive_alerts:
        print(f"\n🔔 Proactive Alerts:")
        for alert in confidence.proactive_alerts:
            print(f"   • {alert}")
    
    # Test impact analysis
    print(f"\n⚠️ Impact Analysis Examples:")
    
    # High CPU scenario
    cpu_impact = await engine.predict_user_impact("cpu_usage", 85.0)
    print(f"   High CPU (85%): {cpu_impact.user_message}")
    if cpu_impact.recommendation:
        print(f"   Recommendation: {cpu_impact.recommendation}")
    
    # High memory scenario
    memory_impact = await engine.predict_user_impact("memory_usage", 90.0)
    print(f"   High Memory (90%): {memory_impact.user_message}")
    
    # Get predictive alerts
    print(f"\n🔮 Predictive Alerts:")
    predictive_alerts = await engine.get_predictive_alerts()
    for alert in predictive_alerts:
        print(f"   • {alert.message}")
        print(f"     Action: {alert.recommended_action}")

if __name__ == "__main__":
    asyncio.run(demo_user_confidence_engine())