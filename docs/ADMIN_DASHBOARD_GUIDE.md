# Comprehensive Admin Dashboard Guide

## Overview

The Comprehensive Admin Dashboard provides administrators with complete control and visibility over the transcription platform. It includes real-time monitoring, user management, system configuration, audit logging, and backup capabilities.

## Key Features

### 1. System Monitoring Service
- **Real-time Metrics**: CPU, memory, disk, and network usage
- **Service Health Checks**: Database, Redis, storage, email, and WebSocket status
- **Performance Monitoring**: API response times, database queries, transcription processing
- **Alert System**: Automatic alerts for system issues

### 2. Admin Dashboard UI (`streamlit_admin_dashboard.py`)
- **Dashboard Overview**: Quick stats and system health
- **User Management**: View, create, update, suspend users
- **Team Management**: Manage teams and permissions
- **Subscription Management**: View and manage subscriptions
- **System Configuration**: Update system settings
- **Reports**: Generate various reports

### 3. Admin Usage Dashboard (`streamlit_admin_usage_dashboard.py`)
- **System Overview**: Total usage metrics across all users
- **User Analytics**: Top users by usage type
- **Plan Distribution**: Usage breakdown by subscription plan
- **Resource Usage**: Storage and processing analytics
- **Revenue Analytics**: MRR, churn, and growth metrics
- **Alerts & Actions**: Administrative controls

### 4. Audit Logging System
- **Comprehensive Logging**: All system activities logged
- **Event Types**: Authentication, user management, data access, configuration changes
- **Compliance Reports**: Generate reports for auditing
- **Search & Filter**: Advanced search capabilities
- **Export Options**: CSV and JSON export

### 5. Backup Service
- **Automated Backups**: Scheduled full and incremental backups
- **Component Selection**: Database, configuration, files, audit logs
- **Compression**: Optional backup compression
- **S3 Integration**: Upload backups to S3 for redundancy
- **Restore Capability**: Selective component restoration

### 6. WebSocket Monitoring
- **Real-time Updates**: Live system metrics via WebSocket
- **Admin Commands**: Remote system control
- **Alert Broadcasting**: Instant alert notifications

## Architecture

### Services

1. **System Monitoring Service** (`services/system_monitoring_service.py`)
   - Collects system metrics using psutil
   - Monitors service health
   - Tracks performance metrics
   - Generates alerts

2. **Audit Logging Service** (`services/audit_logging_service.py`)
   - Separate database for audit logs
   - Comprehensive event tracking
   - Compliance reporting
   - Log retention management

3. **Usage Analytics Service** (`services/usage_analytics_service.py`)
   - Usage trend analysis
   - Forecasting
   - Alert generation
   - Report generation

4. **Backup Service** (`services/backup_service.py`)
   - Database backups using pg_dump
   - Configuration backup
   - File storage backup
   - S3 integration

### API Endpoints

1. **Admin Endpoints** (`api/endpoints/admin.py`)
   - `/api/admin/stats/quick` - Quick statistics
   - `/api/admin/stats/detailed` - Detailed statistics
   - `/api/admin/users` - User management
   - `/api/admin/announcement` - System announcements
   - `/api/admin/system/health` - System health check
   - `/api/admin/backup` - Backup management

2. **Audit Endpoints** (`api/endpoints/audit.py`)
   - `/api/audit/logs` - Query audit logs
   - `/api/audit/logs/security` - Security events
   - `/api/audit/logs/compliance-report` - Compliance reports
   - `/api/audit/logs/export` - Export logs
   - `/api/audit/my-activity` - User's own activity

3. **Admin WebSocket** (`api/websocket/admin_monitoring_ws.py`)
   - `/api/ws/admin/monitoring` - Real-time monitoring

### Middleware

**Audit Middleware** (`api/middleware/audit_middleware.py`)
- Automatically logs API requests
- Tracks authentication attempts
- Records data access
- Monitors configuration changes

## Usage Examples

### Accessing the Admin Dashboard

```python
# Streamlit UI
streamlit run streamlit_admin_dashboard.py

# Admin must be authenticated
# Access requires 'admin' role
```

### System Monitoring

```python
from services.system_monitoring_service import monitoring_service

# Get current system metrics
metrics = monitoring_service.get_system_metrics()

# Check service health
health = monitoring_service.check_service_health()

# Get performance metrics
performance = monitoring_service.get_performance_metrics(minutes=60)

# Get alerts
alerts = monitoring_service.get_alerts()
```

### Audit Logging

