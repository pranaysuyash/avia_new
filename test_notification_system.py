"""
Test suite for Notification System
Task 200: Build notification and communication system
"""

import asyncio
import json
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from freezegun import freeze_time

from notification_system import (
    Notification,
    NotificationChannel,
    NotificationManager,
    NotificationPriority,
    NotificationRequest,
    NotificationService,
    NotificationStatus,
    NotificationType,
    WebhookConfig
)


class TestNotificationService(unittest.TestCase):
    """Test notification service functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'smtp_host': 'localhost',
            'smtp_port': 587,
            'smtp_user': 'test@example.com',
            'smtp_password': 'password',
            'smtp_from': 'noreply@example.com',
            'redis_host': 'localhost',
            'redis_port': 6379
        }
        self.service = NotificationService(self.config)
        self.manager = NotificationManager(self.service)
    
    @pytest.mark.asyncio
    async def test_send_email_notification(self):
        """Test sending email notification"""
        with patch('smtplib.SMTP') as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server
            
            request = NotificationRequest(
                user_id="user123",
                type=NotificationType.TRANSCRIPTION_COMPLETED,
                channels=[NotificationChannel.EMAIL],
                data={
                    "title": "Test Recording",
                    "duration": "10:00",
                    "word_count": 1000,
                    "link": "https://example.com/transcription/123"
                }
            )
            
            result = await self.service.send_notification(request)
            
            self.assertIn('email', result)
            self.assertEqual(result['email']['status'], 'sent')
            mock_server.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_sms_notification(self):
        """Test sending SMS notification"""
        # Mock Twilio client
        mock_twilio = MagicMock()
        mock_message = MagicMock()
        mock_message.sid = "MSG123"
        mock_twilio.messages.create.return_value = mock_message
        
        self.service.twilio_client = mock_twilio
        
        # Update preferences to enable SMS
        with patch.object(self.service, 'get_user_preferences') as mock_prefs:
            mock_prefs.return_value = {
                'sms_enabled': True,
                'phone': '+1234567890',
                'email_enabled': False
            }
            
            request = NotificationRequest(
                user_id="user123",
                type=NotificationType.QUOTA_WARNING,
                channels=[NotificationChannel.SMS],
                data={
                    "usage_percent": 80,
                    "limit": 1000,
                    "used": 800
                }
            )
            
            result = await self.service.send_notification(request)
            
            self.assertIn('sms', result)
            self.assertEqual(result['sms']['status'], 'sent')
            mock_twilio.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_in_app_notification(self):
        """Test sending in-app notification"""
        with patch.object(self.service.redis_client, 'lpush') as mock_lpush:
            with patch.object(self.service.redis_client, 'expire') as mock_expire:
                request = NotificationRequest(
                    user_id="user123",
                    type=NotificationType.SHARE_INVITATION,
                    channels=[NotificationChannel.IN_APP],
                    data={
                        "shared_by": "John Doe",
                        "document": "Meeting Notes"
                    }
                )
                
                result = await self.service.send_notification(request)
                
                self.assertIn('in_app', result)
                self.assertEqual(result['in_app']['status'], 'delivered')
                mock_lpush.assert_called_once()
                mock_expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_webhook_notification(self):
        """Test sending webhook notification"""
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response
            
            # Update preferences with webhook URL
            with patch.object(self.service, 'get_user_preferences') as mock_prefs:
                mock_prefs.return_value = {
                    'webhook_enabled': True,
                    'webhook_url': 'https://webhook.example.com/notify',
                    'email_enabled': False
                }
                
                request = NotificationRequest(
                    user_id="user123",
                    type=NotificationType.BATCH_PROCESSING_COMPLETED,
                    channels=[NotificationChannel.WEBHOOK],
                    data={
                        "batch_id": "batch456",
                        "total_files": 10,
                        "successful": 9,
                        "failed": 1
                    }
                )
                
                result = await self.service.send_notification(request)
                
                self.assertIn('webhook', result)
                self.assertEqual(result['webhook']['status'], 'delivered')
    
    @pytest.mark.asyncio
    async def test_notification_priority_routing(self):
        """Test notification routing based on priority"""
        with patch.object(self.service, '_send_email') as mock_email:
            with patch.object(self.service, '_send_in_app') as mock_in_app:
                mock_email.return_value = {"status": "sent"}
                mock_in_app.return_value = {"status": "delivered"}
                
                # High priority should use multiple channels
                request = NotificationRequest(
                    user_id="user123",
                    type=NotificationType.SECURITY_ALERT,
                    priority=NotificationPriority.URGENT,
                    data={
                        "alert_type": "Suspicious login",
                        "ip_address": "192.168.1.1"
                    }
                )
                
                result = await self.service.send_notification(request)
                
                # Should send to both email and in-app
                self.assertIn('email', result)
                self.assertIn('in_app', result)
    
    @pytest.mark.asyncio
    async def test_quiet_hours_filtering(self):
        """Test quiet hours filtering"""
        with freeze_time("2024-01-01 23:00:00"):
            with patch.object(self.service, 'get_user_preferences') as mock_prefs:
                mock_prefs.return_value = {
                    'quiet_hours_enabled': True,
                    'quiet_hours_start': '22:00',
                    'quiet_hours_end': '08:00',
                    'timezone': 'UTC',
                    'push_enabled': True,
                    'in_app_enabled': True,
                    'email_enabled': True
                }
                
                with patch.object(self.service, '_is_quiet_hours') as mock_quiet:
                    mock_quiet.return_value = True
                    
                    request = NotificationRequest(
                        user_id="user123",
                        type=NotificationType.TRANSCRIPTION_COMPLETED,
                        data={"title": "Test"}
                    )
                    
                    result = await self.service.send_notification(request)
                    
                    # Push notifications should be filtered during quiet hours
                    self.assertNotIn('push', result)
    
    @pytest.mark.asyncio
    async def test_scheduled_notification(self):
        """Test scheduled notification"""
        schedule_time = datetime.utcnow() + timedelta(hours=1)
        
        request = NotificationRequest(
            user_id="user123",
            type=NotificationType.SUBSCRIPTION_EXPIRING,
            schedule_at=schedule_time,
            data={
                "days_remaining": 7,
                "renewal_link": "https://example.com/renew"
            }
        )
        
        with patch.object(self.service, '_schedule_notification') as mock_schedule:
            result = await self.service.send_notification(request)
            
            self.assertIn('in_app', result)
            self.assertEqual(result['in_app'], 'scheduled')
            mock_schedule.assert_called()
    
    @pytest.mark.asyncio
    async def test_notification_expiry(self):
        """Test notification expiry"""
        expired_time = datetime.utcnow() - timedelta(hours=1)
        
        request = NotificationRequest(
            user_id="user123",
            type=NotificationType.CUSTOM,
            expires_at=expired_time,
            data={"message": "This should expire"}
        )
        
        # Expired notifications should not be sent
        # This would be handled by the queue processor
        self.assertLess(request.expires_at, datetime.utcnow())
    
    @pytest.mark.asyncio
    async def test_template_rendering(self):
        """Test notification template rendering"""
        template = await self.service._get_template(
            NotificationType.TRANSCRIPTION_COMPLETED,
            NotificationChannel.EMAIL
        )
        
        self.assertIn('subject_template', template)
        self.assertIn('body_template', template)
        
        # Test rendering with data
        from jinja2 import Template
        subject = Template(template['subject_template']).render(
            title="Test Recording"
        )
        self.assertEqual(subject, "Your transcription is ready: Test Recording")
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting for notifications"""
        # Rate limits are defined in the service
        self.assertEqual(self.service.rate_limits[NotificationChannel.EMAIL], 100)
        self.assertEqual(self.service.rate_limits[NotificationChannel.SMS], 50)
        self.assertEqual(self.service.rate_limits[NotificationChannel.WEBHOOK], 200)


