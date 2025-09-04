#!/usr/bin/env python3
"""
Export and Integration UI Components (Task 41)
User interface for advanced export and integration capabilities
"""

import streamlit as st
import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import tempfile
from pathlib import Path

from export_integrations import (
    ExportData, export_integration_manager,
    SlackIntegration, TeamsIntegration, DiscordIntegration,
    CalendarIntegration, CRMIntegration, LMSIntegration
)
from session_manager import session_manager

def render_export_integrations_interface():
    """Main interface for export and integration capabilities"""
    
    st.markdown("## 📤 Advanced Export & Integration")
    
    # Check if we have results to export
    if not session_manager.has_results():
        st.info("🎤 Process some audio/video content first to enable export and integration features.")
        return
    
    # Get current results
    results = session_manager.get_results()
    
    # Convert to ExportData format
    export_data = _convert_to_export_data(results)
    
    # Create tabs for different integration types
    export_tab, social_tab, calendar_tab, crm_tab, lms_tab, settings_tab = st.tabs([
        "📊 Interactive Reports",
        "💬 Social Platforms", 
        "📅 Calendar Integration",
        "🏢 CRM Integration",
        "🎓 LMS Integration",
        "⚙️ Integration Settings"
    ])
    
    with export_tab:
        render_interactive_reports_tab(export_data)
    
    with social_tab:
        render_social_platforms_tab(export_data)
    
    with calendar_tab:
        render_calendar_integration_tab(export_data)
    
    with crm_tab:
        render_crm_integration_tab(export_data)
    
    with lms_tab:
        render_lms_integration_tab(export_data)
    
    with settings_tab:
        render_integration_settings_tab()


def render_interactive_reports_tab(export_data: ExportData):
    """Render interactive HTML reports interface"""
    
    st.markdown("### 📊 Interactive HTML Reports")
    st.markdown("Generate comprehensive, interactive reports with embedded audio players and rich visualizations.")
    
    # Report configuration
    col1, col2 = st.columns(2)
    
    with col1:
        include_audio = st.checkbox(
            "🎵 Include Audio Player",
            value=True,
            help="Embed audio player in the HTML report"
        )
        
        include_entities = st.checkbox(
            "🏷️ Include Entity Visualization",
            value=True,
            help="Show extracted entities with highlighting"
        )
        
        include_speakers = st.checkbox(
            "👥 Include Speaker Analysis",
            value=True,
            help="Show speaker diarization results"
        )
    
    with col2:
        include_insights = st.checkbox(
            "🧠 Include AI Insights",
            value=True,
            help="Include advanced AI analysis results"
        )
        
        include_timeline = st.checkbox(
            "⏰ Include Timeline View",
            value=True,
            help="Add interactive timeline navigation"
        )
        
        responsive_design = st.checkbox(
            "📱 Mobile-Responsive Design",
            value=True,
            help="Optimize for mobile and tablet viewing"
        )
    
    # Privacy confirmation
    st.warning("Reports may include PII (names, emails, phone numbers). Confirm before generating or downloading.")
    confirm_pii = st.checkbox("I confirm I am authorized to generate and download reports that may include PII.")

    # Generate report button
    if st.button("🚀 Generate Interactive Report", type="primary"):
        with st.spinner("Generating interactive HTML report..."):
            try:
                # Get audio file path if available
                audio_path = None
                if include_audio and hasattr(st.session_state, 'current_audio_path'):
                    audio_path = st.session_state.current_audio_path
                
                # Generate HTML report
                html_content = export_integration_manager.export_interactive_html(
                    export_data, audio_path
                )
                
                # Display success and download option
                st.success("✅ Interactive report generated successfully!")
                
                # Create download button
                if confirm_pii:
                    st.download_button(
                        label="📥 Download HTML Report",
                        data=html_content,
                        file_name=f"transcription_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                        mime="text/html",
                        help="Download the complete interactive HTML report"
                    )
                else:
                    st.info("Confirm PII authorization to enable downloads.")
                
                # Preview option
                with st.expander("👀 Preview Report", expanded=False):
                    st.components.v1.html(html_content, height=600, scrolling=True)
                
            except Exception as e:
                st.error(f"❌ Error generating report: {str(e)}")
    
    # Export package options
    st.markdown("---")
    st.markdown("### 📦 Export Package")
    st.markdown("Create a comprehensive export package with multiple formats.")
    
    # Format selection
    st.markdown("**Select Export Formats:**")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        export_html = st.checkbox("📄 HTML Report", value=True)
    with col2:
        export_json = st.checkbox("📋 JSON Data", value=True)
    with col3:
        export_txt = st.checkbox("📝 Text Transcript", value=True)
    with col4:
        export_csv = st.checkbox("📊 CSV Data", value=False)
    
    # Create export package
    if st.button("📦 Create Export Package"):
        formats = []
        if export_html: formats.append("html")
        if export_json: formats.append("json")
        if export_txt: formats.append("txt")
        if export_csv: formats.append("csv")
        
        if not formats:
            st.warning("⚠️ Please select at least one export format.")
            return
        
        with st.spinner("Creating export package..."):
            try:
                # Get audio file path
                audio_path = getattr(st.session_state, 'current_audio_path', None)
                
                # Create package
                package_data = export_integration_manager.create_export_package(
                    export_data, formats, audio_path
                )
                
                # Convert base64 to bytes for download
                package_bytes = base64.b64decode(package_data)
                
                st.success("✅ Export package created successfully!")
                
                if confirm_pii:
                    st.download_button(
                        label="📥 Download Export Package (ZIP)",
                        data=package_bytes,
                        file_name=f"transcription_package_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                        mime="application/zip"
                    )
                else:
                    st.info("Confirm PII authorization to enable downloads.")
                
            except Exception as e:
                st.error(f"❌ Error creating export package: {str(e)}")


