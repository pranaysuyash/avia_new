# Unit tests for Advanced Named Entity Recognition Module

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from ner_advanced import (
    extract_entities_advanced,
    generate_script,
    analyze_sentiment,
    get_fallback_suggestions,
    _make_gpt_request_with_retry
)
from errors import NERError as AdvancedNERError

class TestAdvancedNER:
    """Test suite for advanced NER functionality"""
    
    @pytest.fixture
    def mock_openai_response(self):
        """Mock OpenAI API response for entity extraction"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.function_call = Mock()
        mock_response.choices[0].message.function_call.arguments = json.dumps({
            "summary": "Discussion about AI technology and its impact on business",
            "persons": ["John Smith", "Dr. Sarah Johnson"],
            "organizations": ["OpenAI", "Microsoft", "Google"],
            "dates": ["2024", "next quarter"],
            "locations": ["San Francisco", "Silicon Valley"],
            "key_topics": ["artificial intelligence", "machine learning", "business transformation"],
            "money": ["$1 million", "$50 billion market"],
            "numbers": ["85%", "2.5x improvement"]
        })
        return mock_response
    
    @pytest.fixture
    def mock_script_response(self):
        """Mock OpenAI API response for script generation"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = """
        Host: Welcome to Tech Talk! Today we're discussing the future of AI.
        
        Guest: Thanks for having me. AI is transforming how we work and live.
        
        Host: Can you give us some specific examples?
        
        Guest: Certainly. In healthcare, AI helps doctors diagnose diseases faster. In finance, it detects fraud in real-time.
        
        Host: That's fascinating. What should businesses know about implementing AI?
        
        Guest: Start small, focus on specific problems, and ensure you have quality data.
        """
        return mock_response
    
    @pytest.fixture
    def mock_sentiment_response(self):
        """Mock OpenAI API response for sentiment analysis"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = """
        {
            "positive": 0.7,
            "negative": 0.1,
            "neutral": 0.2,
            "confidence": 0.85
        }
        """
        return mock_response
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_extract_entities_advanced_success(self, mock_client, mock_openai_response):
        """Test successful entity extraction with GPT"""
        mock_client.chat.completions.create.return_value = mock_openai_response
        
        test_text = "John Smith from OpenAI discussed AI technology in San Francisco, mentioning a $1 million investment."
        
        entities, summary = extract_entities_advanced(test_text)
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify results structure
        assert isinstance(entities, dict)
        assert isinstance(summary, str)
        assert summary == "Discussion about AI technology and its impact on business"
        
        # Verify entity categories
        expected_categories = ["persons", "organizations", "dates", "locations", "key_topics", "money", "numbers"]
        for category in expected_categories:
            assert category in entities
            assert isinstance(entities[category], list)
        
        # Verify specific entities
        assert "John Smith" in entities["persons"]
        assert "OpenAI" in entities["organizations"]
        assert "San Francisco" in entities["locations"]
    
    def test_extract_entities_advanced_empty_text(self):
        """Test entity extraction with empty text"""
        entities, summary = extract_entities_advanced("")
        
        assert entities == {}
        assert summary == "No content to analyze"
    
    @patch.dict(os.environ, {}, clear=True)
    def test_extract_entities_advanced_no_api_key(self):
        """Test entity extraction without API key"""
        with pytest.raises(AdvancedNERError) as exc_info:
            extract_entities_advanced("test text")
        
        assert "OpenAI API key not configured" in str(exc_info.value)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_extract_entities_advanced_api_failure(self, mock_client):
        """Test entity extraction with API failure"""
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        with pytest.raises(AdvancedNERError) as exc_info:
            extract_entities_advanced("test text")
        
        assert "GPT API failed after" in str(exc_info.value)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_extract_entities_advanced_invalid_json(self, mock_client):
        """Test entity extraction with invalid JSON response"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.function_call = Mock()
        mock_response.choices[0].message.function_call.arguments = "invalid json"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(AdvancedNERError) as exc_info:
            extract_entities_advanced("test text")
        
        assert "Failed to parse GPT response" in str(exc_info.value)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_generate_script_success(self, mock_client, mock_script_response):
        """Test successful script generation"""
        mock_client.chat.completions.create.return_value = mock_script_response
        
        prompt = "Create a discussion about AI technology"
        script = generate_script(prompt, style="conversational")
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify script content
        assert isinstance(script, str)
        assert len(script) > 0
        assert "Host:" in script
        assert "Guest:" in script
        assert "AI" in script
    
    def test_generate_script_empty_prompt(self):
        """Test script generation with empty prompt"""
        with pytest.raises(AdvancedNERError) as exc_info:
            generate_script("")
        
        assert "Script prompt cannot be empty" in str(exc_info.value)
    
    @patch.dict(os.environ, {}, clear=True)
    def test_generate_script_no_api_key(self):
        """Test script generation without API key"""
        with pytest.raises(AdvancedNERError) as exc_info:
            generate_script("test prompt")
        
        assert "OpenAI API key not configured" in str(exc_info.value)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_generate_script_different_styles(self, mock_client, mock_script_response):
        """Test script generation with different styles"""
        mock_client.chat.completions.create.return_value = mock_script_response
        
        styles = ["conversational", "formal", "educational", "interview"]
        
        for style in styles:
            script = generate_script("Test prompt", style=style)
            assert isinstance(script, str)
            assert len(script) > 0
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_analyze_sentiment_success(self, mock_client, mock_sentiment_response):
        """Test successful sentiment analysis"""
        mock_client.chat.completions.create.return_value = mock_sentiment_response
        
        test_text = "I love this new technology! It's amazing and will help so many people."
        sentiment = analyze_sentiment(test_text)
        
        # Verify API was called
        mock_client.chat.completions.create.assert_called_once()
        
        # Verify sentiment structure
        required_keys = ["positive", "negative", "neutral", "confidence"]
        for key in required_keys:
            assert key in sentiment
            assert isinstance(sentiment[key], float)
            assert 0.0 <= sentiment[key] <= 1.0
        
        # Verify expected sentiment (should be positive)
        assert sentiment["positive"] == 0.7
        assert sentiment["negative"] == 0.1
        assert sentiment["neutral"] == 0.2
        assert sentiment["confidence"] == 0.85
    
    def test_analyze_sentiment_empty_text(self):
        """Test sentiment analysis with empty text"""
        sentiment = analyze_sentiment("")
        
        expected = {"positive": 0.0, "negative": 0.0, "neutral": 1.0, "confidence": 0.0}
        assert sentiment == expected
    
    @patch.dict(os.environ, {}, clear=True)
    def test_analyze_sentiment_no_api_key(self):
        """Test sentiment analysis without API key"""
        with pytest.raises(AdvancedNERError) as exc_info:
            analyze_sentiment("test text")
        
        assert "OpenAI API key not configured" in str(exc_info.value)
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_analyze_sentiment_invalid_response(self, mock_client):
        """Test sentiment analysis with invalid response format"""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = "This is not JSON format"
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Should return fallback values instead of raising error
        sentiment = analyze_sentiment("test text")
        
        required_keys = ["positive", "negative", "neutral", "confidence"]
        for key in required_keys:
            assert key in sentiment
            assert isinstance(sentiment[key], float)
    
    def test_get_fallback_suggestions(self):
        """Test fallback suggestions function"""
        suggestions = get_fallback_suggestions()
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Verify suggestions contain helpful information
        suggestion_text = " ".join(suggestions)
        assert "Basic Mode" in suggestion_text
        assert "API key" in suggestion_text
        assert "internet connection" in suggestion_text
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_make_gpt_request_with_retry_success(self, mock_client):
        """Test GPT request retry logic with successful response"""
        mock_response = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        
        messages = [{"role": "user", "content": "test"}]
        result = _make_gpt_request_with_retry(messages)
        
        assert result == mock_response
        mock_client.chat.completions.create.assert_called_once()
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    @patch('time.sleep')  # Mock sleep to speed up tests
    def test_make_gpt_request_with_retry_failure(self, mock_sleep, mock_client):
        """Test GPT request retry logic with persistent failure"""
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        messages = [{"role": "user", "content": "test"}]
        
        with pytest.raises(AdvancedNERError) as exc_info:
            _make_gpt_request_with_retry(messages, max_retries=2)
        
        assert "GPT API failed after 2 attempts" in str(exc_info.value)
        assert mock_client.chat.completions.create.call_count == 2
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    @patch('time.sleep')
    def test_make_gpt_request_with_retry_eventual_success(self, mock_sleep, mock_client):
        """Test GPT request retry logic with eventual success"""
        # Fail first call, succeed on second
        mock_response = Mock()
        mock_client.chat.completions.create.side_effect = [Exception("API Error"), mock_response]
        
        messages = [{"role": "user", "content": "test"}]
        result = _make_gpt_request_with_retry(messages, max_retries=3)
        
        assert result == mock_response
        assert mock_client.chat.completions.create.call_count == 2

