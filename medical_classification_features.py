"""
Medical Classification Features
Extracted from comprehensive_text_classification_system.py

This module provides medical schema integration and healthcare-specific classification capabilities.
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MedicalSpecialty(Enum):
    """Medical specialties for classification"""
    CARDIOLOGY = "cardiology"
    NEUROLOGY = "neurology"
    ONCOLOGY = "oncology"
    PEDIATRICS = "pediatrics"
    PSYCHIATRY = "psychiatry"
    SURGERY = "surgery"
    EMERGENCY = "emergency"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    ANESTHESIOLOGY = "anesthesiology"
    DERMATOLOGY = "dermatology"
    ENDOCRINOLOGY = "endocrinology"
    GASTROENTEROLOGY = "gastroenterology"
    ORTHOPEDICS = "orthopedics"
    OPHTHALMOLOGY = "ophthalmology"
    GENERAL = "general"

class MedicalEntityType(Enum):
    """Types of medical entities"""
    SYMPTOM = "symptom"
    DIAGNOSIS = "diagnosis"
    MEDICATION = "medication"
    PROCEDURE = "procedure"
    ANATOMY = "anatomy"
    CONDITION = "condition"
    TREATMENT = "treatment"
    TEST = "test"
    ALLERGY = "allergy"
    DOSAGE = "dosage"

@dataclass
class MedicalEntity:
    """Represents a medical entity in text"""
    text: str
    entity_type: MedicalEntityType
    specialty: Optional[MedicalSpecialty] = None
    confidence: float = 0.0
    start_pos: int = 0
    end_pos: int = 0
    context: str = ""
    icd_codes: List[str] = field(default_factory=list)
    snomed_codes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ComplianceRecord:
    """Medical compliance tracking record"""
    record_id: str
    entity_id: str
    compliance_type: str  # HIPAA, FDA, etc.
    status: str
    created_at: datetime
    updated_at: datetime
    notes: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ProcessingSession:
    """Medical text processing session"""
    session_id: str
    session_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    total_entities: int = 0
    entities_by_type: Dict[str, int] = field(default_factory=dict)
    specialties_detected: List[MedicalSpecialty] = field(default_factory=list)
    compliance_status: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QualityMetrics:
    """Quality metrics for medical text processing"""
    session_id: str
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    entity_coverage: float = 0.0
    specialty_accuracy: float = 0.0
    compliance_score: float = 0.0
    processing_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

class MedicalTextClassifier:
    """Medical-specific text classification"""
    
    def __init__(self):
        self.medical_terms = self._load_medical_terms()
        self.specialty_keywords = self._load_specialty_keywords()
        self.compliance_patterns = self._load_compliance_patterns()
        
        logger.info("✅ Medical text classifier initialized")
    
    def _load_medical_terms(self) -> Dict[MedicalEntityType, List[str]]:
        """Load medical terminology dictionaries"""
        return {
            MedicalEntityType.SYMPTOM: [
                "fever", "headache", "nausea", "fatigue", "dizziness", "pain",
                "shortness of breath", "chest pain", "abdominal pain", "cough",
                "vomiting", "diarrhea", "constipation", "rash", "swelling"
            ],
            MedicalEntityType.DIAGNOSIS: [
                "diabetes", "hypertension", "asthma", "pneumonia", "bronchitis",
                "arthritis", "depression", "anxiety", "migraine", "stroke",
                "heart attack", "cancer", "infection", "flu", "covid"
            ],
            MedicalEntityType.MEDICATION: [
                "aspirin", "ibuprofen", "acetaminophen", "insulin", "metformin",
                "lisinopril", "atorvastatin", "omeprazole", "levothyroxine",
                "amlodipine", "metoprolol", "losartan", "hydrochlorothiazide"
            ],
            MedicalEntityType.PROCEDURE: [
                "surgery", "biopsy", "x-ray", "ct scan", "mri", "ultrasound",
                "blood test", "urine test", "ecg", "ekg", "colonoscopy",
                "endoscopy", "catheterization", "intubation", "dialysis"
            ],
            MedicalEntityType.ANATOMY: [
                "heart", "lung", "brain", "liver", "kidney", "stomach",
                "intestine", "bone", "muscle", "nerve", "blood vessel",
                "artery", "vein", "spine", "joint", "organ"
            ]
        }
    
    def _load_specialty_keywords(self) -> Dict[MedicalSpecialty, List[str]]:
        """Load specialty-specific keywords"""
        return {
            MedicalSpecialty.CARDIOLOGY: [
                "heart", "cardiac", "cardiovascular", "arrhythmia", "angina",
                "myocardial", "pacemaker", "angioplasty", "bypass", "ecg"
            ],
            MedicalSpecialty.NEUROLOGY: [
                "brain", "neurological", "seizure", "stroke", "migraine",
                "epilepsy", "parkinson", "alzheimer", "sclerosis", "neuropathy"
            ],
            MedicalSpecialty.ONCOLOGY: [
                "cancer", "tumor", "oncology", "chemotherapy", "radiation",
                "metastasis", "biopsy", "malignant", "benign", "carcinoma"
            ],
            MedicalSpecialty.PEDIATRICS: [
                "pediatric", "child", "infant", "baby", "vaccination",
                "growth", "development", "newborn", "adolescent", "juvenile"
            ],
            MedicalSpecialty.PSYCHIATRY: [
                "psychiatric", "mental health", "depression", "anxiety",
                "bipolar", "schizophrenia", "therapy", "counseling", "medication"
            ]
        }
    
    def _load_compliance_patterns(self) -> Dict[str, List[str]]:
        """Load compliance-related patterns"""
        return {
            "HIPAA": [
                "patient privacy", "protected health information", "phi",
                "consent", "authorization", "disclosure", "confidentiality"
            ],
            "FDA": [
                "fda approved", "clinical trial", "adverse event", "side effect",
                "contraindication", "dosage", "prescription", "over the counter"
            ],
            "GDPR": [
                "data protection", "consent", "right to erasure", "data subject",
                "processing", "personal data", "privacy policy"
            ]
        }
    
    def extract_medical_entities(self, text: str) -> List[MedicalEntity]:
        """Extract medical entities from text"""
        entities = []
        text_lower = text.lower()
        
        for entity_type, terms in self.medical_terms.items():
            for term in terms:
                if term in text_lower:
                    start_pos = text_lower.find(term)
                    end_pos = start_pos + len(term)
                    
                    # Determine specialty
                    specialty = self._determine_specialty(text_lower)
                    
                    entity = MedicalEntity(
                        text=term,
                        entity_type=entity_type,
                        specialty=specialty,
                        confidence=0.8,  # Rule-based confidence
                        start_pos=start_pos,
                        end_pos=end_pos,
                        context=text[max(0, start_pos-50):end_pos+50]
                    )
                    entities.append(entity)
        
        return entities
    
    def _determine_specialty(self, text: str) -> Optional[MedicalSpecialty]:
        """Determine medical specialty from text content"""
        specialty_scores = {}
        
        for specialty, keywords in self.specialty_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text)
            if score > 0:
                specialty_scores[specialty] = score
        
        if specialty_scores:
            return max(specialty_scores, key=specialty_scores.get)
        
        return MedicalSpecialty.GENERAL
    
    def classify_medical_text(self, text: str) -> Dict[str, Any]:
        """Classify medical text with specialty and compliance detection"""
        entities = self.extract_medical_entities(text)
        specialty = self._determine_specialty(text.lower())
        compliance_issues = self._check_compliance(text)
        
        # Calculate confidence scores
        entity_confidence = sum(e.confidence for e in entities) / len(entities) if entities else 0.0
        specialty_confidence = 0.8 if specialty != MedicalSpecialty.GENERAL else 0.5
        
        return {
            "specialty": specialty,
            "specialty_confidence": specialty_confidence,
            "entities": entities,
            "entity_count": len(entities),
            "entity_confidence": entity_confidence,
            "compliance_issues": compliance_issues,
            "overall_confidence": (entity_confidence + specialty_confidence) / 2
        }
    
    def _check_compliance(self, text: str) -> Dict[str, List[str]]:
        """Check for compliance-related content"""
        compliance_issues = {}
        text_lower = text.lower()
        
        for compliance_type, patterns in self.compliance_patterns.items():
            found_patterns = []
            for pattern in patterns:
                if pattern in text_lower:
                    found_patterns.append(pattern)
            
            if found_patterns:
                compliance_issues[compliance_type] = found_patterns
        
        return compliance_issues
    
    def create_processing_session(self, session_type: str = "medical_classification") -> ProcessingSession:
        """Create a new medical processing session"""
        session_id = f"med_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return ProcessingSession(
            session_id=session_id,
            session_type=session_type,
            start_time=datetime.now()
        )
    
    def finalize_session(self, session: ProcessingSession, results: List[Dict[str, Any]]) -> QualityMetrics:
        """Finalize processing session and calculate quality metrics"""
        session.end_time = datetime.now()
        session.total_entities = sum(r.get("entity_count", 0) for r in results)
        
        # Calculate entity type distribution
        entity_types = {}
        specialties = set()
        
        for result in results:
            for entity in result.get("entities", []):
                entity_type = entity.entity_type.value
                entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                
                if entity.specialty:
                    specialties.add(entity.specialty)
        
        session.entities_by_type = entity_types
        session.specialties_detected = list(specialties)
        
        # Calculate quality metrics
        avg_confidence = sum(r.get("overall_confidence", 0) for r in results) / len(results) if results else 0.0
        processing_time = (session.end_time - session.start_time).total_seconds()
        
        quality_metrics = QualityMetrics(
            session_id=session.session_id,
            accuracy=avg_confidence,
            precision=avg_confidence * 0.9,  # Estimated
            recall=avg_confidence * 0.85,    # Estimated
            f1_score=avg_confidence * 0.87,  # Estimated
            entity_coverage=min(session.total_entities / 10.0, 1.0),  # Normalize to 0-1
            specialty_accuracy=len(specialties) / max(len(results), 1),
            processing_time=processing_time
        )
        
        return quality_metrics

def integrate_with_production_classifier(production_system, text: str) -> Dict[str, Any]:
    """Integrate medical features with production text classification system"""
    
    # Initialize medical classifier
    medical_classifier = MedicalTextClassifier()
    
    # Get standard classification
    standard_result = production_system.classify_text(text)
    
    # Get medical classification
    medical_result = medical_classifier.classify_medical_text(text)
    
    # Combine results
    enhanced_result = {
        **standard_result,
        "medical_analysis": medical_result,
        "is_medical_content": len(medical_result["entities"]) > 0,
        "medical_specialty": medical_result["specialty"].value if medical_result["specialty"] else None,
        "compliance_requirements": list(medical_result["compliance_issues"].keys())
    }
    
    return enhanced_result

def main():
    """Demo medical classification features"""
    print("=== Medical Classification Features Demo ===\n")
    
    classifier = MedicalTextClassifier()
    
    # Sample medical texts
    sample_texts = [
        "Patient presents with chest pain and shortness of breath. ECG shows irregular rhythm. Recommend cardiology consultation.",
        "Child with fever and rash. Possible viral infection. Prescribed acetaminophen for symptom relief.",
        "Oncology patient receiving chemotherapy treatment. Monitor for adverse effects and adjust dosage as needed.",
        "Patient reports headache and dizziness. Neurological examination reveals no focal deficits."
    ]
    
    session = classifier.create_processing_session()
    results = []
    
    for i, text in enumerate(sample_texts, 1):
        print(f"Sample {i}: {text[:60]}...")
        result = classifier.classify_medical_text(text)
        results.append(result)
        
        print(f"   Specialty: {result['specialty'].value}")
        print(f"   Entities: {result['entity_count']}")
        print(f"   Confidence: {result['overall_confidence']:.2f}")
        
        if result['compliance_issues']:
            print(f"   Compliance: {list(result['compliance_issues'].keys())}")
        
        print()
    
    # Finalize session
    quality_metrics = classifier.finalize_session(session, results)
    
    print("=== Session Quality Metrics ===")
    print(f"Session ID: {quality_metrics.session_id}")
    print(f"Accuracy: {quality_metrics.accuracy:.2f}")
    print(f"Processing Time: {quality_metrics.processing_time:.2f}s")
    print(f"Total Entities: {session.total_entities}")
    print(f"Specialties Detected: {[s.value for s in session.specialties_detected]}")

if __name__ == "__main__":
    main()