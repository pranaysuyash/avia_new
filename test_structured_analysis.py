#!/usr/bin/env python3
"""
Test suite for structured analysis with JSON schema validation
Tests domain-specific templates and schema validation functionality
"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import modules to test
from structured_analysis import (
    StructuredAnalyzer, AnalysisTemplate, AnalysisResult,
    structured_analyzer, get_available_templates, analyze_with_schema,
    validate_analysis_result, export_analysis
)
from errors import NERError, APIError, ErrorCode

class TestStructuredAnalyzer:
    """Test the StructuredAnalyzer class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = StructuredAnalyzer()
        
        # Sample test data
        self.sample_medical_text = """
        Patient John Doe, age 45, came in for a consultation today. 
        He reported chest pain and shortness of breath. 
        Dr. Smith examined him and prescribed Lisinopril 10mg daily.
        Follow-up appointment scheduled for next week.
        """
        
        self.sample_business_text = """
        Meeting with Sarah Johnson and Mike Chen from Marketing department.
        Discussed Q4 budget allocation of $50,000 for new campaign.
        Action item: Sarah to prepare presentation by Friday.
        Next meeting scheduled for December 15th.
        """
        
        self.sample_legal_text = """
        Case No. 2024-CV-1234, Smith vs. Johnson.
        Attorney Williams representing plaintiff.
        Motion to dismiss filed under Rule 12(b)(6).
        Hearing scheduled for January 10, 2024.
        """
    
    def test_initialization(self):
        """Test analyzer initialization"""
        assert self.analyzer is not None
        assert len(self.analyzer.templates) > 0
        
        # Check default templates are loaded
        template_names = list(self.analyzer.templates.keys())
        assert "medical_consultation" in template_names
        assert "legal_proceeding" in template_names
        assert "business_meeting" in template_names
        assert "educational_content" in template_names
    
    def test_get_templates(self):
        """Test template retrieval"""
        # Get all templates
        all_templates = self.analyzer.get_templates()
        assert len(all_templates) >= 4
        
        # Get templates by domain
        medical_templates = self.analyzer.get_templates("medical")
        assert len(medical_templates) >= 1
        assert all(t.domain == "medical" for t in medical_templates)
        
        business_templates = self.analyzer.get_templates("business")
        assert len(business_templates) >= 1
        assert all(t.domain == "business" for t in business_templates)
    
    def test_get_template(self):
        """Test getting specific template"""
        template = self.analyzer.get_template("medical_consultation")
        assert template is not None
        assert template.name == "medical_consultation"
        assert template.domain == "medical"
        assert "schema" in template.__dict__
        assert "prompt_template" in template.__dict__
        
        # Test non-existent template
        assert self.analyzer.get_template("non_existent") is None
    
    def test_validate_data(self):
        """Test data validation against schema"""
        template = self.analyzer.get_template("medical_consultation")
        
        # Valid data
        valid_data = {
            "summary": "Patient consultation completed",
            "symptoms": ["chest pain", "shortness of breath"],
            "medications": [{"name": "Lisinopril", "dosage": "10mg"}]
        }
        
        errors = self.analyzer.validate_data(valid_data, template.schema)
        assert len(errors) == 0
        
        # Invalid data (missing required field)
        invalid_data = {
            "symptoms": ["chest pain"]
            # Missing required "summary" field
        }
        
        errors = self.analyzer.validate_data(invalid_data, template.schema)
        assert len(errors) > 0
    
    def test_calculate_confidence(self):
        """Test confidence calculation"""
        template = self.analyzer.get_template("medical_consultation")
        
        # Complete data
        complete_data = {
            "summary": "Complete consultation",
            "symptoms": ["symptom1"],
            "diagnoses": ["diagnosis1"],
            "medications": [{"name": "med1"}],
            "healthcare_providers": ["Dr. Smith"]
        }
        
        confidence = self.analyzer._calculate_confidence(complete_data, template)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be relatively high for complete data
        
        # Minimal data
        minimal_data = {
            "summary": "Minimal consultation"
        }
        
        confidence_minimal = self.analyzer._calculate_confidence(minimal_data, template)
        assert confidence_minimal < confidence  # Should be lower than complete data
    
    def test_add_template(self):
        """Test adding custom template"""
        custom_schema = {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"}
            },
            "required": ["title"]
        }
        
        custom_template = AnalysisTemplate(
            name="test_template",
            description="Test template",
            schema=custom_schema,
            prompt_template="Test prompt",
            domain="test"
        )
        
        initial_count = len(self.analyzer.templates)
        self.analyzer.add_template(custom_template)
        
        assert len(self.analyzer.templates) == initial_count + 1
        assert "test_template" in self.analyzer.templates
        
        retrieved = self.analyzer.get_template("test_template")
        assert retrieved.name == "test_template"
        assert retrieved.domain == "test"
    
    def test_create_custom_template(self):
        """Test creating custom template"""
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"}
            },
            "required": ["summary"]
        }
        
        template = self.analyzer.create_custom_template(
            name="custom_test",
            description="Custom test template",
            domain="custom",
            schema=schema,
            prompt_template="Custom prompt"
        )
        
        assert template.name == "custom_test"
        assert template.domain == "custom"
        assert template.version == "custom"
        assert "custom_test" in self.analyzer.templates
    
    @patch('structured_analysis.OpenAI')
    def test_analyze_with_template_success(self, mock_openai_class):
        """Test successful analysis with template"""
        # Mock OpenAI response
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "summary": "Test summary",
            "symptoms": ["test symptom"],
            "medications": [{"name": "test med"}]
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Set up environment
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            result = self.analyzer.analyze_with_template(
                self.sample_medical_text, 
                "medical_consultation"
            )
        
        assert isinstance(result, AnalysisResult)
        assert result.template_name == "medical_consultation"
        assert result.domain == "medical"
        assert "summary" in result.data
        assert result.confidence > 0
        assert result.processing_time > 0
    
    @patch('structured_analysis.OpenAI')
    def test_analyze_with_template_invalid_json(self, mock_openai_class):
        """Test analysis with invalid JSON response"""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON response"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            with pytest.raises(NERError) as exc_info:
                self.analyzer.analyze_with_template(
                    self.sample_medical_text, 
                    "medical_consultation"
                )
            
            assert exc_info.value.error_code == ErrorCode.NER_PROCESSING_ERROR
    
    def test_analyze_with_template_no_api_key(self):
        """Test analysis without API key"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(APIError) as exc_info:
                self.analyzer.analyze_with_template(
                    self.sample_medical_text, 
                    "medical_consultation"
                )
            
            assert exc_info.value.error_code == ErrorCode.API_KEY_MISSING
    
    def test_analyze_with_template_empty_text(self):
        """Test analysis with empty text"""
        with pytest.raises(NERError) as exc_info:
            self.analyzer.analyze_with_template("", "medical_consultation")
        
        assert exc_info.value.error_code == ErrorCode.NER_INVALID_INPUT
    
    def test_analyze_with_template_invalid_template(self):
        """Test analysis with invalid template"""
        with pytest.raises(NERError) as exc_info:
            self.analyzer.analyze_with_template(
                self.sample_medical_text, 
                "non_existent_template"
            )
        
        assert exc_info.value.error_code == ErrorCode.NER_INVALID_INPUT
    
    def test_export_result_json(self):
        """Test JSON export"""
        result = AnalysisResult(
            template_name="test_template",
            domain="test",
            data={"summary": "test"},
            confidence=0.8,
            processing_time=1.5,
            timestamp=datetime.now().isoformat()
        )
        
        json_export = self.analyzer.export_result(result, "json")
        
        # Should be valid JSON
        parsed = json.loads(json_export)
        assert parsed["template_name"] == "test_template"
        assert parsed["domain"] == "test"
        assert parsed["confidence"] == 0.8
    
    def test_export_result_csv(self):
        """Test CSV export"""
        result = AnalysisResult(
            template_name="test_template",
            domain="test",
            data={"summary": "test", "items": ["item1", "item2"]},
            confidence=0.8,
            processing_time=1.5,
            timestamp=datetime.now().isoformat()
        )
        
        csv_export = self.analyzer.export_result(result, "csv")
        
        # Should contain CSV headers and data
        assert "Field,Value" in csv_export
        assert "test_template" in csv_export
        assert "test" in csv_export
    
    def test_export_result_invalid_format(self):
        """Test export with invalid format"""
        result = AnalysisResult(
            template_name="test",
            domain="test",
            data={},
            confidence=0.5,
            processing_time=1.0,
            timestamp=datetime.now().isoformat()
        )
        
        with pytest.raises(ValueError):
            self.analyzer.export_result(result, "invalid_format")

class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_get_available_templates(self):
        """Test getting available templates"""
        templates = get_available_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Check structure
        for template in templates:
            assert "name" in template
            assert "description" in template
            assert "domain" in template
            assert "version" in template
        
        # Test domain filtering
        medical_templates = get_available_templates("medical")
        assert all(t["domain"] == "medical" for t in medical_templates)
    
    @patch('structured_analysis.structured_analyzer.analyze_with_template')
    def test_analyze_with_schema(self, mock_analyze):
        """Test analyze_with_schema convenience function"""
        mock_result = AnalysisResult(
            template_name="test",
            domain="test",
            data={"summary": "test"},
            confidence=0.8,
            processing_time=1.0,
            timestamp=datetime.now().isoformat()
        )
        
        mock_analyze.return_value = mock_result
        
        result_dict = analyze_with_schema("test text", "test_template")
        
        assert isinstance(result_dict, dict)
        assert "template_name" in result_dict
        assert "data" in result_dict
        
        mock_analyze.assert_called_once_with("test text", "test_template")
    
    def test_validate_analysis_result(self):
        """Test validation convenience function"""
        # Valid data for medical template
        valid_data = {
            "summary": "Test summary",
            "symptoms": ["symptom1"]
        }
        
        errors = validate_analysis_result(valid_data, "medical_consultation")
        assert len(errors) == 0
        
        # Invalid data
        invalid_data = {}  # Missing required summary
        
        errors = validate_analysis_result(invalid_data, "medical_consultation")
        assert len(errors) > 0
        
        # Non-existent template
        errors = validate_analysis_result(valid_data, "non_existent")
        assert len(errors) > 0
        assert "not found" in errors[0]
    
    def test_export_analysis(self):
        """Test export convenience function"""
        result = AnalysisResult(
            template_name="test",
            domain="test",
            data={"summary": "test"},
            confidence=0.8,
            processing_time=1.0,
            timestamp=datetime.now().isoformat()
        )
        
        json_export = export_analysis(result, "json")
        assert isinstance(json_export, str)
        
        # Should be valid JSON
        parsed = json.loads(json_export)
        assert "template_name" in parsed

class TestDomainSpecificTemplates:
    """Test domain-specific template functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = StructuredAnalyzer()
    
    def test_medical_template_schema(self):
        """Test medical template schema structure"""
        template = self.analyzer.get_template("medical_consultation")
        
        assert template is not None
        assert template.domain == "medical"
        
        schema = template.schema
        properties = schema.get("properties", {})
        
        # Check required medical fields
        assert "summary" in properties
        assert "symptoms" in properties
        assert "medications" in properties
        assert "healthcare_providers" in properties
        
        # Check required fields
        required = schema.get("required", [])
        assert "summary" in required
    
    def test_legal_template_schema(self):
        """Test legal template schema structure"""
        template = self.analyzer.get_template("legal_proceeding")
        
        assert template is not None
        assert template.domain == "legal"
        
        schema = template.schema
        properties = schema.get("properties", {})
        
        # Check required legal fields
        assert "summary" in properties
        assert "parties" in properties
        assert "legal_issues" in properties
        assert "case_info" in properties
    
    def test_business_template_schema(self):
        """Test business template schema structure"""
        template = self.analyzer.get_template("business_meeting")
        
        assert template is not None
        assert template.domain == "business"
        
        schema = template.schema
        properties = schema.get("properties", {})
        
        # Check required business fields
        assert "summary" in properties
        assert "attendees" in properties
        assert "action_items" in properties
        assert "decisions" in properties
    
    def test_educational_template_schema(self):
        """Test educational template schema structure"""
        template = self.analyzer.get_template("educational_content")
        
        assert template is not None
        assert template.domain == "educational"
        
        schema = template.schema
        properties = schema.get("properties", {})
        
        # Check required educational fields
        assert "summary" in properties
        assert "learning_objectives" in properties
        assert "key_concepts" in properties
        assert "topics_covered" in properties

