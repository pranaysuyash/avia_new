"""
Named Entity Recognition API Endpoints
FastAPI endpoints for NER functionality
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime

from api.auth_middleware import get_current_user
from database.connection import get_db
from sqlalchemy.orm import Session

# Import NER functionality
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import ner_basic
import ner_advanced

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ner")

# Pydantic models
class NERRequest(BaseModel):
    text: str = Field(..., description="Text to extract entities from")
    entity_types: Optional[List[str]] = Field(
        default=None,
        description="Specific entity types to extract (if None, extract all)"
    )
    advanced_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Advanced NER options"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California on April 1, 1976.",
                "entity_types": ["PERSON", "ORG", "LOC", "DATE"],
                "advanced_options": {
                    "confidence_threshold": 0.8,
                    "merge_entities": True
                }
            }
        }

class Entity(BaseModel):
    text: str
    type: str
    start: int
    end: int
    confidence: float

class NERResponse(BaseModel):
    success: bool
    entities: List[Entity]
    processing_time: float
    metadata: Optional[Dict[str, Any]] = None

@router.post("/extract", response_model=NERResponse)
async def extract_entities(
    request: NERRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract named entities from text
    
    Supports various entity types including:
    - PERSON: People names
    - ORG: Organizations
    - LOC: Locations
    - DATE: Dates
    - TIME: Times
    - MONEY: Monetary values
    - PERCENT: Percentages
    - And more...
    """
    try:
        start_time = datetime.now()
        
        # Use basic or advanced NER based on options
        if request.advanced_options:
            # Use advanced NER
            results = ner_advanced.extract_entities_advanced(
                request.text,
                request.advanced_options
            )
            entities_data = results.get("entities", [])
        else:
            # Use basic NER
            entities_data = ner_basic.extract_entities(
                request.text,
                entity_types=request.entity_types
            )
        
        # Convert to response format
        entities = []
        for entity in entities_data:
            entities.append(Entity(
                text=entity.get("text", ""),
                type=entity.get("type", "UNKNOWN"),
                start=entity.get("start", 0),
                end=entity.get("end", 0),
                confidence=entity.get("confidence", 1.0)
            ))
        
        # Filter by requested entity types if specified
        if request.entity_types:
            entities = [e for e in entities if e.type in request.entity_types]
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return NERResponse(
            success=True,
            entities=entities,
            processing_time=processing_time,
            metadata={
                "total_entities": len(entities),
                "entity_types": list(set(e.type for e in entities)),
                "text_length": len(request.text)
            }
        )
        
    except Exception as e:
        logger.error(f"NER error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract entities: {str(e)}"
        )

@router.get("/entity-types")
async def get_entity_types(
    current_user: dict = Depends(get_current_user)
):
    """Get list of supported entity types"""
    try:
        # Standard spaCy entity types
        entity_types = [
            {"code": "PERSON", "name": "Person", "description": "People, including fictional"},
            {"code": "NORP", "name": "Nationalities/Groups", "description": "Nationalities, religious or political groups"},
            {"code": "FAC", "name": "Facility", "description": "Buildings, airports, highways, bridges, etc."},
            {"code": "ORG", "name": "Organization", "description": "Companies, agencies, institutions, etc."},
            {"code": "GPE", "name": "Geopolitical Entity", "description": "Countries, cities, states"},
            {"code": "LOC", "name": "Location", "description": "Non-GPE locations, mountain ranges, bodies of water"},
            {"code": "PRODUCT", "name": "Product", "description": "Objects, vehicles, foods, etc."},
            {"code": "EVENT", "name": "Event", "description": "Named hurricanes, battles, wars, sports events, etc."},
            {"code": "WORK_OF_ART", "name": "Work of Art", "description": "Titles of books, songs, etc."},
            {"code": "LAW", "name": "Law", "description": "Named documents made into laws"},
            {"code": "LANGUAGE", "name": "Language", "description": "Any named language"},
            {"code": "DATE", "name": "Date", "description": "Absolute or relative dates or periods"},
            {"code": "TIME", "name": "Time", "description": "Times smaller than a day"},
            {"code": "PERCENT", "name": "Percentage", "description": "Percentage, including '%'"},
            {"code": "MONEY", "name": "Money", "description": "Monetary values, including unit"},
            {"code": "QUANTITY", "name": "Quantity", "description": "Measurements, as of weight or distance"},
            {"code": "ORDINAL", "name": "Ordinal", "description": "First, second, etc."},
            {"code": "CARDINAL", "name": "Cardinal", "description": "Numerals that do not fall under another type"}
        ]
        
        return {"entity_types": entity_types}
        
    except Exception as e:
        logger.error(f"Error getting entity types: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get entity types: {str(e)}"
        )

@router.post("/batch/extract")
async def batch_extract_entities(
    texts: List[str],
    entity_types: Optional[List[str]] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Batch extract entities from multiple texts
    
    Admin only endpoint
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if len(texts) > 100:
        raise HTTPException(
            status_code=400,
            detail="Maximum 100 texts per batch"
        )
    
    results = []
    
    for i, text in enumerate(texts):
        try:
            request = NERRequest(text=text, entity_types=entity_types)
            response = await extract_entities(request, current_user, None)
            
            results.append({
                "index": i,
                "success": True,
                "entities": response.entities,
                "entity_count": len(response.entities)
            })
            
        except Exception as e:
            results.append({
                "index": i,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(texts),
        "successful": sum(1 for r in results if r['success']),
        "failed": sum(1 for r in results if not r['success']),
        "results": results
    }

@router.post("/analyze")
async def analyze_entity_distribution(
    text: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze entity distribution in text
    
    Returns statistics about entity types and their frequency
    """
    try:
        # Extract entities
        entities = ner_basic.extract_entities(text)
        
        # Calculate statistics
        entity_stats = {}
        for entity in entities:
            entity_type = entity.get("type", "UNKNOWN")
            if entity_type not in entity_stats:
                entity_stats[entity_type] = {
                    "count": 0,
                    "examples": [],
                    "percentage": 0
                }
            
            entity_stats[entity_type]["count"] += 1
            if len(entity_stats[entity_type]["examples"]) < 5:
                entity_stats[entity_type]["examples"].append(entity.get("text", ""))
        
        # Calculate percentages
        total_entities = len(entities)
        for entity_type in entity_stats:
            entity_stats[entity_type]["percentage"] = (
                entity_stats[entity_type]["count"] / total_entities * 100
                if total_entities > 0 else 0
            )
        
        return {
            "total_entities": total_entities,
            "unique_entities": len(set(e.get("text", "") for e in entities)),
            "entity_types": len(entity_stats),
            "distribution": entity_stats,
            "text_length": len(text),
            "entity_density": total_entities / len(text.split()) if text else 0
        }
        
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to analyze entities: {str(e)}"
        )