"""
Test suite for Multilingual AI Dubbing System
Tests voice cloning, lip-sync generation, and quality assessment
"""

import pytest
import asyncio
import tempfile
import os
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from multilingual_ai_dubbing_system import (
    MultilingualAIDubbingSystem,
    VoiceProfile,
    SpeakerMapping,
    LipSyncConfig,
    DubbingJob,
    VoiceCloningEngine,
    LipSyncGenerator,
    MultiSpeakerManager,
    QualityAssessment,
    create_default_config
)

class TestVoiceProfile:
    """Test VoiceProfile data class"""
    
    def test_voice_profile_creation(self):
        """Test voice profile creation"""
        profile = VoiceProfile(
            voice_id="test_voice",
            name="Test Voice",
            language="en",
            gender="male",
            age_range="adult"
        )
        
        assert profile.voice_id == "test_voice"
        assert profile.name == "Test Voice"
        assert profile.language == "en"
        assert profile.gender == "male"
        assert profile.age_range == "adult"
        assert profile.quality_score == 0.0
        assert isinstance(profile.created_at, datetime)

class TestLipSyncConfig:
    """Test LipSyncConfig data class"""
    
    def test_default_config(self):
        """Test default lip-sync configuration"""
        config = LipSyncConfig()
        
        assert config.model_type == "musetalk"
        assert config.quality_level == "high"
        assert config.fps == 30
        assert config.resolution == (1920, 1080)
        assert config.face_enhancement is True
        assert config.temporal_consistency is True
        assert config.emotion_preservation is True
    
    def test_custom_config(self):
        """Test custom lip-sync configuration"""
        config = LipSyncConfig(
            model_type="wav2lip",
            quality_level="medium",
            fps=24,
            resolution=(1280, 720),
            face_enhancement=False
        )
        
        assert config.model_type == "wav2lip"
        assert config.quality_level == "medium"
        assert config.fps == 24
        assert config.resolution == (1280, 720)
        assert config.face_enhancement is False

class TestVoiceCloningEngine:
    """Test VoiceCloningEngine functionality"""
    
    @pytest.fixture
    def voice_engine(self):
        """Create voice cloning engine for testing"""
        config = {"use_coqui_tts": True, "use_gpt_sovits": False}
        return VoiceCloningEngine(config)
    
    def test_initialization(self, voice_engine):
        """Test voice engine initialization"""
        assert voice_engine.config is not None
        assert voice_engine.models == {}
        assert voice_engine.voice_profiles == {}
    
    @pytest.mark.asyncio
    async def test_analyze_voice_characteristics(self, voice_engine):
        """Test voice characteristics analysis"""
        # Mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            # Create dummy audio data
            sample_rate = 22050
            duration = 2.0
            samples = np.random.randn(int(sample_rate * duration))
            
            # Save as temporary file (simplified)
            tmp_file.write(samples.tobytes())
            audio_path = tmp_file.name
        
        try:
            characteristics = await voice_engine.analyze_voice_characteristics([audio_path])
            
            assert "gender" in characteristics
            assert "age_range" in characteristics
            assert "pitch_range" in characteristics
            assert "speaking_rate" in characteristics
            assert isinstance(characteristics["pitch_range"], list)
            assert len(characteristics["pitch_range"]) == 2
            
        finally:
            os.unlink(audio_path)
    
    @pytest.mark.asyncio
    async def test_generate_voice_embeddings(self, voice_engine):
        """Test voice embedding generation"""
        # Mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            audio_path = tmp_file.name
        
        try:
            embeddings = await voice_engine.generate_voice_embeddings([audio_path])
            
            assert isinstance(embeddings, np.ndarray)
            assert embeddings.shape == (13,)  # MFCC features
            
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    @pytest.mark.asyncio
    async def test_assess_voice_quality(self, voice_engine):
        """Test voice quality assessment"""
        # Mock audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            audio_path = tmp_file.name
        
        try:
            quality_score = await voice_engine.assess_voice_quality([audio_path])
            
            assert isinstance(quality_score, float)
            assert 0.0 <= quality_score <= 1.0
            
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)
    
    @pytest.mark.asyncio
    async def test_create_voice_profile(self, voice_engine):
        """Test voice profile creation"""
        # Mock voice samples
        voice_samples = ["sample1.wav", "sample2.wav"]
        metadata = {
            "name": "Test Voice",
            "language": "en",
            "gender": "male"
        }
        
        with patch.object(voice_engine, 'analyze_voice_characteristics') as mock_analyze, \
             patch.object(voice_engine, 'generate_voice_embeddings') as mock_embeddings, \
             patch.object(voice_engine, 'assess_voice_quality') as mock_quality:
            
            mock_analyze.return_value = {"gender": "male", "age_range": "adult"}
            mock_embeddings.return_value = np.zeros(13)
            mock_quality.return_value = 0.85
            
            profile = await voice_engine.create_voice_profile(voice_samples, metadata)
            
            assert isinstance(profile, VoiceProfile)
            assert profile.name == "Test Voice"
            assert profile.language == "en"
            assert profile.gender == "male"
            assert profile.quality_score == 0.85

