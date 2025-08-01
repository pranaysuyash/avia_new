"""
Advanced result ranking system for search results
"""

import logging
import math
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RankingFeatures:
    """Features used for ranking search results"""
    text_relevance: float = 0.0
    title_match: float = 0.0
    content_match: float = 0.0
    entity_match: float = 0.0
    recency: float = 0.0
    quality_score: float = 0.0
    user_interactions: float = 0.0
    
    @property
    def total_score(self) -> float:
        """Calculate total ranking score"""
        return (
            self.text_relevance * 0.4 +
            self.title_match * 0.25 +
            self.content_match * 0.15 +
            self.entity_match * 0.1 +
            self.recency * 0.05 +
            self.quality_score * 0.03 +
            self.user_interactions * 0.02
        )


class ResultRanker:
    """Advanced result ranking system"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.interaction_weights = {
            'view': 1.0,
            'share': 2.0,
            'export': 1.5,
            'save': 2.5
        }
        
    def rank_results(self, 
                    results: List[Dict[str, Any]], 
                    query: str,
                    user_context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Rank search results using multiple factors
        
        Args:
            results: List of search results
            query: Original search query
            user_context: Optional user context for personalization
            
        Returns:
            Ranked list of results
        """
        if not results:
            return results
            
        # Calculate ranking features for each result
        ranked_results = []
        
        for result in results:
            features = self._calculate_ranking_features(result, query, user_context)
            
            # Add ranking information to result
            result['ranking_features'] = features
            result['final_score'] = features.total_score
            
            ranked_results.append(result)
        
        # Sort by final score (descending)
        ranked_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        # Add ranking positions
        for i, result in enumerate(ranked_results):
            result['rank_position'] = i + 1
            
        logger.debug(f"Ranked {len(ranked_results)} results")
        
        return ranked_results
    
    def _calculate_ranking_features(self, 
                                  result: Dict[str, Any], 
                                  query: str,
                                  user_context: Dict[str, Any] = None) -> RankingFeatures:
        """Calculate ranking features for a single result"""
        features = RankingFeatures()
        
        # Text relevance (from search engine)
        features.text_relevance = self._normalize_score(result.get('rank', 0))
        
        # Title match score
        features.title_match = self._calculate_title_match(result.get('title', ''), query)
        
        # Content match score
        features.content_match = self._calculate_content_match(result.get('content', ''), query)
        
        # Entity match score
        features.entity_match = self._calculate_entity_match(result.get('metadata', {}), query)
        
        # Recency score
        features.recency = self._calculate_recency_score(result.get('indexed_at'))
        
        # Quality score
        features.quality_score = self._calculate_quality_score(result)
        
        # User interaction score
        if user_context:
            features.user_interactions = self._calculate_interaction_score(
                result.get('doc_id', ''), 
                user_context
            )
        
        return features
    
    def _calculate_title_match(self, title: str, query: str) -> float:
        """Calculate how well the query matches the title"""
        if not title or not query:
            return 0.0
            
        title_lower = title.lower()
        query_lower = query.lower()
        
        # Exact match bonus
        if query_lower in title_lower:
            return 1.0
            
        # Word-level matching
        query_words = set(query_lower.split())
        title_words = set(title_lower.split())
        
        if not query_words:
            return 0.0
            
        # Calculate overlap
        overlap = len(query_words.intersection(title_words))
        return overlap / len(query_words)
    
    def _calculate_content_match(self, content: str, query: str) -> float:
        """Calculate content relevance score"""
        if not content or not query:
            return 0.0
            
        content_lower = content.lower()
        query_lower = query.lower()
        
        # Count occurrences of query terms
        query_words = query_lower.split()
        content_words = content_lower.split()
        
        if not query_words or not content_words:
            return 0.0
        
        # Calculate term frequency
        total_matches = 0
        for word in query_words:
            matches = content_lower.count(word)
            total_matches += matches
            
        # Normalize by content length
        tf_score = total_matches / len(content_words)
        
        # Add position bias (matches early in content score higher)
        position_bias = 0.0
        for word in query_words:
            pos = content_lower.find(word)
            if pos >= 0:
                # Earlier positions get higher scores
                position_bias += max(0, 1 - (pos / len(content_lower)))
        
        position_bias /= len(query_words)
        
        return min(1.0, tf_score * 10 + position_bias * 0.2)
    
    def _calculate_entity_match(self, metadata: Dict[str, Any], query: str) -> float:
        """Calculate entity match score"""
        entities = metadata.get('entities', [])
        if not entities or not query:
            return 0.0
            
        query_lower = query.lower()
        entity_matches = 0
        
        for entity in entities:
            if isinstance(entity, dict):
                entity_text = entity.get('text', '').lower()
                if entity_text and entity_text in query_lower:
                    entity_matches += 1
            elif isinstance(entity, str):
                if entity.lower() in query_lower:
                    entity_matches += 1
        
        # Normalize by number of entities
        return min(1.0, entity_matches / max(1, len(entities)))
    
    def _calculate_recency_score(self, indexed_at: str) -> float:
        """Calculate recency score (newer content scores higher)"""
        if not indexed_at:
            return 0.0
            
        try:
            indexed_date = datetime.fromisoformat(indexed_at.replace('Z', '+00:00'))
            now = datetime.now(indexed_date.tzinfo)
            
            # Calculate days since indexing
            days_old = (now - indexed_date).days
            
            # Decay function: newer content gets higher scores
            # Score decreases exponentially with age
            decay_rate = 0.1  # Adjust this to control how quickly scores decay
            recency_score = math.exp(-decay_rate * days_old / 30)  # 30-day half-life
            
            return min(1.0, recency_score)
            
        except Exception:
            return 0.0
    
    def _calculate_quality_score(self, result: Dict[str, Any]) -> float:
        """Calculate content quality score"""
        metadata = result.get('metadata', {})
        
        quality_factors = []
        
        # Confidence score
        confidence = metadata.get('confidence', 0.5)
        quality_factors.append(confidence)
        
        # Content length (moderate length preferred)
        content = result.get('content', '')
        content_length = len(content.split())
        
        if content_length < 50:
            length_score = content_length / 50  # Too short
        elif content_length > 2000:
            length_score = 1.0 - ((content_length - 2000) / 5000)  # Too long
        else:
            length_score = 1.0  # Good length
            
        quality_factors.append(max(0.0, length_score))
        
        # Entity richness
        entities = metadata.get('entities', [])
        entity_score = min(1.0, len(entities) / 10)  # More entities = higher quality
        quality_factors.append(entity_score)
        
        # Tags presence
        tags = metadata.get('tags', [])
        tag_score = 1.0 if tags else 0.0
        quality_factors.append(tag_score)
        
        # Calculate average quality score
        return sum(quality_factors) / len(quality_factors) if quality_factors else 0.0
    
    def _calculate_interaction_score(self, doc_id: str, user_context: Dict[str, Any]) -> float:
        """Calculate user interaction score"""
        interactions = user_context.get('interactions', {}).get(doc_id, {})
        
        if not interactions:
            return 0.0
            
        score = 0.0
        for interaction_type, count in interactions.items():
            weight = self.interaction_weights.get(interaction_type, 1.0)
            score += count * weight
            
        # Normalize score
        return min(1.0, score / 10)
    
    def _normalize_score(self, score: float, max_score: float = 10.0) -> float:
        """Normalize a score to 0-1 range"""
        if max_score <= 0:
            return 0.0
        return min(1.0, max(0.0, score / max_score))
    
    def explain_ranking(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Explain why a result was ranked as it was"""
        features = result.get('ranking_features')
        if not features:
            return {'error': 'No ranking features available'}
            
        explanation = {
            'final_score': features.total_score,
            'rank_position': result.get('rank_position', 0),
            'factors': {
                'text_relevance': {
                    'score': features.text_relevance,
                    'weight': 0.4,
                    'contribution': features.text_relevance * 0.4
                },
                'title_match': {
                    'score': features.title_match,
                    'weight': 0.25,
                    'contribution': features.title_match * 0.25
                },
                'content_match': {
                    'score': features.content_match,
                    'weight': 0.15,
                    'contribution': features.content_match * 0.15
                },
                'entity_match': {
                    'score': features.entity_match,
                    'weight': 0.1,
                    'contribution': features.entity_match * 0.1
                },
                'recency': {
                    'score': features.recency,
                    'weight': 0.05,
                    'contribution': features.recency * 0.05
                },
                'quality_score': {
                    'score': features.quality_score,
                    'weight': 0.03,
                    'contribution': features.quality_score * 0.03
                },
                'user_interactions': {
                    'score': features.user_interactions,
                    'weight': 0.02,
                    'contribution': features.user_interactions * 0.02
                }
            }
        }
        
        # Sort factors by contribution
        explanation['top_factors'] = sorted(
            explanation['factors'].items(),
            key=lambda x: x[1]['contribution'],
            reverse=True
        )[:3]
        
        return explanation