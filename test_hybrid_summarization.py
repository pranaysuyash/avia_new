#!/usr/bin/env python3
"""
Test Suite for Hybrid Summarization System
Tests for Task 123: Build hybrid summarization system

This module provides comprehensive tests for:
- Extractive summarization
- Abstractive summarization  
- Hybrid summarization approaches
- Multi-document summarization
- Query-focused summarization
- Personalization features
"""

import unittest
import asyncio
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json

# Import the modules to test
try:
    from hybrid_summarization_system import (
        SummarizationService, SummarizationRequest, SummaryResult,
        SummarizationType, SummaryLength, SummaryStyle,
        ExtractiveSummarizer, AbstractiveSummarizer, HybridSummarizer,
        MultiDocumentSummarizer, SummarizationPersonalizer,
        TextProcessor
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure hybrid_summarization_system.py is in the same directory")
    exit(1)

class TestTextProcessor(unittest.TestCase):
    """Test cases for TextProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.processor = TextProcessor()
    
    def test_tokenize_sentences(self):
        """Test sentence tokenization"""
        text = "This is the first sentence. This is the second sentence! Is this the third?"
        sentences = self.processor.tokenize_sentences(text)
        
        self.assertEqual(len(sentences), 3)
        self.assertIn("This is the first sentence", sentences[0])
        self.assertIn("This is the second sentence", sentences[1])
        self.assertIn("Is this the third", sentences[2])
    
    def test_tokenize_words(self):
        """Test word tokenization"""
        text = "Hello, world! This is a test."
        words = self.processor.tokenize_words(text)
        
        self.assertIn("hello", words)
        self.assertIn("world", words)
        self.assertIn("test", words)
        self.assertNotIn(",", words)  # Punctuation should be filtered
    
    def test_remove_stop_words(self):
        """Test stop word removal"""
        words = ["the", "quick", "brown", "fox", "is", "running"]
        filtered = self.processor.remove_stop_words(words)
        
        self.assertNotIn("the", filtered)
        self.assertNotIn("is", filtered)
        self.assertIn("quick", filtered)
        self.assertIn("brown", filtered)
        self.assertIn("fox", filtered)
        self.assertIn("running", filtered)
    
    def test_calculate_sentence_similarity(self):
        """Test sentence similarity calculation"""
        sent1 = "The cat sat on the mat"
        sent2 = "A cat was sitting on a mat"
        sent3 = "The dog ran in the park"
        
        # Similar sentences should have higher similarity
        sim1 = self.processor.calculate_sentence_similarity(sent1, sent2)
        sim2 = self.processor.calculate_sentence_similarity(sent1, sent3)
        
        self.assertGreater(sim1, sim2)
        self.assertGreater(sim1, 0)
        self.assertLessEqual(sim1, 1)
    
    def test_extract_keywords(self):
        """Test keyword extraction"""
        text = "Machine learning algorithms are used in artificial intelligence. Machine learning is a subset of artificial intelligence."
        keywords = self.processor.extract_keywords(text, top_k=5)
        
        self.assertIn("machine", keywords)
        self.assertIn("learning", keywords)
        self.assertIn("artificial", keywords)
        self.assertIn("intelligence", keywords)

class TestExtractiveSummarizer(unittest.TestCase):
    """Test cases for ExtractiveSummarizer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.summarizer = ExtractiveSummarizer()
        self.sample_text = """
        Artificial intelligence (AI) is intelligence demonstrated by machines. 
        It contrasts with natural intelligence displayed by humans and animals.
        Leading AI textbooks define the field as the study of intelligent agents.
        These agents perceive their environment and take actions to maximize success.
        Machine learning is a core part of AI research.
        It builds models based on training data to make predictions.
        AI has been successful in many applications like game playing and medical diagnosis.
        However, some argue that AI progress may be slowing down.
        """
    
    def test_summarize_basic(self):
        """Test basic extractive summarization"""
        summary, extracted_sentences, confidence = self.summarizer.summarize(
            self.sample_text, num_sentences=3
        )
        
        self.assertIsInstance(summary, str)
        self.assertIsInstance(extracted_sentences, list)
        self.assertIsInstance(confidence, float)
        
        self.assertEqual(len(extracted_sentences), 3)
        self.assertGreater(len(summary), 0)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
    
    def test_summarize_with_keywords(self):
        """Test extractive summarization with focus keywords"""
        focus_keywords = ["machine", "learning", "AI"]
        
        summary, extracted_sentences, confidence = self.summarizer.summarize(
            self.sample_text, num_sentences=2, focus_keywords=focus_keywords
        )
        
        # Summary should contain focus keywords
        summary_lower = summary.lower()
        keyword_found = any(keyword.lower() in summary_lower for keyword in focus_keywords)
        self.assertTrue(keyword_found)
    
    def test_summarize_short_text(self):
        """Test summarization of text shorter than requested sentences"""
        short_text = "This is a short text."
        
        summary, extracted_sentences, confidence = self.summarizer.summarize(
            short_text, num_sentences=5
        )
        
        # Should return the original text
        self.assertEqual(summary.strip(), short_text.strip())
        self.assertEqual(confidence, 1.0)

class TestAbstractiveSummarizer(unittest.TestCase):
    """Test cases for AbstractiveSummarizer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.summarizer = AbstractiveSummarizer()
        self.sample_text = """
        Climate change refers to long-term shifts in global temperatures and weather patterns.
        While climate variations are natural, human activities have been the main driver since the 1800s.
        Burning fossil fuels generates greenhouse gas emissions that trap heat in Earth's atmosphere.
        The consequences include rising temperatures, melting ice caps, and extreme weather events.
        Addressing climate change requires reducing emissions and transitioning to renewable energy.
        """
    
    @patch('openai.OpenAI')
    async def test_summarize_with_openai_mock(self, mock_openai):
        """Test abstractive summarization with mocked OpenAI"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Climate change is caused by human activities and requires urgent action."
        
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        self.summarizer.openai_client = mock_client
        
        summary, confidence = await self.summarizer.summarize(
            self.sample_text, max_length=50, style=SummaryStyle.FORMAL
        )
        
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertGreaterEqual(confidence, 0)
        self.assertLessEqual(confidence, 1)
    
    async def test_summarize_fallback(self):
        """Test fallback when no AI services available"""
        # Disable AI services
        self.summarizer.openai_client = None
        self.summarizer.hf_summarizer = None
        
        summary, confidence = await self.summarizer.summarize(
            self.sample_text, max_length=50
        )
        
        # Should return fallback summary
        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)
        self.assertEqual(confidence, 0.3)  # Low confidence for fallback

