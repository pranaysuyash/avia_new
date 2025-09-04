"""
Demo Script for Professional Audio Format Handler
Demonstrates comprehensive audio format handling and conversion capabilities

Requirements: 1.3
Dependencies: professional_audio_format_handler.py
"""

import asyncio
import numpy as np
import soundfile as sf
import tempfile
import os
import json
from pathlib import Path
import logging
import time

try:
    from professional_audio_format_handler import (
        ProfessionalAudioFormatHandler, AudioFormat, AudioCodec,
        QualityLevel, ConversionMode, ConversionSettings,
        BatchProcessingJob, AudioMetadata
    )
    FORMAT_HANDLER_AVAILABLE = True
except ImportError:
    FORMAT_HANDLER_AVAILABLE = False
    print("❌ Professional Audio Format Handler not available")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_sample_audio_files():
    """Create sample audio files in different formats for demonstration"""
    print("🎵 Creating sample audio files...")
    
    sample_rate = 44100
    duration = 3.0  # seconds
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    files_created = {}
    
    # 1. High-quality stereo WAV file
    print("  Creating high-quality stereo WAV file...")
    left = (np.sin(2 * np.pi * 440 * t) * 0.4 +  # A4
            np.sin(2 * np.pi * 880 * t) * 0.2 +  # A5
            np.sin(2 * np.pi * 1320 * t) * 0.1)  # E6
    right = (np.sin(2 * np.pi * 523 * t) * 0.4 +  # C5
             np.sin(2 * np.pi * 1047 * t) * 0.2 + # C6
             np.sin(2 * np.pi * 1571 * t) * 0.1)  # G6
    
    # Add some envelope to make it more musical
    envelope = np.exp(-t * 0.5) * (1 - np.exp(-t * 5))
    left *= envelope
    right *= envelope
    
    stereo_audio = np.column_stack([left, right])
    
    wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='_stereo_hq.wav')
    sf.write(wav_file.name, stereo_audio, sample_rate, subtype='PCM_24')
    files_created['wav_stereo'] = wav_file.name
    
    # 2. Mono speech-like WAV file
    print("  Creating mono speech-like WAV file...")
    # Simulate speech-like content with formants
    speech_like = (np.sin(2 * np.pi * 200 * t) * 0.3 +  # Fundamental
                   np.sin(2 * np.pi * 800 * t) * 0.2 +   # First formant
                   np.sin(2 * np.pi * 2400 * t) * 0.1)   # Second formant
    
    # Add some noise to simulate speech characteristics
    noise = np.random.normal(0, 0.05, len(speech_like))
    speech_like += noise
    
    # Apply speech-like envelope
    speech_envelope = np.ones_like(t)
    # Add some pauses
    pause_starts = [0.8, 1.6, 2.4]
    pause_duration = 0.2
    for start in pause_starts:
        start_idx = int(start * sample_rate)
        end_idx = int((start + pause_duration) * sample_rate)
        if end_idx < len(speech_envelope):
            speech_envelope[start_idx:end_idx] *= 0.1
    
    speech_like *= speech_envelope
    
    mono_file = tempfile.NamedTemporaryFile(delete=False, suffix='_mono_speech.wav')
    sf.write(mono_file.name, speech_like, sample_rate)
    files_created['wav_mono'] = mono_file.name
    
    # 3. High sample rate file
    print("  Creating high sample rate WAV file...")
    high_sr = 96000
    t_high = np.linspace(0, duration, int(high_sr * duration))
    
    # Create content with high-frequency components
    high_freq_audio = (np.sin(2 * np.pi * 440 * t_high) * 0.3 +
                       np.sin(2 * np.pi * 8000 * t_high) * 0.2 +
                       np.sin(2 * np.pi * 15000 * t_high) * 0.1)
    
    high_freq_audio *= np.exp(-t_high * 0.3)
    
    high_sr_file = tempfile.NamedTemporaryFile(delete=False, suffix='_96khz.wav')
    sf.write(high_sr_file.name, high_freq_audio, high_sr, subtype='PCM_24')
    files_created['wav_96khz'] = high_sr_file.name
    
    # 4. Multi-channel file (5.1 simulation)
    print("  Creating multi-channel WAV file...")
    # Create 6-channel audio (5.1 surround simulation)
    channels = []
    frequencies = [440, 523, 659, 80, 349, 415]  # Different freq for each channel
    
    for i, freq in enumerate(frequencies):
        channel_audio = np.sin(2 * np.pi * freq * t) * 0.3
        # Add some delay for spatial effect
        delay_samples = i * 1000
        if delay_samples < len(channel_audio):
            delayed_audio = np.zeros_like(channel_audio)
            delayed_audio[delay_samples:] = channel_audio[:-delay_samples]
            channel_audio = delayed_audio
        
        channel_audio *= np.exp(-t * 0.4)
        channels.append(channel_audio)
    
    multichannel_audio = np.column_stack(channels)
    
    multichannel_file = tempfile.NamedTemporaryFile(delete=False, suffix='_5_1.wav')
    sf.write(multichannel_file.name, multichannel_audio, sample_rate)
    files_created['wav_multichannel'] = multichannel_file.name
    
    # 5. FLAC file for lossless testing
    print("  Creating FLAC file...")
    flac_file = tempfile.NamedTemporaryFile(delete=False, suffix='_lossless.flac')
    sf.write(flac_file.name, stereo_audio, sample_rate, subtype='PCM_16')
    files_created['flac_lossless'] = flac_file.name
    
    print(f"✅ Created {len(files_created)} sample audio files")
    return files_created


