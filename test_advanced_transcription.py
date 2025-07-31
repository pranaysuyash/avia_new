#!/usr/bin/env python3
"""
Test Advanced Transcription Features
Basic tests for the advanced transcription functionality
"""

import pytest
import os
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock

# Import modules to test
from advanced_transcription import (
    AdvancedTranscriber, TranscriptEditor, AdvancedTranscriptionResult,
    SpeakerSegment, TimestampedWord, transcribe_advanced, detect_audio_language,
    get_supported_languages, edit_transcript, export_transcript
)

class TestAdvancedTranscriber:
    """Test the AdvancedTranscriber class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.transcriber = AdvancedTranscriber()
        
        # Create a temporary audio file for testing
        self.temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.temp_audio.write(b'fake audio data')  # Placeholder data
        self.temp_audio.close()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_audio.name):
            os.unlink(self.temp_audio.name)
    
    def test_supported_languages(self):
        """Test that supported languages are properly loaded"""
        languages = self.transcriber.get_supported_languages()
        
        assert isinstance(languages, dict)
        assert len(languages) > 0
        assert 'en' in languages
        assert languages['en'] == 'English'
        assert 'es' in languages
        assert languages['es'] == 'Spanish'
    
    @patch('advanced_transcription.whisper.load_model')
    @patch('advanced_transcription.whisper.load_audio')
    @patch('advanced_transcription.whisper.pad_or_trim')
    @patch('advanced_transcription.whisper.log_mel_spectrogram')
    def test_detect_language(self, mock_mel, mock_pad, mock_load_audio, mock_load_model):
        """Test language detection functionality"""
        # Mock the Whisper model and its methods
        mock_model = Mock()
        mock_model.device = 'cpu'
        mock_model.detect_language.return_value = (None, {
            'en': 0.8,
            'es': 0.15,
            'fr': 0.05
        })
        mock_load_model.return_value = mock_model
        
        # Mock audio processing
        mock_load_audio.return_value = Mock()
        mock_pad.return_value = Mock()
        mock_mel.return_value = Mock()
        mock_mel.return_value.to.return_value = Mock()
        
        # Test language detection
        languages = self.transcriber.detect_language(self.temp_audio.name)
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert languages[0]['code'] == 'en'
        assert languages[0]['name'] == 'English'
        assert languages[0]['confidence'] == 0.8
    
    @patch('advanced_transcription.WhisperTranscriber._load_local_model')
    def test_transcribe_with_speaker_diarization(self, mock_load_model):
        """Test transcription with speaker diarization"""
        # Mock the Whisper model and transcription result
        mock_model = Mock()
        mock_transcribe_result = {
            'text': 'Hello, this is a test transcription with multiple speakers.',
            'language': 'en',
            'segments': [
                {
                    'text': 'Hello, this is a test.',
                    'start': 0.0,
                    'end': 2.0,
                    'avg_logprob': -0.2,
                    'words': [
                        {'word': 'Hello', 'start': 0.0, 'end': 0.5, 'probability': 0.9},
                        {'word': 'this', 'start': 0.6, 'end': 0.8, 'probability': 0.8}
                    ]
                },
                {
                    'text': 'This is another speaker.',
                    'start': 3.0,
                    'end': 5.0,
                    'avg_logprob': -0.3,
                    'words': [
                        {'word': 'This', 'start': 3.0, 'end': 3.2, 'probability': 0.85},
                        {'word': 'is', 'start': 3.3, 'end': 3.4, 'probability': 0.9}
                    ]
                }
            ]
        }
        
        mock_model.transcribe.return_value = mock_transcribe_result
        mock_load_model.return_value = mock_model
        
        # Test transcription with speaker diarization
        result = self.transcriber.transcribe_with_speaker_diarization(
            self.temp_audio.name, language='en', use_api=False
        )
        
        assert isinstance(result, AdvancedTranscriptionResult)
        assert result.text == mock_transcribe_result['text']
        assert result.language == 'en'
        assert len(result.speakers) > 0
        assert len(result.timestamped_words) > 0
        
        # Check speaker segments
        for speaker in result.speakers:
            assert isinstance(speaker, SpeakerSegment)
            assert speaker.speaker_id.startswith('Speaker_')
            assert speaker.start_time >= 0
            assert speaker.end_time > speaker.start_time
            assert len(speaker.text) > 0
        
        # Check timestamped words
        for word in result.timestamped_words:
            assert isinstance(word, TimestampedWord)
            assert len(word.word) > 0
            assert word.start_time >= 0
            assert word.end_time > word.start_time

class TestTranscriptEditor:
    """Test the TranscriptEditor class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.editor = TranscriptEditor()
        
        # Create sample advanced transcription result
        self.sample_speakers = [
            SpeakerSegment(
                speaker_id="Speaker_1",
                start_time=0.0,
                end_time=2.0,
                text="Hello, how are you?",
                confidence=0.9
            ),
            SpeakerSegment(
                speaker_id="Speaker_2",
                start_time=2.5,
                end_time=4.0,
                text="I'm doing well, thank you.",
                confidence=0.85
            )
        ]
        
        self.sample_words = [
            TimestampedWord("Hello", 0.0, 0.5, 0.9, "Speaker_1"),
            TimestampedWord("how", 0.6, 0.8, 0.85, "Speaker_1"),
            TimestampedWord("are", 0.9, 1.1, 0.9, "Speaker_1"),
            TimestampedWord("you", 1.2, 1.4, 0.8, "Speaker_1")
        ]
        
        self.sample_result = AdvancedTranscriptionResult(
            text="Hello, how are you? I'm doing well, thank you.",
            language="en",
            confidence=0.875,
            processing_time=2.5,
            model_used="whisper-local-base-diarized",
            speakers=self.sample_speakers,
            timestamped_words=self.sample_words,
            detected_languages=[{'code': 'en', 'name': 'English', 'confidence': 0.9}]
        )
    
    def test_edit_transcript_text_replace(self):
        """Test text replacement editing"""
        edits = [
            {
                'type': 'text_replace',
                'old_text': 'Hello, how are you?',
                'new_text': 'Hi, how are you doing?'
            }
        ]
        
        edited_result = self.editor.edit_transcript(self.sample_result, edits)
        
        assert isinstance(edited_result, AdvancedTranscriptionResult)
        assert 'Hi, how are you doing?' in edited_result.text
        assert 'Hello, how are you?' not in edited_result.text
        assert edited_result.model_used.endswith('_edited')
    
    def test_edit_transcript_speaker_rename(self):
        """Test speaker renaming"""
        edits = [
            {
                'type': 'speaker_rename',
                'old_speaker': 'Speaker_1',
                'new_speaker': 'Alice'
            }
        ]
        
        edited_result = self.editor.edit_transcript(self.sample_result, edits)
        
        # Check that speaker was renamed in segments
        alice_segments = [s for s in edited_result.speakers if s.speaker_id == 'Alice']
        assert len(alice_segments) > 0
        
        # Check that speaker was renamed in words
        alice_words = [w for w in edited_result.timestamped_words if w.speaker_id == 'Alice']
        assert len(alice_words) > 0
    
    def test_export_transcript_txt(self):
        """Test TXT export format"""
        exported = self.editor.export_transcript(
            self.sample_result, 'txt', include_speakers=True, include_timestamps=True
        )
        
        assert isinstance(exported, str)
        assert 'Speaker_1:' in exported
        assert 'Speaker_2:' in exported
        assert '00:00' in exported  # Timestamp format
        assert 'Hello, how are you?' in exported
    
    def test_export_transcript_json(self):
        """Test JSON export format"""
        exported = self.editor.export_transcript(
            self.sample_result, 'json'
        )
        
        assert isinstance(exported, str)
        
        # Parse JSON to verify structure
        data = json.loads(exported)
        assert 'text' in data
        assert 'speakers' in data
        assert 'timestamped_words' in data
        assert 'language' in data
        assert data['language'] == 'en'
    
    def test_export_transcript_srt(self):
        """Test SRT subtitle export format"""
        exported = self.editor.export_transcript(
            self.sample_result, 'srt', include_speakers=True
        )
        
        assert isinstance(exported, str)
        assert '1\n' in exported  # SRT numbering
        assert '-->' in exported  # SRT timestamp separator
        assert 'Speaker_1:' in exported
        assert '00:00:00,000' in exported  # SRT timestamp format
    
    def test_export_transcript_vtt(self):
        """Test WebVTT export format"""
        exported = self.editor.export_transcript(
            self.sample_result, 'vtt', include_speakers=True
        )
        
        assert isinstance(exported, str)
        assert exported.startswith('WEBVTT')
        assert '-->' in exported
        assert '<v Speaker_1>' in exported  # VTT speaker format
    
    def test_export_transcript_csv(self):
        """Test CSV export format"""
        exported = self.editor.export_transcript(
            self.sample_result, 'csv', include_speakers=True, include_timestamps=True
        )
        
        assert isinstance(exported, str)
        lines = exported.strip().split('\n')
        assert len(lines) > 1  # Header + data rows
        
        # Check header
        header = lines[0]
        assert 'Speaker' in header
        assert 'Text' in header
        assert 'Start_Time' in header
        assert 'End_Time' in header

