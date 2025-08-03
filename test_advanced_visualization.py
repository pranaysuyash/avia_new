#!/usr/bin/env python3
"""
Test Suite for Advanced Visualization Dashboard (Task 43)
Comprehensive testing of visualization components and analytics
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
import os

# Import the visualization dashboard
try:
    from advanced_visualization_dashboard import (
        AdvancedVisualizationDashboard, TranscriptData, SentimentPoint, TopicData
    )
except ImportError:
    print("Warning: Could not import visualization dashboard. Some tests may fail.")

class TestTranscriptData(unittest.TestCase):
    """Test TranscriptData structure"""
    
    def test_transcript_data_creation(self):
        """Test creating TranscriptData objects"""
        transcript = TranscriptData(
            id="test_1",
            title="Test Meeting",
            content="John: Hello everyone. Sarah: Hi John!",
            timestamp=datetime.now(),
            speakers=["John", "Sarah"],
            duration=300.0,
            metadata={"type": "meeting"}
        )
        
        self.assertEqual(transcript.id, "test_1")
        self.assertEqual(transcript.title, "Test Meeting")
        self.assertEqual(len(transcript.speakers), 2)
        self.assertIn("John", transcript.speakers)
        self.assertIn("Sarah", transcript.speakers)

class TestVisualizationDashboard(unittest.TestCase):
    """Test the main visualization dashboard functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock streamlit to avoid import issues in testing
        self.mock_st = Mock()
        
        # Create test dashboard instance
        with patch('advanced_visualization_dashboard.st', self.mock_st):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
    
    def test_dashboard_initialization(self):
        """Test dashboard initialization"""
        self.assertIsNotNone(self.dashboard)
        # Test that sample data is loaded
        self.assertTrue(hasattr(self.dashboard, 'load_sample_data'))
    
    def test_load_sample_data(self):
        """Test loading sample transcript data"""
        sample_data = self.dashboard.load_sample_data()
        
        self.assertIsInstance(sample_data, list)
        self.assertGreater(len(sample_data), 0)
        
        # Check first transcript
        first_transcript = sample_data[0]
        self.assertIsInstance(first_transcript, TranscriptData)
        self.assertIsInstance(first_transcript.speakers, list)
        self.assertGreater(len(first_transcript.content), 0)
    
    def test_preprocess_text_for_wordcloud(self):
        """Test text preprocessing for word cloud"""
        test_text = """
        John: Hello everyone, this is a great meeting!
        Sarah: I agree, John. This is really exciting.
        Mike: Yes, yes, I think we should proceed.
        """
        
        processed = self.dashboard.preprocess_text_for_wordcloud(test_text, min_length=3)
        
        # Should remove speaker labels and common words
        self.assertNotIn("john:", processed.lower())
        self.assertNotIn("sarah:", processed.lower())
        self.assertIn("meeting", processed.lower())
        self.assertIn("exciting", processed.lower())
        
        # Should filter short words
        processed_short = self.dashboard.preprocess_text_for_wordcloud(test_text, min_length=5)
        self.assertNotIn("yes", processed_short.lower())
        self.assertIn("meeting", processed_short.lower())
    
    def test_get_word_frequencies(self):
        """Test word frequency calculation"""
        test_text = "hello world hello python world hello"
        frequencies = self.dashboard.get_word_frequencies(test_text)
        
        self.assertIsInstance(frequencies, dict)
        self.assertEqual(frequencies["hello"], 3)
        self.assertEqual(frequencies["world"], 2)
        self.assertEqual(frequencies["python"], 1)
    
    def test_find_word_contexts(self):
        """Test finding word contexts"""
        test_text = "This is a test. Testing is important. We test everything."
        contexts = self.dashboard.find_word_contexts(test_text, "test", context_length=10)
        
        self.assertIsInstance(contexts, list)
        self.assertGreater(len(contexts), 0)
        
        # Should find multiple occurrences
        self.assertGreaterEqual(len(contexts), 2)
        
        # Each context should contain the word
        for context in contexts:
            self.assertIn("test", context.lower())
    
    def test_split_by_speaker_turns(self):
        """Test splitting text by speaker turns"""
        test_text = """
        John: Hello everyone.
        This is my opening statement.
        Sarah: Thank you John.
        I have some questions.
        Mike: Great points from both of you.
        """
        
        turns = self.dashboard.split_by_speaker_turns(test_text)
        
        self.assertIsInstance(turns, list)
        self.assertEqual(len(turns), 3)  # Three speakers
        
        # Check that each turn starts with speaker name
        self.assertTrue(turns[0].strip().startswith("John:"))
        self.assertTrue(turns[1].strip().startswith("Sarah:"))
        self.assertTrue(turns[2].strip().startswith("Mike:"))
    
    def test_smooth_data(self):
        """Test data smoothing function"""
        test_data = [1, 5, 2, 8, 3, 7, 4, 6]
        
        # Test with window size 1 (no smoothing)
        smoothed_1 = self.dashboard.smooth_data(test_data, 1)
        self.assertEqual(smoothed_1, test_data)
        
        # Test with window size 3
        smoothed_3 = self.dashboard.smooth_data(test_data, 3)
        self.assertEqual(len(smoothed_3), len(test_data))
        
        # Smoothed data should be less variable
        original_std = np.std(test_data)
        smoothed_std = np.std(smoothed_3)
        self.assertLess(smoothed_std, original_std)
    
    def test_analyze_sentiment_flow(self):
        """Test sentiment analysis flow"""
        # Create test transcript
        test_transcript = TranscriptData(
            id="sentiment_test",
            title="Sentiment Test",
            content="""
            John: I'm really excited about this project! It's going to be amazing.
            Sarah: I'm not sure about this. There are many challenges ahead.
            Mike: I think we can overcome the difficulties. Let's stay positive.
            """,
            timestamp=datetime.now(),
            speakers=["John", "Sarah", "Mike"],
            duration=180.0,
            metadata={}
        )
        
        sentiment_data = self.dashboard.analyze_sentiment_flow(test_transcript, "Sentence")
        
        self.assertIsInstance(sentiment_data, list)
        self.assertGreater(len(sentiment_data), 0)
        
        # Check sentiment point structure
        first_point = sentiment_data[0]
        self.assertIsInstance(first_point, SentimentPoint)
        self.assertIsInstance(first_point.sentiment, float)
        self.assertIsInstance(first_point.confidence, float)
        self.assertIsInstance(first_point.timestamp, float)
        
        # Sentiment should be between -1 and 1
        for point in sentiment_data:
            self.assertGreaterEqual(point.sentiment, -1.0)
            self.assertLessEqual(point.sentiment, 1.0)
            self.assertGreaterEqual(point.confidence, 0.0)
            self.assertLessEqual(point.confidence, 1.0)
    
    def test_build_speaker_network(self):
        """Test building speaker interaction networks"""
        test_transcript = TranscriptData(
            id="network_test",
            title="Network Test",
            content="""
            John: Hello Sarah and Mike.
            Sarah: Hi John, thanks for organizing this.
            Mike: Good to see you both.
            John: Let's start with the agenda.
            Sarah: I have some updates to share.
            Mike: That sounds great, Sarah.
            """,
            timestamp=datetime.now(),
            speakers=["John", "Sarah", "Mike"],
            duration=300.0,
            metadata={}
        )
        
        network_data = self.dashboard.build_speaker_network(test_transcript)
        
        self.assertIsInstance(network_data, dict)
        self.assertIn('interactions', network_data)
        self.assertIn('speaker_stats', network_data)
        
        # Check interactions
        interactions = network_data['interactions']
        self.assertIsInstance(interactions, dict)
        
        # Should have interactions between speakers
        interaction_pairs = list(interactions.keys())
        self.assertGreater(len(interaction_pairs), 0)
        
        # Check speaker statistics
        speaker_stats = network_data['speaker_stats']
        self.assertIn('John', speaker_stats)
        self.assertIn('Sarah', speaker_stats)
        self.assertIn('Mike', speaker_stats)
        
        # Each speaker should have word count and turn count
        for speaker, stats in speaker_stats.items():
            self.assertIn('total_words', stats)
            self.assertIn('turns', stats)
            self.assertGreater(stats['total_words'], 0)
            self.assertGreater(stats['turns'], 0)

