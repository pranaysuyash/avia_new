"""
Demo Script for Dynamic Output Templates System
Demonstrates the capabilities of the template engine and smart formatter
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dynamic_output_templates import (
    TemplateEngine, SmartFormatter, TemplateManager,
    ContentMetadata, TranscriptSegment, ActionItem, KeyPoint,
    create_sample_content, format_time_duration
)

def print_header(title: str):
    """Print formatted header"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def print_subheader(title: str):
    """Print formatted subheader"""
    print(f"\n--- {title} ---")

def demo_basic_functionality():
    """Demonstrate basic template engine functionality"""
    print_header("DYNAMIC OUTPUT TEMPLATES DEMO")
    
    # Initialize system
    print("🚀 Initializing Template System...")
    template_manager = TemplateManager("demo_templates")
    
    print(f"✅ Template system initialized")
    print(f"📁 Templates directory: {template_manager.template_engine.templates_dir}")
    
    # Show available templates
    templates = template_manager.template_engine.get_available_templates()
    print(f"📋 Available templates: {len(templates)}")
    
    for template in templates:
        print(f"   • {template['name']} ({template['format']}): {template['description']}")

def demo_content_analysis():
    """Demonstrate content analysis capabilities"""
    print_header("CONTENT ANALYSIS DEMO")
    
    template_manager = TemplateManager("demo_templates")
    
    # Test different content types
    content_samples = {
        "Meeting": [
            TranscriptSegment(0, 30, "Sarah", "Let's start today's meeting with the agenda review"),
            TranscriptSegment(30, 75, "Mike", "We have three action items from last week to discuss"),
            TranscriptSegment(75, 120, "Lisa", "The budget meeting is scheduled for Friday")
        ],
        "Interview": [
            TranscriptSegment(0, 45, "Interviewer", "Tell me about your experience with Python development"),
            TranscriptSegment(45, 120, "Candidate", "I have five years of experience building web applications"),
            TranscriptSegment(120, 180, "Interviewer", "What's your background with machine learning?")
        ],
        "Lecture": [
            TranscriptSegment(0, 60, "Professor", "Today we will cover advanced algorithms and data structures"),
            TranscriptSegment(60, 120, "Professor", "Your assignment for next week is to implement a binary search tree"),
            TranscriptSegment(120, 180, "Student", "Will this be covered on the exam?")
        ],
        "Podcast": [
            TranscriptSegment(0, 45, "Host", "Welcome back to Tech Talk, I'm your host Jennifer"),
            TranscriptSegment(45, 90, "Guest", "Thanks for having me on the show, I'm excited to be here"),
            TranscriptSegment(90, 150, "Host", "Don't forget to subscribe and leave us a review")
        ]
    }
    
    for content_name, segments in content_samples.items():
        print_subheader(f"Analyzing {content_name} Content")
        
        detected_type = template_manager.smart_formatter.analyze_content_type(segments)
        print(f"🔍 Detected content type: {detected_type}")
        
        action_items = template_manager.smart_formatter.extract_action_items(segments)
        print(f"📋 Action items found: {len(action_items)}")
        for item in action_items[:2]:  # Show first 2
            print(f"   • {item.text}")
        
        key_points = template_manager.smart_formatter.extract_key_points(segments)
        print(f"🎯 Key points found: {len(key_points)}")
        for point in key_points[:2]:  # Show first 2
            print(f"   • {point.text}")

