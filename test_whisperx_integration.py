"""
Comprehensive tests for WhisperX enhanced speaker diarization
"""

import pytest
import asyncio
import numpy as np
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from speaker_diarization.providers.whisperx_provider import WhisperXProvider
from speaker_diarization.speaker_profiler import SpeakerProfiler, SpeakerProfile
from speaker_diarization.integration import TranscriptionDiarizationIntegrator
from speaker_diarization.diarization_manager import DiarizationResult, SpeakerSegment


class TestWhisperXProvider:
    """Test WhisperX provider functionality"""
    
    @pytest.fixture
    def mock_whisperx(self):
        """Mock WhisperX module"""
        with patch.dict('sys.modules', {'whisperx': Mock()}):
            import sys
            mock_whisperx = sys.modules['whisperx']
            # Mock model loading
            mock_model = Mock()
            mock_align_model = Mock()
            mock_metadata = {'language': 'en'}
            mock_diarize_model = Mock()
            
            mock_whisperx.load_model.return_value = mock_model
            mock_whisperx.load_align_model.return_value = (mock_align_model, mock_metadata)
            mock_whisperx.DiarizationPipeline.return_value = mock_diarize_model
            mock_whisperx.load_audio.return_value = np.random.random(16000 * 10)  # 10 seconds
            
            # Mock transcription result
            mock_model.transcribe.return_value = {
                'segments': [
                    {'start': 0.0, 'end': 5.0, 'text': 'Hello world'},
                    {'start': 5.5, 'end': 10.0, 'text': 'How are you'}
                ],
                'language': 'en'
            }
            
            # Mock alignment result
            mock_whisperx.align.return_value = {
                'segments': [
                    {'start': 0.0, 'end': 5.0, 'text': 'Hello world', 'speaker': 'SPEAKER_00'},
                    {'start': 5.5, 'end': 10.0, 'text': 'How are you', 'speaker': 'SPEAKER_01'}
                ],
                'word_segments': []
            }
            
            # Mock diarization segments
            mock_diarize_segments = Mock()
            mock_diarize_segments.itertracks.return_value = [
                (Mock(start=0.0, end=5.0, duration=5.0), None, 'SPEAKER_00'),
                (Mock(start=5.5, end=10.0, duration=4.5), None, 'SPEAKER_01')
            ]
            mock_diarize_model.return_value = mock_diarize_segments
            
            # Mock speaker assignment
            mock_whisperx.assign_word_speakers.return_value = {
                'segments': [
                    {'start': 0.0, 'end': 5.0, 'text': 'Hello world', 'speaker': 'SPEAKER_00'},
                    {'start': 5.5, 'end': 10.0, 'text': 'How are you', 'speaker': 'SPEAKER_01'}
                ]
            }
            
            yield mock_whisperx
    
    @pytest.fixture
    def provider(self, mock_whisperx):
        """Create WhisperX provider instance"""
        config = {
            'model_size': 'base',
            'device': 'cpu',
            'language': 'en'
        }
        return WhisperXProvider(config)
    
    def test_provider_initialization(self, provider, mock_whisperx):
        """Test provider initialization"""
        assert provider.model_size == 'base'
        assert provider.device == 'cpu'
        assert provider.language == 'en'
        assert provider.is_available()
    
    def test_provider_not_available_without_whisperx(self):
        """Test provider availability without WhisperX"""
        with patch.dict('sys.modules', {'whisperx': None}):
            provider = WhisperXProvider()
            assert not provider.is_available()
    
    @pytest.mark.asyncio
    async def test_diarization_process(self, provider, mock_whisperx, tmp_path):
        """Test complete diarization process"""
        # Create temporary audio file
        audio_file = tmp_path / "test_audio.wav"
        audio_file.write_bytes(b"fake audio data")
        
        # Mock audio duration
        with patch.object(provider, 'get_audio_duration', return_value=10.0):
            result = await provider.diarize(str(audio_file))
        
        assert isinstance(result, DiarizationResult)
        assert result.audio_duration == 10.0
        assert len(result.speakers) == 2
        assert len(result.segments) == 2
        assert result.metadata['provider'] == 'whisperx'
    
    def test_convert_whisperx_result(self, provider):
        """Test conversion of WhisperX results to our format"""
        whisperx_data = {
            'segments': [
                {'start': 0.0, 'end': 5.0, 'text': 'Hello world', 'speaker': 'SPEAKER_00'},
                {'start': 5.5, 'end': 10.0, 'text': 'How are you', 'speaker': 'SPEAKER_01'}
            ]
        }
        
        result = provider._convert_whisperx_result(whisperx_data, 10.0, 1.0)
        
        assert len(result.segments) == 2
        assert result.segments[0].speaker_id == 'SPEAKER_00'
        assert result.segments[0].text == 'Hello world'
        assert result.segments[1].speaker_id == 'SPEAKER_01'
        assert result.segments[1].text == 'How are you'
    
    @patch('speaker_diarization.providers.whisperx_provider.EncoderClassifier')
    def test_extract_speaker_embeddings(self, mock_classifier, provider, mock_whisperx):
        """Test speaker embedding extraction"""
        # Mock classifier
        mock_classifier_instance = Mock()
        mock_classifier_instance.encode_batch.return_value = Mock()
        mock_classifier_instance.encode_batch.return_value.squeeze.return_value.cpu.return_value.numpy.return_value = np.random.random(512)
        mock_classifier.from_hparams.return_value = mock_classifier_instance
        
        # Create test segments
        segments = [
            SpeakerSegment('SPEAKER_00', 0.0, 5.0, 0.95),
            SpeakerSegment('SPEAKER_01', 5.5, 10.0, 0.90)
        ]
        
        embeddings = provider.extract_speaker_embeddings("fake_audio.wav", segments)
        
        assert len(embeddings) == 2
        assert 'SPEAKER_00' in embeddings
        assert 'SPEAKER_01' in embeddings
        assert embeddings['SPEAKER_00'].shape == (512,)
    
    def test_cluster_speakers(self, provider):
        """Test speaker clustering"""
        # Create mock embeddings
        embeddings = {
            'SPEAKER_00': np.random.random(512),
            'SPEAKER_01': np.random.random(512),
            'SPEAKER_02': np.random.random(512)
        }
        
        with patch('speaker_diarization.providers.whisperx_provider.SpectralClustering') as mock_clustering:
            mock_clusterer = Mock()
            mock_clusterer.fit_predict.return_value = np.array([0, 1, 0])
            mock_clustering.return_value = mock_clusterer
            
            mapping = provider.cluster_speakers(embeddings, n_clusters=2)
            
            assert len(mapping) == 3
            assert all(speaker_id in mapping for speaker_id in embeddings.keys())
    
    def test_create_speaker_profiles(self, provider):
        """Test speaker profile creation"""
        embeddings = {
            'SPEAKER_00': np.random.random(512),
            'SPEAKER_01': np.random.random(512)
        }
        
        segments = [
            SpeakerSegment('SPEAKER_00', 0.0, 5.0, 0.95, text="Hello"),
            SpeakerSegment('SPEAKER_00', 6.0, 8.0, 0.90, text="world"),
            SpeakerSegment('SPEAKER_01', 8.5, 12.0, 0.85, text="How are you")
        ]
        
        profiles = provider.create_speaker_profiles(embeddings, segments)
        
        assert len(profiles) == 2
        assert 'SPEAKER_00' in profiles
        assert 'SPEAKER_01' in profiles
        
        profile_00 = profiles['SPEAKER_00']
        assert profile_00['total_speaking_time'] == 7.0  # 5.0 + 2.0
        assert profile_00['segment_count'] == 2
        assert 'voice_characteristics' in profile_00
        assert 'speaking_pattern' in profile_00


