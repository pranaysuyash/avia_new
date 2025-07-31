#!/usr/bin/env python3
"""
Unit tests for media processing utilities
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import ffmpeg

from media import (
    validate_media_file,
    extract_audio,
    convert_audio_format,
    get_media_info,
    cleanup_temp_file,
    is_video_file,
    is_audio_file,
    SUPPORTED_AUDIO_FORMATS,
    SUPPORTED_VIDEO_FORMATS
)
from errors import MediaProcessingError, FileProcessingError


class TestMediaProcessing(unittest.TestCase):
    """Test cases for media processing functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create test files
        self.valid_audio_file = os.path.join(self.temp_dir, "test_audio.wav")
        self.valid_video_file = os.path.join(self.temp_dir, "test_video.mp4")
        self.invalid_file = os.path.join(self.temp_dir, "test_invalid.txt")
        self.empty_file = os.path.join(self.temp_dir, "test_empty.wav")
        self.nonexistent_file = os.path.join(self.temp_dir, "nonexistent.wav")
        
        # Create actual test files
        with open(self.valid_audio_file, 'wb') as f:
            f.write(b'fake audio data' * 100)  # Create non-empty file
        
        with open(self.valid_video_file, 'wb') as f:
            f.write(b'fake video data' * 100)  # Create non-empty file
            
        with open(self.invalid_file, 'w') as f:
            f.write('invalid format')
            
        with open(self.empty_file, 'w') as f:
            pass  # Create empty file
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_file_type_detection(self):
        """Test file type detection functions"""
        # Test audio file detection
        self.assertTrue(is_audio_file("test.mp3"))
        self.assertTrue(is_audio_file("test.wav"))
        self.assertTrue(is_audio_file("test.m4a"))
        self.assertFalse(is_audio_file("test.mp4"))
        self.assertFalse(is_audio_file("test.txt"))
        
        # Test video file detection
        self.assertTrue(is_video_file("test.mp4"))
        self.assertTrue(is_video_file("test.avi"))
        self.assertTrue(is_video_file("test.mov"))
        self.assertFalse(is_video_file("test.mp3"))
        self.assertFalse(is_video_file("test.txt"))
    
    def test_validate_media_file_nonexistent(self):
        """Test validation of non-existent file"""
        with self.assertRaises(FileProcessingError) as context:
            validate_media_file(self.nonexistent_file)
        self.assertIn("File does not exist", str(context.exception))
    
    def test_validate_media_file_empty(self):
        """Test validation of empty file"""
        with self.assertRaises(FileProcessingError) as context:
            validate_media_file(self.empty_file)
        self.assertIn("File is empty", str(context.exception))
    
    def test_validate_media_file_unsupported_format(self):
        """Test validation of unsupported file format"""
        with self.assertRaises(FileProcessingError) as context:
            validate_media_file(self.invalid_file)
        self.assertIn("Unsupported file format", str(context.exception))
    
    @patch('ffmpeg.probe')
    def test_validate_media_file_no_audio_stream(self, mock_probe):
        """Test validation of file with no audio stream"""
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'video'}  # No audio stream
            ]
        }
        
        with self.assertRaises(MediaProcessingError) as context:
            validate_media_file(self.valid_video_file)
        self.assertIn("No audio stream found", str(context.exception))
    
    @patch('ffmpeg.probe')
    def test_validate_media_file_corrupted(self, mock_probe):
        """Test validation of corrupted file"""
        mock_probe.side_effect = ffmpeg.Error('ffmpeg', '', 'Corrupted file')
        
        with self.assertRaises(MediaProcessingError) as context:
            validate_media_file(self.valid_audio_file)
        self.assertIn("File appears to be corrupted", str(context.exception))
    
    @patch('ffmpeg.probe')
    def test_validate_media_file_success(self, mock_probe):
        """Test successful file validation"""
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'pcm_s16le'}
            ]
        }
        
        result = validate_media_file(self.valid_audio_file)
        self.assertTrue(result)
    
    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    def test_extract_audio_success(self, mock_input, mock_probe):
        """Test successful audio extraction"""
        # Mock validation
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'aac'}
            ]
        }
        
        # Mock ffmpeg processing
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run.return_value = None
        
        result = extract_audio(self.valid_video_file)
        
        # Verify result is a valid path
        self.assertTrue(isinstance(result, str))
        self.assertTrue(result.endswith('.wav'))
        
        # Verify ffmpeg was called with correct parameters
        mock_stream.output.assert_called_once()
        call_args = mock_stream.output.call_args
        self.assertEqual(call_args[1]['acodec'], 'pcm_s16le')
        self.assertEqual(call_args[1]['ac'], 1)
        self.assertEqual(call_args[1]['ar'], 16000)
    
    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    def test_extract_audio_ffmpeg_error(self, mock_input, mock_probe):
        """Test audio extraction with FFmpeg error"""
        # Mock validation
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'aac'}
            ]
        }
        
        # Mock ffmpeg error
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run.side_effect = ffmpeg.Error('ffmpeg', '', b'FFmpeg error')
        
        with self.assertRaises(MediaProcessingError) as context:
            extract_audio(self.valid_video_file)
        self.assertIn("FFmpeg audio extraction failed", str(context.exception))
    
    @patch('ffmpeg.probe')
    @patch('ffmpeg.input')
    def test_convert_audio_format_success(self, mock_input, mock_probe):
        """Test successful audio format conversion"""
        # Mock validation
        mock_probe.return_value = {
            'streams': [
                {'codec_type': 'audio', 'codec_name': 'mp3'}
            ]
        }
        
        # Mock ffmpeg processing
        mock_stream = MagicMock()
        mock_input.return_value = mock_stream
        mock_stream.output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run.return_value = None
        
        result = convert_audio_format(self.valid_audio_file)
        
        # Verify result is a valid path
        self.assertTrue(isinstance(result, str))
        self.assertTrue(result.endswith('.wav'))
        
        # Verify ffmpeg was called with correct parameters
        mock_stream.output.assert_called_once()
        call_args = mock_stream.output.call_args
        self.assertEqual(call_args[1]['acodec'], 'pcm_s16le')
        self.assertEqual(call_args[1]['ac'], 1)
        self.assertEqual(call_args[1]['ar'], 16000)
    
    @patch('ffmpeg.probe')
    def test_get_media_info_success(self, mock_probe):
        """Test successful media info retrieval"""
        mock_probe.return_value = {
            'format': {
                'duration': '120.5',
                'format_name': 'wav',
                'size': '1024000',
                'bit_rate': '128000'
            },
            'streams': [
                {
                    'codec_type': 'audio',
                    'codec_name': 'pcm_s16le',
                    'sample_rate': '44100',
                    'channels': '2'
                }
            ]
        }
        
        info = get_media_info(self.valid_audio_file)
        
        self.assertEqual(info['duration'], 120.5)
        self.assertEqual(info['format_name'], 'wav')
        self.assertEqual(info['size'], 1024000)
        self.assertEqual(info['bit_rate'], 128000)
        self.assertEqual(info['sample_rate'], 44100)
        self.assertEqual(info['channels'], 2)
        self.assertEqual(info['codec'], 'pcm_s16le')
    
    @patch('ffmpeg.probe')
    def test_get_media_info_no_audio_stream(self, mock_probe):
        """Test media info with no audio stream"""
        mock_probe.return_value = {
            'format': {},
            'streams': [
                {'codec_type': 'video'}  # No audio stream
            ]
        }
        
        with self.assertRaises(MediaProcessingError) as context:
            get_media_info(self.valid_video_file)
        self.assertIn("No audio stream found", str(context.exception))
    
    def test_cleanup_temp_file(self):
        """Test temporary file cleanup"""
        # Create a temporary file
        temp_file = os.path.join(self.temp_dir, "temp_test.wav")
        with open(temp_file, 'w') as f:
            f.write('temp data')
        
        # Verify file exists
        self.assertTrue(os.path.exists(temp_file))
        
        # Clean up file
        cleanup_temp_file(temp_file)
        
        # Verify file is removed
        self.assertFalse(os.path.exists(temp_file))
    
    def test_cleanup_temp_file_nonexistent(self):
        """Test cleanup of non-existent file (should not raise error)"""
        nonexistent = os.path.join(self.temp_dir, "nonexistent.wav")
        
        # Should not raise an exception
        cleanup_temp_file(nonexistent)


