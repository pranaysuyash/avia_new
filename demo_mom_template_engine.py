#!/usr/bin/env python3
"""
Demo script for MOM Template Engine
Showcases professional meeting minutes generation with multiple styles and formats
"""

import sys
import os
from datetime import datetime
import json

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mom_template_engine import (
    MOMTemplateEngine,
    MOMConfiguration,
    MOMFormat,
    MOMStyle,
    create_mom_template_engine,
    generate_mom_from_meeting
)

from meeting_element_identification import analyze_meeting_transcript
from action_item_extraction_system import extract_action_items_from_meeting

def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def demo_corporate_style():
    """Demo corporate style MOM generation"""
    print_separator("DEMO 1: Corporate Style Meeting Minutes", "=")
    
    transcript = """
[14:00] CEO: Welcome to our quarterly board meeting.
[14:02] CEO: Let's begin with the financial review for Q4.
[14:05] CFO: Revenue increased by 15% compared to last quarter.
[14:07] CFO: Operating expenses were within budget at 92% utilization.
[14:10] CEO: Excellent results. The board approves the Q4 financial report.
[14:12] CEO: Moving to agenda item 2 - strategic initiatives for next year.
[14:15] VP Strategy: We propose expanding into the European market.
[14:17] VP Strategy: Initial investment required is $2.5 million.
[14:20] Board Member 1: What's the projected ROI for this expansion?
[14:22] VP Strategy: We estimate 25% ROI within 18 months.
[14:25] CEO: The board approves the European expansion initiative.
[14:27] CEO: Action item for VP Strategy - prepare detailed implementation plan by March 1st.
[14:29] VP Strategy: I'll have the comprehensive plan ready by March 1st.
[14:32] CEO: Action item for CFO - secure funding for the expansion by February 15th.
[14:34] CFO: I'll coordinate with our banking partners for the funding.
[14:36] CEO: Any other business before we adjourn?
[14:38] Board Member 2: We should schedule a follow-up meeting in 6 weeks.
[14:40] CEO: Agreed. Secretary will send calendar invites for the follow-up.
[14:42] CEO: Thank you all. Meeting adjourned.
    """
    
    context = {
        'meeting_id': 'board_meeting_q4_2024',
        'title': 'Quarterly Board Meeting - Q4 2024',
        'date': datetime(2024, 12, 15, 14, 0),
        'speaker_roles': {
            'CEO': 'Chief Executive Officer',
            'CFO': 'Chief Financial Officer',
            'VP Strategy': 'Vice President of Strategy',
            'Board Member 1': 'Board Member',
            'Board Member 2': 'Board Member'
        }
    }
    
    print("📊 Analyzing corporate board meeting...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    config = MOMConfiguration(
        style=MOMStyle.CORPORATE,
        format=MOMFormat.MARKDOWN,
        include_timestamps=True,
        include_speaker_names=True,
        show_decision_rationale=True,
        custom_fields={
            'meeting_type': 'Board Meeting',
            'location': 'Corporate Headquarters'
        }
    )
    
    print(f"\n📋 Generating Corporate Style MOM...")
    rendered = generate_mom_from_meeting(meeting, action_items, config)
    
    print(f"\n📄 Corporate Meeting Minutes:")
    print("-" * 60)
    print(rendered)

