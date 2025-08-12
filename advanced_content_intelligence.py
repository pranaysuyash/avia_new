"""
Advanced Content Intelligence System
Automated content analysis, tagging, recommendations, and insights
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import spacy
import nltk
from transformers import pipeline, AutoTokenizer, AutoModel
import torch
from collections import Counter, defaultdict
import re
import json

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content"""
    TRANSCRIPT = "transcript"
    DOCUMENT = "document"
    VIDEO = "video"
    AUDIO = "audio"
    MIXED = "mixed"


class ContentCategory(Enum):
    """Content categories"""
    EDUCATION = "education"
    BUSINESS = "business"
    TECHNOLOGY = "technology"
    ENTERTAINMENT = "entertainment"
    NEWS = "news"
    PODCAST = "podcast"
    MEETING = "meeting"
    WEBINAR = "webinar"
    INTERVIEW = "interview"
    TUTORIAL = "tutorial"
    DOCUMENTARY = "documentary"
    PRESENTATION = "presentation"


@dataclass
class ContentMetadata:
    """Rich metadata for content"""
    content_id: str
    title: str
    type: ContentType
    category: Optional[ContentCategory] = None
    language: str = "en"
    duration: Optional[float] = None
    word_count: int = 0
    
    # Extracted features
    tags: List[str] = field(default_factory=list)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    keywords: List[Tuple[str, float]] = field(default_factory=list)
    topics: List[Tuple[str, float]] = field(default_factory=list)
    sentiment: Dict[str, float] = field(default_factory=dict)
    
    # Quality metrics
    quality_score: float = 0.0
    readability_score: float = 0.0
    coherence_score: float = 0.0
    information_density: float = 0.0
    
    # Engagement predictions
    predicted_engagement: float = 0.0
    virality_score: float = 0.0
    target_audience: List[str] = field(default_factory=list)
    
    # Relationships
    similar_content: List[str] = field(default_factory=list)
    recommended_next: List[str] = field(default_factory=list)
    prerequisite_content: List[str] = field(default_factory=list)


