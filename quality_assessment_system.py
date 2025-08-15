"""
Comprehensive Quality Assessment System
Multi-dimensional quality evaluation for transcriptions with medical specialization
"""

import json
import numpy as np
import statistics
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import re
import logging
from abc import ABC, abstractmethod

# NLP and ML imports
try:
    import spacy
    from transformers import pipeline, AutoTokenizer, AutoModel
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import torch
    NLP_AVAILABLE = True
except ImportError:
    NLP_AVAILABLE = False

logger = logging.getLogger(__name__)


class QualityDimension(Enum):
    """Quality assessment dimensions"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    CONSISTENCY = "consistency"
    CLARITY = "clarity"
    MEDICAL_ACCURACY = "medical_accuracy"
    CLINICAL_RELEVANCE = "clinical_relevance"
    HIPAA_COMPLIANCE = "hipaa_compliance"
    SEMANTIC_COHERENCE = "semantic_coherence"
    LINGUISTIC_QUALITY = "linguistic_quality"
    CONTENT_STRUCTURE = "content_structure"


class QualityLevel(Enum):
    """Quality levels with numerical scores"""
    EXCELLENT = (95, 100, "Exceptional quality, exceeds expectations")
    VERY_GOOD = (85, 94, "High quality with minor issues")
    GOOD = (75, 84, "Acceptable quality with some improvements needed")
    FAIR = (65, 74, "Below average quality, requires attention")
    POOR = (0, 64, "Significant quality issues, major improvements required")
    
    def __init__(self, min_score: int, max_score: int, description: str):
        self.min_score = min_score
        self.max_score = max_score
        self.description = description
    
    @classmethod
    def from_score(cls, score: float) -> 'QualityLevel':
        """Get quality level from numerical score"""
        for level in cls:
            if level.min_score <= score <= level.max_score:
                return level
        return cls.POOR


@dataclass
class QualityMetric:
    """Individual quality metric result"""
    dimension: QualityDimension
    score: float  # 0-100
    level: QualityLevel
    details: str
    suggestions: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QualityAssessmentResult:
    """Comprehensive quality assessment result"""
    overall_score: float
    overall_level: QualityLevel
    dimension_scores: Dict[QualityDimension, QualityMetric]
    summary: str
    recommendations: List[str]
    strengths: List[str]
    weaknesses: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "overall_score": self.overall_score,
            "overall_level": self.overall_level.name,
            "overall_level_description": self.overall_level.description,
            "dimension_scores": {
                dim.value: {
                    "score": metric.score,
                    "level": metric.level.name,
                    "level_description": metric.level.description,
                    "details": metric.details,
                    "suggestions": metric.suggestions,
                    "evidence": metric.evidence,
                    "confidence": metric.confidence
                }
                for dim, metric in self.dimension_scores.items()
            },
            "summary": self.summary,
            "recommendations": self.recommendations,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
            "metadata": self.metadata,
            "assessment_timestamp": self.assessment_timestamp.isoformat()
        }


class QualityAssessor(ABC):
    """Abstract base class for quality assessors"""
    
    @abstractmethod
    def assess(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> QualityMetric:
        """Assess quality for specific dimension"""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> QualityDimension:
        """Quality dimension this assessor evaluates"""
        pass


class AccuracyAssessor(QualityAssessor):
    """Assess transcription accuracy"""
    
    @property
    def dimension(self) -> QualityDimension:
        return QualityDimension.ACCURACY
    
    def assess(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> QualityMetric:
        """Assess transcription accuracy based on various indicators"""
        score = 85.0  # Base score
        suggestions = []
        evidence = {}
        
        # Check for common transcription errors
        error_patterns = [
            (r'\b(um|uh|er|ah)\b', -2, "Excessive filler words detected"),
            (r'\[inaudible\]|\[unclear\]', -5, "Inaudible/unclear segments found"),
            (r'\b(huh|what|sorry)\b', -1, "Potential misunderstandings"),
            (r'[A-Z]{3,}', -1, "Possible OCR/transcription errors (all caps)")
        ]
        
        for pattern, penalty, description in error_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            if matches:
                count = len(matches)
                score += penalty * min(count, 10)  # Cap penalty
                evidence[description] = count
                if count > 5:
                    suggestions.append(f"Review and correct {description.lower()}")
        
        # Check for proper sentence structure
        sentences = re.split(r'[.!?]+', transcript)
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            if avg_sentence_length < 3:
                score -= 10
                suggestions.append("Sentences appear too short, check for proper punctuation")
            elif avg_sentence_length > 50:
                score -= 5
                suggestions.append("Very long sentences detected, check for run-on sentences")
            
            evidence["average_sentence_length"] = avg_sentence_length
            evidence["sentence_count"] = len(sentences)
        
        # Check confidence score from metadata
        if metadata and "confidence" in metadata:
            confidence_score = metadata["confidence"]
            if confidence_score < 0.8:
                score -= (0.8 - confidence_score) * 30
                suggestions.append("Low transcription confidence detected, consider re-processing")
            evidence["transcription_confidence"] = confidence_score
        
        score = max(0, min(100, score))
        level = QualityLevel.from_score(score)
        
        details = f"Accuracy assessment based on error patterns, sentence structure, and confidence metrics."
        
        return QualityMetric(
            dimension=self.dimension,
            score=score,
            level=level,
            details=details,
            suggestions=suggestions,
            evidence=evidence
        )


class CompletenessAssessor(QualityAssessor):
    """Assess transcription completeness"""
    
    @property
    def dimension(self) -> QualityDimension:
        return QualityDimension.COMPLETENESS
    
    def assess(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> QualityMetric:
        """Assess completeness of transcription"""
        score = 90.0  # Base score
        suggestions = []
        evidence = {}
        
        # Check for incomplete markers
        incomplete_patterns = [
            (r'\[incomplete\]|\[cut off\]', -10, "Incomplete segments"),
            (r'\.\.\.', -2, "Ellipses indicating missing content"),
            (r'\[silence\]|\[pause\]', -1, "Long pauses/silences"),
            (r'\bmissing\b|\blost\b', -3, "Missing content indicators")
        ]
        
        for pattern, penalty, description in incomplete_patterns:
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            if matches:
                count = len(matches)
                score += penalty * count
                evidence[description] = count
                suggestions.append(f"Address {description.lower()}")
        
        # Check transcript length vs expected duration
        if metadata and "duration" in metadata:
            duration = metadata["duration"]  # in seconds
            word_count = len(transcript.split())
            
            # Average speaking rate is 150-200 words per minute
            expected_words_min = (duration / 60) * 120
            expected_words_max = (duration / 60) * 220
            
            if word_count < expected_words_min * 0.7:
                score -= 15
                suggestions.append("Transcript appears significantly shorter than expected for duration")
            elif word_count < expected_words_min:
                score -= 5
                suggestions.append("Transcript may be missing some content")
            
            evidence["word_count"] = word_count
            evidence["expected_word_range"] = (expected_words_min, expected_words_max)
            evidence["duration_seconds"] = duration
        
        # Check for section completeness in medical transcripts
        if metadata and metadata.get("type") == "medical":
            medical_sections = [
                "chief complaint", "history", "examination", "assessment", "plan"
            ]
            present_sections = []
            for section in medical_sections:
                if re.search(section, transcript, re.IGNORECASE):
                    present_sections.append(section)
            
            completeness_ratio = len(present_sections) / len(medical_sections)
            if completeness_ratio < 0.6:
                score -= 20
                suggestions.append("Key medical sections appear to be missing")
            elif completeness_ratio < 0.8:
                score -= 10
                suggestions.append("Some medical sections may be incomplete")
            
            evidence["medical_sections_present"] = present_sections
            evidence["medical_completeness_ratio"] = completeness_ratio
        
        score = max(0, min(100, score))
        level = QualityLevel.from_score(score)
        
        details = f"Completeness assessment based on missing content indicators and expected length."
        
        return QualityMetric(
            dimension=self.dimension,
            score=score,
            level=level,
            details=details,
            suggestions=suggestions,
            evidence=evidence
        )


class ConsistencyAssessor(QualityAssessor):
    """Assess transcription consistency"""
    
    @property
    def dimension(self) -> QualityDimension:
        return QualityDimension.CONSISTENCY
    
    def assess(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> QualityMetric:
        """Assess consistency in terminology, formatting, and style"""
        score = 90.0
        suggestions = []
        evidence = {}
        
        # Check terminology consistency
        words = transcript.lower().split()
        word_variants = {}
        
        # Common medical term variations
        medical_variants = {
            'medication': ['medication', 'medicine', 'drug', 'med'],
            'patient': ['patient', 'pt'],
            'doctor': ['doctor', 'dr', 'physician'],
            'blood_pressure': ['blood pressure', 'bp', 'blood-pressure']
        }
        
        for canonical, variants in medical_variants.items():
            found_variants = [v for v in variants if v in words]
            if len(found_variants) > 1:
                word_variants[canonical] = found_variants
                score -= 2
                suggestions.append(f"Inconsistent terminology for {canonical}: {', '.join(found_variants)}")
        
        evidence["terminology_variants"] = word_variants
        
        # Check capitalization consistency
        sentences = re.split(r'[.!?]+', transcript)
        capitalization_issues = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and not sentence[0].isupper():
                capitalization_issues += 1
        
        if capitalization_issues > 0:
            score -= min(capitalization_issues * 2, 10)
            suggestions.append(f"Inconsistent capitalization in {capitalization_issues} sentences")
            evidence["capitalization_issues"] = capitalization_issues
        
        # Check punctuation consistency
        punctuation_patterns = {
            'multiple_spaces': r'\s{2,}',
            'inconsistent_quotes': r'["""]',
            'mixed_dashes': r'[-–—]'
        }
        
        for pattern_name, pattern in punctuation_patterns.items():
            matches = re.findall(pattern, transcript)
            if len(set(matches)) > 1:  # Multiple different types found
                score -= 3
                suggestions.append(f"Inconsistent {pattern_name.replace('_', ' ')}")
                evidence[pattern_name] = list(set(matches))
        
        # Check format consistency for times, dates, measurements
        time_formats = re.findall(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm)?\b', transcript)
        date_formats = re.findall(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', transcript)
        
        if len(set(time_formats)) > 1:
            score -= 3
            suggestions.append("Inconsistent time formatting")
            evidence["time_format_variations"] = list(set(time_formats))
        
        if len(set(date_formats)) > 1:
            score -= 3
            suggestions.append("Inconsistent date formatting")
            evidence["date_format_variations"] = list(set(date_formats))
        
        score = max(0, min(100, score))
        level = QualityLevel.from_score(score)
        
        details = "Consistency assessment based on terminology, formatting, and style uniformity."
        
        return QualityMetric(
            dimension=self.dimension,
            score=score,
            level=level,
            details=details,
            suggestions=suggestions,
            evidence=evidence
        )


class MedicalAccuracyAssessor(QualityAssessor):
    """Assess medical terminology accuracy and clinical correctness using comprehensive medical schema"""
    
    def __init__(self):
        self.comprehensive_schema = self._load_comprehensive_schema()
        self.medical_terms = self._load_medical_terms()
        self.drug_names = self._load_drug_names()
        
    @property
    def dimension(self) -> QualityDimension:
        return QualityDimension.MEDICAL_ACCURACY
    
    def _load_comprehensive_schema(self) -> Dict[str, Any]:
        """Load comprehensive medical schema for validation"""
        try:
            from comprehensive_medical_schema import COMPREHENSIVE_MEDICAL_SCHEMA
            return COMPREHENSIVE_MEDICAL_SCHEMA
        except ImportError:
            logger.warning("Comprehensive medical schema not available, using basic schema")
            return {}
    
    def _load_medical_terms(self) -> Dict[str, List[str]]:
        """Load extensive medical terminology dictionary"""
        return {
            "diagnoses": [
                "hypertension", "diabetes", "pneumonia", "asthma", "copd",
                "myocardial infarction", "stroke", "depression", "anxiety",
                "cancer", "arthritis", "fibromyalgia", "lupus", "multiple sclerosis",
                "parkinson's disease", "alzheimer's disease", "dementia", "epilepsy",
                "migraine", "chronic pain", "irritable bowel syndrome", "crohn's disease"
            ],
            "procedures": [
                "colonoscopy", "endoscopy", "biopsy", "surgery", "catheterization",
                "angioplasty", "intubation", "cardioversion", "mri", "ct scan",
                "x-ray", "ultrasound", "ecg", "eeg", "blood work", "urinalysis",
                "mammography", "bone density scan", "stress test", "pulmonary function"
            ],
            "anatomy": [
                "heart", "lung", "kidney", "liver", "brain", "spine", "abdomen",
                "chest", "pelvis", "extremities", "joints", "muscles", "bones",
                "skin", "eyes", "ears", "nose", "throat", "gastrointestinal",
                "cardiovascular", "respiratory", "neurological", "endocrine"
            ],
            "symptoms": [
                "chest pain", "shortness of breath", "nausea", "vomiting", "fever",
                "headache", "dizziness", "fatigue", "weakness", "joint pain",
                "muscle aches", "back pain", "abdominal pain", "constipation",
                "diarrhea", "insomnia", "anxiety", "depression", "confusion",
                "memory loss", "tremor", "numbness", "tingling", "swelling"
            ],
            "vital_signs": [
                "blood pressure", "heart rate", "respiratory rate", "temperature",
                "oxygen saturation", "pulse", "weight", "height", "bmi"
            ],
            "social_determinants": [
                "housing", "employment", "education", "insurance", "transportation",
                "food security", "social support", "income", "language barriers",
                "cultural factors", "neighborhood safety", "access to care"
            ],
            "preventive_care": [
                "vaccination", "screening", "mammogram", "colonoscopy", "pap smear",
                "cholesterol check", "blood pressure monitoring", "diabetes screening",
                "osteoporosis screening", "skin cancer screening", "eye exam",
                "dental care", "lifestyle counseling", "smoking cessation"
            ],
            "mental_health": [
                "depression", "anxiety", "ptsd", "bipolar disorder", "schizophrenia",
                "panic disorder", "ocd", "adhd", "autism", "eating disorder",
                "substance abuse", "addiction", "suicide risk", "psychotherapy",
                "psychiatric medication", "mental health screening"
            ]
        }
    
    def _load_drug_names(self) -> List[str]:
        """Load comprehensive drug names"""
        return [
            # Cardiovascular
            "aspirin", "lisinopril", "atorvastatin", "metoprolol", "amlodipine", 
            "losartan", "carvedilol", "warfarin", "clopidogrel", "simvastatin",
            # Diabetes
            "metformin", "insulin", "glipizide", "glyburide", "pioglitazone",
            "sitagliptin", "januvia", "lantus", "humalog", "novolog",
            # Pain/Anti-inflammatory
            "ibuprofen", "acetaminophen", "naproxen", "celecoxib", "tramadol",
            "morphine", "oxycodone", "hydrocodone", "gabapentin", "pregabalin",
            # Mental Health
            "sertraline", "fluoxetine", "escitalopram", "paroxetine", "venlafaxine",
            "duloxetine", "bupropion", "trazodone", "lorazepam", "clonazepam",
            # Antibiotics
            "amoxicillin", "azithromycin", "ciprofloxacin", "doxycycline", "cephalexin",
            # GI
            "omeprazole", "pantoprazole", "ranitidine", "metoclopramide", "ondansetron",
            # Respiratory
            "albuterol", "prednisone", "montelukast", "fluticasone", "budesonide",
            # Thyroid
            "levothyroxine", "liothyronine", "methimazole", "propylthiouracil"
        ]
    
    def assess(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> QualityMetric:
        """Assess medical accuracy using comprehensive medical schema"""
        if not metadata or metadata.get("type") != "medical":
            # Not a medical transcript, return high score with note
            return QualityMetric(
                dimension=self.dimension,
                score=95.0,
                level=QualityLevel.EXCELLENT,
                details="Non-medical transcript - medical accuracy assessment not applicable",
                suggestions=[],
                evidence={"transcript_type": "non-medical"}
            )
        
        score = 85.0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        # Comprehensive medical terminology assessment
        schema_coverage = self._assess_schema_coverage(transcript, metadata)
        score += schema_coverage["coverage_bonus"]
        suggestions.extend(schema_coverage["suggestions"])
        evidence.update(schema_coverage["evidence"])
        
        # Enhanced medical terminology validation
        medical_term_accuracy = self._validate_medical_terminology(transcript)
        score += medical_term_accuracy["accuracy_adjustment"]
        suggestions.extend(medical_term_accuracy["suggestions"])
        evidence.update(medical_term_accuracy["evidence"])
        
        # Social determinants of health assessment
        sdoh_assessment = self._assess_social_determinants(transcript)
        score += sdoh_assessment["score_adjustment"]
        suggestions.extend(sdoh_assessment["suggestions"])
        evidence.update(sdoh_assessment["evidence"])
        
        # Comprehensive vital signs and measurements validation
        vitals_assessment = self._validate_comprehensive_vitals(transcript)
        score += vitals_assessment["score_adjustment"]
        suggestions.extend(vitals_assessment["suggestions"])
        evidence.update(vitals_assessment["evidence"])
        
        # Care quality indicators assessment
        care_quality = self._assess_care_quality_indicators(transcript)
        score += care_quality["score_adjustment"]
        suggestions.extend(care_quality["suggestions"])
        evidence.update(care_quality["evidence"])
        
        # Preventive care completeness
        preventive_assessment = self._assess_preventive_care(transcript)
        score += preventive_assessment["score_adjustment"]
        suggestions.extend(preventive_assessment["suggestions"])
        evidence.update(preventive_assessment["evidence"])
        
        # Mental health considerations
        mental_health_assessment = self._assess_mental_health_completeness(transcript)
        score += mental_health_assessment["score_adjustment"]
        suggestions.extend(mental_health_assessment["suggestions"])
        evidence.update(mental_health_assessment["evidence"])
        
        # Enhanced medication management assessment
        medication_assessment = self._assess_comprehensive_medication_management(transcript)
        score += medication_assessment["score_adjustment"]
        suggestions.extend(medication_assessment["suggestions"])
        evidence.update(medication_assessment["evidence"])
        
        # Patient engagement and communication quality
        engagement_assessment = self._assess_patient_engagement_quality(transcript)
        score += engagement_assessment["score_adjustment"]
        suggestions.extend(engagement_assessment["suggestions"])
        evidence.update(engagement_assessment["evidence"])
        
        score = max(0, min(100, score))
        level = QualityLevel.from_score(score)
        
        details = f"Comprehensive medical accuracy assessment using full medical schema covering {len(evidence)} validation areas."
        
        return QualityMetric(
            dimension=self.dimension,
            score=score,
            level=level,
            details=details,
            suggestions=suggestions,
            evidence=evidence
        )
    
    def _assess_schema_coverage(self, transcript: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Assess coverage of comprehensive medical schema elements"""
        coverage_score = 0
        suggestions = []
        evidence = {}
        
        if not self.comprehensive_schema:
            return {"coverage_bonus": 0, "suggestions": [], "evidence": {"schema_available": False}}
        
        transcript_lower = transcript.lower()
        
        # Check coverage of major schema sections
        schema_sections = {
            "patient_information": ["demographics", "history", "current status", "health behaviors"],
            "clinical_data": ["test results", "medications", "physical examination", "laboratory"],
            "care_quality_assessment": ["guideline adherence", "comprehensiveness", "patient safety"],
            "treatment_and_follow_up": ["current treatment", "care plan", "medication adjustments"],
            "patient_engagement": ["communication", "health literacy", "patient education"],
            "social_determinants_of_health": ["housing", "employment", "food security", "transportation"],
            "preventive_care": ["screenings", "lifestyle modifications", "vaccination"],
            "medication_management": ["current medications", "reconciliation", "adherence"]
        }
        
        sections_covered = 0
        total_sections = len(schema_sections)
        
        for section_name, keywords in schema_sections.items():
            section_found = any(keyword in transcript_lower for keyword in keywords)
            if section_found:
                sections_covered += 1
                evidence[f"{section_name}_present"] = True
            else:
                evidence[f"{section_name}_present"] = False
                if section_name in ["patient_information", "clinical_data", "care_quality_assessment"]:
                    suggestions.append(f"Consider including {section_name.replace('_', ' ')} elements")
        
        coverage_ratio = sections_covered / total_sections
        evidence["schema_coverage_ratio"] = coverage_ratio
        evidence["sections_covered"] = sections_covered
        evidence["total_sections"] = total_sections
        
        if coverage_ratio >= 0.8:
            coverage_score = 10  # Excellent coverage
        elif coverage_ratio >= 0.6:
            coverage_score = 5   # Good coverage
        elif coverage_ratio >= 0.4:
            coverage_score = 0   # Fair coverage
        else:
            coverage_score = -5  # Poor coverage
            suggestions.append("Medical documentation lacks comprehensiveness across key areas")
        
        return {"coverage_bonus": coverage_score, "suggestions": suggestions, "evidence": evidence}
    
    def _validate_medical_terminology(self, transcript: str) -> Dict[str, Any]:
        """Enhanced medical terminology validation"""
        accuracy_score = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        # Comprehensive medical term validation
        for category, terms in self.medical_terms.items():
            found_terms = []
            for term in terms:
                if term.lower() in transcript_lower:
                    found_terms.append(term)
            
            if found_terms:
                evidence[f"{category}_terminology_found"] = found_terms
                evidence[f"{category}_count"] = len(found_terms)
                
                # Bonus for appropriate terminology usage
                if category in ["social_determinants", "preventive_care", "mental_health"]:
                    accuracy_score += len(found_terms) * 0.5  # Bonus for comprehensive care
        
        # Enhanced drug name validation with comprehensive list
        drug_validation = self._validate_comprehensive_medications(transcript)
        accuracy_score += drug_validation["score_adjustment"]
        suggestions.extend(drug_validation["suggestions"])
        evidence.update(drug_validation["evidence"])
        
        return {"accuracy_adjustment": accuracy_score, "suggestions": suggestions, "evidence": evidence}
    
    def _validate_comprehensive_medications(self, transcript: str) -> Dict[str, Any]:
        """Validate medication names, dosages, and interactions"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        
        medications_found = []
        dosage_patterns = []
        
        for drug in self.drug_names:
            pattern = rf'\b{re.escape(drug)}\b'
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            
            for match in matches:
                medications_found.append(match)
                
                # Check for dosage information nearby
                dosage_context = re.search(
                    rf'\b{re.escape(drug)}\b\s*(\d+\s*(?:mg|mcg|g|ml|units?|iu)\b)',
                    transcript, re.IGNORECASE
                )
                if dosage_context:
                    dosage_patterns.append(f"{drug}: {dosage_context.group(1)}")
                    score_adjustment += 1  # Bonus for complete medication information
        
        evidence["medications_identified"] = medications_found
        evidence["medications_with_dosages"] = dosage_patterns
        evidence["medication_completeness_ratio"] = len(dosage_patterns) / max(len(medications_found), 1)
        
        if medications_found and len(dosage_patterns) / len(medications_found) < 0.7:
            suggestions.append("Consider including dosage information for all medications mentioned")
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _assess_social_determinants(self, transcript: str) -> Dict[str, Any]:
        """Assess social determinants of health coverage"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        sdoh_categories = self.medical_terms.get("social_determinants", [])
        sdoh_found = []
        
        for determinant in sdoh_categories:
            if determinant in transcript_lower:
                sdoh_found.append(determinant)
                score_adjustment += 2  # Bonus for comprehensive care
        
        evidence["social_determinants_addressed"] = sdoh_found
        evidence["sdoh_coverage_ratio"] = len(sdoh_found) / len(sdoh_categories)
        
        if len(sdoh_found) == 0:
            suggestions.append("Consider addressing social determinants of health")
        elif len(sdoh_found) >= 3:
            score_adjustment += 5  # Additional bonus for comprehensive SDOH coverage
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _validate_comprehensive_vitals(self, transcript: str) -> Dict[str, Any]:
        """Enhanced vital signs validation with comprehensive ranges"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        
        vital_patterns = {
            'blood_pressure': (r'(\d{2,3})/(\d{2,3})', lambda s, d: 70 <= int(s) <= 250 and 40 <= int(d) <= 150),
            'heart_rate': (r'(\d{1,3})\s*(?:bpm|beats)', lambda hr: 30 <= int(hr) <= 200),
            'respiratory_rate': (r'(\d{1,2})\s*(?:breaths|respirations)', lambda rr: 8 <= int(rr) <= 40),
            'temperature': (r'(\d{2,3}(?:\.\d)?)\s*°?[fF]', lambda t: 95.0 <= float(t) <= 110.0),
            'oxygen_saturation': (r'(\d{2,3})%\s*(?:sat|o2|oxygen)', lambda o2: 70 <= int(o2) <= 100),
            'weight': (r'(\d{2,3}(?:\.\d)?)\s*(?:lbs?|pounds?|kg)', lambda w: 50 <= float(w) <= 500),
            'height': (r'(\d{1,2}(?:\'\d{1,2}\"?|\.\d)?)\s*(?:ft|feet|inches?)', lambda h: True)  # Height validation complex
        }
        
        vitals_found = []
        implausible_vitals = []
        
        for vital_type, (pattern, validator) in vital_patterns.items():
            matches = re.findall(pattern, transcript, re.IGNORECASE)
            
            for match in matches:
                vitals_found.append(vital_type)
                
                try:
                    if vital_type == 'blood_pressure':
                        if not validator(match[0], match[1]):
                            implausible_vitals.append(f"{vital_type}: {match[0]}/{match[1]}")
                            score_adjustment -= 3
                    else:
                        value = match if isinstance(match, str) else match[0]
                        if not validator(value):
                            implausible_vitals.append(f"{vital_type}: {value}")
                            score_adjustment -= 2
                except (ValueError, IndexError):
                    continue
        
        evidence["vital_signs_documented"] = list(set(vitals_found))
        evidence["vital_signs_count"] = len(set(vitals_found))
        evidence["implausible_vitals"] = implausible_vitals
        
        if implausible_vitals:
            suggestions.append(f"Review {len(implausible_vitals)} potentially implausible vital sign readings")
        
        if len(set(vitals_found)) >= 4:
            score_adjustment += 3  # Bonus for comprehensive vital signs documentation
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _assess_care_quality_indicators(self, transcript: str) -> Dict[str, Any]:
        """Assess care quality indicators"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        quality_indicators = {
            "patient_safety": ["safety", "adverse event", "medication error", "fall risk", "infection control"],
            "care_coordination": ["referral", "specialist", "follow-up", "coordination", "continuity"],
            "patient_centered_care": ["patient preference", "shared decision", "cultural", "language"],
            "evidence_based_care": ["guideline", "protocol", "evidence", "best practice", "standard of care"],
            "care_efficiency": ["timely", "appropriate", "cost-effective", "resource", "efficiency"]
        }
        
        indicators_present = {}
        for category, indicators in quality_indicators.items():
            found_indicators = [ind for ind in indicators if ind in transcript_lower]
            if found_indicators:
                indicators_present[category] = found_indicators
                score_adjustment += len(found_indicators)
        
        evidence["care_quality_indicators_present"] = indicators_present
        evidence["quality_categories_covered"] = len(indicators_present)
        
        if len(indicators_present) >= 3:
            score_adjustment += 5  # Bonus for comprehensive quality coverage
        elif len(indicators_present) == 0:
            suggestions.append("Consider documenting care quality indicators and safety measures")
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _assess_preventive_care(self, transcript: str) -> Dict[str, Any]:
        """Assess preventive care documentation"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        preventive_terms = self.medical_terms.get("preventive_care", [])
        preventive_found = [term for term in preventive_terms if term in transcript_lower]
        
        evidence["preventive_care_discussed"] = preventive_found
        evidence["preventive_care_ratio"] = len(preventive_found) / len(preventive_terms)
        
        if preventive_found:
            score_adjustment += len(preventive_found)
            if len(preventive_found) >= 3:
                score_adjustment += 3  # Bonus for comprehensive preventive care
        else:
            suggestions.append("Consider discussing relevant preventive care measures")
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _assess_mental_health_completeness(self, transcript: str) -> Dict[str, Any]:
        """Assess mental health considerations"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        mental_health_terms = self.medical_terms.get("mental_health", [])
        mental_health_found = [term for term in mental_health_terms if term in transcript_lower]
        
        evidence["mental_health_addressed"] = mental_health_found
        evidence["mental_health_screening"] = any(
            screen in transcript_lower for screen in ["phq", "gad", "depression screen", "anxiety screen"]
        )
        
        if mental_health_found:
            score_adjustment += len(mental_health_found)
            if evidence["mental_health_screening"]:
                score_adjustment += 3  # Bonus for mental health screening
        
        # Check for suicide risk assessment in mental health contexts
        if any(term in transcript_lower for term in ["depression", "suicidal", "self-harm"]):
            if any(risk_term in transcript_lower for risk_term in ["suicide risk", "safety plan", "si/hi"]):
                score_adjustment += 2
            else:
                suggestions.append("Consider documenting suicide risk assessment when mental health concerns present")
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _assess_comprehensive_medication_management(self, transcript: str) -> Dict[str, Any]:
        """Comprehensive medication management assessment"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        medication_management_elements = [
            "medication reconciliation", "drug interaction", "adherence", "side effect",
            "medication review", "allergy", "contraindication", "dosing", "frequency"
        ]
        
        elements_found = [elem for elem in medication_management_elements if elem in transcript_lower]
        evidence["medication_management_elements"] = elements_found
        evidence["medication_management_completeness"] = len(elements_found) / len(medication_management_elements)
        
        if elements_found:
            score_adjustment += len(elements_found)
            if len(elements_found) >= 5:
                score_adjustment += 5  # Bonus for comprehensive medication management
        else:
            suggestions.append("Consider comprehensive medication management documentation")
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}
    
    def _assess_patient_engagement_quality(self, transcript: str) -> Dict[str, Any]:
        """Assess patient engagement and communication quality"""
        score_adjustment = 0
        suggestions = []
        evidence = {}
        transcript_lower = transcript.lower()
        
        engagement_indicators = [
            "patient understanding", "questions answered", "patient education", "teach back",
            "health literacy", "patient preference", "shared decision", "patient activation"
        ]
        
        engagement_found = [ind for ind in engagement_indicators if ind in transcript_lower]
        evidence["patient_engagement_indicators"] = engagement_found
        evidence["engagement_quality_score"] = len(engagement_found)
        
        if engagement_found:
            score_adjustment += len(engagement_found) * 2  # Higher weight for patient engagement
        else:
            suggestions.append("Consider documenting patient engagement and education efforts")
        
        return {"score_adjustment": score_adjustment, "suggestions": suggestions, "evidence": evidence}


class SemanticCoherenceAssessor(QualityAssessor):
    """Assess semantic coherence and logical flow"""
    
    def __init__(self):
        self.use_advanced_nlp = NLP_AVAILABLE
        if self.use_advanced_nlp:
            try:
                self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            except:
                self.use_advanced_nlp = False
    
    @property
    def dimension(self) -> QualityDimension:
        return QualityDimension.SEMANTIC_COHERENCE
    
    def assess(self, transcript: str, metadata: Optional[Dict[str, Any]] = None) -> QualityMetric:
        """Assess semantic coherence and flow"""
        score = 85.0
        suggestions = []
        evidence = {}
        
        # Split into sentences for analysis
        sentences = re.split(r'[.!?]+', transcript)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if len(sentences) < 2:
            return QualityMetric(
                dimension=self.dimension,
                score=70.0,
                level=QualityLevel.FAIR,
                details="Insufficient content for coherence assessment",
                suggestions=["Transcript too short for meaningful coherence analysis"],
                evidence={"sentence_count": len(sentences)}
            )
        
        # Basic coherence checks
        coherence_issues = 0
        
        # Check for abrupt topic changes
        topic_transition_indicators = [
            "however", "but", "meanwhile", "additionally", "furthermore",
            "on the other hand", "in contrast", "similarly", "therefore"
        ]
        
        transitions_found = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for indicator in topic_transition_indicators:
                if indicator in sentence_lower:
                    transitions_found += 1
                    break
        
        transition_ratio = transitions_found / len(sentences)
        evidence["transition_ratio"] = transition_ratio
        evidence["transitions_found"] = transitions_found
        
        if transition_ratio < 0.1:
            score -= 10
            suggestions.append("Consider adding transitional phrases to improve flow")
            coherence_issues += 1
        
        # Check for repetitive content
        sentence_similarities = []
        if self.use_advanced_nlp and len(sentences) > 2:
            try:
                sentence_vectors = self.vectorizer.fit_transform(sentences)
                similarity_matrix = cosine_similarity(sentence_vectors)
                
                for i in range(len(sentences)):
                    for j in range(i+1, len(sentences)):
                        similarity = similarity_matrix[i][j]
                        sentence_similarities.append(similarity)
                        
                        if similarity > 0.8:  # Very similar sentences
                            score -= 3
                            suggestions.append(f"High similarity between sentences {i+1} and {j+1}")
                            coherence_issues += 1
                
                avg_similarity = np.mean(sentence_similarities) if sentence_similarities else 0
                evidence["average_sentence_similarity"] = avg_similarity
                evidence["high_similarity_pairs"] = sum(1 for s in sentence_similarities if s > 0.8)
                
            except Exception as e:
                logger.warning(f"Advanced NLP analysis failed: {e}")
        
        # Check for logical progression in medical transcripts
        if metadata and metadata.get("type") == "medical":
            medical_progression_keywords = {
                "beginning": ["presents", "chief complaint", "patient reports"],
                "middle": ["examination", "findings", "results", "noted"],
                "end": ["assessment", "plan", "recommendations", "follow-up"]
            }
            
            progression_score = 0
            transcript_lower = transcript.lower()
            
            for stage, keywords in medical_progression_keywords.items():
                stage_presence = any(keyword in transcript_lower for keyword in keywords)
                if stage_presence:
                    progression_score += 1
            
            if progression_score < 2:
                score -= 15
                suggestions.append("Medical transcript lacks clear progression (presentation → examination → plan)")
                coherence_issues += 1
            
            evidence["medical_progression_score"] = progression_score
        
        # Check for pronoun reference clarity
        pronouns = re.findall(r'\b(he|she|it|they|this|that|these|those)\b', transcript, re.IGNORECASE)
        pronoun_density = len(pronouns) / len(transcript.split())
        
        if pronoun_density > 0.1:  # More than 10% pronouns
            score -= 5
            suggestions.append("High pronoun usage may affect clarity - consider being more specific")
            evidence["pronoun_density"] = pronoun_density
            coherence_issues += 1
        
        # Check for incomplete thoughts
        incomplete_markers = re.findall(r'\.\.\.|\band\s*$|\bbut\s*$|\bor\s*$', transcript, re.IGNORECASE)
        if incomplete_markers:
            score -= len(incomplete_markers) * 2
            suggestions.append(f"Found {len(incomplete_markers)} incomplete thoughts or sentences")
            evidence["incomplete_thoughts"] = len(incomplete_markers)
            coherence_issues += 1
        
        evidence["total_coherence_issues"] = coherence_issues
        evidence["sentence_count"] = len(sentences)
        
        score = max(0, min(100, score))
        level = QualityLevel.from_score(score)
        
        details = f"Semantic coherence assessment analyzing logical flow, transitions, and content organization."
        
        return QualityMetric(
            dimension=self.dimension,
            score=score,
            level=level,
            details=details,
            suggestions=suggestions,
            evidence=evidence
        )


class QualityAssessmentEngine:
    """Main quality assessment engine coordinating all assessors"""
    
    def __init__(self, custom_assessors: Optional[List[QualityAssessor]] = None):
        """Initialize with default or custom assessors"""
        self.assessors = custom_assessors or [
            AccuracyAssessor(),
            CompletenessAssessor(),
            ConsistencyAssessor(),
            MedicalAccuracyAssessor(),
            SemanticCoherenceAssessor()
        ]
        
        # Weights for different dimensions in overall score calculation
        self.dimension_weights = {
            QualityDimension.ACCURACY: 0.25,
            QualityDimension.COMPLETENESS: 0.20,
            QualityDimension.CONSISTENCY: 0.15,
            QualityDimension.MEDICAL_ACCURACY: 0.20,
            QualityDimension.SEMANTIC_COHERENCE: 0.15,
            QualityDimension.CLARITY: 0.05
        }
        
        # Context-specific weight adjustments
        self.context_weights = {
            "medical": {
                QualityDimension.MEDICAL_ACCURACY: 0.35,
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.COMPLETENESS: 0.25,
                QualityDimension.CONSISTENCY: 0.10,
                QualityDimension.SEMANTIC_COHERENCE: 0.05
            },
            "legal": {
                QualityDimension.ACCURACY: 0.40,
                QualityDimension.COMPLETENESS: 0.30,
                QualityDimension.CONSISTENCY: 0.20,
                QualityDimension.SEMANTIC_COHERENCE: 0.10
            },
            "general": {
                QualityDimension.ACCURACY: 0.25,
                QualityDimension.COMPLETENESS: 0.20,
                QualityDimension.CONSISTENCY: 0.15,
                QualityDimension.SEMANTIC_COHERENCE: 0.20,
                QualityDimension.CLARITY: 0.20
            }
        }
    
    def assess_quality(
        self, 
        transcript: str, 
        metadata: Optional[Dict[str, Any]] = None,
        context: str = "general"
    ) -> QualityAssessmentResult:
        """Perform comprehensive quality assessment"""
        
        if not transcript or not transcript.strip():
            return QualityAssessmentResult(
                overall_score=0.0,
                overall_level=QualityLevel.POOR,
                dimension_scores={},
                summary="Empty or invalid transcript provided",
                recommendations=["Provide valid transcript content"],
                strengths=[],
                weaknesses=["No content to assess"],
                metadata={"error": "empty_transcript"}
            )
        
        logger.info(f"Starting quality assessment for transcript ({len(transcript)} characters)")
        
        # Run all assessors
        dimension_scores = {}
        for assessor in self.assessors:
            try:
                metric = assessor.assess(transcript, metadata)
                dimension_scores[assessor.dimension] = metric
                logger.debug(f"{assessor.dimension.value} assessment: {metric.score:.1f}")
            except Exception as e:
                logger.error(f"Error in {assessor.dimension.value} assessment: {e}")
                # Create fallback metric
                dimension_scores[assessor.dimension] = QualityMetric(
                    dimension=assessor.dimension,
                    score=50.0,
                    level=QualityLevel.FAIR,
                    details=f"Assessment failed: {str(e)}",
                    suggestions=["Manual review recommended"],
                    confidence=0.1
                )
        
        # Calculate overall score using context-appropriate weights
        weights = self.context_weights.get(context, self.dimension_weights)
        overall_score = 0.0
        total_weight = 0.0
        
        for dimension, weight in weights.items():
            if dimension in dimension_scores:
                overall_score += dimension_scores[dimension].score * weight
                total_weight += weight
        
        if total_weight > 0:
            overall_score /= total_weight
        else:
            overall_score = 0.0
        
        overall_level = QualityLevel.from_score(overall_score)
        
        # Generate summary and recommendations
        summary, recommendations, strengths, weaknesses = self._generate_summary(
            dimension_scores, overall_score, overall_level
        )
        
        # Compile metadata
        assessment_metadata = {
            "context": context,
            "transcript_length": len(transcript),
            "word_count": len(transcript.split()),
            "assessors_used": [assessor.__class__.__name__ for assessor in self.assessors],
            "weights_used": weights
        }
        
        if metadata:
            assessment_metadata.update(metadata)
        
        result = QualityAssessmentResult(
            overall_score=overall_score,
            overall_level=overall_level,
            dimension_scores=dimension_scores,
            summary=summary,
            recommendations=recommendations,
            strengths=strengths,
            weaknesses=weaknesses,
            metadata=assessment_metadata
        )
        
        logger.info(f"Quality assessment completed: {overall_score:.1f} ({overall_level.name})")
        
        return result
    
    def _generate_summary(
        self, 
        dimension_scores: Dict[QualityDimension, QualityMetric],
        overall_score: float,
        overall_level: QualityLevel
    ) -> Tuple[str, List[str], List[str], List[str]]:
        """Generate summary, recommendations, strengths, and weaknesses"""
        
        # Collect all suggestions
        all_suggestions = []
        for metric in dimension_scores.values():
            all_suggestions.extend(metric.suggestions)
        
        # Identify strengths (high-scoring dimensions)
        strengths = []
        weaknesses = []
        recommendations = []
        
        for dimension, metric in dimension_scores.items():
            if metric.score >= 85:
                strengths.append(f"Excellent {dimension.value.replace('_', ' ')}: {metric.details}")
            elif metric.score < 70:
                weaknesses.append(f"Poor {dimension.value.replace('_', ' ')}: {metric.details}")
                recommendations.extend(metric.suggestions)
            elif metric.suggestions:
                recommendations.extend(metric.suggestions[:2])  # Limit suggestions per dimension
        
        # Remove duplicates while preserving order
        recommendations = list(dict.fromkeys(recommendations))
        
        # Generate summary text
        if overall_level == QualityLevel.EXCELLENT:
            summary = f"Exceptional quality transcript with an overall score of {overall_score:.1f}. "
            summary += "Meets or exceeds quality standards across all dimensions."
        elif overall_level == QualityLevel.VERY_GOOD:
            summary = f"High quality transcript with an overall score of {overall_score:.1f}. "
            summary += "Minor improvements could enhance quality further."
        elif overall_level == QualityLevel.GOOD:
            summary = f"Good quality transcript with an overall score of {overall_score:.1f}. "
            summary += "Acceptable quality with some areas for improvement."
        elif overall_level == QualityLevel.FAIR:
            summary = f"Fair quality transcript with an overall score of {overall_score:.1f}. "
            summary += "Below average quality requiring attention to several areas."
        else:
            summary = f"Poor quality transcript with an overall score of {overall_score:.1f}. "
            summary += "Significant quality issues requiring major improvements."
        
        # Prioritize recommendations
        high_priority_terms = ["medical", "accuracy", "phi", "compliance", "safety"]
        high_priority_recs = [r for r in recommendations 
                             if any(term in r.lower() for term in high_priority_terms)]
        other_recs = [r for r in recommendations 
                     if not any(term in r.lower() for term in high_priority_terms)]
        
        recommendations = high_priority_recs + other_recs[:8]  # Limit total recommendations
        
        return summary, recommendations, strengths, weaknesses
    
    def batch_assess(
        self, 
        transcripts: List[Tuple[str, Optional[Dict[str, Any]]]], 
        context: str = "general"
    ) -> List[QualityAssessmentResult]:
        """Assess quality for multiple transcripts"""
        results = []
        
        for i, (transcript, metadata) in enumerate(transcripts):
            logger.info(f"Processing transcript {i+1}/{len(transcripts)}")
            result = self.assess_quality(transcript, metadata, context)
            results.append(result)
        
        return results
    
    def get_quality_trends(
        self, 
        results: List[QualityAssessmentResult]
    ) -> Dict[str, Any]:
        """Analyze quality trends across multiple assessments"""
        if not results:
            return {"error": "No results to analyze"}
        
        # Extract scores by dimension
        dimension_trends = {}
        overall_scores = [r.overall_score for r in results]
        
        for dimension in QualityDimension:
            scores = []
            for result in results:
                if dimension in result.dimension_scores:
                    scores.append(result.dimension_scores[dimension].score)
            
            if scores:
                dimension_trends[dimension.value] = {
                    "average": statistics.mean(scores),
                    "median": statistics.median(scores),
                    "std_dev": statistics.stdev(scores) if len(scores) > 1 else 0,
                    "min": min(scores),
                    "max": max(scores),
                    "trend": "improving" if len(scores) > 1 and scores[-1] > scores[0] else "stable"
                }
        
        # Quality level distribution
        level_distribution = {}
        for level in QualityLevel:
            count = sum(1 for r in results if r.overall_level == level)
            level_distribution[level.name] = count
        
        # Common issues
        all_recommendations = []
        for result in results:
            all_recommendations.extend(result.recommendations)
        
        recommendation_counts = {}
        for rec in all_recommendations:
            recommendation_counts[rec] = recommendation_counts.get(rec, 0) + 1
        
        common_issues = sorted(recommendation_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "total_assessments": len(results),
            "overall_average_score": statistics.mean(overall_scores),
            "overall_score_trend": dimension_trends,
            "quality_level_distribution": level_distribution,
            "common_issues": common_issues,
            "dimension_averages": {
                dim: data["average"] for dim, data in dimension_trends.items()
            }
        }