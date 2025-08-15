"""
Test Suite for Multi-Channel Audio Engine

Comprehensive tests for multi-channel audio processing, routing,
latency optimization, and high-resolution audio support.
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch

from multi_channel_audio_engine import (
    MultiChannelAudioEngine, MultiChannelAudio, AudioChannel, RoutingMatrix,
    ProcessingConfig, LatencyRequirements, AudioFormat, ChannelLayout,
    ProcessingMode, HighResolutionAudioProcessor, RealTimeMonitor,
    SpatialMetadata, AudioBuffer, ChannelRouter, LatencyOptimizer,
    OptimizedAudioStream
)

class TestAudioChannel:
    """Test AudioChannel functionality"""
    
    def test_audio_channel_creation(self):
        """Test audio channel creation"""
        data = np.random.random(1000).astype(np.float32)
        channel = AudioChannel(
            channel_id=0,
            data=data,
            sample_rate=48000,
            bit_depth=32
        )
        
        assert channel.channel_id == 0
        assert len(channel.data) == 1000
        assert channel.sample_rate == 48000
        assert channel.bit_depth == 32
        assert channel.gain == 1.0
        assert not channel.muted
        assert not channel.solo
        assert channel.pan == 0.0
    
    def test_apply_gain(self):
        """Test gain application"""
        data = np.ones(1000, dtype=np.float32)
        channel = AudioChannel(0, data, 48000, 32)
        
        gained_channel = channel.apply_gain(0.5)
        
        assert np.allclose(gained_channel.data, 0.5)
        assert gained_channel.gain == 0.5
        assert gained_channel.channel_id == 0

class TestMultiChannelAudio:
    """Test MultiChannelAudio functionality"""
    
    def create_test_audio(self, channels=4, samples=1000):
        """Create test multi-channel audio"""
        channel_list = []
        for i in range(channels):
            data = np.random.random(samples).astype(np.float32)
            channel = AudioChannel(i, data, 48000, 32)
            channel_list.append(channel)
        
        return MultiChannelAudio(
            channels=channel_list,
            sample_rate=48000,
            bit_depth=32,
            format=AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.CUSTOM
        )
    
    def test_multichannel_audio_creation(self):
        """Test multi-channel audio creation"""
        audio = self.create_test_audio(8, 2000)
        
        assert audio.channel_count == 8
        assert audio.sample_rate == 48000
        assert audio.bit_depth == 32
        assert audio.format == AudioFormat.FLOAT_32
        assert audio.duration == pytest.approx(2000 / 48000, rel=1e-3)
    
    def test_get_channel(self):
        """Test channel retrieval"""
        audio = self.create_test_audio(4)
        
        channel = audio.get_channel(2)
        assert channel is not None
        assert channel.channel_id == 2
        
        missing_channel = audio.get_channel(10)
        assert missing_channel is None

class TestAudioBuffer:
    """Test AudioBuffer functionality"""
    
    def test_buffer_creation(self):
        """Test buffer creation"""
        buffer = AudioBuffer(1024, 2, 48000)
        
        assert buffer.size == 1024
        assert buffer.channels == 2
        assert buffer.sample_rate == 48000
        assert buffer.available_samples == 0
    
    def test_buffer_write_read(self):
        """Test buffer write and read operations"""
        buffer = AudioBuffer(1024, 2, 48000)
        
        # Write data
        test_data = np.random.random((2, 256)).astype(np.float32)
        success = buffer.write(test_data)
        assert success
        assert buffer.available_samples == 256
        
        # Read data
        read_data = buffer.read(256)
        assert read_data is not None
        assert read_data.shape == (2, 256)
        assert buffer.available_samples == 0
        
        # Verify data integrity
        assert np.allclose(test_data, read_data)
    
    def test_buffer_overflow(self):
        """Test buffer overflow handling"""
        buffer = AudioBuffer(256, 1, 48000)
        
        # Fill buffer completely
        test_data = np.random.random((1, 256)).astype(np.float32)
        success = buffer.write(test_data)
        assert success
        
        # Try to write more data (should fail)
        overflow_data = np.random.random((1, 100)).astype(np.float32)
        success = buffer.write(overflow_data)
        assert not success
    
    def test_buffer_wrap_around(self):
        """Test buffer wrap-around functionality"""
        buffer = AudioBuffer(256, 1, 48000)
        
        # Write and read multiple times to test wrap-around
        for _ in range(5):
            test_data = np.random.random((1, 100)).astype(np.float32)
            buffer.write(test_data)
            read_data = buffer.read(100)
            assert np.allclose(test_data, read_data)

class TestChannelRouter:
    """Test ChannelRouter functionality"""
    
    def test_routing_matrix_creation(self):
        """Test routing matrix creation"""
        router = ChannelRouter()
        
        matrix = router.create_routing_matrix(
            "test", 
            input_channels=[0, 1, 2, 3],
            output_channels=[0, 1]
        )
        
        assert matrix.input_channels == [0, 1, 2, 3]
        assert matrix.output_channels == [0, 1]
        assert len(matrix.routing_map) == 0
    
    def test_routing_configuration(self):
        """Test routing configuration"""
        router = ChannelRouter()
        matrix = router.create_routing_matrix("test", [0, 1, 2, 3], [0, 1])
        
        # Add routing connections
        matrix.add_route(0, 0, 0.8)  # Input 0 -> Output 0
        matrix.add_route(1, 0, 0.2)  # Input 1 -> Output 0 (mix)
        matrix.add_route(2, 1, 1.0)  # Input 2 -> Output 1
        matrix.add_route(3, 1, 0.5)  # Input 3 -> Output 1 (mix)
        
        assert len(matrix.routing_map) == 4
        assert matrix.routing_map[0] == [(0, 0.8)]
        assert matrix.routing_map[1] == [(0, 0.2)]
        assert matrix.routing_map[2] == [(1, 1.0)]
        assert matrix.routing_map[3] == [(1, 0.5)]
    
    def test_audio_routing(self):
        """Test audio routing functionality"""
        router = ChannelRouter()
        
        # Create test audio
        channels = []
        for i in range(4):
            data = np.ones(1000) * (i + 1)  # Channel i has value i+1
            channel = AudioChannel(i, data, 48000, 32)
            channels.append(channel)
        
        audio = MultiChannelAudio(
            channels=channels,
            sample_rate=48000,
            bit_depth=32,
            format=AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.CUSTOM
        )
        
        # Create routing matrix (4 -> 2 channels)
        matrix = router.create_routing_matrix("test", [0, 1, 2, 3], [0, 1])
        matrix.add_route(0, 0, 1.0)  # Ch0 -> Out0
        matrix.add_route(1, 0, 0.5)  # Ch1 -> Out0 (mixed)
        matrix.add_route(2, 1, 1.0)  # Ch2 -> Out1
        matrix.add_route(3, 1, 0.5)  # Ch3 -> Out1 (mixed)
        
        router.routing_matrices["test"] = matrix
        routed_audio = router.route_audio(audio, "test")
        
        assert routed_audio.channel_count == 2
        
        # Check routing results
        # Output 0 should be Ch0 + 0.5*Ch1 = 1 + 0.5*2 = 2
        assert np.allclose(routed_audio.channels[0].data, 2.0)
        
        # Output 1 should be Ch2 + 0.5*Ch3 = 3 + 0.5*4 = 5
        assert np.allclose(routed_audio.channels[1].data, 5.0)

class TestLatencyOptimizer:
    """Test LatencyOptimizer functionality"""
    
    def test_latency_measurement(self):
        """Test latency measurement"""
        optimizer = LatencyOptimizer()
        
        def dummy_processing(data):
            time.sleep(0.001)  # 1ms processing time
            return data
        
        test_data = np.random.random((2, 256))
        latency = optimizer.measure_latency(dummy_processing, test_data)
        
        # Should be approximately 1ms (with some tolerance)
        assert 0.5 < latency < 5.0  # Allow for system variance
    
    def test_buffer_size_optimization(self):
        """Test buffer size optimization"""
        optimizer = LatencyOptimizer()
        
        # Create test audio
        channels = [AudioChannel(0, np.random.random(1000), 48000, 32)]
        audio = MultiChannelAudio(
            channels=channels,
            sample_rate=48000,
            bit_depth=32,
            format=AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.MONO
        )
        
        requirements = LatencyRequirements(max_processing_latency_ms=5.0)
        
        optimal_buffer = optimizer.optimize_buffer_size(audio, requirements)
        
        assert optimal_buffer in optimizer.buffer_sizes
        assert optimal_buffer > 0

class TestMultiChannelAudioEngine:
    """Test MultiChannelAudioEngine functionality"""
    
    def create_test_engine(self):
        """Create test engine"""
        return MultiChannelAudioEngine(max_channels=16)
    
    def create_test_audio_data(self, channels=4, samples=1000):
        """Create test audio data"""
        return [np.random.random(samples).astype(np.float32) for _ in range(channels)]
    
    def test_engine_creation(self):
        """Test engine creation"""
        engine = self.create_test_engine()
        
        assert engine.max_channels == 16
        assert isinstance(engine.channel_router, ChannelRouter)
        assert isinstance(engine.latency_optimizer, LatencyOptimizer)
        assert engine.monitoring_enabled
    
    def test_multichannel_audio_creation(self):
        """Test multi-channel audio creation"""
        engine = self.create_test_engine()
        channel_data = self.create_test_audio_data(8, 2000)
        
        audio = engine.create_multichannel_audio(
            channel_data, 48000, 32, AudioFormat.FLOAT_32, ChannelLayout.CUSTOM
        )
        
        assert audio.channel_count == 8
        assert audio.sample_rate == 48000
        assert audio.bit_depth == 32
        assert audio.format == AudioFormat.FLOAT_32
    
    def test_channel_limit_enforcement(self):
        """Test channel limit enforcement"""
        engine = MultiChannelAudioEngine(max_channels=4)
        channel_data = self.create_test_audio_data(8)  # Exceeds limit
        
        with pytest.raises(ValueError, match="Exceeds maximum channels"):
            engine.create_multichannel_audio(channel_data, 48000)
    
    def test_realtime_processing(self):
        """Test real-time processing mode"""
        engine = self.create_test_engine()
        channel_data = self.create_test_audio_data(4, 1000)
        audio = engine.create_multichannel_audio(channel_data, 48000)
        
        config = ProcessingConfig(
            mode=ProcessingMode.REALTIME,
            buffer_size=256,
            max_latency_ms=10.0,
            thread_count=2
        )
        
        processed_audio = engine.process_multichannel_audio(audio, config)
        
        assert processed_audio.channel_count == audio.channel_count
        assert processed_audio.sample_rate == audio.sample_rate
        assert len(processed_audio.processing_history.operations) > 0
    
    def test_batch_processing(self):
        """Test batch processing mode"""
        engine = self.create_test_engine()
        channel_data = self.create_test_audio_data(4, 1000)
        audio = engine.create_multichannel_audio(channel_data, 48000)
        
        config = ProcessingConfig(
            mode=ProcessingMode.BATCH,
            buffer_size=1024,
            thread_count=4
        )
        
        processed_audio = engine.process_multichannel_audio(audio, config)
        
        assert processed_audio.channel_count == audio.channel_count
        assert "multichannel_processing" in [
            op['operation'] for op in processed_audio.processing_history.operations
        ]
    
    def test_spatial_audio_processing(self):
        """Test spatial audio processing"""
        engine = self.create_test_engine()
        channel_data = self.create_test_audio_data(2, 1000)
        audio = engine.create_multichannel_audio(channel_data, 48000)
        
        spatial_config = {
            'position_x': 1.0,
            'position_y': 0.0,
            'position_z': 0.0,
            'distance': 2.0,
            'reverb_level': 0.3
        }
        
        spatial_audio = engine.handle_spatial_audio(audio, spatial_config)
        
        assert spatial_audio.spatial_metadata is not None
        assert spatial_audio.spatial_metadata.position_x == 1.0
        assert spatial_audio.spatial_metadata.distance == 2.0
        assert spatial_audio.spatial_metadata.reverb_level == 0.3
    
    def test_latency_optimization(self):
        """Test latency optimization"""
        engine = self.create_test_engine()
        channel_data = self.create_test_audio_data(2, 1000)
        audio = engine.create_multichannel_audio(channel_data, 48000)
        
        requirements = LatencyRequirements(
            max_input_latency_ms=2.0,
            max_processing_latency_ms=3.0,
            max_output_latency_ms=2.0,
            max_total_latency_ms=7.0
        )
        
        optimized_stream = engine.optimize_latency(audio, requirements)
        
        assert isinstance(optimized_stream, OptimizedAudioStream)
        assert optimized_stream.audio == audio
        assert optimized_stream.requirements == requirements
    
    def test_performance_statistics(self):
        """Test performance statistics tracking"""
        engine = self.create_test_engine()
        channel_data = self.create_test_audio_data(4, 1000)
        audio = engine.create_multichannel_audio(channel_data, 48000)
        
        config = ProcessingConfig(mode=ProcessingMode.REALTIME)
        
        # Process audio to generate stats
        engine.process_multichannel_audio(audio, config)
        
        stats = engine.get_performance_stats()
        
        assert stats['processed_samples'] > 0
        assert stats['processing_time_ms'] > 0
        assert 'buffer_underruns' in stats
        assert 'buffer_overruns' in stats
        
        # Test stats reset
        engine.reset_performance_stats()
        reset_stats = engine.get_performance_stats()
        assert reset_stats['processed_samples'] == 0
        assert reset_stats['processing_time_ms'] == 0.0

class TestHighResolutionAudioProcessor:
    """Test HighResolutionAudioProcessor functionality"""
    
    def create_test_audio(self, sample_rate=48000, bit_depth=16):
        """Create test audio for high-res conversion"""
        data = np.random.random(1000).astype(np.float32)
        channel = AudioChannel(0, data, sample_rate, bit_depth)
        
        return MultiChannelAudio(
            channels=[channel],
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            format=AudioFormat.PCM_16 if bit_depth == 16 else AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.MONO
        )
    
    def test_high_res_conversion(self):
        """Test high-resolution conversion"""
        processor = HighResolutionAudioProcessor()
        
        # Create low-res audio
        audio = self.create_test_audio(48000, 16)
        
        # Convert to high-res
        hr_audio = processor.convert_to_high_res(audio, 96000, 32)
        
        assert hr_audio.sample_rate == 96000
        assert hr_audio.bit_depth == 32
        assert hr_audio.format == AudioFormat.FLOAT_32
        assert len(hr_audio.channels[0].data) > len(audio.channels[0].data)
    
    def test_already_high_res(self):
        """Test handling of already high-resolution audio"""
        processor = HighResolutionAudioProcessor()
        
        # Create already high-res audio
        audio = self.create_test_audio(192000, 32)
        
        # Should return same audio
        hr_audio = processor.convert_to_high_res(audio, 96000, 24)
        
        assert hr_audio == audio  # Should be unchanged
    
    def test_lossless_validation(self):
        """Test lossless processing validation"""
        processor = HighResolutionAudioProcessor()
        
        original = self.create_test_audio(48000, 24)
        processed = self.create_test_audio(48000, 24)  # Same specs
        
        validation = processor.validate_lossless_processing(original, processed)
        
        assert validation['sample_rate_preserved']
        assert validation['bit_depth_preserved']
        assert validation['channel_count_preserved']
        assert validation['is_lossless']

class TestRealTimeMonitor:
    """Test RealTimeMonitor functionality"""
    
    def create_test_audio(self):
        """Create test audio for monitoring"""
        # Create sine wave at 1kHz
        sample_rate = 48000
        duration = 1.0
        samples = int(sample_rate * duration)
        t = np.linspace(0, duration, samples)
        
        data = np.sin(2 * np.pi * 1000 * t) * 0.5  # 1kHz sine at -6dB
        channel = AudioChannel(0, data, sample_rate, 32)
        
        return MultiChannelAudio(
            channels=[channel],
            sample_rate=sample_rate,
            bit_depth=32,
            format=AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.MONO
        )
    
    def test_monitor_creation(self):
        """Test monitor creation"""
        monitor = RealTimeMonitor(48000)
        
        assert monitor.sample_rate == 48000
        assert not monitor.monitoring_active
        assert len(monitor.level_history) == 0
    
    def test_level_measurement(self):
        """Test audio level measurement"""
        monitor = RealTimeMonitor(48000)
        audio = self.create_test_audio()
        
        levels = monitor.get_current_levels(audio)
        
        assert 0 in levels  # Channel 0 should be present
        channel_levels = levels[0]
        
        assert 'peak_linear' in channel_levels
        assert 'rms_linear' in channel_levels
        assert 'peak_db' in channel_levels
        assert 'rms_db' in channel_levels
        assert 'clipping' in channel_levels
        
        # For a 0.5 amplitude sine wave, peak should be ~0.5, RMS ~0.35
        assert 0.4 < channel_levels['peak_linear'] < 0.6
        assert 0.3 < channel_levels['rms_linear'] < 0.4
        
        # Peak should be around -6dB, RMS around -9dB
        assert -8 < channel_levels['peak_db'] < -4
        assert -12 < channel_levels['rms_db'] < -8
        
        assert not channel_levels['clipping']  # Should not be clipping
    
    def test_frequency_spectrum_analysis(self):
        """Test frequency spectrum analysis"""
        monitor = RealTimeMonitor(48000)
        audio = self.create_test_audio()
        
        spectra = monitor.analyze_frequency_spectrum(audio)
        
        assert 0 in spectra  # Channel 0 should be present
        spectrum = spectra[0]
        
        assert len(spectrum) > 0
        assert isinstance(spectrum, np.ndarray)
        
        # For a 1kHz sine wave, should have peak around 1kHz bin
        # This is a simplified test - in practice would need more sophisticated analysis

class TestOptimizedAudioStream:
    """Test OptimizedAudioStream functionality"""
    
    def create_test_stream(self):
        """Create test optimized audio stream"""
        # Create test audio
        data = np.random.random(1000).astype(np.float32)
        channel = AudioChannel(0, data, 48000, 32)
        audio = MultiChannelAudio(
            channels=[channel],
            sample_rate=48000,
            bit_depth=32,
            format=AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.MONO
        )
        
        requirements = LatencyRequirements(max_total_latency_ms=10.0)
        
        return OptimizedAudioStream(audio, 256, requirements)
    
    def test_stream_creation(self):
        """Test optimized stream creation"""
        stream = self.create_test_stream()
        
        assert stream.buffer_size == 256
        assert not stream.running
        assert stream.processing_thread is None
        assert len(stream.buffers) == 1  # One channel
    
    def test_stream_lifecycle(self):
        """Test stream start/stop lifecycle"""
        stream = self.create_test_stream()
        
        # Start streaming
        stream.start_streaming()
        assert stream.running
        assert stream.processing_thread is not None
        
        # Let it run briefly
        time.sleep(0.1)
        
        # Stop streaming
        stream.stop_streaming()
        assert not stream.running

# Integration tests
class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_processing_workflow(self):
        """Test complete audio processing workflow"""
        # Create engine
        engine = MultiChannelAudioEngine(max_channels=8)
        
        # Create test audio (4 channels)
        channel_data = []
        for i in range(4):
            # Different frequency for each channel
            freq = 440 * (2 ** (i / 12))
            t = np.linspace(0, 1.0, 48000)
            signal = np.sin(2 * np.pi * freq * t) * 0.5
            channel_data.append(signal)
        
        # Create multi-channel audio
        audio = engine.create_multichannel_audio(
            channel_data, 48000, 32, AudioFormat.FLOAT_32, ChannelLayout.CUSTOM
        )
        
        # Configure processing
        config = ProcessingConfig(
            mode=ProcessingMode.REALTIME,
            buffer_size=256,
            max_latency_ms=10.0,
            thread_count=2
        )
        
        # Process audio
        processed_audio = engine.process_multichannel_audio(audio, config)
        
        # Apply spatial processing
        spatial_config = {
            'position_x': 1.0,
            'distance': 2.0,
            'reverb_level': 0.2
        }
        spatial_audio = engine.handle_spatial_audio(processed_audio, spatial_config)
        
        # Create routing matrix (4 -> 2 channels)
        router = engine.channel_router
        matrix = router.create_routing_matrix("stereo", [0, 1, 2, 3], [0, 1])
        matrix.add_route(0, 0, 0.7)  # Ch0 -> Left
        matrix.add_route(1, 0, 0.3)  # Ch1 -> Left (mixed)
        matrix.add_route(2, 1, 0.7)  # Ch2 -> Right
        matrix.add_route(3, 1, 0.3)  # Ch3 -> Right (mixed)
        
        router.routing_matrices["stereo"] = matrix
        routed_audio = router.route_audio(spatial_audio, "stereo")
        
        # Convert to high-resolution
        hr_processor = HighResolutionAudioProcessor()
        hr_audio = hr_processor.convert_to_high_res(routed_audio, 96000, 32)
        
        # Optimize for latency
        requirements = LatencyRequirements(max_total_latency_ms=5.0)
        optimized_stream = engine.optimize_latency(hr_audio, requirements)
        
        # Verify final result
        assert hr_audio.channel_count == 2  # Routed to stereo
        assert hr_audio.sample_rate == 96000  # High-resolution
        assert hr_audio.bit_depth == 32
        assert hr_audio.spatial_metadata is not None
        assert len(hr_audio.processing_history.operations) >= 3  # Multiple operations
        
        # Verify performance stats
        stats = engine.get_performance_stats()
        assert stats['processed_samples'] > 0
        assert stats['processing_time_ms'] > 0
    
    def test_monitoring_workflow(self):
        """Test real-time monitoring workflow"""
        # Create test audio with known characteristics
        sample_rate = 48000
        duration = 0.5
        samples = int(sample_rate * duration)
        
        # Create multi-channel test signals
        channels = []
        for i in range(4):
            t = np.linspace(0, duration, samples)
            # Different amplitude for each channel
            amplitude = 0.1 * (i + 1)  # 0.1, 0.2, 0.3, 0.4
            signal = np.sin(2 * np.pi * 1000 * t) * amplitude
            channel = AudioChannel(i, signal, sample_rate, 32)
            channels.append(channel)
        
        audio = MultiChannelAudio(
            channels=channels,
            sample_rate=sample_rate,
            bit_depth=32,
            format=AudioFormat.FLOAT_32,
            channel_layout=ChannelLayout.CUSTOM
        )
        
        # Monitor levels
        monitor = RealTimeMonitor(sample_rate)
        levels = monitor.get_current_levels(audio)
        
        # Verify level measurements
        for i in range(4):
            channel_levels = levels[i]
            expected_amplitude = 0.1 * (i + 1)
            
            # Peak should match amplitude
            assert abs(channel_levels['peak_linear'] - expected_amplitude) < 0.01
            
            # RMS should be amplitude / sqrt(2) for sine wave
            expected_rms = expected_amplitude / np.sqrt(2)
            assert abs(channel_levels['rms_linear'] - expected_rms) < 0.01
            
            # No clipping for these low levels
            assert not channel_levels['clipping']
        
        # Analyze frequency spectrum
        spectra = monitor.analyze_frequency_spectrum(audio)
        
        for i in range(4):
            spectrum = spectra[i]
            assert len(spectrum) > 0
            assert isinstance(spectrum, np.ndarray)

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])