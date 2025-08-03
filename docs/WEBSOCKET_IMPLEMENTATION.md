# WebSocket Implementation Guide

## Overview

This document describes the enhanced WebSocket implementation for real-time communication in the Audio/Video Transcription API. The system provides real-time updates, live collaboration, and push notifications with JWT authentication and advanced connection management.

## Architecture

### Components

1. **Enhanced WebSocket Manager** (`websocket/enhanced_server.py`)
   - JWT authentication integration
   - Connection lifecycle management
   - Event routing and handling
   - Metrics and monitoring
   - Heartbeat/keepalive mechanism

2. **Connection Manager** (`websocket/connection_manager.py`)
   - Local and Redis-backed connection tracking
   - Room-based messaging
   - User presence management
   - Connection limits and timeouts
   - Scalable across multiple servers

3. **Event System** (`websocket/events.py`)
   - Strongly-typed event definitions
   - Event serialization/deserialization
   - Custom event types support

4. **Event Handlers** (`websocket/handlers.py`)
   - Transcript updates handler
   - Notification handler
   - Collaboration handler
   - Processing status handler
   - Team updates handler
   - System events handler

## Features

### Authentication & Security
- JWT token-based authentication
- Token validation on connection
- User activity verification
- Connection limits per user
- Secure message validation

### Real-time Updates
- Live transcription progress
- Instant notification delivery
- Collaborative editing updates
- Processing status streaming
- Team activity broadcasts

### Connection Management
- Automatic reconnection support
- Heartbeat/keepalive mechanism
- Stale connection cleanup
- Graceful disconnection handling
- Connection metrics tracking

### Scalability
- Redis pub/sub for multi-server support
- Room-based message routing
- Efficient broadcast mechanisms
- Connection pooling
- Load distribution

## Connection Flow

### 1. Client Connection

```javascript
// Connect with JWT token
const ws = new WebSocket('ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  console.log('Connected to WebSocket');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

### 2. Authentication

```
Client → Server: Connect with JWT token
Server: Validate JWT token
Server: Check user active status
Server → Client: CONNECTION_ESTABLISHED event
```

### 3. Message Format

All messages follow this format:

```json
{
  "type": "event_type",
  "data": {
    // Event-specific data
  }
}
```

## Event Types

### Connection Events

#### CONNECTION_ESTABLISHED
Sent when connection is successfully established.
```json
{
  "type": "connection.established",
  "data": {
    "connection_id": "uuid",
    "user_id": 123,
    "server_time": "2024-01-01T00:00:00Z",
    "features": {
      "rooms": true,
      "notifications": true,
      "collaboration": true,
      "real_time_updates": true
    }
  }
}
```

#### PING/PONG
Keep connection alive and measure latency.
```json
// Client → Server
{"type": "ping", "data": {}}

// Server → Client
{"type": "pong", "data": {"timestamp": "2024-01-01T00:00:00Z"}}
```

### Room Management

#### JOIN_ROOM
Join a room for group messaging.
```json
{
  "type": "room.join",
  "data": {
    "room_id": "transcript:123"
  }
}
```

#### LEAVE_ROOM
Leave a room.
```json
{
  "type": "room.leave",
  "data": {
    "room_id": "transcript:123"
  }
}
```

### Transcript Events

#### TRANSCRIPT_UPDATED
Broadcast transcript changes.
```json
{
  "type": "transcript.updated",
  "data": {
    "transcript_id": 123,
    "user_id": 456,
    "changes": {
      "text": "Updated content",
      "word_count": 150,
      "last_modified": "2024-01-01T00:00:00Z"
    }
  }
}
```

### Collaboration Events

#### USER_TYPING
Show typing indicators.
```json
{
  "type": "user.typing",
  "data": {
    "transcript_id": 123,
    "user_id": 456,
    "expires_at": "2024-01-01T00:00:05Z"
  }
}
```

#### ANNOTATION_ADDED
New annotation on transcript.
```json
{
  "type": "annotation.added",
  "data": {
    "transcript_id": 123,
    "annotation_id": 789,
    "user_id": 456,
    "start_pos": 10,
    "end_pos": 20,
    "text": "Important note",
    "type": "highlight"
  }
}
```

### Processing Events

#### PROCESSING_PROGRESS
Update on processing status.
```json
{
  "type": "processing.progress",
  "data": {
    "job_id": "job_123",
    "progress": 75,
    "status": "processing",
    "message": "Extracting entities..."
  }
}
```

#### PROCESSING_COMPLETED
Processing finished.
```json
{
  "type": "processing.completed",
  "data": {
    "job_id": "job_123",
    "result": {
      "transcript_id": 456,
      "duration": 120.5,
      "word_count": 500
    }
  }
}
```

### Notification Events

#### NOTIFICATION_NEW
New notification for user.
```json
{
  "type": "notification.new",
  "data": {
    "notification_id": 123,
    "title": "Transcript Shared",
    "message": "John Doe shared a transcript with you",
    "type": "info",
    "action_url": "/transcript/456"
  }
}
```

## Usage Examples

### 1. Basic Connection

```python
import websockets
import json
import asyncio

async def connect():
    uri = f"ws://localhost:8000/api/v1/ws?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Send a message
        await websocket.send(json.dumps({
            "type": "ping",
            "data": {}
        }))
        
        # Receive messages
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data}")
```

### 2. Joining Transcript Room

```python
# Join transcript room for collaboration
await websocket.send(json.dumps({
    "type": "room.join",
    "data": {"room_id": f"transcript:{transcript_id}"}
}))

