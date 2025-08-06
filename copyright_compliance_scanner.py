#!/usr/bin/env python3
"""
Copyright and Music Compliance Scanner
Advanced system for detecting copyrighted content, music identification,
and licensing compliance for content creators and broadcasters.
"""

import os
import json
import sqlite3
import logging
import hashlib
import numpy as np
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import librosa
import requests
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class AudioFingerprint:
    """Represents an audio fingerprint for content identification"""
    id: str
    file_path: str
    duration: float
    fingerprint_data: str  # Base64 encoded fingerprint
    sample_rate: int
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class CopyrightMatch:
    """Represents a copyright match result"""
    match_id: str
    source_file: str
    matched_content: str
    confidence_score: float
    start_time: float
    end_time: float
    copyright_holder: Optional[str] = None
    license_status: Optional[str] = None  # 'licensed', 'unlicensed', 'unknown'
    action_required: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class ComplianceReport:
    """Comprehensive compliance report"""
    report_id: str
    file_path: str
    scan_date: datetime
    total_matches: int
    high_risk_matches: int
    medium_risk_matches: int
    low_risk_matches: int
    compliance_status: str  # 'compliant', 'non_compliant', 'review_required'
    matches: List[CopyrightMatch]
    recommendations: List[str]
    estimated_cost: Optional[float] = None

class AudioFingerprintGenerator:
    """Generates audio fingerprints for content identification"""
    
    def __init__(self):
        """Initialize the fingerprint generator"""
        self.sample_rate = 22050
        self.hop_length = 512
        self.n_mels = 128
        
    def generate_fingerprint(self, audio_file: str) -> Optional[AudioFingerprint]:
        """Generate audio fingerprint from file"""
        try:
            # Load audio file
            y, sr = librosa.load(audio_file, sr=self.sample_rate)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Extract features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13, hop_length=self.hop_length)
            chroma = librosa.feature.chroma(y=y, sr=sr, hop_length=self.hop_length)
            spectral_contrast = librosa.feature.spectral_contrast(y=y, sr=sr, hop_length=self.hop_length)
            
            # Combine features
            features = np.vstack([mfcc, chroma, spectral_contrast])
            
            # Create compact fingerprint using statistical moments
            fingerprint = np.array([
                np.mean(features, axis=1),
                np.std(features, axis=1),
                np.min(features, axis=1),
                np.max(features, axis=1)
            ]).flatten()
            
            # Convert to base64 string for storage
            fingerprint_bytes = fingerprint.astype(np.float32).tobytes()
            fingerprint_b64 = hashlib.sha256(fingerprint_bytes).hexdigest()
            
            return AudioFingerprint(
                id=hashlib.md5(audio_file.encode()).hexdigest(),
                file_path=audio_file,
                duration=duration,
                fingerprint_data=fingerprint_b64,
                sample_rate=sr
            )
            
        except Exception as e:
            logger.error(f"Failed to generate fingerprint for {audio_file}: {e}")
            return None
    
    def compare_fingerprints(self, fp1: str, fp2: str) -> float:
        """Compare two fingerprints and return similarity score"""
        try:
            # Simple hash comparison for demo
            # In production, use more sophisticated comparison
            return 1.0 if fp1 == fp2 else 0.0
        except Exception as e:
            logger.error(f"Failed to compare fingerprints: {e}")
            return 0.0

class MusicIdentificationService:
    """Service for identifying music and copyrighted content"""
    
    def __init__(self):
        """Initialize the music identification service"""
        self.fingerprint_generator = AudioFingerprintGenerator()
        self.known_content_db = {}  # In production, use external APIs
        
    def identify_music(self, audio_file: str) -> List[CopyrightMatch]:
        """Identify music in audio file"""
        try:
            # Generate fingerprint
            fingerprint = self.fingerprint_generator.generate_fingerprint(audio_file)
            if not fingerprint:
                return []
            
            matches = []
            
            # Mock identification results for demo
            # In production, integrate with services like:
            # - Shazam API
            # - ACRCloud
            # - Gracenote
            # - YouTube Content ID
            
            mock_matches = [
                {
                    "title": "Sample Song",
                    "artist": "Sample Artist",
                    "confidence": 0.85,
                    "start_time": 30.0,
                    "end_time": 180.0,
                    "copyright_holder": "Sample Music Corp",
                    "license_status": "unlicensed"
                }
            ]
            
            for i, match_data in enumerate(mock_matches):
                match = CopyrightMatch(
                    match_id=f"match_{i:03d}",
                    source_file=audio_file,
                    matched_content=f"{match_data['title']} by {match_data['artist']}",
                    confidence_score=match_data['confidence'],
                    start_time=match_data['start_time'],
                    end_time=match_data['end_time'],
                    copyright_holder=match_data['copyright_holder'],
                    license_status=match_data['license_status'],
                    action_required="License required" if match_data['license_status'] == 'unlicensed' else None,
                    metadata=match_data
                )
                matches.append(match)
            
            return matches
            
        except Exception as e:
            logger.error(f"Failed to identify music in {audio_file}: {e}")
            return []
    
    def check_licensing_status(self, content_id: str) -> Dict[str, Any]:
        """Check licensing status for identified content"""
        try:
            # Mock licensing check
            # In production, integrate with licensing databases
            return {
                "content_id": content_id,
                "license_available": True,
                "license_cost": 50.0,
                "license_type": "sync_license",
                "territory": "worldwide",
                "duration": "perpetual",
                "usage_rights": ["broadcast", "streaming", "social_media"]
            }
        except Exception as e:
            logger.error(f"Failed to check licensing for {content_id}: {e}")
            return {}

