"""
OCR API Endpoints
FastAPI endpoints for Optical Character Recognition
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import base64
import tempfile
import os
import logging
from datetime import datetime

from api.auth_middleware import get_current_user
from database.connection import get_db
from sqlalchemy.orm import Session

# Import OCR functionality
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from image_ocr_processor import (
    OCRManager, OCRResult, DocumentResult,
    validate_image_file, estimate_processing_time
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/ocr")

# Initialize OCR manager
ocr_manager = OCRManager()

# Pydantic models
class OCRRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image data")
    language: str = Field(default="en", description="Language code for OCR")
    extract_tables: bool = Field(default=True, description="Extract tables from document")
    enhance_image: bool = Field(default=True, description="Apply image enhancement")
    
    class Config:
        json_schema_extra = {
            "example": {
                "image_data": "base64_encoded_image_here",
                "language": "en",
                "extract_tables": True,
                "enhance_image": True
            }
        }

class BoundingBox(BaseModel):
    text: str
    confidence: float
    x: int
    y: int
    width: int
    height: int

class OCRResponse(BaseModel):
    text: str
    confidence: float
    language: str
    processing_time: float
    word_count: int
    line_count: int
    bounding_boxes: Optional[List[BoundingBox]] = None
    tables: Optional[List[Dict[str, Any]]] = None

@router.post("/extract", response_model=OCRResponse)
async def extract_text_from_image(
    request: OCRRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extract text from image using OCR
    
    Supports multiple languages and table extraction
    """
    try:
        start_time = datetime.now()
        
        # Decode image data
        image_bytes = base64.b64decode(request.image_data)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
            tmp_file.write(image_bytes)
            tmp_path = tmp_file.name
        
        try:
            # Validate image
            is_valid, error_msg = validate_image_file(tmp_path)
            if not is_valid:
                raise HTTPException(status_code=400, detail=error_msg)
            
            # Process OCR
            result = await ocr_manager.process_image(
                tmp_path,
                language=request.language,
                extract_tables=request.extract_tables,
                enhance_contrast=request.enhance_image,
                denoise_image=request.enhance_image,
                deskew_image=request.enhance_image
            )
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Format response
            response = OCRResponse(
                text=result.text,
                confidence=result.confidence,
                language=result.language,
                processing_time=processing_time,
                word_count=result.word_count,
                line_count=result.line_count
            )
            
            # Add bounding boxes if available
            if result.bounding_boxes:
                response.bounding_boxes = [
                    BoundingBox(
                        text=box['text'],
                        confidence=box['confidence'],
                        x=box['bbox'][0],
                        y=box['bbox'][1],
                        width=box['bbox'][2] - box['bbox'][0],
                        height=box['bbox'][3] - box['bbox'][1]
                    )
                    for box in result.bounding_boxes
                ]
            
            # Add tables if extracted
            if hasattr(result, 'tables') and result.tables:
                response.tables = result.tables
            
            return response
            
        finally:
            # Clean up
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"OCR error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to extract text: {str(e)}"
        )

@router.post("/extract/file")
async def extract_text_from_file(
    file: UploadFile = File(...),
    language: str = Form("en"),
    extract_tables: bool = Form(True),
    enhance_image: bool = Form(True),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract text from uploaded image file
    
    Direct file upload endpoint
    """
    try:
        # Check file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="File must be an image"
            )
        
        # Read file content
        content = await file.read()
        
        # Create OCR request
        request = OCRRequest(
            image_data=base64.b64encode(content).decode('utf-8'),
            language=language,
            extract_tables=extract_tables,
            enhance_image=enhance_image
        )
        
        # Process OCR
        response = await extract_text_from_image(request, current_user, None)
        
        return response
        
    except Exception as e:
        logger.error(f"File OCR error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process file: {str(e)}"
        )

@router.post("/extract/document")
async def extract_text_from_document(
    file: UploadFile = File(...),
    language: str = Form("en"),
    current_user: dict = Depends(get_current_user)
):
    """
    Extract text from multi-page document (PDF)
    
    Returns text from all pages
    """
    try:
        if not file.content_type == 'application/pdf':
            raise HTTPException(
                status_code=400,
                detail="File must be a PDF document"
            )
        
        # Read file content
        content = await file.read()
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Process document
            result = await ocr_manager.process_document(
                tmp_path,
                language=language
            )
            
            return {
                "filename": file.filename,
                "total_pages": result.total_pages,
                "pages": [
                    {
                        "page_number": page.page_number,
                        "text": page.text,
                        "confidence": page.confidence,
                        "word_count": page.word_count,
                        "line_count": page.line_count,
                        "has_tables": bool(page.tables),
                        "tables": page.tables
                    }
                    for page in result.pages
                ],
                "full_text": result.full_text,
                "total_confidence": result.total_confidence,
                "total_processing_time": result.total_processing_time
            }
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    except Exception as e:
        logger.error(f"Document OCR error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )

@router.get("/languages")
async def get_supported_languages(
    current_user: dict = Depends(get_current_user)
):
    """Get list of supported OCR languages"""
    try:
        languages = ocr_manager.get_supported_languages()
        return {
            "languages": [
                {"code": code, "name": name}
                for code, name in languages.items()
            ]
        }
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get languages: {str(e)}"
        )

@router.post("/batch/extract")
async def batch_extract_text(
    files: List[UploadFile] = File(...),
    language: str = Form("en"),
    current_user: dict = Depends(get_current_user)
):
    """
    Batch extract text from multiple images
    
    Admin only endpoint
    """
    if current_user['role'] != 'admin':
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if len(files) > 20:
        raise HTTPException(
            status_code=400,
            detail="Maximum 20 files per batch"
        )
    
    results = []
    
    for i, file in enumerate(files):
        try:
            # Check file type
            if not file.content_type.startswith('image/'):
                results.append({
                    "index": i,
                    "filename": file.filename,
                    "success": False,
                    "error": "Not an image file"
                })
                continue
            
            content = await file.read()
            
            request = OCRRequest(
                image_data=base64.b64encode(content).decode('utf-8'),
                language=language
            )
            
            response = await extract_text_from_image(request, current_user, None)
            
            results.append({
                "index": i,
                "filename": file.filename,
                "success": True,
                "text": response.text,
                "confidence": response.confidence,
                "word_count": response.word_count
            })
            
        except Exception as e:
            results.append({
                "index": i,
                "filename": file.filename,
                "success": False,
                "error": str(e)
            })
    
    return {
        "total": len(files),
        "successful": sum(1 for r in results if r['success']),
        "failed": sum(1 for r in results if not r['success']),
        "results": results
    }

@router.get("/status")
async def get_ocr_status(
    current_user: dict = Depends(get_current_user)
):
    """Get OCR system status"""
    try:
        return {
            "tesseract_available": ocr_manager.tesseract_available,
            "easyocr_available": ocr_manager.easyocr_available,
            "supported_formats": ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'pdf'],
            "max_file_size_mb": 50,
            "batch_limit": 20
        }
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get status: {str(e)}"
        )