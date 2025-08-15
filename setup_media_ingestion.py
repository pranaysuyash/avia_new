#!/usr/bin/env python3
"""
Setup script for Media Ingestion Controller dependencies
This script ensures all required Python packages are installed and working correctly.
"""

import subprocess
import sys
import importlib
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_import(module_name, package_name=None, description=None):
    """Check if a module can be imported"""
    if package_name is None:
        package_name = module_name
    if description is None:
        description = module_name
    
    try:
        importlib.import_module(module_name)
        print(f"✅ {description} is available")
        return True
    except ImportError as e:
        print(f"❌ {description} is not available: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Media Ingestion Controller dependencies...")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    print(f"🐍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    # Install core dependencies
    core_packages = [
        "python-magic",
        "PyMuPDF", 
        "aiofiles",
        "ffmpeg-python",
        "Pillow"
    ]
    
    print("\n📦 Installing core packages...")
    for package in core_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"⚠️  Failed to install {package}, continuing...")
    
    print("\n🔍 Checking imports...")
    
    # Check critical imports
    import_checks = [
        ("magic", "python-magic", "python-magic (MIME type detection)"),
        ("fitz", "PyMuPDF", "PyMuPDF (PDF processing)"),
        ("aiofiles", "aiofiles", "aiofiles (async file operations)"),
        ("ffmpeg", "ffmpeg-python", "ffmpeg-python (media processing)"),
        ("PIL", "Pillow", "Pillow (image processing)")
    ]
    
    failed_imports = []
    for module, package, description in import_checks:
        if not check_import(module, package, description):
            failed_imports.append((module, package, description))
    
    # Check Media Ingestion Controller
    print("\n🎯 Testing Media Ingestion Controller...")
    try:
        from media_ingestion_controller import MediaIngestionController
        print("✅ MediaIngestionController imported successfully")
        
        # Test initialization
        controller = MediaIngestionController()
        print("✅ MediaIngestionController initialized successfully")
        
    except Exception as e:
        print(f"❌ MediaIngestionController test failed: {e}")
        failed_imports.append(("media_ingestion_controller", "local", "Media Ingestion Controller"))
    
    # Summary
    print("\n" + "=" * 60)
    if failed_imports:
        print("⚠️  Setup completed with some issues:")
        for module, package, description in failed_imports:
            print(f"   • {description} ({package})")
        
        print("\n💡 Troubleshooting tips:")
        if any("magic" in item[0] for item in failed_imports):
            print("   • For python-magic issues on macOS: brew install libmagic")
            print("   • For python-magic issues on Linux: sudo apt-get install libmagic-dev")
        
        if any("ffmpeg" in item[0] for item in failed_imports):
            print("   • For ffmpeg issues: install FFmpeg system package")
            print("   • macOS: brew install ffmpeg")
            print("   • Linux: sudo apt-get install ffmpeg")
        
        print("\n🔧 Run the system dependency installer:")
        print("   ./install_system_deps.sh")
        
    else:
        print("🎉 Setup completed successfully!")
        print("✅ All dependencies are installed and working correctly")
        
        print("\n🚀 Ready to use Media Ingestion Controller!")
        print("💡 Try running the demo: python demo_media_ingestion_controller.py")

if __name__ == "__main__":
    main()