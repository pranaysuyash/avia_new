"""
API Client for Streamlit Apps

Provides a simple interface to connect Streamlit demos with the FastAPI backend
"""

import os
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

class APIClient:
    """Client for interacting with the FastAPI backend"""
    
    def __init__(self, base_url: str = None):
        """Initialize API client"""
        # Try to get base_url from various sources
        if base_url:
            self.base_url = base_url
        else:
            # Try environment variable first
            self.base_url = os.environ.get("API_URL")
            if not self.base_url:
                try:
                    # Try Streamlit secrets if available
                    import streamlit as st
                    self.base_url = st.secrets.get("API_URL", "http://localhost:8000")
                except:
                    # Default to localhost
                    self.base_url = "http://localhost:8000"
        
        self.session = requests.Session()
        
        # Get auth token from various sources
        self.auth_token = None
        try:
            import streamlit as st
            if 'auth_token' in st.session_state:
                self.auth_token = st.session_state.auth_token
            elif hasattr(st, 'secrets') and 'AUTH_TOKEN' in st.secrets:
                self.auth_token = st.secrets.AUTH_TOKEN
        except:
            # If not in Streamlit context, try environment variable
            self.auth_token = os.environ.get("AUTH_TOKEN")
            
        if self.auth_token:
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"API Error: {str(e)}")
            return {}
    
    # Authentication
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user"""
        response = self._make_request(
            "POST",
            "/api/v1/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.get("access_token"):
            self.auth_token = response["access_token"]
            self.session.headers.update({
                "Authorization": f"Bearer {self.auth_token}"
            })
            st.session_state.auth_token = self.auth_token
            
        return response
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info"""
        return self._make_request("GET", "/api/v1/auth/me")
    
    # Enterprise Sales APIs
    def create_lead(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create sales lead"""
        return self._make_request("POST", "/api/v1/sales/leads", json=lead_data)
    
    def get_leads(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get sales leads"""
        params = {}
        if status:
            params["status"] = status
        return self._make_request("GET", "/api/v1/sales/leads", params=params)
    
    def update_lead(self, lead_id: str, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update lead"""
        return self._make_request("PUT", f"/api/v1/sales/leads/{lead_id}", json=update_data)
    
    def create_activity(self, lead_id: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create sales activity"""
        return self._make_request(
            "POST", 
            f"/api/v1/sales/leads/{lead_id}/activities", 
            json=activity_data
        )
    
    def create_opportunity(self, opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create sales opportunity"""
        return self._make_request("POST", "/api/v1/sales/opportunities", json=opportunity_data)
    
    def get_pipeline_metrics(self, date_from: Optional[str] = None) -> Dict[str, Any]:
        """Get sales pipeline metrics"""
        params = {}
        if date_from:
            params["date_from"] = date_from
        return self._make_request("GET", "/api/v1/sales/metrics/pipeline", params=params)
    
    def calculate_custom_pricing(self, pricing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate custom enterprise pricing"""
        return self._make_request("POST", "/api/v1/sales/pricing/calculate", json=pricing_data)
    
    def schedule_demo(self, demo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule product demo"""
        return self._make_request("POST", "/api/v1/sales/demos", json=demo_data)
    
    def create_trial(self, trial_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create trial account"""
        return self._make_request("POST", "/api/v1/sales/trials", json=trial_data)
    
    # Customer Support APIs
    def create_ticket(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create support ticket"""
        return self._make_request("POST", "/api/v1/support/tickets", json=ticket_data)
    
    def get_tickets(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get support tickets"""
        params = {}
        if status:
            params["status"] = status
        return self._make_request("GET", "/api/v1/support/tickets", params=params)
    
    def add_ticket_message(self, ticket_id: str, message_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add message to ticket"""
        return self._make_request(
            "POST",
            f"/api/v1/support/tickets/{ticket_id}/messages",
            json=message_data
        )
    
    def search_knowledge_base(self, query: str, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        params = {"q": query}
        if category:
            params["category"] = category
        return self._make_request("GET", "/api/v1/support/kb/search", params=params)
    
    def start_live_chat(self, chat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Start live chat session"""
        return self._make_request("POST", "/api/v1/support/chat/start", json=chat_data)
    
    def submit_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit customer feedback"""
        return self._make_request("POST", "/api/v1/support/feedback", json=feedback_data)
    
    def get_support_metrics(self) -> Dict[str, Any]:
        """Get support metrics"""
        return self._make_request("GET", "/api/v1/support/metrics")
    
    # Compliance & Security APIs
    def record_consent(self, consent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Record user consent"""
        return self._make_request("POST", "/api/v1/compliance/consent", json=consent_data)
    
    def get_my_consents(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """Get user's consent records"""
        params = {"active_only": active_only}
        return self._make_request("GET", "/api/v1/compliance/consent", params=params)
    
    def withdraw_consent(self, consent_id: str, reason: Optional[str] = None) -> Dict[str, Any]:
        """Withdraw consent"""
        data = {}
        if reason:
            data["reason"] = reason
        return self._make_request("DELETE", f"/api/v1/compliance/consent/{consent_id}", json=data)
    
    def submit_data_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit GDPR data subject request"""
        return self._make_request("POST", "/api/v1/compliance/data-subject-request", json=request_data)
    
    def export_my_data(self, format: str = "json") -> Dict[str, Any]:
        """Export user data"""
        params = {"format": format}
        return self._make_request("GET", "/api/v1/compliance/my-data", params=params)
    
    def get_audit_logs(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Get audit logs (admin only)"""
        return self._make_request("GET", "/api/v1/compliance/audit-logs", params=filters)
    
    def get_security_posture(self) -> Dict[str, Any]:
        """Get security posture assessment"""
        return self._make_request("GET", "/api/v1/compliance/security-posture")
    
    # API Platform APIs
    def create_api_key(self, key_config: Dict[str, Any]) -> Dict[str, Any]:
        """Create API key"""
        return self._make_request("POST", "/api/v1/developer/api-keys", json=key_config)
    
    def list_api_keys(self) -> List[Dict[str, Any]]:
        """List API keys"""
        return self._make_request("GET", "/api/v1/developer/api-keys")
    
    def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        """Revoke API key"""
        return self._make_request("DELETE", f"/api/v1/developer/api-keys/{key_id}")
    
    def create_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create webhook"""
        return self._make_request("POST", "/api/v1/developer/webhooks", json=webhook_data)
    
    def list_webhooks(self) -> List[Dict[str, Any]]:
        """List webhooks"""
        return self._make_request("GET", "/api/v1/developer/webhooks")
    
    def get_api_usage(self, date_from: Optional[str] = None) -> Dict[str, Any]:
        """Get API usage statistics"""
        params = {}
        if date_from:
            params["date_from"] = date_from
        return self._make_request("GET", "/api/v1/developer/usage", params=params)
    
    def get_sdks(self) -> List[Dict[str, Any]]:
        """Get available SDKs"""
        return self._make_request("GET", "/api/v1/developer/sdks")
    
    # Marketing & Growth APIs
    def create_campaign(self, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create marketing campaign"""
        return self._make_request("POST", "/api/v1/marketing/campaigns", json=campaign_data)
    
    def list_campaigns(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List campaigns"""
        params = {}
        if status:
            params["status"] = status
        return self._make_request("GET", "/api/v1/marketing/campaigns", params=params)
    
    def create_email_campaign(self, campaign_id: str, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create email campaign"""
        email_data["campaign_id"] = campaign_id
        return self._make_request("POST", "/api/v1/marketing/email-campaigns", json=email_data)
    
    def create_referral_program(self, program_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create referral program"""
        return self._make_request("POST", "/api/v1/marketing/referral-programs", json=program_data)
    
    def generate_referral_code(self, program_id: str) -> Dict[str, Any]:
        """Generate referral code"""
        return self._make_request(
            "POST", 
            "/api/v1/marketing/referrals/generate",
            json={"program_id": program_id}
        )
    
    def get_referral_stats(self) -> Dict[str, Any]:
        """Get referral statistics"""
        return self._make_request("GET", "/api/v1/marketing/referrals/stats")
    
    def get_growth_metrics(self, date_from: Optional[str] = None) -> Dict[str, Any]:
        """Get growth analytics"""
        params = {}
        if date_from:
            params["date_from"] = date_from
        return self._make_request("GET", "/api/v1/marketing/analytics/growth", params=params)
    
    def create_ab_test(self, test_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create A/B test"""
        return self._make_request("POST", "/api/v1/marketing/ab-tests", json=test_data)
    
    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results"""
        return self._make_request("GET", f"/api/v1/marketing/ab-tests/{test_id}")
    
    def create_content(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create marketing content"""
        return self._make_request("POST", "/api/v1/marketing/content", json=content_data)
    
    def get_content_performance(self, content_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get content performance metrics"""
        params = {}
        if content_type:
            params["content_type"] = content_type
        return self._make_request("GET", "/api/v1/marketing/content/performance", params=params)
    
    # Core Transcription APIs
    def create_transcription(self, file_path: str, language: str = "en-US", **options) -> Dict[str, Any]:
        """Create a new transcription"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = {
                'language': language,
                **options
            }
            return self._make_request("POST", "/api/transcription/upload", files=files, data=data)
    
    def get_transcription_status(self, transcription_id: str) -> Dict[str, Any]:
        """Get transcription status"""
        return self._make_request("GET", f"/api/transcription/status/{transcription_id}")
    
    def get_transcription_result(self, transcription_id: str) -> Dict[str, Any]:
        """Get transcription result"""
        return self._make_request("GET", f"/api/transcription/result/{transcription_id}")
    
    # Text-to-Speech APIs
    def synthesize_speech(self, text: str, voice: str = "en-US-Standard-A", **options) -> Dict[str, Any]:
        """Synthesize speech from text"""
        data = {
            "text": text,
            "voice": voice,
            **options
        }
        return self._make_request("POST", "/api/v1/tts/synthesize", json=data)
    
    def get_tts_voices(self, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get available TTS voices"""
        params = {}
        if language:
            params["language"] = language
        return self._make_request("GET", "/api/v1/tts/voices", params=params)
    
    # Audio Enhancement APIs
    def enhance_audio(self, audio_data: str, **enhancement_options) -> Dict[str, Any]:
        """Enhance audio with various processing options"""
        data = {
            "audio_data": audio_data,
            "enhancement_options": enhancement_options
        }
        return self._make_request("POST", "/api/v1/audio/enhance", json=data)
    
    def get_audio_enhancement_presets(self) -> Dict[str, Any]:
        """Get available audio enhancement presets"""
        return self._make_request("GET", "/api/v1/audio/presets")
    
    # OCR APIs
    def extract_text_from_image(self, image_data: str, language: str = "en", **options) -> Dict[str, Any]:
        """Extract text from image using OCR"""
        data = {
            "image_data": image_data,
            "language": language,
            "extract_tables": options.get("extract_tables", True),
            "enhance_image": options.get("enhance_image", True)
        }
        return self._make_request("POST", "/api/v1/ocr/extract", json=data)
    
    def get_ocr_languages(self) -> Dict[str, Any]:
        """Get supported OCR languages"""
        return self._make_request("GET", "/api/v1/ocr/languages")
    
    # Named Entity Recognition APIs
    def extract_entities(self, text: str, entity_types: Optional[List[str]] = None) -> Dict[str, Any]:
        """Extract named entities from text"""
        data = {
            "text": text,
            "entity_types": entity_types or []
        }
        return self._make_request("POST", "/api/v1/ner/extract", json=data)
    
    def get_entity_types(self) -> List[str]:
        """Get supported entity types"""
        response = self._make_request("GET", "/api/v1/ner/entity-types")
        return response.get("entity_types", [])
    
    # Media Processing APIs
    def process_media_file(self, file_path: str, **options) -> Dict[str, Any]:
        """Process media file (audio/video)"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            data = options
            return self._make_request("POST", "/api/v1/media/process", files=files, data=data)
    
    def get_media_info(self, file_path: str) -> Dict[str, Any]:
        """Get media file information"""
        with open(file_path, 'rb') as f:
            files = {'file': f}
            return self._make_request("POST", "/api/v1/media/info", files=files)
    
    # Search APIs
    def search_transcripts(self, query: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Search through transcripts"""
        data = {
            "query": query,
            "filters": filters or {}
        }
        return self._make_request("POST", "/api/search", json=data)
    
    # Export APIs
    def export_transcript(self, transcript_id: str, format: str = "json") -> Dict[str, Any]:
        """Export transcript in various formats"""
        data = {
            "transcript_id": transcript_id,
            "format": format
        }
        return self._make_request("POST", "/api/export", json=data)
    
    # Analytics APIs
    def get_analytics_dashboard(self, date_range: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Get analytics dashboard data"""
        params = date_range or {}
        return self._make_request("GET", "/api/analytics/dashboard", params=params)
    
    # Collaboration APIs
    def create_comment(self, transcript_id: str, text: str, **kwargs) -> Dict[str, Any]:
        """Create a comment on a transcript"""
        data = {
            "transcript_id": transcript_id,
            "text": text,
            **kwargs
        }
        return self._make_request("POST", "/api/v1/collaboration/comments", json=data)
    
    def get_transcript_comments(self, transcript_id: str) -> List[Dict[str, Any]]:
        """Get all comments for a transcript"""
        return self._make_request("GET", f"/api/v1/collaboration/comments/{transcript_id}")
    
    # History APIs
    def get_transcription_history(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """Get transcription history"""
        params = {
            "limit": limit,
            "offset": offset
        }
        return self._make_request("GET", "/api/history", params=params)
    
    # Settings APIs
    def get_user_settings(self) -> Dict[str, Any]:
        """Get user settings"""
        return self._make_request("GET", "/api/settings")
    
    def update_user_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        """Update user settings"""
        return self._make_request("PUT", "/api/settings", json=settings)


# Singleton instance
_api_client_instance = None

def get_api_client() -> APIClient:
    """Get or create API client instance"""
    global _api_client_instance
    if _api_client_instance is None:
        _api_client_instance = APIClient()
    return _api_client_instance