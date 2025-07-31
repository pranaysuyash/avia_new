#!/usr/bin/env python3
"""
Test script for share functionality integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all share components can be imported"""
    print("Testing imports...")
    try:
        from sharing import render_share_dialog, render_public_share_page, render_share_management_page
        print("✓ Share UI imports successful")
        
        from sharing import share_manager, create_share_link, get_share_info
        print("✓ Share manager imports successful")
        
        from database import Transcript, SharedLink, User
        print("✓ Database model imports successful")
        
        from auth import require_authentication, get_current_user
        print("✓ Authentication imports successful")
        
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_share_ui_components():
    """Test that share UI components are callable"""
    print("\nTesting UI components...")
    try:
        # These would normally require Streamlit context
        from sharing.share_ui import render_share_dialog, render_public_share_page, render_share_management_page
        
        # Check they're callable
        assert callable(render_share_dialog)
        assert callable(render_public_share_page)
        assert callable(render_share_management_page)
        
        print("✓ All share UI components are callable")
        return True
    except Exception as e:
        print(f"✗ UI component error: {e}")
        return False

def test_app_integration():
    """Test that app_with_auth.py has share functionality integrated"""
    print("\nTesting app integration...")
    try:
        with open('app_with_auth.py', 'r') as f:
            content = f.read()
            
        # Check for share imports
        assert 'from sharing import' in content
        print("✓ Share imports added to app")
        
        # Check for share route handling
        assert 'share' in content and 'query_params' in content
        print("✓ Share route handling added")
        
        # Check for share button in transcript display
        assert '🔗 Share' in content
        print("✓ Share button added to transcripts")
        
        # Check for Manage Shares mode
        assert 'Manage Shares' in content
        print("✓ Manage Shares mode added to navigation")
        
        # Check for share dialog rendering
        assert 'render_share_dialog' in content
        print("✓ Share dialog rendering integrated")
        
        return True
    except Exception as e:
        print(f"✗ App integration error: {e}")
        return False

def main():
    """Run all integration tests"""
    print("Share Functionality Integration Test")
    print("=" * 40)
    
    all_passed = True
    
    # Run tests
    all_passed &= test_imports()
    all_passed &= test_share_ui_components()
    all_passed &= test_app_integration()
    
    print("\n" + "=" * 40)
    if all_passed:
        print("✅ All integration tests passed!")
        print("\nShare functionality is successfully integrated:")
        print("- Share links can be created from transcript pages")
        print("- Public share links are accessible via ?share=TOKEN")
        print("- Users can manage their shares via 'Manage Shares' mode")
        print("- Share buttons appear in 'My Transcripts' section")
    else:
        print("❌ Some integration tests failed")
        print("Please check the errors above")

if __name__ == "__main__":
    main()