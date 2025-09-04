"""
Demo: Multi-Channel Audio Engine

Demonstration of professional multi-channel audio processing capabilities
including channel routing, spatial audio, latency optimization, and
high-resolution audio support.
"""

import numpy as np
import matplotlib.pyplot as plt
import time
import json
from typing import List, Dict, Any

from multi_channel_audio_engine import (
    MultiChannelAudioEngine, MultiChannelAudio, AudioChannel, RoutingMatrix,
    ProcessingConfig, LatencyRequirements, AudioFormat, ChannelLayout,
    ProcessingMode, HighResolutionAudioProcessor, RealTimeMonitor,
    SpatialMetadata
)

def create_demo_audio_signals(sample_rate: int = 48000, duration: float = 2.0) -> List[np.ndarray]:
    """Create diverse demo audio signals for testing"""
    samples = int(sample_rate * duration)
    t = np.linspace(0, duration, samples)
    
    signals = []
    
    # Channel 1: Pure sine wave (440 Hz - A4)
    signals.append(np.sin(2 * np.pi * 440 * t) * 0.3)
    
    # Channel 2: Major third (554.37 Hz - C#5)
    signals.append(np.sin(2 * np.pi * 554.37 * t) * 0.3)
    
    # Channel 3: Perfect fifth (659.25 Hz - E5)
    signals.append(np.sin(2 * np.pi * 659.25 * t) * 0.3)
    
    # Channel 4: Octave (880 Hz - A5)
    signals.append(np.sin(2 * np.pi * 880 * t) * 0.3)
    
    # Channel 5: Frequency sweep (20 Hz to 2 kHz)
    f_start, f_end = 20, 2000
    freq_sweep = f_start + (f_end - f_start) * t / duration
    signals.append(np.sin(2 * np.pi * freq_sweep * t) * 0.2)
    
    # Channel 6: White noise
    signals.append(np.random.normal(0, 0.1, samples))
    
    # Channel 7: Amplitude modulated sine (100 Hz carrier, 5 Hz modulation)
    carrier = np.sin(2 * np.pi * 100 * t)
    modulation = 0.5 * (1 + np.sin(2 * np.pi * 5 * t))
    signals.append(carrier * modulation * 0.2)
    
    # Channel 8: Chirp signal (exponential frequency sweep)
    chirp = np.sin(2 * np.pi * 100 * (2 ** (t / duration)) * t) * 0.2
    signals.append(chirp)
    
    return signals

def demonstrate_basic_functionality():
    """Demonstrate basic multi-channel audio engine functionality"""
    print("=" * 60)
    print("MULTI-CHANNEL AUDIO ENGINE DEMONSTRATION")
    print("=" * 60)
    
    # Create engine
    print("\n1. Creating Multi-Channel Audio Engine...")
    engine = MultiChannelAudioEngine(max_channels=32)
    print(f"   ✓ Engine created with {engine.max_channels} maximum channels")
    
    # Create test audio
    print("\n2. Generating 8-Channel Test Audio...")
    sample_rate = 48000
    duration = 2.0
    channel_data = create_demo_audio_signals(sample_rate, duration)
    
    audio = engine.create_multichannel_audio(
        channel_data, sample_rate, bit_depth=32,
        format=AudioFormat.FLOAT_32, layout=ChannelLayout.CUSTOM
    )
    
    print(f"   ✓ Created {audio.channel_count}-channel audio")
    print(f"   ✓ Sample rate: {audio.sample_rate} Hz")
    print(f"   ✓ Bit depth: {audio.bit_depth}-bit")
    print(f"   ✓ Duration: {audio.duration:.2f} seconds")
    print(f"   ✓ Format: {audio.format.value}")
    
    return engine, audio

