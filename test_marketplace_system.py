#!/usr/bin/env python3
"""
Test Suite for Marketplace and Template System (Task 51)
Comprehensive tests for marketplace functionality, templates, entity rules, voice models, and community features
"""

import unittest
import tempfile
import os
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from marketplace_system import (
    MarketplaceSystem, MarketplaceDatabase, TemplateMarketplace,
    EntityRuleMarketplace, VoiceModelMarketplace, ScriptTemplateLibrary,
    CommunitySystem, MarketplaceItem, Template, EntityExtractionRule,
    VoiceModel, ScriptTemplate, MarketplaceReview, MarketplaceTransaction,
    MarketplaceItemType, ItemStatus, ItemCategory, LicenseType
)

class TestMarketplaceDatabase(unittest.TestCase):
    """Test marketplace database functionality"""
    
    def setUp(self):
        """Set up test database"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
    
    def tearDown(self):
        """Clean up test database"""
        os.unlink(self.temp_db.name)
    
    def test_database_initialization(self):
        """Test database table creation"""
        # Database should initialize without errors
        self.assertIsNotNone(self.db)
        
        # Check if tables exist
        import sqlite3
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Check marketplace_items table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='marketplace_items'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check templates table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='templates'")
            self.assertIsNotNone(cursor.fetchone())
            
            # Check entity_rules table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='entity_rules'")
            self.assertIsNotNone(cursor.fetchone())
    
    def test_add_marketplace_item(self):
        """Test adding marketplace item"""
        item = MarketplaceItem(
            item_id="test_item_1",
            name="Test Template",
            description="A test template for testing",
            item_type=MarketplaceItemType.TEMPLATE.value,
            category=ItemCategory.BUSINESS.value,
            author_id="test_user",
            author_name="Test User",
            version="1.0",
            license_type=LicenseType.FREE.value,
            price=0.0,
            tags=["test", "template"],
            status=ItemStatus.APPROVED.value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        success = self.db.add_marketplace_item(item)
        self.assertTrue(success)
        
        # Verify item was added
        items = self.db.get_marketplace_items(limit=10)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].name, "Test Template")
    
    def test_get_marketplace_items_with_filters(self):
        """Test getting marketplace items with filters"""
        # Add multiple items
        items = [
            MarketplaceItem(
                item_id="template_1", name="Template 1", description="Test template",
                item_type=MarketplaceItemType.TEMPLATE.value, category=ItemCategory.BUSINESS.value,
                author_id="user1", author_name="User 1", version="1.0",
                license_type=LicenseType.FREE.value, price=0.0, tags=["business"],
                status=ItemStatus.APPROVED.value, created_at=datetime.now(), updated_at=datetime.now()
            ),
            MarketplaceItem(
                item_id="rule_1", name="Entity Rule 1", description="Test rule",
                item_type=MarketplaceItemType.ENTITY_RULE.value, category=ItemCategory.GENERAL.value,
                author_id="user2", author_name="User 2", version="1.0",
                license_type=LicenseType.FREE.value, price=0.0, tags=["entity"],
                status=ItemStatus.APPROVED.value, created_at=datetime.now(), updated_at=datetime.now()
            )
        ]
        
        for item in items:
            self.db.add_marketplace_item(item)
        
        # Test type filter
        templates = self.db.get_marketplace_items(item_type=MarketplaceItemType.TEMPLATE.value)
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].item_type, MarketplaceItemType.TEMPLATE.value)
        
        # Test category filter
        business_items = self.db.get_marketplace_items(category=ItemCategory.BUSINESS.value)
        self.assertEqual(len(business_items), 1)
        self.assertEqual(business_items[0].category, ItemCategory.BUSINESS.value)
    
    def test_add_template(self):
        """Test adding template"""
        template = Template(
            template_id="template_test_1",
            name="Test Template",
            description="A test template",
            category="meeting",
            use_case="Testing templates",
            template_data={"sections": ["intro", "body", "conclusion"]},
            author_id="test_user",
            created_at=datetime.now(),
            tags=["test", "meeting"]
        )
        
        success = self.db.add_template(template)
        self.assertTrue(success)
    
    def test_add_entity_rule(self):
        """Test adding entity extraction rule"""
        rule = EntityExtractionRule(
            rule_id="rule_test_1",
            name="Test Rule",
            description="A test entity rule",
            entity_type="ORGANIZATION",
            pattern="Inc|LLC|Corp",
            author_id="test_user",
            created_at=datetime.now(),
            examples=["Apple Inc", "Google LLC"]
        )
        
        success = self.db.add_entity_rule(rule)
        self.assertTrue(success)
    
    def test_add_voice_model(self):
        """Test adding voice model"""
        model = VoiceModel(
            model_id="voice_test_1",
            name="Test Voice",
            description="A test voice model",
            language="en",
            gender="female",
            accent="american",
            author_id="test_user",
            created_at=datetime.now()
        )
        
        success = self.db.add_voice_model(model)
        self.assertTrue(success)
    
    def test_add_script_template(self):
        """Test adding script template"""
        template = ScriptTemplate(
            template_id="script_test_1",
            name="Test Script",
            description="A test script template",
            category="podcast",
            template_content="Welcome to {show_name}",
            variables=["show_name"],
            author_id="test_user",
            created_at=datetime.now()
        )
        
        success = self.db.add_script_template(template)
        self.assertTrue(success)class
 TestTemplateMarketplace(unittest.TestCase):
    """Test template marketplace functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.template_marketplace = TemplateMarketplace(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_template(self):
        """Test template creation"""
        template_id = self.template_marketplace.create_template(
            name="Test Template",
            description="A test template",
            category="meeting",
            use_case="Testing",
            template_data={"sections": ["intro", "body"]},
            author_id="test_user",
            tags=["test"]
        )
        
        self.assertIsNotNone(template_id)
        
        # Verify template was created
        templates = self.template_marketplace.get_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "Test Template")
    
    def test_search_templates(self):
        """Test template search"""
        # Create test templates
        self.template_marketplace.create_template(
            "Meeting Template", "For meetings", "meeting", "Meetings",
            {"sections": ["agenda"]}, "user1", ["meeting"]
        )
        self.template_marketplace.create_template(
            "Interview Template", "For interviews", "interview", "Interviews",
            {"sections": ["questions"]}, "user2", ["interview"]
        )
        
        # Search for meeting templates
        results = self.template_marketplace.search_templates("meeting")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Meeting Template")
    
    def test_get_popular_templates(self):
        """Test getting popular templates"""
        # Create templates with different ratings
        template_id = self.template_marketplace.create_template(
            "Popular Template", "Very popular", "business", "Business",
            {"sections": ["content"]}, "user1", ["popular"]
        )
        
        # Get popular templates
        popular = self.template_marketplace.get_popular_templates(limit=5)
        self.assertIsInstance(popular, list)