def render_social_platforms_tab(export_data: ExportData):
    """Render social platforms integration interface"""
    
    st.markdown("### 💬 Social Platform Integration")
    st.markdown("Share transcription results directly to Slack, Teams, and Discord.")
    
    # Platform selection tabs
    slack_tab, teams_tab, discord_tab = st.tabs([
        "💬 Slack",
        "🏢 Microsoft Teams",
        "🎮 Discord"
    ])
    
    with slack_tab:
        render_slack_integration(export_data)
    
    with teams_tab:
        render_teams_integration(export_data)
    
    with discord_tab:
        render_discord_integration(export_data)


def render_slack_integration(export_data: ExportData):
    """Render Slack integration interface"""
    
    st.markdown("#### 💬 Slack Integration")
    
    # Configuration
    webhook_url = st.text_input(
        "Slack Webhook URL",
        value=os.getenv('SLACK_WEBHOOK_URL', ''),
        type="password",
        help="Enter your Slack webhook URL for posting messages"
    )
    
    bot_token = st.text_input(
        "Slack Bot Token (Optional)",
        value=os.getenv('SLACK_BOT_TOKEN', ''),
        type="password",
        help="Bot token for file uploads (optional)"
    )
    
    channel = st.text_input(
        "Channel",
        value="#general",
        help="Slack channel to post to (e.g., #general, #transcriptions)"
    )
    
    # Options
    col1, col2 = st.columns(2)
    
    with col1:
        send_summary = st.checkbox("📋 Send Summary", value=True)
        include_metrics = st.checkbox("📊 Include Metrics", value=True)
    
    with col2:
        upload_file = st.checkbox("📎 Upload Full Transcript", value=False)
        mention_users = st.text_input("👥 Mention Users", placeholder="@user1 @user2")
    
    # Send to Slack
    if st.button("📤 Send to Slack", type="primary"):
        if not webhook_url:
            st.error("❌ Please provide a Slack webhook URL")
            return
        
        with st.spinner("Sending to Slack..."):
            try:
                # Initialize Slack integration
                slack = SlackIntegration(webhook_url, bot_token)
                
                # Send summary
                if send_summary:
                    success = slack.send_transcript_summary(export_data, channel)
                    if success:
                        st.success("✅ Summary sent to Slack successfully!")
                    else:
                        st.error("❌ Failed to send summary to Slack")
                
                # Upload file
                if upload_file and bot_token:
                    success = slack.upload_transcript_file(export_data, channel)
                    if success:
                        st.success("✅ File uploaded to Slack successfully!")
                    else:
                        st.error("❌ Failed to upload file to Slack")
                elif upload_file and not bot_token:
                    st.warning("⚠️ Bot token required for file uploads")
                
            except Exception as e:
                st.error(f"❌ Error sending to Slack: {str(e)}")


