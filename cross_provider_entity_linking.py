#!/usr/bin/env python3
"""
Cross-Provider Entity Linking System
Implements comprehensive entity linking using multiple APIs and knowledge graphs
including Wikipedia, Wikidata, DBpedia, and various NLP providers.
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import requests
import aiohttp
from urllib.parse import quote
import spacy
from spacy.tokens import Doc, Span
import wikipedia
import wikipediaapi
from SPARQLWrapper import SPARQLWrapper, JSON
import networkx as nx
from collections import defaultdict, Counter
import difflib
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Entity:
    """Represents an entity with linking information."""
    text: str
    start: int
    end: int
    label: str
    confidence: float
    canonical_name: Optional[str] = None
    description: Optional[str] = None
    entity_id: Optional[str] = None
    entity_type: Optional[str] = None
    aliases: List[str] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.aliases is None:
            self.aliases = []
        if self.properties is None:
            self.properties = {}


@dataclass
class EntityLink:
    """Represents a link between an entity mention and a knowledge base entity."""
    mention: str
    entity_id: str
    entity_name: str
    confidence: float
    source: str  # wikipedia, wikidata, dbpedia, etc.
    description: Optional[str] = None
    entity_type: Optional[str] = None
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class EntityRelationship:
    """Represents a relationship between two entities."""
    subject_entity: str
    predicate: str
    object_entity: str
    confidence: float
    source: str
    properties: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


class WikipediaLinker:
    """Wikipedia-based entity linking."""
    
    def __init__(self, language: str = "en"):
        """Initialize Wikipedia linker."""
        self.language = language
        self.wiki_api = wikipediaapi.Wikipedia(
            language=language,
            user_agent="EntityLinker/1.0 (https://example.com/contact)"
        )
        self.session = requests.Session()
        
    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for entities in Wikipedia."""
        try:
            # Use Wikipedia search API
            search_results = wikipedia.search(query, results=limit)
            
            entities = []
            for title in search_results:
                try:
                    page = self.wiki_api.page(title)
                    if page.exists():
                        entities.append({
                            'title': page.title,
                            'summary': page.summary[:500] if page.summary else "",
                            'url': page.fullurl,
                            'categories': list(page.categories.keys())[:10],
                            'links': list(page.links.keys())[:20]
                        })
                except Exception as e:
                    logger.warning(f"Error processing Wikipedia page {title}: {e}")
                    continue
            
            return entities
            
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return []
    
    def get_entity_details(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about an entity."""
        try:
            page = self.wiki_api.page(entity_name)
            if not page.exists():
                return None
            
            return {
                'title': page.title,
                'summary': page.summary,
                'url': page.fullurl,
                'categories': list(page.categories.keys()),
                'links': list(page.links.keys())[:50],
                'backlinks': list(page.backlinks.keys())[:20],
                'coordinates': getattr(page, 'coordinates', None),
                'images': [img for img in page.images if img.endswith(('.jpg', '.png', '.gif'))][:5]
            }
            
        except Exception as e:
            logger.error(f"Error getting Wikipedia entity details: {e}")
            return None
    
    def link_entities(self, entities: List[Entity]) -> List[EntityLink]:
        """Link entities to Wikipedia."""
        links = []
        
        for entity in entities:
            # Search for the entity
            search_results = self.search_entities(entity.text, limit=5)
            
            if search_results:
                # Calculate similarity scores
                best_match = None
                best_score = 0.0
                
                for result in search_results:
                    # Simple similarity based on title and summary
                    title_similarity = difflib.SequenceMatcher(
                        None, entity.text.lower(), result['title'].lower()
                    ).ratio()
                    
                    summary_similarity = 0.0
                    if result['summary']:
                        summary_words = set(result['summary'].lower().split())
                        entity_words = set(entity.text.lower().split())
                        if summary_words and entity_words:
                            summary_similarity = len(summary_words & entity_words) / len(summary_words | entity_words)
                    
                    # Combined score
                    combined_score = (title_similarity * 0.7) + (summary_similarity * 0.3)
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = result
                
                # Create link if confidence is high enough
                if best_match and best_score > 0.3:
                    link = EntityLink(
                        mention=entity.text,
                        entity_id=best_match['url'],
                        entity_name=best_match['title'],
                        confidence=best_score,
                        source="wikipedia",
                        description=best_match['summary'][:200],
                        properties={
                            'categories': best_match['categories'][:5],
                            'url': best_match['url']
                        }
                    )
                    links.append(link)
        
        return links


class WikidataLinker:
    """Wikidata-based entity linking using SPARQL."""
    
    def __init__(self):
        """Initialize Wikidata linker."""
        self.sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
        self.sparql.setReturnFormat(JSON)
        self.session = requests.Session()
        
    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for entities in Wikidata."""
        try:
            # Use Wikidata search API
            search_url = "https://www.wikidata.org/w/api.php"
            params = {
                'action': 'wbsearchentities',
                'search': query,
                'language': 'en',
                'format': 'json',
                'limit': limit
            }
            
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            entities = []
            
            for item in data.get('search', []):
                entities.append({
                    'id': item.get('id'),
                    'label': item.get('label'),
                    'description': item.get('description', ''),
                    'url': item.get('concepturi'),
                    'aliases': [alias.get('value') for alias in item.get('aliases', [])]
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"Wikidata search error: {e}")
            return []
    
    def get_entity_properties(self, entity_id: str) -> Dict[str, Any]:
        """Get properties for a Wikidata entity."""
        try:
            query = f"""
            SELECT ?property ?propertyLabel ?value ?valueLabel WHERE {{
              wd:{entity_id} ?property ?value .
              ?prop wikibase:directClaim ?property .
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
            }}
            LIMIT 50
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            properties = {}
            for result in results["results"]["bindings"]:
                prop_label = result["propertyLabel"]["value"]
                value_label = result.get("valueLabel", {}).get("value", result["value"]["value"])
                
                if prop_label not in properties:
                    properties[prop_label] = []
                properties[prop_label].append(value_label)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error getting Wikidata properties: {e}")
            return {}
    
    def get_entity_relationships(self, entity_id: str) -> List[EntityRelationship]:
        """Get relationships for a Wikidata entity."""
        try:
            query = f"""
            SELECT ?property ?propertyLabel ?object ?objectLabel WHERE {{
              wd:{entity_id} ?property ?object .
              ?prop wikibase:directClaim ?property .
              ?object rdfs:label ?objectLabel .
              FILTER(LANG(?objectLabel) = "en")
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" . }}
            }}
            LIMIT 100
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            relationships = []
            for result in results["results"]["bindings"]:
                if "objectLabel" in result:
                    relationship = EntityRelationship(
                        subject_entity=entity_id,
                        predicate=result["propertyLabel"]["value"],
                        object_entity=result["objectLabel"]["value"],
                        confidence=1.0,  # Wikidata relationships are authoritative
                        source="wikidata"
                    )
                    relationships.append(relationship)
            
            return relationships
            
        except Exception as e:
            logger.error(f"Error getting Wikidata relationships: {e}")
            return []
    
    def link_entities(self, entities: List[Entity]) -> List[EntityLink]:
        """Link entities to Wikidata."""
        links = []
        
        for entity in entities:
            search_results = self.search_entities(entity.text, limit=5)
            
            if search_results:
                best_match = None
                best_score = 0.0
                
                for result in search_results:
                    # Calculate similarity
                    label_similarity = difflib.SequenceMatcher(
                        None, entity.text.lower(), result['label'].lower()
                    ).ratio()
                    
                    # Check aliases
                    alias_similarity = 0.0
                    for alias in result.get('aliases', []):
                        alias_sim = difflib.SequenceMatcher(
                            None, entity.text.lower(), alias.lower()
                        ).ratio()
                        alias_similarity = max(alias_similarity, alias_sim)
                    
                    # Combined score
                    combined_score = max(label_similarity, alias_similarity)
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = result
                
                if best_match and best_score > 0.4:
                    # Get additional properties
                    properties = self.get_entity_properties(best_match['id'])
                    
                    link = EntityLink(
                        mention=entity.text,
                        entity_id=best_match['id'],
                        entity_name=best_match['label'],
                        confidence=best_score,
                        source="wikidata",
                        description=best_match['description'],
                        properties=properties
                    )
                    links.append(link)
        
        return links


class DBpediaLinker:
    """DBpedia-based entity linking using SPARQL."""
    
    def __init__(self):
        """Initialize DBpedia linker."""
        self.sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        self.sparql.setReturnFormat(JSON)
        self.session = requests.Session()
    
    def search_entities(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for entities in DBpedia."""
        try:
            # Use DBpedia Lookup service
            lookup_url = "http://lookup.dbpedia.org/api/search"
            params = {
                'query': query,
                'format': 'json',
                'maxResults': limit
            }
            
            response = self.session.get(lookup_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            entities = []
            
            for item in data.get('results', []):
                entities.append({
                    'uri': item.get('uri'),
                    'label': item.get('label'),
                    'description': item.get('description', ''),
                    'categories': item.get('categories', []),
                    'classes': item.get('classes', [])
                })
            
            return entities
            
        except Exception as e:
            logger.error(f"DBpedia search error: {e}")
            return []
    
    def get_entity_details(self, entity_uri: str) -> Dict[str, Any]:
        """Get detailed information about a DBpedia entity."""
        try:
            query = f"""
            SELECT ?property ?value WHERE {{
              <{entity_uri}> ?property ?value .
              FILTER(LANG(?value) = "en" || !isLiteral(?value))
            }}
            LIMIT 100
            """
            
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            
            properties = defaultdict(list)
            for result in results["results"]["bindings"]:
                prop = result["property"]["value"]
                value = result["value"]["value"]
                
                # Extract property name from URI
                prop_name = prop.split('/')[-1] if '/' in prop else prop
                properties[prop_name].append(value)
            
            return dict(properties)
            
        except Exception as e:
            logger.error(f"Error getting DBpedia entity details: {e}")
            return {}
    
    def link_entities(self, entities: List[Entity]) -> List[EntityLink]:
        """Link entities to DBpedia."""
        links = []
        
        for entity in entities:
            search_results = self.search_entities(entity.text, limit=5)
            
            if search_results:
                best_match = None
                best_score = 0.0
                
                for result in search_results:
                    # Calculate similarity
                    label_similarity = difflib.SequenceMatcher(
                        None, entity.text.lower(), result['label'].lower()
                    ).ratio()
                    
                    # Boost score if entity type matches
                    type_boost = 0.0
                    if entity.label and result.get('classes'):
                        for cls in result['classes']:
                            if entity.label.lower() in cls.lower():
                                type_boost = 0.2
                                break
                    
                    combined_score = label_similarity + type_boost
                    
                    if combined_score > best_score:
                        best_score = combined_score
                        best_match = result
                
                if best_match and best_score > 0.4:
                    # Get additional details
                    details = self.get_entity_details(best_match['uri'])
                    
                    link = EntityLink(
                        mention=entity.text,
                        entity_id=best_match['uri'],
                        entity_name=best_match['label'],
                        confidence=best_score,
                        source="dbpedia",
                        description=best_match['description'],
                        properties=details
                    )
                    links.append(link)
        
        return links


class HuggingFaceLinker:
    """Entity linking using Hugging Face models."""
    
    def __init__(self, model_name: str = "facebook/genre-linking-aidayago2"):
        """Initialize Hugging Face entity linker."""
        try:
            from transformers import pipeline
            self.linker = pipeline("entity-linking", model=model_name)
            self.available = True
        except ImportError:
            logger.warning("Transformers not available, HuggingFace linker disabled")
            self.available = False
        except Exception as e:
            logger.warning(f"Error loading HuggingFace model: {e}")
            self.available = False
    
    def link_entities(self, text: str, entities: List[Entity]) -> List[EntityLink]:
        """Link entities using Hugging Face model."""
        if not self.available:
            return []
        
        links = []
        
        try:
            # Process text with entity linking model
            results = self.linker(text)
            
            for result in results:
                # Find matching entity
                for entity in entities:
                    if (entity.start <= result.get('start', 0) <= entity.end or
                        entity.start <= result.get('end', 0) <= entity.end):
                        
                        link = EntityLink(
                            mention=entity.text,
                            entity_id=result.get('entity_id', ''),
                            entity_name=result.get('entity_name', entity.text),
                            confidence=result.get('score', 0.0),
                            source="huggingface",
                            description=result.get('description', '')
                        )
                        links.append(link)
                        break
            
        except Exception as e:
            logger.error(f"HuggingFace entity linking error: {e}")
        
        return links


class CrossProviderEntityLinker:
    """Main cross-provider entity linking system."""
    
    def __init__(self, providers: List[str] = None):
        """Initialize cross-provider entity linker."""
        if providers is None:
            providers = ["wikipedia", "wikidata", "dbpedia", "huggingface"]
        
        self.providers = {}
        
        # Initialize providers
        if "wikipedia" in providers:
            self.providers["wikipedia"] = WikipediaLinker()
        
        if "wikidata" in providers:
            self.providers["wikidata"] = WikidataLinker()
        
        if "dbpedia" in providers:
            self.providers["dbpedia"] = DBpediaLinker()
        
        if "huggingface" in providers:
            self.providers["huggingface"] = HuggingFaceLinker()
        
        # Initialize spaCy for entity extraction
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found, using blank model")
            self.nlp = spacy.blank("en")
        
        # Entity disambiguation settings
        self.confidence_threshold = 0.3
        self.max_candidates = 5
        
        logger.info(f"Initialized entity linker with providers: {list(self.providers.keys())}")
    
    def extract_entities(self, text: str) -> List[Entity]:
        """Extract entities from text using spaCy."""
        doc = self.nlp(text)
        entities = []
        
        for ent in doc.ents:
            entity = Entity(
                text=ent.text,
                start=ent.start_char,
                end=ent.end_char,
                label=ent.label_,
                confidence=1.0  # spaCy doesn't provide confidence scores
            )
            entities.append(entity)
        
        return entities
    
    def link_entities_single_provider(self, entities: List[Entity], 
                                    provider: str) -> List[EntityLink]:
        """Link entities using a single provider."""
        if provider not in self.providers:
            logger.warning(f"Provider {provider} not available")
            return []
        
        try:
            if provider == "huggingface":
                # HuggingFace needs the full text
                text = " ".join([entity.text for entity in entities])
                return self.providers[provider].link_entities(text, entities)
            else:
                return self.providers[provider].link_entities(entities)
        except Exception as e:
            logger.error(f"Error linking entities with {provider}: {e}")
            return []
    
    def link_entities_all_providers(self, entities: List[Entity], 
                                  text: str = None) -> Dict[str, List[EntityLink]]:
        """Link entities using all available providers."""
        all_links = {}
        
        for provider_name, provider in self.providers.items():
            logger.info(f"Linking entities with {provider_name}")
            
            try:
                if provider_name == "huggingface" and text:
                    links = provider.link_entities(text, entities)
                else:
                    links = provider.link_entities(entities)
                
                all_links[provider_name] = links
                logger.info(f"Found {len(links)} links with {provider_name}")
                
            except Exception as e:
                logger.error(f"Error with provider {provider_name}: {e}")
                all_links[provider_name] = []
        
        return all_links
    
    def disambiguate_entities(self, entity_links: Dict[str, List[EntityLink]]) -> List[EntityLink]:
        """Disambiguate entities across providers using confidence scores and consensus."""
        # Group links by mention
        mention_groups = defaultdict(list)
        for provider, links in entity_links.items():
            for link in links:
                mention_groups[link.mention].append(link)
        
        disambiguated_links = []
        
        for mention, links in mention_groups.items():
            if not links:
                continue
            
            # Sort by confidence
            links.sort(key=lambda x: x.confidence, reverse=True)
            
            # Check for consensus across providers
            entity_votes = defaultdict(list)
            for link in links:
                # Normalize entity names for comparison
                normalized_name = link.entity_name.lower().strip()
                entity_votes[normalized_name].append(link)
            
            # Find best candidate
            best_candidate = None
            
            if len(entity_votes) == 1:
                # All providers agree on the same entity
                candidates = list(entity_votes.values())[0]
                best_candidate = max(candidates, key=lambda x: x.confidence)
                best_candidate.confidence *= 1.2  # Boost for consensus
            
            else:
                # Multiple candidates, choose highest confidence
                best_candidate = links[0]
                
                # Check if multiple high-confidence links exist
                high_conf_links = [link for link in links if link.confidence > 0.7]
                if len(high_conf_links) > 1:
                    # Average confidence across high-confidence links
                    avg_confidence = sum(link.confidence for link in high_conf_links) / len(high_conf_links)
                    best_candidate.confidence = avg_confidence
            
            # Only include if confidence is above threshold
            if best_candidate and best_candidate.confidence >= self.confidence_threshold:
                disambiguated_links.append(best_candidate)
        
        return disambiguated_links
    
    def get_entity_relationships(self, entity_links: List[EntityLink]) -> List[EntityRelationship]:
        """Get relationships between linked entities."""
        relationships = []
        
        # Get relationships from knowledge bases
        for link in entity_links:
            if link.source == "wikidata" and "wikidata" in self.providers:
                try:
                    entity_id = link.entity_id.split('/')[-1]  # Extract Q-ID
                    rels = self.providers["wikidata"].get_entity_relationships(entity_id)
                    relationships.extend(rels)
                except Exception as e:
                    logger.error(f"Error getting relationships for {link.entity_name}: {e}")
        
        return relationships
    
    def build_entity_graph(self, entity_links: List[EntityLink], 
                          relationships: List[EntityRelationship]) -> nx.Graph:
        """Build a graph of entities and their relationships."""
        graph = nx.Graph()
        
        # Add entity nodes
        for link in entity_links:
            graph.add_node(
                link.entity_name,
                entity_id=link.entity_id,
                confidence=link.confidence,
                source=link.source,
                description=link.description
            )
        
        # Add relationship edges
        for rel in relationships:
            if rel.subject_entity in graph.nodes and rel.object_entity in graph.nodes:
                graph.add_edge(
                    rel.subject_entity,
                    rel.object_entity,
                    predicate=rel.predicate,
                    confidence=rel.confidence,
                    source=rel.source
                )
        
        return graph
    
    def process_text(self, text: str) -> Dict[str, Any]:
        """Complete entity linking pipeline for text."""
        logger.info("Starting entity linking pipeline")
        
        # Extract entities
        entities = self.extract_entities(text)
        logger.info(f"Extracted {len(entities)} entities")
        
        # Link entities with all providers
        all_links = self.link_entities_all_providers(entities, text)
        
        # Disambiguate entities
        final_links = self.disambiguate_entities(all_links)
        logger.info(f"Disambiguated to {len(final_links)} final links")
        
        # Get relationships
        relationships = self.get_entity_relationships(final_links)
        logger.info(f"Found {len(relationships)} relationships")
        
        # Build entity graph
        entity_graph = self.build_entity_graph(final_links, relationships)
        
        return {
            'text': text,
            'entities': [asdict(entity) for entity in entities],
            'entity_links': [asdict(link) for link in final_links],
            'relationships': [asdict(rel) for rel in relationships],
            'provider_results': {
                provider: [asdict(link) for link in links]
                for provider, links in all_links.items()
            },
            'graph_stats': {
                'nodes': entity_graph.number_of_nodes(),
                'edges': entity_graph.number_of_edges(),
                'connected_components': nx.number_connected_components(entity_graph)
            },
            'processing_metadata': {
                'timestamp': datetime.utcnow().isoformat(),
                'providers_used': list(self.providers.keys()),
                'confidence_threshold': self.confidence_threshold
            }
        }
    
    def validate_links(self, entity_links: List[EntityLink]) -> Dict[str, Any]:
        """Validate entity links and provide quality metrics."""
        validation_results = {
            'total_links': len(entity_links),
            'high_confidence_links': 0,
            'medium_confidence_links': 0,
            'low_confidence_links': 0,
            'provider_distribution': defaultdict(int),
            'entity_type_distribution': defaultdict(int),
            'average_confidence': 0.0,
            'quality_score': 0.0
        }
        
        if not entity_links:
            return validation_results
        
        # Analyze confidence distribution
        confidences = []
        for link in entity_links:
            confidences.append(link.confidence)
            validation_results['provider_distribution'][link.source] += 1
            
            if link.entity_type:
                validation_results['entity_type_distribution'][link.entity_type] += 1
            
            if link.confidence >= 0.8:
                validation_results['high_confidence_links'] += 1
            elif link.confidence >= 0.5:
                validation_results['medium_confidence_links'] += 1
            else:
                validation_results['low_confidence_links'] += 1
        
        # Calculate metrics
        validation_results['average_confidence'] = sum(confidences) / len(confidences)
        
        # Quality score based on confidence distribution
        high_conf_ratio = validation_results['high_confidence_links'] / len(entity_links)
        medium_conf_ratio = validation_results['medium_confidence_links'] / len(entity_links)
        
        validation_results['quality_score'] = (
            high_conf_ratio * 1.0 + 
            medium_conf_ratio * 0.6 + 
            (1 - high_conf_ratio - medium_conf_ratio) * 0.2
        )
        
        return validation_results


# Utility functions
def create_entity_linker(providers: List[str] = None) -> CrossProviderEntityLinker:
    """Create a cross-provider entity linker with specified providers."""
    return CrossProviderEntityLinker(providers)


def link_entities_in_text(text: str, providers: List[str] = None) -> Dict[str, Any]:
    """Convenience function to link entities in text."""
    linker = create_entity_linker(providers)
    return linker.process_text(text)


if __name__ == "__main__":
    # Example usage
    sample_text = """
    Barack Obama was the 44th President of the United States. He was born in Honolulu, Hawaii.
    Obama served as President from 2009 to 2017. Before becoming President, he was a Senator
    from Illinois. He graduated from Harvard Law School and worked as a community organizer
    in Chicago. His wife Michelle Obama was the First Lady during his presidency.
    """
    
    # Create entity linker
    linker = create_entity_linker(["wikipedia", "wikidata"])
    
    # Process text
    results = linker.process_text(sample_text)
    
    # Print results
    print("Entity Linking Results:")
    print(f"Found {len(results['entity_links'])} linked entities")
    
    for link in results['entity_links']:
        print(f"- {link['mention']} -> {link['entity_name']} ({link['source']}, confidence: {link['confidence']:.2f})")
    
    print(f"\nFound {len(results['relationships'])} relationships")
    for rel in results['relationships'][:5]:  # Show first 5
        print(f"- {rel['subject_entity']} {rel['predicate']} {rel['object_entity']}")
    
    print(f"\nGraph statistics: {results['graph_stats']}")