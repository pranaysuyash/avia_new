#!/usr/bin/env python3
"""
Comprehensive Test Suite for Usage Tracking and Quota Management System (Task 48)
Tests all components including usage tracking, quota enforcement, and analytics
"""

import unittest
import tempfile
import os
import json
import time
import threading
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Import the system components
from usage_tracking_system import (
    UsageTrackingSystem, UsageTracker, UsageDatabase, QuotaManager,
    UsageMetric, UsagePeriod, QuotaAction, SubscriptionTier,
    UsageRecord, QuotaLimit, UsageSummary, QuotaStatus
)

class TestUsageDatabase(unittest.TestCase):
    """Test the usage database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = UsageDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database tables are created correctly"""
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            
            # Check that all required tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = [
                'usage_records', 'quota_limits', 'usage_summaries',
                'quota_violations', 'usage_alerts'
            ]
            
            for table in required_tables:
                self.assertIn(table, tables, f"Table {table} not found")
    
    def test_record_usage(self):
        """Test recording usage in database"""
        usage_record = UsageRecord(
            record_id="test_record_123",
            user_id="test_user",
            team_id=None,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=2.5,
            timestamp=datetime.now().isoformat(),
            metadata={"test": "data"},
            session_id="session_123",
            source="test",
            cost_cents=0
        )
        
        success = self.db.record_usage(usage_record)
        self.assertTrue(success)
        
        # Verify record was stored
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usage_records WHERE record_id = ?", (usage_record.record_id,))
            row = cursor.fetchone()
            
            self.assertIsNotNone(row)
            self.assertEqual(row[1], usage_record.user_id)  # user_id column
            self.assertEqual(row[3], usage_record.metric)   # metric column
            self.assertEqual(row[4], usage_record.quantity) # quantity column
    
    def test_get_usage_summary(self):
        """Test getting usage summary for a period"""
        user_id = "test_summary_user"
        metric = UsageMetric.TRANSCRIPTION_HOURS.value
        
        # Record some usage
        now = datetime.now()
        start_time = (now - timedelta(hours=1)).isoformat()
        end_time = now.isoformat()
        
        usage_records = [
            UsageRecord(
                record_id=f"record_{i}",
                user_id=user_id,
                team_id=None,
                metric=metric,
                quantity=1.0,
                timestamp=now.isoformat(),
                metadata={}
            ) for i in range(3)
        ]
        
        for record in usage_records:
            self.db.record_usage(record)
        
        # Get summary
        total_usage = self.db.get_usage_summary(user_id, metric, "hourly", start_time, end_time)
        self.assertEqual(total_usage, 3.0)
    
    def test_create_quota_limit(self):
        """Test creating quota limits"""
        quota_limit = QuotaLimit(
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            limit=5.0,
            period=UsagePeriod.MONTHLY.value,
            action=QuotaAction.BLOCK.value,
            warning_threshold=0.8,
            overage_rate_cents=500
        )
        
        success = self.db.create_quota_limit(quota_limit, user_id="test_user")
        self.assertTrue(success)
        
        # Verify limit was stored
        limits = self.db.get_quota_limits("test_user")
        self.assertEqual(len(limits), 1)
        self.assertEqual(limits[0].metric, quota_limit.metric)
        self.assertEqual(limits[0].limit, quota_limit.limit)
    
    def test_record_quota_violation(self):
        """Test recording quota violations"""
        success = self.db.record_quota_violation(
            user_id="test_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            attempted_usage=2.0,
            current_usage=4.0,
            limit_value=5.0,
            action_taken="blocked",
            metadata={"reason": "quota_exceeded"}
        )
        
        self.assertTrue(success)
        
        # Verify violation was recorded
        with sqlite3.connect(self.temp_db.name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM quota_violations WHERE user_id = ?", ("test_user",))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

class TestUsageTracker(unittest.TestCase):
    """Test the usage tracker functionality"""
    
    def setUp(self):
        """Set up usage tracker"""
        self.tracker = UsageTracker(flush_interval=1)  # Short flush interval for testing
        self.tracker.start()
    
    def tearDown(self):
        """Clean up usage tracker"""
        self.tracker.stop()
    
    def test_record_usage(self):
        """Test recording usage in memory cache"""
        success = self.tracker.record_usage(
            user_id="test_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=2.5,
            metadata={"test": "data"}
        )
        
        self.assertTrue(success)
        
        # Check that usage is in cache
        cache_key = "test_user:personal:transcription_hours"
        self.assertIn(cache_key, self.tracker.usage_cache)
    
    def test_concurrent_sessions(self):
        """Test concurrent session tracking"""
        user_id = "test_session_user"
        session_ids = ["session_1", "session_2", "session_3"]
        
        # Start sessions
        for session_id in session_ids:
            self.tracker.record_usage(
                user_id=user_id,
                metric=UsageMetric.CONCURRENT_SESSIONS.value,
                quantity=1,
                session_id=session_id
            )
        
        # Check concurrent count
        concurrent_count = self.tracker.get_concurrent_sessions(user_id)
        self.assertEqual(concurrent_count, 3)
        
        # End a session
        self.tracker.end_session(user_id, session_ids[0])
        concurrent_count = self.tracker.get_concurrent_sessions(user_id)
        self.assertEqual(concurrent_count, 2)
    
    def test_cache_flush(self):
        """Test cache flushing to database"""
        # Record usage
        self.tracker.record_usage(
            user_id="test_flush_user",
            metric=UsageMetric.API_CALLS.value,
            quantity=100
        )
        
        # Manually flush cache
        self.tracker.flush_cache()
        
        # Cache should be empty after flush
        self.assertEqual(len(self.tracker.usage_cache), 0)

class TestQuotaManager(unittest.TestCase):
    """Test quota management functionality"""
    
    def setUp(self):
        """Set up quota manager with mocked dependencies"""
        self.usage_tracker = Mock()
        self.subscription_manager = Mock()
        
        # Mock subscription manager to return free tier
        self.subscription_manager.get_subscription_status.return_value = {
            'tier': 'free',
            'limits': {'transcription_hours': 5}
        }
        
        self.quota_manager = QuotaManager(self.usage_tracker, self.subscription_manager)
    
    def test_check_quota_within_limits(self):
        """Test quota check when within limits"""
        # Mock database to return current usage
        with patch.object(self.quota_manager.db, 'get_usage_summary', return_value=2.0):
            with patch.object(self.quota_manager.db, 'get_quota_limits') as mock_limits:
                mock_limits.return_value = [QuotaLimit(
                    metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                    limit=5.0,
                    period=UsagePeriod.MONTHLY.value,
                    action=QuotaAction.BLOCK.value,
                    warning_threshold=0.8,
                    overage_rate_cents=500
                )]
                
                allowed, message, quota_status = self.quota_manager.check_quota(
                    user_id="test_user",
                    metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                    requested_quantity=1.0
                )
                
                self.assertTrue(allowed)
                self.assertEqual(quota_status.current_usage, 2.0)
                self.assertEqual(quota_status.limit, 5.0)
                self.assertFalse(quota_status.is_exceeded)
    
    def test_check_quota_exceeded(self):
        """Test quota check when quota would be exceeded"""
        # Mock database to return usage near limit
        with patch.object(self.quota_manager.db, 'get_usage_summary', return_value=4.5):
            with patch.object(self.quota_manager.db, 'get_quota_limits') as mock_limits:
                with patch.object(self.quota_manager.db, 'record_quota_violation') as mock_violation:
                    mock_limits.return_value = [QuotaLimit(
                        metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                        limit=5.0,
                        period=UsagePeriod.MONTHLY.value,
                        action=QuotaAction.BLOCK.value,
                        warning_threshold=0.8,
                        overage_rate_cents=500
                    )]
                    
                    allowed, message, quota_status = self.quota_manager.check_quota(
                        user_id="test_user",
                        metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                        requested_quantity=1.0  # Would total 5.5, exceeding 5.0 limit
                    )
                    
                    self.assertFalse(allowed)
                    self.assertTrue(quota_status.is_exceeded)
                    mock_violation.assert_called_once()
    
    def test_check_quota_unlimited(self):
        """Test quota check with unlimited quota"""
        with patch.object(self.quota_manager.db, 'get_usage_summary', return_value=100.0):
            with patch.object(self.quota_manager.db, 'get_quota_limits') as mock_limits:
                mock_limits.return_value = [QuotaLimit(
                    metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                    limit=-1,  # Unlimited
                    period=UsagePeriod.MONTHLY.value,
                    action=QuotaAction.WARN.value,
                    warning_threshold=0.8,
                    overage_rate_cents=0
                )]
                
                allowed, message, quota_status = self.quota_manager.check_quota(
                    user_id="test_user",
                    metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                    requested_quantity=1000.0
                )
                
                self.assertTrue(allowed)
                self.assertEqual(quota_status.limit, -1)
                self.assertFalse(quota_status.is_exceeded)
    
    def test_get_usage_analytics(self):
        """Test usage analytics generation"""
        with patch.object(self.quota_manager.db, 'get_quota_limits') as mock_limits:
            with patch.object(self.quota_manager.db, 'get_usage_summary', return_value=3.0):
                mock_limits.return_value = [
                    QuotaLimit(
                        metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                        limit=5.0,
                        period=UsagePeriod.MONTHLY.value,
                        action=QuotaAction.BLOCK.value,
                        warning_threshold=0.8,
                        overage_rate_cents=500
                    ),
                    QuotaLimit(
                        metric=UsageMetric.API_CALLS.value,
                        limit=1000,
                        period=UsagePeriod.MONTHLY.value,
                        action=QuotaAction.THROTTLE.value,
                        warning_threshold=0.9,
                        overage_rate_cents=1
                    )
                ]
                
                analytics = self.quota_manager.get_usage_analytics("test_user")
                
                self.assertIn('user_id', analytics)
                self.assertIn('metrics', analytics)
                self.assertIn('subscription_tier', analytics)
                self.assertEqual(analytics['user_id'], 'test_user')
                self.assertEqual(analytics['subscription_tier'], 'free')

class TestUsageTrackingSystem(unittest.TestCase):
    """Test the complete usage tracking system"""
    
    def setUp(self):
        """Set up usage tracking system"""
        self.usage_system = UsageTrackingSystem()
    
    def tearDown(self):
        """Clean up usage tracking system"""
        self.usage_system.shutdown()
    
    def test_record_usage_with_quota_check(self):
        """Test recording usage with quota checking"""
        success, message, quota_status = self.usage_system.record_usage(
            user_id="test_system_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=2.0,
            metadata={"test": "system"},
            check_quota=True
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(quota_status)
        self.assertEqual(quota_status.current_usage, 2.0)
    
    def test_record_usage_without_quota_check(self):
        """Test recording usage without quota checking"""
        success, message, quota_status = self.usage_system.record_usage(
            user_id="test_system_user_no_quota",
            metric=UsageMetric.API_CALLS.value,
            quantity=100,
            check_quota=False
        )
        
        self.assertTrue(success)
        self.assertIsNone(quota_status)
    
    def test_get_quota_status(self):
        """Test getting quota status"""
        # First record some usage
        self.usage_system.record_usage(
            user_id="test_quota_status_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=1.5
        )
        
        quota_status = self.usage_system.get_quota_status(
            user_id="test_quota_status_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value
        )
        
        self.assertIsInstance(quota_status, QuotaStatus)
        self.assertEqual(quota_status.user_id, "test_quota_status_user")
        self.assertEqual(quota_status.metric, UsageMetric.TRANSCRIPTION_HOURS.value)
    
    def test_get_usage_analytics(self):
        """Test getting usage analytics"""
        user_id = "test_analytics_user"
        
        # Record some usage
        self.usage_system.record_usage(
            user_id=user_id,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=2.0
        )
        
        analytics = self.usage_system.get_usage_analytics(user_id)
        
        self.assertIn('user_id', analytics)
        self.assertIn('metrics', analytics)
        self.assertIn('subscription_tier', analytics)
        self.assertEqual(analytics['user_id'], user_id)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Set up for performance tests"""
        self.usage_system = UsageTrackingSystem()
    
    def tearDown(self):
        """Clean up after performance tests"""
        self.usage_system.shutdown()
    
    def test_high_volume_usage_recording(self):
        """Test recording high volume of usage events"""
        user_id = "performance_test_user"
        start_time = time.time()
        
        # Record 1000 usage events
        for i in range(1000):
            success, _, _ = self.usage_system.record_usage(
                user_id=user_id,
                metric=UsageMetric.API_CALLS.value,
                quantity=1,
                check_quota=False  # Skip quota check for performance
            )
            self.assertTrue(success)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(duration, 10.0, f"High volume test took {duration:.2f} seconds")
        
        # Flush cache to ensure all events are recorded
        self.usage_system.usage_tracker.flush_cache()
    
    def test_concurrent_usage_recording(self):
        """Test concurrent usage recording"""
        user_id = "concurrent_test_user"
        results = []
        
        def record_usage_worker():
            success, _, _ = self.usage_system.record_usage(
                user_id=user_id,
                metric=UsageMetric.TRANSCRIPTION_HOURS.value,
                quantity=0.1,
                check_quota=False
            )
            results.append(success)
        
        # Create and start multiple threads
        threads = []
        for _ in range(50):
            thread = threading.Thread(target=record_usage_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All operations should succeed
        self.assertTrue(all(results))
        self.assertEqual(len(results), 50)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up for error handling tests"""
        self.usage_system = UsageTrackingSystem()
    
    def tearDown(self):
        """Clean up after error handling tests"""
        self.usage_system.shutdown()
    
    def test_invalid_user_id(self):
        """Test handling of invalid user IDs"""
        # Empty user ID
        success, message, _ = self.usage_system.record_usage(
            user_id="",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=1.0
        )
        
        # Should handle gracefully (implementation dependent)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
    
    def test_negative_usage(self):
        """Test handling of negative usage quantities"""
        success, message, _ = self.usage_system.record_usage(
            user_id="test_negative_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=-1.0
        )
        
        # Should handle gracefully
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
    
    def test_very_large_usage(self):
        """Test handling of very large usage quantities"""
        success, message, quota_status = self.usage_system.record_usage(
            user_id="test_large_user",
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=1000000.0,
            check_quota=True
        )
        
        # Should handle gracefully (likely blocked by quota)
        self.assertIsInstance(success, bool)
        self.assertIsInstance(message, str)
    
    def test_invalid_metric(self):
        """Test handling of invalid metrics"""
        try:
            success, message, _ = self.usage_system.record_usage(
                user_id="test_invalid_metric_user",
                metric="invalid_metric",
                quantity=1.0
            )
            # Should either succeed or fail gracefully
            self.assertIsInstance(success, bool)
        except Exception as e:
            # Should not raise unhandled exceptions
            self.fail(f"Unhandled exception for invalid metric: {e}")

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete system"""
    
    def setUp(self):
        """Set up for integration tests"""
        self.usage_system = UsageTrackingSystem()
    
    def tearDown(self):
        """Clean up after integration tests"""
        self.usage_system.shutdown()
    
    def test_complete_workflow(self):
        """Test complete usage tracking workflow"""
        user_id = "integration_workflow_user"
        
        # 1. Record initial usage
        success, message, quota_status = self.usage_system.record_usage(
            user_id=user_id,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=2.0,
            metadata={"workflow": "integration_test"}
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(quota_status)
        self.assertEqual(quota_status.current_usage, 2.0)
        
        # 2. Check quota status
        current_quota = self.usage_system.get_quota_status(
            user_id=user_id,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value
        )
        
        self.assertEqual(current_quota.current_usage, 2.0)
        self.assertFalse(current_quota.is_exceeded)
        
        # 3. Record more usage to approach limit
        success, message, quota_status = self.usage_system.record_usage(
            user_id=user_id,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=2.5
        )
        
        self.assertTrue(success)
        self.assertEqual(quota_status.current_usage, 4.5)
        
        # 4. Try to exceed quota
        success, message, quota_status = self.usage_system.record_usage(
            user_id=user_id,
            metric=UsageMetric.TRANSCRIPTION_HOURS.value,
            quantity=1.0  # Would total 5.5, exceeding 5.0 limit for free tier
        )
        
        # Should be blocked for free tier
        self.assertFalse(success)
        self.assertTrue(quota_status.is_exceeded)
        
        # 5. Get comprehensive analytics
        analytics = self.usage_system.get_usage_analytics(user_id)
        
        self.assertEqual(analytics['user_id'], user_id)
        self.assertIn('metrics', analytics)
        self.assertIn(UsageMetric.TRANSCRIPTION_HOURS.value, analytics['metrics'])
        
        transcription_data = analytics['metrics'][UsageMetric.TRANSCRIPTION_HOURS.value]
        self.assertEqual(transcription_data['current_usage'], 4.5)
        self.assertEqual(transcription_data['limit'], 5.0)

def run_all_tests():
    """Run all test suites"""
    print("🧪 Running Usage Tracking System Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestUsageDatabase,
        TestUsageTracker,
        TestQuotaManager,
        TestUsageTrackingSystem,
        TestPerformance,
        TestErrorHandling,
        TestIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        exit(1)