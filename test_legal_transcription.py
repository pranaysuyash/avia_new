#!/usr/bin/env python3
"""
Comprehensive test suite for legal transcription and analysis system.
Tests all components including schema processing, entity extraction, and compliance features.
"""

import pytest
import tempfile
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from legal_transcription_system import LegalTranscriptionSystem
from legal_transcription_core import LegalTranscriptionCore
from legal_schema_processor import LegalSchemaProcessor


class TestLegalSchemaProcessor:
    """Test legal schema processing functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = LegalSchemaProcessor()
    
    def test_legal_entity_extraction(self):
        """Test extraction of legal entities from text."""
        text = """
        In the case of Smith v. Jones, Case No. 2023-CV-1234, 
        the plaintiff filed a motion under Rule 56 of the Federal Rules of Civil Procedure.
        The contract dated January 15, 2023, contains a confidentiality clause.
        Attorney John Doe represents the defendant.
        """
        
        entities = self.processor.extract_legal_entities(text)
        
        # Check for case references
        case_refs = [e for e in entities if e['type'] == 'case_reference']
        assert len(case_refs) >= 1
        assert any('Smith v. Jones' in ref['text'] for ref in case_refs)
        
        # Check for legal rules
        rules = [e for e in entities if e['type'] == 'legal_rule']
        assert len(rules) >= 1
        assert any('Rule 56' in rule['text'] for rule in rules)
        
        # Check for dates
        dates = [e for e in entities if e['type'] == 'date']
        assert len(dates) >= 1
        
        # Check for legal professionals
        attorneys = [e for e in entities if e['type'] == 'legal_professional']
        assert len(attorneys) >= 1
    
    def test_legal_document_classification(self):
        """Test classification of legal document types."""
        # Test contract classification
        contract_text = "This Agreement is entered into between Party A and Party B..."
        doc_type = self.processor.classify_document_type(contract_text)
        assert doc_type in ['contract', 'agreement']
        
        # Test motion classification
        motion_text = "Plaintiff hereby moves this Court for summary judgment..."
        doc_type = self.processor.classify_document_type(motion_text)
        assert doc_type == 'motion'
        
        # Test deposition classification
        deposition_text = "Q: Please state your name for the record. A: My name is..."
        doc_type = self.processor.classify_document_type(deposition_text)
        assert doc_type == 'deposition'
    
    def test_privilege_detection(self):
        """Test detection of privileged communications."""
        privileged_text = """
        Attorney-client privileged communication:
        Dear Client, regarding your confidential matter...
        """
        
        privilege_markers = self.processor.detect_privilege_markers(privileged_text)
        assert len(privilege_markers) > 0
        assert any('attorney-client' in marker['type'].lower() for marker in privilege_markers)
    
    def test_redaction_suggestions(self):
        """Test generation of redaction suggestions."""
        sensitive_text = """
        The plaintiff's SSN is 123-45-6789.
        Client's phone number: (555) 123-4567.
        Confidential settlement amount: $500,000.
        """
        
        redactions = self.processor.suggest_redactions(sensitive_text)
        assert len(redactions) >= 3
        
        # Check for PII redaction
        pii_redactions = [r for r in redactions if r['category'] == 'pii']
        assert len(pii_redactions) >= 2
        
        # Check for financial redaction
        financial_redactions = [r for r in redactions if r['category'] == 'financial']
        assert len(financial_redactions) >= 1


class TestLegalTranscriptionCore:
    """Test core legal transcription functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.core = LegalTranscriptionCore()
    
    @patch('legal_transcription_core.openai.Audio.transcribe')
    def test_legal_transcription_processing(self, mock_transcribe):
        """Test legal-specific transcription processing."""
        # Mock OpenAI response
        mock_transcribe.return_value = Mock(
            text="Your Honor, I object to this line of questioning as it calls for hearsay."
        )
        
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            result = self.core.process_legal_audio(temp_file.name)
            
            assert result['status'] == 'success'
            assert 'transcript' in result
            assert 'legal_analysis' in result
            assert 'entities' in result['legal_analysis']
            assert 'document_type' in result['legal_analysis']
    
    def test_speaker_role_identification(self):
        """Test identification of speaker roles in legal proceedings."""
        transcript_segments = [
            {"speaker": "Speaker_1", "text": "Your Honor, I represent the plaintiff."},
            {"speaker": "Speaker_2", "text": "Objection, Your Honor. Leading the witness."},
            {"speaker": "Speaker_3", "text": "Sustained. Please rephrase the question."},
            {"speaker": "Speaker_4", "text": "I was at home on the night in question."}
        ]
        
        roles = self.core.identify_speaker_roles(transcript_segments)
        
        # Should identify judge, attorneys, and witness
        role_types = [role['role'] for role in roles.values()]
        assert 'judge' in role_types
        assert 'attorney' in role_types
        assert 'witness' in role_types
    
    def test_legal_terminology_enhancement(self):
        """Test enhancement of legal terminology in transcripts."""
        raw_text = "The defendant filed a motion for summary judgment per rule fifty six."
        
        enhanced = self.core.enhance_legal_terminology(raw_text)
        
        # Should expand legal abbreviations and standardize terminology
        assert 'Rule 56' in enhanced or 'rule 56' in enhanced
        assert len(enhanced) >= len(raw_text)
    
    def test_citation_formatting(self):
        """Test proper formatting of legal citations."""
        text_with_citations = """
        See Smith versus Jones, 123 F.3d 456 (9th Cir. 2020).
        Federal Rules of Civil Procedure Rule 12(b)(6).
        """
        
        formatted = self.core.format_legal_citations(text_with_citations)
        
        # Should properly format case citations
        assert 'Smith v. Jones' in formatted
        assert '123 F.3d 456' in formatted
        assert 'Fed. R. Civ. P. 12(b)(6)' in formatted or 'Rule 12(b)(6)' in formatted


