# Unit tests for basic NER entity extraction module

import pytest
from unittest.mock import patch, MagicMock
import ner_basic
from errors import NERError, AppError

class TestNERBasic:
    """Test suite for basic NER functionality"""
    
    def test_extract_entities_with_sample_text(self):
        """Test entity extraction with known sample text"""
        sample_text = """
        John Smith works at Microsoft Corporation in Seattle. 
        He met with Sarah Johnson on January 15, 2024 at 3:00 PM.
        They discussed the project with Google and Apple Inc.
        The meeting was scheduled for New York City.
        """
        
        # Mock spaCy model and entities
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        
        # Create mock entities
        mock_entities = [
            MagicMock(text="John Smith", label_="PERSON"),
            MagicMock(text="Microsoft Corporation", label_="ORG"),
            MagicMock(text="Seattle", label_="GPE"),
            MagicMock(text="Sarah Johnson", label_="PERSON"),
            MagicMock(text="January 15, 2024", label_="DATE"),
            MagicMock(text="3:00 PM", label_="TIME"),
            MagicMock(text="Google", label_="ORG"),
            MagicMock(text="Apple Inc", label_="ORG"),
            MagicMock(text="New York City", label_="GPE"),
        ]
        
        mock_doc.ents = mock_entities
        mock_nlp.return_value = mock_doc
        
        with patch('ner_basic._load_model', return_value=mock_nlp):
            result = ner_basic.extract_entities(sample_text)
            
            # Verify expected entity types are present
            assert "PERSON" in result
            assert "ORG" in result
            assert "GPE" in result
            assert "DATE" in result
            
            # Verify specific entities
            assert "John Smith" in result["PERSON"]
            assert "Sarah Johnson" in result["PERSON"]
            assert "Microsoft Corporation" in result["ORG"]
            assert "Google" in result["ORG"]
            assert "Apple Inc" in result["ORG"]
            assert "Seattle" in result["GPE"]
            assert "New York City" in result["GPE"]
    
    def test_extract_entities_empty_text(self):
        """Test entity extraction with empty text"""
        result = ner_basic.extract_entities("")
        assert result == {}
        
        result = ner_basic.extract_entities("   ")
        assert result == {}
        
        result = ner_basic.extract_entities(None)
        assert result == {}
    
    def test_extract_entities_no_entities(self):
        """Test entity extraction with text containing no entities"""
        sample_text = "This is a simple sentence with no named entities."
        
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        mock_doc.ents = []  # No entities
        mock_nlp.return_value = mock_doc
        
        with patch('ner_basic._load_model', return_value=mock_nlp):
            result = ner_basic.extract_entities(sample_text)
            assert result == {}
    
    def test_extract_entities_deduplication(self):
        """Test that duplicate entities are properly deduplicated"""
        sample_text = "John mentioned John Smith and John Smith again."
        
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        
        # Create duplicate entities
        mock_entities = [
            MagicMock(text="John", label_="PERSON"),
            MagicMock(text="John Smith", label_="PERSON"),
            MagicMock(text="John Smith", label_="PERSON"),  # Duplicate
        ]
        
        mock_doc.ents = mock_entities
        mock_nlp.return_value = mock_doc  # Fixed: should return mock_doc, not mock_nlp
        
        with patch('ner_basic._load_model', return_value=mock_nlp):
            result = ner_basic.extract_entities(sample_text)
            
            # Should have deduplicated entities
            assert len(result["PERSON"]) == 2
            assert "John" in result["PERSON"]
            assert "John Smith" in result["PERSON"]
    
    def test_get_entity_confidence(self):
        """Test entity confidence scoring"""
        sample_text = "John Smith works at Microsoft."
        
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        
        mock_entities = [
            MagicMock(text="John Smith", label_="PERSON"),
            MagicMock(text="Microsoft", label_="ORG"),
        ]
        
        mock_doc.ents = mock_entities
        mock_nlp.return_value = mock_doc
        
        with patch('ner_basic._load_model', return_value=mock_nlp):
            result = ner_basic.get_entity_confidence(sample_text)
            
            # Should have confidence scores for entities
            assert "PERSON" in result
            assert "ORG" in result
            assert "John Smith" in result["PERSON"]
            assert "Microsoft" in result["ORG"]
            
            # Confidence scores should be between 0 and 1
            assert 0 <= result["PERSON"]["John Smith"] <= 1
            assert 0 <= result["ORG"]["Microsoft"] <= 1
    
    def test_get_entity_confidence_empty_text(self):
        """Test confidence scoring with empty text"""
        result = ner_basic.get_entity_confidence("")
        assert result == {}
        
        result = ner_basic.get_entity_confidence(None)
        assert result == {}
    
    def test_filter_entities_by_type(self):
        """Test filtering entities by specified types"""
        entities = {
            "PERSON": ["John Smith", "Sarah Johnson"],
            "ORG": ["Microsoft", "Google"],
            "GPE": ["Seattle", "New York"],
            "DATE": ["January 15, 2024"]
        }
        
        # Filter for only PERSON and ORG
        result = ner_basic.filter_entities_by_type(entities, ["PERSON", "ORG"])
        
        assert "PERSON" in result
        assert "ORG" in result
        assert "GPE" not in result
        assert "DATE" not in result
        
        assert result["PERSON"] == ["John Smith", "Sarah Johnson"]
        assert result["ORG"] == ["Microsoft", "Google"]
    
    def test_filter_entities_empty_input(self):
        """Test filtering with empty inputs"""
        entities = {"PERSON": ["John Smith"]}
        
        # Empty entity types list
        result = ner_basic.filter_entities_by_type(entities, [])
        assert result == {}
        
        # Empty entities dict
        result = ner_basic.filter_entities_by_type({}, ["PERSON"])
        assert result == {}
        
        # None inputs
        result = ner_basic.filter_entities_by_type(None, ["PERSON"])
        assert result == {}
    
    def test_filter_entities_nonexistent_types(self):
        """Test filtering with non-existent entity types"""
        entities = {
            "PERSON": ["John Smith"],
            "ORG": ["Microsoft"]
        }
        
        # Request non-existent types
        result = ner_basic.filter_entities_by_type(entities, ["LOCATION", "MONEY"])
        assert result == {}
        
        # Mix of existing and non-existing types
        result = ner_basic.filter_entities_by_type(entities, ["PERSON", "LOCATION"])
        assert result == {"PERSON": ["John Smith"]}
    
    def test_model_loading_error(self):
        """Test handling of spaCy model loading errors"""
        with patch('ner_basic.spacy.load', side_effect=OSError("Model not found")):
            with pytest.raises(NERError, match="spaCy model not found"):
                ner_basic._load_model()
    
    def test_extract_entities_processing_error(self):
        """Test handling of processing errors during entity extraction"""
        sample_text = "Test text"
        
        with patch('ner_basic._load_model', side_effect=Exception("Processing error")):
            with pytest.raises(AppError, match="Processing error"):
                ner_basic.extract_entities(sample_text)
    
    def test_entity_categorization_mapping(self):
        """Test that spaCy entity labels are correctly mapped to our categories"""
        sample_text = "Test text"
        
        mock_nlp = MagicMock()
        mock_doc = MagicMock()
        
        # Test various spaCy entity types
        mock_entities = [
            MagicMock(text="John", label_="PERSON"),
            MagicMock(text="Microsoft", label_="ORG"),
            MagicMock(text="January 15, 2024", label_="DATE"),
            MagicMock(text="3:00 PM", label_="TIME"),
            MagicMock(text="Seattle", label_="GPE"),
        ]
        
        mock_doc.ents = mock_entities
        mock_nlp.return_value = mock_doc
        
        with patch('ner_basic._load_model', return_value=mock_nlp):
            result = ner_basic.extract_entities(sample_text)
            
            # Verify correct mapping
            assert "PERSON" in result and "John" in result["PERSON"]
            assert "ORG" in result and "Microsoft" in result["ORG"]
            assert "DATE" in result and "January 15, 2024" in result["DATE"]
            assert "DATE" in result and "3:00 PM" in result["DATE"]  # TIME mapped to DATE
            assert "GPE" in result and "Seattle" in result["GPE"]

if __name__ == "__main__":
    pytest.main([__file__])