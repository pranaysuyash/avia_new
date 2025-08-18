"""
Demo Script for Spatial Audio Processor
Demonstrates spatial audio processing capabilities with sample audio

Requirements: 1.2, 1.5
Dependencies: spatial_audio_processor.py
"""

import asyncio
import numpy as np
import soundfile as sf
import tempfile
import os
import json
from pathlib import Path
import logging

try:
    from spatial_audio_processor import (
        SpatialAudioProcessor, SpatialFormat, SpatialProcessingMode,
        SpatialPosition, SpatialAudioObject, SpatialScene
    )
    SPATIAL_PROCESSOR_AVAILABLE = True
except ImportError:
    SPATIAL_PROCESSOR_AVAILABLE = False
    print("❌ Spatial Audio Processor not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_audio_files():
    """Create sample audio files for demonstration"""
    print("🎵 Creating sample audio files...")
    
    sample_rate = 44100
    duration = 3.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create different test signals
    files_created = {}
    
    # 1. Stereo test file
    print("  Creating stereo test file...")
    left = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.5)  # Decaying 440 Hz
    right = np.sin(2 * np.pi * 880 * t) * np.exp(-t * 0.3)  # Decaying 880 Hz
    stereo_audio = np.array([left, right])
    
    stereo_file = tempfile.NamedTemporaryFile(delete=False, suffix='_stereo.wav')
    sf.write(stereo_file.name, stereo_audio.T, sample_rate)
    files_created['stereo'] = stereo_file.name
    
    # 2. 5.1 Surround test file
    print("  Creating 5.1 surround test file...")
    fl = np.sin(2 * np.pi * 440 * t) * 0.8  # Front Left
    fr = np.sin(2 * np.pi * 880 * t) * 0.8  # Front Right
    c = np.sin(2 * np.pi * 660 * t) * 0.6   # Center
    lfe = np.sin(2 * np.pi * 80 * t) * 0.5  # LFE
    rl = np.sin(2 * np.pi * 330 * t) * 0.4  # Rear Left
    rr = np.sin(2 * np.pi * 990 * t) * 0.4  # Rear Right
    
    surround_5_1 = np.array([fl, fr, c, lfe, rl, rr])
    
    surround_file = tempfile.NamedTemporaryFile(delete=False, suffix='_5_1.wav')
    sf.write(surround_file.name, surround_5_1.T, sample_rate)
    files_created['5.1'] = surround_file.name
    
    # 3. Ambisonics FOA test file
    print("  Creating Ambisonics FOA test file...")
    # Simulate a sound source moving in a circle
    w = np.ones_like(t) * 0.707  # Omnidirectional component
    x = np.sin(2 * np.pi * 0.5 * t) * 0.5  # Front-back movement
    y = np.cos(2 * np.pi * 0.5 * t) * 0.5  # Left-right movement
    z = np.sin(2 * np.pi * 0.25 * t) * 0.3  # Up-down movement
    
    # Add audio content
    audio_signal = np.sin(2 * np.pi * 440 * t) * np.exp(-t * 0.2)
    w *= audio_signal
    x *= audio_signal
    y *= audio_signal
    z *= audio_signal
    
    ambisonics_foa = np.array([w, x, y, z])
    
    ambisonics_file = tempfile.NamedTemporaryFile(delete=False, suffix='_ambisonics_foa.wav')
    sf.write(ambisonics_file.name, ambisonics_foa.T, sample_rate)
    files_created['ambisonics_foa'] = ambisonics_file.name
    
    # 4. Wide stereo test file (for width analysis)
    print("  Creating wide stereo test file...")
    # Create decorrelated signals for wide stereo effect
    left_wide = np.random.random(len(t)) * 0.3 + np.sin(2 * np.pi * 440 * t) * 0.7
    right_wide = np.random.random(len(t)) * 0.3 + np.sin(2 * np.pi * 440 * t) * 0.7
    
    # Apply different delays for width
    delay_samples = int(0.02 * sample_rate)  # 20ms delay
    left_wide = np.concatenate([np.zeros(delay_samples), left_wide[:-delay_samples]])
    
    wide_stereo = np.array([left_wide, right_wide])
    
    wide_file = tempfile.NamedTemporaryFile(delete=False, suffix='_wide_stereo.wav')
    sf.write(wide_file.name, wide_stereo.T, sample_rate)
    files_created['wide_stereo'] = wide_file.name
    
    print(f"✅ Created {len(files_created)} sample audio files")
    return files_created


