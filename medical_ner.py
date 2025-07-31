#!/usr/bin/env python3
"""
Medical Named Entity Recognition Module
Specialized NER for healthcare conversations with medical coding support
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
import json

logger = logging.getLogger(__name__)

@dataclass
class MedicalEntity:
    """Medical entity with coding information"""
    text: str
    entity_type: str
    confidence: float
    start_pos: int
    end_pos: int
    medical_code: Optional[str] = None
    code_system: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    context: Optional[str] = None

class MedicalNER:
    """Medical Named Entity Recognition with healthcare-specific focus"""
    
    def __init__(self):
        self.medical_patterns = self._load_medical_patterns()
        self.medication_patterns = self._load_medication_patterns()
        self.condition_patterns = self._load_condition_patterns()
        self.procedure_patterns = self._load_procedure_patterns()
        self.lab_patterns = self._load_lab_patterns()
        self.vital_patterns = self._load_vital_patterns()
    
    def extract_medical_entities(self, text: str) -> Dict[str, List[MedicalEntity]]:
        """
        Extract comprehensive medical entities from healthcare conversation
        
        Args:
            text: Input healthcare conversation text
            
        Returns:
            Dictionary of medical entity categories with extracted entities
        """
        try:
            entities = {
                'conditions': self._extract_conditions(text),
                'medications': self._extract_medications(text),
                'procedures': self._extract_procedures(text),
                'lab_values': self._extract_lab_values(text),
                'vital_signs': self._extract_vital_signs(text),
                'symptoms': self._extract_symptoms(text),
                'anatomy': self._extract_anatomy(text),
                'allergies': self._extract_allergies(text),
                'devices': self._extract_medical_devices(text),
                'temporal': self._extract_temporal_expressions(text)
            }
            
            # Post-process for medical coding
            entities = self._apply_medical_coding(entities)
            
            # Calculate confidence scores
            entities = self._calculate_confidence_scores(entities, text)
            
            total_entities = sum(len(entity_list) for entity_list in entities.values())
            logger.info(f"Extracted {total_entities} medical entities across {len(entities)} categories")
            
            return entities
            
        except Exception as e:
            logger.error(f"Medical entity extraction failed: {e}")
            return {}
    
    def _extract_conditions(self, text: str) -> List[MedicalEntity]:
        """Extract medical conditions with ICD-10 coding potential"""
        conditions = []
        
        # Common medical conditions patterns
        condition_patterns = [
            r'\b(diabetes|diabetic)\b',
            r'\b(hypertension|high blood pressure)\b',
            r'\b(asthma|asthmatic)\b',
            r'\b(depression|depressed)\b',
            r'\b(anxiety|anxious)\b',
            r'\b(arthritis|arthritic)\b',
            r'\b(cancer|carcinoma|tumor|malignancy)\b',
            r'\b(heart disease|cardiac|coronary)\b',
            r'\b(stroke|cerebrovascular)\b',
            r'\b(pneumonia|lung infection)\b',
            r'\b(migraine|headache)\b',
            r'\b(allergic reaction|allergy)\b',
            r'\b(infection|infectious)\b',
            r'\b(fracture|broken bone)\b',
            r'\b(chronic pain|pain)\b'
        ]
        
        for pattern in condition_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                condition = MedicalEntity(
                    text=match.group(),
                    entity_type='CONDITION',
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                )
                conditions.append(condition)
        
        return conditions
    
    def _extract_medications(self, text: str) -> List[MedicalEntity]:
        """Extract medications with RxNorm coding potential"""
        medications = []
        
        # Common medication patterns
        medication_patterns = [
            r'\b(aspirin|acetaminophen|ibuprofen)\b',
            r'\b(metformin|insulin|glipizide)\b',
            r'\b(lisinopril|amlodipine|metoprolol)\b',
            r'\b(albuterol|prednisone|inhaler)\b',
            r'\b(sertraline|fluoxetine|citalopram)\b',
            r'\b(atorvastatin|simvastatin|statin)\b',
            r'\b(warfarin|coumadin|blood thinner)\b',
            r'\b(antibiotic|amoxicillin|azithromycin)\b',
            r'\b\w+cillin\b',  # Penicillin family
            r'\b\w+pril\b',    # ACE inhibitors
            r'\b\w+olol\b',    # Beta blockers
            r'\b\w+statin\b'   # Statins
        ]
        
        # Dosage patterns
        dosage_pattern = r'(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|units?|tablets?|pills?)'
        
        for pattern in medication_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Look for dosage information nearby
                context_start = max(0, match.start() - 50)
                context_end = min(len(text), match.end() + 50)
                context_text = text[context_start:context_end]
                
                dosage_match = re.search(dosage_pattern, context_text, re.IGNORECASE)
                dosage_info = dosage_match.group() if dosage_match else None
                
                medication = MedicalEntity(
                    text=match.group(),
                    entity_type='MEDICATION',
                    confidence=0.85,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    description=dosage_info,
                    context=self._get_context(text, match.start(), match.end())
                )
                medications.append(medication)
        
        return medications
    
    def _extract_procedures(self, text: str) -> List[MedicalEntity]:
        """Extract medical procedures with CPT coding potential"""
        procedures = []
        
        procedure_patterns = [
            r'\b(surgery|surgical|operation)\b',
            r'\b(biopsy|endoscopy|colonoscopy)\b',
            r'\b(x-ray|CT scan|MRI|ultrasound)\b',
            r'\b(blood test|lab work|laboratory)\b',
            r'\b(injection|vaccination|immunization)\b',
            r'\b(physical exam|examination)\b',
            r'\b(consultation|follow-up|visit)\b',
            r'\b(therapy|treatment|rehabilitation)\b',
            r'\b(screening|test|diagnostic)\b'
        ]
        
        for pattern in procedure_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                procedure = MedicalEntity(
                    text=match.group(),
                    entity_type='PROCEDURE',
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                )
                procedures.append(procedure)
        
        return procedures
    
    def _extract_lab_values(self, text: str) -> List[MedicalEntity]:
        """Extract laboratory values and test results"""
        lab_values = []
        
        # Lab value patterns with units
        lab_patterns = [
            r'\b(glucose|blood sugar)\s*:?\s*(\d+(?:\.\d+)?)\s*(mg/dl|mmol/l)?\b',
            r'\b(cholesterol|ldl|hdl)\s*:?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?\b',
            r'\b(blood pressure|bp)\s*:?\s*(\d+/\d+)\s*(mmhg)?\b',
            r'\b(hemoglobin|hgb|hb)\s*:?\s*(\d+(?:\.\d+)?)\s*(g/dl)?\b',
            r'\b(white blood cell|wbc)\s*:?\s*(\d+(?:\.\d+)?)\s*(k/ul)?\b',
            r'\b(creatinine)\s*:?\s*(\d+(?:\.\d+)?)\s*(mg/dl)?\b',
            r'\b(temperature|temp)\s*:?\s*(\d+(?:\.\d+)?)\s*(f|c|fahrenheit|celsius)?\b'
        ]
        
        for pattern in lab_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                lab_value = MedicalEntity(
                    text=match.group(),
                    entity_type='LAB_VALUE',
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    description=self._interpret_lab_value(match.group()),
                    context=self._get_context(text, match.start(), match.end())
                )
                lab_values.append(lab_value)
        
        return lab_values
    
    def _extract_vital_signs(self, text: str) -> List[MedicalEntity]:
        """Extract vital signs measurements"""
        vitals = []
        
        vital_patterns = [
            r'\b(heart rate|pulse)\s*:?\s*(\d+)\s*(bpm)?\b',
            r'\b(respiratory rate|breathing)\s*:?\s*(\d+)\s*(per minute)?\b',
            r'\b(oxygen saturation|o2 sat|spo2)\s*:?\s*(\d+)\s*%?\b',
            r'\b(weight)\s*:?\s*(\d+(?:\.\d+)?)\s*(lbs?|kg|pounds?)?\b',
            r'\b(height)\s*:?\s*(\d+(?:\'\d+\"?)?|\d+(?:\.\d+)?)\s*(ft|cm|inches?)?\b'
        ]
        
        for pattern in vital_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                vital = MedicalEntity(
                    text=match.group(),
                    entity_type='VITAL_SIGN',
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                )
                vitals.append(vital)
        
        return vitals
    
    def _extract_symptoms(self, text: str) -> List[MedicalEntity]:
        """Extract patient-reported symptoms"""
        symptoms = []
        
        symptom_patterns = [
            r'\b(pain|ache|aching|hurt|hurting)\b',
            r'\b(nausea|nauseous|sick|vomiting)\b',
            r'\b(dizzy|dizziness|lightheaded)\b',
            r'\b(fatigue|tired|exhausted|weakness)\b',
            r'\b(shortness of breath|sob|breathing difficulty)\b',
            r'\b(chest pain|chest discomfort)\b',
            r'\b(headache|head pain|migraine)\b',
            r'\b(fever|feverish|chills)\b',
            r'\b(cough|coughing|wheezing)\b',
            r'\b(swelling|swollen|edema)\b'
        ]
        
        for pattern in symptom_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                # Determine severity from context
                severity = self._determine_symptom_severity(text, match.start(), match.end())
                
                symptom = MedicalEntity(
                    text=match.group(),
                    entity_type='SYMPTOM',
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    severity=severity,
                    context=self._get_context(text, match.start(), match.end())
                )
                symptoms.append(symptom)
        
        return symptoms
    
    def _extract_anatomy(self, text: str) -> List[MedicalEntity]:
        """Extract anatomical references"""
        anatomy = []
        
        anatomy_patterns = [
            r'\b(heart|cardiac|chest)\b',
            r'\b(lung|pulmonary|respiratory)\b',
            r'\b(kidney|renal|nephro)\b',
            r'\b(liver|hepatic)\b',
            r'\b(brain|neurological|neuro)\b',
            r'\b(stomach|gastric|abdominal)\b',
            r'\b(back|spine|spinal)\b',
            r'\b(knee|joint|arthro)\b',
            r'\b(eye|ocular|vision)\b',
            r'\b(ear|hearing|auditory)\b'
        ]
        
        for pattern in anatomy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                anatomical = MedicalEntity(
                    text=match.group(),
                    entity_type='ANATOMY',
                    confidence=0.7,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                )
                anatomy.append(anatomical)
        
        return anatomy
    
    def _extract_allergies(self, text: str) -> List[MedicalEntity]:
        """Extract allergy information"""
        allergies = []
        
        allergy_patterns = [
            r'\ballergic to\s+(\w+(?:\s+\w+)*)\b',
            r'\ballergy to\s+(\w+(?:\s+\w+)*)\b',
            r'\b(penicillin|sulfa|latex|shellfish|nuts?) allergy\b',
            r'\breaction to\s+(\w+(?:\s+\w+)*)\b'
        ]
        
        for pattern in allergy_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                allergy = MedicalEntity(
                    text=match.group(),
                    entity_type='ALLERGY',
                    confidence=0.9,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    severity=self._determine_allergy_severity(match.group()),
                    context=self._get_context(text, match.start(), match.end())
                )
                allergies.append(allergy)
        
        return allergies
    
    def _extract_medical_devices(self, text: str) -> List[MedicalEntity]:
        """Extract medical devices and equipment"""
        devices = []
        
        device_patterns = [
            r'\b(pacemaker|defibrillator|icd)\b',
            r'\b(insulin pump|glucose monitor)\b',
            r'\b(hearing aid|cochlear implant)\b',
            r'\b(wheelchair|walker|cane)\b',
            r'\b(cpap|bipap|oxygen)\b',
            r'\b(stent|catheter|tube)\b'
        ]
        
        for pattern in device_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                device = MedicalEntity(
                    text=match.group(),
                    entity_type='MEDICAL_DEVICE',
                    confidence=0.8,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                )
                devices.append(device)
        
        return devices
    
    def _extract_temporal_expressions(self, text: str) -> List[MedicalEntity]:
        """Extract time-related medical information"""
        temporal = []
        
        temporal_patterns = [
            r'\b(\d+)\s+(days?|weeks?|months?|years?)\s+ago\b',
            r'\bfor\s+(\d+)\s+(days?|weeks?|months?|years?)\b',
            r'\bsince\s+(\w+(?:\s+\w+)*)\b',
            r'\b(daily|weekly|monthly|yearly|twice daily|three times daily)\b',
            r'\b(morning|afternoon|evening|night|bedtime)\b'
        ]
        
        for pattern in temporal_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                temporal_expr = MedicalEntity(
                    text=match.group(),
                    entity_type='TEMPORAL',
                    confidence=0.7,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    context=self._get_context(text, match.start(), match.end())
                )
                temporal.append(temporal_expr)
        
        return temporal
    
    def _get_context(self, text: str, start: int, end: int, window: int = 30) -> str:
        """Get context around an entity"""
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end].strip()
    
    def _determine_symptom_severity(self, text: str, start: int, end: int) -> str:
        """Determine symptom severity from context"""
        context = self._get_context(text, start, end, 50)
        
        if any(word in context.lower() for word in ['severe', 'intense', 'excruciating', 'unbearable']):
            return 'severe'
        elif any(word in context.lower() for word in ['moderate', 'significant', 'considerable']):
            return 'moderate'
        elif any(word in context.lower() for word in ['mild', 'slight', 'minor', 'little']):
            return 'mild'
        else:
            return 'unspecified'
    
    def _determine_allergy_severity(self, allergy_text: str) -> str:
        """Determine allergy severity"""
        if any(word in allergy_text.lower() for word in ['anaphylaxis', 'severe', 'life-threatening']):
            return 'severe'
        elif any(word in allergy_text.lower() for word in ['reaction', 'rash', 'hives']):
            return 'moderate'
        else:
            return 'mild'
    
    def _interpret_lab_value(self, lab_text: str) -> str:
        """Provide basic interpretation of lab values"""
        # This would be expanded with comprehensive reference ranges
        if 'glucose' in lab_text.lower():
            return "Blood glucose level - normal range: 70-100 mg/dL fasting"
        elif 'blood pressure' in lab_text.lower():
            return "Blood pressure - normal: <120/80 mmHg"
        elif 'cholesterol' in lab_text.lower():
            return "Cholesterol - desirable: <200 mg/dL"
        else:
            return "Laboratory value"
    
    def _apply_medical_coding(self, entities: Dict[str, List[MedicalEntity]]) -> Dict[str, List[MedicalEntity]]:
        """Apply medical coding to entities (placeholder for full implementation)"""
        # This would integrate with medical coding databases
        # For now, just add placeholder codes
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                if entity_type == 'conditions':
                    entity.code_system = 'ICD-10'
                    entity.medical_code = self._get_icd10_code(entity.text)
                elif entity_type == 'medications':
                    entity.code_system = 'RxNorm'
                    entity.medical_code = self._get_rxnorm_code(entity.text)
                elif entity_type == 'procedures':
                    entity.code_system = 'CPT'
                    entity.medical_code = self._get_cpt_code(entity.text)
        
        return entities
    
    def _get_icd10_code(self, condition: str) -> Optional[str]:
        """Get ICD-10 code for condition (placeholder)"""
        # This would query a medical coding database
        icd10_mapping = {
            'diabetes': 'E11.9',
            'hypertension': 'I10',
            'asthma': 'J45.9',
            'depression': 'F32.9'
        }
        return icd10_mapping.get(condition.lower())
    
    def _get_rxnorm_code(self, medication: str) -> Optional[str]:
        """Get RxNorm code for medication (placeholder)"""
        rxnorm_mapping = {
            'aspirin': '1191',
            'metformin': '6809',
            'lisinopril': '29046'
        }
        return rxnorm_mapping.get(medication.lower())
    
    def _get_cpt_code(self, procedure: str) -> Optional[str]:
        """Get CPT code for procedure (placeholder)"""
        cpt_mapping = {
            'consultation': '99213',
            'physical exam': '99214',
            'blood test': '80053'
        }
        return cpt_mapping.get(procedure.lower())
    
    def _calculate_confidence_scores(self, entities: Dict[str, List[MedicalEntity]], text: str) -> Dict[str, List[MedicalEntity]]:
        """Calculate and adjust confidence scores based on context"""
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                # Adjust confidence based on context quality
                context_quality = self._assess_context_quality(entity.context)
                entity.confidence = min(1.0, entity.confidence * context_quality)
        
        return entities
    
    def _assess_context_quality(self, context: str) -> float:
        """Assess the quality of context for confidence adjustment"""
        if not context:
            return 0.8
        
        # Higher confidence for medical context
        medical_indicators = ['patient', 'doctor', 'nurse', 'medical', 'clinical', 'diagnosis', 'treatment']
        medical_score = sum(1 for indicator in medical_indicators if indicator in context.lower())
        
        return min(1.0, 0.7 + (medical_score * 0.05))
    
    def _load_medical_patterns(self) -> Dict:
        """Load medical pattern dictionaries (placeholder)"""
        return {}
    
    def _load_medication_patterns(self) -> Dict:
        """Load medication pattern dictionaries (placeholder)"""
        return {}
    
    def _load_condition_patterns(self) -> Dict:
        """Load condition pattern dictionaries (placeholder)"""
        return {}
    
    def _load_procedure_patterns(self) -> Dict:
        """Load procedure pattern dictionaries (placeholder)"""
        return {}
    
    def _load_lab_patterns(self) -> Dict:
        """Load lab pattern dictionaries (placeholder)"""
        return {}
    
    def _load_vital_patterns(self) -> Dict:
        """Load vital sign pattern dictionaries (placeholder)"""
        return {}

# Global medical NER instance
_medical_ner = None

def get_medical_ner() -> MedicalNER:
    """Get or create global medical NER instance"""
    global _medical_ner
    if _medical_ner is None:
        _medical_ner = MedicalNER()
    return _medical_ner

# Public API functions
def extract_medical_entities(text: str) -> Dict[str, List[MedicalEntity]]:
    """Extract medical entities from healthcare conversation"""
    ner = get_medical_ner()
    return ner.extract_medical_entities(text)

def format_medical_entities_for_display(entities: Dict[str, List[MedicalEntity]]) -> Dict[str, List[Dict]]:
    """Format medical entities for UI display"""
    formatted = {}
    
    for entity_type, entity_list in entities.items():
        formatted[entity_type] = []
        for entity in entity_list:
            formatted[entity_type].append({
                'text': entity.text,
                'confidence': entity.confidence,
                'medical_code': entity.medical_code,
                'code_system': entity.code_system,
                'description': entity.description,
                'severity': entity.severity,
                'context': entity.context
            })
    
    return formatted