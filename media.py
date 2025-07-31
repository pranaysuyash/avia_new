# Media Processing Module
# Handles audio extraction from video files and format conversion

import os
import logging
import tempfile
import ffmpeg
from typing import Optional, Tuple
from pathlib import Path

from errors import (
    MediaProcessingError, FileProcessingError, handle_error, 
    ErrorCode, create_file_size_error
)

logger = logging.getLogger(__name__)

# Supported media formats
SUPPORTED_AUDIO_FORMATS = {'.mp3', '.wav', '.m4a', '.flac', '.aac'}
SUPPORTED_VIDEO_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.webm'}
SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS | SUPPORTED_VIDEO_FORMATS

def validate_media_file(file_path: str, max_size_mb: int = 100) -> bool:
    """
    Validate uploaded media file format and integrity
    
    Args:
        file_path: Path to the media file
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        bool: True if file is valid, False otherwise
        
    Raises:
        MediaProcessingError: If file validation fails
    """
    try:
        if not os.path.exists(file_path):
            raise FileProcessingError(
                message=f"File does not exist: {file_path}",
                error_code=ErrorCode.FILE_NOT_FOUND,
                user_message="The specified file could not be found.",
                file_path=file_path,
                suggestions=[
                    "Check that the file exists and the path is correct",
                    "Try uploading the file again"
                ]
            )
        
        # Check file size
        file_size_bytes = os.path.getsize(file_path)
        if file_size_bytes == 0:
            raise FileProcessingError(
                message=f"File is empty: {file_path}",
                error_code=ErrorCode.FILE_CORRUPTED,
                user_message="The file appears to be empty or corrupted.",
                file_path=file_path,
                file_size=0,
                suggestions=[
                    "Try uploading a different file",
                    "Check that the original file is not corrupted"
                ]
            )
        
        file_size_mb = file_size_bytes / (1024 * 1024)
        if file_size_mb > max_size_mb:
            raise create_file_size_error(file_path, int(file_size_mb), max_size_mb)
        
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in SUPPORTED_FORMATS:
            supported_list = ', '.join(sorted(SUPPORTED_FORMATS))
            raise FileProcessingError(
                message=f"Unsupported file format: {file_ext}",
                error_code=ErrorCode.FILE_UNSUPPORTED_FORMAT,
                user_message=f"File format {file_ext} is not supported.",
                file_path=file_path,
                suggestions=[
                    f"Convert to a supported format: {supported_list}",
                    "Try a different file"
                ]
            )
        
        # Probe file with ffmpeg to check integrity
        try:
            probe = ffmpeg.probe(file_path)
            
            # Check if file has audio stream
            audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
            if not audio_streams:
                raise MediaProcessingError(
                    message=f"No audio stream found in file: {file_path}",
                    error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                    user_message="The file does not contain any audio tracks.",
                    media_type=file_ext,
                    suggestions=[
                        "Try a different media file",
                        "Check that the video file contains audio",
                        "Convert the file to include an audio track"
                    ]
                )
            
            logger.info(f"File validation successful: {file_path}")
            return True
            
        except ffmpeg.Error as e:
            raise MediaProcessingError(
                message=f"File appears to be corrupted: {file_path}. FFmpeg error: {str(e)}",
                error_code=ErrorCode.FILE_CORRUPTED,
                user_message="The media file appears to be corrupted or unreadable.",
                media_type=file_ext,
                suggestions=[
                    "Try uploading a different file",
                    "Check that the original file is not corrupted",
                    "Convert the file to a different format"
                ]
            )
    
    except Exception as e:
        if isinstance(e, (MediaProcessingError, FileProcessingError)):
            raise
        # Handle unexpected errors
        app_error = handle_error(e, {"file_path": file_path, "operation": "validation"})
        raise app_error

