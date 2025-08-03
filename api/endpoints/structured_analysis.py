# API endpoints for structured analysis functionality
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
from auth.auth_manager import get_current_user

from structured_analysis import (
    structured_analyzer, get_available_templates, analyze_with_schema,
    validate_analysis_result, export_analysis, AnalysisResult
)
from errors import NERError, APIError

router = APIRouter(prefix="/structured-analysis", tags=["structured-analysis"])

class AnalysisRequest(BaseModel):
    text: str
    template_name: str
    options: Optional[Dict[str, Any]] = None

class ExportRequest(BaseModel):
    result: Dict[str, Any]
    format: str = "json"

@router.get("/templates")
async def list_templates(current_user: dict = Depends(get_current_user)):
    """Get all available analysis templates"""
    try:
        templates = get_available_templates()
        return {"templates": templates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/templates/{template_name}")
async def get_template(template_name: str, current_user: dict = Depends(get_current_user)):
    """Get a specific template with its schema"""
    try:
        template = structured_analyzer.get_template(template_name)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
        
        return {
            "name": template.name,
            "description": template.description,
            "domain": template.domain,
            "schema": template.schema
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze")
async def analyze_content(request: AnalysisRequest, current_user: dict = Depends(get_current_user)):
    """Perform structured analysis on text"""
    try:
        # Perform analysis
        result_dict = analyze_with_schema(request.text, request.template_name, request.options)
        return result_dict
    except (NERError, APIError) as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": e.user_message,
                "error_type": type(e).__name__,
                "suggestions": getattr(e, 'suggestions', [])
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_result(data: Dict[str, Any], template_name: str, current_user: dict = Depends(get_current_user)):
    """Validate analysis result against template schema"""
    try:
        errors = validate_analysis_result(data, template_name)
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/export")
async def export_result(request: ExportRequest, current_user: dict = Depends(get_current_user)):
    """Export analysis result in specified format"""
    try:
        # Convert dict to AnalysisResult object
        result = AnalysisResult(**request.result)
        exported_data = export_analysis(result, request.format)
        
        return exported_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/custom-template")
async def create_custom_template(
    name: str,
    description: str,
    domain: str,
    schema: Dict[str, Any],
    prompt_template: str,
    current_user: dict = Depends(get_current_user)
):
    """Create a custom analysis template"""
    try:
        # Only admins can create custom templates
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Only admins can create custom templates")
        
        template = structured_analyzer.create_custom_template(
            name=name,
            description=description,
            domain=domain,
            schema=schema,
            prompt_template=prompt_template
        )
        
        return {"message": f"Template '{name}' created successfully", "template": template}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))