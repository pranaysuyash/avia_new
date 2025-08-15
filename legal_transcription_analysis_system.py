#!/usr/bin/env python3
"""
Legal Transcription and Analysis System
Task 130: Specialized system for legal proceedings, contracts, 
and compliance with legal documentation standards.
"""

import asyncio
import json
import re
import sqlite3
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalDocumentType(Enum):
    """Types of legal documents."""
    DEPOSITION = "deposition"
    COURT_HEARING = "court_hearing"
    CONTRACT = "contract"
    ARBITRATION = "arbitration"
    MEDIATION = "mediation"
    LEGAL_CONSULTATION = "legal_consultation"
    WITNESS_INTERVIEW = "witness_interview"
    EXPERT_TESTIMONY = "expert_testimony"
    SETTLEMENT_NEGOTIATION = "settlement_negotiation"
    BOARD_MEETING = "board_meeting"
    COMPLIANCE_REVIEW = "compliance_review"

class LegalEntity(Enum):
    """Legal entities involved in proceedings."""
    PLAINTIFF = "plaintiff"
    DEFENDANT = "defendant"
    WITNESS = "witness"
    ATTORNEY = "attorney"
    JUDGE = "judge"
    COURT_REPORTER = "court_reporter"
    EXPERT_WITNESS = "expert_witness"
    MEDIATOR = "mediator"
    ARBITRATOR = "arbitrator"
    CLERK = "clerk"

class LegalAction(Enum):
    """Types of legal actions detected."""
    OBJECTION = "objection"
    SUSTAINED = "sustained"
    OVERRULED = "overruled"
    MOTION = "motion"
    RULING = "ruling"
    RECESS = "recess"
    OFF_THE_RECORD = "off_the_record"
    ON_THE_RECORD = "on_the_record"
    SWEARING_IN = "swearing_in"
    STIPULATION = "stipulation"

class ConfidentialityLevel(Enum):
    """Confidentiality levels for legal content."""
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"
    ATTORNEY_CLIENT = "attorney_client"
    WORK_PRODUCT = "work_product"
    HIGHLY_CONFIDENTIAL = "highly_confidential"
    SEALED = "sealed"

@dataclass
class LegalSpeaker:
    """Information about a speaker in legal proceedings."""
    id: str
    name: str
    role: LegalEntity
    organization: Optional[str] = None
    bar_number: Optional[str] = None
    speaking_time: float = 0.0
    statement_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LegalStatement:
    """A statement made during legal proceedings."""
    id: str
    speaker: LegalSpeaker
    text: str
    timestamp: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    legal_actions: List[LegalAction] = field(default_factory=list)
    objections: List[str] = field(default_factory=list)
    citations: List[str] = field(default_factory=list)
    confidentiality: ConfidentialityLevel = ConfidentialityLevel.PUBLIC
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LegalCitation:
    """A legal citation found in the text."""
    citation_text: str
    case_name: Optional[str] = None
    court: Optional[str] = None
    year: Optional[int] = None
    volume: Optional[str] = None
    reporter: Optional[str] = None
    page: Optional[str] = None
    citation_type: str = "unknown"
    context: str = ""

