#!/usr/bin/env python3
"""
Demo script for Meeting Element Identification Engine
Showcases the capabilities of automatically identifying meeting elements from transcripts
"""

import sys
import os
from datetime import datetime
import json

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from meeting_element_identification import (
    analyze_meeting_transcript,
    create_meeting_identifier,
    MeetingElementType,
    ConfidenceLevel
)

def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def print_elements_by_type(elements, element_type, type_name):
    """Print elements of a specific type"""
    type_elements = [e for e in elements if e.element_type == element_type]
    
    if not type_elements:
        print(f"  No {type_name.lower()} identified")
        return
    
    print(f"  {type_name} ({len(type_elements)}):")
    for i, element in enumerate(type_elements, 1):
        confidence_indicator = "🟢" if element.confidence >= 0.75 else "🟡" if element.confidence >= 0.5 else "🔴"
        speaker_info = f" [{element.speaker}]" if element.speaker else ""
        time_info = f" @{element.start_time:.0f}min" if element.start_time else ""
        
        print(f"    {i}. {element.content}")
        print(f"       {confidence_indicator} Confidence: {element.confidence:.2f}{speaker_info}{time_info}")

def demo_basic_meeting():
    """Demo with a basic meeting transcript"""
    print_separator("DEMO 1: Basic Team Meeting", "=")
    
    transcript = """
[14:00] John Smith: Welcome everyone to today's quarterly planning meeting.
[14:01] Sarah Johnson: Thank you John. I'm excited to discuss our Q4 goals.
[14:02] John Smith: Let's start with agenda item 1 - reviewing last quarter's performance.
[14:05] Mike Davis: The numbers look good. We exceeded our targets by 15%.
[14:07] Sarah Johnson: That's excellent news. I think we should celebrate this achievement.
[14:08] John Smith: Agreed. We've decided to have a team celebration next Friday.
[14:10] Lisa Chen: What about the budget for next quarter?
[14:12] John Smith: Good question. Mike, can you prepare the budget analysis by next Wednesday?
[14:13] Mike Davis: Absolutely. I'll have it ready by Wednesday morning.
[14:15] John Smith: Perfect. Any other questions before we move to the next item?
[14:16] Sarah Johnson: I have a concern about the timeline for the new product launch.
[14:18] John Smith: Let's discuss that. What's your concern?
[14:20] Sarah Johnson: I think we need more time for testing.
[14:22] Lisa Chen: I agree with Sarah. Quality is important.
[14:24] John Smith: Okay, we'll extend the timeline by two weeks. Final decision.
[14:26] John Smith: Action item for Lisa - please update the project timeline.
[14:28] Lisa Chen: Will do. I'll send the updated timeline to everyone by Friday.
[14:30] John Smith: Great. Let's wrap up. Follow up meeting next Monday at 2 PM.
[14:31] John Smith: Thank you everyone. Meeting adjourned.
    """
    
    context = {
        'meeting_id': 'quarterly_planning_2024',
        'title': 'Quarterly Planning Meeting',
        'date': datetime(2024, 1, 15, 14, 0)
    }
    
    print("📝 Analyzing meeting transcript...")
    meeting = analyze_meeting_transcript(transcript, context)
    
    print(f"\n📊 Meeting Overview:")
    print(f"  Meeting ID: {meeting.meeting_id}")
    print(f"  Title: {meeting.title}")
    print(f"  Date: {meeting.date.strftime('%Y-%m-%d %H:%M') if meeting.date else 'Not specified'}")
    print(f"  Attendees ({len(meeting.attendees)}): {', '.join(meeting.attendees)}")
    print(f"  Total Elements Identified: {len(meeting.elements)}")
    
    print(f"\n🎯 Identified Elements:")
    print_elements_by_type(meeting.elements, MeetingElementType.AGENDA_ITEM, "Agenda Items")
    print_elements_by_type(meeting.elements, MeetingElementType.DECISION, "Decisions")
    print_elements_by_type(meeting.elements, MeetingElementType.ACTION_ITEM, "Action Items")
    print_elements_by_type(meeting.elements, MeetingElementType.QUESTION, "Questions")
    print_elements_by_type(meeting.elements, MeetingElementType.AGREEMENT, "Agreements")
    print_elements_by_type(meeting.elements, MeetingElementType.FOLLOW_UP, "Follow-ups")
    
    # Statistics
    identifier = create_meeting_identifier()
    stats = identifier.get_element_statistics(meeting)
    
    print(f"\n📈 Statistics:")
    print(f"  Average Confidence: {stats['average_confidence']:.2f}")
    print(f"  High Confidence Elements (≥75%): {stats['high_confidence_count']}")
    print(f"  Elements with Speakers: {stats['elements_with_speakers']}")
    print(f"  Elements with Timestamps: {stats['elements_with_timestamps']}")
    
    print(f"\n📋 Confidence Distribution:")
    for level, count in stats['by_confidence_level'].items():
        if count > 0:
            print(f"  {level.replace('_', ' ').title()}: {count}")

