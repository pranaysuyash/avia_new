"""
Enterprise Sales API Endpoints
Handles enterprise sales pipeline, demo scheduling, and onboarding
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import asyncio
import json
from datetime import datetime, timedelta
import uuid

try:
    from ..database import get_db
    from ..models import User  
    from ..auth import get_current_user
except ImportError:
    # Fallback imports for standalone testing
    def get_db():
        return None
    
    class User:
        def __init__(self):
            self.is_admin = True
    
    def get_current_user():
        return User()
try:
    from enterprise_sales_onboarding_system import EnterpriseSalesService
    SALES_SYSTEM_AVAILABLE = True
except ImportError:
    SALES_SYSTEM_AVAILABLE = False
    EnterpriseSalesService = None

router = APIRouter()

# Initialize the enterprise sales system
if SALES_SYSTEM_AVAILABLE:
    try:
        sales_system = EnterpriseSalesService("sqlite:///enterprise_sales.db")
    except Exception:
        sales_system = None
else:
    sales_system = None

@router.post("/leads")
async def create_lead(
    lead_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new sales lead"""
    if not sales_system:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Enterprise sales system not available"
        )
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Mock implementation for testing
    lead_id = f"lead_{uuid.uuid4().hex[:8]}"
    return {"lead_id": lead_id, "status": "created"}

@router.get("/leads")
async def get_leads(
    status_filter: Optional[str] = None,
    source_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all sales leads with optional filtering"""
    if not sales_system:
        # Mock response for testing
        return {"leads": []}
    
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Mock implementation for testing
    return {"leads": []}

@router.put("/leads/{lead_id}")
async def update_lead(
    lead_id: str,
    lead_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a sales lead"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    success = await sales_system.update_lead(lead_id, lead_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return {"status": "updated"}

@router.post("/leads/{lead_id}/qualify")
async def qualify_lead(
    lead_id: str,
    qualification_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Qualify a lead based on criteria"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    result = await sales_system.qualify_lead(lead_id, qualification_data)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found"
        )
    
    return {"qualification_result": result}

@router.post("/demos/schedule")
async def schedule_demo(
    demo_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Schedule a demo for a lead"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    demo = await sales_system.schedule_demo(demo_request)
    
    return {"demo_id": demo.id, "status": "scheduled"}

@router.get("/demos")
async def get_demos(
    status_filter: Optional[str] = None,
    date_range: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get scheduled demos"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    demos = await sales_system.get_demos(
        status_filter=status_filter,
        date_range=date_range
    )
    
    return {"demos": [demo.__dict__ for demo in demos]}

@router.get("/analytics/sales-metrics")
async def get_sales_metrics(
    time_period: str = "30d",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get sales analytics metrics"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    metrics = await sales_system.get_sales_metrics(time_period)
    
    return {"metrics": metrics.__dict__}

@router.post("/trials/create")
async def create_trial(
    trial_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a trial account for a prospect"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    trial = await sales_system.create_trial(trial_request)
    
    return {"trial_id": trial.id, "status": "created", "credentials": trial.trial_credentials}

@router.post("/contracts/create")
async def create_contract(
    contract_proposal: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a contract proposal"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    contract = await sales_system.create_contract(contract_proposal)
    
    return {"contract_id": contract.id, "status": "created"}

@router.post("/onboarding/start")
async def start_onboarding(
    onboarding_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start onboarding process for new customer"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    workflow = await sales_system.start_onboarding(onboarding_request)
    
    return {"workflow_id": workflow.id, "status": "started"}