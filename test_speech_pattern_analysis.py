"""
Comprehensive Tests for Speech Pattern Analysis System

Tests for:
- Speech rate analysis and speaking pattern detection
- Pause detection and silence analysis
- Filler word detection and removal
- Speaking confidence and hesitation analysis
- Speech coaching suggestions based on patterns

Requirements: 3.1, 5.1
"""

import pytest
import numpy as np
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import json

# Import the modules to test
from speech_pattern_analysis import (
    SpeechPatternAnalysisSystem,
    SpeechSegment,
    AudioFeatureExtractor,
    SpeechRateAnalyzer,
    PauseDetector,
    FillerWordDetector,
    ConfidenceAnalyzer,
    SpeechCoach,
    ComprehensiveSpeechAnalysis,
    create_sample_segments,
    format_analysis_report
)

class TestSpeechSegment:
    """Test SpeechSegment data class"""
    
    def test_speech_segment_creation(self):
        """Test creating a speech segment"""
        segment = SpeechSegment(
            start_time=0.0,
            end_time=5.0,
            text="Hello world",
            speaker_id="speaker1",
            confidence=0.95
        )
        
        assert segment.start_time == 0.0
        assert segment.end_time == 5.0
        assert segment.text == "Hello world"
        assert segment.speaker_id == "speaker1"
        assert segment.confidence == 0.95
        assert segment.duration == 5.0
    
    def test_speech_segment_duration_property(self):
        """Test duration property calculation"""
        segment = SpeechSegment(2.5, 7.3, "Test text")
        assert segment.duration == 4.8

class TestAudioFeatureExtractor:
    """Test AudioFeatureExtractor class"""
    
    def setUp(self):
        self.extractor = AudioFeatureExtractor()
    
    @patch('librosa.load')
    @patch('librosa.feature.mfcc')
    @patch('librosa.feature.spectral_centroid')
    @patch('librosa.feature.rms')
    @patch('librosa.yin')
    @patch('librosa.beat.beat_track')
    def test_extract_features_success(self, mock_beat_track, mock_yin, mock_rms, 
                                    mock_spectral_centroid, mock_mfcc, mock_load):
        """Test successful feature extraction"""
        # Setup mocks
        mock_audio = np.random.randn(16000)  # 1 second of audio
        mock_load.return_value = (mock_audio, 16000)
        mock_mfcc.return_value = np.random.randn(13, 32)
        mock_spectral_centroid.return_value = np.array([np.random.randn(32)])
        mock_rms.return_value = np.array([np.random.randn(32)])
        mock_yin.return_value = np.random.uniform(80, 300, 32)
        mock_beat_track.return_value = (120.0, np.array([0.0, 0.5]))
        
        extractor = AudioFeatureExtractor()
        features = extractor.extract_features("test_audio.wav")
        
        assert 'audio' in features
        assert 'sample_rate' in features
        assert 'duration' in features
        assert 'mfcc' in features
        assert 'spectral_centroid' in features
        assert 'rms_energy' in features
        assert 'pitch' in features
        assert 'tempo' in features
        
        assert features['sample_rate'] == 16000
        assert features['duration'] == 1.0
    
    @patch('librosa.load')
    def test_extract_features_failure(self, mock_load):
        """Test feature extraction failure handling"""
        mock_load.side_effect = Exception("Audio loading failed")
        
        extractor = AudioFeatureExtractor()
        features = extractor.extract_features("nonexistent.wav")
        
        assert features == {}

