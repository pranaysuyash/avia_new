"""
Comprehensive test suite for Timestamping System

Tests cover:
- Word-level timestamp generation and accuracy
- Segment timestamp creation and management
- Time code generation and formatting
- Clickable transcript functionality
- Bookmark system operations
- Search and navigation features
- Export capabilities in multiple formats
- Database operations and data integrity

Requirements: 3.1, 7.4
"""

import pytest
import os
import json
import sqlite3
import tempfile
import shutil
import time
from datetime import datetime
from typing import List, Dict, Any
from unittest.mock import Mock, patch, MagicMock

# Import the timestamping system components
from timestamping_system import (
    TimestampingSystem, WordTimestamp, SegmentTimestamp, 
    TimeCode, Bookmark, TranscriptSegment
)

class TestTimestampingSystem:
    """Test suite for the Timestamping System"""
    
    @pytest.fixture
    def temp_db_path(self):
        """Create temporary database for testing"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test_timestamping.db")
        yield db_path
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def ts_system(self, temp_db_path):
        """Create TimestampingSystem instance with temporary database"""
        return TimestampingSystem(database_path=temp_db_path)
    
    @pytest.fixture
    def sample_transcript(self):
        """Sample transcript for testing"""
        return "Hello world. This is a test transcript. We are testing the system."
    
    @pytest.fixture
    def sample_audio_path(self):
        """Mock audio file path"""
        return "test_audio.wav"
    
    @pytest.fixture
    def sample_content_id(self):
        """Sample content ID for testing"""
        return "test_content_001"
    
    def test_database_initialization(self, ts_system):
        """Test database initialization and table creation"""
        # Check if database file exists
        assert os.path.exists(ts_system.database_path)
        
        # Check if tables are created
        conn = sqlite3.connect(ts_system.database_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'word_timestamps', 'segment_timestamps', 'time_codes', 
            'bookmarks', 'transcript_segments'
        ]
        
        for table in expected_tables:
            assert table in tables, f"Table {table} not found"
        
        conn.close()
    
    def test_word_timestamp_creation(self):
        """Test WordTimestamp dataclass functionality"""
        word_ts = WordTimestamp(
            word="test",
            start_time=1.0,
            end_time=1.5,
            confidence=0.95,
            speaker_id="speaker_1"
        )
        
        assert word_ts.word == "test"
        assert word_ts.start_time == 1.0
        assert word_ts.end_time == 1.5
        assert word_ts.confidence == 0.95
        assert word_ts.speaker_id == "speaker_1"
        assert word_ts.duration() == 0.5
        
        # Test dictionary conversion
        word_dict = word_ts.to_dict()
        assert isinstance(word_dict, dict)
        assert word_dict['word'] == "test"
        assert word_dict['duration'] == 0.5  # This would be calculated if added to to_dict
    
    def test_segment_timestamp_creation(self):
        """Test SegmentTimestamp dataclass functionality"""
        segment_ts = SegmentTimestamp(
            id="seg_1",
            start_time=0.0,
            end_time=10.0,
            segment_type="speaker",
            content="Test segment content",
            speaker_id="speaker_1",
            confidence=0.9
        )
        
        assert segment_ts.id == "seg_1"
        assert segment_ts.duration() == 10.0
        assert segment_ts.segment_type == "speaker"
        assert segment_ts.content == "Test segment content"
        
        # Test dictionary conversion
        segment_dict = segment_ts.to_dict()
        assert isinstance(segment_dict, dict)
        assert segment_dict['id'] == "seg_1"
    
    def test_time_code_formatting(self):
        """Test TimeCode formatting functionality"""
        time_code = TimeCode(
            timestamp=125.750,  # 2 minutes, 5.75 seconds
            label="Test Marker",
            description="Test description",
            category="bookmark"
        )
        
        # Test different time formats
        hms_format = time_code.format_time("hms")
        assert hms_format == "00:02:05.750"
        
        ms_format = time_code.format_time("ms")
        assert ms_format == "02:05.750"
        
        seconds_format = time_code.format_time("seconds")
        assert seconds_format == "125.750s"
    
    def test_bookmark_creation(self):
        """Test Bookmark dataclass functionality"""
        bookmark = Bookmark(
            id="bookmark_1",
            timestamp=30.5,
            title="Important Moment",
            description="Key discussion point",
            tags=["important", "discussion"],
            user_id="user_123"
        )
        
        assert bookmark.id == "bookmark_1"
        assert bookmark.timestamp == 30.5
        assert bookmark.title == "Important Moment"
        assert "important" in bookmark.tags
        assert isinstance(bookmark.created_at, datetime)
        
        # Test dictionary conversion
        bookmark_dict = bookmark.to_dict()
        assert isinstance(bookmark_dict, dict)
        assert bookmark_dict['title'] == "Important Moment"
    
    @patch('timestamping_system.librosa')
    def test_word_timestamp_generation_forced_alignment(self, mock_librosa, ts_system, 
                                                       sample_audio_path, sample_transcript, 
                                                       sample_content_id):
        """Test word timestamp generation using forced alignment method"""
        # Mock librosa functions
        mock_librosa.load.return_value = ([0.1] * 16000, 16000)  # 1 second of audio
        
        word_timestamps = ts_system.generate_word_timestamps(
            audio_path=sample_audio_path,
            transcript=sample_transcript,
            content_id=sample_content_id,
            method="forced_alignment"
        )
        
        assert isinstance(word_timestamps, list)
        assert len(word_timestamps) > 0
        
        # Check first word timestamp
        first_word = word_timestamps[0]
        assert isinstance(first_word, WordTimestamp)
        assert first_word.word in sample_transcript.split()
        assert first_word.start_time >= 0
        assert first_word.end_time > first_word.start_time
        assert 0 <= first_word.confidence <= 1
    
    @patch('timestamping_system.webrtcvad')
    @patch('timestamping_system.librosa')
    def test_word_timestamp_generation_vad_based(self, mock_librosa, mock_webrtcvad, 
                                                ts_system, sample_audio_path, 
                                                sample_transcript, sample_content_id):
        """Test word timestamp generation using VAD-based method"""
        # Mock librosa and webrtcvad
        mock_librosa.load.return_value = ([0.1] * 16000, 16000)
        mock_vad = Mock()
        mock_vad.is_speech.return_value = True
        mock_webrtcvad.Vad.return_value = mock_vad
        
        word_timestamps = ts_system.generate_word_timestamps(
            audio_path=sample_audio_path,
            transcript=sample_transcript,
            content_id=sample_content_id,
            method="vad_based"
        )
        
        assert isinstance(word_timestamps, list)
        assert len(word_timestamps) > 0
        
        # Verify VAD was called
        mock_webrtcvad.Vad.assert_called_once()
    
    def test_word_timestamp_generation_fallback(self, ts_system, sample_audio_path, 
                                               sample_transcript, sample_content_id):
        """Test word timestamp generation fallback method"""
        # This should work without external dependencies
        word_timestamps = ts_system.generate_word_timestamps(
            audio_path=sample_audio_path,
            transcript=sample_transcript,
            content_id=sample_content_id,
            method="unknown_method"  # Should fallback to estimation
        )
        
        assert isinstance(word_timestamps, list)
        # Should still generate timestamps even with unknown method
    
    def test_segment_timestamp_generation(self, ts_system, sample_audio_path, 
                                        sample_transcript, sample_content_id):
        """Test segment timestamp generation"""
        # Test speaker-based segmentation
        speakers = ["Speaker_A", "Speaker_B"]
        
        segments = ts_system.generate_segment_timestamps(
            audio_path=sample_audio_path,
            transcript=sample_transcript,
            content_id=sample_content_id,
            speakers=speakers
        )
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        # Check segment properties
        for segment in segments:
            assert isinstance(segment, SegmentTimestamp)
            assert segment.segment_type == "speaker"
            assert segment.speaker_id in speakers
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
    
    def test_segment_timestamp_generation_topics(self, ts_system, sample_audio_path, 
                                                sample_transcript, sample_content_id):
        """Test topic-based segment timestamp generation"""
        segments = ts_system.generate_segment_timestamps(
            audio_path=sample_audio_path,
            transcript=sample_transcript,
            content_id=sample_content_id
        )
        
        assert isinstance(segments, list)
        assert len(segments) > 0
        
        # Check segment properties
        for segment in segments:
            assert isinstance(segment, SegmentTimestamp)
            assert segment.segment_type == "topic"
            assert segment.topic is not None
    
    def test_time_code_creation(self, ts_system, sample_content_id):
        """Test time code creation from segments and bookmarks"""
        # Create sample segments
        segments = [
            SegmentTimestamp(
                id="seg_1",
                start_time=0.0,
                end_time=10.0,
                segment_type="speaker",
                content="First segment",
                speaker_id="Speaker_A"
            ),
            SegmentTimestamp(
                id="seg_2",
                start_time=10.0,
                end_time=20.0,
                segment_type="topic",
                content="Second segment",
                topic="Introduction"
            )
        ]
        
        # Create sample bookmarks
        bookmarks = [
            Bookmark(
                id="bookmark_1",
                timestamp=5.0,
                title="Important Point",
                description="Key discussion"
            )
        ]
        
        time_codes = ts_system.create_time_codes(
            content_id=sample_content_id,
            segments=segments,
            bookmarks=bookmarks
        )
        
        assert isinstance(time_codes, list)
        assert len(time_codes) >= 3  # 2 segments + 1 bookmark
        
        # Check time code properties
        for time_code in time_codes:
            assert isinstance(time_code, TimeCode)
            assert time_code.timestamp >= 0
            assert time_code.label is not None
            assert time_code.category in ["speaker_change", "topic", "bookmark"]
    
    def test_clickable_transcript_creation(self, ts_system, sample_content_id, sample_transcript):
        """Test clickable transcript creation"""
        # Create sample word timestamps
        words = sample_transcript.split()
        word_timestamps = []
        
        for i, word in enumerate(words):
            word_timestamps.append(WordTimestamp(
                word=word.strip('.,!?'),
                start_time=i * 0.5,
                end_time=(i + 1) * 0.5,
                confidence=0.9
            ))
        
        transcript_segments = ts_system.create_clickable_transcript(
            content_id=sample_content_id,
            transcript=sample_transcript,
            word_timestamps=word_timestamps
        )
        
        assert isinstance(transcript_segments, list)
        assert len(transcript_segments) > 0
        
        # Check transcript segment properties
        for segment in transcript_segments:
            assert isinstance(segment, TranscriptSegment)
            assert segment.text is not None
            assert segment.start_time >= 0
            assert segment.end_time > segment.start_time
            assert segment.is_clickable is True
            assert len(segment.words) > 0
    
    def test_bookmark_management(self, ts_system, sample_content_id):
        """Test bookmark creation and retrieval"""
        # Create bookmark
        bookmark = ts_system.create_bookmark(
            content_id=sample_content_id,
            timestamp=15.5,
            title="Test Bookmark",
            description="Test description",
            tags=["test", "bookmark"],
            user_id="test_user"
        )
        
        assert isinstance(bookmark, Bookmark)
        assert bookmark.timestamp == 15.5
        assert bookmark.title == "Test Bookmark"
        assert "test" in bookmark.tags
        
        # Retrieve bookmarks
        bookmarks = ts_system.get_bookmarks(
            content_id=sample_content_id,
            user_id="test_user"
        )
        
        assert isinstance(bookmarks, list)
        assert len(bookmarks) >= 1
        
        retrieved_bookmark = bookmarks[0]
        assert retrieved_bookmark.title == "Test Bookmark"
        assert retrieved_bookmark.timestamp == 15.5
    
    def test_word_lookup_by_timestamp(self, ts_system, sample_content_id):
        """Test word lookup by timestamp"""
        # First, create some word timestamps
        word_timestamps = [
            WordTimestamp(word="hello", start_time=0.0, end_time=0.5, confidence=0.9),
            WordTimestamp(word="world", start_time=0.5, end_time=1.0, confidence=0.9),
            WordTimestamp(word="test", start_time=1.0, end_time=1.5, confidence=0.9)
        ]
        
        # Store them in database
        ts_system._store_word_timestamps(sample_content_id, word_timestamps)
        
        # Test word lookup
        word_at_time = ts_system.get_word_at_timestamp(sample_content_id, 0.25)
        assert word_at_time is not None
        assert word_at_time.word == "hello"
        
        word_at_time = ts_system.get_word_at_timestamp(sample_content_id, 0.75)
        assert word_at_time is not None
        assert word_at_time.word == "world"
        
        # Test timestamp outside range
        word_at_time = ts_system.get_word_at_timestamp(sample_content_id, 5.0)
        assert word_at_time is None
    
    def test_segment_lookup_by_timestamp(self, ts_system, sample_content_id):
        """Test segment lookup by timestamp"""
        # Create sample segments
        segments = [
            SegmentTimestamp(
                id="seg_1",
                start_time=0.0,
                end_time=10.0,
                segment_type="speaker",
                content="First segment",
                speaker_id="Speaker_A"
            ),
            SegmentTimestamp(
                id="seg_2",
                start_time=10.0,
                end_time=20.0,
                segment_type="topic",
                content="Second segment",
                topic="Topic_1"
            )
        ]
        
        # Store them in database
        ts_system._store_segment_timestamps(sample_content_id, segments)
        
        # Test segment lookup
        segment_at_time = ts_system.get_segment_at_timestamp(sample_content_id, 5.0)
        assert segment_at_time is not None
        assert segment_at_time.id == "seg_1"
        assert segment_at_time.speaker_id == "Speaker_A"
        
        segment_at_time = ts_system.get_segment_at_timestamp(sample_content_id, 15.0)
        assert segment_at_time is not None
        assert segment_at_time.id == "seg_2"
        assert segment_at_time.topic == "Topic_1"
    
    def test_timestamp_range_search(self, ts_system, sample_content_id):
        """Test search by timestamp range"""
        # Create and store test data
        word_timestamps = [
            WordTimestamp(word="word1", start_time=5.0, end_time=5.5, confidence=0.9),
            WordTimestamp(word="word2", start_time=15.0, end_time=15.5, confidence=0.9),
            WordTimestamp(word="word3", start_time=25.0, end_time=25.5, confidence=0.9)
        ]
        ts_system._store_word_timestamps(sample_content_id, word_timestamps)
        
        # Create bookmark
        bookmark = ts_system.create_bookmark(
            content_id=sample_content_id,
            timestamp=10.0,
            title="Test Bookmark",
            user_id="test_user"
        )
        
        # Search in range
        results = ts_system.search_by_timestamp(
            content_id=sample_content_id,
            start_time=4.0,
            end_time=16.0
        )
        
        assert isinstance(results, dict)
        assert 'words' in results
        assert 'segments' in results
        assert 'bookmarks' in results
        
        # Should find 2 words in range
        assert len(results['words']) == 2
        
        # Should find 1 bookmark in range
        assert len(results['bookmarks']) == 1
        assert results['bookmarks'][0]['title'] == "Test Bookmark"
    
    def test_export_json_format(self, ts_system, sample_content_id):
        """Test JSON export functionality"""
        # Create test data
        word_timestamps = [
            WordTimestamp(word="test", start_time=0.0, end_time=0.5, confidence=0.9)
        ]
        ts_system._store_word_timestamps(sample_content_id, word_timestamps)
        
        # Export to JSON
        json_export = ts_system.export_timestamps(sample_content_id, "json")
        
        assert isinstance(json_export, str)
        assert len(json_export) > 0
        
        # Parse JSON to verify structure
        export_data = json.loads(json_export)
        assert 'content_id' in export_data
        assert 'words' in export_data
        assert 'segments' in export_data
        assert 'bookmarks' in export_data
        
        assert export_data['content_id'] == sample_content_id
        assert len(export_data['words']) >= 1
    
    def test_export_srt_format(self, ts_system, sample_content_id):
        """Test SRT export functionality"""
        # Create test segments
        segments = [
            SegmentTimestamp(
                id="seg_1",
                start_time=0.0,
                end_time=2.0,
                segment_type="speaker",
                content="First subtitle line"
            ),
            SegmentTimestamp(
                id="seg_2",
                start_time=2.0,
                end_time=4.0,
                segment_type="speaker",
                content="Second subtitle line"
            )
        ]
        ts_system._store_segment_timestamps(sample_content_id, segments)
        
        # Export to SRT
        srt_export = ts_system.export_timestamps(sample_content_id, "srt")
        
        assert isinstance(srt_export, str)
        assert len(srt_export) > 0
        
        # Check SRT format structure
        lines = srt_export.strip().split('\n')
        assert '1' in lines  # First subtitle number
        assert '-->' in srt_export  # Time separator
        assert 'First subtitle line' in srt_export
        assert 'Second subtitle line' in srt_export
    
    def test_export_vtt_format(self, ts_system, sample_content_id):
        """Test WebVTT export functionality"""
        # Create test segments
        segments = [
            SegmentTimestamp(
                id="seg_1",
                start_time=0.0,
                end_time=2.0,
                segment_type="speaker",
                content="VTT subtitle line"
            )
        ]
        ts_system._store_segment_timestamps(sample_content_id, segments)
        
        # Export to VTT
        vtt_export = ts_system.export_timestamps(sample_content_id, "vtt")
        
        assert isinstance(vtt_export, str)
        assert len(vtt_export) > 0
        assert vtt_export.startswith("WEBVTT")
        assert "-->" in vtt_export
        assert "VTT subtitle line" in vtt_export
    
    def test_export_elan_format(self, ts_system, sample_content_id):
        """Test ELAN EAF export functionality"""
        # Create test segments
        segments = [
            SegmentTimestamp(
                id="seg_1",
                start_time=0.0,
                end_time=2.0,
                segment_type="speaker",
                content="ELAN annotation"
            )
        ]
        ts_system._store_segment_timestamps(sample_content_id, segments)
        
        # Export to ELAN
        elan_export = ts_system.export_timestamps(sample_content_id, "elan")
        
        assert isinstance(elan_export, str)
        assert len(elan_export) > 0
        assert "<?xml" in elan_export
        assert "ANNOTATION_DOCUMENT" in elan_export
        assert "ELAN annotation" in elan_export
    
    def test_database_storage_and_retrieval(self, ts_system, sample_content_id):
        """Test database storage and retrieval operations"""
        # Test word timestamp storage
        word_timestamps = [
            WordTimestamp(word="stored", start_time=0.0, end_time=0.5, confidence=0.9),
            WordTimestamp(word="word", start_time=0.5, end_time=1.0, confidence=0.8)
        ]
        
        # Store and verify
        ts_system._store_word_timestamps(sample_content_id, word_timestamps)
        
        # Verify storage by querying database directly
        conn = sqlite3.connect(ts_system.database_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM word_timestamps WHERE content_id = ?",
            (sample_content_id,)
        )
        count = cursor.fetchone()[0]
        assert count == 2
        
        cursor.execute(
            "SELECT word FROM word_timestamps WHERE content_id = ? ORDER BY start_time",
            (sample_content_id,)
        )
        words = [row[0] for row in cursor.fetchall()]
        assert words == ["stored", "word"]
        
        conn.close()
    
    def test_error_handling_invalid_audio_path(self, ts_system, sample_transcript, sample_content_id):
        """Test error handling for invalid audio paths"""
        # Test with non-existent file
        word_timestamps = ts_system.generate_word_timestamps(
            audio_path="non_existent_file.wav",
            transcript=sample_transcript,
            content_id=sample_content_id,
            method="forced_alignment"
        )
        
        # Should still return some result (fallback method)
        assert isinstance(word_timestamps, list)
    
    def test_error_handling_empty_transcript(self, ts_system, sample_audio_path, sample_content_id):
        """Test error handling for empty transcript"""
        word_timestamps = ts_system.generate_word_timestamps(
            audio_path=sample_audio_path,
            transcript="",
            content_id=sample_content_id,
            method="forced_alignment"
        )
        
        # Should return empty list for empty transcript
        assert isinstance(word_timestamps, list)
        assert len(word_timestamps) == 0
    
    def test_error_handling_invalid_export_format(self, ts_system, sample_content_id):
        """Test error handling for invalid export format"""
        with pytest.raises(ValueError):
            ts_system.export_timestamps(sample_content_id, "invalid_format")
    
    def test_confidence_calculation_methods(self, ts_system):
        """Test confidence calculation helper methods"""
        import numpy as np
        
        # Test alignment confidence calculation
        audio = np.random.random(1000)
        confidence = ts_system._calculate_alignment_confidence(audio, 0.0, 0.5, "test")
        
        assert isinstance(confidence, float)
        assert 0 <= confidence <= 1
        
        # Test ML confidence calculation
        features = np.random.random((13, 100))  # MFCC-like features
        ml_confidence = ts_system._calculate_ml_confidence(features, 0.0, 0.5)
        
        assert isinstance(ml_confidence, float)
        assert 0 <= ml_confidence <= 1
    
    def test_speech_segment_merging(self, ts_system):
        """Test speech segment merging functionality"""
        # Test segments with small gaps
        segments = [(0.0, 1.0), (1.05, 2.0), (2.1, 3.0)]
        merged = ts_system._merge_speech_segments(segments, gap_threshold=0.1)
        
        # Should merge all segments due to small gaps
        assert len(merged) == 1
        assert merged[0] == (0.0, 3.0)
        
        # Test segments with large gaps
        segments = [(0.0, 1.0), (2.0, 3.0), (5.0, 6.0)]
        merged = ts_system._merge_speech_segments(segments, gap_threshold=0.1)
        
        # Should not merge due to large gaps
        assert len(merged) == 3
    
    def test_word_boundary_detection(self, ts_system):
        """Test word boundary detection from features"""
        import numpy as np
        
        # Create mock features
        features = np.random.random((13, 100))
        num_words = 5
        
        boundaries = ts_system._detect_word_boundaries(features, num_words)
        
        assert isinstance(boundaries, list)
        assert len(boundaries) <= num_words
        
        # Boundaries should be in ascending order
        assert boundaries == sorted(boundaries)
    
    def test_sentence_splitting(self, ts_system):
        """Test sentence splitting functionality"""
        text = "First sentence. Second sentence! Third sentence? Fourth sentence."
        sentences = ts_system._split_into_sentences(text)
        
        assert isinstance(sentences, list)
        assert len(sentences) == 4
        assert "First sentence" in sentences[0]
        assert "Second sentence" in sentences[1]
    
    def test_time_formatting_methods(self, ts_system):
        """Test time formatting helper methods"""
        # Test SRT time formatting
        srt_time = ts_system._format_srt_time(125.750)
        assert srt_time == "00:02:05,750"
        
        # Test VTT time formatting
        vtt_time = ts_system._format_vtt_time(125.750)
        assert vtt_time == "00:02:05.750"
    
    def test_transcript_segment_word_lookup(self):
        """Test word lookup within transcript segments"""
        # Create sample words
        words = [
            WordTimestamp(word="hello", start_time=0.0, end_time=0.5, confidence=0.9),
            WordTimestamp(word="world", start_time=0.5, end_time=1.0, confidence=0.9)
        ]
        
        # Create transcript segment
        segment = TranscriptSegment(
            text="hello world",
            start_time=0.0,
            end_time=1.0,
            words=words
        )
        
        # Test word lookup
        word_at_time = segment.get_word_at_time(0.25)
        assert word_at_time is not None
        assert word_at_time.word == "hello"
        
        word_at_time = segment.get_word_at_time(0.75)
        assert word_at_time is not None
        assert word_at_time.word == "world"
        
        # Test time outside range
        word_at_time = segment.get_word_at_time(1.5)
        assert word_at_time is None


class TestTimestampingSystemIntegration:
    """Integration tests for the complete timestamping workflow"""
    
    @pytest.fixture
    def ts_system(self):
        """Create TimestampingSystem instance for integration tests"""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "integration_test.db")
        system = TimestampingSystem(database_path=db_path)
        yield system
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_complete_workflow(self, ts_system):
        """Test complete timestamping workflow from start to finish"""
        content_id = "integration_test_001"
        transcript = "This is a complete workflow test. We will test all components together."
        audio_path = "test_audio.wav"
        
        # Step 1: Generate word timestamps
        word_timestamps = ts_system.generate_word_timestamps(
            audio_path=audio_path,
            transcript=transcript,
            content_id=content_id,
            method="forced_alignment"
        )
        
        assert len(word_timestamps) > 0
        
        # Step 2: Generate segment timestamps
        segments = ts_system.generate_segment_timestamps(
            audio_path=audio_path,
            transcript=transcript,
            content_id=content_id
        )
        
        assert len(segments) > 0
        
        # Step 3: Create bookmarks
        bookmark1 = ts_system.create_bookmark(
            content_id=content_id,
            timestamp=5.0,
            title="First Bookmark",
            description="Test bookmark 1",
            user_id="test_user"
        )
        
        bookmark2 = ts_system.create_bookmark(
            content_id=content_id,
            timestamp=10.0,
            title="Second Bookmark",
            description="Test bookmark 2",
            user_id="test_user"
        )
        
        # Step 4: Create time codes
        time_codes = ts_system.create_time_codes(
            content_id=content_id,
            segments=segments,
            bookmarks=[bookmark1, bookmark2]
        )
        
        assert len(time_codes) >= 2  # At least the bookmarks
        
        # Step 5: Create clickable transcript
        transcript_segments = ts_system.create_clickable_transcript(
            content_id=content_id,
            transcript=transcript,
            word_timestamps=word_timestamps
        )
        
        assert len(transcript_segments) > 0
        
        # Step 6: Test search functionality
        search_results = ts_system.search_by_timestamp(
            content_id=content_id,
            start_time=0.0,
            end_time=15.0
        )
        
        assert len(search_results['words']) > 0
        assert len(search_results['bookmarks']) == 2
        
        # Step 7: Test export functionality
        json_export = ts_system.export_timestamps(content_id, "json")
        assert len(json_export) > 0
        
        srt_export = ts_system.export_timestamps(content_id, "srt")
        assert len(srt_export) > 0
        
        # Step 8: Verify data persistence
        retrieved_bookmarks = ts_system.get_bookmarks(content_id, "test_user")
        assert len(retrieved_bookmarks) == 2
        
        word_at_time = ts_system.get_word_at_timestamp(content_id, 1.0)
        assert word_at_time is not None
    
    def test_multi_user_bookmark_isolation(self, ts_system):
        """Test that bookmarks are properly isolated between users"""
        content_id = "multi_user_test"
        
        # Create bookmarks for different users
        bookmark_user1 = ts_system.create_bookmark(
            content_id=content_id,
            timestamp=5.0,
            title="User 1 Bookmark",
            user_id="user_1"
        )
        
        bookmark_user2 = ts_system.create_bookmark(
            content_id=content_id,
            timestamp=10.0,
            title="User 2 Bookmark",
            user_id="user_2"
        )
        
        # Verify isolation
        user1_bookmarks = ts_system.get_bookmarks(content_id, "user_1")
        user2_bookmarks = ts_system.get_bookmarks(content_id, "user_2")
        
        assert len(user1_bookmarks) == 1
        assert len(user2_bookmarks) == 1
        assert user1_bookmarks[0].title == "User 1 Bookmark"
        assert user2_bookmarks[0].title == "User 2 Bookmark"
        
        # Test getting all bookmarks (no user filter)
        all_bookmarks = ts_system.get_bookmarks(content_id)
        assert len(all_bookmarks) == 2
    
    def test_performance_with_large_dataset(self, ts_system):
        """Test system performance with large amounts of data"""
        content_id = "performance_test"
        
        # Generate large number of word timestamps
        large_word_list = ["word"] * 1000  # 1000 words
        word_timestamps = []
        
        for i, word in enumerate(large_word_list):
            word_timestamps.append(WordTimestamp(
                word=f"{word}_{i}",
                start_time=i * 0.1,
                end_time=(i + 1) * 0.1,
                confidence=0.9
            ))
        
        # Store large dataset
        start_time = time.time()
        ts_system._store_word_timestamps(content_id, word_timestamps)
        storage_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert storage_time < 5.0  # 5 seconds threshold
        
        # Test retrieval performance
        start_time = time.time()
        word_at_time = ts_system.get_word_at_timestamp(content_id, 50.0)
        retrieval_time = time.time() - start_time
        
        assert retrieval_time < 1.0  # 1 second threshold
        assert word_at_time is not None
        
        # Test range search performance
        start_time = time.time()
        search_results = ts_system.search_by_timestamp(content_id, 10.0, 20.0)
        search_time = time.time() - start_time
        
        assert search_time < 2.0  # 2 seconds threshold
        assert len(search_results['words']) > 0


def run_tests():
    """Run all tests with pytest"""
    import sys
    
    print("🧪 Running Comprehensive Timestamping System Tests")
    print("=" * 60)
    
    # Run pytest with verbose output
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "--color=yes"
    ])
    
    if exit_code == 0:
        print("\n✅ All tests passed successfully!")
    else:
        print(f"\n❌ Some tests failed (exit code: {exit_code})")
    
    return exit_code


if __name__ == "__main__":
    import time
    run_tests()