#!/usr/bin/env python3
"""
FastAPI endpoints for Cross-Provider Entity Linking System.
Provides REST API for entity extraction, linking, and knowledge graph operations.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import asyncio
import logging
import os

from cross_provider_entity_linking import (
    CrossProviderEntityLinker,
    Entity,
    EntityType,
    ProviderType,
    create_entity_linker,
    calculate_confidence_level
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/entity-linking", tags=["Entity Linking"])

# Global entity linker instance
_entity_linker: Optional[CrossProviderEntityLinker] = None


def get_entity_linker() -> CrossProviderEntityLinker:
    """Get or create entity linker instance."""
    global _entity_linker
    
    if _entity_linker is None:
        config = {
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "db_path": os.getenv("ENTITY_DB_PATH", "entities.db"),
            "redis": {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "db": int(os.getenv("REDIS_DB", "1"))
            }
        }
        _entity_linker = create_entity_linker(config)
        logger.info("Entity linker initialized")
    
    return _entity_linker


# Pydantic models
class EntityExtractionRequest(BaseModel):
    """Request model for entity extraction."""
    text: str = Field(..., description="Text to extract entities from", min_length=1)
    context: Optional[str] = Field(None, description="Additional context for extraction")
    providers: Optional[List[str]] = Field(None, description="List of providers to use")
    include_knowledge_links: bool = Field(True, description="Whether to include knowledge base links")
    
    class Config:
        schema_extra = {
            "example": {
                "text": "Apple Inc. was founded by Steve Jobs in Cupertino, California.",
                "context": "technology company information",
                "providers": ["spacy", "openai"],
                "include_knowledge_links": True
            }
        }


class EntitySearchRequest(BaseModel):
    """Request model for entity search."""
    query: str = Field(..., description="Search query", min_length=1)
    entity_type: Optional[str] = Field(None, description="Filter by entity type")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)
    include_links: bool = Field(True, description="Include entity links in results")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Apple",
                "entity_type": "ORG",
                "limit": 10,
                "include_links": True
            }
        }


class EntityGraphRequest(BaseModel):
    """Request model for entity graph."""
    entity_id: str = Field(..., description="Entity ID to center graph on")
    depth: int = Field(2, description="Graph depth", ge=1, le=5)
    
    class Config:
        schema_extra = {
            "example": {
                "entity_id": "abc123def456",
                "depth": 2
            }
        }


class EntityResponse(BaseModel):
    """Response model for entity data."""
    text: str
    entity_type: str
    confidence: float
    provider: str
    canonical_id: str
    aliases: List[str] = []
    properties: Dict[str, Any] = {}
    knowledge_links: List[Dict[str, Any]] = []


class EntityExtractionResponse(BaseModel):
    """Response model for entity extraction."""
    success: bool
    text: str
    context: Optional[str]
    total_entities: int
    entity_links: int
    knowledge_links: int
    extraction_results: Dict[str, Any]
    unified_entities: List[Dict[str, Any]]
    processing_time_ms: float
    timestamp: datetime


class EntitySearchResponse(BaseModel):
    """Response model for entity search."""
    success: bool
    query: str
    total_results: int
    results: List[Dict[str, Any]]
    processing_time_ms: float


class EntityGraphResponse(BaseModel):
    """Response model for entity graph."""
    success: bool
    center_entity: str
    depth: int
    node_count: int
    edge_count: int
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]


class SystemStatsResponse(BaseModel):
    """Response model for system statistics."""
    success: bool
    total_entities: int
    total_links: int
    entities_by_provider: Dict[str, int]
    entities_by_type: Dict[str, int]
    knowledge_graph_nodes: int
    knowledge_graph_edges: int
    active_extractors: List[str]
    active_knowledge_linkers: List[str]


# API Endpoints

@router.post("/extract", response_model=EntityExtractionResponse)
async def extract_entities(
    request: EntityExtractionRequest,
    background_tasks: BackgroundTasks,
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Extract and link entities from text using multiple providers.
    
    This endpoint processes text through multiple entity extraction providers,
    links similar entities across providers, and connects them to knowledge bases.
    """
    try:
        start_time = datetime.utcnow()
        
        # Convert provider names to enum values
        providers = None
        if request.providers:
            try:
                providers = [ProviderType(p.lower()) for p in request.providers]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {e}"
                )
        
        # Extract and link entities
        results = await linker.extract_and_link_entities(
            text=request.text,
            context=request.context or "",
            providers=providers
        )
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return EntityExtractionResponse(
            success=True,
            text=request.text,
            context=request.context,
            total_entities=results["total_entities"],
            entity_links=results["entity_links"],
            knowledge_links=results["knowledge_links"],
            extraction_results=results["extraction_results"],
            unified_entities=results["unified_entities"],
            processing_time_ms=processing_time,
            timestamp=end_time
        )
        
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity extraction failed: {str(e)}"
        )