class TestHybridSummarizer(unittest.TestCase):
    """Test cases for HybridSummarizer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.summarizer = HybridSummarizer()
        self.sample_text = """
        The Internet of Things (IoT) refers to the network of physical devices connected to the internet.
        These devices collect and share data through embedded sensors and software.
        IoT applications span smart homes, healthcare, transportation, and industrial automation.
        Benefits include improved efficiency, cost savings, and enhanced user experiences.
        However, IoT also raises concerns about privacy, security, and data management.
        The technology continues to evolve with advances in 5G, edge computing, and artificial intelligence.
        Successful IoT implementation requires careful planning and robust cybersecurity measures.
        """
    
    async def test_extractive_summarization(self):
        """Test extractive summarization through hybrid summarizer"""
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.EXTRACTIVE,
            length=SummaryLength.SHORT,
            style=SummaryStyle.FORMAL
        )
        
        result = await self.summarizer.summarize(request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary_type, SummarizationType.EXTRACTIVE)
        self.assertGreater(len(result.summary), 0)
        self.assertGreater(result.word_count, 0)
        self.assertGreater(result.compression_ratio, 1)
    
    async def test_abstractive_summarization(self):
        """Test abstractive summarization through hybrid summarizer"""
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.ABSTRACTIVE,
            length=SummaryLength.MEDIUM,
            style=SummaryStyle.TECHNICAL
        )
        
        result = await self.summarizer.summarize(request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary_type, SummarizationType.ABSTRACTIVE)
        self.assertGreater(len(result.summary), 0)
        self.assertGreater(result.quality_score, 0)
    
    async def test_hybrid_summarization(self):
        """Test hybrid summarization"""
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.MEDIUM,
            style=SummaryStyle.FORMAL
        )
        
        result = await self.summarizer.summarize(request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.summary_type, SummarizationType.HYBRID)
        self.assertGreater(len(result.summary), 0)
        self.assertGreater(len(result.key_points), 0)
    
    async def test_query_focused_summarization(self):
        """Test query-focused summarization"""
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.QUERY_FOCUSED,
            length=SummaryLength.SHORT,
            query="What are the benefits of IoT?"
        )
        
        result = await self.summarizer.summarize(request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertIn("benefits", result.summary.lower())
    
    def test_determine_target_length(self):
        """Test target length determination"""
        sentences, words = self.summarizer._determine_target_length(
            self.sample_text, SummaryLength.MEDIUM, None, None
        )
        
        self.assertIsInstance(sentences, int)
        self.assertIsInstance(words, int)
        self.assertGreater(sentences, 0)
        self.assertGreater(words, 0)
    
    def test_extract_key_points(self):
        """Test key point extraction"""
        summary = "IoT connects devices to the internet. It improves efficiency and user experience. Security concerns must be addressed."
        key_points = self.summarizer._extract_key_points(summary)
        
        self.assertIsInstance(key_points, list)
        self.assertGreater(len(key_points), 0)
        self.assertLessEqual(len(key_points), 5)
    
    def test_assess_quality(self):
        """Test summary quality assessment"""
        summary = "IoT devices are connected to the internet and collect data."
        original = self.sample_text
        confidence = 0.8
        
        quality = self.summarizer._assess_quality(summary, original, confidence)
        
        self.assertIsInstance(quality, float)
        self.assertGreaterEqual(quality, 0)
        self.assertLessEqual(quality, 1)

class TestMultiDocumentSummarizer(unittest.TestCase):
    """Test cases for MultiDocumentSummarizer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.summarizer = MultiDocumentSummarizer()
        self.sample_documents = [
            {
                'id': 'doc1',
                'title': 'AI in Healthcare',
                'content': 'Artificial intelligence is transforming healthcare through diagnostic tools, drug discovery, and personalized treatment plans. Machine learning algorithms can analyze medical images and detect diseases earlier than traditional methods.'
            },
            {
                'id': 'doc2', 
                'title': 'AI Ethics',
                'content': 'The development of AI systems raises important ethical questions about bias, privacy, and accountability. Ensuring fair and transparent AI requires careful consideration of data sources and algorithmic decision-making processes.'
            },
            {
                'id': 'doc3',
                'title': 'Future of AI',
                'content': 'The future of artificial intelligence includes advances in natural language processing, computer vision, and robotics. These developments will likely impact employment, education, and social interactions in significant ways.'
            }
        ]
    
    async def test_single_document_summarization(self):
        """Test multi-document summarizer with single document"""
        single_doc = [self.sample_documents[0]]
        
        request = SummarizationRequest(
            text="",  # Will be filled by summarizer
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.SHORT
        )
        
        result = await self.summarizer.summarize_documents(single_doc, request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertGreater(len(result.summary), 0)
    
    async def test_multi_document_summarization(self):
        """Test multi-document summarization"""
        request = SummarizationRequest(
            text="",
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.MEDIUM
        )
        
        result = await self.summarizer.summarize_documents(self.sample_documents, request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertGreater(len(result.summary), 0)
        self.assertEqual(result.metadata['document_count'], 3)
        self.assertIn('document_summaries', result.metadata)
        self.assertIn('combined_topics', result.metadata)
    
    async def test_empty_documents_error(self):
        """Test error handling for empty documents list"""
        request = SummarizationRequest(
            text="",
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.SHORT
        )
        
        with self.assertRaises(ValueError):
            await self.summarizer.summarize_documents([], request)

class TestSummarizationPersonalizer(unittest.TestCase):
    """Test cases for SummarizationPersonalizer class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.personalizer = SummarizationPersonalizer()
    
    def test_create_user_profile(self):
        """Test user profile creation"""
        user_id = "test_user"
        preferences = {
            'preferred_length': 'short',
            'preferred_style': 'technical',
            'focus_areas': ['technology', 'science'],
            'avoid_topics': ['politics'],
            'technical_level': 'high'
        }
        
        self.personalizer.create_user_profile(user_id, preferences)
        
        self.assertIn(user_id, self.personalizer.user_profiles)
        profile = self.personalizer.user_profiles[user_id]
        self.assertEqual(profile['preferred_length'], 'short')
        self.assertEqual(profile['preferred_style'], 'technical')
    
    def test_personalize_request(self):
        """Test request personalization"""
        user_id = "test_user"
        preferences = {
            'preferred_length': 'long',
            'preferred_style': 'casual',
            'focus_areas': ['business'],
            'language': 'en'
        }
        
        self.personalizer.create_user_profile(user_id, preferences)
        
        request = SummarizationRequest(
            text="Sample text",
            summary_type=SummarizationType.HYBRID
        )
        
        personalized_request = self.personalizer.personalize_request(request, user_id)
        
        self.assertEqual(personalized_request.length, SummaryLength.LONG)
        self.assertEqual(personalized_request.style, SummaryStyle.CASUAL)
        self.assertIn('business', personalized_request.focus_keywords)
    
    def test_personalize_nonexistent_user(self):
        """Test personalization for non-existent user"""
        request = SummarizationRequest(
            text="Sample text",
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.MEDIUM
        )
        
        original_length = request.length
        personalized_request = self.personalizer.personalize_request(request, "nonexistent_user")
        
        # Should return unchanged request
        self.assertEqual(personalized_request.length, original_length)

class TestSummarizationService(unittest.TestCase):
    """Test cases for SummarizationService class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = SummarizationService()
        self.sample_text = "This is a sample text for testing the summarization service. It contains multiple sentences to test the functionality."
    
    async def test_summarize_basic(self):
        """Test basic summarization through service"""
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.EXTRACTIVE,
            length=SummaryLength.SHORT
        )
        
        result = await self.service.summarize(request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertGreater(len(result.summary), 0)
    
    async def test_summarize_with_user_profile(self):
        """Test summarization with user personalization"""
        user_id = "test_user"
        preferences = {
            'preferred_length': 'brief',
            'preferred_style': 'formal'
        }
        
        self.service.create_user_profile(user_id, preferences)
        
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.HYBRID
        )
        
        result = await self.service.summarize(request, user_id=user_id)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertEqual(result.length, SummaryLength.BRIEF)
        self.assertEqual(result.style, SummaryStyle.FORMAL)
    
    def test_get_summary_templates(self):
        """Test summary template retrieval"""
        templates = self.service.get_summary_templates()
        
        self.assertIsInstance(templates, dict)
        self.assertIn('meeting_minutes', templates)
        self.assertIn('research_paper', templates)
        self.assertIn('news_article', templates)
        
        # Check template structure
        meeting_template = templates['meeting_minutes']
        self.assertIn('summary_type', meeting_template)
        self.assertIn('length', meeting_template)
        self.assertIn('style', meeting_template)
    
    def test_cache_functionality(self):
        """Test caching functionality"""
        # Clear cache first
        self.service.clear_cache()
        
        initial_stats = self.service.get_cache_stats()
        self.assertEqual(initial_stats['cache_size'], 0)
        
        # Cache should work (tested indirectly through repeated requests)
        request = SummarizationRequest(
            text=self.sample_text,
            summary_type=SummarizationType.EXTRACTIVE
        )
        
        cache_key = self.service._generate_cache_key(request)
        self.assertIsInstance(cache_key, str)
        self.assertGreater(len(cache_key), 0)

class TestIntegration(unittest.TestCase):
    """Integration tests for the complete summarization system"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.service = SummarizationService()
    
    async def test_end_to_end_workflow(self):
        """Test complete end-to-end summarization workflow"""
        # Create user profile
        user_id = "integration_test_user"
        preferences = {
            'preferred_length': 'medium',
            'preferred_style': 'technical',
            'focus_areas': ['technology', 'innovation'],
            'technical_level': 'high'
        }
        
        self.service.create_user_profile(user_id, preferences)
        
        # Test different summarization types
        sample_text = """
        Quantum computing represents a revolutionary approach to information processing.
        Unlike classical computers that use bits, quantum computers use quantum bits or qubits.
        These qubits can exist in multiple states simultaneously through superposition.
        Quantum entanglement allows qubits to be correlated in ways that classical systems cannot achieve.
        Major tech companies are investing heavily in quantum computing research.
        Applications include cryptography, drug discovery, and optimization problems.
        However, quantum computers are still in early development stages.
        They require extremely cold temperatures and are prone to errors.
        """
        
        test_cases = [
            SummarizationType.EXTRACTIVE,
            SummarizationType.ABSTRACTIVE,
            SummarizationType.HYBRID
        ]
        
        for summary_type in test_cases:
            request = SummarizationRequest(
                text=sample_text,
                summary_type=summary_type,
                focus_keywords=['quantum', 'computing']
            )
            
            result = await self.service.summarize(request, user_id=user_id)
            
            # Verify result structure
            self.assertIsInstance(result, SummaryResult)
            self.assertEqual(result.summary_type, summary_type)
            self.assertGreater(len(result.summary), 0)
            self.assertGreater(result.quality_score, 0)
            self.assertGreater(result.compression_ratio, 1)
            
            # Verify personalization was applied
            self.assertEqual(result.length, SummaryLength.MEDIUM)
            self.assertEqual(result.style, SummaryStyle.TECHNICAL)
    
    async def test_multi_document_workflow(self):
        """Test multi-document summarization workflow"""
        documents = [
            {
                'id': 'doc1',
                'title': 'Renewable Energy',
                'content': 'Solar and wind power are becoming increasingly cost-effective alternatives to fossil fuels. Government incentives and technological advances are driving adoption rates higher each year.'
            },
            {
                'id': 'doc2',
                'title': 'Energy Storage',
                'content': 'Battery technology improvements are crucial for renewable energy adoption. Lithium-ion batteries are getting cheaper and more efficient, enabling better grid storage solutions.'
            }
        ]
        
        request = SummarizationRequest(
            text="",  # Will be filled by multi-doc summarizer
            summary_type=SummarizationType.HYBRID,
            length=SummaryLength.MEDIUM,
            style=SummaryStyle.EXECUTIVE
        )
        
        result = await self.service.summarize_documents(documents, request)
        
        self.assertIsInstance(result, SummaryResult)
        self.assertGreater(len(result.summary), 0)
        self.assertEqual(result.metadata['document_count'], 2)
        self.assertIn('renewable', result.summary.lower())
    
    def test_error_handling(self):
        """Test error handling throughout the system"""
        # Test empty text
        request = SummarizationRequest(
            text="",
            summary_type=SummarizationType.EXTRACTIVE
        )
        
        # Should handle gracefully (implementation dependent)
        # In a real system, you might want to raise specific exceptions
        
        # Test invalid parameters
        with self.assertRaises(ValueError):
            SummarizationType("invalid_type")
        
        with self.assertRaises(ValueError):
            SummaryLength("invalid_length")

def run_performance_tests():
    """Run performance tests"""
    print("\n" + "="*50)
    print("PERFORMANCE TESTS")
    print("="*50)
    
    import time
    
    service = SummarizationService()
    
    # Test text of varying lengths
    short_text = "This is a short text for testing."
    medium_text = " ".join([short_text] * 10)
    long_text = " ".join([short_text] * 50)
    
    test_texts = [
        ("Short", short_text),
        ("Medium", medium_text), 
        ("Long", long_text)
    ]
    
    async def run_perf_test():
        for name, text in test_texts:
            request = SummarizationRequest(
                text=text,
                summary_type=SummarizationType.EXTRACTIVE,
                length=SummaryLength.SHORT
            )
            
            start_time = time.time()
            result = await service.summarize(request)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            print(f"{name} text ({len(text.split())} words):")
            print(f"  Processing time: {processing_time:.3f}s")
            print(f"  Summary length: {result.word_count} words")
            print(f"  Compression ratio: {result.compression_ratio:.1f}:1")
            print(f"  Quality score: {result.quality_score:.2f}")
            print()
    
    asyncio.run(run_perf_test())

def run_example_scenarios():
    """Run example scenarios"""
    print("\n" + "="*50)
    print("EXAMPLE SCENARIOS")
    print("="*50)
    
    service = SummarizationService()
    
    scenarios = [
        {
            'name': 'News Article Summary',
            'text': 'A major breakthrough in renewable energy technology was announced today. Scientists at MIT have developed a new type of solar cell that is 40% more efficient than current models. The technology uses perovskite materials combined with silicon to capture more sunlight. This could significantly reduce the cost of solar power and accelerate adoption worldwide. The research team expects commercial applications within five years.',
            'type': SummarizationType.HYBRID,
            'length': SummaryLength.SHORT,
            'style': SummaryStyle.JOURNALISTIC
        },
        {
            'name': 'Technical Document Summary',
            'text': 'The implementation of microservices architecture requires careful consideration of service boundaries, data consistency, and communication patterns. Each service should have a single responsibility and be independently deployable. Inter-service communication can be synchronous via REST APIs or asynchronous via message queues. Data consistency across services is challenging and may require eventual consistency patterns. Monitoring and observability become crucial in distributed systems.',
            'type': SummarizationType.EXTRACTIVE,
            'length': SummaryLength.MEDIUM,
            'style': SummaryStyle.TECHNICAL
        },
        {
            'name': 'Meeting Minutes Summary',
            'text': 'The quarterly review meeting covered several key topics. Sales performance exceeded targets by 15% this quarter. The marketing team presented their new campaign strategy focusing on digital channels. IT reported completion of the security audit with minor recommendations. HR announced the new remote work policy will be implemented next month. Action items include updating the employee handbook and scheduling security training sessions.',
            'type': SummarizationType.HYBRID,
            'length': SummaryLength.MEDIUM,
            'style': SummaryStyle.FORMAL
        }
    ]
    
    async def run_scenarios():
        for scenario in scenarios:
            print(f"Scenario: {scenario['name']}")
            print("-" * 40)
            
            request = SummarizationRequest(
                text=scenario['text'],
                summary_type=scenario['type'],
                length=scenario['length'],
                style=scenario['style']
            )
            
            try:
                result = await service.summarize(request)
                
                print(f"Original ({len(scenario['text'].split())} words):")
                print(f"  {scenario['text'][:100]}...")
                print()
                print(f"Summary ({result.word_count} words):")
                print(f"  {result.summary}")
                print()
                print(f"Metrics:")
                print(f"  Compression: {result.compression_ratio:.1f}:1")
                print(f"  Quality: {result.quality_score:.2f}")
                print(f"  Confidence: {result.confidence_score:.2f}")
                
                if result.key_points:
                    print(f"Key Points:")
                    for i, point in enumerate(result.key_points[:3], 1):
                        print(f"  {i}. {point}")
                
            except Exception as e:
                print(f"Error: {str(e)}")
            
            print("\n" + "="*50)
    
    asyncio.run(run_scenarios())

if __name__ == '__main__':
    # Run unit tests
    print("Running Unit Tests...")
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run performance tests
    run_performance_tests()
    
    # Run example scenarios
    run_example_scenarios()
    
    print("\n" + "="*50)
    print("ALL TESTS COMPLETED")
    print("="*50)