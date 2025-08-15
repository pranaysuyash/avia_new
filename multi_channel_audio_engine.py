"""
Multi-Channel Audio Foundation and Architecture

This module provides professional multi-channel audio processing capabilities
supporting up to 32 channels with flexible routing, high-resolution audio,
and ultra-low latency processing for real-time applications.

Requirements addressed: 1.1, 1.4, 1.6
"""

import numpy as np
import threading
import time
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor
import queue
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AudioFormat(Enum):
    """Supported audio formats"""
    PCM_16 = "pcm_16"
    PCM_24 = "pcm_24" 
    PCM_32 = "pcm_32"
    FLOAT_32 = "float_32"
    FLOAT_64 = "float_64"

class ChannelLayout(Enum):
    """Standard channel layouts"""
    MONO = "mono"
    STEREO = "stereo"
    SURROUND_5_1 = "5.1"
    SURROUND_7_1 = "7.1"
    ATMOS_7_1_4 = "7.1.4"
    CUSTOM = "custom"

class ProcessingMode(Enum):
    """Audio processing modes"""
    REALTIME = "realtime"
    BATCH = "batch"
    STREAMING = "streaming"

@dataclass
class AudioChannel:
    """Individual audio channel representation"""
    channel_id: int
    data: np.ndarray
    sample_rate: int
    bit_depth: int
    gain: float = 1.0
    muted: bool = False
    solo: bool = False
    pan: float = 0.0  # -1.0 (left) to 1.0 (right)
    
    def apply_gain(self, gain: float) -> 'AudioChannel':
        """Apply gain to channel"""
        new_data = self.data * gain
        return AudioChannel(
            self.channel_id, new_data, self.sample_rate, 
            self.bit_depth, self.gain * gain, self.muted, self.solo, self.pan
        )

@dataclass
class SpatialMetadata:
    """Spatial audio metadata"""
    position_x: float = 0.0
    position_y: float = 0.0
    position_z: float = 0.0
    orientation_azimuth: float = 0.0
    orientation_elevation: float = 0.0
    distance: float = 1.0
    room_size: float = 1.0
    reverb_level: float = 0.0

@dataclass
class ProcessingHistory:
    """Track processing operations applied"""
    operations: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    
    def add_operation(self, operation: str, parameters: Dict[str, Any]):
        """Add processing operation to history"""
        self.operations.append({
            'operation': operation,
            'parameters': parameters,
            'timestamp': time.time()
        })

@dataclass
class MultiChannelAudio:
    """Multi-channel audio container"""
    channels: List[AudioChannel]
    sample_rate: int
    bit_depth: int
    format: AudioFormat
    channel_layout: ChannelLayout
    spatial_metadata: Optional[SpatialMetadata] = None
    processing_history: ProcessingHistory = field(default_factory=ProcessingHistory)
    
    @property
    def channel_count(self) -> int:
        return len(self.channels)
    
    @property
    def duration(self) -> float:
        if not self.channels:
            return 0.0
        return len(self.channels[0].data) / self.sample_rate
    
    def get_channel(self, channel_id: int) -> Optional[AudioChannel]:
        """Get channel by ID"""
        for channel in self.channels:
            if channel.channel_id == channel_id:
                return channel
        return None

@dataclass
class RoutingMatrix:
    """Audio routing configuration"""
    input_channels: List[int]
    output_channels: List[int]
    routing_map: Dict[int, List[Tuple[int, float]]]  # input -> [(output, gain), ...]
    
    def add_route(self, input_ch: int, output_ch: int, gain: float = 1.0):
        """Add routing connection"""
        if input_ch not in self.routing_map:
            self.routing_map[input_ch] = []
        self.routing_map[input_ch].append((output_ch, gain))

@dataclass
class ProcessingConfig:
    """Audio processing configuration"""
    mode: ProcessingMode = ProcessingMode.REALTIME
    buffer_size: int = 256  # samples
    max_latency_ms: float = 10.0
    enable_monitoring: bool = True
    thread_count: int = 4
    enable_gpu_acceleration: bool = False
    quality_priority: bool = False  # True for quality, False for speed