def demonstrate_channel_controls(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate individual channel controls"""
    print("\n3. Demonstrating Channel Controls...")
    
    # Modify channel properties
    modified_channels = []
    for i, channel in enumerate(audio.channels):
        # Apply different settings to each channel
        if i == 0:
            # Channel 1: Normal
            gain, muted, solo, pan = 1.0, False, False, -0.5
        elif i == 1:
            # Channel 2: Reduced gain
            gain, muted, solo, pan = 0.5, False, False, 0.5
        elif i == 2:
            # Channel 3: Muted
            gain, muted, solo, pan = 1.0, True, False, 0.0
        elif i == 3:
            # Channel 4: Solo
            gain, muted, solo, pan = 1.0, False, True, 0.0
        else:
            # Other channels: Various settings
            gain = 0.7 + 0.3 * np.sin(i)
            muted = False
            solo = False
            pan = np.sin(i * 0.5)
        
        modified_channel = AudioChannel(
            channel_id=channel.channel_id,
            data=channel.data,
            sample_rate=channel.sample_rate,
            bit_depth=channel.bit_depth,
            gain=gain,
            muted=muted,
            solo=solo,
            pan=pan
        )
        modified_channels.append(modified_channel)
        
        print(f"   Channel {i+1}: Gain={gain:.2f}, Muted={muted}, Solo={solo}, Pan={pan:.2f}")
    
    # Create modified audio
    modified_audio = MultiChannelAudio(
        channels=modified_channels,
        sample_rate=audio.sample_rate,
        bit_depth=audio.bit_depth,
        format=audio.format,
        channel_layout=audio.channel_layout,
        spatial_metadata=audio.spatial_metadata,
        processing_history=audio.processing_history
    )
    
    print("   ✓ Channel controls applied")
    return modified_audio

def demonstrate_channel_routing(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate flexible channel routing"""
    print("\n4. Demonstrating Channel Routing...")
    
    router = engine.channel_router
    
    # Create routing matrix: 8 channels -> 4 channels (quad setup)
    matrix = router.create_routing_matrix(
        "quad_mix",
        input_channels=list(range(8)),
        output_channels=list(range(4))
    )
    
    # Configure routing
    # Front Left (Output 0): Channels 1, 2
    matrix.add_route(0, 0, 0.7)  # Channel 1 -> Front Left
    matrix.add_route(1, 0, 0.3)  # Channel 2 -> Front Left (mixed)
    
    # Front Right (Output 1): Channels 3, 4
    matrix.add_route(2, 1, 0.7)  # Channel 3 -> Front Right
    matrix.add_route(3, 1, 0.3)  # Channel 4 -> Front Right (mixed)
    
    # Rear Left (Output 2): Channels 5, 6
    matrix.add_route(4, 2, 0.8)  # Channel 5 -> Rear Left
    matrix.add_route(5, 2, 0.2)  # Channel 6 -> Rear Left (mixed)
    
    # Rear Right (Output 3): Channels 7, 8
    matrix.add_route(6, 3, 0.8)  # Channel 7 -> Rear Right
    matrix.add_route(7, 3, 0.2)  # Channel 8 -> Rear Right (mixed)
    
    print("   Routing Configuration:")
    print("   Front Left  ← Ch1(0.7) + Ch2(0.3)")
    print("   Front Right ← Ch3(0.7) + Ch4(0.3)")
    print("   Rear Left   ← Ch5(0.8) + Ch6(0.2)")
    print("   Rear Right  ← Ch7(0.8) + Ch8(0.2)")
    
    # Apply routing
    router.routing_matrices["quad_mix"] = matrix
    routed_audio = router.route_audio(audio, "quad_mix")
    
    print(f"   ✓ Routed from {audio.channel_count} to {routed_audio.channel_count} channels")
    return routed_audio

def demonstrate_processing_modes(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate different processing modes"""
    print("\n5. Demonstrating Processing Modes...")
    
    processing_results = {}
    
    # Real-time processing
    print("   Testing Real-time Processing...")
    realtime_config = ProcessingConfig(
        mode=ProcessingMode.REALTIME,
        buffer_size=256,
        max_latency_ms=5.0,
        thread_count=4
    )
    
    start_time = time.perf_counter()
    realtime_audio = engine.process_multichannel_audio(audio, realtime_config)
    realtime_time = (time.perf_counter() - start_time) * 1000
    
    processing_results['realtime'] = {
        'processing_time_ms': realtime_time,
        'buffer_size': realtime_config.buffer_size,
        'latency_target_ms': realtime_config.max_latency_ms
    }
    
    print(f"   ✓ Real-time: {realtime_time:.2f}ms processing time")
    
    # Batch processing
    print("   Testing Batch Processing...")
    batch_config = ProcessingConfig(
        mode=ProcessingMode.BATCH,
        buffer_size=1024,
        thread_count=8,
        quality_priority=True
    )
    
    start_time = time.perf_counter()
    batch_audio = engine.process_multichannel_audio(audio, batch_config)
    batch_time = (time.perf_counter() - start_time) * 1000
    
    processing_results['batch'] = {
        'processing_time_ms': batch_time,
        'buffer_size': batch_config.buffer_size,
        'quality_priority': batch_config.quality_priority
    }
    
    print(f"   ✓ Batch: {batch_time:.2f}ms processing time")
    
    # Streaming processing
    print("   Testing Streaming Processing...")
    streaming_config = ProcessingConfig(
        mode=ProcessingMode.STREAMING,
        buffer_size=512,
        thread_count=6
    )
    
    start_time = time.perf_counter()
    streaming_audio = engine.process_multichannel_audio(audio, streaming_config)
    streaming_time = (time.perf_counter() - start_time) * 1000
    
    processing_results['streaming'] = {
        'processing_time_ms': streaming_time,
        'buffer_size': streaming_config.buffer_size
    }
    
    print(f"   ✓ Streaming: {streaming_time:.2f}ms processing time")
    
    # Compare results
    print("\n   Processing Mode Comparison:")
    for mode, results in processing_results.items():
        print(f"   {mode.capitalize():>10}: {results['processing_time_ms']:>6.2f}ms")
    
    return realtime_audio

def demonstrate_spatial_audio(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate spatial audio processing"""
    print("\n6. Demonstrating Spatial Audio Processing...")
    
    # Configure spatial audio parameters
    spatial_configs = [
        {
            'name': 'Center Stage',
            'config': {
                'position_x': 0.0,
                'position_y': 0.0,
                'position_z': 0.0,
                'distance': 1.0,
                'reverb_level': 0.1
            }
        },
        {
            'name': 'Stage Left',
            'config': {
                'position_x': -3.0,
                'position_y': 2.0,
                'position_z': 0.0,
                'distance': 4.0,
                'reverb_level': 0.3
            }
        },
        {
            'name': 'Distant Right',
            'config': {
                'position_x': 5.0,
                'position_y': -1.0,
                'position_z': 2.0,
                'distance': 8.0,
                'reverb_level': 0.5
            }
        }
    ]
    
    spatial_results = []
    
    for spatial_setup in spatial_configs:
        name = spatial_setup['name']
        config = spatial_setup['config']
        
        print(f"   Processing '{name}' spatial configuration...")
        print(f"     Position: ({config['position_x']:.1f}, {config['position_y']:.1f}, {config['position_z']:.1f})")
        print(f"     Distance: {config['distance']:.1f}m")
        print(f"     Reverb: {config['reverb_level']:.1f}")
        
        spatial_audio = engine.handle_spatial_audio(audio, config)
        
        # Analyze spatial processing effects
        original_rms = np.sqrt(np.mean(audio.channels[0].data ** 2))
        processed_rms = np.sqrt(np.mean(spatial_audio.channels[0].data ** 2))
        
        spatial_results.append({
            'name': name,
            'original_rms': original_rms,
            'processed_rms': processed_rms,
            'attenuation_db': 20 * np.log10(processed_rms / original_rms) if processed_rms > 0 else -60
        })
        
        print(f"     ✓ Attenuation: {spatial_results[-1]['attenuation_db']:.1f} dB")
    
    print("\n   Spatial Processing Results:")
    for result in spatial_results:
        print(f"   {result['name']:>12}: {result['attenuation_db']:>6.1f} dB attenuation")
    
    return spatial_audio

def demonstrate_latency_optimization(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate ultra-low latency optimization"""
    print("\n7. Demonstrating Latency Optimization...")
    
    # Test different latency requirements
    latency_scenarios = [
        {
            'name': 'Live Performance',
            'requirements': LatencyRequirements(
                max_input_latency_ms=1.0,
                max_processing_latency_ms=2.0,
                max_output_latency_ms=1.0,
                max_total_latency_ms=4.0,
                jitter_tolerance_ms=0.5
            )
        },
        {
            'name': 'Studio Monitoring',
            'requirements': LatencyRequirements(
                max_input_latency_ms=2.0,
                max_processing_latency_ms=5.0,
                max_output_latency_ms=3.0,
                max_total_latency_ms=10.0,
                jitter_tolerance_ms=1.0
            )
        },
        {
            'name': 'Broadcast',
            'requirements': LatencyRequirements(
                max_input_latency_ms=5.0,
                max_processing_latency_ms=10.0,
                max_output_latency_ms=5.0,
                max_total_latency_ms=20.0,
                jitter_tolerance_ms=2.0
            )
        }
    ]
    
    optimization_results = []
    
    for scenario in latency_scenarios:
        name = scenario['name']
        requirements = scenario['requirements']
        
        print(f"   Optimizing for '{name}' scenario...")
        print(f"     Target total latency: {requirements.max_total_latency_ms:.1f}ms")
        
        # Create optimized stream
        optimized_stream = engine.optimize_latency(audio, requirements)
        
        # Calculate theoretical latency based on buffer size
        buffer_latency_ms = (optimized_stream.buffer_size / audio.sample_rate) * 1000
        
        optimization_results.append({
            'name': name,
            'target_latency_ms': requirements.max_total_latency_ms,
            'buffer_size': optimized_stream.buffer_size,
            'buffer_latency_ms': buffer_latency_ms,
            'meets_requirements': buffer_latency_ms <= requirements.max_processing_latency_ms
        })
        
        print(f"     ✓ Optimized buffer size: {optimized_stream.buffer_size} samples")
        print(f"     ✓ Buffer latency: {buffer_latency_ms:.2f}ms")
        print(f"     ✓ Meets requirements: {'Yes' if optimization_results[-1]['meets_requirements'] else 'No'}")
    
    print("\n   Latency Optimization Summary:")
    for result in optimization_results:
        status = "✓" if result['meets_requirements'] else "✗"
        print(f"   {result['name']:>16}: {result['buffer_latency_ms']:>6.2f}ms {status}")
    
    return optimized_stream

def demonstrate_high_resolution_audio(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate high-resolution audio processing"""
    print("\n8. Demonstrating High-Resolution Audio...")
    
    hr_processor = HighResolutionAudioProcessor()
    
    # Show current audio specs
    print(f"   Original audio: {audio.sample_rate}Hz/{audio.bit_depth}-bit")
    
    # Test different high-resolution targets
    hr_targets = [
        {'sample_rate': 96000, 'bit_depth': 32, 'name': 'Studio Quality'},
        {'sample_rate': 192000, 'bit_depth': 32, 'name': 'Mastering Quality'},
        {'sample_rate': 384000, 'bit_depth': 32, 'name': 'Ultra High-Res'}
    ]
    
    hr_results = []
    
    for target in hr_targets:
        name = target['name']
        target_sr = target['sample_rate']
        target_bd = target['bit_depth']
        
        print(f"   Converting to {name} ({target_sr}Hz/{target_bd}-bit)...")
        
        start_time = time.perf_counter()
        hr_audio = hr_processor.convert_to_high_res(audio, target_sr, target_bd)
        conversion_time = (time.perf_counter() - start_time) * 1000
        
        # Validate lossless processing
        validation = hr_processor.validate_lossless_processing(audio, hr_audio)
        
        # Calculate size increase
        original_samples = sum(len(ch.data) for ch in audio.channels)
        hr_samples = sum(len(ch.data) for ch in hr_audio.channels)
        size_ratio = hr_samples / original_samples
        
        hr_results.append({
            'name': name,
            'sample_rate': hr_audio.sample_rate,
            'bit_depth': hr_audio.bit_depth,
            'conversion_time_ms': conversion_time,
            'size_ratio': size_ratio,
            'is_lossless': validation['is_lossless']
        })
        
        print(f"     ✓ Converted in {conversion_time:.2f}ms")
        print(f"     ✓ Size increase: {size_ratio:.1f}x")
        print(f"     ✓ Lossless: {'Yes' if validation['is_lossless'] else 'No'}")
    
    print("\n   High-Resolution Conversion Summary:")
    for result in hr_results:
        print(f"   {result['name']:>16}: {result['sample_rate']:>6}Hz/{result['bit_depth']:>2}bit "
              f"({result['conversion_time_ms']:>6.2f}ms)")
    
    return hr_audio

def demonstrate_real_time_monitoring(engine: MultiChannelAudioEngine, audio: MultiChannelAudio):
    """Demonstrate real-time audio monitoring"""
    print("\n9. Demonstrating Real-Time Monitoring...")
    
    monitor = RealTimeMonitor(audio.sample_rate)
    
    # Analyze audio levels
    print("   Analyzing audio levels...")
    levels = monitor.get_current_levels(audio)
    
    print("   Channel Level Analysis:")
    print("   Ch#  Peak(dB)  RMS(dB)   Peak(Lin)  RMS(Lin)   Clipping")
    print("   " + "-" * 55)
    
    for ch_id, level_info in levels.items():
        clipping_status = "YES" if level_info['clipping'] else "NO"
        print(f"   {ch_id+1:>2}   {level_info['peak_db']:>7.1f}  {level_info['rms_db']:>7.1f}   "
              f"{level_info['peak_linear']:>8.3f}  {level_info['rms_linear']:>7.3f}   {clipping_status:>8}")
    
    # Analyze frequency spectrum
    print("\n   Analyzing frequency spectrum...")
    spectra = monitor.analyze_frequency_spectrum(audio)
    
    # Find dominant frequencies for each channel
    print("   Dominant Frequency Analysis:")
    for ch_id, spectrum in spectra.items():
        freqs = np.fft.rfftfreq(len(audio.channels[ch_id].data), 1/audio.sample_rate)
        
        # Find peak frequency
        peak_idx = np.argmax(spectrum)
        peak_freq = freqs[peak_idx]
        peak_magnitude = spectrum[peak_idx]
        
        print(f"   Channel {ch_id+1}: Peak at {peak_freq:.1f} Hz ({peak_magnitude:.1f} dB)")
    
    # Monitor performance
    print("\n   Performance Monitoring:")
    stats = engine.get_performance_stats()
    
    if stats['processed_samples'] > 0:
        print(f"   Processed samples: {stats['processed_samples']:,}")
        print(f"   Total processing time: {stats['processing_time_ms']:.2f} ms")
        print(f"   Average time per sample: {stats['processing_time_ms']/stats['processed_samples']*1000:.3f} μs")
        print(f"   Buffer underruns: {stats['buffer_underruns']}")
        print(f"   Buffer overruns: {stats['buffer_overruns']}")
    else:
        print("   No processing statistics available yet")
    
    return levels, spectra

def demonstrate_processing_history(audio: MultiChannelAudio):
    """Demonstrate processing history tracking"""
    print("\n10. Processing History Analysis...")
    
    if not audio.processing_history.operations:
        print("   No processing operations recorded")
        return
    
    print("   Processing Operations:")
    print("   #  Operation                    Timestamp           Parameters")
    print("   " + "-" * 70)
    
    for i, operation in enumerate(audio.processing_history.operations):
        timestamp = time.strftime('%H:%M:%S', time.localtime(operation['timestamp']))
        op_name = operation['operation']
        params = json.dumps(operation['parameters'], separators=(',', ':'))[:30] + "..."
        
        print(f"   {i+1:>2} {op_name:<25} {timestamp} {params}")
    
    print(f"\n   Total operations: {len(audio.processing_history.operations)}")

def create_visualization_plots(audio: MultiChannelAudio, levels: Dict, spectra: Dict):
    """Create visualization plots for the demo"""
    print("\n11. Creating Visualization Plots...")
    
    try:
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Multi-Channel Audio Analysis', fontsize=16)
        
        # Plot 1: Waveforms (first 4 channels)
        ax1 = axes[0, 0]
        time_axis = np.linspace(0, audio.duration, len(audio.channels[0].data))
        
        for i, channel in enumerate(audio.channels[:4]):
            ax1.plot(time_axis, channel.data, label=f'Channel {i+1}', alpha=0.7)
        
        ax1.set_title('Channel Waveforms')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Amplitude')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Level meters
        ax2 = axes[0, 1]
        channels = list(levels.keys())
        peak_levels = [levels[ch]['peak_db'] for ch in channels]
        rms_levels = [levels[ch]['rms_db'] for ch in channels]
        
        x = np.arange(len(channels))
        width = 0.35
        
        ax2.bar(x - width/2, peak_levels, width, label='Peak', alpha=0.8)
        ax2.bar(x + width/2, rms_levels, width, label='RMS', alpha=0.8)
        
        ax2.set_title('Audio Levels')
        ax2.set_xlabel('Channel')
        ax2.set_ylabel('Level (dB)')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f'Ch{ch+1}' for ch in channels])
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='r', linestyle='--', alpha=0.5, label='0 dB')
        
        # Plot 3: Frequency spectrum (first channel)
        ax3 = axes[1, 0]
        if 0 in spectra:
            freqs = np.fft.rfftfreq(len(audio.channels[0].data), 1/audio.sample_rate)
            spectrum = spectra[0]
            
            ax3.semilogx(freqs[1:], spectrum[1:])  # Skip DC component
            ax3.set_title('Frequency Spectrum (Channel 1)')
            ax3.set_xlabel('Frequency (Hz)')
            ax3.set_ylabel('Magnitude (dB)')
            ax3.grid(True, alpha=0.3)
            ax3.set_xlim(20, audio.sample_rate/2)
        
        # Plot 4: Channel correlation matrix
        ax4 = axes[1, 1]
        
        # Calculate correlation matrix
        channel_data = np.array([ch.data for ch in audio.channels[:6]])  # First 6 channels
        correlation_matrix = np.corrcoef(channel_data)
        
        im = ax4.imshow(correlation_matrix, cmap='coolwarm', vmin=-1, vmax=1)
        ax4.set_title('Channel Correlation Matrix')
        ax4.set_xlabel('Channel')
        ax4.set_ylabel('Channel')
        
        # Add colorbar
        plt.colorbar(im, ax=ax4)
        
        # Add correlation values as text
        for i in range(len(correlation_matrix)):
            for j in range(len(correlation_matrix)):
                text = ax4.text(j, i, f'{correlation_matrix[i, j]:.2f}',
                              ha="center", va="center", color="black", fontsize=8)
        
        plt.tight_layout()
        plt.savefig('multi_channel_audio_analysis.png', dpi=300, bbox_inches='tight')
        print("   ✓ Visualization saved as 'multi_channel_audio_analysis.png'")
        
    except ImportError:
        print("   ⚠ Matplotlib not available - skipping visualization")
    except Exception as e:
        print(f"   ⚠ Visualization error: {e}")