def demo_complex_meeting():
    """Demo with a more complex meeting transcript"""
    print_separator("DEMO 2: Complex Board Meeting", "=")
    
    transcript = """
[10:00] Chairman Roberts: Good morning, board members. I call this meeting to order.
[10:01] Secretary Williams: All members are present. We have a quorum.
[10:02] Chairman Roberts: Thank you. First agenda item - approval of last meeting's minutes.
[10:03] Director Johnson: I move to approve the minutes as presented.
[10:04] Director Smith: I second the motion.
[10:05] Chairman Roberts: All in favor? Motion carries unanimously.
[10:06] Chairman Roberts: Next, we'll discuss the quarterly financial report.
[10:08] CFO Martinez: Revenue is up 12% compared to last quarter. However, expenses have also increased.
[10:10] Director Johnson: What's driving the expense increase?
[10:11] CFO Martinez: Primarily increased marketing spend and new hires in engineering.
[10:13] Director Brown: I'm concerned about the marketing ROI. Do we have metrics?
[10:15] CMO Davis: Yes, our customer acquisition cost is down 8%, so the spend is justified.
[10:17] Director Smith: That's encouraging. I support continued investment in marketing.
[10:19] Chairman Roberts: Any objections to the current marketing strategy?
[10:20] Director Brown: I still have reservations, but I won't block the decision.
[10:22] Chairman Roberts: Noted. We'll proceed with the current strategy but monitor closely.
[10:24] Chairman Roberts: Moving to agenda item 3 - the proposed merger with TechCorp.
[10:26] CEO Thompson: The due diligence is complete. I recommend we proceed with the acquisition.
[10:28] Director Johnson: What's the proposed timeline?
[10:29] CEO Thompson: We aim to close by end of Q2, pending regulatory approval.
[10:31] Director Smith: I have concerns about integration challenges.
[10:33] CTO Wilson: We've identified potential synergies worth $50M annually.
[10:35] Director Brown: The numbers look good, but cultural integration is always risky.
[10:37] Chairman Roberts: Valid concerns. Let's vote. All in favor of proceeding?
[10:38] Secretary Williams: Motion carries 4-1, with Director Brown dissenting.
[10:40] Chairman Roberts: Action item - CEO Thompson will finalize the merger agreement.
[10:41] CEO Thompson: I'll have the final terms ready for review by next Friday.
[10:43] Chairman Roberts: Excellent. Any other business?
[10:44] Director Johnson: Just a reminder - the annual shareholder meeting is next month.
[10:45] Secretary Williams: Invitations have been sent. We expect good attendance.
[10:46] Chairman Roberts: Perfect. Meeting adjourned. Thank you all.
    """
    
    context = {
        'meeting_id': 'board_meeting_q1_2024',
        'title': 'Quarterly Board Meeting',
        'date': datetime(2024, 3, 15, 10, 0)
    }
    
    print("📝 Analyzing complex board meeting transcript...")
    meeting = analyze_meeting_transcript(transcript, context)
    
    print(f"\n📊 Meeting Overview:")
    print(f"  Meeting ID: {meeting.meeting_id}")
    print(f"  Title: {meeting.title}")
    print(f"  Attendees ({len(meeting.attendees)}): {', '.join(meeting.attendees)}")
    print(f"  Total Elements Identified: {len(meeting.elements)}")
    
    print(f"\n🎯 Key Meeting Elements:")
    
    # Show high-confidence elements only for complex meetings
    high_conf_elements = meeting.get_high_confidence_elements(0.6)
    
    agenda_items = [e for e in high_conf_elements if e.element_type == MeetingElementType.AGENDA_ITEM]
    decisions = [e for e in high_conf_elements if e.element_type == MeetingElementType.DECISION]
    action_items = [e for e in high_conf_elements if e.element_type == MeetingElementType.ACTION_ITEM]
    questions = [e for e in high_conf_elements if e.element_type == MeetingElementType.QUESTION]
    objections = [e for e in high_conf_elements if e.element_type == MeetingElementType.OBJECTION]
    
    if agenda_items:
        print(f"\n  📋 Agenda Items ({len(agenda_items)}):")
        for i, item in enumerate(agenda_items, 1):
            print(f"    {i}. {item.content} (confidence: {item.confidence:.2f})")
    
    if decisions:
        print(f"\n  ✅ Decisions Made ({len(decisions)}):")
        for i, decision in enumerate(decisions, 1):
            print(f"    {i}. {decision.content} (confidence: {decision.confidence:.2f})")
    
    if action_items:
        print(f"\n  📝 Action Items ({len(action_items)}):")
        for i, action in enumerate(action_items, 1):
            speaker_info = f" - {action.speaker}" if action.speaker else ""
            print(f"    {i}. {action.content}{speaker_info} (confidence: {action.confidence:.2f})")
    
    if questions:
        print(f"\n  ❓ Key Questions ({len(questions)}):")
        for i, question in enumerate(questions, 1):
            print(f"    {i}. {question.content} (confidence: {question.confidence:.2f})")
    
    if objections:
        print(f"\n  ⚠️  Concerns/Objections ({len(objections)}):")
        for i, objection in enumerate(objections, 1):
            print(f"    {i}. {objection.content} (confidence: {objection.confidence:.2f})")

