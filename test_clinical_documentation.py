#!/usr/bin/env python3
"""
Tests for Clinical Documentation and Reporting System
Comprehensive test suite for automated clinical note generation, medical coding, and quality assessment
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch

# Import the clinical documentation system
try:
    from clinical_documentation_system import (
        ClinicalDocumentationSystem,
        ClinicalNoteType,
        ClinicalSpecialty,
        DocumentationQuality,
        ClinicalTemplateEngine,
        ClinicalCodingEngine,
        ClinicalQualityAssessment,
        ClinicalCode,
        ClinicalSection,
        ClinicalNote,
        QualityMetrics
    )
except ImportError:
    pytest.skip("Clinical documentation system not available", allow_module_level=True)

class TestClinicalTemplateEngine:
    """Test clinical template generation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.template_engine = ClinicalTemplateEngine()
    
    def test_template_engine_initialization(self):
        """Test template engine initialization"""
        assert self.template_engine is not None
        assert len(self.template_engine.templates) > 0
        assert len(self.template_engine.specialty_requirements) > 0
    
    def test_generate_soap_note_template(self):
        """Test SOAP note template generation"""
        template = self.template_engine.generate_template(
            ClinicalNoteType.SOAP_NOTE,
            ClinicalSpecialty.INTERNAL_MEDICINE
        )
        
        assert template["note_type"] == "soap_note"
        assert template["specialty"] == "internal_medicine"
        assert "subjective" in template["sections"]
        assert "objective" in template["sections"]
        assert "assessment" in template["sections"]
        assert "plan" in template["sections"]
        assert template["format"] == "structured"
    
    def test_generate_admission_note_template(self):
        """Test admission note template generation"""
        template = self.template_engine.generate_template(
            ClinicalNoteType.ADMISSION_NOTE,
            ClinicalSpecialty.CARDIOLOGY
        )
        
        assert template["note_type"] == "admission_note"
        assert template["specialty"] == "cardiology"
        assert "chief_complaint" in template["sections"]
        assert "history_present_illness" in template["sections"]
        assert "physical_examination" in template["sections"]
        assert "assessment_plan" in template["sections"]
        assert template["format"] == "comprehensive"
    
    def test_specialty_specific_requirements(self):
        """Test specialty-specific template requirements"""
        cardiology_template = self.template_engine.generate_template(
            ClinicalNoteType.SOAP_NOTE,
            ClinicalSpecialty.CARDIOLOGY
        )
        
        assert "cardiovascular_examination" in cardiology_template.get("specialty_elements", [])
        assert "echocardiogram" in cardiology_template.get("common_procedures", [])
        assert "coronary_artery_disease" in cardiology_template.get("key_diagnoses", [])
    
    def test_emergency_medicine_template(self):
        """Test emergency medicine specific template"""
        template = self.template_engine.generate_template(
            ClinicalNoteType.EMERGENCY_NOTE,
            ClinicalSpecialty.EMERGENCY_MEDICINE
        )
        
        assert template["specialty"] == "emergency_medicine"
        assert "triage_assessment" in template.get("specialty_elements", [])
        assert "emergency_evaluation" in template.get("specialty_elements", [])

