#!/usr/bin/env python3
"""
Test script for enterprise-grade UI
Run this to see the new professional interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the enterprise UI demo
from ui_enterprise_grade import demo_enterprise_ui

if __name__ == "__main__":
    print("🚀 Launching Enterprise UI Demo...")
    print("=" * 50)
    print("Open your browser to see the new interface")
    print("Features:")
    print("  ✅ Professional gradient headers")
    print("  ✅ Animated metric cards")
    print("  ✅ Glass morphism effects")
    print("  ✅ Status timelines")
    print("  ✅ Dark/Light theme toggle")
    print("  ✅ Smooth animations")
    print("  ✅ Modern typography")
    print("=" * 50)
    
    demo_enterprise_ui()