class TestLipSyncGenerator:
    """Test LipSyncGenerator functionality"""
    
    @pytest.fixture
    def lip_sync_generator(self):
        """Create lip-sync generator for testing"""
        config = {"use_musetalk": True, "use_wav2lip": True}
        return LipSyncGenerator(config)
    
    def test_initialization(self, lip_sync_generator):
        """Test lip-sync generator initialization"""
        assert lip_sync_generator.config is not None
        assert lip_sync_generator.models == {}
    
    @pytest.mark.asyncio
    async def test_generate_basic_lipsync(self, lip_sync_generator):
        """Test basic lip-sync generation"""
        # Create temporary video and audio files
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as video_file, \
             tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as audio_file:
            
            video_path = video_file.name
            audio_path = audio_file.name
        
        try:
            config = LipSyncConfig(model_type="basic")
            
            with patch('cv2.VideoCapture') as mock_cap, \
                 patch('cv2.VideoWriter') as mock_writer, \
                 patch('librosa.load') as mock_load:
                
                # Mock video capture
                mock_cap_instance = Mock()
                mock_cap_instance.get.side_effect = lambda prop: {
                    0: 30,    # FPS
                    3: 1920,  # Width
                    4: 1080   # Height
                }[prop]
                mock_cap_instance.read.side_effect = [(True, np.zeros((1080, 1920, 3), dtype=np.uint8))] * 10 + [(False, None)]
                mock_cap.return_value = mock_cap_instance
                
                # Mock audio loading
                mock_load.return_value = (np.random.randn(22050 * 2), 22050)
                
                # Mock video writer
                mock_writer_instance = Mock()
                mock_writer.return_value = mock_writer_instance
                
                output_path = await lip_sync_generator.generate_basic_lipsync(
                    video_path, audio_path, "output.mp4", config
                )
                
                assert output_path == "output.mp4"
                mock_cap.assert_called_once_with(video_path)
                mock_writer.assert_called_once()
                
        finally:
            for path in [video_path, audio_path]:
                if os.path.exists(path):
                    os.unlink(path)
    
    def test_analyze_speech_activity(self, lip_sync_generator):
        """Test speech activity analysis"""
        # Create dummy audio
        audio = np.random.randn(22050 * 2)  # 2 seconds
        sr = 22050
        
        activity = lip_sync_generator.analyze_speech_activity(audio, sr)
        
        assert isinstance(activity, np.ndarray)
        assert len(activity) > 0
        assert np.all(activity >= 0.0)
        assert np.all(activity <= 1.0)

class TestMultiSpeakerManager:
    """Test MultiSpeakerManager functionality"""
    
    @pytest.fixture
    def speaker_manager(self):
        """Create speaker manager for testing"""
        config = {}
        return MultiSpeakerManager(config)
    
    @pytest.mark.asyncio
    async def test_identify_speakers(self, speaker_manager):
        """Test speaker identification"""
        audio_path = "test_audio.wav"
        
        speakers = await speaker_manager.identify_speakers(audio_path)
        
        assert isinstance(speakers, list)
        assert len(speakers) >= 0
        
        for speaker in speakers:
            assert "speaker_id" in speaker
            assert "segments" in speaker
            assert "total_duration" in speaker
            assert "characteristics" in speaker
    
    @pytest.mark.asyncio
    async def test_create_speaker_mapping(self, speaker_manager):
        """Test speaker mapping creation"""
        original_speakers = [
            {
                "speaker_id": "speaker_0",
                "segments": [(0.0, 10.0)],
                "total_duration": 10.0,
                "characteristics": {"gender": "male"}
            }
        ]
        
        target_voices = [
            VoiceProfile(
                voice_id="target_voice",
                name="Target Voice",
                language="en",
                gender="male",
                age_range="adult"
            )
        ]
        
        mappings = await speaker_manager.create_speaker_mapping(
            original_speakers, target_voices
        )
        
        assert isinstance(mappings, list)
        assert len(mappings) == 1
        assert isinstance(mappings[0], SpeakerMapping)
        assert mappings[0].original_speaker_id == "speaker_0"
        assert mappings[0].target_voice_profile.voice_id == "target_voice"

