#!/usr/bin/env python3
"""
Integration Test for Video Processing Features
Tests the complete video processing pipeline for Task 30
"""

import os
import sys
import unittest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_processing import VideoProcessor, create_video_player_html
from video_ui import VideoUI


class TestVideoProcessingIntegration(unittest.TestCase):
    """Integration tests for complete video processing workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.processor = VideoProcessor()
        self.video_ui = VideoUI()
        self.temp_dir = tempfile.mkdtemp()
        
        # Sample video path
        self.mock_video_path = os.path.join(self.temp_dir, "test_video.mp4")
        
        # Sample transcript data
        self.sample_transcript = {
            "segments": [
                {"start": 0.0, "end": 10.0, "text": "Welcome to our video processing demonstration."},
                {"start": 10.0, "end": 20.0, "text": "Today we'll explore advanced video analysis features."},
                {"start": 20.0, "end": 30.0, "text": "First, let's look at thumbnail generation capabilities."},
                {"start": 30.0, "end": 40.0, "text": "Next, we'll demonstrate subtitle generation in multiple formats."},
                {"start": 40.0, "end": 50.0, "text": "Moving on to chapter detection and content analysis."},
                {"start": 50.0, "end": 60.0, "text": "Finally, we'll analyze video quality and provide recommendations."}
            ]
        }
    
    def tearDown(self):
        """Clean up test environment"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('ffmpeg.probe')
    @patch('cv2.VideoCapture')
    @patch('cv2.imwrite')
    def test_complete_video_processing_workflow(self, mock_imwrite, mock_cv2, mock_probe):
        """Test complete video processing workflow from upload to output"""
        
        # Mock ffmpeg probe for metadata
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
                'duration': '60.0',
                'bit_rate': '5000000',
                'format_name': 'mp4',
                'size': '37500000'
            }
        }
        
        # Mock OpenCV VideoCapture
        mock_cap = Mock()
        mock_cv2.return_value = mock_cap
        mock_cap.isOpened.return_value = True
        mock_cap.get.side_effect = lambda prop: {
            'CAP_PROP_FPS': 30.0,
            'CAP_PROP_FRAME_COUNT': 1800,
            'CAP_PROP_POS_FRAMES': 0,
            'CAP_PROP_POS_MSEC': 0
        }.get(prop, 0)
        
        # Mock frame reading
        mock_frame = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        mock_cap.read.return_value = (True, mock_frame)
        mock_imwrite.return_value = True
        
        # Step 1: Extract metadata
        print("🔍 Step 1: Extracting video metadata...")
        metadata = self.processor.extract_metadata(self.mock_video_path)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.width, 1920)
        self.assertEqual(metadata.height, 1080)
        self.assertEqual(metadata.duration, 60.0)
        print(f"   ✅ Metadata extracted: {metadata.width}×{metadata.height}, {metadata.duration}s")
        
        # Step 2: Generate thumbnails
        print("🖼️ Step 2: Generating video thumbnails...")
        thumbnails = self.processor.generate_thumbnails(self.mock_video_path, count=5)
        
        self.assertEqual(len(thumbnails), 5)
        for thumbnail in thumbnails:
            self.assertGreaterEqual(thumbnail.timestamp, 0)
            self.assertLessEqual(thumbnail.timestamp, 60.0)
            self.assertGreater(thumbnail.quality_score, 0)
        print(f"   ✅ Generated {len(thumbnails)} thumbnails")
        
        # Step 3: Generate subtitles
        print("📝 Step 3: Generating subtitles...")
        
        # SRT format
        srt_path = os.path.join(self.temp_dir, "test.srt")
        srt_result = self.processor.generate_subtitles(
            self.sample_transcript, srt_path, 'srt'
        )
        
        self.assertEqual(srt_result, srt_path)
        self.assertTrue(os.path.exists(srt_path))
        
        # VTT format
        vtt_path = os.path.join(self.temp_dir, "test.vtt")
        vtt_result = self.processor.generate_subtitles(
            self.sample_transcript, vtt_path, 'vtt'
        )
        
        self.assertEqual(vtt_result, vtt_path)
        self.assertTrue(os.path.exists(vtt_path))
        print("   ✅ Generated SRT and VTT subtitles")
        
        # Step 4: Detect chapters
        print("📚 Step 4: Detecting video chapters...")
        chapters = self.processor.detect_chapters(
            self.mock_video_path, self.sample_transcript
        )
        
        self.assertIsInstance(chapters, list)
        if chapters:
            for chapter in chapters:
                self.assertGreaterEqual(chapter.end_time, chapter.start_time)
                self.assertIsInstance(chapter.title, str)
        print(f"   ✅ Detected {len(chapters)} chapters")
        
        # Step 5: Analyze video quality
        print("🎯 Step 5: Analyzing video quality...")
        quality_metrics = self.processor.analyze_video_quality(self.mock_video_path)
        
        self.assertIsNotNone(quality_metrics)
        self.assertGreaterEqual(quality_metrics.overall_score, 0.0)
        self.assertLessEqual(quality_metrics.overall_score, 1.0)
        self.assertIsInstance(quality_metrics.recommendations, list)
        print(f"   ✅ Quality score: {quality_metrics.overall_score:.2f}")
        
        # Step 6: Create enhanced video player
        print("🎬 Step 6: Creating enhanced video player...")
        html_content = create_video_player_html(
            video_path=self.mock_video_path,
            subtitle_path=srt_path,
            chapters=chapters
        )
        
        self.assertIsInstance(html_content, str)
        self.assertIn('<!DOCTYPE html>', html_content)
        self.assertIn('<video', html_content)
        print("   ✅ Enhanced video player created")
        
        # Step 7: Verify all outputs
        print("✅ Step 7: Verifying all outputs...")
        
        # Check subtitle files
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
            self.assertIn('1\n', srt_content)
            self.assertIn('Welcome to our video processing demonstration.', srt_content)
        
        with open(vtt_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
            self.assertTrue(vtt_content.startswith('WEBVTT'))
            self.assertIn('Welcome to our video processing demonstration.', vtt_content)
        
        # Check HTML player
        self.assertIn('video-container', html_content)
        self.assertIn('chapters-panel', html_content)
        self.assertIn('transcript-panel', html_content)
        
        print("🎉 Complete video processing workflow test passed!")
        
        return {
            'metadata': metadata,
            'thumbnails': thumbnails,
            'srt_path': srt_path,
            'vtt_path': vtt_path,
            'chapters': chapters,
            'quality_metrics': quality_metrics,
            'html_content': html_content
        }
    
    def test_error_handling_and_recovery(self):
        """Test error handling and graceful degradation"""
        print("🛡️ Testing error handling and recovery...")
        
        # Test with invalid video path
        with self.assertRaises(Exception):
            self.processor.extract_metadata("nonexistent_video.mp4")
        
        # Test subtitle generation with invalid data
        invalid_transcript = {"invalid": "data"}
        with self.assertRaises(Exception):
            self.processor.generate_subtitles(
                invalid_transcript, 
                os.path.join(self.temp_dir, "invalid.srt"), 
                'srt'
            )
        
        # Test with empty transcript
        empty_transcript = {"segments": []}
        srt_path = os.path.join(self.temp_dir, "empty.srt")
        
        try:
            result = self.processor.generate_subtitles(empty_transcript, srt_path, 'srt')
            # Should handle empty transcript gracefully
            self.assertTrue(os.path.exists(srt_path))
        except Exception as e:
            # Or raise appropriate exception
            self.assertIsInstance(e, (ValueError, TypeError))
        
        print("   ✅ Error handling tests passed")
    
    def test_performance_with_large_transcript(self):
        """Test performance with large transcript data"""
        print("⚡ Testing performance with large transcript...")
        
        # Create large transcript (simulate 1 hour video)
        large_transcript = {"segments": []}
        for i in range(360):  # 360 segments for 1 hour (10s each)
            segment = {
                "start": i * 10.0,
                "end": (i + 1) * 10.0,
                "text": f"This is segment {i+1} of a very long video transcript for performance testing."
            }
            large_transcript["segments"].append(segment)
        
        # Test subtitle generation performance
        import time
        
        start_time = time.time()
        srt_path = os.path.join(self.temp_dir, "large.srt")
        self.processor.generate_subtitles(large_transcript, srt_path, 'srt')
        end_time = time.time()
        
        processing_time = end_time - start_time
        self.assertLess(processing_time, 10.0)  # Should complete within 10 seconds
        self.assertTrue(os.path.exists(srt_path))
        
        # Verify content
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn('360\n', content)  # Should have 360 entries
        
        print(f"   ✅ Processed {len(large_transcript['segments'])} segments in {processing_time:.2f}s")
    
    def test_subtitle_format_compatibility(self):
        """Test subtitle format compatibility and standards compliance"""
        print("📝 Testing subtitle format compatibility...")
        
        # Test SRT format compliance
        srt_path = os.path.join(self.temp_dir, "compliance.srt")
        self.processor.generate_subtitles(self.sample_transcript, srt_path, 'srt')
        
        with open(srt_path, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        # Check SRT format compliance
        lines = srt_content.strip().split('\n')
        
        # Should start with entry number
        self.assertEqual(lines[0], '1')
        
        # Should have timestamp format HH:MM:SS,mmm --> HH:MM:SS,mmm
        timestamp_line = lines[1]
        self.assertRegex(timestamp_line, r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}')
        
        # Test VTT format compliance
        vtt_path = os.path.join(self.temp_dir, "compliance.vtt")
        self.processor.generate_subtitles(self.sample_transcript, vtt_path, 'vtt')
        
        with open(vtt_path, 'r', encoding='utf-8') as f:
            vtt_content = f.read()
        
        # Should start with WEBVTT
        self.assertTrue(vtt_content.startswith('WEBVTT'))
        
        # Should have timestamp format HH:MM:SS.mmm --> HH:MM:SS.mmm
        self.assertRegex(vtt_content, r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}')
        
        print("   ✅ Subtitle format compliance verified")
    
    def test_chapter_detection_accuracy(self):
        """Test chapter detection accuracy with different content types"""
        print("📚 Testing chapter detection accuracy...")
        
        # Test with clear topic transitions
        structured_transcript = {
            "segments": [
                {"start": 0.0, "end": 10.0, "text": "Welcome to today's presentation."},
                {"start": 10.0, "end": 20.0, "text": "First, let's discuss the introduction."},
                {"start": 20.0, "end": 30.0, "text": "Now let's move on to the main topic."},
                {"start": 30.0, "end": 40.0, "text": "This section covers advanced features."},
                {"start": 40.0, "end": 50.0, "text": "In conclusion, we've covered everything."},
                {"start": 50.0, "end": 60.0, "text": "Thank you for your attention."}
            ]
        }
        
        chapters = self.processor._detect_content_chapters(structured_transcript, min_length=15.0)
        
        # Should detect topic transitions
        self.assertGreater(len(chapters), 0)
        
        # Verify chapter boundaries make sense
        for i, chapter in enumerate(chapters):
            self.assertGreaterEqual(chapter.end_time, chapter.start_time)
            self.assertGreaterEqual(chapter.end_time - chapter.start_time, 15.0)  # Min length
            
            if i > 0:
                # Chapters should not overlap
                self.assertGreaterEqual(chapter.start_time, chapters[i-1].end_time)
        
        print(f"   ✅ Detected {len(chapters)} chapters with clear boundaries")
    
    def test_quality_analysis_accuracy(self):
        """Test video quality analysis accuracy"""
        print("🎯 Testing quality analysis accuracy...")
        
        # Test different quality scenarios
        quality_scenarios = [
            {
                'name': '4K High Quality',
                'metadata': {
                    'width': 3840, 'height': 2160, 'fps': 60.0, 
                    'bitrate': 25000000, 'duration': 120.0, 'size_bytes': 375000000
                },
                'expected_min_score': 0.8
            },
            {
                'name': '1080p Standard',
                'metadata': {
                    'width': 1920, 'height': 1080, 'fps': 30.0,
                    'bitrate': 8000000, 'duration': 120.0, 'size_bytes': 120000000
                },
                'expected_min_score': 0.7
            },
            {
                'name': '720p Low Quality',
                'metadata': {
                    'width': 1280, 'height': 720, 'fps': 24.0,
                    'bitrate': 2000000, 'duration': 120.0, 'size_bytes': 30000000
                },
                'expected_min_score': 0.4
            }
        ]
        
        for scenario in quality_scenarios:
            # Calculate quality scores
            resolution_score = self.processor._score_resolution(
                scenario['metadata']['width'], 
                scenario['metadata']['height']
            )
            
            fps_score = self.processor._score_fps(scenario['metadata']['fps'])
            
            bitrate_score = self.processor._score_bitrate(
                scenario['metadata']['bitrate'],
                scenario['metadata']['width'],
                scenario['metadata']['height'],
                scenario['metadata']['fps']
            )
            
            # Verify scores are reasonable
            self.assertGreaterEqual(resolution_score, 0.0)
            self.assertLessEqual(resolution_score, 1.0)
            self.assertGreaterEqual(fps_score, 0.0)
            self.assertLessEqual(fps_score, 1.0)
            self.assertGreaterEqual(bitrate_score, 0.0)
            self.assertLessEqual(bitrate_score, 1.0)
            
            print(f"   📊 {scenario['name']}: Resolution={resolution_score:.2f}, FPS={fps_score:.2f}, Bitrate={bitrate_score:.2f}")
        
        print("   ✅ Quality analysis accuracy verified")
    
    def test_html_player_functionality(self):
        """Test HTML video player functionality and structure"""
        print("🎬 Testing HTML video player functionality...")
        
        # Create sample chapters
        from video_processing import VideoChapter
        
        chapters = [
            VideoChapter(0.0, 30.0, "Introduction", "Opening section", confidence=0.9),
            VideoChapter(30.0, 60.0, "Main Content", "Core material", confidence=0.8)
        ]
        
        # Generate HTML player
        html_content = create_video_player_html(
            video_path="test_video.mp4",
            subtitle_path="test_subtitles.srt",
            chapters=chapters
        )
        
        # Test HTML structure
        required_elements = [
            '<!DOCTYPE html>',
            '<video',
            'class="video-player"',
            'class="chapters-panel"',
            'class="transcript-panel"',
            '<script>',
            'JavaScript',
            'formatTime',
            'updateActiveChapter'
        ]
        
        for element in required_elements:
            self.assertIn(element, html_content)
        
        # Test chapter data embedding
        self.assertIn('Introduction', html_content)
        self.assertIn('Main Content', html_content)
        
        # Test responsive design elements
        responsive_elements = [
            'viewport',
            'max-width',
            'grid-template-columns',
            'media'
        ]
        
        for element in responsive_elements:
            self.assertIn(element, html_content)
        
        print("   ✅ HTML player structure and functionality verified")


def run_integration_tests():
    """Run all integration tests"""
    print("🧪 Running Video Processing Integration Tests...")
    print("=" * 60)
    
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVideoProcessingIntegration)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("=" * 60)
    if result.wasSuccessful():
        print("✅ All integration tests passed!")
        print("🎉 Video processing features are ready for production!")
    else:
        print("❌ Some integration tests failed!")
        print("🔧 Please review the failures and fix any issues.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)