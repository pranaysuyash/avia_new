"""
Comprehensive File Format Validation and Conversion System (Task 275)

This system provides:
- File format detection and validation
- Audio format conversion to standardized formats
- Batch conversion capabilities
- Detailed error reporting and format support information
- Quality validation after conversion
"""

import os
import sqlite3
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
try:
    import magic
except ImportError:
    magic = None
import hashlib

class AudioFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"
    AAC = "aac"
    WMA = "wma"
    AIFF = "aiff"
    AU = "au"
    MP4 = "mp4"
    WEBM = "webm"
    MKV = "mkv"

class ConversionStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    IN_PROGRESS = "in_progress"

class ValidationResult(Enum):
    VALID = "valid"
    INVALID_FORMAT = "invalid_format"
    CORRUPTED = "corrupted"
    UNSUPPORTED = "unsupported"
    TOO_LARGE = "too_large"
    TOO_SHORT = "too_short"

@dataclass
class FileFormatInfo:
    original_path: str
    detected_format: Optional[str]
    file_size: int
    duration_seconds: Optional[float]
    sample_rate: Optional[int]
    channels: Optional[int]
    bitrate: Optional[int]
    codec: Optional[str]
    is_supported: bool
    validation_result: ValidationResult
    validation_errors: List[str] = field(default_factory=list)

@dataclass
class ConversionResult:
    original_file: str
    converted_file: Optional[str]
    original_format: str
    target_format: str
    status: ConversionStatus
    file_size_before: int
    file_size_after: Optional[int]
    duration_before: Optional[float]
    duration_after: Optional[float]
    conversion_time: Optional[float]
    quality_score: Optional[float]
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class BatchConversionJob:
    job_id: str
    input_files: List[str]
    target_format: AudioFormat
    output_directory: str
    total_files: int
    processed_files: int = 0
    successful_conversions: int = 0
    failed_conversions: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    results: List[ConversionResult] = field(default_factory=list)

