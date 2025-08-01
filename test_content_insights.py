#!/usr/bin/env python3
"""
Test content insights functionality
"""

import os
import sys
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from content_insights import ContentInsightsAnalyzer


def test_content_insights():
    """Test content insights analysis"""
    print("🧠 Testing Content Insights")
    print("=" * 50)
    
    analyzer = ContentInsightsAnalyzer()
    
    # Sample transcript for testing
    sample_transcript = """
    Welcome to our quarterly planning meeting. I'm excited to discuss our progress and set goals for the next quarter.
    
    First, let's review what we accomplished. Our team successfully launched the new product feature last month, 
    which has received positive feedback from users. The user engagement increased by 25%, which exceeded our expectations.
    
    However, we did face some challenges with the initial rollout. There were a few bugs that caused user frustration, 
    but our development team worked quickly to resolve them. Moving forward, we need to improve our testing process.
    
    For next quarter, I propose we focus on three main areas: improving product quality, expanding our user base, 
    and enhancing our customer support capabilities. These initiatives will help us achieve our annual growth targets.
    
    Sarah, can you take the lead on the quality improvement initiative? And Mike, would you be willing to head up 
    the user acquisition efforts? We'll need to allocate additional resources to these projects.
    
    Let's schedule follow-up meetings to track our progress and make sure we stay on course. 
    Thank you all for your hard work and dedication.
    """
    
    # Sample speaker segments
    sample_segments = [
        {
            'speaker_id': 'speaker_1',
            'text': 'Welcome to our quarterly planning meeting. I\'m excited to discuss our progress and set goals for the next quarter.',
            'duration': 8.5,
            'start_time': 0.0,
            'end_time': 8.5
        },
        {
            'speaker_id': 'speaker_1', 
            'text': 'First, let\'s review what we accomplished. Our team successfully launched the new product feature last month.',
            'duration': 6.2,
            'start_time': 8.5,
            'end_time': 14.7
        },
        {
            'speaker_id': 'speaker_2',
            'text': 'The user engagement increased by 25%, which exceeded our expectations.',
            'duration': 4.1,
            'start_time': 14.7,
            'end_time': 18.8
        },
        {
            'speaker_id': 'speaker_1',
            'text': 'However, we did face some challenges with the initial rollout. There were a few bugs that caused user frustration.',
            'duration': 7.3,
            'start_time': 18.8,
            'end_time': 26.1
        }
    ]
    
    try:
        print("\n1️⃣ Running content insights analysis...")
        
        # Run analysis
        insights = asyncio.run(analyzer.analyze_content(
            transcript=sample_transcript,
            transcript_id="test_meeting_001",
            speaker_segments=sample_segments,
            metadata={'meeting_type': 'quarterly_planning', 'duration': '15_minutes'}
        ))
        
        print("✅ Analysis completed successfully!")
        
        # Display results
        print(f"\n📊 Analysis Results:")
        print(f"   Transcript ID: {insights.transcript_id}")
        print(f"   Analyzed at: {insights.analyzed_at}")
        
        print(f"\n📝 Summary:")
        print(f"   Brief: {insights.summary.brief}")
        print(f"   Key Points: {len(insights.summary.key_points)} identified")
        print(f"   Action Items: {len(insights.summary.action_items)} identified")
        
        print(f"\n😊 Sentiment Analysis:")
        print(f"   Overall: {insights.sentiment.overall_sentiment} (confidence: {insights.sentiment.confidence:.1%})")
        print(f"   Positive: {insights.sentiment.positive_score:.1%}")
        print(f"   Negative: {insights.sentiment.negative_score:.1%}")
        print(f"   Neutral: {insights.sentiment.neutral_score:.1%}")
        
        if insights.sentiment.emotions:
            print(f"   Emotions detected: {', '.join(insights.sentiment.emotions.keys())}")
        
        print(f"\n🏷️ Topics Identified: {len(insights.topics)}")
        for i, topic in enumerate(insights.topics, 1):
            print(f"   {i}. {topic.topic} (confidence: {topic.confidence:.1%})")
            print(f"      Keywords: {', '.join(topic.keywords)}")
        
        print(f"\n🎤 Speaker Insights: {len(insights.speaker_insights)}")
        for speaker in insights.speaker_insights:
            print(f"   {speaker.speaker_id}:")
            print(f"     Speaking time: {speaker.speaking_time:.1f}s")
            print(f"     Words: {speaker.word_count}")
            print(f"     Pace: {speaker.avg_speaking_pace:.1f} WPM")
            print(f"     Style: {speaker.communication_style}")
            print(f"     Sentiment: {speaker.sentiment.overall_sentiment}")
        
        print(f"\n⭐ Key Moments: {len(insights.key_moments)}")
        for i, moment in enumerate(insights.key_moments, 1):
            print(f"   {i}. {moment.get('description', 'No description')}")
            if 'significance' in moment:
                print(f"      Significance: {moment['significance']}")
        
        # Test serialization
        print(f"\n🔄 Testing serialization...")
        insights_dict = insights.to_dict()
        print(f"   Serialized to dict with {len(insights_dict)} top-level keys")
        
        print(f"\n✅ All content insights tests passed!")
        
    except Exception as e:
        print(f"\n❌ Content insights test failed: {e}")
        import traceback
        traceback.print_exc()


def test_basic_functionality():
    """Test basic functionality without OpenAI"""
    print("\n🔧 Testing Basic Functionality (without OpenAI)")
    print("=" * 30)
    
    # Temporarily disable OpenAI to test fallback
    analyzer = ContentInsightsAnalyzer()
    analyzer.client = None  # Disable OpenAI client
    
    simple_text = "This is a great meeting. We made excellent progress on our project. The team is very happy with the results."
    
    try:
        insights = asyncio.run(analyzer.analyze_content(
            transcript=simple_text,
            transcript_id="basic_test"
        ))
        
        print("✅ Basic analysis completed")
        print(f"   Sentiment: {insights.sentiment.overall_sentiment}")
        print(f"   Topics: {len(insights.topics)}")
        print(f"   Summary available: {bool(insights.summary.brief)}")
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")


if __name__ == "__main__":
    print("🧪 Content Insights Test Suite")
    print("=" * 50)
    
    # Run tests
    test_content_insights()
    test_basic_functionality()
    
    print("\n🎉 Content insights testing completed!")