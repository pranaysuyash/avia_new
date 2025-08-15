#!/usr/bin/env python3
"""
Clinical Documentation and Reporting System - Task 141
Advanced clinical documentation with automatic note generation, ICD-10/CPT coding, and clinical workflow integration
"""

import os
import re
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import asyncio

# Import medical transcription system
try:
    from medical_transcription_system import (
        MedicalTranscriptionSystem,
        MedicalEntity,
        MedicalEntityType,
        HIPAACompliance
    )
except ImportError:
    MedicalTranscriptionSystem = None

logger = logging.getLogger(__name__)

class ClinicalNoteType(Enum):
    """Types of clinical notes"""
    SOAP_NOTE = "soap_note"
    PROGRESS_NOTE = "progress_note"
    ADMISSION_NOTE = "admission_note"
    DISCHARGE_SUMMARY = "discharge_summary"
    CONSULTATION_NOTE = "consultation_note"
    PROCEDURE_NOTE = "procedure_note"
    OPERATIVE_REPORT = "operative_report"
    PATHOLOGY_REPORT = "pathology_report"
    RADIOLOGY_REPORT = "radiology_report"
    EMERGENCY_NOTE = "emergency_note"

class ClinicalSpecialty(Enum):
    """Medical specialties for specialized documentation"""
    INTERNAL_MEDICINE = "internal_medicine"
    CARDIOLOGY = "cardiology"
    PULMONOLOGY = "pulmonology"
    NEUROLOGY = "neurology"
    ORTHOPEDICS = "orthopedics"
    SURGERY = "surgery"
    EMERGENCY_MEDICINE = "emergency_medicine"
    RADIOLOGY = "radiology"
    PATHOLOGY = "pathology"
    PSYCHIATRY = "psychiatry"
    PEDIATRICS = "pediatrics"
    OBSTETRICS_GYNECOLOGY = "obstetrics_gynecology"

class DocumentationQuality(Enum):
    """Quality levels for clinical documentation"""
    EXCELLENT = "excellent"
    GOOD = "good"
    ADEQUATE = "adequate"
    NEEDS_IMPROVEMENT = "needs_improvement"
    INCOMPLETE = "incomplete"

@dataclass
class ClinicalCode:
    """Clinical coding information"""
    code: str
    description: str
    code_type: str  # ICD-10, CPT, HCPCS, etc.
    confidence: float
    context: str
    modifier: Optional[str] = None
    billing_units: Optional[int] = None
    reimbursement_rate: Optional[float] = None

@dataclass
class ClinicalSection:
    """Clinical documentation section"""
    section_name: str
    content: str
    structured_data: Dict[str, Any]
    entities: List[MedicalEntity]
    codes: List[ClinicalCode]
    quality_score: float
    completeness_score: float
    recommendations: List[str]

@dataclass
class ClinicalNote:
    """Complete clinical note"""
    note_id: str
    note_type: ClinicalNoteType
    specialty: ClinicalSpecialty
    patient_id: str
    provider_id: str
    encounter_id: str
    created_at: datetime
    sections: Dict[str, ClinicalSection]
    primary_diagnosis: Optional[str] = None
    secondary_diagnoses: List[str] = field(default_factory=list)
    procedures: List[str] = field(default_factory=list)
    medications: List[str] = field(default_factory=list)
    overall_quality: DocumentationQuality = DocumentationQuality.ADEQUATE
    billing_codes: List[ClinicalCode] = field(default_factory=list)
    compliance_status: str = "pending"
    word_count: int = 0
    estimated_time_saved: float = 0.0

@dataclass
class QualityMetrics:
    """Clinical documentation quality metrics"""
    completeness_score: float
    accuracy_score: float
    specificity_score: float
    coding_accuracy: float
    documentation_time: float
    missing_elements: List[str]
    improvement_suggestions: List[str]

