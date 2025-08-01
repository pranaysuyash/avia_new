#!/usr/bin/env python3
"""
Minimal integration test
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("🧪 Minimal Integration Test")
print("=" * 50)

# Test imports
tests_passed = 0
tests_total = 0

# Test 1: WebSocket imports
tests_total += 1
try:
    from websocket import EventType, Event
    print("✅ WebSocket imports successful")
    tests_passed += 1
except Exception as e:
    print(f"❌ WebSocket import failed: {e}")

# Test 2: Search imports
tests_total += 1
try:
    from search.search_manager import SearchManager
    print("✅ Search imports successful")
    tests_passed += 1
except Exception as e:
    print(f"❌ Search import failed: {e}")

# Test 3: Diarization imports
tests_total += 1
try:
    from speaker_diarization.diarization_manager import DiarizationManager
    print("✅ Diarization imports successful")
    tests_passed += 1
except Exception as e:
    print(f"❌ Diarization import failed: {e}")

# Test 4: Auth imports
tests_total += 1
try:
    from auth.auth_manager import AuthManager
    print("✅ Auth imports successful")
    tests_passed += 1
except Exception as e:
    print(f"❌ Auth import failed: {e}")

print(f"\n📊 Results: {tests_passed}/{tests_total} tests passed")

if tests_passed == tests_total:
    print("✅ All imports successful!")
else:
    print("⚠️ Some imports failed")