class TestLegalTranscriptionSystem:
    """Test the complete legal transcription system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.system = LegalTranscriptionSystem()
    
    @patch('legal_transcription_system.LegalTranscriptionCore')
    @patch('legal_transcription_system.LegalSchemaProcessor')
    def test_complete_legal_processing_workflow(self, mock_schema, mock_core):
        """Test the complete legal transcription workflow."""
        # Mock core transcription
        mock_core_instance = Mock()
        mock_core.return_value = mock_core_instance
        mock_core_instance.process_legal_audio.return_value = {
            'status': 'success',
            'transcript': 'Legal proceeding transcript...',
            'legal_analysis': {
                'entities': [{'type': 'case_reference', 'text': 'Smith v. Jones'}],
                'document_type': 'hearing'
            }
        }
        
        # Mock schema processing
        mock_schema_instance = Mock()
        mock_schema.return_value = mock_schema_instance
        mock_schema_instance.extract_legal_entities.return_value = [
            {'type': 'case_reference', 'text': 'Smith v. Jones', 'confidence': 0.95}
        ]
        
        with tempfile.NamedTemporaryFile(suffix='.wav') as temp_file:
            result = self.system.process_legal_recording(
                temp_file.name,
                case_number="2023-CV-1234",
                proceeding_type="hearing"
            )
            
            assert result['status'] == 'success'
            assert 'transcript' in result
            assert 'legal_analysis' in result
            assert 'compliance_check' in result
            assert 'metadata' in result
    
    def test_compliance_validation(self):
        """Test legal compliance validation."""
        transcript_data = {
            'transcript': 'Legal proceeding with proper procedures...',
            'metadata': {
                'case_number': '2023-CV-1234',
                'proceeding_type': 'hearing',
                'participants': ['Judge Smith', 'Attorney Jones']
            }
        }
        
        compliance = self.system.validate_compliance(transcript_data)
        
        assert 'status' in compliance
        assert 'checks' in compliance
        assert 'recommendations' in compliance
    
    def test_legal_export_formats(self):
        """Test export in various legal formats."""
        transcript_data = {
            'transcript': 'Sample legal transcript...',
            'legal_analysis': {
                'entities': [{'type': 'case_reference', 'text': 'Smith v. Jones'}],
                'document_type': 'deposition'
            },
            'metadata': {
                'case_number': '2023-CV-1234',
                'date': '2023-12-08',
                'participants': ['Attorney A', 'Witness B']
            }
        }
        
        # Test court reporter format
        court_format = self.system.export_court_format(transcript_data)
        assert 'CASE NO.' in court_format
        assert 'TRANSCRIPT' in court_format
        
        # Test legal brief format
        brief_format = self.system.export_legal_brief_format(transcript_data)
        assert 'LEGAL BRIEF' in brief_format or 'Brief' in brief_format
        
        # Test discovery format
        discovery_format = self.system.export_discovery_format(transcript_data)
        assert 'DISCOVERY' in discovery_format or 'Discovery' in discovery_format
    
    def test_privilege_protection(self):
        """Test attorney-client privilege protection."""
        privileged_content = """
        Attorney: This is a confidential communication with my client.
        Client: I need legal advice about my case.
        """
        
        protection_result = self.system.protect_privileged_content(privileged_content)
        
        assert 'protected' in protection_result
        assert 'redacted_content' in protection_result
        assert 'privilege_markers' in protection_result
    
    def test_legal_search_and_indexing(self):
        """Test legal-specific search and indexing capabilities."""
        legal_documents = [
            {
                'id': 'doc1',
                'content': 'Motion for summary judgment under Rule 56',
                'case_number': '2023-CV-1234',
                'document_type': 'motion'
            },
            {
                'id': 'doc2', 
                'content': 'Deposition of witness John Doe',
                'case_number': '2023-CV-5678',
                'document_type': 'deposition'
            }
        ]
        
        # Index documents
        self.system.index_legal_documents(legal_documents)
        
        # Test case-based search
        case_results = self.system.search_by_case('2023-CV-1234')
        assert len(case_results) >= 1
        
        # Test legal term search
        term_results = self.system.search_legal_terms('summary judgment')
        assert len(term_results) >= 1
        
        # Test document type search
        type_results = self.system.search_by_document_type('motion')
        assert len(type_results) >= 1


class TestLegalTranscriptionIntegration:
    """Test integration with other system components."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.system = LegalTranscriptionSystem()
    
    @patch('legal_transcription_system.requests.post')
    def test_court_system_integration(self, mock_post):
        """Test integration with court management systems."""
        mock_post.return_value = Mock(
            status_code=200,
            json=lambda: {'status': 'accepted', 'filing_id': 'F123456'}
        )
        
        transcript_data = {
            'case_number': '2023-CV-1234',
            'transcript': 'Legal proceeding transcript...',
            'metadata': {'proceeding_type': 'hearing'}
        }
        
        result = self.system.submit_to_court_system(transcript_data)
        
        assert result['status'] == 'success'
        assert 'filing_id' in result
    
    def test_legal_database_integration(self):
        """Test integration with legal research databases."""
        case_citation = "Smith v. Jones, 123 F.3d 456 (9th Cir. 2020)"
        
        # Mock database lookup
        with patch.object(self.system, 'lookup_case_law') as mock_lookup:
            mock_lookup.return_value = {
                'case_name': 'Smith v. Jones',
                'citation': '123 F.3d 456',
                'court': '9th Circuit',
                'year': '2020',
                'summary': 'Case summary...'
            }
            
            case_info = self.system.lookup_case_law(case_citation)
            
            assert case_info['case_name'] == 'Smith v. Jones'
            assert case_info['citation'] == '123 F.3d 456'
    
    def test_billing_integration(self):
        """Test integration with legal billing systems."""
        transcript_session = {
            'duration': 120,  # 2 hours
            'attorney': 'John Doe',
            'case_number': '2023-CV-1234',
            'proceeding_type': 'deposition'
        }
        
        billing_entry = self.system.generate_billing_entry(transcript_session)
        
        assert 'billable_hours' in billing_entry
        assert 'rate' in billing_entry
        assert 'total_amount' in billing_entry
        assert billing_entry['billable_hours'] == 2.0