def demo_template_formatting():
    """Demonstrate template formatting with different templates"""
    print_header("TEMPLATE FORMATTING DEMO")
    
    template_manager = TemplateManager("demo_templates")
    
    # Create comprehensive sample data
    metadata = ContentMetadata(
        title="Q4 Planning Meeting - Product Development",
        content_type="meeting",
        duration=3600,  # 1 hour
        speakers=["Sarah Johnson (PM)", "Mike Chen (Dev)", "Lisa Rodriguez (Design)", "Alex Kim (QA)"],
        date_created=datetime.now(),
        summary="Quarterly planning meeting to discuss product roadmap, resource allocation, and timeline for Q4 deliverables.",
        key_topics=["Product Roadmap", "Resource Planning", "Timeline Review", "Budget Allocation"]
    )
    
    segments = [
        TranscriptSegment(0, 45, "Sarah Johnson", "Good morning everyone. Let's start our Q4 planning session with a review of our current progress."),
        TranscriptSegment(45, 120, "Mike Chen", "We've completed 85% of the planned features for Q3. The main blocker has been the API integration with the new payment system."),
        TranscriptSegment(120, 200, "Lisa Rodriguez", "From a design perspective, we need to finalize the UI mockups for the mobile app by next Friday."),
        TranscriptSegment(200, 280, "Alex Kim", "I've identified several critical bugs that need to be addressed before the Q4 release. We should prioritize these in our sprint planning."),
        TranscriptSegment(280, 360, "Sarah Johnson", "Great points everyone. Let's create action items for each of these areas. Mike, can you lead the API integration effort?"),
        TranscriptSegment(360, 440, "Mike Chen", "Absolutely. I'll coordinate with the payments team and have a timeline ready by Wednesday."),
        TranscriptSegment(440, 520, "Lisa Rodriguez", "I'll work with the UX team to finalize the mobile designs. We should have everything ready for developer handoff by Friday."),
        TranscriptSegment(520, 600, "Alex Kim", "I'll create detailed bug reports and work with the development team to prioritize fixes based on severity."),
        TranscriptSegment(600, 680, "Sarah Johnson", "Perfect. Let's schedule a follow-up meeting for next week to review progress on all action items.")
    ]
    
    action_items = [
        ActionItem("Lead API integration with payments team", "Mike Chen", datetime.now() + timedelta(days=3), "high"),
        ActionItem("Finalize mobile UI mockups", "Lisa Rodriguez", datetime.now() + timedelta(days=5), "high"),
        ActionItem("Create detailed bug reports and prioritization", "Alex Kim", datetime.now() + timedelta(days=2), "medium"),
        ActionItem("Schedule follow-up meeting", "Sarah Johnson", datetime.now() + timedelta(days=7), "low")
    ]
    
    key_points = [
        KeyPoint("85% of Q3 features completed", 45, 1.0, "Progress"),
        KeyPoint("API integration is main blocker", 45, 0.9, "Blocker"),
        KeyPoint("Mobile UI mockups due Friday", 120, 0.8, "Deadline"),
        KeyPoint("Critical bugs identified for Q4", 200, 0.9, "Quality")
    ]
    
    # Test different templates
    templates_to_test = [
        ("meeting_minutes.html", "HTML Meeting Minutes"),
        ("executive_summary.html", "Executive Summary"),
        ("action_items.md", "Action Items List"),
        ("detailed_transcript.html", "Detailed Transcript")
    ]
    
    for template_name, description in templates_to_test:
        print_subheader(f"Generating {description}")
        
        try:
            result = template_manager.template_engine.format_content(
                template_name=template_name,
                metadata=metadata,
                transcript_segments=segments,
                action_items=action_items,
                key_points=key_points
            )
            
            print(f"✅ Generated {result.format_type.upper()} output")
            print(f"📄 Template: {result.template_name}")
            print(f"📊 Content length: {len(result.content)} characters")
            print(f"🕒 Generated at: {result.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Save output to file for inspection
            output_dir = Path("demo_outputs")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / f"{template_name.split('.')[0]}_output.{result.format_type}"
            output_file.write_text(result.content)
            print(f"💾 Saved to: {output_file}")
            
            # Show preview of content
            preview = result.content[:200] + "..." if len(result.content) > 200 else result.content
            print(f"👁️  Preview:\n{preview}")
            
        except Exception as e:
            print(f"❌ Error generating {description}: {str(e)}")

def demo_custom_template():
    """Demonstrate custom template creation"""
    print_header("CUSTOM TEMPLATE DEMO")
    
    template_manager = TemplateManager("demo_templates")
    
    # Create a custom template
    custom_template_content = """
# {{ metadata.title }}

**Meeting Summary Report**

---

## Overview
- **Date:** {{ metadata.date_created.strftime('%B %d, %Y') if metadata.date_created else 'N/A' }}
- **Duration:** {{ metadata.duration | format_duration if metadata.duration else 'N/A' }}
- **Participants:** {{ metadata.speakers | length if metadata.speakers else 0 }}

{% if metadata.summary %}
## Executive Summary
{{ metadata.summary }}
{% endif %}

## Key Metrics
- **Total Segments:** {{ transcript_segments | length }}
- **Action Items:** {{ action_items | length }}
- **Key Points:** {{ key_points | length }}
- **Word Count:** {{ transcript_segments | map(attribute='text') | join(' ') | wordcount }}

{% if action_items %}
## Priority Actions
{% for item in action_items %}
{% if item.priority == 'high' %}
- 🔴 **{{ item.text }}** ({{ item.assignee }})
{% elif item.priority == 'medium' %}
- 🟡 **{{ item.text }}** ({{ item.assignee }})
{% else %}
- 🟢 **{{ item.text }}** ({{ item.assignee }})
{% endif %}
{% endfor %}
{% endif %}

## Discussion Highlights
{% for point in key_points %}
- {{ point.text }} {% if point.timestamp %}*[{{ point.timestamp | format_time }}]*{% endif %}
{% endfor %}

---
*Generated on {{ generated_at.strftime('%B %d, %Y at %I:%M %p') }}*
"""
    
    print("🛠️  Creating custom template...")
    
    success = template_manager.template_engine.create_custom_template(
        name="custom_summary_report",
        content=custom_template_content,
        description="Custom meeting summary report with metrics and priority actions",
        format_type="markdown"
    )
    
    if success:
        print("✅ Custom template created successfully!")
        
        # Test the custom template
        sample_data = create_sample_content()
        
        result = template_manager.template_engine.format_content(
            template_name="custom_summary_report.markdown",
            metadata=sample_data["metadata"],
            transcript_segments=sample_data["transcript_segments"],
            action_items=sample_data["action_items"],
            key_points=sample_data["key_points"]
        )
        
        print(f"📄 Generated custom output ({len(result.content)} characters)")
        
        # Save custom output
        output_dir = Path("demo_outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_file = output_dir / "custom_summary_report.md"
        output_file.write_text(result.content)
        print(f"💾 Saved custom output to: {output_file}")
        
        # Show preview
        preview_lines = result.content.split('\n')[:15]
        print(f"👁️  Preview:\n" + '\n'.join(preview_lines) + "\n...")
        
    else:
        print("❌ Failed to create custom template")

def demo_batch_processing():
    """Demonstrate batch processing capabilities"""
    print_header("BATCH PROCESSING DEMO")
    
    template_manager = TemplateManager("demo_templates")
    
    # Create multiple content samples
    batch_data = [
        {
            "name": "Team Standup",
            "metadata": ContentMetadata(
                title="Daily Team Standup - Sprint 23",
                content_type="meeting",
                duration=900,  # 15 minutes
                speakers=["Alice", "Bob", "Carol"],
                date_created=datetime.now() - timedelta(days=1)
            ),
            "segments": [
                TranscriptSegment(0, 30, "Alice", "Good morning team. Let's start with yesterday's progress."),
                TranscriptSegment(30, 60, "Bob", "I completed the user authentication module."),
                TranscriptSegment(60, 90, "Carol", "I'm working on the database optimization.")
            ]
        },
        {
            "name": "Client Interview",
            "metadata": ContentMetadata(
                title="Client Requirements Interview - Project Phoenix",
                content_type="interview",
                duration=2700,  # 45 minutes
                speakers=["Interviewer", "Client"],
                date_created=datetime.now() - timedelta(days=2)
            ),
            "segments": [
                TranscriptSegment(0, 45, "Interviewer", "What are your main requirements for this project?"),
                TranscriptSegment(45, 120, "Client", "We need a scalable solution that can handle 10,000 users."),
                TranscriptSegment(120, 180, "Interviewer", "What's your timeline for implementation?")
            ]
        },
        {
            "name": "Training Session",
            "metadata": ContentMetadata(
                title="New Employee Training - Security Protocols",
                content_type="lecture",
                duration=3600,  # 1 hour
                speakers=["Trainer", "Employee1", "Employee2"],
                date_created=datetime.now() - timedelta(days=3)
            ),
            "segments": [
                TranscriptSegment(0, 60, "Trainer", "Today we'll cover our security protocols and best practices."),
                TranscriptSegment(60, 120, "Employee1", "What should we do if we suspect a security breach?"),
                TranscriptSegment(120, 180, "Trainer", "Immediately contact the security team and document the incident.")
            ]
        }
    ]
    
    print(f"📦 Processing {len(batch_data)} content items...")
    
    # Process each item with auto-formatting
    results = []
    for item in batch_data:
        print_subheader(f"Processing: {item['name']}")
        
        result = template_manager.smart_formatter.auto_format(
            transcript_segments=item["segments"],
            metadata=item["metadata"],
            preferred_format="html"
        )
        
        results.append((item["name"], result))
        print(f"✅ Processed {item['name']} -> {result.template_name}")
    
    # Save all results
    output_dir = Path("demo_outputs/batch")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for name, result in results:
        filename = f"{name.lower().replace(' ', '_')}.{result.format_type}"
        output_file = output_dir / filename
        output_file.write_text(result.content)
        print(f"💾 Saved {name} to: {output_file}")
    
    print(f"\n🎉 Batch processing complete! Generated {len(results)} outputs.")

def demo_statistics_and_analytics():
    """Demonstrate statistics and analytics features"""
    print_header("STATISTICS & ANALYTICS DEMO")
    
    template_manager = TemplateManager("demo_templates")
    
    # Get template statistics
    stats = template_manager.get_template_stats()
    
    print_subheader("Template Statistics")
    print(f"📊 Total templates: {stats['total_templates']}")
    print(f"🏗️  Built-in templates: {stats['builtin_templates']}")
    print(f"🛠️  Custom templates: {stats['custom_templates']}")
    
    print("\n📋 Templates by format:")
    for format_type, count in stats['by_format'].items():
        print(f"   • {format_type.upper()}: {count}")
    
    # Analyze sample content
    sample_data = create_sample_content()
    
    print_subheader("Content Analysis")
    
    from dynamic_output_templates import extract_text_statistics
    text_stats = extract_text_statistics(sample_data["transcript_segments"])
    
    print(f"📝 Total words: {text_stats['total_words']}")
    print(f"📄 Total characters: {text_stats['total_characters']}")
    print(f"🎤 Unique speakers: {text_stats['unique_speakers']}")
    print(f"⏱️  Total duration: {format_time_duration(text_stats['total_duration'])}")
    print(f"📊 Average words per segment: {text_stats['average_words_per_segment']:.1f}")
    
    # Show content type analysis
    detected_type = template_manager.smart_formatter.analyze_content_type(sample_data["transcript_segments"])
    print(f"🔍 Detected content type: {detected_type}")

def main():
    """Run all demos"""
    print("🎬 Starting Dynamic Output Templates Demo")
    print("This demo will showcase the capabilities of the template system")
    
    try:
        demo_basic_functionality()
        demo_content_analysis()
        demo_template_formatting()
        demo_custom_template()
        demo_batch_processing()
        demo_statistics_and_analytics()
        
        print_header("DEMO COMPLETE")
        print("🎉 All demos completed successfully!")
        print("📁 Check the 'demo_outputs' directory for generated files")
        print("🔧 Template files are stored in 'demo_templates' directory")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()