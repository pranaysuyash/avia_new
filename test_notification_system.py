#!/usr/bin/env python3
"""
Test script for the enhanced notification system
"""

import asyncio
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notifications.enhanced_notification_manager import (
    EnhancedNotificationManager,
    NotificationRequest,
    NotificationType,
    NotificationChannel,
    NotificationPriority,
    NotificationConfig
)

# Load environment variables
load_dotenv()

async def test_email_notification():
    """Test email notification"""
    print("\n🧪 Testing Email Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.PROCESSING_COMPLETE,
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.EMAIL],
        data={
            "user_name": "Test User",
            "file_name": "test_audio.mp3",
            "duration": 300,
            "language": "English",
            "speaker_count": 3,
            "processing_time": 60,
            "transcript_url": "https://example.com/transcript/123",
            "transcript_id": "123",
            "timestamp": datetime.utcnow().isoformat()
        }
    )
    
    results = await manager.send_notification(request)
    print(f"Email Result: {results}")

async def test_sms_notification():
    """Test SMS notification"""
    print("\n🧪 Testing SMS Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.PROCESSING_COMPLETE,
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.SMS],
        data={
            "file_name": "test_audio.mp3",
            "short_url": "https://bit.ly/test123"
        }
    )
    
    results = await manager.send_notification(request)
    print(f"SMS Result: {results}")

async def test_webhook_notification():
    """Test webhook notification"""
    print("\n🧪 Testing Webhook Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.PROCESSING_COMPLETE,
        priority=NotificationPriority.MEDIUM,
        channels=[NotificationChannel.WEBHOOK],
        data={
            "timestamp": datetime.utcnow().isoformat(),
            "transcript_id": "123",
            "file_name": "test_audio.mp3",
            "duration": 300,
            "language": "English",
            "download_url": "https://example.com/download/123"
        }
    )
    
    results = await manager.send_notification(request)
    print(f"Webhook Result: {results}")

async def test_in_app_notification():
    """Test in-app notification"""
    print("\n🧪 Testing In-App Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.PROCESSING_COMPLETE,
        priority=NotificationPriority.MEDIUM,
        channels=[NotificationChannel.IN_APP],
        data={
            "file_name": "test_audio.mp3",
            "transcript_url": "/transcript/123"
        }
    )
    
    results = await manager.send_notification(request)
    print(f"In-App Result: {results}")
    
    # Get notifications
    notifications = await manager.get_user_notifications("1", limit=5)
    print(f"\nRecent notifications: {len(notifications)}")
    for notif in notifications[:3]:
        print(f"  - {notif.get('title')} ({notif.get('timestamp')})")

async def test_multi_channel_notification():
    """Test multi-channel notification"""
    print("\n🧪 Testing Multi-Channel Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.USAGE_LIMIT_WARNING,
        priority=NotificationPriority.HIGH,
        channels=[
            NotificationChannel.EMAIL,
            NotificationChannel.IN_APP,
            NotificationChannel.WEBHOOK
        ],
        data={
            "user_name": "Test User",
            "usage_percentage": 90,
            "current_usage": 900,
            "limit": 1000,
            "unit": "minutes",
            "upgrade_url": "https://example.com/pricing"
        }
    )
    
    results = await manager.send_notification(request)
    print(f"Multi-Channel Results:")
    for channel, result in results.items():
        print(f"  - {channel}: {result}")

async def test_priority_routing():
    """Test priority-based routing"""
    print("\n🧪 Testing Priority-Based Routing...")
    
    manager = EnhancedNotificationManager()
    
    # Critical priority - should use all channels
    critical_request = NotificationRequest(
        user_id="1",
        type=NotificationType.CRITICAL_ALERT,
        priority=NotificationPriority.CRITICAL,
        data={
            "message": "Critical system alert - immediate attention required!"
        }
    )
    
    results = await manager.send_notification(critical_request)
    print(f"Critical Priority Results (should use multiple channels):")
    for channel, result in results.items():
        print(f"  - {channel}: {result}")

