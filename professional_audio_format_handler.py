"""
Professional Audio Format Handler
Task 3: Professional Audio Format Handling and Conversion

Comprehensive audio format support and conversion system with professional
codec support, metadata preservation, batch processing, and quality assessment.

Requirements: 1.3
Dependencies: Multi-channel audio engine, spatial audio processor
"""

import os
import asyncio
import tempfile
import logging
import json
import uuid
import hashlib
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor, as_completed

# Core audio processing libraries
import numpy as np
import soundfile as sf
import librosa
import scipy.signal

# Third-party imports with fallbacks
try:
    import mutagen
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM
    from mutagen.flac import FLAC
    from mutagen.mp4 import MP4
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False
    logging.warning("Mutagen not available - metadata support will be limited")

try:
    import pydub
    from pydub import AudioSegment
    from pydub.utils import which
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("PyDub not available - some format conversions will be limited")

try:
    import ffmpeg
    FFMPEG_AVAILABLE = True
except ImportError:
    FFMPEG_AVAILABLE = False
    logging.warning("FFmpeg-python not available - advanced codec support limited")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    FLAC = "flac"
    MP3 = "mp3"
    AAC = "aac"
    M4A = "m4a"
    OGG = "ogg"
    OPUS = "opus"
    AIFF = "aiff"
    AU = "au"
    CAF = "caf"
    WMA = "wma"
    AC3 = "ac3"
    DTS = "dts"
    ALAC = "alac"
    APE = "ape"
    WV = "wv"  # WavPack


class AudioCodec(Enum):
    """Supported audio codecs"""
    PCM = "pcm"
    FLAC = "flac"
    MP3 = "mp3"
    AAC = "aac"
    OPUS = "opus"
    VORBIS = "vorbis"
    ALAC = "alac"
    APE = "ape"
    WAVPACK = "wavpack"
    DTS = "dts"
    AC3 = "ac3"
    EAC3 = "eac3"


class QualityLevel(Enum):
    """Audio quality levels"""
    DRAFT = "draft"          # Low quality, small file size
    STANDARD = "standard"    # Standard quality
    HIGH = "high"           # High quality
    LOSSLESS = "lossless"   # Lossless compression
    ARCHIVE = "archive"     # Maximum quality for archival


class ConversionMode(Enum):
    """Conversion processing modes"""
    FAST = "fast"           # Prioritize speed
    BALANCED = "balanced"   # Balance speed and quality
    QUALITY = "quality"     # Prioritize quality
    CUSTOM = "custom"       # Custom settings


@dataclass
class AudioMetadata:
    """Comprehensive audio metadata"""
    # Basic metadata
    title: Optional[str] = None
    artist: Optional[str] = None
    album: Optional[str] = None
    year: Optional[int] = None
    genre: Optional[str] = None
    track_number: Optional[int] = None
    total_tracks: Optional[int] = None
    
    # Technical metadata
    duration: Optional[float] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    
    # Professional metadata
    engineer: Optional[str] = None
    producer: Optional[str] = None
    studio: Optional[str] = None
    recording_date: Optional[str] = None
    mastering_date: Optional[str] = None
    isrc: Optional[str] = None
    catalog_number: Optional[str] = None
    
    # Quality metrics
    peak_level: Optional[float] = None
    rms_level: Optional[float] = None
    dynamic_range: Optional[float] = None
    lufs: Optional[float] = None
    
    # Custom metadata
    custom_tags: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FormatInfo:
    """Information about an audio format"""
    format: AudioFormat
    codec: AudioCodec
    supports_metadata: bool
    supports_multichannel: bool
    max_channels: int
    max_sample_rate: int
    max_bit_depth: int
    is_lossless: bool
    typical_bitrates: List[int]
    file_extensions: List[str]


@dataclass
class ConversionSettings:
    """Settings for audio format conversion"""
    target_format: AudioFormat
    target_codec: Optional[AudioCodec] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    bit_depth: Optional[int] = None
    bitrate: Optional[int] = None
    quality_level: QualityLevel = QualityLevel.STANDARD
    conversion_mode: ConversionMode = ConversionMode.BALANCED
    preserve_metadata: bool = True
    normalize_audio: bool = False
    apply_dithering: bool = True
    custom_parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConversionResult:
    """Result of audio format conversion"""
    success: bool
    input_file: str
    output_file: Optional[str] = None
    original_format: Optional[AudioFormat] = None
    target_format: Optional[AudioFormat] = None
    original_size: Optional[int] = None
    converted_size: Optional[int] = None
    compression_ratio: Optional[float] = None
    processing_time: Optional[float] = None
    quality_metrics: Dict[str, float] = field(default_factory=dict)
    error_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