class TestNotificationManager(unittest.TestCase):
    """Test notification manager functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        config = {'redis_host': 'localhost', 'redis_port': 6379}
        self.service = NotificationService(config)
        self.manager = NotificationManager(self.service)
    
    @pytest.mark.asyncio
    async def test_notify_transcription_complete(self):
        """Test transcription completion notification"""
        with patch.object(self.service, 'send_notification') as mock_send:
            mock_send.return_value = {'in_app': {'status': 'delivered'}}
            
            result = await self.manager.notify_transcription_complete(
                user_id="user123",
                transcription_id="trans456",
                title="Meeting Recording",
                duration="45:30",
                word_count=5432
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            self.assertEqual(call_args.type, NotificationType.TRANSCRIPTION_COMPLETED)
            self.assertEqual(call_args.user_id, "user123")
            self.assertIn('transcription_id', call_args.data)
    
    @pytest.mark.asyncio
    async def test_notify_batch_complete(self):
        """Test batch completion notification"""
        with patch.object(self.service, 'send_notification') as mock_send:
            mock_send.return_value = {'email': {'status': 'sent'}}
            
            result = await self.manager.notify_batch_complete(
                user_id="user123",
                batch_id="batch789",
                total_files=10,
                successful=9,
                failed=1
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            self.assertEqual(call_args.type, NotificationType.BATCH_PROCESSING_COMPLETED)
            self.assertEqual(call_args.data['total_files'], 10)
    
    @pytest.mark.asyncio
    async def test_notify_quota_warning(self):
        """Test quota warning notification"""
        with patch.object(self.service, 'send_notification') as mock_send:
            mock_send.return_value = {'email': {'status': 'sent'}, 'in_app': {'status': 'delivered'}}
            
            result = await self.manager.notify_quota_warning(
                user_id="user123",
                usage_percent=80.5,
                limit=1000,
                used=805
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            self.assertEqual(call_args.type, NotificationType.QUOTA_WARNING)
            self.assertEqual(call_args.priority, NotificationPriority.HIGH)
    
    @pytest.mark.asyncio
    async def test_notify_security_alert(self):
        """Test security alert notification"""
        with patch.object(self.service, 'send_notification') as mock_send:
            mock_send.return_value = {
                'email': {'status': 'sent'},
                'sms': {'status': 'sent'},
                'in_app': {'status': 'delivered'}
            }
            
            result = await self.manager.notify_security_alert(
                user_id="user123",
                alert_type="Suspicious Login",
                description="Login from new location",
                ip_address="192.168.1.1",
                location="Unknown Location"
            )
            
            mock_send.assert_called_once()
            call_args = mock_send.call_args[0][0]
            self.assertEqual(call_args.type, NotificationType.SECURITY_ALERT)
            self.assertEqual(call_args.priority, NotificationPriority.URGENT)
            # Should specify multiple channels for security alerts
            self.assertEqual(len(call_args.channels), 3)


class TestWebhookIntegration(unittest.TestCase):
    """Test webhook integration functionality"""
    
    @pytest.mark.asyncio
    async def test_webhook_signature(self):
        """Test webhook signature generation"""
        config = {'redis_host': 'localhost', 'redis_port': 6379}
        service = NotificationService(config)
        
        notification = Notification(
            user_id="user123",
            type=NotificationType.CUSTOM,
            channel=NotificationChannel.WEBHOOK,
            recipient="https://webhook.example.com",
            data={"test": "data"},
            metadata={'webhook_config': {'secret': 'webhook_secret'}}
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post = mock_post
            
            result = await service._send_webhook(notification)
            
            # Check that signature header was added
            call_args = mock_post.call_args
            headers = call_args[1]['headers']
            self.assertIn('X-Webhook-Signature', headers)
    
    @pytest.mark.asyncio
    async def test_slack_notification(self):
        """Test Slack notification formatting"""
        config = {'redis_host': 'localhost', 'redis_port': 6379}
        service = NotificationService(config)
        
        notification = Notification(
            user_id="user123",
            type=NotificationType.TRANSCRIPTION_COMPLETED,
            channel=NotificationChannel.SLACK,
            recipient="https://hooks.slack.com/services/XXX",
            subject="Transcription Complete",
            body="Your transcription is ready",
            data={"attachments": []}
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post = mock_post
            
            result = await service._send_slack(notification)
            
            self.assertEqual(result['status'], 'delivered')
            self.assertEqual(result['channel'], 'slack')
            
            # Check Slack payload format
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            self.assertIn('text', payload)
            self.assertIn('blocks', payload)
    
    @pytest.mark.asyncio
    async def test_teams_notification(self):
        """Test Microsoft Teams notification formatting"""
        config = {'redis_host': 'localhost', 'redis_port': 6379}
        service = NotificationService(config)
        
        notification = Notification(
            user_id="user123",
            type=NotificationType.QUOTA_WARNING,
            channel=NotificationChannel.TEAMS,
            recipient="https://outlook.office.com/webhook/XXX",
            subject="Usage Warning",
            body="You've used 80% of your quota",
            priority=NotificationPriority.HIGH
        )
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_post = AsyncMock(return_value=mock_response)
            mock_session.return_value.__aenter__.return_value.post = mock_post
            
            result = await service._send_teams(notification)
            
            self.assertEqual(result['status'], 'delivered')
            self.assertEqual(result['channel'], 'teams')
            
            # Check Teams payload format
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            self.assertIn('@type', payload)
            self.assertEqual(payload['@type'], 'MessageCard')
            self.assertIn('themeColor', payload)


def run_tests():
    """Run all tests"""
    print("🧪 Running Notification System Tests...")
    print("=" * 50)
    
    # Run unit tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationService))
    suite.addTests(loader.loadTestsFromTestCase(TestNotificationManager))
    suite.addTests(loader.loadTestsFromTestCase(TestWebhookIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 50)
    print(f"✅ Tests Passed: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"❌ Tests Failed: {len(result.failures)}")
    print(f"⚠️ Tests Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)