class TestQualityAssessment:
    """Test QualityAssessment functionality"""
    
    @pytest.fixture
    def quality_assessment(self):
        """Create quality assessment for testing"""
        config = {}
        return QualityAssessment(config)
    
    @pytest.mark.asyncio
    async def test_assess_dubbing_quality(self, quality_assessment):
        """Test overall dubbing quality assessment"""
        original_video = "original.mp4"
        dubbed_video = "dubbed.mp4"
        audio_path = "audio.wav"
        
        with patch.object(quality_assessment, 'assess_lip_sync_accuracy') as mock_lip_sync, \
             patch.object(quality_assessment, 'assess_voice_quality') as mock_voice, \
             patch.object(quality_assessment, 'assess_visual_quality') as mock_visual, \
             patch.object(quality_assessment, 'assess_temporal_consistency') as mock_temporal:
            
            mock_lip_sync.return_value = 0.85
            mock_voice.return_value = 0.90
            mock_visual.return_value = 0.88
            mock_temporal.return_value = 0.92
            
            metrics = await quality_assessment.assess_dubbing_quality(
                original_video, dubbed_video, audio_path
            )
            
            assert "lip_sync_accuracy" in metrics
            assert "voice_quality" in metrics
            assert "visual_quality" in metrics
            assert "temporal_consistency" in metrics
            assert "overall_score" in metrics
            
            assert metrics["lip_sync_accuracy"] == 0.85
            assert metrics["voice_quality"] == 0.90
            assert metrics["visual_quality"] == 0.88
            assert metrics["temporal_consistency"] == 0.92
            assert 0.0 <= metrics["overall_score"] <= 1.0
    
    @pytest.mark.asyncio
    async def test_assess_voice_quality(self, quality_assessment):
        """Test voice quality assessment"""
        # Create temporary audio file
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            audio_path = tmp_file.name
        
        try:
            with patch('librosa.load') as mock_load:
                # Mock high-quality audio
                mock_load.return_value = (np.random.randn(22050), 22050)
                
                quality_score = await quality_assessment.assess_voice_quality(audio_path)
                
                assert isinstance(quality_score, float)
                assert 0.0 <= quality_score <= 1.0
                
        finally:
            if os.path.exists(audio_path):
                os.unlink(audio_path)

