#!/usr/bin/env python3
"""
Quick runner for Image Entity Extraction System
Demonstrates the enhanced features without requiring full model downloads
"""

import sys
import os

def run_streamlit_ui():
    """Run the Streamlit UI"""
    print("🚀 Starting Image Entity Extraction UI...")
    print("📍 URL: http://localhost:8501")
    print("💡 Upload an image to see the enhanced analysis features!")
    
    os.system("venv/bin/streamlit run image_entity_extraction_ui.py")

def run_demo():
    """Run the system demo"""
    print("🎯 Running Image Entity Extraction Demo...")
    os.system("venv/bin/python image_entity_extraction_system.py")

def run_tests():
    """Run the test suite"""
    print("🧪 Running Test Suite...")
    os.system("venv/bin/python test_image_entity_extraction_simple.py")

def main():
    """Main menu"""
    print("🖼️ Image Entity Extraction System")
    print("=" * 50)
    print("Enhanced with:")
    print("✅ Object detection and recognition")
    print("✅ Face recognition and person identification")
    print("✅ Scene understanding and contextual analysis")
    print("✅ Logo and brand detection for compliance")
    print("✅ Visual content moderation and safety detection")
    print()
    
    options = {
        "1": ("Run Streamlit UI", run_streamlit_ui),
        "2": ("Run System Demo", run_demo),
        "3": ("Run Tests", run_tests),
        "4": ("Exit", lambda: sys.exit(0))
    }
    
    while True:
        print("Choose an option:")
        for key, (desc, _) in options.items():
            print(f"  {key}. {desc}")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice in options:
            _, func = options[choice]
            try:
                func()
                if choice != "4":
                    input("\nPress Enter to continue...")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                input("Press Enter to continue...")
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()