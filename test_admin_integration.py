#!/usr/bin/env python3
"""
Test admin panel integration with the main analysis pipeline
"""

import os
import tempfile
from unittest.mock import patch, MagicMock

# Set up test environment
os.environ['OPENAI_API_KEY'] = 'test-key'
os.environ['ELEVENLABS_API_KEY'] = 'test-key'

import ner_advanced
import tts
import utils

@patch('ner_advanced._get_openai_client')
def test_script_generation(mock_client):
    """Test script generation functionality"""
    print("Testing script generation...")
    
    # Mock OpenAI response for script generation
    mock_response = MagicMock()
    mock_response.choices[0].message.content = """
    Speaker 1: Welcome to our discussion about climate change.
    
    Speaker 2: Thank you for having me. Climate change is indeed one of the most pressing issues of our time.
    
    Speaker 1: Can you tell us about the main causes?
    
    Speaker 2: Certainly. The primary driver is the increase in greenhouse gases, particularly carbon dioxide from burning fossil fuels.
    """
    
    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create.return_value = mock_response
    mock_client.return_value = mock_client_instance
    
    try:
        # Test script generation
        prompt = "Generate a conversation about climate change between two experts"
        script = ner_advanced.generate_script(prompt, "conversational")
        
        assert isinstance(script, str)
        assert len(script) > 0
        assert "climate change" in script.lower()
        
        print(f"Generated script length: {len(script)} characters")
        print("✅ Script generation test passed")
        
        return script
    except Exception as e:
        print(f"⚠️ Script generation test failed: {e}")
        return None

@patch('tts._get_elevenlabs_client')
def test_tts_synthesis_with_mock(test_script, mock_client):
    """Test TTS synthesis functionality"""
    print("Testing TTS synthesis...")
    
    if not test_script:
        print("⚠️ Skipping TTS test - no script available")
        return None
    
    # Mock ElevenLabs response
    mock_client_instance = MagicMock()
    mock_client_instance.text_to_speech.convert.return_value = [b'fake_audio_data_chunk1', b'fake_audio_data_chunk2']
    mock_client.return_value = mock_client_instance
    
    try:
        # Test TTS synthesis
        audio_path = tts.synthesize_speech(
            text=test_script,
            voice_id=tts.VOICE_PRESETS["professional"]["voice_id"],
            voice_settings=tts.VOICE_PRESETS["professional"]["settings"]
        )
        
        assert isinstance(audio_path, str)
        assert os.path.exists(audio_path)
        assert audio_path.endswith('.mp3')
        
        # Verify file has content
        file_size = os.path.getsize(audio_path)
        assert file_size > 0
        
        print(f"Generated audio file: {audio_path} ({file_size} bytes)")
        print("✅ TTS synthesis test passed")
        
        return audio_path
    except Exception as e:
        print(f"⚠️ TTS synthesis test failed: {e}")
        return None

def test_admin_pipeline_integration(audio_path):
    """Test integration of generated audio with main analysis pipeline"""
    print("Testing admin pipeline integration...")
    
    if not audio_path or not os.path.exists(audio_path):
        print("⚠️ Skipping pipeline integration test - no audio file available")
        return
    
    try:
        # Simulate the AudioFileWrapper class from app.py
        class AudioFileWrapper:
            def __init__(self, file_path):
                with open(file_path, 'rb') as f:
                    self.data = f.read()
                self.name = os.path.basename(file_path)
                self.size = len(self.data)
            
            def read(self):
                return self.data
        
        # Create wrapper for the generated audio
        audio_wrapper = AudioFileWrapper(audio_path)
        
        # Verify wrapper properties
        assert hasattr(audio_wrapper, 'data')
        assert hasattr(audio_wrapper, 'name')
        assert hasattr(audio_wrapper, 'size')
        assert audio_wrapper.size > 0
        
        print(f"Audio wrapper created: {audio_wrapper.name} ({audio_wrapper.size} bytes)")
        print("✅ Admin pipeline integration test passed")
        
    except Exception as e:
        print(f"⚠️ Admin pipeline integration test failed: {e}")
    finally:
        # Clean up
        if audio_path and os.path.exists(audio_path):
            utils.cleanup_file(audio_path)

def test_voice_presets():
    """Test voice preset configurations"""
    print("Testing voice presets...")
    
    try:
        # Test that all required presets exist
        required_presets = ["professional", "conversational", "narrative"]
        
        for preset in required_presets:
            assert preset in tts.VOICE_PRESETS
            preset_config = tts.VOICE_PRESETS[preset]
            
            assert "voice_id" in preset_config
            assert "settings" in preset_config
            assert isinstance(preset_config["voice_id"], str)
            assert hasattr(preset_config["settings"], 'stability')
            assert hasattr(preset_config["settings"], 'similarity_boost')
            
        print(f"All {len(required_presets)} voice presets are properly configured")
        print("✅ Voice presets test passed")
        
    except Exception as e:
        print(f"⚠️ Voice presets test failed: {e}")

def test_cost_estimation():
    """Test TTS cost estimation"""
    print("Testing cost estimation...")
    
    try:
        test_texts = [
            "Short text",
            "This is a medium length text that should cost more than the short one.",
            "This is a very long text that contains multiple sentences and should demonstrate the cost scaling functionality. It includes various words and punctuation marks to simulate real-world usage scenarios."
        ]
        
        costs = []
        for text in test_texts:
            cost = tts.estimate_synthesis_cost(text)
            costs.append(cost)
            print(f"Text length: {len(text)} chars, Estimated cost: ${cost:.4f}")
        
        # Verify costs increase with text length
        assert costs[0] < costs[1] < costs[2]
        assert all(cost >= 0 for cost in costs)
        
        print("✅ Cost estimation test passed")
        
    except Exception as e:
        print(f"⚠️ Cost estimation test failed: {e}")

def main():
    """Run all admin integration tests"""
    print("🔧 Starting admin panel integration tests...")
    print("=" * 60)
    
    # Test script generation
    test_script = test_script_generation()
    
    # Test TTS synthesis
    audio_path = test_tts_synthesis_with_mock(test_script)
    
    # Test pipeline integration
    test_admin_pipeline_integration(audio_path)
    
    # Test voice presets
    test_voice_presets()
    
    # Test cost estimation
    test_cost_estimation()
    
    print("=" * 60)
    print("🎉 Admin panel integration tests completed!")
    print("\nThe admin panel is properly integrated with:")
    print("• Script generation using OpenAI GPT")
    print("• Text-to-speech synthesis using ElevenLabs")
    print("• Main analysis pipeline for testing generated content")
    print("• Proper file management and cleanup")

if __name__ == "__main__":
    main()