async def demo_format_detection(handler, sample_files):
    """Demonstrate format detection and metadata extraction"""
    print("\n🔍 FORMAT DETECTION & METADATA EXTRACTION DEMO")
    print("=" * 60)
    
    for file_type, file_path in sample_files.items():
        print(f"\nAnalyzing {file_type}...")
        
        try:
            format_detected, metadata = await handler.detect_format(file_path)
            
            print(f"  📁 Format: {format_detected.value.upper()}")
            print(f"  ⏱️  Duration: {metadata.duration:.2f} seconds")
            print(f"  🔊 Sample Rate: {metadata.sample_rate} Hz")
            print(f"  📻 Channels: {metadata.channels}")
            print(f"  🎚️  Bit Depth: {metadata.bit_depth} bits")
            
            if metadata.bitrate:
                print(f"  📊 Bitrate: {metadata.bitrate} kbps")
            
            # Quality metrics
            if metadata.peak_level is not None:
                print(f"  📈 Peak Level: {metadata.peak_level:.3f}")
            if metadata.rms_level is not None:
                print(f"  📊 RMS Level: {metadata.rms_level:.3f}")
            if metadata.dynamic_range is not None:
                print(f"  🎛️  Dynamic Range: {metadata.dynamic_range:.1f} dB")
            if metadata.lufs is not None:
                print(f"  📏 LUFS: {metadata.lufs:.1f}")
            
        except Exception as e:
            print(f"  ❌ Error analyzing {file_type}: {e}")


