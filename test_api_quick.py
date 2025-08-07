#!/usr/bin/env python3
"""
Quick API Test
Fast test for basic application functionality
"""

import os
import sys
from datetime import datetime
import json

def test_file_structure():
    """Test basic file structure"""
    print("🏗️ Testing File Structure...")
    
    required_files = {
        "API Core": [
            ("api/app.py", "Main API application"),
            ("api/database.py", "Database connection"),
            ("api/auth.py", "Authentication"),
        ],
        "Services": [
            ("services/internationalization_service.py", "I18n service"),
        ],
        "UI": [
            ("app.py", "Streamlit main app"),
            ("internationalization_ui.py", "I18n UI"),
        ],
        "Frontend": [
            ("frontend/src/components/i18n/InternationalizationProvider.tsx", "React I18n Provider"),
            ("desktop_app/src/renderer/src/components/i18n/InternationalizationDesktop.tsx", "Desktop I18n"),
            ("mobile/src/components/i18n/InternationalizationMobile.tsx", "Mobile I18n"),
        ]
    }
    
    results = {}
    total_files = 0
    found_files = 0
    
    for category, files in required_files.items():
        category_results = []
        for file_path, description in files:
            total_files += 1
            exists = os.path.exists(file_path)
            if exists:
                found_files += 1
                size = os.path.getsize(file_path) / 1024  # KB
                status = "✅"
                category_results.append((file_path, True, f"{size:.1f}KB"))
            else:
                status = "❌"
                category_results.append((file_path, False, "Missing"))
            
            print(f"  {status} {description}: {file_path}")
        
        results[category] = category_results
    
    success_rate = (found_files / total_files * 100) if total_files > 0 else 0
    print(f"\n📊 File Structure: {success_rate:.1f}% ({found_files}/{total_files})")
    
    return results, success_rate

def test_api_endpoints():
    """Test API endpoint files"""
    print("\n🌐 Testing API Endpoints...")
    
    endpoints_dir = "api/endpoints"
    if not os.path.exists(endpoints_dir):
        print(f"  ❌ Endpoints directory not found: {endpoints_dir}")
        return {}, 0
    
    expected_endpoints = [
        "internationalization.py",
        "transcription.py", 
        "analytics.py",
        "auth_endpoints.py",
        "users.py",
        "media.py"
    ]
    
    found_endpoints = 0
    results = {}
    
    for endpoint in expected_endpoints:
        file_path = os.path.join(endpoints_dir, endpoint)
        if os.path.exists(file_path):
            found_endpoints += 1
            size = os.path.getsize(file_path) / 1024
            
            # Quick check for FastAPI router
            with open(file_path, 'r') as f:
                content = f.read()
            has_router = "router" in content and "APIRouter" in content
            endpoints_count = content.count("@router.")
            
            status = "✅" if has_router else "⚠️"
            print(f"  {status} {endpoint}: {endpoints_count} endpoints, {size:.1f}KB")
            results[endpoint] = {"exists": True, "has_router": has_router, "endpoints": endpoints_count}
        else:
            print(f"  ❌ {endpoint}: Missing")
            results[endpoint] = {"exists": False}
    
    success_rate = (found_endpoints / len(expected_endpoints) * 100) if expected_endpoints else 0
    print(f"\n📊 API Endpoints: {success_rate:.1f}% ({found_endpoints}/{len(expected_endpoints)})")
    
    return results, success_rate

def test_i18n_implementation():
    """Test internationalization implementation"""
    print("\n🌐 Testing I18n Implementation...")
    
    i18n_files = {
        "Backend Service": "services/internationalization_service.py",
        "API Endpoints": "api/endpoints/internationalization.py", 
        "Streamlit UI": "internationalization_ui.py",
        "React Provider": "frontend/src/components/i18n/InternationalizationProvider.tsx",
        "Desktop Component": "desktop_app/src/renderer/src/components/i18n/InternationalizationDesktop.tsx",
        "Mobile Component": "mobile/src/components/i18n/InternationalizationMobile.tsx"
    }
    
    results = {}
    found_files = 0
    
    for component, file_path in i18n_files.items():
        if os.path.exists(file_path):
            found_files += 1
            size = os.path.getsize(file_path) / 1024
            
            # Check for key i18n patterns
            with open(file_path, 'r') as f:
                content = f.read()
            
            i18n_patterns = ["translate", "language", "locale", "i18n"]
            pattern_count = sum(1 for pattern in i18n_patterns if pattern.lower() in content.lower())
            
            print(f"  ✅ {component}: {size:.1f}KB, {pattern_count}/4 i18n patterns")
            results[component] = {"exists": True, "size_kb": size, "patterns": pattern_count}
        else:
            print(f"  ❌ {component}: Missing")
            results[component] = {"exists": False}
    
    success_rate = (found_files / len(i18n_files) * 100) if i18n_files else 0
    print(f"\n📊 I18n Implementation: {success_rate:.1f}% ({found_files}/{len(i18n_files)})")
    
    return results, success_rate