@dataclass
class ComplianceFlag:
    """A compliance or procedural issue flag."""
    flag_id: str
    flag_type: str
    severity: str  # low, medium, high, critical
    description: str
    location: str
    timestamp: str
    resolution_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class LegalAnalysisResult:
    """Complete legal analysis result."""
    document_id: str
    document_type: LegalDocumentType
    transcript_text: str
    speakers: List[LegalSpeaker]
    statements: List[LegalStatement]
    legal_citations: List[LegalCitation]
    compliance_flags: List[ComplianceFlag]
    confidentiality_assessment: ConfidentialityLevel
    key_issues: List[str]
    procedural_timeline: List[Dict[str, Any]]
    summary: str
    processing_metadata: Dict[str, Any]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class LegalSpeakerIdentifier:
    """Identifies and tracks speakers in legal proceedings."""
    
    def __init__(self):
        self.speaker_patterns = self._initialize_speaker_patterns()
        self.role_indicators = self._initialize_role_indicators()
    
    def _initialize_speaker_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for identifying speakers."""
        return {
            'attorney_patterns': [
                r'(ATTORNEY|COUNSELOR|COUNSEL)\s+([A-Z][a-z]+)',
                r'(MR\.|MS\.|MRS\.)\s+([A-Z][A-Z]+)',
                r'([A-Z][a-z]+),?\s+(ESQ\.?|Attorney)',
            ],
            'witness_patterns': [
                r'(WITNESS|THE WITNESS)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+),?\s+(WITNESS|being duly sworn)',
            ],
            'court_patterns': [
                r'(THE COURT|JUDGE|YOUR HONOR)',
                r'(JUDGE\s+[A-Z][a-z]+)',
            ],
            'reporter_patterns': [
                r'(COURT REPORTER|REPORTER)',
                r'([A-Z][a-z]+),?\s+(CSR|CCR|RPR)',
            ]
        }
    
    def _initialize_role_indicators(self) -> Dict[str, LegalEntity]:
        """Initialize role indicator mappings."""
        return {
            'attorney': LegalEntity.ATTORNEY,
            'counsel': LegalEntity.ATTORNEY,
            'counselor': LegalEntity.ATTORNEY,
            'witness': LegalEntity.WITNESS,
            'court': LegalEntity.JUDGE,
            'judge': LegalEntity.JUDGE,
            'reporter': LegalEntity.COURT_REPORTER,
            'plaintiff': LegalEntity.PLAINTIFF,
            'defendant': LegalEntity.DEFENDANT,
            'mediator': LegalEntity.MEDIATOR,
            'arbitrator': LegalEntity.ARBITRATOR,
        }
    
    def identify_speakers(self, transcript_text: str) -> List[LegalSpeaker]:
        """Identify all speakers in the transcript."""
        speakers = {}
        lines = transcript_text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('('):
                continue
            
            # Look for speaker identification patterns
            speaker_info = self._extract_speaker_info(line)
            if speaker_info:
                speaker_id = speaker_info['id']
                
                if speaker_id not in speakers:
                    speakers[speaker_id] = LegalSpeaker(
                        id=speaker_id,
                        name=speaker_info['name'],
                        role=speaker_info['role'],
                        organization=speaker_info.get('organization'),
                        bar_number=speaker_info.get('bar_number')
                    )
                
                # Update speaking statistics
                speakers[speaker_id].statement_count += 1
        
        return list(speakers.values())
    
    def _extract_speaker_info(self, line: str) -> Optional[Dict[str, Any]]:
        """Extract speaker information from a line."""
        
        # Common pattern: "MR. SMITH: text" or "WITNESS: text"
        speaker_match = re.match(r'^([A-Z][A-Z\s\.]+):\s', line)
        if not speaker_match:
            return None
        
        speaker_text = speaker_match.group(1).strip()
        
        # Determine role and name
        role = LegalEntity.ATTORNEY  # Default
        name = speaker_text
        
        # Check for specific role indicators
        for indicator, entity in self.role_indicators.items():
            if indicator.upper() in speaker_text.upper():
                role = entity
                break
        
        # Clean up name
        if speaker_text.startswith(('MR.', 'MS.', 'MRS.', 'DR.')):
            name = speaker_text.split(None, 1)[-1] if len(speaker_text.split()) > 1 else speaker_text
        elif speaker_text in ['THE COURT', 'THE WITNESS', 'COURT REPORTER']:
            name = speaker_text
        
        return {
            'id': hashlib.md5(name.encode()).hexdigest()[:8],
            'name': name,
            'role': role,
            'raw_text': speaker_text
        }

class LegalActionDetector:
    """Detects legal actions and procedural events."""
    
    def __init__(self):
        self.action_patterns = self._initialize_action_patterns()
    
    def _initialize_action_patterns(self) -> Dict[LegalAction, List[str]]:
        """Initialize legal action detection patterns."""
        return {
            LegalAction.OBJECTION: [
                r'\bOBJECTION\b',
                r'\bI object\b',
                r'\bObjecting\b',
            ],
            LegalAction.SUSTAINED: [
                r'\bSUSTAINED\b',
                r'\bObjection sustained\b',
            ],
            LegalAction.OVERRULED: [
                r'\bOVERRULED\b',
                r'\bObjection overruled\b',
            ],
            LegalAction.MOTION: [
                r'\bMOTION\b',
                r'\bI move\b',
                r'\bMotion to\b',
            ],
            LegalAction.RULING: [
                r'\bRULING\b',
                r'\bI rule\b',
                r'\bThe court rules\b',
            ],
            LegalAction.RECESS: [
                r'\bRECESS\b',
                r'\bWe\'ll take a\s+(?:brief\s+)?(?:recess|break)\b',
                r'\bCourt is in recess\b',
            ],
            LegalAction.OFF_THE_RECORD: [
                r'\bOFF THE RECORD\b',
                r'\boff-the-record\b',
            ],
            LegalAction.ON_THE_RECORD: [
                r'\bON THE RECORD\b',
                r'\bBack on the record\b',
            ],
            LegalAction.SWEARING_IN: [
                r'\bDo you swear\b',
                r'\bRaise your right hand\b',
                r'\bbeing duly sworn\b',
            ],
            LegalAction.STIPULATION: [
                r'\bSTIPULATION\b',
                r'\bWe stipulate\b',
                r'\bstipulated\b',
            ],
        }
    
    def detect_actions(self, text: str) -> List[LegalAction]:
        """Detect legal actions in text."""
        detected_actions = []
        
        for action, patterns in self.action_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_actions.append(action)
                    break  # Only add each action once per text
        
        return detected_actions

class LegalCitationExtractor:
    """Extracts and parses legal citations."""
    
    def __init__(self):
        self.citation_patterns = self._initialize_citation_patterns()
    
    def _initialize_citation_patterns(self) -> List[Dict[str, str]]:
        """Initialize legal citation patterns."""
        return [
            {
                'pattern': r'(\d+)\s+([A-Z][a-z\.]+)\s+(\d+)',
                'type': 'case_citation',
                'format': 'volume reporter page'
            },
            {
                'pattern': r'(\d+)\s+U\.S\.\s+(\d+)',
                'type': 'supreme_court',
                'format': 'volume U.S. page'
            },
            {
                'pattern': r'(\d+)\s+F\.(?:2d|3d)\s+(\d+)',
                'type': 'federal_circuit',
                'format': 'volume F.2d/3d page'
            },
            {
                'pattern': r'(\d+)\s+S\.Ct\.\s+(\d+)',
                'type': 'supreme_court_reporter',
                'format': 'volume S.Ct. page'
            },
            {
                'pattern': r'(\d+\s+USC\s+§?\s*\d+)',
                'type': 'federal_statute',
                'format': 'USC section'
            },
            {
                'pattern': r'(\d+\s+CFR\s+§?\s*[\d\.]+)',
                'type': 'federal_regulation',
                'format': 'CFR section'
            }
        ]
    
    def extract_citations(self, text: str) -> List[LegalCitation]:
        """Extract legal citations from text."""
        citations = []
        
        for pattern_info in self.citation_patterns:
            pattern = pattern_info['pattern']
            citation_type = pattern_info['type']
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                citation = LegalCitation(
                    citation_text=match.group(0),
                    citation_type=citation_type,
                    context=self._get_context(text, match.start(), match.end())
                )
                
                # Parse specific fields based on type
                self._parse_citation_fields(citation, match, citation_type)
                citations.append(citation)
        
        return citations
    
    def _get_context(self, text: str, start: int, end: int, context_length: int = 100) -> str:
        """Get context around a citation."""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        return text[context_start:context_end].strip()
    
    def _parse_citation_fields(self, citation: LegalCitation, match: re.Match, citation_type: str):
        """Parse specific fields from citation match."""
        groups = match.groups()
        
        if citation_type == 'case_citation' and len(groups) >= 3:
            citation.volume = groups[0]
            citation.reporter = groups[1]
            citation.page = groups[2]
        elif citation_type in ['supreme_court', 'federal_circuit', 'supreme_court_reporter'] and len(groups) >= 2:
            citation.volume = groups[0]
            citation.page = groups[1]
        elif citation_type in ['federal_statute', 'federal_regulation']:
            # These are already captured in citation_text
            pass

class ComplianceChecker:
    """Checks legal compliance and procedural requirements."""
    
    def __init__(self):
        self.compliance_rules = self._initialize_compliance_rules()
    
    def _initialize_compliance_rules(self) -> Dict[str, Dict[str, Any]]:
        """Initialize compliance checking rules."""
        return {
            'attorney_identification': {
                'pattern': r'(Attorney|Counsel|Esq)',
                'severity': 'medium',
                'description': 'Attorney identification required',
                'check_type': 'presence'
            },
            'witness_oath': {
                'pattern': r'(sworn|oath|swear)',
                'severity': 'high',
                'description': 'Witness oath administration required',
                'check_type': 'presence'
            },
            'off_record_notation': {
                'pattern': r'off\s+(?:the\s+)?record',
                'severity': 'medium',
                'description': 'Off-record portions must be clearly marked',
                'check_type': 'proper_notation'
            },
            'objection_ruling': {
                'pattern': r'objection',
                'follow_up': r'(sustained|overruled)',
                'severity': 'high',
                'description': 'All objections must be ruled upon',
                'check_type': 'follow_up_required'
            },
            'confidential_material': {
                'pattern': r'(confidential|privileged|attorney.client)',
                'severity': 'critical',
                'description': 'Confidential material handling',
                'check_type': 'special_handling'
            }
        }
    
    def check_compliance(self, transcript_text: str, document_type: LegalDocumentType) -> List[ComplianceFlag]:
        """Check compliance issues in the transcript."""
        flags = []
        
        for rule_name, rule in self.compliance_rules.items():
            violations = self._check_rule(transcript_text, rule_name, rule)
            flags.extend(violations)
        
        # Document type specific checks
        type_specific_flags = self._check_document_type_compliance(transcript_text, document_type)
        flags.extend(type_specific_flags)
        
        return flags
    
    def _check_rule(self, text: str, rule_name: str, rule: Dict[str, Any]) -> List[ComplianceFlag]:
        """Check a specific compliance rule."""
        flags = []
        
        if rule['check_type'] == 'presence':
            if not re.search(rule['pattern'], text, re.IGNORECASE):
                flags.append(ComplianceFlag(
                    flag_id=str(uuid.uuid4()),
                    flag_type=rule_name,
                    severity=rule['severity'],
                    description=rule['description'],
                    location='document_wide',
                    timestamp=datetime.now().isoformat()
                ))
        
        elif rule['check_type'] == 'follow_up_required':
            # Find all instances of the pattern
            matches = list(re.finditer(rule['pattern'], text, re.IGNORECASE))
            
            for match in matches:
                # Check if follow-up pattern exists nearby
                context_start = max(0, match.start() - 500)
                context_end = min(len(text), match.end() + 500)
                context = text[context_start:context_end]
                
                if not re.search(rule['follow_up'], context, re.IGNORECASE):
                    flags.append(ComplianceFlag(
                        flag_id=str(uuid.uuid4()),
                        flag_type=rule_name,
                        severity=rule['severity'],
                        description=f"{rule['description']} at position {match.start()}",
                        location=f"position_{match.start()}",
                        timestamp=datetime.now().isoformat()
                    ))
        
        elif rule['check_type'] == 'special_handling':
            matches = list(re.finditer(rule['pattern'], text, re.IGNORECASE))
            
            for match in matches:
                flags.append(ComplianceFlag(
                    flag_id=str(uuid.uuid4()),
                    flag_type=rule_name,
                    severity=rule['severity'],
                    description=f"{rule['description']} found at position {match.start()}",
                    location=f"position_{match.start()}",
                    timestamp=datetime.now().isoformat(),
                    metadata={'matched_text': match.group(0)}
                ))
        
        return flags
    
    def _check_document_type_compliance(self, text: str, doc_type: LegalDocumentType) -> List[ComplianceFlag]:
        """Check document type specific compliance requirements."""
        flags = []
        
        if doc_type == LegalDocumentType.DEPOSITION:
            # Depositions require specific opening statements
            if not re.search(r'deposition.*taken.*pursuant', text, re.IGNORECASE):
                flags.append(ComplianceFlag(
                    flag_id=str(uuid.uuid4()),
                    flag_type='deposition_opening',
                    severity='high',
                    description='Deposition opening statement may be incomplete',
                    location='document_start',
                    timestamp=datetime.now().isoformat()
                ))
        
        elif doc_type == LegalDocumentType.COURT_HEARING:
            # Court hearings should have case information
            if not re.search(r'(case\s+no|cause\s+no|docket)', text, re.IGNORECASE):
                flags.append(ComplianceFlag(
                    flag_id=str(uuid.uuid4()),
                    flag_type='case_identification',
                    severity='medium',
                    description='Case number or identification may be missing',
                    location='document_header',
                    timestamp=datetime.now().isoformat()
                ))
        
        return flags

class LegalDatabase:
    """SQLite database for storing legal analysis results."""
    
    def __init__(self, db_path: str = "legal_analysis.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Main legal documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_documents (
                    id TEXT PRIMARY KEY,
                    document_type TEXT,
                    confidentiality_level TEXT,
                    summary TEXT,
                    key_issues TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Speakers table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_speakers (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    name TEXT,
                    role TEXT,
                    organization TEXT,
                    speaking_time REAL,
                    statement_count INTEGER,
                    FOREIGN KEY (document_id) REFERENCES legal_documents (id)
                )
            """)
            
            # Legal statements table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_statements (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    speaker_id TEXT,
                    text TEXT,
                    timestamp TEXT,
                    start_time REAL,
                    end_time REAL,
                    legal_actions TEXT,
                    confidentiality TEXT,
                    FOREIGN KEY (document_id) REFERENCES legal_documents (id),
                    FOREIGN KEY (speaker_id) REFERENCES legal_speakers (id)
                )
            """)
            
            # Legal citations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS legal_citations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    document_id TEXT,
                    citation_text TEXT,
                    case_name TEXT,
                    court TEXT,
                    year INTEGER,
                    citation_type TEXT,
                    context TEXT,
                    FOREIGN KEY (document_id) REFERENCES legal_documents (id)
                )
            """)
            
            # Compliance flags table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS compliance_flags (
                    id TEXT PRIMARY KEY,
                    document_id TEXT,
                    flag_type TEXT,
                    severity TEXT,
                    description TEXT,
                    location TEXT,
                    resolution_required BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES legal_documents (id)
                )
            """)
            
            conn.commit()
    
    def store_analysis(self, analysis: LegalAnalysisResult) -> str:
        """Store legal analysis results in database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Store main document
            cursor.execute("""
                INSERT OR REPLACE INTO legal_documents 
                (id, document_type, confidentiality_level, summary, key_issues)
                VALUES (?, ?, ?, ?, ?)
            """, (
                analysis.document_id,
                analysis.document_type.value,
                analysis.confidentiality_assessment.value,
                analysis.summary,
                json.dumps(analysis.key_issues)
            ))
            
            # Store speakers
            for speaker in analysis.speakers:
                cursor.execute("""
                    INSERT OR REPLACE INTO legal_speakers 
                    (id, document_id, name, role, organization, speaking_time, statement_count)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    speaker.id,
                    analysis.document_id,
                    speaker.name,
                    speaker.role.value,
                    speaker.organization,
                    speaker.speaking_time,
                    speaker.statement_count
                ))
            
            # Store statements
            for statement in analysis.statements:
                cursor.execute("""
                    INSERT OR REPLACE INTO legal_statements 
                    (id, document_id, speaker_id, text, timestamp, start_time, end_time, legal_actions, confidentiality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    statement.id,
                    analysis.document_id,
                    statement.speaker.id,
                    statement.text,
                    statement.timestamp,
                    statement.start_time,
                    statement.end_time,
                    json.dumps([action.value for action in statement.legal_actions]),
                    statement.confidentiality.value
                ))
            
            # Store citations
            for citation in analysis.legal_citations:
                cursor.execute("""
                    INSERT INTO legal_citations 
                    (document_id, citation_text, case_name, court, year, citation_type, context)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    analysis.document_id,
                    citation.citation_text,
                    citation.case_name,
                    citation.court,
                    citation.year,
                    citation.citation_type,
                    citation.context
                ))
            
            # Store compliance flags
            for flag in analysis.compliance_flags:
                cursor.execute("""
                    INSERT OR REPLACE INTO compliance_flags 
                    (id, document_id, flag_type, severity, description, location, resolution_required)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    flag.flag_id,
                    analysis.document_id,
                    flag.flag_type,
                    flag.severity,
                    flag.description,
                    flag.location,
                    flag.resolution_required
                ))
            
            conn.commit()
            return analysis.document_id
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get legal analysis statistics."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total documents
            cursor.execute("SELECT COUNT(*) FROM legal_documents")
            total_documents = cursor.fetchone()[0]
            
            # Document type distribution
            cursor.execute("""
                SELECT document_type, COUNT(*) 
                FROM legal_documents 
                GROUP BY document_type 
                ORDER BY COUNT(*) DESC
            """)
            document_types = cursor.fetchall()
            
            # Compliance statistics
            cursor.execute("""
                SELECT severity, COUNT(*) 
                FROM compliance_flags 
                GROUP BY severity
            """)
            compliance_stats = cursor.fetchall()
            
            # Citation statistics
            cursor.execute("SELECT COUNT(*) FROM legal_citations")
            total_citations = cursor.fetchone()[0]
            
            return {
                'total_documents': total_documents,
                'document_type_distribution': document_types,
                'compliance_statistics': compliance_stats,
                'total_citations': total_citations
            }

