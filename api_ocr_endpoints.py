"""
OCR API Endpoints
FastAPI endpoints for handling OCR requests from web, desktop, and mobile clients
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any, Union
import tempfile
import base64
import json
import asyncio
from pathlib import Path
import logging
from datetime import datetime

from image_ocr_processor import (
    OCRManager, OCRResult, DocumentResult, DocumentPage,
    validate_image_file, estimate_processing_time
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="OCR Processing API",
    description="Advanced OCR API for image and document text extraction",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OCR manager
ocr_manager = OCRManager()

# Pydantic models for request/response
class OCRRequest(BaseModel):
    file_data: str  # Base64 encoded file data
    filename: str
    language: str = "en"
    extract_tables: bool = True
    enhance_contrast: bool = True
    denoise_image: bool = True
    deskew_image: bool = True

class OCRResponse(BaseModel):
    success: bool
    data: Optional[Union[Dict[str, Any], str]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BatchOCRRequest(BaseModel):
    files: List[OCRRequest]
    create_zip: bool = True
    include_metadata: bool = True

class LanguageInfo(BaseModel):
    code: str
    name: str

class SystemStatus(BaseModel):
    tesseract_available: bool
    easyocr_available: bool
    supported_formats: List[str]
    supported_languages: int
    temp_directory: str

# Helper functions
def serialize_ocr_result(result: Union[OCRResult, DocumentResult]) -> Dict[str, Any]:
    """Serialize OCR result to JSON-compatible format"""
    if isinstance(result, OCRResult):
        return {
            "type": "ocr_result",
            "text": result.text,
            "confidence": result.confidence,
            "language": result.language,
            "processing_time": result.processing_time,
            "word_count": result.word_count,
            "line_count": result.line_count,
            "bounding_boxes": result.bounding_boxes,
            "metadata": result.metadata
        }
    elif isinstance(result, DocumentResult):
        return {
            "type": "document_result",
            "filename": result.filename,
            "total_pages": result.total_pages,
            "pages": [
                {
                    "page_number": page.page_number,
                    "text": page.text,
                    "confidence": page.confidence,
                    "tables": page.tables
                }
                for page in result.pages
            ],
            "combined_text": result.combined_text,
            "processing_time": result.processing_time,
            "metadata": result.metadata
        }
    else:
        raise ValueError(f"Unknown result type: {type(result)}")

async def save_temp_file(file_data: str, filename: str) -> str:
    """Save base64 file data to temporary file"""
    try:
        # Decode base64 data
        decoded_data = base64.b64decode(file_data)
        
        # Create temporary file
        suffix = Path(filename).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(decoded_data)
        temp_file.close()
        
        return temp_file.name
    except Exception as e:
        logger.error(f"Error saving temp file: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid file data: {str(e)}")

# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "OCR Processing API",
        "version": "1.0.0",
        "endpoints": {
            "process": "/api/ocr/process",
            "process_mobile": "/api/ocr/process-mobile",
            "batch": "/api/ocr/batch",
            "languages": "/api/ocr/languages",
            "status": "/api/ocr/status"
        }
    }

@app.post("/api/ocr/process", response_model=OCRResponse)
async def process_file_upload(
    file: UploadFile = File(...),
    language: str = Form("en"),
    extract_tables: bool = Form(True),
    enhance_contrast: bool = Form(True),
    denoise_image: bool = Form(True),
    deskew_image: bool = Form(True)
):
    """
    Process uploaded file (for web/desktop clients)
    """
    start_time = datetime.now()
    
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file size (limit to 50MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            raise HTTPException(status_code=413, detail="File too large (max 50MB)")
        
        # Save to temporary file
        suffix = Path(file.filename).suffix
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        temp_file.write(content)
        temp_file.close()
        
        # Process file
        result = ocr_manager.process_file(
            temp_file.name,
            language=language,
            extract_tables=extract_tables
        )
        
        # Clean up temp file
        Path(temp_file.name).unlink()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OCRResponse(
            success=True,
            data=serialize_ocr_result(result),
            processing_time=processing_time,
            metadata={
                "filename": file.filename,
                "file_size": file_size,
                "settings": {
                    "language": language,
                    "extract_tables": extract_tables,
                    "enhance_contrast": enhance_contrast,
                    "denoise_image": denoise_image,
                    "deskew_image": deskew_image
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing file upload: {str(e)}")
        return OCRResponse(
            success=False,
            error=str(e),
            processing_time=(datetime.now() - start_time).total_seconds()
        )

@app.post("/api/ocr/process-mobile", response_model=OCRResponse)
async def process_mobile_file(request: OCRRequest):
    """
    Process file from mobile client (base64 encoded)
    """
    start_time = datetime.now()
    
    try:
        # Save base64 data to temp file
        temp_file_path = await save_temp_file(request.file_data, request.filename)
        
        # Process file
        result = ocr_manager.process_file(
            temp_file_path,
            language=request.language,
            extract_tables=request.extract_tables
        )
        
        # Clean up temp file
        Path(temp_file_path).unlink()
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OCRResponse(
            success=True,
            data=serialize_ocr_result(result),
            processing_time=processing_time,
            metadata={
                "filename": request.filename,
                "settings": {
                    "language": request.language,
                    "extract_tables": request.extract_tables,
                    "enhance_contrast": request.enhance_contrast,
                    "denoise_image": request.denoise_image,
                    "deskew_image": request.deskew_image
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing mobile file: {str(e)}")
        return OCRResponse(
            success=False,
            error=str(e),
            processing_time=(datetime.now() - start_time).total_seconds()
        )

@app.post("/api/ocr/batch")
async def process_batch_files(request: BatchOCRRequest):
    """
    Process multiple files in batch
    """
    start_time = datetime.now()
    
    try:
        results = []
        
        for file_request in request.files:
            try:
                # Save base64 data to temp file
                temp_file_path = await save_temp_file(
                    file_request.file_data, 
                    file_request.filename
                )
                
                # Process file
                result = ocr_manager.process_file(
                    temp_file_path,
                    language=file_request.language,
                    extract_tables=file_request.extract_tables
                )
                
                # Clean up temp file
                Path(temp_file_path).unlink()
                
                results.append({
                    "filename": file_request.filename,
                    "success": True,
                    "data": serialize_ocr_result(result)
                })
                
            except Exception as e:
                logger.error(f"Error processing {file_request.filename}: {str(e)}")
                results.append({
                    "filename": file_request.filename,
                    "success": False,
                    "error": str(e)
                })
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Calculate statistics
        successful = sum(1 for r in results if r["success"])
        failed = len(results) - successful
        
        return {
            "success": True,
            "results": results,
            "statistics": {
                "total_files": len(results),
                "successful": successful,
                "failed": failed,
                "processing_time": processing_time
            },
            "metadata": {
                "create_zip": request.create_zip,
                "include_metadata": request.include_metadata
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing batch: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "processing_time": (datetime.now() - start_time).total_seconds()
        }

@app.get("/api/ocr/languages", response_model=List[LanguageInfo])
async def get_supported_languages():
    """
    Get list of supported languages
    """
    try:
        languages = ocr_manager.get_supported_languages()
        return [LanguageInfo(**lang) for lang in languages]
    except Exception as e:
        logger.error(f"Error getting languages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ocr/status", response_model=SystemStatus)
async def get_system_status():
    """
    Get system status and capabilities
    """
    try:
        stats = ocr_manager.get_processing_stats()
        return SystemStatus(**stats)
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ocr/validate")
async def validate_file(file: UploadFile = File(...)):
    """
    Validate uploaded file without processing
    """
    try:
        # Check file extension
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        file_ext = Path(file.filename).suffix.lower()
        supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.pdf']
        
        if file_ext not in supported_formats:
            return {
                "valid": False,
                "error": f"Unsupported format: {file_ext}",
                "supported_formats": supported_formats
            }
        
        # Check file size
        content = await file.read()
        file_size = len(content)
        
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return {
                "valid": False,
                "error": "File too large (max 50MB)",
                "file_size": file_size
            }
        
        # Estimate processing time
        estimated_time = estimate_processing_time(file.filename)
        
        return {
            "valid": True,
            "filename": file.filename,
            "file_size": file_size,
            "format": file_ext,
            "estimated_processing_time": estimated_time
        }
        
    except Exception as e:
        logger.error(f"Error validating file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/ocr/cleanup")
async def cleanup_temp_files():
    """
    Clean up temporary files
    """
    try:
        ocr_manager.cleanup_temp_files()
        return {"success": True, "message": "Temporary files cleaned up"}
    except Exception as e:
        logger.error(f"Error cleaning up: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/ocr/health")
async def health_check():
    """
    Health check endpoint
    """
    try:
        stats = ocr_manager.get_processing_stats()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "ocr_engines": {
                "tesseract": stats["tesseract_available"],
                "easyocr": stats["easyocr_available"]
            },
            "supported_formats": len(stats["supported_formats"]),
            "supported_languages": stats["supported_languages"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "status_code": 500
        }
    )

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("OCR API starting up...")
    
    # Verify OCR engines are available
    stats = ocr_manager.get_processing_stats()
    logger.info(f"Tesseract available: {stats['tesseract_available']}")
    logger.info(f"EasyOCR available: {stats['easyocr_available']}")
    logger.info(f"Supported formats: {len(stats['supported_formats'])}")
    logger.info(f"Supported languages: {stats['supported_languages']}")
    
    logger.info("OCR API startup complete")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("OCR API shutting down...")
    
    # Clean up temporary files
    try:
        ocr_manager.cleanup_temp_files()
        logger.info("Temporary files cleaned up")
    except Exception as e:
        logger.warning(f"Error cleaning up temp files: {str(e)}")
    
    logger.info("OCR API shutdown complete")

if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "api_ocr_endpoints:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )