"""
Medical Transcription Specialization System - Task 129
HIPAA-compliant medical transcription with specialized medical NLP capabilities
"""

import os
import re
import json
import logging
import hashlib
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from pathlib import Path
import unicodedata

# Medical NLP and entity recognition
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span

# Encryption and security
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

# Database
import sqlite3
from datetime import datetime, timedelta

# Configuration
from dataclasses import dataclass
import uuid

logger = logging.getLogger(__name__)

class MedicalEntityType(Enum):
    """Medical entity types for NER"""
    SYMPTOM = "symptom"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    DIAGNOSIS = "diagnosis"
    ANATOMY = "anatomy"
    DOSAGE = "dosage"
    MEASUREMENT = "measurement"
    CONDITION = "condition"
    PROVIDER = "provider"
    FACILITY = "facility"

class HIPAACompliance(Enum):
    """HIPAA compliance levels"""
    STRICT = "strict"
    STANDARD = "standard"
    RESEARCH = "research"

@dataclass
class MedicalEntity:
    """Medical entity with confidence and context"""
    text: str
    entity_type: MedicalEntityType
    confidence: float
    start_pos: int
    end_pos: int
    normalized_form: str
    medical_code: Optional[str] = None  # ICD-10, CPT, etc.
    context: Optional[str] = None
    severity: Optional[str] = None

@dataclass
class MedicalAbbreviation:
    """Medical abbreviation expansion"""
    abbreviation: str
    expansion: str
    category: str
    confidence: float
    context_dependent: bool = False

@dataclass
class HIPAAViolation:
    """HIPAA violation detection"""
    violation_type: str
    text: str
    position: Tuple[int, int]
    severity: str
    recommendation: str

@dataclass
class MedicalReport:
    """Generated medical report"""
    report_id: str
    patient_id: str  # Encrypted/anonymized
    provider_id: str  # Encrypted/anonymized
    transcript_id: str
    report_type: str
    sections: Dict[str, str]
    entities: List[MedicalEntity]
    medications: List[Dict[str, Any]]
    procedures: List[Dict[str, Any]]
    diagnoses: List[Dict[str, Any]]
    created_at: datetime
    encrypted_content: bytes
    compliance_status: str

class MedicalTerminologyValidator:
    """Validates and normalizes medical terminology"""
    
    def __init__(self):
        self.medical_terms = {}
        self.load_medical_dictionaries()
        
    def load_medical_dictionaries(self):
        """Load medical terminology dictionaries"""
        # Load ICD-10 codes
        self.icd10_codes = {
            'fever': 'R50.9',
            'headache': 'R51',
            'chest pain': 'R07.89',
            'shortness of breath': 'R06.00',
            'nausea': 'R11',
            'vomiting': 'R11',
            'diarrhea': 'K59.1',
            'constipation': 'K59.00',
            'fatigue': 'R53.83',
            'dizziness': 'R42'
        }
        
        # Load CPT codes for procedures
        self.cpt_codes = {
            'blood pressure check': '99213',
            'electrocardiogram': '93000',
            'chest x-ray': '71020',
            'blood glucose test': '82947',
            'urinalysis': '81003',
            'complete blood count': '85025'
        }
        
        # Load drug names and interactions
        self.medications = {
            'acetaminophen': {
                'generic': 'acetaminophen',
                'brand': ['tylenol', 'panadol'],
                'category': 'analgesic',
                'interactions': ['warfarin', 'alcohol']
            },
            'ibuprofen': {
                'generic': 'ibuprofen',
                'brand': ['advil', 'motrin'],
                'category': 'nsaid',
                'interactions': ['warfarin', 'aspirin']
            },
            'lisinopril': {
                'generic': 'lisinopril',
                'brand': ['prinivil', 'zestril'],
                'category': 'ace_inhibitor',
                'interactions': ['potassium supplements']
            }
        }
        
        # Load medical abbreviations
        self.abbreviations = {
            'bp': MedicalAbbreviation('bp', 'blood pressure', 'vital_signs', 0.95),
            'hr': MedicalAbbreviation('hr', 'heart rate', 'vital_signs', 0.95),
            'rr': MedicalAbbreviation('rr', 'respiratory rate', 'vital_signs', 0.95),
            'temp': MedicalAbbreviation('temp', 'temperature', 'vital_signs', 0.95),
            'dx': MedicalAbbreviation('dx', 'diagnosis', 'clinical', 0.90),
            'tx': MedicalAbbreviation('tx', 'treatment', 'clinical', 0.90),
            'hx': MedicalAbbreviation('hx', 'history', 'clinical', 0.90),
            'sx': MedicalAbbreviation('sx', 'symptoms', 'clinical', 0.90),
            'cc': MedicalAbbreviation('cc', 'chief complaint', 'clinical', 0.85),
            'hpi': MedicalAbbreviation('hpi', 'history of present illness', 'clinical', 0.90),
            'ros': MedicalAbbreviation('ros', 'review of systems', 'clinical', 0.90),
            'pe': MedicalAbbreviation('pe', 'physical examination', 'clinical', 0.90),
            'a&p': MedicalAbbreviation('a&p', 'assessment and plan', 'clinical', 0.90),
            'sob': MedicalAbbreviation('sob', 'shortness of breath', 'symptoms', 0.95),
            'cp': MedicalAbbreviation('cp', 'chest pain', 'symptoms', 0.90, True),  # Context dependent
            'n/v': MedicalAbbreviation('n/v', 'nausea and vomiting', 'symptoms', 0.95),
            'uri': MedicalAbbreviation('uri', 'upper respiratory infection', 'diagnosis', 0.90),
            'uti': MedicalAbbreviation('uti', 'urinary tract infection', 'diagnosis', 0.95),
            'dm': MedicalAbbreviation('dm', 'diabetes mellitus', 'condition', 0.90),
            'htn': MedicalAbbreviation('htn', 'hypertension', 'condition', 0.95),
            'cad': MedicalAbbreviation('cad', 'coronary artery disease', 'condition', 0.95),
            'copd': MedicalAbbreviation('copd', 'chronic obstructive pulmonary disease', 'condition', 0.95),
            'bid': MedicalAbbreviation('bid', 'twice daily', 'dosing', 0.95),
            'tid': MedicalAbbreviation('tid', 'three times daily', 'dosing', 0.95),
            'qid': MedicalAbbreviation('qid', 'four times daily', 'dosing', 0.95),
            'prn': MedicalAbbreviation('prn', 'as needed', 'dosing', 0.95),
            'po': MedicalAbbreviation('po', 'by mouth', 'route', 0.95),
            'iv': MedicalAbbreviation('iv', 'intravenous', 'route', 0.95),
            'im': MedicalAbbreviation('im', 'intramuscular', 'route', 0.95),
            'sl': MedicalAbbreviation('sl', 'sublingual', 'route', 0.90)
        }
        
    def validate_medical_term(self, term: str) -> Dict[str, Any]:
        """Validate and normalize medical terminology"""
        term_lower = term.lower().strip()
        
        # Check against known medical terms
        validation_result = {
            'original': term,
            'normalized': term_lower,
            'is_valid': False,
            'category': None,
            'code': None,
            'confidence': 0.0,
            'suggestions': []
        }
        
        # Check ICD-10 codes
        if term_lower in self.icd10_codes:
            validation_result.update({
                'is_valid': True,
                'category': 'diagnosis',
                'code': self.icd10_codes[term_lower],
                'confidence': 0.95
            })
            
        # Check medications
        elif term_lower in self.medications:
            med_info = self.medications[term_lower]
            validation_result.update({
                'is_valid': True,
                'category': 'medication',
                'normalized': med_info['generic'],
                'confidence': 0.90,
                'additional_info': med_info
            })
            
        # Check for brand names
        else:
            for generic, med_info in self.medications.items():
                if term_lower in [brand.lower() for brand in med_info['brand']]:
                    validation_result.update({
                        'is_valid': True,
                        'category': 'medication',
                        'normalized': generic,
                        'confidence': 0.85,
                        'additional_info': med_info
                    })
                    break
        
        return validation_result
    
    def expand_abbreviation(self, abbrev: str, context: str = None) -> Optional[MedicalAbbreviation]:
        """Expand medical abbreviation with context awareness"""
        abbrev_lower = abbrev.lower().strip()
        
        if abbrev_lower in self.abbreviations:
            abbreviation = self.abbreviations[abbrev_lower]
            
            # Handle context-dependent abbreviations
            if abbreviation.context_dependent and context:
                # Simple context analysis for 'cp'
                if abbrev_lower == 'cp':
                    if any(word in context.lower() for word in ['chest', 'cardiac', 'heart']):
                        return abbreviation
                    elif any(word in context.lower() for word in ['cerebral', 'brain', 'neuro']):
                        return MedicalAbbreviation('cp', 'cerebral palsy', 'condition', 0.85)
                    
            return abbreviation
        
        return None

class HIPAAComplianceChecker:
    """HIPAA compliance validation and PHI detection"""
    
    def __init__(self):
        self.phi_patterns = self._load_phi_patterns()
        self.safe_harbor_rules = self._load_safe_harbor_rules()
        
    def _load_phi_patterns(self) -> Dict[str, re.Pattern]:
        """Load PHI detection patterns"""
        return {
            'ssn': re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'date_birth': re.compile(r'\b(?:dob|date of birth|born)[\s:]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b', re.IGNORECASE),
            'mrn': re.compile(r'\b(?:mrn|medical record|patient id)[\s:]*([a-z0-9]{6,})\b', re.IGNORECASE),
            'address': re.compile(r'\b\d+\s+[A-Za-z\s]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|boulevard|blvd)\b', re.IGNORECASE),
            'zip_code': re.compile(r'\b\d{5}(?:-\d{4})?\b'),
            'credit_card': re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
            'name_pattern': re.compile(r'\b(?:patient|mr|mrs|ms|dr)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b')
        }
    
    def _load_safe_harbor_rules(self) -> Dict[str, Any]:
        """Load HIPAA Safe Harbor de-identification rules"""
        return {
            'direct_identifiers': [
                'names', 'addresses', 'dates', 'phone_numbers', 
                'email_addresses', 'ssn', 'mrn', 'account_numbers',
                'certificate_numbers', 'vehicle_identifiers',
                'device_identifiers', 'web_urls', 'ip_addresses',
                'biometric_identifiers', 'photos'
            ],
            'age_threshold': 89,  # Ages 90+ must be aggregated
            'small_geographic_areas': [
                'zip_codes_with_populations_less_than_20000'
            ]
        }
    
    def detect_phi(self, text: str) -> List[HIPAAViolation]:
        """Detect potential PHI in medical text"""
        violations = []
        
        for pattern_name, pattern in self.phi_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                violation = HIPAAViolation(
                    violation_type=f"potential_{pattern_name}",
                    text=match.group(0),
                    position=(match.start(), match.end()),
                    severity=self._get_violation_severity(pattern_name),
                    recommendation=self._get_deidentification_recommendation(pattern_name)
                )
                violations.append(violation)
        
        return violations
    
    def _get_violation_severity(self, pattern_name: str) -> str:
        """Get severity level for different PHI types"""
        high_risk = ['ssn', 'mrn', 'credit_card', 'date_birth']
        medium_risk = ['phone', 'email', 'address', 'name_pattern']
        
        if pattern_name in high_risk:
            return 'high'
        elif pattern_name in medium_risk:
            return 'medium'
        else:
            return 'low'
    
    def _get_deidentification_recommendation(self, pattern_name: str) -> str:
        """Get de-identification recommendations"""
        recommendations = {
            'ssn': 'Replace with random identifier or remove entirely',
            'phone': 'Replace with generic contact information',
            'email': 'Replace with generic email format',
            'date_birth': 'Replace with age or age range',
            'mrn': 'Replace with study-specific identifier',
            'address': 'Replace with city/state or remove',
            'zip_code': 'Use only first 3 digits if population > 20,000',
            'credit_card': 'Remove entirely',
            'name_pattern': 'Replace with generic identifiers (Patient A, Provider B)'
        }
        return recommendations.get(pattern_name, 'Review and consider de-identification')
    
    def anonymize_text(self, text: str, compliance_level: HIPAACompliance = HIPAACompliance.STANDARD) -> str:
        """Anonymize text according to HIPAA requirements"""
        anonymized = text
        violations = self.detect_phi(text)
        
        # Sort violations by position (reverse order to maintain positions)
        violations.sort(key=lambda x: x.position[0], reverse=True)
        
        for violation in violations:
            start, end = violation.position
            replacement = self._generate_replacement(violation, compliance_level)
            anonymized = anonymized[:start] + replacement + anonymized[end:]
        
        return anonymized
    
    def _generate_replacement(self, violation: HIPAAViolation, compliance_level: HIPAACompliance) -> str:
        """Generate appropriate replacement for PHI"""
        if 'ssn' in violation.violation_type:
            return '[SSN-REMOVED]'
        elif 'phone' in violation.violation_type:
            return '[PHONE-REMOVED]'
        elif 'email' in violation.violation_type:
            return '[EMAIL-REMOVED]'
        elif 'date_birth' in violation.violation_type:
            return '[DOB-REMOVED]'
        elif 'mrn' in violation.violation_type:
            return '[MRN-REMOVED]'
        elif 'address' in violation.violation_type:
            return '[ADDRESS-REMOVED]'
        elif 'name_pattern' in violation.violation_type:
            return '[NAME-REMOVED]'
        else:
            return '[PHI-REMOVED]'

