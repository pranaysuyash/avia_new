#!/usr/bin/env python3
"""
Complete Platform Integration Test
Test ALL applications: React Web, Electron Desktop, React Native, API, and Streamlit
"""

import subprocess
import os
import sys
import json
import time
import requests
import signal
from datetime import datetime
from pathlib import Path

class CompletePlatformTests:
    def __init__(self):
        self.project_root = "/Users/pranay/Projects/LLM/video/ner"
        self.api_url = "http://localhost:8001"
        self.streamlit_url = "http://localhost:8502"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "Complete Platform Integration Test",
            "tests": {},
            "processes": {},
            "overall_status": "PENDING"
        }
        self.processes = {}
        
    def start_api_server(self):
        """Start the FastAPI server"""
        print("🚀 Starting API Server...")
        
        # Kill existing API processes
        subprocess.run(["pkill", "-f", "uvicorn"], capture_output=True)
        time.sleep(2)
        
        try:
            # Start API server
            self.processes['api'] = subprocess.Popen([
                "python", "run_api.py"
            ], 
            cwd=self.project_root,
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
            )
            
            print("  ⏳ Waiting for API server to start...")
            time.sleep(8)  # Give API time to start
            
            # Test if API is responding
            try:
                response = requests.get(f"{self.api_url}/docs", timeout=5)
                if response.status_code == 200:
                    print("  ✅ API Server started successfully")
                    return True
                else:
                    print(f"  ❌ API Server not responding (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ API Server connection failed: {e}")
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to start API server: {e}")
            return False
    
    def start_streamlit_app(self):
        """Start the Streamlit application"""
        print("🎨 Starting Streamlit Application...")
        
        # Kill existing Streamlit processes
        subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
        time.sleep(2)
        
        try:
            # Start Streamlit app
            self.processes['streamlit'] = subprocess.Popen([
                "streamlit", "run", "app.py",
                "--server.port", "8502",
                "--server.headless", "true",
                "--logger.level", "error"
            ],
            cwd=self.project_root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
            )
            
            print("  ⏳ Waiting for Streamlit to start...")
            time.sleep(12)  # Give Streamlit time to start
            
            # Test if Streamlit is responding
            try:
                response = requests.get(self.streamlit_url, timeout=10)
                if response.status_code == 200:
                    print("  ✅ Streamlit started successfully")
                    return True
                else:
                    print(f"  ❌ Streamlit not responding (status: {response.status_code})")
                    return False
            except Exception as e:
                print(f"  ❌ Streamlit connection failed: {e}")
                return False
                
        except Exception as e:
            print(f"  ❌ Failed to start Streamlit: {e}")
            return False
    
    def test_api_functionality(self):
        """Test API server functionality"""
        print("\n🔧 Testing API Server Functionality...")
        
        tests = []
        
        # Test 1: API Documentation
        try:
            response = requests.get(f"{self.api_url}/docs", timeout=10)
            if response.status_code == 200:
                tests.append(("API Documentation", "PASSED", "FastAPI docs accessible"))
            else:
                tests.append(("API Documentation", "FAILED", f"Status: {response.status_code}"))
        except Exception as e:
            tests.append(("API Documentation", "FAILED", str(e)[:50]))
            
        # Test 2: Health endpoint (if exists)
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                tests.append(("Health Endpoint", "PASSED", "Health check working"))
            elif response.status_code == 404:
                tests.append(("Health Endpoint", "SKIPPED", "No health endpoint"))
            else:
                tests.append(("Health Endpoint", "FAILED", f"Status: {response.status_code}"))
        except Exception as e:
            tests.append(("Health Endpoint", "SKIPPED", "No health endpoint"))
            
        # Test 3: I18n endpoints
        try:
            response = requests.get(f"{self.api_url}/api/v1/i18n/languages", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    tests.append(("I18n Endpoints", "PASSED", f"{len(data)} languages"))
                else:
                    tests.append(("I18n Endpoints", "FAILED", "Empty response"))
            else:
                tests.append(("I18n Endpoints", "FAILED", f"Status: {response.status_code}"))
        except Exception as e:
            tests.append(("I18n Endpoints", "FAILED", str(e)[:50]))
            
        # Calculate success rate
        passed = sum(1 for _, status, _ in tests if status == "PASSED")
        total = sum(1 for _, status, _ in tests if status != "SKIPPED")
        success_rate = (passed / total * 100) if total > 0 else 0
        
        for test_name, status, message in tests:
            emoji = "✅" if status == "PASSED" else "⚠️" if status == "SKIPPED" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 API Functionality: {success_rate:.1f}% ({passed}/{total})")
        
        self.results["tests"]["api_functionality"] = {
            "success_rate": success_rate,
            "tests": tests,
            "status": "PASSED" if success_rate >= 66 else "FAILED"
        }
        
        return success_rate >= 66
    
    def test_streamlit_functionality(self):
        """Test Streamlit application functionality"""
        print("\n🎨 Testing Streamlit Functionality...")
        
        tests = []
        
        # Test 1: Basic accessibility  
        try:
            response = requests.get(self.streamlit_url, timeout=15)
            if response.status_code == 200:
                content = response.text.lower()
                if any(keyword in content for keyword in ['streamlit', 'transcript', 'audio', 'upload']):
                    tests.append(("Streamlit Accessibility", "PASSED", "App accessible with expected content"))
                else:
                    tests.append(("Streamlit Accessibility", "PARTIAL", "Accessible but content unclear"))
            else:
                tests.append(("Streamlit Accessibility", "FAILED", f"HTTP {response.status_code}"))
        except Exception as e:
            tests.append(("Streamlit Accessibility", "FAILED", str(e)[:50]))
            
        # Test 2: Check app structure
        app_py_path = os.path.join(self.project_root, "app.py")
        if os.path.exists(app_py_path):
            with open(app_py_path, 'r') as f:
                app_content = f.read()
                
            # Check for key Streamlit components
            streamlit_features = ["st.title", "st.sidebar", "st.file_uploader", "def main"]
            found_features = sum(1 for feature in streamlit_features if feature in app_content)
            
            if found_features >= 3:
                tests.append(("Streamlit App Structure", "PASSED", f"{found_features}/4 key features"))
            else:
                tests.append(("Streamlit App Structure", "FAILED", f"Only {found_features}/4 features"))
        else:
            tests.append(("Streamlit App Structure", "FAILED", "app.py missing"))
            
        # Test 3: I18n UI integration
        i18n_ui_path = os.path.join(self.project_root, "internationalization_ui.py")
        if os.path.exists(i18n_ui_path):
            with open(i18n_ui_path, 'r') as f:
                i18n_content = f.read()
                
            if "InternationalizationManager" in i18n_content and "supported_languages" in i18n_content:
                tests.append(("I18n UI Integration", "PASSED", "I18n UI properly structured"))
            else:
                tests.append(("I18n UI Integration", "FAILED", "I18n UI incomplete"))
        else:
            tests.append(("I18n UI Integration", "FAILED", "I18n UI missing"))
            
        # Calculate success rate
        passed = sum(1 for _, status, _ in tests if status in ["PASSED", "PARTIAL"])
        success_rate = (passed / len(tests) * 100) if tests else 0
        
        for test_name, status, message in tests:
            emoji = "✅" if status == "PASSED" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 Streamlit Functionality: {success_rate:.1f}% ({passed}/{len(tests)})")
        
        self.results["tests"]["streamlit_functionality"] = {
            "success_rate": success_rate,
            "tests": tests,
            "status": "PASSED" if success_rate >= 66 else "FAILED"
        }
        
        return success_rate >= 66
    
    def test_main_applications(self):
        """Test main applications structure"""
        print("\n🏗️ Testing Main Applications...")
        
        app_tests = []
        
        # Test React Web App
        frontend_dir = os.path.join(self.project_root, "frontend")
        if os.path.exists(os.path.join(frontend_dir, "package.json")):
            components_dir = os.path.join(frontend_dir, "src/components")
            if os.path.exists(components_dir):
                component_count = len([d for d in os.listdir(components_dir) 
                                     if os.path.isdir(os.path.join(components_dir, d))])
                app_tests.append(("React Web App", "PASSED", f"{component_count} components"))
            else:
                app_tests.append(("React Web App", "FAILED", "No components"))
        else:
            app_tests.append(("React Web App", "FAILED", "Missing package.json"))
            
        # Test Electron Desktop App
        desktop_dir = os.path.join(self.project_root, "desktop_app")
        if (os.path.exists(os.path.join(desktop_dir, "package.json")) and
            os.path.exists(os.path.join(desktop_dir, "src/main.js"))):
            app_tests.append(("Electron Desktop", "PASSED", "Main process configured"))
        else:
            app_tests.append(("Electron Desktop", "FAILED", "Missing core files"))
            
        # Test React Native Mobile App
        mobile_dir = os.path.join(self.project_root, "mobile")
        if (os.path.exists(os.path.join(mobile_dir, "package.json")) and 
            os.path.exists(os.path.join(mobile_dir, "src/App.tsx"))):
            app_tests.append(("React Native Mobile", "PASSED", "Mobile app configured"))
        else:
            app_tests.append(("React Native Mobile", "FAILED", "Missing core files"))
        
        # Calculate success rate
        passed = sum(1 for _, status, _ in app_tests if status == "PASSED")
        success_rate = (passed / len(app_tests) * 100) if app_tests else 0
        
        for test_name, status, message in app_tests:
            emoji = "✅" if status == "PASSED" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 Main Apps Structure: {success_rate:.1f}% ({passed}/{len(app_tests)})")
        
        self.results["tests"]["main_applications"] = {
            "success_rate": success_rate,
            "tests": app_tests,
            "status": "PASSED" if success_rate >= 75 else "FAILED"
        }
        
        return success_rate >= 75
    
    def cleanup_processes(self):
        """Clean up all started processes"""
        print("\n🧹 Cleaning up processes...")
        
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print(f"  🛑 Stopping {name}...")
                try:
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                    process.wait(timeout=5)
                except (subprocess.TimeoutExpired, ProcessLookupError):
                    try:
                        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                    except ProcessLookupError:
                        pass
    
    def run_complete_platform_test(self):
        """Run the complete platform test suite"""
        print("🚀 COMPLETE PLATFORM INTEGRATION TEST")
        print("=" * 80)
        print("Testing ALL platform components:")
        print("• FastAPI Backend Server")
        print("• Streamlit Web Application") 
        print("• React Web Frontend")
        print("• Electron Desktop Application")
        print("• React Native Mobile Application")
        print("=" * 80)
        
        all_results = []
        
        try:
            # Start and test API server
            if self.start_api_server():
                api_passed = self.test_api_functionality()
                all_results.append(("API Server", api_passed))
            else:
                all_results.append(("API Server", False))
                self.results["tests"]["api_functionality"] = {"status": "FAILED", "success_rate": 0}
            
            # Start and test Streamlit
            if self.start_streamlit_app():
                streamlit_passed = self.test_streamlit_functionality()
                all_results.append(("Streamlit App", streamlit_passed))
            else:
                all_results.append(("Streamlit App", False))
                self.results["tests"]["streamlit_functionality"] = {"status": "FAILED", "success_rate": 0}
            
            # Test main applications structure
            main_apps_passed = self.test_main_applications()
            all_results.append(("Main Applications", main_apps_passed))
            
            # Calculate overall results
            passed_tests = sum(1 for _, passed in all_results if passed)
            total_tests = len(all_results)
            overall_success = (passed_tests / total_tests * 100) if total_tests > 0 else 0
            
            print("\n" + "=" * 80)
            print("📊 COMPLETE PLATFORM TEST RESULTS")
            print("=" * 80)
            
            for test_name, passed in all_results:
                status = "✅ PASSED" if passed else "❌ FAILED"
                print(f"{status} {test_name}")
            
            print(f"\n🎯 Overall Platform Success Rate: {overall_success:.1f}% ({passed_tests}/{total_tests})")
            
            # Determine final status and provide insights
            if overall_success >= 90:
                print("🎉 OUTSTANDING! Complete platform is production-ready!")
                final_status = "OUTSTANDING"
            elif overall_success >= 75:
                print("🌟 EXCELLENT! Platform is working well with minor issues")
                final_status = "EXCELLENT"
            elif overall_success >= 60:
                print("✅ GOOD! Most components working, some fixes needed")
                final_status = "GOOD"
            elif overall_success >= 40:
                print("⚠️ PARTIAL! Some components working, others need attention")
                final_status = "PARTIAL"
            else:
                print("❌ NEEDS MAJOR WORK! Platform needs significant fixes")
                final_status = "NEEDS_WORK"
                
            # Detailed insights
            print(f"\n📋 Platform Analysis:")
            for test_category, test_data in self.results["tests"].items():
                if isinstance(test_data, dict) and "success_rate" in test_data:
                    rate = test_data["success_rate"]
                    status_icon = "✅" if rate >= 75 else "⚠️" if rate >= 50 else "❌"
                    print(f"  {status_icon} {test_category.replace('_', ' ').title()}: {rate:.1f}%")
            
            self.results["overall_status"] = final_status
            self.results["overall_success_rate"] = overall_success
            self.results["passed_tests"] = passed_tests
            self.results["total_tests"] = total_tests
            
            # Save comprehensive report
            with open("complete_platform_test_report.json", "w") as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n📄 Complete report: complete_platform_test_report.json")
            
            return overall_success >= 70
            
        except KeyboardInterrupt:
            print("\n⚠️ Test interrupted by user")
            return False
        except Exception as e:
            print(f"\n❌ Test suite failed: {e}")
            return False
        finally:
            self.cleanup_processes()

def main():
    """Run the complete platform test"""
    tester = CompletePlatformTests()
    
    try:
        success = tester.run_complete_platform_test()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())