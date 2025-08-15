"""
Medical Test Helpers
Specialized testing utilities for medical transcription features
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import random


class MedicalTestHelpers:
    """Helper utilities for testing medical transcription features"""
    
    @staticmethod
    def generate_test_patient_id() -> str:
        """Generate test patient ID"""
        return f"PAT_{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def generate_test_provider_id() -> str:
        """Generate test provider ID"""
        return f"DOC_{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def generate_test_encounter_id() -> str:
        """Generate test encounter ID"""
        return f"ENC_{uuid.uuid4().hex[:8].upper()}"
    
    @staticmethod
    def create_sample_medical_transcript() -> str:
        """Create sample medical transcript with various medical entities"""
        return """
        Patient presents today for follow-up of hypertension and type 2 diabetes mellitus.
        
        Chief Complaint: "I've been feeling tired and my blood pressure readings at home have been high."
        
        History of Present Illness: 
        The patient is a 65-year-old male with a history of hypertension diagnosed 5 years ago and 
        type 2 diabetes mellitus diagnosed 3 years ago. He reports fatigue for the past 2 weeks and 
        home blood pressure readings consistently above 160/90 mmHg. Current medications include 
        lisinopril 10 mg daily and metformin 500 mg twice daily. Patient reports good adherence 
        to medications. Denies chest pain, shortness of breath, or dizziness.
        
        Past Medical History:
        - Hypertension (2018)
        - Type 2 diabetes mellitus (2020)
        - Dyslipidemia (2019)
        
        Current Medications:
        - Lisinopril 10 mg once daily
        - Metformin 500 mg twice daily
        - Atorvastatin 20 mg once daily
        
        Physical Examination:
        Vital Signs: Blood pressure 168/94 mmHg, heart rate 78 bpm, respiratory rate 16, 
        temperature 98.6°F, oxygen saturation 98% on room air, BMI 28.5
        
        General: Well-appearing male in no acute distress
        HEENT: Normocephalic, atraumatic. PERRLA. No scleral icterus.
        Cardiovascular: Regular rate and rhythm, no murmurs, rubs, or gallops
        Pulmonary: Clear to auscultation bilaterally
        Extremities: No edema, pulses intact
        
        Laboratory Results:
        - Hemoglobin A1c: 7.8% (elevated)
        - Fasting glucose: 145 mg/dL (elevated) 
        - Creatinine: 0.9 mg/dL (normal)
        - Total cholesterol: 220 mg/dL (borderline high)
        - LDL: 140 mg/dL (elevated)
        
        Assessment and Plan:
        1. Hypertension, uncontrolled
           - Increase lisinopril to 20 mg daily
           - Continue home blood pressure monitoring
           - Follow up in 4 weeks
        
        2. Type 2 diabetes mellitus, suboptimal control
           - Continue metformin
           - Add glipizide 5 mg daily
           - Diabetes education referral
           - Repeat A1c in 3 months
        
        3. Dyslipidemia
           - Continue atorvastatin
           - Recheck lipid panel in 6 months
        
        Patient counseled on medication compliance, dietary modifications, and regular exercise.
        Follow-up appointment scheduled in 4 weeks.
        """
    
    @staticmethod
    def create_sample_medical_entities() -> List[Dict[str, Any]]:
        """Create sample medical entities for testing"""
        return [
            {
                "text": "hypertension",
                "entity_type": "diagnosis", 
                "confidence": 0.95,
                "start_pos": 45,
                "end_pos": 57,
                "normalized_form": "Hypertension",
                "medical_code": "I10",
                "context": "follow-up of hypertension",
                "severity": "uncontrolled",
                "category": "cardiovascular",
                "subcategory": "blood_pressure_disorder"
            },
            {
                "text": "type 2 diabetes mellitus",
                "entity_type": "diagnosis",
                "confidence": 0.92,
                "start_pos": 62,
                "end_pos": 86,
                "normalized_form": "Type 2 Diabetes Mellitus",
                "medical_code": "E11.9",
                "context": "follow-up of type 2 diabetes mellitus",
                "severity": "suboptimal_control",
                "category": "endocrine",
                "subcategory": "diabetes"
            },
            {
                "text": "lisinopril 10 mg daily",
                "entity_type": "medication",
                "confidence": 0.98,
                "start_pos": 280,
                "end_pos": 302,
                "normalized_form": "Lisinopril",
                "medical_code": "RXN:29046",
                "context": "Current medications include lisinopril",
                "value": "10",
                "unit": "mg"
            },
            {
                "text": "blood pressure 168/94 mmHg",
                "entity_type": "vital_sign",
                "confidence": 0.96,
                "start_pos": 650,
                "end_pos": 677,
                "normalized_form": "Blood Pressure",
                "context": "Vital Signs measurement",
                "value": "168/94",
                "unit": "mmHg"
            }
        ]
    
    @staticmethod
    def create_sample_voice_biomarkers() -> List[Dict[str, Any]]:
        """Create sample voice biomarker data"""
        return [
            {
                "biomarker_type": "speech_rate",
                "value": 145.2,
                "interpretation": "Slightly elevated speech rate may indicate anxiety",
                "confidence": 0.87,
                "clinical_relevance": "Consider stress assessment"
            },
            {
                "biomarker_type": "vocal_tremor",
                "value": 0.23,
                "interpretation": "Minimal vocal tremor detected",
                "confidence": 0.78,
                "clinical_relevance": "Within normal range for age group"
            },
            {
                "biomarker_type": "pause_frequency",
                "value": 3.7,
                "interpretation": "Increased pause frequency suggests cognitive processing",
                "confidence": 0.82,
                "clinical_relevance": "Monitor for cognitive changes"
            }
        ]
    
    @staticmethod
    def create_sample_social_determinants() -> List[Dict[str, Any]]:
        """Create sample social determinants of health data"""
        return [
            {
                "category": "housing",
                "factor": "stable_housing",
                "impact_level": "low",
                "notes": "Patient reports stable housing situation",
                "confidence": 0.85
            },
            {
                "category": "employment",
                "factor": "recent_retirement",
                "impact_level": "medium",
                "notes": "Recently retired, adjusting to lifestyle changes",
                "confidence": 0.78
            },
            {
                "category": "transportation",
                "factor": "reliable_transportation",
                "impact_level": "low",
                "notes": "Has reliable transportation to appointments",
                "confidence": 0.90
            },
            {
                "category": "social_support",
                "factor": "strong_family_support",
                "impact_level": "positive",
                "notes": "Strong support from spouse and adult children",
                "confidence": 0.88
            }
        ]
    
    @staticmethod
    def create_sample_phi_violations() -> List[Dict[str, Any]]:
        """Create sample PHI violations for testing"""
        return [
            {
                "violation_type": "date_of_birth",
                "text": "DOB 01/01/1980",
                "position": [125, 138],
                "severity": "medium",
                "recommendation": "Replace with age or age range",
                "confidence": 0.95
            },
            {
                "violation_type": "phone_number",
                "text": "(555) 123-4567",
                "position": [245, 259], 
                "severity": "high",
                "recommendation": "Remove or mask phone number",
                "confidence": 0.98
            },
            {
                "violation_type": "address",
                "text": "123 Main Street, Anytown, ST 12345",
                "position": [180, 214],
                "severity": "high",
                "recommendation": "Replace with city/state only",
                "confidence": 0.92
            }
        ]
    
    @staticmethod
    def create_comprehensive_analysis() -> Dict[str, Any]:
        """Create sample comprehensive analysis results"""
        return {
            "patient_engagement_score": 8.2,
            "care_quality_indicators": [
                {
                    "indicator": "Patient Communication Quality",
                    "status": "excellent",
                    "details": "Patient actively engaged and provided detailed history",
                    "score": 9.1,
                    "benchmark": 8.0
                },
                {
                    "indicator": "Clinical Documentation Completeness",
                    "status": "good",
                    "details": "All required sections documented with good detail",
                    "score": 8.7,
                    "benchmark": 8.5
                },
                {
                    "indicator": "Medication Reconciliation",
                    "status": "excellent",
                    "details": "Complete medication list with dosages verified",
                    "score": 9.3,
                    "benchmark": 8.2
                }
            ],
            "clinical_decision_support": [
                {
                    "recommendation": "Consider ACE inhibitor dose optimization",
                    "evidence_level": "A",
                    "priority": "medium",
                    "supporting_data": "Current BP readings indicate suboptimal control",
                    "implementation_timeline": "within 1 week"
                },
                {
                    "recommendation": "Diabetes education referral indicated", 
                    "evidence_level": "B",
                    "priority": "medium",
                    "supporting_data": "A1c above target suggests need for additional education",
                    "implementation_timeline": "within 2 weeks"
                }
            ],
            "risk_assessment": "Moderate cardiovascular risk due to uncontrolled hypertension and diabetes",
            "care_gaps": [
                "Annual diabetic eye exam due",
                "Pneumococcal vaccination status unclear",
                "Depression screening recommended"
            ]
        }
    
    @staticmethod
    def mock_medical_transcription_service():
        """Create mock for medical transcription service"""
        mock_service = Mock()
        
        # Mock successful transcription
        mock_service.process_medical_transcription.return_value = {
            "success": True,
            "processing_id": f"proc_{uuid.uuid4().hex[:8]}",
            "transcript": MedicalTestHelpers.create_sample_medical_transcript(),
            "confidence": 0.94,
            "entities": MedicalTestHelpers.create_sample_medical_entities(),
            "voice_biomarkers": MedicalTestHelpers.create_sample_voice_biomarkers(),
            "social_determinants": MedicalTestHelpers.create_sample_social_determinants(),
            "phi_violations": [],  # No PHI in test data
            "comprehensive_analysis": MedicalTestHelpers.create_comprehensive_analysis(),
            "compliance_status": "compliant",
            "medications": [
                {
                    "name": "Lisinopril",
                    "normalized_name": "lisinopril",
                    "confidence": 0.98,
                    "dosage": "10 mg",
                    "frequency": "daily",
                    "medical_code": "RXN:29046"
                },
                {
                    "name": "Metformin", 
                    "normalized_name": "metformin",
                    "confidence": 0.96,
                    "dosage": "500 mg", 
                    "frequency": "twice daily",
                    "medical_code": "RXN:6809"
                }
            ],
            "procedures": [
                {
                    "name": "Blood pressure measurement",
                    "normalized_name": "blood pressure check",
                    "confidence": 0.92,
                    "medical_code": "G8476"
                }
            ],
            "diagnoses": [
                {
                    "name": "Hypertension", 
                    "normalized_name": "hypertension",
                    "confidence": 0.95,
                    "severity": "uncontrolled",
                    "medical_code": "I10"
                },
                {
                    "name": "Type 2 Diabetes Mellitus",
                    "normalized_name": "type 2 diabetes mellitus", 
                    "confidence": 0.92,
                    "severity": "suboptimal_control",
                    "medical_code": "E11.9"
                }
            ],
            "vital_signs": [
                {
                    "type": "blood_pressure",
                    "value": 168.0,
                    "unit": "mmHg_systolic", 
                    "interpretation": "elevated",
                    "abnormal": True
                },
                {
                    "type": "heart_rate",
                    "value": 78.0,
                    "unit": "bpm",
                    "interpretation": "normal", 
                    "abnormal": False
                }
            ],
            "sections": {
                "chief_complaint": "I've been feeling tired and my blood pressure readings at home have been high.",
                "history_present_illness": "The patient is a 65-year-old male...",
                "physical_exam": "Vital Signs: Blood pressure 168/94 mmHg...",
                "assessment_plan": "1. Hypertension, uncontrolled..."
            }
        }
        
        return mock_service
    
    @staticmethod  
    def mock_phi_detection_service():
        """Create mock for PHI detection service with violations"""
        mock_service = Mock()
        
        # Mock PHI detection with violations
        mock_service.process_medical_transcription.return_value = {
            "success": True,
            "processing_id": f"proc_{uuid.uuid4().hex[:8]}",
            "transcript": "Patient John Doe, DOB 01/01/1980, phone (555) 123-4567...",
            "confidence": 0.89,
            "entities": [],
            "phi_violations": MedicalTestHelpers.create_sample_phi_violations(),
            "compliance_status": "violations_detected",
            "anonymized_content": "Patient [NAME], DOB [MASKED], phone [MASKED]...",
            "sections": {}
        }
        
        return mock_service
    
    @staticmethod
    def create_test_audio_file() -> bytes:
        """Create fake audio file data for testing"""
        # Create minimal WAV header + some fake audio data
        wav_header = bytes([
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x08, 0x00, 0x00,  # File size - 8
            0x57, 0x41, 0x56, 0x45,  # "WAVE"  
            0x66, 0x6D, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # Subchunk1Size (16)
            0x01, 0x00,              # AudioFormat (PCM)
            0x01, 0x00,              # NumChannels (mono)
            0x44, 0xAC, 0x00, 0x00,  # SampleRate (44100)
            0x88, 0x58, 0x01, 0x00,  # ByteRate
            0x02, 0x00,              # BlockAlign
            0x10, 0x00,              # BitsPerSample (16)
            0x64, 0x61, 0x74, 0x61,  # "data"
            0x00, 0x08, 0x00, 0x00   # Subchunk2Size
        ])
        
        # Add some fake audio data (random bytes)
        fake_audio_data = bytes([random.randint(0, 255) for _ in range(2048)])
        
        return wav_header + fake_audio_data
    
    @staticmethod
    def create_hipaa_compliance_test_cases() -> List[Dict[str, Any]]:
        """Create test cases for different HIPAA compliance levels"""
        return [
            {
                "compliance_level": "strict",
                "description": "No PHI allowed - all personal information removed",
                "expected_behavior": {
                    "phi_detection": True,
                    "phi_removal": True,
                    "anonymization": True,
                    "audit_logging": True
                },
                "test_transcript": "Patient presents for routine checkup. No identifying information should remain.",
                "expected_violations": []
            },
            {
                "compliance_level": "standard", 
                "description": "PHI anonymized using secure tokens",
                "expected_behavior": {
                    "phi_detection": True,
                    "phi_removal": False,
                    "anonymization": True,
                    "audit_logging": True
                },
                "test_transcript": "Patient John Doe, DOB 01/01/1980, presents for followup.",
                "expected_violations": [
                    {"type": "name", "severity": "high"},
                    {"type": "date_of_birth", "severity": "medium"}
                ]
            },
            {
                "compliance_level": "research",
                "description": "Limited PHI allowed for research with consent",
                "expected_behavior": {
                    "phi_detection": True, 
                    "phi_removal": False,
                    "anonymization": False,
                    "audit_logging": True
                },
                "test_transcript": "Patient John Doe, DOB 01/01/1980, enrolled in research study XYZ123.",
                "expected_violations": []  # PHI allowed with consent
            }
        ]
    
    @staticmethod
    def generate_medical_test_scenarios() -> List[Dict[str, Any]]:
        """Generate comprehensive medical test scenarios"""
        return [
            {
                "scenario": "routine_checkup",
                "patient_type": "healthy_adult",
                "encounter_type": "routine_visit",
                "expected_entities": ["vital_signs", "general_assessment"],
                "expected_medications": [],
                "expected_diagnoses": [],
                "complexity_score": 1
            },
            {
                "scenario": "chronic_disease_management",
                "patient_type": "chronic_conditions", 
                "encounter_type": "follow_up",
                "expected_entities": ["medications", "vital_signs", "diagnoses", "procedures"],
                "expected_medications": ["antihypertensives", "diabetes_medications"],
                "expected_diagnoses": ["hypertension", "diabetes"],
                "complexity_score": 3
            },
            {
                "scenario": "emergency_consultation",
                "patient_type": "acute_presentation",
                "encounter_type": "emergency",
                "expected_entities": ["symptoms", "vital_signs", "procedures", "medications"],
                "expected_medications": ["emergency_medications"],
                "expected_diagnoses": ["acute_conditions"],
                "complexity_score": 4
            },
            {
                "scenario": "mental_health_assessment",
                "patient_type": "psychiatric",
                "encounter_type": "psychiatric_evaluation",
                "expected_entities": ["emotional_state", "social_determinants", "medications"],
                "expected_medications": ["psychiatric_medications"],
                "expected_diagnoses": ["psychiatric_conditions"],
                "complexity_score": 2
            }
        ]