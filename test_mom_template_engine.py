#!/usr/bin/env python3
"""
Test suite for MOM Template Engine
"""

import pytest
import sys
import os
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mom_template_engine import (
    MOMTemplateEngine,
    MOMConfiguration,
    MOMDocument,
    MOMSection,
    MOMFormat,
    MOMStyle,
    TemplateLoader,
    TemplateValidationLevel,
    create_mom_template_engine,
    generate_mom_from_meeting
)

from meeting_element_identification import (
    MeetingStructure,
    MeetingElement,
    MeetingElementType,
    analyze_meeting_transcript
)

from action_item_extraction_system import (
    ActionItem,
    ActionItemPriority,
    ActionItemStatus,
    ActionItemAssignee,
    ActionItemDeadline,
    DeadlineType,
    extract_action_items_from_meeting
)

class TestMOMConfiguration:
    """Test MOM configuration class"""
    
    def test_default_configuration(self):
        """Test default configuration values"""
        config = MOMConfiguration()
        
        assert config.format == MOMFormat.MARKDOWN
        assert config.style == MOMStyle.CORPORATE
        assert config.include_timestamps == True
        assert config.include_speaker_names == True
        assert config.include_confidence_scores == False
        assert config.group_by_topic == True
        assert config.show_action_item_details == True
        assert config.show_decision_rationale == True
        assert config.include_attendance == True
        assert config.include_summary == True
        assert config.max_content_length is None
        assert isinstance(config.custom_fields, dict)
        assert isinstance(config.template_variables, dict)
    
    def test_custom_configuration(self):
        """Test custom configuration"""
        config = MOMConfiguration(
            format=MOMFormat.HTML,
            style=MOMStyle.AGILE,
            include_timestamps=False,
            max_content_length=5000,
            custom_fields={'meeting_type': 'Sprint Planning'},
            template_variables={'company_name': 'Test Corp'}
        )
        
        assert config.format == MOMFormat.HTML
        assert config.style == MOMStyle.AGILE
        assert config.include_timestamps == False
        assert config.max_content_length == 5000
        assert config.custom_fields['meeting_type'] == 'Sprint Planning'
        assert config.template_variables['company_name'] == 'Test Corp'

class TestMOMSection:
    """Test MOM section class"""
    
    def test_section_creation(self):
        """Test section creation and basic operations"""
        section = MOMSection(title="Test Section", order=1)
        
        assert section.title == "Test Section"
        assert section.order == 1
        assert len(section.content) == 0
        assert len(section.subsections) == 0
        assert isinstance(section.metadata, dict)
    
    def test_add_content(self):
        """Test adding content to section"""
        section = MOMSection(title="Test Section")
        
        section.add_content("First item")
        section.add_content("Second item")
        
        assert len(section.content) == 2
        assert section.content[0] == "First item"
        assert section.content[1] == "Second item"
    
    def test_add_subsection(self):
        """Test adding subsections"""
        main_section = MOMSection(title="Main Section")
        sub1 = MOMSection(title="Sub 1", order=2)
        sub2 = MOMSection(title="Sub 2", order=1)
        
        main_section.add_subsection(sub1)
        main_section.add_subsection(sub2)
        
        assert len(main_section.subsections) == 2
        # Should be sorted by order
        assert main_section.subsections[0].title == "Sub 2"  # order=1
        assert main_section.subsections[1].title == "Sub 1"  # order=2

class TestMOMDocument:
    """Test MOM document class"""
    
    def test_document_creation(self):
        """Test document creation"""
        doc = MOMDocument(
            title="Test Meeting",
            meeting_id="test_001",
            date=datetime(2024, 1, 15, 14, 0),
            attendees=["Alice", "Bob", "Charlie"]
        )
        
        assert doc.title == "Test Meeting"
        assert doc.meeting_id == "test_001"
        assert doc.date == datetime(2024, 1, 15, 14, 0)
        assert len(doc.attendees) == 3
        assert len(doc.sections) == 0
        assert isinstance(doc.generated_at, datetime)
    
    def test_add_section(self):
        """Test adding sections to document"""
        doc = MOMDocument(title="Test", meeting_id="test")
        
        section1 = MOMSection(title="Section 1", order=2)
        section2 = MOMSection(title="Section 2", order=1)
        
        doc.add_section(section1)
        doc.add_section(section2)
        
        assert len(doc.sections) == 2
        # Should be sorted by order
        assert doc.sections[0].title == "Section 2"  # order=1
        assert doc.sections[1].title == "Section 1"  # order=2
    
    def test_get_section(self):
        """Test getting section by title"""
        doc = MOMDocument(title="Test", meeting_id="test")
        
        section = MOMSection(title="Test Section")
        doc.add_section(section)
        
        found_section = doc.get_section("Test Section")
        assert found_section is not None
        assert found_section.title == "Test Section"
        
        not_found = doc.get_section("Non-existent Section")
        assert not_found is None