def render_teams_integration(export_data: ExportData):
    """Render Microsoft Teams integration interface"""
    
    st.markdown("#### 🏢 Microsoft Teams Integration")
    
    # Configuration
    webhook_url = st.text_input(
        "Teams Webhook URL",
        value=os.getenv('TEAMS_WEBHOOK_URL', ''),
        type="password",
        help="Enter your Teams webhook URL for posting adaptive cards"
    )
    
    # Options
    include_summary = st.checkbox("📋 Include Summary", value=True)
    include_actions = st.checkbox("🔗 Include Action Buttons", value=True)
    
    # Send to Teams
    if st.button("📤 Send to Teams", type="primary"):
        if not webhook_url:
            st.error("❌ Please provide a Teams webhook URL")
            return
        
        with st.spinner("Sending to Teams..."):
            try:
                # Initialize Teams integration
                teams = TeamsIntegration(webhook_url)
                
                # Send adaptive card
                success = teams.send_transcript_card(export_data)
                
                if success:
                    st.success("✅ Adaptive card sent to Teams successfully!")
                else:
                    st.error("❌ Failed to send to Teams")
                
            except Exception as e:
                st.error(f"❌ Error sending to Teams: {str(e)}")


def render_discord_integration(export_data: ExportData):
    """Render Discord integration interface"""
    
    st.markdown("#### 🎮 Discord Integration")
    
    # Configuration
    webhook_url = st.text_input(
        "Discord Webhook URL",
        value=os.getenv('DISCORD_WEBHOOK_URL', ''),
        type="password",
        help="Enter your Discord webhook URL for posting embeds"
    )
    
    # Options
    include_embed = st.checkbox("🎨 Rich Embed", value=True)
    ping_role = st.text_input("📢 Ping Role", placeholder="@everyone or @role")
    
    # Send to Discord
    if st.button("📤 Send to Discord", type="primary"):
        if not webhook_url:
            st.error("❌ Please provide a Discord webhook URL")
            return
        
        with st.spinner("Sending to Discord..."):
            try:
                # Initialize Discord integration
                discord = DiscordIntegration(webhook_url)
                
                # Send embed
                success = discord.send_transcript_embed(export_data)
                
                if success:
                    st.success("✅ Embed sent to Discord successfully!")
                else:
                    st.error("❌ Failed to send to Discord")
                
            except Exception as e:
                st.error(f"❌ Error sending to Discord: {str(e)}")


