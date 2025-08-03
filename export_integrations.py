#!/usr/bin/env python3
"""
Advanced Export and Integration Capabilities (Task 41)
Interactive HTML reports, Slack/Teams/Discord integration, calendar events, CRM integration, LMS integration
"""

import streamlit as st
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
import base64
from dataclasses import dataclass, asdict
from pathlib import Path
import tempfile
import zipfile

logger = logging.getLogger(__name__)

@dataclass
class ExportData:
    """Data structure for export content"""
    transcript: str
    entities: List[Dict]
    summary: str
    duration: float
    language: str
    confidence: float
    created_at: str
    speakers: List[Dict]
    insights: Dict
    file_info: Dict

class HTMLReportGenerator:
    """Generate interactive HTML reports with embedded audio players"""
    
    def __init__(self):
        self.template_path = Path(__file__).parent / "templates"
        self.template_path.mkdir(exist_ok=True)
    
    def generate_interactive_report(self, export_data: ExportData, audio_file_path: Optional[str] = None) -> str:
        """Generate comprehensive HTML report"""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Transcription Report - {title}</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 10px 10px 0 0; }}
        .content {{ padding: 30px; }}
        .section {{ margin-bottom: 30px; padding: 20px; border-left: 4px solid #667eea; background: #f8f9ff; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
        .metric {{ background: white; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .metric-value {{ font-size: 2em; font-weight: bold; color: #667eea; }}
        .metric-label {{ color: #666; margin-top: 5px; }}
        .transcript {{ background: white; padding: 20px; border-radius: 8px; line-height: 1.6; max-height: 400px; overflow-y: auto; }}
        .entity {{ display: inline-block; margin: 2px; padding: 4px 8px; border-radius: 4px; font-size: 0.9em; }}
        .entity-PERSON {{ background: #e3f2fd; color: #1976d2; }}
        .entity-ORG {{ background: #f3e5f5; color: #7b1fa2; }}
        .entity-DATE {{ background: #e8f5e8; color: #388e3c; }}
        .entity-GPE {{ background: #fff3e0; color: #f57c00; }}
        .audio-player {{ margin: 20px 0; text-align: center; }}
        .insights {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .insight-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .speakers {{ display: flex; flex-wrap: wrap; gap: 15px; }}
        .speaker {{ background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .timestamp {{ color: #666; font-size: 0.9em; cursor: pointer; }}
        .timestamp:hover {{ color: #667eea; text-decoration: underline; }}
        @media (max-width: 768px) {{
            .container {{ margin: 10px; }}
            .header, .content {{ padding: 20px; }}
            .metrics {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Transcription Analysis Report</h1>
            <p>Generated on {created_at}</p>
        </div>
        
        <div class="content">
            <!-- Metrics Overview -->
            <div class="section">
                <h2>📈 Overview</h2>
                <div class="metrics">
                    <div class="metric">
                        <div class="metric-value">{word_count}</div>
                        <div class="metric-label">Words</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{duration:.1f}s</div>
                        <div class="metric-label">Duration</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{confidence:.1%}</div>
                        <div class="metric-label">Confidence</div>
                    </div>
                    <div class="metric">
                        <div class="metric-value">{language}</div>
                        <div class="metric-label">Language</div>
                    </div>
                </div>
            </div>
            
            <!-- Audio Player -->
            {audio_player_html}
            
            <!-- Transcript -->
            <div class="section">
                <h2>📝 Transcript</h2>
                <div class="transcript" id="transcript">
                    {formatted_transcript}
                </div>
            </div>
            
            <!-- Entities -->
            <div class="section">
                <h2>🏷️ Extracted Entities</h2>
                <div class="entities">
                    {entities_html}
                </div>
            </div>
            
            <!-- Speakers -->
            {speakers_html}
            
            <!-- Insights -->
            {insights_html}
            
            <!-- Summary -->
            <div class="section">
                <h2>📋 Summary</h2>
                <p>{summary}</p>
            </div>
        </div>
    </div>
    
    <script>
        // Audio player sync with transcript
        function seekToTime(seconds) {{
            const audio = document.getElementById('audio-player');
            if (audio) {{
                audio.currentTime = seconds;
                audio.play();
            }}
        }}
        
        // Highlight current transcript section
        function highlightTranscript(startTime, endTime) {{
            // Implementation for highlighting current transcript section
            console.log('Highlighting transcript from', startTime, 'to', endTime);
        }}
    </script>
</body>
</html>
        """
        
        # Format data for template
        word_count = len(export_data.transcript.split())
        
        # Generate audio player HTML if audio file provided
        audio_player_html = ""
        if audio_file_path and os.path.exists(audio_file_path):
            audio_data = self._encode_audio_file(audio_file_path)
            audio_player_html = f"""
            <div class="section">
                <h2>🎵 Audio Player</h2>
                <div class="audio-player">
                    <audio id="audio-player" controls style="width: 100%; max-width: 600px;">
                        <source src="data:audio/wav;base64,{audio_data}" type="audio/wav">
                        Your browser does not support the audio element.
                    </audio>
                </div>
            </div>
            """
        
        # Format entities
        entities_html = self._format_entities_html(export_data.entities)
        
        # Format speakers
        speakers_html = self._format_speakers_html(export_data.speakers)
        
        # Format insights
        insights_html = self._format_insights_html(export_data.insights)
        
        # Format transcript with timestamps
        formatted_transcript = self._format_transcript_with_timestamps(export_data.transcript)
        
        # Fill template
        html_content = html_template.format(
            title=f"Report_{datetime.now().strftime('%Y%m%d_%H%M')}",
            created_at=export_data.created_at,
            word_count=word_count,
            duration=export_data.duration,
            confidence=export_data.confidence,
            language=export_data.language.upper(),
            audio_player_html=audio_player_html,
            formatted_transcript=formatted_transcript,
            entities_html=entities_html,
            speakers_html=speakers_html,
            insights_html=insights_html,
            summary=export_data.summary
        )
        
        return html_content
    
    def _encode_audio_file(self, audio_path: str) -> str:
        """Encode audio file to base64 for embedding"""
        try:
            with open(audio_path, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error encoding audio file: {e}")
            return ""
    
    def _format_entities_html(self, entities: List[Dict]) -> str:
        """Format entities as HTML"""
        if not entities:
            return "<p>No entities extracted.</p>"
        
        html_parts = []
        for entity in entities:
            entity_type = entity.get('type', 'UNKNOWN')
            entity_text = entity.get('text', '')
            confidence = entity.get('confidence', 0)
            
            html_parts.append(
                f'<span class="entity entity-{entity_type}" title="Confidence: {confidence:.2f}">'
                f'{entity_text}</span>'
            )
        
        return ' '.join(html_parts)
    
    def _format_speakers_html(self, speakers: List[Dict]) -> str:
        """Format speakers information as HTML"""
        if not speakers:
            return ""
        
        speakers_html = """
        <div class="section">
            <h2>👥 Speakers</h2>
            <div class="speakers">
        """
        
        for speaker in speakers:
            speaker_id = speaker.get('id', 'Unknown')
            duration = speaker.get('duration', 0)
            segments = speaker.get('segments', 0)
            
            speakers_html += f"""
            <div class="speaker">
                <h4>Speaker {speaker_id}</h4>
                <p>Duration: {duration:.1f}s</p>
                <p>Segments: {segments}</p>
            </div>
            """
        
        speakers_html += "</div></div>"
        return speakers_html
    
    def _format_insights_html(self, insights: Dict) -> str:
        """Format insights as HTML"""
        if not insights:
            return ""
        
        insights_html = """
        <div class="section">
            <h2>🧠 AI Insights</h2>
            <div class="insights">
        """
        
        for key, value in insights.items():
            if isinstance(value, dict):
                insights_html += f"""
                <div class="insight-card">
                    <h4>{key.replace('_', ' ').title()}</h4>
                    <p>{json.dumps(value, indent=2)}</p>
                </div>
                """
            else:
                insights_html += f"""
                <div class="insight-card">
                    <h4>{key.replace('_', ' ').title()}</h4>
                    <p>{value}</p>
                </div>
                """
        
        insights_html += "</div></div>"
        return insights_html
    
    def _format_transcript_with_timestamps(self, transcript: str) -> str:
        """Format transcript with clickable timestamps"""
        # Simple implementation - in real app would use actual timestamp data
        lines = transcript.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            if line.strip():
                timestamp = i * 10  # Mock timestamp every 10 seconds
                formatted_lines.append(
                    f'<span class="timestamp" onclick="seekToTime({timestamp})">[{timestamp:02d}:{timestamp%60:02d}]</span> {line}'
                )
        
        return '<br>'.join(formatted_lines)


class SlackIntegration:
    """Slack integration for sharing transcripts and analysis"""
    
    def __init__(self, webhook_url: Optional[str] = None, bot_token: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('SLACK_WEBHOOK_URL')
        self.bot_token = bot_token or os.getenv('SLACK_BOT_TOKEN')
    
    def send_transcript_summary(self, export_data: ExportData, channel: str = "#general") -> bool:
        """Send transcript summary to Slack channel"""
        try:
            if not self.webhook_url:
                raise ValueError("Slack webhook URL not configured")
            
            # Create rich message
            message = {
                "channel": channel,
                "username": "Transcription Bot",
                "icon_emoji": ":microphone:",
                "attachments": [
                    {
                        "color": "good",
                        "title": "📊 New Transcription Analysis",
                        "fields": [
                            {
                                "title": "Duration",
                                "value": f"{export_data.duration:.1f} seconds",
                                "short": True
                            },
                            {
                                "title": "Confidence",
                                "value": f"{export_data.confidence:.1%}",
                                "short": True
                            },
                            {
                                "title": "Language",
                                "value": export_data.language.upper(),
                                "short": True
                            },
                            {
                                "title": "Word Count",
                                "value": str(len(export_data.transcript.split())),
                                "short": True
                            }
                        ],
                        "text": f"*Summary:* {export_data.summary[:200]}...",
                        "footer": "Transcription App",
                        "ts": int(datetime.now().timestamp())
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=message)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Slack: {e}")
            return False
    
    def upload_transcript_file(self, export_data: ExportData, channel: str = "#general") -> bool:
        """Upload full transcript as file to Slack"""
        try:
            if not self.bot_token:
                raise ValueError("Slack bot token not configured")
            
            # Create temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(f"Transcription Analysis Report\n")
                f.write(f"Generated: {export_data.created_at}\n")
                f.write(f"Duration: {export_data.duration:.1f}s\n")
                f.write(f"Confidence: {export_data.confidence:.1%}\n")
                f.write(f"Language: {export_data.language}\n\n")
                f.write(f"SUMMARY:\n{export_data.summary}\n\n")
                f.write(f"TRANSCRIPT:\n{export_data.transcript}")
                temp_path = f.name
            
            # Upload file
            files = {'file': open(temp_path, 'rb')}
            data = {
                'channels': channel,
                'title': 'Transcription Report',
                'initial_comment': '📊 Complete transcription analysis report'
            }
            headers = {'Authorization': f'Bearer {self.bot_token}'}
            
            response = requests.post(
                'https://slack.com/api/files.upload',
                headers=headers,
                data=data,
                files=files
            )
            
            # Cleanup
            os.unlink(temp_path)
            files['file'].close()
            
            return response.json().get('ok', False)
            
        except Exception as e:
            logger.error(f"Error uploading to Slack: {e}")
            return False


class TeamsIntegration:
    """Microsoft Teams integration"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('TEAMS_WEBHOOK_URL')
    
    def send_transcript_card(self, export_data: ExportData) -> bool:
        """Send adaptive card to Teams channel"""
        try:
            if not self.webhook_url:
                raise ValueError("Teams webhook URL not configured")
            
            # Create adaptive card
            card = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7",
                "summary": "New Transcription Analysis",
                "sections": [
                    {
                        "activityTitle": "📊 Transcription Analysis Complete",
                        "activitySubtitle": f"Generated on {export_data.created_at}",
                        "facts": [
                            {"name": "Duration", "value": f"{export_data.duration:.1f} seconds"},
                            {"name": "Confidence", "value": f"{export_data.confidence:.1%}"},
                            {"name": "Language", "value": export_data.language.upper()},
                            {"name": "Words", "value": str(len(export_data.transcript.split()))}
                        ],
                        "text": f"**Summary:** {export_data.summary[:300]}..."
                    }
                ],
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "View Full Report",
                        "targets": [
                            {"os": "default", "uri": "https://your-app.com/reports"}
                        ]
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=card)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Teams: {e}")
            return False


class DiscordIntegration:
    """Discord integration"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv('DISCORD_WEBHOOK_URL')
    
    def send_transcript_embed(self, export_data: ExportData) -> bool:
        """Send rich embed to Discord channel"""
        try:
            if not self.webhook_url:
                raise ValueError("Discord webhook URL not configured")
            
            # Create embed
            embed = {
                "username": "Transcription Bot",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/2040/2040946.png",
                "embeds": [
                    {
                        "title": "📊 New Transcription Analysis",
                        "description": f"**Summary:** {export_data.summary[:200]}...",
                        "color": 5814783,  # Blue color
                        "fields": [
                            {
                                "name": "⏱️ Duration",
                                "value": f"{export_data.duration:.1f}s",
                                "inline": True
                            },
                            {
                                "name": "🎯 Confidence",
                                "value": f"{export_data.confidence:.1%}",
                                "inline": True
                            },
                            {
                                "name": "🌍 Language",
                                "value": export_data.language.upper(),
                                "inline": True
                            },
                            {
                                "name": "📝 Word Count",
                                "value": str(len(export_data.transcript.split())),
                                "inline": True
                            }
                        ],
                        "footer": {
                            "text": "Transcription App",
                            "icon_url": "https://cdn-icons-png.flaticon.com/512/2040/2040946.png"
                        },
                        "timestamp": datetime.now().isoformat()
                    }
                ]
            }
            
            response = requests.post(self.webhook_url, json=embed)
            response.raise_for_status()
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending to Discord: {e}")
            return False


class CalendarIntegration:
    """Calendar integration for creating events from meeting transcripts"""
    
    def __init__(self):
        self.google_credentials = os.getenv('GOOGLE_CALENDAR_CREDENTIALS')
        self.outlook_credentials = os.getenv('OUTLOOK_CALENDAR_CREDENTIALS')
    
    def create_meeting_event(self, export_data: ExportData, meeting_info: Dict) -> Dict:
        """Create calendar event from meeting transcript"""
        try:
            # Extract meeting details from transcript and metadata
            event_data = self._extract_meeting_details(export_data, meeting_info)
            
            # Create event in multiple calendar systems
            results = {}
            
            if self.google_credentials:
                results['google'] = self._create_google_event(event_data)
            
            if self.outlook_credentials:
                results['outlook'] = self._create_outlook_event(event_data)
            
            return results
            
        except Exception as e:
            logger.error(f"Error creating calendar event: {e}")
            return {"error": str(e)}
    
    def _extract_meeting_details(self, export_data: ExportData, meeting_info: Dict) -> Dict:
        """Extract meeting details from transcript"""
        # Use AI to extract meeting details
        details = {
            "title": meeting_info.get("title", "Meeting Transcript"),
            "description": f"Meeting Summary: {export_data.summary}",
            "start_time": meeting_info.get("start_time", datetime.now()),
            "duration": export_data.duration,
            "attendees": meeting_info.get("attendees", []),
            "location": meeting_info.get("location", ""),
            "action_items": self._extract_action_items(export_data.transcript),
            "key_decisions": self._extract_key_decisions(export_data.transcript)
        }
        
        return details
    
    def _extract_action_items(self, transcript: str) -> List[str]:
        """Extract action items from transcript"""
        # Simple keyword-based extraction
        action_keywords = ["action item", "todo", "follow up", "next step", "assign"]
        action_items = []
        
        lines = transcript.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in action_keywords):
                action_items.append(line.strip())
        
        return action_items[:10]  # Limit to 10 items
    
    def _extract_key_decisions(self, transcript: str) -> List[str]:
        """Extract key decisions from transcript"""
        # Simple keyword-based extraction
        decision_keywords = ["decided", "agreed", "conclusion", "resolution"]
        decisions = []
        
        lines = transcript.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in decision_keywords):
                decisions.append(line.strip())
        
        return decisions[:5]  # Limit to 5 decisions
    
    def _create_google_event(self, event_data: Dict) -> Dict:
        """Create Google Calendar event"""
        # Mock implementation - would use Google Calendar API
        return {
            "status": "success",
            "event_id": f"google_event_{datetime.now().timestamp()}",
            "url": "https://calendar.google.com/calendar/event?eid=mock"
        }
    
    def _create_outlook_event(self, event_data: Dict) -> Dict:
        """Create Outlook Calendar event"""
        # Mock implementation - would use Microsoft Graph API
        return {
            "status": "success", 
            "event_id": f"outlook_event_{datetime.now().timestamp()}",
            "url": "https://outlook.office.com/calendar/event/mock"
        }


class CRMIntegration:
    """CRM integration for customer call analysis"""
    
    def __init__(self):
        self.salesforce_token = os.getenv('SALESFORCE_TOKEN')
        self.hubspot_token = os.getenv('HUBSPOT_TOKEN')
        self.pipedrive_token = os.getenv('PIPEDRIVE_TOKEN')
    
    def analyze_customer_call(self, export_data: ExportData, customer_info: Dict) -> Dict:
        """Analyze customer call and update CRM"""
        try:
            # Analyze call content
            analysis = self._analyze_call_content(export_data)
            
            # Update CRM systems
            results = {}
            
            if self.salesforce_token:
                results['salesforce'] = self._update_salesforce(customer_info, analysis)
            
            if self.hubspot_token:
                results['hubspot'] = self._update_hubspot(customer_info, analysis)
            
            if self.pipedrive_token:
                results['pipedrive'] = self._update_pipedrive(customer_info, analysis)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in CRM integration: {e}")
            return {"error": str(e)}
    
    def _analyze_call_content(self, export_data: ExportData) -> Dict:
        """Analyze call content for CRM insights"""
        transcript = export_data.transcript.lower()
        
        # Sentiment analysis (simplified)
        positive_words = ["great", "excellent", "satisfied", "happy", "good", "yes"]
        negative_words = ["problem", "issue", "unhappy", "disappointed", "no", "bad"]
        
        positive_count = sum(transcript.count(word) for word in positive_words)
        negative_count = sum(transcript.count(word) for word in negative_words)
        
        sentiment_score = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        
        # Extract key topics
        topics = self._extract_topics(transcript)
        
        # Extract next steps
        next_steps = self._extract_next_steps(transcript)
        
        return {
            "sentiment_score": sentiment_score,
            "sentiment": "positive" if sentiment_score > 0.1 else "negative" if sentiment_score < -0.1 else "neutral",
            "topics": topics,
            "next_steps": next_steps,
            "call_duration": export_data.duration,
            "call_summary": export_data.summary,
            "key_entities": [e.get('text', '') for e in export_data.entities[:10]]
        }
    
    def _extract_topics(self, transcript: str) -> List[str]:
        """Extract main topics from call"""
        # Simple keyword-based topic extraction
        topic_keywords = {
            "pricing": ["price", "cost", "budget", "expensive", "cheap"],
            "features": ["feature", "functionality", "capability", "option"],
            "support": ["support", "help", "assistance", "service"],
            "integration": ["integrate", "connect", "api", "sync"],
            "timeline": ["when", "timeline", "schedule", "deadline"]
        }
        
        topics = []
        for topic, keywords in topic_keywords.items():
            if any(keyword in transcript for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def _extract_next_steps(self, transcript: str) -> List[str]:
        """Extract next steps from call"""
        next_step_indicators = ["next step", "follow up", "will send", "schedule", "call back"]
        next_steps = []
        
        lines = transcript.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in next_step_indicators):
                next_steps.append(line.strip())
        
        return next_steps[:5]
    
    def _update_salesforce(self, customer_info: Dict, analysis: Dict) -> Dict:
        """Update Salesforce with call analysis"""
        # Mock implementation - would use Salesforce API
        return {
            "status": "success",
            "record_id": f"sf_record_{datetime.now().timestamp()}",
            "updated_fields": ["call_sentiment", "last_call_date", "call_notes"]
        }
    
    def _update_hubspot(self, customer_info: Dict, analysis: Dict) -> Dict:
        """Update HubSpot with call analysis"""
        # Mock implementation - would use HubSpot API
        return {
            "status": "success",
            "contact_id": f"hs_contact_{datetime.now().timestamp()}",
            "updated_properties": ["call_sentiment", "last_call_summary"]
        }
    
    def _update_pipedrive(self, customer_info: Dict, analysis: Dict) -> Dict:
        """Update Pipedrive with call analysis"""
        # Mock implementation - would use Pipedrive API
        return {
            "status": "success",
            "deal_id": f"pd_deal_{datetime.now().timestamp()}",
            "activity_id": f"pd_activity_{datetime.now().timestamp()}"
        }


class LMSIntegration:
    """Learning Management System integration for educational content"""
    
    def __init__(self):
        self.canvas_token = os.getenv('CANVAS_API_TOKEN')
        self.moodle_token = os.getenv('MOODLE_API_TOKEN')
        self.blackboard_token = os.getenv('BLACKBOARD_API_TOKEN')
    
    def process_educational_content(self, export_data: ExportData, course_info: Dict) -> Dict:
        """Process educational content for LMS integration"""
        try:
            # Analyze educational content
            analysis = self._analyze_educational_content(export_data)
            
            # Create learning materials
            materials = self._create_learning_materials(export_data, analysis)
            
            # Update LMS systems
            results = {}
            
            if self.canvas_token:
                results['canvas'] = self._update_canvas(course_info, materials)
            
            if self.moodle_token:
                results['moodle'] = self._update_moodle(course_info, materials)
            
            if self.blackboard_token:
                results['blackboard'] = self._update_blackboard(course_info, materials)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in LMS integration: {e}")
            return {"error": str(e)}
    
    def _analyze_educational_content(self, export_data: ExportData) -> Dict:
        """Analyze educational content"""
        transcript = export_data.transcript
        
        # Extract key concepts
        concepts = self._extract_key_concepts(transcript)
        
        # Generate quiz questions
        quiz_questions = self._generate_quiz_questions(transcript, concepts)
        
        # Create study notes
        study_notes = self._create_study_notes(transcript, concepts)
        
        # Estimate difficulty level
        difficulty = self._estimate_difficulty(transcript)
        
        return {
            "key_concepts": concepts,
            "quiz_questions": quiz_questions,
            "study_notes": study_notes,
            "difficulty_level": difficulty,
            "estimated_study_time": len(transcript.split()) // 200 * 5,  # 5 min per 200 words
            "learning_objectives": self._extract_learning_objectives(transcript)
        }
    
    def _extract_key_concepts(self, transcript: str) -> List[str]:
        """Extract key educational concepts"""
        # Simple implementation - would use NLP for better extraction
        concept_indicators = ["define", "concept", "theory", "principle", "law", "formula"]
        concepts = []
        
        sentences = transcript.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in concept_indicators):
                # Extract the main concept (simplified)
                words = sentence.split()
                if len(words) > 3:
                    concepts.append(' '.join(words[:10]) + "...")
        
        return concepts[:10]
    
    def _generate_quiz_questions(self, transcript: str, concepts: List[str]) -> List[Dict]:
        """Generate quiz questions from content"""
        questions = []
        
        # Simple question generation based on concepts
        for i, concept in enumerate(concepts[:5]):
            questions.append({
                "id": i + 1,
                "type": "multiple_choice",
                "question": f"What is the main idea behind: {concept[:50]}...?",
                "options": [
                    "Option A (generated)",
                    "Option B (generated)", 
                    "Option C (generated)",
                    "Option D (generated)"
                ],
                "correct_answer": 0,
                "explanation": "This would be generated based on the transcript content."
            })
        
        return questions
    
    def _create_study_notes(self, transcript: str, concepts: List[str]) -> str:
        """Create structured study notes"""
        notes = f"""
# Study Notes

## Key Concepts:
{chr(10).join(f"- {concept}" for concept in concepts)}

## Summary:
{transcript[:500]}...

## Important Points:
- Point 1 (extracted from transcript)
- Point 2 (extracted from transcript)
- Point 3 (extracted from transcript)

## Review Questions:
1. What are the main concepts covered?
2. How do these concepts relate to each other?
3. What are the practical applications?
        """
        
        return notes.strip()
    
    def _estimate_difficulty(self, transcript: str) -> str:
        """Estimate content difficulty level"""
        # Simple heuristic based on vocabulary complexity
        words = transcript.split()
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        if avg_word_length < 4:
            return "Beginner"
        elif avg_word_length < 6:
            return "Intermediate"
        else:
            return "Advanced"
    
    def _extract_learning_objectives(self, transcript: str) -> List[str]:
        """Extract learning objectives"""
        objective_indicators = ["learn", "understand", "explain", "demonstrate", "analyze"]
        objectives = []
        
        sentences = transcript.split('.')
        for sentence in sentences:
            if any(indicator in sentence.lower() for indicator in objective_indicators):
                objectives.append(sentence.strip())
        
        return objectives[:5]
    
    def _create_learning_materials(self, export_data: ExportData, analysis: Dict) -> Dict:
        """Create comprehensive learning materials"""
        return {
            "transcript": export_data.transcript,
            "summary": export_data.summary,
            "study_notes": analysis["study_notes"],
            "quiz_questions": analysis["quiz_questions"],
            "key_concepts": analysis["key_concepts"],
            "learning_objectives": analysis["learning_objectives"],
            "difficulty_level": analysis["difficulty_level"],
            "estimated_study_time": analysis["estimated_study_time"]
        }
    
    def _update_canvas(self, course_info: Dict, materials: Dict) -> Dict:
        """Update Canvas LMS"""
        # Mock implementation - would use Canvas API
        return {
            "status": "success",
            "course_id": course_info.get("course_id", "mock_course"),
            "module_id": f"canvas_module_{datetime.now().timestamp()}",
            "materials_uploaded": ["transcript", "study_notes", "quiz"]
        }
    
    def _update_moodle(self, course_info: Dict, materials: Dict) -> Dict:
        """Update Moodle LMS"""
        # Mock implementation - would use Moodle API
        return {
            "status": "success",
            "course_id": course_info.get("course_id", "mock_course"),
            "resource_id": f"moodle_resource_{datetime.now().timestamp()}",
            "materials_uploaded": ["transcript", "study_notes", "quiz"]
        }
    
    def _update_blackboard(self, course_info: Dict, materials: Dict) -> Dict:
        """Update Blackboard LMS"""
        # Mock implementation - would use Blackboard API
        return {
            "status": "success",
            "course_id": course_info.get("course_id", "mock_course"),
            "content_id": f"bb_content_{datetime.now().timestamp()}",
            "materials_uploaded": ["transcript", "study_notes", "quiz"]
        }


class ExportIntegrationManager:
    """Main manager for all export and integration capabilities"""
    
    def __init__(self):
        self.html_generator = HTMLReportGenerator()
        self.slack = SlackIntegration()
        self.teams = TeamsIntegration()
        self.discord = DiscordIntegration()
        self.calendar = CalendarIntegration()
        self.crm = CRMIntegration()
        self.lms = LMSIntegration()
    
    def export_interactive_html(self, export_data: ExportData, audio_file_path: Optional[str] = None) -> str:
        """Generate interactive HTML report"""
        return self.html_generator.generate_interactive_report(export_data, audio_file_path)
    
    def share_to_slack(self, export_data: ExportData, channel: str = "#general", include_file: bool = False) -> Dict:
        """Share to Slack"""
        results = {}
        
        # Send summary
        results['summary'] = self.slack.send_transcript_summary(export_data, channel)
        
        # Upload file if requested
        if include_file:
            results['file_upload'] = self.slack.upload_transcript_file(export_data, channel)
        
        return results
    
    def share_to_teams(self, export_data: ExportData) -> bool:
        """Share to Microsoft Teams"""
        return self.teams.send_transcript_card(export_data)
    
    def share_to_discord(self, export_data: ExportData) -> bool:
        """Share to Discord"""
        return self.discord.send_transcript_embed(export_data)
    
    def create_calendar_event(self, export_data: ExportData, meeting_info: Dict) -> Dict:
        """Create calendar event from meeting transcript"""
        return self.calendar.create_meeting_event(export_data, meeting_info)
    
    def analyze_customer_call(self, export_data: ExportData, customer_info: Dict) -> Dict:
        """Analyze customer call for CRM"""
        return self.crm.analyze_customer_call(export_data, customer_info)
    
    def process_educational_content(self, export_data: ExportData, course_info: Dict) -> Dict:
        """Process educational content for LMS"""
        return self.lms.process_educational_content(export_data, course_info)
    
    def create_export_package(self, export_data: ExportData, formats: List[str], audio_file_path: Optional[str] = None) -> str:
        """Create comprehensive export package"""
        try:
            # Create temporary directory for export package
            with tempfile.TemporaryDirectory() as temp_dir:
                package_dir = Path(temp_dir) / "export_package"
                package_dir.mkdir()
                
                # Generate different formats
                if "html" in formats:
                    html_content = self.export_interactive_html(export_data, audio_file_path)
                    (package_dir / "report.html").write_text(html_content, encoding='utf-8')
                
                if "json" in formats:
                    json_content = json.dumps(asdict(export_data), indent=2, default=str)
                    (package_dir / "data.json").write_text(json_content, encoding='utf-8')
                
                if "txt" in formats:
                    txt_content = f"""Transcription Report
Generated: {export_data.created_at}
Duration: {export_data.duration:.1f} seconds
Confidence: {export_data.confidence:.1%}
Language: {export_data.language}

SUMMARY:
{export_data.summary}

TRANSCRIPT:
{export_data.transcript}
"""
                    (package_dir / "transcript.txt").write_text(txt_content, encoding='utf-8')
                
                if "csv" in formats:
                    csv_content = "Type,Content,Confidence\n"
                    csv_content += f"Transcript,\"{export_data.transcript.replace('\"', '\"\"')}\",{export_data.confidence}\n"
                    for entity in export_data.entities:
                        csv_content += f"Entity,\"{entity.get('text', '').replace('\"', '\"\"')}\",{entity.get('confidence', 0)}\n"
                    (package_dir / "data.csv").write_text(csv_content, encoding='utf-8')
                
                # Include audio file if provided
                if audio_file_path and os.path.exists(audio_file_path):
                    import shutil
                    audio_filename = Path(audio_file_path).name
                    shutil.copy2(audio_file_path, package_dir / audio_filename)
                
                # Create ZIP package
                zip_path = Path(temp_dir) / "export_package.zip"
                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for file_path in package_dir.rglob('*'):
                        if file_path.is_file():
                            zipf.write(file_path, file_path.relative_to(package_dir))
                
                # Read ZIP content
                with open(zip_path, 'rb') as f:
                    zip_content = f.read()
                
                return base64.b64encode(zip_content).decode('utf-8')
                
        except Exception as e:
            logger.error(f"Error creating export package: {e}")
            raise


# Global instance
export_integration_manager = ExportIntegrationManager()