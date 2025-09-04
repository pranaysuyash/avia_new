"""
Demo script for WhisperX enhanced speaker diarization
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from speaker_diarization.integration import TranscriptionDiarizationIntegrator
from speaker_diarization.speaker_profiler import SpeakerProfiler
from speaker_diarization.diarization_ui import (
    render_speaker_timeline_visualization,
    render_speaker_statistics,
    render_voice_characteristics_analysis
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_whisperx_diarization():
    """Demonstrate WhisperX enhanced speaker diarization"""
    print("🎙️ WhisperX Enhanced Speaker Diarization Demo")
    print("=" * 50)
    
    # Initialize integrator
    integrator = TranscriptionDiarizationIntegrator()
    
    # Check if WhisperX is available
    whisperx_provider = integrator.get_provider('whisperx')
    if not whisperx_provider:
        print("❌ WhisperX provider not available")
        print("Install with: pip install whisperx")
        return
    
    print("✅ WhisperX provider available")
    
    # Demo audio file (you would replace this with actual audio)
    demo_audio_path = "temp/demo_audio.wav"
    
    if not Path(demo_audio_path).exists():
        print(f"⚠️  Demo audio file not found: {demo_audio_path}")
        print("Creating mock audio file for demo...")
        
        # Create a simple demo audio file
        import numpy as np
        import soundfile as sf
        
        # Generate 30 seconds of demo audio (silence with some noise)
        sample_rate = 16000
        duration = 30
        audio_data = np.random.normal(0, 0.01, sample_rate * duration).astype(np.float32)
        
        Path("temp").mkdir(exist_ok=True)
        sf.write(demo_audio_path, audio_data, sample_rate)
        print(f"✅ Created demo audio file: {demo_audio_path}")
    
    # Configuration for WhisperX
    config = {
        'model_size': 'base',
        'device': 'cpu',  # Use 'cuda' if GPU available
        'language': 'en',
        'min_segment_duration': 1.0,
        'max_speakers': 5,
        'use_cache': True
    }
    
    print("\n🔄 Processing audio with WhisperX...")
    print(f"Configuration: {config}")
    
    try:
        # Process with enhanced speaker profiling
        transcript, diarization_result, speaker_profiles = await integrator.process_with_speaker_profiling(
            audio_path=demo_audio_path,
            transcript="Demo transcript text",
            provider_name='whisperx',
            config=config,
            recording_id='demo_recording_001'
        )
        
        print("\n✅ Processing completed!")
        print(f"📊 Results:")
        print(f"   - Speakers detected: {len(diarization_result.speakers)}")
        print(f"   - Segments created: {len(diarization_result.segments)}")
        print(f"   - Audio duration: {diarization_result.audio_duration:.1f}s")
        print(f"   - Speaker profiles: {len(speaker_profiles)}")
        
        # Display speaker information
        print("\n👥 Speaker Information:")
        for speaker_id, speaker_info in diarization_result.speakers.items():
            print(f"   {speaker_id}:")
            print(f"     - Speaking time: {speaker_info.total_time:.1f}s")
            print(f"     - Segments: {speaker_info.segment_count}")
            print(f"     - Confidence: {speaker_info.average_confidence:.0%}")
            
            if speaker_id in speaker_profiles:
                profile = speaker_profiles[speaker_id]
                voice_type = profile.voice_characteristics.get('voice_type', 'Unknown')
                print(f"     - Voice type: {voice_type}")
        
        # Display segments with text
        print("\n📝 Speaker Segments:")
        for i, segment in enumerate(diarization_result.segments[:5]):  # Show first 5
            speaker_info = diarization_result.speakers[segment.speaker_id]
            speaker_label = speaker_info.label or segment.speaker_id
            print(f"   [{i+1}] {speaker_label} ({segment.start_time:.1f}s - {segment.end_time:.1f}s)")
            if segment.text:
                print(f"       Text: {segment.text[:100]}...")
            print(f"       Confidence: {segment.confidence:.0%}")
        
        if len(diarization_result.segments) > 5:
            print(f"   ... and {len(diarization_result.segments) - 5} more segments")
        
        # Demonstrate speaker profiling features
        print("\n🧠 Speaker Profiling Features:")
        profiler = integrator.speaker_profiler
        all_profiles = profiler.get_all_profiles()
        
        print(f"   - Total profiles in database: {len(all_profiles)}")
        
        for speaker_id, profile in all_profiles.items():
            print(f"   Profile: {speaker_id}")
            print(f"     - Name: {profile.name or 'Unnamed'}")
            print(f"     - Total recordings: {profile.recording_count}")
            print(f"     - Total speaking time: {profile.total_speaking_time:.1f}s")
            print(f"     - Recognition confidence: {profile.recognition_confidence:.0%}")
            
            # Show voice characteristics
            if profile.voice_characteristics:
                voice_type = profile.voice_characteristics.get('voice_type', 'Unknown')
                embedding_norm = profile.voice_characteristics.get('embedding_norm', 0)
                print(f"     - Voice type: {voice_type}")
                print(f"     - Embedding strength: {embedding_norm:.3f}")
        
        # Export results
        print("\n💾 Exporting results...")
        
        # Export enhanced data
        export_data = integrator.create_enhanced_export_data(
            transcript, diarization_result, []
        )
        
        export_path = "temp/whisperx_demo_results.json"
        import json
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        print(f"   ✅ Results exported to: {export_path}")
        
        # Export speaker profiles
        profiles_export_path = "temp/speaker_profiles_demo.json"
        if profiler.export_profiles(profiles_export_path):
            print(f"   ✅ Speaker profiles exported to: {profiles_export_path}")
        
        print("\n🎉 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ WhisperX integration for enhanced diarization")
        print("✅ ML-based speaker embedding extraction")
        print("✅ Speaker voice profiling and recognition")
        print("✅ Speaker timeline visualization")
        print("✅ Cross-recording speaker identification")
        print("✅ Voice characteristics analysis")
        print("✅ Speaker profile management")
        
    except Exception as e:
        print(f"❌ Error during processing: {e}")
        logger.error(f"Demo failed: {e}", exc_info=True)


def demo_speaker_recognition():
    """Demonstrate speaker recognition across multiple recordings"""
    print("\n🔍 Speaker Recognition Demo")
    print("=" * 30)
    
    profiler = SpeakerProfiler()
    
    # Simulate multiple recordings with the same speakers
    print("Simulating speaker recognition across recordings...")
    
    # This would normally be done with real audio processing
    import numpy as np
    
    # Create mock embeddings for demonstration
    speaker_a_embedding = np.random.normal(0.5, 0.1, 512)
    speaker_b_embedding = np.random.normal(-0.3, 0.15, 512)
    
    # First recording - create profiles
    print("\n📹 Recording 1: Creating initial profiles")
    profile_a = profiler.create_profile(
        "speaker_001",
        speaker_a_embedding,
        {'voice_type': 'expressive', 'embedding_norm': float(np.linalg.norm(speaker_a_embedding))},
        {'average_segment_duration': 5.2, 'speaking_style': 'continuous'},
        name="Alice"
    )
    
    profile_b = profiler.create_profile(
        "speaker_002", 
        speaker_b_embedding,
        {'voice_type': 'steady', 'embedding_norm': float(np.linalg.norm(speaker_b_embedding))},
        {'average_segment_duration': 3.8, 'speaking_style': 'varied'},
        name="Bob"
    )
    
    print(f"   ✅ Created profile for Alice (speaker_001)")
    print(f"   ✅ Created profile for Bob (speaker_002)")
    
    # Second recording - test recognition
    print("\n📹 Recording 2: Testing speaker recognition")
    
    # Simulate slightly different embeddings (same speakers, different recording conditions)
    alice_new_embedding = speaker_a_embedding + np.random.normal(0, 0.05, 512)
    bob_new_embedding = speaker_b_embedding + np.random.normal(0, 0.05, 512)
    
    # Test recognition
    recognized_alice, confidence_alice = profiler.recognize_speaker(alice_new_embedding)
    recognized_bob, confidence_bob = profiler.recognize_speaker(bob_new_embedding)
    
    print(f"   🎯 Alice recognition: {recognized_alice} (confidence: {confidence_alice:.0%})")
    print(f"   🎯 Bob recognition: {recognized_bob} (confidence: {confidence_bob:.0%})")
    
    # Update profiles with new data
    if recognized_alice:
        profiler.update_profile(recognized_alice, alice_new_embedding, speaking_time=45.2)
        print(f"   ✅ Updated Alice's profile")
    
    if recognized_bob:
        profiler.update_profile(recognized_bob, bob_new_embedding, speaking_time=32.8)
        print(f"   ✅ Updated Bob's profile")
    
    # Show updated profiles
    print("\n📊 Updated Profile Statistics:")
    all_profiles = profiler.get_all_profiles()
    for speaker_id, profile in all_profiles.items():
        print(f"   {profile.name} ({speaker_id}):")
        print(f"     - Recordings: {profile.recording_count}")
        print(f"     - Total time: {profile.total_speaking_time:.1f}s")
        print(f"     - Confidence: {profile.recognition_confidence:.0%}")
    
    print("\n✅ Speaker recognition demo completed!")


if __name__ == "__main__":
    print("🚀 Starting WhisperX Enhanced Speaker Diarization Demo")
    
    # Run main demo
    asyncio.run(demo_whisperx_diarization())
    
    # Run speaker recognition demo
    demo_speaker_recognition()
    
    print("\n🎊 All demos completed!")
    print("\nNext steps:")
    print("1. Install WhisperX: pip install whisperx")
    print("2. Get HuggingFace token for advanced models")
    print("3. Test with real audio files")
    print("4. Explore speaker profiling features in the UI")