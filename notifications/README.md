# Enhanced Notification System

A comprehensive multi-channel notification system supporting Email, SMS, Webhooks, In-App notifications, and third-party integrations (Slack, Teams, Discord).

## Features

### Multi-Channel Support
- **Email** - Rich HTML emails with customizable templates
- **SMS** - Text messages via Twilio
- **Webhooks** - Real-time notifications to external systems
- **In-App** - Real-time notifications via Redis and WebSockets
- **Slack** - Team notifications via webhooks
- **Microsoft Teams** - Corporate communication via webhooks
- **Discord** - Community notifications via webhooks

### Smart Routing
- Priority-based delivery (Low, Medium, High, Critical)
- User preference management
- Channel fallback support
- Retry mechanisms with exponential backoff
- Rate limiting

### Templates
- Pre-defined templates for common notification types
- Jinja2-based template rendering
- Support for HTML emails and structured messages
- Customizable per channel

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
# Email configuration (SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAIL_FROM=noreply@yourapp.com
EMAIL_FROM_NAME=Your App Name

# SMS configuration (Twilio)
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# AWS SNS (optional)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1

# Redis (for in-app notifications)
REDIS_URL=redis://localhost:6379

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

## Quick Start

### Basic Usage

```python
from notifications.api import notify_processing_complete

# Send notification when processing is complete
await notify_processing_complete(
    user_id="123",
    file_name="audio.mp3",
    transcript_id="abc123",
    duration=180,
    language="English",
    speaker_count=2
)
```

### Using the API Wrapper

```python
from notifications import api as notify_api

# Processing complete
await notify_api.notify_processing_complete(
    user_id="123",
    file_name="meeting.mp4",
    transcript_id="transcript_123",
    duration=3600,
    language="English",
    speaker_count=5,
    processing_time=120.5
)

# Processing failed
await notify_api.notify_processing_failed(
    user_id="123",
    file_name="corrupted.mp3",
    error_message="Audio file is corrupted"
)

# Usage warning
await notify_api.notify_usage_limit_warning(
    user_id="123",
    usage_percentage=90,
    current_usage=900,
    limit=1000,
    unit="minutes"
)

# Batch complete
await notify_api.notify_batch_complete(
    user_id="123",
    total_files=25,
    successful_files=23,
    failed_files=2,
    batch_id="batch_456",
    total_duration="2 hours 15 minutes"
)

# Simple in-app notification
await notify_api.send_in_app(
    user_id="123",
    title="New Feature Available",
    message="Check out our new speaker identification feature!",
    action_url="/features/speaker-id"
)
```

### Direct Manager Usage

```python
from notifications.enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationType,
    NotificationChannel,
    NotificationPriority
)

manager = EnhancedNotificationManager()

request = NotificationRequest(
    user_id="123",
    type=NotificationType.PROCESSING_COMPLETE,
    priority=NotificationPriority.HIGH,
    channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
    data={
        "user_name": "John Doe",
        "file_name": "audio.mp3",
        "duration": 180,
        "transcript_url": "/transcript/abc123"
    }
)

results = await manager.send_notification(request)
```

## Integration with Main Application

### In STT Processing

```python
# In stt.py or your processing module
from notifications import api as notify_api

async def process_audio_file(file_path, user_id):
    try:
        # Start processing
        start_time = time.time()
        
        # ... your processing code ...
        transcript = await transcribe_audio(file_path)
        transcript_id = save_transcript(transcript)
        
        # Send success notification
        processing_time = time.time() - start_time
        await notify_api.notify_processing_complete(
            user_id=user_id,
            file_name=os.path.basename(file_path),
            transcript_id=transcript_id,
            duration=get_audio_duration(file_path),
            language=transcript.language,
            speaker_count=len(transcript.speakers),
            processing_time=processing_time
        )
        
    except Exception as e:
        # Send failure notification
        await notify_api.notify_processing_failed(
            user_id=user_id,
            file_name=os.path.basename(file_path),
            error_message=str(e)
        )
        raise
```

### In Batch Processing