class ClinicalTemplateEngine:
    """Generate clinical documentation templates"""
    
    def __init__(self):
        self.templates = self._load_clinical_templates()
        self.specialty_requirements = self._load_specialty_requirements()
    
    def _load_clinical_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load clinical documentation templates"""
        return {
            ClinicalNoteType.SOAP_NOTE.value: {
                "sections": ["subjective", "objective", "assessment", "plan"],
                "required_elements": {
                    "subjective": ["chief_complaint", "history_present_illness"],
                    "objective": ["vital_signs", "physical_examination"],
                    "assessment": ["primary_diagnosis", "differential_diagnosis"],
                    "plan": ["treatment_plan", "follow_up"]
                },
                "format": "structured",
                "billing_level": "evaluation_management"
            },
            
            ClinicalNoteType.PROGRESS_NOTE.value: {
                "sections": ["subjective", "objective", "assessment", "plan"],
                "required_elements": {
                    "subjective": ["interval_history", "symptoms"],
                    "objective": ["vital_signs", "examination_findings"],
                    "assessment": ["clinical_status", "response_to_treatment"],
                    "plan": ["continued_treatment", "modifications"]
                },
                "format": "structured",
                "billing_level": "subsequent_care"
            },
            
            ClinicalNoteType.ADMISSION_NOTE.value: {
                "sections": [
                    "chief_complaint", "history_present_illness", "past_medical_history",
                    "medications", "allergies", "social_history", "family_history",
                    "review_of_systems", "physical_examination", "assessment_plan"
                ],
                "required_elements": {
                    "chief_complaint": ["primary_concern"],
                    "history_present_illness": ["onset", "duration", "severity", "quality"],
                    "physical_examination": ["general_appearance", "vital_signs", "system_examination"],
                    "assessment_plan": ["primary_diagnosis", "treatment_plan", "disposition"]
                },
                "format": "comprehensive",
                "billing_level": "initial_hospital_care"
            },
            
            ClinicalNoteType.DISCHARGE_SUMMARY.value: {
                "sections": [
                    "admission_diagnosis", "discharge_diagnosis", "hospital_course",
                    "procedures_performed", "discharge_medications", "discharge_instructions",
                    "follow_up_care", "prognosis"
                ],
                "required_elements": {
                    "hospital_course": ["significant_events", "treatment_response"],
                    "discharge_medications": ["medication_list", "dosing", "instructions"],
                    "discharge_instructions": ["activity_restrictions", "diet", "wound_care"],
                    "follow_up_care": ["appointments", "monitoring_requirements"]
                },
                "format": "comprehensive",
                "billing_level": "discharge_management"
            },
            
            ClinicalNoteType.PROCEDURE_NOTE.value: {
                "sections": [
                    "indication", "procedure_performed", "technique", "findings",
                    "complications", "post_procedure_care", "impression"
                ],
                "required_elements": {
                    "indication": ["clinical_reason", "medical_necessity"],
                    "procedure_performed": ["procedure_name", "approach", "equipment"],
                    "technique": ["step_by_step", "anatomical_landmarks"],
                    "findings": ["normal_findings", "abnormal_findings"],
                    "complications": ["intraoperative", "immediate_post_procedure"]
                },
                "format": "detailed",
                "billing_level": "procedure_based"
            }
        }
    
    def _load_specialty_requirements(self) -> Dict[str, Dict[str, Any]]:
        """Load specialty-specific documentation requirements"""
        return {
            ClinicalSpecialty.CARDIOLOGY.value: {
                "required_elements": [
                    "cardiovascular_examination", "ecg_interpretation", "risk_stratification"
                ],
                "common_procedures": ["echocardiogram", "stress_test", "cardiac_catheterization"],
                "key_diagnoses": ["coronary_artery_disease", "heart_failure", "arrhythmia"],
                "documentation_focus": ["chest_pain_evaluation", "cardiac_risk_factors"]
            },
            
            ClinicalSpecialty.PULMONOLOGY.value: {
                "required_elements": [
                    "pulmonary_examination", "oxygen_saturation", "respiratory_assessment"
                ],
                "common_procedures": ["pulmonary_function_test", "bronchoscopy", "chest_ct"],
                "key_diagnoses": ["copd", "asthma", "pneumonia", "pulmonary_embolism"],
                "documentation_focus": ["dyspnea_evaluation", "smoking_history"]
            },
            
            ClinicalSpecialty.NEUROLOGY.value: {
                "required_elements": [
                    "neurological_examination", "mental_status", "cranial_nerves", "motor_function"
                ],
                "common_procedures": ["eeg", "emg", "lumbar_puncture", "brain_mri"],
                "key_diagnoses": ["stroke", "seizure_disorder", "multiple_sclerosis", "dementia"],
                "documentation_focus": ["neurological_deficits", "cognitive_assessment"]
            },
            
            ClinicalSpecialty.EMERGENCY_MEDICINE.value: {
                "required_elements": [
                    "triage_assessment", "emergency_evaluation", "disposition_planning"
                ],
                "common_procedures": ["trauma_evaluation", "emergency_procedures", "stabilization"],
                "key_diagnoses": ["trauma", "acute_illness", "emergency_conditions"],
                "documentation_focus": ["acuity_level", "time_sensitive_care"]
            }
        }
    
    def generate_template(self, note_type: ClinicalNoteType, specialty: ClinicalSpecialty) -> Dict[str, Any]:
        """Generate clinical documentation template"""
        base_template = self.templates.get(note_type.value, {})
        specialty_requirements = self.specialty_requirements.get(specialty.value, {})
        
        # Merge base template with specialty requirements
        template = {
            "note_type": note_type.value,
            "specialty": specialty.value,
            "sections": base_template.get("sections", []),
            "required_elements": base_template.get("required_elements", {}),
            "specialty_elements": specialty_requirements.get("required_elements", []),
            "common_procedures": specialty_requirements.get("common_procedures", []),
            "key_diagnoses": specialty_requirements.get("key_diagnoses", []),
            "documentation_focus": specialty_requirements.get("documentation_focus", []),
            "format": base_template.get("format", "structured"),
            "billing_level": base_template.get("billing_level", "evaluation_management")
        }
        
        return template

class ClinicalCodingEngine:
    """Advanced clinical coding with ICD-10, CPT, and HCPCS"""
    
    def __init__(self):
        self.icd10_database = self._load_icd10_database()
        self.cpt_database = self._load_cpt_database()
        self.hcpcs_database = self._load_hcpcs_database()
        self.coding_rules = self._load_coding_rules()
    
    def _load_icd10_database(self) -> Dict[str, Dict[str, Any]]:
        """Load ICD-10 diagnostic codes database"""
        return {
            # Cardiovascular
            "I21.9": {
                "description": "Acute myocardial infarction, unspecified",
                "category": "cardiovascular",
                "keywords": ["heart attack", "myocardial infarction", "mi", "ami"],
                "severity": "high",
                "reimbursement_weight": 1.5
            },
            "I10": {
                "description": "Essential hypertension",
                "category": "cardiovascular",
                "keywords": ["hypertension", "high blood pressure", "htn"],
                "severity": "medium",
                "reimbursement_weight": 0.8
            },
            "I50.9": {
                "description": "Heart failure, unspecified",
                "category": "cardiovascular",
                "keywords": ["heart failure", "chf", "congestive heart failure"],
                "severity": "high",
                "reimbursement_weight": 1.3
            },
            
            # Respiratory
            "J44.1": {
                "description": "Chronic obstructive pulmonary disease with acute exacerbation",
                "category": "respiratory",
                "keywords": ["copd", "chronic obstructive pulmonary disease", "exacerbation"],
                "severity": "high",
                "reimbursement_weight": 1.2
            },
            "J45.9": {
                "description": "Asthma, unspecified",
                "category": "respiratory",
                "keywords": ["asthma", "bronchial asthma", "reactive airway"],
                "severity": "medium",
                "reimbursement_weight": 0.9
            },
            "J18.9": {
                "description": "Pneumonia, unspecified organism",
                "category": "respiratory",
                "keywords": ["pneumonia", "lung infection", "pulmonary infection"],
                "severity": "high",
                "reimbursement_weight": 1.1
            },
            
            # Endocrine
            "E11.9": {
                "description": "Type 2 diabetes mellitus without complications",
                "category": "endocrine",
                "keywords": ["diabetes", "diabetes mellitus", "dm", "t2dm"],
                "severity": "medium",
                "reimbursement_weight": 0.9
            },
            "E11.65": {
                "description": "Type 2 diabetes mellitus with hyperglycemia",
                "category": "endocrine",
                "keywords": ["diabetes", "hyperglycemia", "high blood sugar"],
                "severity": "medium",
                "reimbursement_weight": 1.0
            },
            
            # Neurological
            "G93.1": {
                "description": "Anoxic brain damage, not elsewhere classified",
                "category": "neurological",
                "keywords": ["brain damage", "anoxic", "hypoxic brain injury"],
                "severity": "high",
                "reimbursement_weight": 1.8
            },
            "F32.9": {
                "description": "Major depressive disorder, single episode, unspecified",
                "category": "psychiatric",
                "keywords": ["depression", "major depression", "depressive disorder"],
                "severity": "medium",
                "reimbursement_weight": 0.7
            }
        }
    
    def _load_cpt_database(self) -> Dict[str, Dict[str, Any]]:
        """Load CPT procedure codes database"""
        return {
            # Evaluation and Management
            "99213": {
                "description": "Office visit, established patient, low complexity",
                "category": "evaluation_management",
                "keywords": ["office visit", "established patient", "follow up"],
                "work_rvu": 0.97,
                "time_minutes": 20,
                "reimbursement_rate": 109.00
            },
            "99214": {
                "description": "Office visit, established patient, moderate complexity",
                "category": "evaluation_management",
                "keywords": ["office visit", "established patient", "moderate complexity"],
                "work_rvu": 1.50,
                "time_minutes": 30,
                "reimbursement_rate": 167.00
            },
            "99215": {
                "description": "Office visit, established patient, high complexity",
                "category": "evaluation_management",
                "keywords": ["office visit", "established patient", "high complexity"],
                "work_rvu": 2.11,
                "time_minutes": 40,
                "reimbursement_rate": 211.00
            },
            
            # Procedures
            "93000": {
                "description": "Electrocardiogram, routine ECG with interpretation",
                "category": "diagnostic",
                "keywords": ["ecg", "ekg", "electrocardiogram"],
                "work_rvu": 0.17,
                "time_minutes": 5,
                "reimbursement_rate": 25.00
            },
            "71020": {
                "description": "Chest X-ray, frontal view, single view",
                "category": "radiology",
                "keywords": ["chest x-ray", "chest radiograph", "cxr"],
                "work_rvu": 0.22,
                "time_minutes": 10,
                "reimbursement_rate": 42.00
            },
            "85025": {
                "description": "Blood count; complete (CBC), automated",
                "category": "laboratory",
                "keywords": ["cbc", "complete blood count", "blood count"],
                "work_rvu": 0.00,
                "time_minutes": 0,
                "reimbursement_rate": 10.00
            },
            "82947": {
                "description": "Glucose; quantitative, blood",
                "category": "laboratory",
                "keywords": ["glucose", "blood sugar", "blood glucose"],
                "work_rvu": 0.00,
                "time_minutes": 0,
                "reimbursement_rate": 8.00
            }
        }
    
    def _load_hcpcs_database(self) -> Dict[str, Dict[str, Any]]:
        """Load HCPCS codes database"""
        return {
            "G0439": {
                "description": "Annual wellness visit; includes a personalized prevention plan of service",
                "category": "preventive",
                "keywords": ["annual wellness visit", "preventive care", "wellness"],
                "reimbursement_rate": 174.00
            },
            "G0442": {
                "description": "Annual alcohol misuse screening",
                "category": "screening",
                "keywords": ["alcohol screening", "substance abuse screening"],
                "reimbursement_rate": 18.00
            }
        }
    
    def _load_coding_rules(self) -> Dict[str, Any]:
        """Load clinical coding rules and guidelines"""
        return {
            "primary_diagnosis_required": True,
            "max_secondary_diagnoses": 24,
            "procedure_modifier_rules": {
                "bilateral": "50",
                "multiple_procedures": "51",
                "reduced_services": "52"
            },
            "documentation_requirements": {
                "history_levels": ["problem_focused", "expanded_problem_focused", "detailed", "comprehensive"],
                "examination_levels": ["problem_focused", "expanded_problem_focused", "detailed", "comprehensive"],
                "decision_making_levels": ["straightforward", "low_complexity", "moderate_complexity", "high_complexity"]
            }
        }
    
    def suggest_icd10_codes(self, clinical_text: str, entities: List[MedicalEntity]) -> List[ClinicalCode]:
        """Suggest ICD-10 diagnostic codes based on clinical text and entities"""
        suggested_codes = []
        text_lower = clinical_text.lower()
        
        # Score each ICD-10 code based on keyword matches and entity presence
        for code, code_info in self.icd10_database.items():
            score = 0.0
            matched_keywords = []
            
            # Check keyword matches
            for keyword in code_info["keywords"]:
                if keyword in text_lower:
                    score += 1.0
                    matched_keywords.append(keyword)
            
            # Check entity matches
            for entity in entities:
                if entity.entity_type in [MedicalEntityType.DIAGNOSIS, MedicalEntityType.CONDITION]:
                    entity_text = entity.text.lower()
                    for keyword in code_info["keywords"]:
                        if keyword in entity_text or entity_text in keyword:
                            score += 0.5
                            break
            
            # Calculate confidence based on score and context
            if score > 0:
                confidence = min(score / len(code_info["keywords"]), 1.0)
                
                if confidence >= 0.3:  # Minimum threshold
                    clinical_code = ClinicalCode(
                        code=code,
                        description=code_info["description"],
                        code_type="ICD-10",
                        confidence=confidence,
                        context=f"Matched keywords: {', '.join(matched_keywords)}",
                        reimbursement_rate=code_info.get("reimbursement_weight", 1.0) * 100
                    )
                    suggested_codes.append(clinical_code)
        
        # Sort by confidence and return top suggestions
        suggested_codes.sort(key=lambda x: x.confidence, reverse=True)
        return suggested_codes[:10]
    
    def suggest_cpt_codes(self, clinical_text: str, entities: List[MedicalEntity], note_type: ClinicalNoteType) -> List[ClinicalCode]:
        """Suggest CPT procedure codes based on clinical text and note type"""
        suggested_codes = []
        text_lower = clinical_text.lower()
        
        # Determine appropriate E&M code based on note type and complexity
        if note_type in [ClinicalNoteType.SOAP_NOTE, ClinicalNoteType.PROGRESS_NOTE]:
            # Analyze complexity for E&M coding
            complexity_score = self._assess_documentation_complexity(clinical_text, entities)
            
            if complexity_score >= 0.8:
                em_code = "99215"  # High complexity
            elif complexity_score >= 0.6:
                em_code = "99214"  # Moderate complexity
            else:
                em_code = "99213"  # Low complexity
            
            if em_code in self.cpt_database:
                code_info = self.cpt_database[em_code]
                clinical_code = ClinicalCode(
                    code=em_code,
                    description=code_info["description"],
                    code_type="CPT",
                    confidence=0.9,
                    context=f"E&M level based on complexity score: {complexity_score:.2f}",
                    reimbursement_rate=code_info["reimbursement_rate"]
                )
                suggested_codes.append(clinical_code)
        
        # Check for procedure-specific codes
        for code, code_info in self.cpt_database.items():
            if code_info["category"] in ["diagnostic", "radiology", "laboratory"]:
                score = 0.0
                matched_keywords = []
                
                for keyword in code_info["keywords"]:
                    if keyword in text_lower:
                        score += 1.0
                        matched_keywords.append(keyword)
                
                if score > 0:
                    confidence = min(score / len(code_info["keywords"]), 1.0)
                    
                    if confidence >= 0.5:
                        clinical_code = ClinicalCode(
                            code=code,
                            description=code_info["description"],
                            code_type="CPT",
                            confidence=confidence,
                            context=f"Matched keywords: {', '.join(matched_keywords)}",
                            reimbursement_rate=code_info["reimbursement_rate"]
                        )
                        suggested_codes.append(clinical_code)
        
        suggested_codes.sort(key=lambda x: x.confidence, reverse=True)
        return suggested_codes[:5]
    
    def _assess_documentation_complexity(self, clinical_text: str, entities: List[MedicalEntity]) -> float:
        """Assess documentation complexity for E&M coding"""
        complexity_score = 0.0
        
        # Word count factor
        word_count = len(clinical_text.split())
        if word_count > 500:
            complexity_score += 0.3
        elif word_count > 200:
            complexity_score += 0.2
        elif word_count > 100:
            complexity_score += 0.1
        
        # Entity complexity
        entity_types = set(entity.entity_type for entity in entities)
        complexity_score += len(entity_types) * 0.1
        
        # Diagnosis complexity
        diagnosis_entities = [e for e in entities if e.entity_type == MedicalEntityType.DIAGNOSIS]
        if len(diagnosis_entities) > 3:
            complexity_score += 0.2
        elif len(diagnosis_entities) > 1:
            complexity_score += 0.1
        
        # Medication complexity
        medication_entities = [e for e in entities if e.entity_type == MedicalEntityType.MEDICATION]
        if len(medication_entities) > 5:
            complexity_score += 0.2
        elif len(medication_entities) > 2:
            complexity_score += 0.1
        
        return min(complexity_score, 1.0)

class ClinicalQualityAssessment:
    """Assess clinical documentation quality and completeness"""
    
    def __init__(self):
        self.quality_criteria = self._load_quality_criteria()
        self.completeness_requirements = self._load_completeness_requirements()
    
    def _load_quality_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Load clinical documentation quality criteria"""
        return {
            "completeness": {
                "weight": 0.3,
                "criteria": [
                    "all_required_sections_present",
                    "adequate_detail_in_sections",
                    "no_missing_critical_information"
                ]
            },
            "accuracy": {
                "weight": 0.25,
                "criteria": [
                    "medical_terminology_correct",
                    "consistent_information",
                    "appropriate_clinical_reasoning"
                ]
            },
            "specificity": {
                "weight": 0.2,
                "criteria": [
                    "specific_diagnoses_documented",
                    "detailed_examination_findings",
                    "precise_treatment_plans"
                ]
            },
            "timeliness": {
                "weight": 0.15,
                "criteria": [
                    "documented_within_timeframe",
                    "current_information",
                    "up_to_date_assessments"
                ]
            },
            "legibility": {
                "weight": 0.1,
                "criteria": [
                    "clear_language",
                    "proper_formatting",
                    "readable_structure"
                ]
            }
        }
    
    def _load_completeness_requirements(self) -> Dict[str, List[str]]:
        """Load completeness requirements by note type"""
        return {
            ClinicalNoteType.SOAP_NOTE.value: [
                "chief_complaint", "history_present_illness", "physical_examination",
                "assessment", "plan", "vital_signs"
            ],
            ClinicalNoteType.ADMISSION_NOTE.value: [
                "chief_complaint", "history_present_illness", "past_medical_history",
                "medications", "allergies", "social_history", "physical_examination",
                "assessment", "plan"
            ],
            ClinicalNoteType.DISCHARGE_SUMMARY.value: [
                "admission_diagnosis", "discharge_diagnosis", "hospital_course",
                "discharge_medications", "discharge_instructions", "follow_up"
            ]
        }
    
    def assess_quality(self, clinical_note: ClinicalNote) -> QualityMetrics:
        """Assess overall quality of clinical documentation"""
        completeness_score = self._assess_completeness(clinical_note)
        accuracy_score = self._assess_accuracy(clinical_note)
        specificity_score = self._assess_specificity(clinical_note)
        coding_accuracy = self._assess_coding_accuracy(clinical_note)
        
        # Calculate weighted overall score
        overall_score = (
            completeness_score * 0.3 +
            accuracy_score * 0.25 +
            specificity_score * 0.2 +
            coding_accuracy * 0.25
        )
        
        # Identify missing elements and improvement suggestions
        missing_elements = self._identify_missing_elements(clinical_note)
        improvement_suggestions = self._generate_improvement_suggestions(clinical_note, overall_score)
        
        return QualityMetrics(
            completeness_score=completeness_score,
            accuracy_score=accuracy_score,
            specificity_score=specificity_score,
            coding_accuracy=coding_accuracy,
            documentation_time=self._estimate_documentation_time(clinical_note),
            missing_elements=missing_elements,
            improvement_suggestions=improvement_suggestions
        )
    
    def _assess_completeness(self, clinical_note: ClinicalNote) -> float:
        """Assess documentation completeness"""
        required_elements = self.completeness_requirements.get(clinical_note.note_type.value, [])
        
        if not required_elements:
            return 1.0
        
        present_elements = 0
        for element in required_elements:
            # Check if element is present in any section
            for section in clinical_note.sections.values():
                if element.replace("_", " ") in section.content.lower():
                    present_elements += 1
                    break
        
        return present_elements / len(required_elements)
    
    def _assess_accuracy(self, clinical_note: ClinicalNote) -> float:
        """Assess medical accuracy and consistency"""
        accuracy_score = 0.8  # Base score
        
        # Check for medical terminology accuracy
        total_entities = sum(len(section.entities) for section in clinical_note.sections.values())
        if total_entities > 0:
            high_confidence_entities = sum(
                1 for section in clinical_note.sections.values()
                for entity in section.entities
                if entity.confidence > 0.8
            )
            accuracy_score += (high_confidence_entities / total_entities) * 0.2
        
        return min(accuracy_score, 1.0)
    
    def _assess_specificity(self, clinical_note: ClinicalNote) -> float:
        """Assess specificity and detail level"""
        specificity_score = 0.0
        
        # Check for specific diagnoses
        if clinical_note.primary_diagnosis:
            specificity_score += 0.3
        
        # Check for detailed examination findings
        total_word_count = sum(len(section.content.split()) for section in clinical_note.sections.values())
        if total_word_count > 300:
            specificity_score += 0.3
        elif total_word_count > 150:
            specificity_score += 0.2
        elif total_word_count > 75:
            specificity_score += 0.1
        
        # Check for treatment plans
        plan_sections = [s for s in clinical_note.sections.values() if "plan" in s.section_name.lower()]
        if plan_sections and any(len(s.content.split()) > 50 for s in plan_sections):
            specificity_score += 0.4
        
        return min(specificity_score, 1.0)
    
    def _assess_coding_accuracy(self, clinical_note: ClinicalNote) -> float:
        """Assess accuracy of clinical coding"""
        if not clinical_note.billing_codes:
            return 0.5  # Neutral score if no codes
        
        # Check code confidence levels
        total_confidence = sum(code.confidence for code in clinical_note.billing_codes)
        average_confidence = total_confidence / len(clinical_note.billing_codes)
        
        return average_confidence
    
    def _identify_missing_elements(self, clinical_note: ClinicalNote) -> List[str]:
        """Identify missing required elements"""
        required_elements = self.completeness_requirements.get(clinical_note.note_type.value, [])
        missing_elements = []
        
        for element in required_elements:
            found = False
            for section in clinical_note.sections.values():
                if element.replace("_", " ") in section.content.lower():
                    found = True
                    break
            
            if not found:
                missing_elements.append(element.replace("_", " ").title())
        
        return missing_elements
    
    def _generate_improvement_suggestions(self, clinical_note: ClinicalNote, overall_score: float) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        if overall_score < 0.7:
            suggestions.append("Consider adding more detailed clinical information")
        
        if not clinical_note.primary_diagnosis:
            suggestions.append("Document primary diagnosis clearly")
        
        if len(clinical_note.billing_codes) == 0:
            suggestions.append("Add appropriate billing codes for reimbursement")
        
        if clinical_note.word_count < 100:
            suggestions.append("Expand documentation with more clinical details")
        
        missing_elements = self._identify_missing_elements(clinical_note)
        if missing_elements:
            suggestions.append(f"Add missing elements: {', '.join(missing_elements[:3])}")
        
        return suggestions
    
    def _estimate_documentation_time(self, clinical_note: ClinicalNote) -> float:
        """Estimate time saved through automated documentation"""
        # Base time estimates (in minutes)
        base_times = {
            ClinicalNoteType.SOAP_NOTE: 15,
            ClinicalNoteType.PROGRESS_NOTE: 10,
            ClinicalNoteType.ADMISSION_NOTE: 30,
            ClinicalNoteType.DISCHARGE_SUMMARY: 25,
            ClinicalNoteType.PROCEDURE_NOTE: 20
        }
        
        base_time = base_times.get(clinical_note.note_type, 15)
        
        # Adjust based on complexity
        complexity_factor = min(clinical_note.word_count / 200, 2.0)
        estimated_time = base_time * complexity_factor
        
        # Assume 60-70% time savings with automated documentation
        time_saved = estimated_time * 0.65
        
        return time_saved

