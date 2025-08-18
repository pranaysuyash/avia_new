"""
Test Suite for Professional Audio Format Handler
Comprehensive testing for audio format handling and conversion

Requirements: 1.3
Dependencies: professional_audio_format_handler.py
"""

import pytest
import numpy as np
import tempfile
import os
import asyncio
import soundfile as sf
from unittest.mock import Mock, patch
from pathlib import Path

try:
    from professional_audio_format_handler import (
        ProfessionalAudioFormatHandler, AudioFormat, AudioCodec,
        QualityLevel, ConversionMode, ConversionSettings,
        BatchProcessingJob, AudioMetadata, ConversionResult
    )
    FORMAT_HANDLER_AVAILABLE = True
except ImportError:
    FORMAT_HANDLER_AVAILABLE = False
    pytest.skip("Professional Audio Format Handler not available", allow_module_level=True)


class TestProfessionalAudioFormatHandler:
    """Test cases for ProfessionalAudioFormatHandler"""
    
    @pytest.fixture
    def handler(self):
        """Create a ProfessionalAudioFormatHandler instance for testing"""
        return ProfessionalAudioFormatHandler()
    
    @pytest.fixture
    def sample_audio_data(self):
        """Create sample audio data for testing"""
        duration = 2.0  # seconds
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create stereo test signal
        left = np.sin(2 * np.pi * 440 * t) * 0.5  # 440 Hz sine wave
        right = np.sin(2 * np.pi * 880 * t) * 0.3  # 880 Hz sine wave
        
        return np.column_stack([left, right]), sample_rate
    
    @pytest.fixture
    def sample_wav_file(self, sample_audio_data):
        """Create a temporary WAV file for testing"""
        audio_data, sample_rate = sample_audio_data
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            yield tmp_file.name
        
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)
    
    @pytest.fixture
    def sample_flac_file(self, sample_audio_data):
        """Create a temporary FLAC file for testing"""
        audio_data, sample_rate = sample_audio_data
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.flac') as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate, subtype='PCM_16')
            yield tmp_file.name
        
        # Cleanup
        if os.path.exists(tmp_file.name):
            os.unlink(tmp_file.name)
    
    def test_handler_initialization(self, handler):
        """Test handler initialization"""
        assert handler is not None
        assert hasattr(handler, 'format_info')
        assert hasattr(handler, 'codec_configs')
        assert hasattr(handler, 'processing_stats')
        assert len(handler.format_info) > 0
    
    def test_format_info_initialization(self, handler):
        """Test format information initialization"""
        # Check that all major formats are supported
        expected_formats = [
            AudioFormat.WAV, AudioFormat.FLAC, AudioFormat.MP3,
            AudioFormat.AAC, AudioFormat.OGG, AudioFormat.OPUS
        ]
        
        for format in expected_formats:
            assert format in handler.format_info
            info = handler.format_info[format]
            assert info.format == format
            assert info.max_channels > 0
            assert info.max_sample_rate > 0
            assert len(info.file_extensions) > 0
    
    def test_codec_config_initialization(self, handler):
        """Test codec configuration initialization"""
        expected_codecs = [AudioCodec.MP3, AudioCodec.AAC, AudioCodec.FLAC, AudioCodec.OPUS]
        
        for codec in expected_codecs:
            assert codec in handler.codec_configs
            config = handler.codec_configs[codec]
            assert 'quality_settings' in config
            assert len(config['quality_settings']) > 0
    
    @pytest.mark.asyncio
    async def test_format_detection_wav(self, handler, sample_wav_file):
        """Test WAV format detection"""
        format_detected, metadata = await handler.detect_format(sample_wav_file)
        
        assert format_detected == AudioFormat.WAV
        assert metadata is not None
        assert metadata.duration is not None
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
    
    @pytest.mark.asyncio
    async def test_format_detection_flac(self, handler, sample_flac_file):
        """Test FLAC format detection"""
        format_detected, metadata = await handler.detect_format(sample_flac_file)
        
        assert format_detected == AudioFormat.FLAC
        assert metadata is not None
        assert metadata.duration is not None
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
    
    @pytest.mark.asyncio
    async def test_metadata_extraction(self, handler, sample_wav_file):
        """Test metadata extraction"""
        format_detected, metadata = await handler.detect_format(sample_wav_file)
        
        # Check technical metadata
        assert metadata.duration > 0
        assert metadata.sample_rate > 0
        assert metadata.channels > 0
        assert metadata.bit_depth is not None
        
        # Check quality metrics
        assert metadata.peak_level is not None
        assert metadata.rms_level is not None
        assert metadata.dynamic_range is not None
    
    @pytest.mark.asyncio
    async def test_conversion_settings_validation(self, handler, sample_wav_file):
        """Test conversion settings validation"""
        # Get input metadata
        _, input_metadata = await handler.detect_format(sample_wav_file)
        
        # Test valid settings
        settings = ConversionSettings(
            target_format=AudioFormat.FLAC,
            sample_rate=48000,
            channels=2,
            quality_level=QualityLevel.HIGH
        )
        
        validated_settings = handler._validate_conversion_settings(settings, input_metadata)
        assert validated_settings.target_format == AudioFormat.FLAC
        assert validated_settings.sample_rate == 48000
        assert validated_settings.channels == 2
    
    @pytest.mark.asyncio
    async def test_wav_to_flac_conversion(self, handler, sample_wav_file):
        """Test WAV to FLAC conversion"""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.flac').name
        
        try:
            settings = ConversionSettings(
                target_format=AudioFormat.FLAC,
                quality_level=QualityLevel.HIGH,
                preserve_metadata=True
            )
            
            result = await handler.convert_format(sample_wav_file, output_file, settings)
            
            assert result.success
            assert result.output_file == output_file
            assert result.original_format == AudioFormat.WAV
            assert result.target_format == AudioFormat.FLAC
            assert os.path.exists(output_file)
            
            # Verify converted file
            converted_info = sf.info(output_file)
            assert converted_info.channels == 2
            assert converted_info.samplerate == 44100
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @pytest.mark.asyncio
    async def test_sample_rate_conversion(self, handler, sample_wav_file):
        """Test sample rate conversion"""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        
        try:
            settings = ConversionSettings(
                target_format=AudioFormat.WAV,
                sample_rate=48000,  # Convert from 44100 to 48000
                quality_level=QualityLevel.HIGH
            )
            
            result = await handler.convert_format(sample_wav_file, output_file, settings)
            
            assert result.success
            assert os.path.exists(output_file)
            
            # Verify sample rate conversion
            converted_info = sf.info(output_file)
            assert converted_info.samplerate == 48000
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @pytest.mark.asyncio
    async def test_channel_conversion(self, handler, sample_wav_file):
        """Test channel conversion (stereo to mono)"""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        
        try:
            settings = ConversionSettings(
                target_format=AudioFormat.WAV,
                channels=1,  # Convert stereo to mono
                quality_level=QualityLevel.HIGH
            )
            
            result = await handler.convert_format(sample_wav_file, output_file, settings)
            
            assert result.success
            assert os.path.exists(output_file)
            
            # Verify channel conversion
            converted_info = sf.info(output_file)
            assert converted_info.channels == 1
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @pytest.mark.asyncio
    async def test_quality_metrics_calculation(self, handler, sample_wav_file):
        """Test quality metrics calculation"""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.flac').name
        
        try:
            settings = ConversionSettings(
                target_format=AudioFormat.FLAC,
                quality_level=QualityLevel.HIGH
            )
            
            result = await handler.convert_format(sample_wav_file, output_file, settings)
            
            assert result.success
            assert result.quality_metrics is not None
            
            # Check that quality metrics are calculated
            if 'snr_db' in result.quality_metrics:
                assert isinstance(result.quality_metrics['snr_db'], float)
            if 'correlation' in result.quality_metrics:
                assert 0 <= result.quality_metrics['correlation'] <= 1
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, handler, sample_audio_data):
        """Test batch processing functionality"""
        # Create multiple test files
        test_files = []
        for i in range(3):
            audio_data, sample_rate = sample_audio_data
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'_test_{i}.wav')
            sf.write(temp_file.name, audio_data, sample_rate)
            test_files.append(temp_file.name)
        
        output_dir = tempfile.mkdtemp()
        
        try:
            # Create batch job
            settings = ConversionSettings(
                target_format=AudioFormat.FLAC,
                quality_level=QualityLevel.STANDARD
            )
            
            job = BatchProcessingJob(
                job_id="test_batch",
                input_files=test_files,
                output_directory=output_dir,
                conversion_settings=settings,
                parallel_workers=2
            )
            
            # Process batch
            completed_job = await handler.batch_convert(job)
            
            assert completed_job.status in ["completed", "partially_completed"]
            assert len(completed_job.results) == len(test_files)
            
            # Check that at least some conversions succeeded
            successful_conversions = sum(1 for r in completed_job.results if r.success)
            assert successful_conversions > 0
            
        finally:
            # Cleanup
            for file in test_files:
                if os.path.exists(file):
                    os.unlink(file)
            
            # Cleanup output directory
            import shutil
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
    
    @pytest.mark.asyncio
    async def test_audio_validation(self, handler, sample_wav_file):
        """Test audio file validation"""
        validation_result = await handler.validate_audio_file(sample_wav_file)
        
        assert validation_result['is_valid']
        assert validation_result['file_exists']
        assert validation_result['format_detected'] is not None
        assert validation_result['metadata'] is not None
        assert isinstance(validation_result['issues'], list)
        assert isinstance(validation_result['recommendations'], list)
    
    @pytest.mark.asyncio
    async def test_invalid_file_validation(self, handler):
        """Test validation of invalid/non-existent file"""
        validation_result = await handler.validate_audio_file("nonexistent_file.wav")
        
        assert not validation_result['is_valid']
        assert not validation_result['file_exists']
        assert "File does not exist" in validation_result['issues']
    
    @pytest.mark.asyncio
    async def test_format_info_retrieval(self, handler):
        """Test format information retrieval"""
        wav_info = await handler.get_format_info(AudioFormat.WAV)
        
        assert wav_info is not None
        assert wav_info.format == AudioFormat.WAV
        assert wav_info.codec == AudioCodec.PCM
        assert wav_info.is_lossless
        assert wav_info.supports_metadata
        assert wav_info.max_channels >= 2
        assert wav_info.max_sample_rate >= 44100
    
    @pytest.mark.asyncio
    async def test_supported_formats_list(self, handler):
        """Test getting list of supported formats"""
        supported_formats = await handler.get_supported_formats()
        
        assert isinstance(supported_formats, list)
        assert len(supported_formats) > 0
        assert AudioFormat.WAV in supported_formats
        assert AudioFormat.FLAC in supported_formats
    
    @pytest.mark.asyncio
    async def test_conversion_recommendations(self, handler, sample_wav_file):
        """Test conversion recommendations for different use cases"""
        use_cases = ["streaming", "podcast", "archival", "mobile", "broadcast"]
        
        for use_case in use_cases:
            recommendations = await handler.get_conversion_recommendations(
                sample_wav_file, use_case
            )
            
            assert isinstance(recommendations, ConversionSettings)
            assert recommendations.target_format is not None
            assert recommendations.quality_level is not None
            
            # Verify use case specific settings
            if use_case == "podcast":
                assert recommendations.channels == 1  # Mono for speech
            elif use_case == "archival":
                assert recommendations.target_format == AudioFormat.FLAC
                assert recommendations.quality_level == QualityLevel.ARCHIVE
    
    @pytest.mark.asyncio
    async def test_processing_statistics(self, handler, sample_wav_file):
        """Test processing statistics tracking"""
        # Perform a conversion to generate statistics
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.flac').name
        
        try:
            settings = ConversionSettings(
                target_format=AudioFormat.FLAC,
                quality_level=QualityLevel.HIGH
            )
            
            await handler.convert_format(sample_wav_file, output_file, settings)
            
            # Get statistics
            stats = await handler.get_processing_statistics()
            
            assert isinstance(stats, dict)
            assert 'total_conversions' in stats
            assert 'successful_conversions' in stats
            assert 'failed_conversions' in stats
            assert 'success_rate' in stats
            assert 'average_processing_time' in stats
            
            assert stats['total_conversions'] > 0
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    def test_conversion_settings_creation(self):
        """Test ConversionSettings creation and validation"""
        settings = ConversionSettings(
            target_format=AudioFormat.MP3,
            sample_rate=44100,
            channels=2,
            bitrate=192,
            quality_level=QualityLevel.HIGH,
            preserve_metadata=True
        )
        
        assert settings.target_format == AudioFormat.MP3
        assert settings.sample_rate == 44100
        assert settings.channels == 2
        assert settings.bitrate == 192
        assert settings.quality_level == QualityLevel.HIGH
        assert settings.preserve_metadata
    
    def test_audio_metadata_creation(self):
        """Test AudioMetadata creation"""
        metadata = AudioMetadata(
            title="Test Song",
            artist="Test Artist",
            duration=120.5,
            sample_rate=44100,
            channels=2,
            bit_depth=16
        )
        
        assert metadata.title == "Test Song"
        assert metadata.artist == "Test Artist"
        assert metadata.duration == 120.5
        assert metadata.sample_rate == 44100
        assert metadata.channels == 2
        assert metadata.bit_depth == 16
    
    def test_batch_processing_job_creation(self):
        """Test BatchProcessingJob creation"""
        settings = ConversionSettings(target_format=AudioFormat.FLAC)
        
        job = BatchProcessingJob(
            job_id="test_job",
            input_files=["file1.wav", "file2.wav"],
            output_directory="/tmp/output",
            conversion_settings=settings,
            parallel_workers=4
        )
        
        assert job.job_id == "test_job"
        assert len(job.input_files) == 2
        assert job.output_directory == "/tmp/output"
        assert job.conversion_settings.target_format == AudioFormat.FLAC
        assert job.parallel_workers == 4
        assert job.status == "pending"
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_input(self, handler):
        """Test error handling for invalid input file"""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.flac').name
        
        try:
            settings = ConversionSettings(target_format=AudioFormat.FLAC)
            
            result = await handler.convert_format(
                "nonexistent_file.wav", output_file, settings
            )
            
            assert not result.success
            assert result.error_message is not None
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @pytest.mark.asyncio
    async def test_normalization_feature(self, handler, sample_wav_file):
        """Test audio normalization feature"""
        output_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
        
        try:
            settings = ConversionSettings(
                target_format=AudioFormat.WAV,
                normalize_audio=True,
                quality_level=QualityLevel.HIGH
            )
            
            result = await handler.convert_format(sample_wav_file, output_file, settings)
            
            assert result.success
            assert os.path.exists(output_file)
            
            # Load and check normalized audio
            normalized_audio, _ = sf.read(output_file)
            peak_level = np.max(np.abs(normalized_audio))
            
            # Normalized audio should have peak close to but not exceeding 1.0
            assert 0.9 <= peak_level <= 1.0
            
        finally:
            if os.path.exists(output_file):
                os.unlink(output_file)
    
    @pytest.mark.asyncio
    async def test_cleanup(self, handler):
        """Test handler cleanup"""
        await handler.cleanup()
        # Should complete without errors