class TestMediaProcessingIntegration(unittest.TestCase):
    """Integration tests that require actual FFmpeg (optional)"""
    
    def setUp(self):
        """Set up integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up integration test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @unittest.skipUnless(os.system('which ffmpeg') == 0, "FFmpeg not available")
    def test_create_and_process_real_audio(self):
        """Integration test with real FFmpeg (requires FFmpeg installation)"""
        # Create a simple sine wave audio file using FFmpeg
        test_audio = os.path.join(self.temp_dir, "test_sine.wav")
        
        try:
            # Generate a 1-second sine wave at 440Hz
            (
                ffmpeg
                .input('sine=frequency=440:duration=1', f='lavfi')
                .output(test_audio, acodec='pcm_s16le', ar=44100, ac=2)
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
            
            # Test validation
            self.assertTrue(validate_media_file(test_audio))
            
            # Test format conversion
            converted = convert_audio_format(test_audio)
            self.assertTrue(os.path.exists(converted))
            
            # Test media info
            info = get_media_info(test_audio)
            self.assertGreater(info['duration'], 0.9)  # Should be close to 1 second
            self.assertEqual(info['sample_rate'], 44100)
            
            # Clean up
            cleanup_temp_file(converted)
            
        except ffmpeg.Error as e:
            self.skipTest(f"FFmpeg integration test failed: {e}")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)