class TestSentimentAnalysis(unittest.TestCase):
    """Test sentiment analysis functionality"""
    
    def setUp(self):
        """Set up sentiment analysis tests"""
        with patch('advanced_visualization_dashboard.st'):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
    
    def test_positive_sentiment_detection(self):
        """Test detection of positive sentiment"""
        positive_transcript = TranscriptData(
            id="positive_test",
            title="Positive Test",
            content="John: This is absolutely wonderful! I'm so excited and happy about our success!",
            timestamp=datetime.now(),
            speakers=["John"],
            duration=60.0,
            metadata={}
        )
        
        sentiment_data = self.dashboard.analyze_sentiment_flow(positive_transcript, "Sentence")
        
        # Should detect positive sentiment
        avg_sentiment = np.mean([point.sentiment for point in sentiment_data])
        self.assertGreater(avg_sentiment, 0.1)  # Should be positive
    
    def test_negative_sentiment_detection(self):
        """Test detection of negative sentiment"""
        negative_transcript = TranscriptData(
            id="negative_test",
            title="Negative Test",
            content="John: This is terrible! I'm really disappointed and frustrated with these results.",
            timestamp=datetime.now(),
            speakers=["John"],
            duration=60.0,
            metadata={}
        )
        
        sentiment_data = self.dashboard.analyze_sentiment_flow(negative_transcript, "Sentence")
        
        # Should detect negative sentiment
        avg_sentiment = np.mean([point.sentiment for point in sentiment_data])
        self.assertLess(avg_sentiment, -0.1)  # Should be negative
    
    def test_neutral_sentiment_detection(self):
        """Test detection of neutral sentiment"""
        neutral_transcript = TranscriptData(
            id="neutral_test",
            title="Neutral Test",
            content="John: The meeting is scheduled for 3 PM. We will discuss the quarterly reports.",
            timestamp=datetime.now(),
            speakers=["John"],
            duration=60.0,
            metadata={}
        )
        
        sentiment_data = self.dashboard.analyze_sentiment_flow(neutral_transcript, "Sentence")
        
        # Should detect neutral sentiment
        avg_sentiment = np.mean([point.sentiment for point in sentiment_data])
        self.assertGreater(avg_sentiment, -0.2)
        self.assertLess(avg_sentiment, 0.2)

