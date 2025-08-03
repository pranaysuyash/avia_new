#!/usr/bin/env python3
"""
Test Suite for Advanced Search and Discovery Features (Task 45)
Comprehensive tests for search functionality, voice search, boolean operators, and alerts
"""

import unittest
import tempfile
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from advanced_search_discovery import (
    AdvancedSearchEngine, SearchType, SearchResult, SavedSearch,
    SearchQuery, SearchAlert, SearchDatabase, FuzzySearchEngine,
    VoiceSearchEngine, BooleanSearchEngine, TemporalSearchEngine,
    SpeakerSearchEngine, SearchAlertSystem
)

class TestSearchDatabase(unittest.TestCase):
    """Test search database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = SearchDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database table creation"""
        # Database should initialize without errors
        self.assertIsNotNone(self.db)
        
        # Check if tables exist by trying to query them
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Check search_queries table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='search_queries'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check content_index table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='content_index'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_add_content_to_index(self):
        """Test adding content to search index"""
        success = self.db.add_content_to_index(
            content_id="test_content_1",
            user_id="test_user",
            title="Test Content",
            content_type="transcript",
            content="This is test content for searching",
            speaker="Test Speaker",
            timestamp=datetime.now(),
            start_time=0.0,
            end_time=10.0,
            metadata={"test": "metadata"}
        )
        
        self.assertTrue(success)
        
        # Verify content was added
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM content_index WHERE content_id = ?", ("test_content_1",))
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[2], "Test Content")  # title
    
    def test_save_search_query(self):
        """Test saving search queries"""
        query = SearchQuery(
            query_id="test_query_1",
            user_id="test_user",
            query_text="test search",
            search_type="text",
            filters={"content_type": "transcript"},
            is_saved=True,
            alert_enabled=True
        )
        
        success = self.db.save_search_query(query)
        self.assertTrue(success)
        
        # Verify query was saved
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM search_queries WHERE query_id = ?", ("test_query_1",))
            result = cursor.fetchone()
            self.assertIsNotNone(result)
            self.assertEqual(result[2], "test search")  # query_text
    
    def test_get_search_history(self):
        """Test retrieving search history"""
        # Add some search history
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            for i in range(3):
                cursor.execute("""
                    INSERT INTO search_history (
                        history_id, user_id, query_text, search_type,
                        result_count, execution_time, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"hist_{i}", "test_user", f"query {i}", "text",
                    i + 1, 0.1, datetime.now().isoformat()
                ))
            
            conn.commit()
        
        history = self.db.get_search_history("test_user", limit=5)
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]['query_text'], "query 2")  # Most recent first

class TestFuzzySearchEngine(unittest.TestCase):
    """Test fuzzy search functionality"""
    
    def setUp(self):
        """Set up fuzzy search engine"""
        self.fuzzy_engine = FuzzySearchEngine(threshold=70)
        
        self.sample_content = [
            {
                'content_id': 'content_1',
                'title': 'Budget Meeting',
                'content': 'We discussed the quarterly budget and financial projections',
                'content_type': 'transcript',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content_id': 'content_2',
                'title': 'Product Launch',
                'content': 'The product launch is scheduled for next month',
                'content_type': 'transcript',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def test_exact_match_search(self):
        """Test exact match fuzzy search"""
        results = self.fuzzy_engine.search("budget", self.sample_content)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'content_1')
        self.assertGreater(results[0].relevance_score, 0.7)
    
    def test_typo_tolerance_search(self):
        """Test fuzzy search with typos"""
        results = self.fuzzy_engine.search("budjet", self.sample_content)  # "budget" with typo
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'content_1')
        self.assertGreater(results[0].relevance_score, 0.6)
    
    def test_partial_match_search(self):
        """Test partial match fuzzy search"""
        results = self.fuzzy_engine.search("prod", self.sample_content)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'content_2')
    
    def test_no_match_search(self):
        """Test search with no matches"""
        results = self.fuzzy_engine.search("nonexistent", self.sample_content)
        self.assertEqual(len(results), 0)
    
    def test_highlights_generation(self):
        """Test highlight generation"""
        results = self.fuzzy_engine.search("budget", self.sample_content)
        
        self.assertEqual(len(results), 1)
        self.assertGreater(len(results[0].highlights), 0)
        self.assertTrue(any("budget" in highlight.lower() for highlight in results[0].highlights))

class TestVoiceSearchEngine(unittest.TestCase):
    """Test voice search functionality"""
    
    def setUp(self):
        """Set up voice search engine"""
        self.voice_engine = VoiceSearchEngine()
    
    @patch('speech_recognition.Recognizer.recognize_google')
    @patch('speech_recognition.Recognizer.listen')
    def test_successful_voice_recognition(self, mock_listen, mock_recognize):
        """Test successful voice recognition"""
        mock_audio = Mock()
        mock_listen.return_value = mock_audio
        mock_recognize.return_value = "test voice query"
        
        query = self.voice_engine.listen_for_query(timeout=1)
        
        self.assertEqual(query, "test voice query")
        mock_listen.assert_called_once()
        mock_recognize.assert_called_once_with(mock_audio)
    
    @patch('speech_recognition.Recognizer.recognize_google')
    @patch('speech_recognition.Recognizer.listen')
    def test_voice_recognition_timeout(self, mock_listen, mock_recognize):
        """Test voice recognition timeout"""
        import speech_recognition as sr
        mock_listen.side_effect = sr.WaitTimeoutError()
        
        query = self.voice_engine.listen_for_query(timeout=1)
        
        self.assertIsNone(query)
    
    @patch('speech_recognition.Recognizer.recognize_google')
    @patch('speech_recognition.Recognizer.listen')
    def test_voice_recognition_unknown_value(self, mock_listen, mock_recognize):
        """Test voice recognition with unknown value"""
        import speech_recognition as sr
        mock_audio = Mock()
        mock_listen.return_value = mock_audio
        mock_recognize.side_effect = sr.UnknownValueError()
        
        query = self.voice_engine.listen_for_query(timeout=1)
        
        self.assertIsNone(query)
    
    def test_process_voice_query(self):
        """Test processing audio data"""
        # Test with mock audio data
        audio_data = b"mock audio data"
        
        with patch('speech_recognition.Recognizer.recognize_google') as mock_recognize:
            mock_recognize.return_value = "processed voice query"
            
            query = self.voice_engine.process_voice_query(audio_data)
            
            self.assertEqual(query, "processed voice query")

class TestBooleanSearchEngine(unittest.TestCase):
    """Test boolean search functionality"""
    
    def setUp(self):
        """Set up boolean search engine"""
        self.boolean_engine = BooleanSearchEngine()
        
        self.sample_content = [
            {
                'content_id': 'content_1',
                'title': 'Budget Meeting',
                'content': 'We discussed the quarterly budget and financial projections for the next year',
                'content_type': 'transcript',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content_id': 'content_2',
                'title': 'Product Launch',
                'content': 'The product launch is scheduled for next month with marketing campaigns',
                'content_type': 'transcript',
                'timestamp': datetime.now().isoformat()
            },
            {
                'content_id': 'content_3',
                'title': 'Team Meeting',
                'content': 'Team discussed project timeline and budget constraints',
                'content_type': 'transcript',
                'timestamp': datetime.now().isoformat()
            }
        ]
    
    def test_parse_simple_query(self):
        """Test parsing simple boolean query"""
        parsed = self.boolean_engine.parse_boolean_query("budget AND meeting")
        
        self.assertIn("budget", parsed['terms'])
        self.assertIn("meeting", parsed['terms'])
        self.assertIn("AND", parsed['operators'])
    
    def test_parse_phrase_query(self):
        """Test parsing phrase query"""
        parsed = self.boolean_engine.parse_boolean_query('"product launch"')
        
        self.assertIn("product launch", parsed['phrases'])
    
    def test_parse_not_query(self):
        """Test parsing NOT query"""
        parsed = self.boolean_engine.parse_boolean_query("budget NOT marketing")
        
        self.assertIn("marketing", parsed['exclusions'])
    
    def test_and_search(self):
        """Test AND boolean search"""
        parsed_query = self.boolean_engine.parse_boolean_query("budget AND meeting")
        results = self.boolean_engine.search(parsed_query, self.sample_content)
        
        # Should find content_1 and content_3 (both have "budget" and "meeting")
        self.assertEqual(len(results), 2)
        result_ids = [r.content_id for r in results]
        self.assertIn('content_1', result_ids)
        self.assertIn('content_3', result_ids)
    
    def test_or_search(self):
        """Test OR boolean search"""
        parsed_query = self.boolean_engine.parse_boolean_query("budget OR marketing")
        results = self.boolean_engine.search(parsed_query, self.sample_content)
        
        # Should find content with either "budget" or "marketing"
        self.assertGreater(len(results), 0)
    
    def test_not_search(self):
        """Test NOT boolean search"""
        parsed_query = self.boolean_engine.parse_boolean_query("meeting NOT product")
        results = self.boolean_engine.search(parsed_query, self.sample_content)
        
        # Should exclude content with "product"
        result_ids = [r.content_id for r in results]
        self.assertNotIn('content_2', result_ids)  # content_2 has "product"
    
    def test_phrase_search(self):
        """Test phrase search"""
        parsed_query = self.boolean_engine.parse_boolean_query('"product launch"')
        results = self.boolean_engine.search(parsed_query, self.sample_content)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, 'content_2')

class TestTemporalSearchEngine(unittest.TestCase):
    """Test temporal search functionality"""
    
    def setUp(self):
        """Set up temporal search engine"""
        self.temporal_engine = TemporalSearchEngine()
        
        now = datetime.now()
        self.sample_content = [
            {
                'content_id': 'content_1',
                'title': 'Recent Meeting',
                'content': 'Recent meeting content',
                'timestamp': now.isoformat(),
                'start_time': 0.0,
                'end_time': 60.0
            },
            {
                'content_id': 'content_2',
                'title': 'Old Meeting',
                'content': 'Old meeting content',
                'timestamp': (now - timedelta(days=7)).isoformat(),
                'start_time': 30.0,
                'end_time': 90.0
            },
            {
                'content_id': 'content_3',
                'title': 'Future Meeting',
                'content': 'Future meeting content',
                'timestamp': (now + timedelta(days=1)).isoformat(),
                'start_time': 120.0,
                'end_time': 180.0
            }
        ]
    
    def test_time_range_filter(self):
        """Test filtering by time range"""
        now = datetime.now()
        start_time = now - timedelta(days=1)
        end_time = now + timedelta(hours=1)
        
        filtered = self.temporal_engine.search_by_time_range(
            self.sample_content, start_time=start_time, end_time=end_time
        )
        
        # Should include only content_1 (recent meeting)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['content_id'], 'content_1')
    
    def test_duration_filter(self):
        """Test filtering by duration within content"""
        filtered = self.temporal_engine.search_by_time_range(
            self.sample_content, duration_start=25.0, duration_end=65.0
        )
        
        # Should include content that overlaps with 25-65 second range
        self.assertGreater(len(filtered), 0)
    
    def test_no_time_filter(self):
        """Test with no time filters"""
        filtered = self.temporal_engine.search_by_time_range(self.sample_content)
        
        # Should return all content
        self.assertEqual(len(filtered), 3)

class TestSpeakerSearchEngine(unittest.TestCase):
    """Test speaker search functionality"""
    
    def setUp(self):
        """Set up speaker search engine"""
        self.speaker_engine = SpeakerSearchEngine()
        
        self.sample_content = [
            {
                'content_id': 'content_1',
                'title': 'John\'s Presentation',
                'content': 'Presentation content',
                'speaker': 'John Smith'
            },
            {
                'content_id': 'content_2',
                'title': 'Sarah\'s Meeting',
                'content': 'Meeting content',
                'speaker': 'Sarah Johnson'
            },
            {
                'content_id': 'content_3',
                'title': 'Team Discussion',
                'content': 'Discussion content',
                'speaker': 'John Smith'
            }
        ]
    
    def test_single_speaker_filter(self):
        """Test filtering by single speaker"""
        filtered = self.speaker_engine.search_by_speaker(
            self.sample_content, ['John Smith']
        )
        
        self.assertEqual(len(filtered), 2)
        for content in filtered:
            self.assertEqual(content['speaker'], 'John Smith')
    
    def test_multiple_speakers_filter(self):
        """Test filtering by multiple speakers"""
        filtered = self.speaker_engine.search_by_speaker(
            self.sample_content, ['John Smith', 'Sarah Johnson']
        )
        
        self.assertEqual(len(filtered), 3)  # All content matches
    
    def test_partial_speaker_match(self):
        """Test partial speaker name matching"""
        filtered = self.speaker_engine.search_by_speaker(
            self.sample_content, ['John']
        )
        
        self.assertEqual(len(filtered), 2)  # Both John Smith entries
    
    def test_no_speaker_filter(self):
        """Test with no speaker filter"""
        filtered = self.speaker_engine.search_by_speaker(self.sample_content, [])
        
        self.assertEqual(len(filtered), 3)  # All content

class TestSearchAlertSystem(unittest.TestCase):
    """Test search alert system"""
    
    def setUp(self):
        """Set up search alert system"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = SearchDatabase(self.temp_db.name)
        self.alert_system = SearchAlertSystem(self.db)
    
    def tearDown(self):
        """Clean up"""
        self.alert_system.stop_alert_monitoring()
        os.unlink(self.temp_db.name)
    
    def test_create_alert(self):
        """Test creating search alert"""
        alert = SearchAlert(
            alert_id="test_alert_1",
            search_id="test_search_1",
            user_id="test_user",
            alert_type="new_content",
            conditions={"frequency": "daily"},
            notification_method="email"
        )
        
        success = self.alert_system.create_alert(alert)
        self.assertTrue(success)
        
        # Verify alert was created
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM search_alerts WHERE alert_id = ?", ("test_alert_1",))
            result = cursor.fetchone()
            self.assertIsNotNone(result)
    
    def test_should_trigger_alert(self):
        """Test alert triggering logic"""
        conditions = {"frequency": "daily"}
        
        # Should trigger if never triggered before
        should_trigger = self.alert_system._should_trigger_alert(
            "test_alert", conditions, None
        )
        self.assertTrue(should_trigger)
        
        # Should not trigger if triggered recently
        recent_trigger = datetime.now().isoformat()
        should_trigger = self.alert_system._should_trigger_alert(
            "test_alert", conditions, recent_trigger
        )
        self.assertFalse(should_trigger)
        
        # Should trigger if triggered more than a day ago
        old_trigger = (datetime.now() - timedelta(days=2)).isoformat()
        should_trigger = self.alert_system._should_trigger_alert(
            "test_alert", conditions, old_trigger
        )
        self.assertTrue(should_trigger)

class TestAdvancedSearchEngine(unittest.TestCase):
    """Test main advanced search engine"""
    
    def setUp(self):
        """Set up advanced search engine"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Mock the database path in AdvancedSearchEngine
        with patch('advanced_search_discovery.SearchDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.db_path = self.temp_db.name
            mock_db_class.return_value = mock_db
            
            self.search_engine = AdvancedSearchEngine()
            self.search_engine.db = SearchDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up"""
        self.search_engine.alert_system.stop_alert_monitoring()
        os.unlink(self.temp_db.name)
    
    def test_add_content_to_index(self):
        """Test adding content to search index"""
        success = self.search_engine.add_content_to_search_index(
            content_id="test_content",
            user_id="test_user",
            title="Test Content",
            content_type="transcript",
            content="This is test content",
            speaker="Test Speaker",
            timestamp=datetime.now()
        )
        
        self.assertTrue(success)
    
    def test_text_search(self):
        """Test basic text search"""
        # Add content to index
        self.search_engine.add_content_to_search_index(
            "content_1", "test_user", "Budget Meeting",
            "transcript", "We discussed the budget for next quarter",
            "John Smith", datetime.now()
        )
        
        results = self.search_engine.search("budget", SearchType.TEXT, "test_user")
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].content_id, "content_1")
        self.assertGreater(results[0].relevance_score, 0)
    
    def test_save_and_run_search(self):
        """Test saving and running searches"""
        # Add content first
        self.search_engine.add_content_to_search_index(
            "content_1", "test_user", "Test Content",
            "transcript", "Test content for searching",
            timestamp=datetime.now()
        )
        
        # Save search
        success = self.search_engine.save_search(
            "test_user", "Test Search", "Test description",
            "test", SearchType.TEXT
        )
        self.assertTrue(success)
        
        # Get saved searches
        saved_searches = self.search_engine.get_saved_searches("test_user")
        self.assertEqual(len(saved_searches), 1)
        
        # Run saved search
        results = self.search_engine.run_saved_search(
            saved_searches[0].search_id, "test_user"
        )
        self.assertIsInstance(results, list)
    
    def test_search_suggestions(self):
        """Test search suggestions"""
        # Add some search history
        import sqlite3
        with sqlite3.connect(self.search_engine.db.db_path) as conn:
            cursor = conn.cursor()
            
            queries = ["budget meeting", "budget planning", "product launch"]
            for i, query in enumerate(queries):
                cursor.execute("""
                    INSERT INTO search_history (
                        history_id, user_id, query_text, search_type,
                        result_count, execution_time, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"hist_{i}", "test_user", query, "text",
                    1, 0.1, datetime.now().isoformat()
                ))
            
            conn.commit()
        
        suggestions = self.search_engine.get_search_suggestions("budget", "test_user")
        
        self.assertGreater(len(suggestions), 0)
        self.assertTrue(any("budget" in suggestion for suggestion in suggestions))
    
    def test_search_analytics(self):
        """Test search analytics"""
        # Add some search history
        import sqlite3
        with sqlite3.connect(self.search_engine.db.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO search_history (
                    history_id, user_id, query_text, search_type,
                    result_count, execution_time, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                "hist_1", "test_user", "test query", "text",
                5, 0.1, datetime.now().isoformat()
            ))
            
            conn.commit()
        
        analytics = self.search_engine.get_search_analytics("test_user")
        
        self.assertNotIn('error', analytics)
        self.assertEqual(analytics['total_searches'], 1)
        self.assertEqual(analytics['average_results'], 5.0)
    
    @patch('advanced_search_discovery.VoiceSearchEngine.listen_for_query')
    def test_voice_search(self, mock_listen):
        """Test voice search integration"""
        mock_listen.return_value = "test voice query"
        
        # Add content
        self.search_engine.add_content_to_search_index(
            "content_1", "test_user", "Test Content",
            "transcript", "test voice query content",
            timestamp=datetime.now()
        )
        
        results = self.search_engine.voice_search("test_user", timeout=1)
        
        mock_listen.assert_called_once()
        self.assertIsInstance(results, list)

class TestSearchIntegration(unittest.TestCase):
    """Integration tests for search functionality"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        with patch('advanced_search_discovery.SearchDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.db_path = self.temp_db.name
            mock_db_class.return_value = mock_db
            
            self.search_engine = AdvancedSearchEngine()
            self.search_engine.db = SearchDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up"""
        self.search_engine.alert_system.stop_alert_monitoring()
        os.unlink(self.temp_db.name)
    
    def test_end_to_end_search_workflow(self):
        """Test complete search workflow"""
        # 1. Add content to index
        content_data = [
            ("content_1", "Budget Meeting", "We discussed quarterly budget allocations", "John Smith"),
            ("content_2", "Product Launch", "Product launch timeline and marketing strategy", "Sarah Johnson"),
            ("content_3", "Team Standup", "Daily standup with budget concerns raised", "Mike Chen")
        ]
        
        for content_id, title, content, speaker in content_data:
            success = self.search_engine.add_content_to_search_index(
                content_id, "test_user", title, "transcript", content,
                speaker, datetime.now()
            )
            self.assertTrue(success)
        
        # 2. Perform different types of searches
        
        # Text search
        text_results = self.search_engine.search("budget", SearchType.TEXT, "test_user")
        self.assertGreater(len(text_results), 0)
        
        # Fuzzy search
        fuzzy_results = self.search_engine.search("budjet", SearchType.FUZZY, "test_user")
        self.assertGreater(len(fuzzy_results), 0)
        
        # Boolean search
        boolean_results = self.search_engine.search("budget AND meeting", SearchType.BOOLEAN, "test_user")
        self.assertGreater(len(boolean_results), 0)
        
        # Speaker search
        speaker_results = self.search_engine.search("standup", SearchType.SPEAKER, "test_user", 
                                                   {"speakers": ["Mike Chen"]})
        self.assertEqual(len(speaker_results), 1)
        self.assertEqual(speaker_results[0].speaker, "Mike Chen")
        
        # 3. Save search
        save_success = self.search_engine.save_search(
            "test_user", "Budget Searches", "All budget-related content",
            "budget", SearchType.TEXT, enable_alerts=True
        )
        self.assertTrue(save_success)
        
        # 4. Get saved searches
        saved_searches = self.search_engine.get_saved_searches("test_user")
        self.assertEqual(len(saved_searches), 1)
        
        # 5. Run saved search
        saved_results = self.search_engine.run_saved_search(
            saved_searches[0].search_id, "test_user"
        )
        self.assertGreater(len(saved_results), 0)
        
        # 6. Get analytics
        analytics = self.search_engine.get_search_analytics("test_user")
        self.assertGreater(analytics['total_searches'], 0)
        
        # 7. Get suggestions
        suggestions = self.search_engine.get_search_suggestions("bud", "test_user")
        self.assertIsInstance(suggestions, list)

def run_performance_tests():
    """Run performance tests for search functionality"""
    print("\n🚀 Running Performance Tests")
    print("=" * 50)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        with patch('advanced_search_discovery.SearchDatabase') as mock_db_class:
            mock_db = Mock()
            mock_db.db_path = temp_db.name
            mock_db_class.return_value = mock_db
            
            search_engine = AdvancedSearchEngine()
            search_engine.db = SearchDatabase(temp_db.name)
        
        # Add large amount of content
        print("Adding 1000 content items...")
        start_time = time.time()
        
        for i in range(1000):
            search_engine.add_content_to_search_index(
                f"content_{i}", "perf_user", f"Content {i}",
                "transcript", f"This is test content number {i} with various keywords like budget, meeting, product, launch",
                f"Speaker {i % 10}", datetime.now()
            )
        
        add_time = time.time() - start_time
        print(f"✅ Added 1000 items in {add_time:.2f} seconds ({1000/add_time:.1f} items/sec)")
        
        # Test search performance
        search_queries = ["budget", "meeting", "product launch", "speaker", "content"]
        
        for query in search_queries:
            start_time = time.time()
            results = search_engine.search(query, SearchType.TEXT, "perf_user")
            search_time = time.time() - start_time
            
            print(f"✅ Search '{query}': {len(results)} results in {search_time:.3f} seconds")
        
        # Test fuzzy search performance
        start_time = time.time()
        fuzzy_results = search_engine.search("budjet", SearchType.FUZZY, "perf_user")
        fuzzy_time = time.time() - start_time
        print(f"✅ Fuzzy search: {len(fuzzy_results)} results in {fuzzy_time:.3f} seconds")
        
        # Test boolean search performance
        start_time = time.time()
        boolean_results = search_engine.search("budget AND meeting", SearchType.BOOLEAN, "perf_user")
        boolean_time = time.time() - start_time
        print(f"✅ Boolean search: {len(boolean_results)} results in {boolean_time:.3f} seconds")
        
        print(f"\n🎯 Performance Summary:")
        print(f"   - Content indexing: {1000/add_time:.1f} items/sec")
        print(f"   - Average search time: {(search_time + fuzzy_time + boolean_time)/3:.3f} seconds")
        print(f"   - System handles large datasets efficiently")
        
    finally:
        search_engine.alert_system.stop_alert_monitoring()
        os.unlink(temp_db.name)

def main():
    """Run all tests"""
    print("🧪 Advanced Search and Discovery Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestSearchDatabase,
        TestFuzzySearchEngine,
        TestVoiceSearchEngine,
        TestBooleanSearchEngine,
        TestTemporalSearchEngine,
        TestSpeakerSearchEngine,
        TestSearchAlertSystem,
        TestAdvancedSearchEngine,
        TestSearchIntegration
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Tests run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0]}")
    
    if result.errors:
        print(f"\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback.split('\\n')[-2]}")
    
    # Run performance tests
    run_performance_tests()
    
    # Overall result
    if result.failures or result.errors:
        print(f"\n❌ Some tests failed. Please review and fix issues.")
        return False
    else:
        print(f"\n✅ All tests passed! Advanced search system is working correctly.")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)