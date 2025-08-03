"""
Unit tests for monitoring components
"""

import pytest
import os
import sys
import json
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock, call
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from monitoring.logger_config import (
    setup_logging,
    get_logger,
    create_logger,
    JSONFormatter,
    add_correlation_id
)
from monitoring.metrics_collector import (
    MetricsCollector,
    ApplicationMetrics
)
from monitoring.audit_logger import (
    AuditLogger,
    AuditEventType
)


class TestJSONFormatter:
    """Test JSON log formatter"""
    
    def test_format_basic_log(self):
        """Test formatting basic log entry"""
        formatter = JSONFormatter()
        
        # Create a log record
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=100,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['level'] == 'INFO'
        assert log_data['logger'] == 'test.logger'
        assert log_data['message'] == 'Test message'
        assert log_data['module'] == 'test'
        assert log_data['line'] == 100
        assert 'timestamp' in log_data
    
    def test_format_with_exception(self):
        """Test formatting log with exception"""
        formatter = JSONFormatter()
        
        # Create exception info
        try:
            raise ValueError("Test exception")
        except Exception:
            exc_info = sys.exc_info()
        
        record = logging.LogRecord(
            name='test.logger',
            level=logging.ERROR,
            pathname='test.py',
            lineno=100,
            msg='Error occurred',
            args=(),
            exc_info=exc_info
        )
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['level'] == 'ERROR'
        assert 'exception' in log_data
        assert 'ValueError: Test exception' in log_data['exception']
    
    def test_format_with_extra_fields(self):
        """Test formatting with extra fields"""
        formatter = JSONFormatter()
        
        record = logging.LogRecord(
            name='test.logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=100,
            msg='User action',
            args=(),
            exc_info=None
        )
        
        # Add extra fields
        record.user_id = 123
        record.request_id = 'req-456'
        record.duration = 1234.56
        
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        assert log_data['user_id'] == 123
        assert log_data['request_id'] == 'req-456'
        assert log_data['duration'] == 1234.56


class TestLoggerConfig:
    """Test logger configuration"""
    
    def test_setup_logging(self):
        """Test basic logging setup"""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, 'test.log')
            
            handlers = setup_logging(
                log_level='INFO',
                log_file=log_file,
                enable_json_logging=True
            )
            
            assert 'console' in handlers
            assert 'file' in handlers
            assert 'error_tracking' in handlers
            
            # Test that logger works
            logger = get_logger('test')
            logger.info("Test message")
            
            # Check log file was created
            assert os.path.exists(log_file)
    
    def test_get_logger(self):
        """Test getting logger instance"""
        logger1 = get_logger('test.module1')
        logger2 = get_logger('test.module2')
        logger3 = get_logger('test.module1')  # Same name
        
        assert logger1.name == 'test.module1'
        assert logger2.name == 'test.module2'
        assert logger1 is logger3  # Same instance
    
    def test_create_logger_with_context(self):
        """Test creating logger with default context"""
        logger = create_logger(
            'test.context',
            user_id=123,
            session_id='sess-456'
        )
        
        # Mock handler to capture log output
        handler = Mock()
        logger.addHandler(handler)
        
        logger.info("Test message")
        
        # Verify extra fields were added
        call_args = handler.handle.call_args[0][0]
        assert hasattr(call_args, 'user_id')
        assert call_args.user_id == 123
        assert hasattr(call_args, 'session_id')
        assert call_args.session_id == 'sess-456'
    
    def test_add_correlation_id(self):
        """Test adding correlation ID to log record"""
        record = Mock()
        record.correlation_id = None
        
        # Test with new correlation ID
        with patch('monitoring.logger_config.correlation_context', {'correlation_id': 'corr-123'}):
            add_correlation_id(record)
            assert record.correlation_id == 'corr-123'
        
        # Test without correlation ID
        with patch('monitoring.logger_config.correlation_context', {}):
            record.correlation_id = None
            add_correlation_id(record)
            assert record.correlation_id is None
    
    @patch.dict(os.environ, {'LOG_FORMAT': 'json'})
    def test_json_console_formatter(self):
        """Test JSON formatter for console in production"""
        handlers = setup_logging(log_level='INFO', enable_json_logging=True)
        
        console_handler = handlers.get('console')
        assert console_handler is not None
        
        # In production mode, should use JSON formatter
        formatter = console_handler.formatter
        assert isinstance(formatter, (JSONFormatter, type(None)))


