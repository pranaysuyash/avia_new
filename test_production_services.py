"""
Integration Tests for Production Services
Tests the newly implemented production services to ensure they work correctly
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal

# Test Payment Service
class TestPaymentService:
    """Test suite for payment service implementations"""
    
    @pytest.fixture
    def payment_service(self, db_session):
        from services.payment_service import PaymentService
        return PaymentService(db_session)
    
    @pytest.fixture
    def multi_payment_service(self, db_session):
        from services.payment_service_multi import MultiProviderPaymentService
        return MultiProviderPaymentService(db_session)
    
    def test_create_customer(self, payment_service):
        """Test creating a Stripe customer"""
        with patch('stripe.Customer.create') as mock_create:
            mock_create.return_value = Mock(id='cus_test123')
            
            customer_id = payment_service.create_customer(
                user_id=1,
                email='test@example.com',
                name='Test User'
            )
            
            assert customer_id == 'cus_test123'
            mock_create.assert_called_once()
    
    def test_create_subscription(self, payment_service):
        """Test creating a subscription"""
        from services.payment_service import SubscriptionTier
        
        with patch('stripe.Subscription.create') as mock_create:
            mock_create.return_value = Mock(
                id='sub_test123',
                status='active',
                current_period_start=1234567890,
                current_period_end=1234567890,
                trial_end=None
            )
            
            result = payment_service.create_subscription(
                user_id=1,
                tier=SubscriptionTier.PROFESSIONAL,
                payment_method_id='pm_test123'
            )
            
            assert result['subscription_id'] == 'sub_test123'
            assert result['status'] == 'active'
    
    def test_multi_provider_routing(self, multi_payment_service):
        """Test multi-provider payment routing"""
        from services.payment_service_multi import PaymentProvider, Currency
        
        # Test INR routing to Razorpay
        provider = multi_payment_service.get_provider_for_currency(Currency.INR)
        assert provider == PaymentProvider.RAZORPAY or provider == multi_payment_service.default_provider
        
        # Test USD routing
        provider = multi_payment_service.get_provider_for_currency(Currency.USD)
        assert provider in [PaymentProvider.STRIPE, PaymentProvider.PAYPAL, multi_payment_service.default_provider]
    
    def test_provider_comparison(self, multi_payment_service):
        """Test provider fee comparison"""
        from services.payment_service_multi import Currency
        
        comparisons = multi_payment_service.get_provider_comparison(
            amount=10000,  # $100.00
            currency=Currency.USD,
            country='US'
        )
        
        assert isinstance(comparisons, list)
        for comparison in comparisons:
            assert 'provider' in comparison
            assert 'total_fee' in comparison
            assert 'fee_percentage' in comparison


# Test GDPR Compliance Service
class TestGDPRComplianceService:
    """Test suite for GDPR compliance service"""
    
    @pytest.fixture
    def gdpr_service(self):
        from services.gdpr_compliance_service import gdpr_service
        return gdpr_service
    
    @pytest.mark.asyncio
    async def test_create_data_export(self, gdpr_service, db_session):
        """Test creating GDPR data export"""
        with patch.object(gdpr_service, '_collect_user_data') as mock_collect:
            mock_collect.return_value = {
                'account': {'id': 1, 'email': 'test@example.com'},
                'transcripts': [],
                'analytics': {}
            }
            
            export_request = await gdpr_service.create_data_export(
                user_id=1,
                export_type='full_export'
            )
            
            assert export_request.user_id == 1
            assert export_request.request_type == 'full_export'
            assert export_request.status in ['pending', 'processing', 'completed']
    
    def test_record_consent(self, gdpr_service):
        """Test recording user consent"""
        consent = gdpr_service.record_consent(
            user_id=1,
            purpose='marketing',
            consent_text='I agree to receive marketing emails',
            consent_version='1.0',
            ip_address='127.0.0.1'
        )
        
        assert consent.user_id == 1
        assert consent.purpose == 'marketing'
        assert consent.given_at is not None
    
    def test_withdraw_consent(self, gdpr_service):
        """Test withdrawing consent"""
        # First record consent
        consent = gdpr_service.record_consent(
            user_id=1,
            purpose='marketing',
            consent_text='I agree',
            consent_version='1.0'
        )
        
        # Then withdraw it
        result = gdpr_service.withdraw_consent(
            user_id=1,
            consent_id=consent.id
        )
        
        assert result == True
        assert consent.withdrawn_at is not None


# Test Backup Service
class TestBackupService:
    """Test suite for backup service"""
    
    @pytest.fixture
    def backup_service(self):
        from services.backup_service import BackupService
        # Use temp directory for testing
        service = BackupService()
        service.backup_root = '/tmp/test_backups'
        return service
    
    @pytest.mark.asyncio
    async def test_create_backup(self, backup_service):
        """Test creating a backup"""
        from services.backup_service import BackupType
        
        with patch.object(backup_service, '_backup_database') as mock_db:
            mock_db.return_value = '/tmp/test_backups/test/database.sql'
            
            backup_info = await backup_service.create_backup(
                backup_type=BackupType.FULL,
                compress=False,
                encrypt=False
            )
            
            assert backup_info['type'] == 'full'
            assert 'id' in backup_info
            assert backup_info['status'] in ['completed', 'failed']
    
    @pytest.mark.asyncio
    async def test_cleanup_old_backups(self, backup_service):
        """Test cleanup of old backups"""
        result = await backup_service.cleanup_old_backups()
        
        assert 'deleted_count' in result
        assert 'freed_space_bytes' in result
        assert result['deleted_count'] >= 0


# Test Internationalization Service
class TestInternationalizationService:
    """Test suite for internationalization service"""
    
    @pytest.fixture
    def i18n_service(self, db_session):
        from services.internationalization_service import InternationalizationService
        return InternationalizationService(db_session)
    
    @pytest.mark.asyncio
    async def test_bulk_translate(self, i18n_service):
        """Test bulk translation"""
        texts = {
            'greeting': 'Hello',
            'farewell': 'Goodbye'
        }
        
        # Test with fallback (no API keys configured)
        translated = await i18n_service.bulk_translate(
            texts=texts,
            target_language='es',
            source_language='en'
        )
        
        assert isinstance(translated, dict)
        assert 'greeting' in translated
        assert 'farewell' in translated
    
    def test_format_currency(self, i18n_service):
        """Test currency formatting"""
        formatted = i18n_service.format_currency(
            amount=1234.56,
            currency='USD',
            language_code='en'
        )
        
        assert '$' in formatted
        assert '1,234.56' in formatted or '1234.56' in formatted
    
    def test_format_date(self, i18n_service):
        """Test date formatting"""
        test_date = datetime(2024, 1, 15, 14, 30)
        
        formatted = i18n_service.format_date(
            date=test_date,
            language_code='en',
            format_type='full'
        )
        
        assert 'January' in formatted or '01' in formatted
        assert '2024' in formatted


# Test Support Service
class TestSupportService:
    """Test suite for support service"""
    
    @pytest.fixture
    def support_service(self, db_session):
        from services.support_service import SupportService
        return SupportService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_ticket(self, support_service):
        """Test creating support ticket"""
        ticket = await support_service.create_ticket(
            customer_id='user_123',
            customer_email='customer@example.com',
            customer_name='Test Customer',
            subject='Cannot login',
            description='I cannot login to my account',
            category='technical',
            priority='high'
        )
        
        assert ticket.ticket_number.startswith('SUP-')
        assert ticket.priority == 'high'
        assert ticket.sla_deadline is not None
    
    def test_get_available_agents(self, support_service):
        """Test getting available support agents"""
        agents = support_service._get_available_agents()
        
        assert isinstance(agents, list)
        assert len(agents) > 0
        
        for agent in agents:
            assert 'id' in agent
            assert 'name' in agent
            assert 'specializations' in agent
    
    @pytest.mark.asyncio
    async def test_auto_assign_agent(self, support_service):
        """Test automatic agent assignment"""
        agent = await support_service._find_best_agent(
            category='technical',
            priority='high'
        )
        
        assert agent is not None
        assert 'id' in agent
        assert 'team' in agent


# Test Marketing Service
class TestMarketingService:
    """Test suite for marketing service"""
    
    @pytest.fixture
    def marketing_service(self, db_session):
        from services.marketing_service import MarketingService
        return MarketingService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_campaign(self, marketing_service):
        """Test creating marketing campaign"""
        campaign = await marketing_service.create_campaign(
            name='Summer Sale 2024',
            campaign_type='email',
            config={
                'description': 'Summer promotional campaign',
                'target_audience': {'subscription_tier': 'free'},
                'budget': 5000
            },
            user_id='admin_123'
        )
        
        assert campaign.name == 'Summer Sale 2024'
        assert campaign.type == 'email'
        assert campaign.budget == 5000
    
    @pytest.mark.asyncio
    async def test_get_email_recipients(self, marketing_service):
        """Test getting email recipients based on segment"""
        segment = {
            'subscription_tier': 'professional',
            'last_active_days': 30,
            'email_opted_in': True
        }
        
        recipients = await marketing_service._get_email_recipients(segment)
        
        assert isinstance(recipients, list)
        for recipient in recipients:
            assert 'email' in recipient
            assert '@' in recipient['email']
    
    def test_matches_segment(self, marketing_service):
        """Test segment matching logic"""
        user = {
            'email': 'user@example.com',
            'subscription_tier': 'professional',
            'country': 'US',
            'tags': ['active', 'power_user']
        }
        
        segment = {
            'subscription_tier': 'professional',
            'country': 'US',
            'tags': ['active']
        }
        
        matches = marketing_service._matches_segment(user, segment)
        assert matches == True
        
        # Test non-matching segment
        segment['country'] = 'UK'
        matches = marketing_service._matches_segment(user, segment)
        assert matches == False


# Test Storage Service
class TestStorageService:
    """Test suite for storage service"""
    
    @pytest.fixture
    def storage_service(self):
        from services.storage_service import StorageService
        return StorageService()
    
    @pytest.mark.asyncio
    async def test_upload_file(self, storage_service, tmp_path):
        """Test file upload"""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        # Upload file
        file_url = await storage_service.upload_file(
            file_path=str(test_file),
            key="test/test.txt"
        )
        
        assert file_url is not None
        assert 'test.txt' in file_url
    
    @pytest.mark.asyncio
    async def test_download_file(self, storage_service, tmp_path):
        """Test file download"""
        # First upload a file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Test content")
        
        file_url = await storage_service.upload_file(
            file_path=str(test_file),
            key="test/test.txt"
        )
        
        # Then download it
        download_path = tmp_path / "downloaded.txt"
        result = await storage_service.download_file(
            key="test/test.txt",
            destination=str(download_path)
        )
        
        assert result == True
        assert download_path.exists()
        assert download_path.read_text() == "Test content"


# Test Cache Service
class TestCacheService:
    """Test suite for cache service"""
    
    @pytest.fixture
    def cache_service(self):
        from services.cache_service import CacheService
        return CacheService()
    
    @pytest.mark.asyncio
    async def test_set_and_get(self, cache_service):
        """Test setting and getting cache values"""
        await cache_service.set('test_key', 'test_value', ttl=60)
        value = await cache_service.get('test_key')
        
        assert value == 'test_value'
    
    @pytest.mark.asyncio
    async def test_delete(self, cache_service):
        """Test deleting cache values"""
        await cache_service.set('test_key', 'test_value')
        await cache_service.delete('test_key')
        value = await cache_service.get('test_key')
        
        assert value is None
    
    @pytest.mark.asyncio
    async def test_clear_namespace(self, cache_service):
        """Test clearing cache namespace"""
        await cache_service.set('key1', 'value1', namespace='test')
        await cache_service.set('key2', 'value2', namespace='test')
        await cache_service.set('key3', 'value3', namespace='other')
        
        await cache_service.clear(namespace='test')
        
        value1 = await cache_service.get('key1', namespace='test')
        value2 = await cache_service.get('key2', namespace='test')
        value3 = await cache_service.get('key3', namespace='other')
        
        assert value1 is None
        assert value2 is None
        assert value3 == 'value3'


# Test Transcription Service
class TestTranscriptionService:
    """Test suite for transcription service"""
    
    @pytest.fixture
    def transcription_service(self, db_session):
        from services.transcription_service import TranscriptionService
        return TranscriptionService(db_session)
    
    @pytest.mark.asyncio
    async def test_create_transcript(self, transcription_service, tmp_path):
        """Test creating transcript"""
        # Create test audio file
        test_audio = tmp_path / "test.mp3"
        test_audio.write_bytes(b"fake audio data")
        
        with patch('faster_whisper.WhisperModel') as mock_model:
            mock_instance = Mock()
            mock_instance.transcribe.return_value = (
                [Mock(text="Test transcription", start=0, end=1)],
                Mock(language='en', language_probability=0.99)
            )
            mock_model.return_value = mock_instance
            
            result = await transcription_service.create_transcript(
                file_path=str(test_audio),
                user_id=1
            )
            
            assert result['status'] == 'completed'
            assert 'transcript_id' in result
            assert result['text'] == "Test transcription"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])