# Send typing indicator
await websocket.send(json.dumps({
    "type": "user.typing",
    "data": {"transcript_id": transcript_id}
}))

# Add annotation
await websocket.send(json.dumps({
    "type": "annotation.added",
    "data": {
        "transcript_id": transcript_id,
        "start_pos": 100,
        "end_pos": 150,
        "text": "Important section",
        "type": "highlight"
    }
}))
```

### 3. Using Event Emitter (Server-side)

```python
from api.websocket_routes_enhanced import ws_event_emitter

# Emit transcript update
await ws_event_emitter.emit_transcript_update(
    transcript_id=123,
    user_id=456,
    changes={"text": "Updated content"}
)

# Emit processing progress
await ws_event_emitter.emit_processing_progress(
    job_id="job_123",
    user_id=456,
    progress=50,
    message="Processing audio..."
)

# Send notification
await ws_event_emitter.emit_notification(
    user_id=456,
    title="Processing Complete",
    message="Your transcript is ready",
    notification_type="success"
)
```

## Configuration

### Environment Variables

```bash
# Enable enhanced WebSocket implementation
USE_ENHANCED_WEBSOCKET=true

# Redis configuration for scaling
WEBSOCKET_USE_REDIS=true
REDIS_URL=redis://localhost:6379

# Connection limits
WS_MAX_CONNECTIONS_PER_USER=5
WS_CONNECTION_TIMEOUT=300
WS_HEARTBEAT_INTERVAL=30
WS_MAX_MESSAGE_SIZE=65536
```

### Server Configuration

```python
# In websocket/enhanced_server.py
self.config = {
    'max_message_size': 65536,      # 64KB max message size
    'heartbeat_interval': 30,        # 30 second heartbeat
    'connection_timeout': 300,       # 5 minute timeout
    'max_connections_per_user': 5    # Max concurrent connections
}
```

## Testing

### Run WebSocket Tests

```bash
# Basic functionality test
python test_websocket_enhanced.py

# Load testing with multiple connections
python test_websocket_load.py

# Integration tests
pytest tests/test_websocket_integration.py
```

### Manual Testing with wscat

```bash
# Install wscat
npm install -g wscat

# Connect with token
wscat -c "ws://localhost:8000/api/v1/ws?token=YOUR_JWT_TOKEN"

# Send ping
> {"type": "ping", "data": {}}

# Join room
> {"type": "room.join", "data": {"room_id": "transcript:123"}}
```

## Monitoring & Metrics

### Available Metrics

```http
GET /api/v1/ws/metrics

Response:
{
  "total_connections": 150,
  "failed_connections": 5,
  "messages_processed": 10000,
  "errors": 12,
  "active_connections": 45,
  "active_users": 30,
  "active_rooms": 15
}
```

### User Connection Info

```http
GET /api/v1/ws/connections/{user_id}

Response:
{
  "user_id": 123,
  "connection_count": 2,
  "connection_ids": ["uuid1", "uuid2"],
  "rooms": ["transcript:456", "transcript:789"]
}
```

## Error Handling

### Connection Errors

| Code | Reason | Description |
|------|--------|-------------|
| 1008 | Policy Violation | Invalid authentication token |
| 4001 | Invalid Token | JWT token expired or invalid |
| 4008 | Connection Limit | User exceeded connection limit |
| 1011 | Internal Error | Server error during processing |

### Message Errors

Error events are sent for invalid messages:

```json
{
  "type": "error",
  "data": {
    "message": "Invalid event type: unknown.event",
    "details": {},
    "timestamp": "2024-01-01T00:00:00Z"
  }
}
```

## Best Practices

### Client Implementation

1. **Reconnection Logic**
   ```javascript
   let reconnectInterval = 1000;
   
   function connect() {
     const ws = new WebSocket(wsUrl);
     
     ws.onclose = () => {
       setTimeout(() => {
         reconnectInterval = Math.min(reconnectInterval * 2, 30000);
         connect();
       }, reconnectInterval);
     };
     
     ws.onopen = () => {
       reconnectInterval = 1000;
     };
   }
   ```

2. **Message Queue**
   - Queue messages when disconnected
   - Send queued messages on reconnection
   - Implement message acknowledgment

3. **Error Handling**
   - Handle all error types gracefully
   - Show user-friendly error messages
   - Log errors for debugging

### Server Implementation

1. **Event Handler Design**
   - Keep handlers lightweight
   - Use async/await properly
   - Handle database errors gracefully
   - Validate all input data

2. **Broadcasting**
   - Use rooms for group messages
   - Minimize broadcast scope
   - Batch updates when possible
   - Consider rate limiting

3. **Security**
   - Validate all incoming data
   - Check permissions for each action
   - Sanitize broadcast messages
   - Monitor for abuse patterns

## Troubleshooting

### Common Issues

1. **Connection Drops**
   - Check token expiration
   - Verify heartbeat is working
   - Check for network issues
   - Review connection timeout settings

2. **Messages Not Received**
   - Verify room membership
   - Check event handler registration
   - Review permission checks
   - Enable debug logging

3. **Performance Issues**
   - Monitor active connections
   - Check message sizes
   - Review broadcast patterns
   - Consider enabling Redis

### Debug Mode

Enable debug logging:

```python
# Set in environment
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.getLogger('websocket').setLevel(logging.DEBUG)
```

## Future Enhancements

- [ ] Binary message support
- [ ] Message compression
- [ ] Custom event plugins
- [ ] Rate limiting per event type
- [ ] Message history/replay
- [ ] Presence indicators
- [ ] Direct messaging between users
- [ ] File transfer support
- [ ] Voice/video signaling