class TestMetricsCollector:
    """Test metrics collection"""
    
    @pytest.fixture
    def collector(self):
        """Create MetricsCollector instance"""
        return MetricsCollector()
    
    def test_record_counter(self, collector):
        """Test recording counter metrics"""
        collector.record_counter('test.counter', 1)
        collector.record_counter('test.counter', 2)
        collector.record_counter('test.counter', 3, labels={'type': 'test'})
        
        metrics = collector.get_metrics()
        
        # Check unlabeled counter
        key = 'test.counter'
        assert key in metrics['counters']
        assert metrics['counters'][key]['value'] == 3  # 1 + 2
        
        # Check labeled counter
        labeled_key = 'test.counter{type="test"}'
        assert labeled_key in metrics['counters']
        assert metrics['counters'][labeled_key]['value'] == 3
    
    def test_record_gauge(self, collector):
        """Test recording gauge metrics"""
        collector.record_gauge('test.gauge', 10)
        collector.record_gauge('test.gauge', 20)  # Should replace
        collector.record_gauge('test.gauge', 30, labels={'env': 'prod'})
        
        metrics = collector.get_metrics()
        
        # Check unlabeled gauge
        assert metrics['gauges']['test.gauge']['value'] == 20
        
        # Check labeled gauge
        assert metrics['gauges']['test.gauge{env="prod"}']['value'] == 30
    
    def test_record_histogram(self, collector):
        """Test recording histogram metrics"""
        # Record multiple values
        for i in range(100):
            collector.record_histogram('response.time', i)
        
        metrics = collector.get_metrics()
        hist = metrics['histograms']['response.time']
        
        assert hist['count'] == 100
        assert hist['min'] == 0
        assert hist['max'] == 99
        assert hist['sum'] == sum(range(100))
        assert 'buckets' in hist
        
        # Check percentiles
        assert hist['p50'] >= 45 and hist['p50'] <= 55
        assert hist['p95'] >= 90
        assert hist['p99'] >= 95
    
    def test_record_summary(self, collector):
        """Test recording summary metrics"""
        # Record values over time
        values = [10, 20, 30, 40, 50]
        for v in values:
            collector.record_summary('process.duration', v)
        
        metrics = collector.get_metrics()
        summary = metrics['summaries']['process.duration']
        
        assert summary['count'] == 5
        assert summary['sum'] == 150
        assert summary['avg'] == 30
    
    def test_export_prometheus_format(self, collector):
        """Test exporting metrics in Prometheus format"""
        # Add various metrics
        collector.record_counter('http_requests_total', 100, {'method': 'GET'})
        collector.record_gauge('active_connections', 45)
        collector.record_histogram('request_duration_ms', 234)
        
        prometheus_output = collector.export_prometheus()
        
        assert '# TYPE http_requests_total counter' in prometheus_output
        assert 'http_requests_total{method="GET"} 100' in prometheus_output
        assert '# TYPE active_connections gauge' in prometheus_output
        assert 'active_connections 45' in prometheus_output
        assert '# TYPE request_duration_ms histogram' in prometheus_output
    
    @patch('psutil.cpu_percent')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_collect_system_metrics(self, mock_disk, mock_memory, mock_cpu, collector):
        """Test system metrics collection"""
        # Mock system values
        mock_cpu.return_value = 45.5
        mock_memory.return_value = Mock(
            percent=60.2,
            used=4000000000,
            available=2000000000
        )
        mock_disk.return_value = Mock(
            percent=75.0,
            used=80000000000,
            free=20000000000
        )
        
        collector.collect_system_metrics()
        metrics = collector.get_metrics()
        
        assert metrics['gauges']['system.cpu.percent']['value'] == 45.5
        assert metrics['gauges']['system.memory.percent']['value'] == 60.2
        assert metrics['gauges']['system.disk.percent']['value'] == 75.0


