"""
Tests for Comprehensive Search System
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy.orm import Session

from services.comprehensive_search_service import (
    search_service,
    SearchType,
    SearchFilter,
    SortOption,
    SearchResult
)
from api.database import User, Transcript, Team, Media, APIKey


class TestComprehensiveSearchService:
    """Test comprehensive search service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def sample_transcripts(self):
        """Create sample transcripts"""
        transcripts = []
        for i in range(5):
            transcript = Mock(spec=Transcript)
            transcript.id = i + 1
            transcript.title = f"Test Transcript {i + 1}"
            transcript.text = f"This is sample transcript content {i + 1} with search terms"
            transcript.created_at = datetime.utcnow() - timedelta(days=i)
            transcript.user_id = 1
            transcript.duration = 300 + (i * 60)
            transcript.language = "en"
            transcript.file_path = f"/path/to/file{i + 1}.mp4"
            transcripts.append(transcript)
        return transcripts
    
    @pytest.fixture
    def sample_users(self):
        """Create sample users"""
        users = []
        for i in range(3):
            user = Mock(spec=User)
            user.id = i + 1
            user.username = f"testuser{i + 1}"
            user.email = f"test{i + 1}@example.com"
            user.full_name = f"Test User {i + 1}"
            user.created_at = datetime.utcnow() - timedelta(days=i * 10)
            users.append(user)
        return users
    
    @pytest.fixture
    def sample_teams(self):
        """Create sample teams"""
        teams = []
        for i in range(2):
            team = Mock(spec=Team)
            team.id = i + 1
            team.name = f"Test Team {i + 1}"
            team.description = f"This is a test team description {i + 1}"
            team.created_at = datetime.utcnow() - timedelta(days=i * 5)
            teams.append(team)
        return teams
    
    @pytest.mark.asyncio
    async def test_search_all_types(self, mock_db, sample_transcripts, sample_users, sample_teams):
        """Test searching across all data types"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.side_effect = [
            sample_transcripts,  # Transcripts
            sample_users,        # Users
            sample_teams,        # Teams
            []                   # Media files
        ]
        
        # Test search
        results = await search_service.search(
            db=mock_db,
            query="test",
            search_types=[SearchType.ALL],
            user_id=1
        )
        
        # Verify results
        assert "transcripts" in results
        assert "users" in results
        assert "teams" in results
        assert "media" in results
        assert len(results["transcripts"]) == 5
        assert len(results["users"]) == 3
        assert len(results["teams"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_with_filters(self, mock_db, sample_transcripts):
        """Test search with filters applied"""
        # Setup filters
        filters = SearchFilter(
            date_from=datetime.utcnow() - timedelta(days=2),
            date_to=datetime.utcnow(),
            languages=["en"],
            min_duration=300,
            max_duration=400
        )
        
        # Filter transcripts based on criteria
        filtered_transcripts = [t for t in sample_transcripts if t.duration <= 400]
        mock_db.query.return_value.filter.return_value.all.return_value = filtered_transcripts
        
        # Test search
        results = await search_service.search(
            db=mock_db,
            query="transcript",
            search_types=[SearchType.TRANSCRIPTS],
            filters=filters,
            user_id=1
        )
        
        # Verify filtering
        assert len(results["transcripts"]) <= len(sample_transcripts)
    
    @pytest.mark.asyncio
    async def test_fuzzy_search(self, mock_db, sample_transcripts):
        """Test fuzzy matching in search"""
        # Setup mocks for fuzzy search
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts
        
        # Test with typo
        results = await search_service.search(
            db=mock_db,
            query="transcirpt",  # Typo
            search_types=[SearchType.TRANSCRIPTS],
            user_id=1,
            fuzzy=True
        )
        
        # Should still find transcripts due to fuzzy matching
        assert len(results["transcripts"]) > 0
        
        # Verify relevance scores are calculated
        for result in results["transcripts"]:
            assert "relevance_score" in result
            assert 0 <= result["relevance_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_search_sorting(self, mock_db, sample_transcripts):
        """Test search result sorting"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = sorted(
            sample_transcripts,
            key=lambda x: x.created_at,
            reverse=True
        )
        
        # Test search with date sorting
        results = await search_service.search(
            db=mock_db,
            query="test",
            search_types=[SearchType.TRANSCRIPTS],
            sort_by=SortOption.DATE_DESC,
            user_id=1
        )
        
        # Verify sorting
        transcripts = results["transcripts"]
        for i in range(len(transcripts) - 1):
            assert transcripts[i]["created_at"] >= transcripts[i + 1]["created_at"]
    
    @pytest.mark.asyncio
    async def test_search_pagination(self, mock_db, sample_transcripts):
        """Test search with pagination"""
        # Setup mocks
        page_size = 2
        mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = sample_transcripts[:page_size]
        mock_db.query.return_value.filter.return_value.count.return_value = len(sample_transcripts)
        
        # Test search with pagination
        results = await search_service.search(
            db=mock_db,
            query="test",
            search_types=[SearchType.TRANSCRIPTS],
            user_id=1,
            page=1,
            page_size=page_size
        )
        
        # Verify pagination
        assert len(results["transcripts"]) <= page_size
        assert results["pagination"]["total"] == len(sample_transcripts)
        assert results["pagination"]["page"] == 1
        assert results["pagination"]["page_size"] == page_size
        assert results["pagination"]["total_pages"] == 3
    
    @pytest.mark.asyncio
    async def test_save_search_history(self, mock_db):
        """Test saving search to history"""
        # Setup mocks
        mock_db.add = Mock()
        mock_db.commit = Mock()
        
        # Save search
        await search_service.save_search_history(
            db=mock_db,
            user_id=1,
            query="test query",
            search_types=[SearchType.ALL],
            results_count=10
        )
        
        # Verify save
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_search_suggestions(self, mock_db):
        """Test getting search suggestions"""
        # Create mock search history
        history = []
        for i in range(5):
            search = Mock()
            search.query = f"test query {i}"
            search.search_count = 5 - i
            history.append(search)
        
        # Setup mocks
        mock_db.query.return_value.filter.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value = history
        
        # Get suggestions
        suggestions = await search_service.get_search_suggestions(
            db=mock_db,
            user_id=1,
            partial_query="test"
        )
        
        # Verify suggestions
        assert len(suggestions) == 5
        assert all(s["query"].startswith("test") for s in suggestions)
        # Should be ordered by frequency
        for i in range(len(suggestions) - 1):
            assert suggestions[i]["frequency"] >= suggestions[i + 1]["frequency"]
    
    @pytest.mark.asyncio
    async def test_search_with_elasticsearch(self, mock_db, sample_transcripts):
        """Test search using Elasticsearch backend"""
        # Mock Elasticsearch client
        with patch('services.comprehensive_search_service.search_service.es_client') as mock_es:
            mock_es.search.return_value = {
                "hits": {
                    "total": {"value": len(sample_transcripts)},
                    "hits": [
                        {
                            "_id": str(t.id),
                            "_score": 1.0,
                            "_source": {
                                "title": t.title,
                                "text": t.text,
                                "created_at": t.created_at.isoformat()
                            }
                        }
                        for t in sample_transcripts
                    ]
                }
            }
            
            # Enable Elasticsearch
            search_service.es_enabled = True
            
            # Test search
            results = await search_service.search(
                db=mock_db,
                query="test",
                search_types=[SearchType.TRANSCRIPTS],
                user_id=1
            )
            
            # Verify Elasticsearch was used
            mock_es.search.assert_called_once()
            assert len(results["transcripts"]) == len(sample_transcripts)
    
    @pytest.mark.asyncio
    async def test_export_search_results(self, mock_db, sample_transcripts):
        """Test exporting search results"""
        # Setup mocks
        mock_db.query.return_value.filter.return_value.all.return_value = sample_transcripts
        
        # Test CSV export
        csv_data = await search_service.export_search_results(
            db=mock_db,
            query="test",
            search_types=[SearchType.TRANSCRIPTS],
            user_id=1,
            format="csv"
        )
        
        # Verify CSV format
        assert isinstance(csv_data, bytes)
        assert b"title,text,created_at" in csv_data
        
        # Test JSON export
        json_data = await search_service.export_search_results(
            db=mock_db,
            query="test",
            search_types=[SearchType.TRANSCRIPTS],
            user_id=1,
            format="json"
        )
        
        # Verify JSON format
        parsed = json.loads(json_data)
        assert "results" in parsed
        assert "metadata" in parsed