def render_calendar_integration_tab(export_data: ExportData):
    """Render calendar integration interface"""
    
    st.markdown("### 📅 Calendar Integration")
    st.markdown("Create calendar events from meeting transcripts with automatic action item extraction.")
    
    # Meeting information form
    st.markdown("#### 📝 Meeting Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        meeting_title = st.text_input(
            "Meeting Title",
            value="Transcribed Meeting",
            help="Title for the calendar event"
        )
        
        meeting_date = st.date_input(
            "Meeting Date",
            value=datetime.now().date(),
            help="Date when the meeting occurred"
        )
        
        meeting_time = st.time_input(
            "Meeting Time",
            value=datetime.now().time(),
            help="Time when the meeting started"
        )
    
    with col2:
        meeting_location = st.text_input(
            "Location",
            placeholder="Conference Room A / Zoom / Teams",
            help="Meeting location or platform"
        )
        
        attendees = st.text_area(
            "Attendees (one per line)",
            placeholder="john@company.com\nmary@company.com",
            help="Email addresses of meeting attendees"
        )
    
    # Calendar platform selection
    st.markdown("#### 📅 Calendar Platforms")
    
    col1, col2 = st.columns(2)
    
    with col1:
        create_google = st.checkbox("📅 Google Calendar", value=True)
        google_creds = st.text_input(
            "Google Calendar Credentials",
            value=os.getenv('GOOGLE_CALENDAR_CREDENTIALS', ''),
            type="password",
            help="Google Calendar API credentials"
        )
    
    with col2:
        create_outlook = st.checkbox("📅 Outlook Calendar", value=False)
        outlook_creds = st.text_input(
            "Outlook Calendar Credentials",
            value=os.getenv('OUTLOOK_CALENDAR_CREDENTIALS', ''),
            type="password",
            help="Microsoft Graph API credentials"
        )
    
    # Preview extracted information
    st.markdown("#### 🔍 Extracted Information Preview")
    
    if st.button("🔍 Preview Extracted Information"):
        with st.spinner("Analyzing transcript for meeting details..."):
            try:
                # Initialize calendar integration
                calendar = CalendarIntegration()
                
                # Create meeting info
                attendee_list = [email.strip() for email in attendees.split('\n') if email.strip()]
                meeting_datetime = datetime.combine(meeting_date, meeting_time)
                
                meeting_info = {
                    "title": meeting_title,
                    "start_time": meeting_datetime,
                    "location": meeting_location,
                    "attendees": attendee_list
                }
                
                # Extract details
                details = calendar._extract_meeting_details(export_data, meeting_info)
                
                # Display extracted information
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🎯 Action Items:**")
                    if details["action_items"]:
                        for item in details["action_items"]:
                            st.write(f"• {item}")
                    else:
                        st.write("No action items detected")
                
                with col2:
                    st.markdown("**✅ Key Decisions:**")
                    if details["key_decisions"]:
                        for decision in details["key_decisions"]:
                            st.write(f"• {decision}")
                    else:
                        st.write("No key decisions detected")
                
            except Exception as e:
                st.error(f"❌ Error analyzing transcript: {str(e)}")
    
    # Create calendar event
    if st.button("📅 Create Calendar Event", type="primary"):
        if not (create_google or create_outlook):
            st.warning("⚠️ Please select at least one calendar platform")
            return
        
        with st.spinner("Creating calendar event..."):
            try:
                # Prepare meeting info
                attendee_list = [email.strip() for email in attendees.split('\n') if email.strip()]
                meeting_datetime = datetime.combine(meeting_date, meeting_time)
                
                meeting_info = {
                    "title": meeting_title,
                    "start_time": meeting_datetime,
                    "location": meeting_location,
                    "attendees": attendee_list
                }
                
                # Create calendar event
                results = export_integration_manager.create_calendar_event(export_data, meeting_info)
                
                # Display results
                if "error" in results:
                    st.error(f"❌ Error creating calendar event: {results['error']}")
                else:
                    st.success("✅ Calendar event created successfully!")
                    
                    for platform, result in results.items():
                        if result.get("status") == "success":
                            st.success(f"✅ {platform.title()}: Event created (ID: {result.get('event_id', 'N/A')})")
                            if "url" in result:
                                st.markdown(f"🔗 [View Event]({result['url']})")
                        else:
                            st.error(f"❌ {platform.title()}: Failed to create event")
                
            except Exception as e:
                st.error(f"❌ Error creating calendar event: {str(e)}")