def demo_agile_style():
    """Demo agile/scrum style MOM generation"""
    print_separator("DEMO 2: Agile/Scrum Style Meeting Minutes", "=")
    
    transcript = """
[09:00] Scrum Master: Good morning team! Welcome to Sprint 23 planning.
[09:02] Scrum Master: Let's review our sprint goal and backlog items.
[09:05] Product Owner: Our main goal is to complete the user authentication feature.
[09:07] Product Owner: We have 8 story points planned for this sprint.
[09:10] Developer 1: I can take the login API implementation - that's 3 points.
[09:12] Developer 2: I'll handle the frontend login form - 2 points.
[09:15] QA Engineer: I'll create test cases for the auth flow - 2 points.
[09:17] Scrum Master: Perfect! That leaves the password reset feature.
[09:20] Developer 1: I can also take that one - it's only 1 point.
[09:22] Scrum Master: Great! We've committed to all 8 story points.
[09:25] Scrum Master: Any blockers or dependencies we should discuss?
[09:27] Developer 2: I'll need the API endpoints ready before I start the frontend.
[09:29] Developer 1: No problem, I'll have the API done by Wednesday.
[09:32] QA Engineer: I'll need access to the staging environment for testing.
[09:34] DevOps: I'll set up the staging auth service by tomorrow.
[09:36] Scrum Master: Awesome! Any other concerns?
[09:38] Product Owner: Let's make sure we demo this to stakeholders on Friday.
[09:40] Scrum Master: Noted! Demo scheduled for Friday at 3 PM.
[09:42] Scrum Master: Sprint 23 is officially started! Let's crush it! 🚀
    """
    
    context = {
        'meeting_id': 'sprint_23_planning',
        'title': 'Sprint 23 Planning',
        'date': datetime(2024, 2, 5, 9, 0),
        'speaker_roles': {
            'Scrum Master': 'Scrum Master',
            'Product Owner': 'Product Owner',
            'Developer 1': 'Senior Developer',
            'Developer 2': 'Frontend Developer',
            'QA Engineer': 'QA Engineer',
            'DevOps': 'DevOps Engineer'
        }
    }
    
    print("🏃‍♂️ Analyzing agile sprint planning meeting...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    config = MOMConfiguration(
        style=MOMStyle.AGILE,
        format=MOMFormat.MARKDOWN,
        include_timestamps=False,  # Agile style focuses less on exact timing
        group_by_topic=True,
        custom_fields={
            'sprint_number': 'Sprint 23',
            'story_points': '8 points committed'
        }
    )
    
    print(f"\n🎯 Generating Agile Style MOM...")
    rendered = generate_mom_from_meeting(meeting, action_items, config)
    
    print(f"\n📋 Agile Sprint Planning Minutes:")
    print("-" * 60)
    print(rendered)

def demo_executive_style():
    """Demo executive summary style MOM generation"""
    print_separator("DEMO 3: Executive Summary Style", "=")
    
    transcript = """
[10:00] Chairman: Welcome to the executive leadership meeting.
[10:02] Chairman: Today we're focusing on strategic decisions for Q1.
[10:05] CEO: Our market position has strengthened significantly.
[10:07] CEO: We're seeing 30% growth in our core business segments.
[10:10] CMO: Brand awareness is up 45% following our recent campaign.
[10:12] CMO: Customer acquisition costs have decreased by 20%.
[10:15] Chairman: Outstanding results. We approve the marketing strategy continuation.
[10:18] CTO: Our technology infrastructure is ready for scale.
[10:20] CTO: We can handle 10x current traffic with our new architecture.
[10:23] CEO: Perfect timing. We're expecting significant growth this quarter.
[10:25] Chairman: The board approves increased technology investment.
[10:28] CFO: We have $50M available for strategic initiatives.
[10:30] CFO: Recommend allocating $30M to market expansion, $20M to technology.
[10:33] Chairman: Approved. CFO will execute the budget allocation immediately.
[10:35] CEO: We should also consider strategic partnerships.
[10:37] CEO: I'll explore opportunities with industry leaders.
[10:40] Chairman: Excellent. This positions us well for market leadership.
[10:42] Chairman: Next executive meeting in 4 weeks to review progress.
    """
    
    context = {
        'meeting_id': 'exec_leadership_q1_2024',
        'title': 'Executive Leadership Meeting - Q1 Strategy',
        'date': datetime(2024, 1, 8, 10, 0),
        'speaker_roles': {
            'Chairman': 'Board Chairman',
            'CEO': 'Chief Executive Officer',
            'CMO': 'Chief Marketing Officer',
            'CTO': 'Chief Technology Officer',
            'CFO': 'Chief Financial Officer'
        }
    }
    
    print("👔 Analyzing executive leadership meeting...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    config = MOMConfiguration(
        style=MOMStyle.EXECUTIVE,
        format=MOMFormat.MARKDOWN,
        include_summary=True,
        show_decision_rationale=True,
        custom_fields={
            'confidentiality': 'Executive Level',
            'distribution': 'C-Suite Only'
        }
    )
    
    print(f"\n📈 Generating Executive Summary...")
    rendered = generate_mom_from_meeting(meeting, action_items, config)
    
    print(f"\n📊 Executive Meeting Summary:")
    print("-" * 60)
    print(rendered)