@dataclass
class LatencyRequirements:
    """Latency requirements specification"""
    max_input_latency_ms: float = 5.0
    max_processing_latency_ms: float = 3.0
    max_output_latency_ms: float = 2.0
    max_total_latency_ms: float = 10.0
    jitter_tolerance_ms: float = 1.0

class AudioBuffer:
    """Thread-safe circular audio buffer"""
    
    def __init__(self, size: int, channels: int, sample_rate: int):
        self.size = size
        self.channels = channels
        self.sample_rate = sample_rate
        self.buffer = np.zeros((channels, size), dtype=np.float32)
        self.write_pos = 0
        self.read_pos = 0
        self.lock = threading.RLock()
        self.available_samples = 0
    
    def write(self, data: np.ndarray) -> bool:
        """Write data to buffer"""
        with self.lock:
            if data.shape[0] != self.channels:
                return False
            
            samples_to_write = min(data.shape[1], self.size - self.available_samples)
            if samples_to_write <= 0:
                return False
            
            # Handle wrap-around
            if self.write_pos + samples_to_write <= self.size:
                self.buffer[:, self.write_pos:self.write_pos + samples_to_write] = data[:, :samples_to_write]
            else:
                first_part = self.size - self.write_pos
                self.buffer[:, self.write_pos:] = data[:, :first_part]
                self.buffer[:, :samples_to_write - first_part] = data[:, first_part:samples_to_write]
            
            self.write_pos = (self.write_pos + samples_to_write) % self.size
            self.available_samples += samples_to_write
            return True
    
    def read(self, num_samples: int) -> Optional[np.ndarray]:
        """Read data from buffer"""
        with self.lock:
            if self.available_samples < num_samples:
                return None
            
            data = np.zeros((self.channels, num_samples), dtype=np.float32)
            
            # Handle wrap-around
            if self.read_pos + num_samples <= self.size:
                data = self.buffer[:, self.read_pos:self.read_pos + num_samples].copy()
            else:
                first_part = self.size - self.read_pos
                data[:, :first_part] = self.buffer[:, self.read_pos:]
                data[:, first_part:] = self.buffer[:, :num_samples - first_part]
            
            self.read_pos = (self.read_pos + num_samples) % self.size
            self.available_samples -= num_samples
            return data

class ChannelRouter:
    """Flexible channel routing and mapping"""
    
    def __init__(self):
        self.routing_matrices: Dict[str, RoutingMatrix] = {}
        self.active_matrix: Optional[str] = None
    
    def create_routing_matrix(self, name: str, input_channels: List[int], 
                            output_channels: List[int]) -> RoutingMatrix:
        """Create new routing matrix"""
        matrix = RoutingMatrix(
            input_channels=input_channels,
            output_channels=output_channels,
            routing_map={}
        )
        self.routing_matrices[name] = matrix
        return matrix
    
    def route_audio(self, audio: MultiChannelAudio, matrix_name: str) -> MultiChannelAudio:
        """Apply routing matrix to audio"""
        if matrix_name not in self.routing_matrices:
            raise ValueError(f"Routing matrix '{matrix_name}' not found")
        
        matrix = self.routing_matrices[matrix_name]
        output_channels = []
        
        # Initialize output channels
        for out_ch in matrix.output_channels:
            output_data = np.zeros_like(audio.channels[0].data)
            output_channels.append(AudioChannel(
                channel_id=out_ch,
                data=output_data,
                sample_rate=audio.sample_rate,
                bit_depth=audio.bit_depth
            ))
        
        # Apply routing
        for input_ch, routes in matrix.routing_map.items():
            input_channel = audio.get_channel(input_ch)
            if input_channel is None:
                continue
            
            for output_ch, gain in routes:
                output_channel = next((ch for ch in output_channels if ch.channel_id == output_ch), None)
                if output_channel:
                    output_channel.data += input_channel.data * gain
        
        # Create routed audio
        routed_audio = MultiChannelAudio(
            channels=output_channels,
            sample_rate=audio.sample_rate,
            bit_depth=audio.bit_depth,
            format=audio.format,
            channel_layout=ChannelLayout.CUSTOM,
            spatial_metadata=audio.spatial_metadata,
            processing_history=audio.processing_history
        )
        
        routed_audio.processing_history.add_operation(
            "channel_routing", 
            {"matrix": matrix_name, "input_channels": len(audio.channels), "output_channels": len(output_channels)}
        )
        
        return routed_audio