class TestAdvancedNERIntegration:
    """Integration tests for advanced NER module"""
    
    @patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'})
    @patch('ner_advanced.client')
    def test_full_pipeline_entity_extraction(self, mock_client):
        """Test complete entity extraction pipeline"""
        # Mock successful entity extraction
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.function_call = Mock()
        mock_response.choices[0].message.function_call.arguments = json.dumps({
            "summary": "Business meeting discussing Q4 results",
            "persons": ["Alice Johnson", "Bob Smith"],
            "organizations": ["TechCorp", "DataSystems Inc"],
            "dates": ["Q4 2024", "January 15th"],
            "locations": ["New York", "headquarters"],
            "key_topics": ["quarterly results", "revenue growth", "market expansion"],
            "money": ["$2.5M revenue", "$500K profit"],
            "numbers": ["25% growth", "150 employees"]
        })
        
        mock_client.chat.completions.create.return_value = mock_response
        
        # Test with realistic business content
        test_text = """
        In our Q4 2024 meeting at headquarters in New York, Alice Johnson presented 
        the quarterly results to Bob Smith. TechCorp achieved $2.5M revenue with 
        $500K profit, showing 25% growth. DataSystems Inc partnership helped us 
        reach 150 employees. We're planning market expansion for January 15th.
        """
        
        entities, summary = extract_entities_advanced(test_text)
        
        # Verify comprehensive extraction
        assert len(entities["persons"]) == 2
        assert len(entities["organizations"]) == 2
        assert len(entities["dates"]) == 2
        assert len(entities["locations"]) == 2
        assert len(entities["key_topics"]) == 3
        assert len(entities["money"]) == 2
        assert len(entities["numbers"]) == 2
        
        assert "Business meeting discussing Q4 results" in summary

if __name__ == "__main__":
    pytest.main([__file__, "-v"])