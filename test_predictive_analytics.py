#!/usr/bin/env python3
"""
Test Suite for Predictive Analytics and Forecasting
Tests for Task 69: Build predictive analytics and forecasting
"""

import unittest
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from predictive_analytics import (
    ContentTrendPredictor, UserBehaviorPredictor, RevenueForecaster,
    MarketAnalyzer, PredictiveAnalyticsService, ForecastResult,
    ForecastType, ModelType, ScenarioAnalysis
)

class TestContentTrendPredictor(unittest.TestCase):
    """Test cases for ContentTrendPredictor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = ContentTrendPredictor(":memory:")  # Use in-memory database
        
        # Create sample data
        dates = pd.date_range(start='2023-01-01', periods=100, freq='D')
        self.sample_data = pd.DataFrame({
            'date': dates,
            'views': np.random.randint(100, 1000, 100),
            'engagement_rate': np.random.uniform(0.1, 0.8, 100)
        })
    
    def test_database_initialization(self):
        """Test database initialization"""
        # Database should be initialized without errors
        self.assertIsNotNone(self.predictor.db_path)
    
    def test_create_features(self):
        """Test feature creation for ML models"""
        features_df = self.predictor._create_features(self.sample_data)
        
        # Should have additional feature columns
        self.assertIn('day_of_week', features_df.columns)
        self.assertIn('month', features_df.columns)
        self.assertIn('is_weekend', features_df.columns)
        
        # Should have lag features
        self.assertIn('views_lag_1', features_df.columns)
        self.assertIn('views_lag_7', features_df.columns)
        
        # Should have rolling statistics
        self.assertIn('views_rolling_mean_7', features_df.columns)
        self.assertIn('views_rolling_std_7', features_df.columns)
    
    def test_fallback_forecast(self):
        """Test fallback forecast creation"""
        forecast = self.predictor._create_fallback_forecast(30)
        
        self.assertIsInstance(forecast, ForecastResult)
        self.assertEqual(len(forecast.predictions), 30)
        self.assertEqual(forecast.forecast_type, ForecastType.CONTENT_TRENDS)
        self.assertEqual(forecast.model_type, ModelType.LINEAR_REGRESSION)
        self.assertTrue(forecast.metadata.get('fallback', False))
    
    @patch('predictive_analytics.Prophet')
    def test_predict_with_prophet_mock(self, mock_prophet_class):
        """Test Prophet prediction with mocked Prophet"""
        # Mock Prophet model
        mock_model = Mock()
        mock_prophet_class.return_value = mock_model
        
        # Mock forecast result
        mock_forecast = pd.DataFrame({
            'yhat': [100, 110, 120, 130, 140] + [150] * 30,  # 5 historical + 30 future
            'yhat_lower': [90, 100, 110, 120, 130] + [140] * 30,
            'yhat_upper': [110, 120, 130, 140, 150] + [160] * 30
        })
        mock_model.predict.return_value = mock_forecast
        
        # Mock future dataframe
        mock_model.make_future_dataframe.return_value = pd.DataFrame({
            'ds': pd.date_range(start='2023-01-01', periods=35, freq='D')
        })
        
        result = self.predictor._predict_with_prophet(self.sample_data[:5], 30)
        
        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(len(result.predictions), 30)
        self.assertEqual(result.model_type, ModelType.PROPHET)
        self.assertIsNotNone(result.confidence_intervals)
        self.assertEqual(len(result.confidence_intervals), 30)
    
    def test_predict_content_trends_fallback(self):
        """Test content trend prediction with fallback"""
        # This should use fallback since Prophet might not be available
        result = self.predictor.predict_content_trends(self.sample_data, 30)
        
        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(len(result.predictions), 30)
        self.assertEqual(result.forecast_type, ForecastType.CONTENT_TRENDS)


class TestUserBehaviorPredictor(unittest.TestCase):
    """Test cases for UserBehaviorPredictor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.predictor = UserBehaviorPredictor(":memory:")
        
        # Create sample user features
        self.user_features = pd.DataFrame({
            'last_login': [datetime.now() - timedelta(days=i) for i in range(1, 11)],
            'session_count': np.random.randint(5, 50, 10),
            'total_session_time': np.random.uniform(100, 1000, 10),
            'pages_viewed': np.random.randint(10, 200, 10),
            'actions_taken': np.random.randint(5, 100, 10)
        })
        
        # Create sample user engagement data
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        self.user_data = pd.DataFrame({
            'date': dates,
            'session_duration': np.random.uniform(5, 45, 30),
            'pages_viewed': np.random.poisson(8, 30),
            'actions_taken': np.random.poisson(3, 30)
        })
    
    def test_prepare_churn_features(self):
        """Test churn feature preparation"""
        features = self.predictor._prepare_churn_features(self.user_features)
        
        # Should have derived features
        self.assertIn('days_since_last_login', features.columns)
        self.assertIn('avg_session_duration', features.columns)
        self.assertIn('engagement_rate', features.columns)
        
        # Should not have missing values
        self.assertFalse(features.isnull().any().any())
    
    def test_predict_user_churn(self):
        """Test user churn prediction"""
        result = self.predictor.predict_user_churn(self.user_features)
        
        # Should return prediction results
        self.assertIn('churn_probabilities', result)
        self.assertIn('churn_predictions', result)
        self.assertIn('feature_importance', result)
        
        # Should have correct number of predictions
        self.assertEqual(len(result['churn_probabilities']), len(self.user_features))
        self.assertEqual(len(result['churn_predictions']), len(self.user_features))
    
    def test_predict_user_engagement(self):
        """Test user engagement prediction"""
        result = self.predictor.predict_user_engagement(self.user_data, 30)
        
        self.assertIsInstance(result, ForecastResult)
        self.assertEqual(result.forecast_type, ForecastType.USER_BEHAVIOR)
        self.assertEqual(len(result.predictions), 30)
    
    def test_fallback_engagement_forecast(self):
        """Test fallback engagement forecast"""
        forecast = self.predictor._create_fallback_engagement_forecast(30)
        
        self.assertIsInstance(forecast, ForecastResult)
        self.assertEqual(len(forecast.predictions), 30)
        self.assertEqual(forecast.forecast_type, ForecastType.USER_BEHAVIOR)
        self.assertTrue(forecast.metadata.get('fallback', False))


