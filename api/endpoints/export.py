"""
Export API Endpoints
REST API for exporting transcriptions and entities in various formats
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional, List, Dict, Any
import logging
import json
import csv
import io
from datetime import datetime
from pydantic import BaseModel

from api.dependencies import auth_required, create_api_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])

# Data models
class ExportRequest(BaseModel):
    format: str  # json, csv, txt
    include_timestamps: bool = True
    include_confidence: bool = False
    include_entities: bool = True

@router.post("/transcription/{transcription_id}")
async def export_transcription(
    transcription_id: str = Path(...),
    export_request: ExportRequest = None,
    user_id: str = "test_user"
):
    """Export a single transcription in the specified format"""
    try:
        if not transcription_id.startswith("transcript_"):
            raise HTTPException(status_code=404, detail="Transcription not found")
        
        # Mock transcription data
        data = {
            "id": transcription_id,
            "title": f"Transcription {transcription_id.split('_')[1]}",
            "transcript": "Sample transcription text with entities like John Smith and Microsoft.",
            "entities": {
                "PERSON": ["John Smith"],
                "ORG": ["Microsoft"]
            },
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Sample transcription text", "confidence": 0.95}
            ]
        }
        
        if export_request.format == "json":
            content = json.dumps(data, indent=2)
            media_type = "application/json"
            filename = f"{transcription_id}.json"
        elif export_request.format == "csv":
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Start", "End", "Text", "Confidence"])
            for segment in data["segments"]:
                writer.writerow([segment["start"], segment["end"], segment["text"], segment["confidence"]])
            content = output.getvalue()
            media_type = "text/csv"
            filename = f"{transcription_id}.csv"
        else:
            raise HTTPException(status_code=400, detail="Unsupported format")
        
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export transcription: {e}")
        raise HTTPException(status_code=500, detail="Failed to export transcription")

@router.get("/formats")
async def get_supported_export_formats():
    """Get list of supported export formats"""
    try:
        formats = [
            {"format": "json", "name": "JSON", "description": "JavaScript Object Notation"},
            {"format": "csv", "name": "CSV", "description": "Comma-separated values"}
        ]
        
        return create_api_response(formats, "Export formats retrieved successfully")
        
    except Exception as e:
        logger.error(f"Failed to get export formats: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve export formats")