class TestSpeakerProfiler:
    """Test speaker profiling functionality"""
    
    @pytest.fixture
    def profiler(self, tmp_path):
        """Create speaker profiler with temporary directory"""
        return SpeakerProfiler(str(tmp_path / "profiles"))
    
    def test_profiler_initialization(self, profiler):
        """Test profiler initialization"""
        assert profiler.profile_dir.exists()
        assert profiler.db_path.exists()
        assert isinstance(profiler._profile_cache, dict)
    
    def test_create_profile(self, profiler):
        """Test creating a new speaker profile"""
        embedding = np.random.random(512)
        voice_chars = {'voice_type': 'expressive', 'embedding_norm': 1.5}
        speaking_patterns = {'average_segment_duration': 5.2}
        
        profile = profiler.create_profile(
            'test_speaker',
            embedding,
            voice_chars,
            speaking_patterns,
            name='Test Speaker'
        )
        
        assert profile.speaker_id == 'test_speaker'
        assert profile.name == 'Test Speaker'
        assert len(profile.embedding) == 512
        assert profile.voice_characteristics == voice_chars
        assert profile.speaking_patterns == speaking_patterns
        assert 'test_speaker' in profiler._profile_cache
    
    def test_update_profile(self, profiler):
        """Test updating an existing profile"""
        # Create initial profile
        embedding = np.random.random(512)
        profile = profiler.create_profile('test_speaker', embedding, {}, {})
        
        # Update profile
        new_embedding = np.random.random(512)
        new_chars = {'voice_type': 'steady'}
        
        updated_profile = profiler.update_profile(
            'test_speaker',
            new_embedding=new_embedding,
            new_characteristics=new_chars,
            speaking_time=10.5
        )
        
        assert updated_profile is not None
        assert updated_profile.recording_count == 2
        assert updated_profile.total_speaking_time == 10.5
        assert updated_profile.voice_characteristics['voice_type'] == 'steady'
    
    def test_recognize_speaker(self, profiler):
        """Test speaker recognition"""
        # Create known speaker
        known_embedding = np.random.random(512)
        profiler.create_profile('known_speaker', known_embedding, {}, {})
        
        # Test recognition with similar embedding
        similar_embedding = known_embedding + np.random.normal(0, 0.01, 512)
        recognized_id, confidence = profiler.recognize_speaker(similar_embedding)
        
        assert recognized_id == 'known_speaker'
        assert confidence > 0.8
        
        # Test with very different embedding
        different_embedding = np.random.random(512) * 10
        recognized_id, confidence = profiler.recognize_speaker(different_embedding)
        
        # Either no recognition or low confidence
        if recognized_id is not None:
            assert confidence < profiler.similarity_threshold
        else:
            assert confidence < profiler.similarity_threshold
    
    def test_merge_profiles(self, profiler):
        """Test merging two speaker profiles"""
        # Create two profiles
        embedding1 = np.random.random(512)
        embedding2 = np.random.random(512)
        
        profiler.create_profile('speaker1', embedding1, {}, {})
        profiler.create_profile('speaker2', embedding2, {}, {})
        
        # Merge profiles
        success = profiler.merge_profiles('speaker1', 'speaker2')
        
        assert success
        assert 'speaker1' in profiler._profile_cache
        assert 'speaker2' not in profiler._profile_cache
        
        merged_profile = profiler.get_profile('speaker1')
        assert merged_profile.recording_count == 2
    
    def test_export_import_profiles(self, profiler, tmp_path):
        """Test profile export and import"""
        # Create test profile
        embedding = np.random.random(512)
        profiler.create_profile('test_speaker', embedding, {'voice_type': 'test'}, {})
        
        # Export profiles
        export_path = tmp_path / "exported_profiles.json"
        success = profiler.export_profiles(str(export_path))
        
        assert success
        assert export_path.exists()
        
        # Create new profiler and import
        new_profiler = SpeakerProfiler(str(tmp_path / "new_profiles"))
        success = new_profiler.import_profiles(str(export_path))
        
        assert success
        assert 'test_speaker' in new_profiler._profile_cache
        
        imported_profile = new_profiler.get_profile('test_speaker')
        assert imported_profile.voice_characteristics['voice_type'] == 'test'


