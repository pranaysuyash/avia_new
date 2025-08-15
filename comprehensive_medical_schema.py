"""
Comprehensive Medical Schema Implementation - Enhanced Medical Transcription
Integrates the detailed medical transcript schema for complete healthcare documentation
"""

import json
import re
import logging
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import spacy
from spacy.matcher import PhraseMatcher, Matcher
from spacy.tokens import Doc, Span, Token

logger = logging.getLogger(__name__)

# Comprehensive Medical Schema Definition
COMPREHENSIVE_MEDICAL_SCHEMA = {
    "metadata": {
        "location": "",
        "setting": "",
        "duration": "",
        "visit_type": "",
        "technology_used": "",
        "healthcare_providers": [],
        "call_quality": "",
        "connection_issues": "",
        "background_noise": "",
        "language_of_consultation": ""
    },
    "transcription": {
        "segments": []
    },
    "content_summary": {
        "main_points": "",
        "interaction_purpose": "",
        "key_decisions_made": ""
    },
    "participants": [],
    "patient_information": {
        "demographics": {},
        "history": {},
        "current_status": {},
        "health_behaviors": {},
        "insurance_information": {}
    },
    "clinical_data": {
        "test_results": [],
        "diagnostic_imaging": {},
        "medications": [],
        "medical_devices": [],
        "physical_examination": {},
        "laboratory_tests": [],
        "allergies_and_intolerances": [],
        "immunizations": []
    },
    "interaction_analysis": {
        "significant_events": [],
        "emotional_psychological": [],
        "keyword_topic_analysis": {},
        "doctor_patient_dynamics": {},
        "non_verbal_cues": [],
        "behavioral_markers": [],
        "voice_biomarkers": [],
        "ambient_sounds": []
    },
    "care_quality_assessment": {
        "guideline_adherence": "",
        "comprehensiveness": "",
        "identified_gaps": "",
        "efficiency_assessment": "",
        "cultural_competence": {},
        "patient_satisfaction_indicators": {},
        "health_equity_considerations": {},
        "care_continuity": "",
        "patient_safety_measures": ""
    },
    "treatment_and_follow_up": {
        "current_treatment": {},
        "therapeutic_response": {},
        "follow_up_actions": {},
        "care_plan": {},
        "medication_adjustments": [],
        "prescription_details": []
    },
    "patient_engagement": {
        "communication_style": {},
        "health_literacy": {},
        "patient_activation": {},
        "self_management": {},
        "patient_education": {},
        "support_system": {},
        "patient_preferences": {},
        "motivational_interviewing": {}
    },
    "decision_making": {
        "options_presented": "",
        "patient_involvement": "",
        "reasoning_explained": "",
        "shared_decision_making_approach": "",
        "patient_values_considered": ""
    },
    "specialized_considerations": {
        "pain_assessment": {},
        "end_of_life_care": {},
        "genetic_considerations": {},
        "environmental_health": {},
        "emergency_preparedness": {},
        "integrative_medicine": {},
        "reproductive_health": {},
        "mental_health": {},
        "nutritional_assessment": {},
        "rehabilitation_needs": {}
    },
    "healthcare_system_interactions": {
        "facilities_mentioned": [],
        "healthcare_costs": {},
        "care_coordination": {},
        "health_information_technology": {},
        "digital_health_integration": {},
        "prior_authorizations": []
    },
    "compliance_and_legal": {
        "hipaa_adherence": "",
        "informed_consent": "",
        "documentation_completeness": "",
        "capacity_assessment": "",
        "advance_directive_discussion": "",
        "ethical_dilemmas_addressed": "",
        "malpractice_risk_assessment": ""
    },
    "research_and_data": {
        "research_participation": {},
        "cross_patient_comparison": {},
        "longitudinal_health_trends": {},
        "region_specific_trends": {},
        "patient_reported_outcomes": {}
    },
    "social_determinants_of_health": {
        "housing_situation": "",
        "food_security": "",
        "transportation_access": "",
        "employment_status": "",
        "education_level": "",
        "social_support_network": "",
        "access_to_healthcare": "",
        "neighborhood_safety": ""
    },
    "preventive_care": {
        "screenings_recommended": "",
        "lifestyle_modifications_suggested": "",
        "vaccination_status_reviewed": "",
        "health_risk_assessments": "",
        "preventive_medications_discussed": ""
    },
    "medication_management": {
        "current_medications_reviewed": "",
        "medication_changes_made": "",
        "potential_drug_interactions_identified": "",
        "medication_reconciliation_performed": "",
        "adherence_strategies_discussed": ""
    },
    "overall_assessment": {
        "key_findings": "",
        "critical_points": "",
        "areas_for_improvement": "",
        "positive_aspects": "",
        "follow_up_recommendations": "",
        "prognosis": "",
        "care_plan_summary": ""
    },
    "telemedicine_specifics": {
        "visual_assessment_quality": "",
        "technical_difficulties_impact": "",
        "physical_exam_limitations": "",
        "patient_comfort_with_technology": "",
        "remote_monitoring_equipment_used": ""
    },
    "follow_up_communication": {
        "scheduled_follow_up_method": "",
        "patient_instructions_provided": "",
        "care_summary_sent": "",
        "post_visit_survey_planned": "",
        "patient_portal_messages": []
    }
}

class ComprehensiveEntityType(Enum):
    """Extended entity types for comprehensive schema"""
    # Basic medical entities
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
    
    # Advanced comprehensive entities
    VITAL_SIGN = "vital_sign"
    TEST_RESULT = "test_result"
    ALLERGY = "allergy"
    IMMUNIZATION = "immunization"
    DEVICE = "medical_device"
    COST = "healthcare_cost"
    EMOTION = "emotion"
    VOICE_BIOMARKER = "voice_biomarker"
    AMBIENT_SOUND = "ambient_sound"
    NON_VERBAL_CUE = "non_verbal_cue"
    BEHAVIORAL_MARKER = "behavioral_marker"
    SOCIAL_DETERMINANT = "social_determinant"
    HEALTH_BEHAVIOR = "health_behavior"
    INSURANCE = "insurance"
    TECHNOLOGY = "technology"
    COMMUNICATION_PREFERENCE = "communication_preference"

@dataclass
class ComprehensiveEntity:
    """Enhanced entity with comprehensive schema support"""
    text: str
    entity_type: ComprehensiveEntityType
    confidence: float
    start_pos: int
    end_pos: int
    normalized_form: str
    medical_code: Optional[str] = None
    context: Optional[str] = None
    severity: Optional[str] = None
    timestamp: Optional[str] = None
    speaker: Optional[str] = None
    clinical_significance: Optional[str] = None
    follow_up_needed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class VitalSigns:
    """Structured vital signs data"""
    blood_pressure: Optional[str] = None
    heart_rate: Optional[str] = None
    respiratory_rate: Optional[str] = None
    temperature: Optional[str] = None
    oxygen_saturation: Optional[str] = None
    timestamp: Optional[str] = None
    context: Optional[str] = None

