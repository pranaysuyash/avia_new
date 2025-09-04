#!/usr/bin/env python3
"""
Test script for spatial audio format conversions
"""

import numpy as np
import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from spatial_audio_processor import SpatialAudioProcessor, SpatialFormat

async def test_format_conversions():
    """Test the new format conversion implementations"""
    print("Testing Spatial Audio Format Conversions")
    print("=" * 50)
    
    processor = SpatialAudioProcessor()
    
    # Create test stereo audio data
    # 2 channels, 44100 Hz, 1 second of audio
    sample_rate = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create simple test signals
    left_channel = np.sin(2 * np.pi * 440 * t)  # 440 Hz sine wave
    right_channel = np.sin(2 * np.pi * 880 * t)  # 880 Hz sine wave
    stereo_audio = np.array([left_channel, right_channel])
    
    print(f"Created test stereo audio: {stereo_audio.shape}")
    
    # Test conversions from stereo to advanced formats
    print("\nTesting stereo to advanced format conversions:")
    
    # Test stereo to DOLBY_ATMOS
    try:
        atmos_audio = processor._stereo_to_dolby_atmos(stereo_audio)
        print(f"  Stereo to Dolby Atmos: {stereo_audio.shape} -> {atmos_audio.shape}")
    except Exception as e:
        print(f"  Stereo to Dolby Atmos: FAILED - {e}")
    
    # Test stereo to DTS_X
    try:
        dts_x_audio = processor._stereo_to_dts_x(stereo_audio)
        print(f"  Stereo to DTS:X: {stereo_audio.shape} -> {dts_x_audio.shape}")
    except Exception as e:
        print(f"  Stereo to DTS:X: FAILED - {e}")
    
    # Test stereo to AMBISONICS_HOA
    try:
        hoa_audio = processor._stereo_to_ambisonics_hoa(stereo_audio)
        print(f"  Stereo to Ambisonics HOA: {stereo_audio.shape} -> {hoa_audio.shape}")
    except Exception as e:
        print(f"  Stereo to Ambisonics HOA: FAILED - {e}")
    
    # Test stereo to QUAD
    try:
        quad_audio = processor._stereo_to_quad(stereo_audio)
        print(f"  Stereo to Quad: {stereo_audio.shape} -> {quad_audio.shape}")
    except Exception as e:
        print(f"  Stereo to Quad: FAILED - {e}")
    
    # Test the reverse conversions
    print("\nTesting advanced format to stereo conversions:")
    
    # Test Dolby Atmos to stereo
    try:
        atmos_to_stereo = processor._dolby_atmos_to_stereo(atmos_audio)
        print(f"  Dolby Atmos to Stereo: {atmos_audio.shape} -> {atmos_to_stereo.shape}")
    except Exception as e:
        print(f"  Dolby Atmos to Stereo: FAILED - {e}")
    
    # Test DTS:X to stereo
    try:
        dts_x_to_stereo = processor._dts_x_to_stereo(dts_x_audio)
        print(f"  DTS:X to Stereo: {dts_x_audio.shape} -> {dts_x_to_stereo.shape}")
    except Exception as e:
        print(f"  DTS:X to Stereo: FAILED - {e}")
    
    # Test Ambisonics HOA to stereo
    try:
        hoa_to_stereo = processor._ambisonics_hoa_to_stereo(hoa_audio)
        print(f"  Ambisonics HOA to Stereo: {hoa_audio.shape} -> {hoa_to_stereo.shape}")
    except Exception as e:
        print(f"  Ambisonics HOA to Stereo: FAILED - {e}")
    
    # Test Quad to stereo
    try:
        quad_to_stereo = processor._quad_to_stereo(quad_audio)
        print(f"  Quad to Stereo: {quad_audio.shape} -> {quad_to_stereo.shape}")
    except Exception as e:
        print(f"  Quad to Stereo: FAILED - {e}")
    
    # Test some cross-conversions
    print("\nTesting cross-format conversions:")
    
    # Test 5.1 to DOLBY_ATMOS
    try:
        surround_5_1 = processor._stereo_to_5_1(stereo_audio)
        atmos_from_5_1 = processor._5_1_to_dolby_atmos(surround_5_1)
        print(f"  5.1 to Dolby Atmos: {surround_5_1.shape} -> {atmos_from_5_1.shape}")
    except Exception as e:
        print(f"  5.1 to Dolby Atmos: FAILED - {e}")
    
    # Test AMBISONICS_FOA to AMBISONICS_HOA
    try:
        foa_audio = processor._stereo_to_ambisonics_foa(stereo_audio)
        hoa_from_foa = processor._ambisonics_foa_to_ambisonics_hoa(foa_audio)
        print(f"  FOA to HOA: {foa_audio.shape} -> {hoa_from_foa.shape}")
    except Exception as e:
        print(f"  FOA to HOA: FAILED - {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    asyncio.run(test_format_conversions())
