#!/usr/bin/env python3
"""
Test Security and Theme Integration
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_security_integration():
    """Test security manager integration"""
    print("🔒 Testing Security Integration...")
    
    try:
        from security_manager import SecurityManager, create_security_manager
        
        # Test security manager creation
        security_manager = create_security_manager()
        print("✅ Security manager created successfully")
        
        # Test encryption
        test_data = "This is sensitive test data"
        encrypted = security_manager.encryption_manager.encrypt_data(test_data)
        decrypted = security_manager.encryption_manager.decrypt_data(encrypted)
        assert decrypted == test_data
        print("✅ Encryption/decryption working")
        
        # Test user creation
        success = security_manager.access_control.create_user("test_user", "test_password", "user")
        print(f"✅ User creation: {success}")
        
        # Test authentication
        token = security_manager.access_control.authenticate_user("test_user", "test_password")
        print(f"✅ Authentication: {'Success' if token else 'Failed'}")
        
        # Test security status
        status = security_manager.get_security_status()
        print(f"✅ Security status: {len(status)} metrics")
        
        return True
        
    except Exception as e:
        print(f"❌ Security integration error: {e}")
        return False

def test_theme_integration():
    """Test theme manager integration"""
    print("\n🎨 Testing Theme Integration...")
    
    try:
        from theme_manager import ThemeManager, theme_manager
        
        # Test theme manager
        tm = ThemeManager()
        print("✅ Theme manager created successfully")
        
        # Test color conversions
        rgb = tm.hex_to_rgb("#FF0000")
        assert rgb == (255, 0, 0)
        print("✅ Color conversion working")
        
        # Test contrast calculation
        contrast = tm.calculate_contrast_ratio("#000000", "#FFFFFF")
        assert contrast > 20  # Should be 21:1
        print(f"✅ Contrast calculation: {contrast:.2f}:1")
        
        # Test accessibility rating
        rating, status = tm.get_accessibility_rating(contrast)
        assert rating == "AAA"
        print(f"✅ Accessibility rating: {rating} - {status}")
        
        # Test themes
        themes = tm.themes
        assert len(themes) >= 4
        print(f"✅ Available themes: {list(themes.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Theme integration error: {e}")
        return False

def test_ui_components():
    """Test UI component integration"""
    print("\n🖥️ Testing UI Components...")
    
    try:
        from security_ui import SecurityUI, render_privacy_notice
        from theme_manager import render_enhanced_metric
        
        # Test security UI
        security_ui = SecurityUI()
        print("✅ Security UI initialized")
        
        # Test function imports
        print("✅ UI components imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ UI component error: {e}")
        return False

def test_app_imports():
    """Test main app can import all components"""
    print("\n📱 Testing App Integration...")
    
    try:
        # Test critical imports that were failing
        from webhooks import WebhookEventType
        print("✅ WebhookEventType import fixed")
        
        from speaker_diarization.diarization_ui import DiarizationUI
        print("✅ DiarizationUI import working")
        
        # Test new imports
        from theme_manager import apply_custom_theme
        from security_ui import render_privacy_notice
        print("✅ New theme and security imports working")
        
        return True
        
    except Exception as e:
        print(f"❌ App integration error: {e}")
        return False

def test_dependencies():
    """Test all required dependencies"""
    print("\n📦 Testing Dependencies...")
    
    dependencies = [
        'cryptography',
        'streamlit', 
        'plotly',
        'pandas',
        'bcrypt',
        'jwt'
    ]
    
    missing = []
    for dep in dependencies:
        try:
            __import__(dep)
            print(f"✅ {dep}")
        except ImportError:
            print(f"❌ {dep} - MISSING")
            missing.append(dep)
    
    return len(missing) == 0

def main():
    """Run all integration tests"""
    print("🧪 Security and Theme Integration Test Suite")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("App Imports", test_app_imports),
        ("Security Integration", test_security_integration),
        ("Theme Integration", test_theme_integration),
        ("UI Components", test_ui_components)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<20}: {status}")
    
    print(f"\n🎯 OVERALL: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if all(results.values()):
        print("🎉 ALL TESTS PASSED! Integration successful.")
        print("\n🚀 Ready to run: streamlit run app.py")
    else:
        print("⚠️ Some tests failed. Check implementation details.")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILURE'}: Integration test {'completed successfully' if success else 'had failures'}")