class AdvancedContentIntelligence:
    """Advanced content analysis and intelligence system"""
    
    def __init__(self, db: Session = None):
        self.db = db
        
        # Initialize NLP models
        self._init_nlp_models()
        
        # Initialize vectorizers
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            ngram_range=(1, 3),
            stop_words='english'
        )
        
        # Content embeddings cache
        self.content_embeddings = {}
        
        # Category classifiers
        self._init_classifiers()
        
        # Quality metrics
        self._init_quality_metrics()
    
    def _init_nlp_models(self):
        """Initialize NLP models"""
        try:
            # SpaCy for entity extraction
            self.nlp = spacy.load("en_core_web_sm")
        except:
            logger.warning("SpaCy model not found, downloading...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
        
        # Transformers for advanced analysis
        try:
            # Sentiment analysis
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            
            # Zero-shot classification for categories
            self.zero_shot_classifier = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
            
            # Summarization
            self.summarizer = pipeline(
                "summarization",
                model="facebook/bart-large-cnn"
            )
            
            # Question answering
            self.qa_model = pipeline(
                "question-answering",
                model="distilbert-base-cased-distilled-squad"
            )
            
            # Embeddings model
            self.embedding_tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
            self.embedding_model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
            
        except Exception as e:
            logger.error(f"Error loading transformer models: {e}")
            self.sentiment_analyzer = None
            self.zero_shot_classifier = None
            self.summarizer = None
            self.qa_model = None
    
    def _init_classifiers(self):
        """Initialize content classifiers"""
        # Category keywords for rule-based classification
        self.category_keywords = {
            ContentCategory.EDUCATION: [
                'learn', 'tutorial', 'course', 'lesson', 'teach', 'education',
                'training', 'workshop', 'lecture', 'study', 'academic'
            ],
            ContentCategory.BUSINESS: [
                'business', 'company', 'revenue', 'profit', 'strategy', 'market',
                'sales', 'customer', 'enterprise', 'corporate', 'startup'
            ],
            ContentCategory.TECHNOLOGY: [
                'technology', 'software', 'coding', 'programming', 'AI', 'machine learning',
                'data', 'cloud', 'API', 'framework', 'development'
            ],
            ContentCategory.ENTERTAINMENT: [
                'movie', 'music', 'game', 'entertainment', 'fun', 'comedy',
                'drama', 'show', 'performance', 'artist', 'celebrity'
            ],
            ContentCategory.NEWS: [
                'news', 'breaking', 'report', 'update', 'latest', 'today',
                'yesterday', 'announcement', 'press', 'media'
            ]
        }
    
    def _init_quality_metrics(self):
        """Initialize quality metric calculators"""
        # Readability metrics
        self.readability_weights = {
            'flesch_reading_ease': 0.3,
            'avg_sentence_length': 0.2,
            'vocabulary_diversity': 0.2,
            'structure_score': 0.3
        }
    
    async def analyze_content(
        self,
        content: str,
        content_id: str,
        title: str = "",
        content_type: ContentType = ContentType.TRANSCRIPT,
        deep_analysis: bool = True
    ) -> ContentMetadata:
        """
        Perform comprehensive content analysis
        
        Args:
            content: The text content to analyze
            content_id: Unique identifier for the content
            title: Content title
            content_type: Type of content
            deep_analysis: Whether to perform deep analysis
        
        Returns:
            ContentMetadata with all extracted features
        """
        
        metadata = ContentMetadata(
            content_id=content_id,
            title=title,
            type=content_type,
            word_count=len(content.split())
        )
        
        # Basic analysis
        metadata.language = await self._detect_language(content)
        
        # Entity extraction
        metadata.entities = await self._extract_entities(content)
        
        # Keyword extraction
        metadata.keywords = await self._extract_keywords(content)
        
        # Topic modeling
        metadata.topics = await self._extract_topics(content)
        
        # Sentiment analysis
        metadata.sentiment = await self._analyze_sentiment(content)
        
        # Category classification
        metadata.category = await self._classify_category(content, title)
        
        # Tag generation
        metadata.tags = await self._generate_tags(content, metadata)
        
        # Quality scoring
        metadata.quality_score = await self._calculate_quality_score(content)
        metadata.readability_score = await self._calculate_readability(content)
        metadata.coherence_score = await self._calculate_coherence(content)
        metadata.information_density = await self._calculate_information_density(content)
        
        if deep_analysis:
            # Engagement prediction
            metadata.predicted_engagement = await self._predict_engagement(metadata)
            metadata.virality_score = await self._calculate_virality_score(metadata)
            
            # Target audience identification
            metadata.target_audience = await self._identify_target_audience(content, metadata)
            
            # Find similar content
            metadata.similar_content = await self._find_similar_content(content_id, content)
            
            # Generate recommendations
            metadata.recommended_next = await self._generate_recommendations(content_id, metadata)
            
            # Identify prerequisites
            metadata.prerequisite_content = await self._identify_prerequisites(content, metadata)
        
        # Store embeddings for future similarity calculations
        embeddings = await self._generate_embeddings(content)
        self.content_embeddings[content_id] = embeddings
        
        return metadata
    
    async def _detect_language(self, content: str) -> str:
        """Detect content language"""
        try:
            from langdetect import detect
            return detect(content[:1000])  # Use first 1000 chars for speed
        except:
            return "en"
    
    async def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract named entities from content"""
        doc = self.nlp(content[:10000])  # Limit for performance
        
        entities = defaultdict(list)
        for ent in doc.ents:
            entities[ent.label_].append(ent.text)
        
        # Deduplicate while preserving order
        for label in entities:
            entities[label] = list(dict.fromkeys(entities[label]))
        
        return dict(entities)
    
    async def _extract_keywords(self, content: str, top_n: int = 20) -> List[Tuple[str, float]]:
        """Extract keywords using TF-IDF"""
        try:
            # Fit and transform in one step for single document
            tfidf_matrix = self.tfidf_vectorizer.fit_transform([content])
            
            # Get feature names and scores
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            scores = tfidf_matrix.toarray()[0]
            
            # Create keyword-score pairs
            keywords = [(feature_names[i], scores[i]) 
                       for i in scores.argsort()[-top_n:][::-1]
                       if scores[i] > 0]
            
            return keywords
        except Exception as e:
            logger.error(f"Keyword extraction error: {e}")
            return []
    
    async def _extract_topics(self, content: str, num_topics: int = 5) -> List[Tuple[str, float]]:
        """Extract topics using LDA or similar"""
        try:
            # Simple topic extraction using noun phrases
            doc = self.nlp(content[:10000])
            
            # Extract noun phrases
            noun_phrases = []
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Limit phrase length
                    noun_phrases.append(chunk.text.lower())
            
            # Count and rank
            phrase_counts = Counter(noun_phrases)
            total = sum(phrase_counts.values())
            
            # Return top topics with probability scores
            topics = [(phrase, count/total) 
                     for phrase, count in phrase_counts.most_common(num_topics)]
            
            return topics
        except Exception as e:
            logger.error(f"Topic extraction error: {e}")
            return []
    
    async def _analyze_sentiment(self, content: str) -> Dict[str, float]:
        """Analyze content sentiment"""
        if not self.sentiment_analyzer:
            return {"neutral": 1.0}
        
        try:
            # Analyze in chunks for long content
            chunks = [content[i:i+512] for i in range(0, len(content), 512)][:10]
            
            sentiments = []
            for chunk in chunks:
                result = self.sentiment_analyzer(chunk)[0]
                sentiments.append(result)
            
            # Aggregate sentiments
            positive_score = np.mean([s['score'] for s in sentiments if s['label'] == 'POSITIVE'])
            negative_score = np.mean([s['score'] for s in sentiments if s['label'] == 'NEGATIVE'])
            
            return {
                "positive": float(positive_score) if not np.isnan(positive_score) else 0,
                "negative": float(negative_score) if not np.isnan(negative_score) else 0,
                "neutral": 1.0 - (positive_score + negative_score) if not np.isnan(positive_score + negative_score) else 1.0
            }
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return {"neutral": 1.0}
    
    async def _classify_category(self, content: str, title: str) -> Optional[ContentCategory]:
        """Classify content into categories"""
        combined_text = f"{title} {content[:1000]}"
        
        # Try zero-shot classification first
        if self.zero_shot_classifier:
            try:
                candidate_labels = [cat.value for cat in ContentCategory]
                result = self.zero_shot_classifier(
                    combined_text,
                    candidate_labels=candidate_labels
                )
                
                if result['scores'][0] > 0.5:
                    return ContentCategory(result['labels'][0])
            except Exception as e:
                logger.error(f"Zero-shot classification error: {e}")
        
        # Fallback to keyword-based classification
        combined_lower = combined_text.lower()
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in combined_lower)
            category_scores[category] = score
        
        if category_scores:
            best_category = max(category_scores.items(), key=lambda x: x[1])
            if best_category[1] > 0:
                return best_category[0]
        
        return None
    
    async def _generate_tags(
        self,
        content: str,
        metadata: ContentMetadata,
        max_tags: int = 10
    ) -> List[str]:
        """Generate relevant tags for content"""
        tags = set()
        
        # Add category as tag
        if metadata.category:
            tags.add(metadata.category.value)
        
        # Add top keywords as tags
        for keyword, score in metadata.keywords[:5]:
            if score > 0.1 and len(keyword) > 3:
                tags.add(keyword)
        
        # Add significant entities as tags
        for entity_type, entities in metadata.entities.items():
            if entity_type in ['PERSON', 'ORG', 'PRODUCT', 'WORK_OF_ART']:
                tags.update(entities[:2])  # Add top 2 entities of each type
        
        # Add topic-based tags
        for topic, score in metadata.topics[:3]:
            if score > 0.1:
                tags.add(topic)
        
        # Add sentiment tags if significant
        if metadata.sentiment.get('positive', 0) > 0.7:
            tags.add('positive')
        elif metadata.sentiment.get('negative', 0) > 0.7:
            tags.add('negative')
        
        # Add content type tag
        tags.add(metadata.type.value)
        
        # Limit and clean tags
        tags = list(tags)[:max_tags]
        tags = [tag.lower().replace(' ', '_') for tag in tags if len(tag) > 2]
        
        return tags
    
    async def _calculate_quality_score(self, content: str) -> float:
        """Calculate overall content quality score"""
        scores = []
        
        # Length score (optimal length)
        word_count = len(content.split())
        if 500 <= word_count <= 5000:
            length_score = 1.0
        elif 200 <= word_count < 500 or 5000 < word_count <= 10000:
            length_score = 0.7
        else:
            length_score = 0.4
        scores.append(length_score)
        
        # Vocabulary diversity
        words = content.lower().split()
        unique_words = set(words)
        diversity_score = min(len(unique_words) / len(words) * 2, 1.0) if words else 0
        scores.append(diversity_score)
        
        # Sentence structure variety
        doc = self.nlp(content[:5000])
        sentence_lengths = [len(sent.text.split()) for sent in doc.sents]
        if sentence_lengths:
            length_variance = np.std(sentence_lengths) / np.mean(sentence_lengths)
            structure_score = min(length_variance, 1.0)
        else:
            structure_score = 0
        scores.append(structure_score)
        
        # Grammar and spelling (simplified)
        # In production, use language_tool_python or similar
        grammar_score = 0.9  # Placeholder
        scores.append(grammar_score)
        
        return float(np.mean(scores))
    
    async def _calculate_readability(self, content: str) -> float:
        """Calculate readability score (Flesch Reading Ease approximation)"""
        words = content.split()
        sentences = content.split('.')
        syllables = sum(self._count_syllables(word) for word in words)
        
        if len(sentences) > 0 and len(words) > 0:
            avg_sentence_length = len(words) / len(sentences)
            avg_syllables_per_word = syllables / len(words)
            
            # Flesch Reading Ease formula
            score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word
            
            # Normalize to 0-1 range
            normalized_score = max(0, min(score, 100)) / 100
            return float(normalized_score)
        
        return 0.5
    
    def _count_syllables(self, word: str) -> int:
        """Count syllables in a word (approximation)"""
        word = word.lower()
        vowels = "aeiou"
        syllable_count = 0
        previous_was_vowel = False
        
        for char in word:
            is_vowel = char in vowels
            if is_vowel and not previous_was_vowel:
                syllable_count += 1
            previous_was_vowel = is_vowel
        
        # Adjust for silent e
        if word.endswith('e'):
            syllable_count -= 1
        
        # Ensure at least one syllable
        return max(1, syllable_count)
    
    async def _calculate_coherence(self, content: str) -> float:
        """Calculate content coherence score"""
        # Split into paragraphs or sentences
        sentences = content.split('.')[:50]  # Limit for performance
        
        if len(sentences) < 2:
            return 0.5
        
        # Calculate sentence-to-sentence similarity
        similarities = []
        for i in range(len(sentences) - 1):
            if sentences[i] and sentences[i+1]:
                # Simple word overlap similarity
                words1 = set(sentences[i].lower().split())
                words2 = set(sentences[i+1].lower().split())
                
                if words1 and words2:
                    overlap = len(words1 & words2)
                    total = len(words1 | words2)
                    similarity = overlap / total if total > 0 else 0
                    similarities.append(similarity)
        
        if similarities:
            # Higher similarity indicates better coherence
            coherence_score = float(np.mean(similarities))
            return min(coherence_score * 3, 1.0)  # Scale and cap at 1.0
        
        return 0.5
    
    async def _calculate_information_density(self, content: str) -> float:
        """Calculate information density of content"""
        # Extract meaningful words (nouns, verbs, adjectives)
        doc = self.nlp(content[:5000])
        
        meaningful_pos = {'NOUN', 'VERB', 'ADJ', 'PROPN'}
        meaningful_words = [token for token in doc if token.pos_ in meaningful_pos]
        
        total_words = len(doc)
        if total_words > 0:
            density = len(meaningful_words) / total_words
            return float(min(density * 2, 1.0))  # Scale and cap
        
        return 0.5
    
    async def _predict_engagement(self, metadata: ContentMetadata) -> float:
        """Predict content engagement level"""
        engagement_score = 0.0
        
        # Quality contributes to engagement
        engagement_score += metadata.quality_score * 0.3
        
        # Readability affects engagement
        engagement_score += metadata.readability_score * 0.2
        
        # Positive sentiment increases engagement
        engagement_score += metadata.sentiment.get('positive', 0) * 0.2
        
        # Information density (not too high, not too low)
        optimal_density = 0.6
        density_diff = abs(metadata.information_density - optimal_density)
        engagement_score += (1 - density_diff) * 0.15
        
        # Category bonuses
        engaging_categories = {
            ContentCategory.ENTERTAINMENT: 0.15,
            ContentCategory.TUTORIAL: 0.10,
            ContentCategory.NEWS: 0.08
        }
        
        if metadata.category in engaging_categories:
            engagement_score += engaging_categories[metadata.category]
        
        return float(min(engagement_score, 1.0))
    
    async def _calculate_virality_score(self, metadata: ContentMetadata) -> float:
        """Calculate potential virality score"""
        virality_score = 0.0
        
        # High engagement potential
        virality_score += metadata.predicted_engagement * 0.3
        
        # Strong sentiment (either positive or negative)
        max_sentiment = max(
            metadata.sentiment.get('positive', 0),
            metadata.sentiment.get('negative', 0)
        )
        virality_score += max_sentiment * 0.25
        
        # Trending topics boost virality
        # In production, check against trending topics database
        trending_bonus = 0.2  # Placeholder
        virality_score += trending_bonus
        
        # Optimal length for sharing
        if 300 <= metadata.word_count <= 2000:
            virality_score += 0.15
        
        # Entity mentions (celebrities, brands, etc.)
        if metadata.entities.get('PERSON') or metadata.entities.get('ORG'):
            virality_score += 0.1
        
        return float(min(virality_score, 1.0))
    
    async def _identify_target_audience(
        self,
        content: str,
        metadata: ContentMetadata
    ) -> List[str]:
        """Identify target audience segments"""
        audiences = []
        
        # Based on category
        category_audiences = {
            ContentCategory.EDUCATION: ['students', 'educators', 'learners'],
            ContentCategory.BUSINESS: ['professionals', 'entrepreneurs', 'managers'],
            ContentCategory.TECHNOLOGY: ['developers', 'tech_enthusiasts', 'IT_professionals'],
            ContentCategory.ENTERTAINMENT: ['general_audience', 'fans', 'casual_viewers'],
            ContentCategory.NEWS: ['news_readers', 'informed_citizens', 'current_affairs_enthusiasts']
        }
        
        if metadata.category and metadata.category in category_audiences:
            audiences.extend(category_audiences[metadata.category])
        
        # Based on complexity (readability)
        if metadata.readability_score > 0.7:
            audiences.append('general_audience')
        elif metadata.readability_score < 0.4:
            audiences.append('expert_audience')
        else:
            audiences.append('intermediate_audience')
        
        # Based on entities mentioned
        if 'ORG' in metadata.entities:
            audiences.append('business_audience')
        
        if 'PERSON' in metadata.entities:
            if any('CEO' in e or 'founder' in e.lower() for e in metadata.entities['PERSON']):
                audiences.append('leadership_audience')
        
        # Deduplicate
        return list(set(audiences))
    
    async def _generate_embeddings(self, content: str) -> np.ndarray:
        """Generate semantic embeddings for content"""
        if not self.embedding_model:
            # Fallback to TF-IDF if transformer not available
            return self.tfidf_vectorizer.fit_transform([content]).toarray()[0]
        
        try:
            # Truncate content for embedding model
            max_length = 512
            inputs = self.embedding_tokenizer(
                content[:max_length],
                return_tensors='pt',
                truncation=True,
                padding=True,
                max_length=max_length
            )
            
            with torch.no_grad():
                outputs = self.embedding_model(**inputs)
                # Use mean pooling
                embeddings = outputs.last_hidden_state.mean(dim=1).numpy()[0]
            
            return embeddings
        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            return np.zeros(384)  # Default embedding size
    
    async def _find_similar_content(
        self,
        content_id: str,
        content: str,
        top_k: int = 5
    ) -> List[str]:
        """Find similar content based on embeddings"""
        if not self.content_embeddings:
            return []
        
        # Generate embedding for current content
        current_embedding = await self._generate_embeddings(content)
        
        # Calculate similarities
        similarities = []
        for other_id, other_embedding in self.content_embeddings.items():
            if other_id != content_id:
                similarity = cosine_similarity(
                    [current_embedding],
                    [other_embedding]
                )[0][0]
                similarities.append((other_id, similarity))
        
        # Sort and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [content_id for content_id, _ in similarities[:top_k]]
    
    async def _generate_recommendations(
        self,
        content_id: str,
        metadata: ContentMetadata
    ) -> List[str]:
        """Generate content recommendations"""
        recommendations = []
        
        # Get similar content as base recommendations
        recommendations.extend(metadata.similar_content[:3])
        
        # Add content from same category
        if self.db and metadata.category:
            try:
                from database.models import Transcript
                
                same_category = self.db.query(Transcript).filter(
                    Transcript.metadata['category'].astext == metadata.category.value,
                    Transcript.id != content_id
                ).limit(2).all()
                
                recommendations.extend([t.id for t in same_category])
            except Exception as e:
                logger.error(f"Database recommendation query error: {e}")
        
        # Add trending content (placeholder - would query trending service)
        # recommendations.extend(get_trending_content()[:2])
        
        # Deduplicate while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations[:5]
    
    async def _identify_prerequisites(
        self,
        content: str,
        metadata: ContentMetadata
    ) -> List[str]:
        """Identify prerequisite content"""
        prerequisites = []
        
        # For technical content, check for advanced terms
        if metadata.category == ContentCategory.TECHNOLOGY:
            advanced_terms = ['advanced', 'expert', 'deep dive', 'masterclass']
            if any(term in content.lower() for term in advanced_terms):
                # Would query for beginner/intermediate content in same topic
                prerequisites.append('beginner_' + metadata.category.value)
        
        # For educational content, check for level indicators
        if metadata.category == ContentCategory.EDUCATION:
            if 'prerequisite' in content.lower() or 'requires' in content.lower():
                # Extract mentioned prerequisites
                doc = self.nlp(content[:2000])
                for sent in doc.sents:
                    if 'prerequisite' in sent.text.lower() or 'requires' in sent.text.lower():
                        # Extract noun phrases as potential prerequisites
                        for chunk in sent.noun_chunks:
                            if len(chunk.text) > 3:
                                prerequisites.append(chunk.text)
                                if len(prerequisites) >= 3:
                                    break
        
        return prerequisites[:5]
    
    async def generate_summary(
        self,
        content: str,
        max_length: int = 150,
        style: str = "bullets"
    ) -> str:
        """Generate content summary"""
        if not self.summarizer:
            # Fallback to simple extractive summary
            sentences = content.split('.')[:3]
            return '. '.join(sentences)
        
        try:
            # Use transformer for summary
            summary = self.summarizer(
                content[:1024],  # Limit input length
                max_length=max_length,
                min_length=50,
                do_sample=False
            )[0]['summary_text']
            
            if style == "bullets":
                # Convert to bullet points
                sentences = summary.split('.')
                bullets = []
                for sent in sentences:
                    if sent.strip():
                        bullets.append(f"• {sent.strip()}")
                return '\n'.join(bullets)
            
            return summary
        except Exception as e:
            logger.error(f"Summarization error: {e}")
            return content[:max_length]
    
    async def extract_key_insights(
        self,
        content: str,
        metadata: ContentMetadata
    ) -> List[str]:
        """Extract key insights from content"""
        insights = []
        
        # Look for insight indicators
        insight_patterns = [
            r"key (?:finding|insight|takeaway)",
            r"important(?:ly)?",
            r"significant(?:ly)?",
            r"notable|notably",
            r"conclusion",
            r"the (?:main|primary|key) (?:point|idea|concept)"
        ]
        
        doc = self.nlp(content)
        for sent in doc.sents:
            sent_lower = sent.text.lower()
            for pattern in insight_patterns:
                if re.search(pattern, sent_lower):
                    insights.append(sent.text.strip())
                    break
        
        # Add top entities as insights
        if metadata.entities.get('ORG'):
            for org in metadata.entities['ORG'][:2]:
                insights.append(f"Mentions {org}")
        
        # Add significant statistics
        stat_pattern = r'\d+(?:\.\d+)?%|\$\d+(?:,\d{3})*(?:\.\d+)?[MBK]?'
        stats = re.findall(stat_pattern, content)
        for stat in stats[:3]:
            # Find context around statistic
            idx = content.find(stat)
            if idx > 0:
                start = max(0, idx - 50)
                end = min(len(content), idx + 50)
                context = content[start:end]
                insights.append(f"Key metric: {context.strip()}")
        
        return insights[:5]
    
    async def cluster_content(
        self,
        content_ids: List[str],
        num_clusters: int = 5
    ) -> Dict[int, List[str]]:
        """Cluster content into groups"""
        if len(content_ids) < num_clusters:
            num_clusters = len(content_ids)
        
        # Get embeddings for all content
        embeddings = []
        valid_ids = []
        
        for content_id in content_ids:
            if content_id in self.content_embeddings:
                embeddings.append(self.content_embeddings[content_id])
                valid_ids.append(content_id)
        
        if len(embeddings) < 2:
            return {0: valid_ids}
        
        # Perform clustering
        kmeans = KMeans(n_clusters=min(num_clusters, len(embeddings)))
        cluster_labels = kmeans.fit_predict(embeddings)
        
        # Group content by cluster
        clusters = defaultdict(list)
        for content_id, label in zip(valid_ids, cluster_labels):
            clusters[int(label)].append(content_id)
        
        return dict(clusters)
    
    def get_trending_topics(
        self,
        time_window: timedelta = timedelta(days=7)
    ) -> List[Tuple[str, int]]:
        """Get trending topics from recent content"""
        # This would query a time-series database in production
        # For now, return placeholder trending topics
        return [
            ("artificial_intelligence", 150),
            ("sustainability", 120),
            ("remote_work", 100),
            ("cryptocurrency", 90),
            ("mental_health", 85)
        ]


# Global instance
content_intelligence = AdvancedContentIntelligence()