"""
Tests for GDPR Compliance System
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from services.gdpr_compliance_service import (
    gdpr_service,
    DataExportFormat,
    DeletionRequest,
    ConsentType,
    ConsentStatus
)
from api.database import User, Transcript, Team, AuditLog


class TestGDPRComplianceService:
    """Test GDPR compliance service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_user(self):
        """Create sample user"""
        user = Mock(spec=User)
        user.id = 1
        user.email = "test@example.com"
        user.username = "testuser"
        user.full_name = "Test User"
        user.created_at = datetime.utcnow() - timedelta(days=30)
        user.subscription_tier = "pro"
        return user
    
    @pytest.fixture
    def sample_transcripts(self):
        """Create sample transcripts"""
        transcripts = []
        for i in range(3):
            transcript = Mock(spec=Transcript)
            transcript.id = i + 1
            transcript.user_id = 1
            transcript.title = f"Transcript {i + 1}"
            transcript.text = f"Sample transcript text {i + 1}"
            transcript.created_at = datetime.utcnow() - timedelta(days=i)
            transcript.file_path = f"/path/to/file{i + 1}.mp3"
            transcript.duration = 300
            transcript.language = "en"
            transcripts.append(transcript)
        return transcripts
    
    @pytest.mark.asyncio
    async def test_export_user_data_json(self, mock_db, sample_user, sample_transcripts):
        """Test exporting user data in JSON format"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts
        
        # Test export
        result = await gdpr_service.export_user_data(
            db=mock_db,
            user_id=1,
            format=DataExportFormat.JSON
        )
        
        # Verify result
        assert result[1] == "application/json"
        
        # Parse JSON data
        data = json.loads(result[0].decode('utf-8'))
        assert data["user"]["email"] == "test@example.com"
        assert len(data["transcripts"]) == 3
        assert data["export_metadata"]["format"] == "json"
    
    @pytest.mark.asyncio
    async def test_export_user_data_pdf(self, mock_db, sample_user, sample_transcripts):
        """Test exporting user data in PDF format"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts
        
        # Test export
        result = await gdpr_service.export_user_data(
            db=mock_db,
            user_id=1,
            format=DataExportFormat.PDF
        )
        
        # Verify result
        assert result[1] == "application/pdf"
        assert len(result[0]) > 0  # PDF content exists
    
    @pytest.mark.asyncio
    async def test_request_deletion(self, mock_db, sample_user):
        """Test requesting account deletion"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Test deletion request
        request_id = await gdpr_service.request_deletion(
            db=mock_db,
            user_id=1,
            reason="No longer using service"
        )
        
        # Verify
        assert request_id is not None
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_process_deletion(self, mock_db, sample_user, sample_transcripts):
        """Test processing deletion request"""
        # Create deletion request
        deletion_request = Mock(spec=DeletionRequest)
        deletion_request.id = "del_123"
        deletion_request.user_id = 1
        deletion_request.status = "pending"
        deletion_request.created_at = datetime.utcnow()
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.side_effect = [
            deletion_request,  # First call returns deletion request
            sample_user        # Second call returns user
        ]
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        # Test processing
        with patch('services.gdpr_compliance_service.gdpr_service._delete_user_files', new_callable=AsyncMock):
            success = await gdpr_service.process_deletion_request(
                db=mock_db,
                request_id="del_123",
                admin_id=2
            )
        
        # Verify
        assert success is True
        assert deletion_request.status == "completed"
        assert mock_db.delete.call_count == 4  # User + 3 transcripts
    
    @pytest.mark.asyncio
    async def test_update_consent(self, mock_db, sample_user):
        """Test updating user consent"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Test consent update
        success = await gdpr_service.update_consent(
            db=mock_db,
            user_id=1,
            consent_type=ConsentType.MARKETING,
            status=ConsentStatus.GRANTED
        )
        
        # Verify
        assert success is True
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_user_consents(self, mock_db):
        """Test retrieving user consents"""
        # Create mock consents
        consents = []
        for consent_type in [ConsentType.MARKETING, ConsentType.ANALYTICS]:
            consent = Mock()
            consent.consent_type = consent_type.value
            consent.status = ConsentStatus.GRANTED.value
            consent.granted_at = datetime.utcnow()
            consent.ip_address = "127.0.0.1"
            consents.append(consent)
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = consents
        
        # Test getting consents
        result = await gdpr_service.get_user_consents(
            db=mock_db,
            user_id=1
        )
        
        # Verify
        assert len(result) == 2
        assert all(c["status"] == "granted" for c in result)
    
    @pytest.mark.asyncio
    async def test_apply_retention_policies(self, mock_db):
        """Test applying data retention policies"""
        # Create old transcripts
        old_transcripts = []
        for i in range(5):
            transcript = Mock(spec=Transcript)
            transcript.id = i + 1
            transcript.created_at = datetime.utcnow() - timedelta(days=400)  # Older than retention period
            old_transcripts.append(transcript)
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.return_value = old_transcripts
        mock_db.delete = Mock()
        mock_db.commit = Mock()
        
        # Test retention policies
        with patch('services.gdpr_compliance_service.gdpr_service._delete_transcript_files', new_callable=AsyncMock):
            deleted_count = await gdpr_service.apply_retention_policies(mock_db)
        
        # Verify
        assert deleted_count == 5
        assert mock_db.delete.call_count == 5
    
    def test_anonymize_user_data(self):
        """Test user data anonymization"""
        # Create user data
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "full_name": "Test User",
            "ip_address": "192.168.1.1",
            "phone": "+1234567890"
        }
        
        # Test anonymization
        anonymized = gdpr_service._anonymize_user_data(user_data)
        
        # Verify
        assert anonymized["email"] != user_data["email"]
        assert "@" in anonymized["email"]  # Still valid email format
        assert anonymized["username"].startswith("anon_")
        assert anonymized["full_name"] == "Anonymous User"
        assert anonymized["ip_address"] == "0.0.0.0"
        assert "phone" not in anonymized  # Removed entirely
    
    @pytest.mark.asyncio
    async def test_get_data_categories(self, mock_db):
        """Test retrieving data categories"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.count.side_effect = [
            10,  # Transcripts
            5,   # Teams
            3,   # API keys
            100  # Audit logs
        ]
        
        # Test getting categories
        categories = await gdpr_service.get_data_categories(
            db=mock_db,
            user_id=1
        )
        
        # Verify
        assert len(categories) == 5  # Profile + 4 categories
        assert categories[0]["name"] == "Profile Information"
        assert categories[1]["count"] == 10  # Transcripts
        assert categories[1]["deletable"] is True
    
    @pytest.mark.asyncio
    async def test_generate_privacy_report(self, mock_db, sample_user):
        """Test generating privacy report"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.first.return_value = sample_user
        mock_db.query.return_value.filter.return_value.count.return_value = 10
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        
        # Test report generation
        report = await gdpr_service.generate_privacy_report(
            db=mock_db,
            user_id=1
        )
        
        # Verify
        assert report["user_id"] == 1
        assert "data_collected" in report
        assert "data_shared" in report
        assert "consent_history" in report
        assert "retention_period" in report
        assert report["rights"]["access"] is True
        assert report["rights"]["deletion"] is True


