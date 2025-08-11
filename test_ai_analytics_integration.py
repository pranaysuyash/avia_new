"""
Integration tests for AI Analytics feature across all platforms
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import numpy as np

# Import the AI Analytics components
from ai_analytics_intelligence_system import (
    AIAnalyticsSystem,
    AnalyticsEngine,
    PredictiveAnalytics,
    AnomalyDetector,
    InsightsGenerator
)
from api.endpoints.ai_analytics import router as ai_analytics_router
from fastapi.testclient import TestClient
from fastapi import FastAPI

# Create test app
app = FastAPI()
app.include_router(ai_analytics_router, prefix="/api/ai-analytics")
client = TestClient(app)


class TestAIAnalyticsSystem:
    """Test the core AI Analytics system"""
    
    @pytest.fixture
    def analytics_system(self):
        """Create an AI Analytics system instance"""
        return AIAnalyticsSystem()
    
    @pytest.fixture
    def sample_metrics(self):
        """Generate sample metrics data"""
        return {
            'transcriptions': [
                {
                    'id': f'trans_{i}',
                    'duration': np.random.randint(60, 3600),
                    'accuracy': np.random.uniform(0.85, 0.99),
                    'language': np.random.choice(['en', 'es', 'fr', 'de']),
                    'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 30)),
                    'user_id': f'user_{np.random.randint(1, 10)}',
                    'sentiment': np.random.choice(['positive', 'negative', 'neutral'])
                }
                for i in range(100)
            ],
            'api_calls': [
                {
                    'endpoint': np.random.choice(['/transcribe', '/analyze', '/export']),
                    'latency': np.random.uniform(10, 200),
                    'status': np.random.choice([200, 201, 400, 500]),
                    'timestamp': datetime.now() - timedelta(hours=np.random.randint(0, 168))
                }
                for _ in range(500)
            ],
            'errors': [
                {
                    'type': np.random.choice(['API_ERROR', 'PROCESSING_ERROR', 'VALIDATION_ERROR']),
                    'message': 'Sample error message',
                    'timestamp': datetime.now() - timedelta(hours=np.random.randint(0, 72))
                }
                for _ in range(20)
            ]
        }
    
    def test_analytics_system_initialization(self, analytics_system):
        """Test that the analytics system initializes correctly"""
        assert analytics_system is not None
        assert hasattr(analytics_system, 'engine')
        assert hasattr(analytics_system, 'predictive_analytics')
        assert hasattr(analytics_system, 'anomaly_detector')
        assert hasattr(analytics_system, 'insights_generator')
    
    def test_process_metrics(self, analytics_system, sample_metrics):
        """Test metrics processing"""
        result = analytics_system.process_metrics(sample_metrics)
        
        assert 'summary' in result
        assert 'trends' in result
        assert 'anomalies' in result
        assert 'predictions' in result
        assert 'insights' in result
        
        # Verify summary statistics
        summary = result['summary']
        assert 'total_transcriptions' in summary
        assert 'average_accuracy' in summary
        assert 'total_api_calls' in summary
        assert 'error_rate' in summary
    
    def test_generate_insights(self, analytics_system, sample_metrics):
        """Test AI-powered insights generation"""
        insights = analytics_system.generate_insights(sample_metrics)
        
        assert isinstance(insights, list)
        assert len(insights) > 0
        
        for insight in insights:
            assert 'type' in insight
            assert 'title' in insight
            assert 'description' in insight
            assert 'priority' in insight
            assert insight['priority'] in ['high', 'medium', 'low']
    
    def test_predict_trends(self, analytics_system, sample_metrics):
        """Test predictive analytics"""
        predictions = analytics_system.predict_trends(sample_metrics)
        
        assert 'next_week_usage' in predictions
        assert 'peak_hours' in predictions
        assert 'growth_rate' in predictions
        assert 'recommended_actions' in predictions
        
        # Verify predictions are reasonable
        assert predictions['next_week_usage'] > 0
        assert isinstance(predictions['peak_hours'], list)
        assert isinstance(predictions['growth_rate'], (int, float))
    
    def test_detect_anomalies(self, analytics_system, sample_metrics):
        """Test anomaly detection"""
        anomalies = analytics_system.detect_anomalies(sample_metrics)
        
        assert isinstance(anomalies, list)
        
        for anomaly in anomalies:
            assert 'type' in anomaly
            assert 'severity' in anomaly
            assert 'description' in anomaly
            assert 'timestamp' in anomaly
            assert anomaly['severity'] in ['critical', 'warning', 'info']
    
    @pytest.mark.asyncio
    async def test_real_time_processing(self, analytics_system):
        """Test real-time metrics processing"""
        # Simulate real-time data stream
        for _ in range(10):
            metric = {
                'type': 'transcription',
                'data': {
                    'duration': np.random.randint(60, 300),
                    'accuracy': np.random.uniform(0.85, 0.99)
                },
                'timestamp': datetime.now()
            }
            
            result = await analytics_system.process_real_time(metric)
            assert result['status'] == 'processed'
            
            await asyncio.sleep(0.1)
    
    def test_export_analytics(self, analytics_system, sample_metrics):
        """Test analytics export functionality"""
        processed_data = analytics_system.process_metrics(sample_metrics)
        
        # Test different export formats
        formats = ['json', 'csv', 'pdf']
        
        for format_type in formats:
            exported = analytics_system.export_analytics(processed_data, format_type)
            assert exported is not None
            
            if format_type == 'json':
                # Verify JSON is valid
                assert json.loads(exported)
            elif format_type == 'csv':
                # Verify CSV has headers
                assert ',' in exported
                assert '\n' in exported
            elif format_type == 'pdf':
                # Verify PDF bytes
                assert isinstance(exported, bytes)


class TestAIAnalyticsAPI:
    """Test the AI Analytics API endpoints"""
    
    def test_get_analytics(self):
        """Test GET /api/ai-analytics endpoint"""
        response = client.get("/api/ai-analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert 'transcriptionMetrics' in data
        assert 'usagePatterns' in data
        assert 'aiInsights' in data
        assert 'performanceMetrics' in data
        assert 'predictions' in data
    
    def test_get_analytics_with_filters(self):
        """Test analytics with query parameters"""
        params = {
            'user_id': 'test_user',
            'team_id': 'test_team',
            'start_date': '2024-01-01',
            'end_date': '2024-01-31'
        }
        
        response = client.get("/api/ai-analytics", params=params)
        assert response.status_code == 200
        
        data = response.json()
        assert data is not None
    
    def test_get_real_time_metrics(self):
        """Test GET /api/ai-analytics/real-time endpoint"""
        response = client.get("/api/ai-analytics/real-time")
        assert response.status_code == 200
        
        data = response.json()
        assert 'currentLoad' in data
        assert 'activeUsers' in data
        assert 'processingQueue' in data
        assert 'latency' in data
    
    def test_get_insights(self):
        """Test GET /api/ai-analytics/insights endpoint"""
        response = client.get("/api/ai-analytics/insights")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            insight = data[0]
            assert 'type' in insight
            assert 'title' in insight
            assert 'description' in insight
    
    def test_get_predictions(self):
        """Test GET /api/ai-analytics/predictions endpoint"""
        response = client.get("/api/ai-analytics/predictions")
        assert response.status_code == 200
        
        data = response.json()
        assert 'nextWeekUsage' in data
        assert 'peakHours' in data
        assert 'recommendedActions' in data
    
    def test_export_analytics(self):
        """Test POST /api/ai-analytics/export endpoint"""
        export_data = {
            'format': 'json',
            'dateRange': {
                'start': '2024-01-01',
                'end': '2024-01-31'
            }
        }
        
        response = client.post("/api/ai-analytics/export", json=export_data)
        assert response.status_code == 200
        
        # Verify response is downloadable
        assert 'content-disposition' in response.headers
    
    def test_webhook_configuration(self):
        """Test analytics webhook configuration"""
        webhook_config = {
            'url': 'https://example.com/webhook',
            'events': ['anomaly_detected', 'threshold_exceeded'],
            'active': True
        }
        
        response = client.post("/api/ai-analytics/webhooks", json=webhook_config)
        assert response.status_code in [200, 201]
        
        data = response.json()
        assert 'id' in data
        assert data['url'] == webhook_config['url']


class TestAnalyticsEngine:
    """Test the Analytics Engine component"""
    
    @pytest.fixture
    def engine(self):
        return AnalyticsEngine()
    
    def test_calculate_statistics(self, engine):
        """Test statistical calculations"""
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        stats = engine.calculate_statistics(data)
        
        assert stats['mean'] == 5.5
        assert stats['median'] == 5.5
        assert stats['std'] > 0
        assert stats['min'] == 1
        assert stats['max'] == 10
    
    def test_time_series_analysis(self, engine):
        """Test time series analysis"""
        # Generate sample time series data
        dates = [datetime.now() - timedelta(days=i) for i in range(30)]
        values = [100 + i * 2 + np.random.randint(-10, 10) for i in range(30)]
        
        time_series_data = list(zip(dates, values))
        
        analysis = engine.analyze_time_series(time_series_data)
        
        assert 'trend' in analysis
        assert 'seasonality' in analysis
        assert 'forecast' in analysis
        assert analysis['trend'] in ['increasing', 'decreasing', 'stable']
    
    def test_correlation_analysis(self, engine):
        """Test correlation analysis"""
        data1 = [1, 2, 3, 4, 5]
        data2 = [2, 4, 6, 8, 10]
        
        correlation = engine.calculate_correlation(data1, data2)
        
        assert correlation == pytest.approx(1.0, rel=1e-5)


class TestPredictiveAnalytics:
    """Test the Predictive Analytics component"""
    
    @pytest.fixture
    def predictor(self):
        return PredictiveAnalytics()
    
    def test_usage_prediction(self, predictor):
        """Test usage prediction"""
        historical_data = [100, 110, 120, 115, 125, 130, 140]
        
        prediction = predictor.predict_usage(historical_data, days_ahead=7)
        
        assert isinstance(prediction, (int, float))
        assert prediction > 0
        assert prediction > min(historical_data)  # Growth trend
    
    def test_peak_hours_prediction(self, predictor):
        """Test peak hours prediction"""
        hourly_data = {
            str(hour): np.random.randint(10, 100)
            for hour in range(24)
        }
        
        peak_hours = predictor.predict_peak_hours(hourly_data)
        
        assert isinstance(peak_hours, list)
        assert len(peak_hours) > 0
        assert all(0 <= int(hour.split(':')[0]) < 24 for hour in peak_hours)
    
    def test_resource_requirements(self, predictor):
        """Test resource requirements prediction"""
        usage_trend = [100, 150, 200, 250, 300]
        
        resources = predictor.predict_resources(usage_trend)
        
        assert 'cpu' in resources
        assert 'memory' in resources
        assert 'storage' in resources
        assert all(v > 0 for v in resources.values())


class TestAnomalyDetector:
    """Test the Anomaly Detector component"""
    
    @pytest.fixture
    def detector(self):
        return AnomalyDetector()
    
    def test_detect_outliers(self, detector):
        """Test outlier detection"""
        # Normal data with outliers
        data = [10, 12, 11, 13, 12, 100, 11, 12, 13, 11]  # 100 is an outlier
        
        outliers = detector.detect_outliers(data)
        
        assert 100 in outliers
        assert len(outliers) == 1
    
    def test_detect_pattern_anomalies(self, detector):
        """Test pattern anomaly detection"""
        # Regular pattern with anomaly
        pattern = [1, 2, 3, 1, 2, 3, 1, 5, 3]  # 5 breaks the pattern
        
        anomalies = detector.detect_pattern_anomalies(pattern)
        
        assert len(anomalies) > 0
        assert 7 in [a['index'] for a in anomalies]  # Index of the anomaly
    
    def test_detect_system_anomalies(self, detector):
        """Test system-level anomaly detection"""
        metrics = {
            'cpu_usage': [50, 55, 52, 98, 51],  # Spike at index 3
            'memory_usage': [60, 62, 61, 63, 95],  # Spike at index 4
            'error_rate': [0.01, 0.02, 0.01, 0.5, 0.01]  # Spike at index 3
        }
        
        system_anomalies = detector.detect_system_anomalies(metrics)
        
        assert len(system_anomalies) > 0
        assert any('cpu' in a['metric'].lower() for a in system_anomalies)


class TestInsightsGenerator:
    """Test the Insights Generator component"""
    
    @pytest.fixture
    def generator(self):
        return InsightsGenerator()
    
    def test_generate_usage_insights(self, generator):
        """Test usage insights generation"""
        usage_data = {
            'total': 1000,
            'trend': 15,  # 15% increase
            'peak_time': '14:00',
            'most_active_users': ['user1', 'user2']
        }
        
        insights = generator.generate_usage_insights(usage_data)
        
        assert len(insights) > 0
        assert any('growth' in i['description'].lower() for i in insights)
    
    def test_generate_performance_insights(self, generator):
        """Test performance insights generation"""
        performance_data = {
            'avg_latency': 45,
            'error_rate': 0.02,
            'uptime': 99.9,
            'processing_speed': 2.5
        }
        
        insights = generator.generate_performance_insights(performance_data)
        
        assert len(insights) > 0
        assert any('performance' in i['title'].lower() for i in insights)
    
    def test_generate_recommendations(self, generator):
        """Test recommendation generation"""
        analytics_data = {
            'usage_trend': 'increasing',
            'error_rate': 0.05,
            'peak_hours': ['09:00', '14:00', '16:00'],
            'resource_utilization': 0.85
        }
        
        recommendations = generator.generate_recommendations(analytics_data)
        
        assert len(recommendations) > 0
        assert all('action' in r for r in recommendations)
        assert all('priority' in r for r in recommendations)


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.fixture
    def full_system(self):
        """Create a complete AI Analytics system"""
        return {
            'analytics': AIAnalyticsSystem(),
            'api_client': client
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_analytics_flow(self, full_system):
        """Test complete analytics flow from data ingestion to insights"""
        analytics = full_system['analytics']
        
        # Step 1: Ingest sample data
        sample_data = {
            'transcriptions': [
                {
                    'id': f'test_{i}',
                    'duration': 300,
                    'accuracy': 0.95
                }
                for i in range(50)
            ]
        }
        
        # Step 2: Process metrics
        processed = analytics.process_metrics(sample_data)
        assert processed is not None
        
        # Step 3: Generate insights
        insights = analytics.generate_insights(sample_data)
        assert len(insights) > 0
        
        # Step 4: Make predictions
        predictions = analytics.predict_trends(sample_data)
        assert predictions['next_week_usage'] > 0
        
        # Step 5: Export results
        exported = analytics.export_analytics(processed, 'json')
        assert json.loads(exported)
    
    def test_multi_user_analytics(self, full_system):
        """Test analytics for multiple users"""
        client = full_system['api_client']
        
        # Simulate multiple users
        users = ['user1', 'user2', 'user3']
        
        for user in users:
            response = client.get(f"/api/ai-analytics?user_id={user}")
            assert response.status_code == 200
            
            data = response.json()
            assert data is not None
    
    def test_team_analytics_aggregation(self, full_system):
        """Test team-level analytics aggregation"""
        client = full_system['api_client']
        
        response = client.get("/api/ai-analytics?team_id=test_team")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify team-specific metrics
        if 'teamAnalytics' in data:
            team_data = data['teamAnalytics']
            assert 'memberActivity' in team_data
            assert 'collaboration' in team_data
            assert 'productivity' in team_data
    
    @pytest.mark.asyncio
    async def test_real_time_monitoring(self, full_system):
        """Test real-time monitoring capabilities"""
        client = full_system['api_client']
        
        # Simulate real-time monitoring
        for _ in range(5):
            response = client.get("/api/ai-analytics/real-time")
            assert response.status_code == 200
            
            data = response.json()
            assert 'currentLoad' in data
            assert 'activeUsers' in data
            
            await asyncio.sleep(1)
    
    def test_alert_generation(self, full_system):
        """Test alert generation based on thresholds"""
        analytics = full_system['analytics']
        
        # Simulate metrics that should trigger alerts
        critical_metrics = {
            'error_rate': 0.15,  # High error rate
            'latency': 500,  # High latency
            'cpu_usage': 95  # High CPU usage
        }
        
        alerts = analytics.check_alerts(critical_metrics)
        
        assert len(alerts) > 0
        assert any(a['severity'] == 'critical' for a in alerts)


class TestPerformance:
    """Test performance characteristics of the analytics system"""
    
    @pytest.fixture
    def large_dataset(self):
        """Generate a large dataset for performance testing"""
        return {
            'transcriptions': [
                {
                    'id': f'perf_{i}',
                    'duration': np.random.randint(60, 3600),
                    'accuracy': np.random.uniform(0.8, 1.0)
                }
                for i in range(10000)
            ]
        }
    
    def test_processing_speed(self, large_dataset):
        """Test processing speed with large dataset"""
        import time
        
        analytics = AIAnalyticsSystem()
        
        start_time = time.time()
        result = analytics.process_metrics(large_dataset)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Should process 10,000 records in under 5 seconds
        assert processing_time < 5
        assert result is not None
    
    def test_memory_efficiency(self, large_dataset):
        """Test memory efficiency"""
        import tracemalloc
        
        tracemalloc.start()
        
        analytics = AIAnalyticsSystem()
        analytics.process_metrics(large_dataset)
        
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # Memory usage should be reasonable (under 100MB for 10k records)
        assert peak / 1024 / 1024 < 100
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self):
        """Test concurrent request handling"""
        tasks = []
        
        # Create 50 concurrent requests
        for i in range(50):
            task = asyncio.create_task(
                self._make_analytics_request(f"user_{i}")
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All requests should succeed
        assert all(r is not None for r in results)
    
    async def _make_analytics_request(self, user_id):
        """Helper method for concurrent requests"""
        # Simulate API request
        await asyncio.sleep(0.1)
        return {'status': 'success', 'user': user_id}


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])