class TestSpeechRateAnalyzer:
    """Test SpeechRateAnalyzer class"""
    
    def setUp(self):
        self.analyzer = SpeechRateAnalyzer()
    
    def test_count_syllables(self):
        """Test syllable counting"""
        analyzer = SpeechRateAnalyzer()
        
        assert analyzer.count_syllables("hello") == 2
        assert analyzer.count_syllables("world") == 1
        assert analyzer.count_syllables("beautiful") == 3
        assert analyzer.count_syllables("communication") == 5
        assert analyzer.count_syllables("") == 1  # Minimum 1 syllable
    
    def test_analyze_speech_rate(self):
        """Test speech rate analysis"""
        segments = [
            SpeechSegment(0.0, 2.0, "Hello world this is a test", confidence=0.9),
            SpeechSegment(2.0, 4.0, "Another sentence here", confidence=0.8),
            SpeechSegment(4.0, 6.0, "Final words", confidence=0.95)
        ]
        
        audio_features = {
            'duration': 6.0,
            'audio': np.random.randn(96000),  # 6 seconds at 16kHz
            'sample_rate': 16000
        }
        
        analyzer = SpeechRateAnalyzer()
        result = analyzer.analyze_speech_rate(segments, audio_features)
        
        assert result.words_per_minute > 0
        assert result.syllables_per_minute > 0
        assert result.characters_per_minute > 0
        assert result.speaking_time == 6.0
        assert result.total_time == 6.0
        assert result.speech_rate_variability >= 0
        assert isinstance(result.tempo_changes, list)
    
    def test_analyze_speech_rate_empty_segments(self):
        """Test speech rate analysis with empty segments"""
        segments = []
        audio_features = {'duration': 5.0}
        
        analyzer = SpeechRateAnalyzer()
        result = analyzer.analyze_speech_rate(segments, audio_features)
        
        assert result.words_per_minute == 0
        assert result.syllables_per_minute == 0
        assert result.characters_per_minute == 0

class TestPauseDetector:
    """Test PauseDetector class"""
    
    def test_detect_pauses(self):
        """Test pause detection"""
        # Create mock audio features with clear silence regions
        duration = 10.0
        n_frames = 200  # 10 seconds worth of frames
        
        # Create RMS energy with silence regions
        rms_energy = np.ones(n_frames) * 0.05  # Above threshold
        rms_energy[40:60] = 0.005  # Silence region 1
        rms_energy[120:140] = 0.005  # Silence region 2
        
        audio_features = {
            'audio': np.random.randn(160000),  # 10 seconds at 16kHz
            'sample_rate': 16000,
            'duration': duration,
            'rms_energy': rms_energy
        }
        
        segments = [
            SpeechSegment(0.0, 2.0, "First segment"),
            SpeechSegment(6.0, 8.0, "Second segment")
        ]
        
        detector = PauseDetector(min_pause_duration=0.3)
        result = detector.detect_pauses(audio_features, segments)
        
        assert result.total_pause_time >= 0
        assert result.pause_count >= 0
        assert result.pause_frequency >= 0
        assert isinstance(result.pause_locations, list)
    
    def test_detect_pauses_no_audio(self):
        """Test pause detection with no audio data"""
        audio_features = {}
        segments = []
        
        detector = PauseDetector()
        result = detector.detect_pauses(audio_features, segments)
        
        assert result.total_pause_time == 0
        assert result.pause_count == 0
        assert result.average_pause_duration == 0
        assert result.longest_pause == 0
        assert result.pause_locations == []
        assert result.pause_frequency == 0

class TestFillerWordDetector:
    """Test FillerWordDetector class"""
    
    def test_detect_filler_words(self):
        """Test filler word detection"""
        segments = [
            SpeechSegment(0.0, 3.0, "Um, hello everyone. I, uh, want to talk about this."),
            SpeechSegment(3.0, 6.0, "Like, you know, it's really important to, er, focus."),
            SpeechSegment(6.0, 9.0, "So, basically, we need to improve our communication.")
        ]
        
        detector = FillerWordDetector()
        result = detector.detect_filler_words(segments)
        
        # Check that hesitation markers are detected (even if not counted as filler words)
        assert len(result.hesitation_markers) > 0
        assert result.filler_percentage >= 0
        assert isinstance(result.repetitions, list)
        assert isinstance(result.false_starts, list)
        
        # Check that some common fillers are detected in hesitation markers
        hesitation_texts = [marker[1] for marker in result.hesitation_markers]
        assert any('um' in text.lower() for text in hesitation_texts)
    
    def test_detect_filler_words_clean_speech(self):
        """Test filler word detection with clean speech"""
        segments = [
            SpeechSegment(0.0, 3.0, "Good morning everyone. Today we will discuss important topics."),
            SpeechSegment(3.0, 6.0, "Clear communication is essential for business success.")
        ]
        
        detector = FillerWordDetector()
        result = detector.detect_filler_words(segments)
        
        assert result.total_filler_count == 0
        assert result.filler_percentage == 0.0
        assert len(result.filler_words) == 0
        assert len(result.hesitation_markers) == 0
    
    def test_detect_repetitions(self):
        """Test repetition detection"""
        segments = [
            SpeechSegment(0.0, 3.0, "I think think we should go go there.")
        ]
        
        detector = FillerWordDetector()
        result = detector.detect_filler_words(segments)
        
        assert len(result.repetitions) > 0