def demo_technical_style():
    """Demo technical meeting style MOM generation"""
    print_separator("DEMO 4: Technical Meeting Style", "=")
    
    transcript = """
[15:00] Tech Lead: Welcome to our architecture review meeting.
[15:02] Tech Lead: Today we're reviewing the microservices migration plan.
[15:05] Senior Dev: The user service migration is complete and tested.
[15:07] Senior Dev: Performance improved by 40% with the new architecture.
[15:10] DevOps: Container orchestration is working well with Kubernetes.
[15:12] DevOps: We have auto-scaling configured for peak loads.
[15:15] Tech Lead: Excellent. We approve the user service deployment to production.
[15:18] Database Admin: The data migration strategy needs refinement.
[15:20] Database Admin: We need zero-downtime migration for the payment service.
[15:23] Senior Dev: I can implement blue-green deployment for that.
[15:25] Tech Lead: Good solution. Implement blue-green for payment service migration.
[15:28] Security Engineer: We need to review API security before production.
[15:30] Security Engineer: OAuth 2.0 implementation requires penetration testing.
[15:33] Tech Lead: Critical point. Security review is mandatory before deployment.
[15:35] QA Lead: Automated testing coverage is at 85% for the new services.
[15:37] QA Lead: We need integration tests for the payment flow.
[15:40] Senior Dev: I'll write the integration tests by end of week.
[15:42] Tech Lead: Perfect. All services must have 90%+ test coverage.
[15:45] Tech Lead: Next architecture review in 2 weeks to assess progress.
    """
    
    context = {
        'meeting_id': 'arch_review_microservices_2024',
        'title': 'Architecture Review - Microservices Migration',
        'date': datetime(2024, 2, 12, 15, 0),
        'speaker_roles': {
            'Tech Lead': 'Technical Lead',
            'Senior Dev': 'Senior Developer',
            'DevOps': 'DevOps Engineer',
            'Database Admin': 'Database Administrator',
            'Security Engineer': 'Security Engineer',
            'QA Lead': 'QA Lead'
        }
    }
    
    print("🔧 Analyzing technical architecture meeting...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    config = MOMConfiguration(
        style=MOMStyle.TECHNICAL,
        format=MOMFormat.MARKDOWN,
        include_timestamps=True,
        show_action_item_details=True,
        custom_fields={
            'project': 'Microservices Migration',
            'architecture': 'Kubernetes + Docker'
        }
    )
    
    print(f"\n⚙️ Generating Technical Meeting Documentation...")
    rendered = generate_mom_from_meeting(meeting, action_items, config)
    
    print(f"\n🔧 Technical Meeting Minutes:")
    print("-" * 60)
    print(rendered)

def demo_html_format():
    """Demo HTML format generation"""
    print_separator("DEMO 5: HTML Format Generation", "=")
    
    transcript = """
[11:00] Project Manager: Welcome to our project kickoff meeting.
[11:02] Project Manager: Let's introduce our team and discuss project goals.
[11:05] Designer: I'm Sarah, the UX/UI designer for this project.
[11:07] Developer: I'm Mike, the lead developer. Excited to work on this!
[11:10] QA: I'm Lisa, QA engineer. I'll ensure quality throughout.
[11:12] Project Manager: Great team! Our goal is to launch the new app in 3 months.
[11:15] Project Manager: We've decided to use React Native for cross-platform development.
[11:18] Designer: I'll create wireframes and prototypes by next Friday.
[11:20] Developer: I'll set up the development environment by Wednesday.
[11:22] QA: I'll prepare the testing strategy document by Thursday.
[11:25] Project Manager: Perfect! We have a solid plan to move forward.
[11:27] Project Manager: Weekly check-ins every Monday at 11 AM.
[11:30] Project Manager: Any questions before we wrap up?
[11:32] Project Manager: Excellent. Let's build something amazing!
    """
    
    context = {
        'meeting_id': 'project_kickoff_mobile_app',
        'title': 'Mobile App Project Kickoff',
        'date': datetime(2024, 3, 1, 11, 0),
        'speaker_roles': {
            'Project Manager': 'Project Manager',
            'Designer': 'UX/UI Designer',
            'Developer': 'Lead Developer',
            'QA': 'QA Engineer'
        }
    }
    
    print("📱 Analyzing project kickoff meeting...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    config = MOMConfiguration(
        style=MOMStyle.CORPORATE,
        format=MOMFormat.HTML,
        include_timestamps=True,
        include_speaker_names=True,
        show_action_item_details=True,
        custom_fields={
            'project_name': 'Mobile App Development',
            'timeline': '3 months'
        }
    )
    
    print(f"\n🌐 Generating HTML Format MOM...")
    rendered = generate_mom_from_meeting(meeting, action_items, config)
    
    print(f"\n📄 HTML Meeting Minutes:")
    print("-" * 60)
    print(rendered[:1000] + "..." if len(rendered) > 1000 else rendered)
    print("-" * 60)
    print(f"Full HTML document generated ({len(rendered)} characters)")

