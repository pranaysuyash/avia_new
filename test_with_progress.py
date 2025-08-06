#!/usr/bin/env python3
"""
Test the image entity extraction system with progress tracking
"""

import sys
import time
from threading import Thread
import subprocess

def show_progress():
    """Show progress animation while models are downloading"""
    chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    i = 0
    while True:
        print(f"\r{chars[i % len(chars)]} Downloading AI models... This may take a few minutes on first run", end="", flush=True)
        time.sleep(0.1)
        i += 1

def run_system_test():
    """Run the system test with progress tracking"""
    print("🎯 Enhanced Image Entity Extraction System Test")
    print("=" * 60)
    print("📥 First run will download AI models (CLIP, BLIP, DETR, ViT)")
    print("⏱️ This may take 5-10 minutes depending on your internet connection")
    print("🔄 Subsequent runs will be much faster")
    print()
    
    # Start progress animation
    progress_thread = Thread(target=show_progress, daemon=True)
    progress_thread.start()
    
    try:
        # Run the actual system
        result = subprocess.run([
            "venv/bin/python", 
            "image_entity_extraction_system.py"
        ], capture_output=True, text=True, timeout=600)  # 10 minute timeout
        
        # Stop progress animation
        print("\r" + " " * 80 + "\r", end="")  # Clear progress line
        
        if result.returncode == 0:
            print("✅ System test completed successfully!")
            print("\n📊 Output:")
            print(result.stdout)
        else:
            print("❌ System test failed!")
            print("\n🚨 Error:")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print("\r" + " " * 80 + "\r", end="")  # Clear progress line
        print("⏰ Test timed out after 10 minutes")
        print("💡 This usually means the models are still downloading")
        print("🔄 Try running again - models will be cached for faster startup")
        
    except KeyboardInterrupt:
        print("\r" + " " * 80 + "\r", end="")  # Clear progress line
        print("\n\n⏹️ Test interrupted by user")
        
    except Exception as e:
        print("\r" + " " * 80 + "\r", end="")  # Clear progress line
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    run_system_test()