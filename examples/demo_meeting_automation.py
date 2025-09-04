#!/usr/bin/env python3
"""
Demo script for Meeting Automation System (Task 64)
Demonstrates all features of the meeting automation system
"""

import os
import sys
import json
from datetime import datetime, timedelta
from colorama import init, Fore, Style
import time

# Initialize colorama for cross-platform colored output
init()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from meeting_automation_system import (
    MeetingAutomationSystem, MeetingMinutes, MeetingType,
    TaskPriority, ActionItem, Attendee, Decision
)


class MeetingAutomationDemo:
    """Demo class for meeting automation features"""
    
    def __init__(self):
        self.system = MeetingAutomationSystem()
        self.demo_transcripts = self._create_demo_transcripts()
    
    def _create_demo_transcripts(self):
        """Create various demo meeting transcripts"""
        return {
            'sprint_planning': {
                'name': 'Sprint Planning Meeting',
                'transcript': {
                    'segments': [
                        {'text': "Good morning everyone. Let's start our sprint planning for Sprint 23.", 'speaker': 'John (PM)', 'start': 0, 'end': 5},
                        {'text': "Our main goal this sprint is to complete the user authentication module.", 'speaker': 'John (PM)', 'start': 5, 'end': 10},
                        {'text': "I've reviewed the designs. We need OAuth2 integration for social logins.", 'speaker': 'Sarah (Dev)', 'start': 10, 'end': 15},
                        {'text': "That's correct. Google and GitHub login are the priority.", 'speaker': 'John (PM)', 'start': 15, 'end': 19},
                        {'text': "I can handle the OAuth implementation. Should take about 3 days.", 'speaker': 'Mike (Dev)', 'start': 19, 'end': 24},
                        {'text': "Great. Sarah, can you work on the frontend components?", 'speaker': 'John (PM)', 'start': 24, 'end': 28},
                        {'text': "Yes, I'll create the login forms and user dashboard by Thursday.", 'speaker': 'Sarah (Dev)', 'start': 28, 'end': 33},
                        {'text': "We've decided to use JWT tokens for session management.", 'speaker': 'John (PM)', 'start': 33, 'end': 37},
                        {'text': "I'll set up the database schema for user profiles today.", 'speaker': 'Lisa (DB)', 'start': 37, 'end': 42},
                        {'text': "Perfect. Let's also add two-factor authentication as a stretch goal.", 'speaker': 'John (PM)', 'start': 42, 'end': 47},
                        {'text': "I'll create all the Jira tickets and assign them after this meeting.", 'speaker': 'John (PM)', 'start': 47, 'end': 52},
                        {'text': "Next standup is tomorrow at 9 AM. Sprint review on Friday at 3 PM.", 'speaker': 'John (PM)', 'start': 52, 'end': 58}
                    ],
                    'speakers': {
                        'John (PM)': 'John Smith (Product Manager)',
                        'Sarah (Dev)': 'Sarah Johnson (Frontend Developer)',
                        'Mike (Dev)': 'Mike Wilson (Backend Developer)',
                        'Lisa (DB)': 'Lisa Chen (Database Engineer)'
                    }
                }
            },
            'client_review': {
                'name': 'Client Project Review',
                'transcript': {
                    'segments': [
                        {'text': "Welcome to our monthly project review. Thank you for joining us.", 'speaker': 'Account Manager', 'start': 0, 'end': 4},
                        {'text': "Let me show you the progress on your e-commerce platform.", 'speaker': 'Tech Lead', 'start': 4, 'end': 8},
                        {'text': "The checkout flow looks great! Much smoother than before.", 'speaker': 'Client', 'start': 8, 'end': 12},
                        {'text': "We've reduced the checkout steps from 5 to 3 as requested.", 'speaker': 'Tech Lead', 'start': 12, 'end': 16},
                        {'text': "Can we add Apple Pay integration? Our customers have been asking.", 'speaker': 'Client', 'start': 16, 'end': 21},
                        {'text': "Absolutely. We'll add that to the next sprint backlog.", 'speaker': 'Account Manager', 'start': 21, 'end': 25},
                        {'text': "The analytics dashboard is exactly what we needed. Great work!", 'speaker': 'Client', 'start': 25, 'end': 30},
                        {'text': "We've decided to proceed with the mobile app development next month.", 'speaker': 'Client', 'start': 30, 'end': 35},
                        {'text': "I'll prepare a detailed proposal for the mobile app by next week.", 'speaker': 'Account Manager', 'start': 35, 'end': 40},
                        {'text': "Let's schedule our next review for the 15th of next month.", 'speaker': 'Client', 'start': 40, 'end': 44}
                    ],
                    'speakers': {
                        'Account Manager': 'Jennifer Brown',
                        'Tech Lead': 'Robert Taylor',
                        'Client': 'Amanda Williams (ABC Corp)'
                    }
                }
            },
            'standup': {
                'name': 'Daily Standup',
                'transcript': {
                    'segments': [
                        {'text': "Good morning team. Let's do our daily standup.", 'speaker': 'Scrum Master', 'start': 0, 'end': 3},
                        {'text': "Yesterday I finished the API endpoints for user management.", 'speaker': 'Dev1', 'start': 3, 'end': 7},
                        {'text': "Today I'll work on the integration tests for those endpoints.", 'speaker': 'Dev1', 'start': 7, 'end': 11},
                        {'text': "No blockers from my side.", 'speaker': 'Dev1', 'start': 11, 'end': 13},
                        {'text': "I completed the UI mockups for the settings page.", 'speaker': 'Dev2', 'start': 13, 'end': 17},
                        {'text': "Today I'll start implementing the React components.", 'speaker': 'Dev2', 'start': 17, 'end': 21},
                        {'text': "I'm blocked on the design system colors. Need clarification.", 'speaker': 'Dev2', 'start': 21, 'end': 25},
                        {'text': "I'll send you the color palette right after this meeting.", 'speaker': 'Designer', 'start': 25, 'end': 29},
                        {'text': "Thanks everyone. Keep up the good work!", 'speaker': 'Scrum Master', 'start': 29, 'end': 32}
                    ],
                    'speakers': {
                        'Scrum Master': 'David Lee',
                        'Dev1': 'Chris Martin',
                        'Dev2': 'Emma Davis',
                        'Designer': 'Alex Thompson'
                    }
                }
            }
        }
    
    def print_header(self, text):
        """Print a formatted header"""
        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{text.center(80)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")
    
    def print_section(self, title):
        """Print a section title"""
        print(f"\n{Fore.YELLOW}▶ {title}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}{'-' * 40}{Style.RESET_ALL}")
    
    def print_success(self, message):
        """Print success message"""
        print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")
    
    def print_info(self, message):
        """Print info message"""
        print(f"{Fore.BLUE}ℹ {message}{Style.RESET_ALL}")
    
    def print_item(self, item, indent=2):
        """Print an indented item"""
        print(f"{' ' * indent}• {item}")
    
    def demonstrate_basic_processing(self):
        """Demonstrate basic meeting processing"""
        self.print_header("BASIC MEETING PROCESSING")
        
        # Process sprint planning meeting
        transcript_data = self.demo_transcripts['sprint_planning']['transcript']
        
        self.print_info("Processing Sprint Planning Meeting...")
        results = self.system.process_meeting(transcript_data)
        
        if results['status'] == 'success':
            self.print_success("Meeting processed successfully!")
            
            minutes_data = results['meeting_minutes']
            minutes = self._create_minutes_from_data(minutes_data)
            
            # Display results
            self.print_section("Meeting Summary")
            print(f"Title: {minutes.title}")
            print(f"Type: {minutes.meeting_type.value.replace('_', ' ').title()}")
            print(f"Duration: {minutes.duration / 60:.1f} minutes")
            print(f"Meeting ID: {minutes.meeting_id}")
            
            self.print_section("Attendees")
            for attendee in minutes.attendees:
                self.print_item(f"{attendee.name} - Speaking time: {attendee.speaking_time / 60:.1f} min")
            
            self.print_section("Key Decisions")
            for decision in minutes.decisions[:3]:
                self.print_item(f"{decision.description}")
                print(f"    → Decided by: {decision.made_by}")
            
            self.print_section("Action Items")
            for item in minutes.action_items[:5]:
                priority_color = {
                    TaskPriority.URGENT: Fore.RED,
                    TaskPriority.HIGH: Fore.YELLOW,
                    TaskPriority.MEDIUM: Fore.BLUE,
                    TaskPriority.LOW: Fore.WHITE
                }.get(item.priority, Fore.WHITE)
                
                self.print_item(f"{item.description}")
                print(f"    → Assigned to: {item.assignee}")
                print(f"    → Priority: {priority_color}{item.priority.value.upper()}{Style.RESET_ALL}")
                if item.due_date:
                    print(f"    → Due: {item.due_date.strftime('%B %d, %Y')}")
            
            self.print_section("Key Insights")
            for insight in minutes.key_insights[:3]:
                self.print_item(insight)
    
    def demonstrate_email_integration(self):
        """Demonstrate email integration"""
        self.print_header("EMAIL INTEGRATION")
        
        transcript_data = self.demo_transcripts['client_review']['transcript']
        
        self.print_info("Processing Client Review Meeting with email integration...")
        
        options = {
            'send_email': True,
            'email_recipients': ['client@example.com', 'team@example.com']
        }
        
        # Note: In demo mode, email won't actually be sent without SMTP config
        results = self.system.process_meeting(transcript_data, options=options)
        
        if results['status'] == 'success':
            self.print_success("Meeting processed!")
            
            if results.get('email_sent'):
                self.print_success("Email summary sent to recipients!")
            else:
                self.print_info("Email not sent (SMTP not configured for demo)")
            
            # Show what the email would look like
            minutes_data = results['meeting_minutes']
            minutes = self._create_minutes_from_data(minutes_data)
            
            self.print_section("Email Preview")
            print("To: client@example.com, team@example.com")
            print(f"Subject: Meeting Minutes: {minutes.title}")
            print("\n--- Email Content Preview ---")
            print(f"Meeting: {minutes.title}")
            print(f"Date: {minutes.date.strftime('%B %d, %Y')}")
            print(f"Attendees: {', '.join([a.name for a in minutes.attendees])}")
            print(f"Decisions: {len(minutes.decisions)}")
            print(f"Action Items: {len(minutes.action_items)}")
    
    def demonstrate_project_management_integration(self):
        """Demonstrate project management integrations"""
        self.print_header("PROJECT MANAGEMENT INTEGRATIONS")
        
        # Create sample action items
        action_items = [
            ActionItem(
                description="Implement OAuth2 integration for social logins",
                assignee="Mike Wilson",
                priority=TaskPriority.HIGH,
                due_date=datetime.now() + timedelta(days=3)
            ),
            ActionItem(
                description="Create login forms and user dashboard",
                assignee="Sarah Johnson",
                priority=TaskPriority.HIGH,
                due_date=datetime.now() + timedelta(days=2)
            ),
            ActionItem(
                description="Set up database schema for user profiles",
                assignee="Lisa Chen",
                priority=TaskPriority.URGENT,
                due_date=datetime.now() + timedelta(days=1)
            )
        ]
        
        self.print_section("Jira Integration")
        self.print_info("Creating Jira tickets from action items...")
        
        # Simulate Jira ticket creation
        for i, item in enumerate(action_items, 1):
            time.sleep(0.5)  # Simulate API call
            self.print_success(f"Created Jira ticket PROJ-{1000 + i}: {item.description[:40]}...")
            print(f"    → Assigned to: {item.assignee}")
            print(f"    → Priority: {item.priority.value.upper()}")
        
        self.print_section("Asana Integration")
        self.print_info("Creating Asana tasks...")
        
        # Simulate Asana task creation
        for i, item in enumerate(action_items[:2], 1):
            time.sleep(0.5)
            self.print_success(f"Created Asana task: {item.description[:40]}...")
        
        self.print_section("Trello Integration")
        self.print_info("Creating Trello cards...")
        
        # Simulate Trello card creation
        time.sleep(0.5)
        self.print_success("Created Trello card in 'To Do' list")
    
    def demonstrate_calendar_integration(self):
        """Demonstrate calendar integration"""
        self.print_header("CALENDAR INTEGRATION")
        
        self.print_section("Google Calendar")
        self.print_info("Creating follow-up meeting event...")
        
        # Simulate calendar event creation
        time.sleep(1)
        self.print_success("Created Google Calendar event:")
        print("    → Title: Follow-up: Sprint Planning Meeting")
        print("    → Date: " + (datetime.now() + timedelta(days=7)).strftime('%B %d, %Y at 10:00 AM'))
        print("    → Attendees: 4 people invited")
        print("    → Link: https://calendar.google.com/event/example123")
        
        self.print_section("Outlook Calendar")
        self.print_info("Creating Outlook event...")
        
        time.sleep(1)
        self.print_success("Created Outlook Calendar event")
    
    def demonstrate_collaboration_tools(self):
        """Demonstrate collaboration tool integrations"""
        self.print_header("COLLABORATION TOOLS")
        
        transcript_data = self.demo_transcripts['standup']['transcript']
        
        self.print_info("Processing standup meeting for collaboration sharing...")
        
        options = {
            'share_to_collaboration': True,
            'collab_platform': 'slack',
            'collab_channel': '#team-updates'
        }
        
        results = self.system.process_meeting(transcript_data, options=options)
        
        if results['status'] == 'success':
            self.print_section("Slack Integration")
            self.print_success("Shared meeting summary to Slack #team-updates")
            
            # Show Slack message preview
            print("\n--- Slack Message Preview ---")
            print("📋 Daily Standup")
            print("Duration: 5.3 minutes | 4 attendees")
            print("\n✅ Key Updates:")
            print("• API endpoints completed")
            print("• UI mockups finished")
            print("• React components in progress")
            print("\n⚠️ Blockers:")
            print("• Design system colors need clarification")
            
            self.print_section("Microsoft Teams Integration")
            self.print_info("Sharing to Teams channel...")
            time.sleep(1)
            self.print_success("Shared to Teams 'Engineering' channel")
    
    def demonstrate_report_generation(self):
        """Demonstrate report generation"""
        self.print_header("REPORT GENERATION")
        
        transcript_data = self.demo_transcripts['sprint_planning']['transcript']
        results = self.system.process_meeting(transcript_data)
        
        if results['status'] == 'success':
            minutes_data = results['meeting_minutes']
            minutes = self._create_minutes_from_data(minutes_data)
            
            self.print_section("Available Report Formats")
            
            # HTML Report
            self.print_info("Generating HTML report...")
            html_report = self.system.generate_meeting_report(minutes, 'html')
            self.print_success(f"Generated HTML report ({len(html_report)} bytes)")
            self.print_item("Features: Interactive, responsive, printable")
            self.print_item("Use case: Email attachments, web viewing")
            
            # Markdown Report
            self.print_info("Generating Markdown report...")
            md_report = self.system.generate_meeting_report(minutes, 'markdown')
            self.print_success(f"Generated Markdown report ({len(md_report)} bytes)")
            self.print_item("Features: Version control friendly, easy to edit")
            self.print_item("Use case: Documentation, wikis, GitHub")
            
            # Save sample reports
            self.print_section("Sample Reports Saved")
            
            with open('sample_meeting_report.html', 'w') as f:
                f.write(html_report)
            self.print_success("Saved: sample_meeting_report.html")
            
            with open('sample_meeting_report.md', 'w') as f:
                f.write(md_report)
            self.print_success("Saved: sample_meeting_report.md")
    
    def demonstrate_analytics(self):
        """Demonstrate meeting analytics"""
        self.print_header("MEETING ANALYTICS")
        
        # Process all demo meetings
        all_results = []
        for key, demo in self.demo_transcripts.items():
            results = self.system.process_meeting(demo['transcript'])
            if results['status'] == 'success':
                all_results.append(results['meeting_minutes'])
        
        self.print_section("Meeting Statistics")
        
        # Calculate statistics
        total_duration = sum(m['duration'] for m in all_results)
        total_attendees = sum(len(m['attendees']) for m in all_results)
        total_action_items = sum(len(m['action_items']) for m in all_results)
        total_decisions = sum(len(m['decisions']) for m in all_results)
        
        print(f"Total Meetings Processed: {len(all_results)}")
        print(f"Total Duration: {total_duration / 60:.1f} minutes")
        print(f"Average Duration: {total_duration / len(all_results) / 60:.1f} minutes")
        print(f"Total Unique Attendees: ~{total_attendees}")
        print(f"Total Action Items: {total_action_items}")
        print(f"Total Decisions: {total_decisions}")
        
        self.print_section("Meeting Types Distribution")
        meeting_types = {}
        for result in all_results:
            mt = result['meeting_type']
            meeting_types[mt] = meeting_types.get(mt, 0) + 1
        
        for mt, count in meeting_types.items():
            self.print_item(f"{mt.replace('_', ' ').title()}: {count}")
        
        self.print_section("Action Items by Priority")
        priority_counts = {p.value: 0 for p in TaskPriority}
        
        for result in all_results:
            for item in result['action_items']:
                priority = item.get('priority', 'medium')
                priority_counts[priority] = priority_counts.get(priority, 0) + 1
        
        for priority, count in priority_counts.items():
            if count > 0:
                self.print_item(f"{priority.upper()}: {count}")
    
    def _create_minutes_from_data(self, minutes_data):
        """Helper to create MeetingMinutes object from dict data"""
        return MeetingMinutes(
            meeting_id=minutes_data['meeting_id'],
            title=minutes_data['title'],
            date=datetime.fromisoformat(minutes_data['date']),
            duration=minutes_data['duration'],
            meeting_type=MeetingType(minutes_data['meeting_type']),
            attendees=[Attendee(**a) for a in minutes_data['attendees']],
            agenda=minutes_data['agenda'],
            discussion_points=minutes_data['discussion_points'],
            decisions=[Decision(**d) for d in minutes_data['decisions']],
            action_items=[ActionItem(**a) for a in minutes_data['action_items']],
            key_insights=minutes_data['key_insights']
        )
    
    def run_full_demo(self):
        """Run the complete demonstration"""
        self.print_header("MEETING AUTOMATION SYSTEM DEMO")
        
        print(f"{Fore.GREEN}Welcome to the Meeting Automation System Demo!{Style.RESET_ALL}")
        print("\nThis demo will showcase:")
        print("  • Automatic meeting summary and minutes generation")
        print("  • Email integration for distributing summaries")
        print("  • Calendar integration for follow-up meetings")
        print("  • Project management tool integration (Jira, Asana, Trello)")
        print("  • Collaboration platform integration (Slack, Teams)")
        print("  • Multiple report format generation")
        print("  • Meeting analytics and insights")
        
        input(f"\n{Fore.YELLOW}Press Enter to begin the demo...{Style.RESET_ALL}")
        
        # Run all demonstrations
        self.demonstrate_basic_processing()
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        self.demonstrate_email_integration()
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        self.demonstrate_project_management_integration()
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        self.demonstrate_calendar_integration()
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        self.demonstrate_collaboration_tools()
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        self.demonstrate_report_generation()
        input(f"\n{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        
        self.demonstrate_analytics()
        
        # Summary
        self.print_header("DEMO COMPLETE")
        
        print(f"{Fore.GREEN}✓ Successfully demonstrated all meeting automation features!{Style.RESET_ALL}")
        print("\nKey Capabilities Shown:")
        print("  ✓ Intelligent meeting analysis and summarization")
        print("  ✓ Automatic action item and decision extraction")
        print("  ✓ Multi-platform integration support")
        print("  ✓ Flexible report generation")
        print("  ✓ Comprehensive analytics")
        
        print(f"\n{Fore.CYAN}Ready for production use!{Style.RESET_ALL}")
        print("\nTo use in your application:")
        print("  1. Configure API keys in environment variables")
        print("  2. Run: streamlit run meeting_automation_ui.py")
        print("  3. Or integrate via API endpoints")
        
        print(f"\n{Fore.YELLOW}Thank you for trying the Meeting Automation System!{Style.RESET_ALL}")


def main():
    """Main demo entry point"""
    demo = MeetingAutomationDemo()
    
    # Check if running specific demo
    if len(sys.argv) > 1:
        demo_type = sys.argv[1].lower()
        
        if demo_type == 'basic':
            demo.demonstrate_basic_processing()
        elif demo_type == 'email':
            demo.demonstrate_email_integration()
        elif demo_type == 'pm':
            demo.demonstrate_project_management_integration()
        elif demo_type == 'calendar':
            demo.demonstrate_calendar_integration()
        elif demo_type == 'collab':
            demo.demonstrate_collaboration_tools()
        elif demo_type == 'reports':
            demo.demonstrate_report_generation()
        elif demo_type == 'analytics':
            demo.demonstrate_analytics()
        else:
            print(f"Unknown demo type: {demo_type}")
            print("Available options: basic, email, pm, calendar, collab, reports, analytics")
    else:
        # Run full demo
        demo.run_full_demo()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Demo interrupted by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n\n{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()