class TestTemplateLoader:
    """Test template loader functionality"""
    
    def test_builtin_templates_loaded(self):
        """Test that builtin templates are loaded"""
        loader = TemplateLoader()
        
        expected_templates = [
            'corporate_markdown',
            'corporate_html',
            'agile_markdown',
            'executive_markdown',
            'technical_markdown',
            'simple_plain_text',
            'detailed_markdown'
        ]
        
        for template_name in expected_templates:
            assert template_name in loader.builtin_templates
            assert len(loader.builtin_templates[template_name]) > 0
    
    def test_get_builtin_template_source(self):
        """Test getting builtin template source"""
        loader = TemplateLoader()
        
        # Mock environment
        env = MagicMock()
        
        source, name, uptodate = loader.get_source(env, 'corporate_markdown')
        
        assert isinstance(source, str)
        assert len(source) > 0
        assert name == 'corporate_markdown'
        assert uptodate() == True
    
    def test_template_not_found(self):
        """Test handling of non-existent template"""
        loader = TemplateLoader()
        env = MagicMock()
        
        with pytest.raises(Exception):  # Should raise TemplateError
            loader.get_source(env, 'non_existent_template')

class TestMOMTemplateEngine:
    """Test the main MOM template engine"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = MOMTemplateEngine()
        
        # Create sample meeting data
        self.meeting = MeetingStructure("test_meeting")
        self.meeting.title = "Test Meeting"
        self.meeting.date = datetime(2024, 1, 15, 14, 0)
        self.meeting.duration = 60.0
        self.meeting.attendees = ["Alice", "Bob", "Charlie"]
        
        # Add meeting elements
        agenda_item = MeetingElement(
            element_type=MeetingElementType.AGENDA_ITEM,
            content="Discuss project timeline",
            speaker="Alice",
            confidence=0.8,
            start_time=5.0
        )
        
        decision = MeetingElement(
            element_type=MeetingElementType.DECISION,
            content="Approved budget increase",
            speaker="Bob",
            confidence=0.9,
            start_time=15.0
        )
        
        discussion = MeetingElement(
            element_type=MeetingElementType.DISCUSSION_POINT,
            content="Team capacity concerns",
            speaker="Charlie",
            confidence=0.7,
            start_time=25.0
        )
        
        self.meeting.add_element(agenda_item)
        self.meeting.add_element(decision)
        self.meeting.add_element(discussion)
        
        # Create sample action items
        self.action_items = [
            ActionItem(
                id="action_1",
                content="Update project documentation",
                assignees=[ActionItemAssignee(name="Alice", confidence=0.8)],
                priority=ActionItemPriority.HIGH,
                confidence=0.8,
                tags=['process:document']
            ),
            ActionItem(
                id="action_2",
                content="Review budget proposal",
                assignees=[ActionItemAssignee(name="Bob", confidence=0.9)],
                priority=ActionItemPriority.MEDIUM,
                confidence=0.7,
                deadline=ActionItemDeadline(
                    deadline_type=DeadlineType.RELATIVE_TIME,
                    original_text="by Friday",
                    confidence=0.8
                )
            )
        ]
    
    def test_generate_mom_basic(self):
        """Test basic MOM generation"""
        config = MOMConfiguration()
        mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
        
        assert isinstance(mom_doc, MOMDocument)
        assert mom_doc.title == "Test Meeting"
        assert mom_doc.meeting_id == "test_meeting"
        assert mom_doc.date == self.meeting.date
        assert len(mom_doc.attendees) == 3
        assert len(mom_doc.sections) > 0
        
        # Check that sections were created
        section_titles = [s.title for s in mom_doc.sections]
        assert "Summary" in section_titles
        assert "Agenda Items" in section_titles
        assert "Decisions Made" in section_titles
        assert "Action Items" in section_titles
    
    def test_generate_mom_without_summary(self):
        """Test MOM generation without summary"""
        config = MOMConfiguration(include_summary=False)
        mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
        
        section_titles = [s.title for s in mom_doc.sections]
        assert "Summary" not in section_titles
    
    def test_render_mom_markdown(self):
        """Test rendering MOM to markdown"""
        config = MOMConfiguration(style=MOMStyle.CORPORATE, format=MOMFormat.MARKDOWN)
        mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
        
        rendered = self.engine.render_mom(mom_doc, config)
        
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "# Meeting Minutes: Test Meeting" in rendered
        assert "test_meeting" in rendered
        assert "Alice" in rendered
        assert "Bob" in rendered
        assert "Charlie" in rendered
    
    def test_render_mom_html(self):
        """Test rendering MOM to HTML"""
        config = MOMConfiguration(style=MOMStyle.CORPORATE, format=MOMFormat.HTML)
        mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
        
        rendered = self.engine.render_mom(mom_doc, config)
        
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "<!DOCTYPE html>" in rendered
        assert "<html" in rendered
        assert "<title>Meeting Minutes: Test Meeting</title>" in rendered
        assert "</html>" in rendered
    
    def test_render_different_styles(self):
        """Test rendering with different styles"""
        styles = [MOMStyle.CORPORATE, MOMStyle.AGILE, MOMStyle.EXECUTIVE, MOMStyle.TECHNICAL]
        
        for style in styles:
            config = MOMConfiguration(style=style, format=MOMFormat.MARKDOWN)
            mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
            
            rendered = self.engine.render_mom(mom_doc, config)
            
            assert isinstance(rendered, str)
            assert len(rendered) > 0
            # Each style should have different content/formatting
            assert "Test Meeting" in rendered or "test_meeting" in rendered
    
    def test_custom_filters(self):
        """Test custom Jinja2 filters"""
        # Test format_duration filter
        assert self.engine.jinja_env.filters['format_duration'](90) == "1h 30m"
        assert self.engine.jinja_env.filters['format_duration'](45) == "45m"
        assert self.engine.jinja_env.filters['format_duration'](None) == "N/A"
        
        # Test format_priority filter
        assert "HIGH" in self.engine.jinja_env.filters['format_priority']("high")
        assert "🟠" in self.engine.jinja_env.filters['format_priority']("high")
        
        # Test format_confidence filter
        assert "🟢" in self.engine.jinja_env.filters['format_confidence'](0.95)
        assert "🟡" in self.engine.jinja_env.filters['format_confidence'](0.75)
        assert "🔴" in self.engine.jinja_env.filters['format_confidence'](0.45)
        
        # Test truncate_smart filter
        long_text = "This is a very long text that should be truncated at word boundaries"
        truncated = self.engine.jinja_env.filters['truncate_smart'](long_text, 30)
        assert len(truncated) <= 34  # 30 + "..."
        assert truncated.endswith("...")
    
    def test_template_validation(self):
        """Test template validation"""
        # Valid template
        valid_template = "# {{ title }}\n\nDate: {{ date }}\nAttendees: {{ attendees | join(', ') }}"
        result = self.engine.validate_template(valid_template)
        
        assert result['valid'] == True
        assert len(result['errors']) == 0
        
        # Invalid template (unclosed variable)
        invalid_template = "# {{ title }\n\nDate: {{ date }}"
        result = self.engine.validate_template(invalid_template)
        
        assert result['valid'] == False
        assert len(result['errors']) > 0
    
    def test_list_available_templates(self):
        """Test listing available templates"""
        templates = self.engine.list_available_templates()
        
        assert isinstance(templates, dict)
        assert len(templates) > 0
        
        # Check that builtin templates are listed
        assert 'corporate_markdown' in templates
        assert 'agile_markdown' in templates
        
        # Check template info structure
        template_info = templates['corporate_markdown']
        assert 'name' in template_info
        assert 'style' in template_info
        assert 'format' in template_info
        assert 'builtin' in template_info
        assert 'description' in template_info
        assert template_info['builtin'] == True
    
    def test_fallback_rendering(self):
        """Test fallback rendering when main template fails"""
        config = MOMConfiguration()
        mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
        
        # Force fallback by using non-existent template
        with patch.object(self.engine, '_get_template') as mock_get_template:
            mock_get_template.side_effect = Exception("Template not found")
            
            rendered = self.engine.render_mom(mom_doc, config)
            
            assert isinstance(rendered, str)
            assert len(rendered) > 0
            assert "Test Meeting" in rendered
    
    def test_content_length_limit(self):
        """Test content length limiting"""
        config = MOMConfiguration(max_content_length=100)
        mom_doc = self.engine.generate_mom(self.meeting, self.action_items, config)
        
        rendered = self.engine.render_mom(mom_doc, config)
        
        # Should be truncated
        assert len(rendered) <= 150  # Some buffer for truncation message
        assert "[Content truncated due to length limit]" in rendered
    
    def test_group_action_items_by_topic(self):
        """Test grouping action items by topic"""
        # Create action items with different tags
        action_items = [
            ActionItem(
                id="tech_1",
                content="Fix database bug",
                tags=['tech:database'],
                confidence=0.8
            ),
            ActionItem(
                id="business_1",
                content="Update marketing strategy",
                tags=['business:marketing'],
                confidence=0.7
            ),
            ActionItem(
                id="comm_1",
                content="Send project update email",
                tags=['communication:email'],
                confidence=0.9
            )
        ]
        
        grouped = self.engine._group_action_items_by_topic(action_items)
        
        assert 'Technical Tasks' in grouped
        assert 'Business Tasks' in grouped
        assert 'Communication Tasks' in grouped
        
        assert len(grouped['Technical Tasks']) == 1
        assert len(grouped['Business Tasks']) == 1
        assert len(grouped['Communication Tasks']) == 1
    
    def test_generate_summary(self):
        """Test summary generation"""
        summary = self.engine._generate_summary(self.meeting, self.action_items)
        
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "3 participants" in summary
        assert "1 key decisions" in summary
        assert "2 action items" in summary
        assert "1 agenda items" in summary

class TestUtilityFunctions:
    """Test utility functions"""
    
    def test_create_mom_template_engine(self):
        """Test engine creation utility"""
        engine = create_mom_template_engine()
        
        assert isinstance(engine, MOMTemplateEngine)
        assert engine.template_loader is not None
        assert engine.jinja_env is not None
    
    def test_generate_mom_from_meeting(self):
        """Test utility function for generating MOM"""
        # Create sample data
        meeting = MeetingStructure("test_meeting")
        meeting.title = "Test Meeting"
        meeting.attendees = ["Alice", "Bob"]
        
        action_items = [
            ActionItem(
                id="test_action",
                content="Test action item",
                confidence=0.8
            )
        ]
        
        config = MOMConfiguration(style=MOMStyle.SIMPLE, format=MOMFormat.PLAIN_TEXT)
        
        rendered = generate_mom_from_meeting(meeting, action_items, config)
        
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "Test Meeting" in rendered

class TestIntegrationWithMeetingData:
    """Test integration with real meeting data"""
    
    def test_full_pipeline_integration(self):
        """Test full pipeline from transcript to MOM"""
        transcript = """