async def demo_format_conversion(handler, sample_files):
    """Demonstrate format conversion capabilities"""
    print("\n🔄 FORMAT CONVERSION DEMO")
    print("=" * 60)
    
    conversions_to_test = [
        ('wav_stereo', AudioFormat.FLAC, QualityLevel.LOSSLESS, "Stereo WAV → FLAC"),
        ('wav_mono', AudioFormat.MP3, QualityLevel.STANDARD, "Mono WAV → MP3"),
        ('wav_96khz', AudioFormat.WAV, QualityLevel.HIGH, "96kHz → 48kHz WAV"),
        ('flac_lossless', AudioFormat.AAC, QualityLevel.HIGH, "FLAC → AAC"),
        ('wav_multichannel', AudioFormat.FLAC, QualityLevel.ARCHIVE, "Multi-channel → FLAC")
    ]
    
    for source_key, target_format, quality, description in conversions_to_test:
        if source_key not in sample_files:
            continue
        
        print(f"\n{description}...")
        
        try:
            # Create conversion settings
            settings = ConversionSettings(
                target_format=target_format,
                quality_level=quality,
                preserve_metadata=True
            )
            
            # Special settings for specific conversions
            if "96kHz → 48kHz" in description:
                settings.sample_rate = 48000
            elif "MP3" in description:
                settings.bitrate = 192
                settings.channels = 1  # Keep mono
            
            # Perform conversion
            output_file = tempfile.NamedTemporaryFile(
                delete=False, 
                suffix=f'.{target_format.value}'
            ).name
            
            start_time = time.time()
            result = await handler.convert_format(
                sample_files[source_key], output_file, settings
            )
            conversion_time = time.time() - start_time
            
            if result.success:
                print(f"  ✅ Conversion successful in {conversion_time:.2f}s")
                print(f"  📁 Output: {Path(output_file).name}")
                
                if result.original_size and result.converted_size:
                    size_reduction = (1 - result.converted_size / result.original_size) * 100
                    print(f"  📊 Size: {result.original_size / 1024:.1f}KB → {result.converted_size / 1024:.1f}KB ({size_reduction:+.1f}%)")
                
                if result.compression_ratio:
                    print(f"  🗜️  Compression: {result.compression_ratio:.2f}x")
                
                # Quality metrics
                if result.quality_metrics:
                    if 'snr_db' in result.quality_metrics:
                        print(f"  🎯 SNR: {result.quality_metrics['snr_db']:.1f} dB")
                    if 'correlation' in result.quality_metrics:
                        print(f"  🔗 Correlation: {result.quality_metrics['correlation']:.3f}")
                
                # Verify converted file
                try:
                    converted_info = sf.info(output_file)
                    print(f"  ✓ Verified: {converted_info.channels}ch, {converted_info.samplerate}Hz")
                except:
                    pass
                
                # Clean up
                os.unlink(output_file)
            else:
                print(f"  ❌ Conversion failed: {result.error_message}")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")


async def demo_batch_processing(handler, sample_files):
    """Demonstrate batch processing capabilities"""
    print("\n⚡ BATCH PROCESSING DEMO")
    print("=" * 60)
    
    # Select files for batch processing
    batch_files = [sample_files['wav_stereo'], sample_files['wav_mono'], sample_files['wav_96khz']]
    
    print(f"Processing {len(batch_files)} files in batch...")
    
    try:
        # Create output directory
        output_dir = tempfile.mkdtemp(prefix="batch_converted_")
        
        # Create batch job
        batch_settings = ConversionSettings(
            target_format=AudioFormat.FLAC,
            quality_level=QualityLevel.HIGH,
            preserve_metadata=True,
            normalize_audio=True
        )
        
        job = BatchProcessingJob(
            job_id="demo_batch",
            input_files=batch_files,
            output_directory=output_dir,
            conversion_settings=batch_settings,
            parallel_workers=2
        )
        
        # Progress tracking
        processed_count = 0
        def progress_callback(progress, result):
            nonlocal processed_count
            processed_count += 1
            print(f"  📁 Processed {processed_count}/{len(batch_files)}: {Path(result.input_file).name}")
        
        job.progress_callback = progress_callback
        
        # Process batch
        start_time = time.time()
        completed_job = await handler.batch_convert(job)
        batch_time = time.time() - start_time
        
        print(f"\n✅ Batch processing completed in {batch_time:.2f}s")
        print(f"📊 Status: {completed_job.status}")
        
        # Results summary
        successful = sum(1 for r in completed_job.results if r.success)
        failed = len(completed_job.results) - successful
        
        print(f"📈 Results: {successful} successful, {failed} failed")
        
        # Detailed results
        total_original_size = 0
        total_converted_size = 0
        
        for result in completed_job.results:
            filename = Path(result.input_file).name
            if result.success:
                print(f"  ✅ {filename}: {result.processing_time:.2f}s")
                if result.original_size and result.converted_size:
                    total_original_size += result.original_size
                    total_converted_size += result.converted_size
            else:
                print(f"  ❌ {filename}: {result.error_message}")
        
        if total_original_size > 0 and total_converted_size > 0:
            overall_compression = total_original_size / total_converted_size
            print(f"🗜️  Overall compression: {overall_compression:.2f}x")
        
        # Clean up output directory
        import shutil
        shutil.rmtree(output_dir)
        
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")