def demo_different_formats():
    """Demo with different transcript formats"""
    print_separator("DEMO 3: Different Transcript Formats", "=")
    
    formats = [
        {
            'name': 'Format 1: Timestamp + Speaker',
            'transcript': """
[09:00] Alice: Good morning team.
[09:01] Bob: Morning Alice. Ready for the sprint planning?
[09:02] Alice: Absolutely. Let's start with agenda item 1 - backlog review.
[09:05] Bob: I think we should prioritize the user authentication feature.
[09:07] Alice: Agreed. That's our decision for this sprint.
            """
        },
        {
            'name': 'Format 2: Speaker - Content',
            'transcript': """
Alice - Welcome to our daily standup meeting.
Bob - Thanks Alice. I completed the API integration yesterday.
Charlie - Great work Bob. I have a question about the database schema.
Alice - Let's discuss that. What's your concern Charlie?
Charlie - The new table structure might affect performance.
Alice - Good point. Bob, can you review the performance impact by tomorrow?
Bob - Sure, I'll analyze it and report back.
            """
        },
        {
            'name': 'Format 3: [Speaker] Content',
            'transcript': """
[Project Manager] Let's begin today's project review meeting.
[Developer 1] The frontend components are 80% complete.
[Developer 2] Backend APIs are ready for testing.
[QA Lead] I have concerns about the testing timeline.
[Project Manager] What's the issue with the timeline?
[QA Lead] We need at least two more days for comprehensive testing.
[Project Manager] Understood. We've decided to extend the testing phase by two days.
[Developer 1] That works for us. I'll adjust the deployment schedule.
            """
        }
    ]
    
    for i, format_demo in enumerate(formats, 1):
        print(f"\n{format_demo['name']}:")
        print("-" * 50)
        
        meeting = analyze_meeting_transcript(format_demo['transcript'])
        
        print(f"Attendees identified: {', '.join(meeting.attendees) if meeting.attendees else 'None'}")
        print(f"Elements found: {len(meeting.elements)}")
        
        if meeting.elements:
            print("Sample elements:")
            for element in meeting.elements[:3]:  # Show first 3 elements
                type_name = element.element_type.value.replace('_', ' ').title()
                print(f"  • {type_name}: {element.content[:50]}{'...' if len(element.content) > 50 else ''}")

