"""
Streamlit UI components for webhook management
"""

import streamlit as st
import json
from datetime import datetime
from typing import List, Optional
from .webhook_manager import webhook_manager, WebhookEventType, WebhookSubscription


def render_webhook_settings():
    """Render webhook management interface"""
    
    st.header("🔗 Webhook Settings")
    
    # Webhook system status
    stats = webhook_manager.get_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Subscriptions", stats['total_subscriptions'])
    with col2:
        st.metric("Active Subscriptions", stats['active_subscriptions'])
    with col3:
        st.metric("Events in Queue", stats['events_in_queue'])
    with col4:
        st.metric("Workers Running", stats['workers_running'])
    
    # System controls
    st.subheader("System Controls")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("▶️ Start Webhook System", disabled=stats['is_running']):
            import asyncio
            asyncio.create_task(webhook_manager.start_workers())
            st.success("Webhook system started!")
            st.rerun()
    
    with col2:
        if st.button("⏹️ Stop Webhook System", disabled=not stats['is_running']):
            import asyncio
            asyncio.create_task(webhook_manager.stop_workers())
            st.success("Webhook system stopped!")
            st.rerun()
    
    # Tabs for different webhook management functions
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Add Webhook", "📋 Manage Webhooks", "🧪 Test Webhook", "📊 Event Log"])
    
    with tab1:
        render_add_webhook_form()
    
    with tab2:
        render_webhook_list()
    
    with tab3:
        render_webhook_test()
    
    with tab4:
        render_event_log()


