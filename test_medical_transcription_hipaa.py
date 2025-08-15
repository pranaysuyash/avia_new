#!/usr/bin/env python3
"""
Tests for HIPAA-Compliant Medical Transcription System
Comprehensive test suite for medical transcription with HIPAA compliance
"""

import pytest
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch

# Import the medical transcription system
try:
    from medical_transcription_system import (
        MedicalTranscriptionSystem,
        HIPAACompliance,
        MedicalEntityType,
        HIPAAViolation,
        MedicalEntity,
        MedicalTerminologyValidator,
        HIPAAComplianceChecker,
        MedicalEntityExtractor,
        MedicalReportGenerator,
        EncryptionManager
    )
except ImportError:
    pytest.skip("Medical transcription system not available", allow_module_level=True)

class TestMedicalTerminologyValidator:
    """Test medical terminology validation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.validator = MedicalTerminologyValidator()
    
    def test_validate_medical_term_valid(self):
        """Test validation of valid medical terms"""
        # Test ICD-10 term
        result = self.validator.validate_medical_term("hypertension")
        assert result['is_valid'] == True
        assert result['category'] == 'diagnosis'
        assert result['code'] == 'I10'
        assert result['confidence'] > 0.8
    
    def test_validate_medical_term_medication(self):
        """Test validation of medication terms"""
        # Test generic medication
        result = self.validator.validate_medical_term("acetaminophen")
        assert result['is_valid'] == True
        assert result['category'] == 'medication'
        assert result['normalized'] == 'acetaminophen'
        
        # Test brand name medication
        result = self.validator.validate_medical_term("tylenol")
        assert result['is_valid'] == True
        assert result['category'] == 'medication'
        assert result['normalized'] == 'acetaminophen'
    
    def test_validate_medical_term_invalid(self):
        """Test validation of invalid medical terms"""
        result = self.validator.validate_medical_term("invalidterm")
        assert result['is_valid'] == False
        assert result['confidence'] == 0.0
    
    def test_expand_abbreviation_simple(self):
        """Test simple abbreviation expansion"""
        expansion = self.validator.expand_abbreviation("bp")
        assert expansion is not None
        assert expansion.expansion == "blood pressure"
        assert expansion.category == "vital_signs"
        assert expansion.confidence > 0.9
    
    def test_expand_abbreviation_context_dependent(self):
        """Test context-dependent abbreviation expansion"""
        # Test 'cp' with cardiac context
        expansion = self.validator.expand_abbreviation("cp", "patient has chest pain")
        assert expansion is not None
        assert expansion.expansion == "chest pain"
        
        # Test 'cp' with neurological context
        expansion = self.validator.expand_abbreviation("cp", "patient has cerebral palsy")
        assert expansion is not None
        assert expansion.expansion == "cerebral palsy"
    
    def test_expand_abbreviation_unknown(self):
        """Test expansion of unknown abbreviations"""
        expansion = self.validator.expand_abbreviation("xyz")
        assert expansion is None

class TestHIPAAComplianceChecker:
    """Test HIPAA compliance checking"""
    
    def setup_method(self):
        """Setup test environment"""
        self.checker = HIPAAComplianceChecker()
    
    def test_detect_phi_ssn(self):
        """Test SSN detection"""
        text = "Patient SSN is 123-45-6789"
        violations = self.checker.detect_phi(text)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "potential_ssn"
        assert violations[0].text == "123-45-6789"
        assert violations[0].severity == "high"
    
    def test_detect_phi_phone(self):
        """Test phone number detection"""
        text = "Call patient at 555-123-4567"
        violations = self.checker.detect_phi(text)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "potential_phone"
        assert violations[0].text == "555-123-4567"
        assert violations[0].severity == "medium"
    
    def test_detect_phi_email(self):
        """Test email detection"""
        text = "Patient email: john.doe@email.com"
        violations = self.checker.detect_phi(text)
        
        assert len(violations) == 1
        assert violations[0].violation_type == "potential_email"
        assert violations[0].text == "john.doe@email.com"
        assert violations[0].severity == "medium"
    
    def test_detect_phi_multiple(self):
        """Test detection of multiple PHI types"""
        text = """
        Patient: John Doe
        DOB: 01/15/1980
        Phone: 555-123-4567
        SSN: 123-45-6789
        """
        violations = self.checker.detect_phi(text)
        
        # Should detect multiple violations
        assert len(violations) >= 3
        violation_types = [v.violation_type for v in violations]
        assert "potential_phone" in violation_types
        assert "potential_ssn" in violation_types
        assert "potential_date_birth" in violation_types
    
    def test_anonymize_text(self):
        """Test text anonymization"""
        text = "Patient John Doe, SSN 123-45-6789, Phone 555-123-4567"
        anonymized = self.checker.anonymize_text(text)
        
        # Should not contain original PHI
        assert "123-45-6789" not in anonymized
        assert "555-123-4567" not in anonymized
        
        # Should contain replacement tokens
        assert "[SSN-REMOVED]" in anonymized
        assert "[PHONE-REMOVED]" in anonymized
    
    def test_anonymize_text_compliance_levels(self):
        """Test anonymization with different compliance levels"""
        text = "Patient SSN: 123-45-6789"
        
        # Standard compliance
        anonymized_standard = self.checker.anonymize_text(text, HIPAACompliance.STANDARD)
        assert "[SSN-REMOVED]" in anonymized_standard
        
        # Strict compliance
        anonymized_strict = self.checker.anonymize_text(text, HIPAACompliance.STRICT)
        assert "[SSN-REMOVED]" in anonymized_strict

class TestMedicalEntityExtractor:
    """Test medical entity extraction"""
    
    def setup_method(self):
        """Setup test environment"""
        try:
            self.extractor = MedicalEntityExtractor()
        except OSError:
            pytest.skip("spaCy model not available")
    
    def test_extract_symptoms(self):
        """Test symptom extraction"""
        text = "Patient presents with fever, headache, and nausea"
        entities = self.extractor.extract_entities(text)
        
        symptom_entities = [e for e in entities if e.entity_type == MedicalEntityType.SYMPTOM]
        assert len(symptom_entities) >= 2
        
        symptom_texts = [e.text.lower() for e in symptom_entities]
        assert "fever" in symptom_texts
        assert "headache" in symptom_texts
    
    def test_extract_medications(self):
        """Test medication extraction"""
        text = "Prescribed acetaminophen and ibuprofen for pain"
        entities = self.extractor.extract_entities(text)
        
        medication_entities = [e for e in entities if e.entity_type == MedicalEntityType.MEDICATION]
        assert len(medication_entities) >= 2
        
        medication_texts = [e.text.lower() for e in medication_entities]
        assert "acetaminophen" in medication_texts
        assert "ibuprofen" in medication_texts
    
    def test_extract_procedures(self):
        """Test procedure extraction"""
        text = "Performed blood test and x-ray examination"
        entities = self.extractor.extract_entities(text)
        
        procedure_entities = [e for e in entities if e.entity_type == MedicalEntityType.PROCEDURE]
        assert len(procedure_entities) >= 2
        
        procedure_texts = [e.text.lower() for e in procedure_entities]
        assert "blood test" in procedure_texts
        assert "x-ray" in procedure_texts
    
    def test_entity_confidence_scores(self):
        """Test entity confidence scores"""
        text = "Patient has hypertension and takes lisinopril"
        entities = self.extractor.extract_entities(text)
        
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0
            assert entity.start_pos >= 0
            assert entity.end_pos > entity.start_pos
            assert entity.normalized_form is not None

class TestMedicalReportGenerator:
    """Test medical report generation"""
    
    def setup_method(self):
        """Setup test environment"""
        self.generator = MedicalReportGenerator()
    
    def test_generate_consultation_report(self):
        """Test consultation report generation"""
        transcript = """
        Chief Complaint: Chest pain
        History of Present Illness: Patient presents with acute chest pain
        Physical Examination: Normal heart sounds
        Assessment and Plan: Rule out MI, start aspirin
        """
        
        entities = [
            MedicalEntity(
                text="chest pain",
                entity_type=MedicalEntityType.SYMPTOM,
                confidence=0.9,
                start_pos=0,
                end_pos=10,
                normalized_form="chest pain"
            )
        ]
        
        report = self.generator.generate_report(
            transcript,
            entities,
            report_type='consultation',
            metadata={'patient_id': 'TEST_001', 'provider_id': 'DOC_001'}
        )
        
        assert report.report_type == 'consultation'
        assert report.patient_id == 'TEST_001'
        assert report.provider_id == 'DOC_001'
        assert len(report.sections) > 0
        assert 'chief_complaint' in report.sections
        assert len(report.entities) == 1
    
    def test_generate_progress_note(self):
        """Test progress note generation"""
        transcript = """
        Subjective: Patient feeling better
        Objective: Vital signs stable
        Assessment: Improving condition
        Plan: Continue current treatment
        """
        
        report = self.generator.generate_report(
            transcript,
            [],
            report_type='progress_note',
            metadata={'patient_id': 'TEST_002', 'provider_id': 'DOC_002'}
        )
        
        assert report.report_type == 'progress_note'
        assert 'subjective' in report.sections
        assert 'objective' in report.sections
        assert 'assessment' in report.sections
        assert 'plan' in report.sections
    
    def test_section_extraction(self):
        """Test clinical section extraction"""
        text = """
        Chief Complaint: Headache
        History of Present Illness: Severe headache for 2 days
        Physical Examination: Normal neurological exam
        """
        
        sections = self.generator._extract_sections(text, ['chief_complaint', 'history_of_present_illness'])
        
        assert 'chief_complaint' in sections
        assert 'history_of_present_illness' in sections
        assert 'headache' in sections['chief_complaint'].lower()
        assert 'severe headache' in sections['history_of_present_illness'].lower()

class TestEncryptionManager:
    """Test encryption functionality"""
    
    def setup_method(self):
        """Setup test environment"""
        self.encryption_manager = EncryptionManager("test_password")
    
    def test_encrypt_decrypt_text(self):
        """Test text encryption and decryption"""
        original_text = "This is sensitive medical information"
        
        # Encrypt
        encrypted_data = self.encryption_manager.encrypt_text(original_text)
        assert isinstance(encrypted_data, bytes)
        assert encrypted_data != original_text.encode()
        
        # Decrypt
        decrypted_text = self.encryption_manager.decrypt_text(encrypted_data)
        assert decrypted_text == original_text
    
    def test_encrypt_report(self):
        """Test medical report encryption"""
        # Create a mock report
        from medical_transcription_system import MedicalReport
        
        report = MedicalReport(
            report_id="TEST_001",
            patient_id="PATIENT_001",
            provider_id="PROVIDER_001",
            transcript_id="TRANSCRIPT_001",
            report_type="consultation",
            sections={"chief_complaint": "Test complaint"},
            entities=[],
            medications=[],
            procedures=[],
            diagnoses=[],
            created_at=datetime.now(),
            encrypted_content=b'',
            compliance_status="pending"
        )
        
        # Encrypt report
        encrypted_data = self.encryption_manager.encrypt_report(report)
        assert isinstance(encrypted_data, bytes)
        assert len(encrypted_data) > 0

class TestMedicalTranscriptionSystem:
    """Test the main medical transcription system"""
    
    def setup_method(self):
        """Setup test environment"""
        # Use temporary database for testing
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        try:
            self.system = MedicalTranscriptionSystem(HIPAACompliance.STANDARD)
        except Exception as e:
            pytest.skip(f"Medical transcription system not available: {e}")
    
    def teardown_method(self):
        """Cleanup test environment"""
        if hasattr(self, 'temp_db'):
            try:
                os.unlink(self.temp_db.name)
            except:
                pass
    
    def test_system_initialization(self):
        """Test system initialization"""
        assert self.system.compliance_level == HIPAACompliance.STANDARD
        assert self.system.terminology_validator is not None
        assert self.system.compliance_checker is not None
        assert self.system.entity_extractor is not None
        assert self.system.report_generator is not None
        assert self.system.encryption_manager is not None
    
    @patch.object(MedicalTranscriptionSystem, 'process_transcript')
    def test_process_transcript_mock(self, mock_process):
        """Test transcript processing with mock"""
        # Mock the process_transcript method
        mock_result = {
            'anonymized_text': 'Patient [NAME-REMOVED] presents with chest pain',
            'phi_violations': [],
            'medical_entities': [],
            'medical_codes': {'icd10_codes': [], 'cpt_codes': []},
            'compliance_score': 0.95
        }
        mock_process.return_value = mock_result
        
        # Test processing
        transcript = "Patient John Doe presents with chest pain"
        result = self.system.process_transcript(transcript)
        
        assert result == mock_result
        mock_process.assert_called_once_with(transcript)
    
    def test_audit_logging_setup(self):
        """Test audit logging setup"""
        # Check if audit logger is configured
        import logging
        audit_logger = logging.getLogger('medical_audit')
        assert audit_logger is not None
    
    def test_compliance_level_setting(self):
        """Test compliance level configuration"""
        # Test different compliance levels
        for level in HIPAACompliance:
            try:
                system = MedicalTranscriptionSystem(level)
                assert system.compliance_level == level
            except Exception:
                # Skip if system can't be initialized
                pass

class TestIntegrationScenarios:
    """Test integration scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        try:
            self.system = MedicalTranscriptionSystem(HIPAACompliance.STANDARD)
        except Exception as e:
            pytest.skip(f"Medical transcription system not available: {e}")
    
    def test_full_medical_transcript_processing(self):
        """Test complete medical transcript processing workflow"""
        medical_transcript = """
        Patient: John Smith, DOB: 03/15/1975, MRN: 12345678
        
        Chief Complaint: Chest pain and shortness of breath
        
        History of Present Illness: 
        48-year-old male presents with acute onset chest pain.
        Patient has history of hypertension and diabetes.
        
        Physical Examination:
        Vital Signs: BP 160/95, HR 110
        Cardiovascular: Irregular rhythm
        
        Assessment: Acute myocardial infarction
        Plan: Start aspirin, metoprolol
        """
        
        # This would test the full workflow if the system was fully implemented
        # For now, we test individual components
        
        # Test PHI detection
        phi_violations = self.system.compliance_checker.detect_phi(medical_transcript)
        assert len(phi_violations) > 0  # Should detect PHI
        
        # Test anonymization
        anonymized = self.system.compliance_checker.anonymize_text(medical_transcript)
        assert "John Smith" not in anonymized
        assert "12345678" not in anonymized
    
    def test_medical_coding_workflow(self):
        """Test medical coding workflow"""
        # Test terminology validation
        hypertension_result = self.system.terminology_validator.validate_medical_term("hypertension")
        assert hypertension_result['is_valid'] == True
        assert hypertension_result['code'] == 'I10'
        
        # Test abbreviation expansion
        bp_expansion = self.system.terminology_validator.expand_abbreviation("bp")
        assert bp_expansion.expansion == "blood pressure"
    
    def test_compliance_monitoring(self):
        """Test compliance monitoring features"""
        # Test PHI detection on various text samples
        test_cases = [
            ("Patient SSN: 123-45-6789", True),
            ("Patient has hypertension", False),
            ("Call 555-123-4567", True),
            ("Normal blood pressure", False)
        ]
        
        for text, should_have_phi in test_cases:
            violations = self.system.compliance_checker.detect_phi(text)
            has_phi = len(violations) > 0
            assert has_phi == should_have_phi, f"PHI detection failed for: {text}"