def test_streamlit_app():
    """Test Streamlit app"""
    print("\n🎨 Testing Streamlit App...")
    
    if not os.path.exists("app.py"):
        print("  ❌ app.py not found")
        return {"exists": False}, 0
    
    size = os.path.getsize("app.py") / 1024
    
    with open("app.py", 'r') as f:
        content = f.read()
    
    # Check for Streamlit patterns
    streamlit_patterns = ["st.", "streamlit", "sidebar", "selectbox", "button"]
    found_patterns = sum(1 for pattern in streamlit_patterns if pattern in content)
    
    # Check for app structure
    has_main = "def main()" in content or "if __name__" in content
    has_pages = "pages" in content.lower() or "page" in content.lower()
    
    print(f"  ✅ app.py exists: {size:.1f}KB")
    print(f"  ✅ Streamlit patterns: {found_patterns}/{len(streamlit_patterns)}")
    print(f"  {'✅' if has_main else '⚠️'} Main function: {'Yes' if has_main else 'No'}")
    print(f"  {'✅' if has_pages else '⚠️'} Page structure: {'Yes' if has_pages else 'No'}")
    
    success_score = (found_patterns / len(streamlit_patterns)) * 100
    
    return {
        "exists": True,
        "size_kb": size,
        "patterns": found_patterns,
        "has_main": has_main,
        "has_pages": has_pages
    }, success_score

def run_quick_tests():
    """Run all quick tests"""
    print("🚀 Running Quick Application Tests")
    print("=" * 50)
    
    test_results = {}
    success_rates = []
    
    # Run tests
    file_results, file_rate = test_file_structure()
    test_results["file_structure"] = file_results
    success_rates.append(file_rate)
    
    endpoint_results, endpoint_rate = test_api_endpoints()
    test_results["api_endpoints"] = endpoint_results  
    success_rates.append(endpoint_rate)
    
    i18n_results, i18n_rate = test_i18n_implementation()
    test_results["i18n_implementation"] = i18n_results
    success_rates.append(i18n_rate)
    
    streamlit_results, streamlit_rate = test_streamlit_app()
    test_results["streamlit_app"] = streamlit_results
    success_rates.append(streamlit_rate)
    
    # Calculate overall success
    overall_success = sum(success_rates) / len(success_rates) if success_rates else 0
    
    print("\n" + "=" * 50)
    print("📊 FINAL RESULTS")
    print("=" * 50)
    
    categories = [
        ("File Structure", success_rates[0]),
        ("API Endpoints", success_rates[1]), 
        ("I18n Implementation", success_rates[2]),
        ("Streamlit App", success_rates[3])
    ]
    
    for category, rate in categories:
        status = "✅" if rate >= 80 else "⚠️" if rate >= 60 else "❌"
        print(f"{status} {category}: {rate:.1f}%")
    
    print(f"\n🎯 Overall Success Rate: {overall_success:.1f}%")
    
    if overall_success >= 85:
        print("🎉 Excellent! All applications are in great shape!")
    elif overall_success >= 70:
        print("✅ Good! Applications are working well with minor issues")
    elif overall_success >= 50:
        print("⚠️ Moderate: Applications need some improvements")
    else:
        print("❌ Poor: Applications need significant work")
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_success_rate": overall_success,
        "category_rates": dict(categories),
        "detailed_results": test_results
    }
    
    with open("quick_app_test_report.json", "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved: quick_app_test_report.json")
    
    return overall_success >= 70

if __name__ == "__main__":
    success = run_quick_tests()
    sys.exit(0 if success else 1)