def demo_template_customization():
    """Demo template customization and validation"""
    print_separator("DEMO 6: Template Customization & Validation", "=")
    
    print("🛠️ Demonstrating template engine capabilities...")
    
    engine = create_mom_template_engine()
    
    # List available templates
    print(f"\n📋 Available Templates:")
    templates = engine.list_available_templates()
    
    for template_name, info in templates.items():
        style_icon = {
            'corporate': '🏢',
            'agile': '🏃‍♂️',
            'executive': '👔',
            'technical': '🔧',
            'simple': '📝'
        }.get(info['style'], '📄')
        
        format_icon = {
            'markdown': '📝',
            'html': '🌐',
            'plain_text': '📄'
        }.get(info['format'], '📄')
        
        builtin_status = "✅ Built-in" if info['builtin'] else "🔧 Custom"
        print(f"  {style_icon} {format_icon} {template_name} - {builtin_status}")
        print(f"    {info['description']}")
    
    # Test template validation
    print(f"\n🔍 Template Validation Examples:")
    
    # Valid template
    valid_template = """
# Meeting: {{ title }}
Date: {{ date.strftime('%Y-%m-%d') if date else 'TBD' }}
Attendees: {{ attendees | join(', ') }}

{% if decisions_section %}
## Decisions
{% for decision in decisions_section.content %}
- {{ decision }}
{% endfor %}
{% endif %}
    """
    
    validation_result = engine.validate_template(valid_template)
    print(f"✅ Valid template: {validation_result['valid']}")
    if validation_result['warnings']:
        print(f"   Warnings: {len(validation_result['warnings'])}")
    
    # Invalid template
    invalid_template = """
# Meeting: {{ title }
Date: {{ date
Attendees: {{ attendees | join(', ') }}
    """
    
    validation_result = engine.validate_template(invalid_template)
    print(f"❌ Invalid template: {validation_result['valid']}")
    print(f"   Errors: {len(validation_result['errors'])}")
    for error in validation_result['errors']:
        print(f"   - {error}")
    
    # Test custom filters
    print(f"\n🎨 Custom Filter Examples:")
    
    # Duration formatting
    durations = [30, 90, 150, 240]
    for duration in durations:
        formatted = engine.jinja_env.filters['format_duration'](duration)
        print(f"  {duration} minutes → {formatted}")
    
    # Priority formatting
    priorities = ['critical', 'high', 'medium', 'low']
    for priority in priorities:
        formatted = engine.jinja_env.filters['format_priority'](priority)
        print(f"  {priority} → {formatted}")
    
    # Confidence formatting
    confidences = [0.95, 0.75, 0.45, 0.25]
    for confidence in confidences:
        formatted = engine.jinja_env.filters['format_confidence'](confidence)
        print(f"  {confidence:.2f} → {formatted}")

