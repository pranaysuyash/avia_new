#!/usr/bin/env python3
"""
Audio/Video Transcription App - Startup Script
One-command deployment with configuration validation and setup
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Import configuration
from config import Config, validate_environment, print_configuration_status

def check_dependencies():
    """Check if required dependencies are installed"""
    print("🔍 Checking dependencies...")
    
    missing_deps = []
    
    # Check Python packages
    try:
        import streamlit
        import openai
        import spacy
        import ffmpeg
        import elevenlabs
        import dotenv
        print("✅ Python packages installed")
    except ImportError as e:
        missing_deps.append(f"Python package: {e.name}")
    
    # Check spaCy model
    try:
        import spacy
        nlp = spacy.load(Config.SPACY_MODEL)
        print("✅ spaCy model available")
    except OSError:
        missing_deps.append(f"spaCy model: {Config.SPACY_MODEL}")
    
    # Check FFmpeg
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg available")
        else:
            missing_deps.append("FFmpeg binary")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        missing_deps.append("FFmpeg binary")
    
    return missing_deps

def setup_environment():
    """Setup application environment"""
    print("⚙️ Setting up environment...")
    
    # Create temp directory
    temp_dir = Path(Config.TEMP_DIR)
    temp_dir.mkdir(exist_ok=True)
    print(f"✅ Temp directory: {temp_dir}")
    
    # Create logs directory
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    print(f"✅ Logs directory: {logs_dir}")
    
    # Check .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("⚠️ .env file not found")
        print("📋 Copying .env.example to .env...")
        
        example_file = Path(".env.example")
        if example_file.exists():
            import shutil
            shutil.copy(example_file, env_file)
            print("✅ .env file created from template")
            print("🔧 Please edit .env file with your API keys before running again")
            return False
        else:
            print("❌ .env.example file not found")
            return False
    
    return True

def install_missing_dependencies(missing_deps):
    """Install missing dependencies"""
    if not missing_deps:
        return True
    
    print(f"❌ Missing dependencies: {', '.join(missing_deps)}")
    print("🔧 Attempting to install missing dependencies...")
    
    for dep in missing_deps:
        if "spaCy model" in dep:
            model_name = dep.split(": ")[1]
            print(f"📥 Installing spaCy model: {model_name}")
            try:
                subprocess.run([sys.executable, "-m", "spacy", "download", model_name], 
                             check=True)
                print(f"✅ Installed {model_name}")
            except subprocess.CalledProcessError:
                print(f"❌ Failed to install {model_name}")
                print("💡 Try running: python -m spacy download en_core_web_sm")
                return False
        
        elif "Python package" in dep:
            print("❌ Missing Python packages detected")
            print("💡 Try running: pip install -r requirements.txt")
            return False
        
        elif "FFmpeg" in dep:
            print("❌ FFmpeg not found")
            print("💡 Install FFmpeg:")
            print("  - macOS: brew install ffmpeg")
            print("  - Ubuntu: sudo apt install ffmpeg")
            print("  - Windows: Download from https://ffmpeg.org/")
            return False
    
    return True

def start_application():
    """Start the Streamlit application"""
    print("🚀 Starting Audio/Video Transcription App...")
    print("📱 Application will be available at: http://localhost:8501")
    print("🛑 Press Ctrl+C to stop the application")
    print("-" * 50)
    
    try:
        # Start Streamlit with optimized settings
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--server.headless=false",
            "--browser.gatherUsageStats=false",
            "--server.fileWatcherType=none"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Failed to start application: {e}")
        return False
    
    return True

def main():
    """Main startup function"""
    print("=" * 60)
    print("🎵 AUDIO/VIDEO TRANSCRIPTION APP - STARTUP")
    print("=" * 60)
    
    # Step 1: Check dependencies
    missing_deps = check_dependencies()
    if missing_deps:
        if not install_missing_dependencies(missing_deps):
            print("\n❌ Setup failed. Please resolve dependency issues and try again.")
            sys.exit(1)
    
    # Step 2: Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed. Please configure .env file and try again.")
        sys.exit(1)
    
    # Step 3: Validate configuration
    print("\n📋 Configuration Status:")
    print_configuration_status()
    
    is_valid, config_message = validate_environment()
    if not is_valid:
        print(f"\n⚠️ Configuration Issues:")
        print(config_message)
        print("\n💡 The application will start but some features may not work.")
        print("   Please configure your API keys in the .env file for full functionality.")
        
        # Ask user if they want to continue
        try:
            response = input("\nContinue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Setup cancelled by user.")
                sys.exit(0)
        except KeyboardInterrupt:
            print("\nSetup cancelled by user.")
            sys.exit(0)
    
    # Step 4: Start application
    print("\n" + "=" * 60)
    if not start_application():
        sys.exit(1)
    
    print("\n👋 Thank you for using Audio/Video Transcription App!")

if __name__ == "__main__":
    main()