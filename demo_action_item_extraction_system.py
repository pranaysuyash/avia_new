#!/usr/bin/env python3
"""
Demo script for Action Item Extraction and Assignment System
Showcases advanced action item extraction, deadline parsing, and assignee identification
"""

import sys
import os
from datetime import datetime, timedelta
import json

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from action_item_extraction_system import (
    extract_action_items_from_meeting,
    create_action_item_extractor,
    ActionItemPriority,
    ActionItemStatus,
    DeadlineType
)

from meeting_element_identification import analyze_meeting_transcript

def print_separator(title="", char="=", width=80):
    """Print a formatted separator"""
    if title:
        title_line = f" {title} "
        padding = (width - len(title_line)) // 2
        print(char * padding + title_line + char * padding)
    else:
        print(char * width)

def print_action_item(action, index):
    """Print a formatted action item"""
    priority_icons = {
        ActionItemPriority.CRITICAL: "🔴",
        ActionItemPriority.HIGH: "🟠",
        ActionItemPriority.MEDIUM: "🟡",
        ActionItemPriority.LOW: "🟢",
        ActionItemPriority.UNSPECIFIED: "⚪"
    }
    
    confidence_icon = "🟢" if action.confidence >= 0.75 else "🟡" if action.confidence >= 0.5 else "🔴"
    priority_icon = priority_icons.get(action.priority, "⚪")
    
    print(f"\n{index}. {action.content}")
    print(f"   {priority_icon} Priority: {action.priority.value.title()}")
    print(f"   {confidence_icon} Confidence: {action.confidence:.2f} ({action.confidence_level.value.replace('_', ' ').title()})")
    
    if action.assignees:
        assignee_names = []
        for assignee in action.assignees:
            name_with_confidence = f"{assignee.name} ({assignee.confidence:.2f})"
            if assignee.role:
                name_with_confidence += f" - {assignee.role}"
            assignee_names.append(name_with_confidence)
        print(f"   👤 Assignees: {', '.join(assignee_names)}")
    
    if action.deadline:
        deadline_icon = "⏰"
        if action.deadline.parsed_date:
            date_str = action.deadline.parsed_date.strftime('%Y-%m-%d')
            days_until = action.deadline.days_until_deadline()
            if days_until is not None:
                if days_until < 0:
                    deadline_icon = "🚨"
                    date_str += f" (OVERDUE by {abs(days_until)} days)"
                elif days_until <= 1:
                    deadline_icon = "⚡"
                    date_str += f" (Due in {days_until} day{'s' if days_until != 1 else ''})"
                else:
                    date_str += f" (Due in {days_until} days)"
            print(f"   {deadline_icon} Deadline: {date_str} - \"{action.deadline.original_text}\"")
        else:
            print(f"   {deadline_icon} Deadline: {action.deadline.original_text}")
    
    if action.tags:
        print(f"   🏷️  Tags: {', '.join(action.tags)}")
    
    extraction_method = action.context.get('extraction_method', 'unknown')
    method_icon = "🎯" if extraction_method == 'explicit' else "🔍"
    print(f"   {method_icon} Method: {extraction_method.title()}")
    
    if action.dependencies:
        print(f"   🔗 Dependencies: {len(action.dependencies)} items")

