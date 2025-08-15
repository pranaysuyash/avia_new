#!/usr/bin/env python3
"""
Comprehensive test suite for Cross-Provider Entity Linking System.
Tests entity extraction, linking, disambiguation, and relationship extraction.
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from cross_provider_entity_linking import (
    Entity,
    EntityLink,
    EntityRelationship,
    WikipediaLinker,
    WikidataLinker,
    DBpediaLinker,
    HuggingFaceLinker,
    CrossProviderEntityLinker,
    create_entity_linker,
    link_entities_in_text
)


class TestEntityDataClasses:
    """Test entity data classes."""
    
    def test_entity_creation(self):
        """Test Entity creation and defaults."""
        entity = Entity(
            text="Apple Inc.",
            start=0,
            end=10,
            label="ORG",
            confidence=0.95
        )
        
        assert entity.text == "Apple Inc."
        assert entity.start == 0
        assert entity.end == 10
        assert entity.label == "ORG"
        assert entity.confidence == 0.95
        assert entity.aliases == []
        assert entity.properties == {}
    
    def test_entity_link_creation(self):
        """Test EntityLink creation."""
        link = EntityLink(
            mention="Apple Inc.",
            entity_id="Q312",
            entity_name="Apple Inc.",
            confidence=0.9,
            source="wikidata",
            description="American technology company"
        )
        
        assert link.mention == "Apple Inc."
        assert link.entity_id == "Q312"
        assert link.confidence == 0.9
        assert link.source == "wikidata"
        assert link.properties == {}
    
    def test_entity_relationship_creation(self):
        """Test EntityRelationship creation."""
        relationship = EntityRelationship(
            subject_entity="Q312",
            predicate="founded by",
            object_entity="Q19837",
            confidence=1.0,
            source="wikidata"
        )
        
        assert relationship.subject_entity == "Q312"
        assert relationship.predicate == "founded by"
        assert relationship.object_entity == "Q19837"
        assert relationship.confidence == 1.0
        assert relationship.properties == {}


class TestWikipediaLinker:
    """Test Wikipedia-based entity linking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.linker = WikipediaLinker()
    
    @patch('cross_provider_entity_linking.wikipedia.search')
    @patch('cross_provider_entity_linking.wikipediaapi.Wikipedia')
    def test_search_entities(self, mock_wiki_api, mock_search):
        """Test Wikipedia entity search."""
        # Mock search results
        mock_search.return_value = ["Apple Inc.", "Apple"]
        
        # Mock Wikipedia API
        mock_page = Mock()
        mock_page.exists.return_value = True
        mock_page.title = "Apple Inc."
        mock_page.summary = "American technology company"
        mock_page.fullurl = "https://en.wikipedia.org/wiki/Apple_Inc."
        mock_page.categories = {"Technology companies": None}
        mock_page.links = {"Steve Jobs": None, "iPhone": None}
        
        mock_wiki_instance = Mock()
        mock_wiki_instance.page.return_value = mock_page
        mock_wiki_api.return_value = mock_wiki_instance
        
        # Test search
        results = self.linker.search_entities("Apple Inc.")
        
        assert len(results) > 0
        assert results[0]['title'] == "Apple Inc."
        assert "technology company" in results[0]['summary'].lower()
    
    def test_link_entities(self):
        """Test entity linking with mocked Wikipedia."""
        entities = [
            Entity(text="Apple Inc.", start=0, end=10, label="ORG", confidence=0.9)
        ]
        
        # Mock search results
        with patch.object(self.linker, 'search_entities') as mock_search:
            mock_search.return_value = [{
                'title': 'Apple Inc.',
                'summary': 'American multinational technology company',
                'url': 'https://en.wikipedia.org/wiki/Apple_Inc.',
                'categories': ['Technology companies'],
                'links': ['Steve Jobs', 'iPhone']
            }]
            
            links = self.linker.link_entities(entities)
            
            assert len(links) == 1
            assert links[0].mention == "Apple Inc."
            assert links[0].entity_name == "Apple Inc."
            assert links[0].source == "wikipedia"
            assert links[0].confidence > 0.3


