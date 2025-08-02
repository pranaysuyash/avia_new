"""
Export API Endpoints
REST API for multimedia export and sharing functionality
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional, List, Dict, Any
import os
import sys
import tempfile
import logging
from datetime import datetime, timedelta
import mimetypes

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.auth import auth_required, export_required, create_api_response
from api.models import ExportRequest, ExportResponse, ExportFormat

# Import export modules
from export_manager import MultimediaExporter, ExportConfig
from session_manager import SessionManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/export", tags=["Export"])

# Initialize components
session_manager = SessionManager()


def get_exporter():
    """Get or create export manager instance"""
    try:
        # Create temp directory for exports
        temp_dir = tempfile.mkdtemp(prefix="api_exports_")
        return MultimediaExporter(temp_dir)
    except Exception as e:
        logger.error(f"Failed to initialize exporter: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Export service unavailable"
        )


@router.post("/transcript/{transcript_id}", response_model=ExportResponse)
async def export_transcript(
    transcript_id: str,
    request: ExportRequest,
    user_id: str = Depends(export_required)
):
    """Export transcript in specified format"""
    try:
        # Get transcript data from session
        results = session_manager.get_stored_results(user_id)
        transcript_data = None
        
        for result in results:
            if result.get('transcript_id') == transcript_id:
                transcript_data = result['result']
                break
        
        if not transcript_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transcript not found"
            )
        
        exporter = get_exporter()
        
        # Create export configuration
        config = ExportConfig(
            format=request.format.value,
            include_metadata=request.include_metadata,
            include_entities=request.include_entities,
            include_speakers=request.include_speakers,
            custom_template=request.custom_template
        )
        
        # Prepare data for export
        export_data = {
            'id': transcript_id,
            'title': f"Transcript {transcript_id}",
            'transcript': transcript_data['text'],
            'duration': transcript_data.get('duration', 0),
            'language': transcript_data.get('language', 'unknown'),
            'word_count': transcript_data.get('word_count', 0),
            'created_at': transcript_data.get('created_at'),
            'entities': transcript_data.get('entities', []) if request.include_entities else [],
            'speakers': transcript_data.get('speakers', []) if request.include_speakers else [],
            'metadata': {
                'processing_time': transcript_data.get('processing_time', 0),
                'confidence': transcript_data.get('confidence'),
                'exported_at': datetime.now().isoformat(),
                'exported_by': user_id
            } if request.include_metadata else {}
        }
        
        # Export transcript
        export_path = exporter.export_transcript(export_data, config)
        
        if not os.path.exists(export_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Export failed - file not created"
            )
        
        # Get file info
        file_size = os.path.getsize(export_path)
        file_name = os.path.basename(export_path)
        
        # Store export info for download
        export_id = f"export_{user_id}_{int(datetime.now().timestamp())}"
        session_data = session_manager.get_session_data(user_id) or {}
        if 'exports' not in session_data:
            session_data['exports'] = {}
        
        session_data['exports'][export_id] = {
            'file_path': export_path,
            'file_name': file_name,
            'file_size': file_size,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'transcript_id': transcript_id,
            'format': request.format.value
        }
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response({
            "export_id": export_id,
            "download_url": f"/api/v1/export/download/{export_id}",
            "file_name": file_name,
            "file_size": file_size,
            "format": request.format.value,
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }, "Export completed successfully")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export operation failed"
        )


@router.get("/download/{export_id}")
async def download_export(
    export_id: str,
    user_id: str = Depends(auth_required)
):
    """Download exported file"""
    try:
        # Get export info from session
        session_data = session_manager.get_session_data(user_id) or {}
        exports = session_data.get('exports', {})
        
        if export_id not in exports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        export_info = exports[export_id]
        
        # Check if export has expired
        expires_at = datetime.fromisoformat(export_info['expires_at'])
        if datetime.now() > expires_at:
            # Clean up expired file
            try:
                os.unlink(export_info['file_path'])
            except:
                pass
            del exports[export_id]
            session_manager.set_session_data(user_id, session_data)
            
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Export has expired"
            )
        
        file_path = export_info['file_path']
        file_name = export_info['file_name']
        
        if not os.path.exists(file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export file not found"
            )
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(file_name)
        if not content_type:
            content_type = 'application/octet-stream'
        
        return FileResponse(
            path=file_path,
            filename=file_name,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Download failed"
        )


@router.post("/batch")
async def export_batch(
    transcript_ids: List[str],
    format: ExportFormat,
    include_metadata: bool = True,
    include_entities: bool = True,
    include_speakers: bool = True,
    user_id: str = Depends(export_required)
):
    """Export multiple transcripts as a ZIP package"""
    try:
        if len(transcript_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 50 transcripts per batch export"
            )
        
        # Get transcript data
        results = session_manager.get_stored_results(user_id)
        transcript_data_list = []
        
        for transcript_id in transcript_ids:
            found = False
            for result in results:
                if result.get('transcript_id') == transcript_id:
                    transcript_data_list.append({
                        'id': transcript_id,
                        'data': result['result']
                    })
                    found = True
                    break
            
            if not found:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Transcript {transcript_id} not found"
                )
        
        exporter = get_exporter()
        
        # Create batch export
        export_configs = []
        for transcript_info in transcript_data_list:
            transcript_id = transcript_info['id']
            transcript_data = transcript_info['data']
            
            config = ExportConfig(
                format=format.value,
                include_metadata=include_metadata,
                include_entities=include_entities,
                include_speakers=include_speakers
            )
            
            export_data = {
                'id': transcript_id,
                'title': f"Transcript {transcript_id}",
                'transcript': transcript_data['text'],
                'duration': transcript_data.get('duration', 0),
                'language': transcript_data.get('language', 'unknown'),
                'word_count': transcript_data.get('word_count', 0),
                'created_at': transcript_data.get('created_at'),
                'entities': transcript_data.get('entities', []) if include_entities else [],
                'speakers': transcript_data.get('speakers', []) if include_speakers else [],
                'metadata': {
                    'processing_time': transcript_data.get('processing_time', 0),
                    'confidence': transcript_data.get('confidence'),
                    'exported_at': datetime.now().isoformat(),
                    'exported_by': user_id
                } if include_metadata else {}
            }
            
            export_configs.append((export_data, config))
        
        # Create batch export (ZIP file)
        zip_path = exporter.export_batch(export_configs)
        
        if not os.path.exists(zip_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Batch export failed"
            )
        
        # Store export info
        file_size = os.path.getsize(zip_path)
        file_name = os.path.basename(zip_path)
        export_id = f"batch_export_{user_id}_{int(datetime.now().timestamp())}"
        
        session_data = session_manager.get_session_data(user_id) or {}
        if 'exports' not in session_data:
            session_data['exports'] = {}
        
        session_data['exports'][export_id] = {
            'file_path': zip_path,
            'file_name': file_name,
            'file_size': file_size,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat(),
            'transcript_ids': transcript_ids,
            'format': format.value,
            'type': 'batch'
        }
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response({
            "export_id": export_id,
            "download_url": f"/api/v1/export/download/{export_id}",
            "file_name": file_name,
            "file_size": file_size,
            "format": format.value,
            "transcript_count": len(transcript_ids),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }, f"Batch export of {len(transcript_ids)} transcripts completed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Batch export failed"
        )


@router.get("/formats")
async def get_export_formats():
    """Get available export formats and their capabilities"""
    return create_api_response({
        "formats": [
            {
                "name": "json",
                "description": "Machine-readable JSON format",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "application/json",
                "extension": ".json"
            },
            {
                "name": "csv",
                "description": "Spreadsheet-compatible CSV format",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": False,
                "mime_type": "text/csv",
                "extension": ".csv"
            },
            {
                "name": "pdf",
                "description": "Professional PDF document",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "application/pdf",
                "extension": ".pdf"
            },
            {
                "name": "docx",
                "description": "Microsoft Word document",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "extension": ".docx"
            },
            {
                "name": "txt",
                "description": "Plain text format",
                "supports_metadata": False,
                "supports_entities": False,
                "supports_speakers": False,
                "mime_type": "text/plain",
                "extension": ".txt"
            },
            {
                "name": "markdown",
                "description": "Markdown format for documentation",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "text/markdown",
                "extension": ".md"
            },
            {
                "name": "html",
                "description": "Web-compatible HTML format",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "text/html",
                "extension": ".html"
            },
            {
                "name": "xml",
                "description": "Structured XML format",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "application/xml",
                "extension": ".xml"
            },
            {
                "name": "xlsx",
                "description": "Excel spreadsheet format",
                "supports_metadata": True,
                "supports_entities": True,
                "supports_speakers": True,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "extension": ".xlsx"
            }
        ]
    }, "Export formats retrieved")


@router.get("/history")
async def get_export_history(
    limit: int = Query(default=20, ge=1, le=100),
    user_id: str = Depends(auth_required)
):
    """Get user's export history"""
    try:
        session_data = session_manager.get_session_data(user_id) or {}
        exports = session_data.get('exports', {})
        
        # Convert to list and sort by creation time
        export_list = []
        for export_id, export_info in exports.items():
            export_list.append({
                "export_id": export_id,
                "file_name": export_info['file_name'],
                "file_size": export_info['file_size'],
                "format": export_info['format'],
                "created_at": export_info['created_at'],
                "expires_at": export_info['expires_at'],
                "type": export_info.get('type', 'single'),
                "transcript_count": len(export_info.get('transcript_ids', [export_info.get('transcript_id', '')]))
            })
        
        # Sort by creation time (newest first)
        export_list.sort(key=lambda x: x['created_at'], reverse=True)
        
        # Apply limit
        export_list = export_list[:limit]
        
        return create_api_response({
            "exports": export_list,
            "count": len(export_list),
            "total_exports": len(exports)
        }, "Export history retrieved")
        
    except Exception as e:
        logger.error(f"Export history error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get export history"
        )


@router.delete("/{export_id}")
async def delete_export(
    export_id: str,
    user_id: str = Depends(auth_required)
):
    """Delete an export file"""
    try:
        session_data = session_manager.get_session_data(user_id) or {}
        exports = session_data.get('exports', {})
        
        if export_id not in exports:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        export_info = exports[export_id]
        
        # Delete file
        try:
            os.unlink(export_info['file_path'])
        except:
            pass  # File might already be deleted
        
        # Remove from session
        del exports[export_id]
        session_manager.set_session_data(user_id, session_data)
        
        return create_api_response(
            {"export_id": export_id},
            "Export deleted successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete export error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete export"
        )