class TestAudioFormats:
    """Test audio format enumerations and utilities"""
    
    def test_audio_format_enum(self):
        """Test AudioFormat enumeration"""
        assert AudioFormat.WAV.value == "wav"
        assert AudioFormat.FLAC.value == "flac"
        assert AudioFormat.MP3.value == "mp3"
        assert AudioFormat.AAC.value == "aac"
        assert AudioFormat.OGG.value == "ogg"
    
    def test_audio_codec_enum(self):
        """Test AudioCodec enumeration"""
        assert AudioCodec.PCM.value == "pcm"
        assert AudioCodec.FLAC.value == "flac"
        assert AudioCodec.MP3.value == "mp3"
        assert AudioCodec.AAC.value == "aac"
    
    def test_quality_level_enum(self):
        """Test QualityLevel enumeration"""
        assert QualityLevel.DRAFT.value == "draft"
        assert QualityLevel.STANDARD.value == "standard"
        assert QualityLevel.HIGH.value == "high"
        assert QualityLevel.LOSSLESS.value == "lossless"
        assert QualityLevel.ARCHIVE.value == "archive"


class TestConversionMethods:
    """Test different conversion method implementations"""
    
    @pytest.fixture
    def handler(self):
        return ProfessionalAudioFormatHandler()
    
    def test_soundfile_subtype_selection(self, handler):
        """Test SoundFile subtype selection"""
        # Test WAV subtypes
        settings_16 = ConversionSettings(target_format=AudioFormat.WAV, bit_depth=16)
        assert handler._get_soundfile_subtype(settings_16) == 'PCM_16'
        
        settings_24 = ConversionSettings(target_format=AudioFormat.WAV, bit_depth=24)
        assert handler._get_soundfile_subtype(settings_24) == 'PCM_24'
        
        settings_32 = ConversionSettings(target_format=AudioFormat.WAV, bit_depth=32)
        assert handler._get_soundfile_subtype(settings_32) == 'PCM_32'
        
        # Test FLAC subtype
        flac_settings = ConversionSettings(target_format=AudioFormat.FLAC)
        assert handler._get_soundfile_subtype(flac_settings) == 'PCM_16'
    
    def test_codec_settings_validation(self, handler):
        """Test codec-specific settings validation"""
        # Test MP3 settings
        mp3_settings = ConversionSettings(
            target_format=AudioFormat.MP3,
            bitrate=192,
            quality_level=QualityLevel.HIGH
        )
        
        # Should not raise any exceptions
        validated = handler._validate_conversion_settings(mp3_settings, AudioMetadata())
        assert validated.target_format == AudioFormat.MP3
        
        # Test FLAC settings (bitrate should be ignored)
        flac_settings = ConversionSettings(
            target_format=AudioFormat.FLAC,
            bitrate=192,  # Should be ignored for lossless
            quality_level=QualityLevel.LOSSLESS
        )
        
        validated = handler._validate_conversion_settings(flac_settings, AudioMetadata())
        assert validated.target_format == AudioFormat.FLAC


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])