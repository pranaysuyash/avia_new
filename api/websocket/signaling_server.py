"""
WebRTC Signaling Server
Handles signaling for peer-to-peer connections
"""

import asyncio
import json
import logging
from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class User:
    """User in a collaboration room"""
    user_id: str
    user_name: str
    websocket: WebSocket
    joined_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Room:
    """Collaboration room"""
    room_id: str
    users: Dict[str, User] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def add_user(self, user: User):
        """Add user to room"""
        self.users[user.user_id] = user
    
    def remove_user(self, user_id: str):
        """Remove user from room"""
        self.users.pop(user_id, None)
    
    def get_other_users(self, user_id: str) -> list[User]:
        """Get all users except the specified one"""
        return [u for uid, u in self.users.items() if uid != user_id]


class SignalingServer:
    """WebRTC signaling server for managing rooms and connections"""
    
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.user_to_room: Dict[str, str] = {}
    
    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection"""
        await websocket.accept()
        user_id = None
        
        try:
            while True:
                data = await websocket.receive_json()
                message_type = data.get("type")
                
                if message_type == "join":
                    user_id = await self._handle_join(websocket, data)
                
                elif message_type == "leave":
                    await self._handle_leave(data)
                
                elif message_type == "offer":
                    await self._handle_offer(data)
                
                elif message_type == "answer":
                    await self._handle_answer(data)
                
                elif message_type == "ice-candidate":
                    await self._handle_ice_candidate(data)
                
                else:
                    logger.warning(f"Unknown message type: {message_type}")
        
        except WebSocketDisconnect:
            if user_id:
                await self._cleanup_user(user_id)
        
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            if user_id:
                await self._cleanup_user(user_id)
    
    async def _handle_join(self, websocket: WebSocket, data: dict) -> str:
        """Handle user joining a room"""
        room_id = data.get("roomId")
        user_id = data.get("userId")
        user_name = data.get("userName", "Anonymous")
        
        if not room_id or not user_id:
            await websocket.send_json({
                "type": "error",
                "message": "Missing roomId or userId"
            })
            return ""
        
        # Create room if it doesn't exist
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id=room_id)
        
        room = self.rooms[room_id]
        user = User(user_id=user_id, user_name=user_name, websocket=websocket)
        
        # Get existing users before adding new one
        existing_users = list(room.users.values())
        
        # Add user to room
        room.add_user(user)
        self.user_to_room[user_id] = room_id
        
        # Send existing users to new user
        await websocket.send_json({
            "type": "room-users",
            "users": [
                {"userId": u.user_id, "userName": u.user_name}
                for u in existing_users
            ]
        })
        
        # Notify existing users about new user
        for existing_user in existing_users:
            try:
                await existing_user.websocket.send_json({
                    "type": "user-joined",
                    "userId": user_id,
                    "userName": user_name
                })
            except Exception as e:
                logger.error(f"Failed to notify user {existing_user.user_id}: {e}")
        
        logger.info(f"User {user_id} joined room {room_id}")
        return user_id
    
    async def _handle_leave(self, data: dict):
        """Handle user leaving a room"""
        user_id = data.get("userId")
        if user_id:
            await self._cleanup_user(user_id)
    
    async def _handle_offer(self, data: dict):
        """Forward WebRTC offer to target user"""
        await self._forward_to_user(data["to"], {
            "type": "offer",
            "from": data["from"],
            "offer": data["offer"],
            "userName": data.get("userName")
        })
    
    async def _handle_answer(self, data: dict):
        """Forward WebRTC answer to target user"""
        await self._forward_to_user(data["to"], {
            "type": "answer",
            "from": data["from"],
            "answer": data["answer"]
        })
    
    async def _handle_ice_candidate(self, data: dict):
        """Forward ICE candidate to target user"""
        await self._forward_to_user(data["to"], {
            "type": "ice-candidate",
            "from": data["from"],
            "candidate": data["candidate"]
        })
    
    async def _forward_to_user(self, target_user_id: str, message: dict):
        """Forward message to specific user"""
        room_id = self.user_to_room.get(target_user_id)
        if not room_id:
            return
        
        room = self.rooms.get(room_id)
        if not room:
            return
        
        target_user = room.users.get(target_user_id)
        if target_user:
            try:
                await target_user.websocket.send_json(message)
            except Exception as e:
                logger.error(f"Failed to forward message to {target_user_id}: {e}")
    
    async def _cleanup_user(self, user_id: str):
        """Clean up user when they disconnect"""
        room_id = self.user_to_room.get(user_id)
        if not room_id:
            return
        
        room = self.rooms.get(room_id)
        if not room:
            return
        
        # Remove user from room
        room.remove_user(user_id)
        del self.user_to_room[user_id]
        
        # Notify other users
        for other_user in room.users.values():
            try:
                await other_user.websocket.send_json({
                    "type": "user-left",
                    "userId": user_id
                })
            except Exception as e:
                logger.error(f"Failed to notify user {other_user.user_id}: {e}")
        
        # Clean up empty rooms
        if not room.users:
            del self.rooms[room_id]
            logger.info(f"Room {room_id} deleted (empty)")
        
        logger.info(f"User {user_id} left room {room_id}")
    
    def get_room_info(self, room_id: str) -> dict:
        """Get information about a room"""
        room = self.rooms.get(room_id)
        if not room:
            return {"exists": False}
        
        return {
            "exists": True,
            "room_id": room_id,
            "user_count": len(room.users),
            "users": [
                {
                    "user_id": u.user_id,
                    "user_name": u.user_name,
                    "joined_at": u.joined_at.isoformat()
                }
                for u in room.users.values()
            ],
            "created_at": room.created_at.isoformat()
        }
    
    def get_all_rooms(self) -> list[dict]:
        """Get information about all active rooms"""
        return [
            self.get_room_info(room_id)
            for room_id in self.rooms.keys()
        ]


# Global signaling server instance
signaling_server = SignalingServer()