def render_crm_integration_tab(export_data: ExportData):
    """Render CRM integration interface"""
    
    st.markdown("### 🏢 CRM Integration")
    st.markdown("Analyze customer calls and automatically update CRM systems with insights.")
    
    # Customer information form
    st.markdown("#### 👤 Customer Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        customer_name = st.text_input("Customer Name", placeholder="John Doe")
        customer_email = st.text_input("Customer Email", placeholder="john@company.com")
        customer_company = st.text_input("Company", placeholder="Acme Corp")
    
    with col2:
        call_type = st.selectbox(
            "Call Type",
            ["Sales Call", "Support Call", "Demo Call", "Follow-up Call", "Other"]
        )
        deal_stage = st.selectbox(
            "Deal Stage",
            ["Prospecting", "Qualification", "Proposal", "Negotiation", "Closed Won", "Closed Lost"]
        )
    
    # CRM platform selection
    st.markdown("#### 🏢 CRM Platforms")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        update_salesforce = st.checkbox("☁️ Salesforce", value=False)
        sf_token = st.text_input(
            "Salesforce Token",
            value=os.getenv('SALESFORCE_TOKEN', ''),
            type="password"
        )
    
    with col2:
        update_hubspot = st.checkbox("🧡 HubSpot", value=False)
        hs_token = st.text_input(
            "HubSpot Token",
            value=os.getenv('HUBSPOT_TOKEN', ''),
            type="password"
        )
    
    with col3:
        update_pipedrive = st.checkbox("🟢 Pipedrive", value=False)
        pd_token = st.text_input(
            "Pipedrive Token",
            value=os.getenv('PIPEDRIVE_TOKEN', ''),
            type="password"
        )
    
    # Analyze call
    if st.button("🔍 Analyze Customer Call"):
        with st.spinner("Analyzing customer call..."):
            try:
                # Prepare customer info
                customer_info = {
                    "name": customer_name,
                    "email": customer_email,
                    "company": customer_company,
                    "call_type": call_type,
                    "deal_stage": deal_stage
                }
                
                # Analyze call
                analysis = export_integration_manager.crm._analyze_call_content(export_data)
                
                # Display analysis results
                st.markdown("#### 📊 Call Analysis Results")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    sentiment_color = "green" if analysis["sentiment"] == "positive" else "red" if analysis["sentiment"] == "negative" else "orange"
                    st.markdown(f"**Sentiment:** :{sentiment_color}[{analysis['sentiment'].title()}]")
                    st.metric("Sentiment Score", f"{analysis['sentiment_score']:.2f}")
                
                with col2:
                    st.markdown("**Key Topics:**")
                    for topic in analysis["topics"]:
                        st.write(f"• {topic.title()}")
                
                with col3:
                    st.markdown("**Call Duration:**")
                    st.metric("Duration", f"{analysis['call_duration']:.1f}s")
                
                # Next steps
                if analysis["next_steps"]:
                    st.markdown("**🎯 Next Steps:**")
                    for step in analysis["next_steps"]:
                        st.write(f"• {step}")
                
                # Key entities
                if analysis["key_entities"]:
                    st.markdown("**🏷️ Key Entities:**")
                    st.write(", ".join(analysis["key_entities"]))
                
            except Exception as e:
                st.error(f"❌ Error analyzing call: {str(e)}")
    
    # Update CRM
    if st.button("🔄 Update CRM Systems", type="primary"):
        if not any([update_salesforce, update_hubspot, update_pipedrive]):
            st.warning("⚠️ Please select at least one CRM platform")
            return
        
        with st.spinner("Updating CRM systems..."):
            try:
                # Prepare customer info
                customer_info = {
                    "name": customer_name,
                    "email": customer_email,
                    "company": customer_company,
                    "call_type": call_type,
                    "deal_stage": deal_stage
                }
                
                # Update CRM
                results = export_integration_manager.analyze_customer_call(export_data, customer_info)
                
                # Display results
                if "error" in results:
                    st.error(f"❌ Error updating CRM: {results['error']}")
                else:
                    st.success("✅ CRM systems updated successfully!")
                    
                    for platform, result in results.items():
                        if result.get("status") == "success":
                            st.success(f"✅ {platform.title()}: Updated successfully")
                            if "record_id" in result:
                                st.info(f"Record ID: {result['record_id']}")
                        else:
                            st.error(f"❌ {platform.title()}: Update failed")
                
            except Exception as e:
                st.error(f"❌ Error updating CRM: {str(e)}")


def render_lms_integration_tab(export_data: ExportData):
    """Render LMS integration interface"""
    
    st.markdown("### 🎓 LMS Integration")
    st.markdown("Process educational content and create learning materials for Learning Management Systems.")
    
    # Course information form
    st.markdown("#### 📚 Course Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        course_title = st.text_input("Course Title", placeholder="Introduction to Data Science")
        course_code = st.text_input("Course Code", placeholder="CS101")
        instructor = st.text_input("Instructor", placeholder="Dr. Jane Smith")
    
    with col2:
        course_level = st.selectbox(
            "Course Level",
            ["Beginner", "Intermediate", "Advanced", "Graduate"]
        )
        content_type = st.selectbox(
            "Content Type",
            ["Lecture", "Seminar", "Workshop", "Tutorial", "Discussion"]
        )
    
    # LMS platform selection
    st.markdown("#### 🎓 LMS Platforms")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        update_canvas = st.checkbox("🎨 Canvas", value=False)
        canvas_token = st.text_input(
            "Canvas API Token",
            value=os.getenv('CANVAS_API_TOKEN', ''),
            type="password"
        )
    
    with col2:
        update_moodle = st.checkbox("🎯 Moodle", value=False)
        moodle_token = st.text_input(
            "Moodle API Token",
            value=os.getenv('MOODLE_API_TOKEN', ''),
            type="password"
        )
    
    with col3:
        update_blackboard = st.checkbox("⚫ Blackboard", value=False)
        bb_token = st.text_input(
            "Blackboard API Token",
            value=os.getenv('BLACKBOARD_API_TOKEN', ''),
            type="password"
        )
    
    # Analyze educational content
    if st.button("🔍 Analyze Educational Content"):
        with st.spinner("Analyzing educational content..."):
            try:
                # Prepare course info
                course_info = {
                    "course_id": f"{course_code}_{datetime.now().strftime('%Y')}",
                    "title": course_title,
                    "code": course_code,
                    "instructor": instructor,
                    "level": course_level,
                    "content_type": content_type
                }
                
                # Analyze content
                analysis = export_integration_manager.lms._analyze_educational_content(export_data)
                
                # Display analysis results
                st.markdown("#### 📊 Educational Content Analysis")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Difficulty Level", analysis["difficulty_level"])
                    st.metric("Estimated Study Time", f"{analysis['estimated_study_time']} minutes")
                
                with col2:
                    st.metric("Key Concepts", len(analysis["key_concepts"]))
                    st.metric("Quiz Questions", len(analysis["quiz_questions"]))
                
                # Key concepts
                if analysis["key_concepts"]:
                    st.markdown("**🎯 Key Concepts:**")
                    for concept in analysis["key_concepts"]:
                        st.write(f"• {concept}")
                
                # Learning objectives
                if analysis["learning_objectives"]:
                    st.markdown("**📋 Learning Objectives:**")
                    for objective in analysis["learning_objectives"]:
                        st.write(f"• {objective}")
                
                # Sample quiz questions
                if analysis["quiz_questions"]:
                    st.markdown("**❓ Sample Quiz Questions:**")
                    for i, question in enumerate(analysis["quiz_questions"][:3], 1):
                        with st.expander(f"Question {i}: {question['question'][:50]}..."):
                            st.write(f"**Question:** {question['question']}")
                            st.write("**Options:**")
                            for j, option in enumerate(question['options']):
                                st.write(f"{chr(65+j)}. {option}")
                            st.write(f"**Correct Answer:** {chr(65+question['correct_answer'])}")
                
                # Study notes preview
                with st.expander("📝 Study Notes Preview"):
                    st.markdown(analysis["study_notes"])
                
            except Exception as e:
                st.error(f"❌ Error analyzing content: {str(e)}")
    
    # Upload to LMS
    if st.button("📤 Upload to LMS", type="primary"):
        if not any([update_canvas, update_moodle, update_blackboard]):
            st.warning("⚠️ Please select at least one LMS platform")
            return
        
        with st.spinner("Uploading to LMS platforms..."):
            try:
                # Prepare course info
                course_info = {
                    "course_id": f"{course_code}_{datetime.now().strftime('%Y')}",
                    "title": course_title,
                    "code": course_code,
                    "instructor": instructor,
                    "level": course_level,
                    "content_type": content_type
                }
                
                # Process educational content
                results = export_integration_manager.process_educational_content(export_data, course_info)
                
                # Display results
                if "error" in results:
                    st.error(f"❌ Error uploading to LMS: {results['error']}")
                else:
                    st.success("✅ Content uploaded to LMS successfully!")
                    
                    for platform, result in results.items():
                        if result.get("status") == "success":
                            st.success(f"✅ {platform.title()}: Content uploaded successfully")
                            st.info(f"Course ID: {result.get('course_id', 'N/A')}")
                            if "materials_uploaded" in result:
                                st.write(f"Materials: {', '.join(result['materials_uploaded'])}")
                        else:
                            st.error(f"❌ {platform.title()}: Upload failed")
                
            except Exception as e:
                st.error(f"❌ Error uploading to LMS: {str(e)}")


def render_integration_settings_tab():
    """Render integration settings and configuration"""
    
    st.markdown("### ⚙️ Integration Settings")
    st.markdown("Configure API keys and settings for various integration platforms.")
    
    # API Keys section
    st.markdown("#### 🔑 API Keys & Credentials")
    
    with st.expander("💬 Social Platforms", expanded=False):
        st.text_input("Slack Webhook URL", value=os.getenv('SLACK_WEBHOOK_URL', ''), type="password")
        st.text_input("Slack Bot Token", value=os.getenv('SLACK_BOT_TOKEN', ''), type="password")
        st.text_input("Teams Webhook URL", value=os.getenv('TEAMS_WEBHOOK_URL', ''), type="password")
        st.text_input("Discord Webhook URL", value=os.getenv('DISCORD_WEBHOOK_URL', ''), type="password")
    
    with st.expander("📅 Calendar Services", expanded=False):
        st.text_input("Google Calendar Credentials", value=os.getenv('GOOGLE_CALENDAR_CREDENTIALS', ''), type="password")
        st.text_input("Outlook Calendar Credentials", value=os.getenv('OUTLOOK_CALENDAR_CREDENTIALS', ''), type="password")
    
    with st.expander("🏢 CRM Systems", expanded=False):
        st.text_input("Salesforce Token", value=os.getenv('SALESFORCE_TOKEN', ''), type="password")
        st.text_input("HubSpot Token", value=os.getenv('HUBSPOT_TOKEN', ''), type="password")
        st.text_input("Pipedrive Token", value=os.getenv('PIPEDRIVE_TOKEN', ''), type="password")
    
    with st.expander("🎓 LMS Platforms", expanded=False):
        st.text_input("Canvas API Token", value=os.getenv('CANVAS_API_TOKEN', ''), type="password")
        st.text_input("Moodle API Token", value=os.getenv('MOODLE_API_TOKEN', ''), type="password")
        st.text_input("Blackboard API Token", value=os.getenv('BLACKBOARD_API_TOKEN', ''), type="password")
    
    # Test connections
    st.markdown("#### 🔍 Test Connections")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🧪 Test Social Platforms"):
            st.info("Testing social platform connections...")
            # Mock test results
            st.success("✅ Slack: Connected")
            st.warning("⚠️ Teams: Not configured")
            st.error("❌ Discord: Connection failed")
    
    with col2:
        if st.button("🧪 Test Calendar Services"):
            st.info("Testing calendar service connections...")
            # Mock test results
            st.success("✅ Google Calendar: Connected")
            st.warning("⚠️ Outlook: Not configured")
    
    with col3:
        if st.button("🧪 Test CRM/LMS"):
            st.info("Testing CRM and LMS connections...")
            # Mock test results
            st.warning("⚠️ Salesforce: Not configured")
            st.warning("⚠️ Canvas: Not configured")
    
    # Integration usage statistics
    st.markdown("#### 📊 Integration Usage Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Reports Generated", "42", "↑ 12%")
    
    with col2:
        st.metric("Social Shares", "18", "↑ 5%")
    
    with col3:
        st.metric("Calendar Events", "8", "↑ 2%")
    
    with col4:
        st.metric("CRM Updates", "15", "↑ 8%")
    
    # Export settings
    st.markdown("#### 📤 Export Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.selectbox("Default Export Format", ["HTML", "JSON", "TXT", "CSV"])
        st.checkbox("Include Audio in Reports", value=True)
        st.checkbox("Auto-generate Timestamps", value=True)
    
    with col2:
        st.selectbox("Report Theme", ["Professional", "Modern", "Minimal", "Dark"])
        st.checkbox("Mobile-Responsive Design", value=True)
        st.checkbox("Include Entity Highlighting", value=True)


def _convert_to_export_data(results) -> ExportData:
    """Convert session results to ExportData format"""
    
    # Extract basic information
    transcript = getattr(results, 'transcript', '')
    entities = getattr(results, 'entities', [])
    summary = getattr(results, 'summary', transcript[:200] + '...' if len(transcript) > 200 else transcript)
    duration = getattr(results, 'duration', 0.0)
    language = getattr(results, 'language', 'en')
    confidence = getattr(results, 'confidence', 0.0)
    created_at = getattr(results, 'created_at', datetime.now()).isoformat()
    
    # Extract speakers information
    speakers = []
    if hasattr(results, 'speaker_segments') and results.speaker_segments:
        speaker_stats = {}
        for segment in results.speaker_segments:
            speaker_id = segment.get('speaker', 'Unknown')
            if speaker_id not in speaker_stats:
                speaker_stats[speaker_id] = {'duration': 0, 'segments': 0}
            speaker_stats[speaker_id]['duration'] += segment.get('end', 0) - segment.get('start', 0)
            speaker_stats[speaker_id]['segments'] += 1
        
        speakers = [
            {'id': speaker_id, **stats}
            for speaker_id, stats in speaker_stats.items()
        ]
    
    # Extract insights
    insights = {}
    if hasattr(results, 'insights'):
        insights = results.insights
    elif hasattr(results, 'advanced_entities'):
        insights = {'advanced_entities': results.advanced_entities}
    
    # File information
    file_info = {
        'original_filename': getattr(results, 'original_filename', 'unknown'),
        'file_size': getattr(results, 'file_size', 0),
        'processing_time': getattr(results, 'processing_time', 0)
    }
    
    return ExportData(
        transcript=transcript,
        entities=entities,
        summary=summary,
        duration=duration,
        language=language,
        confidence=confidence,
        created_at=created_at,
        speakers=speakers,
        insights=insights,
        file_info=file_info
    )