def render_add_webhook_form():
    """Render form to add new webhook subscription"""
    
    st.subheader("Add New Webhook")
    
    with st.form("add_webhook_form"):
        # Basic webhook configuration
        url = st.text_input(
            "Webhook URL *",
            placeholder="https://your-app.com/webhooks/transcription",
            help="The URL where webhook events will be sent"
        )
        
        # Event type selection
        st.write("**Select Event Types:**")
        event_types = []
        
        # Group events by category
        transcription_events = [
            WebhookEventType.TRANSCRIPTION_STARTED,
            WebhookEventType.TRANSCRIPTION_COMPLETED,
            WebhookEventType.TRANSCRIPTION_FAILED
        ]
        
        batch_events = [
            WebhookEventType.BATCH_JOB_STARTED,
            WebhookEventType.BATCH_JOB_COMPLETED,
            WebhookEventType.BATCH_JOB_FAILED
        ]
        
        user_events = [
            WebhookEventType.USER_REGISTERED,
            WebhookEventType.TEAM_MEMBER_ADDED,
            WebhookEventType.TRANSCRIPT_SHARED,
            WebhookEventType.ANNOTATION_ADDED
        ]
        
        other_events = [
            WebhookEventType.ENTITY_EXTRACTION_COMPLETED,
            WebhookEventType.EXPORT_COMPLETED
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Transcription Events:**")
            for event in transcription_events:
                if st.checkbox(event.value.replace('_', ' ').title(), key=f"event_{event.value}"):
                    event_types.append(event)
            
            st.write("**Batch Processing Events:**")
            for event in batch_events:
                if st.checkbox(event.value.replace('_', ' ').title(), key=f"event_{event.value}"):
                    event_types.append(event)
        
        with col2:
            st.write("**User & Team Events:**")
            for event in user_events:
                if st.checkbox(event.value.replace('_', ' ').title(), key=f"event_{event.value}"):
                    event_types.append(event)
            
            st.write("**Other Events:**")
            for event in other_events:
                if st.checkbox(event.value.replace('_', ' ').title(), key=f"event_{event.value}"):
                    event_types.append(event)
        
        # Advanced settings
        with st.expander("⚙️ Advanced Settings"):
            secret = st.text_input(
                "Webhook Secret",
                type="password",
                help="Optional secret for HMAC signature verification. Leave empty to auto-generate."
            )
            
            timeout = st.number_input(
                "Timeout (seconds)",
                min_value=5,
                max_value=300,
                value=30,
                help="Request timeout in seconds"
            )
            
            retry_count = st.number_input(
                "Retry Count",
                min_value=0,
                max_value=10,
                value=3,
                help="Number of retry attempts on failure"
            )
            
            # Custom headers
            st.write("**Custom Headers:**")
            headers_text = st.text_area(
                "Headers (JSON format)",
                placeholder='{"Authorization": "Bearer token", "X-Custom-Header": "value"}',
                help="Optional custom headers in JSON format"
            )
        
        # Submit button
        submitted = st.form_submit_button("➕ Add Webhook", type="primary")
        
        if submitted:
            # Validate inputs
            if not url:
                st.error("Webhook URL is required")
                return
            
            if not event_types:
                st.error("Please select at least one event type")
                return
            
            # Parse custom headers
            headers = {}
            if headers_text.strip():
                try:
                    headers = json.loads(headers_text)
                except json.JSONDecodeError:
                    st.error("Invalid JSON format for custom headers")
                    return
            
            try:
                # Add webhook subscription
                subscription_id = webhook_manager.add_subscription(
                    url=url,
                    event_types=event_types,
                    secret=secret if secret else None,
                    headers=headers,
                    timeout=int(timeout),
                    retry_count=int(retry_count)
                )
                
                st.success(f"✅ Webhook added successfully! ID: {subscription_id}")
                
                # Show the generated secret if auto-generated
                subscription = webhook_manager.get_subscription(subscription_id)
                if subscription and not secret:
                    st.info(f"🔐 Auto-generated secret: `{subscription.secret}`")
                    st.warning("⚠️ Save this secret securely - it won't be shown again!")
                
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Failed to add webhook: {str(e)}")


def render_webhook_list():
    """Render list of existing webhook subscriptions"""
    
    st.subheader("Webhook Subscriptions")
    
    subscriptions = webhook_manager.list_subscriptions(active_only=False)
    
    if not subscriptions:
        st.info("No webhook subscriptions configured.")
        return
    
    for subscription in subscriptions:
        with st.expander(f"🔗 {subscription.url} {'✅' if subscription.active else '❌'}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Configuration:**")
                st.write(f"• **ID:** `{subscription.id}`")
                st.write(f"• **URL:** {subscription.url}")
                st.write(f"• **Status:** {'Active' if subscription.active else 'Inactive'}")
                st.write(f"• **Created:** {subscription.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                if subscription.last_triggered:
                    st.write(f"• **Last Triggered:** {subscription.last_triggered.strftime('%Y-%m-%d %H:%M:%S')}")
                st.write(f"• **Failure Count:** {subscription.failure_count}/{subscription.max_failures}")
            
            with col2:
                st.write("**Event Types:**")
                for event_type in subscription.event_types:
                    st.write(f"• {event_type.value.replace('_', ' ').title()}")
                
                st.write("**Settings:**")
                st.write(f"• **Timeout:** {subscription.timeout}s")
                st.write(f"• **Retry Count:** {subscription.retry_count}")
                if subscription.headers:
                    st.write(f"• **Custom Headers:** {len(subscription.headers)} headers")
            
            # Action buttons
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✏️ Edit", key=f"edit_{subscription.id}"):
                    st.session_state[f"edit_webhook_{subscription.id}"] = True
                    st.rerun()
            
            with col2:
                status_text = "Deactivate" if subscription.active else "Activate"
                status_icon = "⏸️" if subscription.active else "▶️"
                if st.button(f"{status_icon} {status_text}", key=f"toggle_{subscription.id}"):
                    webhook_manager.update_subscription(
                        subscription.id,
                        active=not subscription.active
                    )
                    st.success(f"Webhook {'deactivated' if subscription.active else 'activated'}!")
                    st.rerun()
            
            with col3:
                if st.button("🧪 Test", key=f"test_{subscription.id}"):
                    st.session_state[f"test_webhook_{subscription.id}"] = True
                    st.rerun()
            
            with col4:
                if st.button("🗑️ Delete", key=f"delete_{subscription.id}", type="secondary"):
                    if st.session_state.get(f"confirm_delete_{subscription.id}", False):
                        webhook_manager.remove_subscription(subscription.id)
                        st.success("Webhook deleted!")
                        st.rerun()
                    else:
                        st.session_state[f"confirm_delete_{subscription.id}"] = True
                        st.warning("Click again to confirm deletion")
            
            # Handle edit mode
            if st.session_state.get(f"edit_webhook_{subscription.id}", False):
                render_edit_webhook_form(subscription)


def render_edit_webhook_form(subscription: WebhookSubscription):
    """Render form to edit existing webhook subscription"""
    
    st.write("---")
    st.write("**Edit Webhook:**")
    
    with st.form(f"edit_webhook_form_{subscription.id}"):
        # URL
        new_url = st.text_input("Webhook URL", value=subscription.url)
        
        # Event types
        st.write("**Event Types:**")
        new_event_types = []
        
        for event_type in WebhookEventType:
            if st.checkbox(
                event_type.value.replace('_', ' ').title(),
                value=event_type in subscription.event_types,
                key=f"edit_event_{subscription.id}_{event_type.value}"
            ):
                new_event_types.append(event_type)
        
        # Settings
        col1, col2 = st.columns(2)
        with col1:
            new_timeout = st.number_input(
                "Timeout (seconds)",
                min_value=5,
                max_value=300,
                value=subscription.timeout
            )
        with col2:
            new_retry_count = st.number_input(
                "Retry Count",
                min_value=0,
                max_value=10,
                value=subscription.retry_count
            )
        
        # Custom headers
        headers_json = json.dumps(subscription.headers, indent=2) if subscription.headers else ""
        new_headers_text = st.text_area(
            "Custom Headers (JSON)",
            value=headers_json,
            help="Custom headers in JSON format"
        )
        
        # Submit buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.form_submit_button("💾 Save Changes", type="primary"):
                try:
                    # Parse headers
                    new_headers = {}
                    if new_headers_text.strip():
                        new_headers = json.loads(new_headers_text)
                    
                    # Update subscription
                    webhook_manager.update_subscription(
                        subscription.id,
                        url=new_url,
                        event_types=new_event_types,
                        headers=new_headers
                    )
                    
                    st.success("✅ Webhook updated successfully!")
                    st.session_state[f"edit_webhook_{subscription.id}"] = False
                    st.rerun()
                    
                except json.JSONDecodeError:
                    st.error("Invalid JSON format for custom headers")
                except Exception as e:
                    st.error(f"Failed to update webhook: {str(e)}")
        
        with col2:
            if st.form_submit_button("❌ Cancel"):
                st.session_state[f"edit_webhook_{subscription.id}"] = False
                st.rerun()


def render_webhook_test():
    """Render webhook testing interface"""
    
    st.subheader("Test Webhook")
    
    subscriptions = webhook_manager.list_subscriptions(active_only=True)
    
    if not subscriptions:
        st.info("No active webhook subscriptions to test.")
        return
    
    # Select subscription to test
    subscription_options = {
        f"{sub.url} ({sub.id[:8]}...)": sub.id
        for sub in subscriptions
    }
    
    selected_subscription = st.selectbox(
        "Select Webhook to Test",
        options=list(subscription_options.keys())
    )
    
    if not selected_subscription:
        return
    
    subscription_id = subscription_options[selected_subscription]
    subscription = webhook_manager.get_subscription(subscription_id)
    
    # Select event type to test
    event_type_options = [
        event.value.replace('_', ' ').title()
        for event in subscription.event_types
    ]
    
    selected_event_type = st.selectbox(
        "Select Event Type",
        options=event_type_options
    )
    
    if not selected_event_type:
        return
    
    # Convert back to enum
    event_type = None
    for event in subscription.event_types:
        if event.value.replace('_', ' ').title() == selected_event_type:
            event_type = event
            break
    
    # Test data input
    st.write("**Test Event Data:**")
    
    # Provide sample data based on event type
    sample_data = get_sample_event_data(event_type)
    
    test_data_text = st.text_area(
        "Event Data (JSON)",
        value=json.dumps(sample_data, indent=2),
        height=200,
        help="Customize the test event data"
    )
    
    # Test button
    if st.button("🚀 Send Test Event", type="primary"):
        try:
            test_data = json.loads(test_data_text)
            
            # Trigger test event
            import asyncio
            event_id = asyncio.run(webhook_manager.trigger_event(
                event_type=event_type,
                data=test_data,
                user_id="test-user-123",
                team_id="test-team-456",
                resource_id="test-resource-789"
            ))
            
            st.success(f"✅ Test event sent! Event ID: {event_id}")
            st.info("Check your webhook endpoint to verify the event was received.")
            
        except json.JSONDecodeError:
            st.error("Invalid JSON format for test data")
        except Exception as e:
            st.error(f"Failed to send test event: {str(e)}")


def render_event_log():
    """Render webhook event log"""
    
    st.subheader("Event Log")
    
    # This would typically connect to a database or log file
    # For now, show placeholder information
    
    st.info("📝 Event logging is not yet implemented. This would show:")
    st.write("• Recent webhook events")
    st.write("• Delivery status and response codes")
    st.write("• Retry attempts and failures")
    st.write("• Performance metrics")
    
    # Placeholder metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Events Today", "42")
    with col2:
        st.metric("Success Rate", "98.5%")
    with col3:
        st.metric("Avg Response Time", "245ms")
    with col4:
        st.metric("Failed Deliveries", "2")


def get_sample_event_data(event_type: WebhookEventType) -> dict:
    """Get sample data for different event types"""
    
    if event_type == WebhookEventType.TRANSCRIPTION_COMPLETED:
        return {
            "transcript_id": "trans_123456789",
            "file_name": "meeting_recording.mp3",
            "duration": 1800,
            "word_count": 2450,
            "confidence_score": 94.5,
            "processing_time": 45.2,
            "language": "en",
            "model_used": "whisper-1",
            "transcript_url": "https://app.example.com/transcripts/trans_123456789"
        }
    
    elif event_type == WebhookEventType.TRANSCRIPTION_FAILED:
        return {
            "transcript_id": "trans_123456789",
            "file_name": "corrupted_audio.mp3",
            "error_code": "AUDIO_DECODE_ERROR",
            "error_message": "Unable to decode audio file",
            "retry_count": 2
        }
    
    elif event_type == WebhookEventType.BATCH_JOB_COMPLETED:
        return {
            "batch_id": "batch_987654321",
            "job_type": "transcription",
            "files_processed": 25,
            "successful_jobs": 23,
            "failed_jobs": 2,
            "total_processing_time": 1200.5,
            "cost_savings": "45%"
        }
    
    elif event_type == WebhookEventType.USER_REGISTERED:
        return {
            "username": "john_doe",
            "email": "john@example.com",
            "registration_method": "email",
            "account_type": "free"
        }
    
    elif event_type == WebhookEventType.TEAM_MEMBER_ADDED:
        return {
            "user_id": "user_456789",
            "role": "member",
            "invited_by": "admin_123",
            "team_name": "Engineering Team",
            "member_count": 8
        }
    
    else:
        return {
            "message": f"Sample data for {event_type.value}",
            "timestamp": datetime.utcnow().isoformat(),
            "status": "success"
        }