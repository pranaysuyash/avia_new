#!/usr/bin/env python3
"""
Test Suite for AI-Powered Content Generation System (Task 44)
Comprehensive testing of content generation, optimization, and enhancement features
"""

import unittest
import asyncio
import json
import tempfile
import os
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import time

# Import the content generation system
try:
    from ai_content_generation import (
        AIContentGenerator, ContentGenerationRequest, GeneratedContent,
        ContentOptimization, ContentType, AudienceType, ContentTone
    )
except ImportError:
    print("Warning: Could not import AI content generation system. Some tests may fail.")

class TestContentGenerationRequest(unittest.TestCase):
    """Test ContentGenerationRequest data structure"""
    
    def test_request_creation(self):
        """Test creating content generation requests"""
        request = ContentGenerationRequest(
            content_type=ContentType.PODCAST_INTRO.value,
            source_text="This is a test transcript about AI technology.",
            target_audience=AudienceType.TECHNICAL.value,
            tone=ContentTone.PROFESSIONAL.value,
            length="medium"
        )
        
        self.assertEqual(request.content_type, ContentType.PODCAST_INTRO.value)
        self.assertEqual(request.target_audience, AudienceType.TECHNICAL.value)
        self.assertEqual(request.tone, ContentTone.PROFESSIONAL.value)
        self.assertEqual(request.length, "medium")
    
    def test_request_with_custom_instructions(self):
        """Test request with custom instructions"""
        request = ContentGenerationRequest(
            content_type=ContentType.FAQ.value,
            source_text="Test content",
            custom_instructions="Focus on beginner-friendly explanations"
        )
        
        self.assertEqual(request.custom_instructions, "Focus on beginner-friendly explanations")

class TestAIContentGenerator(unittest.TestCase):
    """Test the main AI content generator"""
    
    def setUp(self):
        """Set up test environment"""
        # Create generator without API key for testing
        self.generator = AIContentGenerator(api_key=None)
    
    def test_generator_initialization(self):
        """Test generator initialization"""
        self.assertIsNotNone(self.generator)
        self.assertIsNotNone(self.generator.templates)
        self.assertIsInstance(self.generator.generation_stats, dict)
    
    def test_template_loading(self):
        """Test content template loading"""
        templates = self.generator.templates
        
        # Check that all required content types have templates
        required_types = [
            ContentType.PODCAST_INTRO.value,
            ContentType.PODCAST_OUTRO.value,
            ContentType.EXPANDED_TEXT.value,
            ContentType.FAQ.value,
            ContentType.TAGS.value,
            ContentType.OPTIMIZATION.value
        ]
        
        for content_type in required_types:
            self.assertIn(content_type, templates)
            self.assertIn('system_prompt', templates[content_type])
            self.assertIn('user_prompt', templates[content_type])
    
    def test_token_counting(self):
        """Test token counting functionality"""
        test_text = "This is a test sentence for token counting."
        
        # Should return a reasonable token count
        token_count = self.generator.count_tokens(test_text)
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)
        self.assertLess(token_count, len(test_text))  # Should be less than character count
    
    def test_cost_estimation(self):
        """Test API cost estimation"""
        prompt_tokens = 100
        completion_tokens = 50
        
        cost = self.generator.estimate_cost(prompt_tokens, completion_tokens)
        
        self.assertIsInstance(cost, float)
        self.assertGreaterEqual(cost, 0.0)
    
    def test_extract_key_topics(self):
        """Test key topic extraction"""
        test_text = """
        This is a discussion about artificial intelligence and machine learning.
        We cover neural networks, deep learning, and natural language processing.
        The conversation includes topics about data science and automation.
        """
        
        topics = self.generator._extract_key_topics(test_text)
        
        self.assertIsInstance(topics, list)
        self.assertGreater(len(topics), 0)
        
        # Should extract relevant topics
        topic_text = ' '.join(topics).lower()
        self.assertTrue(any(term in topic_text for term in ['intelligence', 'learning', 'networks', 'data']))
    
    def test_extract_key_takeaways(self):
        """Test key takeaway extraction"""
        test_text = """
        The most important aspect of this discussion is understanding AI fundamentals.
        A key point to remember is that machine learning requires quality data.
        The essential takeaway is that automation can improve efficiency significantly.
        """
        
        takeaways = self.generator._extract_key_takeaways(test_text)
        
        self.assertIsInstance(takeaways, list)
        self.assertGreater(len(takeaways), 0)
        
        # Should contain relevant takeaways
        takeaway_text = ' '.join(takeaways).lower()
        self.assertTrue(any(term in takeaway_text for term in ['important', 'key', 'essential']))
    
    def test_readability_score_calculation(self):
        """Test readability score calculation"""
        # Simple text
        simple_text = "This is easy to read. Short sentences work well."
        simple_score = self.generator._calculate_readability_score(simple_text)
        
        # Complex text
        complex_text = "The implementation of sophisticated algorithmic methodologies necessitates comprehensive understanding of multifaceted computational paradigms."
        complex_score = self.generator._calculate_readability_score(complex_text)
        
        self.assertIsInstance(simple_score, float)
        self.assertIsInstance(complex_score, float)
        self.assertGreaterEqual(simple_score, 0)
        self.assertLessEqual(simple_score, 100)
        self.assertGreater(simple_score, complex_score)  # Simple should be more readable

