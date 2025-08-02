#!/usr/bin/env python3
"""
Demo Script for AI-Powered Content Insights
Demonstrates Task 31: AI-powered content insights functionality

This script showcases:
- Automatic meeting minutes generation
- Action item extraction and task identification
- Sentiment analysis timeline
- Topic clustering and content categorization
- Automatic summary generation with key highlights
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Dict, List, Any

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_content_insights import AIContentInsights, ContentType


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f"🧠 {title}")
    print("=" * 80)


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n📊 {title}")
    print("-" * 60)


def create_sample_meeting_transcript() -> Dict[str, Any]:
    """Create a comprehensive sample meeting transcript for demonstration"""
    return {
        "segments": [
            {
                "start": 0.0,
                "end": 8.0,
                "text": "Good morning everyone, welcome to our quarterly planning meeting. I'm excited to discuss our progress and upcoming initiatives.",
                "speaker": "Sarah"
            },
            {
                "start": 8.0,
                "end": 15.0,
                "text": "Let's start with a review of last quarter's performance. Overall, I think we exceeded our targets, which is fantastic news.",
                "speaker": "Sarah"
            },
            {
                "start": 15.0,
                "end": 22.0,
                "text": "Yes, the sales numbers were particularly strong. We saw a 25% increase compared to the same period last year.",
                "speaker": "Mike"
            },
            {
                "start": 22.0,
                "end": 30.0,
                "text": "That's excellent! However, I'm concerned about the customer support response times. We've been getting some complaints.",
                "speaker": "Jennifer"
            },
            {
                "start": 30.0,
                "end": 38.0,
                "text": "You're right, Jennifer. We need to address this urgently. Mike, can you work with the support team to improve response times by next Friday?",
                "speaker": "Sarah"
            },
            {
                "start": 38.0,
                "end": 45.0,
                "text": "Absolutely, I'll prioritize this. I think we can implement some automation to help with the initial responses.",
                "speaker": "Mike"
            },
            {
                "start": 45.0,
                "end": 53.0,
                "text": "Great! Now, let's discuss the new product launch. The development team has been working hard, but we're facing some technical challenges.",
                "speaker": "Sarah"
            },
            {
                "start": 53.0,
                "end": 62.0,
                "text": "The main issue is with the database performance under high load. It's causing significant delays in our testing phase.",
                "speaker": "David"
            },
            {
                "start": 62.0,
                "end": 70.0,
                "text": "This is critical for our launch timeline. David, what do you need to resolve this? Do we need additional resources?",
                "speaker": "Sarah"
            },
            {
                "start": 70.0,
                "end": 78.0,
                "text": "I think we need to bring in a database specialist. Also, Jennifer should review the user experience flow to ensure it's optimized.",
                "speaker": "David"
            },
            {
                "start": 78.0,
                "end": 85.0,
                "text": "I can definitely help with the UX review. I'll have a comprehensive analysis ready by Wednesday.",
                "speaker": "Jennifer"
            },
            {
                "start": 85.0,
                "end": 93.0,
                "text": "Perfect! I'm feeling more optimistic about this. Let's also discuss our marketing strategy for the launch.",
                "speaker": "Sarah"
            },
            {
                "start": 93.0,
                "end": 102.0,
                "text": "We've prepared a multi-channel campaign focusing on social media and content marketing. The budget allocation looks good.",
                "speaker": "Mike"
            },
            {
                "start": 102.0,
                "end": 110.0,
                "text": "Excellent work, Mike. However, I'm worried about the competitive landscape. Our main competitor just announced a similar product.",
                "speaker": "Sarah"
            },
            {
                "start": 110.0,
                "end": 118.0,
                "text": "That's concerning, but I believe our unique features will differentiate us. We should emphasize our superior user experience.",
                "speaker": "Jennifer"
            },
            {
                "start": 118.0,
                "end": 126.0,
                "text": "Agreed. Let's schedule a follow-up meeting next week to finalize our competitive positioning strategy.",
                "speaker": "Sarah"
            },
            {
                "start": 126.0,
                "end": 134.0,
                "text": "Before we wrap up, I want to discuss team morale. The recent survey results show some areas for improvement.",
                "speaker": "Sarah"
            },
            {
                "start": 134.0,
                "end": 142.0,
                "text": "Yes, work-life balance seems to be a concern. Maybe we should consider flexible working arrangements or additional time off.",
                "speaker": "Jennifer"
            },
            {
                "start": 142.0,
                "end": 150.0,
                "text": "That's a great suggestion. I'll draft a proposal for flexible work policies and present it to HR by the end of this week.",
                "speaker": "Mike"
            },
            {
                "start": 150.0,
                "end": 158.0,
                "text": "Wonderful! I think this has been a very productive meeting. Thank you all for your contributions and commitment.",
                "speaker": "Sarah"
            }
        ]
    }


def create_sample_interview_transcript() -> Dict[str, Any]:
    """Create a sample interview transcript for demonstration"""
    return {
        "segments": [
            {
                "start": 0.0,
                "end": 6.0,
                "text": "Thank you for joining us today. Could you start by telling us about your background in software development?",
                "speaker": "Interviewer"
            },
            {
                "start": 6.0,
                "end": 15.0,
                "text": "Certainly! I have over eight years of experience in full-stack development, primarily working with Python and JavaScript frameworks.",
                "speaker": "Candidate"
            },
            {
                "start": 15.0,
                "end": 22.0,
                "text": "That's impressive. Can you describe a challenging project you worked on recently?",
                "speaker": "Interviewer"
            },
            {
                "start": 22.0,
                "end": 35.0,
                "text": "I led the development of a real-time analytics platform that processes millions of events per day. The main challenge was optimizing for both speed and accuracy.",
                "speaker": "Candidate"
            },
            {
                "start": 35.0,
                "end": 42.0,
                "text": "How did you approach the performance optimization?",
                "speaker": "Interviewer"
            },
            {
                "start": 42.0,
                "end": 55.0,
                "text": "We implemented a multi-tier caching strategy and used message queues for asynchronous processing. This reduced response times by 70%.",
                "speaker": "Candidate"
            },
            {
                "start": 55.0,
                "end": 62.0,
                "text": "Excellent problem-solving approach. What interests you most about this position?",
                "speaker": "Interviewer"
            },
            {
                "start": 62.0,
                "end": 72.0,
                "text": "I'm excited about the opportunity to work on AI-powered applications and contribute to innovative solutions that can make a real impact.",
                "speaker": "Candidate"
            }
        ]
    }


def demonstrate_basic_analysis(analyzer: AIContentInsights, transcript_data: Dict[str, Any], content_type: ContentType):
    """Demonstrate basic analysis functionality"""
    print_section("Basic Analysis")
    
    print("🔍 Analyzing transcript...")
    start_time = time.time()
    
    try:
        results = analyzer.analyze_content(
            transcript_data=transcript_data,
            content_type=content_type
        )
        
        analysis_time = time.time() - start_time
        print(f"✅ Analysis completed in {analysis_time:.2f} seconds")
        
        # Display basic statistics
        stats = results.get('transcript_stats', {})
        print(f"\n📈 Transcript Statistics:")
        print(f"   • Duration: {stats.get('total_duration', 0):.1f} seconds")
        print(f"   • Total segments: {stats.get('total_segments', 0)}")
        print(f"   • Word count: {stats.get('word_count', 0):,}")
        print(f"   • Speaking rate: {stats.get('speaking_rate', 0):.1f} words/minute")
        
        return results
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return None


def demonstrate_summary_generation(results: Dict[str, Any]):
    """Demonstrate summary generation"""
    print_section("Content Summary")
    
    summary = results.get('summary', {})
    if isinstance(summary, dict):
        print("📋 Executive Summary:")
        print(f"   {summary.get('executive_summary', 'No summary available')}")
        
        key_points = summary.get('key_points', [])
        if key_points:
            print(f"\n🔑 Key Points ({len(key_points)}):")
            for i, point in enumerate(key_points, 1):
                print(f"   {i}. {point}")
        
        main_topics = summary.get('main_topics', [])
        if main_topics:
            print(f"\n🏷️ Main Topics: {', '.join(main_topics)}")
        
        print(f"\n💯 Confidence Score: {summary.get('confidence_score', 0):.2f}")


def demonstrate_action_items(results: Dict[str, Any]):
    """Demonstrate action item extraction"""
    print_section("Action Items Analysis")
    
    action_items = results.get('action_items', [])
    
    if not action_items:
        print("ℹ️ No action items identified")
        return
    
    print(f"✅ Found {len(action_items)} action items:")
    
    # Group by priority
    priority_groups = {'high': [], 'medium': [], 'low': []}
    for item in action_items:
        # Handle both dict and ActionItem object
        if hasattr(item, 'priority'):
            priority = item.priority.value if hasattr(item.priority, 'value') else str(item.priority)
        else:
            priority = item.get('priority', 'medium')
        priority_groups[priority].append(item)
    
    priority_icons = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}
    
    for priority, items in priority_groups.items():
        if items:
            print(f"\n{priority_icons[priority]} {priority.upper()} Priority ({len(items)} items):")
            for item in items:
                # Handle both dict and ActionItem object
                if hasattr(item, 'text'):
                    text = item.text
                    assignee = f" → {item.assignee or 'Unassigned'}" if item.assignee else ""
                    due_date = f" (Due: {item.due_date})" if item.due_date else ""
                    confidence = f" [{item.confidence:.2f}]"
                else:
                    text = item.get('text', '')
                    assignee = f" → {item.get('assignee', 'Unassigned')}" if item.get('assignee') else ""
                    due_date = f" (Due: {item.get('due_date')})" if item.get('due_date') else ""
                    confidence = f" [{item.get('confidence', 0):.2f}]"
                
                print(f"   • {text}{assignee}{due_date}{confidence}")


def demonstrate_sentiment_analysis(results: Dict[str, Any]):
    """Demonstrate sentiment analysis"""
    print_section("Sentiment Analysis")
    
    sentiment_data = results.get('sentiment_analysis', [])
    
    if not sentiment_data:
        print("ℹ️ No sentiment analysis data available")
        return
    
    # Calculate sentiment distribution
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    total_score = 0
    
    for point in sentiment_data:
        # Handle both dict and SentimentPoint object
        if hasattr(point, 'sentiment'):
            sentiment = point.sentiment.value if hasattr(point.sentiment, 'value') else str(point.sentiment)
            score = point.score
        else:
            sentiment = point.get('sentiment', 'neutral')
            score = point.get('score', 0)
        
        sentiment_counts[sentiment] += 1
        total_score += score
    
    total_segments = len(sentiment_data)
    avg_score = total_score / total_segments if total_segments > 0 else 0
    
    print(f"📊 Sentiment Distribution:")
    print(f"   😊 Positive: {sentiment_counts['positive']} ({sentiment_counts['positive']/total_segments*100:.1f}%)")
    print(f"   😐 Neutral:  {sentiment_counts['neutral']} ({sentiment_counts['neutral']/total_segments*100:.1f}%)")
    print(f"   😞 Negative: {sentiment_counts['negative']} ({sentiment_counts['negative']/total_segments*100:.1f}%)")
    print(f"   📈 Average Score: {avg_score:.3f} (-1 to 1 scale)")
    
    # Show sentiment timeline highlights
    print(f"\n🎯 Sentiment Highlights:")
    
    # Find most positive and negative segments
    positive_segments = []
    negative_segments = []
    
    for p in sentiment_data:
        if hasattr(p, 'sentiment'):
            sentiment = p.sentiment.value if hasattr(p.sentiment, 'value') else str(p.sentiment)
        else:
            sentiment = p.get('sentiment', 'neutral')
        
        if sentiment == 'positive':
            positive_segments.append(p)
        elif sentiment == 'negative':
            negative_segments.append(p)
    
    if positive_segments:
        most_positive = max(positive_segments, key=lambda x: x.score if hasattr(x, 'score') else x.get('score', 0))
        if hasattr(most_positive, 'text_segment'):
            text = most_positive.text_segment
            score = most_positive.score
        else:
            text = most_positive.get('text_segment', '')
            score = most_positive.get('score', 0)
        print(f"   😊 Most Positive: \"{text[:60]}...\" (Score: {score:.2f})")
    
    if negative_segments:
        most_negative = min(negative_segments, key=lambda x: x.score if hasattr(x, 'score') else x.get('score', 0))
        if hasattr(most_negative, 'text_segment'):
            text = most_negative.text_segment
            score = most_negative.score
        else:
            text = most_negative.get('text_segment', '')
            score = most_negative.get('score', 0)
        print(f"   😞 Most Negative: \"{text[:60]}...\" (Score: {score:.2f})")


def demonstrate_topic_clustering(results: Dict[str, Any]):
    """Demonstrate topic clustering"""
    print_section("Topic Clustering")
    
    topics = results.get('topic_clusters', [])
    
    if not topics:
        print("ℹ️ No topic clusters identified")
        return
    
    print(f"🏷️ Identified {len(topics)} topic clusters:")
    
    for i, topic in enumerate(topics, 1):
        # Handle both dict and TopicCluster object
        if hasattr(topic, 'name'):
            name = topic.name
            confidence = topic.confidence
            keywords = topic.keywords
            segments_count = len(topic.segments)
        else:
            name = topic.get('name', f'Topic {i}')
            confidence = topic.get('confidence', 0)
            keywords = topic.get('keywords', [])
            segments_count = len(topic.get('segments', []))
        
        print(f"\n   {i}. {name}")
        print(f"      📊 Confidence: {confidence:.3f}")
        print(f"      🔑 Keywords: {', '.join(keywords[:5])}")
        print(f"      📝 Segments: {segments_count}")
        
        if hasattr(topic, 'summary'):
            summary = topic.summary
        else:
            summary = topic.get('summary', '')
        if summary:
            print(f"      📋 Summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")


def demonstrate_meeting_minutes(results: Dict[str, Any]):
    """Demonstrate meeting minutes generation"""
    print_section("Meeting Minutes")
    
    meeting_minutes = results.get('meeting_minutes')
    
    if not meeting_minutes:
        print("ℹ️ Meeting minutes not available (only generated for meeting-type content)")
        return
    
    # Handle both dict and MeetingMinutes object
    if hasattr(meeting_minutes, 'title'):
        title = meeting_minutes.title
        date = meeting_minutes.date
        duration = meeting_minutes.duration
        participants = meeting_minutes.participants
        summary = meeting_minutes.summary
        agenda_items = meeting_minutes.agenda_items
        decisions = meeting_minutes.key_decisions
        next_steps = meeting_minutes.next_steps
    else:
        title = meeting_minutes.get('title', 'Meeting Minutes')
        date = meeting_minutes.get('date', 'Unknown')
        duration = meeting_minutes.get('duration', 0)
        participants = meeting_minutes.get('participants', [])
        summary = meeting_minutes.get('summary', '')
        agenda_items = meeting_minutes.get('agenda_items', [])
        decisions = meeting_minutes.get('key_decisions', [])
        next_steps = meeting_minutes.get('next_steps', [])
    
    print(f"📅 {title}")
    print(f"📆 Date: {date}")
    print(f"⏱️ Duration: {duration:.1f} seconds")
    
    if participants:
        print(f"👥 Participants: {', '.join(participants)}")
    
    # Summary
    if summary:
        print(f"\n📋 Summary:")
        print(f"   {summary}")
    
    # Agenda items
    if agenda_items:
        print(f"\n📋 Agenda Items:")
        for i, item in enumerate(agenda_items, 1):
            print(f"   {i}. {item}")
    
    # Key decisions
    if decisions:
        print(f"\n✅ Key Decisions:")
        for i, decision in enumerate(decisions, 1):
            print(f"   {i}. {decision}")
    
    # Next steps
    if next_steps:
        print(f"\n➡️ Next Steps:")
        for i, step in enumerate(next_steps, 1):
            print(f"   {i}. {step}")


def demonstrate_content_categorization(results: Dict[str, Any]):
    """Demonstrate content categorization"""
    print_section("Content Categorization")
    
    categories = results.get('content_categories', {})
    
    if not categories:
        print("ℹ️ No content categorization available")
        return
    
    print("🏷️ Content Classification:")
    print(f"   📝 Discussion Type: {categories.get('discussion_type', 'Unknown').title()}")
    print(f"   🎭 Formality Level: {categories.get('formality_level', 'Unknown').title()}")
    print(f"   🔧 Technical Level: {categories.get('technical_level', 'Unknown').title()}")
    print(f"   😊 Emotional Tone: {categories.get('emotional_tone', 'Unknown').title()}")
    
    themes = categories.get('content_themes', [])
    if themes:
        print(f"   🎯 Main Themes: {', '.join(themes)}")


def demonstrate_key_insights(results: Dict[str, Any]):
    """Demonstrate key insights extraction"""
    print_section("Key Insights")
    
    insights = results.get('key_insights', {})
    
    if not insights:
        print("ℹ️ No key insights available")
        return
    
    insight_categories = {
        'summary_insights': '📋 Summary Insights',
        'action_insights': '✅ Action Insights',
        'sentiment_insights': '📈 Sentiment Insights',
        'topic_insights': '🏷️ Topic Insights'
    }
    
    for category, title in insight_categories.items():
        insight_list = insights.get(category, [])
        if insight_list:
            print(f"\n{title}:")
            for insight in insight_list:
                print(f"   • {insight}")


def demonstrate_export_functionality(results: Dict[str, Any]):
    """Demonstrate export functionality"""
    print_section("Export Functionality")
    
    # Create export directory
    export_dir = "ai_insights_exports"
    os.makedirs(export_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Export full results as JSON
    json_filename = f"{export_dir}/ai_insights_{timestamp}.json"
    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"📄 Full results exported to: {json_filename}")
    
    # Export action items as CSV-like format
    action_items = results.get('action_items', [])
    if action_items:
        csv_filename = f"{export_dir}/action_items_{timestamp}.txt"
        with open(csv_filename, 'w') as f:
            f.write("Action Item,Assignee,Priority,Due Date,Confidence,Timestamp\n")
            for item in action_items:
                # Handle both dict and ActionItem object
                if hasattr(item, 'text'):
                    text = item.text
                    assignee = item.assignee or 'Unassigned'
                    priority = item.priority.value if hasattr(item.priority, 'value') else str(item.priority)
                    due_date = item.due_date or 'Not specified'
                    confidence = item.confidence
                    timestamp = item.timestamp
                else:
                    text = item.get('text', '')
                    assignee = item.get('assignee', 'Unassigned')
                    priority = item.get('priority', 'medium')
                    due_date = item.get('due_date', 'Not specified')
                    confidence = item.get('confidence', 0)
                    timestamp = item.get('timestamp', 0)
                
                f.write(f"\"{text}\",")
                f.write(f"{assignee},")
                f.write(f"{priority},")
                f.write(f"{due_date},")
                f.write(f"{confidence:.3f},")
                f.write(f"{timestamp:.1f}\n")
        print(f"✅ Action items exported to: {csv_filename}")
    
    # Export meeting minutes as text
    meeting_minutes = results.get('meeting_minutes')
    if meeting_minutes:
        minutes_filename = f"{export_dir}/meeting_minutes_{timestamp}.txt"
        with open(minutes_filename, 'w') as f:
            f.write(f"MEETING MINUTES\n")
            f.write(f"{'='*50}\n")
            if hasattr(meeting_minutes, 'title'):
                f.write(f"Title: {meeting_minutes.title}\n")
                f.write(f"Date: {meeting_minutes.date}\n")
                f.write(f"Duration: {meeting_minutes.duration:.1f} seconds\n\n")
            else:
                f.write(f"Title: {meeting_minutes.get('title', 'Meeting')}\n")
                f.write(f"Date: {meeting_minutes.get('date', 'Unknown')}\n")
                f.write(f"Duration: {meeting_minutes.get('duration', 0):.1f} seconds\n\n")
            
            if hasattr(meeting_minutes, 'summary'):
                summary = meeting_minutes.summary
                agenda_items = meeting_minutes.agenda_items
                decisions = meeting_minutes.key_decisions
            else:
                summary = meeting_minutes.get('summary', '')
                agenda_items = meeting_minutes.get('agenda_items', [])
                decisions = meeting_minutes.get('key_decisions', [])
            
            if summary:
                f.write(f"SUMMARY\n{'-'*20}\n{summary}\n\n")
            
            if agenda_items:
                f.write(f"AGENDA ITEMS\n{'-'*20}\n")
                for i, item in enumerate(agenda_items, 1):
                    f.write(f"{i}. {item}\n")
                f.write("\n")
            
            if decisions:
                f.write(f"KEY DECISIONS\n{'-'*20}\n")
                for i, decision in enumerate(decisions, 1):
                    f.write(f"{i}. {decision}\n")
                f.write("\n")
        
        print(f"📝 Meeting minutes exported to: {minutes_filename}")


def run_comprehensive_demo():
    """Run a comprehensive demonstration of all AI content insights features"""
    print_header("AI-Powered Content Insights Demo")
    print("This demo showcases Task 31: AI-powered content insights functionality")
    print("Features demonstrated:")
    print("• Automatic meeting minutes generation")
    print("• Action item extraction and task identification") 
    print("• Sentiment analysis timeline")
    print("• Topic clustering and content categorization")
    print("• Automatic summary generation with key highlights")
    
    # Initialize analyzer
    print("\n🔧 Initializing AI Content Insights analyzer...")
    analyzer = AIContentInsights()
    
    # Check for OpenAI API key
    if analyzer.openai_api_key:
        print("✅ OpenAI API key found - enhanced analysis enabled")
    else:
        print("⚠️ OpenAI API key not found - using basic analysis")
    
    # Demo 1: Meeting Analysis
    print_header("Demo 1: Meeting Analysis")
    meeting_transcript = create_sample_meeting_transcript()
    
    results = demonstrate_basic_analysis(analyzer, meeting_transcript, ContentType.MEETING)
    
    if results:
        demonstrate_summary_generation(results)
        demonstrate_action_items(results)
        demonstrate_sentiment_analysis(results)
        demonstrate_topic_clustering(results)
        demonstrate_meeting_minutes(results)
        demonstrate_content_categorization(results)
        demonstrate_key_insights(results)
        demonstrate_export_functionality(results)
    
    # Demo 2: Interview Analysis
    print_header("Demo 2: Interview Analysis")
    interview_transcript = create_sample_interview_transcript()
    
    results = demonstrate_basic_analysis(analyzer, interview_transcript, ContentType.INTERVIEW)
    
    if results:
        demonstrate_summary_generation(results)
        demonstrate_sentiment_analysis(results)
        demonstrate_topic_clustering(results)
        demonstrate_content_categorization(results)
    
    print_header("Demo Complete")
    print("✅ All AI content insights features have been demonstrated!")
    print("📁 Check the 'ai_insights_exports' directory for exported files")
    print("\n🚀 Ready for production use!")


def run_interactive_demo():
    """Run an interactive demo where users can input their own transcript"""
    print_header("Interactive AI Content Insights Demo")
    
    analyzer = AIContentInsights()
    
    print("📁 Please provide a transcript file path or use sample data:")
    print("1. Use sample meeting transcript")
    print("2. Use sample interview transcript")
    print("3. Provide custom transcript file path")
    
    choice = input("\nEnter your choice (1-3): ").strip()
    
    if choice == "1":
        transcript_data = create_sample_meeting_transcript()
        content_type = ContentType.MEETING
        print("✅ Using sample meeting transcript")
    elif choice == "2":
        transcript_data = create_sample_interview_transcript()
        content_type = ContentType.INTERVIEW
        print("✅ Using sample interview transcript")
    elif choice == "3":
        file_path = input("Enter transcript file path (JSON format): ").strip()
        try:
            with open(file_path, 'r') as f:
                transcript_data = json.load(f)
            
            print("Select content type:")
            print("1. Meeting")
            print("2. Interview")
            print("3. Lecture")
            print("4. Presentation")
            
            type_choice = input("Enter choice (1-4): ").strip()
            content_types = {
                "1": ContentType.MEETING,
                "2": ContentType.INTERVIEW,
                "3": ContentType.LECTURE,
                "4": ContentType.PRESENTATION
            }
            content_type = content_types.get(type_choice, ContentType.MEETING)
            
            print(f"✅ Loaded transcript from {file_path}")
        except Exception as e:
            print(f"❌ Error loading file: {e}")
            return
    else:
        print("❌ Invalid choice")
        return
    
    # Perform analysis
    results = demonstrate_basic_analysis(analyzer, transcript_data, content_type)
    
    if not results:
        return
    
    # Interactive feature selection
    while True:
        print("\n" + "="*60)
        print("Select analysis to view:")
        print("1. Summary")
        print("2. Action Items")
        print("3. Sentiment Analysis")
        print("4. Topic Clustering")
        print("5. Meeting Minutes (if applicable)")
        print("6. Content Categorization")
        print("7. Key Insights")
        print("8. Export Results")
        print("9. View All")
        print("0. Exit")
        
        choice = input("\nEnter your choice (0-9): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            demonstrate_summary_generation(results)
        elif choice == "2":
            demonstrate_action_items(results)
        elif choice == "3":
            demonstrate_sentiment_analysis(results)
        elif choice == "4":
            demonstrate_topic_clustering(results)
        elif choice == "5":
            demonstrate_meeting_minutes(results)
        elif choice == "6":
            demonstrate_content_categorization(results)
        elif choice == "7":
            demonstrate_key_insights(results)
        elif choice == "8":
            demonstrate_export_functionality(results)
        elif choice == "9":
            demonstrate_summary_generation(results)
            demonstrate_action_items(results)
            demonstrate_sentiment_analysis(results)
            demonstrate_topic_clustering(results)
            demonstrate_meeting_minutes(results)
            demonstrate_content_categorization(results)
            demonstrate_key_insights(results)
        else:
            print("❌ Invalid choice")
    
    print("\n👋 Thank you for using AI Content Insights!")


def main():
    """Main function"""
    print("🧠 AI-Powered Content Insights Demo")
    print("Choose demo mode:")
    print("1. Comprehensive Demo (automated)")
    print("2. Interactive Demo (user-controlled)")
    
    choice = input("\nEnter your choice (1-2): ").strip()
    
    if choice == "1":
        run_comprehensive_demo()
    elif choice == "2":
        run_interactive_demo()
    else:
        print("❌ Invalid choice. Running comprehensive demo...")
        run_comprehensive_demo()


if __name__ == "__main__":
    main()