class ClinicalDocumentationSystem:
    """Main clinical documentation and reporting system"""
    
    def __init__(self):
        self.template_engine = ClinicalTemplateEngine()
        self.coding_engine = ClinicalCodingEngine()
        self.quality_assessment = ClinicalQualityAssessment()
        
        # Initialize medical transcription system if available
        if MedicalTranscriptionSystem:
            self.medical_system = MedicalTranscriptionSystem(HIPAACompliance.STANDARD)
        else:
            self.medical_system = None
    
    async def generate_clinical_note(
        self,
        transcript_text: str,
        note_type: ClinicalNoteType,
        specialty: ClinicalSpecialty,
        patient_id: str,
        provider_id: str,
        encounter_id: str
    ) -> ClinicalNote:
        """Generate complete clinical note from transcript"""
        
        # Extract medical entities if medical system is available
        entities = []
        if self.medical_system:
            try:
                entities = self.medical_system.entity_extractor.extract_entities(transcript_text)
            except Exception as e:
                logger.warning(f"Entity extraction failed: {e}")
        
        # Get template for note type and specialty
        template = self.template_engine.generate_template(note_type, specialty)
        
        # Extract sections from transcript
        sections = await self._extract_clinical_sections(transcript_text, template, entities)
        
        # Generate clinical codes
        icd10_codes = self.coding_engine.suggest_icd10_codes(transcript_text, entities)
        cpt_codes = self.coding_engine.suggest_cpt_codes(transcript_text, entities, note_type)
        
        # Create clinical note
        clinical_note = ClinicalNote(
            note_id=str(uuid.uuid4()),
            note_type=note_type,
            specialty=specialty,
            patient_id=patient_id,
            provider_id=provider_id,
            encounter_id=encounter_id,
            created_at=datetime.now(),
            sections=sections,
            billing_codes=icd10_codes + cpt_codes,
            word_count=len(transcript_text.split())
        )
        
        # Extract primary diagnosis and other key information
        clinical_note.primary_diagnosis = self._extract_primary_diagnosis(entities, icd10_codes)
        clinical_note.secondary_diagnoses = self._extract_secondary_diagnoses(entities, icd10_codes)
        clinical_note.procedures = self._extract_procedures(entities, cpt_codes)
        clinical_note.medications = self._extract_medications(entities)
        
        # Assess quality
        quality_metrics = self.quality_assessment.assess_quality(clinical_note)
        clinical_note.overall_quality = self._determine_quality_level(quality_metrics.completeness_score)
        clinical_note.estimated_time_saved = quality_metrics.documentation_time
        
        return clinical_note
    
    async def _extract_clinical_sections(
        self,
        transcript_text: str,
        template: Dict[str, Any],
        entities: List[MedicalEntity]
    ) -> Dict[str, ClinicalSection]:
        """Extract clinical sections from transcript"""
        sections = {}
        
        for section_name in template["sections"]:
            section_content = self._extract_section_content(transcript_text, section_name)
            
            # Get entities relevant to this section
            section_entities = self._filter_entities_for_section(entities, section_name)
            
            # Generate codes for this section
            section_codes = []
            if section_name in ["assessment", "diagnosis", "impression"]:
                section_codes = self.coding_engine.suggest_icd10_codes(section_content, section_entities)
            elif section_name in ["plan", "procedure", "treatment"]:
                section_codes = self.coding_engine.suggest_cpt_codes(
                    section_content, section_entities, ClinicalNoteType.PROCEDURE_NOTE
                )
            
            # Create structured data for section
            structured_data = self._create_structured_data(section_content, section_entities, section_name)
            
            # Assess section quality
            quality_score = self._assess_section_quality(section_content, section_entities)
            completeness_score = self._assess_section_completeness(section_content, section_name, template)
            
            # Generate recommendations
            recommendations = self._generate_section_recommendations(
                section_content, section_entities, section_name, quality_score
            )
            
            sections[section_name] = ClinicalSection(
                section_name=section_name,
                content=section_content,
                structured_data=structured_data,
                entities=section_entities,
                codes=section_codes,
                quality_score=quality_score,
                completeness_score=completeness_score,
                recommendations=recommendations
            )
        
        return sections
    
    def _extract_section_content(self, transcript_text: str, section_name: str) -> str:
        """Extract content for specific clinical section"""
        # Define section keywords and patterns
        section_patterns = {
            "chief_complaint": [r"chief complaint[:\s]*(.*?)(?=history|physical|$)", r"cc[:\s]*(.*?)(?=history|physical|$)"],
            "subjective": [r"subjective[:\s]*(.*?)(?=objective|physical|assessment|$)", r"patient reports[:\s]*(.*?)(?=objective|physical|$)"],
            "objective": [r"objective[:\s]*(.*?)(?=assessment|plan|$)", r"physical exam[:\s]*(.*?)(?=assessment|plan|$)"],
            "assessment": [r"assessment[:\s]*(.*?)(?=plan|$)", r"impression[:\s]*(.*?)(?=plan|$)", r"diagnosis[:\s]*(.*?)(?=plan|$)"],
            "plan": [r"plan[:\s]*(.*?)$", r"treatment[:\s]*(.*?)$", r"recommendations[:\s]*(.*?)$"],
            "history_present_illness": [r"history of present illness[:\s]*(.*?)(?=past medical|physical|review|$)", r"hpi[:\s]*(.*?)(?=past medical|physical|$)"],
            "physical_examination": [r"physical exam[:\s]*(.*?)(?=assessment|impression|plan|$)", r"examination[:\s]*(.*?)(?=assessment|plan|$)"],
            "medications": [r"medications[:\s]*(.*?)(?=allergies|social|physical|$)", r"current medications[:\s]*(.*?)(?=allergies|social|$)"],
            "allergies": [r"allergies[:\s]*(.*?)(?=social|family|physical|$)", r"drug allergies[:\s]*(.*?)(?=social|family|$)"]
        }
        
        patterns = section_patterns.get(section_name, [])
        
        for pattern in patterns:
            match = re.search(pattern, transcript_text, re.IGNORECASE | re.DOTALL)
            if match:
                content = match.group(1).strip()
                if content and len(content) > 10:  # Minimum content length
                    return content
        
        # If no specific pattern found, look for section name in text
        lines = transcript_text.split('\n')
        section_content = []
        capturing = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts a new section
            if any(keyword in line.lower() for keyword in [section_name.replace('_', ' '), section_name.replace('_', '')]):
                capturing = True
                # Include the content after the section header
                if ':' in line:
                    section_content.append(line.split(':', 1)[1].strip())
                continue
            
            # Check if we've hit another section
            if capturing and any(other_section in line.lower() for other_section in 
                               ['subjective', 'objective', 'assessment', 'plan', 'history', 'physical', 'medications']):
                if section_name.replace('_', ' ') not in line.lower():
                    break
            
            if capturing:
                section_content.append(line)
        
        return '\n'.join(section_content) if section_content else ""
    
    def _filter_entities_for_section(self, entities: List[MedicalEntity], section_name: str) -> List[MedicalEntity]:
        """Filter entities relevant to specific section"""
        section_entity_mapping = {
            "chief_complaint": [MedicalEntityType.SYMPTOM, MedicalEntityType.CONDITION],
            "subjective": [MedicalEntityType.SYMPTOM, MedicalEntityType.CONDITION],
            "objective": [MedicalEntityType.MEASUREMENT, MedicalEntityType.ANATOMY],
            "assessment": [MedicalEntityType.DIAGNOSIS, MedicalEntityType.CONDITION],
            "plan": [MedicalEntityType.MEDICATION, MedicalEntityType.PROCEDURE],
            "medications": [MedicalEntityType.MEDICATION, MedicalEntityType.DOSAGE],
            "physical_examination": [MedicalEntityType.ANATOMY, MedicalEntityType.MEASUREMENT]
        }
        
        relevant_types = section_entity_mapping.get(section_name, list(MedicalEntityType))
        return [entity for entity in entities if entity.entity_type in relevant_types]
    
    def _create_structured_data(self, content: str, entities: List[MedicalEntity], section_name: str) -> Dict[str, Any]:
        """Create structured data from section content"""
        structured_data = {
            "word_count": len(content.split()),
            "entity_count": len(entities),
            "entities_by_type": {}
        }
        
        # Group entities by type
        for entity in entities:
            entity_type = entity.entity_type.value
            if entity_type not in structured_data["entities_by_type"]:
                structured_data["entities_by_type"][entity_type] = []
            structured_data["entities_by_type"][entity_type].append({
                "text": entity.text,
                "confidence": entity.confidence,
                "normalized_form": entity.normalized_form
            })
        
        # Section-specific structured data
        if section_name == "objective":
            structured_data["vital_signs"] = self._extract_vital_signs(content)
        elif section_name == "medications":
            structured_data["medication_list"] = self._extract_medication_list(content, entities)
        elif section_name == "assessment":
            structured_data["diagnoses"] = self._extract_diagnoses(content, entities)
        
        return structured_data
    
    def _extract_vital_signs(self, content: str) -> Dict[str, str]:
        """Extract vital signs from objective section"""
        vital_signs = {}
        
        # Blood pressure
        bp_match = re.search(r'bp[:\s]*(\d+/\d+)', content, re.IGNORECASE)
        if bp_match:
            vital_signs["blood_pressure"] = bp_match.group(1)
        
        # Heart rate
        hr_match = re.search(r'hr[:\s]*(\d+)', content, re.IGNORECASE)
        if hr_match:
            vital_signs["heart_rate"] = hr_match.group(1)
        
        # Temperature
        temp_match = re.search(r'temp[:\s]*(\d+\.?\d*)', content, re.IGNORECASE)
        if temp_match:
            vital_signs["temperature"] = temp_match.group(1)
        
        # Respiratory rate
        rr_match = re.search(r'rr[:\s]*(\d+)', content, re.IGNORECASE)
        if rr_match:
            vital_signs["respiratory_rate"] = rr_match.group(1)
        
        return vital_signs
    
    def _extract_medication_list(self, content: str, entities: List[MedicalEntity]) -> List[Dict[str, str]]:
        """Extract structured medication list"""
        medications = []
        
        for entity in entities:
            if entity.entity_type == MedicalEntityType.MEDICATION:
                # Look for dosage information near the medication
                context_start = max(0, entity.start_pos - 50)
                context_end = min(len(content), entity.end_pos + 50)
                context = content[context_start:context_end]
                
                # Extract dosage
                dosage_match = re.search(r'(\d+\s*mg|\d+\s*mcg|\d+\s*units)', context, re.IGNORECASE)
                dosage = dosage_match.group(1) if dosage_match else ""
                
                # Extract frequency
                frequency_match = re.search(r'(daily|bid|tid|qid|once|twice|three times)', context, re.IGNORECASE)
                frequency = frequency_match.group(1) if frequency_match else ""
                
                medications.append({
                    "name": entity.text,
                    "dosage": dosage,
                    "frequency": frequency,
                    "confidence": entity.confidence
                })
        
        return medications
    
    def _extract_diagnoses(self, content: str, entities: List[MedicalEntity]) -> List[Dict[str, str]]:
        """Extract structured diagnosis list"""
        diagnoses = []
        
        for entity in entities:
            if entity.entity_type in [MedicalEntityType.DIAGNOSIS, MedicalEntityType.CONDITION]:
                diagnoses.append({
                    "diagnosis": entity.text,
                    "normalized_form": entity.normalized_form,
                    "confidence": entity.confidence
                })
        
        return diagnoses
    
    def _assess_section_quality(self, content: str, entities: List[MedicalEntity]) -> float:
        """Assess quality of individual section"""
        if not content.strip():
            return 0.0
        
        quality_score = 0.5  # Base score
        
        # Content length factor
        word_count = len(content.split())
        if word_count > 50:
            quality_score += 0.2
        elif word_count > 20:
            quality_score += 0.1
        
        # Entity presence factor
        if entities:
            quality_score += min(len(entities) * 0.05, 0.3)
        
        return min(quality_score, 1.0)
    
    def _assess_section_completeness(self, content: str, section_name: str, template: Dict[str, Any]) -> float:
        """Assess completeness of section based on template requirements"""
        required_elements = template.get("required_elements", {}).get(section_name, [])
        
        if not required_elements:
            return 1.0 if content.strip() else 0.0
        
        present_elements = 0
        for element in required_elements:
            if element.replace("_", " ") in content.lower():
                present_elements += 1
        
        return present_elements / len(required_elements)
    
    def _generate_section_recommendations(
        self, content: str, entities: List[MedicalEntity], section_name: str, quality_score: float
    ) -> List[str]:
        """Generate recommendations for section improvement"""
        recommendations = []
        
        if not content.strip():
            recommendations.append(f"Add content to {section_name.replace('_', ' ')} section")
            return recommendations
        
        if quality_score < 0.6:
            recommendations.append(f"Expand {section_name.replace('_', ' ')} with more detail")
        
        if len(content.split()) < 20:
            recommendations.append(f"Provide more comprehensive {section_name.replace('_', ' ')} information")
        
        if not entities and section_name in ["assessment", "plan", "medications"]:
            recommendations.append(f"Include specific medical terms in {section_name.replace('_', ' ')}")
        
        return recommendations
    
    def _extract_primary_diagnosis(self, entities: List[MedicalEntity], icd10_codes: List[ClinicalCode]) -> Optional[str]:
        """Extract primary diagnosis from entities and codes"""
        # Look for highest confidence diagnosis
        diagnosis_entities = [e for e in entities if e.entity_type == MedicalEntityType.DIAGNOSIS]
        
        if diagnosis_entities:
            primary = max(diagnosis_entities, key=lambda x: x.confidence)
            return primary.text
        
        # Fallback to highest confidence ICD-10 code
        if icd10_codes:
            primary_code = max(icd10_codes, key=lambda x: x.confidence)
            return primary_code.description
        
        return None
    
    def _extract_secondary_diagnoses(self, entities: List[MedicalEntity], icd10_codes: List[ClinicalCode]) -> List[str]:
        """Extract secondary diagnoses"""
        diagnosis_entities = [e for e in entities if e.entity_type == MedicalEntityType.DIAGNOSIS]
        
        # Return all but the highest confidence diagnosis
        if len(diagnosis_entities) > 1:
            sorted_diagnoses = sorted(diagnosis_entities, key=lambda x: x.confidence, reverse=True)
            return [d.text for d in sorted_diagnoses[1:]]
        
        return []
    
    def _extract_procedures(self, entities: List[MedicalEntity], cpt_codes: List[ClinicalCode]) -> List[str]:
        """Extract procedures from entities and codes"""
        procedure_entities = [e for e in entities if e.entity_type == MedicalEntityType.PROCEDURE]
        procedures = [p.text for p in procedure_entities]
        
        # Add procedures from CPT codes
        for code in cpt_codes:
            if code.code_type == "CPT" and "procedure" in code.description.lower():
                procedures.append(code.description)
        
        return procedures
    
    def _extract_medications(self, entities: List[MedicalEntity]) -> List[str]:
        """Extract medications from entities"""
        medication_entities = [e for e in entities if e.entity_type == MedicalEntityType.MEDICATION]
        return [m.text for m in medication_entities]
    
    def _determine_quality_level(self, completeness_score: float) -> DocumentationQuality:
        """Determine overall quality level"""
        if completeness_score >= 0.9:
            return DocumentationQuality.EXCELLENT
        elif completeness_score >= 0.8:
            return DocumentationQuality.GOOD
        elif completeness_score >= 0.6:
            return DocumentationQuality.ADEQUATE
        elif completeness_score >= 0.4:
            return DocumentationQuality.NEEDS_IMPROVEMENT
        else:
            return DocumentationQuality.INCOMPLETE
    
    def generate_clinical_report(self, clinical_note: ClinicalNote) -> Dict[str, Any]:
        """Generate comprehensive clinical report"""
        quality_metrics = self.quality_assessment.assess_quality(clinical_note)
        
        # Calculate billing information
        total_reimbursement = sum(
            code.reimbursement_rate or 0 for code in clinical_note.billing_codes
        )
        
        report = {
            "note_summary": {
                "note_id": clinical_note.note_id,
                "note_type": clinical_note.note_type.value,
                "specialty": clinical_note.specialty.value,
                "created_at": clinical_note.created_at.isoformat(),
                "word_count": clinical_note.word_count,
                "overall_quality": clinical_note.overall_quality.value
            },
            "clinical_content": {
                "primary_diagnosis": clinical_note.primary_diagnosis,
                "secondary_diagnoses": clinical_note.secondary_diagnoses,
                "procedures": clinical_note.procedures,
                "medications": clinical_note.medications,
                "sections": {
                    name: {
                        "content": section.content,
                        "quality_score": section.quality_score,
                        "completeness_score": section.completeness_score,
                        "entity_count": len(section.entities),
                        "recommendations": section.recommendations
                    }
                    for name, section in clinical_note.sections.items()
                }
            },
            "coding_information": {
                "billing_codes": [
                    {
                        "code": code.code,
                        "description": code.description,
                        "type": code.code_type,
                        "confidence": code.confidence,
                        "reimbursement_rate": code.reimbursement_rate
                    }
                    for code in clinical_note.billing_codes
                ],
                "total_estimated_reimbursement": total_reimbursement
            },
            "quality_assessment": {
                "completeness_score": quality_metrics.completeness_score,
                "accuracy_score": quality_metrics.accuracy_score,
                "specificity_score": quality_metrics.specificity_score,
                "coding_accuracy": quality_metrics.coding_accuracy,
                "missing_elements": quality_metrics.missing_elements,
                "improvement_suggestions": quality_metrics.improvement_suggestions
            },
            "efficiency_metrics": {
                "estimated_time_saved": clinical_note.estimated_time_saved,
                "documentation_efficiency": quality_metrics.documentation_time,
                "automation_percentage": 0.75  # Estimated automation benefit
            }
        }
        
        return report