class TestFallbackGeneration(unittest.TestCase):
    """Test fallback content generation (without OpenAI API)"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_podcast_intro_fallback(self):
        """Test podcast intro generation fallback"""
        test_text = "Today we discuss artificial intelligence, machine learning, and data science applications."
        
        intro = self.generator._generate_podcast_intro_fallback(test_text, AudienceType.TECHNICAL.value)
        
        self.assertIsInstance(intro, str)
        self.assertGreater(len(intro), 50)  # Should be substantial
        self.assertIn("welcome", intro.lower())  # Should be welcoming
    
    def test_podcast_outro_fallback(self):
        """Test podcast outro generation fallback"""
        test_text = "We covered AI fundamentals, machine learning basics, and practical applications."
        
        outro = self.generator._generate_podcast_outro_fallback(test_text, AudienceType.GENERAL.value)
        
        self.assertIsInstance(outro, str)
        self.assertGreater(len(outro), 50)
        self.assertIn("thanks", outro.lower())  # Should thank audience
        self.assertIn("subscribe", outro.lower())  # Should encourage subscription
    
    def test_expanded_text_fallback(self):
        """Test text expansion fallback"""
        bullet_points = """
        • AI is transforming industries
        • Machine learning improves efficiency
        • Data quality is crucial
        """
        
        expanded = self.generator._generate_expanded_text_fallback(bullet_points)
        
        self.assertIsInstance(expanded, str)
        self.assertGreater(len(expanded), len(bullet_points))  # Should be longer
        self.assertIn("AI", expanded)
        self.assertIn("machine learning", expanded.lower())
    
    def test_faq_fallback(self):
        """Test FAQ generation fallback"""
        test_text = "This content covers artificial intelligence, machine learning, and data science topics."
        
        faq = self.generator._generate_faq_fallback(test_text)
        
        self.assertIsInstance(faq, str)
        self.assertIn("Q", faq)  # Should contain questions
        self.assertIn("A", faq)  # Should contain answers
        self.assertGreater(faq.count("Q"), 2)  # Should have multiple questions
    
    def test_tags_fallback(self):
        """Test tag generation fallback"""
        test_text = """
        This discussion covers artificial intelligence, machine learning, deep learning,
        neural networks, data science, automation, and natural language processing.
        We explore applications in business, technology, and research domains.
        """
        
        tags = self.generator._generate_tags_fallback(test_text)
        
        self.assertIsInstance(tags, str)
        self.assertIn(",", tags)  # Should be comma-separated
        
        tag_list = [tag.strip().lower() for tag in tags.split(",")]
        self.assertGreater(len(tag_list), 3)  # Should have multiple tags
        
        # Should contain relevant terms
        relevant_found = any(term in ' '.join(tag_list) for term in ['intelligence', 'learning', 'data', 'neural'])
        self.assertTrue(relevant_found)
    
    def test_optimization_fallback(self):
        """Test content optimization fallback"""
        test_text = "We need to utilize advanced methodologies to implement comprehensive solutions."
        
        # Test technical audience optimization
        tech_optimized = self.generator._generate_optimization_fallback(test_text, AudienceType.TECHNICAL.value)
        self.assertIn("OPTIMIZED TEXT:", tech_optimized)
        self.assertIn("IMPROVEMENTS:", tech_optimized)
        
        # Test casual audience optimization
        casual_optimized = self.generator._generate_optimization_fallback(test_text, AudienceType.CASUAL.value)
        self.assertIn("use", casual_optimized.lower())  # Should simplify "utilize"

class TestContentGeneration(unittest.TestCase):
    """Test content generation functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)  # Use fallback mode
    
    def test_generate_podcast_intro(self):
        """Test podcast intro generation"""
        request = ContentGenerationRequest(
            content_type=ContentType.PODCAST_INTRO.value,
            source_text="Today we discuss AI and machine learning applications in business.",
            target_audience=AudienceType.BUSINESS.value,
            tone=ContentTone.ENTHUSIASTIC.value
        )
        
        result = asyncio.run(self.generator.generate_content(request))
        
        self.assertIsInstance(result, GeneratedContent)
        self.assertEqual(result.content_type, ContentType.PODCAST_INTRO.value)
        self.assertGreater(len(result.generated_text), 20)
        self.assertGreater(result.word_count, 0)
        self.assertGreaterEqual(result.confidence_score, 0.0)
        self.assertLessEqual(result.confidence_score, 1.0)
    
    def test_generate_faq(self):
        """Test FAQ generation"""
        request = ContentGenerationRequest(
            content_type=ContentType.FAQ.value,
            source_text="This content explains machine learning basics, including supervised learning, unsupervised learning, and neural networks.",
            target_audience=AudienceType.EDUCATIONAL.value
        )
        
        result = asyncio.run(self.generator.generate_content(request))
        
        self.assertIsInstance(result, GeneratedContent)
        self.assertEqual(result.content_type, ContentType.FAQ.value)
        self.assertIn("Q", result.generated_text)
        self.assertIn("A", result.generated_text)
        self.assertGreater(result.generated_text.count("Q"), 1)  # Multiple questions
    
    def test_generate_tags(self):
        """Test tag generation"""
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text="Discussion about artificial intelligence, machine learning, data science, and automation in modern business applications."
        )
        
        result = asyncio.run(self.generator.generate_content(request))
        
        self.assertIsInstance(result, GeneratedContent)
        self.assertEqual(result.content_type, ContentType.TAGS.value)
        self.assertIn(",", result.generated_text)  # Should be comma-separated
        
        tags = [tag.strip() for tag in result.generated_text.split(",")]
        self.assertGreater(len(tags), 3)  # Should have multiple tags
    
    def test_generate_expanded_text(self):
        """Test text expansion"""
        bullet_points = """
        • AI revolutionizes business processes
        • Machine learning enables predictive analytics
        • Automation reduces operational costs
        """
        
        request = ContentGenerationRequest(
            content_type=ContentType.EXPANDED_TEXT.value,
            source_text=bullet_points,
            target_audience=AudienceType.BUSINESS.value,
            length="long"
        )
        
        result = asyncio.run(self.generator.generate_content(request))
        
        self.assertIsInstance(result, GeneratedContent)
        self.assertGreater(len(result.generated_text), len(bullet_points))
        self.assertIn("AI", result.generated_text)
    
    def test_content_post_processing(self):
        """Test content post-processing"""
        # Test tag formatting
        raw_tags = "  artificial intelligence  ,   machine learning,data science  ,  "
        processed_tags = self.generator._post_process_content(raw_tags, ContentType.TAGS.value)
        
        self.assertNotIn("  ", processed_tags)  # No double spaces
        self.assertFalse(processed_tags.startswith(","))  # No leading comma
        self.assertFalse(processed_tags.endswith(","))  # No trailing comma
        
        # Test sentence ending
        raw_intro = "Welcome to our podcast about AI"
        processed_intro = self.generator._post_process_content(raw_intro, ContentType.PODCAST_INTRO.value)
        
        self.assertTrue(processed_intro.endswith(('.', '!', '?')))  # Should end with punctuation
    
    def test_suggestion_generation(self):
        """Test improvement suggestion generation"""
        request = ContentGenerationRequest(
            content_type=ContentType.PODCAST_INTRO.value,
            source_text="Test content",
            target_audience=AudienceType.TECHNICAL.value,
            length="short"
        )
        
        generated_content = "This is a very long introduction that goes on and on with lots of technical details and complex explanations."
        
        suggestions = self.generator._generate_suggestions(request, generated_content)
        
        self.assertIsInstance(suggestions, list)
        # Should suggest shortening for short length request
        self.assertTrue(any("shorter" in suggestion.lower() for suggestion in suggestions))