class TestComprehensiveSearchAPI:
    """Test comprehensive search API endpoints"""
    
    @pytest.fixture
    def client(self, test_app):
        """Get test client"""
        return test_app
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        return {"Authorization": "Bearer test_token"}
    
    @pytest.mark.asyncio
    async def test_search_endpoint(self, client, auth_headers):
        """Test main search endpoint"""
        with patch('services.comprehensive_search_service.search_service.search') as mock_search:
            mock_search.return_value = {
                "transcripts": [{"id": 1, "title": "Test"}],
                "users": [],
                "teams": [],
                "media": []
            }
            
            response = await client.post(
                "/api/v1/search",
                json={
                    "query": "test",
                    "search_types": ["transcripts"]
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "transcripts" in data["results"]
    
    @pytest.mark.asyncio
    async def test_search_suggestions_endpoint(self, client, auth_headers):
        """Test search suggestions endpoint"""
        with patch('services.comprehensive_search_service.search_service.get_search_suggestions') as mock_suggestions:
            mock_suggestions.return_value = [
                {"query": "test query", "frequency": 5},
                {"query": "test search", "frequency": 3}
            ]
            
            response = await client.get(
                "/api/v1/search/suggestions?q=test",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "suggestions" in data
            assert len(data["suggestions"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_history_endpoint(self, client, auth_headers):
        """Test search history endpoint"""
        with patch('services.comprehensive_search_service.search_service.get_search_history') as mock_history:
            mock_history.return_value = [
                {
                    "query": "recent search",
                    "timestamp": datetime.utcnow().isoformat(),
                    "results_count": 10
                }
            ]
            
            response = await client.get(
                "/api/v1/search/history",
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "history" in data
            assert len(data["history"]) == 1
    
    @pytest.mark.asyncio
    async def test_save_search_endpoint(self, client, auth_headers):
        """Test saving search endpoint"""
        with patch('services.comprehensive_search_service.search_service.save_search') as mock_save:
            mock_save.return_value = {"id": "search_123", "saved": True}
            
            response = await client.post(
                "/api/v1/search/save",
                json={
                    "name": "My Search",
                    "query": "test",
                    "filters": {}
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["saved"] is True
    
    @pytest.mark.asyncio
    async def test_export_results_endpoint(self, client, auth_headers):
        """Test export results endpoint"""
        with patch('services.comprehensive_search_service.search_service.export_search_results') as mock_export:
            mock_export.return_value = b"id,title,text\n1,Test,Content"
            
            response = await client.post(
                "/api/v1/search/export",
                json={
                    "query": "test",
                    "format": "csv"
                },
                headers=auth_headers
            )
            
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/csv"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])