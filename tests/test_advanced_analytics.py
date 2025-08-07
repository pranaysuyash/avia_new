"""
Tests for Advanced Analytics System
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from services.advanced_analytics_service import (
    analytics_service,
    AnalyticsQuery,
    AnalyticsResult,
    ReportType,
    TimeGranularity
)
from api.database import User, Transcript, Team, APIKey, AuditLog


class TestAdvancedAnalyticsService:
    """Test advanced analytics service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_users(self):
        """Create sample users for analytics"""
        users = []
        for i in range(20):
            user = Mock(spec=User)
            user.id = i + 1
            user.username = f"user{i + 1}"
            user.email = f"user{i + 1}@example.com"
            user.created_at = datetime.utcnow() - timedelta(days=i * 5)
            user.subscription_tier = ["basic", "pro", "enterprise"][i % 3]
            user.is_active = i % 7 != 0  # Some inactive users
            user.last_login = datetime.utcnow() - timedelta(days=i % 10)
            users.append(user)
        return users
    
    @pytest.fixture
    def sample_transcripts(self):
        """Create sample transcripts for analytics"""
        transcripts = []
        for i in range(100):
            transcript = Mock(spec=Transcript)
            transcript.id = i + 1
            transcript.user_id = (i % 20) + 1
            transcript.created_at = datetime.utcnow() - timedelta(days=i // 5)
            transcript.duration = 60 + (i * 30)  # 1-50 minutes
            transcript.file_size = 1024 * 1024 * (1 + i % 10)  # 1-10MB
            transcript.language = ["en", "es", "fr"][i % 3]
            transcript.status = "completed" if i % 10 != 0 else "failed"
            transcripts.append(transcript)
        return transcripts
    
    @pytest.fixture
    def sample_api_calls(self):
        """Create sample API calls for analytics"""
        calls = []
        for i in range(500):
            call = Mock()
            call.id = i + 1
            call.user_id = (i % 20) + 1
            call.endpoint = ["/api/v1/transcripts", "/api/v1/users", "/api/v1/teams"][i % 3]
            call.method = ["GET", "POST", "PUT", "DELETE"][i % 4]
            call.status_code = 200 if i % 15 != 0 else [400, 401, 404, 500][i % 4]
            call.response_time = 50 + (i % 100) * 5  # 50-550ms
            call.timestamp = datetime.utcnow() - timedelta(minutes=i)
            calls.append(call)
        return calls
    
    @pytest.mark.asyncio
    async def test_generate_user_activity_report(self, mock_db, sample_users, sample_transcripts):
        """Test generating user activity analytics"""
        # Setup query
        query = AnalyticsQuery(
            report_type=ReportType.USER_ACTIVITY,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            granularity=TimeGranularity.DAILY
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            sample_users,
            sample_transcripts
        ]
        
        # Generate analytics
        result = await analytics_service.generate_analytics(
            db=mock_db,
            query=query,
            user_id=1
        )
        
        # Verify result structure
        assert isinstance(result, AnalyticsResult)
        assert result.report_type == ReportType.USER_ACTIVITY
        assert "daily_active_users" in result.data
        assert "transcription_activity" in result.data
        assert len(result.insights) > 0
    
    @pytest.mark.asyncio
    async def test_generate_usage_patterns_report(self, mock_db, sample_transcripts, sample_api_calls):
        """Test generating usage patterns analytics"""
        query = AnalyticsQuery(
            report_type=ReportType.USAGE_PATTERNS,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow(),
            granularity=TimeGranularity.HOURLY
        )
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            sample_transcripts,
            sample_api_calls
        ]
        
        result = await analytics_service.generate_analytics(
            db=mock_db,
            query=query,
            user_id=1
        )
        
        assert result.report_type == ReportType.USAGE_PATTERNS
        assert "peak_hours" in result.data
        assert "endpoint_usage" in result.data
        assert "language_distribution" in result.data
    
    @pytest.mark.asyncio
    async def test_generate_revenue_analytics(self, mock_db, sample_users):
        """Test generating revenue analytics"""
        # Add subscription data to users
        revenue_data = []
        for user in sample_users:
            if user.subscription_tier == "pro":
                amount = 29.99
            elif user.subscription_tier == "enterprise":
                amount = 99.99
            else:
                amount = 0.0
            
            revenue_item = Mock()
            revenue_item.user_id = user.id
            revenue_item.amount = amount
            revenue_item.created_at = user.created_at
            revenue_data.append(revenue_item)
        
        query = AnalyticsQuery(
            report_type=ReportType.REVENUE,
            start_date=datetime.utcnow() - timedelta(days=90),
            end_date=datetime.utcnow(),
            granularity=TimeGranularity.MONTHLY
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = revenue_data
        
        result = await analytics_service.generate_analytics(
            db=mock_db,
            query=query,
            user_id=1
        )
        
        assert result.report_type == ReportType.REVENUE
        assert "monthly_revenue" in result.data
        assert "subscription_breakdown" in result.data
        assert "churn_rate" in result.data
    
    @pytest.mark.asyncio
    async def test_generate_retention_analytics(self, mock_db, sample_users):
        """Test generating user retention analytics"""
        query = AnalyticsQuery(
            report_type=ReportType.RETENTION,
            start_date=datetime.utcnow() - timedelta(days=180),
            end_date=datetime.utcnow(),
            cohort_period="monthly"
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = sample_users
        
        result = await analytics_service.generate_analytics(
            db=mock_db,
            query=query,
            user_id=1
        )
        
        assert result.report_type == ReportType.RETENTION
        assert "cohort_analysis" in result.data
        assert "retention_rates" in result.data
        assert "churn_analysis" in result.data
    
    @pytest.mark.asyncio
    async def test_ai_insights_generation(self, mock_db, sample_users, sample_transcripts):
        """Test AI-powered insights generation"""
        # Mock LLM service
        with patch('services.advanced_analytics_service.llm_service.generate_insights') as mock_llm:
            mock_llm.return_value = [
                "User activity has increased by 15% over the last month",
                "Peak usage occurs between 2-4 PM daily",
                "Enterprise users show 40% higher retention rates"
            ]
            
            query = AnalyticsQuery(
                report_type=ReportType.USER_ACTIVITY,
                start_date=datetime.utcnow() - timedelta(days=30),
                end_date=datetime.utcnow(),
                include_ai_insights=True
            )
            
            mock_db.query.return_value.filter.return_value.all.side_effect = [
                sample_users,
                sample_transcripts
            ]
            
            result = await analytics_service.generate_analytics(
                db=mock_db,
                query=query,
                user_id=1
            )
            
            assert len(result.insights) == 3
            assert "increased by 15%" in result.insights[0]
            mock_llm.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_custom_metrics_calculation(self, mock_db, sample_transcripts):
        """Test custom metrics calculation"""
        query = AnalyticsQuery(
            report_type=ReportType.CUSTOM,
            custom_metrics=[
                {"name": "avg_duration", "type": "average", "field": "duration"},
                {"name": "total_files", "type": "count", "field": "id"},
                {"name": "success_rate", "type": "percentage", "field": "status", "value": "completed"}
            ]
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts
        
        result = await analytics_service.generate_analytics(
            db=mock_db,
            query=query,
            user_id=1
        )
        
        assert "avg_duration" in result.data
        assert "total_files" in result.data
        assert "success_rate" in result.data
        assert result.data["total_files"] == len(sample_transcripts)
    
    @pytest.mark.asyncio
    async def test_comparative_analysis(self, mock_db, sample_users):
        """Test comparative analysis between periods"""
        query = AnalyticsQuery(
            report_type=ReportType.USER_ACTIVITY,
            start_date=datetime.utcnow() - timedelta(days=30),
            end_date=datetime.utcnow(),
            compare_previous_period=True
        )
        
        # Mock current and previous period data
        current_users = sample_users[:15]
        previous_users = sample_users[:10]
        
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            current_users,   # Current period
            previous_users   # Previous period
        ]
        
        result = await analytics_service.generate_analytics(
            db=mock_db,
            query=query,
            user_id=1
        )
        
        assert "comparison" in result.data
        assert "growth_rate" in result.data["comparison"]
        assert "period_over_period_change" in result.data["comparison"]
    
    @pytest.mark.asyncio
    async def test_export_analytics_data(self, mock_db, sample_transcripts):
        """Test exporting analytics data in different formats"""
        query = AnalyticsQuery(
            report_type=ReportType.USER_ACTIVITY,
            start_date=datetime.utcnow() - timedelta(days=7),
            end_date=datetime.utcnow()
        )
        
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts[:10]
        
        # Test CSV export
        csv_data = await analytics_service.export_analytics(
            db=mock_db,
            query=query,
            format="csv",
            user_id=1
        )
        
        assert isinstance(csv_data, bytes)
        assert b"timestamp" in csv_data
        
        # Test Excel export
        excel_data = await analytics_service.export_analytics(
            db=mock_db,
            query=query,
            format="xlsx",
            user_id=1
        )
        
        assert isinstance(excel_data, bytes)
        assert len(excel_data) > 0
        
        # Test JSON export
        json_data = await analytics_service.export_analytics(
            db=mock_db,
            query=query,
            format="json",
            user_id=1
        )
        
        parsed_data = json.loads(json_data)
        assert "data" in parsed_data
        assert "metadata" in parsed_data
    
    @pytest.mark.asyncio
    async def test_scheduled_reports(self, mock_db):
        """Test scheduling automated reports"""
        schedule_config = {
            "report_type": "USER_ACTIVITY",
            "frequency": "weekly",
            "recipients": ["admin@example.com"],
            "format": "pdf"
        }
        
        with patch('services.advanced_analytics_service.scheduler.schedule_report') as mock_schedule:
            mock_schedule.return_value = {"schedule_id": "sched_123", "next_run": datetime.utcnow() + timedelta(days=7)}
            
            result = await analytics_service.schedule_report(
                db=mock_db,
                config=schedule_config,
                user_id=1
            )
            
            assert result["schedule_id"] == "sched_123"
            assert "next_run" in result
            mock_schedule.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_real_time_metrics(self, mock_db):
        """Test real-time metrics collection"""
        # Mock real-time data
        real_time_data = {
            "active_users": 25,
            "concurrent_transcriptions": 8,
            "api_requests_per_minute": 150,
            "error_rate": 2.1,
            "avg_response_time": 245
        }
        
        with patch('services.advanced_analytics_service.metrics_collector.get_real_time_metrics') as mock_metrics:
            mock_metrics.return_value = real_time_data
            
            metrics = await analytics_service.get_real_time_metrics(mock_db)
            
            assert metrics["active_users"] == 25
            assert metrics["concurrent_transcriptions"] == 8
            assert "timestamp" in metrics
    
    @pytest.mark.asyncio
    async def test_predictive_analytics(self, mock_db, sample_users):
        """Test predictive analytics and forecasting"""
        # Historical data for prediction
        historical_data = []
        for i in range(90):  # 90 days of data
            date = datetime.utcnow() - timedelta(days=i)
            data_point = {
                "date": date,
                "active_users": 100 + (i % 20) - 10,  # Simulated growth
                "revenue": 5000 + (i * 50) + (i % 100),
                "new_signups": 5 + (i % 10)
            }
            historical_data.append(data_point)
        
        with patch('services.advanced_analytics_service.ml_service.predict_trends') as mock_predict:
            mock_predict.return_value = {
                "predictions": {
                    "active_users_30d": 150,
                    "revenue_30d": 8500,
                    "churn_rate_30d": 5.2
                },
                "confidence_interval": {"lower": 0.85, "upper": 0.95}
            }
            
            predictions = await analytics_service.generate_predictions(
                db=mock_db,
                historical_data=historical_data,
                forecast_days=30
            )
            
            assert "active_users_30d" in predictions["predictions"]
            assert "confidence_interval" in predictions


class TestAdvancedAnalyticsAPI:
    """Test advanced analytics API endpoints"""
    
    @pytest.fixture
    def client(self, test_app):
        """Get test client"""
        return test_app
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        return {"Authorization": "Bearer test_token"}
    
    @pytest.mark.asyncio
    async def test_generate_report_endpoint(self, client, auth_headers):
        """Test generating analytics report"""
        mock_result = AnalyticsResult(
            report_type=ReportType.USER_ACTIVITY,
            data={"active_users": 100},
            insights=["User activity is growing"],
            generated_at=datetime.utcnow(),
            query_time_ms=250
        )
        
        with patch('services.advanced_analytics_service.analytics_service.generate_analytics') as mock_generate:
            mock_generate.return_value = mock_result
            
            response = await client.post(
                "/api/v1/analytics/generate",
                json={
                    "report_type": "user_activity",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "granularity": "daily"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["report_type"] == "user_activity"
            assert data["data"]["active_users"] == 100
    
    @pytest.mark.asyncio
    async def test_export_report_endpoint(self, client, auth_headers):
        """Test exporting analytics report"""
        with patch('services.advanced_analytics_service.analytics_service.export_analytics') as mock_export:
            mock_export.return_value = b"Date,Users,Revenue\n2024-01-01,100,5000"
            
            response = await client.post(
                "/api/v1/analytics/export",
                json={
                    "report_type": "user_activity",
                    "format": "csv",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"
    
    @pytest.mark.asyncio
    async def test_real_time_metrics_endpoint(self, client, auth_headers):
        """Test real-time metrics endpoint"""
        mock_metrics = {
            "active_users": 42,
            "api_requests_per_minute": 125,
            "avg_response_time": 180,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        with patch('services.advanced_analytics_service.analytics_service.get_real_time_metrics') as mock_get:
            mock_get.return_value = mock_metrics
            
            response = await client.get(
                "/api/v1/analytics/realtime",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["active_users"] == 42
    
    @pytest.mark.asyncio
    async def test_schedule_report_endpoint(self, client, auth_headers):
        """Test scheduling automated reports"""
        with patch('services.advanced_analytics_service.analytics_service.schedule_report') as mock_schedule:
            mock_schedule.return_value = {
                "schedule_id": "sched_456",
                "next_run": "2024-02-01T00:00:00Z"
            }
            
            response = await client.post(
                "/api/v1/analytics/schedule",
                json={
                    "report_type": "revenue",
                    "frequency": "monthly",
                    "recipients": ["admin@example.com"],
                    "format": "pdf"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["schedule_id"] == "sched_456"
    
    @pytest.mark.asyncio
    async def test_get_insights_endpoint(self, client, auth_headers):
        """Test getting AI-powered insights"""
        mock_insights = [
            "Revenue has grown 25% this quarter",
            "Mobile usage increased 40% last month",
            "Peak hours shifted 2 hours earlier"
        ]
        
        with patch('services.advanced_analytics_service.analytics_service.get_insights') as mock_get:
            mock_get.return_value = mock_insights
            
            response = await client.get(
                "/api/v1/analytics/insights",
                params={"period": "30d"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["insights"]) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])