def main():
    """Main demonstration function"""
    print("Starting Multi-Channel Audio Engine Demonstration...")
    
    try:
        # Basic functionality
        engine, audio = demonstrate_basic_functionality()
        
        # Channel controls
        audio = demonstrate_channel_controls(engine, audio)
        
        # Channel routing
        routed_audio = demonstrate_channel_routing(engine, audio)
        
        # Processing modes
        processed_audio = demonstrate_processing_modes(engine, routed_audio)
        
        # Spatial audio
        spatial_audio = demonstrate_spatial_audio(engine, processed_audio)
        
        # Latency optimization
        optimized_stream = demonstrate_latency_optimization(engine, spatial_audio)
        
        # High-resolution audio
        hr_audio = demonstrate_high_resolution_audio(engine, spatial_audio)
        
        # Real-time monitoring
        levels, spectra = demonstrate_real_time_monitoring(engine, hr_audio)
        
        # Processing history
        demonstrate_processing_history(hr_audio)
        
        # Create visualizations
        create_visualization_plots(hr_audio, levels, spectra)
        
        # Final summary
        print("\n" + "=" * 60)
        print("DEMONSTRATION COMPLETE")
        print("=" * 60)
        
        final_stats = engine.get_performance_stats()
        print(f"Final Performance Statistics:")
        print(f"  Total samples processed: {final_stats['processed_samples']:,}")
        print(f"  Total processing time: {final_stats['processing_time_ms']:.2f} ms")
        print(f"  Buffer underruns: {final_stats['buffer_underruns']}")
        print(f"  Buffer overruns: {final_stats['buffer_overruns']}")
        
        print(f"\nFinal Audio Specifications:")
        print(f"  Channels: {hr_audio.channel_count}")
        print(f"  Sample Rate: {hr_audio.sample_rate} Hz")
        print(f"  Bit Depth: {hr_audio.bit_depth}-bit")
        print(f"  Duration: {hr_audio.duration:.2f} seconds")
        print(f"  Processing Operations: {len(hr_audio.processing_history.operations)}")
        
        if hr_audio.spatial_metadata:
            print(f"  Spatial Processing: Enabled")
            print(f"    Position: ({hr_audio.spatial_metadata.position_x:.1f}, "
                  f"{hr_audio.spatial_metadata.position_y:.1f}, "
                  f"{hr_audio.spatial_metadata.position_z:.1f})")
            print(f"    Distance: {hr_audio.spatial_metadata.distance:.1f}m")
            print(f"    Reverb Level: {hr_audio.spatial_metadata.reverb_level:.1f}")
        
        print("\n✓ Multi-Channel Audio Engine demonstration completed successfully!")
        
    except Exception as e:
        print(f"\n✗ Demonstration failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()