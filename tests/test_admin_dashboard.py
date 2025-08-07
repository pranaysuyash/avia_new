"""
Tests for Admin Dashboard System
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from services.admin_dashboard_service import (
    admin_dashboard_service,
    SystemMetrics,
    UserStats,
    AdminDashboardStats
)
from api.database import User, Transcript, Team, APIKey, AuditLog


class TestAdminDashboardService:
    """Test admin dashboard service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_users(self):
        """Create sample users"""
        users = []
        for i in range(10):
            user = Mock(spec=User)
            user.id = i + 1
            user.username = f"testuser{i + 1}"
            user.email = f"test{i + 1}@example.com"
            user.created_at = datetime.utcnow() - timedelta(days=i * 10)
            user.subscription_tier = "pro" if i % 3 == 0 else "basic"
            user.is_active = i % 5 != 0  # Some inactive users
            users.append(user)
        return users
    
    @pytest.fixture
    def sample_transcripts(self):
        """Create sample transcripts"""
        transcripts = []
        for i in range(50):
            transcript = Mock(spec=Transcript)
            transcript.id = i + 1
            transcript.user_id = (i % 10) + 1
            transcript.created_at = datetime.utcnow() - timedelta(days=i // 5)
            transcript.duration = 300 + (i * 60)
            transcript.file_size = 1024 * 1024 * (i + 1)  # 1MB to 50MB
            transcripts.append(transcript)
        return transcripts
    
    @pytest.fixture
    def sample_audit_logs(self):
        """Create sample audit logs"""
        logs = []
        for i in range(100):
            log = Mock(spec=AuditLog)
            log.id = i + 1
            log.user_id = (i % 10) + 1
            log.action = f"action_{i % 5}"
            log.timestamp = datetime.utcnow() - timedelta(hours=i)
            log.ip_address = "192.168.1.1"
            log.status = "success" if i % 4 != 0 else "error"
            logs.append(log)
        return logs
    
    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self, mock_db, sample_users, sample_transcripts):
        """Test getting dashboard statistics"""
        # Setup mocks for various counts
        mock_db.query.return_value.count.side_effect = [
            len(sample_users),      # Total users
            len([u for u in sample_users if u.is_active]),  # Active users
            len(sample_transcripts), # Total transcripts
            5,  # Failed transcripts
            3,  # Teams
            25, # API keys
            sum(t.file_size for t in sample_transcripts),  # Storage used
            0   # System errors today
        ]
        
        # Mock user registration stats
        mock_db.query.return_value.filter.return_value.count.side_effect = [5, 3, 2]  # Last 30, 7, 1 days
        
        # Test getting stats
        stats = await admin_dashboard_service.get_dashboard_stats(mock_db)
        
        # Verify stats
        assert stats.total_users == len(sample_users)
        assert stats.active_users == len([u for u in sample_users if u.is_active])
        assert stats.total_transcripts == len(sample_transcripts)
        assert stats.storage_used > 0
        assert stats.new_users_30d == 5
        assert stats.new_users_7d == 3
        assert stats.new_users_24h == 2
    
    @pytest.mark.asyncio
    async def test_get_system_metrics(self, mock_db):
        """Test getting system metrics"""
        # Mock system info
        with patch('psutil.cpu_percent') as mock_cpu, \
             patch('psutil.virtual_memory') as mock_memory, \
             patch('psutil.disk_usage') as mock_disk:
            
            mock_cpu.return_value = 45.5
            mock_memory.return_value = Mock(percent=67.3, used=8 * 1024**3, total=12 * 1024**3)
            mock_disk.return_value = Mock(percent=82.1, used=100 * 1024**3, total=120 * 1024**3)
            
            # Mock database connection count
            mock_db.execute.return_value.fetchone.return_value = (15,)
            
            metrics = await admin_dashboard_service.get_system_metrics(mock_db)
            
            assert metrics.cpu_usage == 45.5
            assert metrics.memory_usage == 67.3
            assert metrics.disk_usage == 82.1
            assert metrics.active_connections == 15
    
    @pytest.mark.asyncio
    async def test_get_user_activity(self, mock_db, sample_audit_logs):
        """Test getting user activity statistics"""
        # Filter logs for last 24 hours
        recent_logs = [log for log in sample_audit_logs if log.timestamp >= datetime.utcnow() - timedelta(hours=24)]
        mock_db.query.return_value.filter.return_value.all.return_value = recent_logs
        
        activity = await admin_dashboard_service.get_user_activity(mock_db)
        
        assert len(activity) > 0
        # Should be grouped by hour
        for item in activity:
            assert "timestamp" in item
            assert "activity_count" in item
            assert "unique_users" in item
    
    @pytest.mark.asyncio
    async def test_get_error_logs(self, mock_db, sample_audit_logs):
        """Test getting error logs"""
        # Filter error logs
        error_logs = [log for log in sample_audit_logs if log.status == "error"]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = error_logs[:10]
        
        errors = await admin_dashboard_service.get_error_logs(mock_db, limit=10)
        
        assert len(errors) <= 10
        for error in errors:
            assert "timestamp" in error
            assert "action" in error
            assert "user_id" in error
            assert "error_details" in error
    
    @pytest.mark.asyncio
    async def test_manage_user(self, mock_db, sample_users):
        """Test user management operations"""
        # Setup user mock
        user = sample_users[0]
        mock_db.query.return_value.filter.return_value.first.return_value = user
        mock_db.commit = Mock()
        
        # Test suspending user
        result = await admin_dashboard_service.manage_user(
            db=mock_db,
            user_id=1,
            action="suspend",
            admin_id=999
        )
        
        assert result["success"] is True
        assert user.is_active is False
        mock_db.commit.assert_called_once()
        
        # Reset for next test
        user.is_active = True
        mock_db.reset_mock()
        
        # Test activating user
        result = await admin_dashboard_service.manage_user(
            db=mock_db,
            user_id=1,
            action="activate",
            admin_id=999
        )
        
        assert result["success"] is True
        assert user.is_active is True
    
    @pytest.mark.asyncio
    async def test_bulk_user_operations(self, mock_db, sample_users):
        """Test bulk user operations"""
        # Setup mocks
        selected_users = sample_users[:5]
        mock_db.query.return_value.filter.return_value.all.return_value = selected_users
        mock_db.commit = Mock()
        
        # Test bulk suspend
        result = await admin_dashboard_service.bulk_user_operation(
            db=mock_db,
            user_ids=[1, 2, 3, 4, 5],
            action="suspend",
            admin_id=999
        )
        
        assert result["success"] is True
        assert result["affected_count"] == 5
        
        # Verify all users are suspended
        for user in selected_users:
            assert user.is_active is False
    
    @pytest.mark.asyncio
    async def test_get_subscription_analytics(self, mock_db, sample_users):
        """Test subscription analytics"""
        # Group users by subscription tier
        basic_users = [u for u in sample_users if u.subscription_tier == "basic"]
        pro_users = [u for u in sample_users if u.subscription_tier == "pro"]
        
        mock_db.query.return_value.group_by.return_value.all.return_value = [
            ("basic", len(basic_users)),
            ("pro", len(pro_users))
        ]
        
        analytics = await admin_dashboard_service.get_subscription_analytics(mock_db)
        
        assert "basic" in analytics
        assert "pro" in analytics
        assert analytics["basic"] == len(basic_users)
        assert analytics["pro"] == len(pro_users)
    
    @pytest.mark.asyncio
    async def test_send_system_announcement(self, mock_db):
        """Test sending system announcement"""
        with patch('services.admin_dashboard_service.notification_service.send_bulk_notification') as mock_notify:
            mock_notify.return_value = {"sent": 100, "failed": 0}
            
            result = await admin_dashboard_service.send_system_announcement(
                db=mock_db,
                title="System Maintenance",
                message="Scheduled maintenance tonight",
                admin_id=999,
                target_users="all"
            )
            
            assert result["success"] is True
            assert result["sent"] == 100
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_maintenance(self, mock_db):
        """Test scheduling maintenance"""
        maintenance_time = datetime.utcnow() + timedelta(hours=2)
        
        result = await admin_dashboard_service.schedule_maintenance(
            db=mock_db,
            scheduled_time=maintenance_time,
            duration_minutes=60,
            description="Database optimization",
            admin_id=999
        )
        
        assert result["success"] is True
        assert "maintenance_id" in result
    
    @pytest.mark.asyncio
    async def test_export_user_data(self, mock_db, sample_users):
        """Test exporting user data"""
        mock_db.query.return_value.all.return_value = sample_users
        
        # Test CSV export
        csv_data = await admin_dashboard_service.export_user_data(
            db=mock_db,
            format="csv",
            filters={}
        )
        
        assert isinstance(csv_data, bytes)
        assert b"username,email,subscription_tier" in csv_data
        
        # Test JSON export
        json_data = await admin_dashboard_service.export_user_data(
            db=mock_db,
            format="json",
            filters={}
        )
        
        parsed_data = json.loads(json_data)
        assert "users" in parsed_data
        assert len(parsed_data["users"]) == len(sample_users)
    
    @pytest.mark.asyncio
    async def test_get_api_usage_stats(self, mock_db):
        """Test getting API usage statistics"""
        # Mock API call logs
        mock_logs = []
        for i in range(100):
            log = Mock()
            log.endpoint = f"/api/v1/endpoint{i % 5}"
            log.method = "GET" if i % 2 == 0 else "POST"
            log.status_code = 200 if i % 10 != 0 else 500
            log.response_time = 100 + (i % 50) * 10  # 100-590ms
            log.timestamp = datetime.utcnow() - timedelta(minutes=i)
            mock_logs.append(log)
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_logs
        
        stats = await admin_dashboard_service.get_api_usage_stats(mock_db)
        
        assert "total_requests" in stats
        assert "success_rate" in stats
        assert "avg_response_time" in stats
        assert "top_endpoints" in stats
        assert stats["total_requests"] == len(mock_logs)
        assert 0 <= stats["success_rate"] <= 100


