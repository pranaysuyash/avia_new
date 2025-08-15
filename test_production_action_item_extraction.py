#!/usr/bin/env python3
"""
Comprehensive Test Suite for Production Action Item Extraction System
Tests BERT-NER based extraction, database operations, and enterprise features.
"""

import unittest
import os
import tempfile
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from production_action_item_extraction_system import (
    ProductionActionItemExtractionSystem,
    ActionItem,
    ActionItemPriority,
    ActionItemStatus,
    ActionItemAssignee,
    ActionItemDeadline,
    DeadlineType,
    ExtractionMethod,
    EntityType,
    EntityExtraction,
    BERTActionItemExtractor,
    SpacyActionItemExtractor,
    RuleBasedActionItemExtractor,
    ActionItemDatabase,
    extract_action_items_from_meeting
)

class TestProductionActionItemExtractionSystem(unittest.TestCase):
    """Test the main production action item extraction system"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create temporary database
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize system
        self.system = ProductionActionItemExtractionSystem(db_path=self.db_path)
        
        # Sample test data
        self.sample_transcript = """
        [14:00] Project Manager: Welcome to our weekly project review meeting.
        [14:02] Sarah: I'll complete the API documentation review by tomorrow end of day.
        [14:05] John: The dashboard implementation needs to be done by next Friday. Can you handle that, Mike?
        [14:07] Mike: Yes, I'll have the dashboard ready by Friday morning.
        [14:10] Project Manager: Alice, please prepare the client presentation urgently for Monday's meeting.
        [14:12] Alice: I'll work on the presentation this weekend to have it ready.
        [14:15] Project Manager: We also need someone to test the new authentication module.
        [14:17] Sarah: I can test the auth module after I finish the documentation review.
        """
        
        self.complex_transcript = """
        [09:00] CEO: Good morning everyone. We have several critical items to discuss today.
        [09:02] Product Manager: The new feature rollout is behind schedule. Tom, can you prioritize the backend API by end of week?
        [09:05] Tom: Absolutely. I'll have the API endpoints completed by Friday 5 PM.
        [09:08] Marketing Director: We need the marketing campaign materials ASAP. Lisa, can you handle the social media content?
        [09:10] Lisa: Sure, I'll create the social media posts by tomorrow morning.
        [09:12] CEO: The quarterly report is due next month. Finance team, please prepare the initial draft by the 15th.
        [09:15] CFO: We'll have the financial analysis ready by the 15th. Jane will handle the revenue projections.
        [09:18] Product Manager: The user testing sessions need to be scheduled. Can someone coordinate with the UX team?
        [09:20] UX Lead: I'll set up the testing sessions within 2 weeks and send out the calendar invites.
        [09:22] CEO: Great. Let's also ensure the security audit is completed before the product launch.
        """
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_system_initialization(self):
        """Test system initialization"""
        self.assertIsNotNone(self.system)
        self.assertIsNotNone(self.system.db)
        self.assertIsNotNone(self.system.bert_extractor)
        self.assertIsNotNone(self.system.spacy_extractor)
        self.assertIsNotNone(self.system.rule_extractor)
        self.assertTrue(len(self.system.session_id) > 0)
    
    def test_basic_action_item_extraction(self):
        """Test basic action item extraction"""
        action_items = self.system.extract_action_items(self.sample_transcript, "test_meeting_001")
        
        self.assertGreater(len(action_items), 0)
        
        # Check that action items have required fields
        for item in action_items:
            self.assertIsInstance(item, ActionItem)
            self.assertTrue(len(item.id) > 0)
            self.assertTrue(len(item.content) > 0)
            self.assertIsInstance(item.priority, ActionItemPriority)
            self.assertIsInstance(item.status, ActionItemStatus)
            self.assertIsInstance(item.assignees, list)
            self.assertGreaterEqual(item.confidence, 0.0)
            self.assertLessEqual(item.confidence, 1.0)
            self.assertIsInstance(item.extraction_method, ExtractionMethod)
    
    def test_complex_transcript_extraction(self):
        """Test extraction from complex meeting transcript"""
        action_items = self.system.extract_action_items(self.complex_transcript, "complex_meeting_001")
        
        self.assertGreater(len(action_items), 3)  # Should extract multiple items
        
        # Check for specific expected extractions
        extracted_content = [item.content.lower() for item in action_items]
        
        # Should extract various types of action items
        has_api_task = any('api' in content for content in extracted_content)
        has_marketing_task = any('marketing' in content or 'social media' in content for content in extracted_content)
        has_report_task = any('report' in content or 'financial' in content for content in extracted_content)
        
        # At least some of these should be found
        self.assertTrue(has_api_task or has_marketing_task or has_report_task)
    
    def test_assignee_extraction(self):
        """Test assignee extraction from transcripts"""
        action_items = self.system.extract_action_items(self.sample_transcript, "assignee_test")
        
        # Check for extracted assignees
        all_assignees = []
        for item in action_items:
            all_assignees.extend([a.name for a in item.assignees])
        
        # Should extract some names
        self.assertGreater(len(all_assignees), 0)
        
        # Check assignee properties
        for item in action_items:
            for assignee in item.assignees:
                self.assertIsInstance(assignee, ActionItemAssignee)
                self.assertTrue(len(assignee.name) > 0)
                self.assertGreaterEqual(assignee.confidence, 0.0)
                self.assertLessEqual(assignee.confidence, 1.0)
                self.assertTrue(len(assignee.assignment_method) > 0)
    
    def test_deadline_extraction(self):
        """Test deadline extraction and parsing"""
        transcript_with_deadlines = """
        [10:00] Manager: Please complete the report by tomorrow.
        [10:05] Developer: I'll finish the feature by next Friday.
        [10:10] Designer: The mockups need to be done by end of week.
        [10:15] Analyst: Can you submit the analysis by the 15th of next month?
        """
        
        action_items = self.system.extract_action_items(transcript_with_deadlines, "deadline_test")
        
        # Check for deadline extraction
        items_with_deadlines = [item for item in action_items if item.deadline is not None]
        self.assertGreater(len(items_with_deadlines), 0)
        
        # Check deadline properties
        for item in items_with_deadlines:
            self.assertIsInstance(item.deadline, ActionItemDeadline)
            self.assertIsInstance(item.deadline.deadline_type, DeadlineType)
            self.assertTrue(len(item.deadline.original_text) > 0)
            self.assertGreaterEqual(item.deadline.confidence, 0.0)
            self.assertLessEqual(item.deadline.confidence, 1.0)
    
    def test_priority_detection(self):
        """Test priority level detection"""
        transcript_with_priorities = """
        [10:00] Manager: This is urgent - we need the security patch ASAP.
        [10:05] Developer: The low priority feature can wait until next sprint.
        [10:10] Director: Critical issue - fix the production bug immediately.
        [10:15] Lead: When time permits, please update the documentation.
        """
        
        action_items = self.system.extract_action_items(transcript_with_priorities, "priority_test")
        
        # Check for different priority levels
        priorities = [item.priority for item in action_items]
        
        # Should detect various priority levels
        self.assertGreater(len(priorities), 0)
        
        # Check that priorities are valid enum values
        for priority in priorities:
            self.assertIsInstance(priority, ActionItemPriority)
    
    def test_database_storage_and_retrieval(self):
        """Test database storage and retrieval of action items"""
        # Extract and store action items
        action_items = self.system.extract_action_items(self.sample_transcript, "db_test")
        
        # Retrieve all action items
        retrieved_items = self.system.db.get_action_items()
        
        self.assertEqual(len(action_items), len(retrieved_items))
        
        # Check that data is preserved
        for original, retrieved in zip(action_items, retrieved_items):
            self.assertEqual(original.id, retrieved.id)
            self.assertEqual(original.content, retrieved.content)
            self.assertEqual(original.priority, retrieved.priority)
            self.assertEqual(original.status, retrieved.status)
            self.assertEqual(len(original.assignees), len(retrieved.assignees))
    
    def test_status_filtering(self):
        """Test filtering action items by status"""
        # Create action items
        action_items = self.system.extract_action_items(self.sample_transcript, "status_test")
        
        # Update some statuses
        if action_items:
            self.system.update_action_item_status(action_items[0].id, ActionItemStatus.COMPLETED)
            if len(action_items) > 1:
                self.system.update_action_item_status(action_items[1].id, ActionItemStatus.IN_PROGRESS)
        
        # Test filtering
        pending_items = self.system.get_action_items_by_status(ActionItemStatus.PENDING)
        completed_items = self.system.get_action_items_by_status(ActionItemStatus.COMPLETED)
        in_progress_items = self.system.get_action_items_by_status(ActionItemStatus.IN_PROGRESS)
        
        # Should have items in different statuses
        if action_items:
            self.assertGreaterEqual(len(completed_items), 1)
            if len(action_items) > 1:
                self.assertGreaterEqual(len(in_progress_items), 1)
    
    def test_overdue_detection(self):
        """Test overdue action item detection"""
        # Create action item with past deadline
        past_deadline = ActionItemDeadline(
            deadline_type=DeadlineType.SPECIFIC_DATE,
            original_text="yesterday",
            parsed_date=datetime.now() - timedelta(days=1),
            confidence=0.9
        )
        
        overdue_item = ActionItem(
            id="test_overdue_001",
            content="Overdue test task",
            priority=ActionItemPriority.HIGH,
            status=ActionItemStatus.PENDING,
            assignees=[ActionItemAssignee(name="Test User", confidence=0.8)],
            deadline=past_deadline,
            confidence=0.8,
            extraction_method=ExtractionMethod.RULE_BASED
        )
        
        self.system.db.save_action_item(overdue_item)
        
        # Test overdue detection
        overdue_items = self.system.get_overdue_action_items()
        self.assertGreater(len(overdue_items), 0)
        
        # Check that overdue item is detected
        overdue_ids = [item.id for item in overdue_items]
        self.assertIn("test_overdue_001", overdue_ids)
    
    def test_system_status(self):
        """Test system status reporting"""
        # Add some test data
        self.system.extract_action_items(self.sample_transcript, "status_test")
        
        status = self.system.get_system_status()
        
        # Check status structure
        self.assertIn("system_status", status)
        self.assertIn("total_action_items", status)
        self.assertIn("pending_items", status)
        self.assertIn("overdue_items", status)
        self.assertIn("extraction_methods", status)
        self.assertIn("database_path", status)
        self.assertIn("current_session", status)
        
        # Check status values
        self.assertEqual(status["system_status"], "operational")
        self.assertGreaterEqual(status["total_action_items"], 0)
        self.assertGreaterEqual(status["pending_items"], 0)
        self.assertGreaterEqual(status["overdue_items"], 0)
        self.assertEqual(status["database_path"], self.db_path)
        self.assertEqual(status["current_session"], self.system.session_id)
    
    def test_extraction_methods_availability(self):
        """Test that extraction methods are properly initialized"""
        status = self.system.get_system_status()
        extraction_methods = status["extraction_methods"]
        
        # Rule-based should always be available
        self.assertTrue(extraction_methods["rule_based_available"])
        
        # BERT and spaCy availability depends on imports
        self.assertIsInstance(extraction_methods["bert_available"], bool)
        self.assertIsInstance(extraction_methods["spacy_available"], bool)
    
    def test_session_id_generation(self):
        """Test session ID generation and uniqueness"""
        system1 = ProductionActionItemExtractionSystem()
        system2 = ProductionActionItemExtractionSystem()
        
        # Session IDs should be different
        self.assertNotEqual(system1.session_id, system2.session_id)
        
        # Session IDs should be reasonable length
        self.assertGreaterEqual(len(system1.session_id), 8)
        self.assertLessEqual(len(system1.session_id), 20)
    
    def test_empty_transcript_handling(self):
        """Test handling of empty or invalid transcripts"""
        # Empty transcript
        action_items = self.system.extract_action_items("", "empty_test")
        self.assertEqual(len(action_items), 0)
        
        # Whitespace only
        action_items = self.system.extract_action_items("   \n\t  ", "whitespace_test")
        self.assertEqual(len(action_items), 0)
        
        # No action items
        action_items = self.system.extract_action_items("This is just a conversation with no action items.", "no_action_test")
        # Should handle gracefully (may or may not extract items, but shouldn't crash)
        self.assertIsInstance(action_items, list)

class TestActionItemDatabase(unittest.TestCase):
    """Test the action item database functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.db = ActionItemDatabase(db_path=self.db_path)
    
    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test database initialization and schema creation"""
        self.assertTrue(os.path.exists(self.db_path))
        
        # Check that tables were created
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['action_items', 'assignees', 'dependencies', 'tags', 'extraction_metrics']
            for table in expected_tables:
                self.assertIn(table, tables)
    
    def test_action_item_crud_operations(self):
        """Test Create, Read, Update, Delete operations"""
        # Create test action item
        action_item = ActionItem(
            id="test_crud_001",
            content="Test CRUD operations",
            priority=ActionItemPriority.HIGH,
            status=ActionItemStatus.PENDING,
            assignees=[
                ActionItemAssignee(name="Test User 1", confidence=0.9),
                ActionItemAssignee(name="Test User 2", role="Developer", confidence=0.8)
            ],
            deadline=ActionItemDeadline(
                deadline_type=DeadlineType.SPECIFIC_DATE,
                original_text="tomorrow",
                parsed_date=datetime.now() + timedelta(days=1),
                confidence=0.9
            ),
            dependencies=["dep_001", "dep_002"],
            tags=["urgent", "backend"],
            confidence=0.85,
            extraction_method=ExtractionMethod.BERT_NER
        )
        
        # Save action item
        self.db.save_action_item(action_item)
        
        # Retrieve action items
        retrieved_items = self.db.get_action_items()
        self.assertEqual(len(retrieved_items), 1)
        
        retrieved_item = retrieved_items[0]
        self.assertEqual(retrieved_item.id, action_item.id)
        self.assertEqual(retrieved_item.content, action_item.content)
        self.assertEqual(retrieved_item.priority, action_item.priority)
        self.assertEqual(retrieved_item.status, action_item.status)
        self.assertEqual(len(retrieved_item.assignees), 2)
        self.assertEqual(len(retrieved_item.dependencies), 2)
        self.assertEqual(len(retrieved_item.tags), 2)
        self.assertIsNotNone(retrieved_item.deadline)

class TestBERTActionItemExtractor(unittest.TestCase):
    """Test BERT-based action item extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = BERTActionItemExtractor()
    
    def test_extractor_initialization(self):
        """Test BERT extractor initialization"""
        self.assertIsNotNone(self.extractor)
        # Note: BERT models may not be available in all test environments
    
    def test_entity_extraction(self):
        """Test entity extraction functionality"""
        test_text = "John will complete the project by Friday."
        entities = self.extractor.extract_entities(test_text)
        
        # Should return list (may be empty if BERT not available)
        self.assertIsInstance(entities, list)
        
        # If entities are extracted, check their structure
        for entity in entities:
            self.assertIsInstance(entity, EntityExtraction)
            self.assertTrue(len(entity.text) > 0)
            self.assertIsInstance(entity.entity_type, EntityType)
            self.assertGreaterEqual(entity.start_pos, 0)
            self.assertGreaterEqual(entity.end_pos, entity.start_pos)
            self.assertGreaterEqual(entity.confidence, 0.0)
            self.assertLessEqual(entity.confidence, 1.0)
            self.assertEqual(entity.extraction_method, ExtractionMethod.BERT_NER)