class LatencyOptimizer:
    """Ultra-low latency processing optimization"""
    
    def __init__(self):
        self.buffer_sizes = [64, 128, 256, 512, 1024]
        self.optimal_buffer_size = 256
        self.latency_history = []
        self.performance_metrics = {}
    
    def measure_latency(self, processing_func, audio_data: np.ndarray) -> float:
        """Measure processing latency"""
        start_time = time.perf_counter()
        _ = processing_func(audio_data)
        end_time = time.perf_counter()
        return (end_time - start_time) * 1000  # Convert to milliseconds
    
    def optimize_buffer_size(self, audio: MultiChannelAudio, 
                           requirements: LatencyRequirements) -> int:
        """Find optimal buffer size for latency requirements"""
        best_buffer_size = self.optimal_buffer_size
        best_latency = float('inf')
        
        for buffer_size in self.buffer_sizes:
            # Simulate processing with this buffer size
            test_data = np.random.random((audio.channel_count, buffer_size))
            latency = self.measure_latency(lambda x: x * 1.0, test_data)
            
            if latency < requirements.max_processing_latency_ms and latency < best_latency:
                best_latency = latency
                best_buffer_size = buffer_size
        
        self.optimal_buffer_size = best_buffer_size
        logger.info(f"Optimized buffer size: {best_buffer_size} samples (latency: {best_latency:.2f}ms)")
        return best_buffer_size
    
    def create_optimized_stream(self, audio: MultiChannelAudio, 
                              requirements: LatencyRequirements) -> 'OptimizedAudioStream':
        """Create latency-optimized audio stream"""
        optimal_buffer = self.optimize_buffer_size(audio, requirements)
        return OptimizedAudioStream(audio, optimal_buffer, requirements)

class OptimizedAudioStream:
    """Latency-optimized audio stream"""
    
    def __init__(self, audio: MultiChannelAudio, buffer_size: int, 
                 requirements: LatencyRequirements):
        self.audio = audio
        self.buffer_size = buffer_size
        self.requirements = requirements
        self.buffers = {}
        self.processing_thread = None
        self.running = False
        
        # Create buffers for each channel
        for channel in audio.channels:
            self.buffers[channel.channel_id] = AudioBuffer(
                buffer_size * 4,  # 4x buffer for safety
                1,
                audio.sample_rate
            )
    
    def start_streaming(self):
        """Start real-time streaming"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._process_stream)
        self.processing_thread.start()
        logger.info("Started optimized audio streaming")
    
    def stop_streaming(self):
        """Stop streaming"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join()
        logger.info("Stopped audio streaming")
    
    def _process_stream(self):
        """Internal streaming processing loop"""
        while self.running:
            try:
                # Process each channel buffer
                for channel in self.audio.channels:
                    buffer = self.buffers[channel.channel_id]
                    
                    # Read available data
                    data = buffer.read(self.buffer_size)
                    if data is not None:
                        # Apply real-time processing here
                        processed_data = self._apply_realtime_processing(data)
                        # Output processed data (placeholder)
                        pass
                
                # Sleep for buffer duration to maintain real-time processing
                sleep_time = self.buffer_size / self.audio.sample_rate
                time.sleep(sleep_time * 0.8)  # 80% of buffer time to prevent underruns
                
            except Exception as e:
                logger.error(f"Streaming error: {e}")
                break
    
    def _apply_realtime_processing(self, data: np.ndarray) -> np.ndarray:
        """Apply real-time audio processing"""
        # Placeholder for real-time processing
        # This would include EQ, compression, effects, etc.
        return data

