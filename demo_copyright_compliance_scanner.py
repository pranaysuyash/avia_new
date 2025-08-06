#!/usr/bin/env python3
"""
Copyright Compliance Scanner Demo
Demonstrates copyright detection and music licensing compliance features
"""

from datetime import datetime
import os
import tempfile
import numpy as np
from copyright_compliance_scanner import (
    CopyrightComplianceScanner, ComplianceReport, CopyrightMatch,
    AudioFingerprint
)

def print_header(title):
    """Print a formatted header"""
    print(f"\n{'='*60}")
    print(f"⚖️ {title}")
    print(f"{'='*60}\n")

def print_match(match: CopyrightMatch, index: int):
    """Print a copyright match"""
    risk_level = "🔴 HIGH" if match.confidence_score > 0.9 else "🟡 MEDIUM" if match.confidence_score > 0.7 else "🟢 LOW"
    
    print(f"\n   Match #{index}:")
    print(f"   Content: {match.matched_content}")
    print(f"   Confidence: {match.confidence_score:.1%} {risk_level}")
    print(f"   Duration: {match.start_time:.1f}s - {match.end_time:.1f}s")
    if match.copyright_holder:
        print(f"   Copyright: {match.copyright_holder}")
    print(f"   License: {match.license_status}")
    if match.action_required:
        print(f"   ⚠️ Action: {match.action_required}")

def print_report(report: ComplianceReport):
    """Print a compliance report"""
    status_emoji = {
        'compliant': '✅',
        'non_compliant': '❌',
        'review_required': '⚠️'
    }
    
    print(f"\n📊 Compliance Report")
    print(f"   File: {report.file_path}")
    print(f"   Status: {status_emoji.get(report.compliance_status, '❓')} {report.compliance_status.upper()}")
    print(f"   Total Matches: {report.total_matches}")
    print(f"   Risk Breakdown: 🔴 {report.high_risk_matches} | 🟡 {report.medium_risk_matches} | 🟢 {report.low_risk_matches}")
    if report.estimated_cost:
        print(f"   Est. Licensing Cost: ${report.estimated_cost:,.2f}")

def demo_basic_scanning():
    """Demonstrate basic file scanning"""
    print_header("Basic File Scanning Demo")
    
    # Initialize scanner
    scanner = CopyrightComplianceScanner()
    print("✅ Initialized Copyright Compliance Scanner")
    
    # Create a mock audio file
    print("\n🎵 Creating mock audio file for demonstration...")
    
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
        # Generate mock audio data (1 second of sine wave)
        sample_rate = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = np.sin(2 * np.pi * 440 * t)  # 440 Hz tone
        
        # Save as WAV (simplified - in real use, use proper audio library)
        tmp_path = tmp_file.name
        print(f"   Created temporary file: {os.path.basename(tmp_path)}")
    
    # Scan the file
    print("\n🔍 Scanning file for copyright content...")
    
    try:
        report = scanner.scan_file(tmp_path)
        print_report(report)
        
        # Show matches
        if report.matches:
            print("\n📋 Detected Content:")
            for i, match in enumerate(report.matches, 1):
                print_match(match, i)
        
        # Show recommendations
        if report.recommendations:
            print("\n💡 Recommendations:")
            for rec in report.recommendations:
                print(f"   • {rec}")
        
    except Exception as e:
        print(f"   ⚠️ Scan completed with mock data: {e}")
    
    finally:
        # Clean up
        try:
            os.unlink(tmp_path)
        except:
            pass

def demo_whitelist_management():
    """Demonstrate whitelist functionality"""
    print_header("Whitelist Management Demo")
    
    scanner = CopyrightComplianceScanner()
    
    print("📋 Managing copyright whitelist...")
    
    # Add items to whitelist
    whitelist_items = [
        {
            "content_id": "track_001",
            "content_name": "Company Jingle",
            "copyright_holder": "Internal Creative Team",
            "license_info": {"type": "owned", "expires": "perpetual"}
        },
        {
            "content_id": "track_002",
            "content_name": "Background Music Pack",
            "copyright_holder": "Royalty Free Music Co",
            "license_info": {"type": "licensed", "expires": "2025-12-31"}
        },
        {
            "content_id": "track_003",
            "content_name": "Podcast Intro Music",
            "copyright_holder": "Audio Jungle",
            "license_info": {"type": "single_use", "project": "company_podcast"}
        }
    ]
    
    for item in whitelist_items:
        success = scanner.add_to_whitelist(
            item["content_id"],
            item["content_name"],
            item["copyright_holder"],
            item["license_info"]
        )
        if success:
            print(f"   ✅ Added: {item['content_name']}")
    
    # Display whitelist
    print("\n📄 Current Whitelist:")
    whitelist = scanner.get_whitelist()
    for i, (content_id, info) in enumerate(whitelist.items(), 1):
        print(f"\n   {i}. {info['name']}")
        print(f"      ID: {content_id}")
        print(f"      Copyright: {info.get('copyright_holder', 'Unknown')}")
        if 'license_info' in info:
            print(f"      License: {info['license_info'].get('type', 'Unknown')}")
    
    # Remove an item
    print("\n🗑️ Removing item from whitelist...")
    if scanner.remove_from_whitelist("track_003"):
        print("   ✅ Successfully removed 'Podcast Intro Music'")