class TestNetworkAnalysis(unittest.TestCase):
    """Test speaker network analysis functionality"""
    
    def setUp(self):
        """Set up network analysis tests"""
        with patch('advanced_visualization_dashboard.st'):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
    
    def test_two_speaker_network(self):
        """Test network with two speakers"""
        two_speaker_transcript = TranscriptData(
            id="two_speaker_test",
            title="Two Speaker Test",
            content="""
            Alice: Hello Bob, how are you today?
            Bob: I'm doing well, Alice. Thanks for asking.
            Alice: That's great to hear.
            Bob: How about you?
            """,
            timestamp=datetime.now(),
            speakers=["Alice", "Bob"],
            duration=120.0,
            metadata={}
        )
        
        network_data = self.dashboard.build_speaker_network(two_speaker_transcript)
        
        # Should have one interaction pair
        interactions = network_data['interactions']
        self.assertEqual(len(interactions), 1)
        
        # Should have stats for both speakers
        speaker_stats = network_data['speaker_stats']
        self.assertEqual(len(speaker_stats), 2)
        self.assertIn('Alice', speaker_stats)
        self.assertIn('Bob', speaker_stats)
    
    def test_multi_speaker_network(self):
        """Test network with multiple speakers"""
        multi_speaker_transcript = TranscriptData(
            id="multi_speaker_test",
            title="Multi Speaker Test",
            content="""
            Alice: Hello everyone.
            Bob: Hi Alice.
            Charlie: Good morning Alice and Bob.
            Alice: Let's start the meeting.
            Bob: Sounds good.
            Charlie: I agree.
            """,
            timestamp=datetime.now(),
            speakers=["Alice", "Bob", "Charlie"],
            duration=180.0,
            metadata={}
        )
        
        network_data = self.dashboard.build_speaker_network(multi_speaker_transcript)
        
        # Should have multiple interaction pairs
        interactions = network_data['interactions']
        self.assertGreater(len(interactions), 1)
        
        # Should have stats for all speakers
        speaker_stats = network_data['speaker_stats']
        self.assertEqual(len(speaker_stats), 3)
        
        # Each speaker should have spoken
        for speaker in ["Alice", "Bob", "Charlie"]:
            self.assertIn(speaker, speaker_stats)
            self.assertGreater(speaker_stats[speaker]['turns'], 0)
    
    def test_speaker_activity_calculation(self):
        """Test speaker activity metrics calculation"""
        activity_transcript = TranscriptData(
            id="activity_test",
            title="Activity Test",
            content="""
            Verbose: I have a lot to say about this topic. Let me explain in detail.
            Concise: Agreed.
            Verbose: Furthermore, I think we should consider multiple aspects of this issue.
            Concise: Yes.
            """,
            timestamp=datetime.now(),
            speakers=["Verbose", "Concise"],
            duration=120.0,
            metadata={}
        )
        
        network_data = self.dashboard.build_speaker_network(activity_transcript)
        speaker_stats = network_data['speaker_stats']
        
        # Verbose speaker should have more words
        verbose_words = speaker_stats['Verbose']['total_words']
        concise_words = speaker_stats['Concise']['total_words']
        
        self.assertGreater(verbose_words, concise_words)
        
        # Both should have same number of turns
        self.assertEqual(speaker_stats['Verbose']['turns'], 2)
        self.assertEqual(speaker_stats['Concise']['turns'], 2)