class CopyrightComplianceScanner:
    """Main copyright compliance scanner"""
    
    def __init__(self, db_path: str = "copyright_compliance.db"):
        """Initialize the compliance scanner"""
        self.db_path = db_path
        self.music_service = MusicIdentificationService()
        
        # Initialize database
        self._init_database()
        
        logger.info("Copyright Compliance Scanner initialized")
    
    def _init_database(self):
        """Initialize SQLite database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create tables
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audio_fingerprints (
                    id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    duration REAL NOT NULL,
                    fingerprint_data TEXT NOT NULL,
                    sample_rate INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS copyright_matches (
                    match_id TEXT PRIMARY KEY,
                    source_file TEXT NOT NULL,
                    matched_content TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    copyright_holder TEXT,
                    license_status TEXT,
                    action_required TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS compliance_reports (
                    report_id TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    scan_date TIMESTAMP NOT NULL,
                    total_matches INTEGER NOT NULL,
                    high_risk_matches INTEGER NOT NULL,
                    medium_risk_matches INTEGER NOT NULL,
                    low_risk_matches INTEGER NOT NULL,
                    compliance_status TEXT NOT NULL,
                    recommendations TEXT,
                    estimated_cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
    
    def scan_file(self, file_path: str) -> ComplianceReport:
        """Scan a file for copyright compliance"""
        try:
            logger.info(f"Scanning file: {file_path}")
            
            # Identify copyrighted content
            matches = self.music_service.identify_music(file_path)
            
            # Categorize matches by risk level
            high_risk = [m for m in matches if m.confidence_score >= 0.8 and m.license_status == 'unlicensed']
            medium_risk = [m for m in matches if 0.5 <= m.confidence_score < 0.8]
            low_risk = [m for m in matches if m.confidence_score < 0.5]
            
            # Determine compliance status
            if high_risk:
                compliance_status = 'non_compliant'
            elif medium_risk:
                compliance_status = 'review_required'
            else:
                compliance_status = 'compliant'
            
            # Generate recommendations
            recommendations = self._generate_recommendations(matches)
            
            # Estimate licensing costs
            estimated_cost = self._estimate_licensing_cost(matches)
            
            # Create report
            report = ComplianceReport(
                report_id=hashlib.md5(f"{file_path}_{datetime.now().isoformat()}".encode()).hexdigest(),
                file_path=file_path,
                scan_date=datetime.now(),
                total_matches=len(matches),
                high_risk_matches=len(high_risk),
                medium_risk_matches=len(medium_risk),
                low_risk_matches=len(low_risk),
                compliance_status=compliance_status,
                matches=matches,
                recommendations=recommendations,
                estimated_cost=estimated_cost
            )
            
            # Save to database
            self._save_report(report)
            
            return report
            
        except Exception as e:
            logger.error(f"Failed to scan file {file_path}: {e}")
            return ComplianceReport(
                report_id="error",
                file_path=file_path,
                scan_date=datetime.now(),
                total_matches=0,
                high_risk_matches=0,
                medium_risk_matches=0,
                low_risk_matches=0,
                compliance_status='error',
                matches=[],
                recommendations=["Scan failed - please try again"]
            )
    
    def _generate_recommendations(self, matches: List[CopyrightMatch]) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        unlicensed_matches = [m for m in matches if m.license_status == 'unlicensed']
        if unlicensed_matches:
            recommendations.append(f"Obtain licenses for {len(unlicensed_matches)} unlicensed tracks")
            recommendations.append("Consider using royalty-free music alternatives")
        
        high_confidence_matches = [m for m in matches if m.confidence_score >= 0.8]
        if high_confidence_matches:
            recommendations.append("Review high-confidence matches for accuracy")
        
        if not matches:
            recommendations.append("No copyrighted content detected - content appears compliant")
        
        return recommendations
    
    def _estimate_licensing_cost(self, matches: List[CopyrightMatch]) -> float:
        """Estimate total licensing cost"""
        total_cost = 0.0
        
        for match in matches:
            if match.license_status == 'unlicensed':
                # Mock cost estimation
                # In production, integrate with licensing APIs
                total_cost += 50.0  # Base license cost
        
        return total_cost
    
    def _save_report(self, report: ComplianceReport):
        """Save compliance report to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Save report
            cursor.execute('''
                INSERT OR REPLACE INTO compliance_reports
                (report_id, file_path, scan_date, total_matches, high_risk_matches,
                 medium_risk_matches, low_risk_matches, compliance_status, 
                 recommendations, estimated_cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id,
                report.file_path,
                report.scan_date.isoformat(),
                report.total_matches,
                report.high_risk_matches,
                report.medium_risk_matches,
                report.low_risk_matches,
                report.compliance_status,
                json.dumps(report.recommendations),
                report.estimated_cost
            ))
            
            # Save matches
            for match in report.matches:
                cursor.execute('''
                    INSERT OR REPLACE INTO copyright_matches
                    (match_id, source_file, matched_content, confidence_score,
                     start_time, end_time, copyright_holder, license_status,
                     action_required, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    match.match_id,
                    match.source_file,
                    match.matched_content,
                    match.confidence_score,
                    match.start_time,
                    match.end_time,
                    match.copyright_holder,
                    match.license_status,
                    match.action_required,
                    json.dumps(match.metadata) if match.metadata else None
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
    
    def get_report(self, report_id: str) -> Optional[ComplianceReport]:
        """Retrieve a compliance report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get report
            cursor.execute('SELECT * FROM compliance_reports WHERE report_id = ?', (report_id,))
            report_row = cursor.fetchone()
            
            if not report_row:
                return None
            
            # Get matches
            cursor.execute('SELECT * FROM copyright_matches WHERE source_file = ?', (report_row[1],))
            match_rows = cursor.fetchall()
            
            matches = []
            for row in match_rows:
                match = CopyrightMatch(
                    match_id=row[0],
                    source_file=row[1],
                    matched_content=row[2],
                    confidence_score=row[3],
                    start_time=row[4],
                    end_time=row[5],
                    copyright_holder=row[6],
                    license_status=row[7],
                    action_required=row[8],
                    metadata=json.loads(row[9]) if row[9] else None
                )
                matches.append(match)
            
            report = ComplianceReport(
                report_id=report_row[0],
                file_path=report_row[1],
                scan_date=datetime.fromisoformat(report_row[2]),
                total_matches=report_row[3],
                high_risk_matches=report_row[4],
                medium_risk_matches=report_row[5],
                low_risk_matches=report_row[6],
                compliance_status=report_row[7],
                matches=matches,
                recommendations=json.loads(report_row[8]) if report_row[8] else [],
                estimated_cost=report_row[9]
            )
            
            conn.close()
            return report
            
        except Exception as e:
            logger.error(f"Failed to get report {report_id}: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get report statistics
            cursor.execute('SELECT COUNT(*) FROM compliance_reports')
            total_reports = cursor.fetchone()[0]
            
            cursor.execute('SELECT compliance_status, COUNT(*) FROM compliance_reports GROUP BY compliance_status')
            status_counts = dict(cursor.fetchall())
            
            cursor.execute('SELECT AVG(total_matches) FROM compliance_reports')
            avg_matches = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT SUM(estimated_cost) FROM compliance_reports WHERE estimated_cost IS NOT NULL')
            total_estimated_cost = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_reports": total_reports,
                "compliance_status_distribution": status_counts,
                "average_matches_per_file": avg_matches,
                "total_estimated_licensing_cost": total_estimated_cost
            }
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}

# Demo function
def demo_copyright_compliance_scanner():
    """Demonstrate the copyright compliance scanner"""
    print("🔍 Copyright Compliance Scanner Demo")
    print("=" * 50)
    
    # Initialize scanner
    scanner = CopyrightComplianceScanner()
    
    # Create mock audio file for demo
    mock_audio_file = "demo_audio.mp3"
    print(f"📁 Scanning mock file: {mock_audio_file}")
    
    # Scan file
    report = scanner.scan_file(mock_audio_file)
    
    print(f"\n📊 Compliance Report:")
    print(f"Report ID: {report.report_id}")
    print(f"File: {report.file_path}")
    print(f"Scan Date: {report.scan_date}")
    print(f"Compliance Status: {report.compliance_status}")
    print(f"Total Matches: {report.total_matches}")
    print(f"High Risk: {report.high_risk_matches}")
    print(f"Medium Risk: {report.medium_risk_matches}")
    print(f"Low Risk: {report.low_risk_matches}")
    
    if report.estimated_cost:
        print(f"Estimated Licensing Cost: ${report.estimated_cost:.2f}")
    
    print(f"\n🎵 Detected Content:")
    for match in report.matches:
        print(f"  • {match.matched_content}")
        print(f"    Confidence: {match.confidence_score:.2f}")
        print(f"    Time: {match.start_time:.1f}s - {match.end_time:.1f}s")
        print(f"    License Status: {match.license_status}")
        if match.action_required:
            print(f"    Action Required: {match.action_required}")
    
    print(f"\n💡 Recommendations:")
    for rec in report.recommendations:
        print(f"  • {rec}")
    
    # Show statistics
    stats = scanner.get_statistics()
    print(f"\n📈 System Statistics:")
    print(f"Total Reports: {stats.get('total_reports', 0)}")
    print(f"Status Distribution: {stats.get('compliance_status_distribution', {})}")
    print(f"Average Matches: {stats.get('average_matches_per_file', 0):.1f}")
    print(f"Total Estimated Cost: ${stats.get('total_estimated_licensing_cost', 0):.2f}")
    
    print("\n🎉 Demo completed successfully!")

if __name__ == "__main__":
    demo_copyright_compliance_scanner()