class TestPublicAPI:
    """Test the public API functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        self.temp_audio.write(b'fake audio data')
        self.temp_audio.close()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_audio.name):
            os.unlink(self.temp_audio.name)
    
    def test_get_supported_languages(self):
        """Test the public get_supported_languages function"""
        languages = get_supported_languages()
        
        assert isinstance(languages, dict)
        assert len(languages) > 0
        assert 'en' in languages
        assert 'es' in languages
    
    @patch('advanced_transcription.AdvancedTranscriber.detect_language')
    def test_detect_audio_language(self, mock_detect):
        """Test the public detect_audio_language function"""
        mock_detect.return_value = [
            {'code': 'en', 'name': 'English', 'confidence': 0.8}
        ]
        
        languages = detect_audio_language(self.temp_audio.name)
        
        assert isinstance(languages, list)
        assert len(languages) > 0
        assert languages[0]['code'] == 'en'
    
    @patch('advanced_transcription.AdvancedTranscriber.transcribe_with_speaker_diarization')
    def test_transcribe_advanced(self, mock_transcribe):
        """Test the public transcribe_advanced function"""
        # Mock the transcription result
        mock_result = AdvancedTranscriptionResult(
            text="Test transcription",
            language="en",
            confidence=0.9,
            processing_time=1.0,
            model_used="test-model",
            speakers=[],
            timestamped_words=[],
            detected_languages=[]
        )
        mock_transcribe.return_value = mock_result
        
        result = transcribe_advanced(self.temp_audio.name, language='en')
        
        assert isinstance(result, AdvancedTranscriptionResult)
        assert result.text == "Test transcription"
        assert result.language == "en"

def test_data_classes():
    """Test the data classes used in advanced transcription"""
    
    # Test SpeakerSegment
    speaker = SpeakerSegment(
        speaker_id="Speaker_1",
        start_time=0.0,
        end_time=2.5,
        text="Hello world",
        confidence=0.9
    )
    
    assert speaker.duration() == 2.5
    assert isinstance(speaker.to_dict(), dict)
    
    # Test TimestampedWord
    word = TimestampedWord(
        word="hello",
        start_time=0.0,
        end_time=0.5,
        confidence=0.9,
        speaker_id="Speaker_1"
    )
    
    assert isinstance(word.to_dict(), dict)
    
    # Test AdvancedTranscriptionResult
    result = AdvancedTranscriptionResult(
        text="Hello world",
        language="en",
        confidence=0.9,
        processing_time=1.0,
        model_used="test-model",
        speakers=[speaker],
        timestamped_words=[word],
        detected_languages=[{'code': 'en', 'name': 'English', 'confidence': 0.9}]
    )
    
    assert result.get_speaker_count() == 1
    assert result.get_total_duration() == 2.5
    assert isinstance(result.get_speaker_statistics(), dict)
    assert isinstance(result.to_dict(), dict)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])