class MedicalEntityExtractor:
    """Extract medical entities from transcribed text"""
    
    def __init__(self):
        self.setup_nlp_model()
        self.setup_medical_matchers()
        
    def setup_nlp_model(self):
        """Setup medical NLP model"""
        try:
            # Try to load medical-specific model
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model not found. Please install: python -m spacy download en_core_web_sm")
            raise
        
        # Add custom medical component
        if 'medical_entities' not in self.nlp.pipe_names:
            self.nlp.add_pipe('medical_entities', after='ner')
    
    def setup_medical_matchers(self):
        """Setup medical phrase matchers"""
        self.symptom_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.medication_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self.procedure_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        
        # Symptoms
        symptoms = [
            "fever", "headache", "nausea", "vomiting", "diarrhea", "constipation",
            "chest pain", "shortness of breath", "dizziness", "fatigue", "weakness",
            "abdominal pain", "back pain", "joint pain", "muscle pain", "sore throat",
            "cough", "runny nose", "congestion", "rash", "itching", "swelling"
        ]
        
        # Medications
        medications = [
            "acetaminophen", "ibuprofen", "aspirin", "lisinopril", "metoprolol",
            "amlodipine", "metformin", "insulin", "warfarin", "prednisone",
            "albuterol", "omeprazole", "levothyroxine", "simvastatin", "tylenol",
            "advil", "motrin", "lipitor", "nexium", "ventolin"
        ]
        
        # Procedures
        procedures = [
            "blood pressure check", "temperature check", "pulse check",
            "blood test", "urine test", "x-ray", "ct scan", "mri scan",
            "electrocardiogram", "ecg", "ekg", "ultrasound", "endoscopy",
            "colonoscopy", "biopsy", "injection", "vaccination"
        ]
        
        # Convert to spaCy patterns
        symptom_patterns = [self.nlp.make_doc(symptom) for symptom in symptoms]
        medication_patterns = [self.nlp.make_doc(med) for med in medications]
        procedure_patterns = [self.nlp.make_doc(proc) for proc in procedures]
        
        self.symptom_matcher.add("SYMPTOMS", symptom_patterns)
        self.medication_matcher.add("MEDICATIONS", medication_patterns)
        self.procedure_matcher.add("PROCEDURES", procedure_patterns)
    
    def extract_entities(self, text: str) -> List[MedicalEntity]:
        """Extract medical entities from text"""
        doc = self.nlp(text)
        entities = []
        
        # Extract using matchers
        entities.extend(self._extract_with_matcher(doc, self.symptom_matcher, MedicalEntityType.SYMPTOM))
        entities.extend(self._extract_with_matcher(doc, self.medication_matcher, MedicalEntityType.MEDICATION))
        entities.extend(self._extract_with_matcher(doc, self.procedure_matcher, MedicalEntityType.PROCEDURE))
        
        # Extract using spaCy NER
        for ent in doc.ents:
            if ent.label_ in ["PERSON", "ORG"]:
                # Skip potential PHI
                continue
            
            entity_type = self._map_spacy_label_to_medical(ent.label_)
            if entity_type:
                medical_entity = MedicalEntity(
                    text=ent.text,
                    entity_type=entity_type,
                    confidence=0.8,  # Default confidence for spaCy entities
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    normalized_form=ent.text.lower(),
                    context=self._get_entity_context(doc, ent)
                )
                entities.append(medical_entity)
        
        return entities
    
    def _extract_with_matcher(self, doc: Doc, matcher: PhraseMatcher, entity_type: MedicalEntityType) -> List[MedicalEntity]:
        """Extract entities using phrase matcher"""
        entities = []
        matches = matcher(doc)
        
        for match_id, start, end in matches:
            span = doc[start:end]
            entity = MedicalEntity(
                text=span.text,
                entity_type=entity_type,
                confidence=0.9,  # High confidence for exact matches
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_span_context(doc, span)
            )
            entities.append(entity)
        
        return entities
    
    def _map_spacy_label_to_medical(self, label: str) -> Optional[MedicalEntityType]:
        """Map spaCy labels to medical entity types"""
        mapping = {
            "DATE": None,  # Skip dates for PHI reasons
            "TIME": None,  # Skip times
            "PERSON": None,  # Skip persons for PHI reasons
            "ORG": None,   # Skip organizations for PHI reasons
            "QUANTITY": MedicalEntityType.MEASUREMENT,
            "CARDINAL": MedicalEntityType.DOSAGE
        }
        return mapping.get(label)
    
    def _get_entity_context(self, doc: Doc, ent: Span) -> str:
        """Get context around entity"""
        start = max(0, ent.start - 5)
        end = min(len(doc), ent.end + 5)
        context_span = doc[start:end]
        return context_span.text
    
    def _get_span_context(self, doc: Doc, span: Span) -> str:
        """Get context around span"""
        start = max(0, span.start - 5)
        end = min(len(doc), span.end + 5)
        context_span = doc[start:end]
        return context_span.text

