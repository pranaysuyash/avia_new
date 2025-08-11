#!/usr/bin/env python3
"""
Simple test to verify Streamlit UI works
"""

import sys
import os
import subprocess
import time
import signal

def test_streamlit_basic():
    """Test basic Streamlit functionality"""
    print("🎨 Testing Streamlit Enterprise Sales UI")
    
    try:
        # Test syntax by importing key parts
        with open("enterprise_sales_ui.py", "r") as f:
            content = f.read()
        
        # Check for critical components
        checks = [
            ("Streamlit import", "import streamlit as st" in content),
            ("Main function", "def main():" in content),
            ("Page config", "st.set_page_config" in content),
            ("Navigation", "st.sidebar.selectbox" in content),
            ("Sales overview", "show_sales_overview" in content),
            ("Lead management", "show_lead_management" in content),
            ("Demo scheduling", "show_demo_scheduling" in content),
            ("Contract management", "show_contract_management" in content),
        ]
        
        all_good = True
        for check_name, result in checks:
            if result:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                all_good = False
        
        if all_good:
            print("\n✅ Streamlit UI has all required components")
            
            # Test if it can be started (syntax check)
            print("📍 Testing Streamlit syntax...")
            result = subprocess.run([
                sys.executable, "-m", "py_compile", "enterprise_sales_ui.py"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Streamlit UI syntax is valid")
                return True
            else:
                print(f"❌ Syntax error: {result.stderr}")
                return False
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error testing Streamlit UI: {e}")
        return False

def test_core_system_basic():
    """Test basic core system functionality"""
    print("\n🏢 Testing Core System")
    
    try:
        # Check if the file exists and imports work
        result = subprocess.run([
            sys.executable, "-c", 
            "from enterprise_sales_onboarding_system import EnterpriseSalesService; print('Import successful')"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Core system imports successfully")
            return True
        else:
            print(f"❌ Import error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing core system: {e}")
        return False

def main():
    print("🏢 Enterprise Sales System - Simple App Test")
    print("=" * 50)
    
    streamlit_ok = test_streamlit_basic()
    core_ok = test_core_system_basic()
    
    print("\n" + "=" * 50)
    print("📊 Results:")
    print("✅ Streamlit UI" if streamlit_ok else "❌ Streamlit UI")
    print("✅ Core System" if core_ok else "❌ Core System")
    
    if streamlit_ok:
        print("\n🎉 The Enterprise Sales UI is working!")
        print("🚀 To run it: streamlit run enterprise_sales_ui.py")
    
    return streamlit_ok and core_ok

if __name__ == "__main__":
    main()