@dataclass
class BatchProcessingJob:
    """Batch processing job configuration"""
    job_id: str
    input_files: List[str]
    output_directory: str
    conversion_settings: ConversionSettings
    parallel_workers: int = 4
    progress_callback: Optional[callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    results: List[ConversionResult] = field(default_factory=list)


class ProfessionalAudioFormatHandler:
    """
    Professional audio format handler with comprehensive format support,
    metadata preservation, and batch processing capabilities.
    """
    
    def __init__(self, temp_dir: Optional[str] = None, max_workers: int = 4):
        """
        Initialize the professional audio format handler
        
        Args:
            temp_dir: Directory for temporary files
            max_workers: Maximum number of worker threads for batch processing
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
        # Initialize format support
        self._initialize_format_support()
        
        # Initialize codec configurations
        self._initialize_codec_configs()
        
        # Processing statistics
        self.processing_stats = {
            'total_conversions': 0,
            'successful_conversions': 0,
            'failed_conversions': 0,
            'total_processing_time': 0.0,
            'formats_processed': {},
            'average_compression_ratio': 0.0
        }
        
        logger.info(f"ProfessionalAudioFormatHandler initialized with {max_workers} workers")
    
    def _initialize_format_support(self):
        """Initialize supported format information"""
        self.format_info = {
            AudioFormat.WAV: FormatInfo(
                format=AudioFormat.WAV,
                codec=AudioCodec.PCM,
                supports_metadata=True,
                supports_multichannel=True,
                max_channels=32,
                max_sample_rate=192000,
                max_bit_depth=32,
                is_lossless=True,
                typical_bitrates=[1411, 2822, 4608, 9216],  # kbps for different configs
                file_extensions=['.wav']
            ),
            AudioFormat.FLAC: FormatInfo(
                format=AudioFormat.FLAC,
                codec=AudioCodec.FLAC,
                supports_metadata=True,
                supports_multichannel=True,
                max_channels=8,
                max_sample_rate=655350,
                max_bit_depth=32,
                is_lossless=True,
                typical_bitrates=[700, 1000, 1400],
                file_extensions=['.flac']
            ),
            AudioFormat.MP3: FormatInfo(
                format=AudioFormat.MP3,
                codec=AudioCodec.MP3,
                supports_metadata=True,
                supports_multichannel=False,
                max_channels=2,
                max_sample_rate=48000,
                max_bit_depth=16,
                is_lossless=False,
                typical_bitrates=[128, 192, 256, 320],
                file_extensions=['.mp3']
            ),
            AudioFormat.AAC: FormatInfo(
                format=AudioFormat.AAC,
                codec=AudioCodec.AAC,
                supports_metadata=True,
                supports_multichannel=True,
                max_channels=8,
                max_sample_rate=96000,
                max_bit_depth=16,
                is_lossless=False,
                typical_bitrates=[128, 192, 256, 320],
                file_extensions=['.aac', '.m4a']
            ),
            AudioFormat.OGG: FormatInfo(
                format=AudioFormat.OGG,
                codec=AudioCodec.VORBIS,
                supports_metadata=True,
                supports_multichannel=True,
                max_channels=8,
                max_sample_rate=192000,
                max_bit_depth=16,
                is_lossless=False,
                typical_bitrates=[128, 192, 256, 320],
                file_extensions=['.ogg']
            ),
            AudioFormat.OPUS: FormatInfo(
                format=AudioFormat.OPUS,
                codec=AudioCodec.OPUS,
                supports_metadata=True,
                supports_multichannel=True,
                max_channels=8,
                max_sample_rate=48000,
                max_bit_depth=16,
                is_lossless=False,
                typical_bitrates=[64, 96, 128, 192],
                file_extensions=['.opus']
            ),
            AudioFormat.AIFF: FormatInfo(
                format=AudioFormat.AIFF,
                codec=AudioCodec.PCM,
                supports_metadata=True,
                supports_multichannel=True,
                max_channels=32,
                max_sample_rate=192000,
                max_bit_depth=32,
                is_lossless=True,
                typical_bitrates=[1411, 2822, 4608, 9216],
                file_extensions=['.aiff', '.aif']
            )
        }
    
    def _initialize_codec_configs(self):
        """Initialize codec-specific configurations"""
        self.codec_configs = {
            AudioCodec.MP3: {
                'quality_settings': {
                    QualityLevel.DRAFT: {'bitrate': 96, 'vbr': True},
                    QualityLevel.STANDARD: {'bitrate': 192, 'vbr': True},
                    QualityLevel.HIGH: {'bitrate': 256, 'vbr': False},
                    QualityLevel.LOSSLESS: {'bitrate': 320, 'vbr': False}
                },
                'encoder_options': {
                    'joint_stereo': True,
                    'lowpass_filter': True,
                    'psychoacoustic_model': 2
                }
            },
            AudioCodec.AAC: {
                'quality_settings': {
                    QualityLevel.DRAFT: {'bitrate': 96, 'profile': 'aac_low'},
                    QualityLevel.STANDARD: {'bitrate': 128, 'profile': 'aac_low'},
                    QualityLevel.HIGH: {'bitrate': 256, 'profile': 'aac_low'},
                    QualityLevel.LOSSLESS: {'bitrate': 320, 'profile': 'aac_low'}
                },
                'encoder_options': {
                    'cutoff_frequency': 18000,
                    'bandwidth': 'auto'
                }
            },
            AudioCodec.FLAC: {
                'quality_settings': {
                    QualityLevel.DRAFT: {'compression_level': 0},
                    QualityLevel.STANDARD: {'compression_level': 5},
                    QualityLevel.HIGH: {'compression_level': 8},
                    QualityLevel.LOSSLESS: {'compression_level': 8},
                    QualityLevel.ARCHIVE: {'compression_level': 8}
                },
                'encoder_options': {
                    'verify': True,
                    'md5_signature': True
                }
            },
            AudioCodec.OPUS: {
                'quality_settings': {
                    QualityLevel.DRAFT: {'bitrate': 64, 'application': 'audio'},
                    QualityLevel.STANDARD: {'bitrate': 96, 'application': 'audio'},
                    QualityLevel.HIGH: {'bitrate': 128, 'application': 'audio'},
                    QualityLevel.LOSSLESS: {'bitrate': 192, 'application': 'audio'}
                },
                'encoder_options': {
                    'frame_duration': 20,  # ms
                    'complexity': 10
                }
            }
        }
    
    async def detect_format(self, file_path: str) -> Tuple[AudioFormat, AudioMetadata]:
        """Detect audio format and extract metadata"""
        try:
            # Get file extension
            file_ext = Path(file_path).suffix.lower()
            
            # Try to detect format from extension first
            detected_format = None
            for format_enum, info in self.format_info.items():
                if file_ext in info.file_extensions:
                    detected_format = format_enum
                    break
            
            # If not detected by extension, try to read with soundfile
            if not detected_format:
                try:
                    info = sf.info(file_path)
                    # Map soundfile format to our enum
                    format_mapping = {
                        'WAV': AudioFormat.WAV,
                        'FLAC': AudioFormat.FLAC,
                        'AIFF': AudioFormat.AIFF,
                        'OGG': AudioFormat.OGG
                    }
                    detected_format = format_mapping.get(info.format, AudioFormat.WAV)
                except:
                    detected_format = AudioFormat.WAV  # Default fallback
            
            # Extract metadata
            metadata = await self._extract_metadata(file_path, detected_format)
            
            return detected_format, metadata
            
        except Exception as e:
            logger.error(f"Failed to detect format for {file_path}: {e}")
            # Return default format with basic metadata
            basic_metadata = AudioMetadata()
            try:
                info = sf.info(file_path)
                basic_metadata.duration = info.duration
                basic_metadata.sample_rate = info.samplerate
                basic_metadata.channels = info.channels
            except:
                pass
            
            return AudioFormat.WAV, basic_metadata
    
    async def _extract_metadata(self, file_path: str, format: AudioFormat) -> AudioMetadata:
        """Extract comprehensive metadata from audio file"""
        metadata = AudioMetadata()
        
        try:
            # Extract technical metadata using soundfile
            info = sf.info(file_path)
            metadata.duration = info.duration
            metadata.sample_rate = info.samplerate
            metadata.channels = info.channels
            
            # Try to get bit depth and other info
            try:
                metadata.bit_depth = {'PCM_16': 16, 'PCM_24': 24, 'PCM_32': 32, 'FLOAT': 32}.get(info.subtype, 16)
            except:
                metadata.bit_depth = 16
            
            # Calculate file size and bitrate
            file_size = os.path.getsize(file_path)
            if metadata.duration and metadata.duration > 0:
                metadata.bitrate = int((file_size * 8) / metadata.duration / 1000)  # kbps
            
            # Extract metadata tags if mutagen is available
            if MUTAGEN_AVAILABLE:
                metadata = await self._extract_tags_with_mutagen(file_path, metadata, format)
            
            # Calculate audio quality metrics
            metadata = await self._calculate_quality_metrics(file_path, metadata)
            
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path}: {e}")
        
        return metadata
    
    async def _extract_tags_with_mutagen(self, file_path: str, metadata: AudioMetadata, format: AudioFormat) -> AudioMetadata:
        """Extract metadata tags using mutagen"""
        try:
            audio_file = mutagen.File(file_path)
            if audio_file is None:
                return metadata
            
            # Common tag mappings
            tag_mappings = {
                'title': ['TIT2', 'TITLE', '\xa9nam'],
                'artist': ['TPE1', 'ARTIST', '\xa9ART'],
                'album': ['TALB', 'ALBUM', '\xa9alb'],
                'year': ['TDRC', 'DATE', '\xa9day'],
                'genre': ['TCON', 'GENRE', '\xa9gen'],
                'track_number': ['TRCK', 'TRACKNUMBER', 'trkn']
            }
            
            # Extract standard tags
            for field, possible_keys in tag_mappings.items():
                for key in possible_keys:
                    if key in audio_file:
                        value = audio_file[key]
                        if isinstance(value, list) and len(value) > 0:
                            value = value[0]
                        
                        # Convert to appropriate type
                        if field == 'year' and isinstance(value, str):
                            try:
                                value = int(value[:4])  # Extract year from date string
                            except:
                                continue
                        elif field == 'track_number':
                            if isinstance(value, str) and '/' in value:
                                try:
                                    track, total = value.split('/')
                                    metadata.track_number = int(track)
                                    metadata.total_tracks = int(total)
                                    continue
                                except:
                                    pass
                            try:
                                value = int(str(value))
                            except:
                                continue
                        
                        setattr(metadata, field, value)
                        break
            
            # Extract professional metadata
            professional_tags = {
                'engineer': ['TENG', 'ENGINEER'],
                'producer': ['TPRO', 'PRODUCER'],
                'studio': ['TSTU', 'STUDIO'],
                'isrc': ['TSRC', 'ISRC'],
                'catalog_number': ['TCOP', 'CATALOGNUMBER']
            }
            
            for field, possible_keys in professional_tags.items():
                for key in possible_keys:
                    if key in audio_file:
                        value = audio_file[key]
                        if isinstance(value, list) and len(value) > 0:
                            value = str(value[0])
                        setattr(metadata, field, value)
                        break
            
            # Store all other tags in custom_tags
            for key, value in audio_file.items():
                if key not in [k for keys in tag_mappings.values() for k in keys]:
                    if isinstance(value, list) and len(value) > 0:
                        value = value[0]
                    metadata.custom_tags[key] = str(value)
        
        except Exception as e:
            logger.error(f"Failed to extract tags with mutagen: {e}")
        
        return metadata
    
    async def _calculate_quality_metrics(self, file_path: str, metadata: AudioMetadata) -> AudioMetadata:
        """Calculate audio quality metrics"""
        try:
            # Load audio for analysis
            audio_data, sample_rate = librosa.load(file_path, sr=None, mono=False)
            
            # Handle mono/stereo
            if audio_data.ndim == 1:
                mono_audio = audio_data
            else:
                mono_audio = librosa.to_mono(audio_data)
            
            # Calculate peak level
            metadata.peak_level = float(np.max(np.abs(mono_audio)))
            
            # Calculate RMS level
            metadata.rms_level = float(np.sqrt(np.mean(mono_audio**2)))
            
            # Calculate dynamic range (simplified)
            if metadata.peak_level > 0 and metadata.rms_level > 0:
                metadata.dynamic_range = float(20 * np.log10(metadata.peak_level / metadata.rms_level))
            
            # Estimate LUFS (simplified calculation)
            # This is a basic approximation - proper LUFS requires more complex filtering
            if metadata.rms_level > 0:
                metadata.lufs = float(-0.691 + 10 * np.log10(metadata.rms_level**2))
        
        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {e}")
        
        return metadata
    
    async def convert_format(self, input_file: str, output_file: str, 
                           settings: ConversionSettings) -> ConversionResult:
        """Convert audio file to different format"""
        start_time = datetime.now()
        
        try:
            # Detect input format
            input_format, input_metadata = await self.detect_format(input_file)
            
            # Validate conversion settings
            settings = self._validate_conversion_settings(settings, input_metadata)
            
            # Get file sizes
            original_size = os.path.getsize(input_file)
            
            # Perform conversion based on available libraries
            success = False
            error_message = None
            warnings = []
            
            # Try different conversion methods in order of preference
            if FFMPEG_AVAILABLE:
                success, error_message, warnings = await self._convert_with_ffmpeg(
                    input_file, output_file, settings, input_metadata
                )
            elif PYDUB_AVAILABLE:
                success, error_message, warnings = await self._convert_with_pydub(
                    input_file, output_file, settings, input_metadata
                )
            else:
                success, error_message, warnings = await self._convert_with_soundfile(
                    input_file, output_file, settings, input_metadata
                )
            
            # Calculate results
            processing_time = (datetime.now() - start_time).total_seconds()
            
            if success and os.path.exists(output_file):
                converted_size = os.path.getsize(output_file)
                compression_ratio = original_size / converted_size if converted_size > 0 else 1.0
                
                # Preserve metadata if requested
                if settings.preserve_metadata:
                    await self._preserve_metadata(input_file, output_file, input_metadata, settings.target_format)
                
                # Calculate quality metrics
                quality_metrics = await self._calculate_conversion_quality_metrics(
                    input_file, output_file
                )
                
                # Update statistics
                self._update_processing_stats(True, processing_time, input_format, settings.target_format, compression_ratio)
                
                return ConversionResult(
                    success=True,
                    input_file=input_file,
                    output_file=output_file,
                    original_format=input_format,
                    target_format=settings.target_format,
                    original_size=original_size,
                    converted_size=converted_size,
                    compression_ratio=compression_ratio,
                    processing_time=processing_time,
                    quality_metrics=quality_metrics,
                    warnings=warnings
                )
            else:
                self._update_processing_stats(False, processing_time, input_format, settings.target_format)
                
                return ConversionResult(
                    success=False,
                    input_file=input_file,
                    original_format=input_format,
                    target_format=settings.target_format,
                    original_size=original_size,
                    processing_time=processing_time,
                    error_message=error_message or "Conversion failed"
                )
        
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"Conversion failed: {e}")
            
            return ConversionResult(
                success=False,
                input_file=input_file,
                processing_time=processing_time,
                error_message=str(e)
            )
    
    def _validate_conversion_settings(self, settings: ConversionSettings, 
                                    input_metadata: AudioMetadata) -> ConversionSettings:
        """Validate and adjust conversion settings"""
        # Get target format info
        target_info = self.format_info.get(settings.target_format)
        if not target_info:
            raise ValueError(f"Unsupported target format: {settings.target_format}")
        
        # Validate sample rate
        if settings.sample_rate:
            if settings.sample_rate > target_info.max_sample_rate:
                settings.sample_rate = target_info.max_sample_rate
                logger.warning(f"Sample rate reduced to {settings.sample_rate} for {settings.target_format}")
        
        # Validate channels
        if settings.channels:
            if settings.channels > target_info.max_channels:
                settings.channels = target_info.max_channels
                logger.warning(f"Channels reduced to {settings.channels} for {settings.target_format}")
        
        # Validate bit depth
        if settings.bit_depth:
            if settings.bit_depth > target_info.max_bit_depth:
                settings.bit_depth = target_info.max_bit_depth
                logger.warning(f"Bit depth reduced to {settings.bit_depth} for {settings.target_format}")
        
        # Set codec if not specified
        if not settings.target_codec:
            settings.target_codec = target_info.codec
        
        # Validate bitrate for lossy formats
        if not target_info.is_lossless and settings.bitrate:
            if settings.bitrate not in target_info.typical_bitrates:
                # Find closest bitrate
                closest_bitrate = min(target_info.typical_bitrates, 
                                    key=lambda x: abs(x - settings.bitrate))
                settings.bitrate = closest_bitrate
                logger.warning(f"Bitrate adjusted to {settings.bitrate} kbps")
        
        return settings    asy
nc def _convert_with_ffmpeg(self, input_file: str, output_file: str,
                                 settings: ConversionSettings, 
                                 input_metadata: AudioMetadata) -> Tuple[bool, Optional[str], List[str]]:
        """Convert audio using FFmpeg"""
        try:
            warnings = []
            
            # Build FFmpeg command
            input_stream = ffmpeg.input(input_file)
            
            # Apply audio filters and settings
            audio_filters = []
            output_options = {}
            
            # Sample rate conversion
            if settings.sample_rate and settings.sample_rate != input_metadata.sample_rate:
                audio_filters.append(f'aresample={settings.sample_rate}')
            
            # Channel conversion
            if settings.channels and settings.channels != input_metadata.channels:
                if settings.channels == 1:
                    audio_filters.append('pan=mono|c0=0.5*c0+0.5*c1')
                elif settings.channels == 2 and input_metadata.channels == 1:
                    audio_filters.append('pan=stereo|c0=c0|c1=c0')
                else:
                    audio_filters.append(f'pan=stereo|c0=c0|c1=c1')
            
            # Normalization
            if settings.normalize_audio:
                audio_filters.append('loudnorm')
            
            # Apply codec-specific settings
            codec_settings = self._get_ffmpeg_codec_settings(settings)
            output_options.update(codec_settings)
            
            # Apply audio filters
            if audio_filters:
                audio_stream = input_stream.audio.filter('af', ','.join(audio_filters))
            else:
                audio_stream = input_stream.audio
            
            # Create output
            output_stream = ffmpeg.output(audio_stream, output_file, **output_options)
            
            # Run conversion
            ffmpeg.run(output_stream, overwrite_output=True, quiet=True)
            
            return True, None, warnings
            
        except ffmpeg.Error as e:
            error_msg = f"FFmpeg conversion failed: {e.stderr.decode() if e.stderr else str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
        except Exception as e:
            error_msg = f"FFmpeg conversion error: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
    
    def _get_ffmpeg_codec_settings(self, settings: ConversionSettings) -> Dict[str, Any]:
        """Get FFmpeg codec-specific settings"""
        codec_settings = {}
        
        if settings.target_format == AudioFormat.MP3:
            codec_settings['acodec'] = 'libmp3lame'
            if settings.bitrate:
                codec_settings['audio_bitrate'] = f'{settings.bitrate}k'
            
            quality_config = self.codec_configs[AudioCodec.MP3]['quality_settings'].get(
                settings.quality_level, {}
            )
            if quality_config.get('vbr'):
                codec_settings['q:a'] = 2  # VBR quality
        
        elif settings.target_format == AudioFormat.AAC:
            codec_settings['acodec'] = 'aac'
            if settings.bitrate:
                codec_settings['audio_bitrate'] = f'{settings.bitrate}k'
        
        elif settings.target_format == AudioFormat.FLAC:
            codec_settings['acodec'] = 'flac'
            quality_config = self.codec_configs[AudioCodec.FLAC]['quality_settings'].get(
                settings.quality_level, {}
            )
            if 'compression_level' in quality_config:
                codec_settings['compression_level'] = quality_config['compression_level']
        
        elif settings.target_format == AudioFormat.OPUS:
            codec_settings['acodec'] = 'libopus'
            if settings.bitrate:
                codec_settings['audio_bitrate'] = f'{settings.bitrate}k'
        
        elif settings.target_format == AudioFormat.OGG:
            codec_settings['acodec'] = 'libvorbis'
            if settings.bitrate:
                codec_settings['audio_bitrate'] = f'{settings.bitrate}k'
        
        elif settings.target_format == AudioFormat.WAV:
            codec_settings['acodec'] = 'pcm_s16le'
            if settings.bit_depth == 24:
                codec_settings['acodec'] = 'pcm_s24le'
            elif settings.bit_depth == 32:
                codec_settings['acodec'] = 'pcm_s32le'
        
        # Add sample rate if specified
        if settings.sample_rate:
            codec_settings['ar'] = settings.sample_rate
        
        # Add channel count if specified
        if settings.channels:
            codec_settings['ac'] = settings.channels
        
        return codec_settings
    
    async def _convert_with_pydub(self, input_file: str, output_file: str,
                                settings: ConversionSettings,
                                input_metadata: AudioMetadata) -> Tuple[bool, Optional[str], List[str]]:
        """Convert audio using PyDub"""
        try:
            warnings = []
            
            # Load audio with PyDub
            audio = AudioSegment.from_file(input_file)
            
            # Apply conversions
            if settings.sample_rate and settings.sample_rate != audio.frame_rate:
                audio = audio.set_frame_rate(settings.sample_rate)
            
            if settings.channels and settings.channels != audio.channels:
                if settings.channels == 1:
                    audio = audio.set_channels(1)
                elif settings.channels == 2:
                    audio = audio.set_channels(2)
            
            # Normalization
            if settings.normalize_audio:
                audio = audio.normalize()
            
            # Get export parameters
            export_params = self._get_pydub_export_params(settings)
            
            # Export audio
            audio.export(output_file, **export_params)
            
            return True, None, warnings
            
        except Exception as e:
            error_msg = f"PyDub conversion failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
    
    def _get_pydub_export_params(self, settings: ConversionSettings) -> Dict[str, Any]:
        """Get PyDub export parameters"""
        params = {'format': settings.target_format.value}
        
        if settings.target_format == AudioFormat.MP3:
            if settings.bitrate:
                params['bitrate'] = f'{settings.bitrate}k'
            params['parameters'] = ['-q:a', '2'] if settings.quality_level == QualityLevel.HIGH else []
        
        elif settings.target_format == AudioFormat.AAC:
            if settings.bitrate:
                params['bitrate'] = f'{settings.bitrate}k'
        
        elif settings.target_format == AudioFormat.OGG:
            if settings.bitrate:
                params['bitrate'] = f'{settings.bitrate}k'
        
        elif settings.target_format == AudioFormat.FLAC:
            # FLAC is lossless, no bitrate needed
            pass
        
        return params
    
    async def _convert_with_soundfile(self, input_file: str, output_file: str,
                                    settings: ConversionSettings,
                                    input_metadata: AudioMetadata) -> Tuple[bool, Optional[str], List[str]]:
        """Convert audio using SoundFile (limited format support)"""
        try:
            warnings = []
            
            # Load audio
            audio_data, sample_rate = sf.read(input_file)
            
            # Apply sample rate conversion if needed
            if settings.sample_rate and settings.sample_rate != sample_rate:
                # Simple resampling using scipy
                from scipy import signal
                num_samples = int(len(audio_data) * settings.sample_rate / sample_rate)
                audio_data = signal.resample(audio_data, num_samples)
                sample_rate = settings.sample_rate
            
            # Apply channel conversion
            if settings.channels:
                if settings.channels == 1 and audio_data.ndim == 2:
                    # Convert to mono
                    audio_data = np.mean(audio_data, axis=1)
                elif settings.channels == 2 and audio_data.ndim == 1:
                    # Convert to stereo
                    audio_data = np.column_stack([audio_data, audio_data])
            
            # Normalization
            if settings.normalize_audio:
                max_val = np.max(np.abs(audio_data))
                if max_val > 0:
                    audio_data = audio_data / max_val * 0.95
            
            # Determine output format and subtype
            subtype = self._get_soundfile_subtype(settings)
            
            # Write audio
            sf.write(output_file, audio_data, sample_rate, subtype=subtype)
            
            return True, None, warnings
            
        except Exception as e:
            error_msg = f"SoundFile conversion failed: {str(e)}"
            logger.error(error_msg)
            return False, error_msg, []
    
    def _get_soundfile_subtype(self, settings: ConversionSettings) -> str:
        """Get SoundFile subtype for the target format"""
        if settings.target_format == AudioFormat.WAV:
            if settings.bit_depth == 24:
                return 'PCM_24'
            elif settings.bit_depth == 32:
                return 'PCM_32'
            else:
                return 'PCM_16'
        elif settings.target_format == AudioFormat.FLAC:
            return 'PCM_16'  # FLAC default
        elif settings.target_format == AudioFormat.AIFF:
            return 'PCM_16'
        else:
            return 'PCM_16'  # Default
    
    async def _preserve_metadata(self, input_file: str, output_file: str,
                                metadata: AudioMetadata, target_format: AudioFormat):
        """Preserve metadata in the converted file"""
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available - metadata preservation skipped")
            return
        
        try:
            # Load the output file for metadata writing
            output_audio = mutagen.File(output_file)
            if output_audio is None:
                logger.warning(f"Could not load {output_file} for metadata writing")
                return
            
            # Clear existing metadata
            output_audio.clear()
            
            # Write metadata based on target format
            if target_format == AudioFormat.MP3:
                await self._write_id3_metadata(output_audio, metadata)
            elif target_format == AudioFormat.FLAC:
                await self._write_vorbis_metadata(output_audio, metadata)
            elif target_format in [AudioFormat.AAC, AudioFormat.M4A]:
                await self._write_mp4_metadata(output_audio, metadata)
            elif target_format == AudioFormat.OGG:
                await self._write_vorbis_metadata(output_audio, metadata)
            
            # Save metadata
            output_audio.save()
            
        except Exception as e:
            logger.error(f"Failed to preserve metadata: {e}")
    
    async def _write_id3_metadata(self, audio_file, metadata: AudioMetadata):
        """Write ID3 metadata for MP3 files"""
        if metadata.title:
            audio_file['TIT2'] = TIT2(encoding=3, text=metadata.title)
        if metadata.artist:
            audio_file['TPE1'] = TPE1(encoding=3, text=metadata.artist)
        if metadata.album:
            audio_file['TALB'] = TALB(encoding=3, text=metadata.album)
        if metadata.year:
            audio_file['TDRC'] = TDRC(encoding=3, text=str(metadata.year))
        if metadata.genre:
            audio_file['TCON'] = TCON(encoding=3, text=metadata.genre)
        if metadata.track_number:
            track_text = str(metadata.track_number)
            if metadata.total_tracks:
                track_text += f"/{metadata.total_tracks}"
            audio_file['TRCK'] = mutagen.id3.TRCK(encoding=3, text=track_text)
    
    async def _write_vorbis_metadata(self, audio_file, metadata: AudioMetadata):
        """Write Vorbis comments for FLAC/OGG files"""
        if metadata.title:
            audio_file['TITLE'] = metadata.title
        if metadata.artist:
            audio_file['ARTIST'] = metadata.artist
        if metadata.album:
            audio_file['ALBUM'] = metadata.album
        if metadata.year:
            audio_file['DATE'] = str(metadata.year)
        if metadata.genre:
            audio_file['GENRE'] = metadata.genre
        if metadata.track_number:
            audio_file['TRACKNUMBER'] = str(metadata.track_number)
        if metadata.total_tracks:
            audio_file['TRACKTOTAL'] = str(metadata.total_tracks)
    
    async def _write_mp4_metadata(self, audio_file, metadata: AudioMetadata):
        """Write MP4 metadata for AAC/M4A files"""
        if metadata.title:
            audio_file['\xa9nam'] = metadata.title
        if metadata.artist:
            audio_file['\xa9ART'] = metadata.artist
        if metadata.album:
            audio_file['\xa9alb'] = metadata.album
        if metadata.year:
            audio_file['\xa9day'] = str(metadata.year)
        if metadata.genre:
            audio_file['\xa9gen'] = metadata.genre
        if metadata.track_number:
            track_data = [(metadata.track_number, metadata.total_tracks or 0)]
            audio_file['trkn'] = track_data
    
    async def _calculate_conversion_quality_metrics(self, input_file: str, 
                                                  output_file: str) -> Dict[str, float]:
        """Calculate quality metrics comparing input and output files"""
        try:
            # Load both files
            input_audio, input_sr = librosa.load(input_file, sr=None)
            output_audio, output_sr = librosa.load(output_file, sr=None)
            
            # Resample if needed for comparison
            if input_sr != output_sr:
                if len(input_audio) > len(output_audio):
                    input_audio = librosa.resample(input_audio, orig_sr=input_sr, target_sr=output_sr)
                else:
                    output_audio = librosa.resample(output_audio, orig_sr=output_sr, target_sr=input_sr)
            
            # Ensure same length
            min_length = min(len(input_audio), len(output_audio))
            input_audio = input_audio[:min_length]
            output_audio = output_audio[:min_length]
            
            # Calculate metrics
            metrics = {}
            
            # Signal-to-Noise Ratio
            if len(input_audio) > 0 and len(output_audio) > 0:
                noise = input_audio - output_audio
                signal_power = np.mean(input_audio**2)
                noise_power = np.mean(noise**2)
                
                if noise_power > 0:
                    snr = 10 * np.log10(signal_power / noise_power)
                    metrics['snr_db'] = float(snr)
                
                # Peak Signal-to-Noise Ratio
                max_signal = np.max(input_audio**2)
                if noise_power > 0:
                    psnr = 10 * np.log10(max_signal / noise_power)
                    metrics['psnr_db'] = float(psnr)
                
                # Correlation coefficient
                correlation = np.corrcoef(input_audio, output_audio)[0, 1]
                metrics['correlation'] = float(correlation)
                
                # RMS difference
                rms_diff = np.sqrt(np.mean((input_audio - output_audio)**2))
                metrics['rms_difference'] = float(rms_diff)
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to calculate quality metrics: {e}")
            return {}
    
    def _update_processing_stats(self, success: bool, processing_time: float,
                               input_format: AudioFormat, target_format: AudioFormat,
                               compression_ratio: float = 1.0):
        """Update processing statistics"""
        self.processing_stats['total_conversions'] += 1
        self.processing_stats['total_processing_time'] += processing_time
        
        if success:
            self.processing_stats['successful_conversions'] += 1
            
            # Update format statistics
            format_key = f"{input_format.value}_to_{target_format.value}"
            if format_key not in self.processing_stats['formats_processed']:
                self.processing_stats['formats_processed'][format_key] = 0
            self.processing_stats['formats_processed'][format_key] += 1
            
            # Update average compression ratio
            current_avg = self.processing_stats['average_compression_ratio']
            total_successful = self.processing_stats['successful_conversions']
            self.processing_stats['average_compression_ratio'] = (
                (current_avg * (total_successful - 1) + compression_ratio) / total_successful
            )
        else:
            self.processing_stats['failed_conversions'] += 1
    
    async def batch_convert(self, job: BatchProcessingJob) -> BatchProcessingJob:
        """Process multiple files in batch"""
        job.status = "processing"
        
        try:
            # Create output directory if it doesn't exist
            os.makedirs(job.output_directory, exist_ok=True)
            
            # Process files in parallel
            with ThreadPoolExecutor(max_workers=job.parallel_workers) as executor:
                # Submit all conversion tasks
                future_to_file = {}
                
                for input_file in job.input_files:
                    if not os.path.exists(input_file):
                        # Add failed result for missing file
                        job.results.append(ConversionResult(
                            success=False,
                            input_file=input_file,
                            error_message="Input file not found"
                        ))
                        continue
                    
                    # Generate output filename
                    input_path = Path(input_file)
                    output_filename = f"{input_path.stem}.{job.conversion_settings.target_format.value}"
                    output_file = os.path.join(job.output_directory, output_filename)
                    
                    # Submit conversion task
                    future = executor.submit(
                        asyncio.run,
                        self.convert_format(input_file, output_file, job.conversion_settings)
                    )
                    future_to_file[future] = input_file
                
                # Collect results as they complete
                for future in as_completed(future_to_file):
                    try:
                        result = future.result()
                        job.results.append(result)
                        
                        # Call progress callback if provided
                        if job.progress_callback:
                            progress = len(job.results) / len(job.input_files)
                            job.progress_callback(progress, result)
                            
                    except Exception as e:
                        input_file = future_to_file[future]
                        job.results.append(ConversionResult(
                            success=False,
                            input_file=input_file,
                            error_message=str(e)
                        ))
            
            # Update job status
            successful_conversions = sum(1 for r in job.results if r.success)
            if successful_conversions == len(job.results):
                job.status = "completed"
            elif successful_conversions > 0:
                job.status = "partially_completed"
            else:
                job.status = "failed"
            
            return job
            
        except Exception as e:
            job.status = "failed"
            logger.error(f"Batch processing failed: {e}")
            return job
    
    async def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """Validate audio file and return detailed information"""
        validation_result = {
            'is_valid': False,
            'file_exists': False,
            'format_detected': None,
            'metadata': None,
            'issues': [],
            'recommendations': []
        }
        
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                validation_result['issues'].append("File does not exist")
                return validation_result
            
            validation_result['file_exists'] = True
            
            # Try to detect format and extract metadata
            try:
                format_detected, metadata = await self.detect_format(file_path)
                validation_result['format_detected'] = format_detected.value
                validation_result['metadata'] = metadata
                validation_result['is_valid'] = True
            except Exception as e:
                validation_result['issues'].append(f"Cannot read audio file: {str(e)}")
                return validation_result
            
            # Validate audio properties
            if metadata.duration and metadata.duration <= 0:
                validation_result['issues'].append("Invalid duration")
            
            if metadata.sample_rate and metadata.sample_rate < 8000:
                validation_result['issues'].append("Very low sample rate")
                validation_result['recommendations'].append("Consider upsampling to at least 44.1kHz")
            
            if metadata.channels and metadata.channels > 8:
                validation_result['issues'].append("Unusually high channel count")
            
            # Check for clipping
            if metadata.peak_level and metadata.peak_level >= 1.0:
                validation_result['issues'].append("Audio clipping detected")
                validation_result['recommendations'].append("Consider reducing levels or applying limiting")
            
            # Check dynamic range
            if metadata.dynamic_range and metadata.dynamic_range < 6:
                validation_result['issues'].append("Very low dynamic range")
                validation_result['recommendations'].append("Audio may be over-compressed")
            
            # File size checks
            file_size = os.path.getsize(file_path)
            if file_size < 1000:  # Less than 1KB
                validation_result['issues'].append("File size is suspiciously small")
            
            # Format-specific validations
            format_info = self.format_info.get(format_detected)
            if format_info:
                if metadata.sample_rate and metadata.sample_rate > format_info.max_sample_rate:
                    validation_result['issues'].append(
                        f"Sample rate exceeds format maximum ({format_info.max_sample_rate}Hz)"
                    )
                
                if metadata.channels and metadata.channels > format_info.max_channels:
                    validation_result['issues'].append(
                        f"Channel count exceeds format maximum ({format_info.max_channels})"
                    )
            
        except Exception as e:
            validation_result['issues'].append(f"Validation error: {str(e)}")
        
        return validation_result
    
    async def get_format_info(self, format: AudioFormat) -> Optional[FormatInfo]:
        """Get detailed information about a specific audio format"""
        return self.format_info.get(format)
    
    async def get_supported_formats(self) -> List[AudioFormat]:
        """Get list of all supported audio formats"""
        return list(self.format_info.keys())
    
    async def get_conversion_recommendations(self, input_file: str, 
                                          target_use_case: str) -> ConversionSettings:
        """Get recommended conversion settings for specific use cases"""
        # Detect input format and metadata
        input_format, metadata = await self.detect_format(input_file)
        
        # Define use case presets
        use_case_presets = {
            'streaming': ConversionSettings(
                target_format=AudioFormat.AAC,
                bitrate=128,
                sample_rate=44100,
                channels=2,
                quality_level=QualityLevel.STANDARD,
                normalize_audio=True
            ),
            'podcast': ConversionSettings(
                target_format=AudioFormat.MP3,
                bitrate=128,
                sample_rate=44100,
                channels=1,  # Mono for speech
                quality_level=QualityLevel.STANDARD,
                normalize_audio=True
            ),
            'archival': ConversionSettings(
                target_format=AudioFormat.FLAC,
                sample_rate=96000,
                bit_depth=24,
                quality_level=QualityLevel.ARCHIVE,
                preserve_metadata=True
            ),
            'mobile': ConversionSettings(
                target_format=AudioFormat.AAC,
                bitrate=96,
                sample_rate=44100,
                channels=2,
                quality_level=QualityLevel.STANDARD
            ),
            'broadcast': ConversionSettings(
                target_format=AudioFormat.WAV,
                sample_rate=48000,
                bit_depth=24,
                quality_level=QualityLevel.HIGH,
                normalize_audio=True
            ),
            'web': ConversionSettings(
                target_format=AudioFormat.OGG,
                bitrate=192,
                sample_rate=44100,
                channels=2,
                quality_level=QualityLevel.STANDARD
            )
        }
        
        # Get preset or default
        preset = use_case_presets.get(target_use_case.lower())
        if not preset:
            # Default high-quality preset
            preset = ConversionSettings(
                target_format=AudioFormat.FLAC,
                quality_level=QualityLevel.HIGH,
                preserve_metadata=True
            )
        
        # Adjust based on input characteristics
        if metadata.sample_rate and metadata.sample_rate < preset.sample_rate:
            preset.sample_rate = metadata.sample_rate  # Don't upsample
        
        if metadata.channels and metadata.channels < preset.channels:
            preset.channels = metadata.channels  # Don't add channels
        
        return preset
    
    async def get_processing_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        stats = self.processing_stats.copy()
        
        # Calculate additional metrics
        if stats['total_conversions'] > 0:
            stats['success_rate'] = stats['successful_conversions'] / stats['total_conversions']
            stats['average_processing_time'] = stats['total_processing_time'] / stats['total_conversions']
        else:
            stats['success_rate'] = 0.0
            stats['average_processing_time'] = 0.0
        
        return stats
    
    async def cleanup(self):
        """Clean up resources"""
        try:
            self.executor.shutdown(wait=True)
            logger.info("ProfessionalAudioFormatHandler cleanup completed")
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")


# Test and demonstration code
if __name__ == "__main__":
    import asyncio
    
    async def test_format_handler():
        """Test professional audio format handler functionality"""
        handler = ProfessionalAudioFormatHandler()
        
        print("Professional Audio Format Handler Test")
        print("=" * 50)
        
        # Test format support
        supported_formats = await handler.get_supported_formats()
        print(f"Supported formats: {[f.value for f in supported_formats]}")
        
        # Test format info
        wav_info = await handler.get_format_info(AudioFormat.WAV)
        if wav_info:
            print(f"WAV format info: {wav_info.max_channels} channels, {wav_info.max_sample_rate}Hz")
        
        # Test conversion recommendations
        recommendations = await handler.get_conversion_recommendations("test.wav", "streaming")
        print(f"Streaming recommendations: {recommendations.target_format.value}, {recommendations.bitrate}kbps")
        
        print("Format handler test completed")
        
        await handler.cleanup()
    
    # Run test
    asyncio.run(test_format_handler())