async def test_batch_complete_notification():
    """Test batch complete notification"""
    print("\n🧪 Testing Batch Complete Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.BATCH_COMPLETE,
        priority=NotificationPriority.MEDIUM,
        channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        data={
            "user_name": "Test User",
            "total_files": 25,
            "successful_files": 23,
            "failed_files": 2,
            "total_duration": "2 hours 15 minutes",
            "batch_results_url": "https://example.com/batch/results/batch456"
        }
    )
    
    results = await manager.send_notification(request)
    print(f"Batch Complete Results: {results}")

async def test_processing_failed_notification():
    """Test processing failed notification"""
    print("\n🧪 Testing Processing Failed Notification...")
    
    manager = EnhancedNotificationManager()
    
    request = NotificationRequest(
        user_id="1",
        type=NotificationType.PROCESSING_FAILED,
        priority=NotificationPriority.HIGH,
        channels=[NotificationChannel.EMAIL, NotificationChannel.IN_APP],
        data={
            "user_name": "Test User",
            "file_name": "corrupted_audio.mp3",
            "error_message": "Audio file is corrupted or in an unsupported format",
            "support_url": "https://example.com/support"
        }
    )
    
    results = await manager.send_notification(request)
    print(f"Processing Failed Results: {results}")

def check_configuration():
    """Check notification service configuration"""
    print("\n🔧 Checking Configuration...")
    
    config_status = {
        "Email": {
            "SMTP_HOST": os.getenv("SMTP_HOST"),
            "SMTP_USERNAME": os.getenv("SMTP_USERNAME"),
            "configured": bool(os.getenv("SMTP_USERNAME"))
        },
        "SMS": {
            "TWILIO_ACCOUNT_SID": os.getenv("TWILIO_ACCOUNT_SID"),
            "configured": bool(os.getenv("TWILIO_ACCOUNT_SID"))
        },
        "AWS SNS": {
            "AWS_ACCESS_KEY_ID": os.getenv("AWS_ACCESS_KEY_ID"),
            "configured": bool(os.getenv("AWS_ACCESS_KEY_ID"))
        },
        "Redis": {
            "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
            "configured": True
        }
    }
    
    print("\n📊 Service Configuration Status:")
    for service, config in config_status.items():
        status = "✅ Configured" if config["configured"] else "❌ Not Configured"
        print(f"  - {service}: {status}")
        if not config["configured"] and service != "Redis":
            print(f"    💡 Set environment variables to enable {service} notifications")

async def main():
    """Run all tests"""
    print("🚀 Enhanced Notification System Test Suite")
    print("=" * 50)
    
    # Check configuration
    check_configuration()
    
    # Run tests based on available configuration
    manager = EnhancedNotificationManager()
    
    # Always test in-app notifications (uses Redis)
    await test_in_app_notification()
    
    # Test email if configured
    if manager.config.smtp_username:
        await test_email_notification()
    else:
        print("\n⚠️  Skipping email test - SMTP not configured")
    
    # Test SMS if configured
    if manager.twilio_client:
        await test_sms_notification()
    else:
        print("\n⚠️  Skipping SMS test - Twilio not configured")
    
    # Test webhook (usually works with test endpoints)
    await test_webhook_notification()
    
    # Test multi-channel and priority routing
    await test_multi_channel_notification()
    await test_priority_routing()
    
    # Test specific notification types
    await test_batch_complete_notification()
    await test_processing_failed_notification()
    
    print("\n✅ Test suite completed!")
    print("\n📌 Next steps:")
    print("  1. Configure environment variables for email/SMS/webhook services")
    print("  2. Run the demo app: streamlit run demo_notification_system.py")
    print("  3. Integrate notifications into your main application")

if __name__ == "__main__":
    asyncio.run(main())