[14:00] Manager: Welcome to our project review meeting.
[14:02] Manager: Let's start with agenda item 1 - project status update.
[14:05] Developer: The frontend is 80% complete. We're on track.
[14:07] Manager: Excellent. We've decided to proceed with the current timeline.
[14:10] Manager: Action item for Designer - create mockups by Friday.
[14:11] Designer: I'll have the mockups ready by Friday afternoon.
[14:13] Manager: Any other business before we wrap up?
[14:15] Manager: Great. Meeting adjourned.
        """
        
        # Analyze meeting
        meeting = analyze_meeting_transcript(transcript, {
            'meeting_id': 'project_review_2024',
            'title': 'Project Review Meeting',
            'date': datetime(2024, 1, 15, 14, 0)
        })
        
        # Extract action items
        action_items = extract_action_items_from_meeting(meeting)
        
        # Generate MOM
        config = MOMConfiguration(style=MOMStyle.CORPORATE, format=MOMFormat.MARKDOWN)
        rendered = generate_mom_from_meeting(meeting, action_items, config)
        
        # Verify results
        assert isinstance(rendered, str)
        assert len(rendered) > 0
        assert "Project Review Meeting" in rendered
        assert "Manager" in rendered or "Designer" in rendered or "Developer" in rendered
        assert "mockups" in rendered.lower() or "frontend" in rendered.lower()
    
    def test_different_meeting_types(self):
        """Test MOM generation for different meeting types"""
        meeting_types = [
            ("Sprint Planning", MOMStyle.AGILE),
            ("Board Meeting", MOMStyle.EXECUTIVE),
            ("Technical Review", MOMStyle.TECHNICAL),
            ("Team Standup", MOMStyle.SIMPLE)
        ]
        
        for meeting_title, style in meeting_types:
            # Create basic meeting structure
            meeting = MeetingStructure("test_meeting")
            meeting.title = meeting_title
            meeting.attendees = ["Person A", "Person B"]
            
            # Add a basic element
            element = MeetingElement(
                element_type=MeetingElementType.DISCUSSION_POINT,
                content=f"Discussed {meeting_title.lower()} topics",
                confidence=0.8
            )
            meeting.add_element(element)
            
            # Create action item
            action_items = [
                ActionItem(
                    id="test_action",
                    content=f"Follow up on {meeting_title.lower()}",
                    confidence=0.7
                )
            ]
            
            # Generate MOM
            config = MOMConfiguration(style=style, format=MOMFormat.MARKDOWN)
            rendered = generate_mom_from_meeting(meeting, action_items, config)
            
            assert isinstance(rendered, str)
            assert len(rendered) > 0
            assert meeting_title in rendered

class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.engine = MOMTemplateEngine()
    
    def test_empty_meeting(self):
        """Test handling of empty meeting"""
        meeting = MeetingStructure("empty_meeting")
        action_items = []
        
        config = MOMConfiguration()
        mom_doc = self.engine.generate_mom(meeting, action_items, config)
        
        assert isinstance(mom_doc, MOMDocument)
        assert mom_doc.meeting_id == "empty_meeting"
        
        rendered = self.engine.render_mom(mom_doc, config)
        assert isinstance(rendered, str)
    
    def test_meeting_without_date(self):
        """Test meeting without date"""
        meeting = MeetingStructure("no_date_meeting")
        meeting.title = "Meeting Without Date"
        meeting.date = None
        
        config = MOMConfiguration()
        mom_doc = self.engine.generate_mom(meeting, [], config)
        rendered = self.engine.render_mom(mom_doc, config)
        
        assert "Not specified" in rendered or "TBD" in rendered
    
    def test_action_items_without_assignees(self):
        """Test action items without assignees"""
        meeting = MeetingStructure("test_meeting")
        meeting.title = "Test Meeting"
        
        action_items = [
            ActionItem(
                id="unassigned_action",
                content="Unassigned task",
                assignees=[],  # No assignees
                confidence=0.8
            )
        ]
        
        config = MOMConfiguration()
        mom_doc = self.engine.generate_mom(meeting, action_items, config)
        rendered = self.engine.render_mom(mom_doc, config)
        
        assert "Unassigned" in rendered or "unassigned" in rendered
    
    def test_very_long_content(self):
        """Test handling of very long content"""
        meeting = MeetingStructure("long_meeting")
        meeting.title = "Very Long Meeting"
        
        # Create many elements
        for i in range(50):
            element = MeetingElement(
                element_type=MeetingElementType.DISCUSSION_POINT,
                content=f"This is discussion point number {i} with lots of detailed content that goes on and on",
                confidence=0.8
            )
            meeting.add_element(element)
        
        config = MOMConfiguration(max_content_length=1000)
        mom_doc = self.engine.generate_mom(meeting, [], config)
        rendered = self.engine.render_mom(mom_doc, config)
        
        assert len(rendered) <= 1100  # Some buffer
        assert "[Content truncated due to length limit]" in rendered
    
    def test_invalid_template_style_format_combination(self):
        """Test handling of invalid template combinations"""
        meeting = MeetingStructure("test_meeting")
        meeting.title = "Test Meeting"
        
        # This combination might not exist
        config = MOMConfiguration(style=MOMStyle.EXECUTIVE, format=MOMFormat.DOCX)
        mom_doc = self.engine.generate_mom(meeting, [], config)
        
        # Should fall back gracefully
        rendered = self.engine.render_mom(mom_doc, config)
        assert isinstance(rendered, str)
        assert len(rendered) > 0

def test_comprehensive_mom_generation():
    """Comprehensive test of MOM generation with realistic data"""
    transcript = """
