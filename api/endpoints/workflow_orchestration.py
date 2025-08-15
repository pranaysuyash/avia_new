"""
Workflow Orchestration API Endpoints
RESTful API for managing enterprise workflow orchestration
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
import json
import uuid
from pydantic import BaseModel, Field, validator
from enum import Enum
import logging

# Import workflow systems
from workflow_orchestration_system import WorkflowEngine, WorkflowDefinition, WorkflowExecution, NodeStatus, WorkflowStatus
from enterprise_workflow_management import EnterpriseWorkflowManager, WorkflowCategory, WorkflowApprovalStatus
from workflow_templates_automation import WorkflowTemplateLibrary, AutomationEngine
from api.auth import get_current_user, get_admin_user
from api.database import get_db
from api.models import User

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/workflows", tags=["Workflow Orchestration"])

# Pydantic Models
class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class WorkflowPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class WorkflowNodeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    node_type: str = Field(..., description="Type of workflow node")
    processor: str = Field(..., description="Processor function to execute")
    inputs: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = Field(None, description="Timeout in seconds")

class WorkflowEdgeCreate(BaseModel):
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    condition: Optional[Dict[str, Any]] = Field(None, description="Edge condition")
    data_mapping: Dict[str, str] = Field(default_factory=dict, description="Data mapping between nodes")

class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., max_length=1000)
    category: str = Field(..., description="Workflow category")
    priority: WorkflowPriority = Field(default=WorkflowPriority.MEDIUM)
    nodes: List[WorkflowNodeCreate] = Field(..., min_items=1)
    edges: List[WorkflowEdgeCreate] = Field(default_factory=list)
    triggers: List[Dict[str, Any]] = Field(default_factory=list)
    variables: Dict[str, Any] = Field(default_factory=dict)
    config: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
        return v

class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = None
    priority: Optional[WorkflowPriority] = None
    tags: Optional[List[str]] = None
    config: Optional[Dict[str, Any]] = None

class WorkflowExecuteRequest(BaseModel):
    input_data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)
    priority: Optional[WorkflowPriority] = Field(default=WorkflowPriority.MEDIUM)
    scheduled_for: Optional[datetime] = Field(None, description="Schedule execution for later")

class WorkflowScheduleCreate(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID to schedule")
    cron_expression: str = Field(..., description="Cron expression for scheduling")
    timezone: str = Field(default="UTC", description="Timezone for schedule")
    is_active: bool = Field(default=True)
    max_runs: Optional[int] = Field(None, description="Maximum number of runs")
    start_date: Optional[datetime] = Field(None)
    end_date: Optional[datetime] = Field(None)

class WorkflowTemplateDeployRequest(BaseModel):
    template_id: str = Field(..., description="Template ID to deploy")
    name: str = Field(..., min_length=1, max_length=200)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Template parameters")
    category: Optional[str] = None
    priority: Optional[WorkflowPriority] = Field(default=WorkflowPriority.MEDIUM)
    tags: List[str] = Field(default_factory=list)

class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    version: str
    status: WorkflowStatus
    priority: WorkflowPriority
    node_count: int
    trigger_count: int
    execution_count: int
    success_rate: float
    average_duration: float
    last_executed: Optional[datetime]
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    created_by: str

class WorkflowExecutionResponse(BaseModel):
    id: str
    workflow_id: str
    workflow_name: str
    status: WorkflowStatus
    priority: WorkflowPriority
    progress: float
    started_at: datetime
    completed_at: Optional[datetime]
    duration: Optional[float]
    node_states: Dict[str, NodeStatus]
    results: Dict[str, Any]
    errors: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    context: Dict[str, Any]

class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total_count: int
    page: int
    page_size: int
    total_pages: int

class WorkflowMetricsResponse(BaseModel):
    total_workflows: int
    active_workflows: int
    total_executions: int
    successful_executions: int
    failed_executions: int
    average_success_rate: float
    average_execution_time: float
    executions_by_status: Dict[str, int]
    executions_by_category: Dict[str, int]
    performance_trends: Dict[str, List[float]]

class SystemHealthResponse(BaseModel):
    status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_latency: float
    active_executions: int
    queue_length: int
    worker_nodes: int
    timestamp: datetime

# Global instances
workflow_engine = WorkflowEngine()
enterprise_manager = EnterpriseWorkflowManager()
template_library = WorkflowTemplateLibrary()
automation_engine = AutomationEngine()

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message: dict):
        for connection in self.active_connections[:]:  # Copy to avoid modification during iteration
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                await self.disconnect(connection)

manager = ConnectionManager()

# Workflow Management Endpoints

@router.post("/", response_model=WorkflowResponse, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a new workflow"""
    try:
        # Convert Pydantic models to dict format expected by WorkflowEngine
        nodes_data = [
            {
                'id': str(uuid.uuid4()),
                'name': node.name,
                'type': node.node_type,
                'processor': node.processor,
                'inputs': node.inputs,
                'config': node.config,
                'dependencies': node.dependencies,
                'retry_policy': node.retry_policy,
                'timeout': node.timeout
            }
            for node in workflow.nodes
        ]
        
        edges_data = [
            {
                'source': edge.source,
                'target': edge.target,
                'condition': edge.condition,
                'data_mapping': edge.data_mapping
            }
            for edge in workflow.edges
        ]
        
        # Create workflow using WorkflowEngine
        workflow_def = workflow_engine.create_workflow(
            name=workflow.name,
            description=workflow.description,
            nodes=nodes_data,
            edges=edges_data,
            triggers=workflow.triggers
        )
        
        # Register with enterprise manager
        enterprise_workflow = await enterprise_manager.create_workflow(
            name=workflow.name,
            description=workflow.description,
            category=WorkflowCategory(workflow.category.lower()),
            workflow_definition=workflow_def.__dict__,
            created_by=current_user.id
        )
        
        # Broadcast creation event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "workflow_created",
                "workflow_id": workflow_def.workflow_id,
                "name": workflow.name,
                "created_by": current_user.email
            }
        )
        
        # Return response
        return WorkflowResponse(
            id=workflow_def.workflow_id,
            name=workflow_def.name,
            description=workflow_def.description,
            category=workflow.category,
            version=workflow_def.version,
            status=WorkflowStatus.DRAFT,
            priority=workflow.priority,
            node_count=len(workflow_def.nodes),
            trigger_count=len(workflow_def.triggers),
            execution_count=0,
            success_rate=0.0,
            average_duration=0.0,
            last_executed=None,
            tags=workflow.tags,
            created_at=workflow_def.created_at,
            updated_at=workflow_def.updated_at,
            created_by=current_user.email
        )
    
    except Exception as e:
        logger.error(f"Failed to create workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    status: Optional[WorkflowStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in name and description"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    sort_by: str = Query("updated_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """List workflows with filtering, sorting, and pagination"""
    try:
        # Get workflows from enterprise manager
        workflows = await enterprise_manager.list_workflows(
            user_id=current_user.id,
            category=category,
            status=status,
            search=search,
            tags=tags,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Convert to response format
        workflow_responses = []
        for wf in workflows.get('workflows', []):
            workflow_responses.append(WorkflowResponse(
                id=wf['id'],
                name=wf['name'],
                description=wf['description'],
                category=wf['category'],
                version=wf.get('version', '1.0.0'),
                status=WorkflowStatus(wf.get('status', 'draft')),
                priority=WorkflowPriority(wf.get('priority', 'medium')),
                node_count=wf.get('node_count', 0),
                trigger_count=wf.get('trigger_count', 0),
                execution_count=wf.get('execution_count', 0),
                success_rate=wf.get('success_rate', 0.0),
                average_duration=wf.get('average_duration', 0.0),
                last_executed=wf.get('last_executed'),
                tags=wf.get('tags', []),
                created_at=wf['created_at'],
                updated_at=wf['updated_at'],
                created_by=wf.get('created_by', '')
            ))
        
        return WorkflowListResponse(
            workflows=workflow_responses,
            total_count=workflows.get('total_count', 0),
            page=page,
            page_size=page_size,
            total_pages=workflows.get('total_pages', 0)
        )
    
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get a specific workflow by ID"""
    try:
        workflow_def = workflow_engine.get_workflow(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Get additional data from enterprise manager
        enterprise_data = await enterprise_manager.get_workflow(workflow_id)
        
        return WorkflowResponse(
            id=workflow_def.workflow_id,
            name=workflow_def.name,
            description=workflow_def.description,
            category=enterprise_data.get('category', ''),
            version=workflow_def.version,
            status=WorkflowStatus(enterprise_data.get('status', 'draft')),
            priority=WorkflowPriority(enterprise_data.get('priority', 'medium')),
            node_count=len(workflow_def.nodes),
            trigger_count=len(workflow_def.triggers),
            execution_count=enterprise_data.get('execution_count', 0),
            success_rate=enterprise_data.get('success_rate', 0.0),
            average_duration=enterprise_data.get('average_duration', 0.0),
            last_executed=enterprise_data.get('last_executed'),
            tags=enterprise_data.get('tags', []),
            created_at=workflow_def.created_at,
            updated_at=workflow_def.updated_at,
            created_by=enterprise_data.get('created_by', '')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(
    workflow_id: str,
    workflow_update: WorkflowUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Update an existing workflow"""
    try:
        # Check if workflow exists
        workflow_def = workflow_engine.get_workflow(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Update workflow in enterprise manager
        updated_workflow = await enterprise_manager.update_workflow(
            workflow_id=workflow_id,
            updates=workflow_update.dict(exclude_unset=True),
            updated_by=current_user.id
        )
        
        # Broadcast update event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "workflow_updated",
                "workflow_id": workflow_id,
                "updated_by": current_user.email
            }
        )
        
        return WorkflowResponse(**updated_workflow)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),  # Admin only
    db = Depends(get_db)
):
    """Delete a workflow (admin only)"""
    try:
        # Check if workflow exists
        workflow_def = workflow_engine.get_workflow(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Delete from enterprise manager
        await enterprise_manager.delete_workflow(workflow_id, deleted_by=current_user.id)
        
        # Broadcast deletion event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "workflow_deleted",
                "workflow_id": workflow_id,
                "deleted_by": current_user.email
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Workflow Execution Endpoints

@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse, status_code=201)
async def execute_workflow(
    workflow_id: str,
    execute_request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Execute a workflow"""
    try:
        # Check if workflow exists
        workflow_def = workflow_engine.get_workflow(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Schedule execution if requested
        if execute_request.scheduled_for:
            # Implementation for scheduled execution would go here
            raise HTTPException(status_code=501, detail="Scheduled execution not yet implemented")
        
        # Execute workflow
        execution = await workflow_engine.execute_workflow(
            workflow_id=workflow_id,
            input_data=execute_request.input_data,
            context=execute_request.context
        )
        
        # Register execution with enterprise manager
        await enterprise_manager.register_execution(
            workflow_id=workflow_id,
            execution_id=execution.execution_id,
            started_by=current_user.id,
            priority=execute_request.priority.value
        )
        
        # Broadcast execution start event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "execution_started",
                "execution_id": execution.execution_id,
                "workflow_id": workflow_id,
                "started_by": current_user.email
            }
        )
        
        # Start background monitoring
        background_tasks.add_task(monitor_execution, execution.execution_id)
        
        return WorkflowExecutionResponse(
            id=execution.execution_id,
            workflow_id=execution.workflow_id,
            workflow_name=workflow_def.name,
            status=WorkflowStatus(execution.status.value),
            priority=execute_request.priority,
            progress=0.0,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration=None,
            node_states={k: NodeStatus(v.value) for k, v in execution.node_states.items()},
            results=execution.results,
            errors=execution.errors,
            metrics=execution.metrics,
            context=execution.context
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to execute workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{workflow_id}/executions", response_model=List[WorkflowExecutionResponse])
async def list_workflow_executions(
    workflow_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[WorkflowStatus] = Query(None),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """List executions for a specific workflow"""
    try:
        executions = await enterprise_manager.list_executions(
            workflow_id=workflow_id,
            user_id=current_user.id,
            status=status.value if status else None,
            page=page,
            page_size=page_size
        )
        
        return [
            WorkflowExecutionResponse(
                id=exec_data['id'],
                workflow_id=exec_data['workflow_id'],
                workflow_name=exec_data.get('workflow_name', ''),
                status=WorkflowStatus(exec_data['status']),
                priority=WorkflowPriority(exec_data.get('priority', 'medium')),
                progress=exec_data.get('progress', 0.0),
                started_at=exec_data['started_at'],
                completed_at=exec_data.get('completed_at'),
                duration=exec_data.get('duration'),
                node_states={k: NodeStatus(v) for k, v in exec_data.get('node_states', {}).items()},
                results=exec_data.get('results', {}),
                errors=exec_data.get('errors', []),
                metrics=exec_data.get('metrics', {}),
                context=exec_data.get('context', {})
            )
            for exec_data in executions
        ]
    
    except Exception as e:
        logger.error(f"Failed to list executions for workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get a specific execution by ID"""
    try:
        execution = workflow_engine.get_execution(execution_id)
        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")
        
        workflow_def = workflow_engine.get_workflow(execution.workflow_id)
        
        # Calculate progress
        total_nodes = len(execution.node_states)
        completed_nodes = sum(1 for status in execution.node_states.values() if status == NodeStatus.COMPLETED)
        progress = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
        
        # Get duration
        duration = None
        if execution.completed_at:
            duration = (execution.completed_at - execution.started_at).total_seconds()
        
        return WorkflowExecutionResponse(
            id=execution.execution_id,
            workflow_id=execution.workflow_id,
            workflow_name=workflow_def.name if workflow_def else '',
            status=WorkflowStatus(execution.status.value),
            priority=WorkflowPriority.MEDIUM,  # Default priority
            progress=progress,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            duration=duration,
            node_states={k: NodeStatus(v.value) for k, v in execution.node_states.items()},
            results=execution.results,
            errors=execution.errors,
            metrics=execution.metrics,
            context=execution.context
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/pause", status_code=204)
async def pause_execution(
    execution_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Pause a running execution"""
    try:
        workflow_engine.pause_execution(execution_id)
        
        # Broadcast pause event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "execution_paused",
                "execution_id": execution_id,
                "paused_by": current_user.email
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to pause execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/resume", status_code=204)
async def resume_execution(
    execution_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Resume a paused execution"""
    try:
        workflow_engine.resume_execution(execution_id)
        
        # Broadcast resume event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "execution_resumed",
                "execution_id": execution_id,
                "resumed_by": current_user.email
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to resume execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/executions/{execution_id}/cancel", status_code=204)
async def cancel_execution(
    execution_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Cancel a running execution"""
    try:
        workflow_engine.cancel_execution(execution_id)
        
        # Broadcast cancel event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "execution_cancelled",
                "execution_id": execution_id,
                "cancelled_by": current_user.email
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to cancel execution {execution_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Template Management Endpoints

@router.get("/templates", response_model=List[Dict[str, Any]])
async def list_templates(
    category: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """List available workflow templates"""
    try:
        templates = template_library.list_templates(
            category=category,
            difficulty=difficulty,
            search=search
        )
        
        return templates
    
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_id}", response_model=Dict[str, Any])
async def get_template(
    template_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific template by ID"""
    try:
        template = template_library.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        return template
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/templates/{template_id}/deploy", response_model=WorkflowResponse, status_code=201)
async def deploy_template(
    template_id: str,
    deploy_request: WorkflowTemplateDeployRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Deploy a workflow template as a new workflow"""
    try:
        # Get template
        template = template_library.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        
        # Deploy template
        workflow_def = await template_library.deploy_template(
            template_id=template_id,
            name=deploy_request.name,
            parameters=deploy_request.parameters,
            deployed_by=current_user.id
        )
        
        # Register with enterprise manager
        enterprise_workflow = await enterprise_manager.create_workflow(
            name=deploy_request.name,
            description=template.get('description', ''),
            category=WorkflowCategory(deploy_request.category.lower() if deploy_request.category else template.get('category', 'general').lower()),
            workflow_definition=workflow_def,
            created_by=current_user.id
        )
        
        # Broadcast deployment event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "template_deployed",
                "template_id": template_id,
                "workflow_id": workflow_def['workflow_id'],
                "deployed_by": current_user.email
            }
        )
        
        return WorkflowResponse(
            id=workflow_def['workflow_id'],
            name=deploy_request.name,
            description=template.get('description', ''),
            category=deploy_request.category or template.get('category', 'general'),
            version="1.0.0",
            status=WorkflowStatus.READY,
            priority=deploy_request.priority,
            node_count=template.get('node_count', 0),
            trigger_count=template.get('trigger_count', 0),
            execution_count=0,
            success_rate=0.0,
            average_duration=0.0,
            last_executed=None,
            tags=deploy_request.tags,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            created_by=current_user.email
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deploy template {template_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scheduling Endpoints

@router.post("/schedules", response_model=Dict[str, Any], status_code=201)
async def create_schedule(
    schedule: WorkflowScheduleCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Create a workflow schedule"""
    try:
        # Verify workflow exists
        workflow_def = workflow_engine.get_workflow(schedule.workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Create schedule
        schedule_data = await enterprise_manager.create_schedule(
            workflow_id=schedule.workflow_id,
            cron_expression=schedule.cron_expression,
            timezone=schedule.timezone,
            is_active=schedule.is_active,
            max_runs=schedule.max_runs,
            start_date=schedule.start_date,
            end_date=schedule.end_date,
            created_by=current_user.id
        )
        
        # Broadcast schedule creation event
        background_tasks.add_task(
            manager.broadcast,
            {
                "type": "schedule_created",
                "schedule_id": schedule_data['id'],
                "workflow_id": schedule.workflow_id,
                "created_by": current_user.email
            }
        )
        
        return schedule_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics and Metrics Endpoints

@router.get("/metrics", response_model=WorkflowMetricsResponse)
async def get_workflow_metrics(
    days_back: int = Query(30, ge=1, le=365),
    category: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db = Depends(get_db)
):
    """Get workflow execution metrics and analytics"""
    try:
        metrics = await enterprise_manager.get_metrics(
            user_id=current_user.id,
            days_back=days_back,
            category=category
        )
        
        return WorkflowMetricsResponse(**metrics)
    
    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(get_current_user)
):
    """Get system health metrics"""
    try:
        # This would typically get real system metrics
        # For now, return mock data
        health_data = {
            "status": "healthy",
            "cpu_usage": 35.2,
            "memory_usage": 67.8,
            "disk_usage": 45.3,
            "network_latency": 23.4,
            "active_executions": 12,
            "queue_length": 3,
            "worker_nodes": 5,
            "timestamp": datetime.now()
        }
        
        return SystemHealthResponse(**health_data)
    
    except Exception as e:
        logger.error(f"Failed to get system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# WebSocket endpoint for real-time updates

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time workflow updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Background task for monitoring executions
async def monitor_execution(execution_id: str):
    """Monitor execution progress and broadcast updates"""
    try:
        while True:
            execution = workflow_engine.get_execution(execution_id)
            if not execution:
                break
            
            # Calculate progress
            total_nodes = len(execution.node_states)
            completed_nodes = sum(1 for status in execution.node_states.values() if status == NodeStatus.COMPLETED)
            progress = (completed_nodes / total_nodes * 100) if total_nodes > 0 else 0
            
            # Broadcast progress update
            await manager.broadcast({
                "type": "execution_progress",
                "execution_id": execution_id,
                "progress": progress,
                "status": execution.status.value,
                "node_states": {k: v.value for k, v in execution.node_states.items()}
            })
            
            # Stop monitoring if execution is complete
            if execution.status.value in ['completed', 'failed', 'cancelled']:
                await manager.broadcast({
                    "type": "execution_finished",
                    "execution_id": execution_id,
                    "final_status": execution.status.value,
                    "duration": (datetime.now() - execution.started_at).total_seconds() if execution.completed_at else None
                })
                break
            
            # Wait before next check
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"Error monitoring execution {execution_id}: {e}")

# Export workflow data endpoint
@router.get("/{workflow_id}/export")
async def export_workflow(
    workflow_id: str,
    format: str = Query("yaml", regex="^(yaml|json)$"),
    current_user: User = Depends(get_current_user)
):
    """Export workflow definition in YAML or JSON format"""
    try:
        workflow_def = workflow_engine.get_workflow(workflow_id)
        if not workflow_def:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        # Export using WorkflowEngine
        exported_data = workflow_engine.export_workflow(workflow_id, format=format)
        
        # Set content type and filename based on format
        content_type = "application/x-yaml" if format == "yaml" else "application/json"
        filename = f"workflow_{workflow_id}.{format}"
        
        return StreamingResponse(
            io.BytesIO(exported_data.encode()),
            media_type=content_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export workflow {workflow_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))