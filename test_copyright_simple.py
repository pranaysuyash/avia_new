#!/usr/bin/env python3
"""Simple test for copyright compliance scanner"""

from copyright_compliance_scanner import CopyrightComplianceScanner, CopyrightMatch, ComplianceReport
from datetime import datetime
import tempfile
import os

try:
    print("Testing Copyright Compliance Scanner...")
    
    # Initialize scanner
    scanner = CopyrightComplianceScanner()
    print("✅ Scanner initialized successfully")
    
    # Create a temporary audio file
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as tmp:
        tmp_path = tmp.name
        tmp.write(b"Mock audio data")
    
    try:
        # Scan file (will use mock data)
        print("🔍 Scanning mock file...")
        report = scanner.scan_file(tmp_path)
        print(f"✅ Scan completed: {report.compliance_status}")
        print(f"   Total matches: {report.total_matches}")
        print(f"   Risk levels: High={report.high_risk_matches}, Medium={report.medium_risk_matches}, Low={report.low_risk_matches}")
        
        # Get statistics
        stats = scanner.get_statistics()
        print(f"✅ Stats retrieved: {stats.get('total_reports', 0)} total reports")
        
        print("\n✅ All basic tests passed!")
        
    finally:
        # Clean up
        os.unlink(tmp_path)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()