```python
from services.audit_logging_service import audit_service, AuditEventType

# Log an event
audit_service.log_event(
    event_type=AuditEventType.CONFIG_CHANGE,
    action="Updated email settings",
    user_id=admin_user.id,
    username=admin_user.username,
    details={'setting': 'email_provider', 'old': 'sendgrid', 'new': 'ses'}
)

# Query logs
logs = audit_service.query_logs(
    start_date=datetime.now() - timedelta(days=7),
    event_types=[AuditEventType.LOGIN_FAILED.value]
)

# Generate compliance report
report = audit_service.get_compliance_report(
    start_date=datetime(2024, 1, 1),
    end_date=datetime(2024, 1, 31)
)
```

### Creating Backups

```python
from services.backup_service import backup_service

# Create full backup
result = await backup_service.create_backup(
    backup_type="full",
    include_files=True,
    compress=True,
    user_id=admin_user.id
)

# List backups
backups = backup_service.list_backups()

# Restore from backup
restore_result = await backup_service.restore_backup(
    backup_id="backup_20240120_120000",
    components=["database", "configuration"]
)
```

### WebSocket Monitoring

```javascript
// Connect to admin monitoring WebSocket
const ws = new WebSocket('ws://localhost:8000/api/ws/admin/monitoring');

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    if (data.type === 'update') {
        // Handle system metrics update
        updateDashboard(data.data);
    } else if (data.type === 'alert') {
        // Handle system alert
        showAlert(data.data);
    }
};

// Send command
ws.send(JSON.stringify({
    type: 'set_interval',
    interval: 10  // Update every 10 seconds
}));
```

## Security Considerations

1. **Role-Based Access**: All admin endpoints require 'admin' role
2. **Audit Trail**: All admin actions are logged
3. **Sensitive Data**: Passwords and secrets are masked in backups
4. **IP Tracking**: Admin actions track IP addresses
5. **Session Management**: Admin sessions have shorter timeouts

## Configuration

### Environment Variables

```bash
# Monitoring
MONITORING_INTERVAL=60  # Seconds between metric collections

# Audit
AUDIT_DATABASE_URL=postgresql://...  # Separate audit database
AUDIT_RETENTION_DAYS=90  # Days to retain audit logs

# Backup
BACKUP_DIR=/var/backups
BACKUP_S3_BUCKET=my-backup-bucket
BACKUP_RETENTION_DAYS=30

# Admin
ADMIN_SESSION_TIMEOUT=1800  # 30 minutes
ADMIN_2FA_REQUIRED=true
```

### Performance Tuning

1. **Monitoring Frequency**: Adjust `update_interval` for WebSocket updates
2. **Audit Batch Size**: Configure audit log query limits
3. **Backup Scheduling**: Set up cron jobs for automated backups
4. **Alert Thresholds**: Customize alert thresholds in monitoring service

## Troubleshooting

### Common Issues

1. **High CPU Usage Alerts**
   - Check monitoring interval settings
   - Review active transcription jobs
   - Verify database query performance

2. **Backup Failures**
   - Check disk space
   - Verify database credentials
   - Ensure S3 permissions

3. **Audit Log Growth**
   - Run cleanup for old logs
   - Adjust retention policy
   - Consider archiving to S3

4. **WebSocket Disconnections**
   - Check network stability
   - Verify authentication
   - Review server logs

## Best Practices

1. **Regular Monitoring**
   - Check dashboard daily
   - Review alerts promptly
   - Monitor resource trends

2. **Backup Strategy**
   - Daily incremental backups
   - Weekly full backups
   - Test restore procedures

3. **Audit Review**
   - Weekly security event review
   - Monthly compliance reports
   - Investigate anomalies

4. **User Management**
   - Regular access reviews
   - Prompt suspension of inactive accounts
   - Document role changes

## Integration Points

1. **Monitoring Integration**
   - Export metrics to Prometheus
   - Send alerts to PagerDuty
   - Log aggregation with ELK stack

2. **Backup Integration**
   - Automated S3 lifecycle policies
   - Glacier archival for old backups
   - Cross-region replication

3. **Audit Integration**
   - SIEM integration
   - Compliance automation
   - Security orchestration

## Future Enhancements

1. **Advanced Analytics**
   - Predictive maintenance
   - Anomaly detection
   - Capacity planning

2. **Automation**
   - Self-healing systems
   - Automated scaling
   - Intelligent alerting

3. **Compliance**
   - GDPR tools
   - SOC 2 reporting
   - HIPAA compliance

## Support

For admin dashboard issues:
1. Check system logs in `/var/log/app/`
2. Review audit logs for errors
3. Contact platform support team
4. Refer to internal documentation