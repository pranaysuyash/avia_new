"""
Test suite for External Media Integration System
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from external_media_integration import (
    ExternalMediaManager, 
    YouTubeIntegration, 
    ZoomIntegration,
    PodcastRSSIntegration,
    CloudStorageIntegration,
    MediaSource,
    ExtractionResult
)

class TestYouTubeIntegration:
    """Test YouTube integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.youtube = YouTubeIntegration()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_extract_video_id_standard_url(self):
        """Test video ID extraction from standard YouTube URL"""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = self.youtube.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_short_url(self):
        """Test video ID extraction from short YouTube URL"""
        url = "https://youtu.be/dQw4w9WgXcQ"
        video_id = self.youtube.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_embed_url(self):
        """Test video ID extraction from embed URL"""
        url = "https://www.youtube.com/embed/dQw4w9WgXcQ"
        video_id = self.youtube.extract_video_id(url)
        assert video_id == "dQw4w9WgXcQ"
    
    def test_extract_video_id_invalid_url(self):
        """Test video ID extraction from invalid URL"""
        url = "https://example.com/not-youtube"
        video_id = self.youtube.extract_video_id(url)
        assert video_id is None
    
    @patch('requests.get')
    def test_get_video_info_success(self, mock_get):
        """Test successful video info retrieval"""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = {
            'items': [{
                'snippet': {
                    'title': 'Test Video',
                    'description': 'Test Description'
                },
                'contentDetails': {
                    'duration': 'PT3M30S'
                }
            }]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        self.youtube.api_key = "test_key"
        result = self.youtube.get_video_info("dQw4w9WgXcQ")
        
        assert result is not None
        assert result['snippet']['title'] == 'Test Video'
    
    def test_get_video_info_no_api_key(self):
        """Test video info retrieval without API key"""
        self.youtube.api_key = None
        result = self.youtube.get_video_info("dQw4w9WgXcQ")
        assert result is None
    
    @patch('yt_dlp.YoutubeDL')
    def test_download_audio_success(self, mock_ydl_class):
        """Test successful audio download"""
        # Mock yt-dlp
        mock_ydl = Mock()
        mock_ydl.extract_info.return_value = {
            'title': 'Test Video',
            'description': 'Test Description',
            'duration': 210,
            'uploader': 'Test Channel'
        }
        mock_ydl.prepare_filename.return_value = f"{self.temp_dir}/test_video.wav"
        mock_ydl.download.return_value = None
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        
        # Create expected output file
        expected_file = f"{self.temp_dir}/test_video.wav"
        with open(expected_file, 'w') as f:
            f.write("fake audio data")
        
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        result = self.youtube.download_audio(url, self.temp_dir)
        
        assert result.success is True
        assert result.media_info.source_type == "youtube"
        assert result.media_info.title == "Test Video"
    
    def test_download_audio_invalid_url(self):
        """Test audio download with invalid URL"""
        url = "https://example.com/not-youtube"
        result = self.youtube.download_audio(url, self.temp_dir)
        
        assert result.success is False
        assert "Invalid YouTube URL" in result.error_message

class TestPodcastRSSIntegration:
    """Test podcast RSS integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.podcast = PodcastRSSIntegration()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    @patch('feedparser.parse')
    def test_parse_rss_feed_success(self, mock_parse):
        """Test successful RSS feed parsing"""
        # Mock feedparser response
        mock_parse.return_value = Mock(
            feed=Mock(title="Test Podcast"),
            entries=[
                Mock(
                    title="Episode 1",
                    summary="Episode 1 description",
                    published="2023-01-01",
                    author="Test Author",
                    link="https://example.com/episode1",
                    enclosures=[Mock(type="audio/mpeg", href="https://example.com/episode1.mp3")]
                ),
                Mock(
                    title="Episode 2",
                    summary="Episode 2 description",
                    published="2023-01-02",
                    author="Test Author",
                    link="https://example.com/episode2",
                    enclosures=[Mock(type="audio/mpeg", href="https://example.com/episode2.mp3")]
                )
            ]
        )
        
        episodes = self.podcast.parse_rss_feed("https://example.com/feed.xml")
        
        assert len(episodes) == 2
        assert episodes[0].title == "Episode 1"
        assert episodes[0].source_type == "podcast"
        assert episodes[1].title == "Episode 2"
    
    @patch('feedparser.parse')
    def test_parse_rss_feed_no_audio(self, mock_parse):
        """Test RSS feed parsing with no audio enclosures"""
        mock_parse.return_value = Mock(
            feed=Mock(title="Test Podcast"),
            entries=[
                Mock(
                    title="Episode 1",
                    summary="Episode 1 description",
                    enclosures=[]  # No audio enclosures
                )
            ]
        )
        
        episodes = self.podcast.parse_rss_feed("https://example.com/feed.xml")
        assert len(episodes) == 0
    
    @patch('requests.Session.get')
    def test_download_episode_success(self, mock_get):
        """Test successful episode download"""
        # Mock HTTP response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"fake audio data"]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        episode = MediaSource(
            source_type="podcast",
            url="https://example.com/episode.mp3",
            title="Test Episode",
            description="Test Description"
        )
        
        result = self.podcast.download_episode(episode, self.temp_dir)
        
        assert result.success is True
        assert result.media_info.title == "Test Episode"
        assert os.path.exists(result.local_path)

class TestCloudStorageIntegration:
    """Test cloud storage integration functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.cloud_storage = CloudStorageIntegration()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_setup_google_drive_missing_deps(self):
        """Test Google Drive setup with missing dependencies"""
        result = self.cloud_storage.setup_google_drive("fake_credentials.json")
        # Should return False due to missing Google API dependencies in test environment
        assert result is False
    
    def test_setup_dropbox_missing_deps(self):
        """Test Dropbox setup with missing dependencies"""
        result = self.cloud_storage.setup_dropbox("fake_token")
        # Should return False due to missing Dropbox API dependencies in test environment
        assert result is False

class TestExternalMediaManager:
    """Test the main external media manager"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = ExternalMediaManager()
        self.temp_dir = tempfile.mkdtemp()
        self.manager.temp_dir = self.temp_dir
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_detect_source_type_youtube(self):
        """Test source type detection for YouTube"""
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ"
        ]
        
        for url in urls:
            assert self.manager.detect_source_type(url) == "youtube"
    
    def test_detect_source_type_zoom(self):
        """Test source type detection for Zoom"""
        url = "https://zoom.us/rec/share/abc123"
        assert self.manager.detect_source_type(url) == "zoom"
    
    def test_detect_source_type_gdrive(self):
        """Test source type detection for Google Drive"""
        url = "https://drive.google.com/file/d/abc123/view"
        assert self.manager.detect_source_type(url) == "gdrive"
    
    def test_detect_source_type_dropbox(self):
        """Test source type detection for Dropbox"""
        url = "https://www.dropbox.com/s/abc123/file.mp3"
        assert self.manager.detect_source_type(url) == "dropbox"
    
    def test_detect_source_type_podcast(self):
        """Test source type detection for podcast RSS"""
        urls = [
            "https://feeds.example.com/podcast.xml",
            "https://example.com/feed.rss",
            "https://example.com/podcast-rss"
        ]
        
        for url in urls:
            assert self.manager.detect_source_type(url) == "podcast"
    
    def test_detect_source_type_unknown(self):
        """Test source type detection for unknown URLs"""
        url = "https://example.com/unknown"
        assert self.manager.detect_source_type(url) == "unknown"
    
    def test_extract_gdrive_file_id(self):
        """Test Google Drive file ID extraction"""
        urls_and_ids = [
            ("https://drive.google.com/file/d/abc123def456/view", "abc123def456"),
            ("https://drive.google.com/open?id=abc123def456", "abc123def456"),
            ("https://docs.google.com/document/d/abc123def456/edit", "abc123def456")
        ]
        
        for url, expected_id in urls_and_ids:
            file_id = self.manager._extract_gdrive_file_id(url)
            assert file_id == expected_id
    
    def test_get_supported_sources(self):
        """Test getting supported source types"""
        sources = self.manager.get_supported_sources()
        expected_sources = ['youtube', 'zoom', 'podcast', 'gdrive', 'dropbox']
        
        assert all(source in sources for source in expected_sources)
    
    def test_cleanup_temp_files(self):
        """Test temporary file cleanup"""
        # Create some test files
        test_files = [
            os.path.join(self.temp_dir, "test1.mp3"),
            os.path.join(self.temp_dir, "test2.wav")
        ]
        
        for file_path in test_files:
            with open(file_path, 'w') as f:
                f.write("test data")
        
        # Verify files exist
        for file_path in test_files:
            assert os.path.exists(file_path)
        
        # Cleanup with 0 hours (should remove all files)
        self.manager.cleanup_temp_files(max_age_hours=0)
        
        # Files should still exist since they were just created
        # (cleanup only removes files older than max_age_hours)
        for file_path in test_files:
            assert os.path.exists(file_path)

class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = ExternalMediaManager()
        self.temp_dir = tempfile.mkdtemp()
        self.manager.temp_dir = self.temp_dir
    
    def teardown_method(self):
        """Cleanup test environment"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_process_unsupported_source(self):
        """Test processing unsupported source type"""
        url = "https://example.com/unsupported"
        result = self.manager.process_external_source(url)
        
        assert result.success is False
        assert "Unsupported source type" in result.error_message
    
    def test_process_zoom_without_setup(self):
        """Test processing Zoom URL without proper setup"""
        url = "https://zoom.us/rec/share/abc123"
        result = self.manager.process_external_source(url, meeting_id="123456789")
        
        assert result.success is False
        assert "Zoom integration not configured" in result.error_message
    
    @patch('external_media_integration.YouTubeIntegration.download_audio')
    def test_process_youtube_success(self, mock_download):
        """Test successful YouTube processing"""
        # Mock successful download
        mock_result = ExtractionResult(
            success=True,
            local_path=f"{self.temp_dir}/test.wav",
            media_info=MediaSource(
                source_type="youtube",
                url="https://www.youtube.com/watch?v=test",
                title="Test Video"
            )
        )
        mock_download.return_value = mock_result
        
        url = "https://www.youtube.com/watch?v=test"
        result = self.manager.process_external_source(url)
        
        assert result.success is True
        assert result.media_info.source_type == "youtube"
        mock_download.assert_called_once()
    
    @patch('external_media_integration.PodcastRSSIntegration.parse_rss_feed')
    @patch('external_media_integration.PodcastRSSIntegration.download_episode')
    def test_process_podcast_success(self, mock_download, mock_parse):
        """Test successful podcast processing"""
        # Mock RSS parsing
        test_episode = MediaSource(
            source_type="podcast",
            url="https://example.com/episode.mp3",
            title="Test Episode"
        )
        mock_parse.return_value = [test_episode]
        
        # Mock episode download
        mock_result = ExtractionResult(
            success=True,
            local_path=f"{self.temp_dir}/test_episode.mp3",
            media_info=test_episode
        )
        mock_download.return_value = mock_result
        
        url = "https://feeds.example.com/podcast.xml"
        result = self.manager.process_external_source(url)
        
        assert result.success is True
        assert result.media_info.source_type == "podcast"
        mock_parse.assert_called_once_with(url)
        mock_download.assert_called_once()

# Performance and stress tests
class TestPerformance:
    """Test performance and resource usage"""
    
    def setup_method(self):
        """Setup test environment"""
        self.manager = ExternalMediaManager()
    
    def test_multiple_source_detection(self):
        """Test performance of source type detection with multiple URLs"""
        urls = [
            "https://www.youtube.com/watch?v=test1",
            "https://youtu.be/test2",
            "https://zoom.us/rec/share/test3",
            "https://feeds.example.com/podcast.xml",
            "https://drive.google.com/file/d/test4/view",
            "https://www.dropbox.com/s/test5/file.mp3"
        ] * 100  # Test with 600 URLs
        
        import time
        start_time = time.time()
        
        for url in urls:
            self.manager.detect_source_type(url)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 600 URLs in less than 1 second
        assert processing_time < 1.0
    
    def test_memory_usage_with_large_metadata(self):
        """Test memory usage with large metadata objects"""
        large_metadata = {
            'description': 'x' * 10000,  # 10KB description
            'tags': ['tag' + str(i) for i in range(1000)],  # 1000 tags
            'comments': [{'text': 'comment' + str(i)} for i in range(100)]  # 100 comments
        }
        
        media_sources = []
        for i in range(100):
            media_source = MediaSource(
                source_type="test",
                url=f"https://example.com/test{i}",
                title=f"Test {i}",
                metadata=large_metadata.copy()
            )
            media_sources.append(media_source)
        
        # Should be able to create 100 media sources with large metadata
        assert len(media_sources) == 100
        assert all(len(ms.metadata['description']) == 10000 for ms in media_sources)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])