class TestConfidenceAnalyzer:
    """Test ConfidenceAnalyzer class"""
    
    def test_analyze_confidence(self):
        """Test confidence analysis"""
        segments = [
            SpeechSegment(0.0, 2.0, "Hello world", confidence=0.9),
            SpeechSegment(2.0, 4.0, "This is a test", confidence=0.8),
            SpeechSegment(4.0, 6.0, "Final segment", confidence=0.95)
        ]
        
        audio_features = {
            'rms_energy': np.random.uniform(0.02, 0.08, 100),
            'pitch': np.random.uniform(100, 200, 100),
            'duration': 6.0
        }
        
        # Mock filler and pause analysis
        from speech_pattern_analysis import FillerWordAnalysis, PauseAnalysis
        filler_analysis = FillerWordAnalysis({}, 0, 0, [], [], [])
        pause_analysis = PauseAnalysis(1.0, 3, 0.33, 0.5, [], 30)
        
        analyzer = ConfidenceAnalyzer()
        result = analyzer.analyze_confidence(segments, audio_features, filler_analysis, pause_analysis)
        
        assert 0 <= result.overall_confidence_score <= 1
        assert result.hesitation_frequency >= 0
        assert 0 <= result.voice_stability <= 1
        assert 0 <= result.pace_consistency <= 1
        assert 0 <= result.volume_consistency <= 1
        assert isinstance(result.confidence_timeline, list)
    
    def test_confidence_with_high_hesitation(self):
        """Test confidence analysis with high hesitation"""
        segments = [SpeechSegment(0.0, 5.0, "Um, uh, like, you know")]
        audio_features = {'rms_energy': np.array([0.05]), 'pitch': np.array([150]), 'duration': 5.0}
        
        from speech_pattern_analysis import FillerWordAnalysis, PauseAnalysis
        filler_analysis = FillerWordAnalysis({'um': 5, 'uh': 3}, 8, 25.0, [(1, 'um'), (2, 'uh')], [], [])
        pause_analysis = PauseAnalysis(0.5, 2, 0.25, 0.5, [], 24)
        
        analyzer = ConfidenceAnalyzer()
        result = analyzer.analyze_confidence(segments, audio_features, filler_analysis, pause_analysis)
        
        # High hesitation should result in lower confidence
        assert result.overall_confidence_score < 0.7
        assert result.hesitation_frequency > 0

class TestSpeechCoach:
    """Test SpeechCoach class"""
    
    def test_generate_suggestions_good_speech(self):
        """Test coaching suggestions for good speech"""
        # Create mock analysis for good speech
        from speech_pattern_analysis import (
            SpeechRateAnalysis, PauseAnalysis, FillerWordAnalysis, 
            ConfidenceAnalysis, ComprehensiveSpeechAnalysis
        )
        
        analysis = ComprehensiveSpeechAnalysis(
            speech_rate=SpeechRateAnalysis(160, 240, 800, 10, 12, 15, []),
            pause_analysis=PauseAnalysis(2.0, 8, 0.25, 0.5, [], 12),
            filler_analysis=FillerWordAnalysis({'um': 1}, 1, 2.0, [], [], []),
            confidence_analysis=ConfidenceAnalysis(0.85, 0.1, 0.9, 0.8, 0.85, []),
            coaching_suggestions=None,  # Will be generated
            analysis_timestamp=datetime.now(),
            audio_duration=12.0
        )
        
        coach = SpeechCoach()
        suggestions = coach.generate_suggestions(analysis)
        
        assert suggestions.overall_rating in ["Excellent", "Good", "Fair", "Needs Improvement"]
        assert isinstance(suggestions.pace_suggestions, list)
        assert isinstance(suggestions.pause_suggestions, list)
        assert isinstance(suggestions.filler_reduction_tips, list)
        assert isinstance(suggestions.confidence_building_tips, list)
        assert isinstance(suggestions.priority_areas, list)
    
    def test_generate_suggestions_poor_speech(self):
        """Test coaching suggestions for poor speech"""
        from speech_pattern_analysis import (
            SpeechRateAnalysis, PauseAnalysis, FillerWordAnalysis, 
            ConfidenceAnalysis, ComprehensiveSpeechAnalysis
        )
        
        analysis = ComprehensiveSpeechAnalysis(
            speech_rate=SpeechRateAnalysis(80, 120, 400, 10, 12, 50, []),  # Too slow
            pause_analysis=PauseAnalysis(5.0, 20, 0.25, 2.0, [], 40),  # Too many pauses
            filler_analysis=FillerWordAnalysis({'um': 10, 'uh': 8}, 18, 15.0, [], [], []),  # Many fillers
            confidence_analysis=ConfidenceAnalysis(0.3, 1.2, 0.4, 0.3, 0.4, []),  # Low confidence
            coaching_suggestions=None,
            analysis_timestamp=datetime.now(),
            audio_duration=12.0
        )
        
        coach = SpeechCoach()
        suggestions = coach.generate_suggestions(analysis)
        
        assert suggestions.overall_rating in ["Fair", "Needs Improvement"]
        assert len(suggestions.priority_areas) > 0
        assert len(suggestions.pace_suggestions) > 0
        assert len(suggestions.filler_reduction_tips) > 0