def demo_basic_action_extraction():
    """Demo basic action item extraction"""
    print_separator("DEMO 1: Basic Action Item Extraction", "=")
    
    transcript = """
[14:00] Project Manager: Welcome to our weekly project review meeting.
[14:02] Project Manager: Let's start with our action items from last week.
[14:05] Developer: I completed the user authentication module as planned.
[14:07] Project Manager: Excellent. Now for this week's tasks.
[14:10] Project Manager: John, can you implement the dashboard by next Wednesday?
[14:11] John: Sure, I'll have the dashboard ready by Wednesday morning.
[14:13] Project Manager: Sarah, please review the API documentation by tomorrow.
[14:14] Sarah: Will do. I'll complete the review by end of day tomorrow.
[14:16] Project Manager: Action item for Mike - update the deployment scripts by Friday.
[14:17] Mike: Got it. I'll prioritize the deployment script updates.
[14:19] Project Manager: These are all high priority for our next release.
[14:20] Project Manager: Any questions before we wrap up?
[14:21] Project Manager: Great. Meeting adjourned.
    """
    
    context = {
        'meeting_id': 'weekly_review_2024',
        'title': 'Weekly Project Review',
        'date': datetime(2024, 1, 15, 14, 0),
        'speaker_roles': {
            'Project Manager': 'Project Manager',
            'Developer': 'Senior Developer',
            'John': 'Frontend Developer',
            'Sarah': 'Technical Writer',
            'Mike': 'DevOps Engineer'
        }
    }
    
    print("📝 Analyzing meeting transcript for action items...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    print(f"\n📊 Meeting Overview:")
    print(f"  Meeting: {meeting.title}")
    print(f"  Attendees: {', '.join(meeting.attendees)}")
    print(f"  Total Action Items Extracted: {len(action_items)}")
    
    print(f"\n🎯 Extracted Action Items:")
    for i, action in enumerate(action_items, 1):
        print_action_item(action, i)
    
    # Statistics
    extractor = create_action_item_extractor()
    stats = extractor.get_action_item_statistics(action_items)
    
    print(f"\n📈 Statistics:")
    print(f"  Total Actions: {stats['total_actions']}")
    print(f"  With Assignees: {stats['with_assignees']}")
    print(f"  With Deadlines: {stats['with_deadlines']}")
    print(f"  Average Confidence: {stats['average_confidence']:.2f}")
    print(f"  Overdue Count: {stats['overdue_count']}")
    
    if stats['by_priority']:
        print(f"\n📊 By Priority:")
        for priority, count in stats['by_priority'].items():
            print(f"    {priority.title()}: {count}")
    
    if stats['by_extraction_method']:
        print(f"\n🔍 By Extraction Method:")
        for method, count in stats['by_extraction_method'].items():
            print(f"    {method.title()}: {count}")

def demo_complex_deadline_parsing():
    """Demo complex deadline parsing scenarios"""
    print_separator("DEMO 2: Advanced Deadline Parsing", "=")
    
    transcript = """
[10:00] Manager: Let's discuss our upcoming deadlines.
[10:02] Manager: Alice, can you finish the user research by next Friday?
[10:03] Alice: I'll have the research completed by Friday, March 15th.
[10:05] Manager: Bob, please submit the budget proposal by 03/20/2024.
[10:06] Bob: The budget will be ready by March 20th.
[10:08] Manager: Carol, we need the security audit within 5 days.
[10:09] Carol: I'll complete the audit within the next 5 days.
[10:11] Manager: David, can you prepare the presentation by tomorrow?
[10:12] David: I'll have the presentation ready by tomorrow morning.
[10:14] Manager: Eve, please review the contracts by end of this week.
[10:15] Eve: I'll finish the contract review by end of week.
[10:17] Manager: Finally, Frank, update the documentation by our next meeting.
[10:18] Frank: I'll have the docs updated before our next meeting.
[10:20] Manager: These deadlines are critical for our Q1 goals.
    """
    
    context = {
        'meeting_id': 'deadline_planning_2024',
        'title': 'Deadline Planning Meeting',
        'date': datetime(2024, 3, 10, 10, 0)  # Set to March 10, 2024
    }
    
    print("📅 Analyzing various deadline formats...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    print(f"\n⏰ Deadline Analysis Results:")
    
    deadline_types = {
        DeadlineType.SPECIFIC_DATE: "📅 Specific Dates",
        DeadlineType.RELATIVE_TIME: "⏱️  Relative Time",
        DeadlineType.MEETING_BASED: "🤝 Meeting-Based",
        DeadlineType.UNSPECIFIED: "❓ Unspecified"
    }
    
    for deadline_type, type_name in deadline_types.items():
        type_actions = [a for a in action_items if a.deadline and a.deadline.deadline_type == deadline_type]
        if type_actions:
            print(f"\n{type_name} ({len(type_actions)} items):")
            for action in type_actions:
                deadline = action.deadline
                assignee_names = [a.name for a in action.assignees] if action.assignees else ["Unassigned"]
                
                print(f"  • {action.content[:50]}{'...' if len(action.content) > 50 else ''}")
                print(f"    Assignee: {', '.join(assignee_names)}")
                print(f"    Original: \"{deadline.original_text}\"")
                
                if deadline.parsed_date:
                    days_until = deadline.days_until_deadline()
                    status = ""
                    if days_until is not None:
                        if days_until < 0:
                            status = f" (OVERDUE by {abs(days_until)} days)"
                        elif days_until == 0:
                            status = " (DUE TODAY)"
                        elif days_until == 1:
                            status = " (DUE TOMORROW)"
                        else:
                            status = f" (Due in {days_until} days)"
                    
                    print(f"    Parsed: {deadline.parsed_date.strftime('%Y-%m-%d')}{status}")
                
                print(f"    Confidence: {deadline.confidence:.2f}")

def demo_assignee_extraction():
    """Demo assignee extraction and role inference"""
    print_separator("DEMO 3: Advanced Assignee Extraction", "=")
    
    transcript = """
[11:00] CEO: Welcome to our executive planning session.
[11:02] CEO: We have several critical initiatives to assign.
[11:05] CEO: John Smith, our CTO, will oversee the technical architecture review.
[11:07] John Smith: I'll coordinate with the engineering team for the architecture review.
[11:10] CEO: Sarah Johnson, can you handle the marketing campaign launch?
[11:11] Sarah Johnson: Absolutely. I'll manage the campaign rollout.
[11:13] CEO: Action item for Mike Davis, our CFO - prepare the quarterly financial report.
[11:15] Mike Davis: I'll have the financial analysis ready by next week.
[11:17] CEO: Lisa Chen is responsible for coordinating with external vendors.
[11:18] Lisa Chen: I'll reach out to all vendors this week.
[11:20] CEO: Bob Wilson should review the legal compliance requirements.
[11:21] Bob Wilson: I'll conduct a thorough compliance review.
[11:23] CEO: Finally, Alice Brown owns the customer feedback analysis.
[11:24] Alice Brown: I'll analyze all customer feedback from last quarter.
[11:26] CEO: These assignments are critical for our Q2 planning.
    """
    
    context = {
        'meeting_id': 'executive_planning_2024',
        'title': 'Executive Planning Session',
        'date': datetime(2024, 1, 20, 11, 0),
        'attendees': [
            {'name': 'John Smith', 'role': 'CTO'},
            {'name': 'Sarah Johnson', 'role': 'CMO'},
            {'name': 'Mike Davis', 'role': 'CFO'},
            {'name': 'Lisa Chen', 'role': 'Operations Manager'},
            {'name': 'Bob Wilson', 'role': 'Legal Counsel'},
            {'name': 'Alice Brown', 'role': 'Customer Success Manager'}
        ]
    }
    
    print("👥 Analyzing assignee extraction and role inference...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    print(f"\n👤 Assignee Analysis Results:")
    
    assignment_methods = {
        'explicit': "🎯 Explicit Assignments",
        'implicit': "🔍 Implicit Assignments",
        'inferred': "🤔 Inferred Assignments"
    }
    
    for method, method_name in assignment_methods.items():
        method_actions = [
            a for a in action_items 
            if any(assignee.assignment_method == method for assignee in a.assignees)
        ]
        
        if method_actions:
            print(f"\n{method_name} ({len(method_actions)} items):")
            for action in method_actions:
                print(f"  • {action.content[:60]}{'...' if len(action.content) > 60 else ''}")
                
                for assignee in action.assignees:
                    if assignee.assignment_method == method:
                        role_info = f" ({assignee.role})" if assignee.role else ""
                        confidence_icon = "🟢" if assignee.confidence >= 0.8 else "🟡" if assignee.confidence >= 0.6 else "🔴"
                        print(f"    {confidence_icon} {assignee.name}{role_info} - Confidence: {assignee.confidence:.2f}")
    
    # Role distribution
    all_roles = []
    for action in action_items:
        for assignee in action.assignees:
            if assignee.role:
                all_roles.append(assignee.role)
    
    if all_roles:
        from collections import Counter
        role_counts = Counter(all_roles)
        print(f"\n🏢 Role Distribution:")
        for role, count in role_counts.most_common():
            print(f"  {role}: {count} action{'s' if count != 1 else ''}")

def demo_priority_classification():
    """Demo priority classification based on various signals"""
    print_separator("DEMO 4: Priority Classification", "=")
    
    transcript = """
[13:00] Director: We need to prioritize our tasks for the product launch.
[13:02] Director: First, the security vulnerability fix is urgent and critical.
[13:04] Developer: I'll patch the security issue immediately.
[13:06] Director: The user interface improvements are high priority for user experience.
[13:08] Designer: I'll focus on the UI enhancements this week.
[13:10] Director: Documentation updates would be nice to have when possible.
[13:12] Writer: I'll work on the docs when I have time.
[13:14] Director: The performance optimization is important but not blocking.
[13:16] Engineer: I'll optimize performance after the critical fixes.
[13:18] Director: Finally, the analytics dashboard is low priority for now.
[13:20] Analyst: I'll add the dashboard to the backlog.
[13:22] Director: Remember, anything due tomorrow is automatically high priority.
[13:24] Director: The client demo is scheduled for tomorrow, so prep is critical.
[13:26] Manager: I'll ensure the demo environment is ready by tomorrow morning.
    """
    
    context = {
        'meeting_id': 'priority_planning_2024',
        'title': 'Priority Planning Meeting',
        'date': datetime(2024, 1, 25, 13, 0),
        'speaker_roles': {
            'Director': 'Product Director',
            'Developer': 'Senior Developer',
            'Designer': 'UX Designer',
            'Writer': 'Technical Writer',
            'Engineer': 'Performance Engineer',
            'Analyst': 'Data Analyst',
            'Manager': 'Project Manager'
        }
    }
    
    print("🎯 Analyzing priority classification signals...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    print(f"\n📊 Priority Classification Results:")
    
    priority_groups = {}
    for priority in ActionItemPriority:
        priority_actions = [a for a in action_items if a.priority == priority]
        if priority_actions:
            priority_groups[priority] = priority_actions
    
    priority_icons = {
        ActionItemPriority.CRITICAL: "🔴 CRITICAL",
        ActionItemPriority.HIGH: "🟠 HIGH",
        ActionItemPriority.MEDIUM: "🟡 MEDIUM",
        ActionItemPriority.LOW: "🟢 LOW",
        ActionItemPriority.UNSPECIFIED: "⚪ UNSPECIFIED"
    }
    
    for priority in [ActionItemPriority.CRITICAL, ActionItemPriority.HIGH, 
                     ActionItemPriority.MEDIUM, ActionItemPriority.LOW, 
                     ActionItemPriority.UNSPECIFIED]:
        if priority in priority_groups:
            actions = priority_groups[priority]
            print(f"\n{priority_icons[priority]} ({len(actions)} items):")
            
            for action in actions:
                assignee_names = [a.name for a in action.assignees] if action.assignees else ["Unassigned"]
                deadline_info = ""
                if action.deadline:
                    if action.deadline.parsed_date:
                        days_until = action.deadline.days_until_deadline()
                        if days_until is not None and days_until <= 1:
                            deadline_info = " ⚡ (Due soon)"
                    else:
                        deadline_info = f" ⏰ ({action.deadline.original_text})"
                
                print(f"  • {action.content[:50]}{'...' if len(action.content) > 50 else ''}")
                print(f"    Assignee: {', '.join(assignee_names)}{deadline_info}")
                
                # Show priority reasoning
                priority_signals = []
                content_lower = action.content.lower()
                
                if any(word in content_lower for word in ['urgent', 'critical', 'immediately']):
                    priority_signals.append("urgent keywords")
                if any(word in content_lower for word in ['high priority', 'important']):
                    priority_signals.append("priority keywords")
                if action.deadline and action.deadline.days_until_deadline() is not None:
                    days = action.deadline.days_until_deadline()
                    if days <= 1:
                        priority_signals.append("urgent deadline")
                
                speaker_role = context.get('speaker_roles', {}).get(action.source_element.speaker if action.source_element else '', '')
                if any(role in speaker_role.lower() for role in ['director', 'ceo', 'manager']):
                    priority_signals.append("executive request")
                
                if priority_signals:
                    print(f"    Signals: {', '.join(priority_signals)}")

def demo_json_export():
    """Demo JSON export of action items"""
    print_separator("DEMO 5: Action Items JSON Export", "=")
    
    transcript = """
[15:00] Scrum Master: Sprint planning meeting - let's assign our tasks.
[15:02] Scrum Master: Alice, implement the user profile feature by next Friday.
[15:03] Alice: I'll complete the user profiles by Friday. High priority understood.
[15:05] Scrum Master: Bob, can you set up the CI/CD pipeline by Wednesday?
[15:06] Bob: Sure, I'll have the pipeline configured by Wednesday morning.
[15:08] Scrum Master: Action item for Carol - write integration tests by Thursday.
[15:09] Carol: I'll write comprehensive tests by Thursday afternoon.
[15:11] Scrum Master: David, please update the API documentation by end of week.
[15:12] David: Documentation will be updated by Friday evening.
[15:14] Scrum Master: These are all critical for our sprint demo next Monday.
    """
    
    context = {
        'meeting_id': 'sprint_planning_2024_01_30',
        'title': 'Sprint Planning Meeting',
        'date': datetime(2024, 1, 30, 15, 0),
        'speaker_roles': {
            'Scrum Master': 'Scrum Master',
            'Alice': 'Frontend Developer',
            'Bob': 'DevOps Engineer',
            'Carol': 'QA Engineer',
            'David': 'Technical Writer'
        }
    }
    
    print("📄 Generating comprehensive JSON export...")
    meeting = analyze_meeting_transcript(transcript, context)
    action_items = extract_action_items_from_meeting(meeting, context)
    
    # Create comprehensive export data
    export_data = {
        'meeting_info': {
            'id': meeting.meeting_id,
            'title': meeting.title,
            'date': meeting.date.isoformat() if meeting.date else None,
            'attendees': meeting.attendees,
            'total_elements': len(meeting.elements)
        },
        'action_items_summary': {
            'total_count': len(action_items),
            'with_assignees': len([a for a in action_items if a.assignees]),
            'with_deadlines': len([a for a in action_items if a.deadline]),
            'by_priority': {},
            'by_status': {},
            'overdue_count': len([a for a in action_items if a.is_overdue()])
        },
        'action_items': []
    }
    
    # Count by priority and status
    for action in action_items:
        priority_key = action.priority.value
        status_key = action.status.value
        
        export_data['action_items_summary']['by_priority'][priority_key] = \
            export_data['action_items_summary']['by_priority'].get(priority_key, 0) + 1
        export_data['action_items_summary']['by_status'][status_key] = \
            export_data['action_items_summary']['by_status'].get(status_key, 0) + 1
    
    # Export individual action items
    for action in action_items:
        action_data = {
            'id': action.id,
            'content': action.content,
            'priority': action.priority.value,
            'status': action.status.value,
            'confidence': round(action.confidence, 3),
            'confidence_level': action.confidence_level.value,
            'created_at': action.created_at.isoformat(),
            'updated_at': action.updated_at.isoformat(),
            'assignees': [],
            'deadline': None,
            'tags': action.tags,
            'dependencies': action.dependencies,
            'context': {
                'extraction_method': action.context.get('extraction_method'),
                'speaker': action.context.get('speaker'),
                'timestamp': action.context.get('timestamp')
            }
        }
        
        # Add assignees
        for assignee in action.assignees:
            assignee_data = {
                'name': assignee.name,
                'role': assignee.role,
                'confidence': round(assignee.confidence, 3),
                'assignment_method': assignee.assignment_method
            }
            action_data['assignees'].append(assignee_data)
        
        # Add deadline
        if action.deadline:
            deadline_data = {
                'type': action.deadline.deadline_type.value,
                'original_text': action.deadline.original_text,
                'parsed_date': action.deadline.parsed_date.isoformat() if action.deadline.parsed_date else None,
                'relative_days': action.deadline.relative_days,
                'confidence': round(action.deadline.confidence, 3),
                'is_overdue': action.deadline.is_overdue(),
                'days_until': action.deadline.days_until_deadline()
            }
            action_data['deadline'] = deadline_data
        
        export_data['action_items'].append(action_data)
    
    print("📋 Action Items JSON Export:")
    print(json.dumps(export_data, indent=2, default=str))

def main():
    """Run all demos"""
    print_separator("ACTION ITEM EXTRACTION AND ASSIGNMENT SYSTEM DEMO", "=")
    print("🤖 Advanced extraction of action items with assignees, deadlines, and priorities")
    print("📝 Supports explicit and implicit action identification from meeting transcripts")
    print()
    
    try:
        demo_basic_action_extraction()
        print("\n" + "="*80 + "\n")
        
        demo_complex_deadline_parsing()
        print("\n" + "="*80 + "\n")
        
        demo_assignee_extraction()
        print("\n" + "="*80 + "\n")
        
        demo_priority_classification()
        print("\n" + "="*80 + "\n")
        
        demo_json_export()
        
        print_separator("DEMO COMPLETED SUCCESSFULLY", "=")
        print("✅ All demos completed successfully!")
        print("🚀 The Action Item Extraction and Assignment System is ready for use!")
        print("\n🎯 Key Features Demonstrated:")
        print("  • Intelligent action item detection (explicit and implicit)")
        print("  • Advanced deadline parsing (specific dates, relative time, meeting-based)")
        print("  • Smart assignee extraction with role inference")
        print("  • Priority classification based on multiple signals")
        print("  • Comprehensive JSON export for integration")
        
    except Exception as e:
        print(f"❌ Error during demo: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()