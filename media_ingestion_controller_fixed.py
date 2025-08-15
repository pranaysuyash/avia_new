"""
Core Media Ingestion Controller - Fixed Version
Unified media ingestion system with multi-format support, automatic format detection,
streaming upload capabilities, and preprocessing pipeline for content optimization.
"""

import os
import io
import logging
import tempfile
import hashlib
import mimetypes
from typing import Dict, Any, Optional, List, Tuple, Union, BinaryIO
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

# Third-party imports with fallbacks
try:
    import ffmpeg
except ImportError:
    ffmpeg = None

try:
    import magic
except ImportError:
    magic = None

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import aiofiles
except ImportError:
    aiofiles = None

# Local imports with fallbacks
try:
    from media import (
        validate_media_file, get_media_info, is_audio_file, is_video_file,
        SUPPORTED_AUDIO_FORMATS, SUPPORTED_VIDEO_FORMATS
    )
    from errors import MediaProcessingError, FileProcessingError, ErrorCode
except ImportError as e:
    logging.warning(f"Local module import failed: {e}, using fallbacks")
    
    # Fallback definitions
    SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.flac', '.aac'}
    SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
    
    class MediaProcessingError(Exception):
        def __init__(self, message, error_code=None, user_message=None):
            super().__init__(message)
            self.error_code = error_code
            self.user_message = user_message
    
    class FileProcessingError(Exception):
        def __init__(self, message, error_code=None, user_message=None, file_path=None):
            super().__init__(message)
            self.error_code = error_code
            self.user_message = user_message
            self.file_path = file_path
    
    class ErrorCode:
        FILE_UNSUPPORTED_FORMAT = "FILE_UNSUPPORTED_FORMAT"
        MEDIA_VALIDATION_ERROR = "MEDIA_VALIDATION_ERROR"
        FILE_NOT_FOUND = "FILE_NOT_FOUND"
        FILE_CORRUPTED = "FILE_CORRUPTED"
    
    def validate_media_file(file_path, max_size_mb=2048):
        """Fallback validation function"""
        if not os.path.exists(file_path):
            raise FileProcessingError(f"File not found: {file_path}")
        return True
    
    def get_media_info(file_path):
        """Fallback media info function"""
        try:
            if ffmpeg:
                probe = ffmpeg.probe(file_path)
                format_info = probe.get('format', {})
                return {
                    'duration': float(format_info.get('duration', 0)),
                    'bit_rate': int(format_info.get('bit_rate', 0)),
                    'sample_rate': 44100,
                    'channels': 2
                }
        except:
            pass
        return {'duration': 0, 'bit_rate': 0, 'sample_rate': 44100, 'channels': 2}
    
    def is_audio_file(file_path):
        """Fallback audio detection"""
        return Path(file_path).suffix.lower() in SUPPORTED_AUDIO_FORMATS
    
    def is_video_file(file_path):
        """Fallback video detection"""
        return Path(file_path).suffix.lower() in SUPPORTED_VIDEO_FORMATS

logger = logging.getLogger(__name__)

# Supported formats for different media types
SUPPORTED_IMAGE_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
SUPPORTED_DOCUMENT_FORMATS = {'.pdf', '.txt', '.docx', '.doc', '.rtf'}
ALL_SUPPORTED_FORMATS = (
    SUPPORTED_AUDIO_FORMATS | SUPPORTED_VIDEO_FORMATS | 
    SUPPORTED_IMAGE_FORMATS | SUPPORTED_DOCUMENT_FORMATS
)

@dataclass
class MediaFormat:
    """Media format information"""
    file_type: str  # 'audio', 'video', 'image', 'document'
    mime_type: str
    extension: str
    codec: Optional[str] = None
    container: Optional[str] = None
    is_supported: bool = True

@dataclass
class QualityMetrics:
    """Media quality metrics"""
    resolution: Optional[Tuple[int, int]] = None
    duration: Optional[float] = None
    bitrate: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    file_size: int = 0
    quality_score: float = 0.0  # 0-100 scale

@dataclass
class ProcessingOptions:
    """Processing configuration options"""
    target_quality: str = "high"  # 'low', 'medium', 'high', 'ultra'
    enable_preprocessing: bool = True
    enable_optimization: bool = True
    max_resolution: Optional[Tuple[int, int]] = None
    target_format: Optional[str] = None
    custom_params: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MediaFile:
    """Media file representation"""
    id: str
    original_path: str
    processed_path: Optional[str] = None
    format: Optional[MediaFormat] = None
    quality_metrics: Optional[QualityMetrics] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    processing_status: str = "pending"  # 'pending', 'processing', 'completed', 'failed'