class TestWikidataLinker:
    """Test Wikidata-based entity linking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.linker = WikidataLinker()
    
    @patch('requests.Session.get')
    def test_search_entities(self, mock_get):
        """Test Wikidata entity search."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'search': [{
                'id': 'Q312',
                'label': 'Apple Inc.',
                'description': 'American technology company',
                'concepturi': 'http://www.wikidata.org/entity/Q312',
                'aliases': [{'value': 'Apple Computer'}]
            }]
        }
        mock_get.return_value = mock_response
        
        results = self.linker.search_entities("Apple Inc.")
        
        assert len(results) == 1
        assert results[0]['id'] == 'Q312'
        assert results[0]['label'] == 'Apple Inc.'
        assert 'Apple Computer' in results[0]['aliases']
    
    @patch('cross_provider_entity_linking.SPARQLWrapper')
    def test_get_entity_properties(self, mock_sparql_wrapper):
        """Test getting entity properties from Wikidata."""
        # Mock SPARQL results
        mock_sparql = Mock()
        mock_results = {
            "results": {
                "bindings": [
                    {
                        "propertyLabel": {"value": "founded by"},
                        "valueLabel": {"value": "Steve Jobs"}
                    },
                    {
                        "propertyLabel": {"value": "headquarters location"},
                        "valueLabel": {"value": "Cupertino"}
                    }
                ]
            }
        }
        mock_sparql.query.return_value.convert.return_value = mock_results
        mock_sparql_wrapper.return_value = mock_sparql
        
        self.linker.sparql = mock_sparql
        properties = self.linker.get_entity_properties("Q312")
        
        assert "founded by" in properties
        assert "Steve Jobs" in properties["founded by"]
        assert "headquarters location" in properties
    
    def test_link_entities(self):
        """Test entity linking with mocked Wikidata."""
        entities = [
            Entity(text="Apple Inc.", start=0, end=10, label="ORG", confidence=0.9)
        ]
        
        with patch.object(self.linker, 'search_entities') as mock_search, \
             patch.object(self.linker, 'get_entity_properties') as mock_props:
            
            mock_search.return_value = [{
                'id': 'Q312',
                'label': 'Apple Inc.',
                'description': 'American technology company',
                'aliases': ['Apple Computer']
            }]
            
            mock_props.return_value = {
                'founded by': ['Steve Jobs'],
                'industry': ['Technology']
            }
            
            links = self.linker.link_entities(entities)
            
            assert len(links) == 1
            assert links[0].entity_id == 'Q312'
            assert links[0].source == "wikidata"
            assert 'founded by' in links[0].properties


