#!/usr/bin/env python3
"""
Synchronous test for speaker diarization
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from speaker_diarization.providers.mock_provider import MockProvider

print("🎙️ Testing Speaker Diarization (Sync)")
print("=" * 50)

# Test mock provider directly
provider = MockProvider({'processing_delay': 0})
print("\n1. Testing MockProvider creation...")
print(f"✅ Provider created: {provider.name}")
print(f"✅ Provider available: {provider.is_available()}")

# Test segment generation
print("\n2. Testing segment generation...")
segments = provider._generate_mock_segments(60.0, 3)  # 60 seconds, 3 speakers
print(f"✅ Generated {len(segments)} segments")

for i, seg in enumerate(segments[:3]):
    print(f"   {i+1}. Speaker {seg['speaker']} [{seg['start']:.1f}s - {seg['end']:.1f}s]")

print("\n✅ Diarization test completed successfully!")