async def demo_quality_assessment(handler, sample_files):
    """Demonstrate quality assessment and validation"""
    print("\n🔍 QUALITY ASSESSMENT DEMO")
    print("=" * 60)
    
    for file_type, file_path in sample_files.items():
        print(f"\nAssessing quality of {file_type}...")
        
        try:
            validation_result = await handler.validate_audio_file(file_path)
            
            if validation_result['is_valid']:
                print("  ✅ File is valid")
            else:
                print("  ❌ File has issues")
            
            # Display issues
            if validation_result['issues']:
                print("  ⚠️  Issues found:")
                for issue in validation_result['issues']:
                    print(f"    • {issue}")
            
            # Display recommendations
            if validation_result['recommendations']:
                print("  💡 Recommendations:")
                for rec in validation_result['recommendations']:
                    print(f"    • {rec}")
            
            # Quality score calculation (simplified)
            metadata = validation_result.get('metadata')
            if metadata:
                quality_score = calculate_quality_score(metadata)
                print(f"  📊 Quality Score: {quality_score:.1f}/100")
        
        except Exception as e:
            print(f"  ❌ Error assessing {file_type}: {e}")


async def demo_format_information(handler):
    """Demonstrate format information and capabilities"""
    print("\n📋 FORMAT INFORMATION DEMO")
    print("=" * 60)
    
    # Get supported formats
    supported_formats = await handler.get_supported_formats()
    print(f"Supported formats: {len(supported_formats)}")
    
    # Display detailed information for key formats
    key_formats = [AudioFormat.WAV, AudioFormat.FLAC, AudioFormat.MP3, AudioFormat.AAC]
    
    for format in key_formats:
        if format in supported_formats:
            print(f"\n{format.value.upper()} Format Information:")
            
            format_info = await handler.get_format_info(format)
            if format_info:
                print(f"  🎵 Codec: {format_info.codec.value.upper()}")
                print(f"  🔒 Lossless: {'Yes' if format_info.is_lossless else 'No'}")
                print(f"  📝 Metadata Support: {'Yes' if format_info.supports_metadata else 'No'}")
                print(f"  🔊 Max Channels: {format_info.max_channels}")
                print(f"  📊 Max Sample Rate: {format_info.max_sample_rate:,} Hz")
                print(f"  🎚️  Max Bit Depth: {format_info.max_bit_depth} bits")
                print(f"  📁 Extensions: {', '.join(format_info.file_extensions)}")
                print(f"  💾 Typical Bitrates: {', '.join(map(str, format_info.typical_bitrates))} kbps")


async def demo_conversion_recommendations(handler, sample_files):
    """Demonstrate conversion recommendations for different use cases"""
    print("\n💡 CONVERSION RECOMMENDATIONS DEMO")
    print("=" * 60)
    
    use_cases = ["streaming", "podcast", "archival", "mobile", "broadcast", "web"]
    test_file = sample_files['wav_stereo']
    
    for use_case in use_cases:
        print(f"\n{use_case.title()} Use Case:")
        
        try:
            recommendations = await handler.get_conversion_recommendations(test_file, use_case)
            
            print(f"  🎯 Target Format: {recommendations.target_format.value.upper()}")
            print(f"  🏆 Quality Level: {recommendations.quality_level.value.title()}")
            
            if recommendations.sample_rate:
                print(f"  📊 Sample Rate: {recommendations.sample_rate} Hz")
            if recommendations.channels:
                print(f"  🔊 Channels: {recommendations.channels}")
            if recommendations.bitrate:
                print(f"  💾 Bitrate: {recommendations.bitrate} kbps")
            if recommendations.bit_depth:
                print(f"  🎚️  Bit Depth: {recommendations.bit_depth} bits")
            
            print(f"  📝 Preserve Metadata: {'Yes' if recommendations.preserve_metadata else 'No'}")
            print(f"  🔧 Normalize Audio: {'Yes' if recommendations.normalize_audio else 'No'}")
        
        except Exception as e:
            print(f"  ❌ Error getting recommendations: {e}")


