#!/usr/bin/env python3
"""
Enhanced Real-time Collaboration Engine
Advanced collaborative editing platform with operational transform, presence awareness, 
real-time communication, and comprehensive medical schema integration
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
import sqlite3
import difflib
from collections import defaultdict, deque
import hashlib
import threading
import time
import websockets
from websockets.server import WebSocketServerProtocol
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OperationType(Enum):
    """Advanced operation types for collaboration"""
    INSERT = "insert"
    DELETE = "delete"
    REPLACE = "replace"
    RETAIN = "retain"
    FORMAT = "format"
    ANNOTATION = "annotation"
    CURSOR_MOVE = "cursor_move"
    SELECTION = "selection"
    HIGHLIGHT = "highlight"
    COMMENT = "comment"
    RESOLVE = "resolve"
    UNDO = "undo"
    REDO = "redo"
    MEDICAL_ANNOTATION = "medical_annotation"

class DocumentType(Enum):
    """Types of collaborative documents"""
    TRANSCRIPT = "transcript"
    MEDICAL_TRANSCRIPT = "medical_transcript"
    ANALYSIS = "analysis"
    NOTES = "notes"
    REPORT = "report"
    ANNOTATION = "annotation"
    TEMPLATE = "template"
    CLINICAL_NOTES = "clinical_notes"

class UserRole(Enum):
    """Enhanced user roles with medical permissions"""
    OWNER = "owner"
    EDITOR = "editor"
    REVIEWER = "reviewer"
    VIEWER = "viewer"
    MEDICAL_PROFESSIONAL = "medical_professional"
    ADMIN = "admin"

class PresenceStatus(Enum):
    """User presence status"""
    ONLINE = "online"
    EDITING = "editing"
    VIEWING = "viewing"
    REVIEWING = "reviewing"
    ANNOTATING = "annotating"
    IDLE = "idle"
    AWAY = "away"
    OFFLINE = "offline"

class ConflictResolutionStrategy(Enum):
    """Conflict resolution strategies"""
    LAST_WRITE_WINS = "last_write_wins"
    OPERATIONAL_TRANSFORM = "operational_transform"
    THREE_WAY_MERGE = "three_way_merge"
    USER_PRIORITY = "user_priority"
    MANUAL_RESOLUTION = "manual_resolution"

@dataclass
class Operation:
    """Enhanced collaborative operation with medical context"""
    op_id: str
    user_id: str
    document_id: str
    op_type: OperationType
    position: int
    content: str = ""
    length: int = 0
    attributes: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    client_id: str = ""
    sequence_number: int = 0
    parent_op_id: Optional[str] = None
    medical_context: Optional[Dict[str, Any]] = None
    hipaa_compliant: bool = True
    requires_approval: bool = False
    approved_by: Optional[str] = None
    conflict_resolution: ConflictResolutionStrategy = ConflictResolutionStrategy.OPERATIONAL_TRANSFORM

@dataclass 
class User:
    """Enhanced collaborative user with medical permissions"""
    user_id: str
    username: str
    email: str
    role: UserRole
    color: str
    avatar_url: Optional[str] = None
    permissions: Set[str] = field(default_factory=set)
    medical_credentials: Optional[Dict[str, Any]] = None
    hipaa_trained: bool = False
    last_activity: datetime = field(default_factory=datetime.now)
    is_verified: bool = False
    department: Optional[str] = None

@dataclass
class UserPresence:
    """Enhanced user presence with detailed activity tracking"""
    user_id: str
    username: str
    status: PresenceStatus
    cursor_position: int = 0
    selection_start: int = 0
    selection_end: int = 0
    last_seen: datetime = field(default_factory=datetime.now)
    client_id: str = ""
    color: str = "#3B82F6"
    current_section: Optional[str] = None
    active_tool: Optional[str] = None
    is_typing: bool = False
    typing_at_position: Optional[int] = None
    viewport_start: Optional[int] = None
    viewport_end: Optional[int] = None
    zoom_level: float = 1.0
    device_type: str = "desktop"  # desktop, tablet, mobile
    browser_info: Optional[Dict[str, str]] = None

@dataclass
class Document:
    """Enhanced collaborative document with medical features"""
    document_id: str
    title: str
    content: str
    document_type: DocumentType
    owner_id: str
    collaborators: Dict[str, UserRole] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    permissions: Dict[str, Any] = field(default_factory=dict)
    is_medical: bool = False
    hipaa_compliant: bool = False
    patient_id: Optional[str] = None
    medical_schema_version: Optional[str] = None
    encryption_key: Optional[str] = None
    access_log: List[Dict[str, Any]] = field(default_factory=list)
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)
    quality_score: Optional[float] = None
    last_quality_check: Optional[datetime] = None

@dataclass
class Annotation:
    """Enhanced annotation with medical context"""
    annotation_id: str
    document_id: str
    user_id: str
    content: str
    start_position: int
    end_position: int
    annotation_type: str = "comment"
    category: Optional[str] = None
    severity: Optional[str] = None
    medical_code: Optional[str] = None
    icd_10_code: Optional[str] = None
    replies: List[Dict[str, Any]] = field(default_factory=list)
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    requires_medical_review: bool = False
    reviewed_by_medical: Optional[str] = None
    confidence_score: Optional[float] = None
    ai_generated: bool = False

@dataclass
class CollaborationSession:
    """Enhanced collaboration session with comprehensive tracking"""
    session_id: str
    document_id: str
    active_users: Dict[str, UserPresence] = field(default_factory=dict)
    operation_history: List[Operation] = field(default_factory=list)
    annotations: Dict[str, Annotation] = field(default_factory=dict)
    chat_messages: List[Dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)
    session_type: str = "collaborative_editing"
    max_concurrent_users: int = 50
    is_recording_session: bool = False
    recording_metadata: Optional[Dict[str, Any]] = None
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    conflict_count: int = 0
    resolution_count: int = 0
    medical_review_required: bool = False
    hipaa_audit_enabled: bool = True

class AdvancedOperationalTransform:
    """Advanced Operational Transform engine with medical context awareness"""
    
    @staticmethod
    def transform_position(pos: int, operation: Operation, is_own_operation: bool = False) -> int:
        """Transform a position based on an operation with medical context"""
        if operation.op_type == OperationType.INSERT:
            if pos > operation.position or (pos == operation.position and not is_own_operation):
                return pos + len(operation.content)
            return pos
        elif operation.op_type == OperationType.DELETE:
            if pos > operation.position + operation.length:
                return pos - operation.length
            elif pos > operation.position:
                return operation.position
            return pos
        elif operation.op_type == OperationType.REPLACE:
            if pos > operation.position + operation.length:
                return pos - operation.length + len(operation.content)
            elif pos > operation.position:
                return operation.position + len(operation.content)
            return pos
        return pos
    
    @staticmethod
    def transform_operation(op1: Operation, op2: Operation, is_left: bool = True) -> Optional[Operation]:
        """Advanced operation transformation with conflict detection"""
        # Medical annotations get priority
        if op1.medical_context and not op2.medical_context:
            return AdvancedOperationalTransform._prioritize_medical_operation(op1, op2)
        
        if op1.op_type == OperationType.INSERT and op2.op_type == OperationType.INSERT:
            return AdvancedOperationalTransform._transform_insert_insert(op1, op2, is_left)
        elif op1.op_type == OperationType.DELETE and op2.op_type == OperationType.DELETE:
            return AdvancedOperationalTransform._transform_delete_delete(op1, op2)
        elif op1.op_type == OperationType.INSERT and op2.op_type == OperationType.DELETE:
            return AdvancedOperationalTransform._transform_insert_delete(op1, op2)
        elif op1.op_type == OperationType.DELETE and op2.op_type == OperationType.INSERT:
            return AdvancedOperationalTransform._transform_delete_insert(op1, op2)
        elif op1.op_type == OperationType.REPLACE:
            return AdvancedOperationalTransform._transform_replace(op1, op2)
        
        return op2
    
    @staticmethod
    def _prioritize_medical_operation(medical_op: Operation, other_op: Operation) -> Operation:
        """Give priority to medical operations for safety"""
        logger.info(f"Medical operation {medical_op.op_id} takes priority over {other_op.op_id}")
        
        # Transform the other operation based on medical operation
        if medical_op.op_type == OperationType.INSERT:
            if other_op.position >= medical_op.position:
                new_op = Operation(
                    op_id=other_op.op_id,
                    user_id=other_op.user_id,
                    document_id=other_op.document_id,
                    op_type=other_op.op_type,
                    position=other_op.position + len(medical_op.content),
                    content=other_op.content,
                    length=other_op.length,
                    attributes=other_op.attributes,
                    timestamp=other_op.timestamp,
                    client_id=other_op.client_id,
                    sequence_number=other_op.sequence_number,
                    parent_op_id=other_op.parent_op_id,
                    medical_context=other_op.medical_context,
                    hipaa_compliant=other_op.hipaa_compliant,
                    requires_approval=other_op.requires_approval
                )
                return new_op
        
        return other_op
    
    @staticmethod
    def _transform_insert_insert(op1: Operation, op2: Operation, is_left: bool) -> Operation:
        """Transform two insert operations"""
        if op1.position < op2.position or (op1.position == op2.position and is_left):
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=op2.position + len(op1.content),
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
        return op2
    
    @staticmethod
    def _transform_delete_delete(op1: Operation, op2: Operation) -> Optional[Operation]:
        """Transform two delete operations"""
        if op1.position + op1.length <= op2.position:
            # op1 is before op2
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=op2.position - op1.length,
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
        elif op1.position >= op2.position + op2.length:
            # op1 is after op2
            return op2
        else:
            # Overlapping deletes - resolve conflict
            overlap_start = max(op1.position, op2.position)
            overlap_end = min(op1.position + op1.length, op2.position + op2.length)
            overlap_length = max(0, overlap_end - overlap_start)
            
            new_length = max(0, op2.length - overlap_length)
            if new_length == 0:
                return None  # Operation becomes no-op
            
            new_position = min(op1.position, op2.position)
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=new_position,
                content=op2.content,
                length=new_length,
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
    
    @staticmethod
    def _transform_insert_delete(op1: Operation, op2: Operation) -> Operation:
        """Transform insert followed by delete"""
        if op1.position <= op2.position:
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=op2.position + len(op1.content),
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
        elif op1.position >= op2.position + op2.length:
            return op2
        else:
            # Insert is within delete range
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=op2.position,
                content=op2.content,
                length=op2.length + len(op1.content),
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
    
    @staticmethod
    def _transform_delete_insert(op1: Operation, op2: Operation) -> Operation:
        """Transform delete followed by insert"""
        if op1.position + op1.length <= op2.position:
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=op2.position - op1.length,
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
        elif op1.position >= op2.position:
            return op2
        else:
            # Delete overlaps with insert position
            new_op = Operation(
                op_id=op2.op_id,
                user_id=op2.user_id,
                document_id=op2.document_id,
                op_type=op2.op_type,
                position=op1.position,
                content=op2.content,
                length=op2.length,
                attributes=op2.attributes,
                timestamp=op2.timestamp,
                client_id=op2.client_id,
                sequence_number=op2.sequence_number,
                parent_op_id=op2.parent_op_id,
                medical_context=op2.medical_context,
                hipaa_compliant=op2.hipaa_compliant,
                requires_approval=op2.requires_approval
            )
            return new_op
    
    @staticmethod
    def _transform_replace(op1: Operation, op2: Operation) -> Operation:
        """Transform replace operations"""
        # For replace operations, treat as delete + insert
        if op1.op_type == OperationType.REPLACE:
            # Convert replace to delete
            delete_op = Operation(
                op_id=op1.op_id + "_delete",
                user_id=op1.user_id,
                document_id=op1.document_id,
                op_type=OperationType.DELETE,
                position=op1.position,
                length=op1.length,
                timestamp=op1.timestamp,
                client_id=op1.client_id
            )
            
            # Transform op2 against delete
            transformed = AdvancedOperationalTransform._transform_delete_insert(delete_op, op2)
            if transformed:
                # Now transform against insert
                insert_op = Operation(
                    op_id=op1.op_id + "_insert",
                    user_id=op1.user_id,
                    document_id=op1.document_id,
                    op_type=OperationType.INSERT,
                    position=op1.position,
                    content=op1.content,
                    timestamp=op1.timestamp,
                    client_id=op1.client_id
                )
                return AdvancedOperationalTransform._transform_insert_insert(insert_op, transformed, False)
        
        return op2

class AdvancedConflictResolver:
    """Advanced conflict resolution with medical context awareness"""
    
    def __init__(self):
        self.operation_history = []
        self.conflict_patterns = defaultdict(int)
        self.resolution_strategies = {
            ConflictResolutionStrategy.LAST_WRITE_WINS: self._last_write_wins,
            ConflictResolutionStrategy.OPERATIONAL_TRANSFORM: self._operational_transform,
            ConflictResolutionStrategy.THREE_WAY_MERGE: self._three_way_merge,
            ConflictResolutionStrategy.USER_PRIORITY: self._user_priority,
            ConflictResolutionStrategy.MANUAL_RESOLUTION: self._manual_resolution
        }
    
    async def resolve_conflict(self, operations: List[Operation], strategy: ConflictResolutionStrategy) -> List[Operation]:
        """Resolve conflicts using specified strategy"""
        resolver = self.resolution_strategies.get(strategy, self._operational_transform)
        return await resolver(operations)
    
    async def _last_write_wins(self, operations: List[Operation]) -> List[Operation]:
        """Last write wins strategy"""
        if not operations:
            return []
        
        # Sort by timestamp and return the latest
        operations.sort(key=lambda op: op.timestamp, reverse=True)
        return [operations[0]]
    
    async def _operational_transform(self, operations: List[Operation]) -> List[Operation]:
        """Operational transform strategy"""
        if len(operations) <= 1:
            return operations
        
        resolved_ops = []
        base_op = operations[0]
        
        for op in operations[1:]:
            transformed = AdvancedOperationalTransform.transform_operation(base_op, op, is_left=False)
            if transformed:
                resolved_ops.append(transformed)
            base_op = transformed if transformed else base_op
        
        return [base_op] + resolved_ops
    
    async def _three_way_merge(self, operations: List[Operation]) -> List[Operation]:
        """Three-way merge strategy"""
        if len(operations) < 3:
            return await self._operational_transform(operations)
        
        # Find common ancestor
        base_content = ""
        local_content = operations[0].content if operations[0].op_type == OperationType.INSERT else ""
        remote_content = operations[1].content if operations[1].op_type == OperationType.INSERT else ""
        
        # Simple merge logic - in production, use more sophisticated algorithms
        merged_content = self._merge_content(base_content, local_content, remote_content)
        
        # Create merged operation
        merged_op = Operation(
            op_id=str(uuid.uuid4()),
            user_id="system",
            document_id=operations[0].document_id,
            op_type=OperationType.INSERT,
            position=operations[0].position,
            content=merged_content,
            timestamp=datetime.now()
        )
        
        return [merged_op]
    
    async def _user_priority(self, operations: List[Operation]) -> List[Operation]:
        """User priority strategy - medical professionals get priority"""
        priority_order = {
            UserRole.MEDICAL_PROFESSIONAL: 0,
            UserRole.OWNER: 1,
            UserRole.ADMIN: 2,
            UserRole.EDITOR: 3,
            UserRole.REVIEWER: 4,
            UserRole.VIEWER: 5
        }
        
        # Would need user role information - simplified implementation
        medical_ops = [op for op in operations if op.medical_context]
        if medical_ops:
            return medical_ops[:1]  # Take first medical operation
        
        return operations[:1]  # Take first non-medical operation
    
    async def _manual_resolution(self, operations: List[Operation]) -> List[Operation]:
        """Manual resolution strategy - mark for human review"""
        for op in operations:
            op.requires_approval = True
        
        return operations
    
    def _merge_content(self, base: str, local: str, remote: str) -> str:
        """Simple content merge implementation"""
        if local == remote:
            return local
        elif local == base:
            return remote
        elif remote == base:
            return local
        else:
            # Both changed - create conflict markers
            return f"<<<<<<< LOCAL\n{local}\n=======\n{remote}\n>>>>>>> REMOTE"

class ComprehensiveCollaborationEngine:
    """Enhanced collaboration engine with comprehensive medical features"""
    
    def __init__(self, db_path: str = "enhanced_collaboration.db", redis_url: str = "redis://localhost:6379"):
        self.db_path = db_path
        self.redis_url = redis_url
        self.redis_client = None
        self.operation_transform = AdvancedOperationalTransform()
        self.conflict_resolver = AdvancedConflictResolver()
        self.sessions: Dict[str, CollaborationSession] = {}
        self.documents: Dict[str, Document] = {}
        self.connected_clients: Dict[str, WebSocketServerProtocol] = {}
        self.user_colors = [
            "#3B82F6", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6",
            "#EC4899", "#06B6D4", "#84CC16", "#F97316", "#6366F1",
            "#F472B6", "#A78BFA", "#34D399", "#FBBF24", "#F87171"
        ]
        self.color_index = 0
        self.executor = ThreadPoolExecutor(max_workers=8)
        self.websocket_handlers: Dict[str, WebSocketServerProtocol] = {}
        
        # Medical-specific settings
        self.hipaa_audit_enabled = True
        self.medical_review_queue = deque()
        self.quality_thresholds = {
            'minimum_accuracy': 0.95,
            'medical_terminology_accuracy': 0.98,
            'hipaa_compliance_score': 0.99
        }
        
        # Initialize systems
        self._init_database()
        self._start_background_tasks()
    
    def _init_database(self):
        """Initialize enhanced database schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    document_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    document_type TEXT NOT NULL,
                    owner_id TEXT NOT NULL,
                    collaborators TEXT NOT NULL DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    version INTEGER DEFAULT 1,
                    metadata TEXT DEFAULT '{}',
                    permissions TEXT DEFAULT '{}',
                    is_medical BOOLEAN DEFAULT FALSE,
                    hipaa_compliant BOOLEAN DEFAULT FALSE,
                    patient_id TEXT,
                    medical_schema_version TEXT,
                    encryption_key TEXT,
                    quality_score REAL,
                    last_quality_check TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS operations (
                    op_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    op_type TEXT NOT NULL,
                    position INTEGER NOT NULL,
                    content TEXT DEFAULT '',
                    length INTEGER DEFAULT 0,
                    attributes TEXT DEFAULT '{}',
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    client_id TEXT DEFAULT '',
                    sequence_number INTEGER DEFAULT 0,
                    parent_op_id TEXT,
                    medical_context TEXT,
                    hipaa_compliant BOOLEAN DEFAULT TRUE,
                    requires_approval BOOLEAN DEFAULT FALSE,
                    approved_by TEXT,
                    conflict_resolution_strategy TEXT DEFAULT 'operational_transform',
                    FOREIGN KEY (document_id) REFERENCES documents (document_id)
                );
                
                CREATE TABLE IF NOT EXISTS annotations (
                    annotation_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    start_position INTEGER NOT NULL,
                    end_position INTEGER NOT NULL,
                    annotation_type TEXT DEFAULT 'comment',
                    category TEXT,
                    severity TEXT,
                    medical_code TEXT,
                    icd_10_code TEXT,
                    replies TEXT DEFAULT '[]',
                    resolved BOOLEAN DEFAULT FALSE,
                    resolved_by TEXT,
                    resolved_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT DEFAULT '{}',
                    requires_medical_review BOOLEAN DEFAULT FALSE,
                    reviewed_by_medical TEXT,
                    confidence_score REAL,
                    ai_generated BOOLEAN DEFAULT FALSE,
                    FOREIGN KEY (document_id) REFERENCES documents (document_id)
                );
                
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    session_type TEXT DEFAULT 'collaborative_editing',
                    max_concurrent_users INTEGER DEFAULT 50,
                    is_recording_session BOOLEAN DEFAULT FALSE,
                    recording_metadata TEXT,
                    conflict_count INTEGER DEFAULT 0,
                    resolution_count INTEGER DEFAULT 0,
                    medical_review_required BOOLEAN DEFAULT FALSE,
                    hipaa_audit_enabled BOOLEAN DEFAULT TRUE,
                    FOREIGN KEY (document_id) REFERENCES documents (document_id)
                );
                
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL,
                    role TEXT NOT NULL,
                    color TEXT NOT NULL,
                    avatar_url TEXT,
                    permissions TEXT DEFAULT '{}',
                    medical_credentials TEXT,
                    hipaa_trained BOOLEAN DEFAULT FALSE,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_verified BOOLEAN DEFAULT FALSE,
                    department TEXT
                );
                
                CREATE TABLE IF NOT EXISTS presence (
                    user_id TEXT,
                    session_id TEXT,
                    status TEXT NOT NULL,
                    cursor_position INTEGER DEFAULT 0,
                    selection_start INTEGER DEFAULT 0,
                    selection_end INTEGER DEFAULT 0,
                    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    client_id TEXT,
                    color TEXT,
                    current_section TEXT,
                    active_tool TEXT,
                    is_typing BOOLEAN DEFAULT FALSE,
                    device_type TEXT DEFAULT 'desktop',
                    PRIMARY KEY (user_id, session_id)
                );
                
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    details TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    hipaa_relevant BOOLEAN DEFAULT FALSE
                );
                
                CREATE TABLE IF NOT EXISTS conflicts (
                    conflict_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    operation_ids TEXT NOT NULL,
                    resolution_strategy TEXT NOT NULL,
                    resolved_at TIMESTAMP,
                    resolved_by TEXT,
                    resolution_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_operations_document_timestamp 
                ON operations (document_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_annotations_document 
                ON annotations (document_id);
                CREATE INDEX IF NOT EXISTS idx_sessions_document 
                ON sessions (document_id);
                CREATE INDEX IF NOT EXISTS idx_presence_session 
                ON presence (session_id);
                CREATE INDEX IF NOT EXISTS idx_audit_session_timestamp 
                ON audit_log (session_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_conflicts_session 
                ON conflicts (session_id);
            """)
    
    def _start_background_tasks(self):
        """Start enhanced background maintenance tasks"""
        def cleanup_inactive_sessions():
            while True:
                try:
                    cutoff_time = datetime.now() - timedelta(minutes=30)
                    inactive_sessions = []
                    
                    for session_id, session in self.sessions.items():
                        if session.last_activity < cutoff_time:
                            inactive_sessions.append(session_id)
                    
                    for session_id in inactive_sessions:
                        self._cleanup_session(session_id)
                    
                    time.sleep(300)  # Check every 5 minutes
                except Exception as e:
                    logger.error(f"Error in cleanup task: {e}")
                    time.sleep(60)
        
        def process_medical_review_queue():
            while True:
                try:
                    if self.medical_review_queue:
                        annotation = self.medical_review_queue.popleft()
                        self._process_medical_review(annotation)
                    time.sleep(10)  # Check every 10 seconds
                except Exception as e:
                    logger.error(f"Error in medical review task: {e}")
                    time.sleep(30)
        
        def quality_assessment_task():
            while True:
                try:
                    self._run_quality_assessments()
                    time.sleep(1800)  # Run every 30 minutes
                except Exception as e:
                    logger.error(f"Error in quality assessment task: {e}")
                    time.sleep(300)
        
        # Start background threads
        cleanup_thread = threading.Thread(target=cleanup_inactive_sessions, daemon=True)
        cleanup_thread.start()
        
        medical_review_thread = threading.Thread(target=process_medical_review_queue, daemon=True)
        medical_review_thread.start()
        
        quality_thread = threading.Thread(target=quality_assessment_task, daemon=True)
        quality_thread.start()
    
    async def initialize_redis(self):
        """Initialize Redis connection"""
        self.redis_client = redis.from_url(self.redis_url)
        logger.info("Redis connection initialized")
    
    async def create_document(self, user: User, title: str, content: str = "", 
                            document_type: DocumentType = DocumentType.TRANSCRIPT,
                            is_medical: bool = False, patient_id: Optional[str] = None) -> Document:
        """Create enhanced collaborative document with medical features"""
        document_id = str(uuid.uuid4())
        
        # Generate encryption key for medical documents
        encryption_key = None
        if is_medical:
            encryption_key = hashlib.sha256(f"{document_id}:{user.user_id}:{datetime.now()}".encode()).hexdigest()
        
        document = Document(
            document_id=document_id,
            title=title,
            content=content,
            document_type=document_type,
            owner_id=user.user_id,
            collaborators={user.user_id: UserRole.OWNER},
            is_medical=is_medical,
            hipaa_compliant=is_medical,
            patient_id=patient_id,
            encryption_key=encryption_key,
            metadata={
                'created_by': user.username,
                'language': 'en',
                'encoding': 'utf-8',
                'medical_context': is_medical,
                'requires_hipaa_compliance': is_medical
            }
        )
        
        self.documents[document_id] = document
        await self._save_document(document)
        
        # Log audit trail for medical documents
        if is_medical and self.hipaa_audit_enabled:
            await self._log_hipaa_audit(
                user.user_id, 
                "document_created", 
                f"Created medical document {document_id}",
                {"document_id": document_id, "patient_id": patient_id}
            )
        
        logger.info(f"Created {'medical ' if is_medical else ''}document {document_id} by user {user.username}")
        return document
    
    def _cleanup_session(self, session_id: str):
        """Enhanced session cleanup with audit logging"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            
            # Save session analytics
            self._save_session_analytics(session)
            
            # Clean up websocket connections
            for user_id, presence in session.active_users.items():
                if presence.client_id in self.connected_clients:
                    del self.connected_clients[presence.client_id]
            
            del self.sessions[session_id]
            logger.info(f"Cleaned up session {session_id}")
    
    def _save_session_analytics(self, session: CollaborationSession):
        """Save session analytics for reporting"""
        analytics = {
            'session_id': session.session_id,
            'document_id': session.document_id,
            'duration': (session.last_activity - session.created_at).total_seconds(),
            'total_operations': len(session.operation_history),
            'total_annotations': len(session.annotations),
            'total_messages': len(session.chat_messages),
            'max_concurrent_users': len(session.active_users),
            'conflict_count': session.conflict_count,
            'resolution_count': session.resolution_count,
            'medical_review_required': session.medical_review_required
        }
        
        # In production, save to analytics database
        logger.info(f"Session analytics: {analytics}")
    
    def _process_medical_review(self, annotation: Annotation):
        """Process annotations requiring medical review"""
        logger.info(f"Processing medical review for annotation {annotation.annotation_id}")
        
        # In production, integrate with medical review system
        # For now, just log the requirement
        if annotation.medical_code or annotation.icd_10_code:
            logger.info(f"Medical annotation requires review: {annotation.medical_code or annotation.icd_10_code}")
    
    def _run_quality_assessments(self):
        """Run quality assessments on active documents"""
        for document in self.documents.values():
            if document.is_medical and (
                not document.last_quality_check or 
                datetime.now() - document.last_quality_check > timedelta(hours=1)
            ):
                quality_score = self._assess_document_quality(document)
                document.quality_score = quality_score
                document.last_quality_check = datetime.now()
                logger.info(f"Quality assessment for document {document.document_id}: {quality_score}")
    
    def _assess_document_quality(self, document: Document) -> float:
        """Assess document quality using comprehensive medical schema"""
        # Simplified quality assessment - in production, integrate with quality_assessment_system.py
        base_score = 0.8
        
        # Medical context bonus
        if document.is_medical and document.patient_id:
            base_score += 0.1
        
        # HIPAA compliance check
        if document.hipaa_compliant:
            base_score += 0.1
        
        # Content completeness check
        if len(document.content) > 100:
            base_score += min(0.1, len(document.content) / 10000)
        
        return min(1.0, base_score)
    
    async def _save_document(self, document: Document):
        """Save enhanced document with medical features"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO documents 
                (document_id, title, content, document_type, owner_id, collaborators, 
                 created_at, updated_at, version, metadata, permissions, is_medical, 
                 hipaa_compliant, patient_id, medical_schema_version, encryption_key,
                 quality_score, last_quality_check)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                document.document_id, document.title, document.content, document.document_type.value,
                document.owner_id, json.dumps({k: v.value for k, v in document.collaborators.items()}),
                document.created_at.isoformat(), document.updated_at.isoformat(), document.version,
                json.dumps(document.metadata), json.dumps(document.permissions),
                document.is_medical, document.hipaa_compliant, document.patient_id,
                document.medical_schema_version, document.encryption_key,
                document.quality_score,
                document.last_quality_check.isoformat() if document.last_quality_check else None
            ))
    
    async def _log_hipaa_audit(self, user_id: str, action: str, details: str, metadata: Dict[str, Any]):
        """Log HIPAA-relevant audit events"""
        if not self.hipaa_audit_enabled:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO audit_log 
                (session_id, user_id, action, details, timestamp, hipaa_relevant)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                metadata.get('session_id', 'system'),
                user_id,
                action,
                details,
                datetime.now().isoformat(),
                True
            ))
        
        logger.info(f"HIPAA audit logged: {action} by {user_id}")

# Example usage and comprehensive testing
async def main():
    """Comprehensive demonstration of the enhanced collaboration system"""
    engine = ComprehensiveCollaborationEngine()
    await engine.initialize_redis()
    
    # Create enhanced test users with medical credentials
    medical_user = User(
        user_id="med_user_001",
        username="dr_smith",
        email="dr.smith@hospital.com",
        role=UserRole.MEDICAL_PROFESSIONAL,
        color="#3B82F6",
        permissions={"read", "write", "comment", "medical_annotate", "prescribe"},
        medical_credentials={"license": "MD123456", "specialty": "cardiology"},
        hipaa_trained=True,
        is_verified=True,
        department="Cardiology"
    )
    
    editor_user = User(
        user_id="editor_001",
        username="sarah_editor",
        email="sarah@transcription.com",
        role=UserRole.EDITOR,
        color="#10B981",
        permissions={"read", "write", "comment"},
        hipaa_trained=True,
        is_verified=True,
        department="Medical Transcription"
    )
    
    # Create a medical document
    document = await engine.create_document(
        user=medical_user,
        title="Patient Cardiac Consultation - John Doe",
        content="Patient presented with chest pain and dyspnea. ECG shows ST elevation in leads II, III, aVF suggesting inferior STEMI.",
        document_type=DocumentType.MEDICAL_TRANSCRIPT,
        is_medical=True,
        patient_id="patient_12345"
    )
    
    print(f"Created medical document: {document.document_id}")
    print(f"HIPAA compliant: {document.hipaa_compliant}")
    print(f"Encryption key: {document.encryption_key[:16]}..." if document.encryption_key else "No encryption")
    print(f"Patient ID: {document.patient_id}")
    print(f"Quality score: {document.quality_score}")
    
    # Simulate collaborative operations with medical context
    medical_annotation_op = Operation(
        op_id=str(uuid.uuid4()),
        user_id=medical_user.user_id,
        document_id=document.document_id,
        op_type=OperationType.MEDICAL_ANNOTATION,
        position=45,
        content="Recommend immediate cardiac catheterization",
        medical_context={
            "diagnosis_code": "I21.1",
            "severity": "high",
            "requires_immediate_action": True
        },
        hipaa_compliant=True,
        requires_approval=False
    )
    
    edit_operation = Operation(
        op_id=str(uuid.uuid4()),
        user_id=editor_user.user_id,
        document_id=document.document_id,
        op_type=OperationType.INSERT,
        position=len(document.content),
        content=" Blood pressure 140/90 mmHg, heart rate 98 bpm.",
        hipaa_compliant=True,
        requires_approval=False
    )
    
    print(f"\nMedical annotation: {medical_annotation_op.content}")
    print(f"Medical context: {medical_annotation_op.medical_context}")
    print(f"Editor addition: {edit_operation.content}")
    
    # Test operational transform with medical priority
    transformed_op = AdvancedOperationalTransform.transform_operation(
        medical_annotation_op, edit_operation, is_left=True
    )
    
    print(f"\nTransformed operation position: {transformed_op.position}")
    print(f"Medical operations take priority: {medical_annotation_op.medical_context is not None}")

if __name__ == "__main__":
    asyncio.run(main())