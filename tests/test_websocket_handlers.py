"""
Unit tests for WebSocket handlers
"""

import pytest
import os
import sys
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from websocket.handlers import (
    WebSocketHandlers,
    TranscriptionHandler,
    AnalyticsHandler,
    CollaborationHandler,
    NotificationHandler
)


class TestWebSocketHandlers:
    """Test base WebSocket handlers class"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def handlers(self, mock_db):
        """Create WebSocketHandlers instance"""
        return WebSocketHandlers(mock_db)
    
    @pytest.mark.asyncio
    async def test_handle_message_valid(self, handlers):
        """Test handling valid message"""
        # Mock a handler
        mock_handler = AsyncMock(return_value={'status': 'success'})
        handlers.handlers['test_event'] = mock_handler
        
        message = {
            'event': 'test_event',
            'data': {'key': 'value'}
        }
        
        response = await handlers.handle_message(message, user_id=123)
        
        assert response['event'] == 'test_event_response'
        assert response['data']['status'] == 'success'
        assert 'timestamp' in response
        
        # Verify handler was called
        mock_handler.assert_called_once_with({'key': 'value'}, 123)
    
    @pytest.mark.asyncio
    async def test_handle_message_invalid_format(self, handlers):
        """Test handling message with invalid format"""
        # Message without event
        message = {'data': {'key': 'value'}}
        
        response = await handlers.handle_message(message, user_id=123)
        
        assert response['event'] == 'error'
        assert response['data']['error'] == 'Invalid message format'
    
    @pytest.mark.asyncio
    async def test_handle_message_unknown_event(self, handlers):
        """Test handling unknown event"""
        message = {
            'event': 'unknown_event',
            'data': {}
        }
        
        response = await handlers.handle_message(message, user_id=123)
        
        assert response['event'] == 'error'
        assert 'Unknown event' in response['data']['error']
    
    @pytest.mark.asyncio
    async def test_handle_message_handler_error(self, handlers):
        """Test handling when handler raises error"""
        # Mock a handler that raises exception
        mock_handler = AsyncMock(side_effect=Exception("Handler error"))
        handlers.handlers['test_event'] = mock_handler
        
        message = {
            'event': 'test_event',
            'data': {}
        }
        
        response = await handlers.handle_message(message, user_id=123)
        
        assert response['event'] == 'test_event_error'
        assert 'error' in response['data']
    
    def test_get_available_events(self, handlers):
        """Test getting list of available events"""
        # Add some handlers
        handlers.handlers['event1'] = Mock()
        handlers.handlers['event2'] = Mock()
        
        events = handlers.get_available_events()
        
        assert 'event1' in events
        assert 'event2' in events
        assert len(events) >= 2  # May have default handlers


class TestTranscriptionHandler:
    """Test transcription WebSocket handler"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def handler(self, mock_db):
        """Create TranscriptionHandler instance"""
        return TranscriptionHandler(mock_db)
    
    @pytest.mark.asyncio
    async def test_handle_start_transcription(self, handler, mock_db):
        """Test starting transcription"""
        # Mock database queries
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.status = 'pending'
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {'transcript_id': 456}
        response = await handler.handle_start_transcription(data, user_id=123)
        
        assert response['status'] == 'started'
        assert response['transcript_id'] == 456
        
        # Verify status update
        assert mock_transcript.status == 'processing'
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_start_transcription_not_found(self, handler, mock_db):
        """Test starting transcription with invalid ID"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query
        
        data = {'transcript_id': 999}
        
        with pytest.raises(ValueError, match="Transcript not found"):
            await handler.handle_start_transcription(data, user_id=123)
    
    @pytest.mark.asyncio
    async def test_handle_update_progress(self, handler, mock_db):
        """Test updating transcription progress"""
        # Mock transcript
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.user_id = 123
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {
            'transcript_id': 456,
            'progress': 75,
            'current_step': 'Processing audio'
        }
        
        response = await handler.handle_update_progress(data, user_id=123)
        
        assert response['status'] == 'updated'
        assert response['progress'] == 75
        
        # Verify updates
        assert mock_transcript.progress == 75
        assert mock_transcript.current_step == 'Processing audio'
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_complete_transcription(self, handler, mock_db):
        """Test completing transcription"""
        # Mock transcript
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.user_id = 123
        mock_transcript.status = 'processing'
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {
            'transcript_id': 456,
            'text': 'Transcribed text here',
            'duration': 120.5,
            'word_count': 250
        }
        
        response = await handler.handle_complete_transcription(data, user_id=123)
        
        assert response['status'] == 'completed'
        assert response['transcript_id'] == 456
        
        # Verify updates
        assert mock_transcript.status == 'completed'
        assert mock_transcript.text == 'Transcribed text here'
        assert mock_transcript.duration == 120.5
        assert mock_transcript.word_count == 250
        assert mock_transcript.completed_at is not None
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_error_transcription(self, handler, mock_db):
        """Test handling transcription error"""
        # Mock transcript
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.user_id = 123
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {
            'transcript_id': 456,
            'error': 'Audio format not supported'
        }
        
        response = await handler.handle_error_transcription(data, user_id=123)
        
        assert response['status'] == 'error'
        assert response['error'] == 'Audio format not supported'
        
        # Verify updates
        assert mock_transcript.status == 'error'
        assert mock_transcript.error_message == 'Audio format not supported'
        mock_db.commit.assert_called_once()


class TestAnalyticsHandler:
    """Test analytics WebSocket handler"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def handler(self, mock_db):
        """Create AnalyticsHandler instance"""
        return AnalyticsHandler(mock_db)
    
    @pytest.mark.asyncio
    async def test_handle_get_stats(self, handler, mock_db):
        """Test getting user statistics"""
        # Mock query results
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 50  # Total transcripts
        
        # Mock aggregate results
        mock_aggregate = Mock()
        mock_aggregate.scalar.return_value = 3600  # Total duration
        mock_query.with_entities.return_value = mock_aggregate
        
        mock_db.query.return_value = mock_query
        
        data = {'period': 'month'}
        response = await handler.handle_get_stats(data, user_id=123)
        
        assert response['total_transcripts'] == 50
        assert response['total_duration'] == 3600
        assert response['period'] == 'month'
    
    @pytest.mark.asyncio
    async def test_handle_get_usage_trend(self, handler, mock_db):
        """Test getting usage trend data"""
        # Mock query results
        mock_results = [
            Mock(date='2024-01-01', count=5),
            Mock(date='2024-01-02', count=8),
            Mock(date='2024-01-03', count=3)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        
        data = {'days': 7}
        response = await handler.handle_get_usage_trend(data, user_id=123)
        
        assert 'trend' in response
        assert len(response['trend']) == 3
        assert response['trend'][0]['date'] == '2024-01-01'
        assert response['trend'][0]['count'] == 5
    
    @pytest.mark.asyncio
    async def test_handle_get_top_languages(self, handler, mock_db):
        """Test getting top languages"""
        # Mock query results
        mock_results = [
            Mock(language='en', count=30),
            Mock(language='es', count=15),
            Mock(language='fr', count=5)
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.group_by.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_results
        mock_db.query.return_value = mock_query
        
        data = {'limit': 5}
        response = await handler.handle_get_top_languages(data, user_id=123)
        
        assert 'languages' in response
        assert len(response['languages']) == 3
        assert response['languages'][0]['language'] == 'en'
        assert response['languages'][0]['count'] == 30


class TestCollaborationHandler:
    """Test collaboration WebSocket handler"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def handler(self, mock_db):
        """Create CollaborationHandler instance"""
        return CollaborationHandler(mock_db)
    
    @pytest.mark.asyncio
    async def test_handle_join_room(self, handler, mock_db):
        """Test joining collaboration room"""
        # Mock transcript with sharing enabled
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.sharing_enabled = True
        mock_transcript.owner_id = 100
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {'transcript_id': 456}
        response = await handler.handle_join_room(data, user_id=123)
        
        assert response['status'] == 'joined'
        assert response['room_id'] == 'transcript_456'
        assert response['role'] == 'viewer'
    
    @pytest.mark.asyncio
    async def test_handle_join_room_owner(self, handler, mock_db):
        """Test room owner joining"""
        # Mock transcript owned by user
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.sharing_enabled = True
        mock_transcript.owner_id = 123  # Same as user
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {'transcript_id': 456}
        response = await handler.handle_join_room(data, user_id=123)
        
        assert response['status'] == 'joined'
        assert response['role'] == 'owner'
    
    @pytest.mark.asyncio
    async def test_handle_join_room_not_shared(self, handler, mock_db):
        """Test joining room that's not shared"""
        # Mock transcript without sharing
        mock_transcript = Mock()
        mock_transcript.id = 456
        mock_transcript.sharing_enabled = False
        mock_transcript.owner_id = 100
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_transcript
        mock_db.query.return_value = mock_query
        
        data = {'transcript_id': 456}
        
        with pytest.raises(ValueError, match="not shared"):
            await handler.handle_join_room(data, user_id=123)
    
    @pytest.mark.asyncio
    async def test_handle_send_comment(self, handler, mock_db):
        """Test sending comment"""
        # Mock transcript and user
        mock_transcript = Mock()
        mock_transcript.id = 456
        
        mock_user = Mock()
        mock_user.username = "testuser"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.side_effect = [mock_transcript, mock_user]
        mock_db.query.return_value = mock_query
        
        data = {
            'transcript_id': 456,
            'comment': 'Great transcription!',
            'timestamp': 45.5
        }
        
        response = await handler.handle_send_comment(data, user_id=123)
        
        assert response['status'] == 'sent'
        assert response['comment']['text'] == 'Great transcription!'
        assert response['comment']['username'] == 'testuser'
        assert response['comment']['timestamp'] == 45.5
        
        # Verify comment was saved
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_update_cursor(self, handler, mock_db):
        """Test updating cursor position"""
        # Mock user
        mock_user = Mock()
        mock_user.username = "testuser"
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_user
        mock_db.query.return_value = mock_query
        
        data = {
            'transcript_id': 456,
            'position': 120,
            'selection': {'start': 100, 'end': 150}
        }
        
        response = await handler.handle_update_cursor(data, user_id=123)
        
        assert response['username'] == 'testuser'
        assert response['position'] == 120
        assert response['selection']['start'] == 100
        assert response['selection']['end'] == 150


class TestNotificationHandler:
    """Test notification WebSocket handler"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def handler(self, mock_db):
        """Create NotificationHandler instance"""
        return NotificationHandler(mock_db)
    
    @pytest.mark.asyncio
    async def test_handle_mark_read(self, handler, mock_db):
        """Test marking notification as read"""
        # Mock notification
        mock_notification = Mock()
        mock_notification.id = 789
        mock_notification.user_id = 123
        mock_notification.is_read = False
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_notification
        mock_db.query.return_value = mock_query
        
        data = {'notification_id': 789}
        response = await handler.handle_mark_read(data, user_id=123)
        
        assert response['status'] == 'marked_read'
        assert response['notification_id'] == 789
        
        # Verify update
        assert mock_notification.is_read == True
        assert mock_notification.read_at is not None
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_mark_all_read(self, handler, mock_db):
        """Test marking all notifications as read"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.update.return_value = 5  # Updated count
        mock_db.query.return_value = mock_query
        
        data = {}
        response = await handler.handle_mark_all_read(data, user_id=123)
        
        assert response['status'] == 'all_marked_read'
        assert response['count'] == 5
        
        # Verify update was called with correct values
        mock_query.update.assert_called_once()
        update_args = mock_query.update.call_args[0][0]
        assert 'is_read' in update_args
        assert update_args['is_read'] == True
        
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_get_unread_count(self, handler, mock_db):
        """Test getting unread notification count"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.count.return_value = 7
        mock_db.query.return_value = mock_query
        
        data = {}
        response = await handler.handle_get_unread_count(data, user_id=123)
        
        assert response['unread_count'] == 7
    
    @pytest.mark.asyncio
    async def test_handle_get_recent(self, handler, mock_db):
        """Test getting recent notifications"""
        # Mock notifications
        mock_notifications = [
            Mock(
                id=1,
                type='transcription_complete',
                title='Transcription Complete',
                message='Your transcription is ready',
                is_read=False,
                created_at=datetime.utcnow()
            ),
            Mock(
                id=2,
                type='share_received',
                title='New Share',
                message='Someone shared a transcript with you',
                is_read=True,
                created_at=datetime.utcnow()
            )
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_notifications
        mock_db.query.return_value = mock_query
        
        data = {'limit': 10}
        response = await handler.handle_get_recent(data, user_id=123)
        
        assert 'notifications' in response
        assert len(response['notifications']) == 2
        assert response['notifications'][0]['id'] == 1
        assert response['notifications'][0]['type'] == 'transcription_complete'
        assert response['notifications'][0]['is_read'] == False


class TestHandlerIntegration:
    """Test handler integration and error scenarios"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock()
    
    @pytest.fixture
    def handlers(self, mock_db):
        """Create handlers with all sub-handlers"""
        handlers = WebSocketHandlers(mock_db)
        handlers.transcription_handler = TranscriptionHandler(mock_db)
        handlers.analytics_handler = AnalyticsHandler(mock_db)
        handlers.collaboration_handler = CollaborationHandler(mock_db)
        handlers.notification_handler = NotificationHandler(mock_db)
        
        # Register handlers
        handlers.register_handlers()
        return handlers
    
    @pytest.mark.asyncio
    async def test_handler_registration(self, handlers):
        """Test that all handlers are registered"""
        events = handlers.get_available_events()
        
        # Check transcription events
        assert 'transcription.start' in events
        assert 'transcription.progress' in events
        assert 'transcription.complete' in events
        assert 'transcription.error' in events
        
        # Check analytics events
        assert 'analytics.get_stats' in events
        assert 'analytics.get_trend' in events
        
        # Check collaboration events
        assert 'collaboration.join' in events
        assert 'collaboration.comment' in events
        
        # Check notification events
        assert 'notification.mark_read' in events
        assert 'notification.get_unread' in events
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, handlers, mock_db):
        """Test handling database errors"""
        # Mock database error
        mock_db.query.side_effect = Exception("Database connection lost")
        
        message = {
            'event': 'analytics.get_stats',
            'data': {'period': 'week'}
        }
        
        response = await handlers.handle_message(message, user_id=123)
        
        assert response['event'] == 'analytics.get_stats_error'
        assert 'error' in response['data']
        assert 'Database connection lost' in response['data']['error']
    
    @pytest.mark.asyncio
    async def test_missing_required_field(self, handlers):
        """Test handling missing required fields"""
        # Message missing transcript_id
        message = {
            'event': 'transcription.start',
            'data': {}
        }
        
        response = await handlers.handle_message(message, user_id=123)
        
        assert response['event'] == 'transcription.start_error'
        assert 'error' in response['data']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])