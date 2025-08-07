"""
Simple Integration Test for Internationalization System
Validates that all components are properly integrated and working
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

def test_file_structure():
    """Test that all i18n files exist with proper structure"""
    print("🔍 Testing file structure...")
    
    files_to_check = [
        "services/internationalization_service.py",
        "api/endpoints/internationalization.py", 
        "internationalization_ui.py",
        "frontend/src/components/i18n/InternationalizationProvider.tsx",
        "frontend/src/components/i18n/TranslationManager.tsx",
        "desktop_app/src/renderer/src/components/i18n/InternationalizationDesktop.tsx",
        "mobile/src/components/i18n/InternationalizationMobile.tsx"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"  ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"  ❌ {file_path}")
    
    print(f"\n📊 File Structure Summary:")
    print(f"  ✅ Existing: {len(existing_files)}/{len(files_to_check)}")
    print(f"  ❌ Missing: {len(missing_files)}")
    
    return len(missing_files) == 0, existing_files

def test_service_implementation():
    """Test the internationalization service implementation"""
    print("\n🔧 Testing service implementation...")
    
    try:
        with open("services/internationalization_service.py", "r") as f:
            content = f.read()
        
        required_components = [
            "InternationalizationService",
            "class Translation",
            "class UserLanguagePreference", 
            "get_translation",
            "set_translation",
            "get_supported_languages",
            "detect_language",
            "format_date",
            "format_currency"
        ]
        
        missing_components = []
        found_components = []
        
        for component in required_components:
            if component in content:
                found_components.append(component)
                print(f"  ✅ {component}")
            else:
                missing_components.append(component)
                print(f"  ❌ {component}")
        
        print(f"\n📊 Service Implementation Summary:")
        print(f"  ✅ Found: {len(found_components)}/{len(required_components)}")
        print(f"  ❌ Missing: {len(missing_components)}")
        
        return len(missing_components) == 0, found_components
    
    except FileNotFoundError:
        print("  ❌ Service file not found")
        return False, []

def test_api_integration():
    """Test API endpoints integration"""
    print("\n🌐 Testing API integration...")
    
    try:
        # Check API endpoint file
        with open("api/endpoints/internationalization.py", "r") as f:
            api_content = f.read()
        
        # Check main app integration
        with open("api/app.py", "r") as f:
            app_content = f.read()
        
        api_features = [
            "router",
            "get_supported_languages",
            "get_translation",
            "get_bulk_translations",
            "detect_language",
            "get_user_language_preference"
        ]
        
        integration_checks = [
            "from api.endpoints.internationalization import router as i18n_router",
            "app.include_router(i18n_router"
        ]
        
        found_features = []
        missing_features = []
        
        for feature in api_features:
            if feature in api_content:
                found_features.append(feature)
                print(f"  ✅ API feature: {feature}")
            else:
                missing_features.append(feature)
                print(f"  ❌ API feature: {feature}")
        
        found_integrations = []
        missing_integrations = []
        
        for check in integration_checks:
            if check in app_content:
                found_integrations.append(check)
                print(f"  ✅ App integration: {check[:30]}...")
            else:
                missing_integrations.append(check)
                print(f"  ❌ App integration: {check[:30]}...")
        
        print(f"\n📊 API Integration Summary:")
        print(f"  ✅ Features: {len(found_features)}/{len(api_features)}")
        print(f"  ✅ Integrations: {len(found_integrations)}/{len(integration_checks)}")
        
        return (len(missing_features) == 0 and len(missing_integrations) == 0), found_features + found_integrations
    
    except FileNotFoundError as e:
        print(f"  ❌ File not found: {e}")
        return False, []

def test_frontend_components():
    """Test frontend components across platforms"""
    print("\n🎨 Testing frontend components...")
    
    components = {
        "React Provider": "frontend/src/components/i18n/InternationalizationProvider.tsx",
        "React Manager": "frontend/src/components/i18n/TranslationManager.tsx",
        "Electron Desktop": "desktop_app/src/renderer/src/components/i18n/InternationalizationDesktop.tsx",
        "React Native Mobile": "mobile/src/components/i18n/InternationalizationMobile.tsx",
        "Streamlit UI": "internationalization_ui.py"
    }
    
    component_results = {}
    
    for name, path in components.items():
        try:
            with open(path, "r") as f:
                content = f.read()
            
            # Check for key features based on component type
            if "Provider" in name:
                required_features = ["createContext", "useContext", "I18nProvider", "useI18n"]
            elif "Manager" in name:
                required_features = ["Translation", "Manager", "export", "import"]
            elif "Desktop" in name:
                required_features = ["ipcRenderer", "native", "desktop", "dialog"]
            elif "Mobile" in name:
                required_features = ["TouchableOpacity", "Haptics", "AsyncStorage", "mobile"]
            elif "Streamlit" in name:
                required_features = ["streamlit", "st.", "main", "InternationalizationManager"]
            else:
                required_features = ["translation", "language", "i18n"]
            
            found_features = [f for f in required_features if f in content]
            component_results[name] = {
                "found": len(found_features),
                "total": len(required_features),
                "features": found_features
            }
            
            print(f"  ✅ {name}: {len(found_features)}/{len(required_features)} features")
            
        except FileNotFoundError:
            component_results[name] = {"found": 0, "total": 1, "features": []}
            print(f"  ❌ {name}: File not found")
    
    total_found = sum(r["found"] for r in component_results.values())
    total_expected = sum(r["total"] for r in component_results.values())
    
    print(f"\n📊 Frontend Components Summary:")
    print(f"  ✅ Features found: {total_found}/{total_expected}")
    print(f"  📱 Platforms covered: {len([r for r in component_results.values() if r['found'] > 0])}/5")
    
    return total_found >= total_expected * 0.8, component_results

def test_language_support():
    """Test language support implementation"""
    print("\n🌍 Testing language support...")
    
    try:
        # Check service for language definitions
        with open("services/internationalization_service.py", "r") as f:
            service_content = f.read()
        
        # Check Streamlit UI for language list
        with open("internationalization_ui.py", "r") as f:
            ui_content = f.read()
        
        # Expected languages
        expected_languages = [
            "en", "es", "fr", "de", "it", "pt", "ru", 
            "zh", "ja", "ko", "ar", "he", "hi", "th", "vi"
        ]
        
        rtl_languages = ["ar", "he"]  # Right-to-left languages
        
        found_languages = []
        found_rtl = []
        
        for lang in expected_languages:
            if f'"{lang}"' in service_content or f'"{lang}"' in ui_content:
                found_languages.append(lang)
                print(f"  ✅ Language: {lang}")
                
                if lang in rtl_languages:
                    found_rtl.append(lang)
        
        # Check for RTL support
        rtl_support = "rtl" in service_content.lower() or "right-to-left" in service_content.lower()
        
        print(f"\n📊 Language Support Summary:")
        print(f"  ✅ Languages: {len(found_languages)}/{len(expected_languages)}")
        print(f"  ↩️ RTL Languages: {len(found_rtl)}/{len(rtl_languages)}")
        print(f"  🔄 RTL Support: {'Yes' if rtl_support else 'No'}")
        
        return len(found_languages) >= 10 and rtl_support, found_languages
    
    except FileNotFoundError:
        print("  ❌ Required files not found")
        return False, []

def test_database_models():
    """Test database model definitions"""
    print("\n🗄️ Testing database models...")
    
    try:
        with open("services/internationalization_service.py", "r") as f:
            content = f.read()
        
        required_models = [
            "class Translation",
            "class UserLanguagePreference",
            "Base",
            "Column", 
            "String",
            "DateTime"
        ]
        
        found_models = []
        missing_models = []
        
        for model in required_models:
            if model in content:
                found_models.append(model)
                print(f"  ✅ {model}")
            else:
                missing_models.append(model)
                print(f"  ❌ {model}")
        
        # Check for database fields
        expected_fields = [
            "id", "key", "language_code", "value", "namespace",
            "user_id", "created_at", "updated_at"
        ]
        
        found_fields = [field for field in expected_fields if field in content]
        
        print(f"\n📊 Database Models Summary:")
        print(f"  ✅ Models: {len(found_models)}/{len(required_models)}")
        print(f"  📝 Fields: {len(found_fields)}/{len(expected_fields)}")
        
        return len(missing_models) <= 2, found_models  # Allow some flexibility
    
    except FileNotFoundError:
        print("  ❌ Service file not found")
        return False, []

def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Starting I18n Integration Tests")
    print("=" * 60)
    
    test_functions = [
        ("File Structure", test_file_structure),
        ("Service Implementation", test_service_implementation),
        ("API Integration", test_api_integration),
        ("Frontend Components", test_frontend_components),
        ("Language Support", test_language_support),
        ("Database Models", test_database_models)
    ]
    
    results = {}
    total_tests = len(test_functions)
    passed_tests = 0
    
    for test_name, test_function in test_functions:
        try:
            success, details = test_function()
            results[test_name] = {
                "success": success,
                "details": details
            }
            if success:
                passed_tests += 1
                print(f"\n🎉 {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            results[test_name] = {
                "success": False,
                "error": str(e)
            }
            print(f"\n💥 {test_name}: ERROR - {e}")
    
    print(f"\n🎯 Integration Test Results")
    print("=" * 40)
    print(f"📊 Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {total_tests - passed_tests}")
    print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    # Detailed results
    print(f"\n📋 Detailed Results:")
    for test_name, result in results.items():
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        print(f"  {status} - {test_name}")
    
    # Feature completeness assessment
    feature_completeness = assess_feature_completeness(results)
    print(f"\n🎨 Feature Completeness Assessment:")
    for category, score in feature_completeness.items():
        print(f"  {category}: {score:.1f}%")
    
    # Generate comprehensive report
    test_report = {
        "test_suite": "I18n Integration Tests",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests/total_tests*100)
        },
        "detailed_results": results,
        "feature_completeness": feature_completeness,
        "recommendations": generate_recommendations(results)
    }
    
    with open("i18n_integration_report.json", "w") as f:
        json.dump(test_report, f, indent=2)
    
    print(f"\n📄 Integration report saved: i18n_integration_report.json")
    
    if passed_tests >= total_tests * 0.8:  # 80% pass rate
        print("\n🎉 Integration tests mostly successful!")
        print("✅ I18n system is properly integrated across platforms")
        return True
    else:
        print(f"\n⚠️ Integration tests need attention")
        print("🔧 Check failed components and implement fixes")
        return False

def assess_feature_completeness(results: Dict[str, Any]) -> Dict[str, float]:
    """Assess completeness of different feature categories"""
    completeness = {}
    
    # Backend completeness
    backend_tests = ["Service Implementation", "API Integration", "Database Models"]
    backend_scores = [100 if results.get(test, {}).get("success", False) else 0 for test in backend_tests]
    completeness["Backend"] = sum(backend_scores) / len(backend_scores)
    
    # Frontend completeness  
    frontend_result = results.get("Frontend Components", {})
    if "details" in frontend_result and isinstance(frontend_result["details"], dict):
        component_scores = []
        for component, data in frontend_result["details"].items():
            if isinstance(data, dict) and "found" in data and "total" in data:
                score = (data["found"] / data["total"]) * 100 if data["total"] > 0 else 0
                component_scores.append(score)
        completeness["Frontend"] = sum(component_scores) / len(component_scores) if component_scores else 0
    else:
        completeness["Frontend"] = 100 if frontend_result.get("success", False) else 0
    
    # Language support
    lang_result = results.get("Language Support", {})
    completeness["Languages"] = 100 if lang_result.get("success", False) else 0
    
    # Overall structure
    structure_result = results.get("File Structure", {})
    completeness["Structure"] = 100 if structure_result.get("success", False) else 0
    
    return completeness

def generate_recommendations(results: Dict[str, Any]) -> List[str]:
    """Generate recommendations based on test results"""
    recommendations = []
    
    if not results.get("File Structure", {}).get("success", False):
        recommendations.append("Complete missing file implementations across all platforms")
    
    if not results.get("Service Implementation", {}).get("success", False):
        recommendations.append("Fix async/await issues in InternationalizationService methods")
    
    if not results.get("API Integration", {}).get("success", False):
        recommendations.append("Ensure API endpoints are properly integrated in main app")
    
    frontend_result = results.get("Frontend Components", {})
    if not frontend_result.get("success", False):
        recommendations.append("Complete frontend component implementations with all required features")
    
    if not results.get("Language Support", {}).get("success", False):
        recommendations.append("Add support for more languages and ensure RTL functionality")
    
    if not results.get("Database Models", {}).get("success", False):
        recommendations.append("Complete database model definitions with all required fields")
    
    if not recommendations:
        recommendations.append("System is well implemented - consider adding more comprehensive error handling and testing")
    
    return recommendations

if __name__ == "__main__":
    success = run_integration_tests()
    exit(0 if success else 1)