def demo_comprehensive_comparison():
    """Demo comprehensive comparison of all styles"""
    print_separator("DEMO 7: Comprehensive Style Comparison", "=")
    
    # Use a rich meeting transcript
    transcript = """
[14:00] CEO: Welcome everyone to our quarterly all-hands meeting.
[14:02] CEO: Today we'll review Q3 results and plan for Q4.
[14:05] CFO: Q3 revenue exceeded targets by 12%. We're at $2.3M.
[14:07] CFO: Profit margins improved to 18%, up from 15% last quarter.
[14:10] VP Sales: We closed 15 new enterprise deals this quarter.
[14:12] VP Sales: Pipeline for Q4 looks strong with $5M in opportunities.
[14:15] CEO: Outstanding results! The board approves Q3 performance.
[14:18] CTO: Our platform now serves 100K+ active users daily.
[14:20] CTO: System uptime was 99.9% with zero critical incidents.
[14:23] VP Marketing: Brand awareness increased 35% following our campaign.
[14:25] VP Marketing: Customer acquisition cost decreased by 22%.
[14:28] CEO: Excellent work across all departments. We approve the Q4 strategy.
[14:30] CEO: Action item for CFO - prepare Q4 budget by October 15th.
[14:32] CFO: I'll have the detailed budget ready by mid-October.
[14:35] CEO: Action item for CTO - scale infrastructure for 200K users.
[14:37] CTO: I'll implement the scaling plan by November 1st.
[14:40] CEO: Action item for VP Sales - launch enterprise partnership program.
[14:42] VP Sales: I'll roll out the partner program by December 1st.
[14:45] CEO: These initiatives are critical for our growth targets.
[14:47] CEO: Next all-hands meeting in January to review Q4 results.
[14:50] CEO: Thank you all for an exceptional quarter!
    """
    
    context = {
        'meeting_id': 'q3_all_hands_2024',
        'title': 'Q3 All-Hands Meeting',
        'date': datetime(2024, 9, 30, 14, 0),
        'speaker_roles': {
            'CEO': 'Chief Executive Officer',
            'CFO': 'Chief Financial Officer',
            'CTO': 'Chief Technology Officer',
            'VP Sales': 'VP of Sales',
            'VP Marketing': 'VP of Marketing'
        }
    }
    
    print("📊 Analyzing comprehensive quarterly meeting...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    print(f"📈 Meeting Analysis Results:")
    print(f"  - Total Elements: {len(meeting.elements)}")
    print(f"  - Action Items: {len(action_items)}")
    print(f"  - Attendees: {len(meeting.attendees)}")
    print(f"  - Duration: {meeting.duration or 'N/A'} minutes")
    
    # Generate MOM in all styles
    styles = [
        (MOMStyle.CORPORATE, "Professional corporate format"),
        (MOMStyle.EXECUTIVE, "High-level executive summary"),
        (MOMStyle.AGILE, "Agile/startup friendly format"),
        (MOMStyle.TECHNICAL, "Technical documentation style"),
        (MOMStyle.DETAILED, "Comprehensive detailed format")
    ]
    
    print(f"\n📋 Generating MOM in {len(styles)} different styles:")
    
    for style, description in styles:
        config = MOMConfiguration(
            style=style,
            format=MOMFormat.MARKDOWN,
            include_timestamps=True,
            include_speaker_names=True,
            show_action_item_details=True,
            custom_fields={
                'quarter': 'Q3 2024',
                'performance': 'Exceeded Targets'
            }
        )
        
        rendered = generate_mom_from_meeting(meeting, action_items, config)
        
        print(f"\n{'-'*60}")
        print(f"📄 {style.value.upper()} STYLE - {description}")
        print(f"{'-'*60}")
        
        # Show first 800 characters of each style
        preview = rendered[:800] + "..." if len(rendered) > 800 else rendered
        print(preview)
        
        print(f"\n📊 Style Statistics:")
        print(f"  - Total Length: {len(rendered)} characters")
        print(f"  - Lines: {len(rendered.split(chr(10)))}")
        
        # Count style-specific elements
        emoji_count = sum(1 for char in rendered if ord(char) > 127)
        code_blocks = rendered.count('```') + rendered.count('`')
        headers = rendered.count('#')
        
        print(f"  - Emojis/Special chars: {emoji_count}")
        print(f"  - Code formatting: {code_blocks}")
        print(f"  - Headers: {headers}")

def main():
    """Run all demos"""
    print_separator("MOM TEMPLATE ENGINE COMPREHENSIVE DEMO", "=")
    print("📝 Professional Meeting Minutes Generation with Multiple Styles & Formats")
    print("🎨 Customizable templates with intelligent content organization")
    print()
    
    try:
        demo_corporate_style()
        print("\n" + "="*80 + "\n")
        
        demo_agile_style()
        print("\n" + "="*80 + "\n")
        
        demo_executive_style()
        print("\n" + "="*80 + "\n")
        
        demo_technical_style()
        print("\n" + "="*80 + "\n")
        
        demo_html_format()
        print("\n" + "="*80 + "\n")
        
        demo_template_customization()
        print("\n" + "="*80 + "\n")
        
        demo_comprehensive_comparison()
        
        print_separator("DEMO COMPLETED SUCCESSFULLY", "=")
        print("✅ All demos completed successfully!")
        print("🚀 The MOM Template Engine is ready for professional use!")
        print("\n🎯 Key Features Demonstrated:")
        print("  • Multiple professional styles (Corporate, Agile, Executive, Technical)")
        print("  • Multiple output formats (Markdown, HTML, Plain Text)")
        print("  • Intelligent content organization and grouping")
        print("  • Customizable templates with validation")
        print("  • Advanced filtering and formatting")
        print("  • Integration with meeting analysis and action item extraction")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()