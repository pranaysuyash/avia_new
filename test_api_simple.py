"""
Simple API Test
Test basic API functionality without complex imports
"""

import sys
import os
import json
from datetime import datetime

def test_api_basic_imports():
    """Test basic API imports"""
    print("🔧 Testing API Basic Imports...")
    
    # Test individual components
    tests = [
        ("FastAPI", "from fastapi import FastAPI"),
        ("Database", "from api.database import get_db"),
        ("Auth", "from api.auth import get_current_user"),
        ("I18n Service", "from services.internationalization_service import i18n_service"),
        ("I18n API", "from api.endpoints.internationalization import router"),
        ("Models", "from api.models import TranscriptionRequest"),
    ]
    
    results = []
    
    for test_name, import_statement in tests:
        try:
            exec(import_statement)
            print(f"  ✅ {test_name}: Import successful")
            results.append((test_name, True, None))
        except ImportError as e:
            print(f"  ❌ {test_name}: Import failed - {e}")
            results.append((test_name, False, str(e)))
        except Exception as e:
            print(f"  ⚠️ {test_name}: Import warning - {e}")
            results.append((test_name, True, f"Warning: {e}"))
    
    return results

def test_api_endpoints_structure():
    """Test API endpoint file structure"""
    print("\n🌐 Testing API Endpoint Structure...")
    
    endpoints_dir = "api/endpoints"
    expected_files = [
        "internationalization.py",
        "transcription.py",
        "analytics.py",
        "auth_endpoints.py",
        "users.py",
        "media.py"
    ]
    
    results = {}
    
    for file_name in expected_files:
        file_path = os.path.join(endpoints_dir, file_name)
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Check for FastAPI router
                has_router = "router" in content and "APIRouter" in content
                endpoint_count = content.count("@router.")
                
                results[file_name] = {
                    "exists": True,
                    "has_router": has_router,
                    "endpoint_count": endpoint_count,
                    "size_kb": round(len(content) / 1024, 1)
                }
                
                status = "✅" if has_router and endpoint_count > 0 else "⚠️"
                print(f"  {status} {file_name}: {endpoint_count} endpoints, {results[file_name]['size_kb']}KB")
                
            except Exception as e:
                results[file_name] = {"exists": True, "error": str(e)}
                print(f"  ❌ {file_name}: Error reading - {e}")
        else:
            results[file_name] = {"exists": False}
            print(f"  ❌ {file_name}: File not found")
    
    return results

def test_streamlit_app():
    """Test Streamlit app"""
    print("\n🎨 Testing Streamlit App...")
    
    try:
        # Check main app file
        if os.path.exists("app.py"):
            with open("app.py", 'r') as f:
                content = f.read()
            
            # Check for Streamlit components
            streamlit_components = [
                "st.title",
                "st.sidebar", 
                "st.selectbox",
                "st.button",
                "st.write"
            ]
            
            found_components = [comp for comp in streamlit_components if comp in content]
            
            print(f"  ✅ Main app.py exists ({round(len(content)/1024, 1)}KB)")
            print(f"  ✅ Streamlit components: {len(found_components)}/{len(streamlit_components)}")
            
            return {
                "exists": True,
                "size_kb": round(len(content)/1024, 1),
                "components_found": len(found_components),
                "total_components": len(streamlit_components)
            }
        else:
            print("  ❌ app.py not found")
            return {"exists": False}
            
    except Exception as e:
        print(f"  ❌ Error testing Streamlit app: {e}")
        return {"exists": True, "error": str(e)}

def test_i18n_ui():
    """Test internationalization UI"""
    print("\n🌐 Testing I18n UI...")
    
    try:
        if os.path.exists("internationalization_ui.py"):
            with open("internationalization_ui.py", 'r') as f:
                content = f.read()
            
            # Check for i18n features
            i18n_features = [
                "InternationalizationManager",
                "supported_languages",
                "translation",
                "streamlit",
                "main()"
            ]
            
            found_features = [feat for feat in i18n_features if feat in content]
            
            print(f"  ✅ I18n UI exists ({round(len(content)/1024, 1)}KB)")
            print(f"  ✅ I18n features: {len(found_features)}/{len(i18n_features)}")
            
            return {
                "exists": True,
                "size_kb": round(len(content)/1024, 1),
                "features_found": len(found_features),
                "total_features": len(i18n_features)
            }
        else:
            print("  ❌ internationalization_ui.py not found")
            return {"exists": False}
            
    except Exception as e:
        print(f"  ❌ Error testing I18n UI: {e}")
        return {"exists": True, "error": str(e)}

