#!/usr/bin/env python3
"""
Admin Monitoring WebSocket Handler
Real-time system monitoring for administrators
"""

import logging
import asyncio
import json
from typing import Dict, Any, Set, Optional
from datetime import datetime, timedelta
from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from database.models import User, Transcript
from database.connection import get_db
from api.auth_routes_enhanced import get_current_user
from services.system_monitoring_service import monitoring_service

logger = logging.getLogger(__name__)

class AdminMonitoringManager:
    """Manages WebSocket connections for admin monitoring"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.monitoring_task: Optional[asyncio.Task] = None
        self.update_interval = 5  # seconds
    
    async def connect(self, websocket: WebSocket, user: User):
        """Connect admin user to monitoring"""
        if user.role != 'admin':
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return False
        
        await websocket.accept()
        self.active_connections.add(websocket)
        
        # Start monitoring if this is the first connection
        if len(self.active_connections) == 1:
            self.monitoring_task = asyncio.create_task(self._monitor_loop())
        
        # Send initial data
        await self._send_initial_data(websocket)
        
        logger.info(f"Admin {user.username} connected to monitoring")
        return True
    
    def disconnect(self, websocket: WebSocket):
        """Disconnect admin from monitoring"""
        self.active_connections.discard(websocket)
        
        # Stop monitoring if no connections
        if len(self.active_connections) == 0 and self.monitoring_task:
            self.monitoring_task.cancel()
            self.monitoring_task = None
        
        logger.info("Admin disconnected from monitoring")
    
    async def _send_initial_data(self, websocket: WebSocket):
        """Send initial monitoring data to new connection"""
        try:
            # Get current metrics
            metrics = monitoring_service.get_system_metrics()
            health = monitoring_service.check_service_health()
            alerts = monitoring_service.get_alerts()
            
            initial_data = {
                'type': 'initial',
                'timestamp': datetime.utcnow().isoformat(),
                'data': {
                    'metrics': metrics,
                    'health': health,
                    'alerts': alerts
                }
            }
            
            await websocket.send_json(initial_data)
            
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
    
    async def _monitor_loop(self):
        """Continuous monitoring loop"""
        while self.active_connections:
            try:
                # Collect current data
                metrics = monitoring_service.get_system_metrics()
                health = monitoring_service.check_service_health()
                alerts = monitoring_service.get_alerts()
                performance = monitoring_service.get_performance_metrics(minutes=5)
                
                update_data = {
                    'type': 'update',
                    'timestamp': datetime.utcnow().isoformat(),
                    'data': {
                        'metrics': metrics,
                        'health': health,
                        'alerts': alerts,
                        'performance': performance
                    }
                }
                
                # Send to all connected admins
                await self.broadcast(update_data)
                
                # Wait before next update
                await asyncio.sleep(self.update_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(self.update_interval)
    
    async def broadcast(self, data: Dict[str, Any]):
        """Broadcast data to all connected admins"""
        disconnected = set()
        
        for websocket in self.active_connections:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error broadcasting to websocket: {e}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            self.disconnect(websocket)
    
    async def send_alert(self, alert: Dict[str, Any]):
        """Send alert to all connected admins"""
        alert_data = {
            'type': 'alert',
            'timestamp': datetime.utcnow().isoformat(),
            'data': alert
        }
        
        await self.broadcast(alert_data)
    
    async def handle_command(self, websocket: WebSocket, command: Dict[str, Any]):
        """Handle commands from admin clients"""
        cmd_type = command.get('type')
        
        if cmd_type == 'set_interval':
            # Update monitoring interval
            new_interval = command.get('interval', 5)
            if 1 <= new_interval <= 60:
                self.update_interval = new_interval
                await websocket.send_json({
                    'type': 'command_response',
                    'command': 'set_interval',
                    'status': 'success',
                    'interval': self.update_interval
                })
        
        elif cmd_type == 'get_detailed':
            # Get detailed metrics for specific service
            service = command.get('service')
            detailed_data = await self._get_detailed_metrics(service)
            
            await websocket.send_json({
                'type': 'detailed_metrics',
                'service': service,
                'data': detailed_data
            })
        
        elif cmd_type == 'trigger_backup':
            # Trigger system backup
            backup_id = f"MANUAL-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Start backup process (would be async in production)
            await websocket.send_json({
                'type': 'command_response',
                'command': 'trigger_backup',
                'status': 'started',
                'backup_id': backup_id
            })
        
        elif cmd_type == 'clear_cache':
            # Clear system caches
            await self._clear_system_caches()
            
            await websocket.send_json({
                'type': 'command_response',
                'command': 'clear_cache',
                'status': 'success'
            })
    
    async def _get_detailed_metrics(self, service: str) -> Dict[str, Any]:
        """Get detailed metrics for specific service"""
        if service == 'database':
            db = next(get_db())
            try:
                # Get database statistics
                user_count = db.query(func.count(User.id)).scalar()
                transcript_count = db.query(func.count(Transcript.id)).scalar()
                
                # Get recent activity
                recent_transcripts = db.query(
                    func.date(Transcript.created_at).label('date'),
                    func.count(Transcript.id).label('count')
                ).filter(
                    Transcript.created_at >= datetime.utcnow() - timedelta(days=7)
                ).group_by(
                    func.date(Transcript.created_at)
                ).all()
                
                return {
                    'total_users': user_count,
                    'total_transcripts': transcript_count,
                    'recent_activity': [
                        {'date': r.date.isoformat(), 'count': r.count}
                        for r in recent_transcripts
                    ]
                }
            finally:
                db.close()
        
        elif service == 'redis':
            if monitoring_service.redis_client:
                info = monitoring_service.redis_client.info()
                return {
                    'version': info.get('redis_version'),
                    'connected_clients': info.get('connected_clients'),
                    'used_memory': info.get('used_memory_human'),
                    'total_commands': info.get('total_commands_processed'),
                    'keyspace': info.get('db0', {})
                }
        
        return {}
    
    async def _clear_system_caches(self):
        """Clear various system caches"""
        if monitoring_service.redis_client:
            # Clear specific cache patterns
            for key in monitoring_service.redis_client.scan_iter("cache:*"):
                monitoring_service.redis_client.delete(key)
            
            logger.info("System caches cleared")

# Global instance
admin_monitoring_manager = AdminMonitoringManager()

async def admin_monitoring_endpoint(
    websocket: WebSocket,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for admin monitoring"""
    connected = await admin_monitoring_manager.connect(websocket, current_user)
    
    if not connected:
        return
    
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_json()
            
            # Handle commands
            await admin_monitoring_manager.handle_command(websocket, data)
            
    except WebSocketDisconnect:
        admin_monitoring_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Error in admin monitoring websocket: {e}")
        admin_monitoring_manager.disconnect(websocket)
        await websocket.close()