class LegalTranscriptionAnalysisSystem:
    """Main system for legal transcription analysis."""
    
    def __init__(self, db_path: str = "legal_analysis.db"):
        self.speaker_identifier = LegalSpeakerIdentifier()
        self.action_detector = LegalActionDetector()
        self.citation_extractor = LegalCitationExtractor()
        self.compliance_checker = ComplianceChecker()
        self.database = LegalDatabase(db_path)
        
        logger.info("Legal Transcription Analysis System initialized")
    
    async def analyze_legal_transcript(self, transcript_text: str, 
                                     document_type: LegalDocumentType,
                                     case_info: Optional[Dict[str, Any]] = None) -> LegalAnalysisResult:
        """Perform comprehensive legal analysis of transcript."""
        try:
            document_id = str(uuid.uuid4())
            logger.info(f"Analyzing legal transcript: {document_id}")
            
            # 1. Speaker identification
            speakers = self.speaker_identifier.identify_speakers(transcript_text)
            
            # 2. Parse statements
            statements = self._parse_statements(transcript_text, speakers)
            
            # 3. Extract legal citations
            legal_citations = self.citation_extractor.extract_citations(transcript_text)
            
            # 4. Compliance checking
            compliance_flags = self.compliance_checker.check_compliance(transcript_text, document_type)
            
            # 5. Assess confidentiality
            confidentiality_assessment = self._assess_confidentiality(transcript_text, statements)
            
            # 6. Extract key issues
            key_issues = self._extract_key_issues(transcript_text, statements)
            
            # 7. Create procedural timeline
            procedural_timeline = self._create_procedural_timeline(statements)
            
            # 8. Generate summary
            summary = self._generate_summary(transcript_text, document_type, key_issues)
            
            # 9. Create analysis result
            analysis = LegalAnalysisResult(
                document_id=document_id,
                document_type=document_type,
                transcript_text=transcript_text,
                speakers=speakers,
                statements=statements,
                legal_citations=legal_citations,
                compliance_flags=compliance_flags,
                confidentiality_assessment=confidentiality_assessment,
                key_issues=key_issues,
                procedural_timeline=procedural_timeline,
                summary=summary,
                processing_metadata={
                    'speakers_count': len(speakers),
                    'statements_count': len(statements),
                    'citations_count': len(legal_citations),
                    'compliance_flags_count': len(compliance_flags),
                    'case_info': case_info or {},
                    'processing_time': '<1s'
                }
            )
            
            # 10. Store in database
            self.database.store_analysis(analysis)
            
            logger.info("Legal transcript analysis completed successfully")
            return analysis
            
        except Exception as e:
            logger.error(f"Error in legal transcript analysis: {str(e)}")
            # Return minimal analysis with error info
            return LegalAnalysisResult(
                document_id=str(uuid.uuid4()),
                document_type=document_type,
                transcript_text=transcript_text,
                speakers=[],
                statements=[],
                legal_citations=[],
                compliance_flags=[],
                confidentiality_assessment=ConfidentialityLevel.PUBLIC,
                key_issues=[],
                procedural_timeline=[],
                summary="Analysis failed due to error.",
                processing_metadata={'error': str(e)}
            )
    
    def _parse_statements(self, transcript_text: str, speakers: List[LegalSpeaker]) -> List[LegalStatement]:
        """Parse individual statements from transcript."""
        statements = []
        lines = transcript_text.split('\n')
        current_speaker = None
        
        # Create speaker lookup
        speaker_lookup = {speaker.name: speaker for speaker in speakers}
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
            
            # Check for speaker identification
            speaker_match = re.match(r'^([A-Z][A-Z\s\.]+):\s*(.*)$', line)
            if speaker_match:
                speaker_name = speaker_match.group(1).strip()
                statement_text = speaker_match.group(2).strip()
                
                # Find matching speaker
                current_speaker = None
                for name, speaker in speaker_lookup.items():
                    if name in speaker_name or speaker_name in name:
                        current_speaker = speaker
                        break
                
                if current_speaker and statement_text:
                    # Detect legal actions in statement
                    legal_actions = self.action_detector.detect_actions(statement_text)
                    
                    # Create statement
                    statement = LegalStatement(
                        id=str(uuid.uuid4()),
                        speaker=current_speaker,
                        text=statement_text,
                        timestamp=datetime.now().isoformat(),
                        legal_actions=legal_actions
                    )
                    statements.append(statement)
            
            elif current_speaker and line and not line.startswith('('):
                # Continuation of previous statement
                if statements and statements[-1].speaker.id == current_speaker.id:
                    statements[-1].text += " " + line
                    # Re-detect legal actions with updated text
                    statements[-1].legal_actions = self.action_detector.detect_actions(statements[-1].text)
        
        return statements
    
    def _assess_confidentiality(self, transcript_text: str, statements: List[LegalStatement]) -> ConfidentialityLevel:
        """Assess the confidentiality level of the document."""
        text_lower = transcript_text.lower()
        
        # Check for highest confidentiality markers first
        if any(marker in text_lower for marker in ['sealed', 'court sealed', 'confidential sealed']):
            return ConfidentialityLevel.SEALED
        
        if any(marker in text_lower for marker in ['attorney-client', 'attorney client privilege', 'privileged']):
            return ConfidentialityLevel.ATTORNEY_CLIENT
        
        if any(marker in text_lower for marker in ['work product', 'attorney work product']):
            return ConfidentialityLevel.WORK_PRODUCT
        
        if any(marker in text_lower for marker in ['highly confidential', 'confidential - attorney eyes only']):
            return ConfidentialityLevel.HIGHLY_CONFIDENTIAL
        
        if any(marker in text_lower for marker in ['confidential', 'not for public disclosure']):
            return ConfidentialityLevel.CONFIDENTIAL
        
        return ConfidentialityLevel.PUBLIC
    
    def _extract_key_issues(self, transcript_text: str, statements: List[LegalStatement]) -> List[str]:
        """Extract key legal issues from the transcript."""
        key_issues = []
        text_lower = transcript_text.lower()
        
        # Common legal issue patterns
        issue_patterns = {
            'liability': r'\b(liable|liability|negligent|negligence)\b',
            'damages': r'\b(damages|compensation|monetary|financial harm)\b',
            'breach_of_contract': r'\b(breach|contract|agreement|violation)\b',
            'discovery': r'\b(discovery|document production|interrogatories)\b',
            'motion': r'\b(motion|summary judgment|dismiss)\b',
            'settlement': r'\b(settlement|settle|negotiate|mediation)\b',
            'evidence': r'\b(evidence|exhibit|testimony|witness)\b',
            'jurisdiction': r'\b(jurisdiction|venue|court|forum)\b',
            'statute_of_limitations': r'\b(statute of limitations|time.barred|untimely)\b',
            'constitutional': r'\b(constitutional|amendment|rights|due process)\b'
        }
        
        for issue, pattern in issue_patterns.items():
            if re.search(pattern, text_lower):
                key_issues.append(issue.replace('_', ' ').title())
        
        # Look for specific case types
        case_type_patterns = {
            'Personal Injury': r'\b(injury|accident|medical malpractice|slip and fall)\b',
            'Employment Law': r'\b(employment|discrimination|wrongful termination|harassment)\b',
            'Corporate Law': r'\b(corporate|board|shareholder|merger|acquisition)\b',
            'Intellectual Property': r'\b(patent|copyright|trademark|trade secret)\b',
            'Real Estate': r'\b(real estate|property|lease|title|easement)\b',
            'Family Law': r'\b(divorce|custody|alimony|child support|marriage)\b',
            'Criminal Law': r'\b(criminal|felony|misdemeanor|plea|sentence)\b'
        }
        
        for case_type, pattern in case_type_patterns.items():
            if re.search(pattern, text_lower):
                key_issues.append(case_type)
        
        return list(set(key_issues))  # Remove duplicates
    
    def _create_procedural_timeline(self, statements: List[LegalStatement]) -> List[Dict[str, Any]]:
        """Create a timeline of procedural events."""
        timeline = []
        
        for i, statement in enumerate(statements):
            if statement.legal_actions:
                for action in statement.legal_actions:
                    timeline.append({
                        'sequence': i + 1,
                        'action': action.value,
                        'speaker': statement.speaker.name,
                        'speaker_role': statement.speaker.role.value,
                        'timestamp': statement.timestamp,
                        'context': statement.text[:100] + "..." if len(statement.text) > 100 else statement.text
                    })
        
        return timeline
    
    def _generate_summary(self, transcript_text: str, document_type: LegalDocumentType, key_issues: List[str]) -> str:
        """Generate a summary of the legal proceeding."""
        summary_parts = []
        
        # Document type summary
        summary_parts.append(f"Legal {document_type.value.replace('_', ' ').title()}")
        
        # Key issues summary
        if key_issues:
            issues_text = ", ".join(key_issues[:3])  # Top 3 issues
            summary_parts.append(f"Primary issues: {issues_text}")
        
        # Basic statistics
        word_count = len(transcript_text.split())
        summary_parts.append(f"Document length: {word_count} words")
        
        return ". ".join(summary_parts) + "."
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        try:
            db_stats = self.database.get_statistics()
            
            return {
                'database_statistics': db_stats,
                'supported_document_types': len(LegalDocumentType),
                'supported_entity_types': len(LegalEntity),
                'compliance_rules': len(self.compliance_checker.compliance_rules),
                'system_status': 'operational'
            }
        except Exception as e:
            return {
                'error': str(e),
                'system_status': 'error'
            }

