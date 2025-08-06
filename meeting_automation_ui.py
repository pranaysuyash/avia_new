#!/usr/bin/env python3
"""
Meeting Automation System UI (Task 64)
Streamlit interface for automated meeting processing, summary generation,
and integration with various tools
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
import tempfile
from typing import Dict, List, Optional, Any
import pandas as pd

from meeting_automation_system import (
    MeetingAutomationSystem, MeetingMinutes, MeetingType,
    TaskPriority, ActionItem, Attendee, Decision
)

# Page configuration
st.set_page_config(
    page_title="Meeting Automation System",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 1rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }
    .meeting-card {
        background: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .action-item {
        background: #fff5e6;
        border-left: 4px solid #ff9800;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .decision-item {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 10px;
        margin: 5px 0;
        border-radius: 4px;
    }
    .attendee-chip {
        display: inline-block;
        background: #e3f2fd;
        padding: 5px 10px;
        border-radius: 15px;
        margin: 2px;
        font-size: 0.9em;
    }
    .priority-urgent {
        border-left-color: #f44336;
        background: #ffebee;
    }
    .priority-high {
        border-left-color: #ff9800;
    }
    .priority-medium {
        border-left-color: #2196f3;
        background: #e3f2fd;
    }
    .priority-low {
        border-left-color: #9e9e9e;
        background: #f5f5f5;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'meeting_system' not in st.session_state:
    st.session_state.meeting_system = MeetingAutomationSystem()
if 'processed_meetings' not in st.session_state:
    st.session_state.processed_meetings = []
if 'current_transcript' not in st.session_state:
    st.session_state.current_transcript = None
if 'integration_settings' not in st.session_state:
    st.session_state.integration_settings = {
        'email': {'enabled': False, 'recipients': []},
        'calendar': {'enabled': False, 'type': 'google'},
        'jira': {'enabled': False, 'project_key': 'PROJ'},
        'asana': {'enabled': False, 'workspace_id': ''},
        'trello': {'enabled': False, 'board_id': ''},
        'slack': {'enabled': False, 'channel': '#general'},
        'teams': {'enabled': False}
    }

def main():
    st.title("📋 Meeting Automation System")
    st.markdown("Automatically process meeting recordings, generate summaries, and integrate with your tools")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Integration settings
        with st.expander("📧 Email Integration", expanded=False):
            st.session_state.integration_settings['email']['enabled'] = st.checkbox(
                "Enable email summaries",
                value=st.session_state.integration_settings['email']['enabled']
            )
            if st.session_state.integration_settings['email']['enabled']:
                recipients = st.text_area(
                    "Recipients (one per line)",
                    value='\n'.join(st.session_state.integration_settings['email']['recipients'])
                )
                st.session_state.integration_settings['email']['recipients'] = [
                    r.strip() for r in recipients.split('\n') if r.strip()
                ]
        
        with st.expander("📅 Calendar Integration", expanded=False):
            st.session_state.integration_settings['calendar']['enabled'] = st.checkbox(
                "Create follow-up events",
                value=st.session_state.integration_settings['calendar']['enabled']
            )
            if st.session_state.integration_settings['calendar']['enabled']:
                st.session_state.integration_settings['calendar']['type'] = st.radio(
                    "Calendar type",
                    ["google", "outlook"],
                    index=0 if st.session_state.integration_settings['calendar']['type'] == 'google' else 1
                )
        
        with st.expander("🎯 Project Management", expanded=False):
            # Jira
            st.session_state.integration_settings['jira']['enabled'] = st.checkbox(
                "Enable Jira integration",
                value=st.session_state.integration_settings['jira']['enabled']
            )
            if st.session_state.integration_settings['jira']['enabled']:
                st.session_state.integration_settings['jira']['project_key'] = st.text_input(
                    "Jira project key",
                    value=st.session_state.integration_settings['jira']['project_key']
                )
            
            # Asana
            st.session_state.integration_settings['asana']['enabled'] = st.checkbox(
                "Enable Asana integration",
                value=st.session_state.integration_settings['asana']['enabled']
            )
            
            # Trello
            st.session_state.integration_settings['trello']['enabled'] = st.checkbox(
                "Enable Trello integration",
                value=st.session_state.integration_settings['trello']['enabled']
            )
        
        with st.expander("💬 Collaboration Tools", expanded=False):
            # Slack
            st.session_state.integration_settings['slack']['enabled'] = st.checkbox(
                "Share to Slack",
                value=st.session_state.integration_settings['slack']['enabled']
            )
            if st.session_state.integration_settings['slack']['enabled']:
                st.session_state.integration_settings['slack']['channel'] = st.text_input(
                    "Slack channel",
                    value=st.session_state.integration_settings['slack']['channel']
                )
            
            # Teams
            st.session_state.integration_settings['teams']['enabled'] = st.checkbox(
                "Share to Microsoft Teams",
                value=st.session_state.integration_settings['teams']['enabled']
            )
    
    # Main content
    tabs = st.tabs(["🎙️ Process Meeting", "📊 Meeting History", "📋 Templates", "🔧 Configuration"])
    
    with tabs[0]:
        process_meeting_tab()
    
    with tabs[1]:
        meeting_history_tab()
    
    with tabs[2]:
        templates_tab()
    
    with tabs[3]:
        configuration_tab()

def process_meeting_tab():
    """Tab for processing new meetings"""
    st.header("Process New Meeting")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Meeting input options
        input_method = st.radio(
            "Input Method",
            ["Upload Transcript", "Paste Text", "Use Sample"],
            horizontal=True
        )
        
        transcript_data = None
        metadata = {}
        
        if input_method == "Upload Transcript":
            uploaded_file = st.file_uploader(
                "Upload transcript file",
                type=['json', 'txt', 'vtt', 'srt'],
                help="Upload a transcript file in JSON, TXT, VTT, or SRT format"
            )
            
            if uploaded_file:
                content = uploaded_file.read().decode('utf-8')
                
                if uploaded_file.name.endswith('.json'):
                    try:
                        transcript_data = json.loads(content)
                    except:
                        st.error("Invalid JSON format")
                else:
                    # Convert text to transcript format
                    lines = content.strip().split('\n')
                    segments = []
                    for i, line in enumerate(lines):
                        if line.strip():
                            segments.append({
                                'text': line.strip(),
                                'speaker': 'Speaker',
                                'start': i * 5,
                                'end': (i + 1) * 5
                            })
                    transcript_data = {'segments': segments}
        
        elif input_method == "Paste Text":
            meeting_text = st.text_area(
                "Paste meeting transcript",
                height=300,
                placeholder="Paste your meeting transcript here..."
            )
            
            if meeting_text:
                lines = meeting_text.strip().split('\n')
                segments = []
                for i, line in enumerate(lines):
                    if line.strip():
                        # Simple speaker detection
                        if ':' in line:
                            parts = line.split(':', 1)
                            speaker = parts[0].strip()
                            text = parts[1].strip()
                        else:
                            speaker = 'Speaker'
                            text = line.strip()
                        
                        segments.append({
                            'text': text,
                            'speaker': speaker,
                            'start': i * 5,
                            'end': (i + 1) * 5
                        })
                transcript_data = {'segments': segments}
        
        else:  # Use Sample
            if st.button("Load Sample Meeting"):
                transcript_data = generate_sample_transcript()
                st.success("Sample meeting loaded!")
        
        # Meeting metadata
        with st.expander("Meeting Details", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                meeting_title = st.text_input(
                    "Meeting Title",
                    placeholder="e.g., Sprint Planning Meeting"
                )
                metadata['title'] = meeting_title
            
            with col2:
                meeting_type = st.selectbox(
                    "Meeting Type",
                    [t.value for t in MeetingType],
                    format_func=lambda x: x.replace('_', ' ').title()
                )
                metadata['meeting_type'] = meeting_type
            
            with col3:
                recording_url = st.text_input(
                    "Recording URL (optional)",
                    placeholder="https://..."
                )
                if recording_url:
                    metadata['recording_url'] = recording_url
        
        # Process button
        if st.button("🚀 Process Meeting", type="primary", disabled=transcript_data is None):
            process_meeting(transcript_data, metadata)
    
    with col2:
        # Quick actions
        st.subheader("Quick Actions")
        
        if st.session_state.current_transcript:
            st.markdown("**Current Meeting:**")
            st.info(st.session_state.current_transcript.get('title', 'Untitled Meeting'))
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📧 Send Email", use_container_width=True):
                    send_email_summary()
                
                if st.button("🎯 Create Tasks", use_container_width=True):
                    create_project_tasks()
            
            with col2:
                if st.button("📅 Schedule Follow-up", use_container_width=True):
                    schedule_follow_up()
                
                if st.button("💬 Share to Slack", use_container_width=True):
                    share_to_collaboration()
        
        # Integration status
        st.subheader("Integration Status")
        integrations = [
            ("Email", st.session_state.integration_settings['email']['enabled'], "📧"),
            ("Calendar", st.session_state.integration_settings['calendar']['enabled'], "📅"),
            ("Jira", st.session_state.integration_settings['jira']['enabled'], "🎯"),
            ("Slack", st.session_state.integration_settings['slack']['enabled'], "💬"),
            ("Teams", st.session_state.integration_settings['teams']['enabled'], "💼")
        ]
        
        for name, enabled, icon in integrations:
            if enabled:
                st.success(f"{icon} {name} ✓")
            else:
                st.info(f"{icon} {name} ✗")

def process_meeting(transcript_data: Dict[str, Any], metadata: Dict[str, Any]):
    """Process the meeting transcript"""
    with st.spinner("🔄 Processing meeting..."):
        try:
            # Prepare options based on integration settings
            options = {
                'send_email': st.session_state.integration_settings['email']['enabled'],
                'email_recipients': st.session_state.integration_settings['email']['recipients'],
                'create_calendar_event': st.session_state.integration_settings['calendar']['enabled'],
                'calendar_type': st.session_state.integration_settings['calendar']['type'],
                'create_tasks': any([
                    st.session_state.integration_settings['jira']['enabled'],
                    st.session_state.integration_settings['asana']['enabled'],
                    st.session_state.integration_settings['trello']['enabled']
                ]),
                'share_to_collaboration': any([
                    st.session_state.integration_settings['slack']['enabled'],
                    st.session_state.integration_settings['teams']['enabled']
                ])
            }
            
            # Determine PM platform
            if st.session_state.integration_settings['jira']['enabled']:
                options['pm_platform'] = 'jira'
            elif st.session_state.integration_settings['asana']['enabled']:
                options['pm_platform'] = 'asana'
            elif st.session_state.integration_settings['trello']['enabled']:
                options['pm_platform'] = 'trello'
            
            # Determine collaboration platform
            if st.session_state.integration_settings['slack']['enabled']:
                options['collab_platform'] = 'slack'
                options['collab_channel'] = st.session_state.integration_settings['slack']['channel']
            elif st.session_state.integration_settings['teams']['enabled']:
                options['collab_platform'] = 'teams'
            
            # Process the meeting
            results = st.session_state.meeting_system.process_meeting(
                transcript_data,
                metadata,
                options
            )
            
            if results['status'] == 'success':
                st.success("✅ Meeting processed successfully!")
                
                # Store results
                st.session_state.current_transcript = results['meeting_minutes']
                st.session_state.processed_meetings.append({
                    'timestamp': datetime.now(),
                    'results': results
                })
                
                # Display summary
                display_meeting_summary(results)
                
                # Show integration results
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    if results['email_sent']:
                        st.success("📧 Email sent")
                    elif options['send_email']:
                        st.warning("📧 Email failed")
                
                with col2:
                    if results['calendar_event']:
                        st.success("📅 Event created")
                    elif options['create_calendar_event']:
                        st.warning("📅 Event failed")
                
                with col3:
                    if results['tasks_created']:
                        st.success(f"🎯 {len(results['tasks_created'])} tasks created")
                    elif options['create_tasks']:
                        st.warning("🎯 Task creation failed")
                
                with col4:
                    if results['collaboration_shared']:
                        st.success("💬 Shared")
                    elif options['share_to_collaboration']:
                        st.warning("💬 Sharing failed")
            
            else:
                st.error(f"❌ Processing failed: {', '.join(results['errors'])}")
                
        except Exception as e:
            st.error(f"Error processing meeting: {str(e)}")

def display_meeting_summary(results: Dict[str, Any]):
    """Display the processed meeting summary"""
    if not results.get('meeting_minutes'):
        return
    
    minutes_data = results['meeting_minutes']
    
    # Create meeting minutes object
    minutes = MeetingMinutes(
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
    
    # Display summary
    st.markdown("### 📋 Meeting Summary")
    
    # Basic info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Duration", f"{minutes.duration / 60:.1f} min")
    with col2:
        st.metric("Attendees", len(minutes.attendees))
    with col3:
        st.metric("Action Items", len(minutes.action_items))
    with col4:
        st.metric("Decisions", len(minutes.decisions))
    
    # Attendees
    if minutes.attendees:
        st.markdown("### 👥 Attendees")
        attendees_html = ""
        for attendee in minutes.attendees:
            attendees_html += f'<span class="attendee-chip">{attendee.name}</span>'
        st.markdown(attendees_html, unsafe_allow_html=True)
    
    # Key Decisions
    if minutes.decisions:
        st.markdown("### ✅ Key Decisions")
        for decision in minutes.decisions[:3]:  # Show top 3
            st.markdown(
                f'<div class="decision-item">'
                f'<strong>{decision.description}</strong><br>'
                f'<small>Decided by: {decision.made_by}</small>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Action Items
    if minutes.action_items:
        st.markdown("### 📌 Action Items")
        for item in minutes.action_items[:5]:  # Show top 5
            priority_class = f"priority-{item.priority.value}"
            due_date = f" | Due: {item.due_date.strftime('%B %d')}" if item.due_date else ""
            st.markdown(
                f'<div class="action-item {priority_class}">'
                f'<strong>{item.description}</strong><br>'
                f'<small>Assigned to: {item.assignee} | Priority: {item.priority.value.upper()}{due_date}</small>'
                f'</div>',
                unsafe_allow_html=True
            )
    
    # Key Insights
    if minutes.key_insights:
        st.markdown("### 💡 Key Insights")
        for insight in minutes.key_insights:
            st.write(f"- {insight}")
    
    # Export options
    st.markdown("### 📤 Export Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📄 Download HTML Report"):
            html_report = st.session_state.meeting_system.generate_meeting_report(minutes, "html")
            st.download_button(
                "Download HTML",
                html_report,
                f"meeting_report_{minutes.meeting_id}.html",
                "text/html"
            )
    
    with col2:
        if st.button("📝 Download Markdown"):
            md_report = st.session_state.meeting_system.generate_meeting_report(minutes, "markdown")
            st.download_button(
                "Download Markdown",
                md_report,
                f"meeting_report_{minutes.meeting_id}.md",
                "text/markdown"
            )
    
    with col3:
        if st.button("📊 Download JSON"):
            st.download_button(
                "Download JSON",
                json.dumps(minutes_data, indent=2),
                f"meeting_data_{minutes.meeting_id}.json",
                "application/json"
            )

def meeting_history_tab():
    """Tab for viewing meeting history"""
    st.header("Meeting History")
    
    if not st.session_state.processed_meetings:
        st.info("No meetings processed yet. Go to 'Process Meeting' tab to get started.")
        return
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        date_filter = st.date_input(
            "Filter by date",
            value=None,
            max_value=datetime.now().date()
        )
    
    with col2:
        type_filter = st.selectbox(
            "Filter by type",
            ["All"] + [t.value for t in MeetingType],
            format_func=lambda x: x.replace('_', ' ').title() if x != "All" else x
        )
    
    with col3:
        search_query = st.text_input(
            "Search meetings",
            placeholder="Search by title or content..."
        )
    
    # Display meetings
    filtered_meetings = st.session_state.processed_meetings
    
    # Apply filters
    if date_filter:
        filtered_meetings = [
            m for m in filtered_meetings
            if m['timestamp'].date() == date_filter
        ]
    
    if type_filter != "All":
        filtered_meetings = [
            m for m in filtered_meetings
            if m['results']['meeting_minutes']['meeting_type'] == type_filter
        ]
    
    if search_query:
        filtered_meetings = [
            m for m in filtered_meetings
            if search_query.lower() in m['results']['meeting_minutes']['title'].lower()
        ]
    
    # Display filtered meetings
    for meeting_record in reversed(filtered_meetings):
        meeting = meeting_record['results']['meeting_minutes']
        timestamp = meeting_record['timestamp']
        
        with st.expander(
            f"📋 {meeting['title']} - {timestamp.strftime('%B %d, %Y at %I:%M %p')}",
            expanded=False
        ):
            # Meeting details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Type:** {meeting['meeting_type'].replace('_', ' ').title()}")
                st.write(f"**Duration:** {meeting['duration'] / 60:.1f} minutes")
            
            with col2:
                st.write(f"**Attendees:** {len(meeting['attendees'])}")
                st.write(f"**Action Items:** {len(meeting['action_items'])}")
            
            with col3:
                st.write(f"**Decisions:** {len(meeting['decisions'])}")
                st.write(f"**Insights:** {len(meeting['key_insights'])}")
            
            # Re-export options
            st.markdown("---")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button(f"📧 Resend Email", key=f"email_{meeting['meeting_id']}"):
                    # Resend email logic
                    st.info("Email resent!")
            
            with col2:
                if st.button(f"📄 View Report", key=f"report_{meeting['meeting_id']}"):
                    # Show report in modal
                    st.info("Opening report...")
            
            with col3:
                if st.button(f"🗑️ Delete", key=f"delete_{meeting['meeting_id']}"):
                    # Delete meeting
                    st.session_state.processed_meetings.remove(meeting_record)
                    st.rerun()

def templates_tab():
    """Tab for meeting templates"""
    st.header("Meeting Templates")
    
    # Predefined templates
    templates = {
        "Sprint Planning": {
            "agenda": [
                "Review previous sprint",
                "Discuss sprint goals",
                "Review backlog items",
                "Estimate story points",
                "Assign tasks",
                "Set sprint timeline"
            ],
            "type": MeetingType.PLANNING
        },
        "Daily Standup": {
            "agenda": [
                "What did you complete yesterday?",
                "What will you work on today?",
                "Are there any blockers?"
            ],
            "type": MeetingType.STANDUP
        },
        "Retrospective": {
            "agenda": [
                "What went well?",
                "What could be improved?",
                "Action items for next sprint"
            ],
            "type": MeetingType.RETROSPECTIVE
        },
        "Client Review": {
            "agenda": [
                "Project status update",
                "Demo of completed features",
                "Feedback collection",
                "Next steps discussion",
                "Timeline review"
            ],
            "type": MeetingType.CLIENT_MEETING
        }
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Available Templates")
        
        selected_template = st.radio(
            "Select a template",
            list(templates.keys())
        )
        
        if st.button("➕ Create Custom Template"):
            st.session_state.show_custom_template = True
    
    with col2:
        if selected_template:
            template = templates[selected_template]
            
            st.subheader(f"📋 {selected_template} Template")
            
            st.write(f"**Meeting Type:** {template['type'].value.replace('_', ' ').title()}")
            
            st.write("**Agenda Items:**")
            for i, item in enumerate(template['agenda'], 1):
                st.write(f"{i}. {item}")
            
            st.markdown("---")
            
            # Template actions
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📋 Copy to Clipboard", key=f"copy_{selected_template}"):
                    # In a real app, would use JavaScript to copy
                    st.info("Template copied to clipboard!")
            
            with col2:
                if st.button("🚀 Start Meeting with Template", key=f"start_{selected_template}"):
                    # Load template into process tab
                    st.info("Template loaded! Go to 'Process Meeting' tab.")
        
        # Custom template creation
        if hasattr(st.session_state, 'show_custom_template') and st.session_state.show_custom_template:
            st.subheader("Create Custom Template")
            
            template_name = st.text_input("Template Name")
            template_type = st.selectbox(
                "Meeting Type",
                [t.value for t in MeetingType],
                format_func=lambda x: x.replace('_', ' ').title()
            )
            
            agenda_items = st.text_area(
                "Agenda Items (one per line)",
                height=150
            )
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Save Template"):
                    if template_name and agenda_items:
                        # Save template logic
                        st.success(f"Template '{template_name}' saved!")
                        st.session_state.show_custom_template = False
            
            with col2:
                if st.button("❌ Cancel"):
                    st.session_state.show_custom_template = False

def configuration_tab():
    """Tab for system configuration"""
    st.header("System Configuration")
    
    # API Configuration
    with st.expander("🔑 API Configuration", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Email Settings")
            smtp_host = st.text_input("SMTP Host", value=os.getenv('SMTP_HOST', 'smtp.gmail.com'))
            smtp_port = st.number_input("SMTP Port", value=int(os.getenv('SMTP_PORT', '587')))
            smtp_username = st.text_input("SMTP Username", value=os.getenv('SMTP_USERNAME', ''))
            smtp_password = st.text_input("SMTP Password", type="password")
        
        with col2:
            st.subheader("Calendar Settings")
            google_calendar = st.checkbox("Enable Google Calendar", value=bool(os.getenv('GOOGLE_CALENDAR_CREDENTIALS')))
            outlook_calendar = st.checkbox("Enable Outlook Calendar", value=bool(os.getenv('OUTLOOK_CLIENT_ID')))
            
            if outlook_calendar:
                outlook_client_id = st.text_input("Outlook Client ID")
                outlook_tenant_id = st.text_input("Outlook Tenant ID")
    
    # Project Management Tools
    with st.expander("🎯 Project Management Integration", expanded=False):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Jira")
            jira_url = st.text_input("Jira URL", value=os.getenv('JIRA_URL', ''))
            jira_username = st.text_input("Jira Username")
            jira_api_token = st.text_input("Jira API Token", type="password")
        
        with col2:
            st.subheader("Asana")
            asana_token = st.text_input("Asana Access Token", type="password")
            asana_workspace = st.text_input("Asana Workspace ID")
        
        with col3:
            st.subheader("Trello")
            trello_key = st.text_input("Trello API Key")
            trello_token = st.text_input("Trello Token", type="password")
            trello_board = st.text_input("Trello Board ID")
    
    # Collaboration Tools
    with st.expander("💬 Collaboration Tools", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Slack")
            slack_webhook = st.text_input("Slack Webhook URL", type="password")
            slack_bot_token = st.text_input("Slack Bot Token", type="password")
        
        with col2:
            st.subheader("Microsoft Teams")
            teams_webhook = st.text_input("Teams Webhook URL", type="password")
    
    # Save configuration
    if st.button("💾 Save Configuration", type="primary"):
        # In a real app, would save to environment or config file
        st.success("Configuration saved successfully!")
    
    # Test connections
    st.markdown("---")
    st.subheader("Test Connections")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Test Email"):
            test_connection("email")
    
    with col2:
        if st.button("Test Calendar"):
            test_connection("calendar")
    
    with col3:
        if st.button("Test Jira"):
            test_connection("jira")
    
    with col4:
        if st.button("Test Slack"):
            test_connection("slack")

def generate_sample_transcript() -> Dict[str, Any]:
    """Generate a sample meeting transcript"""
    return {
        'segments': [
            {'text': "Good morning everyone, let's start our product planning meeting.", 'speaker': 'John Smith', 'start': 0, 'end': 4},
            {'text': "Today we need to discuss the Q2 roadmap and prioritize features.", 'speaker': 'John Smith', 'start': 4, 'end': 8},
            {'text': "I think we should focus on the mobile app improvements first.", 'speaker': 'Sarah Johnson', 'start': 8, 'end': 12},
            {'text': "The customer feedback shows that's our biggest pain point.", 'speaker': 'Sarah Johnson', 'start': 12, 'end': 16},
            {'text': "Agreed. I'll take ownership of the mobile app redesign.", 'speaker': 'Mike Wilson', 'start': 16, 'end': 20},
            {'text': "We need to have the designs ready by end of next week.", 'speaker': 'John Smith', 'start': 20, 'end': 24},
            {'text': "I'll create the Jira tickets for the mobile app work.", 'speaker': 'Mike Wilson', 'start': 24, 'end': 28},
            {'text': "We've decided to postpone the analytics dashboard to Q3.", 'speaker': 'John Smith', 'start': 28, 'end': 32},
            {'text': "Also, we need to follow up with the infrastructure team about scaling.", 'speaker': 'Sarah Johnson', 'start': 32, 'end': 36},
            {'text': "Let's schedule our next sync for Friday at 2 PM.", 'speaker': 'John Smith', 'start': 36, 'end': 40}
        ],
        'speakers': {
            'John Smith': 'John Smith',
            'Sarah Johnson': 'Sarah Johnson',
            'Mike Wilson': 'Mike Wilson'
        }
    }

def send_email_summary():
    """Send email summary of current meeting"""
    if st.session_state.current_transcript:
        st.info("Sending email summary...")
        # Implementation would call email integration
        st.success("Email sent successfully!")

def create_project_tasks():
    """Create project management tasks"""
    if st.session_state.current_transcript:
        st.info("Creating project tasks...")
        # Implementation would call PM integration
        st.success("Tasks created successfully!")

def schedule_follow_up():
    """Schedule follow-up meeting"""
    if st.session_state.current_transcript:
        st.info("Creating calendar event...")
        # Implementation would call calendar integration
        st.success("Follow-up meeting scheduled!")

def share_to_collaboration():
    """Share to collaboration platform"""
    if st.session_state.current_transcript:
        st.info("Sharing to collaboration platform...")
        # Implementation would call collaboration integration
        st.success("Meeting summary shared!")

def test_connection(service: str):
    """Test connection to a service"""
    with st.spinner(f"Testing {service} connection..."):
        # Simulate connection test
        import time
        time.sleep(1)
        
        # In real implementation, would actually test the connection
        if service in ["email", "calendar"]:
            st.success(f"✅ {service.capitalize()} connection successful!")
        else:
            st.warning(f"⚠️ {service.capitalize()} connection failed. Check configuration.")

if __name__ == "__main__":
    main()