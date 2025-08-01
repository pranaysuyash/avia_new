"""
Webhook handlers for different event types
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .webhook_manager import WebhookEvent, WebhookEventType

logger = logging.getLogger(__name__)


class WebhookHandler(ABC):
    """Abstract base class for webhook handlers"""
    
    @abstractmethod
    async def handle_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle a webhook event and return response data"""
        pass
    
    @abstractmethod
    def get_supported_events(self) -> list[WebhookEventType]:
        """Return list of supported event types"""
        pass


class DefaultWebhookHandler(WebhookHandler):
    """Default webhook handler for common events"""
    
    def get_supported_events(self) -> list[WebhookEventType]:
        """Return all supported event types"""
        return list(WebhookEventType)
    
    async def handle_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle webhook event with default processing"""
        
        logger.info(f"Processing webhook event: {event.event_type.value}")
        
        # Common response structure
        response = {
            'event_id': event.id,
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'status': 'processed'
        }
        
        # Event-specific processing
        if event.event_type == WebhookEventType.TRANSCRIPTION_COMPLETED:
            response.update(await self._handle_transcription_completed(event))
            
        elif event.event_type == WebhookEventType.TRANSCRIPTION_FAILED:
            response.update(await self._handle_transcription_failed(event))
            
        elif event.event_type == WebhookEventType.ENTITY_EXTRACTION_COMPLETED:
            response.update(await self._handle_entity_extraction_completed(event))
            
        elif event.event_type == WebhookEventType.BATCH_JOB_COMPLETED:
            response.update(await self._handle_batch_job_completed(event))
            
        elif event.event_type == WebhookEventType.BATCH_JOB_FAILED:
            response.update(await self._handle_batch_job_failed(event))
            
        elif event.event_type == WebhookEventType.USER_REGISTERED:
            response.update(await self._handle_user_registered(event))
            
        elif event.event_type == WebhookEventType.TEAM_MEMBER_ADDED:
            response.update(await self._handle_team_member_added(event))
            
        elif event.event_type == WebhookEventType.TRANSCRIPT_SHARED:
            response.update(await self._handle_transcript_shared(event))
            
        elif event.event_type == WebhookEventType.EXPORT_COMPLETED:
            response.update(await self._handle_export_completed(event))
            
        else:
            response.update(await self._handle_generic_event(event))
        
        return response
    
    async def _handle_transcription_completed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle transcription completion event"""
        data = event.data
        
        return {
            'transcript_id': data.get('transcript_id'),
            'file_name': data.get('file_name'),
            'duration': data.get('duration'),
            'word_count': data.get('word_count'),
            'confidence_score': data.get('confidence_score'),
            'processing_time': data.get('processing_time'),
            'language': data.get('language', 'en'),
            'model_used': data.get('model_used'),
            'message': 'Transcription completed successfully'
        }
    
    async def _handle_transcription_failed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle transcription failure event"""
        data = event.data
        
        return {
            'transcript_id': data.get('transcript_id'),
            'file_name': data.get('file_name'),
            'error_code': data.get('error_code'),
            'error_message': data.get('error_message'),
            'retry_count': data.get('retry_count', 0),
            'message': 'Transcription failed'
        }
    
    async def _handle_entity_extraction_completed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle entity extraction completion event"""
        data = event.data
        
        return {
            'transcript_id': data.get('transcript_id'),
            'extraction_mode': data.get('extraction_mode'),
            'entities_found': data.get('entities_count', 0),
            'entity_types': data.get('entity_types', []),
            'processing_time': data.get('processing_time'),
            'confidence_score': data.get('confidence_score'),
            'message': 'Entity extraction completed successfully'
        }
    
    async def _handle_batch_job_completed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle batch job completion event"""
        data = event.data
        
        return {
            'batch_id': data.get('batch_id'),
            'job_type': data.get('job_type'),
            'files_processed': data.get('files_processed', 0),
            'successful_jobs': data.get('successful_jobs', 0),
            'failed_jobs': data.get('failed_jobs', 0),
            'total_processing_time': data.get('total_processing_time'),
            'cost_savings': data.get('cost_savings'),
            'message': 'Batch job completed successfully'
        }
    
    async def _handle_batch_job_failed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle batch job failure event"""
        data = event.data
        
        return {
            'batch_id': data.get('batch_id'),
            'job_type': data.get('job_type'),
            'error_code': data.get('error_code'),
            'error_message': data.get('error_message'),
            'files_processed': data.get('files_processed', 0),
            'retry_available': data.get('retry_available', False),
            'message': 'Batch job failed'
        }
    
    async def _handle_user_registered(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle user registration event"""
        data = event.data
        
        return {
            'user_id': event.user_id,
            'username': data.get('username'),
            'email': data.get('email'),
            'registration_method': data.get('registration_method', 'email'),
            'account_type': data.get('account_type', 'free'),
            'message': 'User registered successfully'
        }
    
    async def _handle_team_member_added(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle team member addition event"""
        data = event.data
        
        return {
            'team_id': event.team_id,
            'user_id': data.get('user_id'),
            'role': data.get('role'),
            'invited_by': data.get('invited_by'),
            'team_name': data.get('team_name'),
            'member_count': data.get('member_count'),
            'message': 'Team member added successfully'
        }
    
    async def _handle_transcript_shared(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle transcript sharing event"""
        data = event.data
        
        return {
            'transcript_id': event.resource_id,
            'shared_with': data.get('shared_with'),
            'permission_level': data.get('permission_level'),
            'share_type': data.get('share_type'),
            'expires_at': data.get('expires_at'),
            'share_url': data.get('share_url'),
            'message': 'Transcript shared successfully'
        }
    
    async def _handle_export_completed(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle export completion event"""
        data = event.data
        
        return {
            'export_id': data.get('export_id'),
            'transcript_id': event.resource_id,
            'export_format': data.get('export_format'),
            'file_size': data.get('file_size'),
            'download_url': data.get('download_url'),
            'expires_at': data.get('expires_at'),
            'message': 'Export completed successfully'
        }
    
    async def _handle_generic_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle generic/unknown event types"""
        return {
            'data': event.data,
            'message': f'Generic event {event.event_type.value} processed'
        }


class SlackWebhookHandler(WebhookHandler):
    """Specialized handler for Slack webhook integration"""
    
    def get_supported_events(self) -> list[WebhookEventType]:
        """Return Slack-relevant event types"""
        return [
            WebhookEventType.TRANSCRIPTION_COMPLETED,
            WebhookEventType.TRANSCRIPTION_FAILED,
            WebhookEventType.BATCH_JOB_COMPLETED,
            WebhookEventType.BATCH_JOB_FAILED,
            WebhookEventType.TEAM_MEMBER_ADDED
        ]
    
    async def handle_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle event with Slack-formatted messages"""
        
        if event.event_type == WebhookEventType.TRANSCRIPTION_COMPLETED:
            return await self._format_transcription_completed_slack(event)
        elif event.event_type == WebhookEventType.TRANSCRIPTION_FAILED:
            return await self._format_transcription_failed_slack(event)
        elif event.event_type == WebhookEventType.BATCH_JOB_COMPLETED:
            return await self._format_batch_completed_slack(event)
        elif event.event_type == WebhookEventType.TEAM_MEMBER_ADDED:
            return await self._format_team_member_added_slack(event)
        else:
            return await self._format_generic_slack(event)
    
    async def _format_transcription_completed_slack(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format transcription completion for Slack"""
        data = event.data
        
        return {
            "text": "🎉 Transcription Completed",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Transcription completed successfully!*\n\n"
                                f"📁 *File:* {data.get('file_name', 'Unknown')}\n"
                                f"⏱️ *Duration:* {data.get('duration', 'Unknown')} seconds\n"
                                f"📝 *Words:* {data.get('word_count', 'Unknown')}\n"
                                f"🎯 *Confidence:* {data.get('confidence_score', 'Unknown')}%\n"
                                f"🌐 *Language:* {data.get('language', 'en').upper()}"
                    }
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {
                                "type": "plain_text",
                                "text": "View Transcript"
                            },
                            "url": data.get('transcript_url', '#'),
                            "style": "primary"
                        }
                    ]
                }
            ]
        }
    
    async def _format_transcription_failed_slack(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format transcription failure for Slack"""
        data = event.data
        
        return {
            "text": "❌ Transcription Failed",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Transcription failed*\n\n"
                                f"📁 *File:* {data.get('file_name', 'Unknown')}\n"
                                f"❌ *Error:* {data.get('error_message', 'Unknown error')}\n"
                                f"🔄 *Retry Count:* {data.get('retry_count', 0)}"
                    }
                }
            ]
        }
    
    async def _format_batch_completed_slack(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format batch job completion for Slack"""
        data = event.data
        
        return {
            "text": "📦 Batch Job Completed",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Batch processing completed!*\n\n"
                                f"📦 *Batch ID:* {data.get('batch_id', 'Unknown')}\n"
                                f"✅ *Successful:* {data.get('successful_jobs', 0)}\n"
                                f"❌ *Failed:* {data.get('failed_jobs', 0)}\n"
                                f"💰 *Cost Savings:* {data.get('cost_savings', 'Unknown')}"
                    }
                }
            ]
        }
    
    async def _format_team_member_added_slack(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format team member addition for Slack"""
        data = event.data
        
        return {
            "text": "👥 New Team Member",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*New team member added!*\n\n"
                                f"👤 *User:* {data.get('username', 'Unknown')}\n"
                                f"🏢 *Team:* {data.get('team_name', 'Unknown')}\n"
                                f"🎭 *Role:* {data.get('role', 'member').title()}\n"
                                f"👥 *Total Members:* {data.get('member_count', 'Unknown')}"
                    }
                }
            ]
        }
    
    async def _format_generic_slack(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format generic event for Slack"""
        return {
            "text": f"📢 {event.event_type.value.replace('_', ' ').title()}",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Event:* {event.event_type.value}\n"
                                f"*Time:* {event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                                f"*ID:* {event.id}"
                    }
                }
            ]
        }


class TeamsWebhookHandler(WebhookHandler):
    """Specialized handler for Microsoft Teams webhook integration"""
    
    def get_supported_events(self) -> list[WebhookEventType]:
        """Return Teams-relevant event types"""
        return [
            WebhookEventType.TRANSCRIPTION_COMPLETED,
            WebhookEventType.TRANSCRIPTION_FAILED,
            WebhookEventType.BATCH_JOB_COMPLETED,
            WebhookEventType.TEAM_MEMBER_ADDED
        ]
    
    async def handle_event(self, event: WebhookEvent) -> Dict[str, Any]:
        """Handle event with Teams-formatted messages"""
        
        if event.event_type == WebhookEventType.TRANSCRIPTION_COMPLETED:
            return await self._format_transcription_completed_teams(event)
        elif event.event_type == WebhookEventType.TRANSCRIPTION_FAILED:
            return await self._format_transcription_failed_teams(event)
        else:
            return await self._format_generic_teams(event)
    
    async def _format_transcription_completed_teams(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format transcription completion for Teams"""
        data = event.data
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": "Transcription Completed",
            "sections": [
                {
                    "activityTitle": "🎉 Transcription Completed Successfully",
                    "activitySubtitle": f"File: {data.get('file_name', 'Unknown')}",
                    "facts": [
                        {"name": "Duration", "value": f"{data.get('duration', 'Unknown')} seconds"},
                        {"name": "Word Count", "value": str(data.get('word_count', 'Unknown'))},
                        {"name": "Confidence", "value": f"{data.get('confidence_score', 'Unknown')}%"},
                        {"name": "Language", "value": data.get('language', 'en').upper()},
                        {"name": "Processing Time", "value": f"{data.get('processing_time', 'Unknown')} seconds"}
                    ],
                    "markdown": True
                }
            ],
            "potentialAction": [
                {
                    "@type": "OpenUri",
                    "name": "View Transcript",
                    "targets": [
                        {"os": "default", "uri": data.get('transcript_url', '#')}
                    ]
                }
            ]
        }
    
    async def _format_transcription_failed_teams(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format transcription failure for Teams"""
        data = event.data
        
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "FF0000",
            "summary": "Transcription Failed",
            "sections": [
                {
                    "activityTitle": "❌ Transcription Failed",
                    "activitySubtitle": f"File: {data.get('file_name', 'Unknown')}",
                    "facts": [
                        {"name": "Error", "value": data.get('error_message', 'Unknown error')},
                        {"name": "Error Code", "value": data.get('error_code', 'Unknown')},
                        {"name": "Retry Count", "value": str(data.get('retry_count', 0))}
                    ],
                    "markdown": True
                }
            ]
        }
    
    async def _format_generic_teams(self, event: WebhookEvent) -> Dict[str, Any]:
        """Format generic event for Teams"""
        return {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": event.event_type.value.replace('_', ' ').title(),
            "sections": [
                {
                    "activityTitle": f"📢 {event.event_type.value.replace('_', ' ').title()}",
                    "activitySubtitle": f"Event ID: {event.id}",
                    "facts": [
                        {"name": "Time", "value": event.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')},
                        {"name": "Event Type", "value": event.event_type.value}
                    ],
                    "markdown": True
                }
            ]
        }