class TestSpacyActionItemExtractor(unittest.TestCase):
    """Test spaCy-based action item extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = SpacyActionItemExtractor()
    
    def test_extractor_initialization(self):
        """Test spaCy extractor initialization"""
        self.assertIsNotNone(self.extractor)
    
    def test_entity_extraction(self):
        """Test entity extraction functionality"""
        test_text = "Sarah will prepare the presentation by Monday."
        entities = self.extractor.extract_entities(test_text)
        
        # Should return list (may be empty if spaCy not available)
        self.assertIsInstance(entities, list)
        
        # If entities are extracted, check their structure
        for entity in entities:
            self.assertIsInstance(entity, EntityExtraction)
            self.assertTrue(len(entity.text) > 0)
            self.assertIsInstance(entity.entity_type, EntityType)
            self.assertGreaterEqual(entity.start_pos, 0)
            self.assertGreaterEqual(entity.end_pos, entity.start_pos)
            self.assertGreaterEqual(entity.confidence, 0.0)
            self.assertLessEqual(entity.confidence, 1.0)
            self.assertEqual(entity.extraction_method, ExtractionMethod.SPACY_NER)

class TestRuleBasedActionItemExtractor(unittest.TestCase):
    """Test rule-based action item extraction"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = RuleBasedActionItemExtractor()
    
    def test_extractor_initialization(self):
        """Test rule-based extractor initialization"""
        self.assertIsNotNone(self.extractor)
        self.assertIsInstance(self.extractor.action_patterns, list)
        self.assertIsInstance(self.extractor.person_patterns, list)
        self.assertIsInstance(self.extractor.deadline_patterns, list)
        self.assertIsInstance(self.extractor.priority_patterns, list)
    
    def test_person_extraction(self):
        """Test person name extraction"""
        test_text = "John will complete the task and @sarah will review it."
        entities = self.extractor.extract_entities(test_text)
        
        person_entities = [e for e in entities if e.entity_type == EntityType.PERSON]
        self.assertGreater(len(person_entities), 0)
        
        # Check for specific extractions
        person_names = [e.text.lower() for e in person_entities]
        self.assertTrue(any('john' in name for name in person_names) or any('sarah' in name for name in person_names))
    
    def test_deadline_extraction(self):
        """Test deadline extraction"""
        test_text = "Please complete this by tomorrow and submit the report by next Friday."
        entities = self.extractor.extract_entities(test_text)
        
        deadline_entities = [e for e in entities if e.entity_type == EntityType.DEADLINE]
        self.assertGreater(len(deadline_entities), 0)
        
        # Check for specific deadline patterns
        deadline_texts = [e.text.lower() for e in deadline_entities]
        self.assertTrue(any('tomorrow' in text for text in deadline_texts) or any('friday' in text for text in deadline_texts))
    
    def test_priority_extraction(self):
        """Test priority extraction"""
        test_text = "This is urgent - we need it ASAP. The low priority task can wait."
        entities = self.extractor.extract_entities(test_text)
        
        priority_entities = [e for e in entities if e.entity_type == EntityType.PRIORITY]
        self.assertGreater(len(priority_entities), 0)
        
        # Check for specific priority patterns
        priority_texts = [e.text.lower() for e in priority_entities]
        self.assertTrue(any('urgent' in text or 'asap' in text for text in priority_texts))

