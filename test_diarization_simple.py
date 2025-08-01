#!/usr/bin/env python3
"""
Simple test for speaker diarization functionality
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speaker_diarization import DiarizationManager, MockProvider

async def test_diarization():
    """Test basic diarization functionality"""
    print("🎙️ Testing Speaker Diarization")
    print("=" * 50)
    
    # Create mock provider for testing
    provider = MockProvider({'processing_delay': 0.1})
    manager = DiarizationManager(provider)
    
    # Create a dummy audio file for testing
    audio_path = "test_audio.wav"
    Path(audio_path).touch()
    
    try:
        print("\n1. Processing audio with mock provider...")
        result = await manager.process_audio(
            audio_path,
            min_segment_duration=1.0,
            max_speakers=3,
            use_cache=False
        )
        
        print(f"✅ Found {len(result.speakers)} speakers: {', '.join(result.speakers)}")
        print(f"✅ Generated {len(result.segments)} segments")
        print(f"✅ Audio duration: {result.audio_duration:.1f}s")
        
        print("\n2. Sample segments:")
        for i, segment in enumerate(result.segments[:3]):
            print(f"   {i+1}. [{segment.start:.1f}s - {segment.end:.1f}s] {segment.speaker}: \"{segment.text}\"")
        
        print("\n✅ Speaker diarization test completed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        # Clean up
        if os.path.exists(audio_path):
            os.remove(audio_path)

if __name__ == "__main__":
    asyncio.run(test_diarization())