class TestIntegrationScenarios:
    """Test integration scenarios and edge cases"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.analyzer = StructuredAnalyzer()
    
    @patch('structured_analysis.OpenAI')
    def test_end_to_end_medical_analysis(self, mock_openai_class):
        """Test complete medical analysis workflow"""
        # Mock OpenAI response with realistic medical data
        mock_client = Mock()
        mock_openai_class.return_value = mock_client
        
        medical_response = {
            "summary": "Patient consultation for chest pain and shortness of breath",
            "patient_info": {
                "age": "45",
                "gender": "male"
            },
            "symptoms": ["chest pain", "shortness of breath"],
            "diagnoses": ["possible angina"],
            "medications": [
                {
                    "name": "Lisinopril",
                    "dosage": "10mg",
                    "frequency": "daily"
                }
            ],
            "healthcare_providers": ["Dr. Smith"],
            "follow_up": ["Follow-up appointment in one week"]
        }
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(medical_response)
        mock_client.chat.completions.create.return_value = mock_response
        
        medical_text = """
        Patient John Doe, 45-year-old male, presented with chest pain and shortness of breath.
        Dr. Smith conducted examination and diagnosed possible angina.
        Prescribed Lisinopril 10mg daily.
        Follow-up appointment scheduled for next week.
        """
        
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            result = self.analyzer.analyze_with_template(medical_text, "medical_consultation")
        
        # Verify result structure
        assert result.template_name == "medical_consultation"
        assert result.domain == "medical"
        assert result.validation_errors is None or len(result.validation_errors) == 0
        
        # Verify data content
        data = result.data
        assert "summary" in data
        assert "symptoms" in data
        assert len(data["symptoms"]) > 0
        assert "medications" in data
        assert len(data["medications"]) > 0
        
        # Test export
        json_export = self.analyzer.export_result(result, "json")
        assert "Lisinopril" in json_export
        
        csv_export = self.analyzer.export_result(result, "csv")
        assert "chest pain" in csv_export
    
    def test_schema_validation_edge_cases(self):
        """Test schema validation with edge cases"""
        template = self.analyzer.get_template("medical_consultation")
        
        # Test with empty arrays (valid)
        data_with_empty_arrays = {
            "summary": "Test summary",
            "symptoms": [],
            "medications": []
        }
        
        errors = self.analyzer.validate_data(data_with_empty_arrays, template.schema)
        # Should not error on empty arrays for optional fields
        assert len(errors) == 0
        
        # Test with wrong data types
        data_wrong_types = {
            "summary": 123,  # Should be string
            "symptoms": "not an array"  # Should be array
        }
        
        errors = self.analyzer.validate_data(data_wrong_types, template.schema)
        assert len(errors) > 0
    
    def test_confidence_calculation_scenarios(self):
        """Test confidence calculation in various scenarios"""
        template = self.analyzer.get_template("business_meeting")
        
        # Empty data (only required fields)
        minimal_data = {"summary": "Minimal meeting"}
        confidence_minimal = self.analyzer._calculate_confidence(minimal_data, template)
        
        # Partial data
        partial_data = {
            "summary": "Meeting summary",
            "attendees": [{"name": "John"}],
            "decisions": [{"decision": "Approved budget"}]
        }
        confidence_partial = self.analyzer._calculate_confidence(partial_data, template)
        
        # Complete data
        complete_data = {
            "summary": "Complete meeting summary",
            "meeting_info": {"title": "Q4 Planning"},
            "attendees": [{"name": "John", "role": "Manager"}],
            "decisions": [{"decision": "Approved budget", "rationale": "Good ROI"}],
            "action_items": [{"task": "Prepare report", "assignee": "Sarah"}],
            "projects": [{"name": "Project X", "status": "On track"}]
        }
        confidence_complete = self.analyzer._calculate_confidence(complete_data, template)
        
        # Confidence should increase with more complete data
        assert confidence_minimal < confidence_partial < confidence_complete
        assert 0.0 <= confidence_minimal <= 1.0
        assert 0.0 <= confidence_partial <= 1.0
        assert 0.0 <= confidence_complete <= 1.0

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--tb=short"])