class ComprehensiveFileFormatSystem:
    def __init__(self, database_path: str = "file_format_system.db"):
        self.database_path = database_path
        self.supported_formats = {
            AudioFormat.WAV, AudioFormat.MP3, AudioFormat.FLAC, 
            AudioFormat.M4A, AudioFormat.OGG
        }
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        self.min_duration = 0.1  # 0.1 seconds
        self.max_duration = 3600  # 1 hour
        self.init_database()

    def init_database(self):
        """Initialize SQLite database for storing conversion history and metadata"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS file_validations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            file_hash TEXT,
            detected_format TEXT,
            file_size INTEGER,
            duration_seconds REAL,
            sample_rate INTEGER,
            channels INTEGER,
            bitrate INTEGER,
            codec TEXT,
            is_supported BOOLEAN,
            validation_result TEXT,
            validation_errors TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_file TEXT NOT NULL,
            converted_file TEXT,
            original_format TEXT,
            target_format TEXT,
            status TEXT,
            file_size_before INTEGER,
            file_size_after INTEGER,
            duration_before REAL,
            duration_after REAL,
            conversion_time REAL,
            quality_score REAL,
            errors TEXT,
            warnings TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS batch_jobs (
            job_id TEXT PRIMARY KEY,
            input_files TEXT,
            target_format TEXT,
            output_directory TEXT,
            total_files INTEGER,
            processed_files INTEGER,
            successful_conversions INTEGER,
            failed_conversions INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()

    def detect_file_format(self, file_path: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """Detect file format and extract metadata"""
        if not os.path.exists(file_path):
            return None, {"error": "File not found"}
        
        try:
            # Use python-magic for MIME type detection if available
            if magic:
                file_type = magic.from_file(file_path, mime=True)
            else:
                # Fallback MIME type detection based on extension
                file_ext = Path(file_path).suffix.lower().lstrip('.')
                mime_map = {
                    'wav': 'audio/wav',
                    'mp3': 'audio/mpeg',
                    'flac': 'audio/flac',
                    'm4a': 'audio/mp4',
                    'ogg': 'audio/ogg',
                    'aac': 'audio/aac',
                    'wma': 'audio/x-ms-wma'
                }
                file_type = mime_map.get(file_ext, 'application/octet-stream')
            
            # Extract audio metadata using ffprobe if available
            metadata = self._extract_audio_metadata(file_path)
            
            # Determine format from file extension and MIME type
            file_ext = Path(file_path).suffix.lower().lstrip('.')
            detected_format = self._determine_format(file_ext, file_type, metadata)
            
            return detected_format, metadata
            
        except Exception as e:
            return None, {"error": str(e)}

    def _extract_audio_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract audio metadata using ffprobe"""
        try:
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', file_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                metadata = json.loads(result.stdout)
                
                # Extract relevant audio information
                audio_info = {}
                if 'format' in metadata:
                    format_info = metadata['format']
                    audio_info['duration'] = float(format_info.get('duration', 0))
                    audio_info['size'] = int(format_info.get('size', 0))
                    audio_info['bitrate'] = int(format_info.get('bit_rate', 0))
                
                # Find audio stream
                if 'streams' in metadata:
                    for stream in metadata['streams']:
                        if stream.get('codec_type') == 'audio':
                            audio_info['codec'] = stream.get('codec_name')
                            audio_info['sample_rate'] = int(stream.get('sample_rate', 0))
                            audio_info['channels'] = int(stream.get('channels', 0))
                            break
                
                return audio_info
            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
            pass
        except FileNotFoundError:
            # ffprobe not available
            pass
        
        # Fallback to basic file info
        return {
            'size': os.path.getsize(file_path),
            'duration': None,
            'sample_rate': None,
            'channels': None,
            'bitrate': None,
            'codec': None
        }

    def _determine_format(self, file_ext: str, mime_type: str, metadata: Dict[str, Any]) -> Optional[str]:
        """Determine audio format from extension, MIME type, and metadata"""
        
        # Format mapping
        format_mapping = {
            'wav': AudioFormat.WAV,
            'mp3': AudioFormat.MP3,
            'flac': AudioFormat.FLAC,
            'm4a': AudioFormat.M4A,
            'ogg': AudioFormat.OGG,
            'aac': AudioFormat.AAC,
            'wma': AudioFormat.WMA,
            'aiff': AudioFormat.AIFF,
            'au': AudioFormat.AU,
            'mp4': AudioFormat.MP4,
            'webm': AudioFormat.WEBM,
            'mkv': AudioFormat.MKV
        }
        
        # MIME type mapping
        mime_mapping = {
            'audio/wav': AudioFormat.WAV,
            'audio/wave': AudioFormat.WAV,
            'audio/mpeg': AudioFormat.MP3,
            'audio/mp3': AudioFormat.MP3,
            'audio/flac': AudioFormat.FLAC,
            'audio/mp4': AudioFormat.M4A,
            'audio/x-m4a': AudioFormat.M4A,
            'audio/ogg': AudioFormat.OGG,
            'audio/aac': AudioFormat.AAC,
            'audio/x-ms-wma': AudioFormat.WMA,
            'audio/aiff': AudioFormat.AIFF,
            'audio/basic': AudioFormat.AU,
            'video/mp4': AudioFormat.MP4,
            'video/webm': AudioFormat.WEBM,
            'video/x-matroska': AudioFormat.MKV
        }
        
        # Try file extension first
        if file_ext in format_mapping:
            detected_format = format_mapping[file_ext]
        # Try MIME type
        elif mime_type in mime_mapping:
            detected_format = mime_mapping[mime_type]
        else:
            return None
        
        return detected_format.value

    def validate_file(self, file_path: str) -> FileFormatInfo:
        """Comprehensive file validation"""
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        file_hash = self._calculate_file_hash(file_path)
        
        # Detect format and metadata
        detected_format, metadata = self.detect_file_format(file_path)
        
        validation_errors = []
        validation_result = ValidationResult.VALID
        
        # Check file size
        if file_size > self.max_file_size:
            validation_errors.append(f"File too large: {file_size / (1024*1024):.1f}MB > {self.max_file_size / (1024*1024):.1f}MB")
            validation_result = ValidationResult.TOO_LARGE
        
        # Check format support
        is_supported = False
        if detected_format:
            try:
                format_enum = AudioFormat(detected_format)
                is_supported = format_enum in self.supported_formats
            except ValueError:
                validation_errors.append(f"Unknown format: {detected_format}")
                validation_result = ValidationResult.UNSUPPORTED
        else:
            validation_errors.append("Could not detect file format")
            validation_result = ValidationResult.INVALID_FORMAT
        
        if not is_supported and validation_result == ValidationResult.VALID:
            validation_result = ValidationResult.UNSUPPORTED
        
        # Check duration if available
        duration = metadata.get('duration')
        if duration is not None:
            if duration < self.min_duration:
                validation_errors.append(f"Audio too short: {duration:.2f}s < {self.min_duration}s")
                validation_result = ValidationResult.TOO_SHORT
            elif duration > self.max_duration:
                validation_errors.append(f"Audio too long: {duration:.2f}s > {self.max_duration}s")
                validation_result = ValidationResult.TOO_LARGE
        
        # Check for corruption indicators
        if 'error' in metadata:
            validation_errors.append(f"File corruption detected: {metadata['error']}")
            validation_result = ValidationResult.CORRUPTED
        
        file_info = FileFormatInfo(
            original_path=file_path,
            detected_format=detected_format,
            file_size=file_size,
            duration_seconds=metadata.get('duration'),
            sample_rate=metadata.get('sample_rate'),
            channels=metadata.get('channels'),
            bitrate=metadata.get('bitrate'),
            codec=metadata.get('codec'),
            is_supported=is_supported,
            validation_result=validation_result,
            validation_errors=validation_errors
        )
        
        # Store validation result
        self._store_validation_result(file_info, file_hash)
        
        return file_info

    def convert_audio_format(self, input_path: str, output_path: str, 
                           target_format: AudioFormat, quality_preset: str = "medium") -> ConversionResult:
        """Convert audio file to target format"""
        start_time = datetime.now()
        
        # Validate input file
        file_info = self.validate_file(input_path)
        
        if file_info.validation_result != ValidationResult.VALID:
            return ConversionResult(
                original_file=input_path,
                converted_file=None,
                original_format=file_info.detected_format or "unknown",
                target_format=target_format.value,
                status=ConversionStatus.FAILED,
                file_size_before=file_info.file_size,
                file_size_after=None,
                duration_before=file_info.duration_seconds,
                duration_after=None,
                conversion_time=None,
                quality_score=None,
                errors=[f"Input validation failed: {', '.join(file_info.validation_errors)}"]
            )
        
        try:
            # Build ffmpeg command
            cmd = self._build_conversion_command(input_path, output_path, target_format, quality_preset)
            
            # Execute conversion
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            conversion_time = (datetime.now() - start_time).total_seconds()
            
            if result.returncode == 0:
                # Validate converted file
                converted_info = self.validate_file(output_path)
                quality_score = self._calculate_quality_score(file_info, converted_info)
                
                conversion_result = ConversionResult(
                    original_file=input_path,
                    converted_file=output_path,
                    original_format=file_info.detected_format,
                    target_format=target_format.value,
                    status=ConversionStatus.SUCCESS,
                    file_size_before=file_info.file_size,
                    file_size_after=converted_info.file_size,
                    duration_before=file_info.duration_seconds,
                    duration_after=converted_info.duration_seconds,
                    conversion_time=conversion_time,
                    quality_score=quality_score,
                    warnings=self._extract_ffmpeg_warnings(result.stderr)
                )
            else:
                conversion_result = ConversionResult(
                    original_file=input_path,
                    converted_file=None,
                    original_format=file_info.detected_format,
                    target_format=target_format.value,
                    status=ConversionStatus.FAILED,
                    file_size_before=file_info.file_size,
                    file_size_after=None,
                    duration_before=file_info.duration_seconds,
                    duration_after=None,
                    conversion_time=conversion_time,
                    quality_score=None,
                    errors=[f"FFmpeg error: {result.stderr}"]
                )
        
        except subprocess.TimeoutExpired:
            conversion_result = ConversionResult(
                original_file=input_path,
                converted_file=None,
                original_format=file_info.detected_format,
                target_format=target_format.value,
                status=ConversionStatus.FAILED,
                file_size_before=file_info.file_size,
                file_size_after=None,
                duration_before=file_info.duration_seconds,
                duration_after=None,
                conversion_time=(datetime.now() - start_time).total_seconds(),
                quality_score=None,
                errors=["Conversion timeout (10 minutes exceeded)"]
            )
        except FileNotFoundError:
            conversion_result = ConversionResult(
                original_file=input_path,
                converted_file=None,
                original_format=file_info.detected_format,
                target_format=target_format.value,
                status=ConversionStatus.FAILED,
                file_size_before=file_info.file_size,
                file_size_after=None,
                duration_before=file_info.duration_seconds,
                duration_after=None,
                conversion_time=None,
                quality_score=None,
                errors=["FFmpeg not found. Please install FFmpeg."]
            )
        except Exception as e:
            conversion_result = ConversionResult(
                original_file=input_path,
                converted_file=None,
                original_format=file_info.detected_format,
                target_format=target_format.value,
                status=ConversionStatus.FAILED,
                file_size_before=file_info.file_size,
                file_size_after=None,
                duration_before=file_info.duration_seconds,
                duration_after=None,
                conversion_time=(datetime.now() - start_time).total_seconds(),
                quality_score=None,
                errors=[str(e)]
            )
        
        # Store conversion result
        self._store_conversion_result(conversion_result)
        
        return conversion_result

    def _build_conversion_command(self, input_path: str, output_path: str, 
                                target_format: AudioFormat, quality_preset: str) -> List[str]:
        """Build ffmpeg conversion command"""
        cmd = ['ffmpeg', '-i', input_path, '-y']  # -y to overwrite output
        
        # Quality presets
        quality_settings = {
            "low": {"bitrate": "64k", "sample_rate": "22050"},
            "medium": {"bitrate": "128k", "sample_rate": "44100"},
            "high": {"bitrate": "256k", "sample_rate": "44100"},
            "lossless": {"sample_rate": "44100"}
        }
        
        settings = quality_settings.get(quality_preset, quality_settings["medium"])
        
        # Format-specific encoding options
        if target_format == AudioFormat.WAV:
            cmd.extend(['-acodec', 'pcm_s16le'])
        elif target_format == AudioFormat.MP3:
            cmd.extend(['-acodec', 'libmp3lame', '-ab', settings["bitrate"]])
        elif target_format == AudioFormat.FLAC:
            cmd.extend(['-acodec', 'flac', '-compression_level', '5'])
        elif target_format == AudioFormat.M4A:
            cmd.extend(['-acodec', 'aac', '-ab', settings["bitrate"]])
        elif target_format == AudioFormat.OGG:
            cmd.extend(['-acodec', 'libvorbis', '-ab', settings["bitrate"]])
        
        # Set sample rate if specified
        if "sample_rate" in settings:
            cmd.extend(['-ar', settings["sample_rate"]])
        
        # Set to mono or stereo
        cmd.extend(['-ac', '2'])  # Stereo by default
        
        cmd.append(output_path)
        
        return cmd

    def _calculate_quality_score(self, original: FileFormatInfo, converted: FileFormatInfo) -> float:
        """Calculate conversion quality score (0-10)"""
        score = 10.0
        
        # Duration preservation
        if original.duration_seconds and converted.duration_seconds:
            duration_diff = abs(original.duration_seconds - converted.duration_seconds)
            if duration_diff > 0.1:
                score -= min(2.0, duration_diff * 2)
        
        # File size considerations
        if converted.file_size and original.file_size:
            size_ratio = converted.file_size / original.file_size
            if size_ratio > 2:  # Converted file much larger
                score -= 1.0
            elif size_ratio < 0.1:  # Converted file much smaller (quality loss)
                score -= 2.0
        
        # Sample rate considerations
        if original.sample_rate and converted.sample_rate:
            if converted.sample_rate < original.sample_rate:
                score -= 1.0
        
        # Channel considerations
        if original.channels and converted.channels:
            if converted.channels < original.channels:
                score -= 0.5
        
        return max(0.0, min(10.0, score))

    def _extract_ffmpeg_warnings(self, stderr: str) -> List[str]:
        """Extract warnings from ffmpeg stderr output"""
        warnings = []
        for line in stderr.split('\n'):
            if 'warning' in line.lower() or 'deprecated' in line.lower():
                warnings.append(line.strip())
        return warnings

    def create_batch_conversion_job(self, input_files: List[str], target_format: AudioFormat,
                                  output_directory: str) -> BatchConversionJob:
        """Create and execute batch conversion job"""
        job_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(str(input_files).encode()).hexdigest()[:8]}"
        
        # Ensure output directory exists
        os.makedirs(output_directory, exist_ok=True)
        
        job = BatchConversionJob(
            job_id=job_id,
            input_files=input_files,
            target_format=target_format,
            output_directory=output_directory,
            total_files=len(input_files),
            start_time=datetime.now()
        )
        
        # Store job in database
        self._store_batch_job(job)
        
        # Process files
        for input_file in input_files:
            try:
                input_path = Path(input_file)
                output_filename = f"{input_path.stem}.{target_format.value}"
                output_path = os.path.join(output_directory, output_filename)
                
                result = self.convert_audio_format(input_file, output_path, target_format)
                job.results.append(result)
                
                if result.status == ConversionStatus.SUCCESS:
                    job.successful_conversions += 1
                else:
                    job.failed_conversions += 1
                
                job.processed_files += 1
                
                # Update job progress in database
                self._update_batch_job_progress(job)
                
            except Exception as e:
                error_result = ConversionResult(
                    original_file=input_file,
                    converted_file=None,
                    original_format="unknown",
                    target_format=target_format.value,
                    status=ConversionStatus.FAILED,
                    file_size_before=0,
                    file_size_after=None,
                    duration_before=None,
                    duration_after=None,
                    conversion_time=None,
                    quality_score=None,
                    errors=[str(e)]
                )
                job.results.append(error_result)
                job.failed_conversions += 1
                job.processed_files += 1
        
        job.end_time = datetime.now()
        self._finalize_batch_job(job)
        
        return job

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get information about supported formats"""
        return {
            "input_formats": {
                "supported": [fmt.value for fmt in AudioFormat],
                "recommended": [fmt.value for fmt in self.supported_formats],
                "description": "All formats can be read, recommended formats have full feature support"
            },
            "output_formats": {
                "supported": [fmt.value for fmt in self.supported_formats],
                "default": AudioFormat.WAV.value,
                "description": "Formats available for conversion output"
            },
            "quality_presets": {
                "low": "64kbps, 22kHz - Smallest file size",
                "medium": "128kbps, 44kHz - Balanced quality/size",
                "high": "256kbps, 44kHz - High quality",
                "lossless": "44kHz - Maximum quality, larger files"
            },
            "limitations": {
                "max_file_size_mb": self.max_file_size // (1024 * 1024),
                "max_duration_minutes": self.max_duration // 60,
                "min_duration_seconds": self.min_duration
            }
        }

    def get_conversion_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent conversion history"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT * FROM conversions 
        ORDER BY created_at DESC 
        LIMIT ?
        ''', (limit,))
        
        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row[0],
                "original_file": row[1],
                "converted_file": row[2],
                "original_format": row[3],
                "target_format": row[4],
                "status": row[5],
                "file_size_before": row[6],
                "file_size_after": row[7],
                "duration_before": row[8],
                "duration_after": row[9],
                "conversion_time": row[10],
                "quality_score": row[11],
                "errors": json.loads(row[12]) if row[12] else [],
                "warnings": json.loads(row[13]) if row[13] else [],
                "created_at": row[14]
            })
        
        conn.close()
        return results

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file"""
        if not os.path.exists(file_path):
            return ""
        
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
        except Exception:
            return ""
        
        return hash_sha256.hexdigest()

    def _store_validation_result(self, file_info: FileFormatInfo, file_hash: str):
        """Store validation result in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO file_validations (
            file_path, file_hash, detected_format, file_size, duration_seconds,
            sample_rate, channels, bitrate, codec, is_supported, 
            validation_result, validation_errors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            file_info.original_path,
            file_hash,
            file_info.detected_format,
            file_info.file_size,
            file_info.duration_seconds,
            file_info.sample_rate,
            file_info.channels,
            file_info.bitrate,
            file_info.codec,
            file_info.is_supported,
            file_info.validation_result.value,
            json.dumps(file_info.validation_errors)
        ))
        
        conn.commit()
        conn.close()

    def _store_conversion_result(self, result: ConversionResult):
        """Store conversion result in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO conversions (
            original_file, converted_file, original_format, target_format, status,
            file_size_before, file_size_after, duration_before, duration_after,
            conversion_time, quality_score, errors, warnings
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.original_file,
            result.converted_file,
            result.original_format,
            result.target_format,
            result.status.value,
            result.file_size_before,
            result.file_size_after,
            result.duration_before,
            result.duration_after,
            result.conversion_time,
            result.quality_score,
            json.dumps(result.errors),
            json.dumps(result.warnings)
        ))
        
        conn.commit()
        conn.close()

    def _store_batch_job(self, job: BatchConversionJob):
        """Store batch job in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO batch_jobs (
            job_id, input_files, target_format, output_directory, total_files,
            processed_files, successful_conversions, failed_conversions,
            start_time, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            job.job_id,
            json.dumps(job.input_files),
            job.target_format.value,
            job.output_directory,
            job.total_files,
            job.processed_files,
            job.successful_conversions,
            job.failed_conversions,
            job.start_time.isoformat() if job.start_time else None,
            "in_progress"
        ))
        
        conn.commit()
        conn.close()

    def _update_batch_job_progress(self, job: BatchConversionJob):
        """Update batch job progress in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE batch_jobs SET 
            processed_files = ?, 
            successful_conversions = ?, 
            failed_conversions = ?
        WHERE job_id = ?
        ''', (
            job.processed_files,
            job.successful_conversions,
            job.failed_conversions,
            job.job_id
        ))
        
        conn.commit()
        conn.close()

    def _finalize_batch_job(self, job: BatchConversionJob):
        """Finalize batch job in database"""
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE batch_jobs SET 
            end_time = ?, 
            status = ?
        WHERE job_id = ?
        ''', (
            job.end_time.isoformat() if job.end_time else None,
            "completed",
            job.job_id
        ))
        
        conn.commit()
        conn.close()