def demo_risk_assessment():
    """Demonstrate risk assessment features"""
    print_header("Risk Assessment Demo")
    
    scanner = CopyrightComplianceScanner()
    
    print("🎯 Simulating different risk scenarios...")
    
    # Create mock reports with different risk levels
    scenarios = [
        {
            "name": "Low Risk Content",
            "matches": [
                CopyrightMatch(
                    match_id="low_001",
                    source_file="podcast_episode_001.mp3",
                    matched_content="Ambient Background Music",
                    confidence_score=0.65,
                    start_time=10.0,
                    end_time=15.0,
                    copyright_holder="Generic Music Library",
                    license_status="royalty_free"
                )
            ]
        },
        {
            "name": "Medium Risk Content",
            "matches": [
                CopyrightMatch(
                    match_id="med_001",
                    source_file="video_promo.mp4",
                    matched_content="Popular Song (Instrumental)",
                    confidence_score=0.82,
                    start_time=0.0,
                    end_time=30.0,
                    copyright_holder="Major Record Label",
                    license_status="unlicensed",
                    action_required="Obtain sync license"
                )
            ]
        },
        {
            "name": "High Risk Content",
            "matches": [
                CopyrightMatch(
                    match_id="high_001",
                    source_file="livestream_recording.mp4",
                    matched_content="Chart-Topping Hit Song",
                    confidence_score=0.95,
                    start_time=120.0,
                    end_time=240.0,
                    copyright_holder="Universal Music Group",
                    license_status="unlicensed",
                    action_required="Immediate removal or licensing required"
                ),
                CopyrightMatch(
                    match_id="high_002",
                    source_file="livestream_recording.mp4",
                    matched_content="Movie Soundtrack",
                    confidence_score=0.91,
                    start_time=300.0,
                    end_time=360.0,
                    copyright_holder="Warner Bros",
                    license_status="unlicensed",
                    action_required="Content may be blocked or monetized"
                )
            ]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📁 Scenario: {scenario['name']}")
        
        # Create report
        report = ComplianceReport(
            report_id=f"demo_{scenario['name'].lower().replace(' ', '_')}",
            file_path=scenario['matches'][0].source_file,
            scan_date=datetime.now(),
            matches=scenario['matches']
        )
        
        # Analyze report
        scanner._analyze_compliance_status(report)
        
        # Display results
        print_report(report)
        
        if report.matches:
            for i, match in enumerate(report.matches, 1):
                print_match(match, i)

def demo_statistics_and_analytics():
    """Demonstrate statistics and analytics"""
    print_header("Statistics and Analytics Demo")
    
    scanner = CopyrightComplianceScanner()
    
    # Generate mock scan history
    print("📊 Generating mock scan history...")
    
    mock_reports = []
    statuses = ['compliant', 'non_compliant', 'review_required']
    
    for i in range(20):
        status = np.random.choice(statuses, p=[0.6, 0.2, 0.2])
        matches = np.random.randint(0, 5)
        
        report = ComplianceReport(
            report_id=f"stat_{i:03d}",
            file_path=f"file_{i:03d}.mp3",
            scan_date=datetime.now(),
            compliance_status=status,
            total_matches=matches,
            high_risk_matches=max(0, matches - 2),
            medium_risk_matches=min(matches, 1),
            low_risk_matches=min(matches, 1),
            estimated_cost=matches * 50.0 if status == 'non_compliant' else 0
        )
        mock_reports.append(report)
        scanner.reports[report.report_id] = report
    
    # Get statistics
    stats = scanner.get_statistics()
    
    print("\n📈 Compliance Statistics:")
    print(f"   Total Reports: {stats.get('total_reports', 0)}")
    print(f"   Compliance Rate: {stats.get('compliance_rate', 0):.1f}%")
    print(f"   Average Matches/File: {stats.get('average_matches_per_file', 0):.1f}")
    print(f"   Total Est. Licensing Cost: ${stats.get('total_estimated_licensing_cost', 0):,.2f}")
    
    # Status distribution
    print("\n📊 Status Distribution:")
    status_dist = stats.get('compliance_status_distribution', {})
    for status, count in status_dist.items():
        percentage = (count / stats.get('total_reports', 1)) * 100
        print(f"   {status.replace('_', ' ').title()}: {count} ({percentage:.1f}%)")
    
    # Risk distribution
    print("\n⚠️ Risk Distribution:")
    risk_dist = stats.get('risk_distribution', {})
    print(f"   High Risk: {risk_dist.get('high', 0)} matches")
    print(f"   Medium Risk: {risk_dist.get('medium', 0)} matches")
    print(f"   Low Risk: {risk_dist.get('low', 0)} matches")

def demo_batch_scanning():
    """Demonstrate batch scanning capabilities"""
    print_header("Batch Scanning Demo")
    
    scanner = CopyrightComplianceScanner()
    
    print("📦 Preparing batch scan simulation...")
    
    # Simulate batch of files
    files = [
        "podcast_ep001.mp3",
        "podcast_ep002.mp3",
        "marketing_video.mp4",
        "training_video.mp4",
        "background_music.wav"
    ]
    
    print(f"\n   Files to scan: {len(files)}")
    for file in files:
        print(f"   • {file}")
    
    print("\n🔍 Starting batch scan...")
    
    results = []
    for i, file in enumerate(files, 1):
        print(f"\n   Scanning {i}/{len(files)}: {file}")
        
        # Simulate scan with random results
        has_matches = np.random.random() > 0.5
        
        if has_matches:
            matches = []
            num_matches = np.random.randint(1, 4)
            
            for j in range(num_matches):
                match = CopyrightMatch(
                    match_id=f"batch_{i}_{j}",
                    source_file=file,
                    matched_content=f"Sample Content {j+1}",
                    confidence_score=np.random.uniform(0.6, 0.95),
                    start_time=j * 30.0,
                    end_time=(j + 1) * 30.0,
                    license_status="unlicensed" if np.random.random() > 0.5 else "licensed"
                )
                matches.append(match)
            
            report = ComplianceReport(
                report_id=f"batch_{i}",
                file_path=file,
                scan_date=datetime.now(),
                matches=matches
            )
            scanner._analyze_compliance_status(report)
        else:
            report = ComplianceReport(
                report_id=f"batch_{i}",
                file_path=file,
                scan_date=datetime.now(),
                compliance_status='compliant',
                matches=[]
            )
        
        results.append(report)
        print(f"   Status: {report.compliance_status.upper()}")
    
    # Summary
    print("\n📊 Batch Scan Summary:")
    compliant = sum(1 for r in results if r.compliance_status == 'compliant')
    non_compliant = sum(1 for r in results if r.compliance_status == 'non_compliant')
    review = sum(1 for r in results if r.compliance_status == 'review_required')
    
    print(f"   ✅ Compliant: {compliant}")
    print(f"   ❌ Non-Compliant: {non_compliant}")
    print(f"   ⚠️ Review Required: {review}")
    
    total_cost = sum(r.estimated_cost or 0 for r in results)
    print(f"\n   💰 Total Estimated Licensing Cost: ${total_cost:,.2f}")

def main():
    """Run all demos"""
    print("\n" + "="*60)
    print("⚖️ COPYRIGHT COMPLIANCE SCANNER DEMO")
    print("AI-Powered Copyright Detection & Music Licensing")
    print("="*60)
    
    demos = [
        ("Basic File Scanning", demo_basic_scanning),
        ("Whitelist Management", demo_whitelist_management),
        ("Risk Assessment", demo_risk_assessment),
        ("Statistics & Analytics", demo_statistics_and_analytics),
        ("Batch Scanning", demo_batch_scanning)
    ]
    
    for name, demo_func in demos:
        input(f"\n⏯️  Press Enter to run {name} demo...")
        try:
            demo_func()
            print(f"\n✅ {name} demo completed successfully!")
        except Exception as e:
            print(f"\n❌ Error in {name} demo: {e}")
    
    print("\n" + "="*60)
    print("🎉 All demos completed!")
    print("="*60)

if __name__ == "__main__":
    main()