class TestAdminDashboardAPI:
    """Test admin dashboard API endpoints"""
    
    @pytest.fixture
    def client(self, test_app):
        """Get test client"""
        return test_app
    
    @pytest.fixture
    def admin_headers(self):
        """Get admin auth headers"""
        return {"Authorization": "Bearer admin_token"}
    
    @pytest.mark.asyncio
    async def test_dashboard_stats_endpoint(self, client, admin_headers):
        """Test dashboard stats endpoint"""
        mock_stats = AdminDashboardStats(
            total_users=100,
            active_users=85,
            total_transcripts=500,
            failed_transcripts=5,
            storage_used=10 * 1024**3,  # 10GB
            new_users_30d=15,
            new_users_7d=5,
            new_users_24h=2,
            avg_processing_time=45.5,
            system_health="healthy"
        )
        
        with patch('services.admin_dashboard_service.admin_dashboard_service.get_dashboard_stats') as mock_get:
            mock_get.return_value = mock_stats
            
            response = await client.get(
                "/api/v1/admin/dashboard/stats",
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_users"] == 100
            assert data["active_users"] == 85
    
    @pytest.mark.asyncio
    async def test_system_metrics_endpoint(self, client, admin_headers):
        """Test system metrics endpoint"""
        mock_metrics = SystemMetrics(
            cpu_usage=45.5,
            memory_usage=67.3,
            disk_usage=82.1,
            active_connections=15,
            uptime_seconds=86400,
            load_average=[1.2, 1.5, 1.8]
        )
        
        with patch('services.admin_dashboard_service.admin_dashboard_service.get_system_metrics') as mock_get:
            mock_get.return_value = mock_metrics
            
            response = await client.get(
                "/api/v1/admin/dashboard/metrics",
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["cpu_usage"] == 45.5
    
    @pytest.mark.asyncio
    async def test_manage_user_endpoint(self, client, admin_headers):
        """Test user management endpoint"""
        with patch('services.admin_dashboard_service.admin_dashboard_service.manage_user') as mock_manage:
            mock_manage.return_value = {"success": True, "message": "User suspended"}
            
            response = await client.post(
                "/api/v1/admin/users/123/manage",
                json={"action": "suspend", "reason": "Terms violation"},
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.asyncio
    async def test_bulk_user_operation_endpoint(self, client, admin_headers):
        """Test bulk user operations endpoint"""
        with patch('services.admin_dashboard_service.admin_dashboard_service.bulk_user_operation') as mock_bulk:
            mock_bulk.return_value = {"success": True, "affected_count": 5}
            
            response = await client.post(
                "/api/v1/admin/users/bulk",
                json={
                    "user_ids": [1, 2, 3, 4, 5],
                    "action": "suspend"
                },
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["affected_count"] == 5
    
    @pytest.mark.asyncio
    async def test_send_announcement_endpoint(self, client, admin_headers):
        """Test sending system announcement"""
        with patch('services.admin_dashboard_service.admin_dashboard_service.send_system_announcement') as mock_announce:
            mock_announce.return_value = {"success": True, "sent": 100}
            
            response = await client.post(
                "/api/v1/admin/announcements",
                json={
                    "title": "System Update",
                    "message": "New features available",
                    "target_users": "all"
                },
                headers=admin_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["sent"] == 100
    
    @pytest.mark.asyncio
    async def test_export_data_endpoint(self, client, admin_headers):
        """Test data export endpoint"""
        with patch('services.admin_dashboard_service.admin_dashboard_service.export_user_data') as mock_export:
            mock_export.return_value = b"id,username,email\n1,test,test@example.com"
            
            response = await client.post(
                "/api/v1/admin/export/users",
                json={"format": "csv", "filters": {}},
                headers=admin_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"
    
    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client):
        """Test unauthorized access to admin endpoints"""
        response = await client.get("/api/v1/admin/dashboard/stats")
        assert response.status_code == 401
        
        # Non-admin user should also be denied
        user_headers = {"Authorization": "Bearer user_token"}
        response = await client.get(
            "/api/v1/admin/dashboard/stats",
            headers=user_headers
        )
        assert response.status_code == 403  # Forbidden


if __name__ == "__main__":
    pytest.main([__file__, "-v"])