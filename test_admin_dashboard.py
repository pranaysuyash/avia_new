#!/usr/bin/env python3
"""
Test Suite for Admin Dashboard and Business Analytics (Task 49)
Comprehensive tests for admin panel, user management, revenue tracking, and system monitoring
"""

import unittest
import tempfile
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from admin_dashboard import (
    AdminDashboardSystem, AdminDatabase, UserManagementSystem,
    RevenueTrackingSystem, SystemHealthMonitor, SupportTicketSystem,
    BusinessAnalytics, AdminUser, RevenueRecord, UserActivity,
    SystemMetric, SupportTicket, UserStatus, SubscriptionTier,
    TicketStatus, TicketPriority
)

class TestAdminDatabase(unittest.TestCase):
    """Test admin database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = AdminDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database table creation"""
        # Database should initialize without errors
        self.assertIsNotNone(self.db)
        
        # Check if tables exist
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Check admin_users table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_users'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check revenue_records table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='revenue_records'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check support_tickets table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='support_tickets'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_add_user(self):
        """Test adding user to database"""
        user = AdminUser(
            user_id="test_user_1",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            status="active",
            subscription_tier="pro",
            created_at=datetime.now(),
            total_usage=100.5,
            total_revenue=99.99
        )
        
        success = self.db.add_user(user)
        self.assertTrue(success)
        
        # Verify user was added
        users = self.db.get_users(limit=10)
        self.assertEqual(len(users), 1)
        self.assertEqual(users[0].username, "testuser")
        self.assertEqual(users[0].email, "test@example.com")
    
    def test_add_revenue_record(self):
        """Test adding revenue record"""
        # First add a user
        user = AdminUser(
            user_id="test_user_1",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            status="active",
            subscription_tier="pro",
            created_at=datetime.now()
        )
        self.db.add_user(user)
        
        # Add revenue record
        record = RevenueRecord(
            record_id="rev_001",
            user_id="test_user_1",
            amount=99.99,
            currency="USD",
            transaction_type="subscription",
            description="Monthly Pro subscription",
            timestamp=datetime.now(),
            subscription_tier="pro",
            billing_period="monthly"
        )
        
        success = self.db.add_revenue_record(record)
        self.assertTrue(success)
        
        # Verify user's total revenue was updated
        users = self.db.get_users()
        self.assertEqual(users[0].total_revenue, 99.99)
    
    def test_add_user_activity(self):
        """Test adding user activity"""
        activity = UserActivity(
            activity_id="act_001",
            user_id="test_user_1",
            activity_type="transcription",
            description="Transcribed audio file",
            timestamp=datetime.now(),
            duration=15.5
        )
        
        success = self.db.add_user_activity(activity)
        self.assertTrue(success)
    
    def test_add_system_metric(self):
        """Test adding system metric"""
        metric = SystemMetric(
            metric_id="metric_001",
            metric_name="cpu_usage",
            metric_value=75.5,
            metric_unit="percent",
            timestamp=datetime.now(),
            category="performance"
        )
        
        success = self.db.add_system_metric(metric)
        self.assertTrue(success)
    
    def test_add_support_ticket(self):
        """Test adding support ticket"""
        # First add a user
        user = AdminUser(
            user_id="test_user_1",
            username="testuser",
            email="test@example.com",
            full_name="Test User",
            status="active",
            subscription_tier="free",
            created_at=datetime.now()
        )
        self.db.add_user(user)
        
        # Add support ticket
        ticket = SupportTicket(
            ticket_id="ticket_001",
            user_id="test_user_1",
            subject="Login Issue",
            description="Cannot log into account",
            status="open",
            priority="medium",
            category="technical",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        success = self.db.add_support_ticket(ticket)
        self.assertTrue(success)
        
        # Verify user's support ticket count was updated
        users = self.db.get_users()
        self.assertEqual(users[0].support_tickets, 1)

class TestUserManagementSystem(unittest.TestCase):
    """Test user management functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = AdminDatabase(self.temp_db.name)
        self.user_mgmt = UserManagementSystem(self.db)
        
        # Add sample users
        self.sample_users = [
            AdminUser(
                user_id="user_001", username="john_doe", email="john@example.com",
                full_name="John Doe", status="active", subscription_tier="pro",
                created_at=datetime.now() - timedelta(days=30), total_usage=150.5,
                total_revenue=99.0, support_tickets=1
            ),
            AdminUser(
                user_id="user_002", username="jane_smith", email="jane@example.com",
                full_name="Jane Smith", status="active", subscription_tier="enterprise",
                created_at=datetime.now() - timedelta(days=15), total_usage=300.2,
                total_revenue=299.0, support_tickets=0
            ),
            AdminUser(
                user_id="user_003", username="bob_wilson", email="bob@example.com",
                full_name="Bob Wilson", status="inactive", subscription_tier="free",
                created_at=datetime.now() - timedelta(days=60), total_usage=25.1,
                total_revenue=0.0, support_tickets=2
            )
        ]
        
        for user in self.sample_users:
            self.db.add_user(user)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_get_user_overview(self):
        """Test getting user overview statistics"""
        overview = self.user_mgmt.get_user_overview()
        
        self.assertEqual(overview['total_users'], 3)
        self.assertEqual(overview['active_users'], 2)
        self.assertIn('tier_distribution', overview)
        self.assertIn('growth_data', overview)
        self.assertGreater(overview['activity_rate'], 0)
    
    def test_search_users(self):
        """Test user search functionality"""
        # Search by username
        results = self.user_mgmt.search_users("john")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].username, "john_doe")
        
        # Search by email
        results = self.user_mgmt.search_users("jane@example.com")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].email, "jane@example.com")
        
        # Search with filters
        results = self.user_mgmt.search_users("", {"status": "active"})
        self.assertEqual(len(results), 2)
        
        results = self.user_mgmt.search_users("", {"subscription_tier": "enterprise"})
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].subscription_tier, "enterprise")
    
    def test_update_user_status(self):
        """Test updating user status"""
        success = self.user_mgmt.update_user_status(
            "user_001", UserStatus.SUSPENDED, "admin_user"
        )
        self.assertTrue(success)
        
        # Verify status was updated
        users = self.db.get_users()
        updated_user = next(u for u in users if u.user_id == "user_001")
        self.assertEqual(updated_user.status, "suspended")
    
    def test_get_user_activity_summary(self):
        """Test getting user activity summary"""
        # Add some activities
        activities = [
            UserActivity(
                activity_id="act_001", user_id="user_001",
                activity_type="transcription", description="Transcribed file",
                timestamp=datetime.now(), duration=10.0
            ),
            UserActivity(
                activity_id="act_002", user_id="user_001",
                activity_type="analysis", description="Analyzed content",
                timestamp=datetime.now(), duration=5.0
            )
        ]
        
        for activity in activities:
            self.db.add_user_activity(activity)
        
        summary = self.user_mgmt.get_user_activity_summary("user_001")
        
        self.assertIn('activity_types', summary)
        self.assertIn('total_time', summary)
        self.assertIn('recent_activities', summary)
        self.assertEqual(summary['total_time'], 15.0)

class TestRevenueTrackingSystem(unittest.TestCase):
    """Test revenue tracking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = AdminDatabase(self.temp_db.name)
        self.revenue_tracker = RevenueTrackingSystem(self.db)
        
        # Add sample users and revenue records
        user = AdminUser(
            user_id="user_001", username="testuser", email="test@example.com",
            full_name="Test User", status="active", subscription_tier="pro",
            created_at=datetime.now()
        )
        self.db.add_user(user)
        
        # Add revenue records
        records = [
            RevenueRecord(
                record_id="rev_001", user_id="user_001", amount=99.99,
                currency="USD", transaction_type="subscription",
                description="Monthly Pro", timestamp=datetime.now(),
                subscription_tier="pro", billing_period="monthly"
            ),
            RevenueRecord(
                record_id="rev_002", user_id="user_001", amount=19.99,
                currency="USD", transaction_type="usage",
                description="Additional usage", timestamp=datetime.now() - timedelta(days=1)
            )
        ]
        
        for record in records:
            self.db.add_revenue_record(record)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_get_revenue_overview(self):
        """Test getting revenue overview"""
        overview = self.revenue_tracker.get_revenue_overview(30)
        
        self.assertGreater(overview['total_revenue'], 0)
        self.assertGreater(overview['period_revenue'], 0)
        self.assertIn('tier_revenue', overview)
        self.assertIn('type_revenue', overview)
        self.assertIn('daily_revenue', overview)
        self.assertGreater(overview['paying_users'], 0)
    
    def test_get_subscription_metrics(self):
        """Test getting subscription metrics"""
        metrics = self.revenue_tracker.get_subscription_metrics()
        
        self.assertIn('current_distribution', metrics)
        self.assertIn('monthly_mrr', metrics)
        self.assertIn('total_mrr', metrics)
        self.assertIn('churn_rate', metrics)

class TestSystemHealthMonitor(unittest.TestCase):
    """Test system health monitoring"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = AdminDatabase(self.temp_db.name)
        self.health_monitor = SystemHealthMonitor(self.db)
    
    def tearDown(self):
        """Clean up"""
        self.health_monitor.stop_monitoring()
        os.unlink(self.temp_db.name)
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        self.assertFalse(self.health_monitor.monitoring_active)
        
        self.health_monitor.start_monitoring()
        self.assertTrue(self.health_monitor.monitoring_active)
        
        self.health_monitor.stop_monitoring()
        self.assertFalse(self.health_monitor.monitoring_active)
    
    def test_collect_system_metrics(self):
        """Test collecting system metrics"""
        # Manually trigger metric collection
        self.health_monitor._collect_system_metrics()
        
        # Check if metrics were stored
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM system_metrics")
            count = cursor.fetchone()[0]
            self.assertGreater(count, 0)
    
    def test_get_system_health_overview(self):
        """Test getting system health overview"""
        # Add some metrics first
        metrics = [
            SystemMetric(
                metric_id="cpu_001", metric_name="cpu_usage", metric_value=45.0,
                metric_unit="percent", timestamp=datetime.now(), category="performance"
            ),
            SystemMetric(
                metric_id="mem_001", metric_name="memory_usage", metric_value=60.0,
                metric_unit="percent", timestamp=datetime.now(), category="performance"
            )
        ]
        
        for metric in metrics:
            self.db.add_system_metric(metric)
        
        overview = self.health_monitor.get_system_health_overview(1)
        
        self.assertIn('status', overview)
        self.assertIn('alerts', overview)
        self.assertIn('current_metrics', overview)
        self.assertIn('trends', overview)

class TestSupportTicketSystem(unittest.TestCase):
    """Test support ticket system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = AdminDatabase(self.temp_db.name)
        self.support_system = SupportTicketSystem(self.db)
        
        # Add a test user
        user = AdminUser(
            user_id="user_001", username="testuser", email="test@example.com",
            full_name="Test User", status="active", subscription_tier="pro",
            created_at=datetime.now()
        )
        self.db.add_user(user)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_ticket(self):
        """Test creating support ticket"""
        ticket_id = self.support_system.create_ticket(
            "user_001", "Login Issue", "Cannot access my account",
            TicketPriority.HIGH, "technical"
        )
        
        self.assertIsNotNone(ticket_id)
        
        # Verify ticket was created
        tickets = self.support_system.get_tickets()
        self.assertEqual(len(tickets), 1)
        self.assertEqual(tickets[0].subject, "Login Issue")
        self.assertEqual(tickets[0].priority, "high")
    
    def test_get_tickets_with_filters(self):
        """Test getting tickets with filters"""
        # Create multiple tickets
        self.support_system.create_ticket(
            "user_001", "Bug Report", "Found a bug", TicketPriority.MEDIUM, "bug"
        )
        self.support_system.create_ticket(
            "user_001", "Feature Request", "Need new feature", TicketPriority.LOW, "feature"
        )
        
        # Test status filter
        open_tickets = self.support_system.get_tickets(status="open")
        self.assertEqual(len(open_tickets), 2)
        
        # Test priority filter
        medium_tickets = self.support_system.get_tickets(priority="medium")
        self.assertEqual(len(medium_tickets), 1)
    
    def test_update_ticket_status(self):
        """Test updating ticket status"""
        ticket_id = self.support_system.create_ticket(
            "user_001", "Test Ticket", "Test description"
        )
        
        success = self.support_system.update_ticket_status(
            ticket_id, TicketStatus.IN_PROGRESS, assigned_to="support_agent"
        )
        self.assertTrue(success)
        
        # Verify status was updated
        tickets = self.support_system.get_tickets()
        self.assertEqual(tickets[0].status, "in_progress")
        self.assertEqual(tickets[0].assigned_to, "support_agent")
    
    def test_get_support_metrics(self):
        """Test getting support metrics"""
        # Create some tickets
        self.support_system.create_ticket("user_001", "Ticket 1", "Description 1")
        self.support_system.create_ticket("user_001", "Ticket 2", "Description 2")
        
        metrics = self.support_system.get_support_metrics()
        
        self.assertIn('total_tickets', metrics)
        self.assertIn('new_tickets', metrics)
        self.assertIn('status_distribution', metrics)
        self.assertIn('priority_distribution', metrics)
        self.assertEqual(metrics['new_tickets'], 2)

class TestBusinessAnalytics(unittest.TestCase):
    """Test business analytics functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = AdminDatabase(self.temp_db.name)
        self.analytics = BusinessAnalytics(self.db)
        
        # Add sample data
        users = [
            AdminUser(
                user_id="user_001", username="user1", email="user1@example.com",
                full_name="User One", status="active", subscription_tier="pro",
                created_at=datetime.now() - timedelta(days=30),
                last_login=datetime.now() - timedelta(days=1)
            ),
            AdminUser(
                user_id="user_002", username="user2", email="user2@example.com",
                full_name="User Two", status="active", subscription_tier="free",
                created_at=datetime.now() - timedelta(days=60),
                last_login=datetime.now() - timedelta(days=2)
            )
        ]
        
        for user in users:
            self.db.add_user(user)
        
        # Add activities
        activities = [
            UserActivity(
                activity_id="act_001", user_id="user_001",
                activity_type="transcription", description="Transcribed file",
                timestamp=datetime.now(), duration=10.0
            ),
            UserActivity(
                activity_id="act_002", user_id="user_002",
                activity_type="analysis", description="Analyzed content",
                timestamp=datetime.now(), duration=15.0
            )
        ]
        
        for activity in activities:
            self.db.add_user_activity(activity)
        
        # Add revenue records
        revenue = RevenueRecord(
            record_id="rev_001", user_id="user_001", amount=99.99,
            currency="USD", transaction_type="subscription",
            description="Pro subscription", timestamp=datetime.now()
        )
        self.db.add_revenue_record(revenue)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_get_engagement_metrics(self):
        """Test getting engagement metrics"""
        metrics = self.analytics.get_engagement_metrics()
        
        self.assertIn('daily_active_users', metrics)
        self.assertIn('most_active_users', metrics)
        self.assertIn('activity_types', metrics)
        self.assertIn('avg_session_duration', metrics)
    
    def test_get_conversion_funnel(self):
        """Test getting conversion funnel"""
        funnel = self.analytics.get_conversion_funnel()
        
        self.assertIn('funnel_stages', funnel)
        self.assertIn('conversion_rates', funnel)
        
        stages = funnel['funnel_stages']
        self.assertIn('registered', stages)
        self.assertIn('activated', stages)
        self.assertIn('paying', stages)
        
        rates = funnel['conversion_rates']
        self.assertIn('activation_rate', rates)
        self.assertIn('conversion_rate', rates)
    
    def test_get_cohort_analysis(self):
        """Test getting cohort analysis"""
        cohort = self.analytics.get_cohort_analysis()
        
        self.assertIn('cohort_data', cohort)
        self.assertIn('months_analyzed', cohort)
        
        cohort_data = cohort['cohort_data']
        self.assertIsInstance(cohort_data, list)

class TestAdminDashboardSystem(unittest.TestCase):
    """Test main admin dashboard system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.admin_system = AdminDashboardSystem(self.temp_db.name)
        
        # Add sample data
        user = AdminUser(
            user_id="user_001", username="testuser", email="test@example.com",
            full_name="Test User", status="active", subscription_tier="pro",
            created_at=datetime.now(), total_usage=100.0, total_revenue=99.99
        )
        self.admin_system.db.add_user(user)
    
    def tearDown(self):
        """Clean up"""
        self.admin_system.cleanup()
        os.unlink(self.temp_db.name)
    
    def test_get_dashboard_overview(self):
        """Test getting dashboard overview"""
        overview = self.admin_system.get_dashboard_overview()
        
        self.assertIn('users', overview)
        self.assertIn('revenue', overview)
        self.assertIn('system_health', overview)
        self.assertIn('support', overview)
        self.assertIn('engagement', overview)
        self.assertIn('timestamp', overview)
    
    def test_generate_executive_report(self):
        """Test generating executive report"""
        report = self.admin_system.generate_executive_report(30)
        
        self.assertIn('report_date', report)
        self.assertIn('period_days', report)
        self.assertIn('kpis', report)
        self.assertIn('growth_metrics', report)
        self.assertIn('conversion_funnel', report)
        self.assertIn('recommendations', report)
        
        # Check KPIs
        kpis = report['kpis']
        self.assertIn('total_users', kpis)
        self.assertIn('total_revenue', kpis)
        self.assertIn('system_health', kpis)
    
    def test_generate_recommendations(self):
        """Test recommendation generation"""
        kpis = {
            'total_users': 100,
            'conversion_rate': 3.0,
            'support_tickets': 60,
            'system_health': 'warning'
        }
        
        growth_metrics = {
            'user_growth': 50,
            'revenue_growth': 500
        }
        
        recommendations = self.admin_system._generate_recommendations(kpis, growth_metrics)
        
        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for admin dashboard"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.admin_system = AdminDashboardSystem(self.temp_db.name)
    
    def tearDown(self):
        """Clean up"""
        self.admin_system.cleanup()
        os.unlink(self.temp_db.name)
    
    def test_end_to_end_workflow(self):
        """Test complete admin dashboard workflow"""
        # 1. Add users
        users = [
            AdminUser(
                user_id="user_001", username="john_doe", email="john@example.com",
                full_name="John Doe", status="active", subscription_tier="pro",
                created_at=datetime.now() - timedelta(days=30)
            ),
            AdminUser(
                user_id="user_002", username="jane_smith", email="jane@example.com",
                full_name="Jane Smith", status="active", subscription_tier="enterprise",
                created_at=datetime.now() - timedelta(days=15)
            )
        ]
        
        for user in users:
            success = self.admin_system.db.add_user(user)
            self.assertTrue(success)
        
        # 2. Add revenue records
        revenue_records = [
            RevenueRecord(
                record_id="rev_001", user_id="user_001", amount=99.99,
                currency="USD", transaction_type="subscription",
                description="Pro subscription", timestamp=datetime.now()
            ),
            RevenueRecord(
                record_id="rev_002", user_id="user_002", amount=299.99,
                currency="USD", transaction_type="subscription",
                description="Enterprise subscription", timestamp=datetime.now()
            )
        ]
        
        for record in revenue_records:
            success = self.admin_system.db.add_revenue_record(record)
            self.assertTrue(success)
        
        # 3. Add user activities
        activities = [
            UserActivity(
                activity_id="act_001", user_id="user_001",
                activity_type="transcription", description="Transcribed audio",
                timestamp=datetime.now(), duration=20.0
            ),
            UserActivity(
                activity_id="act_002", user_id="user_002",
                activity_type="analysis", description="Analyzed content",
                timestamp=datetime.now(), duration=30.0
            )
        ]
        
        for activity in activities:
            success = self.admin_system.db.add_user_activity(activity)
            self.assertTrue(success)
        
        # 4. Create support tickets
        ticket_id = self.admin_system.support_system.create_ticket(
            "user_001", "Login Issue", "Cannot access account",
            TicketPriority.HIGH, "technical"
        )
        self.assertIsNotNone(ticket_id)
        
        # 5. Get dashboard overview
        overview = self.admin_system.get_dashboard_overview()
        
        self.assertEqual(overview['users']['total_users'], 2)
        self.assertEqual(overview['users']['active_users'], 2)
        self.assertGreater(overview['revenue']['total_revenue'], 0)
        self.assertEqual(overview['support']['new_tickets'], 1)
        
        # 6. Generate executive report
        report = self.admin_system.generate_executive_report(30)
        
        self.assertEqual(report['kpis']['total_users'], 2)
        self.assertGreater(report['kpis']['total_revenue'], 0)
        self.assertIsInstance(report['recommendations'], list)
        
        # 7. Test user management
        user_overview = self.admin_system.user_management.get_user_overview()
        self.assertEqual(user_overview['total_users'], 2)
        
        # Search users
        search_results = self.admin_system.user_management.search_users("john")
        self.assertEqual(len(search_results), 1)
        self.assertEqual(search_results[0].username, "john_doe")
        
        # 8. Test revenue tracking
        revenue_overview = self.admin_system.revenue_tracking.get_revenue_overview(30)
        self.assertGreater(revenue_overview['total_revenue'], 0)
        self.assertEqual(revenue_overview['paying_users'], 2)
        
        # 9. Test support system
        tickets = self.admin_system.support_system.get_tickets()
        self.assertEqual(len(tickets), 1)
        
        support_metrics = self.admin_system.support_system.get_support_metrics()
        self.assertEqual(support_metrics['new_tickets'], 1)
        
        # 10. Test analytics
        engagement_metrics = self.admin_system.analytics.get_engagement_metrics()
        self.assertIn('activity_types', engagement_metrics)
        
        conversion_funnel = self.admin_system.analytics.get_conversion_funnel()
        self.assertEqual(conversion_funnel['funnel_stages']['registered'], 2)

def run_performance_tests():
    """Run performance tests for admin dashboard"""
    print("\n🚀 Running Performance Tests")
    print("=" * 50)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        admin_system = AdminDashboardSystem(temp_db.name)
        
        # Add large amount of data
        print("Adding 1000 users...")
        start_time = time.time()
        
        for i in range(1000):
            user = AdminUser(
                user_id=f"user_{i:04d}",
                username=f"user_{i:04d}",
                email=f"user{i}@example.com",
                full_name=f"User {i}",
                status="active" if i % 4 != 0 else "inactive",
                subscription_tier=["free", "pro", "enterprise"][i % 3],
                created_at=datetime.now() - timedelta(days=i % 365),
                total_usage=float(i * 10),
                total_revenue=float(i * 5)
            )
            admin_system.db.add_user(user)
        
        add_time = time.time() - start_time
        print(f"✅ Added 1000 users in {add_time:.2f} seconds ({1000/add_time:.1f} users/sec)")
        
        # Test dashboard overview performance
        start_time = time.time()
        overview = admin_system.get_dashboard_overview()
        overview_time = time.time() - start_time
        print(f"✅ Dashboard overview: {overview_time:.3f} seconds")
        
        # Test user search performance
        start_time = time.time()
        results = admin_system.user_management.search_users("user_0")
        search_time = time.time() - start_time
        print(f"✅ User search: {len(results)} results in {search_time:.3f} seconds")
        
        # Test executive report performance
        start_time = time.time()
        report = admin_system.generate_executive_report(30)
        report_time = time.time() - start_time
        print(f"✅ Executive report: {report_time:.3f} seconds")
        
        print(f"\n🎯 Performance Summary:")
        print(f"   - User creation: {1000/add_time:.1f} users/sec")
        print(f"   - Dashboard overview: {overview_time:.3f} seconds")
        print(f"   - User search: {search_time:.3f} seconds")
        print(f"   - Executive report: {report_time:.3f} seconds")
        print(f"   - System handles large datasets efficiently")
        
    finally:
        admin_system.cleanup()
        os.unlink(temp_db.name)

def main():
    """Run all tests"""
    print("🧪 Admin Dashboard and Business Analytics Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestAdminDatabase,
        TestUserManagementSystem,
        TestRevenueTrackingSystem,
        TestSystemHealthMonitor,
        TestSupportTicketSystem,
        TestBusinessAnalytics,
        TestAdminDashboardSystem,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('\\n')[-2]}")
    
    # Run performance tests
    run_performance_tests()
    
    # Overall result
    if result.failures or result.errors:
        print(f"\n❌ Some tests failed. Please review and fix issues.")
        return False
    else:
        print(f"\n✅ All tests passed! Admin dashboard system is working correctly.")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)