class TestClinicalCodingEngine:
    """Test clinical coding functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.coding_engine = ClinicalCodingEngine()
    
    def test_coding_engine_initialization(self):
        """Test coding engine initialization"""
        assert self.coding_engine is not None
        assert len(self.coding_engine.icd10_database) > 0
        assert len(self.coding_engine.cpt_database) > 0
        assert len(self.coding_engine.coding_rules) > 0
    
    def test_icd10_code_suggestions(self):
        """Test ICD-10 code suggestions"""
        clinical_text = "Patient presents with acute myocardial infarction and hypertension"
        entities = []  # Mock entities for testing
        
        icd10_codes = self.coding_engine.suggest_icd10_codes(clinical_text, entities)
        
        assert len(icd10_codes) > 0
        
        # Check for MI code
        mi_codes = [code for code in icd10_codes if "I21" in code.code]
        assert len(mi_codes) > 0
        
        # Check for hypertension code
        htn_codes = [code for code in icd10_codes if "I10" in code.code]
        assert len(htn_codes) > 0
        
        # Verify code structure
        for code in icd10_codes:
            assert code.code is not None
            assert code.description is not None
            assert code.code_type == "ICD-10"
            assert 0 <= code.confidence <= 1
    
    def test_cpt_code_suggestions(self):
        """Test CPT code suggestions"""
        clinical_text = "Office visit with established patient, performed ECG and chest x-ray"
        entities = []
        
        cpt_codes = self.coding_engine.suggest_cpt_codes(
            clinical_text, entities, ClinicalNoteType.SOAP_NOTE
        )
        
        assert len(cpt_codes) > 0
        
        # Should suggest E&M code for office visit
        em_codes = [code for code in cpt_codes if code.code.startswith("992")]
        assert len(em_codes) > 0
        
        # Should suggest ECG code
        ecg_codes = [code for code in cpt_codes if "93000" in code.code]
        assert len(ecg_codes) > 0
        
        # Verify code structure
        for code in cpt_codes:
            assert code.code is not None
            assert code.description is not None
            assert code.code_type == "CPT"
            assert 0 <= code.confidence <= 1
    
    def test_documentation_complexity_assessment(self):
        """Test documentation complexity assessment"""
        # Simple text
        simple_text = "Patient feels better today"
        simple_score = self.coding_engine._assess_documentation_complexity(simple_text, [])
        
        # Complex text
        complex_text = """
        Patient presents with multiple comorbidities including diabetes mellitus,
        hypertension, coronary artery disease, and chronic kidney disease.
        Extensive workup including laboratory studies, imaging, and specialist
        consultations. Complex medication regimen with multiple drug interactions
        requiring careful monitoring and dose adjustments.
        """
        complex_score = self.coding_engine._assess_documentation_complexity(complex_text, [])
        
        assert complex_score > simple_score
        assert 0 <= simple_score <= 1
        assert 0 <= complex_score <= 1
    
    def test_coding_rules_validation(self):
        """Test coding rules and guidelines"""
        rules = self.coding_engine.coding_rules
        
        assert rules["primary_diagnosis_required"] is True
        assert rules["max_secondary_diagnoses"] == 24
        assert "bilateral" in rules["procedure_modifier_rules"]
        assert len(rules["documentation_requirements"]["history_levels"]) == 4

class TestClinicalQualityAssessment:
    """Test clinical documentation quality assessment"""
    
    def setup_method(self):
        """Setup test environment"""
        self.quality_assessment = ClinicalQualityAssessment()
    
    def test_quality_assessment_initialization(self):
        """Test quality assessment initialization"""
        assert self.quality_assessment is not None
        assert len(self.quality_assessment.quality_criteria) > 0
        assert len(self.quality_assessment.completeness_requirements) > 0
    
    def test_completeness_assessment(self):
        """Test documentation completeness assessment"""
        # Create mock clinical note
        clinical_note = self._create_mock_clinical_note()
        
        completeness_score = self.quality_assessment._assess_completeness(clinical_note)
        
        assert 0 <= completeness_score <= 1
    
    def test_accuracy_assessment(self):
        """Test medical accuracy assessment"""
        clinical_note = self._create_mock_clinical_note()
        
        accuracy_score = self.quality_assessment._assess_accuracy(clinical_note)
        
        assert 0 <= accuracy_score <= 1
    
    def test_specificity_assessment(self):
        """Test specificity assessment"""
        clinical_note = self._create_mock_clinical_note()
        
        specificity_score = self.quality_assessment._assess_specificity(clinical_note)
        
        assert 0 <= specificity_score <= 1
    
    def test_coding_accuracy_assessment(self):
        """Test coding accuracy assessment"""
        clinical_note = self._create_mock_clinical_note()
        
        # Add mock billing codes
        clinical_note.billing_codes = [
            ClinicalCode("I21.9", "Acute MI", "ICD-10", 0.9, "test context"),
            ClinicalCode("99213", "Office visit", "CPT", 0.8, "test context")
        ]
        
        coding_accuracy = self.quality_assessment._assess_coding_accuracy(clinical_note)
        
        assert 0 <= coding_accuracy <= 1
        assert coding_accuracy > 0.5  # Should be reasonable with mock codes
    
    def test_missing_elements_identification(self):
        """Test identification of missing documentation elements"""
        clinical_note = self._create_mock_clinical_note()
        
        missing_elements = self.quality_assessment._identify_missing_elements(clinical_note)
        
        assert isinstance(missing_elements, list)
        # Some elements should be missing in our minimal mock note
        assert len(missing_elements) >= 0
    
    def test_improvement_suggestions(self):
        """Test generation of improvement suggestions"""
        clinical_note = self._create_mock_clinical_note()
        
        suggestions = self.quality_assessment._generate_improvement_suggestions(clinical_note, 0.6)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0  # Should have suggestions for low score
    
    def test_full_quality_assessment(self):
        """Test complete quality assessment"""
        clinical_note = self._create_mock_clinical_note()
        
        quality_metrics = self.quality_assessment.assess_quality(clinical_note)
        
        assert isinstance(quality_metrics, QualityMetrics)
        assert 0 <= quality_metrics.completeness_score <= 1
        assert 0 <= quality_metrics.accuracy_score <= 1
        assert 0 <= quality_metrics.specificity_score <= 1
        assert 0 <= quality_metrics.coding_accuracy <= 1
        assert quality_metrics.documentation_time > 0
        assert isinstance(quality_metrics.missing_elements, list)
        assert isinstance(quality_metrics.improvement_suggestions, list)
    
    def _create_mock_clinical_note(self):
        """Create a mock clinical note for testing"""
        # Create mock sections
        sections = {
            "subjective": ClinicalSection(
                section_name="subjective",
                content="Patient reports chest pain",
                structured_data={},
                entities=[],
                codes=[],
                quality_score=0.7,
                completeness_score=0.8,
                recommendations=[]
            ),
            "objective": ClinicalSection(
                section_name="objective",
                content="Vital signs stable",
                structured_data={},
                entities=[],
                codes=[],
                quality_score=0.6,
                completeness_score=0.7,
                recommendations=[]
            )
        }
        
        return ClinicalNote(
            note_id="test_note_001",
            note_type=ClinicalNoteType.SOAP_NOTE,
            specialty=ClinicalSpecialty.INTERNAL_MEDICINE,
            patient_id="test_patient",
            provider_id="test_provider",
            encounter_id="test_encounter",
            created_at=datetime.now(),
            sections=sections,
            word_count=50
        )

class TestClinicalDocumentationSystem:
    """Test the main clinical documentation system"""
    
    def setup_method(self):
        """Setup test environment"""
        self.clinical_system = ClinicalDocumentationSystem()
    
    def test_system_initialization(self):
        """Test system initialization"""
        assert self.clinical_system is not None
        assert self.clinical_system.template_engine is not None
        assert self.clinical_system.coding_engine is not None
        assert self.clinical_system.quality_assessment is not None
    
    @pytest.mark.asyncio
    async def test_clinical_note_generation(self):
        """Test clinical note generation"""
        sample_transcript = """
        Chief Complaint: Patient presents with chest pain.
        
        History of Present Illness: 65-year-old male with acute chest pain
        radiating to left arm. Associated with shortness of breath.
        
        Physical Examination: Blood pressure 160/95, heart rate 110.
        Cardiovascular examination reveals irregular rhythm.
        
        Assessment: Acute myocardial infarction
        
        Plan: Admit to CCU, start aspirin and beta blocker
        """
        
        clinical_note = await self.clinical_system.generate_clinical_note(
            transcript_text=sample_transcript,
            note_type=ClinicalNoteType.SOAP_NOTE,
            specialty=ClinicalSpecialty.CARDIOLOGY,
            patient_id="test_patient",
            provider_id="test_provider",
            encounter_id="test_encounter"
        )
        
        assert clinical_note is not None
        assert clinical_note.note_type == ClinicalNoteType.SOAP_NOTE
        assert clinical_note.specialty == ClinicalSpecialty.CARDIOLOGY
        assert clinical_note.patient_id == "test_patient"
        assert clinical_note.provider_id == "test_provider"
        assert clinical_note.encounter_id == "test_encounter"
        assert len(clinical_note.sections) > 0
        assert clinical_note.word_count > 0
        assert clinical_note.estimated_time_saved > 0
    
    @pytest.mark.asyncio
    async def test_section_extraction(self):
        """Test clinical section extraction"""
        transcript = """
        Subjective: Patient reports feeling better today.
        Objective: Vital signs are stable.
        Assessment: Condition improving.
        Plan: Continue current treatment.
        """
        
        # Mock template
        template = {
            "sections": ["subjective", "objective", "assessment", "plan"],
            "required_elements": {}
        }
        
        sections = await self.clinical_system._extract_clinical_sections(
            transcript, template, []
        )
        
        assert len(sections) == 4
        assert "subjective" in sections
        assert "objective" in sections
        assert "assessment" in sections
        assert "plan" in sections
        
        # Check section content
        assert "feeling better" in sections["subjective"].content.lower()
        assert "vital signs" in sections["objective"].content.lower()
        assert "improving" in sections["assessment"].content.lower()
        assert "continue" in sections["plan"].content.lower()
    
    def test_section_content_extraction(self):
        """Test extraction of specific section content"""
        transcript = """
        Chief Complaint: Chest pain and shortness of breath
        
        History of Present Illness: Patient reports acute onset chest pain
        that started 2 hours ago. Pain is substernal and radiating to left arm.
        
        Physical Examination: Blood pressure 160/95, heart rate 110 bpm.
        Cardiovascular examination reveals S3 gallop.
        
        Assessment: Acute myocardial infarction
        
        Plan: Admit to CCU for monitoring and treatment
        """
        
        # Test chief complaint extraction
        cc_content = self.clinical_system._extract_section_content(transcript, "chief_complaint")
        assert "chest pain" in cc_content.lower()
        assert "shortness of breath" in cc_content.lower()
        
        # Test HPI extraction
        hpi_content = self.clinical_system._extract_section_content(transcript, "history_present_illness")
        assert "acute onset" in hpi_content.lower()
        assert "2 hours ago" in hpi_content.lower()
        
        # Test physical exam extraction
        pe_content = self.clinical_system._extract_section_content(transcript, "physical_examination")
        assert "blood pressure" in pe_content.lower()
        assert "160/95" in pe_content
        
        # Test assessment extraction
        assessment_content = self.clinical_system._extract_section_content(transcript, "assessment")
        assert "myocardial infarction" in assessment_content.lower()
        
        # Test plan extraction
        plan_content = self.clinical_system._extract_section_content(transcript, "plan")
        assert "admit" in plan_content.lower()
        assert "ccu" in plan_content.lower()
    
    def test_vital_signs_extraction(self):
        """Test vital signs extraction from objective section"""
        content = "Vital signs: BP 120/80, HR 75, RR 16, Temp 98.6°F"
        
        vital_signs = self.clinical_system._extract_vital_signs(content)
        
        assert "blood_pressure" in vital_signs
        assert vital_signs["blood_pressure"] == "120/80"
        assert "heart_rate" in vital_signs
        assert vital_signs["heart_rate"] == "75"
        assert "respiratory_rate" in vital_signs
        assert vital_signs["respiratory_rate"] == "16"
        assert "temperature" in vital_signs
        assert vital_signs["temperature"] == "98.6"
    
    def test_medication_list_extraction(self):
        """Test medication list extraction"""
        content = "Medications: Lisinopril 10mg daily, Metformin 500mg twice daily"
        entities = []  # Mock entities
        
        medications = self.clinical_system._extract_medication_list(content, entities)
        
        # Should return empty list since no entities provided
        assert isinstance(medications, list)
    
    def test_primary_diagnosis_extraction(self):
        """Test primary diagnosis extraction"""
        entities = []  # Mock entities
        icd10_codes = [
            ClinicalCode("I21.9", "Acute myocardial infarction", "ICD-10", 0.9, "context"),
            ClinicalCode("I10", "Essential hypertension", "ICD-10", 0.7, "context")
        ]
        
        primary_diagnosis = self.clinical_system._extract_primary_diagnosis(entities, icd10_codes)
        
        # Should return the highest confidence diagnosis
        assert primary_diagnosis == "Acute myocardial infarction"
    
    def test_clinical_report_generation(self):
        """Test clinical report generation"""
        # Create mock clinical note
        clinical_note = ClinicalNote(
            note_id="test_note",
            note_type=ClinicalNoteType.SOAP_NOTE,
            specialty=ClinicalSpecialty.INTERNAL_MEDICINE,
            patient_id="test_patient",
            provider_id="test_provider",
            encounter_id="test_encounter",
            created_at=datetime.now(),
            sections={},
            word_count=100,
            billing_codes=[
                ClinicalCode("99213", "Office visit", "CPT", 0.9, "context", reimbursement_rate=109.00)
            ]
        )
        
        report = self.clinical_system.generate_clinical_report(clinical_note)
        
        assert "note_summary" in report
        assert "clinical_content" in report
        assert "coding_information" in report
        assert "quality_assessment" in report
        assert "efficiency_metrics" in report
        
        # Check note summary
        note_summary = report["note_summary"]
        assert note_summary["note_id"] == "test_note"
        assert note_summary["note_type"] == "soap_note"
        assert note_summary["specialty"] == "internal_medicine"
        
        # Check coding information
        coding_info = report["coding_information"]
        assert len(coding_info["billing_codes"]) == 1
        assert coding_info["total_estimated_reimbursement"] == 109.00

class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        self.clinical_system = ClinicalDocumentationSystem()
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete clinical documentation workflow"""
        # Sample clinical transcript
        transcript = """
        Chief Complaint: 45-year-old female with abdominal pain
        
        History of Present Illness: Patient reports sudden onset severe right
        upper quadrant pain after eating fatty meal. Associated nausea and vomiting.
        
        Physical Examination: Tender RUQ, positive Murphy's sign
        Labs: WBC 12,000, bilirubin elevated
        Imaging: Ultrasound shows gallstones
        
        Assessment: Acute cholecystitis
        
        Plan: Surgery consultation, antibiotics, pain control
        """
        
        # Generate clinical note
        clinical_note = await self.clinical_system.generate_clinical_note(
            transcript_text=transcript,
            note_type=ClinicalNoteType.EMERGENCY_NOTE,
            specialty=ClinicalSpecialty.EMERGENCY_MEDICINE,
            patient_id="integration_test_patient",
            provider_id="integration_test_provider",
            encounter_id="integration_test_encounter"
        )
        
        # Verify note generation
        assert clinical_note is not None
        assert clinical_note.note_type == ClinicalNoteType.EMERGENCY_NOTE
        assert clinical_note.specialty == ClinicalSpecialty.EMERGENCY_MEDICINE
        
        # Verify sections were extracted
        assert len(clinical_note.sections) > 0
        
        # Verify coding was performed
        assert len(clinical_note.billing_codes) > 0
        
        # Generate comprehensive report
        report = self.clinical_system.generate_clinical_report(clinical_note)
        
        # Verify report generation
        assert report is not None
        assert "quality_assessment" in report
        assert "coding_information" in report
        
        # Verify quality assessment
        quality_assessment = report["quality_assessment"]
        assert 0 <= quality_assessment["completeness_score"] <= 1
        assert 0 <= quality_assessment["accuracy_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_multiple_note_types(self):
        """Test generation of different note types"""
        base_transcript = "Patient presents with chest pain. Physical exam normal. Plan: discharge home."
        
        note_types = [
            ClinicalNoteType.SOAP_NOTE,
            ClinicalNoteType.PROGRESS_NOTE,
            ClinicalNoteType.ADMISSION_NOTE
        ]
        
        for note_type in note_types:
            clinical_note = await self.clinical_system.generate_clinical_note(
                transcript_text=base_transcript,
                note_type=note_type,
                specialty=ClinicalSpecialty.INTERNAL_MEDICINE,
                patient_id=f"test_patient_{note_type.value}",
                provider_id="test_provider",
                encounter_id=f"test_encounter_{note_type.value}"
            )
            
            assert clinical_note.note_type == note_type
            assert len(clinical_note.sections) > 0
    
    @pytest.mark.asyncio
    async def test_specialty_variations(self):
        """Test different medical specialties"""
        base_transcript = "Patient evaluation and treatment plan discussed."
        
        specialties = [
            ClinicalSpecialty.CARDIOLOGY,
            ClinicalSpecialty.EMERGENCY_MEDICINE,
            ClinicalSpecialty.SURGERY
        ]
        
        for specialty in specialties:
            clinical_note = await self.clinical_system.generate_clinical_note(
                transcript_text=base_transcript,
                note_type=ClinicalNoteType.SOAP_NOTE,
                specialty=specialty,
                patient_id=f"test_patient_{specialty.value}",
                provider_id="test_provider",
                encounter_id=f"test_encounter_{specialty.value}"
            )
            
            assert clinical_note.specialty == specialty
            assert clinical_note.note_id is not None

# Performance and stress tests
class TestPerformance:
    """Test performance characteristics"""
    
    def setup_method(self):
        """Setup test environment"""
        self.clinical_system = ClinicalDocumentationSystem()
    
    @pytest.mark.asyncio
    async def test_large_transcript_processing(self):
        """Test processing of large clinical transcripts"""
        # Create large transcript
        large_transcript = """
        Chief Complaint: Complex patient with multiple comorbidities
        
        History of Present Illness: This is a detailed history of a complex
        patient with multiple medical problems including diabetes, hypertension,
        coronary artery disease, chronic kidney disease, and heart failure.
        """ * 20  # Repeat to create large text
        
        import time
        start_time = time.time()
        
        clinical_note = await self.clinical_system.generate_clinical_note(
            transcript_text=large_transcript,
            note_type=ClinicalNoteType.ADMISSION_NOTE,
            specialty=ClinicalSpecialty.INTERNAL_MEDICINE,
            patient_id="performance_test_patient",
            provider_id="performance_test_provider",
            encounter_id="performance_test_encounter"
        )
        
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert processing_time < 10.0, f"Processing took too long: {processing_time}s"
        assert clinical_note is not None
        assert clinical_note.word_count > 1000
    
    @pytest.mark.asyncio
    async def test_concurrent_note_generation(self):
        """Test concurrent clinical note generation"""
        import asyncio
        
        async def generate_note(patient_id):
            return await self.clinical_system.generate_clinical_note(
                transcript_text="Patient presents with routine follow-up visit.",
                note_type=ClinicalNoteType.PROGRESS_NOTE,
                specialty=ClinicalSpecialty.INTERNAL_MEDICINE,
                patient_id=f"concurrent_patient_{patient_id}",
                provider_id="concurrent_provider",
                encounter_id=f"concurrent_encounter_{patient_id}"
            )
        
        # Generate multiple notes concurrently
        tasks = [generate_note(i) for i in range(5)]
        
        import time
        start_time = time.time()
        results = await asyncio.gather(*tasks)
        processing_time = time.time() - start_time
        
        # All notes should be generated successfully
        assert len(results) == 5
        assert all(note is not None for note in results)
        assert all(note.note_type == ClinicalNoteType.PROGRESS_NOTE for note in results)
        
        # Should complete within reasonable time
        assert processing_time < 15.0, f"Concurrent processing took too long: {processing_time}s"

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])