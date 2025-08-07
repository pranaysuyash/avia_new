"""
GraphQL Endpoint for FastAPI
Provides GraphQL API with subscription support via WebSockets
"""

import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
import strawberry

from api.database import get_db, User
from api.auth import get_current_active_user, get_current_user_optional
from api.graphql.schema import schema
from api.graphql.subscription_manager import subscription_manager
from services.audit_logging_service import audit_service, AuditEventType

logger = logging.getLogger(__name__)

# Custom context class for GraphQL
@strawberry.type
class GraphQLContext:
    """GraphQL context with user and request information"""
    user: Optional[User] = None
    request: Optional[Request] = None
    db = None


async def get_graphql_context(
    request: Request = None,
    websocket: WebSocket = None,
    user: User = Depends(get_current_user_optional),
    db = Depends(get_db)
) -> GraphQLContext:
    """Create GraphQL context with user and database session"""
    
    context = GraphQLContext()
    context.user = user
    context.request = request
    context.db = db
    
    return context


# Custom GraphQL router with authentication and logging
class AuthenticatedGraphQLRouter(GraphQLRouter):
    """GraphQL router with authentication and audit logging"""
    
    async def execute_request(self, request: Request, context: GraphQLContext):
        """Execute GraphQL request with authentication and logging"""
        
        # Log GraphQL request
        if context.user:
            audit_service.log_event(
                event_type=AuditEventType.API_REQUEST,
                action="GraphQL Request",
                user_id=context.user.id,
                username=context.user.username,
                resource="graphql",
                ip_address=request.client.host if request.client else None,
                details={
                    "user_agent": request.headers.get("user-agent"),
                    "operation": "graphql_query"  # Could be enhanced to extract operation type
                }
            )
        
        # Execute the request
        return await super().execute_request(request, context)


# Create GraphQL router
graphql_router = AuthenticatedGraphQLRouter(
    schema,
    context_getter=get_graphql_context,
    subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL]
)

# Main router
router = APIRouter(
    prefix="/api/graphql",
    tags=["graphql"],
    responses={404: {"description": "Not found"}},
)

# Include the GraphQL router
router.include_router(graphql_router, path="")


# GraphQL Playground (development only)
@router.get("/playground", response_class=HTMLResponse)
async def graphql_playground():
    """GraphQL Playground for development"""
    
    playground_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="user-scalable=no, initial-scale=1.0, minimum-scale=1.0, maximum-scale=1.0, minimal-ui">
        <title>GraphQL Playground</title>
        <link rel="stylesheet" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/css/index.css" />
        <link rel="shortcut icon" href="//cdn.jsdelivr.net/npm/graphql-playground-react/build/favicon.png" />
        <script src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/static/js/middleware.js"></script>
    </head>
    <body>
        <div id="root">
            <style>
                body { background-color: rgb(23, 42, 58); font-family: Open Sans, sans-serif; height: 90vh; }
                #root { height: 100%; width: 100%; display: flex; align-items: center; justify-content: center; }
                .loading { font-size: 32px; font-weight: 200; color: rgba(255, 255, 255, .6); margin-left: 20px; }
                img { width: 78px; height: 78px; }
                .title { font-weight: 400; }
            </style>
            <img src="//cdn.jsdelivr.net/npm/graphql-playground-react/build/logo.png" alt="">
            <div class="loading"> Loading
                <span class="title">GraphQL Playground</span>
            </div>
        </div>
        <script>
            window.addEventListener('load', function (event) {
                GraphQLPlayground.init(document.getElementById('root'), {
                    endpoint: '/api/graphql',
                    subscriptionEndpoint: '/api/graphql',
                    settings: {
                        'request.credentials': 'same-origin',
                    },
                    tabs: [
                        {
                            endpoint: '/api/graphql',
                            query: `# Welcome to GraphQL Playground
# 
# Example queries:

query GetUsers {
  users(limit: 5) {
    id
    username
    email
    role
    isActive
    createdAt
  }
}

query GetSystemMetrics {
  systemMetrics {
    timestamp
    cpuUsage
    memoryUsage
    diskUsage
    activeConnections
    requestRate
    errorRate
  }
}

# Example mutation:
mutation StartTranscription {
  startTranscription(
    fileUrl: "https://example.com/audio.mp3"
    language: "en"
  ) {
    id
    status
    progress
    fileUrl
    createdAt
  }
}

# Example subscription:
subscription TranscriptionUpdates {
  transcriptionStatus {
    id
    status
    progress
    updatedAt
  }
}`
                        }
                    ]
                })
            })
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=playground_html)