class TestDBpediaLinker:
    """Test DBpedia-based entity linking."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.linker = DBpediaLinker()
    
    @patch('requests.Session.get')
    def test_search_entities(self, mock_get):
        """Test DBpedia entity search."""
        # Mock API response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            'results': [{
                'uri': 'http://dbpedia.org/resource/Apple_Inc.',
                'label': 'Apple Inc.',
                'description': 'American technology company',
                'categories': ['Technology companies'],
                'classes': ['Company', 'Organization']
            }]
        }
        mock_get.return_value = mock_response
        
        results = self.linker.search_entities("Apple Inc.")
        
        assert len(results) == 1
        assert results[0]['uri'] == 'http://dbpedia.org/resource/Apple_Inc.'
        assert results[0]['label'] == 'Apple Inc.'
        assert 'Company' in results[0]['classes']
    
    def test_link_entities(self):
        """Test entity linking with mocked DBpedia."""
        entities = [
            Entity(text="Apple Inc.", start=0, end=10, label="ORG", confidence=0.9)
        ]
        
        with patch.object(self.linker, 'search_entities') as mock_search, \
             patch.object(self.linker, 'get_entity_details') as mock_details:
            
            mock_search.return_value = [{
                'uri': 'http://dbpedia.org/resource/Apple_Inc.',
                'label': 'Apple Inc.',
                'description': 'American technology company',
                'classes': ['Company']
            }]
            
            mock_details.return_value = {
                'foundedBy': ['Steve Jobs'],
                'industry': ['Technology']
            }
            
            links = self.linker.link_entities(entities)
            
            assert len(links) == 1
            assert links[0].source == "dbpedia"
            assert 'http://dbpedia.org/resource/Apple_Inc.' in links[0].entity_id


class TestHuggingFaceLinker:
    """Test Hugging Face-based entity linking."""
    
    def test_initialization_without_transformers(self):
        """Test initialization when transformers is not available."""
        with patch('cross_provider_entity_linking.pipeline', side_effect=ImportError):
            linker = HuggingFaceLinker()
            assert not linker.available
    
    @patch('cross_provider_entity_linking.pipeline')
    def test_link_entities(self, mock_pipeline):
        """Test entity linking with mocked Hugging Face model."""
        # Mock pipeline
        mock_linker = Mock()
        mock_linker.return_value = [
            {
                'entity_id': 'Q312',
                'entity_name': 'Apple Inc.',
                'score': 0.95,
                'start': 0,
                'end': 10,
                'description': 'Technology company'
            }
        ]
        mock_pipeline.return_value = mock_linker
        
        linker = HuggingFaceLinker()
        entities = [
            Entity(text="Apple Inc.", start=0, end=10, label="ORG", confidence=0.9)
        ]
        
        links = linker.link_entities("Apple Inc. is a company.", entities)
        
        assert len(links) == 1
        assert links[0].source == "huggingface"
        assert links[0].confidence == 0.95


class TestCrossProviderEntityLinker:
    """Test the main cross-provider entity linking system."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.linker = CrossProviderEntityLinker(providers=["wikipedia"])
    
    @patch('spacy.load')
    def test_initialization(self, mock_spacy_load):
        """Test linker initialization."""
        mock_nlp = Mock()
        mock_spacy_load.return_value = mock_nlp
        
        linker = CrossProviderEntityLinker(["wikipedia", "wikidata"])
        
        assert "wikipedia" in linker.providers
        assert "wikidata" in linker.providers
        assert linker.confidence_threshold == 0.3
    
    def test_extract_entities(self):
        """Test entity extraction using spaCy."""
        # Mock spaCy processing
        mock_doc = Mock()
        mock_ent = Mock()
        mock_ent.text = "Apple Inc."
        mock_ent.start_char = 0
        mock_ent.end_char = 10
        mock_ent.label_ = "ORG"
        mock_doc.ents = [mock_ent]
        
        self.linker.nlp = Mock()
        self.linker.nlp.return_value = mock_doc
        
        entities = self.linker.extract_entities("Apple Inc. is a company.")
        
        assert len(entities) == 1
        assert entities[0].text == "Apple Inc."
        assert entities[0].label == "ORG"
    
    def test_disambiguate_entities(self):
        """Test entity disambiguation across providers."""
        # Create test entity links from different providers
        entity_links = {
            "wikipedia": [
                EntityLink(
                    mention="Apple",
                    entity_id="wiki_apple_inc",
                    entity_name="Apple Inc.",
                    confidence=0.8,
                    source="wikipedia"
                )
            ],
            "wikidata": [
                EntityLink(
                    mention="Apple",
                    entity_id="Q312",
                    entity_name="Apple Inc.",
                    confidence=0.9,
                    source="wikidata"
                )
            ]
        }
        
        disambiguated = self.linker.disambiguate_entities(entity_links)
        
        assert len(disambiguated) == 1
        # Should pick the higher confidence one
        assert disambiguated[0].confidence >= 0.8
        assert disambiguated[0].entity_name == "Apple Inc."
    
    def test_validate_links(self):
        """Test entity link validation."""
        entity_links = [
            EntityLink(
                mention="Apple Inc.",
                entity_id="Q312",
                entity_name="Apple Inc.",
                confidence=0.9,
                source="wikidata"
            ),
            EntityLink(
                mention="Steve Jobs",
                entity_id="Q19837",
                entity_name="Steve Jobs",
                confidence=0.7,
                source="wikipedia"
            ),
            EntityLink(
                mention="Something",
                entity_id="unknown",
                entity_name="Unknown Entity",
                confidence=0.2,
                source="test"
            )
        ]
        
        validation = self.linker.validate_links(entity_links)
        
        assert validation['total_links'] == 3
        assert validation['high_confidence_links'] == 1  # >= 0.8
        assert validation['medium_confidence_links'] == 1  # >= 0.5
        assert validation['low_confidence_links'] == 1  # < 0.5
        assert validation['average_confidence'] == pytest.approx(0.6, rel=1e-1)
        assert 0 <= validation['quality_score'] <= 1
    
    def test_process_text_integration(self):
        """Test complete text processing pipeline."""
        # Mock all components
        mock_entities = [
            Entity(text="Apple Inc.", start=0, end=10, label="ORG", confidence=0.9)
        ]
        
        mock_links = {
            "wikipedia": [
                EntityLink(
                    mention="Apple Inc.",
                    entity_id="wiki_apple",
                    entity_name="Apple Inc.",
                    confidence=0.8,
                    source="wikipedia"
                )
            ]
        }
        
        with patch.object(self.linker, 'extract_entities', return_value=mock_entities), \
             patch.object(self.linker, 'link_entities_all_providers', return_value=mock_links), \
             patch.object(self.linker, 'get_entity_relationships', return_value=[]):
            
            results = self.linker.process_text("Apple Inc. is a company.")
            
            assert 'entities' in results
            assert 'entity_links' in results
            assert 'relationships' in results
            assert 'provider_results' in results
            assert 'graph_stats' in results
            assert 'processing_metadata' in results
            
            assert len(results['entities']) == 1
            assert results['entities'][0]['text'] == "Apple Inc."


class TestUtilityFunctions:
    """Test utility functions."""
    
    def test_create_entity_linker(self):
        """Test entity linker creation utility."""
        linker = create_entity_linker(["wikipedia"])
        
        assert isinstance(linker, CrossProviderEntityLinker)
        assert "wikipedia" in linker.providers
    
    @patch('cross_provider_entity_linking.CrossProviderEntityLinker')
    def test_link_entities_in_text(self, mock_linker_class):
        """Test convenience function for entity linking."""
        mock_linker = Mock()
        mock_linker.process_text.return_value = {'test': 'result'}
        mock_linker_class.return_value = mock_linker
        
        result = link_entities_in_text("Test text", ["wikipedia"])
        
        assert result == {'test': 'result'}
        mock_linker.process_text.assert_called_once_with("Test text")