def extract_audio(video_file: str, max_size_mb: int = 100) -> str:
    """
    Extract audio track from video file using FFmpeg
    
    Args:
        video_file: Path to the input video file
        max_size_mb: Maximum allowed file size in MB
        
    Returns:
        str: Path to the extracted audio file
        
    Raises:
        MediaProcessingError: If audio extraction fails
    """
    try:
        # Validate input file first
        validate_media_file(video_file, max_size_mb)
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Extract audio using ffmpeg
            (
                ffmpeg
                .input(video_file)
                .output(
                    output_path,
                    acodec='pcm_s16le',  # 16-bit PCM
                    ac=1,                # Mono
                    ar=16000            # 16kHz sample rate
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Audio extracted successfully: {video_file} -> {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            # Clean up temp file on error
            if os.path.exists(output_path):
                os.unlink(output_path)
            
            stderr = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
            raise MediaProcessingError(
                message=f"FFmpeg audio extraction failed: {stderr}",
                error_code=ErrorCode.MEDIA_EXTRACTION_ERROR,
                user_message="Failed to extract audio from the video file.",
                media_type=Path(video_file).suffix.lower(),
                suggestions=[
                    "Try a different video file",
                    "Check that the video contains an audio track",
                    "Convert the video to a different format"
                ]
            )
    
    except Exception as e:
        if isinstance(e, (MediaProcessingError, FileProcessingError)):
            raise
        # Handle unexpected errors
        app_error = handle_error(e, {
            "file_path": video_file, 
            "operation": "audio_extraction",
            "media_type": Path(video_file).suffix.lower()
        })
        raise app_error

def convert_audio_format(input_path: str, output_format: str = "wav") -> str:
    """
    Convert audio to standardized 16kHz mono WAV format for processing
    
    Args:
        input_path: Path to the input audio file
        output_format: Target format (default: "wav")
        
    Returns:
        str: Path to the converted audio file
        
    Raises:
        MediaProcessingError: If audio conversion fails
    """
    try:
        # Validate input file
        validate_media_file(input_path)
        
        # Create temporary output file
        output_ext = f'.{output_format.lower()}'
        with tempfile.NamedTemporaryFile(suffix=output_ext, delete=False) as temp_file:
            output_path = temp_file.name
        
        try:
            # Convert audio using ffmpeg
            (
                ffmpeg
                .input(input_path)
                .output(
                    output_path,
                    acodec='pcm_s16le',  # 16-bit PCM for WAV
                    ac=1,                # Convert to mono
                    ar=16000            # Standardize to 16kHz
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            logger.info(f"Audio converted successfully: {input_path} -> {output_path}")
            return output_path
            
        except ffmpeg.Error as e:
            # Clean up temp file on error
            if os.path.exists(output_path):
                os.unlink(output_path)
            
            stderr = e.stderr.decode() if e.stderr else "Unknown error"
            raise MediaProcessingError(f"FFmpeg audio conversion failed: {stderr}")
    
    except Exception as e:
        if isinstance(e, MediaProcessingError):
            raise
        logger.error(f"Unexpected error during audio conversion: {str(e)}")
        raise MediaProcessingError(f"Audio conversion failed: {str(e)}")

def get_media_info(file_path: str) -> dict:
    """
    Get media file information using FFmpeg probe
    
    Args:
        file_path: Path to the media file
        
    Returns:
        dict: Media file information including duration, format, etc.
        
    Raises:
        MediaProcessingError: If probe fails
    """
    try:
        probe = ffmpeg.probe(file_path)
        
        # Extract relevant information
        format_info = probe.get('format', {})
        audio_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'audio']
        
        if not audio_streams:
            raise MediaProcessingError(
                message=f"No audio stream found in file: {file_path}",
                error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
                user_message="The file does not contain any audio tracks.",
                media_type=file_ext,
                suggestions=[
                    "Try a different media file",
                    "Check that the video file contains audio",
                    "Convert the file to include an audio track"
                ]
            )
        
        audio_stream = audio_streams[0]  # Use first audio stream
        
        return {
            'duration': float(format_info.get('duration', 0)),
            'format_name': format_info.get('format_name', 'unknown'),
            'size': int(format_info.get('size', 0)),
            'bit_rate': int(format_info.get('bit_rate', 0)),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0)),
            'codec': audio_stream.get('codec_name', 'unknown')
        }
        
    except ffmpeg.Error as e:
        stderr = e.stderr.decode() if e.stderr else "Unknown error"
        raise MediaProcessingError(f"Failed to get media info: {stderr}")
    except Exception as e:
        logger.error(f"Unexpected error getting media info: {str(e)}")
        raise MediaProcessingError(
            message=f"Failed to get media info: {str(e)}",
            error_code=ErrorCode.MEDIA_VALIDATION_ERROR,
            user_message="Failed to analyze the media file.",
            media_type=Path(file_path).suffix.lower(),
            suggestions=[
                "Check that the file is not corrupted",
                "Try a different media file",
                "Ensure the file format is supported"
            ]
        )

def cleanup_temp_file(file_path: str) -> None:
    """
    Clean up temporary files created during processing
    
    Args:
        file_path: Path to the temporary file to remove
    """
    try:
        if os.path.exists(file_path):
            os.unlink(file_path)
            logger.info(f"Cleaned up temporary file: {file_path}")
    except Exception as e:
        logger.warning(f"Failed to clean up temporary file {file_path}: {str(e)}")

def is_video_file(file_path: str) -> bool:
    """
    Check if file is a video file based on extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if file is a video file
    """
    file_ext = Path(file_path).suffix.lower()
    return file_ext in SUPPORTED_VIDEO_FORMATS

def is_audio_file(file_path: str) -> bool:
    """
    Check if file is an audio file based on extension
    
    Args:
        file_path: Path to the file
        
    Returns:
        bool: True if file is an audio file
    """
    file_ext = Path(file_path).suffix.lower()
    return file_ext in SUPPORTED_AUDIO_FORMATS