class TestEntryPointFunction(unittest.TestCase):
    """Test the main entry point function"""
    
    def test_extract_action_items_from_meeting(self):
        """Test the main extraction function"""
        transcript = "Alice will prepare the report by tomorrow."
        action_items = extract_action_items_from_meeting(transcript, "test_meeting")
        
        self.assertIsInstance(action_items, list)
        # Function should work without throwing exceptions

def run_comprehensive_tests():
    """Run all tests with detailed output"""
    
    print("=== Running Comprehensive Production Action Item Extraction Tests ===\n")
    
    # Create test suite
    test_classes = [
        TestProductionActionItemExtractionSystem,
        TestActionItemDatabase,
        TestBERTActionItemExtractor,
        TestSpacyActionItemExtractor,
        TestRuleBasedActionItemExtractor,
        TestEntryPointFunction
    ]
    
    total_tests = 0
    total_failures = 0
    total_errors = 0
    
    for test_class in test_classes:
        print(f"Running {test_class.__name__}...")
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        total_tests += result.testsRun
        total_failures += len(result.failures)
        total_errors += len(result.errors)
        
        if result.failures:
            print(f"❌ Failures in {test_class.__name__}:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback}")
        
        if result.errors:
            print(f"❌ Errors in {test_class.__name__}:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback}")
        
        print()
    
    print("=== Test Results ===")
    print(f"Tests run: {total_tests}")
    print(f"Failures: {total_failures}")
    print(f"Errors: {total_errors}")
    print(f"Success rate: {((total_tests - total_failures - total_errors) / total_tests * 100):.1f}%")
    
    if total_failures == 0 and total_errors == 0:
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)