# Demo and testing functions
async def demo_legal_analysis():
    """Demonstrate the legal analysis capabilities."""
    system = LegalTranscriptionAnalysisSystem()
    
    print("⚖️  Legal Transcription Analysis System Demo")
    print("=" * 55)
    
    # Test cases for different legal document types
    test_cases = [
        {
            'type': LegalDocumentType.DEPOSITION,
            'text': """
MR. ATTORNEY: State your name for the record.
WITNESS: My name is John Smith.
MR. ATTORNEY: Mr. Smith, were you present at the accident scene on January 15th?
WITNESS: Yes, I was there.
MS. OPPOSING_COUNSEL: Objection, leading.
THE COURT: Sustained.
MR. ATTORNEY: What did you observe that day?
WITNESS: I saw the defendant's vehicle run the red light and strike the plaintiff's car.
            """
        },
        {
            'type': LegalDocumentType.COURT_HEARING,
            'text': """
THE COURT: This matter is before the court on defendant's motion to dismiss.
MR. DEFENSE_ATTORNEY: Your Honor, we move to dismiss this case pursuant to Rule 12(b)(6) for failure to state a claim.
MS. PLAINTIFF_ATTORNEY: Objection, Your Honor. Our complaint clearly states valid claims for negligence and breach of contract.
THE COURT: I'll hear arguments. Mr. Johnson, proceed.
MR. DEFENSE_ATTORNEY: The plaintiff has failed to establish the essential elements of negligence as set forth in Smith v. Jones, 123 F.3d 456 (2020).
            """
        },
        {
            'type': LegalDocumentType.LEGAL_CONSULTATION,
            'text': """
ATTORNEY: This consultation is confidential and protected by attorney-client privilege.
CLIENT: I need to understand my rights regarding the employment contract.
ATTORNEY: Let me review the terms. There's a non-compete clause that may be problematic.
CLIENT: Can they enforce it if I'm terminated without cause?
ATTORNEY: Under state law, the enforceability depends on reasonableness of scope and duration.
            """
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 Test Case {i}: {test_case['type'].value.replace('_', ' ').title()}")
        print("-" * 50)
        
        # Analyze transcript
        analysis = await system.analyze_legal_transcript(
            test_case['text'],
            test_case['type'],
            {'test_case': i}
        )
        
        # Display results
        print(f"Document ID: {analysis.document_id}")
        print(f"Document Type: {analysis.document_type.value}")
        print(f"Confidentiality Level: {analysis.confidentiality_assessment.value}")
        
        # Speakers
        print(f"\nSpeakers ({len(analysis.speakers)}):")
        for speaker in analysis.speakers:
            print(f"  - {speaker.name} ({speaker.role.value})")
        
        # Legal Actions
        all_actions = []
        for statement in analysis.statements:
            all_actions.extend(statement.legal_actions)
        
        if all_actions:
            action_counts = {}
            for action in all_actions:
                action_counts[action.value] = action_counts.get(action.value, 0) + 1
            
            print(f"\nLegal Actions:")
            for action, count in action_counts.items():
                print(f"  - {action}: {count}")
        
        # Citations
        if analysis.legal_citations:
            print(f"\nLegal Citations ({len(analysis.legal_citations)}):")
            for citation in analysis.legal_citations[:3]:  # Show first 3
                print(f"  - {citation.citation_text} ({citation.citation_type})")
        
        # Compliance Flags
        if analysis.compliance_flags:
            print(f"\nCompliance Flags ({len(analysis.compliance_flags)}):")
            for flag in analysis.compliance_flags:
                print(f"  - {flag.flag_type} ({flag.severity}): {flag.description}")
        
        # Key Issues
        if analysis.key_issues:
            print(f"\nKey Issues: {', '.join(analysis.key_issues)}")
        
        # Procedural Timeline
        if analysis.procedural_timeline:
            print(f"\nProcedural Timeline ({len(analysis.procedural_timeline)} events):")
            for event in analysis.procedural_timeline[:3]:  # Show first 3
                print(f"  - {event['action']} by {event['speaker']} ({event['speaker_role']})")
        
        print(f"\nSummary: {analysis.summary}")
    
    # System statistics
    print(f"\n📊 System Statistics:")
    stats = system.get_system_statistics()
    db_stats = stats.get('database_statistics', {})
    
    print(f"Total Documents: {db_stats.get('total_documents', 0)}")
    print(f"Document Types: {stats.get('supported_document_types', 0)}")
    print(f"Compliance Rules: {stats.get('compliance_rules', 0)}")
    print(f"System Status: {stats.get('system_status', 'unknown')}")
    
    print(f"\n✅ Legal analysis demo completed!")

if __name__ == "__main__":
    asyncio.run(demo_legal_analysis())