class TestTopicAnalysis(unittest.TestCase):
    """Test topic modeling and analysis functionality"""
    
    def setUp(self):
        """Set up topic analysis tests"""
        with patch('advanced_visualization_dashboard.st'):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
    
    def test_topic_evolution_analysis(self):
        """Test topic evolution over time"""
        topic_transcript = TranscriptData(
            id="topic_test",
            title="Topic Test",
            content="""
            John: Let's discuss our marketing strategy for the new product launch.
            Sarah: The marketing campaign should focus on digital channels and social media.
            Mike: I agree. We need to target younger demographics through online advertising.
            John: What about traditional marketing methods like print and radio?
            Sarah: Traditional methods are still important for reaching older customers.
            Mike: We should balance both digital and traditional approaches.
            John: Let's also consider the budget allocation for different marketing channels.
            Sarah: The budget should prioritize high-ROI channels like search engine marketing.
            """,
            timestamp=datetime.now(),
            speakers=["John", "Sarah", "Mike"],
            duration=480.0,
            metadata={}
        )
        
        # Test with reasonable parameters
        topic_timeline = self.dashboard.analyze_topic_evolution(topic_transcript, num_topics=3, time_segments=4)
        
        if topic_timeline:  # May be None if topic modeling fails
            self.assertIsInstance(topic_timeline, dict)
            self.assertIn('topics', topic_timeline)
            self.assertIn('segments', topic_timeline)
            self.assertIn('segment_texts', topic_timeline)
            
            # Should have the requested number of topics
            topics = topic_timeline['topics']
            self.assertLessEqual(len(topics), 3)
            
            # Each topic should have keywords
            for topic_id, topic_data in topics.items():
                self.assertIn('keywords', topic_data)
                self.assertIsInstance(topic_data['keywords'], list)
                self.assertGreater(len(topic_data['keywords']), 0)