class TestTranscriptionDiarizationIntegrator:
    """Test integration functionality"""
    
    @pytest.fixture
    def integrator(self):
        """Create integrator instance"""
        return TranscriptionDiarizationIntegrator()
    
    def test_integrator_initialization(self, integrator):
        """Test integrator initialization"""
        assert 'whisperx' in integrator.providers
        assert isinstance(integrator.speaker_profiler, SpeakerProfiler)
    
    def test_get_provider(self, integrator):
        """Test provider retrieval"""
        # Test getting mock provider (always available)
        provider = integrator.get_provider('mock')
        assert provider is not None
        assert provider.is_available()
        
        # Test getting non-existent provider
        provider = integrator.get_provider('nonexistent')
        assert provider is None
    
    @pytest.mark.asyncio
    async def test_process_with_diarization(self, integrator, tmp_path):
        """Test basic diarization processing"""
        # Create temporary audio file
        audio_file = tmp_path / "test_audio.wav"
        audio_file.write_bytes(b"fake audio data")
        
        # Use mock provider for testing
        transcript, result = await integrator.process_with_diarization(
            str(audio_file),
            "Test transcript",
            provider_name='mock'
        )
        
        assert isinstance(transcript, str)
        assert isinstance(result, DiarizationResult)
        assert len(result.speakers) > 0
    
    def test_update_speaker_id_in_result(self, integrator):
        """Test updating speaker IDs in results"""
        result = DiarizationResult()
        
        # Add test segment and speaker
        segment = SpeakerSegment('old_id', 0.0, 5.0, 0.95)
        result.add_segment(segment)
        
        # Update speaker ID
        integrator._update_speaker_id_in_result(result, 'old_id', 'new_id')
        
        assert result.segments[0].speaker_id == 'new_id'
        assert 'new_id' in result.speakers
        assert 'old_id' not in result.speakers
    
    def test_create_enhanced_export_data(self, integrator):
        """Test enhanced export data creation"""
        # Create test diarization result
        result = DiarizationResult(audio_duration=10.0)
        segment = SpeakerSegment('SPEAKER_00', 0.0, 5.0, 0.95, text="Hello world")
        result.add_segment(segment)
        
        export_data = integrator.create_enhanced_export_data(
            "Test transcript",
            result,
            [{'type': 'PERSON', 'text': 'John'}]
        )
        
        assert 'transcript' in export_data
        assert 'speakers' in export_data
        assert 'segments' in export_data
        assert 'entities' in export_data
        assert export_data['metadata']['has_speakers']
        assert export_data['metadata']['speaker_count'] == 1