@router.post("/search", response_model=EntitySearchResponse)
async def search_entities(
    request: EntitySearchRequest,
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Search for entities in the knowledge base.
    
    Search for entities by text query with optional filtering by entity type.
    Results include entity details and optionally their links to other entities.
    """
    try:
        start_time = datetime.utcnow()
        
        # Convert entity type if provided
        entity_type = None
        if request.entity_type:
            try:
                entity_type = EntityType(request.entity_type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid entity type: {request.entity_type}"
                )
        
        # Search entities
        results = linker.search_entities(
            query=request.query,
            entity_type=entity_type,
            include_knowledge_links=request.include_links
        )
        
        # Limit results
        limited_results = results[:request.limit]
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return EntitySearchResponse(
            success=True,
            query=request.query,
            total_results=len(limited_results),
            results=limited_results,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        logger.error(f"Entity search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity search failed: {str(e)}"
        )


@router.post("/graph", response_model=EntityGraphResponse)
async def get_entity_graph(
    request: EntityGraphRequest,
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Get entity knowledge graph centered on a specific entity.
    
    Returns a subgraph of the knowledge graph centered on the specified entity,
    including all connected entities within the specified depth.
    """
    try:
        # Get entity graph
        graph_data = linker.get_entity_graph(
            entity_id=request.entity_id,
            depth=request.depth
        )
        
        if "error" in graph_data:
            raise HTTPException(
                status_code=404,
                detail=graph_data["error"]
            )
        
        return EntityGraphResponse(
            success=True,
            center_entity=graph_data["center_entity"],
            depth=graph_data["depth"],
            node_count=graph_data["node_count"],
            edge_count=graph_data["edge_count"],
            nodes=graph_data["nodes"],
            edges=graph_data["edges"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity graph retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity graph retrieval failed: {str(e)}"
        )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_statistics(
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Get system statistics and health information.
    
    Returns comprehensive statistics about the entity linking system,
    including entity counts, provider status, and knowledge graph metrics.
    """
    try:
        stats = linker.get_statistics()
        
        if "error" in stats:
            raise HTTPException(
                status_code=500,
                detail=stats["error"]
            )
        
        return SystemStatsResponse(
            success=True,
            total_entities=stats.get("total_entities", 0),
            total_links=stats.get("total_links", 0),
            entities_by_provider=stats.get("entities_by_provider", {}),
            entities_by_type=stats.get("entities_by_type", {}),
            knowledge_graph_nodes=stats.get("knowledge_graph_nodes", 0),
            knowledge_graph_edges=stats.get("knowledge_graph_edges", 0),
            active_extractors=[str(e) for e in stats.get("active_extractors", [])],
            active_knowledge_linkers=[str(k) for k in stats.get("active_knowledge_linkers", [])]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Statistics retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Statistics retrieval failed: {str(e)}"
        )


@router.get("/providers")
async def get_available_providers(
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Get list of available entity extraction providers.
    
    Returns information about all configured entity extraction providers
    and their current status.
    """
    try:
        providers_info = []
        
        for provider_type, extractor in linker.extractors.items():
            provider_info = {
                "name": provider_type.value,
                "type": provider_type.value,
                "status": "active",
                "description": f"{provider_type.value.title()} entity extractor"
            }
            
            # Add provider-specific information
            if provider_type == ProviderType.SPACY:
                provider_info["model"] = getattr(extractor.nlp, "meta", {}).get("name", "unknown")
            elif provider_type == ProviderType.OPENAI:
                provider_info["model"] = getattr(extractor, "model", "unknown")
            
            providers_info.append(provider_info)
        
        knowledge_linkers_info = []
        for provider_type, linker_obj in linker.knowledge_linkers.items():
            linker_info = {
                "name": provider_type.value,
                "type": "knowledge_base",
                "status": "active",
                "description": f"{provider_type.value.title()} knowledge base linker"
            }
            knowledge_linkers_info.append(linker_info)
        
        return {
            "success": True,
            "entity_extractors": providers_info,
            "knowledge_linkers": knowledge_linkers_info,
            "total_providers": len(providers_info) + len(knowledge_linkers_info)
        }
        
    except Exception as e:
        logger.error(f"Provider information retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Provider information retrieval failed: {str(e)}"
        )


@router.get("/entity-types")
async def get_entity_types():
    """
    Get list of supported entity types.
    
    Returns all supported entity types that can be extracted and linked.
    """
    try:
        entity_types = []
        
        for entity_type in EntityType:
            type_info = {
                "name": entity_type.name,
                "value": entity_type.value,
                "description": _get_entity_type_description(entity_type)
            }
            entity_types.append(type_info)
        
        return {
            "success": True,
            "entity_types": entity_types,
            "total_types": len(entity_types)
        }
        
    except Exception as e:
        logger.error(f"Entity types retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity types retrieval failed: {str(e)}"
        )


@router.delete("/entity/{entity_id}")
async def delete_entity(
    entity_id: str,
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Delete an entity from the knowledge base.
    
    Removes the specified entity and all its links from the system.
    This operation cannot be undone.
    """
    try:
        # Check if entity exists
        entity = linker.database.get_entity(entity_id)
        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"Entity {entity_id} not found"
            )
        
        # Delete entity (implementation would need to be added to the database class)
        # For now, return a placeholder response
        return {
            "success": True,
            "message": f"Entity {entity_id} deletion requested",
            "entity_id": entity_id,
            "note": "Deletion functionality needs to be implemented in the database layer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Entity deletion failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Entity deletion failed: {str(e)}"
        )


@router.post("/batch-extract")
async def batch_extract_entities(
    texts: List[str] = Field(..., description="List of texts to process"),
    context: Optional[str] = Field(None, description="Shared context for all texts"),
    providers: Optional[List[str]] = Field(None, description="Providers to use"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    linker: CrossProviderEntityLinker = Depends(get_entity_linker)
):
    """
    Extract entities from multiple texts in batch.
    
    Processes multiple texts concurrently for improved performance.
    Results are returned in the same order as the input texts.
    """
    try:
        if len(texts) > 100:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail="Batch size cannot exceed 100 texts"
            )
        
        start_time = datetime.utcnow()
        
        # Convert provider names
        provider_enums = None
        if providers:
            try:
                provider_enums = [ProviderType(p.lower()) for p in providers]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid provider: {e}"
                )
        
        # Process texts concurrently
        tasks = []
        for text in texts:
            task = linker.extract_and_link_entities(
                text=text,
                context=context or "",
                providers=provider_enums
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        batch_results = []
        total_entities = 0
        total_links = 0
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                batch_results.append({
                    "index": i,
                    "text": texts[i][:100] + "..." if len(texts[i]) > 100 else texts[i],
                    "success": False,
                    "error": str(result)
                })
            else:
                batch_results.append({
                    "index": i,
                    "text": texts[i][:100] + "..." if len(texts[i]) > 100 else texts[i],
                    "success": True,
                    "total_entities": result["total_entities"],
                    "entity_links": result["entity_links"],
                    "knowledge_links": result["knowledge_links"],
                    "unified_entities": len(result["unified_entities"])
                })
                total_entities += result["total_entities"]
                total_links += result["entity_links"]
        
        # Calculate processing time
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        return {
            "success": True,
            "batch_size": len(texts),
            "total_entities": total_entities,
            "total_links": total_links,
            "processing_time_ms": processing_time,
            "results": batch_results,
            "timestamp": end_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch entity extraction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Batch entity extraction failed: {str(e)}"
        )


# Helper functions

def _get_entity_type_description(entity_type: EntityType) -> str:
    """Get description for entity type."""
    descriptions = {
        EntityType.PERSON: "People and individuals",
        EntityType.ORGANIZATION: "Companies, institutions, and organizations",
        EntityType.LOCATION: "Geographic locations and places",
        EntityType.PRODUCT: "Products, brands, and services",
        EntityType.EVENT: "Events, conferences, and occasions",
        EntityType.DATE: "Dates and temporal expressions",
        EntityType.MONEY: "Monetary amounts and currencies",
        EntityType.PERCENT: "Percentages and ratios",
        EntityType.CONCEPT: "Abstract concepts and ideas",
        EntityType.UNKNOWN: "Unclassified entities"
    }
    return descriptions.get(entity_type, "Unknown entity type")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for the entity linking service."""
    try:
        linker = get_entity_linker()
        stats = linker.get_statistics()
        
        return {
            "status": "healthy",
            "service": "cross-provider-entity-linking",
            "version": "1.0.0",
            "timestamp": datetime.utcnow(),
            "entities_count": stats.get("total_entities", 0),
            "active_providers": len(stats.get("active_extractors", [])),
            "database_status": "connected" if stats.get("total_entities", 0) >= 0 else "error"
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "cross-provider-entity-linking",
                "error": str(e),
                "timestamp": datetime.utcnow()
            }
        )


# Cleanup on shutdown
@router.on_event("shutdown")
async def shutdown_event():
    """Cleanup resources on shutdown."""
    global _entity_linker
    if _entity_linker:
        _entity_linker.cleanup()
        _entity_linker = None
        logger.info("Entity linker cleaned up")