class TestEntityRuleMarketplace(unittest.TestCase):
    """Test entity rule marketplace functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.entity_marketplace = EntityRuleMarketplace(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_entity_rule(self):
        """Test entity rule creation"""
        rule_id = self.entity_marketplace.create_entity_rule(
            name="Company Rule",
            description="Extracts company names",
            entity_type="ORGANIZATION",
            pattern="Inc|LLC|Corp",
            author_id="test_user",
            examples=["Apple Inc", "Google LLC"]
        )
        
        self.assertIsNotNone(rule_id)
        
        # Verify rule was created
        rules = self.entity_marketplace.get_entity_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "Company Rule")
    
    def test_test_entity_rule(self):
        """Test entity rule testing functionality"""
        # Create a rule
        rule_id = self.entity_marketplace.create_entity_rule(
            "Test Rule", "Test rule", "ORGANIZATION", "Inc|LLC",
            "test_user", regex_pattern=r'\b\w+\s+(Inc|LLC)\b'
        )
        
        # Test the rule
        result = self.entity_marketplace.test_entity_rule(
            rule_id, "Apple Inc and Google LLC are companies"
        )
        
        self.assertIn('matches', result)
        self.assertGreater(result['match_count'], 0)class T
estVoiceModelMarketplace(unittest.TestCase):
    """Test voice model marketplace functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.voice_marketplace = VoiceModelMarketplace(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_add_voice_model(self):
        """Test voice model addition"""
        model_id = self.voice_marketplace.add_voice_model(
            name="Test Voice",
            description="A test voice",
            language="en",
            gender="female",
            accent="american",
            author_id="test_user"
        )
        
        self.assertIsNotNone(model_id)
        
        # Verify model was added
        models = self.voice_marketplace.get_voice_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].name, "Test Voice")
    
    def test_preview_voice_model(self):
        """Test voice model preview"""
        # Add a voice model
        model_id = self.voice_marketplace.add_voice_model(
            "Preview Voice", "Test voice", "en", "male", "british", "test_user"
        )
        
        # Test preview
        result = self.voice_marketplace.preview_voice_model(
            model_id, "Hello world"
        )
        
        self.assertIn('model_id', result)
        self.assertIn('preview_text', result)