class TestRevenueForecaster(unittest.TestCase):
    """Test cases for RevenueForecaster class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.forecaster = RevenueForecaster()
        
        # Create sample revenue data
        dates = pd.date_range(start='2023-01-01', periods=12, freq='M')
        self.revenue_data = pd.DataFrame({
            'date': dates,
            'revenue': np.random.uniform(50000, 100000, 12)
        })
    
    def test_generate_revenue_scenarios(self):
        """Test revenue scenario generation"""
        base_predictions = [100000, 110000, 120000, 130000]
        scenarios = self.forecaster._generate_revenue_scenarios(base_predictions)
        
        # Should have all scenario types
        expected_scenarios = ['base_case', 'optimistic', 'pessimistic', 'high_growth', 'recession']
        for scenario in expected_scenarios:
            self.assertIn(scenario, scenarios)
            self.assertEqual(len(scenarios[scenario]), len(base_predictions))
        
        # Optimistic should be higher than base
        self.assertTrue(all(o > b for o, b in zip(scenarios['optimistic'], scenarios['base_case'])))
        
        # Pessimistic should be lower than base
        self.assertTrue(all(p < b for p, b in zip(scenarios['pessimistic'], scenarios['base_case'])))
    
    def test_analyze_scenarios(self):
        """Test scenario analysis"""
        scenarios = {
            'base_case': [100, 110, 120],
            'optimistic': [120, 132, 144],
            'pessimistic': [80, 88, 96],
            'high_growth': [100, 112, 125],
            'recession': [100, 109, 117]
        }
        
        analysis = self.forecaster._analyze_scenarios(scenarios)
        
        self.assertIsInstance(analysis, ScenarioAnalysis)
        self.assertEqual(len(analysis.expected_value), 3)
        self.assertIn('value_at_risk_5%', analysis.risk_metrics)
        self.assertIn('upside_potential', analysis.risk_metrics)
        self.assertIn('downside_risk', analysis.risk_metrics)
    
    def test_forecast_revenue(self):
        """Test revenue forecasting"""
        result = self.forecaster.forecast_revenue(self.revenue_data, 6, True)
        
        # Should return forecast results
        self.assertIn('base_forecast', result)
        self.assertIn('forecast_months', result)
        self.assertIn('scenarios', result)
        self.assertIn('scenario_analysis', result)
        
        # Base forecast should be a ForecastResult
        self.assertIsInstance(result['base_forecast'], ForecastResult)


class TestMarketAnalyzer(unittest.TestCase):
    """Test cases for MarketAnalyzer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = MarketAnalyzer()
        
        # Create sample market data
        dates = pd.date_range(start='2023-01-01', periods=12, freq='M')
        self.market_data = pd.DataFrame({
            'date': dates,
            'market_size': np.random.uniform(1000000, 5000000, 12),
            'revenue': np.random.uniform(50000, 200000, 12)
        })
    
    def test_analyze_market_size(self):
        """Test market size analysis"""
        result = self.analyzer._analyze_market_size(self.market_data)
        
        self.assertIn('current_market_size', result)
        self.assertIn('yoy_growth', result)
        self.assertIn('trend', result)
        
        # Trend should be either 'growing' or 'declining'
        self.assertIn(result['trend'], ['growing', 'declining'])
    
    def test_calculate_growth_rate(self):
        """Test growth rate calculation"""
        result = self.analyzer._calculate_growth_rate(self.market_data)
        
        self.assertIn('monthly_growth_rate', result)
        self.assertIn('quarterly_growth_rate', result)
        self.assertIn('compound_annual_growth_rate', result)
        
        # Growth rates should be numeric
        self.assertIsInstance(result['monthly_growth_rate'], (int, float))
        self.assertIsInstance(result['quarterly_growth_rate'], (int, float))
        self.assertIsInstance(result['compound_annual_growth_rate'], (int, float))
    
    def test_detect_seasonality(self):
        """Test seasonality detection"""
        result = self.analyzer._detect_seasonality(self.market_data)
        
        if 'seasonal_index' in result:
            self.assertIn('peak_months', result)
            self.assertIn('low_months', result)
            self.assertIn('seasonality_strength', result)
            
            # Should have 12 months in seasonal index
            self.assertEqual(len(result['seasonal_index']), 12)
    
    def test_analyze_competition(self):
        """Test competitive analysis"""
        result = self.analyzer._analyze_competition(self.market_data)
        
        # Should return competitive metrics
        self.assertIn('market_share', result)
        self.assertIn('competitor_count', result)
        self.assertIn('market_concentration', result)
        self.assertIn('competitive_intensity', result)
    
    def test_identify_opportunities(self):
        """Test opportunity identification"""
        opportunities = self.analyzer._identify_opportunities(self.market_data)
        
        self.assertIsInstance(opportunities, list)
        
        if opportunities:
            # Each opportunity should have required fields
            for opp in opportunities:
                self.assertIn('opportunity', opp)
                self.assertIn('potential_value', opp)
                self.assertIn('probability', opp)
                self.assertIn('time_to_market', opp)
                self.assertIn('investment_required', opp)
    
    def test_analyze_market_trends(self):
        """Test comprehensive market trend analysis"""
        result = self.analyzer.analyze_market_trends(self.market_data)
        
        # Should return all analysis components
        self.assertIn('market_size_trend', result)
        self.assertIn('growth_rate', result)
        self.assertIn('seasonality', result)
        self.assertIn('competitive_landscape', result)
        self.assertIn('opportunities', result)


