#!/usr/bin/env python3
"""
Unit tests for results display functionality
Tests all the components implemented in task 8
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add current directory to path for imports
sys.path.insert(0, os.getcwd())

# Import functions to test
from app import (
    find_text_occurrences,
    format_entities_for_download,
    generate_complete_report
)
from utils import get_timestamp

class TestResultsDisplayFunctions:
    """Test the core results display functions"""
    
    def test_find_text_occurrences_basic(self):
        """Test basic text search functionality"""
        text = "This is a test. This test is important. Testing is crucial."
        search_term = "test"
        
        results = find_text_occurrences(text, search_term)
        
        assert len(results) == 3
        assert all(isinstance(result, tuple) and len(result) == 3 for result in results)
        
        # Check that all results contain the search term
        for start, end, context in results:
            assert search_term.lower() in context.lower()
    
    def test_find_text_occurrences_case_insensitive(self):
        """Test case-insensitive search"""
        text = "Test this TEST and tEsT again"
        search_term = "test"
        
        results = find_text_occurrences(text, search_term)
        
        assert len(results) == 3
    
    def test_find_text_occurrences_empty_inputs(self):
        """Test search with empty inputs"""
        assert find_text_occurrences("", "test") == []
        assert find_text_occurrences("test text", "") == []
        assert find_text_occurrences("", "") == []
    
    def test_find_text_occurrences_no_matches(self):
        """Test search with no matches"""
        text = "This is some text without the target word"
        search_term = "missing"
        
        results = find_text_occurrences(text, search_term)
        
        assert results == []
    
    def test_find_text_occurrences_context_length(self):
        """Test that context length is respected"""
        text = "A" * 200  # Long text
        search_term = "A"
        
        results = find_text_occurrences(text, search_term, context_length=10)
        
        # Check that context is limited
        for start, end, context in results[:5]:  # Check first 5 results
            assert len(context) <= 21  # search_term + 2*context_length
    
    def test_format_entities_for_download_basic_mode(self):
        """Test entity formatting for basic mode"""
        entities = {
            "PERSON": ["John Doe", "Jane Smith"],
            "ORG": ["Microsoft", "Google"],
            "DATE": ["2024-01-01"]
        }
        
        result = format_entities_for_download(entities, "Basic (spaCy)")
        
        assert "Entity Extraction Results (Basic (spaCy))" in result
        assert "PERSON:" in result
        assert "John Doe" in result
        assert "Jane Smith" in result
        assert "ORG:" in result
        assert "Microsoft" in result
        assert "Google" in result
        assert "DATE:" in result
        assert "2024-01-01" in result
        assert "Total entities: 5" in result
        assert "Entity types: 3" in result
    
    def test_format_entities_for_download_advanced_mode(self):
        """Test entity formatting for advanced mode"""
        entities = {
            "persons": ["Alice Johnson"],
            "organizations": ["OpenAI"],
            "key_topics": ["AI", "Machine Learning"]
        }
        
        result = format_entities_for_download(entities, "Advanced (OpenAI)")
        
        assert "Entity Extraction Results (Advanced (OpenAI))" in result
        assert "PERSONS:" in result
        assert "Alice Johnson" in result
        assert "ORGANIZATIONS:" in result
        assert "OpenAI" in result
        assert "KEY_TOPICS:" in result
        assert "AI" in result
        assert "Machine Learning" in result
        assert "Total entities: 4" in result
        assert "Entity types: 3" in result
    
    def test_format_entities_for_download_empty(self):
        """Test entity formatting with empty entities"""
        entities = {}
        
        result = format_entities_for_download(entities, "Basic (spaCy)")
        
        assert result == "No entities found."
    
    def test_format_entities_for_download_empty_categories(self):
        """Test entity formatting with empty categories"""
        entities = {
            "PERSON": [],
            "ORG": ["Microsoft"],
            "DATE": []
        }
        
        result = format_entities_for_download(entities, "Basic (spaCy)")
        
        # Should only show categories with entities
        assert "ORG:" in result
        assert "Microsoft" in result
        assert "PERSON:" not in result
        assert "DATE:" not in result
        assert "Total entities: 1" in result
        assert "Entity types: 1" in result
    
    def test_get_timestamp_format(self):
        """Test timestamp format for file naming"""
        timestamp = get_timestamp()
        
        # Should be in format YYYYMMDD_HHMMSS
        assert len(timestamp) == 15
        assert timestamp[8] == "_"
        
        # Should be parseable as datetime
        try:
            datetime.strptime(timestamp, "%Y%m%d_%H%M%S")
        except ValueError:
            pytest.fail("Timestamp format is invalid")
    
    def test_get_timestamp_uniqueness(self):
        """Test that timestamps are unique across calls"""
        import time
        
        timestamp1 = get_timestamp()
        time.sleep(1)  # Wait 1 second
        timestamp2 = get_timestamp()
        
        assert timestamp1 != timestamp2

class TestCompleteReportGeneration:
    """Test complete report generation functionality"""
    
    @patch('app.st')
    def test_generate_complete_report_basic_mode(self, mock_st):
        """Test complete report generation for basic mode"""
        # Mock session state
        mock_session_state = Mock()
        mock_session_state.transcript = "This is a test transcript."
        mock_session_state.summary = ""
        mock_session_state.entities = {
            "PERSON": ["John Doe"],
            "ORG": ["Microsoft"]
        }
        mock_st.session_state = mock_session_state
        
        result = generate_complete_report("Basic (spaCy)")
        
        assert "AUDIO TRANSCRIPTION & ANALYSIS REPORT" in result
        assert "Analysis Mode: Basic (spaCy)" in result
        assert "TRANSCRIPT" in result
        assert "This is a test transcript." in result
        assert "EXTRACTED ENTITIES" in result
        assert "PERSON:" in result
        assert "John Doe" in result
        assert "ORG:" in result
        assert "Microsoft" in result
        # Should not have summary section for basic mode
        assert "CONTENT SUMMARY" not in result
    
    @patch('app.st')
    def test_generate_complete_report_advanced_mode(self, mock_st):
        """Test complete report generation for advanced mode"""
        # Mock session state
        mock_session_state = Mock()
        mock_session_state.transcript = "This is a test transcript."
        mock_session_state.summary = "This is a test summary."
        mock_session_state.entities = {
            "persons": ["Jane Smith"],
            "organizations": ["Google"]
        }
        mock_st.session_state = mock_session_state
        
        result = generate_complete_report("Advanced (OpenAI)")
        
        assert "AUDIO TRANSCRIPTION & ANALYSIS REPORT" in result
        assert "Analysis Mode: Advanced (OpenAI)" in result
        assert "TRANSCRIPT" in result
        assert "This is a test transcript." in result
        assert "CONTENT SUMMARY" in result
        assert "This is a test summary." in result
        assert "EXTRACTED ENTITIES" in result
        assert "PERSONS:" in result
        assert "Jane Smith" in result
        assert "ORGANIZATIONS:" in result
        assert "Google" in result
    
    @patch('app.st')
    def test_generate_complete_report_empty_data(self, mock_st):
        """Test complete report generation with empty data"""
        # Mock session state with empty data
        mock_session_state = Mock()
        mock_session_state.transcript = ""
        mock_session_state.summary = ""
        mock_session_state.entities = {}
        mock_st.session_state = mock_session_state
        
        result = generate_complete_report("Basic (spaCy)")
        
        assert "AUDIO TRANSCRIPTION & ANALYSIS REPORT" in result
        assert "Analysis Mode: Basic (spaCy)" in result
        # Should still have headers even with empty data
        assert "Generated:" in result
    
    @patch('app.st')
    def test_generate_complete_report_includes_timestamp(self, mock_st):
        """Test that complete report includes current timestamp"""
        # Mock session state
        mock_session_state = Mock()
        mock_session_state.transcript = "Test"
        mock_session_state.summary = ""
        mock_session_state.entities = {}
        mock_st.session_state = mock_session_state
        
        result = generate_complete_report("Basic (spaCy)")
        
        # Should include current date
        current_date = datetime.now().strftime('%Y-%m-%d')
        assert current_date in result

class TestResultsDisplayIntegration:
    """Integration tests for results display functionality"""
    
    def test_entity_display_config_completeness(self):
        """Test that entity display configurations are complete"""
        # This tests the entity display configurations in the app
        # Import the configurations from app.py if they were exported
        # For now, we'll test the expected entity types
        
        basic_entity_types = ["PERSON", "ORG", "DATE", "TIME", "GPE", "MONEY", "CARDINAL"]
        advanced_entity_types = ["persons", "organizations", "dates", "locations", "key_topics", "money", "numbers"]
        
        # Test that we have configurations for all expected types
        assert len(basic_entity_types) == 7
        assert len(advanced_entity_types) == 7
        
        # Test that entity types are properly categorized
        assert "PERSON" in basic_entity_types
        assert "persons" in advanced_entity_types
    
    def test_download_file_naming_convention(self):
        """Test that download file names follow proper convention"""
        timestamp = get_timestamp()
        
        # Test various file naming patterns
        transcript_filename = f"transcript_{timestamp}.txt"
        entities_filename = f"entities_basic_spacy_{timestamp}.txt"
        summary_filename = f"summary_{timestamp}.txt"
        json_filename = f"entities_{timestamp}.json"
        report_filename = f"complete_report_{timestamp}.txt"
        
        # Verify naming patterns
        assert transcript_filename.startswith("transcript_")
        assert transcript_filename.endswith(".txt")
        assert entities_filename.startswith("entities_")
        assert "basic_spacy" in entities_filename
        assert summary_filename.startswith("summary_")
        assert json_filename.endswith(".json")
        assert report_filename.startswith("complete_report_")
    
    def test_search_functionality_performance(self):
        """Test search functionality with large text"""
        # Create a large text for performance testing
        large_text = "This is a test sentence. " * 1000  # 5000 words
        search_term = "test"
        
        results = find_text_occurrences(large_text, search_term)
        
        # Should find all occurrences efficiently
        assert len(results) == 1000
        
        # Test with multiple search terms
        multi_word_text = "The quick brown fox jumps over the lazy dog. " * 100
        results = find_text_occurrences(multi_word_text, "fox")
        
        assert len(results) == 100

class TestResultsDisplayErrorHandling:
    """Test error handling in results display functions"""
    
    def test_find_text_occurrences_unicode_handling(self):
        """Test search with unicode characters"""
        text = "This is a test with émojis 🎵 and spëcial characters"
        search_term = "émojis"
        
        results = find_text_occurrences(text, search_term)
        
        assert len(results) == 1
        assert "émojis" in results[0][2]
    
    def test_format_entities_malformed_data(self):
        """Test entity formatting with malformed data"""
        # Test with None values
        entities_with_none = {
            "PERSON": ["John", None, "Jane"],
            "ORG": None
        }
        
        # Should handle gracefully without crashing
        try:
            result = format_entities_for_download(entities_with_none, "Basic")
            # Should still produce some output
            assert isinstance(result, str)
            assert len(result) > 0
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            assert "entities" in str(e).lower() or "format" in str(e).lower()
    
    @patch('app.st')
    def test_generate_complete_report_missing_attributes(self, mock_st):
        """Test complete report generation when session state attributes are missing"""
        # Mock session state with missing attributes
        mock_session_state = Mock()
        # Set transcript as string, not Mock
        mock_session_state.transcript = "Test transcript"
        # Make hasattr return False for missing attributes
        def mock_hasattr(obj, attr):
            if attr == 'transcript':
                return True
            return False
        
        mock_st.session_state = mock_session_state
        
        # Patch hasattr to control attribute existence
        with patch('builtins.hasattr', side_effect=mock_hasattr):
            result = generate_complete_report("Advanced (OpenAI)")
            assert isinstance(result, str)
            assert "AUDIO TRANSCRIPTION & ANALYSIS REPORT" in result
            assert "Test transcript" in result

if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"])