class TestGDPRComplianceAPI:
    """Test GDPR compliance API endpoints"""
    
    @pytest.fixture
    def client(self, test_app):
        """Get test client"""
        return test_app
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        return {"Authorization": "Bearer test_token"}
    
    @pytest.mark.asyncio
    async def test_export_data_endpoint(self, client, auth_headers):
        """Test data export endpoint"""
        with patch('services.gdpr_compliance_service.gdpr_service.export_user_data') as mock_export:
            mock_export.return_value = (b'{"data": "test"}', "application/json")
            
            response = await client.post(
                "/api/v1/gdpr/export",
                json={"format": "json"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/json"
    
    @pytest.mark.asyncio
    async def test_request_deletion_endpoint(self, client, auth_headers):
        """Test deletion request endpoint"""
        with patch('services.gdpr_compliance_service.gdpr_service.request_deletion') as mock_delete:
            mock_delete.return_value = "del_123"
            
            response = await client.post(
                "/api/v1/gdpr/delete",
                json={"reason": "No longer needed"},
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["request_id"] == "del_123"
            assert data["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_update_consent_endpoint(self, client, auth_headers):
        """Test consent update endpoint"""
        with patch('services.gdpr_compliance_service.gdpr_service.update_consent') as mock_consent:
            mock_consent.return_value = True
            
            response = await client.post(
                "/api/v1/gdpr/consent",
                json={
                    "consent_type": "marketing",
                    "status": "granted"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
    
    @pytest.mark.asyncio
    async def test_get_consents_endpoint(self, client, auth_headers):
        """Test get consents endpoint"""
        mock_consents = [
            {
                "consent_type": "marketing",
                "status": "granted",
                "granted_at": datetime.utcnow().isoformat()
            }
        ]
        
        with patch('services.gdpr_compliance_service.gdpr_service.get_user_consents') as mock_get:
            mock_get.return_value = mock_consents
            
            response = await client.get(
                "/api/v1/gdpr/consent",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["consents"]) == 1
            assert data["consents"][0]["consent_type"] == "marketing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])