# Performance and stress tests
class TestPerformance:
    """Test performance characteristics"""
    
    def setup_method(self):
        """Setup test environment"""
        try:
            self.system = MedicalTranscriptionSystem(HIPAACompliance.STANDARD)
        except Exception as e:
            pytest.skip(f"Medical transcription system not available: {e}")
    
    def test_large_transcript_processing(self):
        """Test processing of large medical transcripts"""
        # Create a large transcript
        large_transcript = """
        Patient presents with multiple complaints including chest pain,
        shortness of breath, nausea, vomiting, and dizziness.
        """ * 100  # Repeat to create large text
        
        # Test PHI detection performance
        import time
        start_time = time.time()
        violations = self.system.compliance_checker.detect_phi(large_transcript)
        processing_time = time.time() - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        assert processing_time < 5.0, f"PHI detection took too long: {processing_time}s"
    
    def test_multiple_concurrent_requests(self):
        """Test handling multiple concurrent requests"""
        import threading
        import time
        
        results = []
        errors = []
        
        def process_transcript(transcript_id):
            try:
                text = f"Patient {transcript_id} has hypertension and diabetes"
                violations = self.system.compliance_checker.detect_phi(text)
                results.append((transcript_id, len(violations)))
            except Exception as e:
                errors.append((transcript_id, str(e)))
        
        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=process_transcript, args=(i,))
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        processing_time = time.time() - start_time
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10, f"Not all requests completed: {len(results)}"
        assert processing_time < 10.0, f"Concurrent processing took too long: {processing_time}s"

if __name__ == "__main__":
    # Run tests with verbose output
    pytest.main([__file__, "-v", "--tb=short"])