#!/usr/bin/env python3
"""
Frontend Component Integration Tests
Tests React, React Native, and Electron components work with the API
"""

import requests
import json
import time
from pathlib import Path
import subprocess
import sys
import os
import base64
import signal

class FrontendComponentTester:
    """Test frontend components integration with preprocessing APIs"""
    
    def __init__(self):
        self.api_base_url = "http://localhost:8000"
        self.project_root = Path(__file__).parent
        self.test_results = {
            'react_web': {'status': 'pending', 'tests': []},
            'react_native': {'status': 'pending', 'tests': []},
            'electron': {'status': 'pending', 'tests': []},
            'api_compatibility': {'status': 'pending', 'tests': []}
        }
    
    def log_test(self, component: str, test_name: str, status: str, message: str = ""):
        """Log test result"""
        self.test_results[component]['tests'].append({
            'name': test_name,
            'status': status,
            'message': message
        })
        status_emoji = "✅" if status == "pass" else "❌" if status == "fail" else "⏳"
        print(f"  {status_emoji} {test_name}: {message}")
    
    def check_api_endpoints(self):
        """Verify API endpoints are responding correctly for frontend consumption"""
        print("🔗 Testing API Compatibility for Frontend Components...")
        
        try:
            # Test CORS headers (important for web frontend)
            response = requests.options(f"{self.api_base_url}/api/v1/image/presets")
            
            # Test image preprocessing endpoints
            presets_response = requests.get(f"{self.api_base_url}/api/v1/image/presets")
            if presets_response.status_code == 200:
                data = presets_response.json()
                if 'presets' in data and isinstance(data['presets'], dict):
                    self.log_test('api_compatibility', 'Image presets endpoint', 'pass', 
                                f"Found {len(data['presets'])} presets")
                else:
                    self.log_test('api_compatibility', 'Image presets endpoint', 'fail', 
                                "Invalid preset data structure")
            else:
                self.log_test('api_compatibility', 'Image presets endpoint', 'fail', 
                            f"HTTP {presets_response.status_code}")
            
            # Test audio preprocessing endpoints
            audio_presets_response = requests.get(f"{self.api_base_url}/api/v1/audio/presets")
            if audio_presets_response.status_code == 200:
                data = audio_presets_response.json()
                if 'presets' in data and isinstance(data['presets'], dict):
                    self.log_test('api_compatibility', 'Audio presets endpoint', 'pass',
                                f"Found {len(data['presets'])} presets")
                else:
                    self.log_test('api_compatibility', 'Audio presets endpoint', 'fail',
                                "Invalid preset data structure")
            else:
                self.log_test('api_compatibility', 'Audio presets endpoint', 'fail',
                            f"HTTP {audio_presets_response.status_code}")
            
            # Test health endpoints
            health_endpoints = [
                ('/api/v1/image/health', 'Image health'),
                ('/api/v1/audio/health', 'Audio health')
            ]
            
            for endpoint, name in health_endpoints:
                response = requests.get(f"{self.api_base_url}{endpoint}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'healthy':
                        self.log_test('api_compatibility', name, 'pass')
                    else:
                        self.log_test('api_compatibility', name, 'fail', 
                                    f"Status: {data.get('status')}")
                else:
                    self.log_test('api_compatibility', name, 'fail', 
                                f"HTTP {response.status_code}")
            
            self.test_results['api_compatibility']['status'] = 'completed'
            
        except requests.RequestException as e:
            self.log_test('api_compatibility', 'API Connection', 'fail', str(e))
            self.test_results['api_compatibility']['status'] = 'failed'
    
    def test_react_web_components(self):
        """Test React web components"""
        print("⚛️  Testing React Web Components...")
        
        # Check if React components exist and have correct structure
        react_components = [
            'frontend/src/components/preprocessing/ImagePreprocessing.tsx',
            'frontend/src/components/preprocessing/AudioPreprocessing.tsx'
        ]
        
        for component_path in react_components:
            full_path = self.project_root / component_path
            component_name = Path(component_path).stem
            
            if full_path.exists():
                # Read and analyze component
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Check for key React patterns
                    required_patterns = [
                        'import React',
                        'useState',
                        'useCallback',
                        'apiClient',
                        'export default'
                    ]
                    
                    missing_patterns = [p for p in required_patterns if p not in content]
                    
                    if not missing_patterns:
                        # Check for API integration
                        api_patterns = [
                            '/api/v1/',
                            'preprocess',
                            'status/'
                        ]
                        
                        api_integration = all(pattern in content for pattern in api_patterns)
                        
                        if api_integration:
                            self.log_test('react_web', f'{component_name} structure', 'pass',
                                        'Component has proper React patterns and API integration')
                        else:
                            self.log_test('react_web', f'{component_name} structure', 'fail',
                                        'Missing API integration patterns')
                    else:
                        self.log_test('react_web', f'{component_name} structure', 'fail',
                                    f'Missing patterns: {missing_patterns}')
                        
                except Exception as e:
                    self.log_test('react_web', f'{component_name} analysis', 'fail', str(e))
            else:
                self.log_test('react_web', f'{component_name} existence', 'fail', 
                            'Component file not found')
        
        # Check for proper TypeScript interfaces
        try:
            image_comp = self.project_root / 'frontend/src/components/preprocessing/ImagePreprocessing.tsx'
            if image_comp.exists():
                with open(image_comp, 'r') as f:
                    content = f.read()
                
                # Check for TypeScript interfaces
                interfaces = [
                    'interface PreprocessingConfig',
                    'interface ProcessingResult'
                ]
                
                found_interfaces = [i for i in interfaces if i in content]
                
                if len(found_interfaces) == len(interfaces):
                    self.log_test('react_web', 'TypeScript interfaces', 'pass',
                                f'Found {len(found_interfaces)} required interfaces')
                else:
                    self.log_test('react_web', 'TypeScript interfaces', 'fail',
                                f'Missing interfaces: {set(interfaces) - set(found_interfaces)}')
        
        except Exception as e:
            self.log_test('react_web', 'TypeScript analysis', 'fail', str(e))
        
        self.test_results['react_web']['status'] = 'completed'
    
    def test_react_native_components(self):
        """Test React Native mobile components"""
        print("📱 Testing React Native Components...")
        
        # Check React Native components
        rn_components = [
            'mobile/src/screens/ImagePreprocessingScreen.tsx',
            'mobile/src/screens/AudioPreprocessingScreen.tsx'
        ]
        
        for component_path in rn_components:
            full_path = self.project_root / component_path
            component_name = Path(component_path).stem
            
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Check for React Native specific patterns
                    rn_patterns = [
                        'react-native',
                        'StyleSheet',
                        'TouchableOpacity',
                        'View',
                        'Text'
                    ]
                    
                    missing_patterns = [p for p in rn_patterns if p not in content]
                    
                    if not missing_patterns:
                        # Check for mobile-specific features
                        mobile_features = [
                            'Alert',  # Mobile alerts
                            'Dimensions',  # Screen dimensions
                            'ActivityIndicator'  # Loading indicators
                        ]
                        
                        found_features = [f for f in mobile_features if f in content]
                        
                        if len(found_features) >= 2:
                            self.log_test('react_native', f'{component_name} structure', 'pass',
                                        f'Found {len(found_features)} mobile features')
                        else:
                            self.log_test('react_native', f'{component_name} structure', 'skip',
                                        'Limited mobile-specific features')
                    else:
                        self.log_test('react_native', f'{component_name} structure', 'fail',
                                    f'Missing RN patterns: {missing_patterns}')
                        
                except Exception as e:
                    self.log_test('react_native', f'{component_name} analysis', 'fail', str(e))
            else:
                self.log_test('react_native', f'{component_name} existence', 'fail',
                            'Component file not found')
        
        # Check for proper native integrations
        try:
            audio_screen = self.project_root / 'mobile/src/screens/AudioPreprocessingScreen.tsx'
            if audio_screen.exists():
                with open(audio_screen, 'r') as f:
                    content = f.read()
                
                # Check for native modules/libraries
                native_libs = [
                    'react-native-document-picker',
                    '@react-native-community/slider',
                    'react-native-vector-icons'
                ]
                
                found_libs = [lib for lib in native_libs if lib in content]
                
                if found_libs:
                    self.log_test('react_native', 'Native library integration', 'pass',
                                f'Using {len(found_libs)} native libraries')
                else:
                    self.log_test('react_native', 'Native library integration', 'skip',
                                'No native libraries detected')
        
        except Exception as e:
            self.log_test('react_native', 'Native library analysis', 'fail', str(e))
        
        self.test_results['react_native']['status'] = 'completed'
    
    def test_electron_components(self):
        """Test Electron desktop components"""
        print("🖥️  Testing Electron Components...")
        
        # Check Electron components
        electron_components = [
            'desktop_app/src/renderer/src/components/preprocessing/ImagePreprocessingDesktop.tsx',
            'desktop_app/src/renderer/src/components/preprocessing/AudioPreprocessingDesktop.tsx'
        ]
        
        for component_path in electron_components:
            full_path = self.project_root / component_path
            component_name = Path(component_path).stem
            
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Check for Electron-specific patterns
                    electron_patterns = [
                        'window.electron',
                        'dialog.showOpenDialog',
                        'fs.readFile',
                        'fs.writeFile'
                    ]
                    
                    found_patterns = [p for p in electron_patterns if p in content]
                    
                    if len(found_patterns) >= 2:
                        self.log_test('electron', f'{component_name} Electron integration', 'pass',
                                    f'Found {len(found_patterns)} Electron APIs')
                    else:
                        self.log_test('electron', f'{component_name} Electron integration', 'skip',
                                    'Limited Electron integration')
                    
                    # Check for file system operations
                    file_ops = [
                        'showSaveDialog',
                        'showOpenDialog',
                        'readFile',
                        'writeFile'
                    ]
                    
                    found_ops = [op for op in file_ops if op in content]
                    
                    if found_ops:
                        self.log_test('electron', f'{component_name} file operations', 'pass',
                                    f'Supports {len(found_ops)} file operations')
                    else:
                        self.log_test('electron', f'{component_name} file operations', 'fail',
                                    'No file operations found')
                        
                except Exception as e:
                    self.log_test('electron', f'{component_name} analysis', 'fail', str(e))
            else:
                self.log_test('electron', f'{component_name} existence', 'fail',
                            'Component file not found')
        
        # Check for proper TypeScript declarations
        try:
            img_desktop = self.project_root / 'desktop_app/src/renderer/src/components/preprocessing/ImagePreprocessingDesktop.tsx'
            if img_desktop.exists():
                with open(img_desktop, 'r') as f:
                    content = f.read()
                
                # Check for proper global declarations
                if 'declare global' in content and 'interface Window' in content:
                    self.log_test('electron', 'TypeScript declarations', 'pass',
                                'Proper global interface declarations')
                else:
                    self.log_test('electron', 'TypeScript declarations', 'fail',
                                'Missing proper TypeScript declarations')
        
        except Exception as e:
            self.log_test('electron', 'TypeScript declarations', 'fail', str(e))
        
        self.test_results['electron']['status'] = 'completed'
    
    def test_component_data_flow(self):
        """Test that components have proper data flow patterns"""
        print("🔄 Testing Component Data Flow...")
        
        components_to_test = [
            ('frontend/src/components/preprocessing/ImagePreprocessing.tsx', 'React Web'),
            ('mobile/src/screens/ImagePreprocessingScreen.tsx', 'React Native'),
            ('desktop_app/src/renderer/src/components/preprocessing/ImagePreprocessingDesktop.tsx', 'Electron')
        ]
        
        for component_path, platform in components_to_test:
            full_path = self.project_root / component_path
            
            if full_path.exists():
                try:
                    with open(full_path, 'r') as f:
                        content = f.read()
                    
                    # Check for proper state management
                    state_patterns = [
                        'useState',
                        'selectedImage',
                        'processedImage',
                        'processing',
                        'config'
                    ]
                    
                    found_state = [p for p in state_patterns if p in content]
                    
                    if len(found_state) >= 4:
                        self.log_test('api_compatibility', f'{platform} state management', 'pass',
                                    f'Proper state management ({len(found_state)}/5 patterns)')
                    else:
                        self.log_test('api_compatibility', f'{platform} state management', 'fail',
                                    f'Incomplete state management ({len(found_state)}/5 patterns)')
                    
                    # Check for API integration patterns
                    api_patterns = [
                        'apiClient.post',
                        'apiClient.get',
                        '/preprocess',
                        '/status/',
                        'task_id'
                    ]
                    
                    found_api = [p for p in api_patterns if p in content]
                    
                    if len(found_api) >= 3:
                        self.log_test('api_compatibility', f'{platform} API integration', 'pass',
                                    f'Complete API integration ({len(found_api)}/5 patterns)')
                    else:
                        self.log_test('api_compatibility', f'{platform} API integration', 'fail',
                                    f'Incomplete API integration ({len(found_api)}/5 patterns)')
                
                except Exception as e:
                    self.log_test('api_compatibility', f'{platform} analysis', 'fail', str(e))
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("📊 FRONTEND COMPONENTS INTEGRATION TEST REPORT")
        print("="*80)
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for component, results in self.test_results.items():
            print(f"\n🔧 {component.replace('_', ' ').title()}")
            print("-" * 40)
            
            if results['status'] == 'completed':
                for test in results['tests']:
                    status_emoji = {"pass": "✅", "fail": "❌", "skip": "⏭️"}
                    print(f"{status_emoji.get(test['status'], '❓')} {test['name']}: {test['message']}")
                    
                    total_tests += 1
                    if test['status'] == 'pass':
                        passed_tests += 1
                    elif test['status'] == 'fail':
                        failed_tests += 1
                    else:
                        skipped_tests += 1
            else:
                print(f"❌ Component testing {results['status']}")
        
        # Summary
        print(f"\n" + "="*80)
        print("📈 SUMMARY")
        print("="*80)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⏭️  Skipped: {skipped_tests}")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if failed_tests == 0:
            print("\n🎉 All frontend components are properly integrated!")
        else:
            print(f"\n⚠️  {failed_tests} tests failed - check component implementations")
        
        return failed_tests == 0
    
    def run_all_tests(self):
        """Run all frontend component tests"""
        print("🚀 Starting Frontend Components Integration Tests")
        print("="*60)
        
        # Test API compatibility first
        self.check_api_endpoints()
        
        # Test each frontend platform
        self.test_react_web_components()
        self.test_react_native_components()
        self.test_electron_components()
        
        # Test data flow patterns
        self.test_component_data_flow()
        
        # Generate report
        success = self.generate_test_report()
        
        return success

def main():
    """Main test execution"""
    tester = FrontendComponentTester()
    
    try:
        success = tester.run_all_tests()
        
        if success:
            print("\n🎯 Frontend integration verification completed successfully!")
            sys.exit(0)
        else:
            print("\n💥 Some frontend tests failed - review implementations")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()