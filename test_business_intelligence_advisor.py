#!/usr/bin/env python3
"""
Test Suite for Business Intelligence Advisor
Comprehensive testing of strategic insights and recommendations

Intent-First Testing: Validate business value delivery and decision support
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from business_intelligence_advisor import (
    BusinessIntelligenceAdvisor,
    ContentPerformanceAnalyzer,
    UserBehaviorIntelligence,
    MarketIntelligenceEngine,
    BusinessInsight,
    GrowthOpportunity,
    BusinessPriority,
    DecisionUrgency,
    BusinessImpact
)

class TestContentPerformanceAnalyzer:
    """Test content performance analysis capabilities"""
    
    def setup_method(self):
        self.analyzer = ContentPerformanceAnalyzer()
    
    def test_high_roi_content_analysis(self):
        """Test analysis of high-performing content"""
        content_data = {
            "views": 100000,
            "engagement_rate": 0.85,
            "conversion_rate": 0.12,
            "production_cost": 5000,
            "revenue_generated": 20000
        }
        
        result = self.analyzer.analyze_content_roi(content_data)
        
        assert isinstance(result, BusinessInsight)
        assert result.business_impact == BusinessImpact.REVENUE_CRITICAL
        assert result.priority == BusinessPriority.HIGH
        assert result.urgency == DecisionUrgency.IMMEDIATE
        assert result.confidence_score > 0.8
        assert "Scale this content format immediately" in result.recommended_actions[0]
        assert result.potential_value > 0
    
    def test_medium_roi_content_analysis(self):
        """Test analysis of moderately performing content"""
        content_data = {
            "views": 50000,
            "engagement_rate": 0.6,
            "conversion_rate": 0.08,
            "production_cost": 3000,
            "revenue_generated": 6000
        }
        
        result = self.analyzer.analyze_content_roi(content_data)
        
        assert result.business_impact == BusinessImpact.GROWTH_OPPORTUNITY
        assert result.priority == BusinessPriority.MEDIUM
        assert result.urgency == DecisionUrgency.URGENT
        assert "Optimize content distribution" in result.recommended_actions[0]
    
    def test_low_roi_content_analysis(self):
        """Test analysis of underperforming content"""
        content_data = {
            "views": 10000,
            "engagement_rate": 0.3,
            "conversion_rate": 0.02,
            "production_cost": 5000,
            "revenue_generated": 2000
        }
        
        result = self.analyzer.analyze_content_roi(content_data)
        
        assert result.business_impact == BusinessImpact.EFFICIENCY_GAIN
        assert result.priority == BusinessPriority.LOW
        assert result.urgency == DecisionUrgency.PLANNED
        assert "Review content strategy" in result.recommended_actions[0]
    
    def test_zero_cost_content_handling(self):
        """Test handling of content with zero production cost"""
        content_data = {
            "views": 50000,
            "engagement_rate": 0.7,
            "conversion_rate": 0.1,
            "production_cost": 0,
            "revenue_generated": 10000
        }
        
        result = self.analyzer.analyze_content_roi(content_data)
        
        assert isinstance(result, BusinessInsight)
        assert result.supporting_data["current_roi"] == 0  # ROI calculation handles zero cost

class TestUserBehaviorIntelligence:
    """Test user behavior analysis and insights"""
    
    def setup_method(self):
        self.intelligence = UserBehaviorIntelligence()
    
    def test_low_engagement_detection(self):
        """Test detection of low user engagement"""
        user_data = {
            "avg_session_duration": 90,  # 1.5 minutes - low
            "bounce_rate": 0.6,
            "conversion_funnel": {},
            "feature_adoption": {}
        }
        
        insights = self.intelligence.analyze_user_journey(user_data)
        
        assert len(insights) > 0
        engagement_insight = insights[0]
        assert engagement_insight.priority == BusinessPriority.CRITICAL
        assert engagement_insight.urgency == DecisionUrgency.IMMEDIATE
        assert "Low User Engagement Alert" in engagement_insight.title
        assert "onboarding flow" in engagement_insight.recommended_actions[0]
    
    def test_conversion_funnel_analysis(self):
        """Test conversion funnel drop-off detection"""
        user_data = {
            "avg_session_duration": 300,  # Good engagement
            "bounce_rate": 0.3,
            "conversion_funnel": {
                "landing": 1.0,
                "signup": 0.8,
                "trial": 0.4,  # 40% drop - significant
                "purchase": 0.35
            },
            "feature_adoption": {}
        }
        
        insights = self.intelligence.analyze_user_journey(user_data)
        
        # Should detect the big drop at trial step
        funnel_insights = [i for i in insights if "Conversion Drop" in i.title]
        assert len(funnel_insights) > 0
        
        funnel_insight = funnel_insights[0]
        assert funnel_insight.priority == BusinessPriority.HIGH
        assert "trial" in funnel_insight.title.lower()
        assert "Redesign" in funnel_insight.recommended_actions[0]
    
    def test_growth_opportunity_identification(self):
        """Test identification of growth opportunities from user segments"""
        user_segments = {
            "enterprise": {
                "size": 2000,
                "avg_revenue_per_user": 500,
                "growth_rate": 0.25  # 25% growth - good opportunity
            },
            "small_business": {
                "size": 500,  # Too small
                "avg_revenue_per_user": 100,
                "growth_rate": 0.3
            },
            "individual": {
                "size": 5000,
                "avg_revenue_per_user": 50,
                "growth_rate": 0.1  # Low growth
            }
        }
        
        opportunities = self.intelligence.identify_growth_opportunities(user_segments)
        
        # Should identify enterprise segment as opportunity
        assert len(opportunities) > 0
        enterprise_opp = opportunities[0]
        assert "enterprise" in enterprise_opp.title.lower()
        assert enterprise_opp.success_probability > 0.5
        assert enterprise_opp.roi_estimate > 1.0
    
    def test_no_significant_issues(self):
        """Test behavior when no significant issues are detected"""
        user_data = {
            "avg_session_duration": 400,  # Good engagement
            "bounce_rate": 0.2,  # Low bounce rate
            "conversion_funnel": {
                "landing": 1.0,
                "signup": 0.9,
                "trial": 0.8,
                "purchase": 0.7  # Good conversion rates
            },
            "feature_adoption": {"basic": 0.9, "advanced": 0.6}
        }
        
        insights = self.intelligence.analyze_user_journey(user_data)
        
        # Should have no critical insights
        critical_insights = [i for i in insights if i.priority == BusinessPriority.CRITICAL]
        assert len(critical_insights) == 0

class TestMarketIntelligenceEngine:
    """Test market intelligence and competitive analysis"""
    
    def setup_method(self):
        self.engine = MarketIntelligenceEngine()
    
    def test_below_average_performance_detection(self):
        """Test detection of below-average performance metrics"""
        performance_data = {
            "user_acquisition_cost": 80,  # Above market average of 50
            "customer_lifetime_value": 150,  # Below market average of 200
            "churn_rate": 0.20,  # Above market average of 0.15
            "feature_adoption_rate": 0.3  # Below market average of 0.4
        }
        
        insights = self.engine.analyze_competitive_position(performance_data)
        
        # Should identify multiple competitive gaps
        assert len(insights) > 0
        
        # Check for specific metric insights
        cac_insights = [i for i in insights if "user_acquisition_cost" in i.insight_id]
        clv_insights = [i for i in insights if "customer_lifetime_value" in i.insight_id]
        
        assert len(cac_insights) > 0
        assert len(clv_insights) > 0
        
        # All should be high priority due to below-average performance
        for insight in insights:
            assert insight.priority == BusinessPriority.HIGH
            assert insight.urgency == DecisionUrgency.URGENT
    
    def test_above_average_performance(self):
        """Test handling of above-average performance metrics"""
        performance_data = {
            "user_acquisition_cost": 25,  # Better than top quartile of 30
            "customer_lifetime_value": 400,  # Better than top quartile of 350
        }
        
        insights = self.engine.analyze_competitive_position(performance_data)
        
        # Should have no insights for metrics performing above top quartile
        assert len(insights) == 0
    
    def test_market_average_performance(self):
        """Test handling of market-average performance"""
        performance_data = {
            "user_acquisition_cost": 45,  # Close to market average of 50
            "churn_rate": 0.14  # Close to market average of 0.15
        }
        
        insights = self.engine.analyze_competitive_position(performance_data)
        
        # Should have no insights for metrics at market average
        assert len(insights) == 0

class TestBusinessIntelligenceAdvisor:
    """Test main Business Intelligence Advisor functionality"""
    
    def setup_method(self):
        self.advisor = BusinessIntelligenceAdvisor()
    
    def test_comprehensive_analysis(self):
        """Test comprehensive business analysis with all data types"""
        business_data = {
            "content_performance": {
                "views": 75000,
                "engagement_rate": 0.7,
                "conversion_rate": 0.1,
                "production_cost": 8000,
                "revenue_generated": 30000
            },
            "user_behavior": {
                "avg_session_duration": 120,  # Low engagement
                "bounce_rate": 0.4,
                "conversion_funnel": {
                    "landing": 1.0,
                    "signup": 0.7,
                    "trial": 0.3,  # Big drop
                    "purchase": 0.25
                },
                "feature_adoption": {"basic": 0.8, "advanced": 0.4}
            },
            "performance_metrics": {
                "user_acquisition_cost": 70,  # Above average
                "customer_lifetime_value": 180,  # Below average
                "churn_rate": 0.18,  # Above average
                "feature_adoption_rate": 0.35  # Below average
            },
            "user_segments": {
                "enterprise": {
                    "size": 1500,
                    "avg_revenue_per_user": 600,
                    "growth_rate": 0.3
                }
            }
        }
        
        results = self.advisor.generate_strategic_insights(business_data)
        
        # Validate result structure
        assert "executive_summary" in results
        assert "critical_insights" in results
        assert "high_priority_insights" in results
        assert "growth_opportunities" in results
        assert "strategic_recommendations" in results
        assert "next_actions" in results
        assert "insights_summary" in results
        
        # Validate executive summary
        summary = results["executive_summary"]
        assert "business_health_score" in summary
        assert "key_findings" in summary
        assert "top_priorities" in summary
        assert isinstance(summary["business_health_score"], float)
        assert 0 <= summary["business_health_score"] <= 1
        
        # Should have insights due to problematic metrics
        assert len(results["critical_insights"]) > 0 or len(results["high_priority_insights"]) > 0
        
        # Should have growth opportunities
        assert len(results["growth_opportunities"]) > 0
        
        # Should have strategic recommendations
        assert len(results["strategic_recommendations"]) > 0
        
        # Should have prioritized next actions
        assert len(results["next_actions"]) > 0
        
        # Validate insights summary
        stats = results["insights_summary"]
        assert stats["total_insights"] > 0
        assert stats["estimated_total_value"] > 0
        assert stats["processing_time"] > 0
    
    def test_empty_data_handling(self):
        """Test handling of empty or minimal data"""
        business_data = {}
        
        results = self.advisor.generate_strategic_insights(business_data)
        
        # Should still return valid structure
        assert "executive_summary" in results
        assert "insights_summary" in results
        
        # Should have minimal insights
        assert results["insights_summary"]["total_insights"] == 0
    
    def test_business_health_score_calculation(self):
        """Test business health score calculation logic"""
        # Test with critical issues
        critical_insights = [
            BusinessInsight(
                insight_id="test1",
                title="Critical Issue",
                description="Test",
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                priority=BusinessPriority.CRITICAL,
                urgency=DecisionUrgency.IMMEDIATE,
                confidence_score=0.9,
                potential_value=50000,
                recommended_actions=["Fix immediately"],
                success_metrics=["Metric improved"],
                timeline="1 week",
                stakeholders=["Team"],
                risks=["Risk"],
                supporting_data={},
                timestamp=datetime.now()
            )
        ]
        
        health_score = self.advisor._calculate_business_health_score(critical_insights)
        assert health_score < 0.5  # Should be low due to critical issues
        
        # Test with no issues
        health_score_empty = self.advisor._calculate_business_health_score([])
        assert health_score_empty == 0.5  # Default score
    
    def test_next_actions_prioritization(self):
        """Test prioritization of next actions"""
        insights = [
            BusinessInsight(
                insight_id="low_priority",
                title="Low Priority Issue",
                description="Test",
                business_impact=BusinessImpact.EFFICIENCY_GAIN,
                priority=BusinessPriority.LOW,
                urgency=DecisionUrgency.PLANNED,
                confidence_score=0.7,
                potential_value=10000,
                recommended_actions=["Low priority action"],
                success_metrics=["Metric"],
                timeline="1 month",
                stakeholders=["Team"],
                risks=["Risk"],
                supporting_data={},
                timestamp=datetime.now()
            ),
            BusinessInsight(
                insight_id="high_priority",
                title="High Priority Issue",
                description="Test",
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                priority=BusinessPriority.CRITICAL,
                urgency=DecisionUrgency.IMMEDIATE,
                confidence_score=0.9,
                potential_value=100000,
                recommended_actions=["Critical action"],
                success_metrics=["Metric"],
                timeline="1 day",
                stakeholders=["Team"],
                risks=["Risk"],
                supporting_data={},
                timestamp=datetime.now()
            )
        ]
        
        next_actions = self.advisor._prioritize_next_actions(insights)
        
        # High priority should come first
        assert next_actions[0]["action"] == "Critical action"
        assert next_actions[0]["priority"] == "critical"
        assert next_actions[1]["action"] == "Low priority action"
        assert next_actions[1]["priority"] == "low"
    
    def test_strategic_recommendations_generation(self):
        """Test generation of strategic recommendations"""
        revenue_insights = [
            BusinessInsight(
                insight_id="revenue1",
                title="Revenue Issue",
                description="Test",
                business_impact=BusinessImpact.REVENUE_CRITICAL,
                priority=BusinessPriority.CRITICAL,
                urgency=DecisionUrgency.IMMEDIATE,
                confidence_score=0.9,
                potential_value=75000,
                recommended_actions=["Fix revenue"],
                success_metrics=["Revenue up"],
                timeline="2 weeks",
                stakeholders=["Revenue Team"],
                risks=["Revenue risk"],
                supporting_data={},
                timestamp=datetime.now()
            )
        ]
        
        recommendations = self.advisor._create_strategic_recommendations(revenue_insights, [])
        
        assert len(recommendations) > 0
        rec = recommendations[0]
        assert rec.category == "revenue"
        assert "Revenue Optimization" in rec.title
        assert len(rec.implementation_plan) > 0
        assert rec.resource_requirements["budget"] > 0

class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    def setup_method(self):
        self.advisor = BusinessIntelligenceAdvisor()
    
    def test_startup_scenario(self):
        """Test analysis for startup with growth focus"""
        startup_data = {
            "content_performance": {
                "views": 25000,
                "engagement_rate": 0.8,  # High engagement
                "conversion_rate": 0.15,  # Good conversion
                "production_cost": 2000,
                "revenue_generated": 8000  # Good ROI
            },
            "user_behavior": {
                "avg_session_duration": 250,  # Good engagement
                "bounce_rate": 0.25,  # Low bounce
                "conversion_funnel": {
                    "landing": 1.0,
                    "signup": 0.8,
                    "trial": 0.6,
                    "purchase": 0.4  # Decent funnel
                }
            },
            "user_segments": {
                "early_adopters": {
                    "size": 500,
                    "avg_revenue_per_user": 200,
                    "growth_rate": 0.4  # High growth
                }
            }
        }
        
        results = self.advisor.generate_strategic_insights(startup_data)
        
        # Should focus on growth opportunities
        assert len(results["growth_opportunities"]) > 0
        assert results["executive_summary"]["business_health_score"] > 0.6
    
    def test_enterprise_scenario(self):
        """Test analysis for enterprise with optimization focus"""
        enterprise_data = {
            "content_performance": {
                "views": 500000,
                "engagement_rate": 0.5,  # Average engagement
                "conversion_rate": 0.05,  # Low conversion
                "production_cost": 50000,
                "revenue_generated": 100000  # Decent ROI but could improve
            },
            "user_behavior": {
                "avg_session_duration": 180,
                "bounce_rate": 0.4,
                "conversion_funnel": {
                    "landing": 1.0,
                    "signup": 0.6,
                    "trial": 0.3,  # Big drop
                    "purchase": 0.1  # Poor conversion
                }
            },
            "performance_metrics": {
                "user_acquisition_cost": 100,  # High
                "customer_lifetime_value": 300,  # Decent
                "churn_rate": 0.2,  # High
                "feature_adoption_rate": 0.3  # Low
            }
        }
        
        results = self.advisor.generate_strategic_insights(enterprise_data)
        
        # Should identify optimization opportunities
        assert len(results["critical_insights"]) > 0 or len(results["high_priority_insights"]) > 0
        assert len(results["strategic_recommendations"]) > 0
        
        # Should have actionable next steps
        assert len(results["next_actions"]) >= 3

def test_demo_functionality():
    """Test the demo function runs without errors"""
    from business_intelligence_advisor import demo_business_intelligence_advisor
    
    # Should run without exceptions
    try:
        demo_business_intelligence_advisor()
        assert True
    except Exception as e:
        pytest.fail(f"Demo function failed: {e}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])