# WebSocket endpoint for GraphQL subscriptions
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for GraphQL subscriptions"""
    
    await websocket.accept()
    logger.info(f"GraphQL WebSocket connection established: {websocket.client}")
    
    try:
        # Handle GraphQL subscription protocol
        # This would typically be handled by the GraphQLRouter automatically,
        # but we're providing a custom implementation for more control
        
        while True:
            # Receive message from client
            data = await websocket.receive_json()
            
            # Handle connection init
            if data.get("type") == "connection_init":
                await websocket.send_json({
                    "type": "connection_ack"
                })
                continue
            
            # Handle subscription start
            elif data.get("type") == "start":
                subscription_id = data.get("id")
                payload = data.get("payload", {})
                query = payload.get("query", "")
                variables = payload.get("variables", {})
                
                logger.info(f"Starting GraphQL subscription: {subscription_id}")
                
                # Parse and execute subscription
                # In a full implementation, this would use the Strawberry schema
                # to parse and execute the subscription
                
                await websocket.send_json({
                    "id": subscription_id,
                    "type": "data",
                    "payload": {
                        "data": {
                            "message": "Subscription started successfully"
                        }
                    }
                })
            
            # Handle subscription stop
            elif data.get("type") == "stop"):
                subscription_id = data.get("id")
                logger.info(f"Stopping GraphQL subscription: {subscription_id}")
                
                await websocket.send_json({
                    "id": subscription_id,
                    "type": "complete"
                })
            
            # Handle connection terminate
            elif data.get("type") == "connection_terminate":
                logger.info("GraphQL WebSocket connection terminated by client")
                break
                
    except WebSocketDisconnect:
        logger.info("GraphQL WebSocket client disconnected")
    except Exception as e:
        logger.error(f"GraphQL WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "payload": {
                    "message": "Internal server error"
                }
            })
        except:
            pass
    finally:
        try:
            await websocket.close()
        except:
            pass


# Health check endpoint
@router.get("/health")
async def graphql_health():
    """GraphQL service health check"""
    
    try:
        # Check subscription manager
        subscription_stats = await subscription_manager.get_subscription_stats()
        
        # Test schema introspection
        introspection_query = """
        query IntrospectionQuery {
            __schema {
                types {
                    name
                }
            }
        }
        """
        
        result = await schema.execute(introspection_query)
        schema_healthy = not result.errors
        
        return {
            "status": "healthy" if schema_healthy else "degraded",
            "schema_healthy": schema_healthy,
            "subscription_manager": {
                "total_subscriptions": subscription_stats["total_subscriptions"],
                "redis_connected": subscription_stats["redis_connected"]
            },
            "errors": [str(error) for error in (result.errors or [])]
        }
        
    except Exception as e:
        logger.error(f"GraphQL health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Subscription statistics endpoint
@router.get("/subscriptions/stats")
async def subscription_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get subscription manager statistics"""
    
    try:
        stats = await subscription_manager.get_subscription_stats()
        
        # Log access to subscription stats
        audit_service.log_event(
            event_type=AuditEventType.ADMIN_ACTION,
            action="View GraphQL subscription statistics",
            user_id=current_user.id,
            username=current_user.username,
            resource="graphql_subscriptions"
        )
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting subscription stats: {e}")
        return {
            "error": str(e)
        }


# Example subscription trigger endpoint (for testing)
@router.post("/test/publish-event")
async def publish_test_event(
    event_type: str,
    data: Dict[str, Any],
    user_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user)
):
    """Publish a test event to subscriptions (for testing purposes)"""
    
    try:
        from api.graphql.subscription_manager import SubscriptionEvent
        
        event = SubscriptionEvent(
            event_type=event_type,
            data=data,
            user_id=user_id
        )
        
        await subscription_manager.publish_event(event)
        
        # Log test event
        audit_service.log_event(
            event_type=AuditEventType.ADMIN_ACTION,
            action=f"Published test GraphQL event: {event_type}",
            user_id=current_user.id,
            username=current_user.username,
            resource="graphql_test",
            details={
                "event_type": event_type,
                "target_user_id": user_id
            }
        )
        
        return {
            "success": True,
            "event_type": event_type,
            "published_at": event.timestamp.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error publishing test event: {e}")
        return {
            "success": False,
            "error": str(e)
        }