class TestSpeechPatternAnalysisSystem:
    """Test main SpeechPatternAnalysisSystem class"""
    
    @patch('sqlite3.connect')
    def test_init_database(self, mock_connect):
        """Test database initialization"""
        mock_conn = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        system = SpeechPatternAnalysisSystem(":memory:")
        
        mock_conn.execute.assert_called()
        mock_conn.commit.assert_called()
    
    @patch.object(AudioFeatureExtractor, 'extract_features')
    def test_analyze_speech_patterns(self, mock_extract_features):
        """Test complete speech pattern analysis"""
        mock_features = {
            'audio': np.random.randn(16000),
            'sample_rate': 16000,
            'duration': 1.0,
            'rms_energy': np.random.uniform(0.02, 0.08, 32),
            'pitch': np.random.uniform(100, 200, 32)
        }
        mock_extract_features.return_value = mock_features
        
        # Create test segments
        segments = [
            SpeechSegment(0.0, 1.0, "Hello world test", confidence=0.9)
        ]
        
        system = SpeechPatternAnalysisSystem(":memory:")
        result = system.analyze_speech_patterns("test.wav", segments)
        
        assert isinstance(result, ComprehensiveSpeechAnalysis)
        assert result.speech_rate is not None
        assert result.pause_analysis is not None
        assert result.filler_analysis is not None
        assert result.confidence_analysis is not None
        assert result.coaching_suggestions is not None
        assert result.analysis_timestamp is not None
        assert result.audio_duration > 0
    
    @patch.object(AudioFeatureExtractor, 'extract_features')
    def test_analyze_speech_patterns_failure(self, mock_extract_features):
        """Test analysis failure handling"""
        mock_extract_features.return_value = {}  # Empty features = failure
        
        segments = [SpeechSegment(0.0, 1.0, "Test")]
        system = SpeechPatternAnalysisSystem(":memory:")
        
        with pytest.raises(ValueError, match="Failed to extract audio features"):
            system.analyze_speech_patterns("test.wav", segments)
    
    @patch('sqlite3.connect')
    def test_get_analysis_history(self, mock_connect):
        """Test retrieving analysis history"""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_cursor
        
        # Mock database results
        mock_cursor.fetchall.return_value = [
            ("test1.wav", '{"test": "data1"}', "2023-01-01 10:00:00"),
            ("test2.wav", '{"test": "data2"}', "2023-01-01 11:00:00")
        ]
        
        system = SpeechPatternAnalysisSystem(":memory:")
        history = system.get_analysis_history(5)
        
        assert len(history) == 2
        assert history[0]['audio_path'] == "test1.wav"
        assert history[0]['analysis_data'] == {"test": "data1"}
        assert history[1]['audio_path'] == "test2.wav"

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_sample_segments(self):
        """Test creating sample segments"""
        text = "Hello world. This is a test. Final sentence."
        duration = 9.0
        
        segments = create_sample_segments(text, duration)
        
        assert len(segments) == 3  # 3 sentences
        assert segments[0].text == "Hello world"
        assert segments[1].text == "This is a test"
        assert segments[2].text == "Final sentence"
        
        # Check timing (duration is divided equally among segments)
        expected_duration_per_segment = duration / 3
        assert segments[0].start_time == 0.0
        assert segments[0].end_time == expected_duration_per_segment
        assert segments[1].start_time == expected_duration_per_segment
        assert segments[1].end_time == 2 * expected_duration_per_segment
        assert segments[2].start_time == 2 * expected_duration_per_segment
        assert segments[2].end_time == duration
    
    def test_format_analysis_report(self):
        """Test formatting analysis report"""
        from speech_pattern_analysis import (
            SpeechRateAnalysis, PauseAnalysis, FillerWordAnalysis, 
            ConfidenceAnalysis, SpeechCoachingSuggestions, ComprehensiveSpeechAnalysis
        )
        
        analysis = ComprehensiveSpeechAnalysis(
            speech_rate=SpeechRateAnalysis(160, 240, 800, 10, 12, 15, []),
            pause_analysis=PauseAnalysis(2.0, 8, 0.25, 0.5, [], 12),
            filler_analysis=FillerWordAnalysis({'um': 2, 'uh': 1}, 3, 5.0, [], [], []),
            confidence_analysis=ConfidenceAnalysis(0.75, 0.2, 0.8, 0.7, 0.8, []),
            coaching_suggestions=SpeechCoachingSuggestions(
                ["Good pace"], ["Nice pauses"], ["Reduce fillers"], ["Keep confidence"], "Good", ["Fillers"]
            ),
            analysis_timestamp=datetime.now(),
            audio_duration=12.0
        )
        
        report = format_analysis_report(analysis)
        
        assert "SPEECH PATTERN ANALYSIS REPORT" in report
        assert "SPEECH RATE ANALYSIS:" in report
        assert "PAUSE ANALYSIS:" in report
        assert "FILLER WORD ANALYSIS:" in report
        assert "CONFIDENCE ANALYSIS:" in report
        assert "COACHING SUGGESTIONS:" in report
        assert "160.0" in report  # WPM
        assert "5.0%" in report  # Filler percentage