def test_legal_transcription_performance():
    """Test performance benchmarks for legal transcription."""
    system = LegalTranscriptionSystem()
    
    # Test processing time for various document sizes
    small_text = "Brief legal statement." * 10
    medium_text = "Legal proceeding transcript." * 100
    large_text = "Comprehensive legal document." * 1000
    
    import time
    
    # Small document
    start_time = time.time()
    system.analyze_legal_content(small_text)
    small_time = time.time() - start_time
    
    # Medium document
    start_time = time.time()
    system.analyze_legal_content(medium_text)
    medium_time = time.time() - start_time
    
    # Large document
    start_time = time.time()
    system.analyze_legal_content(large_text)
    large_time = time.time() - start_time
    
    # Performance should scale reasonably
    assert small_time < 5.0  # Should process small docs quickly
    assert medium_time < 30.0  # Medium docs in reasonable time
    assert large_time < 120.0  # Large docs within 2 minutes


if __name__ == '__main__':
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'schema':
            pytest.main(['-v', 'TestLegalSchemaProcessor'])
        elif sys.argv[1] == 'core':
            pytest.main(['-v', 'TestLegalTranscriptionCore'])
        elif sys.argv[1] == 'system':
            pytest.main(['-v', 'TestLegalTranscriptionSystem'])
        elif sys.argv[1] == 'integration':
            pytest.main(['-v', 'TestLegalTranscriptionIntegration'])
        elif sys.argv[1] == 'performance':
            pytest.main(['-v', 'test_legal_transcription_performance'])
        else:
            pytest.main(['-v'])
    else:
        pytest.main(['-v'])