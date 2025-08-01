"""
Test script for speaker diarization functionality
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speaker_diarization import (
    DiarizationManager,
    MockProvider,
    SimpleVADProvider,
    PyannoteProvider
)
from speaker_diarization.integration import TranscriptionDiarizationIntegrator


async def test_mock_provider():
    """Test the mock provider"""
    print("\n=== Testing Mock Provider ===")
    
    # Create mock provider
    provider = MockProvider({'processing_delay': 0.5})
    manager = DiarizationManager(provider)
    
    # Process a dummy audio file
    audio_path = "test_data/audio/business_meeting.wav"
    
    # Create dummy file if it doesn't exist
    if not os.path.exists(audio_path):
        os.makedirs(os.path.dirname(audio_path), exist_ok=True)
        Path(audio_path).touch()
    
    try:
        result = await manager.process_audio(
            audio_path,
            min_segment_duration=1.0,
            max_speakers=3,
            use_cache=False
        )
        
        print(f"✓ Found {len(result.speakers)} speakers")
        print(f"✓ Generated {len(result.segments)} segments")
        print(f"✓ Audio duration: {result.audio_duration:.1f}s")
        
        # Print speaker statistics
        print("\nSpeaker Statistics:")
        for speaker_id, speaker_info in result.speakers.items():
            print(f"  {speaker_id}: {speaker_info.total_time:.1f}s ({speaker_info.segment_count} segments)")
        
        # Test timeline generation
        result.generate_timeline(resolution=5.0)
        print(f"✓ Generated timeline with {len(result.timeline)} points")
        
        # Test speaker merging
        if len(result.speakers) >= 2:
            speakers_list = list(result.speakers.keys())
            result.merge_speakers(speakers_list[0], speakers_list[1])
            print(f"✓ Merged speakers, now have {len(result.speakers)} speakers")
        
        # Test serialization
        data = result.to_dict()
        reconstructed = type(result).from_dict(data)
        print(f"✓ Serialization/deserialization working")
        
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_simple_vad_provider():
    """Test the simple VAD provider"""
    print("\n=== Testing Simple VAD Provider ===")
    
    provider = SimpleVADProvider()
    
    if not provider.is_available():
        print("✗ Simple VAD provider not available (missing scipy)")
        return False
    
    print("✓ Simple VAD provider available")
    
    # Would test with actual audio file if available
    return True


async def test_pyannote_provider():
    """Test the pyannote provider"""
    print("\n=== Testing PyAnnote Provider ===")
    
    provider = PyannoteProvider()
    
    if not provider.is_available():
        print("✗ PyAnnote provider not available (missing pyannote.audio)")
        return False
    
    print("✓ PyAnnote provider available")
    
    # Would test with actual audio file if available
    return True


async def test_integration():
    """Test integration with transcription"""
    print("\n=== Testing Integration ===")
    
    integrator = TranscriptionDiarizationIntegrator()
    
    # Test provider discovery
    providers = ['pyannote', 'simple_vad', 'mock']
    available_providers = []
    
    for provider_name in providers:
        provider = integrator.get_provider(provider_name)
        if provider:
            available_providers.append(provider_name)
            print(f"✓ Provider '{provider_name}' available")
        else:
            print(f"✗ Provider '{provider_name}' not available")
    
    if not available_providers:
        print("✗ No providers available")
        return False
    
    # Test with mock provider
    audio_path = "test_audio.wav"
    Path(audio_path).touch()  # Create dummy file
    
    try:
        transcript = "Hello everyone, welcome to our meeting. Thank you for joining us today. Let's discuss the project timeline."
        
        enhanced_transcript, diarization_result = await integrator.process_with_diarization(
            audio_path,
            transcript,
            provider_name='mock',
            config={'min_segment_duration': 1.0, 'max_speakers': 3}
        )
        
        print(f"✓ Integration successful")
        print(f"✓ Enhanced transcript length: {len(enhanced_transcript)}")
        
        # Test export data creation
        export_data = integrator.create_enhanced_export_data(
            transcript,
            diarization_result,
            entities=[{'text': 'project timeline', 'type': 'TOPIC'}]
        )
        
        print(f"✓ Export data created with {len(export_data['segments'])} segments")
        
        # Test SRT formatting
        srt_content = integrator.format_for_srt_with_speakers(diarization_result, transcript)
        print(f"✓ SRT format generated ({len(srt_content.splitlines())} lines)")
        
        # Test VTT formatting  
        vtt_content = integrator.format_for_vtt_with_speakers(diarization_result, transcript)
        print(f"✓ VTT format generated ({len(vtt_content.splitlines())} lines)")
        
        # Clean up
        os.remove(audio_path)
        
        return True
        
    except Exception as e:
        print(f"✗ Integration error: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return False


async def test_ui_data_generation():
    """Test data generation for UI components"""
    print("\n=== Testing UI Data Generation ===")
    
    # Create sample diarization result
    provider = MockProvider({'processing_delay': 0.1})
    manager = DiarizationManager(provider)
    
    audio_path = "test_ui.wav"
    Path(audio_path).touch()
    
    try:
        result = await manager.process_audio(audio_path, use_cache=False)
        
        # Update speaker labels
        for i, (speaker_id, speaker_info) in enumerate(result.speakers.items()):
            manager.update_speaker_label(result, speaker_id, f"Person {i+1}")
        
        # Calculate statistics
        result.calculate_statistics()
        
        # Generate timeline
        result.generate_timeline(resolution=1.0)
        
        print(f"✓ Generated UI data:")
        print(f"  - {len(result.speakers)} speakers with labels")
        print(f"  - {len(result.timeline)} timeline points")
        print(f"  - Speaker statistics calculated")
        
        # Export to JSON for UI testing
        ui_data = {
            'diarization': result.to_dict(),
            'ui_config': {
                'timeline_height': 200,
                'show_confidence': True,
                'allow_merge': True,
                'allow_rename': True
            }
        }
        
        with open('test_diarization_ui_data.json', 'w') as f:
            json.dump(ui_data, f, indent=2)
        
        print(f"✓ Exported UI test data to test_diarization_ui_data.json")
        
        # Clean up
        os.remove(audio_path)
        
        return True
        
    except Exception as e:
        print(f"✗ UI data generation error: {e}")
        if os.path.exists(audio_path):
            os.remove(audio_path)
        return False


async def main():
    """Run all tests"""
    print("🎯 Speaker Diarization Test Suite")
    print("=" * 50)
    
    tests = [
        test_mock_provider,
        test_simple_vad_provider,
        test_pyannote_provider,
        test_integration,
        test_ui_data_generation
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"✓ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")
    
    # Clean up test files
    test_files = ['test_diarization_ui_data.json']
    for file in test_files:
        if os.path.exists(file):
            os.remove(file)


if __name__ == "__main__":
    asyncio.run(main())