class TestScriptTemplateLibrary(unittest.TestCase):
    """Test script template library functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.script_library = ScriptTemplateLibrary(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_script_template(self):
        """Test script template creation"""
        template_id = self.script_library.create_script_template(
            name="Podcast Intro",
            description="Podcast introduction template",
            category="podcast",
            template_content="Welcome to {show_name}",
            variables=["show_name"],
            author_id="test_user"
        )
        
        self.assertIsNotNone(template_id)
        
        # Verify template was created
        templates = self.script_library.get_script_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "Podcast Intro")
    
    def test_generate_script(self):
        """Test script generation"""
        # Create template
        template_id = self.script_library.create_script_template(
            "Test Script", "Test template", "test",
            "Hello {name}, welcome to {show}",
            ["name", "show"], "test_user"
        )
        
        # Generate script
        result = self.script_library.generate_script(
            template_id, {"name": "John", "show": "Tech Talk"}
        )
        
        self.assertIn('generated_content', result)
        self.assertEqual(result['generated_content'], "Hello John, welcome to Tech Talk")

def main():
    """Run all tests"""
    print("🧪 Marketplace and Template System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMarketplaceDatabase,
        TestTemplateMarketplace,
        TestEntityRuleMarketplace,
        TestVoiceModelMarketplace,
        TestScriptTemplateLibrary
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
    success_rate = ((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100) if result.testsRun > 0 else 0
    print(f"   Success rate: {success_rate:.1f}%")
    
    if result.failures or result.errors:
        print(f"\n❌ Some tests failed. Please review and fix issues.")
        return False
    else:
        print(f"\n✅ All tests passed! Marketplace system is working correctly.")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)class 
TestTemplateMarketplace(unittest.TestCase):
    """Test template marketplace functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.template_marketplace = TemplateMarketplace(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_template(self):
        """Test creating template"""
        template_id = self.template_marketplace.create_template(
            name="Test Meeting Template",
            description="Template for team meetings",
            category="meeting",
            use_case="Team standup meetings",
            template_data={
                "sections": ["Agenda", "Discussion", "Action Items"],
                "fields": ["date", "attendees", "duration"]
            },
            author_id="test_user",
            tags=["meeting", "team"]
        )
        
        self.assertIsNotNone(template_id)
        
        # Verify template was created
        templates = self.template_marketplace.get_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "Test Meeting Template")
    
    def test_get_templates_by_category(self):
        """Test getting templates by category"""
        # Create templates in different categories
        self.template_marketplace.create_template(
            "Meeting Template", "Meeting template", "meeting", "Meetings",
            {"sections": ["agenda"]}, "user1", ["meeting"]
        )
        self.template_marketplace.create_template(
            "Interview Template", "Interview template", "interview", "Interviews",
            {"sections": ["questions"]}, "user2", ["interview"]
        )
        
        # Test category filtering
        meeting_templates = self.template_marketplace.get_templates(category="meeting")
        self.assertEqual(len(meeting_templates), 1)
        self.assertEqual(meeting_templates[0].category, "meeting")
        
        interview_templates = self.template_marketplace.get_templates(category="interview")
        self.assertEqual(len(interview_templates), 1)
        self.assertEqual(interview_templates[0].category, "interview")
    
    def test_search_templates(self):
        """Test template search functionality"""
        # Create test templates
        self.template_marketplace.create_template(
            "Meeting Minutes Template", "Template for meeting minutes", "meeting",
            "Recording meeting minutes", {"sections": ["notes"]}, "user1", ["meeting", "minutes"]
        )
        
        # Search by name
        results = self.template_marketplace.search_templates("meeting")
        self.assertEqual(len(results), 1)
        
        # Search by tag
        results = self.template_marketplace.search_templates("minutes")
        self.assertEqual(len(results), 1)