```python
# In your batch processing module
from notifications import api as notify_api

async def process_batch(batch_id, file_list, user_id):
    results = {"success": 0, "failed": 0}
    
    for file in file_list:
        try:
            await process_file(file)
            results["success"] += 1
        except:
            results["failed"] += 1
    
    # Send batch complete notification
    await notify_api.notify_batch_complete(
        user_id=user_id,
        total_files=len(file_list),
        successful_files=results["success"],
        failed_files=results["failed"],
        batch_id=batch_id
    )
```

## Running the Demo

```bash
# Run the test suite
python test_notification_system.py

# Run the interactive demo
streamlit run demo_notification_system.py
```

## Notification Types

### Processing Complete
Sent when audio/video processing finishes successfully.

### Processing Failed
Sent when processing encounters an error.

### Usage Limit Warning
Sent when user approaches their usage limits.

### Batch Complete
Sent when batch processing finishes.

### System Update
General system notifications and announcements.

### Transcript Ready
Sent when transcript is ready for download.

### Export Ready
Sent when export file is ready for download.

## User Preferences

Users can configure their notification preferences:

```python
from notifications import api as notify_api
from notifications.enhanced_notification_manager import NotificationChannel

# Update user preferences
await notify_api.update_user_preferences(
    user_id="123",
    preferences={
        NotificationChannel.EMAIL: True,
        NotificationChannel.SMS: False,
        NotificationChannel.IN_APP: True,
        NotificationChannel.SLACK: True
    }
)
```

## In-App Notifications

Access in-app notifications:

```python
# Get user notifications
notifications = await notify_api.get_user_notifications(
    user_id="123",
    limit=20
)

# Mark as read
await notify_api.mark_notification_read(
    user_id="123",
    notification_id="notif_12345"
)
```

## Webhook Integration

Configure webhooks in user settings:

```json
{
    "webhook_url": "https://your-server.com/webhook",
    "webhook_secret": "your-secret-key"
}
```

Webhook payload example:

```json
{
    "event": "transcription.completed",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "transcript_id": "123",
        "file_name": "audio.mp3",
        "duration": 180,
        "status": "completed"
    }
}
```

## Third-Party Integrations

### Slack
1. Create incoming webhook: https://api.slack.com/messaging/webhooks
2. Add webhook URL to user settings

### Microsoft Teams
1. Create incoming webhook in Teams channel
2. Add webhook URL to user settings

### Discord
1. Create webhook in Discord channel settings
2. Add webhook URL to user settings

## Architecture

```
EnhancedNotificationManager
├── Template System (Jinja2)
├── Channel Handlers
│   ├── Email (SMTP)
│   ├── SMS (Twilio)
│   ├── Webhook (HTTP)
│   ├── In-App (Redis)
│   ├── Slack (Webhook)
│   ├── Teams (Webhook)
│   └── Discord (Webhook)
├── Priority Routing
├── User Preferences
└── Logging & Analytics
```

## Best Practices

1. **Use appropriate priority levels**
   - Critical: System failures, security alerts
   - High: Processing failures, important updates
   - Medium: Processing complete, general updates
   - Low: System announcements, tips

2. **Respect user preferences**
   - Always check user notification preferences
   - Provide easy opt-out mechanisms
   - Use appropriate channels for different types

3. **Template customization**
   - Keep messages concise and actionable
   - Include relevant links and CTAs
   - Use consistent branding

4. **Error handling**
   - Implement retry logic for transient failures
   - Log failures for debugging
   - Have fallback channels

## Testing

Run the test suite:

```bash
python test_notification_system.py
```

This will:
- Check service configuration
- Test each notification channel
- Verify multi-channel delivery
- Test priority-based routing
- Validate notification templates

## Troubleshooting

### Email not sending
- Check SMTP credentials
- Verify firewall/network settings
- Enable "Less secure app access" for Gmail

### SMS not working
- Verify Twilio credentials
- Check phone number format (+1234567890)
- Ensure Twilio account has credits

### In-App notifications not appearing
- Check Redis connection
- Verify Redis is running
- Check WebSocket connection in frontend

### Webhook failures
- Verify webhook URL is accessible
- Check for SSL certificate issues
- Review webhook response codes

## License

This notification system is part of the NER Video Transcription project.