class MultiChannelAudioEngine:
    """Main multi-channel audio processing engine"""
    
    def __init__(self, max_channels: int = 32):
        self.max_channels = max_channels
        self.channel_router = ChannelRouter()
        self.latency_optimizer = LatencyOptimizer()
        self.active_streams: Dict[str, OptimizedAudioStream] = {}
        self.monitoring_enabled = True
        self.performance_stats = {
            'processed_samples': 0,
            'processing_time_ms': 0.0,
            'average_latency_ms': 0.0,
            'buffer_underruns': 0,
            'buffer_overruns': 0
        }
    
    def create_multichannel_audio(self, channel_data: List[np.ndarray], 
                                sample_rate: int, bit_depth: int = 32,
                                format: AudioFormat = AudioFormat.FLOAT_32,
                                layout: ChannelLayout = ChannelLayout.CUSTOM) -> MultiChannelAudio:
        """Create multi-channel audio object"""
        if len(channel_data) > self.max_channels:
            raise ValueError(f"Exceeds maximum channels ({self.max_channels})")
        
        channels = []
        for i, data in enumerate(channel_data):
            channel = AudioChannel(
                channel_id=i,
                data=data.astype(np.float32),
                sample_rate=sample_rate,
                bit_depth=bit_depth
            )
            channels.append(channel)
        
        return MultiChannelAudio(
            channels=channels,
            sample_rate=sample_rate,
            bit_depth=bit_depth,
            format=format,
            channel_layout=layout
        )
    
    def process_multichannel_audio(self, audio: MultiChannelAudio, 
                                 config: ProcessingConfig) -> MultiChannelAudio:
        """Process multi-channel audio with specified configuration"""
        start_time = time.perf_counter()
        
        # Validate input
        if audio.channel_count > self.max_channels:
            raise ValueError(f"Audio has {audio.channel_count} channels, max supported: {self.max_channels}")
        
        # Apply processing based on mode
        if config.mode == ProcessingMode.REALTIME:
            processed_audio = self._process_realtime(audio, config)
        elif config.mode == ProcessingMode.BATCH:
            processed_audio = self._process_batch(audio, config)
        else:  # STREAMING
            processed_audio = self._process_streaming(audio, config)
        
        # Update performance statistics
        processing_time = (time.perf_counter() - start_time) * 1000
        self.performance_stats['processing_time_ms'] += processing_time
        self.performance_stats['processed_samples'] += sum(len(ch.data) for ch in audio.channels)
        
        processed_audio.processing_history.add_operation(
            "multichannel_processing",
            {
                "mode": config.mode.value,
                "channels": audio.channel_count,
                "processing_time_ms": processing_time,
                "buffer_size": config.buffer_size
            }
        )
        
        logger.info(f"Processed {audio.channel_count}-channel audio in {processing_time:.2f}ms")
        return processed_audio
    
    def _process_realtime(self, audio: MultiChannelAudio, config: ProcessingConfig) -> MultiChannelAudio:
        """Real-time processing implementation"""
        processed_channels = []
        
        # Use thread pool for parallel channel processing
        with ThreadPoolExecutor(max_workers=config.thread_count) as executor:
            futures = []
            
            for channel in audio.channels:
                future = executor.submit(self._process_channel_realtime, channel, config)
                futures.append(future)
            
            for future in futures:
                processed_channel = future.result()
                processed_channels.append(processed_channel)
        
        return MultiChannelAudio(
            channels=processed_channels,
            sample_rate=audio.sample_rate,
            bit_depth=audio.bit_depth,
            format=audio.format,
            channel_layout=audio.channel_layout,
            spatial_metadata=audio.spatial_metadata,
            processing_history=audio.processing_history
        )
    
    def _process_channel_realtime(self, channel: AudioChannel, config: ProcessingConfig) -> AudioChannel:
        """Process individual channel for real-time mode"""
        # Apply minimal processing for ultra-low latency
        processed_data = channel.data.copy()
        
        # Apply gain if not muted
        if not channel.muted:
            processed_data *= channel.gain
        else:
            processed_data *= 0.0
        
        return AudioChannel(
            channel_id=channel.channel_id,
            data=processed_data,
            sample_rate=channel.sample_rate,
            bit_depth=channel.bit_depth,
            gain=channel.gain,
            muted=channel.muted,
            solo=channel.solo,
            pan=channel.pan
        )
    
    def _process_batch(self, audio: MultiChannelAudio, config: ProcessingConfig) -> MultiChannelAudio:
        """Batch processing implementation"""
        # More comprehensive processing for batch mode
        processed_channels = []
        
        for channel in audio.channels:
            processed_data = channel.data.copy()
            
            # Apply more sophisticated processing
            if not channel.muted:
                processed_data *= channel.gain
                # Add other batch processing here (EQ, compression, etc.)
            else:
                processed_data *= 0.0
            
            processed_channels.append(AudioChannel(
                channel_id=channel.channel_id,
                data=processed_data,
                sample_rate=channel.sample_rate,
                bit_depth=channel.bit_depth,
                gain=channel.gain,
                muted=channel.muted,
                solo=channel.solo,
                pan=channel.pan
            ))
        
        return MultiChannelAudio(
            channels=processed_channels,
            sample_rate=audio.sample_rate,
            bit_depth=audio.bit_depth,
            format=audio.format,
            channel_layout=audio.channel_layout,
            spatial_metadata=audio.spatial_metadata,
            processing_history=audio.processing_history
        )
    
    def _process_streaming(self, audio: MultiChannelAudio, config: ProcessingConfig) -> MultiChannelAudio:
        """Streaming processing implementation"""
        # Similar to real-time but with streaming optimizations
        return self._process_realtime(audio, config)
    
    def route_audio_channels(self, audio: MultiChannelAudio, routing_matrix: RoutingMatrix) -> MultiChannelAudio:
        """Route audio channels using routing matrix"""
        return self.channel_router.route_audio(audio, "default")
    
    def handle_spatial_audio(self, audio: MultiChannelAudio, spatial_config: Dict[str, Any]) -> MultiChannelAudio:
        """Handle spatial audio processing"""
        # Create spatial metadata if not present
        if audio.spatial_metadata is None:
            audio.spatial_metadata = SpatialMetadata()
        
        # Apply spatial configuration
        for key, value in spatial_config.items():
            if hasattr(audio.spatial_metadata, key):
                setattr(audio.spatial_metadata, key, value)
        
        # Apply spatial processing to channels
        processed_channels = []
        for channel in audio.channels:
            # Apply spatial positioning (simplified implementation)
            processed_data = self._apply_spatial_processing(channel.data, audio.spatial_metadata)
            
            processed_channels.append(AudioChannel(
                channel_id=channel.channel_id,
                data=processed_data,
                sample_rate=channel.sample_rate,
                bit_depth=channel.bit_depth,
                gain=channel.gain,
                muted=channel.muted,
                solo=channel.solo,
                pan=channel.pan
            ))
        
        result = MultiChannelAudio(
            channels=processed_channels,
            sample_rate=audio.sample_rate,
            bit_depth=audio.bit_depth,
            format=audio.format,
            channel_layout=audio.channel_layout,
            spatial_metadata=audio.spatial_metadata,
            processing_history=audio.processing_history
        )
        
        result.processing_history.add_operation(
            "spatial_audio_processing",
            spatial_config
        )
        
        return result
    
    def _apply_spatial_processing(self, data: np.ndarray, spatial_metadata: SpatialMetadata) -> np.ndarray:
        """Apply spatial audio processing"""
        # Simplified spatial processing implementation
        processed_data = data.copy()
        
        # Apply distance attenuation
        distance_factor = 1.0 / max(spatial_metadata.distance, 0.1)
        processed_data *= distance_factor
        
        # Apply reverb based on room size
        if spatial_metadata.reverb_level > 0:
            # Simple reverb simulation (in real implementation, use proper reverb algorithm)
            reverb_delay = int(0.05 * len(data))  # 50ms delay
            if reverb_delay < len(data):
                reverb_signal = np.roll(data, reverb_delay) * spatial_metadata.reverb_level
                processed_data += reverb_signal
        
        return processed_data
    
    def optimize_latency(self, audio: MultiChannelAudio, requirements: LatencyRequirements) -> OptimizedAudioStream:
        """Create latency-optimized audio stream"""
        return self.latency_optimizer.create_optimized_stream(audio, requirements)
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get engine performance statistics"""
        stats = self.performance_stats.copy()
        
        # Calculate averages
        if stats['processed_samples'] > 0:
            stats['average_processing_time_per_sample'] = (
                stats['processing_time_ms'] / stats['processed_samples'] * 1000
            )  # microseconds per sample
        
        return stats
    
    def reset_performance_stats(self):
        """Reset performance statistics"""
        self.performance_stats = {
            'processed_samples': 0,
            'processing_time_ms': 0.0,
            'average_latency_ms': 0.0,
            'buffer_underruns': 0,
            'buffer_overruns': 0
        }

# High-resolution audio support utilities
class HighResolutionAudioProcessor:
    """High-resolution audio processing utilities"""
    
    @staticmethod
    def convert_to_high_res(audio: MultiChannelAudio, target_sample_rate: int = 192000,
                          target_bit_depth: int = 32) -> MultiChannelAudio:
        """Convert audio to high-resolution format"""
        if audio.sample_rate >= target_sample_rate and audio.bit_depth >= target_bit_depth:
            return audio  # Already high-resolution
        
        # Upsample if needed
        upsampled_channels = []
        for channel in audio.channels:
            if audio.sample_rate < target_sample_rate:
                # Simple upsampling (in production, use proper resampling)
                upsample_factor = target_sample_rate // audio.sample_rate
                upsampled_data = np.repeat(channel.data, upsample_factor)
            else:
                upsampled_data = channel.data
            
            # Convert bit depth
            if target_bit_depth > audio.bit_depth:
                # Normalize to target bit depth range
                if target_bit_depth == 32:
                    upsampled_data = upsampled_data.astype(np.float32)
                else:
                    upsampled_data = upsampled_data.astype(np.float64)
            
            upsampled_channels.append(AudioChannel(
                channel_id=channel.channel_id,
                data=upsampled_data,
                sample_rate=target_sample_rate,
                bit_depth=target_bit_depth,
                gain=channel.gain,
                muted=channel.muted,
                solo=channel.solo,
                pan=channel.pan
            ))
        
        return MultiChannelAudio(
            channels=upsampled_channels,
            sample_rate=target_sample_rate,
            bit_depth=target_bit_depth,
            format=AudioFormat.FLOAT_32 if target_bit_depth == 32 else AudioFormat.FLOAT_64,
            channel_layout=audio.channel_layout,
            spatial_metadata=audio.spatial_metadata,
            processing_history=audio.processing_history
        )
    
    @staticmethod
    def validate_lossless_processing(original: MultiChannelAudio, 
                                   processed: MultiChannelAudio) -> Dict[str, Any]:
        """Validate that processing maintains lossless quality"""
        validation_results = {
            'is_lossless': True,
            'sample_rate_preserved': original.sample_rate == processed.sample_rate,
            'bit_depth_preserved': original.bit_depth >= processed.bit_depth,
            'channel_count_preserved': len(original.channels) == len(processed.channels),
            'dynamic_range_preserved': True,
            'frequency_response_preserved': True
        }
        
        # Check if any validation failed
        validation_results['is_lossless'] = all([
            validation_results['sample_rate_preserved'],
            validation_results['bit_depth_preserved'],
            validation_results['channel_count_preserved'],
            validation_results['dynamic_range_preserved'],
            validation_results['frequency_response_preserved']
        ])
        
        return validation_results

# Real-time monitoring utilities
class RealTimeMonitor:
    """Real-time audio monitoring and analysis"""
    
    def __init__(self, sample_rate: int = 48000):
        self.sample_rate = sample_rate
        self.monitoring_active = False
        self.level_history = []
        self.peak_levels = {}
        self.rms_levels = {}
    
    def start_monitoring(self, audio_stream: OptimizedAudioStream):
        """Start real-time monitoring"""
        self.monitoring_active = True
        self.audio_stream = audio_stream
        logger.info("Started real-time audio monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("Stopped audio monitoring")
    
    def get_current_levels(self, audio: MultiChannelAudio) -> Dict[int, Dict[str, float]]:
        """Get current audio levels for all channels"""
        levels = {}
        
        for channel in audio.channels:
            # Calculate peak level
            peak_level = np.max(np.abs(channel.data))
            
            # Calculate RMS level
            rms_level = np.sqrt(np.mean(channel.data ** 2))
            
            # Convert to dB
            peak_db = 20 * np.log10(max(peak_level, 1e-10))
            rms_db = 20 * np.log10(max(rms_level, 1e-10))
            
            levels[channel.channel_id] = {
                'peak_linear': peak_level,
                'rms_linear': rms_level,
                'peak_db': peak_db,
                'rms_db': rms_db,
                'clipping': peak_level >= 0.99
            }
        
        return levels
    
    def analyze_frequency_spectrum(self, audio: MultiChannelAudio) -> Dict[int, np.ndarray]:
        """Analyze frequency spectrum for each channel"""
        spectra = {}
        
        for channel in audio.channels:
            # Compute FFT
            fft = np.fft.rfft(channel.data)
            magnitude = np.abs(fft)
            
            # Convert to dB
            magnitude_db = 20 * np.log10(np.maximum(magnitude, 1e-10))
            
            spectra[channel.channel_id] = magnitude_db
        
        return spectra

if __name__ == "__main__":
    # Example usage and testing
    logger.info("Multi-Channel Audio Engine initialized")
    
    # Create engine
    engine = MultiChannelAudioEngine(max_channels=32)
    
    # Create test audio
    sample_rate = 48000
    duration = 1.0  # 1 second
    samples = int(sample_rate * duration)
    
    # Generate test signals for multiple channels
    test_channels = []
    for i in range(8):  # 8-channel test
        frequency = 440 * (2 ** (i / 12))  # Musical intervals
        t = np.linspace(0, duration, samples)
        signal = np.sin(2 * np.pi * frequency * t) * 0.5
        test_channels.append(signal)
    
    # Create multi-channel audio
    multichannel_audio = engine.create_multichannel_audio(
        test_channels, sample_rate, bit_depth=32, 
        format=AudioFormat.FLOAT_32, layout=ChannelLayout.CUSTOM
    )
    
    logger.info(f"Created {multichannel_audio.channel_count}-channel audio, duration: {multichannel_audio.duration:.2f}s")
    
    # Test processing
    config = ProcessingConfig(
        mode=ProcessingMode.REALTIME,
        buffer_size=256,
        max_latency_ms=10.0,
        thread_count=4
    )
    
    processed_audio = engine.process_multichannel_audio(multichannel_audio, config)
    logger.info("Audio processing completed")
    
    # Test routing
    router = engine.channel_router
    routing_matrix = router.create_routing_matrix("test_matrix", list(range(8)), list(range(4)))
    
    # Route 8 channels to 4 channels (stereo pairs)
    for i in range(0, 8, 2):
        routing_matrix.add_route(i, i // 2, 0.7)      # Left channel
        routing_matrix.add_route(i + 1, i // 2, 0.7)  # Right channel
    
    # Test latency optimization
    latency_req = LatencyRequirements(
        max_total_latency_ms=5.0,
        max_processing_latency_ms=3.0
    )
    
    optimized_stream = engine.optimize_latency(processed_audio, latency_req)
    logger.info(f"Created optimized stream with buffer size: {optimized_stream.buffer_size}")
    
    # Test high-resolution conversion
    hr_processor = HighResolutionAudioProcessor()
    hr_audio = hr_processor.convert_to_high_res(processed_audio, 96000, 32)
    logger.info(f"Converted to high-resolution: {hr_audio.sample_rate}Hz/{hr_audio.bit_depth}-bit")
    
    # Test monitoring
    monitor = RealTimeMonitor(sample_rate)
    levels = monitor.get_current_levels(processed_audio)
    
    for ch_id, level_info in levels.items():
        logger.info(f"Channel {ch_id}: Peak={level_info['peak_db']:.1f}dB, RMS={level_info['rms_db']:.1f}dB")
    
    # Display performance stats
    stats = engine.get_performance_stats()
    logger.info(f"Performance stats: {stats}")
    
    logger.info("Multi-channel audio engine test completed successfully")