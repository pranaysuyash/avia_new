"""
Test Suite for Dynamic Output Templates System
Comprehensive tests for template engine, smart formatter, and UI components
"""

import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
import json

from dynamic_output_templates import (
    TemplateEngine, SmartFormatter, TemplateManager,
    ContentMetadata, TranscriptSegment, ActionItem, KeyPoint,
    create_sample_content, format_time_duration, extract_text_statistics
)

class TestContentMetadata:
    """Test ContentMetadata dataclass"""
    
    def test_content_metadata_creation(self):
        """Test creating ContentMetadata instance"""
        metadata = ContentMetadata(
            title="Test Meeting",
            content_type="meeting",
            duration=1800,
            speakers=["Alice", "Bob"],
            date_created=datetime.now()
        )
        
        assert metadata.title == "Test Meeting"
        assert metadata.content_type == "meeting"
        assert metadata.duration == 1800
        assert len(metadata.speakers) == 2
        assert isinstance(metadata.date_created, datetime)
    
    def test_content_metadata_defaults(self):
        """Test ContentMetadata with default values"""
        metadata = ContentMetadata(
            title="Test",
            content_type="general"
        )
        
        assert metadata.duration is None
        assert metadata.language == "en"
        assert metadata.speakers is None
        assert metadata.date_created is None

class TestTranscriptSegment:
    """Test TranscriptSegment dataclass"""
    
    def test_transcript_segment_creation(self):
        """Test creating TranscriptSegment instance"""
        segment = TranscriptSegment(
            start_time=0.0,
            end_time=30.0,
            speaker="Alice",
            text="Hello everyone",
            confidence=0.95
        )
        
        assert segment.start_time == 0.0
        assert segment.end_time == 30.0
        assert segment.speaker == "Alice"
        assert segment.text == "Hello everyone"
        assert segment.confidence == 0.95
    
    def test_transcript_segment_defaults(self):
        """Test TranscriptSegment with default values"""
        segment = TranscriptSegment(
            start_time=0.0,
            end_time=30.0,
            speaker="Alice",
            text="Hello"
        )
        
        assert segment.confidence is None

