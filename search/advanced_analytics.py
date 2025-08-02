"""
Advanced Search and Analytics Module
Implements trend analysis, topic modeling, and comparative analysis
"""

import logging
import sqlite3
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import numpy as np
import asyncio

from keyword_extractor import KeywordExtractor
from semantic_search.semantic_engine import SemanticSearchEngine

logger = logging.getLogger(__name__)


@dataclass
class TrendAnalysisResult:
    """Result from trend analysis"""
    time_period: str
    trends: List[Dict[str, Any]]
    total_transcripts: int
    analysis_type: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TopicModelResult:
    """Result from topic modeling"""
    topics: List[Dict[str, Any]]
    topic_distribution: Dict[str, float]
    coherence_score: float
    num_topics: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparativeAnalysisResult:
    """Result from comparative analysis"""
    source_a: str
    source_b: str
    similarities: Dict[str, float]
    differences: Dict[str, Any]
    common_themes: List[str]
    unique_themes: Dict[str, List[str]]
    metadata: Dict[str, Any] = field(default_factory=dict)


class AdvancedAnalytics:
    """Advanced analytics engine for transcripts"""
    
    def __init__(self, db_path: str = "search_index.db"):
        self.db_path = db_path
        self.keyword_extractor = KeywordExtractor()
        self.semantic_engine = SemanticSearchEngine()
        self._init_analytics_tables()
    
    def _init_analytics_tables(self):
        """Initialize analytics-specific database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Trend analysis cache table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS trend_analysis_cache (
                        cache_id TEXT PRIMARY KEY,
                        time_period TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        results TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        expires_at TIMESTAMP NOT NULL
                    )
                """)
                
                # Topic modeling results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS topic_models (
                        model_id TEXT PRIMARY KEY,
                        num_topics INTEGER NOT NULL,
                        topics TEXT NOT NULL,
                        coherence_score REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        transcript_ids TEXT NOT NULL
                    )
                """)
                
                # Comparative analysis cache
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS comparative_analysis_cache (
                        analysis_id TEXT PRIMARY KEY,
                        source_a TEXT NOT NULL,
                        source_b TEXT NOT NULL,
                        results TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Analytics tables initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize analytics tables: {e}")
    
    async def analyze_trends(self, 
                           time_period: str = "30d",
                           analysis_type: str = "keywords",
                           filters: Dict[str, Any] = None) -> TrendAnalysisResult:
        """
        Analyze trends across transcripts over time
        
        Args:
            time_period: Time period for analysis (7d, 30d, 90d, 1y)
            analysis_type: Type of trend analysis (keywords, topics, entities, sentiment)
            filters: Additional filters for transcript selection
            
        Returns:
            TrendAnalysisResult with trend data
        """
        try:
            # Check cache first
            cache_key = f"{time_period}_{analysis_type}_{hash(str(filters))}"
            cached_result = self._get_cached_trend_analysis(cache_key)
            if cached_result:
                return cached_result
            
            # Get transcripts for the time period
            transcripts = await self._get_transcripts_for_period(time_period, filters)
            
            if not transcripts:
                return TrendAnalysisResult(
                    time_period=time_period,
                    trends=[],
                    total_transcripts=0,
                    analysis_type=analysis_type
                )
            
            # Perform trend analysis based on type
            if analysis_type == "keywords":
                trends = await self._analyze_keyword_trends(transcripts, time_period)
            elif analysis_type == "topics":
                trends = await self._analyze_topic_trends(transcripts, time_period)
            elif analysis_type == "entities":
                trends = await self._analyze_entity_trends(transcripts, time_period)
            elif analysis_type == "sentiment":
                trends = await self._analyze_sentiment_trends(transcripts, time_period)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
            
            result = TrendAnalysisResult(
                time_period=time_period,
                trends=trends,
                total_transcripts=len(transcripts),
                analysis_type=analysis_type,
                metadata={
                    'analyzed_at': datetime.utcnow().isoformat(),
                    'transcript_count': len(transcripts)
                }
            )
            
            # Cache the result
            self._cache_trend_analysis(cache_key, result)
            
            logger.info(f"Completed {analysis_type} trend analysis for {time_period}")
            return result
            
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            return TrendAnalysisResult(
                time_period=time_period,
                trends=[],
                total_transcripts=0,
                analysis_type=analysis_type
            )
    
    async def extract_topics(self, 
                           transcript_ids: List[str] = None,
                           num_topics: int = 5,
                           method: str = "keyword_clustering") -> TopicModelResult:
        """
        Extract topics from transcripts using various methods
        
        Args:
            transcript_ids: Specific transcript IDs to analyze (None for all)
            num_topics: Number of topics to extract
            method: Topic extraction method (keyword_clustering, semantic_clustering)
            
        Returns:
            TopicModelResult with extracted topics
        """
        try:
            # Get transcripts
            if transcript_ids:
                transcripts = await self._get_transcripts_by_ids(transcript_ids)
            else:
                transcripts = await self._get_all_transcripts()
            
            if not transcripts:
                return TopicModelResult(
                    topics=[],
                    topic_distribution={},
                    coherence_score=0.0,
                    num_topics=0
                )
            
            # Extract topics based on method
            if method == "keyword_clustering":
                topics, distribution, coherence = await self._extract_topics_by_keywords(
                    transcripts, num_topics
                )
            elif method == "semantic_clustering":
                topics, distribution, coherence = await self._extract_topics_by_semantics(
                    transcripts, num_topics
                )
            else:
                raise ValueError(f"Unknown topic extraction method: {method}")
            
            result = TopicModelResult(
                topics=topics,
                topic_distribution=distribution,
                coherence_score=coherence,
                num_topics=len(topics),
                metadata={
                    'method': method,
                    'transcript_count': len(transcripts),
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            )
            
            # Store the model
            self._store_topic_model(result, transcript_ids or [])
            
            logger.info(f"Extracted {len(topics)} topics using {method}")
            return result
            
        except Exception as e:
            logger.error(f"Topic extraction failed: {e}")
            return TopicModelResult(
                topics=[],
                topic_distribution={},
                coherence_score=0.0,
                num_topics=0
            )
    
    async def compare_sources(self, 
                            source_a: str,
                            source_b: str,
                            comparison_type: str = "comprehensive") -> ComparativeAnalysisResult:
        """
        Compare two audio sources or transcript collections
        
        Args:
            source_a: First source identifier (transcript_id or collection)
            source_b: Second source identifier
            comparison_type: Type of comparison (comprehensive, keywords, topics, sentiment)
            
        Returns:
            ComparativeAnalysisResult with comparison data
        """
        try:
            # Check cache
            cache_key = f"{source_a}_{source_b}_{comparison_type}"
            cached_result = self._get_cached_comparative_analysis(cache_key)
            if cached_result:
                return cached_result
            
            # Get content for both sources
            content_a = await self._get_source_content(source_a)
            content_b = await self._get_source_content(source_b)
            
            if not content_a or not content_b:
                return ComparativeAnalysisResult(
                    source_a=source_a,
                    source_b=source_b,
                    similarities={},
                    differences={},
                    common_themes=[],
                    unique_themes={}
                )
            
            # Perform comparison
            similarities = await self._calculate_similarities(content_a, content_b)
            differences = await self._calculate_differences(content_a, content_b)
            common_themes = await self._find_common_themes(content_a, content_b)
            unique_themes = await self._find_unique_themes(content_a, content_b)
            
            result = ComparativeAnalysisResult(
                source_a=source_a,
                source_b=source_b,
                similarities=similarities,
                differences=differences,
                common_themes=common_themes,
                unique_themes=unique_themes,
                metadata={
                    'comparison_type': comparison_type,
                    'analyzed_at': datetime.utcnow().isoformat()
                }
            )
            
            # Cache the result
            self._cache_comparative_analysis(cache_key, result)
            
            logger.info(f"Completed comparative analysis between {source_a} and {source_b}")
            return result
            
        except Exception as e:
            logger.error(f"Comparative analysis failed: {e}")
            return ComparativeAnalysisResult(
                source_a=source_a,
                source_b=source_b,
                similarities={},
                differences={},
                common_themes=[],
                unique_themes={}
            )
    
    async def _get_transcripts_for_period(self, 
                                        time_period: str,
                                        filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get transcripts for a specific time period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            
            if time_period == "7d":
                start_date = end_date - timedelta(days=7)
            elif time_period == "30d":
                start_date = end_date - timedelta(days=30)
            elif time_period == "90d":
                start_date = end_date - timedelta(days=90)
            elif time_period == "1y":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = """
                    SELECT doc_id, title, content, metadata, created_at
                    FROM documents
                    WHERE created_at >= ? AND created_at <= ?
                """
                params = [start_date.isoformat(), end_date.isoformat()]
                
                # Apply additional filters
                if filters:
                    if filters.get('language'):
                        query += " AND JSON_EXTRACT(metadata, '$.language') = ?"
                        params.append(filters['language'])
                    
                    if filters.get('speakers'):
                        query += " AND JSON_EXTRACT(metadata, '$.speakers') IS NOT NULL"
                    
                    if filters.get('tags'):
                        for tag in filters['tags']:
                            query += " AND JSON_EXTRACT(metadata, '$.tags') LIKE ?"
                            params.append(f'%{tag}%')
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                transcripts = []
                for row in rows:
                    doc_id, title, content, metadata_str, created_at = row
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    
                    transcripts.append({
                        'id': doc_id,
                        'title': title,
                        'content': content,
                        'metadata': metadata,
                        'created_at': created_at
                    })
                
                return transcripts
                
        except Exception as e:
            logger.error(f"Failed to get transcripts for period {time_period}: {e}")
            return []
    
    async def _analyze_keyword_trends(self, 
                                    transcripts: List[Dict[str, Any]],
                                    time_period: str) -> List[Dict[str, Any]]:
        """Analyze keyword trends over time"""
        try:
            # Group transcripts by time buckets
            time_buckets = self._create_time_buckets(transcripts, time_period)
            
            trends = []
            
            for bucket_name, bucket_transcripts in time_buckets.items():
                # Extract keywords for this time bucket
                all_text = " ".join([t['content'] for t in bucket_transcripts])
                keywords = self.keyword_extractor.extract_keywords(all_text, max_keywords=20)
                
                # Calculate keyword frequency and growth
                keyword_data = []
                for keyword, score in keywords:
                    keyword_data.append({
                        'keyword': keyword,
                        'score': score,
                        'frequency': all_text.lower().count(keyword.lower()),
                        'transcripts_count': len(bucket_transcripts)
                    })
                
                trends.append({
                    'time_bucket': bucket_name,
                    'keywords': keyword_data,
                    'transcript_count': len(bucket_transcripts)
                })
            
            # Calculate growth rates between buckets
            for i in range(1, len(trends)):
                current_keywords = {kw['keyword']: kw for kw in trends[i]['keywords']}
                previous_keywords = {kw['keyword']: kw for kw in trends[i-1]['keywords']}
                
                for keyword_data in trends[i]['keywords']:
                    keyword = keyword_data['keyword']
                    if keyword in previous_keywords:
                        prev_score = previous_keywords[keyword]['score']
                        current_score = keyword_data['score']
                        
                        if prev_score > 0:
                            growth_rate = ((current_score - prev_score) / prev_score) * 100
                            keyword_data['growth_rate'] = growth_rate
                        else:
                            keyword_data['growth_rate'] = 100.0  # New keyword
                    else:
                        keyword_data['growth_rate'] = 100.0  # New keyword
            
            return trends
            
        except Exception as e:
            logger.error(f"Keyword trend analysis failed: {e}")
            return []
    
    async def _analyze_topic_trends(self, 
                                  transcripts: List[Dict[str, Any]],
                                  time_period: str) -> List[Dict[str, Any]]:
        """Analyze topic trends over time"""
        try:
            # Group transcripts by time buckets
            time_buckets = self._create_time_buckets(transcripts, time_period)
            
            trends = []
            
            for bucket_name, bucket_transcripts in time_buckets.items():
                # Extract topics for this time bucket
                transcript_ids = [t['id'] for t in bucket_transcripts]
                topic_result = await self.extract_topics(transcript_ids, num_topics=5)
                
                trends.append({
                    'time_bucket': bucket_name,
                    'topics': topic_result.topics,
                    'topic_distribution': topic_result.topic_distribution,
                    'coherence_score': topic_result.coherence_score,
                    'transcript_count': len(bucket_transcripts)
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Topic trend analysis failed: {e}")
            return []
    
    async def _analyze_entity_trends(self, 
                                   transcripts: List[Dict[str, Any]],
                                   time_period: str) -> List[Dict[str, Any]]:
        """Analyze entity trends over time"""
        try:
            # Group transcripts by time buckets
            time_buckets = self._create_time_buckets(transcripts, time_period)
            
            trends = []
            
            for bucket_name, bucket_transcripts in time_buckets.items():
                # Extract entities from metadata
                entity_counts = defaultdict(int)
                entity_types = defaultdict(int)
                
                for transcript in bucket_transcripts:
                    entities = transcript.get('metadata', {}).get('entities', [])
                    for entity in entities:
                        if isinstance(entity, dict):
                            entity_text = entity.get('text', '')
                            entity_type = entity.get('label', 'UNKNOWN')
                        else:
                            entity_text = str(entity)
                            entity_type = 'UNKNOWN'
                        
                        entity_counts[entity_text] += 1
                        entity_types[entity_type] += 1
                
                # Get top entities
                top_entities = sorted(entity_counts.items(), key=lambda x: x[1], reverse=True)[:20]
                
                trends.append({
                    'time_bucket': bucket_name,
                    'top_entities': [{'entity': entity, 'count': count} for entity, count in top_entities],
                    'entity_types': dict(entity_types),
                    'total_entities': sum(entity_counts.values()),
                    'transcript_count': len(bucket_transcripts)
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Entity trend analysis failed: {e}")
            return []
    
    async def _analyze_sentiment_trends(self, 
                                      transcripts: List[Dict[str, Any]],
                                      time_period: str) -> List[Dict[str, Any]]:
        """Analyze sentiment trends over time"""
        try:
            # Group transcripts by time buckets
            time_buckets = self._create_time_buckets(transcripts, time_period)
            
            trends = []
            
            for bucket_name, bucket_transcripts in time_buckets.items():
                # Calculate sentiment for this time bucket
                sentiments = []
                
                for transcript in bucket_transcripts:
                    # Extract sentiment from metadata if available
                    sentiment = transcript.get('metadata', {}).get('sentiment', {})
                    if sentiment:
                        sentiments.append(sentiment)
                    else:
                        # Simple sentiment analysis based on keywords
                        content = transcript['content'].lower()
                        positive_words = ['good', 'great', 'excellent', 'positive', 'happy', 'success']
                        negative_words = ['bad', 'terrible', 'negative', 'sad', 'failure', 'problem']
                        
                        positive_count = sum(content.count(word) for word in positive_words)
                        negative_count = sum(content.count(word) for word in negative_words)
                        
                        if positive_count + negative_count > 0:
                            sentiment_score = (positive_count - negative_count) / (positive_count + negative_count)
                        else:
                            sentiment_score = 0.0
                        
                        sentiments.append({'score': sentiment_score})
                
                # Calculate average sentiment
                if sentiments:
                    avg_sentiment = np.mean([s.get('score', 0) for s in sentiments])
                    sentiment_distribution = {
                        'positive': len([s for s in sentiments if s.get('score', 0) > 0.1]),
                        'neutral': len([s for s in sentiments if -0.1 <= s.get('score', 0) <= 0.1]),
                        'negative': len([s for s in sentiments if s.get('score', 0) < -0.1])
                    }
                else:
                    avg_sentiment = 0.0
                    sentiment_distribution = {'positive': 0, 'neutral': 0, 'negative': 0}
                
                trends.append({
                    'time_bucket': bucket_name,
                    'average_sentiment': avg_sentiment,
                    'sentiment_distribution': sentiment_distribution,
                    'transcript_count': len(bucket_transcripts)
                })
            
            return trends
            
        except Exception as e:
            logger.error(f"Sentiment trend analysis failed: {e}")
            return []
    
    def _create_time_buckets(self, 
                           transcripts: List[Dict[str, Any]],
                           time_period: str) -> Dict[str, List[Dict[str, Any]]]:
        """Create time buckets for trend analysis"""
        try:
            buckets = defaultdict(list)
            
            for transcript in transcripts:
                created_at = datetime.fromisoformat(transcript['created_at'])
                
                # Determine bucket based on time period
                if time_period in ["7d", "30d"]:
                    # Daily buckets
                    bucket_key = created_at.strftime("%Y-%m-%d")
                elif time_period == "90d":
                    # Weekly buckets
                    week_start = created_at - timedelta(days=created_at.weekday())
                    bucket_key = week_start.strftime("%Y-W%U")
                elif time_period == "1y":
                    # Monthly buckets
                    bucket_key = created_at.strftime("%Y-%m")
                else:
                    # Default to daily
                    bucket_key = created_at.strftime("%Y-%m-%d")
                
                buckets[bucket_key].append(transcript)
            
            return dict(buckets)
            
        except Exception as e:
            logger.error(f"Failed to create time buckets: {e}")
            return {}
    
    async def _extract_topics_by_keywords(self, 
                                        transcripts: List[Dict[str, Any]],
                                        num_topics: int) -> Tuple[List[Dict[str, Any]], Dict[str, float], float]:
        """Extract topics using keyword clustering"""
        try:
            # Extract keywords from all transcripts
            all_keywords = []
            transcript_keywords = {}
            
            for transcript in transcripts:
                keywords = self.keyword_extractor.extract_keywords(
                    transcript['content'], 
                    max_keywords=15
                )
                transcript_keywords[transcript['id']] = keywords
                all_keywords.extend([kw[0] for kw in keywords])
            
            # Count keyword frequencies
            keyword_counts = Counter(all_keywords)
            top_keywords = [kw for kw, count in keyword_counts.most_common(50)]
            
            # Simple clustering based on co-occurrence
            topics = []
            used_keywords = set()
            
            for i in range(num_topics):
                if not top_keywords:
                    break
                
                # Find the most frequent unused keyword as topic seed
                seed_keyword = None
                for kw in top_keywords:
                    if kw not in used_keywords:
                        seed_keyword = kw
                        break
                
                if not seed_keyword:
                    break
                
                # Find related keywords (co-occurring keywords)
                related_keywords = [seed_keyword]
                used_keywords.add(seed_keyword)
                
                # Simple co-occurrence based clustering
                for transcript in transcripts:
                    transcript_kw_list = [kw[0] for kw in transcript_keywords[transcript['id']]]
                    if seed_keyword in transcript_kw_list:
                        for kw in transcript_kw_list:
                            if kw not in used_keywords and len(related_keywords) < 8:
                                related_keywords.append(kw)
                                used_keywords.add(kw)
                
                # Create topic
                topic = {
                    'topic_id': f"topic_{i+1}",
                    'keywords': related_keywords,
                    'weight': keyword_counts[seed_keyword] / len(transcripts),
                    'description': f"Topic centered around '{seed_keyword}'"
                }
                topics.append(topic)
            
            # Calculate topic distribution
            topic_distribution = {}
            for topic in topics:
                topic_distribution[topic['topic_id']] = topic['weight']
            
            # Simple coherence score (average keyword frequency)
            coherence_score = np.mean([topic['weight'] for topic in topics]) if topics else 0.0
            
            return topics, topic_distribution, coherence_score
            
        except Exception as e:
            logger.error(f"Keyword-based topic extraction failed: {e}")
            return [], {}, 0.0
    
    async def _extract_topics_by_semantics(self, 
                                         transcripts: List[Dict[str, Any]],
                                         num_topics: int) -> Tuple[List[Dict[str, Any]], Dict[str, float], float]:
        """Extract topics using semantic clustering"""
        try:
            # For now, fall back to keyword-based approach
            # In a full implementation, this would use semantic embeddings
            # and clustering algorithms like K-means or LDA
            
            return await self._extract_topics_by_keywords(transcripts, num_topics)
            
        except Exception as e:
            logger.error(f"Semantic topic extraction failed: {e}")
            return [], {}, 0.0
    
    async def _get_source_content(self, source_id: str) -> Optional[Dict[str, Any]]:
        """Get content for a source (transcript or collection)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Try to get as single transcript first
                cursor.execute("""
                    SELECT doc_id, title, content, metadata
                    FROM documents
                    WHERE doc_id = ?
                """, (source_id,))
                
                row = cursor.fetchone()
                if row:
                    doc_id, title, content, metadata_str = row
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    
                    return {
                        'id': doc_id,
                        'title': title,
                        'content': content,
                        'metadata': metadata,
                        'type': 'single_transcript'
                    }
                
                # If not found, try as collection or tag
                cursor.execute("""
                    SELECT doc_id, title, content, metadata
                    FROM documents
                    WHERE JSON_EXTRACT(metadata, '$.tags') LIKE ?
                    OR JSON_EXTRACT(metadata, '$.collection') = ?
                """, (f'%{source_id}%', source_id))
                
                rows = cursor.fetchall()
                if rows:
                    combined_content = []
                    titles = []
                    
                    for row in rows:
                        doc_id, title, content, metadata_str = row
                        combined_content.append(content)
                        titles.append(title)
                    
                    return {
                        'id': source_id,
                        'title': f"Collection: {source_id}",
                        'content': " ".join(combined_content),
                        'metadata': {'collection_size': len(rows), 'titles': titles},
                        'type': 'collection'
                    }
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get source content for {source_id}: {e}")
            return None
    
    async def _calculate_similarities(self, 
                                    content_a: Dict[str, Any],
                                    content_b: Dict[str, Any]) -> Dict[str, float]:
        """Calculate similarities between two content sources"""
        try:
            similarities = {}
            
            # Keyword similarity
            keywords_a = set([kw[0] for kw in self.keyword_extractor.extract_keywords(content_a['content'])])
            keywords_b = set([kw[0] for kw in self.keyword_extractor.extract_keywords(content_b['content'])])
            
            if keywords_a or keywords_b:
                keyword_similarity = len(keywords_a & keywords_b) / len(keywords_a | keywords_b)
                similarities['keyword_similarity'] = keyword_similarity
            
            # Content length similarity
            len_a = len(content_a['content'])
            len_b = len(content_b['content'])
            
            if len_a > 0 and len_b > 0:
                length_similarity = min(len_a, len_b) / max(len_a, len_b)
                similarities['length_similarity'] = length_similarity
            
            # Entity similarity (if available)
            entities_a = set()
            entities_b = set()
            
            for entity in content_a.get('metadata', {}).get('entities', []):
                if isinstance(entity, dict):
                    entities_a.add(entity.get('text', ''))
                else:
                    entities_a.add(str(entity))
            
            for entity in content_b.get('metadata', {}).get('entities', []):
                if isinstance(entity, dict):
                    entities_b.add(entity.get('text', ''))
                else:
                    entities_b.add(str(entity))
            
            if entities_a or entities_b:
                entity_similarity = len(entities_a & entities_b) / len(entities_a | entities_b)
                similarities['entity_similarity'] = entity_similarity
            
            # Overall similarity (weighted average)
            weights = {'keyword_similarity': 0.5, 'length_similarity': 0.2, 'entity_similarity': 0.3}
            overall_similarity = 0.0
            total_weight = 0.0
            
            for sim_type, similarity in similarities.items():
                weight = weights.get(sim_type, 0.1)
                overall_similarity += similarity * weight
                total_weight += weight
            
            if total_weight > 0:
                similarities['overall_similarity'] = overall_similarity / total_weight
            
            return similarities
            
        except Exception as e:
            logger.error(f"Failed to calculate similarities: {e}")
            return {}
    
    async def _calculate_differences(self, 
                                   content_a: Dict[str, Any],
                                   content_b: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate differences between two content sources"""
        try:
            differences = {}
            
            # Length difference
            len_a = len(content_a['content'])
            len_b = len(content_b['content'])
            differences['length_difference'] = abs(len_a - len_b)
            differences['length_ratio'] = len_a / len_b if len_b > 0 else float('inf')
            
            # Keyword differences
            keywords_a = set([kw[0] for kw in self.keyword_extractor.extract_keywords(content_a['content'])])
            keywords_b = set([kw[0] for kw in self.keyword_extractor.extract_keywords(content_b['content'])])
            
            differences['unique_keywords_a'] = list(keywords_a - keywords_b)
            differences['unique_keywords_b'] = list(keywords_b - keywords_a)
            
            # Metadata differences
            metadata_a = content_a.get('metadata', {})
            metadata_b = content_b.get('metadata', {})
            
            differences['metadata_differences'] = {}
            
            # Compare specific metadata fields
            for field in ['language', 'speakers', 'duration', 'confidence']:
                value_a = metadata_a.get(field)
                value_b = metadata_b.get(field)
                
                if value_a != value_b:
                    differences['metadata_differences'][field] = {
                        'source_a': value_a,
                        'source_b': value_b
                    }
            
            return differences
            
        except Exception as e:
            logger.error(f"Failed to calculate differences: {e}")
            return {}
    
    async def _find_common_themes(self, 
                                content_a: Dict[str, Any],
                                content_b: Dict[str, Any]) -> List[str]:
        """Find common themes between two content sources"""
        try:
            # Extract keywords from both sources
            keywords_a = [kw[0] for kw in self.keyword_extractor.extract_keywords(content_a['content'])]
            keywords_b = [kw[0] for kw in self.keyword_extractor.extract_keywords(content_b['content'])]
            
            # Find common keywords
            common_keywords = set(keywords_a) & set(keywords_b)
            
            # Group related keywords into themes
            themes = []
            used_keywords = set()
            
            for keyword in common_keywords:
                if keyword in used_keywords:
                    continue
                
                # Find related keywords
                theme_keywords = [keyword]
                used_keywords.add(keyword)
                
                # Simple theme grouping based on word similarity
                for other_keyword in common_keywords:
                    if other_keyword not in used_keywords:
                        # Check if keywords are related (simple approach)
                        if (keyword in other_keyword or other_keyword in keyword or
                            len(set(keyword.split()) & set(other_keyword.split())) > 0):
                            theme_keywords.append(other_keyword)
                            used_keywords.add(other_keyword)
                
                if len(theme_keywords) >= 1:
                    theme_name = f"Theme: {', '.join(theme_keywords[:3])}"
                    themes.append(theme_name)
            
            return themes[:10]  # Return top 10 themes
            
        except Exception as e:
            logger.error(f"Failed to find common themes: {e}")
            return []
    
    async def _find_unique_themes(self, 
                                content_a: Dict[str, Any],
                                content_b: Dict[str, Any]) -> Dict[str, List[str]]:
        """Find unique themes for each content source"""
        try:
            # Extract keywords from both sources
            keywords_a = set([kw[0] for kw in self.keyword_extractor.extract_keywords(content_a['content'])])
            keywords_b = set([kw[0] for kw in self.keyword_extractor.extract_keywords(content_b['content'])])
            
            # Find unique keywords
            unique_a = keywords_a - keywords_b
            unique_b = keywords_b - keywords_a
            
            return {
                'source_a_unique': list(unique_a)[:10],
                'source_b_unique': list(unique_b)[:10]
            }
            
        except Exception as e:
            logger.error(f"Failed to find unique themes: {e}")
            return {'source_a_unique': [], 'source_b_unique': []}
    
    # Cache management methods
    def _get_cached_trend_analysis(self, cache_key: str) -> Optional[TrendAnalysisResult]:
        """Get cached trend analysis result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT results FROM trend_analysis_cache
                    WHERE cache_id = ? AND expires_at > CURRENT_TIMESTAMP
                """, (cache_key,))
                
                row = cursor.fetchone()
                if row:
                    result_data = json.loads(row[0])
                    return TrendAnalysisResult(**result_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get cached trend analysis: {e}")
            return None
    
    def _cache_trend_analysis(self, cache_key: str, result: TrendAnalysisResult):
        """Cache trend analysis result"""
        try:
            expires_at = datetime.utcnow() + timedelta(hours=1)  # Cache for 1 hour
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO trend_analysis_cache
                    (cache_id, time_period, analysis_type, results, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    cache_key,
                    result.time_period,
                    result.analysis_type,
                    json.dumps(result.__dict__, default=str),
                    expires_at.isoformat()
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to cache trend analysis: {e}")
    
    def _store_topic_model(self, result: TopicModelResult, transcript_ids: List[str]):
        """Store topic model result"""
        try:
            model_id = f"model_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO topic_models
                    (model_id, num_topics, topics, coherence_score, transcript_ids)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    model_id,
                    result.num_topics,
                    json.dumps(result.topics),
                    result.coherence_score,
                    json.dumps(transcript_ids)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to store topic model: {e}")
    
    def _get_cached_comparative_analysis(self, cache_key: str) -> Optional[ComparativeAnalysisResult]:
        """Get cached comparative analysis result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT results FROM comparative_analysis_cache
                    WHERE analysis_id = ?
                """, (cache_key,))
                
                row = cursor.fetchone()
                if row:
                    result_data = json.loads(row[0])
                    return ComparativeAnalysisResult(**result_data)
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get cached comparative analysis: {e}")
            return None
    
    def _cache_comparative_analysis(self, cache_key: str, result: ComparativeAnalysisResult):
        """Cache comparative analysis result"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO comparative_analysis_cache
                    (analysis_id, source_a, source_b, results)
                    VALUES (?, ?, ?, ?)
                """, (
                    cache_key,
                    result.source_a,
                    result.source_b,
                    json.dumps(result.__dict__, default=str)
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Failed to cache comparative analysis: {e}")
    
    async def _get_transcripts_by_ids(self, transcript_ids: List[str]) -> List[Dict[str, Any]]:
        """Get transcripts by their IDs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join(['?' for _ in transcript_ids])
                cursor.execute(f"""
                    SELECT doc_id, title, content, metadata, created_at
                    FROM documents
                    WHERE doc_id IN ({placeholders})
                """, transcript_ids)
                
                rows = cursor.fetchall()
                
                transcripts = []
                for row in rows:
                    doc_id, title, content, metadata_str, created_at = row
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    
                    transcripts.append({
                        'id': doc_id,
                        'title': title,
                        'content': content,
                        'metadata': metadata,
                        'created_at': created_at
                    })
                
                return transcripts
                
        except Exception as e:
            logger.error(f"Failed to get transcripts by IDs: {e}")
            return []
    
    async def _get_all_transcripts(self) -> List[Dict[str, Any]]:
        """Get all transcripts"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT doc_id, title, content, metadata, created_at
                    FROM documents
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                
                transcripts = []
                for row in rows:
                    doc_id, title, content, metadata_str, created_at = row
                    metadata = json.loads(metadata_str) if metadata_str else {}
                    
                    transcripts.append({
                        'id': doc_id,
                        'title': title,
                        'content': content,
                        'metadata': metadata,
                        'created_at': created_at
                    })
                
                return transcripts
                
        except Exception as e:
            logger.error(f"Failed to get all transcripts: {e}")
            return []


# Global analytics instance
_analytics_engine = None

def get_analytics_engine() -> AdvancedAnalytics:
    """Get or create global analytics engine instance"""
    global _analytics_engine
    if _analytics_engine is None:
        _analytics_engine = AdvancedAnalytics()
    return _analytics_engine