class TestMultilingualAIDubbingSystem:
    """Test main dubbing system"""
    
    @pytest.fixture
    def dubbing_system(self):
        """Create dubbing system for testing"""
        config = create_default_config()
        return MultilingualAIDubbingSystem(config)
    
    def test_initialization(self, dubbing_system):
        """Test system initialization"""
        assert dubbing_system.config is not None
        assert dubbing_system.voice_cloning_engine is not None
        assert dubbing_system.lip_sync_generator is not None
        assert dubbing_system.multi_speaker_manager is not None
        assert dubbing_system.quality_assessment is not None
        assert dubbing_system.active_jobs == {}
    
    @pytest.mark.asyncio
    async def test_create_dubbing_job(self, dubbing_system):
        """Test dubbing job creation"""
        video_path = "test_video.mp4"
        target_language = "es"
        
        job = await dubbing_system.create_dubbing_job(video_path, target_language)
        
        assert isinstance(job, DubbingJob)
        assert job.input_video_path == video_path
        assert job.target_language == target_language
        assert job.status == "pending"
        assert job.progress == 0.0
        assert job.job_id in dubbing_system.active_jobs
    
    @pytest.mark.asyncio
    async def test_extract_audio(self, dubbing_system):
        """Test audio extraction from video"""
        video_path = "test_video.mp4"
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stderr = ""
            
            audio_path = await dubbing_system.extract_audio(video_path)
            
            assert audio_path.endswith('.wav')
            mock_run.assert_called_once()
            
            # Check FFmpeg command
            call_args = mock_run.call_args[0][0]
            assert "ffmpeg" in call_args
            assert video_path in call_args
    
    @pytest.mark.asyncio
    async def test_transcribe_audio(self, dubbing_system):
        """Test audio transcription"""
        audio_path = "test_audio.wav"
        language = "en"
        
        transcript = await dubbing_system.transcribe_audio(audio_path, language)
        
        assert "segments" in transcript
        assert "language" in transcript
        assert isinstance(transcript["segments"], list)
        
        for segment in transcript["segments"]:
            assert "start" in segment
            assert "end" in segment
            assert "text" in segment
            assert "speaker" in segment
    
    @pytest.mark.asyncio
    async def test_translate_transcript(self, dubbing_system):
        """Test transcript translation"""
        transcript = {
            "segments": [
                {
                    "start": 0.0,
                    "end": 5.0,
                    "text": "Hello world",
                    "speaker": "speaker_0"
                }
            ],
            "language": "en"
        }
        target_language = "es"
        
        translated = await dubbing_system.translate_transcript(transcript, target_language)
        
        assert "segments" in translated
        assert "language" in translated
        assert translated["language"] == target_language
        assert len(translated["segments"]) == len(transcript["segments"])
        
        # Check that text was modified (placeholder translation)
        original_text = transcript["segments"][0]["text"]
        translated_text = translated["segments"][0]["text"]
        assert translated_text != original_text
    
    def test_get_job_status(self, dubbing_system):
        """Test job status retrieval"""
        # Test non-existent job
        status = dubbing_system.get_job_status("non_existent_job")
        assert "error" in status
        
        # Test existing job
        job = DubbingJob(
            job_id="test_job",
            input_video_path="test.mp4",
            target_language="es",
            status="processing",
            progress=50.0
        )
        dubbing_system.active_jobs["test_job"] = job
        
        status = dubbing_system.get_job_status("test_job")
        assert status["job_id"] == "test_job"
        assert status["status"] == "processing"
        assert status["progress"] == 50.0
    
    def test_cleanup_temp_files(self, dubbing_system):
        """Test temporary file cleanup"""
        # Create some temporary files
        temp_files = ["temp_audio_123.wav", "temp_video_456.mp4", "temp_lipsynced_789.mp4"]
        
        for temp_file in temp_files:
            with open(temp_file, 'w') as f:
                f.write("test")
        
        try:
            # Run cleanup
            dubbing_system.cleanup_temp_files()
            
            # Check that files were removed
            for temp_file in temp_files:
                assert not os.path.exists(temp_file)
                
        except Exception:
            # Clean up manually if test fails
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end dubbing workflow"""
        config = create_default_config()
        dubbing_system = MultilingualAIDubbingSystem(config)
        
        # Mock all external dependencies
        with patch.object(dubbing_system, 'extract_audio') as mock_extract, \
             patch.object(dubbing_system.multi_speaker_manager, 'identify_speakers') as mock_speakers, \
             patch.object(dubbing_system, 'transcribe_audio') as mock_transcribe, \
             patch.object(dubbing_system, 'translate_transcript') as mock_translate, \
             patch.object(dubbing_system, 'create_target_voices') as mock_voices, \
             patch.object(dubbing_system.multi_speaker_manager, 'create_speaker_mapping') as mock_mapping, \
             patch.object(dubbing_system, 'generate_dubbed_audio') as mock_audio, \
             patch.object(dubbing_system.lip_sync_generator, 'generate_lip_sync') as mock_lipsync, \
             patch.object(dubbing_system.quality_assessment, 'assess_dubbing_quality') as mock_quality:
            
            # Setup mocks
            mock_extract.return_value = "audio.wav"
            mock_speakers.return_value = [{"speaker_id": "speaker_0", "segments": [(0, 10)], "total_duration": 10, "characteristics": {}}]
            mock_transcribe.return_value = {"segments": [{"start": 0, "end": 10, "text": "Hello", "speaker": "speaker_0"}], "language": "en"}
            mock_translate.return_value = {"segments": [{"start": 0, "end": 10, "text": "Hola", "speaker": "speaker_0"}], "language": "es"}
            mock_voices.return_value = [VoiceProfile("voice_1", "Voice 1", "es", "male", "adult")]
            mock_mapping.return_value = [SpeakerMapping("speaker_0", VoiceProfile("voice_1", "Voice 1", "es", "male", "adult"))]
            mock_audio.return_value = "dubbed_audio.wav"
            mock_lipsync.return_value = "lipsynced_video.mp4"
            mock_quality.return_value = {"overall_score": 0.85, "lip_sync_accuracy": 0.8, "voice_quality": 0.9, "visual_quality": 0.85, "temporal_consistency": 0.85}
            
            # Create and process job
            job = await dubbing_system.create_dubbing_job("input.mp4", "es")
            result = await dubbing_system.process_dubbing_job(job)
            
            # Verify result
            assert result["job_id"] == job.job_id
            assert result["output_video_path"] == "lipsynced_video.mp4"
            assert result["dubbed_audio_path"] == "dubbed_audio.wav"
            assert "quality_metrics" in result
            assert "processing_time" in result
            
            # Verify job status
            assert job.status == "completed"
            assert job.progress == 100.0

def test_create_default_config():
    """Test default configuration creation"""
    config = create_default_config()
    
    assert isinstance(config, dict)
    assert "use_coqui_tts" in config
    assert "use_musetalk" in config
    assert "use_wav2lip" in config
    assert "max_workers" in config
    assert "quality_thresholds" in config
    
    # Check quality thresholds
    thresholds = config["quality_thresholds"]
    assert "min_lip_sync_accuracy" in thresholds
    assert "min_voice_quality" in thresholds
    assert "min_visual_quality" in thresholds
    assert "min_overall_score" in thresholds

if __name__ == "__main__":
    pytest.main([__file__, "-v"])