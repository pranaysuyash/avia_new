"""
Test suite for Data Analytics and Business Intelligence System
Tests customer lifetime value, churn prediction, usage analytics, competitive analysis, and predictive analytics
"""

import pytest
import os
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_analytics_business_intelligence import (
    DataAnalyticsBI, CustomerSegment, FeatureAdoptionStage,
    CustomerLifetimeValue, ChurnPrediction, FeatureUsage, 
    CompetitiveMetric, BusinessGrowthPrediction
)

class TestDataAnalyticsBI:
    
    @pytest.fixture
    def analytics_system(self):
        """Create a temporary analytics system for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
            db_path = tmp_file.name
        
        system = DataAnalyticsBI(db_path)
        yield system
        
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_database_initialization(self, analytics_system):
        """Test that the database is properly initialized"""
        assert os.path.exists(analytics_system.db_path)
        
        # Test that tables were created
        import sqlite3
        conn = sqlite3.connect(analytics_system.db_path)
        cursor = conn.cursor()
        
        # Check if main tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['customers', 'usage_events', 'revenue_events', 
                          'feature_adoption', 'competitive_benchmarks', 'predictions']
        
        for table in expected_tables:
            assert table in tables
        
        conn.close()
    
    def test_sample_data_creation(self, analytics_system):
        """Test adding sample data"""
        analytics_system.add_sample_data()
        
        # Verify data was added
        import sqlite3
        conn = sqlite3.connect(analytics_system.db_path)
        
        # Check customers
        customer_count = pd.read_sql_query("SELECT COUNT(*) as count FROM customers", conn)
        assert customer_count.iloc[0]['count'] > 0
        
        # Check usage events
        usage_count = pd.read_sql_query("SELECT COUNT(*) as count FROM usage_events", conn)
        assert usage_count.iloc[0]['count'] > 0
        
        # Check revenue events
        revenue_count = pd.read_sql_query("SELECT COUNT(*) as count FROM revenue_events", conn)
        assert revenue_count.iloc[0]['count'] > 0
        
        conn.close()
    
    def test_customer_lifetime_value_calculation(self, analytics_system):
        """Test customer lifetime value calculation"""
        # Add sample data first
        analytics_system.add_sample_data()
        
        # Calculate CLV for a test user
        clv = analytics_system.calculate_customer_ltv("user1")
        
        assert clv is not None
        assert isinstance(clv, CustomerLifetimeValue)
        assert clv.user_id == "user1"
        assert clv.current_clv >= 0
        assert clv.predicted_clv >= 0
        assert isinstance(clv.segment, CustomerSegment)
        assert 0 <= clv.churn_probability <= 1
        assert clv.subscription_months > 0
        assert clv.total_revenue >= 0
        assert clv.acquisition_cost >= 0
    
    def test_clv_cohort_analysis(self, analytics_system):
        """Test CLV cohort analysis"""
        analytics_system.add_sample_data()
        
        # Test monthly cohort analysis
        cohort_data = analytics_system.get_clv_cohort_analysis("monthly")
        
        assert isinstance(cohort_data, pd.DataFrame)
        assert not cohort_data.empty
        assert 'customers' in cohort_data.columns
        assert 'avg_clv' in cohort_data.columns
        assert 'total_clv' in cohort_data.columns
        
        # Test quarterly cohort analysis
        quarterly_data = analytics_system.get_clv_cohort_analysis("quarterly")
        assert isinstance(quarterly_data, pd.DataFrame)
    
    def test_churn_prediction_model_training(self, analytics_system):
        """Test churn prediction model training"""
        analytics_system.add_sample_data()
        
        # Train the model
        results = analytics_system.train_churn_prediction_model()
        
        assert isinstance(results, dict)
        assert "accuracy" in results
        assert "samples" in results
        assert "feature_importance" in results
        
        # Check that accuracy is reasonable (0-1)
        assert 0 <= results["accuracy"] <= 1
        assert results["samples"] > 0
        
        # Check feature importance
        importance = results["feature_importance"]
        assert isinstance(importance, dict)
        assert len(importance) > 0
        
        # Verify model was saved
        assert 'churn_prediction' in analytics_system.models
        assert 'churn_prediction' in analytics_system.scalers
    
    def test_churn_probability_prediction(self, analytics_system):
        """Test individual churn probability prediction"""
        analytics_system.add_sample_data()
        
        # Predict churn probability
        probability = analytics_system.predict_churn_probability("user1")
        
        assert isinstance(probability, float)
        assert 0 <= probability <= 1
        
        # Test with non-existent user
        prob_nonexistent = analytics_system.predict_churn_probability("nonexistent_user")
        assert prob_nonexistent == 0.5  # Default probability
    
    def test_churn_prediction_report(self, analytics_system):
        """Test comprehensive churn prediction report"""
        analytics_system.add_sample_data()
        
        # Generate churn report
        report = analytics_system.generate_churn_prediction_report("user1")
        
        assert isinstance(report, ChurnPrediction)
        assert report.user_id == "user1"
        assert 0 <= report.churn_probability <= 1
        assert report.risk_level in ["low", "medium", "high"]
        assert isinstance(report.key_factors, list)
        assert isinstance(report.recommended_actions, list)
        assert 0 <= report.prediction_confidence <= 1
        assert report.days_to_predicted_churn > 0
    
    def test_feature_usage_tracking(self, analytics_system):
        """Test feature usage tracking"""
        analytics_system.add_sample_data()
        
        # Track feature usage
        analytics_system.track_feature_usage("user1", "transcription", 300)
        analytics_system.track_feature_usage("user1", "transcription", 450)
        analytics_system.track_feature_usage("user2", "translation", 200)
        
        # Verify usage was tracked
        import sqlite3
        conn = sqlite3.connect(analytics_system.db_path)
        
        usage_query = '''
            SELECT COUNT(*) as count FROM usage_events 
            WHERE user_id = 'user1' AND feature_name = 'transcription'
        '''
        usage_count = pd.read_sql_query(usage_query, conn)
        
        # Should have at least 2 new events (plus any from sample data)
        assert usage_count.iloc[0]['count'] >= 2
        
        conn.close()
    
    def test_feature_adoption_analytics(self, analytics_system):
        """Test feature adoption analytics"""
        analytics_system.add_sample_data()
        
        # Track some additional usage to ensure data
        analytics_system.track_feature_usage("user1", "test_feature", 300)
        analytics_system.track_feature_usage("user2", "test_feature", 200)
        
        # Get feature adoption analytics
        features = analytics_system.get_feature_adoption_analytics()
        
        assert isinstance(features, list)
        assert len(features) > 0
        
        for feature in features:
            assert isinstance(feature, FeatureUsage)
            assert feature.total_users >= 0
            assert feature.active_users >= 0
            assert 0 <= feature.adoption_rate <= 100
            assert 0 <= feature.retention_rate <= 100
            assert feature.avg_usage_frequency >= 0
            assert 0 <= feature.user_satisfaction <= 5
            assert isinstance(feature.stage_distribution, dict)
    
    def test_competitive_benchmark_management(self, analytics_system):
        """Test competitive benchmark management"""
        # Add competitive benchmarks
        analytics_system.add_competitive_benchmark(
            "accuracy", 95.5, "Competitor A", 92.0, 90.0, "Test Source"
        )
        analytics_system.add_competitive_benchmark(
            "speed", 2.3, "Competitor B", 3.1, 2.8, "Test Source"
        )
        
        # Get competitive analysis
        metrics = analytics_system.get_competitive_analysis()
        
        assert isinstance(metrics, list)
        assert len(metrics) >= 2
        
        for metric in metrics:
            assert isinstance(metric, CompetitiveMetric)
            assert metric.our_value > 0
            assert metric.competitor_avg > 0
            assert metric.market_leader > 0
            assert 0 <= metric.percentile_rank <= 100
            assert metric.trend_direction in ["improving", "declining", "stable"]
            assert isinstance(metric.benchmark_date, pd.Timestamp)
    
    def test_growth_prediction_model_training(self, analytics_system):
        """Test growth prediction model training"""
        analytics_system.add_sample_data()
        
        # Train revenue growth model
        results = analytics_system.train_growth_prediction_model("revenue")
        
        # Should either succeed or fail gracefully with insufficient data
        assert isinstance(results, dict)
        
        if "error" not in results:
            assert "mse" in results
            assert "samples" in results
            assert "feature_importance" in results
            assert results["mse"] >= 0
            assert results["samples"] > 0
            assert f'growth_revenue' in analytics_system.models
        else:
            # Expected for small sample data
            assert "Insufficient" in results["error"]
    
    def test_business_growth_prediction(self, analytics_system):
        """Test business growth prediction"""
        analytics_system.add_sample_data()
        
        # Predict revenue growth
        prediction = analytics_system.predict_business_growth("revenue", 30)
        
        assert isinstance(prediction, BusinessGrowthPrediction)
        assert prediction.metric_name == "revenue"
        assert prediction.current_value >= 0
        assert prediction.predicted_value >= 0
        assert prediction.prediction_period == "30 days"
        assert isinstance(prediction.confidence_interval, tuple)
        assert len(prediction.confidence_interval) == 2
        assert prediction.confidence_interval[0] <= prediction.confidence_interval[1]
        assert isinstance(prediction.key_drivers, list)
        assert len(prediction.key_drivers) > 0
        assert isinstance(prediction.prediction_date, datetime)
    
    def test_analytics_summary(self, analytics_system):
        """Test comprehensive analytics summary"""
        analytics_system.add_sample_data()
        
        # Get analytics summary
        summary = analytics_system.get_analytics_summary()
        
        assert isinstance(summary, dict)
        assert "customer_metrics" in summary
        assert "usage_metrics" in summary
        assert "revenue_metrics" in summary
        assert "generated_at" in summary
        
        # Check customer metrics
        customer_metrics = summary["customer_metrics"]
        assert "total_customers" in customer_metrics
        assert "active_customers" in customer_metrics
        assert "avg_revenue_per_customer" in customer_metrics
        assert "avg_engagement_score" in customer_metrics
        
        # Check usage metrics
        usage_metrics = summary["usage_metrics"]
        assert "total_usage_events" in usage_metrics
        assert "active_users" in usage_metrics
        assert "avg_session_duration" in usage_metrics
        assert "features_used" in usage_metrics
        
        # Check revenue metrics
        revenue_metrics = summary["revenue_metrics"]
        assert "total_revenue" in revenue_metrics
        assert "avg_transaction" in revenue_metrics
        assert "total_transactions" in revenue_metrics
    
    def test_feature_adoption_stage_progression(self, analytics_system):
        """Test feature adoption stage progression"""
        analytics_system.add_sample_data()
        
        user_id = "test_user"
        feature_name = "test_feature"
        
        # Add customer first
        import sqlite3
        conn = sqlite3.connect(analytics_system.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO customers (user_id, signup_date, subscription_tier, engagement_score)
            VALUES (?, ?, ?, ?)
        ''', (user_id, "2024-01-01", "basic", 75.0))
        conn.commit()
        conn.close()
        
        # Track usage to progress through stages
        # Discovery stage (1 use)
        analytics_system.track_feature_usage(user_id, feature_name, 300)
        
        # Trial stage (2-5 uses)
        for _ in range(3):
            analytics_system.track_feature_usage(user_id, feature_name, 300)
        
        # Adoption stage (6-20 uses)
        for _ in range(10):
            analytics_system.track_feature_usage(user_id, feature_name, 300)
        
        # Check final adoption stage
        conn = sqlite3.connect(analytics_system.db_path)
        stage_query = '''
            SELECT adoption_stage, usage_count FROM feature_adoption 
            WHERE user_id = ? AND feature_name = ?
        '''
        stage_data = pd.read_sql_query(stage_query, conn, params=[user_id, feature_name])
        conn.close()
        
        assert not stage_data.empty
        assert stage_data.iloc[0]['usage_count'] >= 14  # 1 + 3 + 10
        assert stage_data.iloc[0]['adoption_stage'] == FeatureAdoptionStage.ADOPTION.value
    
    def test_error_handling(self, analytics_system):
        """Test error handling for edge cases"""
        # Test CLV calculation for non-existent user
        clv = analytics_system.calculate_customer_ltv("nonexistent_user")
        assert clv is None
        
        # Test churn prediction with no training data
        probability = analytics_system.predict_churn_probability("any_user")
        assert probability == 0.5  # Default probability
        
        # Test feature adoption with no data
        features = analytics_system.get_feature_adoption_analytics()
        assert isinstance(features, list)  # Should return empty list, not error
        
        # Test competitive analysis with no data
        metrics = analytics_system.get_competitive_analysis()
        assert isinstance(metrics, list)  # Should return empty list, not error
    
    def test_data_consistency(self, analytics_system):
        """Test data consistency across different analytics"""
        analytics_system.add_sample_data()
        
        # Get summary data
        summary = analytics_system.get_analytics_summary()
        
        # Check that customer counts are consistent
        customer_metrics = summary["customer_metrics"]
        total_customers = customer_metrics.get("total_customers", 0)
        
        # Verify with direct database query
        import sqlite3
        conn = sqlite3.connect(analytics_system.db_path)
        direct_count = pd.read_sql_query("SELECT COUNT(*) as count FROM customers", conn)
        conn.close()
        
        assert total_customers == direct_count.iloc[0]['count']
    
    def test_model_persistence(self, analytics_system):
        """Test that trained models persist correctly"""
        analytics_system.add_sample_data()
        
        # Train churn model
        analytics_system.train_churn_prediction_model()
        
        # Verify model exists
        assert 'churn_prediction' in analytics_system.models
        assert 'churn_prediction' in analytics_system.scalers
        
        # Make prediction to ensure model works
        probability = analytics_system.predict_churn_probability("user1")
        assert isinstance(probability, float)
        assert 0 <= probability <= 1
    
    def test_date_handling(self, analytics_system):
        """Test proper date handling across the system"""
        analytics_system.add_sample_data()
        
        # Test CLV calculation with date fields
        clv = analytics_system.calculate_customer_ltv("user1")
        assert clv is not None
        assert isinstance(clv.last_activity, pd.Timestamp)
        
        # Test competitive analysis dates
        analytics_system.add_competitive_benchmark(
            "test_metric", 100.0, "Test Competitor", 90.0, 85.0, "Test"
        )
        
        metrics = analytics_system.get_competitive_analysis()
        if metrics:
            assert isinstance(metrics[0].benchmark_date, pd.Timestamp)
        
        # Test growth prediction dates
        prediction = analytics_system.predict_business_growth("revenue", 30)
        assert isinstance(prediction.prediction_date, datetime)

def test_integration_workflow():
    """Integration test for the complete analytics workflow"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as tmp_file:
        db_path = tmp_file.name
    
    try:
        analytics = DataAnalyticsBI(db_path)
        
        # Step 1: Add sample data
        analytics.add_sample_data()
        
        # Step 2: Calculate customer lifetime values
        clv = analytics.calculate_customer_ltv("user1")
        assert clv is not None
        assert clv.predicted_clv > 0
        
        # Step 3: Train and use churn prediction
        churn_results = analytics.train_churn_prediction_model()
        assert "accuracy" in churn_results
        
        churn_report = analytics.generate_churn_prediction_report("user1")
        assert churn_report.user_id == "user1"
        
        # Step 4: Analyze feature adoption
        analytics.track_feature_usage("user1", "new_feature", 600)
        features = analytics.get_feature_adoption_analytics()
        assert len(features) > 0
        
        # Step 5: Add competitive benchmarks
        analytics.add_competitive_benchmark(
            "integration_metric", 95.0, "Test Competitor", 90.0, 88.0, "Integration Test"
        )
        
        competitive_metrics = analytics.get_competitive_analysis()
        assert len(competitive_metrics) > 0
        
        # Step 6: Generate growth predictions
        growth_prediction = analytics.predict_business_growth("revenue", 30)
        assert growth_prediction.metric_name == "revenue"
        
        # Step 7: Get comprehensive summary
        summary = analytics.get_analytics_summary()
        assert "customer_metrics" in summary
        assert "usage_metrics" in summary
        assert "revenue_metrics" in summary
        
        print("✅ Integration test completed successfully!")
        
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    # Run integration test
    test_integration_workflow()
    
    # Run pytest if available
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic integration test only")
        print("Install pytest to run full test suite: pip install pytest")