#!/usr/bin/env python3
"""
Simple test to verify matplotlib import
"""

try:
    import matplotlib
    print(f"✅ matplotlib imported successfully: {matplotlib.__version__}")
    
    import matplotlib.pyplot as plt
    print("✅ matplotlib.pyplot imported successfully")
    
    import numpy as np
    print(f"✅ numpy imported successfully: {np.__version__}")
    
    import librosa
    print(f"✅ librosa imported successfully: {librosa.__version__}")
    
    import soundfile as sf
    print(f"✅ soundfile imported successfully: {sf.__version__}")
    
    print("\n🎉 All required packages are available!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    import sys
    print(f"Python path: {sys.path}")