class TestErrorHandling:
    """Test error handling in entity linking."""
    
    def test_wikipedia_search_error(self):
        """Test handling of Wikipedia search errors."""
        linker = WikipediaLinker()
        
        with patch('cross_provider_entity_linking.wikipedia.search', side_effect=Exception("API Error")):
            results = linker.search_entities("test query")
            assert results == []
    
    def test_wikidata_search_error(self):
        """Test handling of Wikidata search errors."""
        linker = WikidataLinker()
        
        with patch.object(linker.session, 'get', side_effect=Exception("Network Error")):
            results = linker.search_entities("test query")
            assert results == []
    
    def test_dbpedia_search_error(self):
        """Test handling of DBpedia search errors."""
        linker = DBpediaLinker()
        
        with patch.object(linker.session, 'get', side_effect=Exception("Timeout")):
            results = linker.search_entities("test query")
            assert results == []
    
    def test_cross_provider_error_handling(self):
        """Test error handling in cross-provider linking."""
        linker = CrossProviderEntityLinker(["wikipedia"])
        
        # Mock provider to raise exception
        mock_provider = Mock()
        mock_provider.link_entities.side_effect = Exception("Provider Error")
        linker.providers["wikipedia"] = mock_provider
        
        entities = [Entity(text="Test", start=0, end=4, label="TEST", confidence=1.0)]
        
        # Should handle error gracefully
        all_links = linker.link_entities_all_providers(entities)
        assert "wikipedia" in all_links
        assert all_links["wikipedia"] == []


class TestPerformance:
    """Test performance characteristics."""
    
    def test_processing_time(self):
        """Test that processing completes within reasonable time."""
        linker = CrossProviderEntityLinker([])  # No providers for speed
        
        # Mock entity extraction to return empty list
        with patch.object(linker, 'extract_entities', return_value=[]):
            start_time = time.time()
            results = linker.process_text("Short test text.")
            end_time = time.time()
            
            processing_time = end_time - start_time
            assert processing_time < 1.0  # Should complete in under 1 second
    
    def test_large_text_handling(self):
        """Test handling of large text inputs."""
        linker = CrossProviderEntityLinker([])  # No providers for speed
        
        # Create large text
        large_text = "Apple Inc. is a company. " * 1000
        
        with patch.object(linker, 'extract_entities', return_value=[]):
            results = linker.process_text(large_text)
            
            assert results['text'] == large_text
            assert 'processing_metadata' in results


class TestIntegration:
    """Integration tests for the complete system."""
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end entity linking workflow."""
        # Use minimal providers to avoid external dependencies
        linker = CrossProviderEntityLinker([])
        
        # Mock all external calls
        mock_entities = [
            Entity(text="Apple Inc.", start=0, end=10, label="ORG", confidence=0.9),
            Entity(text="Steve Jobs", start=25, end=35, label="PERSON", confidence=0.8)
        ]
        
        mock_links = [
            EntityLink(
                mention="Apple Inc.",
                entity_id="test_apple",
                entity_name="Apple Inc.",
                confidence=0.85,
                source="test"
            )
        ]
        
        with patch.object(linker, 'extract_entities', return_value=mock_entities), \
             patch.object(linker, 'disambiguate_entities', return_value=mock_links), \
             patch.object(linker, 'get_entity_relationships', return_value=[]):
            
            results = linker.process_text("Apple Inc. was founded by Steve Jobs.")
            
            # Verify complete results structure
            assert all(key in results for key in [
                'text', 'entities', 'entity_links', 'relationships',
                'provider_results', 'graph_stats', 'processing_metadata'
            ])
            
            assert len(results['entities']) == 2
            assert len(results['entity_links']) == 1
            assert results['entity_links'][0]['mention'] == "Apple Inc."
    
    def test_confidence_threshold_filtering(self):
        """Test that confidence threshold filtering works correctly."""
        linker = CrossProviderEntityLinker([])
        linker.confidence_threshold = 0.5
        
        # Create links with different confidence scores
        entity_links = {
            "test": [
                EntityLink("High", "id1", "High Confidence", 0.8, "test"),
                EntityLink("Medium", "id2", "Medium Confidence", 0.6, "test"),
                EntityLink("Low", "id3", "Low Confidence", 0.3, "test")
            ]
        }
        
        filtered_links = linker.disambiguate_entities(entity_links)
        
        # Should only include links above threshold
        assert len(filtered_links) == 2
        assert all(link.confidence >= 0.5 for link in filtered_links)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])