def demo_file_format_system():
    """Demonstrate the comprehensive file format system"""
    print("🎵 Comprehensive File Format System Demo")
    print("=" * 50)
    
    # Initialize system
    system = ComprehensiveFileFormatSystem()
    
    # Create test audio files
    test_files = []
    
    # Create a mock WAV file for testing
    test_wav_path = "/tmp/test_audio.wav"
    try:
        # Create a simple sine wave WAV file using numpy if available
        try:
            import numpy as np
            import wave
            
            sample_rate = 44100
            duration = 2.0  # seconds
            frequency = 440  # A4 note
            
            # Generate sine wave
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave_data = np.sin(frequency * 2 * np.pi * t)
            
            # Convert to 16-bit integers
            wave_data = (wave_data * 32767).astype(np.int16)
            
            # Write WAV file
            with wave.open(test_wav_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(wave_data.tobytes())
            
            test_files.append(test_wav_path)
            print(f"✅ Created test WAV file: {test_wav_path}")
            
        except ImportError:
            print("⚠️  NumPy not available, skipping WAV file creation")
    
    except Exception as e:
        print(f"⚠️  Could not create test WAV file: {e}")
    
    # 1. Show supported formats
    print("\n📋 Supported Formats:")
    formats_info = system.get_supported_formats()
    print(f"Input formats: {', '.join(formats_info['input_formats']['supported'])}")
    print(f"Output formats: {', '.join(formats_info['output_formats']['supported'])}")
    print(f"Quality presets: {list(formats_info['quality_presets'].keys())}")
    
    # 2. Validate a file if we have one
    if test_files:
        print(f"\n🔍 Validating file: {test_files[0]}")
        validation_result = system.validate_file(test_files[0])
        
        print(f"Detected format: {validation_result.detected_format}")
        print(f"File size: {validation_result.file_size:,} bytes")
        print(f"Duration: {validation_result.duration_seconds:.2f}s" if validation_result.duration_seconds else "Duration: Unknown")
        print(f"Sample rate: {validation_result.sample_rate}Hz" if validation_result.sample_rate else "Sample rate: Unknown")
        print(f"Channels: {validation_result.channels}" if validation_result.channels else "Channels: Unknown")
        print(f"Is supported: {validation_result.is_supported}")
        print(f"Validation result: {validation_result.validation_result.value}")
        
        if validation_result.validation_errors:
            print(f"Validation errors: {', '.join(validation_result.validation_errors)}")
        
        # 3. Convert file to different format
        if validation_result.is_supported:
            print(f"\n🔄 Converting to MP3 format...")
            output_path = "/tmp/converted_audio.mp3"
            
            conversion_result = system.convert_audio_format(
                test_files[0], 
                output_path, 
                AudioFormat.MP3,
                "medium"
            )
            
            print(f"Conversion status: {conversion_result.status.value}")
            if conversion_result.status == ConversionStatus.SUCCESS:
                print(f"Output file: {conversion_result.converted_file}")
                print(f"Original size: {conversion_result.file_size_before:,} bytes")
                print(f"Converted size: {conversion_result.file_size_after:,} bytes")
                print(f"Quality score: {conversion_result.quality_score:.1f}/10")
                print(f"Conversion time: {conversion_result.conversion_time:.2f}s")
                
                if conversion_result.warnings:
                    print(f"Warnings: {len(conversion_result.warnings)} warning(s)")
            else:
                print(f"Conversion errors: {', '.join(conversion_result.errors)}")
        
        # 4. Batch conversion demo
        print(f"\n📦 Batch Conversion Demo...")
        batch_job = system.create_batch_conversion_job(
            test_files,
            AudioFormat.FLAC,
            "/tmp/batch_output"
        )
        
        print(f"Batch job ID: {batch_job.job_id}")
        print(f"Total files: {batch_job.total_files}")
        print(f"Processed files: {batch_job.processed_files}")
        print(f"Successful conversions: {batch_job.successful_conversions}")
        print(f"Failed conversions: {batch_job.failed_conversions}")
        
        if batch_job.start_time and batch_job.end_time:
            duration = (batch_job.end_time - batch_job.start_time).total_seconds()
            print(f"Total processing time: {duration:.2f}s")
    
    # 5. Show conversion history
    print(f"\n📊 Recent Conversions:")
    history = system.get_conversion_history(5)
    
    if history:
        for i, conversion in enumerate(history[:3], 1):
            print(f"{i}. {Path(conversion['original_file']).name} → {conversion['target_format']} ({conversion['status']})")
    else:
        print("No conversion history found")
    
    # 6. System statistics
    print(f"\n📈 System Statistics:")
    conn = sqlite3.connect(system.database_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM file_validations")
    validation_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM conversions")
    conversion_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM batch_jobs")
    batch_job_count = cursor.fetchone()[0]
    
    print(f"Total validations performed: {validation_count}")
    print(f"Total conversions performed: {conversion_count}")
    print(f"Total batch jobs: {batch_job_count}")
    
    conn.close()
    
    # Cleanup test files
    for test_file in test_files:
        try:
            os.remove(test_file)
        except:
            pass
    
    try:
        os.remove("/tmp/converted_audio.mp3")
        shutil.rmtree("/tmp/batch_output", ignore_errors=True)
    except:
        pass
    
    print(f"\n✅ File format system demonstration complete!")
    print(f"Database: {system.database_path}")


if __name__ == "__main__":
    demo_file_format_system()