async def demo_processing_statistics(handler):
    """Demonstrate processing statistics tracking"""
    print("\n📊 PROCESSING STATISTICS DEMO")
    print("=" * 60)
    
    try:
        stats = await handler.get_processing_statistics()
        
        print("Current Processing Statistics:")
        print(f"  📈 Total Conversions: {stats['total_conversions']}")
        print(f"  ✅ Successful: {stats['successful_conversions']}")
        print(f"  ❌ Failed: {stats['failed_conversions']}")
        print(f"  🎯 Success Rate: {stats['success_rate']:.1%}")
        print(f"  ⏱️  Average Processing Time: {stats['average_processing_time']:.2f}s")
        print(f"  🗜️  Average Compression Ratio: {stats['average_compression_ratio']:.2f}x")
        
        if stats['formats_processed']:
            print("\n  Format Processing Breakdown:")
            for format_combo, count in stats['formats_processed'].items():
                source, target = format_combo.split('_to_')
                print(f"    {source.upper()} → {target.upper()}: {count} conversions")
    
    except Exception as e:
        print(f"❌ Error getting statistics: {e}")


def calculate_quality_score(metadata):
    """Calculate a simple quality score from metadata"""
    score = 50  # Base score
    
    # Sample rate scoring
    if metadata.sample_rate:
        if metadata.sample_rate >= 96000:
            score += 20
        elif metadata.sample_rate >= 48000:
            score += 15
        elif metadata.sample_rate >= 44100:
            score += 10
    
    # Bit depth scoring
    if metadata.bit_depth:
        if metadata.bit_depth >= 24:
            score += 15
        elif metadata.bit_depth >= 16:
            score += 10
    
    # Dynamic range scoring
    if metadata.dynamic_range:
        if metadata.dynamic_range >= 20:
            score += 10
        elif metadata.dynamic_range >= 12:
            score += 5
        else:
            score -= 5
    
    # Peak level scoring (avoid clipping)
    if metadata.peak_level:
        if metadata.peak_level < 0.95:
            score += 5
        elif metadata.peak_level >= 1.0:
            score -= 10
    
    return min(100, max(0, score))


def cleanup_sample_files(sample_files):
    """Clean up temporary sample files"""
    print("\n🧹 Cleaning up sample files...")
    
    for file_type, file_path in sample_files.items():
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
                print(f"  Deleted {file_type}")
        except Exception as e:
            print(f"  ❌ Failed to delete {file_type}: {e}")


async def main():
    """Main demo function"""
    print("🎵 PROFESSIONAL AUDIO FORMAT HANDLER DEMO")
    print("=" * 70)
    
    if not FORMAT_HANDLER_AVAILABLE:
        print("❌ Professional Audio Format Handler not available. Please check dependencies.")
        return
    
    # Initialize handler
    print("Initializing Professional Audio Format Handler...")
    handler = ProfessionalAudioFormatHandler(max_workers=4)
    print("✅ Handler initialized successfully")
    
    # Create sample files
    sample_files = create_sample_audio_files()
    
    try:
        # Run demonstrations
        await demo_format_detection(handler, sample_files)
        await demo_format_information(handler)
        await demo_conversion_recommendations(handler, sample_files)
        await demo_format_conversion(handler, sample_files)
        await demo_batch_processing(handler, sample_files)
        await demo_quality_assessment(handler, sample_files)
        await demo_processing_statistics(handler)
        
        print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("The Professional Audio Format Handler demonstrated:")
        print("✅ Comprehensive format detection and metadata extraction")
        print("✅ Professional-grade format conversion with quality preservation")
        print("✅ Batch processing with parallel execution")
        print("✅ Audio quality assessment and validation")
        print("✅ Use case-specific conversion recommendations")
        print("✅ Detailed format information and capabilities")
        print("✅ Processing statistics and performance tracking")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        logger.exception("Demo failed")
    
    finally:
        # Cleanup
        cleanup_sample_files(sample_files)
        await handler.cleanup()
        print("\n✅ Cleanup completed")


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())