"""
Tests for Real-time Collaboration with Operational Transforms
"""

import pytest
import json
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

from services.operational_transforms_service import (
    ot_service,
    Operation,
    OperationType,
    DocumentState,
    CollaborationSession
)
from api.database import User, Transcript, Team


class TestOperationalTransformsService:
    """Test operational transforms service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_document(self):
        """Create sample document"""
        return DocumentState(
            document_id="doc_123",
            content="Hello World",
            version=1,
            checksum="abc123"
        )
    
    @pytest.fixture
    def sample_operations(self):
        """Create sample operations"""
        return [
            Operation(
                id="op_1",
                type=OperationType.INSERT,
                position=5,
                content=" Beautiful",
                user_id=1,
                timestamp=datetime.utcnow(),
                version=1
            ),
            Operation(
                id="op_2",
                type=OperationType.DELETE,
                position=0,
                length=5,
                user_id=2,
                timestamp=datetime.utcnow(),
                version=1
            )
        ]
    
    def test_create_session(self, mock_db):
        """Test creating a collaboration session"""
        session_id = ot_service.create_session(
            db=mock_db,
            document_id="doc_123",
            user_id=1
        )
        
        assert session_id is not None
        assert session_id in ot_service.sessions
        session = ot_service.sessions[session_id]
        assert session.document_id == "doc_123"
        assert 1 in session.participants
    
    def test_join_session(self, mock_db):
        """Test joining an existing session"""
        # Create session
        session_id = ot_service.create_session(
            db=mock_db,
            document_id="doc_123",
            user_id=1
        )
        
        # Join session
        success = ot_service.join_session(
            db=mock_db,
            session_id=session_id,
            user_id=2
        )
        
        assert success is True
        assert 2 in ot_service.sessions[session_id].participants
    
    def test_leave_session(self, mock_db):
        """Test leaving a session"""
        # Create and join session
        session_id = ot_service.create_session(
            db=mock_db,
            document_id="doc_123",
            user_id=1
        )
        ot_service.join_session(db=mock_db, session_id=session_id, user_id=2)
        
        # Leave session
        ot_service.leave_session(
            db=mock_db,
            session_id=session_id,
            user_id=2
        )
        
        assert 2 not in ot_service.sessions[session_id].participants
        assert 1 in ot_service.sessions[session_id].participants  # Original user still there
    
    def test_apply_operation_insert(self, mock_db, sample_document):
        """Test applying insert operation"""
        operation = Operation(
            id="op_1",
            type=OperationType.INSERT,
            position=5,
            content=" Beautiful",
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Apply operation
        new_content, new_version = ot_service.apply_operation(
            db=mock_db,
            document=sample_document,
            operation=operation
        )
        
        assert new_content == "Hello Beautiful World"
        assert new_version == 2
    
    def test_apply_operation_delete(self, mock_db, sample_document):
        """Test applying delete operation"""
        operation = Operation(
            id="op_2",
            type=OperationType.DELETE,
            position=0,
            length=6,  # "Hello "
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Apply operation
        new_content, new_version = ot_service.apply_operation(
            db=mock_db,
            document=sample_document,
            operation=operation
        )
        
        assert new_content == "World"
        assert new_version == 2
    
    def test_transform_operations_insert_insert(self):
        """Test transforming two insert operations"""
        op1 = Operation(
            id="op_1",
            type=OperationType.INSERT,
            position=5,
            content="AAA",
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        op2 = Operation(
            id="op_2",
            type=OperationType.INSERT,
            position=3,
            content="BBB",
            user_id=2,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Transform op1 against op2
        transformed = ot_service.transform_operation(op1, op2)
        
        # op2 inserts before op1's position, so op1's position should shift
        assert transformed.position == 8  # 5 + 3 (length of "BBB")
        assert transformed.content == "AAA"
    
    def test_transform_operations_delete_insert(self):
        """Test transforming delete against insert"""
        op1 = Operation(
            id="op_1",
            type=OperationType.DELETE,
            position=5,
            length=3,
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        op2 = Operation(
            id="op_2",
            type=OperationType.INSERT,
            position=3,
            content="BBB",
            user_id=2,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Transform op1 against op2
        transformed = ot_service.transform_operation(op1, op2)
        
        # op2 inserts before op1's position, so op1's position should shift
        assert transformed.position == 8  # 5 + 3
        assert transformed.length == 3
    
    def test_transform_operations_delete_delete(self):
        """Test transforming two delete operations"""
        op1 = Operation(
            id="op_1",
            type=OperationType.DELETE,
            position=5,
            length=3,
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        op2 = Operation(
            id="op_2",
            type=OperationType.DELETE,
            position=3,
            length=2,
            user_id=2,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Transform op1 against op2
        transformed = ot_service.transform_operation(op1, op2)
        
        # op2 deletes before op1's position, so op1's position should shift back
        assert transformed.position == 3  # 5 - 2
        assert transformed.length == 3
    
    @pytest.mark.asyncio
    async def test_handle_concurrent_operations(self, mock_db):
        """Test handling concurrent operations"""
        # Create session
        session_id = ot_service.create_session(
            db=mock_db,
            document_id="doc_123",
            user_id=1
        )
        
        # Set initial document state
        ot_service.sessions[session_id].document_state = DocumentState(
            document_id="doc_123",
            content="Hello World",
            version=1,
            checksum="abc123"
        )
        
        # Create concurrent operations
        op1 = Operation(
            id="op_1",
            type=OperationType.INSERT,
            position=5,
            content=" Beautiful",
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        op2 = Operation(
            id="op_2",
            type=OperationType.INSERT,
            position=11,
            content="!",
            user_id=2,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Apply operations
        result1 = await ot_service.handle_operation(
            db=mock_db,
            session_id=session_id,
            operation=op1,
            user_id=1
        )
        
        result2 = await ot_service.handle_operation(
            db=mock_db,
            session_id=session_id,
            operation=op2,
            user_id=2
        )
        
        # Both operations should succeed
        assert result1["success"] is True
        assert result2["success"] is True
        
        # Final content should have both changes
        final_content = ot_service.sessions[session_id].document_state.content
        assert "Beautiful" in final_content
        assert final_content.endswith("!")
    
    def test_operation_history(self, mock_db):
        """Test maintaining operation history"""
        # Create session
        session_id = ot_service.create_session(
            db=mock_db,
            document_id="doc_123",
            user_id=1
        )
        
        # Add operations to history
        ops = []
        for i in range(5):
            op = Operation(
                id=f"op_{i}",
                type=OperationType.INSERT,
                position=i,
                content=str(i),
                user_id=1,
                timestamp=datetime.utcnow(),
                version=i + 1
            )
            ot_service.sessions[session_id].operation_history.append(op)
            ops.append(op)
        
        # Get history
        history = ot_service.get_operation_history(
            db=mock_db,
            session_id=session_id,
            from_version=2
        )
        
        # Should return operations from version 2 onwards
        assert len(history) == 4  # ops with versions 2, 3, 4, 5
        assert history[0].version == 2
    
    def test_conflict_resolution(self):
        """Test conflict resolution between operations"""
        # Create conflicting operations (same position)
        op1 = Operation(
            id="op_1",
            type=OperationType.INSERT,
            position=5,
            content="AAA",
            user_id=1,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        op2 = Operation(
            id="op_2",
            type=OperationType.INSERT,
            position=5,
            content="BBB",
            user_id=2,
            timestamp=datetime.utcnow(),
            version=1
        )
        
        # Transform to resolve conflict
        transformed1 = ot_service.transform_operation(op1, op2)
        transformed2 = ot_service.transform_operation(op2, op1)
        
        # Both operations should have different positions after transformation
        assert transformed1.position != transformed2.position
        # One should come after the other
        assert abs(transformed1.position - transformed2.position) == len("AAA") or abs(transformed1.position - transformed2.position) == len("BBB")


class TestRealtimeCollaborationAPI:
    """Test real-time collaboration API endpoints"""
    
    @pytest.fixture
    def client(self, test_app):
        """Get test client"""
        return TestClient(test_app)
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        return {"Authorization": "Bearer test_token"}
    
    @pytest.mark.asyncio
    async def test_create_session_endpoint(self, client, auth_headers):
        """Test creating collaboration session"""
        with patch('services.operational_transforms_service.ot_service.create_session') as mock_create:
            mock_create.return_value = "session_123"
            
            response = client.post(
                "/api/v1/collaboration/sessions",
                json={"document_id": "doc_123"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["session_id"] == "session_123"
    
    @pytest.mark.asyncio
    async def test_join_session_endpoint(self, client, auth_headers):
        """Test joining collaboration session"""
        with patch('services.operational_transforms_service.ot_service.join_session') as mock_join:
            mock_join.return_value = True
            
            response = client.post(
                "/api/v1/collaboration/sessions/session_123/join",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["joined"] is True
    
    @pytest.mark.asyncio
    async def test_apply_operation_endpoint(self, client, auth_headers):
        """Test applying operation endpoint"""
        with patch('services.operational_transforms_service.ot_service.handle_operation') as mock_handle:
            mock_handle.return_value = {
                "success": True,
                "content": "Updated content",
                "version": 2
            }
            
            response = client.post(
                "/api/v1/collaboration/sessions/session_123/operations",
                json={
                    "type": "insert",
                    "position": 5,
                    "content": "test"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    def test_websocket_connection(self):
        """Test WebSocket connection for real-time collaboration"""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        
        app = FastAPI()
        
        @app.websocket("/ws/{session_id}")
        async def websocket_endpoint(websocket: WebSocket, session_id: str):
            await websocket.accept()
            # Echo test
            data = await websocket.receive_text()
            await websocket.send_text(f"echo: {data}")
        
        client = TestClient(app)
        
        with client.websocket_connect("/ws/session_123") as websocket:
            websocket.send_text("Hello")
            data = websocket.receive_text()
            assert data == "echo: Hello"
    
    @pytest.mark.asyncio
    async def test_cursor_tracking(self, client, auth_headers):
        """Test cursor position tracking"""
        with patch('services.operational_transforms_service.ot_service.update_cursor_position') as mock_cursor:
            mock_cursor.return_value = True
            
            response = client.post(
                "/api/v1/collaboration/sessions/session_123/cursor",
                json={
                    "position": 10,
                    "selection_end": 15
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_get_session_state(self, client, auth_headers):
        """Test getting session state"""
        mock_state = {
            "document_id": "doc_123",
            "content": "Current content",
            "version": 5,
            "participants": [
                {"user_id": 1, "cursor_position": 10},
                {"user_id": 2, "cursor_position": 20}
            ]
        }
        
        with patch('services.operational_transforms_service.ot_service.get_session_state') as mock_get:
            mock_get.return_value = mock_state
            
            response = client.get(
                "/api/v1/collaboration/sessions/session_123",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["version"] == 5
            assert len(data["participants"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])