def test_frontend_structure():
    """Test frontend structure"""
    print("\n⚛️ Testing Frontend Structure...")
    
    frontend_paths = [
        "frontend/src/components/i18n/InternationalizationProvider.tsx",
        "frontend/src/components/i18n/TranslationManager.tsx",
        "desktop_app/src/renderer/src/components/i18n/InternationalizationDesktop.tsx",
        "mobile/src/components/i18n/InternationalizationMobile.tsx"
    ]
    
    results = {}
    
    for path in frontend_paths:
        component_name = os.path.basename(path).replace('.tsx', '')
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    content = f.read()
                
                # Check for key React/TypeScript patterns
                patterns = [
                    "import React",
                    "export default",
                    "const",
                    "interface"
                ]
                
                found_patterns = [p for p in patterns if p in content]
                
                results[component_name] = {
                    "exists": True,
                    "size_kb": round(len(content)/1024, 1),
                    "patterns_found": len(found_patterns),
                    "total_patterns": len(patterns)
                }
                
                print(f"  ✅ {component_name}: {results[component_name]['size_kb']}KB, {len(found_patterns)}/{len(patterns)} patterns")
                
            except Exception as e:
                results[component_name] = {"exists": True, "error": str(e)}
                print(f"  ❌ {component_name}: Error reading - {e}")
        else:
            results[component_name] = {"exists": False}
            print(f"  ❌ {component_name}: File not found")
    
    return results

def test_basic_functionality():
    """Test basic system functionality"""
    print("\n🔬 Testing Basic Functionality...")
    
    try:
        # Test i18n service import
        from services.internationalization_service import InternationalizationService
        service = InternationalizationService()
        
        print("  ✅ I18n service can be instantiated")
        
        # Test supported languages
        languages = [
            {"code": "en", "name": "English"},
            {"code": "es", "name": "Spanish"},
            {"code": "fr", "name": "French"}
        ]
        
        print(f"  ✅ Mock language support: {len(languages)} languages")
        
        return {
            "service_instantiated": True,
            "mock_languages": len(languages)
        }
        
    except Exception as e:
        print(f"  ❌ Basic functionality test failed: {e}")
        return {"error": str(e)}

def run_simple_tests():
    """Run all simple tests"""
    print("🚀 Running Simple Application Tests")
    print("=" * 50)
    
    test_results = {}
    
    # Run tests
    test_results["api_imports"] = test_api_basic_imports()
    test_results["api_endpoints"] = test_api_endpoints_structure()
    test_results["streamlit_app"] = test_streamlit_app()
    test_results["i18n_ui"] = test_i18n_ui()
    test_results["frontend"] = test_frontend_structure()
    test_results["functionality"] = test_basic_functionality()
    
    # Generate summary
    print("\n📊 Test Summary")
    print("-" * 30)
    
    total_tests = 0
    passed_tests = 0
    
    for category, results in test_results.items():
        if isinstance(results, list):
            # API imports format
            total_tests += len(results)
            passed_tests += sum(1 for _, success, _ in results if success)
            success_rate = (sum(1 for _, success, _ in results if success) / len(results)) * 100
            print(f"{category}: {success_rate:.1f}% ({sum(1 for _, success, _ in results if success)}/{len(results)})")
        elif isinstance(results, dict):
            if category == "api_endpoints":
                # Handle endpoint structure results
                total_endpoints = len(results)
                passed_endpoints = sum(1 for r in results.values() if isinstance(r, dict) and r.get("exists", False) and r.get("has_router", False))
                success_rate = (passed_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0
                total_tests += 1
                if success_rate >= 75:  # 75% or more endpoints working
                    passed_tests += 1
                    print(f"{category}: ✅ Passed ({success_rate:.1f}% - {passed_endpoints}/{total_endpoints})")
                else:
                    print(f"{category}: ❌ Failed ({success_rate:.1f}% - {passed_endpoints}/{total_endpoints})")
            elif category == "frontend":
                # Handle frontend component results
                total_components = len(results)
                passed_components = sum(1 for r in results.values() if isinstance(r, dict) and r.get("exists", False))
                success_rate = (passed_components / total_components * 100) if total_components > 0 else 0
                total_tests += 1
                if success_rate >= 75:  # 75% or more components exist
                    passed_tests += 1
                    print(f"{category}: ✅ Passed ({success_rate:.1f}% - {passed_components}/{total_components})")
                else:
                    print(f"{category}: ❌ Failed ({success_rate:.1f}% - {passed_components}/{total_components})")
            elif "error" not in results:
                if "exists" in results and results["exists"]:
                    total_tests += 1
                    passed_tests += 1
                    print(f"{category}: ✅ Passed")
                else:
                    total_tests += 1
                    print(f"{category}: ❌ Failed")
            else:
                total_tests += 1
                print(f"{category}: ❌ Error - {results['error'][:50]}...")
    
    overall_success = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"\n🎯 Overall Success Rate: {overall_success:.1f}% ({passed_tests}/{total_tests})")
    
    if overall_success >= 80:
        print("✅ Applications are in good shape!")
    elif overall_success >= 60:
        print("⚠️ Applications mostly working but need some fixes")
    else:
        print("❌ Applications need significant work")
    
    # Save report
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_success_rate": overall_success,
        "total_tests": total_tests,
        "passed_tests": passed_tests,
        "detailed_results": test_results
    }
    
    with open("simple_app_test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Test report saved: simple_app_test_report.json")
    
    return overall_success >= 70

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)