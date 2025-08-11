#!/usr/bin/env python3
"""
Test suite for Hybrid Summarization API endpoints
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the API app
from api.app import app
from hybrid_summarization_system import (
    SummarizationRequest, SummaryResult, SummarizationType, 
    SummaryLength, SummaryStyle
)

# Create test client
client = TestClient(app)

class TestHybridSummarizationAPI:
    """Test cases for hybrid summarization API endpoints"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.test_text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines, 
        in contrast to the natural intelligence displayed by humans and animals. 
        Leading AI textbooks define the field as the study of "intelligent agents": 
        any device that perceives its environment and takes actions that maximize 
        its chance of successfully achieving its goals. Colloquially, the term 
        "artificial intelligence" is often used to describe machines that mimic 
        "cognitive" functions that humans associate with the human mind, such as 
        "learning" and "problem solving".
        """
        
        self.mock_summary_result = SummaryResult(
            summary="AI is intelligence demonstrated by machines, contrasting with natural intelligence. It involves intelligent agents that perceive environments and take goal-maximizing actions.",
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.SHORT,
            style=SummaryStyle.FORMAL,
            word_count=25,
            sentence_count=2,
            compression_ratio=4.2,
            quality_score=0.85,
            key_points=["AI is machine intelligence", "Involves intelligent agents"],
            extracted_sentences=["AI is intelligence demonstrated by machines.", "It involves intelligent agents."],
            confidence_score=0.9,
            processing_time=1.5,
            metadata={"original_word_count": 105},
            created_at="2024-01-01T12:00:00"
        )

    @patch('api.endpoints.hybrid_summarization.hybrid_summarizer')
    def test_create_summary_success(self, mock_summarizer):
        """Test successful summary creation"""
        # Mock the summarizer
        mock_summarizer.summarize = AsyncMock(return_value=self.mock_summary_result)
        
        # Test data
        request_data = {
            "text": self.test_text,
            "summary_type": "hybrid",
            "length": "short",
            "style": "formal"
        }
        
        # Make request
        response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["summary"] == self.mock_summary_result.summary
        assert data["data"]["word_count"] == 25
        assert data["data"]["quality_score"] == 0.85

    def test_create_summary_invalid_text(self):
        """Test summary creation with invalid text"""
        request_data = {
            "text": "",  # Empty text
            "summary_type": "hybrid"
        }
        
        response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_create_summary_missing_text(self):
        """Test summary creation with missing text field"""
        request_data = {
            "summary_type": "hybrid"
            # Missing text field
        }
        
        response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch('api.endpoints.hybrid_summarization.multi_doc_summarizer')
    def test_multi_document_summary_success(self, mock_multi_summarizer):
        """Test successful multi-document summary creation"""
        # Mock the multi-document summarizer
        mock_multi_summarizer.summarize_documents = AsyncMock(return_value=self.mock_summary_result)
        
        # Test data
        request_data = {
            "documents": [
                {"id": "doc1", "title": "AI Overview", "content": self.test_text},
                {"id": "doc2", "title": "ML Basics", "content": "Machine learning is a subset of AI..."}
            ],
            "summary_type": "hybrid",
            "length": "medium"
        }
        
        # Make request
        response = client.post("/api/v1/hybrid-summarization/multi-document", json=request_data)
        
        # Assertions
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data

    def test_multi_document_summary_empty_documents(self):
        """Test multi-document summary with empty documents list"""
        request_data = {
            "documents": [],  # Empty documents
            "summary_type": "hybrid"
        }
        
        response = client.post("/api/v1/hybrid-summarization/multi-document", json=request_data)
        assert response.status_code == 400  # Bad request

    def test_get_summary_types(self):
        """Test getting available summary types"""
        response = client.get("/api/v1/hybrid-summarization/types")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "summary_types" in data["data"]
        assert "lengths" in data["data"]
        assert "styles" in data["data"]
        
        # Check that we have expected types
        summary_types = [t["value"] for t in data["data"]["summary_types"]]
        assert "hybrid" in summary_types
        assert "extractive" in summary_types
        assert "abstractive" in summary_types

    @patch('api.endpoints.hybrid_summarization.personalizer')
    def test_set_user_preferences(self, mock_personalizer):
        """Test setting user preferences"""
        # Mock the personalizer
        mock_personalizer.create_user_profile = Mock()
        
        user_id = "test_user_123"
        preferences_data = {
            "preferred_length": "medium",
            "preferred_style": "technical",
            "focus_areas": ["AI", "machine learning"],
            "technical_level": "high",
            "include_examples": True,
            "language": "en"
        }
        
        response = client.post(
            f"/api/v1/hybrid-summarization/preferences/{user_id}",
            json=preferences_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == user_id

    @patch('api.endpoints.hybrid_summarization.personalizer')
    def test_get_user_preferences(self, mock_personalizer):
        """Test getting user preferences"""
        user_id = "test_user_123"
        mock_preferences = {
            'preferred_length': 'medium',
            'preferred_style': 'formal',
            'focus_areas': [],
            'technical_level': 'medium',
            'language': 'en'
        }
        
        # Mock the personalizer
        mock_personalizer.user_profiles = {user_id: mock_preferences}
        
        response = client.get(f"/api/v1/hybrid-summarization/preferences/{user_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["user_id"] == user_id
        assert data["data"]["preferences"]["preferred_length"] == "medium"

    @patch('api.endpoints.hybrid_summarization.hybrid_summarizer')
    def test_batch_summarization(self, mock_summarizer):
        """Test batch summarization"""
        # Mock the summarizer
        mock_summarizer.summarize = AsyncMock(return_value=self.mock_summary_result)
        
        # Test data - multiple requests
        requests_data = [
            {
                "text": "First text to summarize...",
                "summary_type": "hybrid",
                "length": "short"
            },
            {
                "text": "Second text to summarize...",
                "summary_type": "extractive",
                "length": "medium"
            }
        ]
        
        response = client.post("/api/v1/hybrid-summarization/batch", json=requests_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total"] == 2
        assert len(data["data"]["results"]) == 2

    def test_batch_summarization_too_many_requests(self):
        """Test batch summarization with too many requests"""
        # Create more than 10 requests (the limit)
        requests_data = [
            {
                "text": f"Text {i} to summarize...",
                "summary_type": "hybrid"
            }
            for i in range(15)  # More than the limit of 10
        ]
        
        response = client.post("/api/v1/hybrid-summarization/batch", json=requests_data)
        assert response.status_code == 400  # Bad request

    @patch('api.endpoints.hybrid_summarization.hybrid_summarizer')
    def test_health_check(self, mock_summarizer):
        """Test health check endpoint"""
        # Mock the summarizer for health check
        mock_health_result = SummaryResult(
            summary="Health check summary",
            summary_type=SummarizationType.EXTRACTIVE,
            length=SummaryLength.BRIEF,
            style=SummaryStyle.FORMAL,
            word_count=3,
            sentence_count=1,
            compression_ratio=2.0,
            quality_score=0.8,
            key_points=["Health check"],
            extracted_sentences=["Health check summary"],
            confidence_score=0.9,
            processing_time=0.1,
            metadata={},
            created_at="2024-01-01T12:00:00"
        )
        
        mock_summarizer.summarize = AsyncMock(return_value=mock_health_result)
        
        response = client.get("/api/v1/hybrid-summarization/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "healthy"
        assert "components" in data["data"]
        assert "test_result" in data["data"]

    def test_query_focused_summarization(self):
        """Test query-focused summarization"""
        request_data = {
            "text": self.test_text,
            "summary_type": "query_focused",
            "query": "What is artificial intelligence?",
            "length": "short"
        }
        
        with patch('api.endpoints.hybrid_summarization.hybrid_summarizer') as mock_summarizer:
            mock_summarizer.summarize = AsyncMock(return_value=self.mock_summary_result)
            
            response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_advanced_options(self):
        """Test summarization with advanced options"""
        request_data = {
            "text": self.test_text,
            "summary_type": "hybrid",
            "length": "custom",
            "max_sentences": 3,
            "max_words": 50,
            "focus_keywords": ["intelligence", "machines"],
            "exclude_keywords": ["textbooks"],
            "preserve_structure": True,
            "include_quotes": False
        }
        
        with patch('api.endpoints.hybrid_summarization.hybrid_summarizer') as mock_summarizer:
            mock_summarizer.summarize = AsyncMock(return_value=self.mock_summary_result)
            
            response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    def test_invalid_summary_type(self):
        """Test with invalid summary type"""
        request_data = {
            "text": self.test_text,
            "summary_type": "invalid_type",  # Invalid type
            "length": "medium"
        }
        
        with patch('api.endpoints.hybrid_summarization.hybrid_summarizer') as mock_summarizer:
            mock_summarizer.summarize = AsyncMock(return_value=self.mock_summary_result)
            
            response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
            
            # Should still work as it defaults to hybrid
            assert response.status_code == 200

    def test_invalid_max_values(self):
        """Test with invalid max sentences/words values"""
        request_data = {
            "text": self.test_text,
            "max_sentences": 100,  # Too high
            "max_words": 5000      # Too high
        }
        
        response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
        assert response.status_code == 422  # Validation error

    @patch('api.endpoints.hybrid_summarization.hybrid_summarizer')
    def test_summarization_error_handling(self, mock_summarizer):
        """Test error handling in summarization"""
        # Mock the summarizer to raise an exception
        mock_summarizer.summarize = AsyncMock(side_effect=Exception("Summarization failed"))
        
        request_data = {
            "text": self.test_text,
            "summary_type": "hybrid"
        }
        
        response = client.post("/api/v1/hybrid-summarization/summarize", json=request_data)
        assert response.status_code == 500  # Internal server error

class TestSummarizationUtils:
    """Test utility functions"""
    
    def test_enum_conversion(self):
        """Test enum conversion utility"""
        from api.endpoints.hybrid_summarization import _convert_enum_values
        
        request_data = {
            "text": "Test text",
            "summary_type": "hybrid",
            "length": "medium",
            "style": "formal"
        }
        
        result = _convert_enum_values(request_data)
        
        assert result.summary_type == SummarizationType.HYBRID
        assert result.length == SummaryLength.MEDIUM
        assert result.style == SummaryStyle.FORMAL

    def test_result_conversion(self):
        """Test result conversion utility"""
        from api.endpoints.hybrid_summarization import _convert_result_to_api
        
        # Create a mock result
        mock_result = SummaryResult(
            summary="Test summary",
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.MEDIUM,
            style=SummaryStyle.FORMAL,
            word_count=10,
            sentence_count=2,
            compression_ratio=3.0,
            quality_score=0.8,
            key_points=["Point 1", "Point 2"],
            extracted_sentences=["Sentence 1", "Sentence 2"],
            confidence_score=0.9,
            processing_time=1.0,
            metadata={"test": "data"},
            created_at="2024-01-01T12:00:00"
        )
        
        api_result = _convert_result_to_api(mock_result)
        
        assert api_result.summary == "Test summary"
        assert api_result.summary_type == "hybrid"
        assert api_result.length == "medium"
        assert api_result.style == "formal"

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])