async def demo_format_detection(processor, sample_files):
    """Demonstrate spatial format detection"""
    print("\n🔍 SPATIAL FORMAT DETECTION DEMO")
    print("=" * 50)
    
    for file_type, file_path in sample_files.items():
        print(f"\nAnalyzing {file_type} file...")
        
        try:
            detected_format = await processor.detect_spatial_format(file_path)
            print(f"  Detected format: {detected_format.value.upper()}")
            
            # Get file info
            info = sf.info(file_path)
            print(f"  Channels: {info.channels}")
            print(f"  Sample rate: {info.samplerate} Hz")
            print(f"  Duration: {info.duration:.2f} seconds")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def demo_spatial_analysis(processor, sample_files):
    """Demonstrate spatial analysis"""
    print("\n📊 SPATIAL ANALYSIS DEMO")
    print("=" * 50)
    
    for file_type, file_path in sample_files.items():
        print(f"\nAnalyzing spatial properties of {file_type}...")
        
        try:
            analysis = await processor.analyze_spatial_properties(file_path)
            
            print(f"  Format: {analysis.format_detected.value.upper()}")
            print(f"  Spatial Width: {analysis.spatial_width:.3f}")
            print(f"  Spatial Depth: {analysis.spatial_depth:.3f}")
            print(f"  Spatial Height: {analysis.spatial_height:.3f}")
            print(f"  Immersion Score: {analysis.immersion_score:.3f}")
            print(f"  Localization Accuracy: {analysis.localization_accuracy:.3f}")
            
            # Center of mass
            com = analysis.center_of_mass
            print(f"  Center of Mass: X={com.x:.3f}, Y={com.y:.3f}, Z={com.z:.3f}")
            
            # Artifacts
            if analysis.spatial_artifacts:
                print(f"  ⚠️  Artifacts detected:")
                for artifact in analysis.spatial_artifacts:
                    print(f"    - {artifact}")
            else:
                print(f"  ✅ No spatial artifacts detected")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def demo_format_conversion(processor, sample_files):
    """Demonstrate format conversion"""
    print("\n🔄 FORMAT CONVERSION DEMO")
    print("=" * 50)
    
    conversions_to_test = [
        ('stereo', SpatialFormat.SURROUND_5_1, "5.1 Surround"),
        ('stereo', SpatialFormat.BINAURAL, "Binaural"),
        ('5.1', SpatialFormat.STEREO, "Stereo"),
        ('ambisonics_foa', SpatialFormat.STEREO, "Stereo"),
        ('ambisonics_foa', SpatialFormat.SURROUND_5_1, "5.1 Surround")
    ]
    
    for source_type, target_format, target_name in conversions_to_test:
        if source_type in sample_files:
            print(f"\nConverting {source_type} to {target_name}...")
            
            try:
                converted_file = await processor.convert_spatial_format(
                    sample_files[source_type], target_format
                )
                
                # Verify conversion
                info = sf.info(converted_file)
                print(f"  ✅ Conversion successful")
                print(f"  Output channels: {info.channels}")
                print(f"  Output file: {Path(converted_file).name}")
                
                # Clean up converted file
                os.unlink(converted_file)
                
            except Exception as e:
                print(f"  ❌ Conversion failed: {e}")


async def demo_spatial_enhancement(processor, sample_files):
    """Demonstrate spatial enhancement"""
    print("\n✨ SPATIAL ENHANCEMENT DEMO")
    print("=" * 50)
    
    enhancement_configs = [
        {
            'name': 'Width Enhancement',
            'config': {
                'width_enhancement': True,
                'enhancement_strength': 1.3
            }
        },
        {
            'name': 'Immersion Boost',
            'config': {
                'immersion_boost': True,
                'enhancement_strength': 1.2
            }
        },
        {
            'name': 'Full Enhancement',
            'config': {
                'width_enhancement': True,
                'depth_enhancement': True,
                'immersion_boost': True,
                'localization_improvement': True,
                'enhancement_strength': 1.1
            }
        }
    ]
    
    # Test enhancement on stereo file
    if 'stereo' in sample_files:
        for enhancement in enhancement_configs:
            print(f"\nApplying {enhancement['name']} to stereo audio...")
            
            try:
                enhanced_file = await processor.enhance_spatial_audio(
                    sample_files['stereo'], enhancement['config']
                )
                
                print(f"  ✅ Enhancement applied successfully")
                print(f"  Enhanced file: {Path(enhanced_file).name}")
                
                # Analyze enhanced audio
                analysis = await processor.analyze_spatial_properties(enhanced_file)
                print(f"  Enhanced spatial width: {analysis.spatial_width:.3f}")
                print(f"  Enhanced immersion score: {analysis.immersion_score:.3f}")
                
                # Clean up enhanced file
                os.unlink(enhanced_file)
                
            except Exception as e:
                print(f"  ❌ Enhancement failed: {e}")


