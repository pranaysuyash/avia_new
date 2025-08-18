"""
Test Suite for Spatial Audio Processor
Comprehensive testing for spatial audio processing functionality

Requirements: 1.2, 1.5
Dependencies: spatial_audio_processor.py
"""

import pytest
import numpy as np
import tempfile
import os
import asyncio
import soundfile as sf
from unittest.mock import Mock, patch
import json

try:
    from spatial_audio_processor import (
        SpatialAudioProcessor, SpatialFormat, SpatialProcessingMode,
        AmbisonicsOrder, SpatialPosition, SpatialAudioObject,
        SpatialScene, SpatialAnalysis
    )
    SPATIAL_PROCESSOR_AVAILABLE = True
except ImportError:
    SPATIAL_PROCESSOR_AVAILABLE = False
    pytest.skip("Spatial Audio Processor not available", allow_module_level=True)


class TestSpatialAudioProcessor:
    """Test cases for SpatialAudioProcessor"""
    
    @pytest.fixture
    def processor(self):
        """Create a SpatialAudioProcessor instance for testing"""
        return SpatialAudioProcessor()
    
    @pytest.fixture
    def sample_stereo_audio(self):
        """Create sample stereo audio for testing"""
        duration = 2.0  # seconds
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create stereo test signal
        left = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
        right = np.sin(2 * np.pi * 880 * t)  # 880 Hz sine wave
        
        return np.array([left, right]), sample_rate
    
    @pytest.fixture
    def sample_5_1_audio(self):
        """Create sample 5.1 surround audio for testing"""
        duration = 2.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create 5.1 test signals
        fl = np.sin(2 * np.pi * 440 * t)   # Front Left
        fr = np.sin(2 * np.pi * 880 * t)   # Front Right
        c = np.sin(2 * np.pi * 660 * t)    # Center
        lfe = np.sin(2 * np.pi * 80 * t)   # LFE
        rl = np.sin(2 * np.pi * 330 * t)   # Rear Left
        rr = np.sin(2 * np.pi * 990 * t)   # Rear Right
        
        return np.array([fl, fr, c, lfe, rl, rr]), sample_rate
    
    @pytest.fixture
    def sample_ambisonics_foa(self):
        """Create sample First Order Ambisonics audio for testing"""
        duration = 2.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Create FOA test signals
        w = np.sin(2 * np.pi * 440 * t) * 0.707  # Omnidirectional
        x = np.sin(2 * np.pi * 440 * t) * 0.5    # Front-Back
        y = np.sin(2 * np.pi * 440 * t) * 0.3    # Left-Right
        z = np.sin(2 * np.pi * 440 * t) * 0.2    # Up-Down
        
        return np.array([w, x, y, z]), sample_rate
    
    def create_temp_audio_file(self, audio_data, sample_rate):
        """Create a temporary audio file for testing"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            sf.write(tmp_file.name, audio_data.T, sample_rate)
            return tmp_file.name
    
    def test_processor_initialization(self, processor):
        """Test processor initialization"""
        assert processor is not None
        assert hasattr(processor, 'hrtf_data')
        assert hasattr(processor, 'room_responses')
        assert hasattr(processor, 'spatial_filters')
        assert hasattr(processor, 'channel_mappings')
    
    @pytest.mark.asyncio
    async def test_stereo_format_detection(self, processor, sample_stereo_audio):
        """Test stereo format detection"""
        audio_data, sample_rate = sample_stereo_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            detected_format = await processor.detect_spatial_format(temp_file)
            assert detected_format == SpatialFormat.STEREO
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_5_1_format_detection(self, processor, sample_5_1_audio):
        """Test 5.1 surround format detection"""
        audio_data, sample_rate = sample_5_1_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            detected_format = await processor.detect_spatial_format(temp_file)
            assert detected_format == SpatialFormat.SURROUND_5_1
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_ambisonics_foa_detection(self, processor, sample_ambisonics_foa):
        """Test Ambisonics FOA format detection"""
        audio_data, sample_rate = sample_ambisonics_foa
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            detected_format = await processor.detect_spatial_format(temp_file)
            assert detected_format == SpatialFormat.AMBISONICS_FOA
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_spatial_analysis(self, processor, sample_stereo_audio):
        """Test spatial analysis functionality"""
        audio_data, sample_rate = sample_stereo_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            analysis = await processor.analyze_spatial_properties(temp_file)
            
            assert isinstance(analysis, SpatialAnalysis)
            assert analysis.format_detected == SpatialFormat.STEREO
            assert 0 <= analysis.spatial_width <= 1
            assert 0 <= analysis.spatial_depth <= 1
            assert 0 <= analysis.spatial_height <= 1
            assert 0 <= analysis.immersion_score <= 1
            assert 0 <= analysis.localization_accuracy <= 1
            assert isinstance(analysis.spatial_artifacts, list)
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_stereo_to_5_1_conversion(self, processor, sample_stereo_audio):
        """Test stereo to 5.1 conversion"""
        audio_data, sample_rate = sample_stereo_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            converted_file = await processor.convert_spatial_format(
                temp_file, SpatialFormat.SURROUND_5_1
            )
            
            # Verify converted file exists and has correct format
            assert os.path.exists(converted_file)
            
            # Load and check converted audio
            converted_audio, _ = sf.read(converted_file)
            assert converted_audio.shape[1] == 6  # 5.1 has 6 channels
            
            os.unlink(converted_file)
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_stereo_to_binaural_conversion(self, processor, sample_stereo_audio):
        """Test stereo to binaural conversion"""
        audio_data, sample_rate = sample_stereo_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            converted_file = await processor.convert_spatial_format(
                temp_file, SpatialFormat.BINAURAL
            )
            
            assert os.path.exists(converted_file)
            
            # Load and check converted audio
            converted_audio, _ = sf.read(converted_file)
            assert converted_audio.shape[1] == 2  # Binaural is still 2 channels
            
            os.unlink(converted_file)
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_5_1_to_stereo_conversion(self, processor, sample_5_1_audio):
        """Test 5.1 to stereo downmix"""
        audio_data, sample_rate = sample_5_1_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            converted_file = await processor.convert_spatial_format(
                temp_file, SpatialFormat.STEREO
            )
            
            assert os.path.exists(converted_file)
            
            # Load and check converted audio
            converted_audio, _ = sf.read(converted_file)
            assert converted_audio.shape[1] == 2  # Stereo has 2 channels
            
            os.unlink(converted_file)
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_spatial_enhancement(self, processor, sample_stereo_audio):
        """Test spatial enhancement functionality"""
        audio_data, sample_rate = sample_stereo_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        enhancement_config = {
            'width_enhancement': True,
            'depth_enhancement': False,
            'height_enhancement': False,
            'immersion_boost': True,
            'localization_improvement': False,
            'enhancement_strength': 1.2
        }
        
        try:
            enhanced_file = await processor.enhance_spatial_audio(
                temp_file, enhancement_config
            )
            
            assert os.path.exists(enhanced_file)
            
            # Load and verify enhanced audio
            enhanced_audio, _ = sf.read(enhanced_file)
            original_audio, _ = sf.read(temp_file)
            
            # Enhanced audio should have same shape as original
            assert enhanced_audio.shape == original_audio.shape
            
            # Enhanced audio should be different from original
            assert not np.array_equal(enhanced_audio, original_audio)
            
            os.unlink(enhanced_file)
            
        finally:
            os.unlink(temp_file)
    
    @pytest.mark.asyncio
    async def test_spatial_visualization(self, processor, sample_stereo_audio):
        """Test spatial visualization generation"""
        audio_data, sample_rate = sample_stereo_audio
        temp_file = self.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            viz_file = await processor.create_spatial_visualization(temp_file)
            
            assert os.path.exists(viz_file)
            
            # Load and verify visualization data
            with open(viz_file, 'r') as f:
                viz_data = json.load(f)
            
            assert 'format' in viz_data
            assert 'spatial_dimensions' in viz_data
            assert 'center_of_mass' in viz_data
            assert 'quality_metrics' in viz_data
            
            os.unlink(viz_file)
            
        finally:
            os.unlink(temp_file)
    
    def test_spatial_position(self):
        """Test SpatialPosition class"""
        position = SpatialPosition(x=0.5, y=-0.3, z=0.8)
        
        assert position.x == 0.5
        assert position.y == -0.3
        assert position.z == 0.8
        
        # Test spherical conversion
        azimuth, elevation, distance = position.to_spherical()
        assert isinstance(azimuth, float)
        assert isinstance(elevation, float)
        assert isinstance(distance, float)
    
    def test_spatial_audio_object(self):
        """Test SpatialAudioObject class"""
        audio_data = np.random.random(1000)
        position = SpatialPosition(x=0.0, y=1.0, z=0.0)
        
        obj = SpatialAudioObject(
            audio_data=audio_data,
            position=position,
            object_id="test_object",
            gain=0.8,
            spread=0.2
        )
        
        assert np.array_equal(obj.audio_data, audio_data)
        assert obj.position == position
        assert obj.object_id == "test_object"
        assert obj.gain == 0.8
        assert obj.spread == 0.2
    
    def test_channel_mappings(self, processor):
        """Test channel mapping definitions"""
        # Test stereo mapping
        stereo_mapping = processor.channel_mappings[SpatialFormat.STEREO]
        assert len(stereo_mapping) == 2
        assert 0 in stereo_mapping
        assert 1 in stereo_mapping
        
        # Test 5.1 mapping
        surround_5_1_mapping = processor.channel_mappings[SpatialFormat.SURROUND_5_1]
        assert len(surround_5_1_mapping) == 6
        
        # Test FOA mapping
        foa_mapping = processor.channel_mappings[SpatialFormat.AMBISONICS_FOA]
        assert len(foa_mapping) == 4
        assert 'W' in foa_mapping[0]  # Omnidirectional component
    
    def test_hrtf_initialization(self, processor):
        """Test HRTF data initialization"""
        assert 'sample_rate' in processor.hrtf_data
        assert 'elevations' in processor.hrtf_data
        assert 'azimuths' in processor.hrtf_data
        assert 'impulse_responses' in processor.hrtf_data
        
        # Check that HRTF responses exist
        assert len(processor.hrtf_data['impulse_responses']) > 0
    
    def test_room_responses(self, processor):
        """Test room impulse response initialization"""
        assert 'anechoic' in processor.room_responses
        assert 'small_room' in processor.room_responses
        assert 'large_hall' in processor.room_responses
        
        # Check that responses are numpy arrays
        for response in processor.room_responses.values():
            assert isinstance(response, np.ndarray)
    
    def test_spatial_filters(self, processor):
        """Test spatial filter initialization"""
        assert 'crossfeed' in processor.spatial_filters
        assert 'width_control' in processor.spatial_filters
        assert 'bass_management' in processor.spatial_filters
    
    def test_binaural_detection(self, processor):
        """Test binaural audio detection"""
        # Create test stereo audio with low correlation (binaural-like)
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Low correlation signals
        left = np.random.random(len(t))
        right = np.random.random(len(t))
        
        stereo_audio = np.array([left, right])
        
        is_binaural = processor._is_binaural(stereo_audio)
        assert isinstance(is_binaural, bool)
    
    def test_phase_issue_detection(self, processor):
        """Test phase issue detection"""
        # Create audio with phase issues
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        signal = np.sin(2 * np.pi * 440 * t)
        inverted_signal = -signal  # 180° phase shift
        
        audio_with_phase_issues = np.array([signal, inverted_signal])
        
        has_phase_issues = processor._has_phase_issues(audio_with_phase_issues)
        assert isinstance(has_phase_issues, bool)
    
    def test_channel_imbalance_detection(self, processor):
        """Test channel imbalance detection"""
        # Create audio with significant level imbalance
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        loud_channel = np.sin(2 * np.pi * 440 * t)
        quiet_channel = loud_channel * 0.1  # -20dB difference
        
        imbalanced_audio = np.array([loud_channel, quiet_channel])
        
        has_imbalance = processor._has_channel_imbalance(imbalanced_audio)
        assert isinstance(has_imbalance, bool)
    
    def test_spatial_width_calculation(self, processor):
        """Test spatial width calculation"""
        # Create stereo audio with known correlation
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Identical channels (narrow width)
        signal = np.sin(2 * np.pi * 440 * t)
        narrow_stereo = np.array([signal, signal])
        narrow_width = processor._calculate_spatial_width(narrow_stereo)
        
        # Uncorrelated channels (wide width)
        left = np.random.random(len(t))
        right = np.random.random(len(t))
        wide_stereo = np.array([left, right])
        wide_width = processor._calculate_spatial_width(wide_stereo)
        
        # Wide stereo should have greater width than narrow
        assert wide_width > narrow_width
        assert 0 <= narrow_width <= 1
        assert 0 <= wide_width <= 1
    
    def test_lfe_extraction(self, processor):
        """Test LFE channel extraction"""
        # Create test signal with low and high frequency content
        duration = 1.0
        sample_rate = 44100
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        # Mix of low and high frequencies
        low_freq = np.sin(2 * np.pi * 60 * t)   # 60 Hz
        high_freq = np.sin(2 * np.pi * 1000 * t)  # 1000 Hz
        mixed_signal = low_freq + high_freq
        
        lfe_signal = processor._extract_lfe(mixed_signal)
        
        # LFE should be same length as input
        assert len(lfe_signal) == len(mixed_signal)
        
        # LFE should have reduced high-frequency content
        lfe_fft = np.fft.fft(lfe_signal)
        original_fft = np.fft.fft(mixed_signal)
        
        # Check that high frequencies are attenuated
        freqs = np.fft.fftfreq(len(lfe_signal), 1/sample_rate)
        high_freq_mask = np.abs(freqs) > 200  # Above 200 Hz
        
        lfe_high_energy = np.mean(np.abs(lfe_fft[high_freq_mask]))
        original_high_energy = np.mean(np.abs(original_fft[high_freq_mask]))
        
        assert lfe_high_energy < original_high_energy
    
    @pytest.mark.asyncio
    async def test_cleanup(self, processor):
        """Test processor cleanup"""
        await processor.cleanup()
        # Should complete without errors


class TestSpatialFormats:
    """Test spatial format enumerations and utilities"""
    
    def test_spatial_format_enum(self):
        """Test SpatialFormat enumeration"""
        assert SpatialFormat.STEREO.value == "stereo"
        assert SpatialFormat.SURROUND_5_1.value == "5.1"
        assert SpatialFormat.SURROUND_7_1.value == "7.1"
        assert SpatialFormat.AMBISONICS_FOA.value == "ambisonics_foa"
        assert SpatialFormat.BINAURAL.value == "binaural"
    
    def test_ambisonics_order_enum(self):
        """Test AmbisonicsOrder enumeration"""
        assert AmbisonicsOrder.FIRST_ORDER.value == 1
        assert AmbisonicsOrder.SECOND_ORDER.value == 2
        assert AmbisonicsOrder.THIRD_ORDER.value == 3
        assert AmbisonicsOrder.FOURTH_ORDER.value == 4


class TestSpatialScene:
    """Test spatial scene management"""
    
    def test_spatial_scene_creation(self):
        """Test spatial scene creation"""
        # Create test objects
        obj1 = SpatialAudioObject(
            audio_data=np.random.random(1000),
            position=SpatialPosition(x=-0.5, y=0.0, z=0.0),
            object_id="left_object"
        )
        
        obj2 = SpatialAudioObject(
            audio_data=np.random.random(1000),
            position=SpatialPosition(x=0.5, y=0.0, z=0.0),
            object_id="right_object"
        )
        
        # Create scene
        scene = SpatialScene(
            objects=[obj1, obj2],
            listener_position=SpatialPosition(x=0.0, y=0.0, z=0.0),
            room_acoustics={'rt60': 0.5, 'absorption': 0.3},
            sample_rate=44100,
            duration=2.0,
            format=SpatialFormat.STEREO
        )
        
        assert len(scene.objects) == 2
        assert scene.sample_rate == 44100
        assert scene.duration == 2.0
        assert scene.format == SpatialFormat.STEREO


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])