@dataclass
class VoiceBiomarker:
    """Voice biomarker analysis"""
    biomarker_type: str
    confidence_level: float
    timestamp: str
    related_symptoms: List[str]
    context: str
    clinical_significance: Optional[str] = None

@dataclass
class AmbientSound:
    """Ambient sound analysis"""
    sound_type: str
    intensity: str
    duration: str
    timestamp: str
    context: str
    clinical_relevance: Optional[str] = None

class ComprehensiveEntityExtractor:
    """Enhanced entity extractor for comprehensive medical schema"""
    
    def __init__(self):
        self.setup_nlp_model()
        self.setup_comprehensive_matchers()
        self.setup_patterns()
        
    def setup_nlp_model(self):
        """Setup enhanced NLP model with medical components"""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model not found. Please install: python -m spacy download en_core_web_sm")
            raise
        
        # Add custom components for comprehensive analysis
        if 'comprehensive_medical' not in self.nlp.pipe_names:
            self.nlp.add_pipe('comprehensive_medical', after='ner')
    
    def setup_comprehensive_matchers(self):
        """Setup matchers for all comprehensive entity types"""
        self.matchers = {}
        
        # Vital signs matcher
        self.vital_signs_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        vital_signs_patterns = [
            "blood pressure", "bp", "heart rate", "hr", "pulse", "respiratory rate", 
            "rr", "breathing rate", "temperature", "temp", "oxygen saturation", 
            "o2 sat", "spo2", "pulse ox"
        ]
        vital_patterns = [self.nlp.make_doc(vs) for vs in vital_signs_patterns]
        self.vital_signs_matcher.add("VITAL_SIGNS", vital_patterns)
        
        # Test results matcher
        self.test_results_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        test_patterns = [
            "blood test", "urine test", "lab results", "cbc", "complete blood count",
            "glucose test", "cholesterol", "hemoglobin", "white blood cell count",
            "platelet count", "creatinine", "bun", "liver function", "thyroid function"
        ]
        test_result_patterns = [self.nlp.make_doc(test) for test in test_patterns]
        self.test_results_matcher.add("TEST_RESULTS", test_result_patterns)
        
        # Healthcare costs matcher
        self.costs_matcher = Matcher(self.nlp.vocab)
        cost_pattern = [
            {"LIKE_NUM": True}, 
            {"LOWER": {"IN": ["dollars", "dollar", "usd", "$"]}},
            {"LOWER": {"IN": ["cost", "fee", "charge", "bill", "payment"]}, "OP": "?"}
        ]
        self.costs_matcher.add("HEALTHCARE_COSTS", [cost_pattern])
        
        # Technology matcher
        self.technology_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        tech_patterns = [
            "telemedicine", "telehealth", "video call", "zoom", "patient portal",
            "electronic health record", "ehr", "emr", "mobile app", "wearable device",
            "fitbit", "apple watch", "glucose monitor", "blood pressure monitor"
        ]
        tech_pattern_docs = [self.nlp.make_doc(tech) for tech in tech_patterns]
        self.technology_matcher.add("TECHNOLOGY", tech_pattern_docs)
        
        # Social determinants matcher
        self.social_determinants_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        social_patterns = [
            "housing", "homeless", "food insecurity", "transportation", "employment",
            "unemployed", "education level", "social support", "family support",
            "insurance coverage", "financial stress", "neighborhood safety"
        ]
        social_pattern_docs = [self.nlp.make_doc(social) for social in social_patterns]
        self.social_determinants_matcher.add("SOCIAL_DETERMINANTS", social_pattern_docs)
        
        # Emotional/psychological matcher
        self.emotion_matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        emotion_patterns = [
            "anxious", "anxiety", "worried", "depressed", "sad", "happy", "frustrated",
            "angry", "fearful", "hopeful", "optimistic", "pessimistic", "stressed",
            "calm", "relaxed", "nervous", "excited", "confused", "overwhelmed"
        ]
        emotion_pattern_docs = [self.nlp.make_doc(emotion) for emotion in emotion_patterns]
        self.emotion_matcher.add("EMOTIONS", emotion_pattern_docs)
    
    def setup_patterns(self):
        """Setup regex patterns for complex extractions"""
        self.patterns = {
            'vital_signs': {
                'blood_pressure': re.compile(r'(?:bp|blood pressure)[\s:]*(\d{2,3})/(\d{2,3})', re.IGNORECASE),
                'heart_rate': re.compile(r'(?:hr|heart rate|pulse)[\s:]*(\d{2,3})(?:\s*bpm)?', re.IGNORECASE),
                'temperature': re.compile(r'(?:temp|temperature)[\s:]*(\d{2,3}(?:\.\d)?)\s*(?:f|fahrenheit|c|celsius)?', re.IGNORECASE),
                'respiratory_rate': re.compile(r'(?:rr|respiratory rate|breathing rate)[\s:]*(\d{1,2})', re.IGNORECASE),
                'oxygen_saturation': re.compile(r'(?:o2 sat|oxygen saturation|spo2|pulse ox)[\s:]*(\d{2,3})%?', re.IGNORECASE)
            },
            'measurements': {
                'weight': re.compile(r'(?:weight|wt)[\s:]*(\d{2,3}(?:\.\d)?)\s*(?:lbs?|pounds?|kg|kilograms?)', re.IGNORECASE),
                'height': re.compile(r'(?:height|ht)[\s:]*(\d{1,2})[\'\']\s*(\d{1,2})[""\""]?|(\d{2,3})\s*(?:cm|centimeters?)', re.IGNORECASE),
                'bmi': re.compile(r'(?:bmi|body mass index)[\s:]*(\d{1,2}(?:\.\d)?)', re.IGNORECASE)
            },
            'test_values': {
                'glucose': re.compile(r'(?:glucose|blood sugar)[\s:]*(\d{2,3})\s*(?:mg/dl)?', re.IGNORECASE),
                'cholesterol': re.compile(r'(?:cholesterol|chol)[\s:]*(\d{2,3})\s*(?:mg/dl)?', re.IGNORECASE),
                'hemoglobin': re.compile(r'(?:hemoglobin|hgb|hb)[\s:]*(\d{1,2}(?:\.\d)?)', re.IGNORECASE)
            },
            'timeline': re.compile(r'(\d{1,2})\s*(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?|years?)\s*(?:ago|before|prior)', re.IGNORECASE),
            'duration': re.compile(r'(?:for|lasting|duration)\s*(\d{1,2})\s*(?:hours?|hrs?|minutes?|mins?|days?|weeks?|months?)', re.IGNORECASE)
        }
    
    def extract_comprehensive_entities(self, transcript_text: str, 
                                     speaker_segments: List[Dict] = None) -> Dict[str, List[ComprehensiveEntity]]:
        """Extract all entities for comprehensive medical schema"""
        doc = self.nlp(transcript_text)
        all_entities = {}
        
        # Extract basic medical entities (from original system)
        basic_entities = self._extract_basic_medical_entities(doc)
        all_entities.update(basic_entities)
        
        # Extract vital signs
        vital_signs = self._extract_vital_signs(doc, transcript_text)
        all_entities['vital_signs'] = vital_signs
        
        # Extract test results
        test_results = self._extract_test_results(doc, transcript_text)
        all_entities['test_results'] = test_results
        
        # Extract healthcare costs
        costs = self._extract_healthcare_costs(doc, transcript_text)
        all_entities['healthcare_costs'] = costs
        
        # Extract technology mentions
        technology = self._extract_technology_mentions(doc)
        all_entities['technology'] = technology
        
        # Extract social determinants
        social_determinants = self._extract_social_determinants(doc)
        all_entities['social_determinants'] = social_determinants
        
        # Extract emotional/psychological indicators
        emotions = self._extract_emotional_indicators(doc, speaker_segments)
        all_entities['emotions'] = emotions
        
        # Extract voice biomarkers (simulated)
        voice_biomarkers = self._extract_voice_biomarkers(transcript_text, speaker_segments)
        all_entities['voice_biomarkers'] = voice_biomarkers
        
        # Extract ambient sounds (simulated)
        ambient_sounds = self._extract_ambient_sounds(transcript_text)
        all_entities['ambient_sounds'] = ambient_sounds
        
        return all_entities
    
    def _extract_basic_medical_entities(self, doc: Doc) -> Dict[str, List[ComprehensiveEntity]]:
        """Extract basic medical entities (symptoms, medications, etc.)"""
        entities = {
            'symptoms': [],
            'medications': [],
            'procedures': [],
            'diagnoses': [],
            'anatomy': []
        }
        
        # Use existing medical matchers and patterns
        # This would integrate with the original MedicalEntityExtractor
        for ent in doc.ents:
            if ent.label_ in ["SYMPTOM", "CONDITION"]:
                entity = ComprehensiveEntity(
                    text=ent.text,
                    entity_type=ComprehensiveEntityType.SYMPTOM,
                    confidence=0.8,
                    start_pos=ent.start_char,
                    end_pos=ent.end_char,
                    normalized_form=ent.text.lower(),
                    context=self._get_context(doc, ent)
                )
                entities['symptoms'].append(entity)
        
        return entities
    
    def _extract_vital_signs(self, doc: Doc, text: str) -> List[ComprehensiveEntity]:
        """Extract vital signs with structured data"""
        vital_signs_entities = []
        
        # Extract using patterns
        for vs_type, pattern in self.patterns['vital_signs'].items():
            matches = pattern.finditer(text)
            for match in matches:
                if vs_type == 'blood_pressure':
                    systolic, diastolic = match.groups()
                    value = f"{systolic}/{diastolic}"
                else:
                    value = match.group(1)
                
                entity = ComprehensiveEntity(
                    text=match.group(0),
                    entity_type=ComprehensiveEntityType.VITAL_SIGN,
                    confidence=0.95,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    normalized_form=f"{vs_type}: {value}",
                    context=self._get_text_context(text, match.start(), match.end()),
                    metadata={
                        'vital_sign_type': vs_type,
                        'value': value,
                        'unit': self._get_vital_sign_unit(vs_type)
                    }
                )
                vital_signs_entities.append(entity)
        
        return vital_signs_entities
    
    def _extract_test_results(self, doc: Doc, text: str) -> List[ComprehensiveEntity]:
        """Extract laboratory test results"""
        test_entities = []
        
        # Extract using test results matcher
        matches = self.test_results_matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            
            # Look for numerical values near test mentions
            test_value = self._find_associated_value(text, span.start_char, span.end_char)
            
            entity = ComprehensiveEntity(
                text=span.text,
                entity_type=ComprehensiveEntityType.TEST_RESULT,
                confidence=0.85,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'test_type': span.text.lower(),
                    'value': test_value,
                    'requires_follow_up': self._assess_test_significance(span.text, test_value)
                }
            )
            test_entities.append(entity)
        
        return test_entities
    
    def _extract_healthcare_costs(self, doc: Doc, text: str) -> List[ComprehensiveEntity]:
        """Extract healthcare cost mentions"""
        cost_entities = []
        
        matches = self.costs_matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            
            # Extract amount
            amount = self._extract_monetary_amount(span.text)
            
            entity = ComprehensiveEntity(
                text=span.text,
                entity_type=ComprehensiveEntityType.COST,
                confidence=0.9,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=f"cost: {amount}",
                context=self._get_context(doc, span),
                metadata={
                    'amount': amount,
                    'currency': 'USD',
                    'cost_type': self._categorize_healthcare_cost(span.text)
                }
            )
            cost_entities.append(entity)
        
        return cost_entities
    
    def _extract_technology_mentions(self, doc: Doc) -> List[ComprehensiveEntity]:
        """Extract healthcare technology mentions"""
        tech_entities = []
        
        matches = self.technology_matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            
            entity = ComprehensiveEntity(
                text=span.text,
                entity_type=ComprehensiveEntityType.TECHNOLOGY,
                confidence=0.85,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'technology_type': self._categorize_technology(span.text),
                    'usage_context': self._get_technology_usage_context(span.text)
                }
            )
            tech_entities.append(entity)
        
        return tech_entities
    
    def _extract_social_determinants(self, doc: Doc) -> List[ComprehensiveEntity]:
        """Extract social determinants of health"""
        social_entities = []
        
        matches = self.social_determinants_matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            
            entity = ComprehensiveEntity(
                text=span.text,
                entity_type=ComprehensiveEntityType.SOCIAL_DETERMINANT,
                confidence=0.8,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                metadata={
                    'determinant_type': self._categorize_social_determinant(span.text),
                    'impact_assessment': self._assess_social_impact(span.text)
                }
            )
            social_entities.append(entity)
        
        return social_entities
    
    def _extract_emotional_indicators(self, doc: Doc, 
                                    speaker_segments: List[Dict] = None) -> List[ComprehensiveEntity]:
        """Extract emotional and psychological indicators"""
        emotion_entities = []
        
        matches = self.emotion_matcher(doc)
        for match_id, start, end in matches:
            span = doc[start:end]
            
            # Determine speaker if segments provided
            speaker = self._identify_speaker(span.start_char, speaker_segments) if speaker_segments else None
            
            entity = ComprehensiveEntity(
                text=span.text,
                entity_type=ComprehensiveEntityType.EMOTION,
                confidence=0.75,
                start_pos=span.start_char,
                end_pos=span.end_char,
                normalized_form=span.text.lower(),
                context=self._get_context(doc, span),
                speaker=speaker,
                metadata={
                    'emotion_type': span.text.lower(),
                    'intensity': self._assess_emotion_intensity(span.text),
                    'valence': self._assess_emotion_valence(span.text)
                }
            )
            emotion_entities.append(entity)
        
        return emotion_entities
    
    def _extract_voice_biomarkers(self, text: str, 
                                 speaker_segments: List[Dict] = None) -> List[VoiceBiomarker]:
        """Extract voice biomarkers (simulated - would require audio analysis)"""
        # This is a placeholder for actual voice analysis
        # In a real implementation, this would analyze audio features
        voice_biomarkers = []
        
        # Simulate voice biomarker detection based on text patterns
        stress_indicators = re.findall(r'(uh+|um+|er+)', text.lower())
        if stress_indicators:
            biomarker = VoiceBiomarker(
                biomarker_type="speech_hesitation",
                confidence_level=0.7,
                timestamp="00:00:00",  # Would be actual timestamp
                related_symptoms=["anxiety", "stress"],
                context="Speech hesitation patterns detected",
                clinical_significance="May indicate patient anxiety or uncertainty"
            )
            voice_biomarkers.append(biomarker)
        
        return voice_biomarkers
    
    def _extract_ambient_sounds(self, text: str) -> List[AmbientSound]:
        """Extract ambient sound analysis (simulated)"""
        # This is a placeholder for actual audio analysis
        ambient_sounds = []
        
        # Simulate ambient sound detection
        sound_patterns = {
            'coughing': re.compile(r'\*cough\*|\bcough\w*\b', re.IGNORECASE),
            'background_noise': re.compile(r'background|noise|static|interference', re.IGNORECASE),
            'medical_equipment': re.compile(r'beeping|monitor|alarm|ventilator', re.IGNORECASE)
        }
        
        for sound_type, pattern in sound_patterns.items():
            matches = pattern.finditer(text)
            for match in matches:
                sound = AmbientSound(
                    sound_type=sound_type,
                    intensity="moderate",  # Would be calculated from audio
                    duration="2s",  # Would be calculated from audio
                    timestamp="00:00:00",  # Would be actual timestamp
                    context=match.group(0),
                    clinical_relevance=self._assess_sound_clinical_relevance(sound_type)
                )
                ambient_sounds.append(sound)
        
        return ambient_sounds
    
    # Helper methods
    def _get_context(self, doc: Doc, span: Span, window: int = 5) -> str:
        """Get context around entity"""
        start = max(0, span.start - window)
        end = min(len(doc), span.end + window)
        return doc[start:end].text
    
    def _get_text_context(self, text: str, start: int, end: int, window: int = 50) -> str:
        """Get text context around position"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    def _get_vital_sign_unit(self, vs_type: str) -> str:
        """Get appropriate unit for vital sign"""
        units = {
            'blood_pressure': 'mmHg',
            'heart_rate': 'bpm',
            'temperature': '°F',
            'respiratory_rate': '/min',
            'oxygen_saturation': '%'
        }
        return units.get(vs_type, '')
    
    def _find_associated_value(self, text: str, start: int, end: int) -> Optional[str]:
        """Find numerical value associated with test mention"""
        # Look for numbers within 20 characters
        context = text[max(0, start-20):min(len(text), end+20)]
        number_pattern = re.compile(r'\d+(?:\.\d+)?')
        match = number_pattern.search(context)
        return match.group(0) if match else None
    
    def _assess_test_significance(self, test_name: str, value: Optional[str]) -> bool:
        """Assess if test result requires follow-up"""
        # Simplified assessment - would be more sophisticated in practice
        if value and value.isdigit():
            if 'glucose' in test_name.lower() and int(value) > 126:
                return True
            if 'cholesterol' in test_name.lower() and int(value) > 200:
                return True
        return False
    
    def _extract_monetary_amount(self, text: str) -> Optional[str]:
        """Extract monetary amount from text"""
        amount_pattern = re.compile(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)')
        match = amount_pattern.search(text)
        return match.group(1) if match else None
    
    def _categorize_healthcare_cost(self, text: str) -> str:
        """Categorize type of healthcare cost"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['consultation', 'visit', 'appointment']):
            return 'consultation'
        elif any(word in text_lower for word in ['medication', 'drug', 'prescription']):
            return 'medication'
        elif any(word in text_lower for word in ['test', 'lab', 'blood']):
            return 'laboratory'
        elif any(word in text_lower for word in ['scan', 'x-ray', 'imaging']):
            return 'imaging'
        else:
            return 'other'
    
    def _categorize_technology(self, text: str) -> str:
        """Categorize healthcare technology"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['telemedicine', 'telehealth', 'video']):
            return 'telemedicine'
        elif any(word in text_lower for word in ['portal', 'app', 'mobile']):
            return 'digital_health'
        elif any(word in text_lower for word in ['monitor', 'device', 'wearable']):
            return 'monitoring_device'
        elif any(word in text_lower for word in ['ehr', 'emr', 'record']):
            return 'health_records'
        else:
            return 'other'
    
    def _get_technology_usage_context(self, text: str) -> str:
        """Get context of technology usage"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['difficult', 'problem', 'issue']):
            return 'problematic'
        elif any(word in text_lower for word in ['helpful', 'useful', 'convenient']):
            return 'beneficial'
        else:
            return 'neutral'
    
    def _categorize_social_determinant(self, text: str) -> str:
        """Categorize social determinant of health"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['housing', 'homeless', 'home']):
            return 'housing'
        elif any(word in text_lower for word in ['food', 'nutrition', 'hungry']):
            return 'food_security'
        elif any(word in text_lower for word in ['transport', 'travel', 'drive']):
            return 'transportation'
        elif any(word in text_lower for word in ['job', 'work', 'employ', 'income']):
            return 'employment'
        elif any(word in text_lower for word in ['education', 'school', 'college']):
            return 'education'
        elif any(word in text_lower for word in ['family', 'support', 'social']):
            return 'social_support'
        elif any(word in text_lower for word in ['insurance', 'coverage', 'pay']):
            return 'healthcare_access'
        else:
            return 'other'
    
    def _assess_social_impact(self, text: str) -> str:
        """Assess impact of social determinant"""
        text_lower = text.lower()
        negative_indicators = ['lack', 'no', 'without', 'unable', 'difficult', 'problem']
        if any(indicator in text_lower for indicator in negative_indicators):
            return 'negative'
        else:
            return 'neutral'
    
    def _identify_speaker(self, position: int, speaker_segments: List[Dict]) -> Optional[str]:
        """Identify speaker at given text position"""
        if not speaker_segments:
            return None
        
        for segment in speaker_segments:
            if segment.get('start_pos', 0) <= position <= segment.get('end_pos', float('inf')):
                return segment.get('speaker')
        
        return None
    
    def _assess_emotion_intensity(self, emotion_text: str) -> str:
        """Assess intensity of emotion"""
        text_lower = emotion_text.lower()
        high_intensity = ['very', 'extremely', 'really', 'so', 'terribly']
        if any(modifier in text_lower for modifier in high_intensity):
            return 'high'
        else:
            return 'moderate'
    
    def _assess_emotion_valence(self, emotion_text: str) -> str:
        """Assess emotional valence (positive/negative)"""
        text_lower = emotion_text.lower()
        positive_emotions = ['happy', 'hopeful', 'optimistic', 'calm', 'relaxed', 'excited']
        negative_emotions = ['anxious', 'worried', 'depressed', 'sad', 'frustrated', 'angry', 'fearful']
        
        if any(emotion in text_lower for emotion in positive_emotions):
            return 'positive'
        elif any(emotion in text_lower for emotion in negative_emotions):
            return 'negative'
        else:
            return 'neutral'
    
    def _assess_sound_clinical_relevance(self, sound_type: str) -> str:
        """Assess clinical relevance of ambient sound"""
        relevance_map = {
            'coughing': 'High - may indicate respiratory symptoms',
            'background_noise': 'Low - environmental factor',
            'medical_equipment': 'Medium - indicates clinical setting'
        }
        return relevance_map.get(sound_type, 'Unknown')

class ComprehensiveSchemaProcessor:
    """Main processor for comprehensive medical schema"""
    
    def __init__(self):
        self.entity_extractor = ComprehensiveEntityExtractor()
        self.schema_template = COMPREHENSIVE_MEDICAL_SCHEMA.copy()
    
    def process_comprehensive_transcript(self, transcript_text: str, 
                                       metadata: Dict[str, Any] = None,
                                       speaker_segments: List[Dict] = None) -> Dict[str, Any]:
        """Process transcript using comprehensive medical schema"""
        
        # Initialize comprehensive report
        comprehensive_report = self.schema_template.copy()
        
        # Extract all entities
        all_entities = self.entity_extractor.extract_comprehensive_entities(
            transcript_text, speaker_segments
        )
        
        # Populate schema sections
        comprehensive_report = self._populate_metadata(comprehensive_report, metadata)
        comprehensive_report = self._populate_transcription(comprehensive_report, transcript_text, speaker_segments)
        comprehensive_report = self._populate_patient_information(comprehensive_report, all_entities, transcript_text)
        comprehensive_report = self._populate_clinical_data(comprehensive_report, all_entities, transcript_text)
        comprehensive_report = self._populate_interaction_analysis(comprehensive_report, all_entities, transcript_text)
        comprehensive_report = self._populate_care_quality_assessment(comprehensive_report, transcript_text)
        comprehensive_report = self._populate_treatment_and_follow_up(comprehensive_report, all_entities, transcript_text)
        comprehensive_report = self._populate_specialized_considerations(comprehensive_report, all_entities, transcript_text)
        comprehensive_report = self._populate_telemedicine_specifics(comprehensive_report, metadata, all_entities)
        comprehensive_report = self._populate_overall_assessment(comprehensive_report, all_entities, transcript_text)
        
        return comprehensive_report
    
    def _populate_metadata(self, report: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Populate metadata section"""
        if metadata:
            report['metadata'].update({
                'location': metadata.get('location', ''),
                'setting': metadata.get('setting', 'telemedicine'),
                'duration': metadata.get('duration', ''),
                'visit_type': metadata.get('visit_type', ''),
                'technology_used': metadata.get('technology_used', 'video conference'),
                'language_of_consultation': metadata.get('language', 'English')
            })
        return report
    
    def _populate_transcription(self, report: Dict[str, Any], text: str, 
                              speaker_segments: List[Dict] = None) -> Dict[str, Any]:
        """Populate transcription section"""
        if speaker_segments:
            report['transcription']['segments'] = speaker_segments
        else:
            # Create basic segments
            report['transcription']['segments'] = [{
                'speaker': 'unknown',
                'text': text,
                'timestamp': '00:00:00'
            }]
        return report
    
    def _populate_patient_information(self, report: Dict[str, Any], 
                                    entities: Dict[str, List], text: str) -> Dict[str, Any]:
        """Populate patient information section"""
        
        # Extract vital signs
        if 'vital_signs' in entities:
            vital_signs_data = {}
            for vs_entity in entities['vital_signs']:
                vs_type = vs_entity.metadata.get('vital_sign_type')
                if vs_type:
                    vital_signs_data[vs_type] = vs_entity.metadata.get('value')
            report['patient_information']['current_status']['vital_signs'] = vital_signs_data
        
        # Extract symptoms
        if 'symptoms' in entities:
            symptoms_data = []
            for symptom in entities['symptoms']:
                symptom_data = {
                    'symptom': symptom.text,
                    'severity': symptom.severity or 'moderate',
                    'timeline': self._extract_timeline_from_context(symptom.context),
                    'progression': '',
                    'triggers': '',
                    'alleviating_factors': ''
                }
                symptoms_data.append(symptom_data)
            report['patient_information']['current_status']['symptoms'] = symptoms_data
        
        # Extract demographics (if mentioned - be careful with PHI)
        demographics = self._extract_demographics_safely(text)
        report['patient_information']['demographics'].update(demographics)
        
        return report
    
    def _populate_clinical_data(self, report: Dict[str, Any], 
                              entities: Dict[str, List], text: str) -> Dict[str, Any]:
        """Populate clinical data section"""
        
        # Extract medications
        if 'medications' in entities:
            medications_data = []
            for med in entities['medications']:
                med_data = {
                    'name': med.text,
                    'dosage': self._extract_dosage_from_context(med.context),
                    'frequency': self._extract_frequency_from_context(med.context),
                    'context_of_use': med.context,
                    'timestamp': med.timestamp or datetime.now().isoformat()
                }
                medications_data.append(med_data)
            report['clinical_data']['medications'] = medications_data
        
        # Extract test results
        if 'test_results' in entities:
            test_results_data = []
            for test in entities['test_results']:
                test_data = {
                    'test_name': test.text,
                    'result': test.metadata.get('value', ''),
                    'clinical_significance': test.metadata.get('clinical_significance', ''),
                    'follow_up_recommended': test.metadata.get('requires_follow_up', False)
                }
                test_results_data.append(test_data)
            report['clinical_data']['test_results'] = test_results_data
        
        # Extract procedures
        if 'procedures' in entities:
            procedures_data = []
            for proc in entities['procedures']:
                proc_data = {
                    'procedure_name': proc.text,
                    'context': proc.context,
                    'timestamp': proc.timestamp or datetime.now().isoformat()
                }
                procedures_data.append(proc_data)
            report['clinical_data']['procedures'] = procedures_data
        
        return report
    
    def _populate_interaction_analysis(self, report: Dict[str, Any], 
                                     entities: Dict[str, List], text: str) -> Dict[str, Any]:
        """Populate interaction analysis section"""
        
        # Extract emotional/psychological data
        if 'emotions' in entities:
            emotional_data = []
            for emotion in entities['emotions']:
                emotion_data = {
                    'speaker': emotion.speaker or 'unknown',
                    'emotion': emotion.metadata.get('emotion_type', emotion.text),
                    'intensity': emotion.metadata.get('intensity', 'moderate'),
                    'timestamp': emotion.timestamp or '00:00:00',
                    'context': emotion.context
                }
                emotional_data.append(emotion_data)
            report['interaction_analysis']['emotional_psychological'] = emotional_data
        
        # Extract voice biomarkers
        if 'voice_biomarkers' in entities:
            report['interaction_analysis']['voice_biomarkers'] = [
                asdict(vb) for vb in entities['voice_biomarkers']
            ]
        
        # Extract ambient sounds
        if 'ambient_sounds' in entities:
            report['interaction_analysis']['ambient_sounds'] = [
                asdict(sound) for sound in entities['ambient_sounds']
            ]
        
        # Analyze keywords and topics
        keywords = self._extract_keywords(text)
        topics = self._analyze_topics(text)
        report['interaction_analysis']['keyword_topic_analysis'] = {
            'keywords': keywords,
            'main_topics': topics
        }
        
        return report
    
    def _populate_care_quality_assessment(self, report: Dict[str, Any], text: str) -> Dict[str, Any]:
        """Populate care quality assessment section"""
        
        # Assess comprehensiveness
        comprehensiveness_score = self._assess_comprehensiveness(text)
        report['care_quality_assessment']['comprehensiveness'] = comprehensiveness_score
        
        # Assess cultural competence
        cultural_indicators = self._assess_cultural_competence(text)
        report['care_quality_assessment']['cultural_competence'] = cultural_indicators
        
        # Assess patient satisfaction indicators
        satisfaction_indicators = self._assess_patient_satisfaction(text)
        report['care_quality_assessment']['patient_satisfaction_indicators'] = satisfaction_indicators
        
        return report
    
    def _populate_treatment_and_follow_up(self, report: Dict[str, Any], 
                                        entities: Dict[str, List], text: str) -> Dict[str, Any]:
        """Populate treatment and follow-up section"""
        
        # Extract follow-up actions
        follow_up_actions = self._extract_follow_up_actions(text)
        report['treatment_and_follow_up']['follow_up_actions'] = follow_up_actions
        
        # Extract care plan
        care_plan = self._extract_care_plan(text)
        report['treatment_and_follow_up']['care_plan'] = care_plan
        
        # Extract prescription details
        if 'medications' in entities:
            prescriptions = []
            for med in entities['medications']:
                prescription = {
                    'medication_name': med.text,
                    'dosage': self._extract_dosage_from_context(med.context),
                    'frequency': self._extract_frequency_from_context(med.context),
                    'special_instructions': med.context
                }
                prescriptions.append(prescription)
            report['treatment_and_follow_up']['prescription_details'] = prescriptions
        
        return report
    
    def _populate_specialized_considerations(self, report: Dict[str, Any], 
                                           entities: Dict[str, List], text: str) -> Dict[str, Any]:
        """Populate specialized considerations section"""
        
        # Pain assessment
        pain_data = self._extract_pain_assessment(text)
        if pain_data:
            report['specialized_considerations']['pain_assessment'] = pain_data
        
        # Mental health assessment
        mental_health_data = self._extract_mental_health_assessment(text, entities.get('emotions', []))
        if mental_health_data:
            report['specialized_considerations']['mental_health'] = mental_health_data
        
        # Nutritional assessment
        nutrition_data = self._extract_nutritional_assessment(text)
        if nutrition_data:
            report['specialized_considerations']['nutritional_assessment'] = nutrition_data
        
        return report
    
    def _populate_telemedicine_specifics(self, report: Dict[str, Any], 
                                       metadata: Dict[str, Any], 
                                       entities: Dict[str, List]) -> Dict[str, Any]:
        """Populate telemedicine-specific section"""
        
        # Extract technology-related information
        if 'technology' in entities:
            tech_mentions = entities['technology']
            
            # Assess technical difficulties
            tech_difficulties = []
            for tech in tech_mentions:
                if tech.metadata.get('usage_context') == 'problematic':
                    tech_difficulties.append(tech.text)
            
            report['telemedicine_specifics']['technical_difficulties_impact'] = ', '.join(tech_difficulties)
            
            # Assess patient comfort with technology
            comfort_level = self._assess_tech_comfort(tech_mentions)
            report['telemedicine_specifics']['patient_comfort_with_technology'] = comfort_level
        
        # Physical exam limitations
        physical_exam_limitations = self._assess_physical_exam_limitations(report)
        report['telemedicine_specifics']['physical_exam_limitations'] = physical_exam_limitations
        
        return report
    
    def _populate_overall_assessment(self, report: Dict[str, Any], 
                                   entities: Dict[str, List], text: str) -> Dict[str, Any]:
        """Populate overall assessment section"""
        
        # Generate key findings
        key_findings = self._generate_key_findings(entities, text)
        report['overall_assessment']['key_findings'] = key_findings
        
        # Generate follow-up recommendations
        follow_up_recommendations = self._generate_follow_up_recommendations(entities, text)
        report['overall_assessment']['follow_up_recommendations'] = follow_up_recommendations
        
        # Generate care plan summary
        care_plan_summary = self._generate_care_plan_summary(entities, text)
        report['overall_assessment']['care_plan_summary'] = care_plan_summary
        
        return report
    
    # Helper methods for data extraction and analysis
    def _extract_timeline_from_context(self, context: str) -> str:
        """Extract timeline information from context"""
        if not context:
            return ''
        
        timeline_pattern = re.compile(r'(\d+)\s*(hours?|days?|weeks?|months?|years?)\s*(ago|before)', re.IGNORECASE)
        match = timeline_pattern.search(context)
        return match.group(0) if match else ''
    
    def _extract_dosage_from_context(self, context: str) -> str:
        """Extract medication dosage from context"""
        if not context:
            return ''
        
        dosage_pattern = re.compile(r'(\d+(?:\.\d+)?)\s*(mg|g|ml|units?)', re.IGNORECASE)
        match = dosage_pattern.search(context)
        return match.group(0) if match else ''
    
    def _extract_frequency_from_context(self, context: str) -> str:
        """Extract medication frequency from context"""
        if not context:
            return ''
        
        frequency_patterns = [
            r'once\s+(?:a\s+)?day|daily|q\.?d\.?',
            r'twice\s+(?:a\s+)?day|b\.?i\.?d\.?',
            r'three\s+times\s+(?:a\s+)?day|t\.?i\.?d\.?',
            r'four\s+times\s+(?:a\s+)?day|q\.?i\.?d\.?',
            r'every\s+\d+\s+hours?',
            r'as\s+needed|p\.?r\.?n\.?'
        ]
        
        for pattern in frequency_patterns:
            match = re.search(pattern, context, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return ''
    
    def _extract_demographics_safely(self, text: str) -> Dict[str, Any]:
        """Extract demographics while avoiding PHI"""
        demographics = {}
        
        # Only extract general demographic information that's not PHI
        age_pattern = re.compile(r'(\d{1,2})\s*year\s*old', re.IGNORECASE)
        age_match = age_pattern.search(text)
        if age_match:
            age = int(age_match.group(1))
            if 18 <= age <= 89:  # HIPAA safe harbor rule for ages
                demographics['age'] = str(age)
        
        # Gender (if explicitly mentioned in medical context)
        gender_pattern = re.compile(r'\b(male|female|man|woman)\b', re.IGNORECASE)
        gender_match = gender_pattern.search(text)
        if gender_match:
            demographics['gender'] = gender_match.group(1).lower()
        
        return demographics
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from text"""
        # Simple keyword extraction - could be enhanced with NLP
        medical_keywords = []
        doc = self.entity_extractor.nlp(text)
        
        for token in doc:
            if (token.pos_ in ['NOUN', 'ADJ'] and 
                len(token.text) > 3 and 
                not token.is_stop and 
                not token.is_punct):
                medical_keywords.append(token.lemma_.lower())
        
        # Return most frequent keywords
        from collections import Counter
        keyword_counts = Counter(medical_keywords)
        return [kw for kw, count in keyword_counts.most_common(10)]
    
    def _analyze_topics(self, text: str) -> List[Dict[str, str]]:
        """Analyze main topics in conversation"""
        # Simple topic analysis - could be enhanced with topic modeling
        topics = []
        
        medical_topics = {
            'symptoms': ['pain', 'symptom', 'feel', 'hurt', 'ache'],
            'treatment': ['treatment', 'therapy', 'medication', 'drug'],
            'diagnosis': ['diagnosis', 'condition', 'disease', 'disorder'],
            'follow_up': ['follow', 'next', 'appointment', 'return']
        }
        
        text_lower = text.lower()
        for topic, keywords in medical_topics.items():
            if any(keyword in text_lower for keyword in keywords):
                topics.append({
                    'topic': topic,
                    'importance': 'high' if len([kw for kw in keywords if kw in text_lower]) > 2 else 'medium'
                })
        
        return topics
    
    def _assess_comprehensiveness(self, text: str) -> str:
        """Assess comprehensiveness of consultation"""
        required_elements = [
            'history', 'symptoms', 'examination', 'assessment', 'plan'
        ]
        
        text_lower = text.lower()
        covered_elements = [elem for elem in required_elements if elem in text_lower]
        
        coverage_ratio = len(covered_elements) / len(required_elements)
        
        if coverage_ratio >= 0.8:
            return 'comprehensive'
        elif coverage_ratio >= 0.6:
            return 'adequate'
        else:
            return 'limited'
    
    def _assess_cultural_competence(self, text: str) -> Dict[str, str]:
        """Assess cultural competence indicators"""
        cultural_indicators = {}
        
        text_lower = text.lower()
        
        # Language considerations
        if any(term in text_lower for term in ['interpreter', 'translate', 'language']):
            cultural_indicators['language_considerations'] = 'addressed'
        else:
            cultural_indicators['language_considerations'] = 'not_mentioned'
        
        # Cultural sensitivities
        if any(term in text_lower for term in ['culture', 'belief', 'tradition', 'custom']):
            cultural_indicators['cultural_sensitivities_addressed'] = 'yes'
        else:
            cultural_indicators['cultural_sensitivities_addressed'] = 'not_mentioned'
        
        return cultural_indicators
    
    def _assess_patient_satisfaction(self, text: str) -> Dict[str, str]:
        """Assess patient satisfaction indicators"""
        satisfaction_indicators = {}
        
        text_lower = text.lower()
        
        # Positive verbal cues
        positive_cues = ['thank', 'helpful', 'understand', 'clear', 'good', 'satisfied']
        if any(cue in text_lower for cue in positive_cues):
            satisfaction_indicators['verbal_cues'] = 'positive'
        
        # Expressed concerns
        concern_words = ['concern', 'worry', 'confused', 'unclear', 'problem']
        if any(concern in text_lower for concern in concern_words):
            satisfaction_indicators['expressed_concerns'] = 'yes'
        else:
            satisfaction_indicators['expressed_concerns'] = 'none_identified'
        
        return satisfaction_indicators
    
    def _extract_follow_up_actions(self, text: str) -> Dict[str, str]:
        """Extract follow-up actions from text"""
        follow_up = {}
        
        # Scheduled appointments
        if re.search(r'follow.{0,20}(week|month|day)', text, re.IGNORECASE):
            follow_up['scheduled_appointments'] = 'mentioned'
        
        # Prescribed tests
        if any(test in text.lower() for test in ['test', 'lab', 'blood', 'scan', 'x-ray']):
            follow_up['prescribed_tests'] = 'mentioned'
        
        # Referrals
        if any(ref in text.lower() for ref in ['refer', 'specialist', 'see']):
            follow_up['referrals'] = 'mentioned'
        
        return follow_up
    
    def _extract_care_plan(self, text: str) -> Dict[str, str]:
        """Extract care plan information"""
        care_plan = {}
        
        # Short-term goals
        if re.search(r'(short.{0,10}term|immediate|next.{0,10}week)', text, re.IGNORECASE):
            care_plan['short_term_goals'] = 'mentioned'
        
        # Long-term goals
        if re.search(r'(long.{0,10}term|future|ongoing)', text, re.IGNORECASE):
            care_plan['long_term_goals'] = 'mentioned'
        
        return care_plan
    
    def _extract_pain_assessment(self, text: str) -> Optional[Dict[str, str]]:
        """Extract pain assessment information"""
        if 'pain' not in text.lower():
            return None
        
        pain_data = {}
        
        # Pain scale
        scale_pattern = re.compile(r'(\d{1,2})\s*(?:out of|/)\s*10', re.IGNORECASE)
        scale_match = scale_pattern.search(text)
        if scale_match:
            pain_data['pain_scale_used'] = f"{scale_match.group(1)}/10"
        
        # Pain description
        pain_descriptors = ['sharp', 'dull', 'burning', 'aching', 'stabbing', 'throbbing']
        for descriptor in pain_descriptors:
            if descriptor in text.lower():
                pain_data['pain_description'] = descriptor
                break
        
        return pain_data if pain_data else None
    
    def _extract_mental_health_assessment(self, text: str, emotions: List) -> Optional[Dict[str, str]]:
        """Extract mental health assessment information"""
        mental_health = {}
        
        # Mood assessment
        if emotions:
            mood_emotions = [e for e in emotions if e.metadata.get('emotion_type') in 
                           ['anxious', 'depressed', 'sad', 'worried', 'stressed']]
            if mood_emotions:
                mental_health['mood_assessment'] = 'negative_indicators_present'
        
        # Anxiety screening
        if any(term in text.lower() for term in ['anxiety', 'anxious', 'panic', 'worry']):
            mental_health['anxiety_screening'] = 'positive_indicators'
        
        return mental_health if mental_health else None
    
    def _extract_nutritional_assessment(self, text: str) -> Optional[Dict[str, str]]:
        """Extract nutritional assessment information"""
        if not any(term in text.lower() for term in ['diet', 'food', 'nutrition', 'eat']):
            return None
        
        nutrition_data = {}
        
        # Dietary restrictions
        if any(term in text.lower() for term in ['allergic', 'restriction', 'avoid', 'cannot eat']):
            nutrition_data['dietary_restrictions'] = 'mentioned'
        
        # Nutritional recommendations
        if any(term in text.lower() for term in ['recommend', 'should eat', 'nutrition']):
            nutrition_data['recommended_dietary_changes'] = 'provided'
        
        return nutrition_data if nutrition_data else None
    
    def _assess_tech_comfort(self, tech_entities: List) -> str:
        """Assess patient comfort with technology"""
        if not tech_entities:
            return 'not_assessed'
        
        problematic_mentions = [t for t in tech_entities if t.metadata.get('usage_context') == 'problematic']
        beneficial_mentions = [t for t in tech_entities if t.metadata.get('usage_context') == 'beneficial']
        
        if len(problematic_mentions) > len(beneficial_mentions):
            return 'low_comfort'
        elif len(beneficial_mentions) > len(problematic_mentions):
            return 'high_comfort'
        else:
            return 'moderate_comfort'
    
    def _assess_physical_exam_limitations(self, report: Dict[str, Any]) -> str:
        """Assess physical examination limitations in telemedicine"""
        # Check if vital signs were taken
        vital_signs = report.get('patient_information', {}).get('current_status', {}).get('vital_signs', {})
        
        if not vital_signs:
            return 'significant_limitations_no_vital_signs'
        elif len(vital_signs) < 3:
            return 'moderate_limitations_limited_vital_signs'
        else:
            return 'minimal_limitations_vital_signs_available'
    
    def _generate_key_findings(self, entities: Dict[str, List], text: str) -> str:
        """Generate summary of key findings"""
        findings = []
        
        # Symptom findings
        if 'symptoms' in entities and entities['symptoms']:
            findings.append(f"Patient reports {len(entities['symptoms'])} symptoms")
        
        # Medication findings
        if 'medications' in entities and entities['medications']:
            findings.append(f"Currently taking {len(entities['medications'])} medications")
        
        # Test findings
        if 'test_results' in entities and entities['test_results']:
            findings.append(f"{len(entities['test_results'])} test results discussed")
        
        # Technology findings
        if 'technology' in entities and entities['technology']:
            findings.append("Telemedicine consultation conducted successfully")
        
        return '; '.join(findings) if findings else 'No specific findings documented'
    
    def _generate_follow_up_recommendations(self, entities: Dict[str, List], text: str) -> str:
        """Generate follow-up recommendations"""
        recommendations = []
        
        # Check for high-risk test results
        if 'test_results' in entities:
            high_risk_tests = [t for t in entities['test_results'] 
                             if t.metadata.get('requires_follow_up', False)]
            if high_risk_tests:
                recommendations.append("Follow up on abnormal test results")
        
        # Check for unresolved symptoms
        if 'symptoms' in entities and len(entities['symptoms']) > 2:
            recommendations.append("Monitor symptom progression")
        
        # Standard telemedicine follow-up
        if 'technology' in entities:
            recommendations.append("Consider in-person evaluation if symptoms persist")
        
        return '; '.join(recommendations) if recommendations else 'Routine follow-up as scheduled'
    
    def _generate_care_plan_summary(self, entities: Dict[str, List], text: str) -> str:
        """Generate care plan summary"""
        plan_elements = []
        
        # Medication management
        if 'medications' in entities and entities['medications']:
            plan_elements.append("Continue current medication regimen")
        
        # Monitoring
        if 'vital_signs' in entities and entities['vital_signs']:
            plan_elements.append("Monitor vital signs")
        
        # Lifestyle modifications
        if any(term in text.lower() for term in ['diet', 'exercise', 'lifestyle']):
            plan_elements.append("Implement lifestyle modifications")
        
        return '; '.join(plan_elements) if plan_elements else 'Standard care plan to be developed'

# Example usage
if __name__ == "__main__":
    # Initialize comprehensive processor
    processor = ComprehensiveSchemaProcessor()
    
    # Example comprehensive medical transcript
    sample_transcript = """
    Patient presents for telemedicine consultation complaining of chest pain for the past 2 hours.
    
    History: 45-year-old male reports sharp chest pain radiating to left arm. Associated with shortness 
    of breath and nausea. No previous cardiac history. Patient appears anxious about symptoms.
    
    Current medications: Lisinopril 5mg daily for hypertension, metformin 500mg twice daily for diabetes.
    
    Vital signs: BP 140/90, HR 95, oxygen saturation 98% on room air. Temperature 98.6F.
    
    Assessment: Chest pain, rule out acute coronary syndrome. Patient reports good understanding of 
    treatment plan. Some technical difficulties with video connection noted.
    
    Plan: EKG ordered, cardiac enzymes, start aspirin 325mg. Follow up in 24 hours or sooner if 
    symptoms worsen. Patient comfortable with technology overall.
    
    Patient expressed appreciation for the consultation and felt his concerns were addressed.
    """
    
    # Process with comprehensive schema
    comprehensive_result = processor.process_comprehensive_transcript(
        sample_transcript,
        metadata={
            'setting': 'telemedicine',
            'technology_used': 'video conference',
            'duration': '30 minutes'
        }
    )
    
    # Print results
    print("Comprehensive Medical Transcript Analysis:")
    print(json.dumps(comprehensive_result, indent=2, default=str))