class TestApplicationMetrics:
    """Test application-specific metrics"""
    
    @pytest.fixture
    def app_metrics(self):
        """Create ApplicationMetrics instance"""
        return ApplicationMetrics()
    
    def test_track_request(self, app_metrics):
        """Test tracking HTTP requests"""
        app_metrics.track_request(
            method='POST',
            path='/api/transcription',
            status_code=200,
            duration_ms=123.45
        )
        
        metrics = app_metrics.get_metrics()
        
        # Check request count
        counter_key = 'http.requests.total{method="POST",path="/api/transcription",status="200"}'
        assert counter_key in metrics['counters']
        assert metrics['counters'][counter_key]['value'] == 1
        
        # Check duration histogram
        assert 'http.request.duration_ms' in metrics['histograms']
        hist = metrics['histograms']['http.request.duration_ms']
        assert hist['count'] == 1
        assert hist['sum'] == 123.45
    
    def test_track_transcription(self, app_metrics):
        """Test tracking transcription metrics"""
        app_metrics.track_transcription(
            duration_seconds=120.5,
            word_count=500,
            language='en',
            success=True
        )
        
        metrics = app_metrics.get_metrics()
        
        # Check counters
        assert metrics['counters']['transcriptions.total']['value'] == 1
        assert metrics['counters']['transcriptions.success']['value'] == 1
        assert metrics['counters']['transcriptions.words.total']['value'] == 500
        
        # Check language-specific counter
        lang_key = 'transcriptions.by_language{language="en"}'
        assert metrics['counters'][lang_key]['value'] == 1
        
        # Check duration histogram
        assert 'transcription.duration_seconds' in metrics['histograms']
    
    def test_track_error(self, app_metrics):
        """Test tracking errors"""
        app_metrics.track_error(
            error_type='ValueError',
            endpoint='/api/process',
            user_id=123
        )
        
        metrics = app_metrics.get_metrics()
        
        # Check error counter
        error_key = 'errors.total{type="ValueError",endpoint="/api/process"}'
        assert error_key in metrics['counters']
        assert metrics['counters'][error_key]['value'] == 1
    
    def test_track_websocket_event(self, app_metrics):
        """Test tracking WebSocket events"""
        app_metrics.track_websocket_event(
            event_type='message.sent',
            success=True
        )
        
        app_metrics.track_websocket_event(
            event_type='message.sent',
            success=False
        )
        
        metrics = app_metrics.get_metrics()
        
        success_key = 'websocket.events{type="message.sent",status="success"}'
        failure_key = 'websocket.events{type="message.sent",status="failure"}'
        
        assert metrics['counters'][success_key]['value'] == 1
        assert metrics['counters'][failure_key]['value'] == 1
    
    def test_update_active_connections(self, app_metrics):
        """Test updating active connection count"""
        app_metrics.update_active_connections(10)
        app_metrics.update_active_connections(15)
        app_metrics.update_active_connections(12)
        
        metrics = app_metrics.get_metrics()
        
        # Should have latest value
        assert metrics['gauges']['websocket.connections.active']['value'] == 12