class TestComparativeAnalysis(unittest.TestCase):
    """Test comparative analysis functionality"""
    
    def setUp(self):
        """Set up comparative analysis tests"""
        with patch('advanced_visualization_dashboard.st'):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
        
        # Create test transcripts for comparison
        self.transcript1 = TranscriptData(
            id="compare_1",
            title="Happy Meeting",
            content="John: This is fantastic! Sarah: I'm so excited about our progress!",
            timestamp=datetime.now(),
            speakers=["John", "Sarah"],
            duration=300.0,
            metadata={}
        )
        
        self.transcript2 = TranscriptData(
            id="compare_2",
            title="Concerned Meeting",
            content="Alice: I'm worried about the timeline. Bob: These challenges are significant.",
            timestamp=datetime.now(),
            speakers=["Alice", "Bob"],
            duration=240.0,
            metadata={}
        )
    
    def test_sentiment_comparison(self):
        """Test sentiment comparison between transcripts"""
        transcripts = [self.transcript1, self.transcript2]
        
        # This would normally be called within the dashboard
        # We'll test the underlying logic
        
        from textblob import TextBlob
        import re
        
        sentiment_data = []
        for transcript in transcripts:
            clean_text = re.sub(r'^[A-Za-z]+:', '', transcript.content, flags=re.MULTILINE)
            blob = TextBlob(clean_text)
            
            sentiment_data.append({
                'Transcript': transcript.title,
                'Sentiment Score': blob.sentiment.polarity,
                'Subjectivity': blob.sentiment.subjectivity
            })
        
        # First transcript should be more positive
        self.assertGreater(sentiment_data[0]['Sentiment Score'], sentiment_data[1]['Sentiment Score'])
    
    def test_duration_comparison(self):
        """Test duration analysis comparison"""
        transcripts = [self.transcript1, self.transcript2]
        
        duration_data = []
        for transcript in transcripts:
            network_data = self.dashboard.build_speaker_network(transcript)
            speaker_stats = network_data['speaker_stats']
            
            total_words = sum(stats['total_words'] for stats in speaker_stats.values())
            
            duration_data.append({
                'Transcript': transcript.title,
                'Duration': transcript.duration,
                'Total Words': total_words,
                'Words per Minute': total_words / (transcript.duration / 60)
            })
        
        # Should have data for both transcripts
        self.assertEqual(len(duration_data), 2)
        
        # Each should have positive values
        for data in duration_data:
            self.assertGreater(data['Duration'], 0)
            self.assertGreater(data['Total Words'], 0)
            self.assertGreater(data['Words per Minute'], 0)

class TestErrorHandling(unittest.TestCase):
    """Test error handling and edge cases"""
    
    def setUp(self):
        """Set up error handling tests"""
        with patch('advanced_visualization_dashboard.st'):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
    
    def test_empty_transcript_handling(self):
        """Test handling of empty transcripts"""
        empty_transcript = TranscriptData(
            id="empty_test",
            title="Empty Test",
            content="",
            timestamp=datetime.now(),
            speakers=[],
            duration=0.0,
            metadata={}
        )
        
        # Should handle empty content gracefully
        processed_text = self.dashboard.preprocess_text_for_wordcloud(empty_transcript.content)
        self.assertEqual(processed_text, "")
        
        # Network analysis should handle empty speakers
        network_data = self.dashboard.build_speaker_network(empty_transcript)
        self.assertIsInstance(network_data, dict)
    
    def test_single_speaker_handling(self):
        """Test handling of single speaker transcripts"""
        single_speaker_transcript = TranscriptData(
            id="single_test",
            title="Single Speaker Test",
            content="John: I'm talking to myself. This is a monologue.",
            timestamp=datetime.now(),
            speakers=["John"],
            duration=60.0,
            metadata={}
        )
        
        # Should handle single speaker gracefully
        network_data = self.dashboard.build_speaker_network(single_speaker_transcript)
        
        # Should have speaker stats but no interactions
        self.assertIn('speaker_stats', network_data)
        self.assertIn('John', network_data['speaker_stats'])
        
        # Interactions should be empty or minimal
        interactions = network_data['interactions']
        self.assertEqual(len(interactions), 0)
    
    def test_malformed_content_handling(self):
        """Test handling of malformed transcript content"""
        malformed_transcript = TranscriptData(
            id="malformed_test",
            title="Malformed Test",
            content="This has no speaker labels just random text without structure",
            timestamp=datetime.now(),
            speakers=["Unknown"],
            duration=30.0,
            metadata={}
        )
        
        # Should handle malformed content without crashing
        processed_text = self.dashboard.preprocess_text_for_wordcloud(malformed_transcript.content)
        self.assertIsInstance(processed_text, str)
        
        # Network analysis should handle gracefully
        network_data = self.dashboard.build_speaker_network(malformed_transcript)
        self.assertIsInstance(network_data, dict)