class TestContentOptimization(unittest.TestCase):
    """Test content optimization functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_content_optimization(self):
        """Test content optimization for different audiences"""
        original_content = "We need to utilize advanced methodologies to implement comprehensive solutions for our clients."
        
        optimization = self.generator.optimize_content_for_audience(
            content=original_content,
            target_audience=AudienceType.CASUAL.value,
            optimization_focus="readability"
        )
        
        self.assertIsInstance(optimization, ContentOptimization)
        self.assertEqual(optimization.original_text, original_content)
        self.assertIsInstance(optimization.optimized_text, str)
        self.assertIsInstance(optimization.improvements, list)
        self.assertIsInstance(optimization.readability_score, float)
        self.assertGreaterEqual(optimization.readability_score, 0)
        self.assertLessEqual(optimization.readability_score, 100)
    
    def test_readability_improvement(self):
        """Test that optimization improves readability"""
        complex_content = "The implementation of sophisticated algorithmic methodologies necessitates comprehensive understanding."
        
        optimization = self.generator.optimize_content_for_audience(
            content=complex_content,
            target_audience=AudienceType.CASUAL.value
        )
        
        # Optimized content should be different from original
        self.assertNotEqual(optimization.original_text, optimization.optimized_text)
        self.assertGreater(len(optimization.improvements), 0)

class TestSpecializedGeneration(unittest.TestCase):
    """Test specialized generation methods"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_podcast_intro_outro_generation(self):
        """Test podcast intro and outro generation"""
        transcript = "Today we discussed AI applications in healthcare, including diagnostic tools and treatment recommendations."
        
        results = self.generator.generate_podcast_intro_outro(
            transcript=transcript,
            show_name="AI Health Talk",
            host_name="Dr. Smith",
            episode_number=42
        )
        
        self.assertIn('intro', results)
        self.assertIn('outro', results)
        
        intro_result = results['intro']
        outro_result = results['outro']
        
        self.assertIsInstance(intro_result, GeneratedContent)
        self.assertIsInstance(outro_result, GeneratedContent)
        
        self.assertEqual(intro_result.content_type, ContentType.PODCAST_INTRO.value)
        self.assertEqual(outro_result.content_type, ContentType.PODCAST_OUTRO.value)
    
    def test_comprehensive_faq_generation(self):
        """Test comprehensive FAQ generation"""
        content = "This guide covers machine learning basics, including supervised and unsupervised learning, neural networks, and practical applications."
        
        faq_result = self.generator.generate_comprehensive_faq(content, num_questions=5)
        
        self.assertIsInstance(faq_result, GeneratedContent)
        self.assertEqual(faq_result.content_type, ContentType.FAQ.value)
        
        # Should contain multiple questions
        question_count = faq_result.generated_text.count('Q')
        self.assertGreaterEqual(question_count, 3)  # At least 3 questions
    
    def test_bullet_point_expansion(self):
        """Test bullet point expansion"""
        bullet_points = """
        • Machine learning automates decision making
        • Data quality affects model performance
        • Regular model updates improve accuracy
        """
        
        expanded_result = self.generator.expand_bullet_points(bullet_points, expansion_level="detailed")
        
        self.assertIsInstance(expanded_result, GeneratedContent)
        self.assertEqual(expanded_result.content_type, ContentType.EXPANDED_TEXT.value)
        self.assertGreater(len(expanded_result.generated_text), len(bullet_points))
    
    def test_content_tag_generation(self):
        """Test content tag generation with categories"""
        content = "This article discusses machine learning algorithms, data preprocessing, model evaluation, and deployment strategies."
        
        tag_result = self.generator.generate_content_tags(
            content=content,
            tag_categories=["technology", "education", "business"]
        )
        
        self.assertIsInstance(tag_result, GeneratedContent)
        self.assertEqual(tag_result.content_type, ContentType.TAGS.value)
        self.assertIn(",", tag_result.generated_text)  # Should be comma-separated

