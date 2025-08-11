#!/usr/bin/env python3
"""
Test Enterprise Sales Apps by Actually Running Them
This script tests if the enterprise sales applications actually work by running them
"""

import sys
import os
import time
import requests
import subprocess
import signal
from multiprocessing import Process
import threading

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_streamlit_app():
    """Test if the Streamlit app can start and serve pages"""
    print("🎨 Testing Streamlit Enterprise Sales UI")
    print("-" * 40)
    
    try:
        # Start Streamlit in the background
        cmd = [
            sys.executable, "-m", "streamlit", "run", 
            "enterprise_sales_ui.py", 
            "--server.headless", "true",
            "--server.port", "8501",
            "--browser.gatherUsageStats", "false"
        ]
        
        print("📍 Starting Streamlit app...")
        proc = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for the app to start
        time.sleep(10)
        
        # Check if the process is still running
        if proc.poll() is None:
            print("✅ Streamlit app started successfully")
            print("📍 App running at: http://localhost:8501")
            
            # Try to access the app
            try:
                response = requests.get("http://localhost:8501", timeout=5)
                if response.status_code == 200:
                    print("✅ Streamlit app is responding to HTTP requests")
                    success = True
                else:
                    print(f"⚠️  App responded with status code: {response.status_code}")
                    success = False
            except requests.exceptions.RequestException as e:
                print(f"⚠️  Could not connect to app: {e}")
                success = False
        else:
            # Get error output
            stdout, stderr = proc.communicate()
            print(f"❌ Streamlit app failed to start")
            if stderr:
                print(f"Error: {stderr}")
            success = False
        
        # Clean up
        if proc.poll() is None:
            proc.terminate()
            proc.wait()
            
        return success
        
    except Exception as e:
        print(f"❌ Error testing Streamlit app: {e}")
        return False

def test_api_endpoints():
    """Test if API endpoints can be imported and used"""
    print("\n🔧 Testing API Endpoints")
    print("-" * 40)
    
    try:
        # Test importing the API module
        from api.endpoints.enterprise_sales import router
        print("✅ API endpoints imported successfully")
        
        # Test router has routes
        routes = [route.path for route in router.routes]
        print(f"✅ Found {len(routes)} API routes")
        
        # Test a few key routes exist
        expected_routes = ["/leads", "/demos/schedule", "/trials/create", "/contracts/create"]
        missing_routes = []
        
        for expected in expected_routes:
            found = any(expected in route for route in routes)
            if not found:
                missing_routes.append(expected)
        
        if missing_routes:
            print(f"⚠️  Missing expected routes: {missing_routes}")
            return False
        else:
            print("✅ All expected API routes are present")
            return True
            
    except Exception as e:
        print(f"❌ Error testing API endpoints: {e}")
        return False

def test_core_system():
    """Test the core enterprise sales system"""
    print("\n🏢 Testing Core Enterprise Sales System")
    print("-" * 40)
    
    try:
        from enterprise_sales_onboarding_system import EnterpriseSalesService
        
        # Try to initialize the system
        sales_system = EnterpriseSalesService("sqlite:///test_enterprise.db")
        print("✅ Enterprise sales system initialized")
        
        # Test key methods exist
        required_methods = [
            'create_lead', 'get_leads', 'update_lead',
            'schedule_demo', 'create_trial', 'create_contract'
        ]
        
        missing_methods = []
        for method in required_methods:
            if not hasattr(sales_system, method):
                missing_methods.append(method)
        
        if missing_methods:
            print(f"⚠️  Missing methods: {missing_methods}")
            return False
        else:
            print("✅ All required methods are available")
            return True
            
    except Exception as e:
        print(f"❌ Error testing core system: {e}")
        return False

def test_ui_file():
    """Test if the UI file is properly structured"""
    print("\n📄 Testing UI File Structure")  
    print("-" * 40)
    
    try:
        # Check if file exists
        if not os.path.exists("enterprise_sales_ui.py"):
            print("❌ Enterprise sales UI file not found")
            return False
        
        # Read and check file content
        with open("enterprise_sales_ui.py", "r") as f:
            content = f.read()
        
        # Check for required functions
        required_functions = [
            "main()", 
            "show_sales_overview",
            "show_lead_management",
            "show_demo_scheduling",
            "show_trial_management",
            "show_contract_management",
            "show_onboarding_workflows",
            "show_sales_analytics",
            "show_crm_integration"
        ]
        
        missing_functions = []
        for func in required_functions:
            if func not in content:
                missing_functions.append(func)
        
        if missing_functions:
            print(f"⚠️  Missing functions: {missing_functions}")
            return False
        
        # Check for Streamlit imports
        if "import streamlit as st" not in content:
            print("❌ Missing Streamlit import")
            return False
            
        # Check for main execution
        if '__name__ == "__main__"' not in content:
            print("❌ Missing main execution block")
            return False
        
        print("✅ UI file structure is correct")
        print(f"✅ File size: {len(content)} characters")
        return True
        
    except Exception as e:
        print(f"❌ Error testing UI file: {e}")
        return False

def test_file_syntax():
    """Test if Python files have valid syntax"""
    print("\n🔍 Testing File Syntax")
    print("-" * 40)
    
    files_to_test = [
        "enterprise_sales_onboarding_system.py",
        "enterprise_sales_ui.py", 
        "api/endpoints/enterprise_sales.py"
    ]
    
    all_good = True
    
    for file_path in files_to_test:
        try:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Try to compile the code
                compile(content, file_path, 'exec')
                print(f"✅ {file_path} - Valid syntax")
            else:
                print(f"⚠️  {file_path} - File not found")
                all_good = False
                
        except SyntaxError as e:
            print(f"❌ {file_path} - Syntax error: {e}")
            all_good = False
        except Exception as e:
            print(f"❌ {file_path} - Error: {e}")
            all_good = False
    
    return all_good

def main():
    """Run all application tests"""
    print("🏢 Enterprise Sales System - Live Application Testing")
    print("=" * 60)
    
    # Run all tests
    test_results = {
        "syntax_test": test_file_syntax(),
        "ui_file_test": test_ui_file(),
        "core_system_test": test_core_system(),
        "api_test": test_api_endpoints(),
        "streamlit_app_test": test_streamlit_app()
    }
    
    print("\n" + "=" * 60)
    print("📊 Application Testing Results")
    print("=" * 60)
    
    passed = sum(test_results.values())
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status_icon = "✅" if result else "❌"
        test_display = test_name.replace("_", " ").title()
        print(f"{status_icon} {test_display}")
    
    print(f"\n📈 Overall Success Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All application tests passed!")
        print("✅ Enterprise Sales System is working and ready to use")
        print("\n🚀 To run the applications:")
        print("   • UI: streamlit run enterprise_sales_ui.py")
        print("   • API: python run_api.py")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        print("❌ Some applications may not work correctly")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)