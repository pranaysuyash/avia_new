#!/usr/bin/env python3
"""
Test script for admin panel functionality
"""

import os
import sys
import tempfile
from unittest.mock import Mock, patch, MagicMock

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_admin_panel_imports():
    """Test that all admin panel related modules can be imported"""
    try:
        import ner_advanced
        import tts
        import utils
        print("✅ All admin panel modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_script_generation():
    """Test script generation functionality"""
    try:
        import ner_advanced
        
        # Mock the OpenAI client to avoid API calls
        with patch('ner_advanced.client') as mock_client:
            # Mock response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = "This is a test script about climate change."
            mock_client.chat.completions.create.return_value = mock_response
            
            # Test script generation
            script = ner_advanced.generate_script("Generate a conversation about climate change", "conversational")
            
            assert script == "This is a test script about climate change."
            print("✅ Script generation test passed")
            return True
            
    except Exception as e:
        print(f"❌ Script generation test failed: {e}")
        return False

def test_tts_voice_presets():
    """Test that TTS voice presets are properly configured"""
    try:
        import tts
        
        # Check that voice presets exist
        assert hasattr(tts, 'VOICE_PRESETS')
        assert 'professional' in tts.VOICE_PRESETS
        assert 'conversational' in tts.VOICE_PRESETS
        assert 'narrative' in tts.VOICE_PRESETS
        
        # Check preset structure
        for preset_name, preset_config in tts.VOICE_PRESETS.items():
            assert 'voice_id' in preset_config
            assert 'settings' in preset_config
            assert hasattr(preset_config['settings'], 'stability')
            assert hasattr(preset_config['settings'], 'similarity_boost')
        
        print("✅ TTS voice presets test passed")
        return True
        
    except Exception as e:
        print(f"❌ TTS voice presets test failed: {e}")
        return False

def test_utils_functions():
    """Test utility functions used by admin panel"""
    try:
        import utils
        
        # Test temp directory creation
        temp_dir = utils.ensure_temp_directory()
        assert os.path.exists(temp_dir)
        
        # Test file cleanup
        test_file = os.path.join(temp_dir, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("test content")
        
        assert os.path.exists(test_file)
        utils.cleanup_file(test_file)
        assert not os.path.exists(test_file)
        
        print("✅ Utils functions test passed")
        return True
        
    except Exception as e:
        print(f"❌ Utils functions test failed: {e}")
        return False

def test_admin_panel_integration():
    """Test admin panel integration with main app"""
    try:
        # Mock streamlit to avoid GUI dependencies
        with patch('streamlit.header'), \
             patch('streamlit.warning'), \
             patch('streamlit.subheader'), \
             patch('streamlit.columns'), \
             patch('streamlit.text_area'), \
             patch('streamlit.selectbox'), \
             patch('streamlit.button'), \
             patch('streamlit.spinner'), \
             patch('streamlit.success'), \
             patch('streamlit.error'), \
             patch('streamlit.info'), \
             patch('streamlit.metric'), \
             patch('streamlit.audio'), \
             patch('streamlit.download_button'), \
             patch('streamlit.expander'), \
             patch('streamlit.markdown'), \
             patch('streamlit.session_state', new_callable=lambda: MagicMock()):
            
            # Import and test admin panel functions
            import app
            
            # Test that admin panel functions exist
            assert hasattr(app, 'render_admin_panel')
            assert hasattr(app, 'generate_admin_script')
            assert hasattr(app, 'convert_script_to_speech')
            assert hasattr(app, 'test_generated_audio_with_pipeline')
            assert hasattr(app, 'cleanup_generated_audio')
            
            print("✅ Admin panel integration test passed")
            return True
            
    except Exception as e:
        print(f"❌ Admin panel integration test failed: {e}")
        return False

def main():
    """Run all admin panel tests"""
    print("🧪 Testing Admin Panel Functionality")
    print("=" * 50)
    
    tests = [
        test_admin_panel_imports,
        test_script_generation,
        test_tts_voice_presets,
        test_utils_functions,
        test_admin_panel_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All admin panel tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)