class TestTemplateEngine:
    """Test TemplateEngine functionality"""
    
    @pytest.fixture
    def temp_templates_dir(self):
        """Create temporary templates directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def template_engine(self, temp_templates_dir):
        """Create TemplateEngine instance with temporary directory"""
        return TemplateEngine(temp_templates_dir)
    
    def test_template_engine_initialization(self, template_engine):
        """Test TemplateEngine initialization"""
        assert template_engine.templates_dir.exists()
        assert template_engine.jinja_env is not None
    
    def test_builtin_templates_creation(self, template_engine):
        """Test that built-in templates are created"""
        templates = template_engine.get_available_templates()
        assert len(templates) > 0
        
        # Check for specific built-in templates
        template_names = [t['name'] for t in templates]
        assert 'meeting_minutes' in template_names
        assert 'interview_summary' in template_names
        assert 'lecture_notes' in template_names
    
    def test_custom_filters(self, template_engine):
        """Test custom Jinja2 filters"""
        # Test format_time filter
        template_content = "{{ 125 | format_time }}"
        template = template_engine.jinja_env.from_string(template_content)
        result = template.render()
        assert result == "02:05"
        
        # Test format_duration filter
        template_content = "{{ 3661 | format_duration }}"
        template = template_engine.jinja_env.from_string(template_content)
        result = template.render()
        assert "1 hour" in result and "1 minute" in result
    
    def test_format_content(self, template_engine):
        """Test content formatting"""
        # Create sample data
        metadata = ContentMetadata(
            title="Test Meeting",
            content_type="meeting",
            duration=1800,
            speakers=["Alice", "Bob"]
        )
        
        segments = [
            TranscriptSegment(0, 30, "Alice", "Hello everyone"),
            TranscriptSegment(30, 60, "Bob", "Thanks for joining")
        ]
        
        # Format content
        result = template_engine.format_content(
            template_name="simple_transcript.txt",
            metadata=metadata,
            transcript_segments=segments
        )
        
        assert result.content is not None
        assert result.format_type == "text"
        assert result.template_name == "simple_transcript.txt"
        assert "Test Meeting" in result.content
        assert "Alice" in result.content
        assert "Bob" in result.content
    
    def test_create_custom_template(self, template_engine):
        """Test creating custom template"""
        template_content = """
        <h1>{{ metadata.title }}</h1>
        <p>Duration: {{ metadata.duration }}</p>
        """
        
        success = template_engine.create_custom_template(
            name="test_custom",
            content=template_content,
            description="Test custom template",
            format_type="html"
        )
        
        assert success
        
        # Check if template file was created
        template_path = template_engine.templates_dir / "test_custom.html"
        assert template_path.exists()
        
        # Check if metadata file was created
        meta_path = template_engine.templates_dir / "test_custom.meta.json"
        assert meta_path.exists()

class TestSmartFormatter:
    """Test SmartFormatter functionality"""
    
    @pytest.fixture
    def smart_formatter(self):
        """Create SmartFormatter instance"""
        temp_dir = tempfile.mkdtemp()
        template_engine = TemplateEngine(temp_dir)
        formatter = SmartFormatter(template_engine)
        yield formatter
        shutil.rmtree(temp_dir)
    
    def test_analyze_content_type(self, smart_formatter):
        """Test content type analysis"""
        # Meeting content
        meeting_segments = [
            TranscriptSegment(0, 30, "Alice", "Let's start the meeting with the agenda"),
            TranscriptSegment(30, 60, "Bob", "We need to discuss action items from last week")
        ]
        
        content_type = smart_formatter.analyze_content_type(meeting_segments)
        assert content_type == "meeting"
        
        # Interview content
        interview_segments = [
            TranscriptSegment(0, 30, "Interviewer", "Tell me about your experience"),
            TranscriptSegment(30, 60, "Candidate", "I have five years of background in this field")
        ]
        
        content_type = smart_formatter.analyze_content_type(interview_segments)
        assert content_type == "interview"
    
    def test_extract_action_items(self, smart_formatter):
        """Test action item extraction"""
        segments = [
            TranscriptSegment(0, 30, "Alice", "Action item: Review the budget proposal by Friday"),
            TranscriptSegment(30, 60, "Bob", "We need to follow up with the client next week"),
            TranscriptSegment(60, 90, "Carol", "I will prepare the presentation for Monday")
        ]
        
        action_items = smart_formatter.extract_action_items(segments)
        assert len(action_items) > 0
        
        # Check if action items contain expected text
        action_texts = [item.text for item in action_items]
        assert any("budget proposal" in text.lower() for text in action_texts)
    
    def test_extract_key_points(self, smart_formatter):
        """Test key point extraction"""
        segments = [
            TranscriptSegment(0, 30, "Alice", "This is a very important point about our strategy"),
            TranscriptSegment(30, 60, "Bob", "The key issue here is resource allocation"),
            TranscriptSegment(60, 90, "Carol", "Remember that we need to focus on customer satisfaction")
        ]
        
        key_points = smart_formatter.extract_key_points(segments)
        assert len(key_points) > 0
        
        # Check if key points contain expected content
        point_texts = [point.text for point in key_points]
        assert any("important" in text.lower() for text in point_texts)
    
    def test_auto_format(self, smart_formatter):
        """Test automatic formatting"""
        metadata = ContentMetadata(
            title="Test Meeting",
            content_type="meeting",
            duration=1800
        )
        
        segments = [
            TranscriptSegment(0, 30, "Alice", "Welcome to our weekly meeting"),
            TranscriptSegment(30, 60, "Bob", "Let's review the action items from last week")
        ]
        
        result = smart_formatter.auto_format(
            transcript_segments=segments,
            metadata=metadata,
            preferred_format="html"
        )
        
        assert result.content is not None
        assert result.format_type == "html"
        assert "Test Meeting" in result.content

class TestTemplateManager:
    """Test TemplateManager functionality"""
    
    @pytest.fixture
    def template_manager(self):
        """Create TemplateManager instance"""
        temp_dir = tempfile.mkdtemp()
        manager = TemplateManager(temp_dir)
        yield manager
        shutil.rmtree(temp_dir)
    
    def test_template_manager_initialization(self, template_manager):
        """Test TemplateManager initialization"""
        assert template_manager.template_engine is not None
        assert template_manager.smart_formatter is not None
    
    def test_get_template_preview(self, template_manager):
        """Test template preview generation"""
        preview = template_manager.get_template_preview("simple_transcript.txt")
        assert preview is not None
        assert len(preview) > 0
        assert "Sample Content Preview" in preview
    
    def test_validate_template(self, template_manager):
        """Test template validation"""
        # Valid template
        valid_template = "<h1>{{ metadata.title }}</h1>"
        result = template_manager.validate_template(valid_template)
        assert result["valid"] is True
        
        # Invalid template
        invalid_template = "<h1>{{ metadata.title }</h1>"  # Missing closing brace
        result = template_manager.validate_template(invalid_template)
        assert result["valid"] is False
    
    def test_get_template_stats(self, template_manager):
        """Test template statistics"""
        stats = template_manager.get_template_stats()
        
        assert "total_templates" in stats
        assert "by_format" in stats
        assert "custom_templates" in stats
        assert "builtin_templates" in stats
        assert stats["total_templates"] > 0

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_sample_content(self):
        """Test sample content creation"""
        sample = create_sample_content()
        
        assert "metadata" in sample
        assert "transcript_segments" in sample
        assert "action_items" in sample
        assert "key_points" in sample
        
        assert isinstance(sample["metadata"], ContentMetadata)
        assert len(sample["transcript_segments"]) > 0
        assert len(sample["action_items"]) > 0
        assert len(sample["key_points"]) > 0
    
    def test_format_time_duration(self):
        """Test time duration formatting"""
        assert format_time_duration(30) == "30 seconds"
        assert format_time_duration(90) == "1 minute"
        assert format_time_duration(150) == "2 minutes"
        assert format_time_duration(3600) == "1 hour"
        assert format_time_duration(3661) == "1 hour 1 minute"
        assert format_time_duration(7320) == "2 hours 2 minutes"
    
    def test_extract_text_statistics(self):
        """Test text statistics extraction"""
        segments = [
            TranscriptSegment(0, 30, "Alice", "Hello everyone, welcome to the meeting"),
            TranscriptSegment(30, 60, "Bob", "Thank you Alice, let's get started"),
            TranscriptSegment(60, 90, "Alice", "First item on the agenda is budget review")
        ]
        
        stats = extract_text_statistics(segments)
        
        assert stats["total_words"] > 0
        assert stats["total_characters"] > 0
        assert stats["total_segments"] == 3
        assert stats["unique_speakers"] == 2
        assert stats["total_duration"] == 90

class TestIntegration:
    """Integration tests for the complete system"""
    
    @pytest.fixture
    def complete_system(self):
        """Set up complete system for integration testing"""
        temp_dir = tempfile.mkdtemp()
        manager = TemplateManager(temp_dir)
        yield manager
        shutil.rmtree(temp_dir)
    
    def test_end_to_end_formatting(self, complete_system):
        """Test complete end-to-end formatting workflow"""
        # Create content
        metadata = ContentMetadata(
            title="Integration Test Meeting",
            content_type="meeting",
            duration=1800,
            speakers=["Alice", "Bob", "Carol"],
            date_created=datetime.now(),
            summary="Test meeting for integration testing"
        )
        
        segments = [
            TranscriptSegment(0, 30, "Alice", "Welcome everyone to our integration test meeting"),
            TranscriptSegment(30, 75, "Bob", "Thanks Alice. We need to review the test results and create action items"),
            TranscriptSegment(75, 120, "Carol", "I agree. The important thing is to ensure all components work together"),
            TranscriptSegment(120, 180, "Alice", "Let's follow up on this next week with a detailed analysis")
        ]
        
        # Auto-format content
        result = complete_system.smart_formatter.auto_format(
            transcript_segments=segments,
            metadata=metadata,
            preferred_format="html"
        )
        
        # Verify result
        assert result is not None
        assert result.content is not None
        assert result.format_type == "html"
        assert "Integration Test Meeting" in result.content
        assert "Alice" in result.content
        assert "Bob" in result.content
        assert "Carol" in result.content
        
        # Verify extracted elements
        assert len(result.content) > 500  # Should be substantial content
    
    def test_multiple_format_generation(self, complete_system):
        """Test generating multiple formats from same content"""
        sample_data = create_sample_content()
        
        formats = ["html", "markdown", "text"]
        results = []
        
        for format_type in formats:
            result = complete_system.smart_formatter.auto_format(
                transcript_segments=sample_data["transcript_segments"],
                metadata=sample_data["metadata"],
                preferred_format=format_type
            )
            results.append(result)
        
        # Verify all formats were generated
        assert len(results) == 3
        assert results[0].format_type == "html"
        assert results[1].format_type == "markdown"
        assert results[2].format_type == "text"
        
        # Verify content differs appropriately
        assert "<html>" in results[0].content or "<h1>" in results[0].content
        assert "#" in results[1].content or "**" in results[1].content
        assert results[2].content.count("\n") > 0  # Text format should have line breaks

if __name__ == "__main__":
    pytest.main([__file__, "-v"])