class TestBatchGeneration(unittest.TestCase):
    """Test batch content generation"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_batch_content_generation(self):
        """Test generating multiple content types in batch"""
        source_text = "This presentation covers AI fundamentals, machine learning applications, and future trends in technology."
        
        requests = [
            ContentGenerationRequest(
                content_type=ContentType.PODCAST_INTRO.value,
                source_text=source_text,
                target_audience=AudienceType.GENERAL.value
            ),
            ContentGenerationRequest(
                content_type=ContentType.FAQ.value,
                source_text=source_text,
                target_audience=AudienceType.EDUCATIONAL.value
            ),
            ContentGenerationRequest(
                content_type=ContentType.TAGS.value,
                source_text=source_text
            )
        ]
        
        results = self.generator.batch_generate_content(requests)
        
        self.assertEqual(len(results), 3)
        
        # Check each result
        for i, result in enumerate(results):
            self.assertIsInstance(result, GeneratedContent)
            self.assertEqual(result.content_type, requests[i].content_type)
            
            # Should not be error results
            self.assertFalse(result.metadata.get('error', False))
    
    def test_batch_generation_with_errors(self):
        """Test batch generation handling errors gracefully"""
        # Create a request with invalid content type
        invalid_request = ContentGenerationRequest(
            content_type="invalid_type",
            source_text="Test content"
        )
        
        results = self.generator.batch_generate_content([invalid_request])
        
        self.assertEqual(len(results), 1)
        result = results[0]
        
        # Should be an error result
        self.assertTrue(result.metadata.get('error', False))
        self.assertEqual(result.confidence_score, 0.0)

class TestStatisticsAndMetrics(unittest.TestCase):
    """Test statistics and metrics functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_generation_statistics(self):
        """Test generation statistics tracking"""
        # Generate some content to create statistics
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text="Test content for statistics"
        )
        
        # Generate content multiple times
        for _ in range(3):
            asyncio.run(self.generator.generate_content(request))
        
        stats = self.generator.get_generation_statistics()
        
        self.assertIsInstance(stats, dict)
        self.assertIn('total_generations', stats)
        self.assertIn('by_content_type', stats)
        self.assertIn('api_available', stats)
        self.assertIn('nlp_available', stats)
        self.assertIn('supported_content_types', stats)
        
        # Should track the generations
        self.assertGreaterEqual(stats['total_generations'], 3)
        self.assertIn(ContentType.TAGS.value, stats['by_content_type'])
        self.assertGreaterEqual(stats['by_content_type'][ContentType.TAGS.value], 3)
    
    def test_supported_content_types(self):
        """Test that all required content types are supported"""
        stats = self.generator.get_generation_statistics()
        supported_types = stats['supported_content_types']
        
        required_types = [
            ContentType.PODCAST_INTRO.value,
            ContentType.PODCAST_OUTRO.value,
            ContentType.EXPANDED_TEXT.value,
            ContentType.FAQ.value,
            ContentType.TAGS.value,
            ContentType.OPTIMIZATION.value
        ]
        
        for content_type in required_types:
            self.assertIn(content_type, supported_types)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_empty_source_text(self):
        """Test handling of empty source text"""
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text=""
        )
        
        # Should handle gracefully without crashing
        try:
            result = asyncio.run(self.generator.generate_content(request))
            self.assertIsInstance(result, GeneratedContent)
        except Exception as e:
            # If it raises an exception, it should be handled gracefully
            self.assertIsInstance(e, (ValueError, RuntimeError))
    
    def test_very_long_source_text(self):
        """Test handling of very long source text"""
        # Create very long text
        long_text = "This is a test sentence. " * 1000  # ~5000 words
        
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text=long_text
        )
        
        # Should handle without crashing
        result = asyncio.run(self.generator.generate_content(request))
        self.assertIsInstance(result, GeneratedContent)
    
    def test_invalid_content_type(self):
        """Test handling of invalid content type"""
        request = ContentGenerationRequest(
            content_type="invalid_type",
            source_text="Test content"
        )
        
        # Should raise appropriate error
        with self.assertRaises(ValueError):
            asyncio.run(self.generator.generate_content(request))
    
    def test_special_characters_in_text(self):
        """Test handling of special characters"""
        special_text = "This text contains émojis 🤖, spëcial chäractërs, and symbols @#$%^&*()!"
        
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text=special_text
        )
        
        # Should handle gracefully
        result = asyncio.run(self.generator.generate_content(request))
        self.assertIsInstance(result, GeneratedContent)
        self.assertGreater(len(result.generated_text), 0)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Set up test environment"""
        self.generator = AIContentGenerator(api_key=None)
    
    def test_generation_speed(self):
        """Test content generation speed"""
        request = ContentGenerationRequest(
            content_type=ContentType.TAGS.value,
            source_text="This is a test content for performance testing with various topics including AI, machine learning, and data science."
        )
        
        start_time = time.time()
        result = asyncio.run(self.generator.generate_content(request))
        end_time = time.time()
        
        generation_time = end_time - start_time
        
        # Should complete within reasonable time (adjust threshold as needed)
        self.assertLess(generation_time, 5.0)  # 5 seconds max
        self.assertGreater(result.generation_time, 0)
        self.assertLessEqual(result.generation_time, generation_time)
    
    def test_batch_generation_performance(self):
        """Test batch generation performance"""
        source_text = "Performance test content about AI and machine learning applications."
        
        requests = [
            ContentGenerationRequest(
                content_type=content_type,
                source_text=source_text
            ) for content_type in [
                ContentType.TAGS.value,
                ContentType.PODCAST_INTRO.value,
                ContentType.FAQ.value
            ]
        ]
        
        start_time = time.time()
        results = self.generator.batch_generate_content(requests)
        end_time = time.time()
        
        batch_time = end_time - start_time
        
        # Should complete batch within reasonable time
        self.assertLess(batch_time, 10.0)  # 10 seconds max for 3 items
        self.assertEqual(len(results), 3)
        
        # All results should be valid
        for result in results:
            self.assertIsInstance(result, GeneratedContent)
            self.assertFalse(result.metadata.get('error', False))
    
    def test_memory_usage(self):
        """Test memory usage with multiple generations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Generate multiple pieces of content
        for i in range(10):
            request = ContentGenerationRequest(
                content_type=ContentType.TAGS.value,
                source_text=f"Test content number {i} with various topics and information."
            )
            asyncio.run(self.generator.generate_content(request))
        
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB)
        self.assertLess(memory_increase, 100 * 1024 * 1024)  # 100MB

def run_all_tests():
    """Run all test suites"""
    print("🧪 Running AI Content Generation Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestContentGenerationRequest,
        TestAIContentGenerator,
        TestFallbackGeneration,
        TestContentGeneration,
        TestContentOptimization,
        TestSpecializedGeneration,
        TestBatchGeneration,
        TestStatisticsAndMetrics,
        TestErrorHandling,
        TestPerformance
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.testsRun > 0:
        success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100)
        print(f"Success rate: {success_rate:.1f}%")
    
    if result.failures:
        print(f"\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print(f"\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_all_tests()
    if success:
        print("\n🎉 All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        exit(1)