class TestEntityRuleMarketplace(unittest.TestCase):
    """Test entity rule marketplace functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.entity_marketplace = EntityRuleMarketplace(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_entity_rule(self):
        """Test creating entity extraction rule"""
        rule_id = self.entity_marketplace.create_entity_rule(
            name="Company Name Extractor",
            description="Extracts company names from text",
            entity_type="ORGANIZATION",
            pattern="Inc|LLC|Corp|Ltd",
            author_id="test_user",
            regex_pattern=r'\b[A-Z][a-zA-Z\s]+(?:Inc|LLC|Corp|Ltd)\b',
            examples=["Apple Inc", "Microsoft Corp", "Google LLC"]
        )
        
        self.assertIsNotNone(rule_id)
        
        # Verify rule was created
        rules = self.entity_marketplace.get_entity_rules()
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0].name, "Company Name Extractor")
    
    def test_get_entity_rules_by_type(self):
        """Test getting entity rules by type"""
        # Create rules for different entity types
        self.entity_marketplace.create_entity_rule(
            "Person Extractor", "Extract person names", "PERSON",
            "Mr|Ms|Dr", "user1", examples=["Mr. Smith"]
        )
        self.entity_marketplace.create_entity_rule(
            "Company Extractor", "Extract companies", "ORGANIZATION",
            "Inc|LLC", "user2", examples=["Apple Inc"]
        )
        
        # Test type filtering
        person_rules = self.entity_marketplace.get_entity_rules(entity_type="PERSON")
        self.assertEqual(len(person_rules), 1)
        self.assertEqual(person_rules[0].entity_type, "PERSON")
        
        org_rules = self.entity_marketplace.get_entity_rules(entity_type="ORGANIZATION")
        self.assertEqual(len(org_rules), 1)
        self.assertEqual(org_rules[0].entity_type, "ORGANIZATION")
    
    def test_test_entity_rule(self):
        """Test entity rule testing functionality"""
        # Create a rule
        rule_id = self.entity_marketplace.create_entity_rule(
            "Test Rule", "Test rule", "ORGANIZATION", "Inc|LLC", "user1",
            regex_pattern=r'\b[A-Z][a-zA-Z\s]+(?:Inc|LLC)\b'
        )
        
        # Test the rule
        result = self.entity_marketplace.test_entity_rule(
            rule_id, "Apple Inc and Google LLC are tech companies."
        )
        
        self.assertIn('matches', result)
        self.assertGreater(result['match_count'], 0)

class TestVoiceModelMarketplace(unittest.TestCase):
    """Test voice model marketplace functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.voice_marketplace = VoiceModelMarketplace(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_add_voice_model(self):
        """Test adding voice model"""
        model_id = self.voice_marketplace.add_voice_model(
            name="Professional Female Voice",
            description="Clear professional female voice",
            language="en",
            gender="female",
            accent="american",
            author_id="test_user"
        )
        
        self.assertIsNotNone(model_id)
        
        # Verify model was added
        models = self.voice_marketplace.get_voice_models()
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0].name, "Professional Female Voice")
    
    def test_get_voice_models_with_filters(self):
        """Test getting voice models with filters"""
        # Add multiple voice models
        self.voice_marketplace.add_voice_model(
            "English Female", "English female voice", "en", "female", "american", "user1"
        )
        self.voice_marketplace.add_voice_model(
            "Spanish Male", "Spanish male voice", "es", "male", "neutral", "user2"
        )
        
        # Test language filter
        english_models = self.voice_marketplace.get_voice_models(language="en")
        self.assertEqual(len(english_models), 1)
        self.assertEqual(english_models[0].language, "en")
        
        # Test gender filter
        female_models = self.voice_marketplace.get_voice_models(gender="female")
        self.assertEqual(len(female_models), 1)
        self.assertEqual(female_models[0].gender, "female")
    
    def test_preview_voice_model(self):
        """Test voice model preview"""
        # Add a voice model
        model_id = self.voice_marketplace.add_voice_model(
            "Test Voice", "Test voice model", "en", "female", "american", "user1"
        )
        
        # Test preview
        result = self.voice_marketplace.preview_voice_model(
            model_id, "Hello, this is a test."
        )
        
        self.assertIn('model_id', result)
        self.assertIn('preview_text', result)
        self.assertEqual(result['model_id'], model_id)

