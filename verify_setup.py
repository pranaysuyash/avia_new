#!/usr/bin/env python3
"""
Setup Verification Script
Quick verification of deployment readiness
"""

import sys
import subprocess
from pathlib import Path
from config import Config, validate_environment

def verify_deployment():
    """Verify deployment readiness"""
    print("🔍 Verifying deployment setup...")
    
    checks = []
    
    # Check Python version
    python_version = sys.version_info
    if python_version >= (3, 8):
        checks.append(("Python Version", True, f"{python_version.major}.{python_version.minor}"))
    else:
        checks.append(("Python Version", False, f"{python_version.major}.{python_version.minor} (requires 3.8+)"))
    
    # Check required files
    required_files = ["app.py", "config.py", "requirements.txt", ".env.example"]
    for file in required_files:
        exists = Path(file).exists()
        checks.append((f"File: {file}", exists, "Present" if exists else "Missing"))
    
    # Check configuration
    is_valid, _ = validate_environment()
    checks.append(("Configuration", is_valid, "Valid" if is_valid else "Issues found"))
    
    # Check dependencies
    try:
        import streamlit
        checks.append(("Streamlit", True, "Installed"))
    except ImportError:
        checks.append(("Streamlit", False, "Not installed"))
    
    # Print results
    print("\n📋 Verification Results:")
    print("-" * 40)
    
    all_passed = True
    for check_name, passed, details in checks:
        status = "✅" if passed else "❌"
        print(f"{status} {check_name:<20} {details}")
        if not passed:
            all_passed = False
    
    print("-" * 40)
    
    if all_passed:
        print("🎉 All checks passed! Ready for deployment.")
        return True
    else:
        print("⚠️ Some checks failed. Please resolve issues before deployment.")
        return False

if __name__ == "__main__":
    success = verify_deployment()
    sys.exit(0 if success else 1)