class TestIntegrationScenarios:
    """Test complete integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_whisperx_processing(self, tmp_path):
        """Test complete end-to-end processing with WhisperX"""
        # This test would require actual WhisperX installation
        # For now, we'll test with mock provider
        
        integrator = TranscriptionDiarizationIntegrator()
        
        # Create test audio file
        audio_file = tmp_path / "test_audio.wav"
        audio_file.write_bytes(b"fake audio data")
        
        config = {
            'min_segment_duration': 1.0,
            'max_speakers': 3,
            'use_cache': False
        }
        
        # Process with mock provider (WhisperX not available in test environment)
        transcript, result, profiles = await integrator.process_with_speaker_profiling(
            str(audio_file),
            "Test transcript",
            provider_name='mock',
            config=config,
            recording_id='test_recording'
        )
        
        assert isinstance(transcript, str)
        assert isinstance(result, DiarizationResult)
        assert isinstance(profiles, dict)
        assert len(result.speakers) > 0
    
    def test_speaker_recognition_workflow(self, tmp_path):
        """Test speaker recognition across multiple recordings"""
        profiler = SpeakerProfiler(str(tmp_path / "profiles"))
        
        # Simulate first recording
        embedding1 = np.random.random(512)
        profile1 = profiler.create_profile(
            'speaker_001',
            embedding1,
            {'voice_type': 'expressive'},
            {'average_duration': 5.0},
            name='Alice'
        )
        
        # Simulate second recording with same speaker
        # (slightly different embedding due to recording conditions)
        embedding2 = embedding1 + np.random.normal(0, 0.02, 512)
        
        recognized_id, confidence = profiler.recognize_speaker(embedding2)
        
        assert recognized_id == 'speaker_001'
        assert confidence > 0.8
        
        # Update profile with new data
        updated_profile = profiler.update_profile(
            recognized_id,
            new_embedding=embedding2,
            speaking_time=15.5
        )
        
        assert updated_profile.recording_count == 2
        assert updated_profile.total_speaking_time == 15.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])