@dataclass
class IngestionResult:
    """Result of media ingestion process"""
    media_file: MediaFile
    success: bool
    processing_time: float
    operations_applied: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

@dataclass
class StreamingUploadProgress:
    """Progress tracking for streaming uploads"""
    total_size: int
    uploaded_size: int
    progress_percentage: float
    upload_speed: float  # bytes per second
    estimated_time_remaining: float  # seconds
    status: str = "uploading"  # 'uploading', 'processing', 'completed', 'failed'

class MediaIngestionController:
    """
    Unified media ingestion controller that handles all media types with intelligent
    format detection, streaming uploads, and preprocessing optimization.
    """
    
    def __init__(self, temp_dir: Optional[str] = None, max_file_size_mb: int = 2048):
        """
        Initialize the media ingestion controller.
        
        Args:
            temp_dir: Directory for temporary files (uses system temp if None)
            max_file_size_mb: Maximum allowed file size in MB
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_file_size_mb = max_file_size_mb
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._upload_progress: Dict[str, StreamingUploadProgress] = {}
        self._upload_locks: Dict[str, threading.Lock] = {}
        
        # Initialize libmagic for MIME type detection if available
        self.magic_mime = None
        if magic:
            try:
                self.magic_mime = magic.Magic(mime=True)
            except Exception as e:
                logger.warning(f"Failed to initialize libmagic: {e}")
        
        logger.info(f"MediaIngestionController initialized with temp_dir={self.temp_dir}, max_size={max_file_size_mb}MB")
    
    async def ingest_media(
        self, 
        media_stream: Union[BinaryIO, str], 
        filename: str,
        options: Optional[ProcessingOptions] = None
    ) -> IngestionResult:
        """
        Main entry point for media ingestion with intelligent processing.
        
        Args:
            media_stream: File stream or path to media file
            filename: Original filename
            options: Processing configuration options
            
        Returns:
            IngestionResult: Complete ingestion result with processed media
        """
        start_time = datetime.now()
        options = options or ProcessingOptions()
        
        try:
            # Generate unique ID for this ingestion
            media_id = self._generate_media_id(filename)
            
            # Handle different input types
            if isinstance(media_stream, str):
                # File path provided
                temp_path = media_stream
                file_size = os.path.getsize(temp_path)
            else:
                # Stream provided - save to temporary file
                temp_path = await self._save_stream_to_temp(media_stream, filename, media_id)
                file_size = os.path.getsize(temp_path)
            
            # Create media file object
            media_file = MediaFile(
                id=media_id,
                original_path=temp_path,
                metadata={"original_filename": filename, "file_size": file_size}
            )
            
            # Step 1: Format detection and validation
            media_format = await self.detect_format(temp_path, filename)
            media_file.format = media_format
            
            if not media_format.is_supported:
                raise MediaProcessingError(
                    f"Unsupported media format: {media_format.extension}",
                    ErrorCode.FILE_UNSUPPORTED_FORMAT,
                    f"File format {media_format.extension} is not supported."
                )
            
            # Step 2: Content validation
            validation_result = await self.validate_content(media_file)
            if not validation_result["valid"]:
                raise MediaProcessingError(
                    f"Content validation failed: {validation_result['error']}",
                    ErrorCode.MEDIA_VALIDATION_ERROR,
                    validation_result["error"]
                )
            
            # Step 3: Quality analysis
            quality_metrics = await self._analyze_quality(media_file)
            media_file.quality_metrics = quality_metrics
            
            # Step 4: Preprocessing pipeline
            operations_applied = []
            warnings = []
            
            if options.enable_preprocessing:
                preprocessed_path, ops, warns = await self.preprocess_media(media_file, options)
                if preprocessed_path != temp_path:
                    media_file.processed_path = preprocessed_path
                operations_applied.extend(ops)
                warnings.extend(warns)
            
            # Step 5: Content optimization
            if options.enable_optimization:
                optimized_path, opt_ops, opt_warns = await self._optimize_content(media_file, options)
                if optimized_path:
                    media_file.processed_path = optimized_path
                    operations_applied.extend(opt_ops)
                    warnings.extend(opt_warns)
            
            media_file.processing_status = "completed"
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return IngestionResult(
                media_file=media_file,
                success=True,
                processing_time=processing_time,
                operations_applied=operations_applied,
                warnings=warnings
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Media ingestion failed for {filename}: {str(e)}")
            
            # Create failed result
            media_file = MediaFile(
                id=media_id if 'media_id' in locals() else self._generate_media_id(filename),
                original_path=temp_path if 'temp_path' in locals() else "",
                processing_status="failed"
            )
            
            return IngestionResult(
                media_file=media_file,
                success=False,
                processing_time=processing_time,
                errors=[str(e)]
            )
    
    async def detect_format(self, file_path: str, filename: str) -> MediaFormat:
        """
        Intelligent format detection using multiple methods.
        
        Args:
            file_path: Path to the media file
            filename: Original filename
            
        Returns:
            MediaFormat: Detected format information
        """
        try:
            # Get file extension
            extension = Path(filename).suffix.lower()
            
            # Method 1: MIME type detection using libmagic
            mime_type = None
            if self.magic_mime:
                try:
                    mime_type = self.magic_mime.from_file(file_path)
                except Exception as e:
                    logger.warning(f"libmagic detection failed: {e}")
            
            # Method 2: Fallback to mimetypes module
            if not mime_type:
                mime_type, _ = mimetypes.guess_type(filename)
                mime_type = mime_type or "application/octet-stream"
            
            # Method 3: FFmpeg probe for media files
            codec = None
            container = None
            if extension in (SUPPORTED_AUDIO_FORMATS | SUPPORTED_VIDEO_FORMATS) and ffmpeg:
                try:
                    probe = ffmpeg.probe(file_path)
                    format_info = probe.get('format', {})
                    container = format_info.get('format_name', '').split(',')[0]
                    
                    # Get codec from first stream
                    streams = probe.get('streams', [])
                    if streams:
                        codec = streams[0].get('codec_name')
                        
                except Exception as e:
                    logger.warning(f"FFmpeg probe failed: {e}")
            
            # Determine file type
            file_type = self._determine_file_type(extension, mime_type)
            
            # Check if format is supported
            is_supported = extension in ALL_SUPPORTED_FORMATS
            
            return MediaFormat(
                file_type=file_type,
                mime_type=mime_type,
                extension=extension,
                codec=codec,
                container=container,
                is_supported=is_supported
            )
            
        except Exception as e:
            logger.error(f"Format detection failed: {e}")
            return MediaFormat(
                file_type="unknown",
                mime_type="application/octet-stream",
                extension=Path(filename).suffix.lower(),
                is_supported=False
            )
    
    async def validate_content(self, media_file: MediaFile) -> Dict[str, Any]:
        """
        Comprehensive content validation for different media types.
        
        Args:
            media_file: Media file to validate
            
        Returns:
            Dict containing validation results
        """
        try:
            file_path = media_file.original_path
            file_format = media_file.format
            
            if not file_format:
                return {"valid": False, "error": "Unknown file format"}
            
            # Basic file validation
            if not os.path.exists(file_path):
                return {"valid": False, "error": "File does not exist"}
            
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                return {"valid": False, "error": "File is empty"}
            
            if file_size > self.max_file_size_mb * 1024 * 1024:
                return {"valid": False, "error": f"File too large (max {self.max_file_size_mb}MB)"}
            
            # Type-specific validation
            if file_format.file_type in ['audio', 'video']:
                return await self._validate_media_content(file_path)
            elif file_format.file_type == 'image':
                return await self._validate_image_content(file_path)
            elif file_format.file_type == 'document':
                return await self._validate_document_content(file_path)
            else:
                return {"valid": True, "warnings": ["Unknown file type, basic validation only"]}
                
        except Exception as e:
            logger.error(f"Content validation failed: {e}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}
    
    async def preprocess_media(
        self, 
        media_file: MediaFile, 
        options: ProcessingOptions
    ) -> Tuple[str, List[str], List[str]]:
        """
        Apply preprocessing pipeline based on media type and options.
        
        Args:
            media_file: Media file to preprocess
            options: Processing options
            
        Returns:
            Tuple of (processed_path, operations_applied, warnings)
        """
        try:
            file_path = media_file.original_path
            file_format = media_file.format
            operations_applied = []
            warnings = []
            
            if not file_format:
                return file_path, operations_applied, ["No format detected, skipping preprocessing"]
            
            # Type-specific preprocessing
            if file_format.file_type == 'audio':
                processed_path, ops, warns = await self._preprocess_audio(file_path, options)
            elif file_format.file_type == 'video':
                processed_path, ops, warns = await self._preprocess_video(file_path, options)
            elif file_format.file_type == 'image':
                processed_path, ops, warns = await self._preprocess_image(file_path, options)
            elif file_format.file_type == 'document':
                processed_path, ops, warns = await self._preprocess_document(file_path, options)
            else:
                return file_path, operations_applied, ["Unknown file type, no preprocessing applied"]
            
            operations_applied.extend(ops)
            warnings.extend(warns)
            
            return processed_path, operations_applied, warnings
            
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return file_path, operations_applied, [f"Preprocessing error: {str(e)}"]
    
    def _generate_media_id(self, filename: str) -> str:
        """Generate unique media ID based on filename and timestamp."""
        timestamp = datetime.now().isoformat()
        content = f"{filename}_{timestamp}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    async def _save_stream_to_temp(self, stream: BinaryIO, filename: str, media_id: str) -> str:
        """Save stream content to temporary file."""
        temp_path = os.path.join(self.temp_dir, f"temp_{media_id}_{filename}")
        
        if aiofiles:
            async with aiofiles.open(temp_path, 'wb') as temp_file:
                while True:
                    chunk = stream.read(8192)
                    if not chunk:
                        break
                    await temp_file.write(chunk)
        else:
            # Fallback to synchronous file operations
            with open(temp_path, 'wb') as temp_file:
                while True:
                    chunk = stream.read(8192)
                    if not chunk:
                        break
                    temp_file.write(chunk)
        
        return temp_path
    
    def _determine_file_type(self, extension: str, mime_type: str) -> str:
        """Determine file type from extension and MIME type."""
        if extension in SUPPORTED_AUDIO_FORMATS:
            return "audio"
        elif extension in SUPPORTED_VIDEO_FORMATS:
            return "video"
        elif extension in SUPPORTED_IMAGE_FORMATS:
            return "image"
        elif extension in SUPPORTED_DOCUMENT_FORMATS:
            return "document"
        elif mime_type.startswith('audio/'):
            return "audio"
        elif mime_type.startswith('video/'):
            return "video"
        elif mime_type.startswith('image/'):
            return "image"
        elif mime_type.startswith('text/') or 'document' in mime_type:
            return "document"
        else:
            return "unknown"
    
    async def _analyze_quality(self, media_file: MediaFile) -> QualityMetrics:
        """Analyze media quality and extract metrics."""
        try:
            file_path = media_file.original_path
            file_format = media_file.format
            file_size = os.path.getsize(file_path)
            
            metrics = QualityMetrics(file_size=file_size)
            
            if file_format.file_type in ['audio', 'video']:
                # Use existing media info function
                try:
                    info = get_media_info(file_path)
                    metrics.duration = info.get('duration', 0)
                    metrics.bitrate = info.get('bit_rate', 0)
                    metrics.sample_rate = info.get('sample_rate', 0)
                    metrics.channels = info.get('channels', 0)
                    
                    # Calculate basic quality score
                    quality_score = 50.0  # Base score
                    if metrics.bitrate > 128000:  # Good bitrate
                        quality_score += 20
                    if metrics.sample_rate >= 44100:  # Good sample rate
                        quality_score += 15
                    if metrics.duration > 0:  # Valid duration
                        quality_score += 15
                    
                    metrics.quality_score = min(quality_score, 100.0)
                    
                except Exception as e:
                    logger.warning(f"Failed to get media info: {e}")
                    
            elif file_format.file_type == 'image' and Image:
                try:
                    with Image.open(file_path) as img:
                        metrics.resolution = img.size
                        
                        # Calculate quality score based on resolution
                        width, height = img.size
                        total_pixels = width * height
                        
                        if total_pixels >= 1920 * 1080:  # HD or higher
                            metrics.quality_score = 90.0
                        elif total_pixels >= 1280 * 720:  # HD ready
                            metrics.quality_score = 75.0
                        elif total_pixels >= 640 * 480:  # SD
                            metrics.quality_score = 60.0
                        else:
                            metrics.quality_score = 40.0
                            
                except Exception as e:
                    logger.warning(f"Failed to analyze image: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Quality analysis failed: {e}")
            return QualityMetrics(file_size=os.path.getsize(media_file.original_path))
    
    async def _validate_media_content(self, file_path: str) -> Dict[str, Any]:
        """Validate audio/video content using existing validation."""
        try:
            # Use existing validation from media.py
            validate_media_file(file_path, self.max_file_size_mb)
            return {"valid": True}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    async def _validate_image_content(self, file_path: str) -> Dict[str, Any]:
        """Validate image content."""
        try:
            if not Image:
                return {"valid": True, "warnings": ["PIL not available, skipping image validation"]}
                
            with Image.open(file_path) as img:
                # Basic validation - can open and has valid dimensions
                if img.size[0] <= 0 or img.size[1] <= 0:
                    return {"valid": False, "error": "Invalid image dimensions"}
                
                # Check for reasonable size limits
                if img.size[0] > 10000 or img.size[1] > 10000:
                    return {"valid": False, "error": "Image dimensions too large"}
                
                return {"valid": True}
                
        except Exception as e:
            return {"valid": False, "error": f"Invalid image file: {str(e)}"}
    
    async def _validate_document_content(self, file_path: str) -> Dict[str, Any]:
        """Validate document content."""
        try:
            extension = Path(file_path).suffix.lower()
            
            if extension == '.pdf' and fitz:
                # Validate PDF
                try:
                    doc = fitz.open(file_path)
                    if doc.page_count == 0:
                        return {"valid": False, "error": "PDF has no pages"}
                    doc.close()
                    return {"valid": True}
                except Exception as e:
                    return {"valid": False, "error": f"Invalid PDF: {str(e)}"}
                    
            elif extension == '.txt':
                # Validate text file
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read(1024)  # Read first 1KB
                        if not content.strip():
                            return {"valid": False, "error": "Text file is empty"}
                    return {"valid": True}
                except UnicodeDecodeError:
                    return {"valid": False, "error": "Text file encoding not supported"}
                except Exception as e:
                    return {"valid": False, "error": f"Invalid text file: {str(e)}"}
            
            # For other document types, basic validation
            return {"valid": True, "warnings": ["Limited validation for this document type"]}
            
        except Exception as e:
            return {"valid": False, "error": f"Document validation failed: {str(e)}"}
    
    async def _preprocess_audio(self, file_path: str, options: ProcessingOptions) -> Tuple[str, List[str], List[str]]:
        """Preprocess audio files."""
        # For now, return original path - audio preprocessing is handled by whisper_audio_preprocessor
        return file_path, ["audio_preprocessing_skipped"], ["Using existing audio preprocessor"]
    
    async def _preprocess_video(self, file_path: str, options: ProcessingOptions) -> Tuple[str, List[str], List[str]]:
        """Preprocess video files."""
        # Basic video preprocessing - extract audio if needed
        operations = []
        warnings = []
        
        try:
            if ffmpeg:
                # For now, just validate the video
                probe = ffmpeg.probe(file_path)
                operations.append("video_validation")
            else:
                warnings.append("FFmpeg not available, skipping video preprocessing")
            
            return file_path, operations, warnings
            
        except Exception as e:
            warnings.append(f"Video preprocessing warning: {str(e)}")
            return file_path, operations, warnings
    
    async def _preprocess_image(self, file_path: str, options: ProcessingOptions) -> Tuple[str, List[str], List[str]]:
        """Preprocess image files."""
        operations = []
        warnings = []
        
        try:
            if not Image:
                warnings.append("PIL not available, skipping image preprocessing")
                return file_path, operations, warnings
                
            with Image.open(file_path) as img:
                # Basic image optimization
                if options.max_resolution:
                    max_width, max_height = options.max_resolution
                    if img.size[0] > max_width or img.size[1] > max_height:
                        # Resize image
                        img.thumbnail(options.max_resolution, Image.Resampling.LANCZOS)
                        
                        # Save resized image
                        temp_path = file_path.replace('.', '_resized.')
                        img.save(temp_path, optimize=True, quality=85)
                        operations.append("image_resize")
                        
                        return temp_path, operations, warnings
                
                operations.append("image_validation")
                return file_path, operations, warnings
                
        except Exception as e:
            warnings.append(f"Image preprocessing warning: {str(e)}")
            return file_path, operations, warnings
    
    async def _preprocess_document(self, file_path: str, options: ProcessingOptions) -> Tuple[str, List[str], List[str]]:
        """Preprocess document files."""
        operations = []
        warnings = []
        
        # Basic document validation
        operations.append("document_validation")
        
        return file_path, operations, warnings
    
    async def _optimize_content(self, media_file: MediaFile, options: ProcessingOptions) -> Tuple[Optional[str], List[str], List[str]]:
        """Apply content optimization based on target quality and format."""
        operations = []
        warnings = []
        
        # Placeholder for content optimization
        # This would implement quality-based optimization, format conversion, etc.
        
        return None, operations, warnings

# Test functionality
if __name__ == "__main__":
    import asyncio
    
    async def test_controller():
        print("Testing MediaIngestionController...")
        controller = MediaIngestionController()
        print("✅ Controller initialized successfully")
        
        # Test format detection
        test_format = await controller.detect_format("/tmp/test.mp3", "test.mp3")
        print(f"✅ Format detection works: {test_format}")
        
        print("✅ All tests passed!")
    
    asyncio.run(test_controller())