class TestAuditLogger:
    """Test audit logging functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def audit_logger(self, mock_db):
        """Create AuditLogger instance"""
        return AuditLogger(mock_db)
    
    def test_log_event_basic(self, audit_logger, mock_db):
        """Test basic event logging"""
        audit_logger.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=123,
            username='testuser',
            ip_address='127.0.0.1'
        )
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Check the audit log entry
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.event_type == AuditEventType.USER_LOGIN.value
        assert audit_entry.user_id == 123
        assert audit_entry.username == 'testuser'
        assert audit_entry.ip_address == '127.0.0.1'
    
    def test_log_event_with_details(self, audit_logger, mock_db):
        """Test logging with additional details"""
        details = {
            'file_name': 'test.mp3',
            'file_size': 1048576,
            'duration': 120.5
        }
        
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=123,
            resource_type='transcript',
            resource_id='456',
            action='export',
            details=details
        )
        
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.resource_type == 'transcript'
        assert audit_entry.resource_id == '456'
        assert audit_entry.action == 'export'
        assert audit_entry.details == json.dumps(details)
    
    def test_log_authentication(self, audit_logger, mock_db):
        """Test authentication logging helper"""
        audit_logger.log_authentication(
            user_id=123,
            username='testuser',
            action='login',
            success=True,
            ip_address='192.168.1.1'
        )
        
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.event_type == AuditEventType.USER_LOGIN.value
        assert audit_entry.result == 'success'
        
        # Test failed login
        audit_logger.log_authentication(
            username='testuser',
            action='login',
            success=False,
            ip_address='192.168.1.1',
            details={'reason': 'Invalid password'}
        )
        
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.event_type == AuditEventType.USER_LOGIN.value
        assert audit_entry.result == 'failure'
        assert 'Invalid password' in audit_entry.details
    
    def test_log_data_access(self, audit_logger, mock_db):
        """Test data access logging helper"""
        audit_logger.log_data_access(
            user_id=123,
            username='testuser',
            action='view',
            resource_type='transcript',
            resource_id='789',
            success=True
        )
        
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.event_type == AuditEventType.DATA_ACCESS.value
        assert audit_entry.action == 'view'
        assert audit_entry.resource_type == 'transcript'
        assert audit_entry.resource_id == '789'
    
    def test_log_security_event(self, audit_logger, mock_db):
        """Test security event logging helper"""
        audit_logger.log_security_event(
            event_type='suspicious_activity',
            user_id=123,
            ip_address='10.0.0.1',
            details={'reason': 'Multiple failed login attempts'}
        )
        
        audit_entry = mock_db.add.call_args[0][0]
        assert audit_entry.event_type == AuditEventType.SECURITY_ALERT.value
        assert 'Multiple failed login attempts' in audit_entry.details
    
    def test_query_logs(self, audit_logger, mock_db):
        """Test querying audit logs"""
        # Mock query results
        mock_logs = [
            Mock(
                id=1,
                event_type='user.login',
                user_id=123,
                created_at=datetime.utcnow()
            ),
            Mock(
                id=2,
                event_type='data.access',
                user_id=123,
                created_at=datetime.utcnow()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_logs
        mock_db.query.return_value = mock_query
        
        # Query with filters
        logs = audit_logger.query_logs(
            user_id=123,
            event_type='user.login',
            limit=10
        )
        
        assert len(logs) == 2
        
        # Verify filters were applied
        mock_query.filter.assert_called()
    
    def test_get_user_activity_summary(self, audit_logger, mock_db):
        """Test getting user activity summary"""
        # Mock query results
        mock_results = [
            Mock(event_type='user.login', count=5),
            Mock(event_type='data.access', count=25),
            Mock(event_type='data.export', count=3)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        
        summary = audit_logger.get_user_activity_summary(
            user_id=123,
            days=30
        )
        
        assert summary['total_events'] == 33  # 5 + 25 + 3
        assert summary['events_by_type']['user.login'] == 5
        assert summary['events_by_type']['data.access'] == 25
        assert summary['events_by_type']['data.export'] == 3
    
    def test_buffered_logging(self, audit_logger, mock_db):
        """Test buffered logging for performance"""
        # Enable buffering
        audit_logger.buffer_size = 5
        audit_logger.buffer = []
        
        # Log multiple events
        for i in range(4):
            audit_logger.log_event(
                event_type=AuditEventType.DATA_ACCESS,
                user_id=i
            )
        
        # Should not commit yet
        assert mock_db.commit.call_count == 0
        
        # Fifth event should trigger flush
        audit_logger.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=5
        )
        
        # Should have flushed buffer
        assert mock_db.add.call_count == 5
        assert mock_db.commit.call_count == 1
    
    def test_database_error_handling(self, audit_logger, mock_db):
        """Test handling database errors"""
        # Mock database error
        mock_db.commit.side_effect = Exception("Database error")
        
        # Should not raise exception
        audit_logger.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=123
        )
        
        # Should have rolled back
        mock_db.rollback.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])