class TestScriptTemplateLibrary(unittest.TestCase):
    """Test script template library functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.script_library = ScriptTemplateLibrary(self.db)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_create_script_template(self):
        """Test creating script template"""
        template_id = self.script_library.create_script_template(
            name="Podcast Intro Template",
            description="Template for podcast introductions",
            category="podcast",
            template_content="Welcome to {podcast_name}, I'm your host {host_name}.",
            variables=["podcast_name", "host_name"],
            author_id="test_user",
            examples=["Welcome to Tech Talk, I'm your host John Smith."]
        )
        
        self.assertIsNotNone(template_id)
        
        # Verify template was created
        templates = self.script_library.get_script_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0].name, "Podcast Intro Template")
    
    def test_generate_script(self):
        """Test script generation from template"""
        # Create template
        template_id = self.script_library.create_script_template(
            "Test Template", "Test template", "test",
            "Hello {name}, welcome to {show}!",
            ["name", "show"], "user1"
        )
        
        # Generate script
        result = self.script_library.generate_script(
            template_id, {"name": "John", "show": "Tech Talk"}
        )
        
        self.assertIn('generated_content', result)
        self.assertEqual(result['generated_content'], "Hello John, welcome to Tech Talk!")
        self.assertIn('word_count', result)
        self.assertGreater(result['word_count'], 0)
    
    def test_generate_script_missing_variables(self):
        """Test script generation with missing variables"""
        # Create template
        template_id = self.script_library.create_script_template(
            "Test Template", "Test template", "test",
            "Hello {name}!", ["name"], "user1"
        )
        
        # Try to generate without providing variables
        result = self.script_library.generate_script(template_id, {})
        
        self.assertIn('error', result)
        self.assertIn('Missing variables', result['error'])

class TestCommunitySystem(unittest.TestCase):
    """Test community system functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db = MarketplaceDatabase(self.temp_db.name)
        self.community = CommunitySystem(self.db)
        
        # Add a test marketplace item
        self.test_item = MarketplaceItem(
            item_id="test_item_1",
            name="Test Item",
            description="A test item",
            item_type=MarketplaceItemType.TEMPLATE.value,
            category=ItemCategory.GENERAL.value,
            author_id="test_author",
            author_name="Test Author",
            version="1.0",
            license_type=LicenseType.FREE.value,
            price=0.0,
            tags=["test"],
            status=ItemStatus.APPROVED.value,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        self.db.add_marketplace_item(self.test_item)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_add_review(self):
        """Test adding review"""
        review_id = self.community.add_review(
            item_id="test_item_1",
            user_id="test_user",
            rating=5,
            comment="Great template!",
            verified_purchase=True
        )
        
        self.assertIsNotNone(review_id)
        
        # Verify review was added
        reviews = self.community.get_reviews("test_item_1")
        self.assertEqual(len(reviews), 1)
        self.assertEqual(reviews[0].rating, 5)
        self.assertEqual(reviews[0].comment, "Great template!")
    
    def test_create_user_collection(self):
        """Test creating user collection"""
        collection_id = self.community.create_user_collection(
            user_id="test_user",
            name="My Favorites",
            description="My favorite templates",
            is_public=False
        )
        
        self.assertIsNotNone(collection_id)
    
    def test_add_item_to_collection(self):
        """Test adding item to collection"""
        # Create collection
        collection_id = self.community.create_user_collection(
            "test_user", "Test Collection", "Test collection"
        )
        
        # Add item to collection
        success = self.community.add_item_to_collection(collection_id, "test_item_1")
        self.assertTrue(success)

class TestMarketplaceSystem(unittest.TestCase):
    """Test main marketplace system"""
    
    def setUp(self):
        """Set up test environment"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.marketplace = MarketplaceSystem(self.temp_db.name)
    
    def tearDown(self):
        """Clean up"""
        os.unlink(self.temp_db.name)
    
    def test_get_marketplace_overview(self):
        """Test getting marketplace overview"""
        # Add some test items
        self.marketplace.template_marketplace.create_template(
            "Test Template", "Test template", "meeting", "Testing",
            {"sections": ["test"]}, "user1", ["test"]
        )
        
        overview = self.marketplace.get_marketplace_overview()
        
        self.assertIn('total_items', overview)
        self.assertIn('items_by_type', overview)
        self.assertIn('categories', overview)
        self.assertGreater(overview['total_items'], 0)
    
    def test_search_marketplace(self):
        """Test marketplace search"""
        # Add test items
        self.marketplace.template_marketplace.create_template(
            "Meeting Template", "Template for meetings", "meeting", "Meetings",
            {"sections": ["agenda"]}, "user1", ["meeting"]
        )
        
        # Search marketplace
        results = self.marketplace.search_marketplace("meeting")
        
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].name, "Meeting Template")
    
    def test_download_item(self):
        """Test item download"""
        # Create a template
        template_id = self.marketplace.template_marketplace.create_template(
            "Download Test", "Test template", "test", "Testing",
            {"sections": ["test"]}, "user1", ["test"]
        )
        
        # Download the item
        result = self.marketplace.download_item(template_id, "test_user")
        
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'success')

def run_performance_tests():
    """Run performance tests for marketplace system"""
    print("\n🚀 Running Performance Tests")
    print("=" * 50)
    
    # Create temporary database
    temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    temp_db.close()
    
    try:
        marketplace = MarketplaceSystem(temp_db.name)
        
        # Add large number of templates
        print("Adding 1000 templates...")
        start_time = time.time()
        
        for i in range(1000):
            marketplace.template_marketplace.create_template(
                f"Template {i}",
                f"Description for template {i}",
                ["meeting", "interview", "podcast"][i % 3],
                f"Use case {i}",
                {"sections": [f"section_{j}" for j in range(3)]},
                f"user_{i % 10}",
                [f"tag_{i % 5}"]
            )
        
        add_time = time.time() - start_time
        print(f"✅ Added 1000 templates in {add_time:.2f} seconds ({1000/add_time:.1f} templates/sec)")
        
        # Test search performance
        start_time = time.time()
        results = marketplace.search_marketplace("template")
        search_time = time.time() - start_time
        print(f"✅ Search: {len(results)} results in {search_time:.3f} seconds")
        
        # Test marketplace overview performance
        start_time = time.time()
        overview = marketplace.get_marketplace_overview()
        overview_time = time.time() - start_time
        print(f"✅ Overview: {overview_time:.3f} seconds")
        
        print(f"\n🎯 Performance Summary:")
        print(f"   - Template creation: {1000/add_time:.1f} templates/sec")
        print(f"   - Search performance: {search_time:.3f} seconds")
        print(f"   - Overview generation: {overview_time:.3f} seconds")
        print(f"   - System handles large datasets efficiently")
        
    finally:
        os.unlink(temp_db.name)

def main():
    """Run all tests"""
    print("🧪 Marketplace and Template System Tests")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestMarketplaceDatabase,
        TestTemplateMarketplace,
        TestEntityRuleMarketplace,
        TestVoiceModelMarketplace,
        TestScriptTemplateLibrary,
        TestCommunitySystem,
        TestMarketplaceSystem
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
        print(f"\n✅ All tests passed! Marketplace system is working correctly.")
        return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)