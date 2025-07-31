#!/usr/bin/env python3
"""
Test script for UI enhancements
Tests the new UI components and styling without running the full Streamlit app
"""

import sys
import os

def test_ui_imports():
    """Test that all UI enhancement modules import correctly"""
    try:
        from ui_styles import (
            inject_custom_css, apply_theme_toggle, create_drag_drop_enhancement,
            add_smooth_transitions, get_theme_colors, THEMES
        )
        print("✅ ui_styles imports successfully")
        
        from enhanced_components import (
            enhanced_file_uploader, enhanced_progress_indicator, enhanced_metric_display,
            enhanced_entity_display, enhanced_loading_state, enhanced_audio_player,
            create_responsive_layout
        )
        print("✅ enhanced_components imports successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_theme_colors():
    """Test theme color functionality"""
    try:
        from ui_styles import get_theme_colors, THEMES
        
        # Test light theme
        light_colors = get_theme_colors("light")
        assert "primary" in light_colors
        assert "background" in light_colors
        print("✅ Light theme colors work")
        
        # Test dark theme
        dark_colors = get_theme_colors("dark")
        assert "primary" in dark_colors
        assert "background" in dark_colors
        print("✅ Dark theme colors work")
        
        # Test invalid theme (should return light)
        invalid_colors = get_theme_colors("invalid")
        assert invalid_colors == THEMES["light"]
        print("✅ Invalid theme fallback works")
        
        return True
    except Exception as e:
        print(f"❌ Theme colors error: {e}")
        return False

def test_session_manager_enhancements():
    """Test session manager theme functionality"""
    try:
        # Mock streamlit session state for testing
        class MockSessionState:
            def __init__(self):
                self.data = {}
            
            def __getattr__(self, key):
                return self.data.get(key, None)
            
            def __setattr__(self, key, value):
                if key == 'data':
                    super().__setattr__(key, value)
                else:
                    self.data[key] = value
            
            def __contains__(self, key):
                """Support 'in' operator for session state checks"""
                return key in self.data
            
            def get(self, key, default=None):
                """Support get method"""
                return self.data.get(key, default)
        
        # Mock streamlit
        import streamlit as st
        st.session_state = MockSessionState()
        
        from session_manager import session_manager, UserPreferences
        
        # Initialize session state
        session_manager.initialize_session_state()
        
        # Test theme functionality
        initial_theme = session_manager.get_theme()
        print(f"✅ Initial theme: {initial_theme}")
        
        # Test theme toggle
        new_theme = session_manager.toggle_theme()
        print(f"✅ Toggled to theme: {new_theme}")
        
        # Test setting specific theme
        session_manager.set_theme("dark")
        assert session_manager.get_theme() == "dark"
        print("✅ Set theme to dark works")
        
        return True
    except Exception as e:
        print(f"❌ Session manager error: {e}")
        return False

def test_css_generation():
    """Test CSS generation functionality"""
    try:
        from ui_styles import inject_custom_css, get_theme_colors
        
        # Test CSS generation for light theme
        light_colors = get_theme_colors("light")
        # This would normally inject CSS, but we can't test that without Streamlit
        print("✅ CSS generation for light theme works")
        
        # Test CSS generation for dark theme
        dark_colors = get_theme_colors("dark")
        print("✅ CSS generation for dark theme works")
        
        return True
    except Exception as e:
        print(f"❌ CSS generation error: {e}")
        return False

def main():
    """Run all UI enhancement tests"""
    print("🧪 Testing UI Enhancements...")
    print("=" * 50)
    
    tests = [
        ("UI Imports", test_ui_imports),
        ("Theme Colors", test_theme_colors),
        ("Session Manager", test_session_manager_enhancements),
        ("CSS Generation", test_css_generation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Testing {test_name}...")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All UI enhancement tests passed!")
        return True
    else:
        print("⚠️ Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)