def demo_confidence_analysis():
    """Demo confidence analysis and filtering"""
    print_separator("DEMO 4: Confidence Analysis", "=")
    
    transcript = """
John: Welcome everyone to the meeting.
Sarah: Let's discuss the budget proposal.
John: I think we should approve it.
Mike: But what about the risks?
Sarah: Good question Mike. We need to consider all factors.
John: After discussion, we've decided to approve the budget with conditions.
Sarah: Action item - Mike will prepare a risk assessment by Friday.
Mike: Absolutely, I'll have it ready.
John: Any other questions before we conclude?
Sarah: No questions from me.
John: Great, meeting adjourned.
    """
    
    meeting = analyze_meeting_transcript(transcript)
    
    print("📊 Confidence Level Analysis:")
    print("-" * 40)
    
    confidence_ranges = [
        (0.8, 1.0, "Very High (80-100%)", "🟢"),
        (0.6, 0.8, "High (60-80%)", "🟡"),
        (0.4, 0.6, "Medium (40-60%)", "🟠"),
        (0.2, 0.4, "Low (20-40%)", "🔴"),
        (0.0, 0.2, "Very Low (0-20%)", "⚫")
    ]
    
    for min_conf, max_conf, label, emoji in confidence_ranges:
        elements_in_range = [
            e for e in meeting.elements 
            if min_conf <= e.confidence < max_conf
        ]
        
        if elements_in_range:
            print(f"\n{emoji} {label} ({len(elements_in_range)} elements):")
            for element in elements_in_range:
                type_name = element.element_type.value.replace('_', ' ').title()
                print(f"  • {type_name}: {element.content} (confidence: {element.confidence:.2f})")
    
    # Show filtering by confidence
    print(f"\n🎯 High-Confidence Elements (≥60%):")
    high_conf = meeting.get_high_confidence_elements(0.6)
    if high_conf:
        for element in high_conf:
            type_name = element.element_type.value.replace('_', ' ').title()
            print(f"  • {type_name}: {element.content}")
    else:
        print("  No high-confidence elements found")

def demo_export_to_json():
    """Demo exporting meeting analysis to JSON"""
    print_separator("DEMO 5: Export to JSON", "=")
    
    transcript = """
[14:00] Manager: Welcome to our project kickoff meeting.
[14:02] Manager: First agenda item - project scope definition.
[14:05] Developer: The scope includes user authentication and dashboard.
[14:07] Designer: I have a question about the UI requirements.
[14:08] Manager: What's your question?
[14:09] Designer: Do we need mobile responsiveness?
[14:10] Manager: Yes, mobile support is required. That's decided.
[14:12] Manager: Action item - Designer will create mobile mockups by next week.
[14:13] Designer: I'll have them ready by Wednesday.
[14:15] Manager: Perfect. Any other questions?
[14:16] Developer: When is the target launch date?
[14:17] Manager: We're aiming for end of next month.
[14:18] Manager: Follow up meeting next Friday to review progress.
[14:19] Manager: Thank you everyone. Meeting concluded.
    """
    
    context = {
        'meeting_id': 'project_kickoff_2024',
        'title': 'Project Kickoff Meeting',
        'date': datetime(2024, 2, 1, 14, 0)
    }
    
    meeting = analyze_meeting_transcript(transcript, context)
    
    # Create JSON export
    meeting_data = {
        'meeting_info': {
            'id': meeting.meeting_id,
            'title': meeting.title,
            'date': meeting.date.isoformat() if meeting.date else None,
            'duration': meeting.duration,
            'attendees': meeting.attendees
        },
        'summary': {
            'total_elements': len(meeting.elements),
            'agenda_items': len(meeting.agenda_items),
            'decisions': len(meeting.decisions),
            'action_items': len(meeting.action_items),
            'questions': len([e for e in meeting.elements if e.element_type == MeetingElementType.QUESTION])
        },
        'elements': []
    }
    
    for element in meeting.elements:
        element_data = {
            'type': element.element_type.value,
            'content': element.content,
            'speaker': element.speaker,
            'confidence': round(element.confidence, 3),
            'confidence_level': element.confidence_level.value,
            'start_time': element.start_time,
            'context': element.context
        }
        meeting_data['elements'].append(element_data)
    
    print("📄 Meeting Analysis JSON Export:")
    print(json.dumps(meeting_data, indent=2, default=str))

def main():
    """Run all demos"""
    print_separator("MEETING ELEMENT IDENTIFICATION ENGINE DEMO", "=")
    print("🤖 Automatically identify and extract meeting elements from transcripts")
    print("📝 Supports: Agenda Items, Decisions, Action Items, Questions, and more!")
    print()
    
    try:
        demo_basic_meeting()
        print("\n" + "="*80 + "\n")
        
        demo_complex_meeting()
        print("\n" + "="*80 + "\n")
        
        demo_different_formats()
        print("\n" + "="*80 + "\n")
        
        demo_confidence_analysis()
        print("\n" + "="*80 + "\n")
        
        demo_export_to_json()
        
        print_separator("DEMO COMPLETED SUCCESSFULLY", "=")
        print("✅ All demos completed successfully!")
        print("🚀 The Meeting Element Identification Engine is ready for use!")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()