class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        """Set up performance tests"""
        with patch('advanced_visualization_dashboard.st'):
            with patch('advanced_visualization_dashboard.nltk'):
                with patch('advanced_visualization_dashboard.spacy'):
                    self.dashboard = AdvancedVisualizationDashboard()
    
    def test_large_transcript_processing(self):
        """Test processing of large transcripts"""
        # Create a large transcript
        large_content = ""
        speakers = ["Alice", "Bob", "Charlie", "David"]
        
        for i in range(100):  # 100 speaking turns
            speaker = speakers[i % len(speakers)]
            large_content += f"{speaker}: This is speaking turn number {i+1}. "
            large_content += "We are discussing important topics and making progress. "
            large_content += "There are many details to cover in this meeting.\n"
        
        large_transcript = TranscriptData(
            id="large_test",
            title="Large Transcript Test",
            content=large_content,
            timestamp=datetime.now(),
            speakers=speakers,
            duration=3600.0,  # 1 hour
            metadata={}
        )
        
        import time
        
        # Test word cloud processing
        start_time = time.time()
        processed_text = self.dashboard.preprocess_text_for_wordcloud(large_transcript.content)
        processing_time = time.time() - start_time
        
        self.assertLess(processing_time, 5.0)  # Should complete within 5 seconds
        self.assertGreater(len(processed_text), 0)
        
        # Test network analysis
        start_time = time.time()
        network_data = self.dashboard.build_speaker_network(large_transcript)
        network_time = time.time() - start_time
        
        self.assertLess(network_time, 5.0)  # Should complete within 5 seconds
        self.assertIsInstance(network_data, dict)
    
    def test_multiple_transcript_comparison(self):
        """Test performance with multiple transcript comparison"""
        # Create multiple transcripts
        transcripts = []
        
        for i in range(10):
            content = f"Speaker1: This is transcript {i+1}. "
            content += f"Speaker2: We are discussing topic {i+1}. "
            content += f"Speaker1: This is important information about subject {i+1}."
            
            transcript = TranscriptData(
                id=f"perf_test_{i+1}",
                title=f"Performance Test {i+1}",
                content=content,
                timestamp=datetime.now() - timedelta(days=i),
                speakers=["Speaker1", "Speaker2"],
                duration=300.0,
                metadata={}
            )
            transcripts.append(transcript)
        
        import time
        
        # Test processing all transcripts
        start_time = time.time()
        
        for transcript in transcripts:
            processed_text = self.dashboard.preprocess_text_for_wordcloud(transcript.content)
            network_data = self.dashboard.build_speaker_network(transcript)
        
        total_time = time.time() - start_time
        
        # Should process all transcripts within reasonable time
        self.assertLess(total_time, 10.0)  # 10 seconds for 10 transcripts

def run_all_tests():
    """Run all test suites"""
    print("🧪 Running Advanced Visualization Dashboard Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestTranscriptData,
        TestVisualizationDashboard,
        TestSentimentAnalysis,
        TestNetworkAnalysis,
        TestTopicAnalysis,
        TestComparativeAnalysis,
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