class TestIntegration:
    """Integration tests for the complete system"""
    
    def test_end_to_end_analysis(self):
        """Test complete end-to-end analysis workflow"""
        # Create realistic test data
        text = """
        Good morning everyone. Um, today I want to discuss, uh, the importance of 
        effective communication. You know, it's really crucial for, like, business success.
        So, let's dive into the key points.
        """
        
        segments = create_sample_segments(text.strip(), 15.0)
        
        # Mock the audio file processing
        with patch.object(AudioFeatureExtractor, 'extract_features') as mock_extract:
            mock_extract.return_value = {
                'audio': np.random.randn(240000),  # 15 seconds at 16kHz
                'sample_rate': 16000,
                'duration': 15.0,
                'rms_energy': np.random.uniform(0.01, 0.1, 300),
                'pitch': np.random.uniform(80, 300, 300),
                'mfcc': np.random.randn(13, 300),
                'spectral_centroid': np.random.uniform(1000, 3000, 300),
                'volume_envelope': np.random.uniform(0, 0.1, 240000)
            }
            
            system = SpeechPatternAnalysisSystem(":memory:")
            analysis = system.analyze_speech_patterns("test.wav", segments)
            
            # Verify all components are present and reasonable
            assert analysis.speech_rate.words_per_minute > 0
            assert len(analysis.filler_analysis.hesitation_markers) > 0  # Should detect hesitation markers
            assert analysis.confidence_analysis.overall_confidence_score > 0
            assert analysis.coaching_suggestions.overall_rating in ["Excellent", "Good", "Fair", "Needs Improvement"]
            
            # Check that hesitation markers contain expected fillers
            hesitation_texts = [marker[1] for marker in analysis.filler_analysis.hesitation_markers]
            assert any('um' in text.lower() for text in hesitation_texts)
            
            # Generate and verify report
            report = format_analysis_report(analysis)
            assert len(report) > 100  # Should be substantial

def test_error_handling():
    """Test error handling throughout the system"""
    system = SpeechPatternAnalysisSystem(":memory:")
    
    # Test with invalid audio path
    with patch.object(AudioFeatureExtractor, 'extract_features', return_value={}):
        with pytest.raises(ValueError):
            system.analyze_speech_patterns("nonexistent.wav", [])
    
    # Test with empty segments
    with patch.object(AudioFeatureExtractor, 'extract_features') as mock_extract:
        mock_extract.return_value = {
            'audio': np.array([]),
            'sample_rate': 16000,
            'duration': 0.0,
            'rms_energy': np.array([]),
            'pitch': np.array([])
        }
        
        # Should handle gracefully
        analysis = system.analyze_speech_patterns("test.wav", [])
        assert analysis.speech_rate.words_per_minute == 0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])