class MedicalReportGenerator:
    """Generate structured medical reports from transcriptions"""
    
    def __init__(self):
        self.report_templates = self._load_report_templates()
        
    def _load_report_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load medical report templates"""
        return {
            'consultation': {
                'sections': [
                    'chief_complaint',
                    'history_of_present_illness',
                    'review_of_systems',
                    'physical_examination',
                    'assessment_and_plan'
                ],
                'required_fields': ['patient_id', 'provider_id', 'date'],
                'format': 'structured'
            },
            'progress_note': {
                'sections': [
                    'subjective',
                    'objective',
                    'assessment',
                    'plan'
                ],
                'required_fields': ['patient_id', 'provider_id', 'date'],
                'format': 'soap'
            },
            'discharge_summary': {
                'sections': [
                    'admission_diagnosis',
                    'discharge_diagnosis',
                    'hospital_course',
                    'discharge_medications',
                    'discharge_instructions',
                    'follow_up'
                ],
                'required_fields': ['patient_id', 'provider_id', 'admission_date', 'discharge_date'],
                'format': 'structured'
            }
        }
    
    def generate_report(self, 
                       transcript_text: str,
                       entities: List[MedicalEntity],
                       report_type: str = 'consultation',
                       metadata: Dict[str, Any] = None) -> MedicalReport:
        """Generate structured medical report"""
        
        if report_type not in self.report_templates:
            raise ValueError(f"Unknown report type: {report_type}")
        
        template = self.report_templates[report_type]
        
        # Extract sections from transcript
        sections = self._extract_sections(transcript_text, template['sections'])
        
        # Group entities by type
        medications = [e for e in entities if e.entity_type == MedicalEntityType.MEDICATION]
        procedures = [e for e in entities if e.entity_type == MedicalEntityType.PROCEDURE]
        diagnoses = [e for e in entities if e.entity_type == MedicalEntityType.DIAGNOSIS]
        
        # Create report
        report = MedicalReport(
            report_id=str(uuid.uuid4()),
            patient_id=metadata.get('patient_id', 'ANONYMOUS'),
            provider_id=metadata.get('provider_id', 'UNKNOWN'),
            transcript_id=metadata.get('transcript_id', ''),
            report_type=report_type,
            sections=sections,
            entities=entities,
            medications=self._format_medications(medications),
            procedures=self._format_procedures(procedures),
            diagnoses=self._format_diagnoses(diagnoses),
            created_at=datetime.now(),
            encrypted_content=b'',  # Will be encrypted separately
            compliance_status='pending_review'
        )
        
        return report
    
    def _extract_sections(self, text: str, section_names: List[str]) -> Dict[str, str]:
        """Extract sections from transcript text"""
        sections = {}
        
        # Simple section extraction based on keywords
        section_keywords = {
            'chief_complaint': ['chief complaint', 'cc:', 'presenting complaint'],
            'history_of_present_illness': ['history of present illness', 'hpi:', 'present illness'],
            'review_of_systems': ['review of systems', 'ros:', 'systems review'],
            'physical_examination': ['physical exam', 'pe:', 'examination', 'physical'],
            'assessment_and_plan': ['assessment and plan', 'a&p:', 'assessment', 'plan'],
            'subjective': ['subjective:', 'patient reports', 'patient states'],
            'objective': ['objective:', 'vital signs', 'examination'],
            'assessment': ['assessment:', 'impression:', 'diagnosis'],
            'plan': ['plan:', 'treatment:', 'recommendations']
        }
        
        for section_name in section_names:
            section_content = self._find_section_content(text, section_keywords.get(section_name, []))
            sections[section_name] = section_content
        
        return sections
    
    def _find_section_content(self, text: str, keywords: List[str]) -> str:
        """Find content for a specific section"""
        text_lower = text.lower()
        
        for keyword in keywords:
            pattern = rf'{re.escape(keyword)}[:\s]*([^.]*(?:\.[^.]*)*?)(?=(?:{'|'.join(keywords)})|$)'
            match = re.search(pattern, text_lower, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def _format_medications(self, medications: List[MedicalEntity]) -> List[Dict[str, Any]]:
        """Format medication entities for report"""
        formatted = []
        for med in medications:
            formatted.append({
                'name': med.text,
                'normalized_name': med.normalized_form,
                'confidence': med.confidence,
                'context': med.context,
                'medical_code': med.medical_code
            })
        return formatted
    
    def _format_procedures(self, procedures: List[MedicalEntity]) -> List[Dict[str, Any]]:
        """Format procedure entities for report"""
        formatted = []
        for proc in procedures:
            formatted.append({
                'name': proc.text,
                'normalized_name': proc.normalized_form,
                'confidence': proc.confidence,
                'context': proc.context,
                'medical_code': proc.medical_code
            })
        return formatted
    
    def _format_diagnoses(self, diagnoses: List[MedicalEntity]) -> List[Dict[str, Any]]:
        """Format diagnosis entities for report"""
        formatted = []
        for diag in diagnoses:
            formatted.append({
                'name': diag.text,
                'normalized_name': diag.normalized_form,
                'confidence': diag.confidence,
                'context': diag.context,
                'medical_code': diag.medical_code
            })
        return formatted

class EncryptionManager:
    """Handle encryption for HIPAA compliance"""
    
    def __init__(self, password: str = None):
        self.password = password or os.environ.get('MEDICAL_ENCRYPTION_KEY', 'default_key_change_me')
        self.fernet = self._create_cipher()
    
    def _create_cipher(self) -> Fernet:
        """Create Fernet cipher from password"""
        password_bytes = self.password.encode()
        salt = b'medical_transcription_salt'  # In production, use random salt per encryption
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def encrypt_text(self, text: str) -> bytes:
        """Encrypt text for secure storage"""
        return self.fernet.encrypt(text.encode())
    
    def decrypt_text(self, encrypted_data: bytes) -> str:
        """Decrypt text from secure storage"""
        return self.fernet.decrypt(encrypted_data).decode()
    
    def encrypt_report(self, report: MedicalReport) -> bytes:
        """Encrypt entire medical report"""
        report_dict = asdict(report)
        # Remove encrypted_content to avoid double encryption
        report_dict.pop('encrypted_content', None)
        report_json = json.dumps(report_dict, default=str)
        return self.encrypt_text(report_json)

class MedicalTranscriptionSystem:
    """Main medical transcription system with HIPAA compliance"""
    
    def __init__(self, compliance_level: HIPAACompliance = HIPAACompliance.STANDARD):
        self.compliance_level = compliance_level
        self.terminology_validator = MedicalTerminologyValidator()
        self.compliance_checker = HIPAAComplianceChecker()
        self.entity_extractor = MedicalEntityExtractor()
        self.report_generator = MedicalReportGenerator()
        self.encryption_manager = EncryptionManager()
        
        # Setup audit logging
        self.setup_audit_logging()
        
        # Initialize database
        self.init_database()
    
    def setup_audit_logging(self):
        """Setup HIPAA-compliant audit logging"""
        self.audit_logger = logging.getLogger('medical_audit')
        handler = logging.FileHandler('medical_audit.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
        self.audit_logger.setLevel(logging.INFO)
    
    def init_database(self):
        """Initialize secure database for medical records"""
        self.db_path = 'medical_transcriptions.db'
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS medical_transcriptions (
                    id TEXT PRIMARY KEY,
                    patient_id_hash TEXT,
                    provider_id_hash TEXT,
                    transcript_id TEXT,
                    report_type TEXT,
                    encrypted_content BLOB,
                    created_at TIMESTAMP,
                    last_accessed TIMESTAMP,
                    compliance_status TEXT,
                    phi_detected BOOLEAN,
                    INDEX(patient_id_hash),
                    INDEX(provider_id_hash),
                    INDEX(created_at)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    user_id TEXT,
                    action TEXT,
                    resource_id TEXT,
                    ip_address TEXT,
                    success BOOLEAN,
                    details TEXT
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS phi_incidents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transcript_id TEXT,
                    violation_type TEXT,
                    violation_text TEXT,
                    position_start INTEGER,
                    position_end INTEGER,
                    severity TEXT,
                    resolved BOOLEAN,
                    created_at TIMESTAMP
                )
            ''')
    
    def process_medical_transcription(self, 
                                    transcript_text: str,
                                    metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process medical transcription with full HIPAA compliance"""
        
        processing_id = str(uuid.uuid4())
        metadata = metadata or {}
        
        try:
            # Log processing start
            self.audit_log('transcription_start', processing_id, metadata)
            
            # Step 1: HIPAA Compliance Check
            phi_violations = self.compliance_checker.detect_phi(transcript_text)
            
            if phi_violations and self.compliance_level == HIPAACompliance.STRICT:
                # In strict mode, fail if PHI detected
                self.audit_log('transcription_failed_phi', processing_id, {
                    'violations_count': len(phi_violations),
                    'violations': [v.violation_type for v in phi_violations]
                })
                return {
                    'success': False,
                    'error': 'PHI detected in strict compliance mode',
                    'violations': phi_violations
                }
            
            # Step 2: Anonymize text if needed
            if phi_violations:
                anonymized_text = self.compliance_checker.anonymize_text(
                    transcript_text, self.compliance_level
                )
                # Store PHI incidents
                self._store_phi_incidents(processing_id, phi_violations)
            else:
                anonymized_text = transcript_text
            
            # Step 3: Expand medical abbreviations
            expanded_text = self._expand_medical_abbreviations(anonymized_text)
            
            # Step 4: Extract medical entities
            entities = self.entity_extractor.extract_entities(expanded_text)
            
            # Step 5: Validate medical terminology
            validated_entities = []
            for entity in entities:
                validation = self.terminology_validator.validate_medical_term(entity.text)
                if validation['is_valid']:
                    entity.confidence *= validation['confidence']
                    entity.medical_code = validation.get('code')
                validated_entities.append(entity)
            
            # Step 6: Generate medical report
            report = self.report_generator.generate_report(
                expanded_text, validated_entities, 
                metadata.get('report_type', 'consultation'),
                metadata
            )
            
            # Step 7: Encrypt and store report
            encrypted_content = self.encryption_manager.encrypt_report(report)
            report.encrypted_content = encrypted_content
            
            # Step 8: Store in database
            self._store_medical_record(report, len(phi_violations) > 0)
            
            # Step 9: Log successful completion
            self.audit_log('transcription_completed', processing_id, {
                'entities_count': len(validated_entities),
                'phi_detected': len(phi_violations) > 0,
                'report_type': report.report_type
            })
            
            return {
                'success': True,
                'processing_id': processing_id,
                'report_id': report.report_id,
                'entities': [asdict(e) for e in validated_entities],
                'sections': report.sections,
                'phi_violations': phi_violations if self.compliance_level != HIPAACompliance.STRICT else [],
                'compliance_status': report.compliance_status,
                'medications': report.medications,
                'procedures': report.procedures,
                'diagnoses': report.diagnoses
            }
            
        except Exception as e:
            self.audit_log('transcription_error', processing_id, {
                'error': str(e),
                'error_type': type(e).__name__
            })
            logger.error(f"Medical transcription processing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'processing_id': processing_id
            }
    
    def _expand_medical_abbreviations(self, text: str) -> str:
        """Expand medical abbreviations in text"""
        expanded_text = text
        words = text.split()
        
        for i, word in enumerate(words):
            # Clean word (remove punctuation for matching)
            clean_word = re.sub(r'[^\w]', '', word.lower())
            
            # Get context (surrounding words)
            context_start = max(0, i - 3)
            context_end = min(len(words), i + 4)
            context = ' '.join(words[context_start:context_end])
            
            # Try to expand abbreviation
            abbreviation = self.terminology_validator.expand_abbreviation(clean_word, context)
            if abbreviation and abbreviation.confidence > 0.8:
                # Replace in text, preserving case and punctuation
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                replacement = abbreviation.expansion
                expanded_text = pattern.sub(replacement, expanded_text, count=1)
        
        return expanded_text
    
    def _store_phi_incidents(self, processing_id: str, violations: List[HIPAAViolation]):
        """Store PHI violations for compliance tracking"""
        with sqlite3.connect(self.db_path) as conn:
            for violation in violations:
                conn.execute('''
                    INSERT INTO phi_incidents 
                    (transcript_id, violation_type, violation_text, position_start, 
                     position_end, severity, resolved, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    processing_id,
                    violation.violation_type,
                    violation.text,
                    violation.position[0],
                    violation.position[1],
                    violation.severity,
                    False,
                    datetime.now()
                ))
    
    def _store_medical_record(self, report: MedicalReport, phi_detected: bool):
        """Store encrypted medical record in database"""
        # Hash patient and provider IDs for privacy
        patient_hash = hashlib.sha256(report.patient_id.encode()).hexdigest()
        provider_hash = hashlib.sha256(report.provider_id.encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO medical_transcriptions 
                (id, patient_id_hash, provider_id_hash, transcript_id, report_type,
                 encrypted_content, created_at, last_accessed, compliance_status, phi_detected)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                report.report_id,
                patient_hash,
                provider_hash,
                report.transcript_id,
                report.report_type,
                report.encrypted_content,
                report.created_at,
                datetime.now(),
                report.compliance_status,
                phi_detected
            ))
    
    def audit_log(self, action: str, resource_id: str, details: Dict[str, Any]):
        """Log audit events for HIPAA compliance"""
        self.audit_logger.info(f"Action: {action}, Resource: {resource_id}, Details: {json.dumps(details)}")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO audit_log 
                (timestamp, user_id, action, resource_id, ip_address, success, details)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now(),
                details.get('user_id', 'system'),
                action,
                resource_id,
                details.get('ip_address', 'localhost'),
                details.get('success', True),
                json.dumps(details)
            ))
    
    def get_medical_record(self, report_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt medical record with audit logging"""
        try:
            self.audit_log('record_access_attempt', report_id, {'user_id': user_id})
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT encrypted_content, created_at, compliance_status
                    FROM medical_transcriptions 
                    WHERE id = ?
                ''', (report_id,))
                
                row = cursor.fetchone()
                if not row:
                    self.audit_log('record_access_failed', report_id, {
                        'user_id': user_id,
                        'reason': 'record_not_found'
                    })
                    return None
                
                encrypted_content, created_at, compliance_status = row
                
                # Decrypt content
                decrypted_json = self.encryption_manager.decrypt_text(encrypted_content)
                record_data = json.loads(decrypted_json)
                
                # Update last accessed
                conn.execute('''
                    UPDATE medical_transcriptions 
                    SET last_accessed = ? 
                    WHERE id = ?
                ''', (datetime.now(), report_id))
                
                self.audit_log('record_access_success', report_id, {'user_id': user_id})
                
                return record_data
                
        except Exception as e:
            self.audit_log('record_access_error', report_id, {
                'user_id': user_id,
                'error': str(e)
            })
            logger.error(f"Error retrieving medical record {report_id}: {e}")
            return None
    
    def get_compliance_report(self, start_date: datetime = None, end_date: datetime = None) -> Dict[str, Any]:
        """Generate HIPAA compliance report"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Total transcriptions
            cursor.execute('''
                SELECT COUNT(*) FROM medical_transcriptions 
                WHERE created_at BETWEEN ? AND ?
            ''', (start_date, end_date))
            total_transcriptions = cursor.fetchone()[0]
            
            # PHI incidents
            cursor.execute('''
                SELECT COUNT(*) FROM phi_incidents 
                WHERE created_at BETWEEN ? AND ?
            ''', (start_date, end_date))
            phi_incidents = cursor.fetchone()[0]
            
            # Unresolved PHI incidents
            cursor.execute('''
                SELECT COUNT(*) FROM phi_incidents 
                WHERE created_at BETWEEN ? AND ? AND resolved = 0
            ''', (start_date, end_date))
            unresolved_phi = cursor.fetchone()[0]
            
            # Audit events
            cursor.execute('''
                SELECT action, COUNT(*) FROM audit_log 
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY action
            ''', (start_date, end_date))
            audit_summary = dict(cursor.fetchall())
            
            return {
                'report_period': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'summary': {
                    'total_transcriptions': total_transcriptions,
                    'phi_incidents_detected': phi_incidents,
                    'unresolved_phi_incidents': unresolved_phi,
                    'compliance_rate': ((total_transcriptions - unresolved_phi) / max(total_transcriptions, 1)) * 100
                },
                'audit_activity': audit_summary,
                'compliance_level': self.compliance_level.value,
                'generated_at': datetime.now().isoformat()
            }

# Example usage and testing
if __name__ == "__main__":
    # Initialize medical transcription system
    medical_system = MedicalTranscriptionSystem(compliance_level=HIPAACompliance.STANDARD)
    
    # Example medical transcription
    sample_transcript = """
    Patient John Doe, DOB 01/15/1980, MRN 123456789, presents with chief complaint of chest pain.
    
    History of Present Illness:
    The patient reports onset of chest pain approximately 2 hours ago. Pain is described as sharp, 
    radiating to left arm. Associated with shortness of breath and nausea. No previous cardiac history.
    
    Physical Examination:
    BP 140/90, HR 95, RR 18, Temp 98.6F
    Heart: Regular rate and rhythm, no murmurs
    Lungs: Clear to auscultation bilaterally
    
    Assessment and Plan:
    1. Chest pain, rule out myocardial infarction
       - EKG ordered
       - Cardiac enzymes ordered
       - Start on aspirin 325mg po
    2. Hypertension
       - Consider lisinopril 5mg bid
    3. Anxiety related to chest pain
       - Reassurance provided
    
    Follow up in 24 hours or sooner if symptoms worsen.
    """
    
    # Process the transcription
    result = medical_system.process_medical_transcription(
        sample_transcript,
        metadata={
            'patient_id': 'PATIENT_001',
            'provider_id': 'DR_SMITH',
            'report_type': 'consultation',
            'transcript_id': 'TRANS_001'
        }
    )
    
    print("Medical Transcription Processing Result:")
    print(json.dumps(result, indent=2, default=str))
    
    # Generate compliance report
    compliance_report = medical_system.get_compliance_report()
    print("\nHIPAA Compliance Report:")
    print(json.dumps(compliance_report, indent=2, default=str))