# Usage example and testing functions
async def main():
    """Main function for testing clinical documentation system"""
    print("📋 Clinical Documentation and Reporting System")
    print("=" * 50)
    
    # Initialize system
    clinical_system = ClinicalDocumentationSystem()
    
    # Sample clinical transcript
    sample_transcript = """
    Chief Complaint: 65-year-old male presents with chest pain and shortness of breath.
    
    History of Present Illness: Patient reports acute onset of substernal chest pain 
    that started 2 hours ago. Pain is 8/10 severity, radiating to left arm. 
    Associated with diaphoresis and nausea. Patient has history of hypertension 
    and diabetes mellitus.
    
    Physical Examination: 
    Vital signs: BP 160/95, HR 110, RR 22, Temp 98.6°F, O2 sat 94%
    General: Appears uncomfortable, diaphoretic
    Cardiovascular: Irregular rhythm, S3 gallop present
    Pulmonary: Bilateral rales at lung bases
    
    Assessment: 
    1. Acute myocardial infarction
    2. Congestive heart failure
    3. Hypertension
    4. Diabetes mellitus
    
    Plan: 
    1. Admit to CCU for monitoring
    2. Start aspirin 325mg daily
    3. Begin metoprolol 25mg BID
    4. Continue lisinopril 10mg daily
    5. Monitor blood glucose, continue metformin
    6. Cardiology consultation
    7. Follow-up echocardiogram
    """
    
    print("\n🏥 Generating Clinical Note...")
    
    # Generate clinical note
    clinical_note = await clinical_system.generate_clinical_note(
        transcript_text=sample_transcript,
        note_type=ClinicalNoteType.ADMISSION_NOTE,
        specialty=ClinicalSpecialty.CARDIOLOGY,
        patient_id="PATIENT_001",
        provider_id="PROVIDER_001",
        encounter_id="ENCOUNTER_001"
    )
    
    print(f"✅ Clinical note generated: {clinical_note.note_id}")
    print(f"   Note type: {clinical_note.note_type.value}")
    print(f"   Specialty: {clinical_note.specialty.value}")
    print(f"   Quality: {clinical_note.overall_quality.value}")
    print(f"   Word count: {clinical_note.word_count}")
    print(f"   Time saved: {clinical_note.estimated_time_saved:.1f} minutes")
    
    # Display sections
    print(f"\n📄 Clinical Sections ({len(clinical_note.sections)}):")
    for section_name, section in clinical_note.sections.items():
        print(f"   • {section_name.replace('_', ' ').title()}: {len(section.content)} chars")
        print(f"     Quality: {section.quality_score:.2f}, Completeness: {section.completeness_score:.2f}")
    
    # Display coding information
    print(f"\n💰 Billing Codes ({len(clinical_note.billing_codes)}):")
    total_reimbursement = 0
    for code in clinical_note.billing_codes[:5]:  # Show first 5
        print(f"   • {code.code} ({code.code_type}): {code.description}")
        print(f"     Confidence: {code.confidence:.2f}, Rate: ${code.reimbursement_rate or 0:.2f}")
        total_reimbursement += code.reimbursement_rate or 0
    
    print(f"\n💵 Total Estimated Reimbursement: ${total_reimbursement:.2f}")
    
    # Generate comprehensive report
    print(f"\n📊 Generating Clinical Report...")
    clinical_report = clinical_system.generate_clinical_report(clinical_note)
    
    quality_assessment = clinical_report["quality_assessment"]
    print(f"   Completeness: {quality_assessment['completeness_score']:.2f}")
    print(f"   Accuracy: {quality_assessment['accuracy_score']:.2f}")
    print(f"   Specificity: {quality_assessment['specificity_score']:.2f}")
    print(f"   Coding Accuracy: {quality_assessment['coding_accuracy']:.2f}")
    
    if quality_assessment["missing_elements"]:
        print(f"   Missing Elements: {', '.join(quality_assessment['missing_elements'][:3])}")
    
    if quality_assessment["improvement_suggestions"]:
        print(f"   Suggestions: {quality_assessment['improvement_suggestions'][0]}")
    
    print(f"\n✅ Clinical documentation system demonstration complete!")

if __name__ == "__main__":
    asyncio.run(main())