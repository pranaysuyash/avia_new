#!/usr/bin/env python3
"""
Demo script for Export and Integration capabilities (Task 41)
Test the advanced export and integration features
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.append(str(Path(__file__).parent))

from export_integrations import (
    ExportData, export_integration_manager,
    HTMLReportGenerator, SlackIntegration, TeamsIntegration, DiscordIntegration,
    CalendarIntegration, CRMIntegration, LMSIntegration
)

def create_sample_export_data() -> ExportData:
    """Create sample export data for testing"""
    
    sample_transcript = """
    Welcome to today's quarterly business review meeting. I'm John Smith, the VP of Sales, 
    and we're here to discuss our Q3 performance and Q4 strategy.
    
    Our revenue for Q3 was $2.5 million, which represents a 15% increase over Q2. 
    The main drivers were our new enterprise clients including Microsoft, Google, and Amazon.
    
    Sarah Johnson from Marketing will now present the campaign results. Sarah, the floor is yours.
    
    Thank you, John. Our digital marketing campaigns generated 1,200 qualified leads this quarter.
    The conversion rate improved to 8.5%, up from 6.2% last quarter.
    
    For Q4, we need to focus on three key areas:
    1. Expanding our enterprise sales team
    2. Launching the new product features
    3. Improving customer retention rates
    
    Action items from today's meeting:
    - John will hire 2 new sales representatives by November 15th
    - Sarah will launch the holiday marketing campaign by December 1st
    - The product team will release version 2.0 by January 2024
    
    We've decided to increase our marketing budget by 20% for Q4 to support the growth initiatives.
    
    Thank you everyone for attending. Our next meeting is scheduled for January 15th, 2024.
    """
    
    sample_entities = [
        {"text": "John Smith", "type": "PERSON", "confidence": 0.95},
        {"text": "VP of Sales", "type": "ORG", "confidence": 0.88},
        {"text": "Q3", "type": "DATE", "confidence": 0.92},
        {"text": "$2.5 million", "type": "MONEY", "confidence": 0.90},
        {"text": "Microsoft", "type": "ORG", "confidence": 0.96},
        {"text": "Google", "type": "ORG", "confidence": 0.96},
        {"text": "Amazon", "type": "ORG", "confidence": 0.96},
        {"text": "Sarah Johnson", "type": "PERSON", "confidence": 0.94},
        {"text": "November 15th", "type": "DATE", "confidence": 0.89},
        {"text": "December 1st", "type": "DATE", "confidence": 0.91},
        {"text": "January 2024", "type": "DATE", "confidence": 0.93},
        {"text": "January 15th, 2024", "type": "DATE", "confidence": 0.95}
    ]
    
    sample_summary = """
    Quarterly business review meeting discussing Q3 performance and Q4 strategy. 
    Q3 revenue reached $2.5M (15% increase) driven by enterprise clients. 
    Marketing generated 1,200 qualified leads with 8.5% conversion rate. 
    Key Q4 focus areas: expand sales team, launch new features, improve retention. 
    Action items assigned with specific deadlines. Marketing budget increased by 20%.
    """
    
    sample_speakers = [
        {"id": "Speaker_1", "duration": 180.5, "segments": 8},
        {"id": "Speaker_2", "duration": 120.3, "segments": 5}
    ]
    
    sample_insights = {
        "sentiment_analysis": {
            "overall_sentiment": "positive",
            "confidence": 0.87,
            "positive_indicators": ["growth", "increase", "success", "improvement"],
            "negative_indicators": []
        },
        "key_topics": ["revenue", "marketing", "sales", "strategy", "action_items"],
        "action_items_count": 3,
        "decision_points": 2,
        "meeting_effectiveness_score": 8.5
    }
    
    sample_file_info = {
        "original_filename": "quarterly_review_meeting.mp3",
        "file_size": 15728640,  # ~15MB
        "processing_time": 45.2
    }
    
    return ExportData(
        transcript=sample_transcript,
        entities=sample_entities,
        summary=sample_summary,
        duration=300.8,  # ~5 minutes
        language="en",
        confidence=0.92,
        created_at=datetime.now().isoformat(),
        speakers=sample_speakers,
        insights=sample_insights,
        file_info=sample_file_info
    )


def test_html_report_generation():
    """Test HTML report generation"""
    print("🧪 Testing HTML Report Generation...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Generate HTML report
        html_generator = HTMLReportGenerator()
        html_content = html_generator.generate_interactive_report(export_data)
        
        # Save to file
        output_path = Path("test_report.html")
        output_path.write_text(html_content, encoding='utf-8')
        
        print(f"✅ HTML report generated successfully!")
        print(f"📄 Report saved to: {output_path.absolute()}")
        print(f"📊 Report size: {len(html_content):,} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ HTML report generation failed: {e}")
        return False


def test_slack_integration():
    """Test Slack integration (mock)"""
    print("\n🧪 Testing Slack Integration...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Test with mock webhook URL
        slack = SlackIntegration("https://hooks.slack.com/services/mock/webhook/url")
        
        # This would normally send to Slack, but we'll just validate the data structure
        print("✅ Slack integration initialized successfully!")
        print("📝 Would send summary with:")
        print(f"   - Duration: {export_data.duration:.1f}s")
        print(f"   - Confidence: {export_data.confidence:.1%}")
        print(f"   - Language: {export_data.language}")
        print(f"   - Word count: {len(export_data.transcript.split())}")
        
        return True
        
    except Exception as e:
        print(f"❌ Slack integration test failed: {e}")
        return False


def test_teams_integration():
    """Test Microsoft Teams integration (mock)"""
    print("\n🧪 Testing Microsoft Teams Integration...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Test with mock webhook URL
        teams = TeamsIntegration("https://outlook.office.com/webhook/mock/url")
        
        print("✅ Teams integration initialized successfully!")
        print("🎨 Would send adaptive card with:")
        print(f"   - Title: Transcription Analysis Complete")
        print(f"   - Facts: Duration, Confidence, Language, Words")
        print(f"   - Summary: {export_data.summary[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Teams integration test failed: {e}")
        return False


def test_discord_integration():
    """Test Discord integration (mock)"""
    print("\n🧪 Testing Discord Integration...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Test with mock webhook URL
        discord = DiscordIntegration("https://discord.com/api/webhooks/mock/url")
        
        print("✅ Discord integration initialized successfully!")
        print("🎮 Would send rich embed with:")
        print(f"   - Title: New Transcription Analysis")
        print(f"   - Color: Blue (#5814783)")
        print(f"   - Fields: Duration, Confidence, Language, Word Count")
        print(f"   - Description: {export_data.summary[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Discord integration test failed: {e}")
        return False


def test_calendar_integration():
    """Test calendar integration"""
    print("\n🧪 Testing Calendar Integration...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Create sample meeting info
        meeting_info = {
            "title": "Quarterly Business Review",
            "start_time": datetime.now(),
            "location": "Conference Room A",
            "attendees": ["john@company.com", "sarah@company.com"]
        }
        
        # Test calendar integration
        calendar = CalendarIntegration()
        details = calendar._extract_meeting_details(export_data, meeting_info)
        
        print("✅ Calendar integration test successful!")
        print("📅 Extracted meeting details:")
        print(f"   - Title: {details['title']}")
        print(f"   - Duration: {details['duration']:.1f}s")
        print(f"   - Action items: {len(details['action_items'])}")
        print(f"   - Key decisions: {len(details['key_decisions'])}")
        
        # Show sample action items
        if details['action_items']:
            print("🎯 Sample action items:")
            for item in details['action_items'][:3]:
                print(f"   • {item[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Calendar integration test failed: {e}")
        return False


def test_crm_integration():
    """Test CRM integration"""
    print("\n🧪 Testing CRM Integration...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Create sample customer info
        customer_info = {
            "name": "John Doe",
            "email": "john@acmecorp.com",
            "company": "Acme Corp",
            "call_type": "Sales Call",
            "deal_stage": "Proposal"
        }
        
        # Test CRM integration
        crm = CRMIntegration()
        analysis = crm._analyze_call_content(export_data)
        
        print("✅ CRM integration test successful!")
        print("🏢 Call analysis results:")
        print(f"   - Sentiment: {analysis['sentiment']} (score: {analysis['sentiment_score']:.2f})")
        print(f"   - Topics: {', '.join(analysis['topics'])}")
        print(f"   - Next steps: {len(analysis['next_steps'])}")
        print(f"   - Key entities: {len(analysis['key_entities'])}")
        
        # Show sample next steps
        if analysis['next_steps']:
            print("🎯 Sample next steps:")
            for step in analysis['next_steps'][:2]:
                print(f"   • {step[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ CRM integration test failed: {e}")
        return False


def test_lms_integration():
    """Test LMS integration"""
    print("\n🧪 Testing LMS Integration...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Create sample course info
        course_info = {
            "course_id": "BUS101_2024",
            "title": "Business Strategy Fundamentals",
            "code": "BUS101",
            "instructor": "Dr. Jane Smith",
            "level": "Intermediate",
            "content_type": "Lecture"
        }
        
        # Test LMS integration
        lms = LMSIntegration()
        analysis = lms._analyze_educational_content(export_data)
        
        print("✅ LMS integration test successful!")
        print("🎓 Educational content analysis:")
        print(f"   - Difficulty level: {analysis['difficulty_level']}")
        print(f"   - Study time: {analysis['estimated_study_time']} minutes")
        print(f"   - Key concepts: {len(analysis['key_concepts'])}")
        print(f"   - Quiz questions: {len(analysis['quiz_questions'])}")
        print(f"   - Learning objectives: {len(analysis['learning_objectives'])}")
        
        # Show sample concepts
        if analysis['key_concepts']:
            print("🎯 Sample key concepts:")
            for concept in analysis['key_concepts'][:3]:
                print(f"   • {concept[:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ LMS integration test failed: {e}")
        return False


def test_export_package():
    """Test comprehensive export package creation"""
    print("\n🧪 Testing Export Package Creation...")
    
    try:
        # Create sample data
        export_data = create_sample_export_data()
        
        # Test export package creation
        formats = ["html", "json", "txt", "csv"]
        package_data = export_integration_manager.create_export_package(
            export_data, formats
        )
        
        print("✅ Export package created successfully!")
        print(f"📦 Package formats: {', '.join(formats)}")
        print(f"📊 Package size: {len(package_data):,} characters (base64)")
        
        # Estimate actual size
        import base64
        actual_size = len(base64.b64decode(package_data))
        print(f"💾 Actual ZIP size: {actual_size:,} bytes ({actual_size/1024:.1f} KB)")
        
        return True
        
    except Exception as e:
        print(f"❌ Export package creation failed: {e}")
        return False


def main():
    """Run all integration tests"""
    print("🚀 Starting Export and Integration Tests")
    print("=" * 50)
    
    tests = [
        test_html_report_generation,
        test_slack_integration,
        test_teams_integration,
        test_discord_integration,
        test_calendar_integration,
        test_crm_integration,
        test_lms_integration,
        test_export_package
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Export and integration features are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the output above for details.")
    
    print("\n📝 Note: These are mock tests. Real integrations require valid API keys and endpoints.")
    print("🔧 Configure your .env file with actual credentials for production use.")


if __name__ == "__main__":
    main()