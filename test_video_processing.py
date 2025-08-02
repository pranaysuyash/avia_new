#!/usr/bin/env python3
"""
Test Suite for Video Processing Features
Comprehensive tests for Task 30: Add video-specific processing features
"""

import os
import sys
import unittest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add the current directory to the path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_processing import (
    VideoProcessor, VideoMetadata, VideoThumbnail, VideoChapter, 
    VideoQualityMetrics, SubtitleEntry, create_video_player_html
)


class TestVideoProcessor(unittest.TestCase):
    """Test cases for VideoProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = VideoProcessor()
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock video file path
        self.mock_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        
        # Sample transcript data for testing
        self.sample_transcript = {
            "segments": [
                {"start": 0.0, "end": 5.0, "text": "Welcome to this video demonstration."},
                {"start": 5.0, "end": 10.0, "text": "Today we'll be exploring video processing features."},
                {"start": 10.0, "end": 15.0, "text": "This includes subtitle generation and chapter detection."},
                {"start": 15.0, "end": 20.0, "text": "Let's move on to the next topic now."},
                {"start": 20.0, "end": 25.0, "text": "This is a new section about advanced features."}
            ]
        }
    
    def tearDown(self):
        """Clean up test fixtures"""
        # Clean up temporary files
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ffmpeg.probe')
    def test_extract_metadata(self, mock_probe):
        """Test video metadata extraction"""
        # Mock ffmpeg probe response
        mock_probe.return_value = {
            'streams': [
                {
                    'codec_type': 'video',
                    'width': 1920,
                    'height': 1080,
                    'r_frame_rate': '30/1',
                    'codec_name': 'h264'
                },
                {
                    'codec_type': 'audio',
                    'codec_name': 'aac',
                    'bit_rate': '128000',
                    'sample_rate': '44100'
                }
            ],
            'format': {
                'duration': '120.5',
                'bit_rate': '5000000',
                'format_name': 'mp4',
                'size': '75000000'
            }
        }
        
        metadata = self.processor.extract_metadata(self.mock_video_path)
        
        self.assertIsInstance(metadata, VideoMetadata)
        self.assertEqual(metadata.width, 1920)
        self.assertEqual(metadata.height, 1080)
        self.assertEqual(metadata.fps, 30.0)
        self.assertEqual(metadata.duration, 120.5)
        self.assertEqual(metadata.bitrate, 5000000)
        self.assertEqual(metadata.codec, 'h264')
        self.assertTrue(metadata.has_audio)
        self.assertEqual(metadata.audio_codec, 'aac')
    
    @patch('cv2.VideoCapture')
    def test_generate_thumbnails(self, mock_cv2):
        """Test thumbnail generation"""
        # Mock OpenCV VideoCapture
        mock_cap = Mock()
        mock_cv2.return_value = mock_cap
        
        # Mock video properties
        mock_cap.get.side_effect = lambda prop: {
            'CAP_PROP_POS_MSEC': 0,
            'CAP_PROP_POS_FRAMES': 0
        }.get(prop, 0)
        
        # Mock frame reading
        mock_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame)
        
        # Mock metadata
        with patch.object(self.processor, 'extract_metadata') as mock_metadata:
            mock_metadata.return_value = VideoMetadata(
                duration=60.0, width=640, height=480, fps=30.0,
                bitrate=2000000, codec='h264', format='mp4',
                size_bytes=15000000, aspect_ratio='4:3', has_audio=True
            )
            
            # Mock cv2.imwrite to avoid actual file writing
            with patch('cv2.imwrite') as mock_imwrite:
                mock_imwrite.return_value = True
                
                thumbnails = self.processor.generate_thumbnails(
                    self.mock_video_path, count=3
                )
        
        self.assertEqual(len(thumbnails), 3)
        for thumbnail in thumbnails:
            self.assertIsInstance(thumbnail, VideoThumbnail)
            self.assertGreaterEqual(thumbnail.timestamp, 0)
            self.assertGreater(thumbnail.quality_score, 0)
    
    def test_generate_srt_subtitles(self):
        """Test SRT subtitle generation"""
        output_path = os.path.join(self.temp_dir, "test_subtitles.srt")
        
        result_path = self.processor.generate_subtitles(
            transcript_data=self.sample_transcript,
            output_path=output_path,
            format_type='srt'
        )
        
        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))
        
        # Check SRT content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Should contain subtitle entries
        self.assertIn('1\n', content)
        self.assertIn('00:00:00,000 --> 00:00:05,000', content)
        self.assertIn('Welcome to this video demonstration.', content)
    
    def test_generate_vtt_subtitles(self):
        """Test VTT subtitle generation"""
        output_path = os.path.join(self.temp_dir, "test_subtitles.vtt")
        
        result_path = self.processor.generate_subtitles(
            transcript_data=self.sample_transcript,
            output_path=output_path,
            format_type='vtt'
        )
        
        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))
        
        # Check VTT content
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Should start with WEBVTT
        self.assertTrue(content.startswith('WEBVTT'))
        self.assertIn('00:00:00.000 --> 00:00:05.000', content)
        self.assertIn('Welcome to this video demonstration.', content)
    
    def test_generate_subtitles_from_plain_text(self):
        """Test subtitle generation from plain text"""
        plain_text = "This is a test transcript. It has multiple sentences. Each sentence should become a subtitle entry."
        
        output_path = os.path.join(self.temp_dir, "plain_text_subtitles.srt")
        
        result_path = self.processor.generate_subtitles(
            transcript_data=plain_text,
            output_path=output_path,
            format_type='srt'
        )
        
        self.assertEqual(result_path, output_path)
        self.assertTrue(os.path.exists(output_path))
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Should contain multiple subtitle entries
        self.assertIn('1\n', content)
        self.assertIn('This is a test transcript.', content)
    
    @patch('cv2.VideoCapture')
    def test_detect_scene_changes(self, mock_cv2):
        """Test scene change detection"""
        # Mock OpenCV VideoCapture
        mock_cap = Mock()
        mock_cv2.return_value = mock_cap
        
        # Mock video properties
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            'CAP_PROP_FPS': 30.0,
            'CAP_PROP_FRAME_COUNT': 1800,  # 60 seconds at 30fps
            'CAP_PROP_POS_FRAMES': 0
        }.get(prop, 0)
        
        # Mock frame reading with different frames to simulate scene changes
        frames = [
            np.full((480, 640, 3), 50, dtype=np.uint8),   # Dark frame
            np.full((480, 640, 3), 200, dtype=np.uint8),  # Bright frame (scene change)
            np.full((480, 640, 3), 100, dtype=np.uint8),  # Medium frame
        ]
        
        frame_index = 0
        def mock_read():
            nonlocal frame_index
            if frame_index < len(frames):
                frame = frames[frame_index % len(frames)]
                frame_index += 1
                return True, frame
            return False, None
        
        mock_cap.read.side_effect = mock_read
        
        chapters = self.processor._detect_scene_changes(
            self.mock_video_path, threshold=0.3, min_length=10.0
        )
        
        self.assertIsInstance(chapters, list)
        for chapter in chapters:
            self.assertIsInstance(chapter, VideoChapter)
            self.assertGreaterEqual(chapter.end_time, chapter.start_time)
    
    def test_detect_content_chapters(self):
        """Test content-based chapter detection"""
        chapters = self.processor._detect_content_chapters(
            self.sample_transcript, min_length=5.0
        )
        
        self.assertIsInstance(chapters, list)
        
        # Should detect at least one chapter based on "next topic" phrase
        topic_change_detected = any(
            "next topic" in chapter.description.lower() 
            for chapter in chapters
        )
        
        for chapter in chapters:
            self.assertIsInstance(chapter, VideoChapter)
            self.assertGreaterEqual(chapter.end_time, chapter.start_time)
            self.assertIsInstance(chapter.title, str)
            self.assertIsInstance(chapter.description, str)
    
    @patch('ffmpeg.probe')
    def test_analyze_video_quality(self, mock_probe):
        """Test video quality analysis"""
        # Mock ffmpeg probe response for a high-quality video
        mock_probe.return_value = {
            'streams': [
                {
                    'codec_type': 'video',
                    'width': 1920,
                    'height': 1080,
                    'r_frame_rate': '30/1',
                    'codec_name': 'h264'
                }
            ],
            'format': {
                'duration': '120.0',
                'bit_rate': '8000000',  # 8 Mbps
                'format_name': 'mp4',
                'size': '120000000'
            }
        }
        
        quality_metrics = self.processor.analyze_video_quality(self.mock_video_path)
        
        self.assertIsInstance(quality_metrics, VideoQualityMetrics)
        self.assertGreaterEqual(quality_metrics.overall_score, 0.0)
        self.assertLessEqual(quality_metrics.overall_score, 1.0)
        self.assertGreaterEqual(quality_metrics.resolution_score, 0.0)
        self.assertGreaterEqual(quality_metrics.bitrate_score, 0.0)
        self.assertGreaterEqual(quality_metrics.fps_score, 0.0)
        self.assertGreaterEqual(quality_metrics.compression_score, 0.0)
        self.assertIsInstance(quality_metrics.recommendations, list)
        self.assertIsInstance(quality_metrics.technical_details, dict)
    
    @patch('ffmpeg.input')
    @patch('ffmpeg.output')
    def test_create_video_preview(self, mock_output, mock_input):
        """Test video preview creation"""
        # Mock ffmpeg operations
        mock_stream = Mock()
        mock_input.return_value = mock_stream
        mock_output.return_value = mock_stream
        mock_stream.overwrite_output.return_value = mock_stream
        mock_stream.run.return_value = None
        
        # Mock metadata
        with patch.object(self.processor, 'extract_metadata') as mock_metadata:
            mock_metadata.return_value = VideoMetadata(
                duration=120.0, width=1920, height=1080, fps=30.0,
                bitrate=5000000, codec='h264', format='mp4',
                size_bytes=75000000, aspect_ratio='16:9', has_audio=True
            )
            
            output_path = os.path.join(self.temp_dir, "preview.mp4")
            result_path = self.processor.create_video_preview(
                self.mock_video_path, output_path, duration=30.0, start_offset=10.0
            )
        
        self.assertEqual(result_path, output_path)
        mock_input.assert_called_once()
        mock_output.assert_called_once()
    
    def test_format_srt_timestamp(self):
        """Test SRT timestamp formatting"""
        # Test various timestamps
        test_cases = [
            (0.0, "00:00:00,000"),
            (65.5, "00:01:05,500"),
            (3661.123, "01:01:01,123"),
            (7323.999, "02:02:03,999")
        ]
        
        for seconds, expected in test_cases:
            result = self.processor._format_srt_timestamp(seconds)
            self.assertEqual(result, expected)
    
    def test_format_vtt_timestamp(self):
        """Test VTT timestamp formatting"""
        # Test various timestamps
        test_cases = [
            (0.0, "00:00:00.000"),
            (65.5, "00:01:05.500"),
            (3661.123, "01:01:01.123"),
            (7323.999, "02:02:03.999")
        ]
        
        for seconds, expected in test_cases:
            result = self.processor._format_vtt_timestamp(seconds)
            self.assertEqual(result, expected)
    
    def test_split_text_for_subtitles(self):
        """Test text splitting for subtitles"""
        long_text = "This is a very long sentence that should be split into multiple lines for subtitle display purposes."
        
        lines = self.processor._split_text_for_subtitles(long_text, max_chars_per_line=30, max_lines=2)
        
        self.assertIsInstance(lines, list)
        self.assertLessEqual(len(lines), 2)  # Should not exceed max_lines
        
        for line in lines:
            self.assertLessEqual(len(line), 30)  # Should not exceed max_chars_per_line
    
    def test_calculate_frame_quality(self):
        """Test frame quality calculation"""
        # Create test frames with different characteristics
        
        # Sharp, well-lit frame
        sharp_frame = np.random.randint(50, 200, (480, 640, 3), dtype=np.uint8)
        sharp_quality = self.processor._calculate_frame_quality(sharp_frame)
        
        # Very dark frame
        dark_frame = np.full((480, 640, 3), 10, dtype=np.uint8)
        dark_quality = self.processor._calculate_frame_quality(dark_frame)
        
        # Very bright frame
        bright_frame = np.full((480, 640, 3), 245, dtype=np.uint8)
        bright_quality = self.processor._calculate_frame_quality(bright_frame)
        
        # Quality scores should be between 0 and 1
        self.assertGreaterEqual(sharp_quality, 0.0)
        self.assertLessEqual(sharp_quality, 1.0)
        self.assertGreaterEqual(dark_quality, 0.0)
        self.assertLessEqual(dark_quality, 1.0)
        self.assertGreaterEqual(bright_quality, 0.0)
        self.assertLessEqual(bright_quality, 1.0)
        
        # Sharp frame should generally have better quality than extreme frames
        self.assertGreaterEqual(sharp_quality, min(dark_quality, bright_quality))
    
    def test_extract_keywords(self):
        """Test keyword extraction from text"""
        text = "This video demonstrates advanced machine learning algorithms and artificial intelligence techniques."
        
        keywords = self.processor._extract_keywords(text)
        
        self.assertIsInstance(keywords, list)
        self.assertIn('machine', keywords)
        self.assertIn('learning', keywords)
        self.assertIn('algorithms', keywords)
        self.assertIn('artificial', keywords)
        self.assertIn('intelligence', keywords)
        
        # Should not include stop words
        self.assertNotIn('this', keywords)
        self.assertNotIn('and', keywords)
    
    def test_score_resolution(self):
        """Test resolution scoring"""
        # Test different resolutions
        test_cases = [
            (3840, 2160, 1.0),    # 4K - should get perfect score
            (1920, 1080, 0.9),    # 1080p - should get high score
            (1280, 720, 0.7),     # 720p - should get good score
            (640, 480, 0.5),      # 480p - should get medium score
            (320, 240, 0.1)       # Very low res - should get low score
        ]
        
        for width, height, expected_min in test_cases:
            score = self.processor._score_resolution(width, height)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            # Allow some tolerance in scoring
            self.assertGreaterEqual(score, expected_min - 0.1)
    
    def test_score_fps(self):
        """Test FPS scoring"""
        test_cases = [
            (60.0, 1.0),    # 60 FPS - perfect
            (30.0, 0.9),    # 30 FPS - high
            (24.0, 0.7),    # 24 FPS - good
            (15.0, 0.4),    # 15 FPS - low
            (10.0, 0.1)     # 10 FPS - very low
        ]
        
        for fps, expected_min in test_cases:
            score = self.processor._score_fps(fps)
            self.assertGreaterEqual(score, 0.0)
            self.assertLessEqual(score, 1.0)
            self.assertGreaterEqual(score, expected_min - 0.1)


class TestVideoPlayerHTML(unittest.TestCase):
    """Test cases for HTML video player generation"""
    
    def test_create_video_player_html(self):
        """Test HTML video player creation"""
        # Sample data
        video_path = "test_video.mp4"
        subtitle_path = "test_subtitles.srt"
        chapters = [
            VideoChapter(
                start_time=0.0,
                end_time=30.0,
                title="Introduction",
                description="Video introduction",
                confidence=0.8
            ),
            VideoChapter(
                start_time=30.0,
                end_time=60.0,
                title="Main Content",
                description="Main video content",
                confidence=0.9
            )
        ]
        
        html_content = create_video_player_html(
            video_path=video_path,
            subtitle_path=subtitle_path,
            chapters=chapters
        )
        
        self.assertIsInstance(html_content, str)
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<video', html_content)
        self.assertIn(video_path, html_content)
        self.assertIn(subtitle_path, html_content)
        self.assertIn('Introduction', html_content)
        self.assertIn('Main Content', html_content)
        self.assertIn('JavaScript', html_content)
    
    def test_create_video_player_html_no_subtitles(self):
        """Test HTML video player creation without subtitles"""
        video_path = "test_video.mp4"
        
        html_content = create_video_player_html(
            video_path=video_path,
            subtitle_path=None,
            chapters=None
        )
        
        self.assertIsInstance(html_content, str)
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<video', html_content)
        self.assertIn(video_path, html_content)
        self.assertNotIn('<track', html_content)


class TestVideoDataClasses(unittest.TestCase):
    """Test cases for video data classes"""
    
    def test_video_metadata_creation(self):
        """Test VideoMetadata data class"""
        metadata = VideoMetadata(
            duration=120.5,
            width=1920,
            height=1080,
            fps=30.0,
            bitrate=5000000,
            codec='h264',
            format='mp4',
            size_bytes=75000000,
            aspect_ratio='16:9',
            has_audio=True,
            audio_codec='aac',
            audio_bitrate=128000,
            audio_sample_rate=44100
        )
        
        self.assertEqual(metadata.duration, 120.5)
        self.assertEqual(metadata.width, 1920)
        self.assertEqual(metadata.height, 1080)
        self.assertTrue(metadata.has_audio)
        self.assertEqual(metadata.audio_codec, 'aac')
    
    def test_video_thumbnail_creation(self):
        """Test VideoThumbnail data class"""
        thumbnail = VideoThumbnail(
            timestamp=30.5,
            image_path="/path/to/thumbnail.jpg",
            width=320,
            height=240,
            quality_score=0.85,
            is_keyframe=True
        )
        
        self.assertEqual(thumbnail.timestamp, 30.5)
        self.assertEqual(thumbnail.quality_score, 0.85)
        self.assertTrue(thumbnail.is_keyframe)
    
    def test_video_chapter_creation(self):
        """Test VideoChapter data class"""
        chapter = VideoChapter(
            start_time=0.0,
            end_time=60.0,
            title="Introduction",
            description="This is the introduction chapter",
            confidence=0.9,
            keywords=['introduction', 'welcome', 'overview']
        )
        
        self.assertEqual(chapter.start_time, 0.0)
        self.assertEqual(chapter.end_time, 60.0)
        self.assertEqual(chapter.title, "Introduction")
        self.assertEqual(chapter.confidence, 0.9)
        self.assertIn('introduction', chapter.keywords)
    
    def test_subtitle_entry_creation(self):
        """Test SubtitleEntry data class"""
        entry = SubtitleEntry(
            index=1,
            start_time=0.0,
            end_time=5.0,
            text="Welcome to this video",
            speaker="Narrator",
            confidence=0.95
        )
        
        self.assertEqual(entry.index, 1)
        self.assertEqual(entry.text, "Welcome to this video")
        self.assertEqual(entry.speaker, "Narrator")
        self.assertEqual(entry.confidence, 0.95)
    
    def test_video_quality_metrics_creation(self):
        """Test VideoQualityMetrics data class"""
        metrics = VideoQualityMetrics(
            resolution_score=0.9,
            bitrate_score=0.8,
            fps_score=0.9,
            compression_score=0.7,
            overall_score=0.85,
            recommendations=["Increase bitrate for better quality"],
            technical_details={"file_size_mb": 75.0, "duration_minutes": 2.0}
        )
        
        self.assertEqual(metrics.overall_score, 0.85)
        self.assertEqual(len(metrics.recommendations), 1)
        self.assertIn("file_size_mb", metrics.technical_details)


def create_test_suite():
    """Create a comprehensive test suite"""
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestVideoProcessor,
        TestVideoPlayerHTML,
        TestVideoDataClasses
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite


def run_tests():
    """Run all tests and return results"""
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    print("🧪 Running Video Processing Tests...")
    print("=" * 50)
    
    success = run_tests()
    
    print("=" * 50)
    if success:
        print("✅ All tests passed!")
    else:
        print("❌ Some tests failed!")
    
    sys.exit(0 if success else 1)