async def demo_spatial_visualization(processor, sample_files):
    """Demonstrate spatial visualization"""
    print("\n📈 SPATIAL VISUALIZATION DEMO")
    print("=" * 50)
    
    for file_type, file_path in sample_files.items():
        print(f"\nGenerating visualization for {file_type}...")
        
        try:
            viz_file = await processor.create_spatial_visualization(file_path)
            
            # Load and display visualization data
            with open(viz_file, 'r') as f:
                viz_data = json.load(f)
            
            print(f"  ✅ Visualization generated")
            print(f"  Format: {viz_data['format']}")
            
            # Display spatial dimensions
            dims = viz_data['spatial_dimensions']
            print(f"  Spatial Dimensions:")
            print(f"    Width: {dims['width']:.3f}")
            print(f"    Depth: {dims['depth']:.3f}")
            print(f"    Height: {dims['height']:.3f}")
            
            # Display quality metrics
            metrics = viz_data['quality_metrics']
            print(f"  Quality Metrics:")
            print(f"    Immersion: {metrics['immersion_score']:.3f}")
            print(f"    Localization: {metrics['localization_accuracy']:.3f}")
            
            # Display center of mass
            com = viz_data['center_of_mass']
            print(f"  Center of Mass: ({com['x']:.3f}, {com['y']:.3f}, {com['z']:.3f})")
            
            # Clean up visualization file
            os.unlink(viz_file)
            
        except Exception as e:
            print(f"  ❌ Visualization failed: {e}")


async def demo_advanced_features(processor, sample_files):
    """Demonstrate advanced spatial processing features"""
    print("\n🚀 ADVANCED FEATURES DEMO")
    print("=" * 50)
    
    # Test spatial position calculations
    print("\n1. Spatial Position Calculations:")
    positions = [
        SpatialPosition(x=-1.0, y=0.0, z=0.0),  # Left
        SpatialPosition(x=1.0, y=0.0, z=0.0),   # Right
        SpatialPosition(x=0.0, y=1.0, z=0.0),   # Front
        SpatialPosition(x=0.0, y=-1.0, z=0.0),  # Back
        SpatialPosition(x=0.0, y=0.0, z=1.0),   # Up
    ]
    
    for i, pos in enumerate(positions):
        azimuth, elevation, distance = pos.to_spherical()
        print(f"  Position {i+1}: Azimuth={np.degrees(azimuth):.1f}°, "
              f"Elevation={np.degrees(elevation):.1f}°, Distance={distance:.2f}")
    
    # Test channel mapping information
    print("\n2. Channel Mapping Information:")
    for format_type in [SpatialFormat.STEREO, SpatialFormat.SURROUND_5_1, 
                       SpatialFormat.AMBISONICS_FOA]:
        if format_type in processor.channel_mappings:
            mapping = processor.channel_mappings[format_type]
            print(f"  {format_type.value.upper()}:")
            for channel, name in mapping.items():
                print(f"    Channel {channel}: {name}")
    
    # Test HRTF information
    print("\n3. HRTF Database Information:")
    hrtf = processor.hrtf_data
    print(f"  Sample Rate: {hrtf['sample_rate']} Hz")
    print(f"  Elevation Range: {min(hrtf['elevations'])}° to {max(hrtf['elevations'])}°")
    print(f"  Azimuth Range: {min(hrtf['azimuths'])}° to {max(hrtf['azimuths'])}°")
    print(f"  Total HRTF Positions: {len(hrtf['impulse_responses'])}")
    
    # Test room responses
    print("\n4. Room Impulse Responses:")
    for room_type, response in processor.room_responses.items():
        rt60_estimate = len(response) / hrtf['sample_rate']
        print(f"  {room_type.replace('_', ' ').title()}: {rt60_estimate:.2f}s length")


def cleanup_sample_files(sample_files):
    """Clean up temporary sample files"""
    print("\n🧹 Cleaning up sample files...")
    
    for file_type, file_path in sample_files.items():
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"  Deleted {file_type} file")
        except Exception as e:
            print(f"  ❌ Failed to delete {file_type} file: {e}")


async def main():
    """Main demo function"""
    print("🎧 SPATIAL AUDIO PROCESSOR DEMO")
    print("=" * 60)
    
    if not SPATIAL_PROCESSOR_AVAILABLE:
        print("❌ Spatial Audio Processor not available. Please check dependencies.")
        return
    
    # Initialize processor
    print("Initializing Spatial Audio Processor...")
    processor = SpatialAudioProcessor()
    print("✅ Processor initialized successfully")
    
    # Create sample files
    sample_files = create_sample_audio_files()
    
    try:
        # Run demonstrations
        await demo_format_detection(processor, sample_files)
        await demo_spatial_analysis(processor, sample_files)
        await demo_format_conversion(processor, sample_files)
        await demo_spatial_enhancement(processor, sample_files)
        await demo_spatial_visualization(processor, sample_files)
        await demo_advanced_features(processor, sample_files)
        
        print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("The Spatial Audio Processor demonstrated:")
        print("✅ Format detection for multiple spatial audio formats")
        print("✅ Comprehensive spatial analysis and quality metrics")
        print("✅ Format conversion between different spatial formats")
        print("✅ Spatial enhancement with configurable parameters")
        print("✅ Spatial visualization and reporting")
        print("✅ Advanced features like HRTF processing and room simulation")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
    
    finally:
        # Cleanup
        cleanup_sample_files(sample_files)
        await processor.cleanup()
        print("\n✅ Cleanup completed")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())