[09:00] Scrum Master: Good morning team. Welcome to our sprint retrospective.
[09:02] Scrum Master: Let's start with what went well this sprint.
[09:05] Developer 1: The new CI/CD pipeline worked great. Deployments were smooth.
[09:07] Developer 2: I agree. The automated testing caught several bugs early.
[09:10] Scrum Master: Excellent. Now, what could we improve?
[09:12] QA Lead: We need better test coverage for edge cases.
[09:15] Developer 1: The code review process took longer than expected.
[09:18] Scrum Master: Good points. Let's discuss action items.
[09:20] Scrum Master: Action item 1 - QA Lead will create test coverage report by Friday.
[09:22] QA Lead: I'll have the coverage analysis ready by Friday morning.
[09:25] Scrum Master: Action item 2 - Developer 2, can you research faster code review tools?
[09:27] Developer 2: Sure, I'll evaluate review tools and present options next week.
[09:30] Scrum Master: We've decided to allocate 20% more time for code reviews next sprint.
[09:32] Scrum Master: Any other concerns before we wrap up?
[09:35] Developer 1: Should we schedule a technical debt planning session?
[09:37] Scrum Master: Good idea. I'll organize that for next month.
[09:40] Scrum Master: Great retrospective everyone. See you at the next sprint planning.
    """
    
    context = {
        'meeting_id': 'sprint_retro_2024_01_30',
        'title': 'Sprint Retrospective',
        'date': datetime(2024, 1, 30, 9, 0),
        'speaker_roles': {
            'Scrum Master': 'Scrum Master',
            'Developer 1': 'Senior Developer',
            'Developer 2': 'Junior Developer',
            'QA Lead': 'QA Lead'
        }
    }
    
    # Analyze meeting and extract action items
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    # Test different MOM styles
    styles_to_test = [
        (MOMStyle.AGILE, "agile retrospective"),
        (MOMStyle.CORPORATE, "professional format"),
        (MOMStyle.TECHNICAL, "technical details"),
        (MOMStyle.DETAILED, "comprehensive coverage")
    ]
    
    for style, description in styles_to_test:
        config = MOMConfiguration(
            style=style,
            format=MOMFormat.MARKDOWN,
            include_timestamps=True,
            include_speaker_names=True,
            show_action_item_details=True,
            custom_fields={
                'meeting_type': 'Sprint Retrospective',
                'sprint_number': 'Sprint 15'
            }
        )
        
        rendered = generate_mom_from_meeting(meeting, action_items, config)
        
        # Comprehensive validation
        assert isinstance(rendered, str)
        assert len(rendered) > 500, f"MOM should be substantial for {style.value}"
        
        # Check for key content
        assert "Sprint Retrospective" in rendered
        assert "QA Lead" in rendered or "Developer" in rendered or "Scrum Master" in rendered
        
        # Check for action items
        assert "test coverage" in rendered.lower() or "coverage" in rendered.lower()
        assert "review" in rendered.lower()
        
        # Check for decisions
        assert "20%" in rendered or "code review" in rendered.lower()
        
        # Style-specific checks
        if style == MOMStyle.AGILE:
            # Agile style should have emojis and casual language
            assert "🚀" in rendered or "🎯" in rendered or "📋" in rendered
        elif style == MOMStyle.CORPORATE:
            # Corporate style should be formal
            assert "Meeting Minutes" in rendered or "Executive Summary" in rendered
        elif style == MOMStyle.TECHNICAL:
            # Technical style should have code-like formatting
            assert "`" in rendered or "```" in rendered
        elif style == MOMStyle.DETAILED:
            # Detailed style should have comprehensive information
            assert "Meeting Information" in rendered
            assert "Statistics" in rendered or "Document Information" in rendered
        
        print(f"✅ {description.title()} MOM generated successfully ({len(rendered)} characters)")
    
    print(f"✅ Comprehensive MOM generation test completed")
    print(f"   Meeting analyzed: {len(meeting.elements)} elements")
    print(f"   Action items extracted: {len(action_items)}")
    print(f"   Styles tested: {len(styles_to_test)}")

if __name__ == "__main__":
    # Run the comprehensive test
    test_comprehensive_mom_generation()
    
    # Run pytest for all other tests
    pytest.main([__file__, "-v"])