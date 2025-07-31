"""
WebSocket server for real-time features
"""

from .events import EventType, Event, EventHandler

# Conditionally import modules that depend on external libraries
try:
    from .server import WebSocketManager, ConnectionManager
    from .handlers import (
        TranscriptEventHandler,
        NotificationEventHandler,
        CollaborationEventHandler,
        ProcessingEventHandler
    )
    _server_available = True
except ImportError:
    _server_available = False

if _server_available:
    __all__ = [
        'WebSocketManager',
        'ConnectionManager',
        'EventType',
        'Event',
        'EventHandler', 
        'TranscriptEventHandler',
        'NotificationEventHandler',
        'CollaborationEventHandler',
        'ProcessingEventHandler'
    ]
else:
    __all__ = [
        'EventType',
        'Event',
        'EventHandler'
    ]