class TestPredictiveAnalyticsService(unittest.TestCase):
    """Test cases for PredictiveAnalyticsService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = PredictiveAnalyticsService(":memory:")
        
        # Create sample data sources
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        
        self.data_sources = {
            'content_data': pd.DataFrame({
                'date': dates,
                'views': np.random.randint(100, 1000, 30)
            }),
            'user_data': pd.DataFrame({
                'date': dates,
                'session_duration': np.random.uniform(5, 45, 30),
                'pages_viewed': np.random.poisson(8, 30),
                'actions_taken': np.random.poisson(3, 30)
            }),
            'revenue_data': pd.DataFrame({
                'date': pd.date_range(start='2023-01-01', periods=12, freq='M'),
                'revenue': np.random.uniform(50000, 100000, 12)
            }),
            'market_data': pd.DataFrame({
                'date': pd.date_range(start='2023-01-01', periods=12, freq='M'),
                'market_size': np.random.uniform(1000000, 5000000, 12),
                'revenue': np.random.uniform(50000, 200000, 12)
            }),
            'user_features': pd.DataFrame({
                'last_login': [datetime.now() - timedelta(days=i) for i in range(1, 6)],
                'session_count': np.random.randint(5, 50, 5),
                'total_session_time': np.random.uniform(100, 1000, 5),
                'pages_viewed': np.random.randint(10, 200, 5),
                'actions_taken': np.random.randint(5, 100, 5)
            })
        }
    
    def test_service_initialization(self):
        """Test service initialization"""
        self.assertIsNotNone(self.service.content_predictor)
        self.assertIsNotNone(self.service.user_predictor)
        self.assertIsNotNone(self.service.revenue_forecaster)
        self.assertIsNotNone(self.service.market_analyzer)
    
    def test_generate_comprehensive_forecast(self):
        """Test comprehensive forecast generation"""
        result = self.service.generate_comprehensive_forecast(self.data_sources, 30)
        
        # Should return structured results
        self.assertIn('forecast_date', result)
        self.assertIn('forecast_horizon_days', result)
        self.assertIn('forecasts', result)
        self.assertIn('summary', result)
        
        # Should have forecast for each data source
        forecasts = result['forecasts']
        self.assertIn('content_trends', forecasts)
        self.assertIn('user_behavior', forecasts)
        self.assertIn('revenue', forecasts)
        self.assertIn('market_analysis', forecasts)
        self.assertIn('churn_prediction', forecasts)
    
    def test_generate_forecast_summary(self):
        """Test forecast summary generation"""
        # Create mock forecasts
        mock_forecasts = {
            'content_trends': Mock(predictions=[100, 110, 120, 130]),
            'churn_prediction': {'high_risk_users': 5, 'model_accuracy': 0.85},
            'revenue': {
                'scenarios': {
                    'base_case': [10000, 11000, 12000],
                    'optimistic': [12000, 13200, 14400]
                }
            }
        }
        
        summary = self.service._generate_forecast_summary(mock_forecasts)
        
        self.assertIn('key_insights', summary)
        self.assertIn('recommendations', summary)
        self.assertIn('risk_factors', summary)
        self.assertIn('opportunities', summary)
    
    def test_get_forecast_accuracy_empty(self):
        """Test getting forecast accuracy when no history exists"""
        accuracy = self.service.get_forecast_accuracy()
        
        # Should return empty dict when no history
        self.assertEqual(accuracy, {})


class TestDataStructures(unittest.TestCase):
    """Test data structures and models"""
    
    def test_forecast_result(self):
        """Test ForecastResult data structure"""
        result = ForecastResult(
            forecast_type=ForecastType.CONTENT_TRENDS,
            model_type=ModelType.PROPHET,
            predictions=[100, 110, 120],
            confidence_intervals=[(90, 110), (100, 120), (110, 130)],
            dates=[datetime.now() + timedelta(days=i) for i in range(3)],
            accuracy_metrics={'mae': 5.0, 'rmse': 7.0},
            feature_importance={'feature1': 0.6, 'feature2': 0.4}
        )
        
        self.assertEqual(result.forecast_type, ForecastType.CONTENT_TRENDS)
        self.assertEqual(result.model_type, ModelType.PROPHET)
        self.assertEqual(len(result.predictions), 3)
        self.assertEqual(len(result.confidence_intervals), 3)
        self.assertEqual(len(result.dates), 3)
        self.assertIn('mae', result.accuracy_metrics)
        self.assertIn('feature1', result.feature_importance)
    
    def test_scenario_analysis(self):
        """Test ScenarioAnalysis data structure"""
        analysis = ScenarioAnalysis(
            scenario_name="Test Scenario",
            base_case=[100, 110, 120],
            optimistic_case=[120, 132, 144],
            pessimistic_case=[80, 88, 96],
            probability_weights={'base': 0.6, 'optimistic': 0.2, 'pessimistic': 0.2},
            expected_value=[104, 114.4, 124.8],
            risk_metrics={'var': 80, 'upside': 24}
        )
        
        self.assertEqual(analysis.scenario_name, "Test Scenario")
        self.assertEqual(len(analysis.base_case), 3)
        self.assertEqual(len(analysis.optimistic_case), 3)
        self.assertEqual(len(analysis.pessimistic_case), 3)
        self.assertEqual(len(analysis.expected_value), 3)
        self.assertIn('var', analysis.risk_metrics)


def run_integration_tests():
    """Run integration tests"""
    print("\n" + "="*50)
    print("INTEGRATION TESTS")
    print("="*50)
    
    try:
        service = PredictiveAnalyticsService(":memory:")
        
        # Test end-to-end workflow
        print("Testing end-to-end predictive analytics workflow...")
        
        # Generate sample data
        dates = pd.date_range(start='2023-01-01', periods=30, freq='D')
        content_data = pd.DataFrame({
            'date': dates,
            'views': np.random.randint(100, 1000, 30)
        })
        
        # Test content trend prediction
        result = service.content_predictor.predict_content_trends(content_data, 7)
        print(f"✓ Content trend prediction: {len(result.predictions)} predictions generated")
        
        # Test user behavior prediction
        user_features = pd.DataFrame({
            'last_login': [datetime.now() - timedelta(days=i) for i in range(1, 6)],
            'session_count': [20, 15, 30, 25, 10],
            'total_session_time': [500, 300, 800, 600, 200],
            'pages_viewed': [100, 80, 150, 120, 50],
            'actions_taken': [50, 40, 75, 60, 25]
        })
        
        churn_result = service.user_predictor.predict_user_churn(user_features)
        print(f"✓ Churn prediction: {len(churn_result['churn_probabilities'])} users analyzed")
        
        # Test revenue forecasting
        revenue_data = pd.DataFrame({
            'date': pd.date_range(start='2023-01-01', periods=12, freq='M'),
            'revenue': [50000 + i*2000 + np.random.randint(-5000, 5000) for i in range(12)]
        })
        
        revenue_result = service.revenue_forecaster.forecast_revenue(revenue_data, 6)
        print(f"✓ Revenue forecasting: 6-month forecast generated")
        
        print("✓ All integration tests passed!")
        
    except Exception as e:
        print(f"✗ Integration test failed: {e}")
        import traceback
        traceback.print_exc()


def run_performance_tests():
    """Run performance tests"""
    print("\n" + "="*50)
    print("PERFORMANCE TESTS")
    print("="*50)
    
    import time
    
    service = PredictiveAnalyticsService(":memory:")
    
    # Test with different data sizes
    data_sizes = [30, 100, 365, 1000]
    
    for size in data_sizes:
        # Generate data
        dates = pd.date_range(start='2023-01-01', periods=size, freq='D')
        data = pd.DataFrame({
            'date': dates,
            'views': np.random.randint(100, 1000, size)
        })
        
        # Time the prediction
        start_time = time.time()
        result = service.content_predictor.predict_content_trends(data, 30)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        print(f"Data size: {size:4d} days | Processing time: {processing_time:.3f}s | "
              f"Rate: {size/processing_time:.1f} days/sec")


if __name__ == '__main__':
    # Run unit tests
    print("Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run integration tests
    run_integration_tests()
    
    # Run performance tests
    run_performance_tests()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)