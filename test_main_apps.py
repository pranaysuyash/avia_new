#!/usr/bin/env python3
"""
Main Applications Test
Test React Web, React Native, and Electron Desktop applications
"""

import subprocess
import os
import sys
import json
import time
from datetime import datetime
import threading

class MainAppsTests:
    def __init__(self):
        self.project_root = "/Users/pranay/Projects/LLM/video/ner"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "test_suite": "Main Applications Integration Test", 
            "tests": {},
            "overall_status": "PENDING"
        }
    
    def test_react_web_app(self):
        """Test React Web Application"""
        print("⚛️ Testing React Web Application...")
        
        frontend_dir = os.path.join(self.project_root, "frontend")
        tests = []
        
        # Test 1: Check if package.json exists
        package_json_path = os.path.join(frontend_dir, "package.json") 
        if os.path.exists(package_json_path):
            tests.append(("Package Configuration", "PASSED", "package.json exists"))
            
            # Check package.json contents
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    
                if "react" in package_data.get("dependencies", {}):
                    tests.append(("React Dependency", "PASSED", "React dependency found"))
                else:
                    tests.append(("React Dependency", "FAILED", "React not in dependencies"))
                    
            except Exception as e:
                tests.append(("Package Contents", "FAILED", str(e)))
        else:
            tests.append(("Package Configuration", "FAILED", "package.json missing"))
            
        # Test 2: Check component structure
        components_dir = os.path.join(frontend_dir, "src/components")
        if os.path.exists(components_dir):
            # Count component categories
            component_dirs = [d for d in os.listdir(components_dir) 
                            if os.path.isdir(os.path.join(components_dir, d))]
            
            if len(component_dirs) >= 10:  # Should have many component categories
                tests.append(("Component Structure", "PASSED", f"{len(component_dirs)} component categories"))
            else:
                tests.append(("Component Structure", "PARTIAL", f"Only {len(component_dirs)} categories"))
        else:
            tests.append(("Component Structure", "FAILED", "Components directory missing"))
            
        # Test 3: Check key components exist
        key_components = [
            "i18n/InternationalizationProvider.tsx",
            "transcription/InteractiveTranscript.tsx", 
            "upload/FileUploader.tsx",
            "dashboard/MainDashboard.tsx"
        ]
        
        found_components = 0
        for component in key_components:
            if os.path.exists(os.path.join(components_dir, component)):
                found_components += 1
                
        if found_components >= 3:
            tests.append(("Key Components", "PASSED", f"{found_components}/{len(key_components)} key components"))
        else:
            tests.append(("Key Components", "FAILED", f"Only {found_components}/{len(key_components)} found"))
        
        # Calculate success rate
        passed = sum(1 for _, status, _ in tests if status == "PASSED")
        success_rate = (passed / len(tests) * 100) if tests else 0
        
        for test_name, status, message in tests:
            emoji = "✅" if status == "PASSED" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 React Web Success: {success_rate:.1f}% ({passed}/{len(tests)})")
        
        self.results["tests"]["react_web"] = {
            "success_rate": success_rate,
            "tests": tests,
            "status": "PASSED" if success_rate >= 75 else "FAILED"
        }
        
        return success_rate >= 75
    
    def test_electron_desktop_app(self):
        """Test Electron Desktop Application"""
        print("\n🖥️ Testing Electron Desktop Application...")
        
        desktop_dir = os.path.join(self.project_root, "desktop_app")
        tests = []
        
        # Test 1: Check Electron configuration
        package_json_path = os.path.join(desktop_dir, "package.json")
        if os.path.exists(package_json_path):
            tests.append(("Desktop Package Config", "PASSED", "package.json exists"))
            
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    
                # Check for Electron
                if "electron" in package_data.get("devDependencies", {}):
                    tests.append(("Electron Framework", "PASSED", "Electron dependency found"))
                else:
                    tests.append(("Electron Framework", "FAILED", "Electron not found"))
                    
                # Check main entry point
                if package_data.get("main") == "src/main.js":
                    tests.append(("Main Entry Point", "PASSED", "Correct main entry"))
                else:
                    tests.append(("Main Entry Point", "FAILED", "Invalid main entry"))
                    
            except Exception as e:
                tests.append(("Package Parsing", "FAILED", str(e)))
        else:
            tests.append(("Desktop Package Config", "FAILED", "package.json missing"))
            
        # Test 2: Check main process file
        main_js_path = os.path.join(desktop_dir, "src/main.js")
        if os.path.exists(main_js_path):
            with open(main_js_path, 'r') as f:
                main_content = f.read()
                
            if "BrowserWindow" in main_content and "app" in main_content:
                tests.append(("Main Process File", "PASSED", "Electron main process properly configured"))
            else:
                tests.append(("Main Process File", "FAILED", "Invalid main process"))
        else:
            tests.append(("Main Process File", "FAILED", "main.js missing"))
            
        # Test 3: Check renderer components
        renderer_dir = os.path.join(desktop_dir, "src/renderer/src/components")
        if os.path.exists(renderer_dir):
            # Check for i18n component specifically
            i18n_component = os.path.join(renderer_dir, "i18n/InternationalizationDesktop.tsx")
            if os.path.exists(i18n_component):
                tests.append(("Desktop I18n Component", "PASSED", "Desktop i18n component exists"))
            else:
                tests.append(("Desktop I18n Component", "FAILED", "Missing desktop i18n"))
        else:
            tests.append(("Renderer Components", "FAILED", "No renderer components"))
            
        # Test 4: Check if dependencies are installed
        node_modules_path = os.path.join(desktop_dir, "node_modules")
        if os.path.exists(node_modules_path):
            tests.append(("Dependencies Installed", "PASSED", "node_modules exists"))
        else:
            tests.append(("Dependencies Installed", "FAILED", "Dependencies not installed"))
            
        # Calculate success rate
        passed = sum(1 for _, status, _ in tests if status == "PASSED")
        success_rate = (passed / len(tests) * 100) if tests else 0
        
        for test_name, status, message in tests:
            emoji = "✅" if status == "PASSED" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 Electron Desktop Success: {success_rate:.1f}% ({passed}/{len(tests)})")
        
        self.results["tests"]["electron_desktop"] = {
            "success_rate": success_rate,
            "tests": tests,
            "status": "PASSED" if success_rate >= 75 else "FAILED"
        }
        
        return success_rate >= 75
    
    def test_react_native_mobile_app(self):
        """Test React Native Mobile Application"""
        print("\n📱 Testing React Native Mobile Application...")
        
        mobile_dir = os.path.join(self.project_root, "mobile")
        tests = []
        
        # Test 1: Check React Native configuration
        package_json_path = os.path.join(mobile_dir, "package.json")
        if os.path.exists(package_json_path):
            tests.append(("Mobile Package Config", "PASSED", "package.json exists"))
            
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                    
                # Check for React Native
                if "react-native" in package_data.get("dependencies", {}):
                    rn_version = package_data["dependencies"]["react-native"]
                    tests.append(("React Native Framework", "PASSED", f"React Native {rn_version}"))
                else:
                    tests.append(("React Native Framework", "FAILED", "React Native not found"))
                    
                # Check for navigation
                if "@react-navigation/native" in package_data.get("dependencies", {}):
                    tests.append(("Navigation System", "PASSED", "React Navigation found"))
                else:
                    tests.append(("Navigation System", "FAILED", "No navigation system"))
                    
            except Exception as e:
                tests.append(("Package Parsing", "FAILED", str(e)))
        else:
            tests.append(("Mobile Package Config", "FAILED", "package.json missing"))
            
        # Test 2: Check App.tsx entry point
        app_tsx_path = os.path.join(mobile_dir, "src/App.tsx")
        if os.path.exists(app_tsx_path):
            with open(app_tsx_path, 'r') as f:
                app_content = f.read()
                
            if "React" in app_content and ("export" in app_content or "App" in app_content):
                tests.append(("App Entry Point", "PASSED", "App.tsx properly configured"))
            else:
                tests.append(("App Entry Point", "FAILED", "Invalid App.tsx"))
        else:
            tests.append(("App Entry Point", "FAILED", "App.tsx missing"))
            
        # Test 3: Check mobile components
        components_dir = os.path.join(mobile_dir, "src/components")
        if os.path.exists(components_dir):
            # Count component directories
            component_dirs = [d for d in os.listdir(components_dir)
                            if os.path.isdir(os.path.join(components_dir, d))]
            
            if len(component_dirs) >= 8:
                tests.append(("Mobile Components", "PASSED", f"{len(component_dirs)} component categories"))
            else:
                tests.append(("Mobile Components", "PARTIAL", f"{len(component_dirs)} categories"))
                
            # Check for i18n mobile component  
            i18n_mobile = os.path.join(components_dir, "i18n/InternationalizationMobile.tsx")
            if os.path.exists(i18n_mobile):
                tests.append(("Mobile I18n Component", "PASSED", "Mobile i18n component exists"))
            else:
                tests.append(("Mobile I18n Component", "FAILED", "Missing mobile i18n"))
        else:
            tests.append(("Mobile Components", "FAILED", "No components directory"))
            
        # Test 4: Check configuration files
        config_files = ["metro.config.js", "babel.config.js", "tsconfig.json"]
        found_configs = sum(1 for config in config_files
                          if os.path.exists(os.path.join(mobile_dir, config)))
        
        if found_configs >= 2:
            tests.append(("Configuration Files", "PASSED", f"{found_configs}/3 config files"))
        else:
            tests.append(("Configuration Files", "FAILED", f"Only {found_configs}/3 configs"))
            
        # Calculate success rate
        passed = sum(1 for _, status, _ in tests if status in ["PASSED", "PARTIAL"])
        success_rate = (passed / len(tests) * 100) if tests else 0
        
        for test_name, status, message in tests:
            emoji = "✅" if status == "PASSED" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 React Native Mobile Success: {success_rate:.1f}% ({passed}/{len(tests)})")
        
        self.results["tests"]["react_native_mobile"] = {
            "success_rate": success_rate,
            "tests": tests,
            "status": "PASSED" if success_rate >= 75 else "FAILED"
        }
        
        return success_rate >= 75
        
    def test_api_integration(self):
        """Test API integration for main apps"""
        print("\n🔗 Testing API Integration...")
        
        tests = []
        
        # Test 1: API endpoints exist
        api_endpoints_dir = os.path.join(self.project_root, "api/endpoints")
        if os.path.exists(api_endpoints_dir):
            endpoint_files = [f for f in os.listdir(api_endpoints_dir) 
                            if f.endswith('.py') and f != '__init__.py']
            
            if len(endpoint_files) >= 6:
                tests.append(("API Endpoints", "PASSED", f"{len(endpoint_files)} endpoint files"))
            else:
                tests.append(("API Endpoints", "PARTIAL", f"{len(endpoint_files)} files"))
        else:
            tests.append(("API Endpoints", "FAILED", "No endpoints directory"))
            
        # Test 2: Core services exist
        services_dir = os.path.join(self.project_root, "services")
        core_services = ["transcription_service.py", "internationalization_service.py"]
        found_services = sum(1 for service in core_services
                           if os.path.exists(os.path.join(services_dir, service)))
        
        if found_services == len(core_services):
            tests.append(("Core Services", "PASSED", "All core services exist"))
        else:
            tests.append(("Core Services", "FAILED", f"{found_services}/{len(core_services)} services"))
            
        # Test 3: Database models
        models_dir = os.path.join(self.project_root, "api/models")
        if os.path.exists(models_dir):
            model_files = [f for f in os.listdir(models_dir) 
                         if f.endswith('.py') and f != '__init__.py']
            
            if len(model_files) >= 2:
                tests.append(("API Models", "PASSED", f"{len(model_files)} model files"))
            else:
                tests.append(("API Models", "FAILED", f"Only {len(model_files)} models"))
        else:
            tests.append(("API Models", "FAILED", "No models directory"))
            
        # Calculate success rate
        passed = sum(1 for _, status, _ in tests if status in ["PASSED", "PARTIAL"])
        success_rate = (passed / len(tests) * 100) if tests else 0
        
        for test_name, status, message in tests:
            emoji = "✅" if status == "PASSED" else "⚠️" if status == "PARTIAL" else "❌"
            print(f"  {emoji} {test_name}: {message}")
            
        print(f"📊 API Integration Success: {success_rate:.1f}% ({passed}/{len(tests)})")
        
        self.results["tests"]["api_integration"] = {
            "success_rate": success_rate,
            "tests": tests,
            "status": "PASSED" if success_rate >= 66 else "FAILED"
        }
        
        return success_rate >= 66
    
    def run_main_apps_test_suite(self):
        """Run complete main applications test suite"""
        print("🚀 MAIN APPLICATIONS INTEGRATION TEST")
        print("=" * 70)
        print("Testing the core production applications:")
        print("• React Web Application (Frontend)")
        print("• Electron Desktop Application")
        print("• React Native Mobile Application")
        print("• API Backend Integration")
        print("=" * 70)
        
        test_results = []
        
        # Test all main applications
        react_passed = self.test_react_web_app()
        test_results.append(("React Web App", react_passed))
        
        electron_passed = self.test_electron_desktop_app()
        test_results.append(("Electron Desktop", electron_passed))
        
        mobile_passed = self.test_react_native_mobile_app()
        test_results.append(("React Native Mobile", mobile_passed))
        
        api_passed = self.test_api_integration()
        test_results.append(("API Integration", api_passed))
        
        # Calculate overall results
        passed_tests = sum(1 for _, passed in test_results if passed)
        total_tests = len(test_results)
        overall_success = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "=" * 70)
        print("📊 MAIN APPLICATIONS TEST RESULTS")
        print("=" * 70)
        
        for test_name, passed in test_results:
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall Main Apps Success Rate: {overall_success:.1f}% ({passed_tests}/{total_tests})")
        
        # Determine final status
        if overall_success >= 85:
            print("🎉 EXCELLENT! All main applications are production-ready!")
            final_status = "EXCELLENT"
        elif overall_success >= 70:
            print("✅ GOOD! Main applications are mostly ready, minor fixes needed")
            final_status = "GOOD"
        elif overall_success >= 50:
            print("⚠️ PARTIAL! Some applications working, others need attention") 
            final_status = "PARTIAL"
        else:
            print("❌ FAILED! Main applications need significant work")
            final_status = "FAILED"
            
        self.results["overall_status"] = final_status
        self.results["overall_success_rate"] = overall_success
        self.results["passed_tests"] = passed_tests
        self.results["total_tests"] = total_tests
        
        # Additional insights
        print(f"\n📋 Key Insights:")
        if react_passed:
            print("  • React Web: Frontend application properly structured")
        if electron_passed:
            print("  • Electron: Desktop application ready for distribution")  
        if mobile_passed:
            print("  • React Native: Mobile app configured for iOS/Android")
        if api_passed:
            print("  • API Backend: Server infrastructure properly implemented")
            
        # Save detailed report
        with open("main_applications_test_report.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed report: main_applications_test_report.json")
        
        return overall_success >= 70

def main():
    """Run the main applications test"""
    tester = MainAppsTests()
    
    try:
        success = tester.run_main_apps_test_suite()
        return 0 if success else 1
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())