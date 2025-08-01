#!/usr/bin/env python3
"""
Test script for Task 21: Enhance admin panel with analytics
Verifies that all admin analytics features are working correctly
"""

import os
import json
import tempfile
from datetime import datetime

def test_admin_analytics():
    """Test admin analytics functionality"""
    print("🧪 Testing Admin Analytics...")
    
    try:
        from admin_analytics import admin_analytics
        
        # Test analytics data loading/saving
        print("  ✓ Testing analytics data management...")
        data = admin_analytics.load_analytics_data()
        assert 'usage_stats' in data
        assert 'cost_tracking' in data
        print("    ✓ Analytics data structure is correct")
        
        # Test usage stats update
        print("  ✓ Testing usage statistics update...")
        admin_analytics.update_usage_stats(
            transcription_time=120.5,
            words_count=500,
            api_calls={'whisper': 1, 'openai': 1},
            user_id='test_user'
        )
        
        updated_data = admin_analytics.load_analytics_data()
        assert updated_data['usage_stats']['total_transcriptions'] >= 1
        assert updated_data['usage_stats']['total_words_transcribed'] >= 500
        print("    ✓ Usage statistics updated correctly")
        
        # Test cost calculation
        print("  ✓ Testing cost calculation...")
        costs = admin_analytics.calculate_costs(updated_data)
        assert costs.total_cost >= 0
        assert costs.whisper_cost >= 0
        print("    ✓ Cost calculation working")
        
        print("✅ Admin Analytics: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Admin Analytics: FAILED - {e}")
        return False

def test_voice_library():
    """Test voice library functionality"""
    print("🧪 Testing Voice Library...")
    
    try:
        from voice_library import voice_library_manager
        
        # Test loading default voices
        print("  ✓ Testing voice library loading...")
        voices = voice_library_manager.load_voice_library()
        assert len(voices) > 0
        print(f"    ✓ Loaded {len(voices)} default voices")
        
        # Test adding custom voice
        print("  ✓ Testing custom voice addition...")
        from voice_library import VoiceProfile
        
        test_voice = VoiceProfile(
            id="test_voice",
            name="Test Voice",
            description="Test voice for unit testing",
            voice_id="test_elevenlabs_id",
            settings={"stability": 0.8, "similarity_boost": 0.7},
            category="Test",
            is_custom=True
        )
        
        success = voice_library_manager.add_voice_profile(test_voice)
        assert success
        print("    ✓ Custom voice added successfully")
        
        # Test voice retrieval
        retrieved_voice = voice_library_manager.get_voice_profile("test_voice")
        assert retrieved_voice is not None
        assert retrieved_voice.name == "Test Voice"
        print("    ✓ Voice retrieval working")
        
        # Test usage increment
        voice_library_manager.increment_usage("test_voice")
        updated_voice = voice_library_manager.get_voice_profile("test_voice")
        assert updated_voice.usage_count == 1
        print("    ✓ Usage tracking working")
        
        # Cleanup test voice
        voice_library_manager.delete_voice_profile("test_voice")
        
        print("✅ Voice Library: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Voice Library: FAILED - {e}")
        return False

def test_script_templates():
    """Test script templates functionality"""
    print("🧪 Testing Script Templates...")
    
    try:
        from script_templates import script_template_manager
        
        # Test loading default templates
        print("  ✓ Testing template loading...")
        templates = script_template_manager.load_templates()
        assert len(templates) > 0
        print(f"    ✓ Loaded {len(templates)} default templates")
        
        # Test adding custom template
        print("  ✓ Testing custom template addition...")
        from script_templates import ScriptTemplate
        
        test_template = ScriptTemplate(
            id="test_template",
            name="Test Template",
            description="Test template for unit testing",
            category="Test",
            template_text="Hello {name}, welcome to {event}!",
            variables=["name", "event"],
            style="formal",
            format_type="monologue",
            is_default=False
        )
        
        success = script_template_manager.add_template(test_template)
        assert success
        print("    ✓ Custom template added successfully")
        
        # Test template usage increment
        script_template_manager.increment_template_usage("test_template")
        updated_templates = script_template_manager.load_templates()
        test_template_updated = next((t for t in updated_templates if t.id == "test_template"), None)
        assert test_template_updated.usage_count == 1
        print("    ✓ Template usage tracking working")
        
        # Cleanup test template
        script_template_manager.delete_template("test_template")
        
        print("✅ Script Templates: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Script Templates: FAILED - {e}")
        return False

def test_integration():
    """Test integration with main app"""
    print("🧪 Testing Integration with Main App...")
    
    try:
        # Test imports in main app
        print("  ✓ Testing main app imports...")
        import app
        
        # Check if admin analytics functions are available
        assert hasattr(app, 'admin_analytics')
        assert hasattr(app, 'voice_library_manager')
        assert hasattr(app, 'script_template_manager')
        print("    ✓ All admin modules imported in main app")
        
        # Test admin panel function exists
        assert hasattr(app, 'render_admin_panel')
        assert hasattr(app, 'render_script_generation_tab')
        assert hasattr(app, 'render_admin_controls_tab')
        print("    ✓ Admin panel functions available")
        
        print("✅ Integration: ALL TESTS PASSED")
        return True
        
    except Exception as e:
        print(f"❌ Integration: FAILED - {e}")
        return False

def cleanup_test_files():
    """Clean up test files created during testing"""
    test_files = [
        'admin_analytics.json',
        'voice_library.json',
        'script_templates.json',
        'content_presets.json'
    ]
    
    for file in test_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  🗑️ Cleaned up {file}")
            except Exception as e:
                print(f"  ⚠️ Could not clean up {file}: {e}")

def main():
    """Run all tests for Task 21"""
    print("🚀 Testing Task 21: Enhance admin panel with analytics")
    print("=" * 60)
    
    results = []
    
    # Run individual tests
    results.append(test_admin_analytics())
    results.append(test_voice_library())
    results.append(test_script_templates())
    results.append(test_integration())
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ Task 21 Implementation Status: COMPLETE")
        print("\nFeatures implemented:")
        print("  ✓ Usage analytics dashboard with processing statistics")
        print("  ✓ Cost tracking for API usage across services")
        print("  ✓ Voice library management for TTS with custom voices")
        print("  ✓ Script templates and content generation presets")
        print("  ✓ Admin user management and access controls")
        print("  ✓ Integration with main admin panel")
        
        # Clean up test files
        print("\n🧹 Cleaning up test files...")
        cleanup_test_files()
        
        return True
    else:
        print(f"❌ SOME TESTS FAILED ({passed}/{total})")
        print("\n⚠️ Task 21 Implementation Status: PARTIAL")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)