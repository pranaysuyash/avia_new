"""
Comprehensive test suite for intelligence systems
Tests for Content Intelligence, Media Asset Intelligence, and Business Intelligence
"""

import pytest
import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import json
from unittest.mock import Mock, MagicMock, patch, AsyncMock
import cv2

# Import the systems to test
from advanced_content_intelligence import (
    AdvancedContentIntelligence,
    ContentMetadata,
    ContentType,
    ContentCategory
)
from media_asset_intelligence import (
    MediaAssetIntelligence,
    MediaAssetMetadata,
    MediaType,
    SceneInfo,
    SceneType,
    HighlightSegment
)
from business_intelligence_roi import (
    BusinessIntelligenceSystem,
    ROIMetrics,
    BusinessMetrics,
    ChurnPrediction,
    RevenueForcast,
    MetricType
)


# Fixtures
@pytest.fixture
def mock_db_session():
    """Create mock database session"""
    session = MagicMock()
    return session


@pytest.fixture
def content_intelligence(mock_db_session):
    """Create ContentIntelligence instance"""
    with patch('advanced_content_intelligence.spacy.load') as mock_spacy:
        mock_spacy.return_value = MagicMock()
        return AdvancedContentIntelligence(mock_db_session)


@pytest.fixture
def media_intelligence(mock_db_session):
    """Create MediaIntelligence instance"""
    with patch('media_asset_intelligence.face_recognition'):
        return MediaAssetIntelligence(mock_db_session)


@pytest.fixture
def business_intelligence(mock_db_session):
    """Create BusinessIntelligence instance"""
    return BusinessIntelligenceSystem(mock_db_session)


@pytest.fixture
def sample_text():
    """Sample text for content analysis"""
    return """
    Artificial Intelligence is transforming the technology landscape. 
    Companies like Google, Microsoft, and OpenAI are leading the charge 
    in developing advanced AI systems. The impact on business productivity 
    has been remarkable, with automation reducing costs by up to 30%.
    Machine learning models are becoming increasingly sophisticated.
    """


@pytest.fixture
def sample_video_path(tmp_path):
    """Create a temporary video file for testing"""
    video_path = tmp_path / "test_video.mp4"
    
    # Create a simple video using OpenCV
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
    
    # Write 30 frames (1 second of video)
    for i in range(30):
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 255
        # Add some variation to simulate content
        cv2.putText(frame, f"Frame {i}", (50, 50), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        out.write(frame)
    
    out.release()
    return str(video_path)


# Content Intelligence Tests

class TestContentIntelligence:
    """Test suite for Content Intelligence System"""
    
    @pytest.mark.asyncio
    async def test_analyze_content_basic(self, content_intelligence, sample_text):
        """Test basic content analysis"""
        # Mock the NLP models
        content_intelligence.sentiment_analyzer = MagicMock(
            return_value=[{'label': 'POSITIVE', 'score': 0.8}]
        )
        
        result = await content_intelligence.analyze_content(
            content=sample_text,
            content_id="test_001",
            title="AI Technology Article",
            content_type=ContentType.DOCUMENT,
            deep_analysis=False
        )
        
        assert isinstance(result, ContentMetadata)
        assert result.content_id == "test_001"
        assert result.title == "AI Technology Article"
        assert result.type == ContentType.DOCUMENT
        assert result.word_count > 0
    
    @pytest.mark.asyncio
    async def test_entity_extraction(self, content_intelligence, sample_text):
        """Test entity extraction"""
        # Mock NLP doc
        mock_doc = MagicMock()
        mock_ent1 = MagicMock(label_="ORG", text="Google")
        mock_ent2 = MagicMock(label_="ORG", text="Microsoft")
        mock_ent3 = MagicMock(label_="PERCENT", text="30%")
        mock_doc.ents = [mock_ent1, mock_ent2, mock_ent3]
        
        content_intelligence.nlp.return_value = mock_doc
        
        entities = await content_intelligence._extract_entities(sample_text)
        
        assert "ORG" in entities
        assert "Google" in entities["ORG"]
        assert "Microsoft" in entities["ORG"]
        assert "PERCENT" in entities
    
    @pytest.mark.asyncio
    async def test_keyword_extraction(self, content_intelligence, sample_text):
        """Test keyword extraction"""
        keywords = await content_intelligence._extract_keywords(sample_text, top_n=5)
        
        assert isinstance(keywords, list)
        assert len(keywords) <= 5
        if keywords:
            assert isinstance(keywords[0], tuple)
            assert isinstance(keywords[0][0], str)
            assert isinstance(keywords[0][1], float)
    
    @pytest.mark.asyncio
    async def test_sentiment_analysis(self, content_intelligence, sample_text):
        """Test sentiment analysis"""
        content_intelligence.sentiment_analyzer = MagicMock(
            return_value=[{'label': 'POSITIVE', 'score': 0.85}]
        )
        
        sentiment = await content_intelligence._analyze_sentiment(sample_text)
        
        assert isinstance(sentiment, dict)
        assert 'positive' in sentiment
        assert 'negative' in sentiment
        assert 'neutral' in sentiment
        assert 0 <= sentiment['positive'] <= 1
    
    @pytest.mark.asyncio
    async def test_category_classification(self, content_intelligence, sample_text):
        """Test content category classification"""
        content_intelligence.zero_shot_classifier = MagicMock(
            return_value={
                'labels': ['technology'],
                'scores': [0.9]
            }
        )
        
        category = await content_intelligence._classify_category(
            sample_text, 
            "AI Technology"
        )
        
        assert category == ContentCategory.TECHNOLOGY
    
    @pytest.mark.asyncio
    async def test_quality_score_calculation(self, content_intelligence, sample_text):
        """Test content quality score calculation"""
        quality_score = await content_intelligence._calculate_quality_score(sample_text)
        
        assert isinstance(quality_score, float)
        assert 0 <= quality_score <= 1
    
    @pytest.mark.asyncio
    async def test_readability_calculation(self, content_intelligence, sample_text):
        """Test readability score calculation"""
        readability = await content_intelligence._calculate_readability(sample_text)
        
        assert isinstance(readability, float)
        assert 0 <= readability <= 1
    
    @pytest.mark.asyncio
    async def test_tag_generation(self, content_intelligence):
        """Test tag generation"""
        metadata = ContentMetadata(
            content_id="test",
            title="Test",
            type=ContentType.DOCUMENT,
            category=ContentCategory.TECHNOLOGY,
            keywords=[("ai", 0.8), ("machine_learning", 0.7)],
            entities={"ORG": ["Google", "Microsoft"]},
            topics=[("artificial_intelligence", 0.9)],
            sentiment={"positive": 0.8, "negative": 0.1, "neutral": 0.1}
        )
        
        tags = await content_intelligence._generate_tags(sample_text, metadata)
        
        assert isinstance(tags, list)
        assert len(tags) > 0
        assert "technology" in tags
    
    @pytest.mark.asyncio
    async def test_content_clustering(self, content_intelligence):
        """Test content clustering"""
        # Add some content to cache
        content_intelligence.content_embeddings = {
            "doc1": np.random.rand(384),
            "doc2": np.random.rand(384),
            "doc3": np.random.rand(384),
            "doc4": np.random.rand(384)
        }
        
        clusters = await content_intelligence.cluster_content(
            content_ids=["doc1", "doc2", "doc3", "doc4"],
            num_clusters=2
        )
        
        assert isinstance(clusters, dict)
        assert len(clusters) <= 2
        assert all(isinstance(v, list) for v in clusters.values())
    
    def test_syllable_counting(self, content_intelligence):
        """Test syllable counting for readability"""
        assert content_intelligence._count_syllables("hello") == 2
        assert content_intelligence._count_syllables("world") == 1
        assert content_intelligence._count_syllables("beautiful") == 3
        assert content_intelligence._count_syllables("a") == 1


# Media Asset Intelligence Tests

class TestMediaAssetIntelligence:
    """Test suite for Media Asset Intelligence System"""
    
    @pytest.mark.asyncio
    async def test_analyze_media_asset_basic(self, media_intelligence):
        """Test basic media asset analysis"""
        with patch('media_asset_intelligence.VideoFileClip') as mock_clip:
            mock_clip.return_value.duration = 60.0
            mock_clip.return_value.w = 1920
            mock_clip.return_value.h = 1080
            mock_clip.return_value.fps = 30.0
            mock_clip.return_value.close = MagicMock()
            
            result = await media_intelligence.analyze_media_asset(
                file_path="test.mp4",
                asset_id="asset_001",
                media_type=MediaType.VIDEO,
                deep_analysis=False,
                extract_highlights=False
            )
            
            assert isinstance(result, MediaAssetMetadata)
            assert result.asset_id == "asset_001"
            assert result.duration == 60.0
            assert result.width == 1920
            assert result.height == 1080
    
    @pytest.mark.asyncio
    async def test_scene_detection(self, media_intelligence):
        """Test scene detection"""
        with patch('media_asset_intelligence.VideoManager'), \
             patch('media_asset_intelligence.SceneManager') as mock_scene_mgr:
            
            mock_scene_mgr.return_value.get_scene_list.return_value = [
                (MagicMock(get_seconds=lambda: 0), MagicMock(get_seconds=lambda: 10)),
                (MagicMock(get_seconds=lambda: 10), MagicMock(get_seconds=lambda: 20))
            ]
            
            scenes = await media_intelligence._detect_scenes("test.mp4")
            
            assert len(scenes) == 2
            assert isinstance(scenes[0], SceneInfo)
            assert scenes[0].start_time == 0
            assert scenes[0].end_time == 10
            assert scenes[0].duration == 10
    
    @pytest.mark.asyncio
    async def test_visual_feature_extraction(self, media_intelligence):
        """Test visual feature extraction"""
        metadata = MediaAssetMetadata(
            asset_id="test",
            file_path="test.mp4",
            media_type=MediaType.VIDEO
        )
        
        with patch('cv2.VideoCapture') as mock_cap:
            mock_cap.return_value.get.return_value = 100  # frame count
            mock_cap.return_value.read.return_value = (True, np.ones((480, 640, 3), dtype=np.uint8))
            
            result = await media_intelligence._extract_visual_features("test.mp4", metadata)
            
            assert result.quality_score >= 0
            assert result.visual_style is not None
            assert isinstance(result.color_palette, list)
    
    @pytest.mark.asyncio
    async def test_highlight_extraction(self, media_intelligence):
        """Test highlight extraction"""
        metadata = MediaAssetMetadata(
            asset_id="test",
            file_path="test.mp4",
            media_type=MediaType.VIDEO,
            scenes=[
                SceneInfo(
                    scene_id="s1",
                    start_time=0,
                    end_time=10,
                    duration=10,
                    scene_type=SceneType.ACTION,
                    confidence=0.9,
                    motion_intensity=0.8,
                    audio_intensity=0.7
                ),
                SceneInfo(
                    scene_id="s2",
                    start_time=10,
                    end_time=20,
                    duration=10,
                    scene_type=SceneType.DIALOGUE,
                    confidence=0.8,
                    motion_intensity=0.3,
                    audio_intensity=0.5
                )
            ]
        )
        
        highlights = await media_intelligence._extract_highlights("test.mp4", metadata)
        
        assert isinstance(highlights, list)
        if highlights:
            assert isinstance(highlights[0], HighlightSegment)
            assert highlights[0].score >= 0
            assert highlights[0].reason != ""
    
    @pytest.mark.asyncio
    async def test_thumbnail_generation(self, media_intelligence):
        """Test smart thumbnail generation"""
        metadata = MediaAssetMetadata(
            asset_id="test",
            file_path="test.mp4",
            media_type=MediaType.VIDEO,
            duration=60.0,
            scenes=[],
            highlights=[]
        )
        
        with patch('cv2.VideoCapture') as mock_cap, \
             patch('cv2.imwrite') as mock_write:
            mock_cap.return_value.read.return_value = (True, np.ones((480, 640, 3), dtype=np.uint8))
            mock_write.return_value = True
            
            result = await media_intelligence._generate_smart_thumbnails("test.mp4", metadata)
            
            assert result.hero_thumbnail is not None
            assert len(result.timeline_thumbnails) > 0
    
    @pytest.mark.asyncio
    async def test_chapter_generation(self, media_intelligence):
        """Test auto-chapter generation"""
        metadata = MediaAssetMetadata(
            asset_id="test",
            file_path="test.mp4",
            media_type=MediaType.VIDEO,
            scenes=[
                SceneInfo("s1", 0, 40, 40, SceneType.INTRO, 0.9),
                SceneInfo("s2", 40, 100, 60, SceneType.CONTENT, 0.9),
                SceneInfo("s3", 100, 150, 50, SceneType.CONTENT, 0.9),
                SceneInfo("s4", 150, 180, 30, SceneType.OUTRO, 0.9)
            ]
        )
        
        chapters = await media_intelligence._generate_chapters(metadata)
        
        assert isinstance(chapters, list)
        assert len(chapters) > 0
        if chapters:
            assert 'title' in chapters[0]
            assert 'start_time' in chapters[0]
            assert 'end_time' in chapters[0]
    
    @pytest.mark.asyncio
    async def test_viral_potential_calculation(self, media_intelligence):
        """Test viral potential calculation"""
        metadata = MediaAssetMetadata(
            asset_id="test",
            file_path="test.mp4",
            media_type=MediaType.VIDEO,
            duration=120,  # 2 minutes - optimal
            quality_score=0.8,
            unique_faces=3,
            highlights=[
                HighlightSegment("h1", 0, 10, 0.9, "High action"),
                HighlightSegment("h2", 20, 30, 0.8, "Emotional moment")
            ],
            scenes=[
                SceneInfo("s1", 0, 30, 30, SceneType.ACTION, 0.9),
                SceneInfo("s2", 30, 60, 30, SceneType.INTERVIEW, 0.9)
            ],
            visual_style="bright_vibrant"
        )
        
        score = await media_intelligence._calculate_viral_potential(metadata)
        
        assert isinstance(score, float)
        assert 0 <= score <= 1
    
    @pytest.mark.asyncio
    async def test_edit_suggestions(self, media_intelligence):
        """Test video edit suggestions"""
        metadata = MediaAssetMetadata(
            asset_id="test",
            file_path="test.mp4",
            media_type=MediaType.VIDEO,
            duration=600,  # 10 minutes
            scenes=[
                SceneInfo("s1", 0, 90, 90, SceneType.CONTENT, 0.9, 
                         motion_intensity=0.2, brightness=0.1, sharpness=0.2),
                SceneInfo("s2", 90, 150, 60, SceneType.CONTENT, 0.9,
                         motion_intensity=0.8, brightness=0.8, sharpness=0.9)
            ],
            highlights=[
                HighlightSegment("h1", 100, 110, 0.9, "Peak moment"),
                HighlightSegment("h2", 120, 130, 0.85, "Great dialogue"),
                HighlightSegment("h3", 140, 150, 0.8, "Action sequence")
            ]
        )
        
        suggestions = await media_intelligence._generate_edit_suggestions(metadata)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        if suggestions:
            assert 'type' in suggestions[0]
            assert 'reason' in suggestions[0]
    
    def test_image_quality_calculation(self, media_intelligence):
        """Test image quality calculation"""
        # Create test image with known characteristics
        image = np.ones((480, 640), dtype=np.uint8) * 128  # Gray image
        
        quality = media_intelligence._calculate_image_quality(image)
        
        assert isinstance(quality, float)
        assert 0 <= quality <= 1


# Business Intelligence Tests

class TestBusinessIntelligence:
    """Test suite for Business Intelligence System"""
    
    @pytest.mark.asyncio
    async def test_calculate_roi(self, business_intelligence, mock_db_session):
        """Test ROI calculation"""
        # Mock database queries
        with patch.object(business_intelligence, '_get_costs_from_db') as mock_costs, \
             patch.object(business_intelligence, '_get_revenue_data') as mock_revenue, \
             patch.object(business_intelligence, '_calculate_cac') as mock_cac, \
             patch.object(business_intelligence, '_calculate_ltv') as mock_ltv:
            
            mock_costs.return_value = {
                'total': 100000,
                'acquisition': 30000,
                'operational': 40000,
                'marketing': 20000,
                'infrastructure': 10000
            }
            
            mock_revenue.return_value = {
                'total': 150000,
                'subscription': 120000,
                'transaction': 20000,
                'addon': 10000
            }
            
            mock_cac.return_value = 500
            mock_ltv.return_value = 2000
            
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            
            roi = await business_intelligence.calculate_roi(start_date, end_date)
            
            assert isinstance(roi, ROIMetrics)
            assert roi.investment == 100000
            assert roi.revenue == 150000
            assert roi.profit == 50000
            assert roi.roi_percentage == 50.0
            assert roi.ltv_cac_ratio == 4.0
    
    @pytest.mark.asyncio
    async def test_get_business_metrics(self, business_intelligence):
        """Test business metrics retrieval"""
        with patch.object(business_intelligence, '_get_revenue_data') as mock_revenue, \
             patch.object(business_intelligence, '_get_costs_from_db') as mock_costs, \
             patch.object(business_intelligence, '_get_user_metrics') as mock_users, \
             patch.object(business_intelligence, '_get_engagement_metrics') as mock_engagement:
            
            mock_revenue.return_value = {'total': 100000, 'subscription': 80000, 'transaction': 15000, 'addon': 5000}
            mock_costs.return_value = {'total': 60000, 'direct': 40000}
            mock_users.return_value = {'total': 1000, 'active': 800, 'new': 100, 'churned': 50}
            mock_engagement.return_value = {'avg_duration': 15.5, 'sessions_per_user': 4.2, 'feature_adoption': 0.65}
            
            start_date = datetime.now() - timedelta(days=30)
            end_date = datetime.now()
            
            metrics = await business_intelligence.get_business_metrics(start_date, end_date)
            
            assert isinstance(metrics, BusinessMetrics)
            assert metrics.total_revenue == 100000
            assert metrics.total_users == 1000
            assert metrics.active_users == 800
            assert 0 <= metrics.retention_rate <= 1
    
    @pytest.mark.asyncio
    async def test_revenue_prediction(self, business_intelligence):
        """Test revenue forecasting"""
        with patch.object(business_intelligence, '_get_historical_revenue') as mock_historical:
            # Create synthetic historical data
            dates = pd.date_range(end=datetime.now(), periods=36, freq='M')
            revenue = np.random.uniform(50000, 100000, 36)
            mock_historical.return_value = pd.DataFrame({'date': dates, 'revenue': revenue})
            
            forecasts = await business_intelligence.predict_revenue(horizon_months=3)
            
            assert isinstance(forecasts, list)
            assert len(forecasts) == 3
            if forecasts:
                assert isinstance(forecasts[0], RevenueForcast)
                assert forecasts[0].predicted_revenue > 0
                assert len(forecasts[0].confidence_interval) == 2
    
    @pytest.mark.asyncio
    async def test_churn_prediction(self, business_intelligence):
        """Test churn prediction"""
        with patch.object(business_intelligence, '_get_active_users') as mock_users, \
             patch.object(business_intelligence, '_prepare_churn_features') as mock_features:
            
            mock_users.return_value = [
                {'id': 1, 'days_since_last_login': 35, 'total_sessions': 2, 'payment_failures': 1},
                {'id': 2, 'days_since_last_login': 5, 'total_sessions': 50, 'payment_failures': 0}
            ]
            
            mock_features.side_effect = [
                np.array([35, 2, 5, 100, 60, 3, 0.2, 1]),  # High churn risk
                np.array([5, 50, 20, 500, 90, 0, 0.8, 0])  # Low churn risk
            ]
            
            predictions = await business_intelligence.predict_churn()
            
            assert isinstance(predictions, list)
            assert len(predictions) == 2
            assert predictions[0].user_id == 1
            assert predictions[0].risk_level in ['high', 'medium', 'low']
            assert 0 <= predictions[0].churn_probability <= 1
    
    @pytest.mark.asyncio
    async def test_ltv_calculation(self, business_intelligence):
        """Test lifetime value calculation"""
        with patch.object(business_intelligence, '_get_user_data') as mock_user, \
             patch.object(business_intelligence, '_predict_remaining_lifetime') as mock_lifetime:
            
            mock_user.return_value = {
                'total_revenue': 1000,
                'monthly_revenue': 100
            }
            mock_lifetime.return_value = 12  # 12 months remaining
            
            ltv = await business_intelligence.calculate_ltv(user_id=123)
            
            assert isinstance(ltv, float)
            assert ltv == 2200  # 1000 historical + 100*12 future
    
    @pytest.mark.asyncio
    async def test_growth_opportunities(self, business_intelligence):
        """Test growth opportunity identification"""
        with patch.object(business_intelligence, '_identify_upsell_candidates') as mock_upsell, \
             patch.object(business_intelligence, '_identify_cross_sell_opportunities') as mock_cross, \
             patch.object(business_intelligence, '_get_churned_users_for_winback') as mock_winback:
            
            mock_upsell.return_value = [{
                'user_id': 1,
                'current_tier': 'basic',
                'recommended_tier': 'pro',
                'upgrade_probability': 0.7,
                'additional_revenue': 50,
                'reason': 'High usage'
            }]
            
            mock_cross.return_value = [{
                'user_id': 2,
                'products': ['addon_1', 'addon_2'],
                'purchase_probability': 0.6,
                'revenue': 30,
                'reason': 'Complementary features'
            }]
            
            mock_winback.return_value = [{
                'id': 3,
                'churned_date': datetime.now() - timedelta(days=60),
                'previous_revenue': 200,
                'win_back_prob': 0.4,
                'offer': '20% discount',
                'potential_revenue': 160
            }]
            
            opportunities = await business_intelligence.identify_growth_opportunities()
            
            assert isinstance(opportunities, dict)
            assert 'upsell' in opportunities
            assert 'cross_sell' in opportunities
            assert 'win_back' in opportunities
            assert len(opportunities['upsell']) == 1
            assert len(opportunities['cross_sell']) == 1
            assert len(opportunities['win_back']) == 1
    
    @pytest.mark.asyncio
    async def test_executive_dashboard(self, business_intelligence):
        """Test executive dashboard generation"""
        with patch.object(business_intelligence, 'get_business_metrics') as mock_metrics, \
             patch.object(business_intelligence, 'predict_revenue') as mock_revenue, \
             patch.object(business_intelligence, 'predict_churn') as mock_churn, \
             patch.object(business_intelligence, 'identify_growth_opportunities') as mock_opps:
            
            # Mock current metrics
            current = BusinessMetrics(
                period_start=datetime.now() - timedelta(days=30),
                period_end=datetime.now(),
                total_revenue=100000,
                recurring_revenue=80000,
                active_users=1000,
                churned_users=50,
                total_users=1200
            )
            current.unit_economics = {'ltv': 2000, 'cac': 500}
            
            mock_metrics.return_value = current
            mock_revenue.return_value = [
                RevenueForcast(
                    forecast_date=datetime.now().date(),
                    predicted_revenue=110000,
                    confidence_interval=(100000, 120000),
                    growth_rate=0.1,
                    seasonality_factor=1.0
                )
            ]
            mock_churn.return_value = [
                ChurnPrediction(1, 0.8, 'high', [], [], None, True, 0.3)
            ]
            mock_opps.return_value = {'upsell': [], 'cross_sell': []}
            
            dashboard = await business_intelligence.generate_executive_dashboard()
            
            assert isinstance(dashboard, dict)
            assert 'summary' in dashboard
            assert 'revenue' in dashboard
            assert 'users' in dashboard
            assert 'health_scores' in dashboard
            assert dashboard['summary']['mrr'] == 80000
            assert dashboard['users']['active'] == 1000
    
    def test_seasonal_factor_calculation(self, business_intelligence):
        """Test seasonal adjustment factor"""
        from datetime import date
        
        # Q4 should have higher factor
        december = date(2024, 12, 15)
        factor_dec = business_intelligence._calculate_seasonal_factor(december)
        assert factor_dec > 1.0
        
        # Q1 should have lower factor
        february = date(2024, 2, 15)
        factor_feb = business_intelligence._calculate_seasonal_factor(february)
        assert factor_feb < 1.0
    
    def test_health_score_calculations(self, business_intelligence):
        """Test various health score calculations"""
        current = BusinessMetrics(
            period_start=datetime.now() - timedelta(days=30),
            period_end=datetime.now(),
            total_revenue=100000,
            recurring_revenue=80000,
            gross_margin=0.6,
            retention_rate=0.9,
            sessions_per_user=4,
            feature_adoption_rate=0.7,
            avg_session_duration=20,
            net_margin=0.2,
            runway_months=18
        )
        
        previous = BusinessMetrics(
            period_start=datetime.now() - timedelta(days=60),
            period_end=datetime.now() - timedelta(days=30),
            total_revenue=90000,
            recurring_revenue=70000
        )
        
        # Test revenue health
        revenue_health = business_intelligence._calculate_revenue_health_score(current, previous)
        assert 0 <= revenue_health <= 100
        
        # Test user health
        user_health = business_intelligence._calculate_user_health_score(current)
        assert 0 <= user_health <= 100
        
        # Test product health
        product_health = business_intelligence._calculate_product_health_score(current)
        assert 0 <= product_health <= 100
        
        # Test financial health
        financial_health = business_intelligence._calculate_financial_health_score(current)
        assert 0 <= financial_health <= 100


# Integration Tests

class TestIntegration:
    """Integration tests across systems"""
    
    @pytest.mark.asyncio
    async def test_content_to_media_pipeline(self, content_intelligence, media_intelligence):
        """Test integration between content and media intelligence"""
        # Analyze content first
        content_result = await content_intelligence.analyze_content(
            content="Test video transcript content",
            content_id="test_001",
            title="Test Video",
            content_type=ContentType.TRANSCRIPT
        )
        
        # Use content analysis to enhance media analysis
        assert content_result.content_id == "test_001"
        assert content_result.type == ContentType.TRANSCRIPT
    
    @pytest.mark.asyncio
    async def test_media_to_business_pipeline(self, media_intelligence, business_intelligence):
        """Test integration between media and business intelligence"""
        # Media analysis provides engagement metrics
        with patch('media_asset_intelligence.VideoFileClip'):
            media_result = await media_intelligence.analyze_media_asset(
                file_path="test.mp4",
                asset_id="asset_001",
                media_type=MediaType.VIDEO
            )
            
            # Business intelligence uses engagement for predictions
            assert media_result.viral_potential >= 0
            # This metric could feed into revenue predictions
    
    @pytest.mark.asyncio
    async def test_full_pipeline(self, content_intelligence, media_intelligence, business_intelligence):
        """Test full pipeline from content to ROI"""
        # Content analysis
        content = await content_intelligence.analyze_content(
            "Enterprise AI solutions for business",
            "c001",
            "AI Solutions"
        )
        
        # Media analysis  
        with patch('media_asset_intelligence.VideoFileClip'):
            media = await media_intelligence.analyze_media_asset(
                "solution_video.mp4",
                "m001",
                MediaType.VIDEO
            )
        
        # Business metrics
        with patch.object(business_intelligence, '_get_revenue_data'):
            metrics = await business_intelligence.get_business_metrics(
                datetime.now() - timedelta(days=30),
                datetime.now()
            )
        
        # Verify pipeline connectivity
        assert content.category in [ContentCategory.BUSINESS, ContentCategory.TECHNOLOGY]
        assert media.media_type == MediaType.VIDEO
        assert hasattr(metrics, 'total_revenue')


# Performance Tests

class TestPerformance:
    """Performance and scalability tests"""
    
    @pytest.mark.asyncio
    async def test_content_analysis_performance(self, content_intelligence):
        """Test content analysis performance"""
        import time
        
        large_text = "AI and machine learning. " * 1000  # ~5000 words
        
        start = time.time()
        result = await content_intelligence.analyze_content(
            large_text,
            "perf_test",
            "Performance Test",
            deep_analysis=False
        )
        duration = time.time() - start
        
        assert duration < 10  # Should complete within 10 seconds
        assert result.word_count > 4000
    
    @pytest.mark.asyncio
    async def test_batch_processing(self, content_intelligence):
        """Test batch content processing"""
        contents = [f"Content {i}" for i in range(10)]
        
        tasks = [
            content_intelligence.analyze_content(
                content,
                f"batch_{i}",
                f"Batch {i}",
                deep_analysis=False
            )
            for i, content in enumerate(contents)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 10
        assert all(isinstance(r, ContentMetadata) for r in results)
    
    @pytest.mark.asyncio
    async def test_concurrent_predictions(self, business_intelligence):
        """Test concurrent prediction processing"""
        with patch.object(business_intelligence, '_get_active_users') as mock_users:
            mock_users.return_value = [{'id': i} for i in range(100)]
            
            # Should handle 100 users efficiently
            predictions = await business_intelligence.predict_churn()
            
            assert len(predictions) <= 100


# Error Handling Tests

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_content_handling(self, content_intelligence):
        """Test handling of empty content"""
        result = await content_intelligence.analyze_content(
            "",
            "empty_001",
            "Empty Content"
        )
        
        assert result.word_count == 0
        assert result.quality_score >= 0
    
    @pytest.mark.asyncio
    async def test_invalid_video_handling(self, media_intelligence):
        """Test handling of invalid video file"""
        with patch('media_asset_intelligence.VideoFileClip') as mock_clip:
            mock_clip.side_effect = Exception("Invalid video file")
            
            result = await media_intelligence.analyze_media_asset(
                "invalid.mp4",
                "invalid_001",
                MediaType.VIDEO
            )
            
            assert result.asset_id == "invalid_001"
            # Should still return metadata even if analysis fails
    
    @pytest.mark.asyncio
    async def test_database_error_handling(self, business_intelligence):
        """Test handling of database errors"""
        business_intelligence.db.query.side_effect = Exception("Database error")
        
        # Should handle gracefully and return default values
        metrics = await business_intelligence.get_business_metrics(
            datetime.now() - timedelta(days=30),
            datetime.now()
        )
        
        assert metrics.total_revenue == 0
        assert metrics.total_users == 0
    
    @pytest.mark.asyncio
    async def test_ml_model_failure(self, content_intelligence):
        """Test handling when ML models fail"""
        content_intelligence.sentiment_analyzer = None
        content_intelligence.zero_shot_classifier = None
        
        # Should fall back to rule-based methods
        result = await content_intelligence.analyze_content(
            "Test content without ML models",
            "fallback_001",
            "Fallback Test"
        )
        
        assert result.sentiment == {"neutral": 1.0}
        assert result.category is None or isinstance(result.category, ContentCategory)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--asyncio-mode=auto"])